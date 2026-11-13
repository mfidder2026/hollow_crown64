#!/usr/bin/env python3
"""teken_smit.py — de smit van Bram, met de hand getekend als C64-pixelart (zoals het toneel, tools/teken_toneel.py).

    python3 tools/teken_smit.py      schrijft data/plaatjes/smit.png en smit_vuur.png (640 x 256) en build/proef/smit_*.png

Kamerpixels (160 x 128), alleen C64-kleuren, dikke zwarte lijnen: dezelfde sfeer als het plein. Bram zelf staat niet in
het plaatje: hij is een figuur (sprite, tools/sprites_hc.py 'bram'), zodat hij er als een mens uitziet.

Het smidsvuur: in de koude haard liggen kolen met een paar gloeiende puntjes (rood). FLAKKER in scripts/smit.hcs laat
rood/oranje/geel in die vakjes rondgaan: de kolen gloeien zacht na, ook als het vuur uit is. smit_vuur.png is dezelfde
kamer met het vuur aan (de patch vuur_aan: vlammen in rood, oranje en geel, die dan flakkeren).
De vakjes van het vuur (FLAKKER en patch): x 64-95, y 56-71.
"""
import os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN, BLAUW, GEEL,   # noqa: E402
                          ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def balken(dk):
    dk.rect(0, 1, B - 1, 9, BRUIN)
    dk.lijn([(0, 9), (B - 1, 9)], ZWART)
    for x in range(6, B, 24):
        dk.rect(x, 1, x + 3, 9, ORANJE)
        dk.lijn([(x - 1, 1), (x - 1, 9)], ZWART)


def muur(dk, rnd):
    dk.rect(0, 10, B - 1, 81, GRIJS)
    for i, y in enumerate(range(10, 82, 6)):                    # stenen in verband
        dk.lijn([(0, y), (B - 1, y)], DGRIJS)
        for x in range(i % 2 * 6, B, 12):
            dk.lijn([(x, y), (x, y + 5)], DGRIJS)
    for _ in range(60):                                          # wat lichtere stenen
        x, y = rnd.randrange(0, B - 10, 12) + 1, rnd.randrange(10, 76, 6) + 1
        dk.rect(x, y, x + 9, y + 4, LGRIJS)
    dk.lijn([(0, 81), (B - 1, 81)], ZWART)


