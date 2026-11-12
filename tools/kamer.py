#!/usr/bin/env python3
"""kamer.py — zet een FLUX-plaatje om naar een kamer: 160x128 multicolor bitmap (§6.2).

    python3 tools/kamer.py data/kamers.txt build/gen

data/kamers.txt, één kamer per regel ('#' is commentaar):
    plein  data/flux/dawnhaven.png  boven=190  kleur=1.5  licht=1.0  sterkte=0.5

    boven    bovenste pixelrij van de strook in het bronplaatje (de strook is 5:2, over de hele breedte)
    kleur    verzadiging vooraf; licht: helderheid vooraf; sterkte: Floyd-Steinberg (0 = geen menging)

Per kamer:
    build/gen/kamer_<naam>.bin   ingepakt (tools/inpak.py): bitmap (16 rijen x 320) | scherm (640) | kleur (640)
    build/gen/kamer_<naam>.png   controle: de bronstrook naast de C64-pixels, zoals de VIC ze uit de bytes leest

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
        opties = {"boven": 0, "kleur": 1.5, "licht": 1.0, "sterkte": 0.5}
        for o in regel[2:]:
            k, _, v = o.partition("=")
            if k not in opties:
                raise SystemExit("%s:%d: onbekende optie %s" % (pad, nr, k))
            opties[k] = float(v)
        kamers.append((regel[0], regel[1], opties, nr))
    return kamers


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


def omzetten(klein, sterkte):
    L = cb.lab(klein)
    keuze, _ = cb.kies_vakjes(cb.afstanden(L), 4, 8, [ACHTER], 3)
    toegestaan = {}

    def kleuren_van(y, x):
        r, c = y // 8, x // 4
        if (r, c) not in toegestaan:
            toegestaan[(r, c)] = np.array([ACHTER] + list(keuze[r, c]))
        return toegestaan[(r, c)]
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
    return bytes(bitmap), bytes(scherm), bytes(kleur)


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
        if not os.path.exists(bron_pad):
            raise SystemExit("%s:%d: plaatje %s bestaat niet" % (lijst, nr, plaatje))
        # alleen opnieuw als de bron, de lijst of dit programma nieuwer is
        if os.path.exists(bin_pad) and all(os.path.getmtime(bin_pad) > os.path.getmtime(p)
                                           for p in (bron_pad, lijst, __file__, cb.__file__)):
            print("[kamer]   %s is bij" % naam)
            continue
        beeld = cb.voorbewerk(cb.laad(bron_pad), o["kleur"], o["licht"])
        bron, klein = strook(beeld, o["boven"])
        bitmap, scherm, kleur = omzetten(klein, o["sterkte"])
        pix = lees_terug(bitmap, scherm, kleur)
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
