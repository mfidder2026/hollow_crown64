#!/usr/bin/env python3
"""kamer.py — zet een FLUX-plaatje om naar een kamer: 160x128 multicolor bitmap (§6.2).

    python3 tools/kamer.py data/kamers.txt build/gen

data/kamers.txt, één kamer per regel ('#' is commentaar):
    plein  data/flux/dawnhaven.png  boven=190  kleur=1.5  licht=1.0  sterkte=0.5

    boven    bovenste pixelrij van de strook in het bronplaatje (de strook is 5:2, over de hele breedte)
    kleur    verzadiging vooraf; licht: helderheid vooraf; sterkte: Floyd-Steinberg (0 = geen menging)
    patch=naam:x,y,b,h:plaatje   (mag vaker) een patch (§6.2): een rechthoek van vakjes (x, b veelvoud van 4;
             y, h veelvoud van 8; kamerpixels) uit een tweede versie van het plaatje (bv. de deur open).
             De scripts zetten hem met PATCH naam; de volgorde hier is zijn nummer.
    voorgrond=data/plein_voorgrond.txt   (mag weg) wat vóór een actor komt die erachter staat (§6.2):
             de '#'-pixels (bv. het torentje van de fontein) worden ook een voorgrond-sprite. In de bitmap krijgen
             ze dezelfde 2 kleuren als die sprite (zwart + 1 kleur), zodat je niets ziet als de sprite aan of uit
             gaat. De motor zet hem aan als de voeten van Eldric in het ACHTER-vak staan (scripts/*.hcs).

Per kamer:
    build/gen/kamer_<naam>.bin   ingepakt (tools/inpak.py): bitmap (16 rijen x 320) | scherm (640) | kleur (640)
    build/gen/kamer_<naam>.png   controle: de bronstrook naast de C64-pixels, zoals de VIC ze uit de bytes leest
    build/gen/kamer_<naam>.prg   het kamerbestand voor de diskette, geladen op KAMER_BUF ($A000):
                                   +0 woord: plek van het voorgrondblok (0 = geen)
                                   +2 woord: plek van de patchtabel
                                   +4 het ingepakte plaatje (bitmap | scherm | kleur)
                                   voorgrondblok: x (multicolor-pixels), y, kleur, 64 bytes sprite
                                   patchtabel: aantal, per patch kolom, rij, breedte, hoogte (vakjes), plek (woord)
                                   van zijn ingepakte data (per rij de bitmapbytes, dan scherm, dan kleur)

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
MAX_INGEPAKT = 6400      # alleen het plaatje (ongepakt is het 5120 + 640 + 640)
KAMER_BUF = 0xA000       # gelijk houden met src/geheugen.asm
KAMER_BUF_GROOTTE = 0x2000


def lees_lijst(pad):
    kamers = []
    for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
        regel = regel.split("#", 1)[0].split()
        if not regel:
            continue
        if len(regel) < 2:
            raise SystemExit("%s:%d: naam en plaatje nodig" % (pad, nr))
        opties = {"boven": 0, "kleur": 1.5, "licht": 1.0, "sterkte": 0.5, "voorgrond": None, "patches": []}
        for o in regel[2:]:
            k, _, v = o.partition("=")
            if k == "patch":
                try:
                    pnaam, vak, plaatje = v.split(":")
                    x, y, b, h = (int(q) for q in vak.split(","))
                except ValueError:
                    raise SystemExit("%s:%d: patch=naam:x,y,b,h:plaatje" % (pad, nr))
                if x % 4 or b % 4 or y % 8 or h % 8 or b < 4 or h < 8 or x + b > B or y + h > H:
                    raise SystemExit("%s:%d: patch %s: x en breedte veelvoud van 4, y en hoogte van 8, in de kamer"
                                     % (pad, nr, pnaam))
                opties["patches"].append((pnaam, (x, y, b, h), plaatje))
                continue
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


def voorgrond_blok(vg, pix, vkleur):
    """De voorgrond-sprite: '#'-pixels met hun kleur uit de kamer; zwart = %01 ($d025), vkleur = %10 (eigen kleur).
    Geeft x, y, kleur en 64 bytes (of None)."""
    if vg is None or not vg.any():
        return None
    if True:
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
        return bytes([x0, y0, vkleur]) + bytes(data)


def patch_data(bitmap, scherm, kleur, x, y, b, h):
    """De vakjes van een patch: per vakjesrij de bitmapbytes, dan alle schermbytes, dan alle kleurbytes."""
    k0, r0, kb, kh = x // 4, y // 8, b // 4, h // 8
    bm, sc, kl = bytearray(), bytearray(), bytearray()
    for r in range(r0, r0 + kh):
        bm += bitmap[(r * 40 + k0) * 8:(r * 40 + k0 + kb) * 8]
        sc += scherm[r * 40 + k0:r * 40 + k0 + kb]
        kl += kleur[r * 40 + k0:r * 40 + k0 + kb]
    return k0, r0, kb, kh, bytes(bm + sc + kl)


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
        prg = os.path.join(uitmap, "kamer_%s.prg" % naam)
        extra = [vg_pad] if vg_pad else []
        extra += [os.path.join(wortel, p[2]) for p in o["patches"]]
        if not os.path.exists(bron_pad):
            raise SystemExit("%s:%d: plaatje %s bestaat niet" % (lijst, nr, plaatje))
        # alleen opnieuw als de bron, de lijst of dit programma nieuwer is
        if os.path.exists(bin_pad) and os.path.exists(prg) and all(os.path.getmtime(prg) > os.path.getmtime(p)
                                                                   for p in [bron_pad, lijst, __file__, cb.__file__] + extra):
            print("[kamer]   %s is bij" % naam)
            continue
        beeld = cb.voorbewerk(cb.laad(bron_pad), o["kleur"], o["licht"])
        bron, klein = strook(beeld, o["boven"])
        vg, vkleur = lees_voorgrond(vg_pad) if vg_pad else (None, None)
        bitmap, scherm, kleur, vkleur = omzetten(klein, o["sterkte"], vg, vkleur)
        pix = lees_terug(bitmap, scherm, kleur)
        vgblok = voorgrond_blok(vg, pix, vkleur)
        patches = []
        for pnaam, (x, y, b, h), plaatje in o["patches"]:
            pbron = os.path.join(wortel, plaatje)
            if not os.path.exists(pbron):
                raise SystemExit("%s:%d: patch %s: plaatje %s bestaat niet" % (lijst, nr, pnaam, plaatje))
            _, pklein = strook(cb.voorbewerk(cb.laad(pbron), o["kleur"], o["licht"]), o["boven"])
            pb, ps, pk, _ = omzetten(pklein, o["sterkte"], vg, vkleur)
            patches.append(patch_data(pb, ps, pk, x, y, b, h))
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
        # het kamerbestand voor de diskette
        bestand = bytearray(4) + data
        vg_plek = 0
        if vgblok:
            vg_plek = len(bestand)
            bestand += vgblok
        tabel = len(bestand)
        bestand += bytes([len(patches)]) + bytes(6 * len(patches))
        for i, (k0, r0, kb, kh, pdata) in enumerate(patches):
            plek = len(bestand)
            bestand += inpak.pak(pdata)
            bestand[tabel + 1 + 6 * i:tabel + 7 + 6 * i] = bytes([k0, r0, kb, kh, plek & 255, plek >> 8])
        bestand[0:4] = bytes([vg_plek & 255, vg_plek >> 8, tabel & 255, tabel >> 8])
        if len(bestand) > KAMER_BUF_GROOTTE:
            raise SystemExit("%s:%d: kamer %s is %d bytes, de kamerbuffer %d" % (lijst, nr, naam, len(bestand), KAMER_BUF_GROOTTE))
        open(prg, "wb").write(bytes([KAMER_BUF & 255, KAMER_BUF >> 8]) + bestand)
        controle_png(Image.fromarray(np.asarray(bron)), pix, os.path.join(uitmap, "kamer_%s.png" % naam))
        print("[kamer]   %s: %d bytes ingepakt (ongepakt %d), kamerbestand %d bytes, %d patches" % (
            naam, len(data), len(bitmap) + len(scherm) + len(kleur), len(bestand), len(patches)))


if __name__ == "__main__":
    main()