def smidsvuur(dk, rnd, aan):
    # de schoorsteen en de kap
    dk.rect(72, 10, 88, 24, DGRIJS)
    dk.lijn([(72, 10), (72, 24)], ZWART)
    dk.lijn([(88, 10), (88, 24)], ZWART)
    dk.poly([(66, 24), (94, 24), (106, 54), (54, 54)], DGRIJS)
    for y in range(30, 54, 6):
        dk.lijn([(60 + (54 - y) // 3, y), (100 - (54 - y) // 3, y)], GRIJS)
    dk.rect(52, 54, 108, 57, LGRIJS)                             # de rand van de kap
    dk.lijn([(52, 54), (108, 54)], ZWART)
    dk.lijn([(52, 57), (108, 57)], ZWART)
    # de stenen voet met de haard
    dk.rect(56, 58, 104, 81, DGRIJS)
    for y in (64, 70, 76):
        dk.lijn([(56, y), (104, y)], ZWART)
    for x in (62, 74, 86, 98):
        dk.lijn([(x, 58), (x, 81)], ZWART)
    dk.rect(56, 58, 104, 63, GRIJS)                              # de bovenrand van de voet
    dk.lijn([(56, 58), (104, 58)], ZWART)
    dk.rect(64, 60, 95, 71, ZWART)                               # de haard: hier liggen de kolen
    if aan:
        # vlammentongen: rood buiten, oranje, een gele kern; ze reiken tot in de kap (rij 56)
        for x0, top in ((66, 62), (71, 58), (76, 56), (81, 57), (86, 56), (90, 59), (93, 62)):
            dk.poly([(x0 - 3, 71), (x0, top), (x0 + 3, 71)], ROOD, ROOD)
            dk.poly([(x0 - 2, 71), (x0, top + 4), (x0 + 2, 71)], ORANJE, ORANJE)
            dk.poly([(x0 - 1, 71), (x0, top + 8), (x0 + 1, 71)], GEEL, GEEL)
        for x in range(65, 95, 3):
            dk.ovaal(x, 68, x + 3, 71, ROOD, ZWART)
    else:
        for x in range(65, 95, 3):                               # de kolen: zwart met een paar gloeiende puntjes
            dk.ovaal(x, 66, x + 3, 70, DGRIJS, ZWART)
        for _ in range(14):
            dk.px(rnd.randint(66, 93), rnd.randint(66, 70), ROOD)
        for _ in range(4):
            dk.px(rnd.randint(68, 91), rnd.randint(67, 70), ORANJE)


def palen_en_wapens(dk):
    for x in (44, 128):                                          # houten palen tegen de muur
        dk.rect(x, 10, x + 3, 81, BRUIN)
        dk.lijn([(x, 10), (x, 81)], ZWART)
        dk.lijn([(x + 3, 10), (x + 3, 81)], ZWART)
        dk.lijn([(x + 1, 10), (x + 1, 81)], ORANJE)
    # een schild en twee gekruiste zwaarden boven de deur: Brams werk
    dk.lijn([(134, 14), (152, 34)], LGRIJS, 2)
    dk.lijn([(152, 14), (134, 34)], LGRIJS, 2)
    dk.ovaal(137, 16, 149, 32, ROOD)
    dk.lijn([(143, 17), (143, 31)], GEEL)
    dk.lijn([(138, 24), (148, 24)], GEEL)


def blaasbalg(dk):
    dk.poly([(40, 72), (52, 66), (54, 80), (42, 80)], BRUIN)
    dk.lijn([(44, 70), (46, 80)], ORANJE)
    dk.lijn([(52, 66), (56, 64)], ZWART)                         # het mondstuk naar het vuur
    dk.rect(38, 74, 41, 76, ORANJE)                              # het handvat


def gereedschap(dk):
    dk.rect(8, 22, 40, 24, BRUIN)                                # de plank met haken
    dk.lijn([(8, 25), (40, 25)], ZWART)
    for x, soort in ((11, "tang"), (18, "hamer"), (26, "tang"), (33, "hamer"), (39, "tang")):
        if soort == "hamer":
            dk.lijn([(x, 26), (x, 42)], BRUIN, 2)
            dk.rect(x - 3, 26, x + 3, 30, DGRIJS)
            dk.lijn([(x - 3, 26), (x + 3, 26)], ZWART)
            dk.lijn([(x - 3, 30), (x + 3, 30)], ZWART)
        else:
            dk.lijn([(x - 1, 26), (x - 2, 44)], ZWART, 2)
            dk.lijn([(x + 1, 26), (x + 2, 44)], ZWART, 2)
            dk.px(x, 27, LGRIJS)
    for x in (12, 22, 32):                                       # hoefijzers
        dk.ovaal(x - 3, 46, x + 3, 52, ZWART, ZWART)
        dk.ovaal(x - 2, 47, x + 2, 51, GRIJS, GRIJS)
        dk.rect(x - 1, 50, x + 1, 52, ZWART)


def raam_en_deur(dk):
    dk.rect(112, 20, 126, 38, ZWART)
    dk.rect(113, 21, 125, 37, PAARS)
    dk.lijn([(119, 21), (119, 37)], ZWART)
    dk.lijn([(113, 29), (125, 29)], ZWART)
    dk.px(115, 23, ROZE)                                         # een ster in de schemer
    dk.rect(133, 39, 153, 81, ZWART)                             # de deur naar het plein
    dk.rect(134, 40, 152, 81, BRUIN)
    for x in (139, 144, 149):
        dk.lijn([(x, 40), (x, 81)], ORANJE)
    for y in (46, 72):
        dk.rect(134, y, 145, y + 1, DGRIJS)                      # scharnieren
    dk.rect(149, 60, 150, 62, GEEL)                              # de klink


def vloer(dk, rnd):
    dk.rect(0, 82, B - 1, 125, BRUIN)
    dk.ovaal(40, 80, 120, 100, ORANJE, ORANJE)                  # warm licht van het smidsvuur op de vloer
    for _ in range(260):
        x, y = rnd.randint(0, B - 1), rnd.randint(82, 125)
        dk.px(x, y, ORANJE if dk.im.getpixel((x, y)) == BRUIN else BRUIN)
    for _ in range(14):                                          # stenen in de aarde
        x, y = rnd.randint(4, 154), rnd.randint(98, 122)
        dk.ovaal(x, y, x + 4, y + 2, GRIJS, DGRIJS)            # (geen zwarte rand: je loopt eroverheen)
    for i in range(10):                                          # stro bij het watervat
        dk.lijn([(22 + i, 118 - i % 3), (26 + i, 114 + i % 4)], GEEL)
    dk.ovaal(96, 114, 104, 120, DGRIJS, DGRIJS)                  # een hoefijzer op de vloer
    dk.ovaal(97, 115, 103, 119, GRIJS, GRIJS)
    dk.rect(98, 118, 102, 120, BRUIN)


def aambeeld_en_vat(dk):
    dk.rect(110, 94, 124, 108, BRUIN)                            # de boomstronk
    dk.lijn([(110, 94), (110, 108)], ZWART)
    dk.lijn([(124, 94), (124, 108)], ZWART)
    dk.lijn([(110, 108), (124, 108)], ZWART)
    dk.ovaal(110, 92, 124, 96, ORANJE)
    dk.poly([(102, 86), (108, 84), (128, 84), (128, 88), (122, 88), (120, 93), (114, 93), (112, 88), (106, 88)], DGRIJS)
    dk.lijn([(108, 84), (128, 84)], LGRIJS)
    # het watervat vooraan links
    dk.rect(4, 88, 20, 108, BRUIN)
    dk.lijn([(4, 88), (4, 108)], ZWART)
    dk.lijn([(20, 88), (20, 108)], ZWART)
    dk.lijn([(4, 108), (20, 108)], ZWART)
    for y in (92, 100):
        dk.lijn([(4, y), (20, y)], DGRIJS)
    dk.ovaal(4, 86, 20, 90, BLAUW)


def teken(aan=False):
    rnd = random.Random(9)
    dk = Doek()
    balken(dk)
    muur(dk, rnd)
    palen_en_wapens(dk)
    gereedschap(dk)
    raam_en_deur(dk)
    smidsvuur(dk, random.Random(3), aan)
    blaasbalg(dk)
    vloer(dk, rnd)
    aambeeld_en_vat(dk)
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    return dk.im


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    for naam, aan in (("smit", False), ("smit_vuur", True)):
        im = teken(aan)
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[smit] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))


if __name__ == "__main__":
    main()
