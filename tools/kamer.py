#!/usr/bin/env python3
"""kamer.py — zet een FLUX-plaatje om naar een kamer: 160x128 multicolor bitmap (§6.2).

    python3 tools/kamer.py data/kamers.txt build/gen

data/kamers.txt, één kamer per regel ('#' is commentaar):
    plein  data/flux/dawnhaven.png  boven=190  kleur=1.5  licht=1.0  sterkte=0.5

    boven    bovenste pixelrij van de strook in het bronplaatje (de strook is 5:2, over de hele breedte)
    kleur    verzadiging vooraf; licht: helderheid vooraf; sterkte: Floyd-Steinberg (0 = geen menging)
    voorgrond=data/plein_voorgrond.txt   (mag weg) wat vóór een actor komt die erachter staat (§6.2):
             de '#'-pixels (bv. het torentje van de fontein) worden ook een voorgrond-sprite. In de bitmap krijgen
             ze dezelfde 2 kleuren als die sprite (zwart + 1 kleur), zodat je niets ziet als de sprite aan of uit
             gaat. De motor zet hem aan als de voeten van Eldric in het ACHTER-vak staan (scripts/*.hcs).

Per kamer:
    build/gen/kamer_<naam>.bin   ingepakt (tools/inpak.py): bitmap (16 rijen x 320) | scherm (640) | kleur (640)
    build/gen/kamer_<naam>.png   controle: de bronstrook naast de C64-pixels, zoals de VIC ze uit de bytes leest
    build/gen/kamer_<naam>_voorgrond.asm   de voorgrond-sprite (64 bytes), zijn plek en kleur (VG_<NAAM> = 0: geen)

Regels (§6.2 en de naden van §6.3):
    - de achtergrondkleur ($d021) is zwart, voor de hele kamer en voor het hele scherm;
    - de bovenste pixelrij en de onderste 2 pixelrijen zijn zwart (de naden met tekst erboven en de balk eronder).
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c64beeld as cb   # noqa: E402  (kleuren, Lab, de keuze van 3 kleuren per vak, Floyd-Steinberg)
import inpak            # noqa: E402

B, H = 160, 128          # multicolor-pixels
RIJEN, KOL = H // 8, B // 4
ACHTER = 0               # zwart
ZWART_BOVEN, ZWART_ONDER = 1, 2
MAX_INGEPAKT = 6400      # de kamerbuffer in src/kamer.asm (ongepakt is het 5120 + 640 + 640)


def lees_lijst(pad):
    kamers = []
    for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
        regel = regel.split("#", 1)[0].split()
        if not regel:
            continue
        if len(regel) < 2:
            raise SystemExit("%s:%d: naam en plaatje nodig" % (pad, nr))
        opties = {"boven": 0, "kleur": 1.5, "licht": 1.0, "sterkte": 0.5, "voorgrond": None}
        for o in regel[2:]:
            k, _, v = o.partition("=")
            if k not in opties:
                raise SystemExit("%s:%d: onbekende optie %s" % (pad, nr, k))
            opties[k] = v if k == "voorgrond" else float(v)
        kamers.append((regel[0], regel[1], opties, nr))
    return kamers


def lees_voorgrond(pad):
    """Een voorgrondbestand: 'VAK x,y b,h' en dan h regels van b tekens ('#' voorgrond, '.' of '-' niet);
    regels die met ';' beginnen zijn opmerkingen; 'KLEUR naam' kiest de kleur (anders de beste).
    Geeft (masker H x B met True = voorgrond, kleurnummer of None)."""
    vak, rijen, vkleur = None, [], None
    for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
        regel = regel.rstrip("\n").rstrip()
        if not regel or regel.startswith(";"):
            continue
        if regel.startswith("KLEUR"):
            naam = regel.split()[1]
            if naam not in cb.NAMEN:
                raise SystemExit("%s:%d: onbekende kleur %s" % (pad, nr, naam))
            vkleur = cb.NAMEN.index(naam)
            continue
        if regel.startswith("VAK"):
            a, b = regel.split()[1:3]
            x, y = (int(v) for v in a.split(","))
            w, h = (int(v) for v in b.split(","))
            vak = (x, y, w, h)
            continue
        if vak is None or set(regel) - set("#.-"):
            raise SystemExit("%s:%d: eerst VAK x,y b,h, dan regels van '#', '.' en '-'" % (pad, nr))
        rijen.append(regel)
    x, y, w, h = vak
    if x + w > B or y + h > H or len(rijen) != h or any(len(r) != w for r in rijen):
        raise SystemExit("%s: verwacht %d regels van %d tekens, binnen de kamer" % (pad, h, w))
    m = np.zeros((H, B), dtype=bool)
    m[y:y + h, x:x + w] = [[c == "#" for c in r] for r in rijen]
    ys, xs = np.nonzero(m)
    if len(ys) and (xs.max() - xs.min() >= 12 or ys.max() - ys.min() >= 21):
        raise SystemExit("%s: de voorgrond past niet in één sprite (12 x 21 multicolor-pixels)" % pad)
    return m, vkleur


def strook(beeld, boven):
    """Snijd een strook van 5:2 uit en verklein naar 160x128 C64-pixels (elk 2 schermpixels breed)."""
    img = Image.fromarray(beeld.astype(np.uint8))
    bw, bh = img.size
    sh = round(bw * 2 / 5)
    boven = int(boven)
    if boven < 0 or boven + sh > bh:
        raise SystemExit("boven=%d past niet: de strook is %d hoog, het plaatje %d" % (boven, sh, bh))
    img = img.crop((0, boven, bw, boven + sh))
    return img, np.asarray(img.resize((B, H), Image.LANCZOS), dtype=np.float32)


def omzetten(klein, sterkte, vg=None, vkleur=None):
    """vg: masker van de voorgrond (of None). Geeft bitmap, scherm, kleur, de C64-pixels en de voorgrondkleur."""
    import itertools
    L = cb.lab(klein)
    D = cb.afstanden(L)
    keuze, _ = cb.kies_vakjes(D, 4, 8, [ACHTER], 3)
    if vg is not None and vg.any():
        # één kleur (naast zwart) voor de hele voorgrond: die heeft de sprite ook
        d = D[vg]
        if vkleur is None:
            vkleur = min(range(1, 16), key=lambda k: np.minimum(d[:, ACHTER], d[:, k]).sum())
        for r, c in {(y // 8, x // 4) for y, x in zip(*np.nonzero(vg))}:
            blok = (slice(r * 8, r * 8 + 8), slice(c * 4, c * 4 + 4))
            dd, v = D[blok].reshape(32, 16), vg[blok].reshape(32)
            beste = None
            for a, b in itertools.combinations_with_replacement(range(16), 2):
                k = np.minimum(dd[v][:, ACHTER], dd[v][:, vkleur]).sum() + \
                    np.minimum.reduce([dd[~v][:, q] for q in (ACHTER, vkleur, a, b)]).sum()
                if beste is None or k < beste[0]:
                    beste = (k, a, b)
            keuze[r, c] = [vkleur, beste[1], beste[2]]
    toegestaan = {}

    def kleuren_van(y, x):
        r, c = y // 8, x // 4
        voor = vg is not None and vg[y, x]
        if (r, c, voor) not in toegestaan:
            toegestaan[(r, c, voor)] = np.array([ACHTER, vkleur] if voor else [ACHTER] + list(keuze[r, c]))
        return toegestaan[(r, c, voor)]
    pix = cb.pixels_kiezen(L, kleuren_van, "fs" if sterkte > 0 else "geen", sterkte)
    pix[:ZWART_BOVEN, :] = ACHTER
    pix[H - ZWART_ONDER:, :] = ACHTER

    bitmap, scherm, kleur = bytearray(RIJEN * 320), bytearray(RIJEN * 40), bytearray(RIJEN * 40)
    for r in range(RIJEN):
        for c in range(KOL):
            k1, k2, k3 = (int(v) for v in keuze[r, c])
            scherm[r * 40 + c] = (k1 << 4) | k2
            kleur[r * 40 + c] = k3
            for y in range(8):
                v = 0
                for x in range(4):
                    p = int(pix[r * 8 + y, c * 4 + x])
                    b = 0 if p == ACHTER else 1 if p == k1 else 2 if p == k2 else 3
                    v |= b << (6 - 2 * x)
                bitmap[(r * 40 + c) * 8 + y] = v
    return bytes(bitmap), bytes(scherm), bytes(kleur), vkleur


def voorgrond_asm(naam, vg, pix, vkleur, pad):
    """De voorgrond-sprite: '#'-pixels met hun kleur uit de kamer; zwart = %01 ($d025), vkleur = %10 (eigen kleur)."""
    N = naam.upper()
    L = ["// gemaakt door tools/kamer.py; niet met de hand wijzigen"]
    if vg is None or not vg.any():
        L += [".const VG_%s = 0" % N]
    else:
        ys, xs = np.nonzero(vg)
        x0, y0 = int(xs.min()), int(ys.min())
        data = []
        for r in range(21):
            bits = 0
            for c in range(12):
                y, x = y0 + r, x0 + c
                code = 0
                if y < H and x < B and vg[y, x]:
                    code = 1 if pix[y, x] == ACHTER else 2
                    assert pix[y, x] in (ACHTER, vkleur)
                bits = bits << 2 | code
            data += [bits >> 16 & 255, bits >> 8 & 255, bits & 255]
        data.append(0)
        L += [".const VG_%s = 1" % N,
              ".const VG_%s_X = %d    // multicolor-pixels" % (N, x0),
              ".const VG_%s_Y = %d    // kamerrij" % (N, y0),
              ".const VG_%s_KLEUR = %d    // %s" % (N, vkleur, cb.NAMEN[vkleur]),
              ".segment Data", "vg_%s_sprite:" % naam]
        for i in range(0, 64, 16):
            L.append("        .byte " + ", ".join("$%02x" % v for v in data[i:i + 16]))
    open(pad, "w").write("\n".join(L) + "\n")


def lees_terug(bitmap, scherm, kleur):
    """Zoals de VIC het leest: uit de bytes terug naar C64-kleuren per multicolor-pixel."""
    uit = np.zeros((H, B), dtype=np.int64)
    for r in range(RIJEN):
        for c in range(KOL):
            s, k = scherm[r * 40 + c], kleur[r * 40 + c] & 15
            kl = [ACHTER, s >> 4, s & 15, k]
            for y in range(8):
                v = bitmap[(r * 40 + c) * 8 + y]
                for x in range(4):
                    uit[r * 8 + y, c * 4 + x] = kl[(v >> (6 - 2 * x)) & 3]
    return uit


def controle_png(bron, pix, pad):
    links = bron.resize((320, 128), Image.LANCZOS)
    rechts = Image.fromarray(cb.RGB[pix].astype(np.uint8)).resize((320, 128), Image.NEAREST)
    doek = Image.new("RGB", (648, 128), (40, 40, 40))
    doek.paste(links, (0, 0))
    doek.paste(rechts, (328, 0))
    doek.resize((648 * 2, 256), Image.NEAREST).save(pad)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    lijst, uitmap = sys.argv[1], sys.argv[2]
    os.makedirs(uitmap, exist_ok=True)
    wortel = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for naam, plaatje, o, nr in lees_lijst(lijst):
        bin_pad = os.path.join(uitmap, "kamer_%s.bin" % naam)
        bron_pad = os.path.join(wortel, plaatje)
        vg_pad = os.path.join(wortel, o["voorgrond"]) if o["voorgrond"] else None
        vg_asm = os.path.join(uitmap, "kamer_%s_voorgrond.asm" % naam)
        if not os.path.exists(bron_pad):
            raise SystemExit("%s:%d: plaatje %s bestaat niet" % (lijst, nr, plaatje))
        # alleen opnieuw als de bron, de lijst of dit programma nieuwer is
        if os.path.exists(bin_pad) and os.path.exists(vg_asm) and all(os.path.getmtime(bin_pad) > os.path.getmtime(p)
                                           for p in (bron_pad, lijst, __file__, cb.__file__) + ((vg_pad,) if vg_pad else ())):
            print("[kamer]   %s is bij" % naam)
            continue
        beeld = cb.voorbewerk(cb.laad(bron_pad), o["kleur"], o["licht"])
        bron, klein = strook(beeld, o["boven"])
        vg, vkleur = lees_voorgrond(vg_pad) if vg_pad else (None, None)
        bitmap, scherm, kleur, vkleur = omzetten(klein, o["sterkte"], vg, vkleur)
        pix = lees_terug(bitmap, scherm, kleur)
        voorgrond_asm(naam, vg, pix, vkleur, vg_asm)
        assert (pix[0] == ACHTER).all() and (pix[-ZWART_ONDER:] == ACHTER).all()
        data = inpak.pak(bitmap) + inpak.pak(scherm) + inpak.pak(kleur)
        if len(data) > MAX_INGEPAKT:
            raise SystemExit("%s:%d: kamer %s is ingepakt %d bytes, de buffer %d" % (lijst, nr, naam, len(data), MAX_INGEPAKT))
        # controle: uitpakken geeft weer hetzelfde
        a, i = inpak.uitpak(data)
        b, i = inpak.uitpak(data, i)
        c, i = inpak.uitpak(data, i)
        assert (a, b, c) == (bitmap, scherm, kleur) and i == len(data)
        open(bin_pad, "wb").write(data)
        controle_png(Image.fromarray(np.asarray(bron)), pix, os.path.join(uitmap, "kamer_%s.png" % naam))
        print("[kamer]   %s: %d bytes ingepakt (ongepakt %d)" % (naam, len(data), len(bitmap) + len(scherm) + len(kleur)))


if __name__ == "__main__":
    main()
