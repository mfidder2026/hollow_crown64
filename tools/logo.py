#!/usr/bin/env python3
"""logo.py — HOLLOW CROWN in een eigen logo-lettertype, voor het intro (§9).

    python3 tools/logo.py build/gen
        schrijft build/gen/logo.asm (de tegels als tekens, en de kaart: welke tegel waar) en build/gen/logo.png.

De letters zijn 10 x 12 blokjes van 2 x 2 pixels (20 x 24 pixels: 3 tekenrijen hoog). Door elke letter loopt een
dunne zwarte snede (pixelrij SNEDE): het oude "chroom"-effect van C64-logo's. Het logo wordt in tegels van 8 x 8
geknipt; gelijke tegels worden één teken. De tekens komen op $80 en verder in het lettertype ($F800): die codes
gebruikt het spel niet (lettertype.py vult alleen de codes onder $80). De kleurenloop zit in het kleur-RAM.
"""
import os, sys

LETTERS = {
    "H": ["###....###", "###....###", "###....###", "###....###", "###....###", "##########",
          "##########", "###....###", "###....###", "###....###", "###....###", "###....###"],
    "O": [".########.", "##########", "###....###", "###....###", "###....###", "###....###",
          "###....###", "###....###", "###....###", "###....###", "##########", ".########."],
    "L": ["###.......", "###.......", "###.......", "###.......", "###.......", "###.......",
          "###.......", "###.......", "###.......", "###.......", "##########", "##########"],
    "W": ["###....###", "###....###", "###....###", "###....###", "###.##.###", "###.##.###",
          "###.##.###", "##########", "##########", "####..####", "###....###", "##......##"],
    "C": [".#########", "##########", "###.......", "###.......", "###.......", "###.......",
          "###.......", "###.......", "###.......", "###.......", "##########", ".#########"],
    "R": ["#########.", "##########", "###....###", "###....###", "###....###", "##########",
          "#########.", "###.###...", "###..###..", "###...###.", "###....###", "###....###"],
    "N": ["####...###", "####...###", "#####..###", "#####..###", "######.###", "###.######",
          "###.######", "###..#####", "###..#####", "###...####", "###...####", "###....###"],
}
TEKST = "HOLLOW CROWN"
BREED, HOOG = 20, 24          # pixels per letter
TUSSEN = 4                    # pixels tussen de letters
SPATIE = 12
SNEDE = 13                    # deze pixelrij blijft zwart
EERSTE = 0x80                 # het eerste tekennummer


def beeld():
    w = sum(SPATIE if c == " " else BREED + TUSSEN for c in TEKST) - TUSSEN
    kolommen = (w + 7) // 8
    links = (kolommen * 8 - w) // 2
    pix = [[0] * (kolommen * 8) for _ in range(HOOG)]
    x = links
    for c in TEKST:
        if c == " ":
            x += SPATIE
            continue
        for r, regel in enumerate(LETTERS[c]):
            for k, ch in enumerate(regel):
                if ch == "#":
                    for dy in (0, 1):
                        for dx in (0, 1):
                            if 2 * r + dy != SNEDE:
                                pix[2 * r + dy][x + 2 * k + dx] = 1
        x += BREED + TUSSEN
    return pix, kolommen


def tegels(pix, kolommen):
    lijst, kaart = [bytes(8)], []                  # tegel 0 = leeg (wordt een spatie)
    for rij in range(HOOG // 8):
        k = []
        for kol in range(kolommen):
            t = bytes(sum(pix[rij * 8 + y][kol * 8 + x] << (7 - x) for x in range(8)) for y in range(8))
            if t not in lijst:
                lijst.append(t)
            k.append(lijst.index(t))
        kaart.append(k)
    return lijst, kaart


def main():
    uit = sys.argv[1]
    pix, kolommen = beeld()
    lijst, kaart = tegels(pix, kolommen)
    assert len(lijst) - 1 <= 0x100 - EERSTE, "te veel tegels: %d" % len(lijst)
    assert kolommen <= 40
    links = (40 - kolommen) // 2
    L = ["// gemaakt door tools/logo.py — niet met de hand wijzigen",
         ".const LOGO_EERSTE = $%02x" % EERSTE,
         ".const LOGO_TEGELS = %d" % (len(lijst) - 1),
         ".const LOGO_RIJEN = %d" % len(kaart),
         ".segment Data",
         "logo_tegels:    // de tekens $%02x..: 8 bytes per teken" % EERSTE]
    for t in lijst[1:]:
        L.append("        .byte " + ", ".join("$%02x" % b for b in t))
    L.append("logo_kaart:     // %d rijen van 40 schermcodes (32 = spatie)" % len(kaart))
    for k in kaart:
        rij = [32] * 40
        for i, t in enumerate(k):
            rij[links + i] = 32 if t == 0 else EERSTE + t - 1
        L.append("        .byte " + ", ".join(str(v) for v in rij))
    open(os.path.join(uit, "logo.asm"), "w").write("\n".join(L) + "\n")
    try:
        from PIL import Image
        img = Image.new("RGB", (len(pix[0]) * 3, HOOG * 3))
        for y, r in enumerate(pix):
            for x, v in enumerate(r):
                if v:
                    for d in range(9):
                        img.putpixel((x * 3 + d % 3, y * 3 + d // 3), (230, 200, 90))
        img.save(os.path.join(uit, "logo.png"))
    except ImportError:
        pass
    print("[logo] %s: %d kolommen, %d tegels" % (TEKST, kolommen, len(lijst) - 1))


if __name__ == "__main__":
    main()
