#!/usr/bin/env python3
"""teken_oever.py — de oever aan het eind van het Duisterwoud (hoofdstuk 2), met de hand getekend als C64-pixelart.

    python3 tools/teken_oever.py   schrijft data/plaatjes/oever.png en oever_boot.png (de patch: er komt een boot)

Scenario: een steiger, een bel, geen boot. In de verte de zee en een eiland met een vuurtoren die donker is (Grom
houdt hem donker). Gebruik bel: in de verte komt een boot met een lampje (patch boot). Links het bos (terug naar de
jachthut). Buiten, dus Eldric wordt kleiner naar achteren (SCHAAL), net als op de bosrand.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import stam, kleuren_per_vakje   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIM = 60                          # de horizon
BOOT = (20, 48, 28, 16)           # patch boot: x, y, breedte, hoogte (op vakjes van 4 x 8)


def lucht(dk, rnd):
    dk.rect(0, 1, B - 1, KIM, PAARS)
    for y in range(30, KIM):                                     # naar de kim toe: blauwer
        for x in range(y % 2, B, 2):
            if rnd.random() < (y - 30) / 32:
                dk.px(x, y, BLAUW)
    dk.ovaal(49, 12, 63, 26, LGRIJS, LGRIJS)                     # de maan (vol)
    dk.px(54, 17, GRIJS)
    dk.px(58, 21, GRIJS)
    dk.px(55, 22, GRIJS)
    for x1, y, x2 in ((40, 28, 76), (90, 14, 140), (100, 26, 156)):
        dk.lijn([(x1, y), (x2, y)], GRIJS)
        dk.lijn([(x1 + 5, y + 1), (x2 - 6, y + 1)], DGRIJS)
    for x, y in ((70, 8), (120, 6), (150, 20), (8, 30), (84, 32)):
        dk.px(x, y, WIT)                                         # sterren


def zee(dk, rnd):
    dk.rect(0, KIM, B - 1, 125, BLAUW)
    dk.lijn([(0, KIM), (B - 1, KIM)], DGRIJS)
    for y in range(KIM + 2, 126, 3):                             # golfjes: dichterbij langer
        lengte = 2 + (y - KIM) // 10
        for x in range(rnd.randint(0, 9), B, 12 + (y - KIM) // 6):
            dk.lijn([(x, y), (x + lengte, y)], DGRIJS if rnd.random() < 0.5 else ZWART)
    for y in range(KIM + 2, 120, 2):                             # de weerspiegeling van de maan
        b = 1 + (y - KIM) // 14
        x = 56 + rnd.randint(-2, 2)
        dk.lijn([(x - b, y), (x + b, y)], LGRIJS if y % 4 else LBLAUW)


def eiland(dk):
    """ver weg, rechts: een rots in zee met een vuurtoren zonder licht"""
    dk.poly([(116, KIM + 1), (122, 54), (130, 52), (138, 48), (146, 50), (152, 55), (158, KIM + 1)], DGRIJS, ZWART)
    dk.poly([(140, 49), (141, 30), (145, 30), (146, 49)], LGRIJS, ZWART)   # de toren
    for y in (36, 42):
        dk.lijn([(141, y), (145, y)], ROOD)                      # rode banden
    dk.rect(140, 25, 146, 29, DGRIJS)                            # de lantaarnkamer, donker
    dk.lijn([(140, 25), (146, 25)], ZWART)
    dk.lijn([(140, 29), (146, 29)], ZWART)
    dk.poly([(139, 25), (143, 21), (147, 25)], ZWART)            # het dakje


def oever(dk, rnd):
    """links de oever: stenen, zand, riet, en het bos waar je vandaan komt"""
    rand = [(0, 56), (14, 58), (26, 66), (40, 80), (52, 94), (60, 108), (66, 126), (0, 126)]
    dk.poly(rand, BRUIN, ZWART)
    dither(dk, (0, 70, 66, 126), ORANJE, 0.35, rnd, BRUIN)       # zand
    for x, y in ((8, 100), (20, 112), (34, 96), (44, 118), (12, 84), (50, 108)):
        dk.ovaal(x, y, x + 6, y + 4, GRIJS)
        dk.lijn([(x + 1, y + 1), (x + 3, y + 1)], LGRIJS)
    for x in (44, 50, 56, 61):                                   # riet in het water
        h = rnd.randint(8, 14)
        y = 90 + (x - 44) * 2
        dk.lijn([(x, y), (x + 1, y - h)], GROEN)
        dk.rect(x + 1, y - h, x + 2, y - h + 3, BRUIN)
    stam(dk, 8, 6, 2, 64, rnd)                                   # de laatste bomen van het bos
    for x, r in ((-4, 16), (14, 12), (26, 9)):
        dk.ovaal(x - r, -6, x + r, 10 + r, ZWART, ZWART)
    for _ in range(40):                                          # donker blad met hier en daar wat groen
        x, y = rnd.randint(0, 36), rnd.randint(1, 22)
        if dk.im.getpixel((x, y)) == ZWART:
            dk.ovaal(x - 2, y - 1, x + 2, y + 1, GROEN, ZWART)


def steiger(dk):
    """de steiger loopt vanaf de oever schuin de zee in; aan het eind een paal met een bel"""
    # het plankier: een parallellogram dat naar achteren smaller wordt
    voor_l, voor_r = (54, 124), (92, 124)
    achter_l, achter_r = (96, 76), (110, 76)
    dk.poly([voor_l, achter_l, achter_r, voor_r], BRUIN, ZWART)
    for i in range(1, 16):                                       # planknaden
        t = (i / 16) ** 1.4
        y = 124 - (124 - 76) * t
        xl = voor_l[0] + (achter_l[0] - voor_l[0]) * t
        xr = voor_r[0] + (achter_r[0] - voor_r[0]) * t
        dk.lijn([(xl, y), (xr, y)], DGRIJS)
    dk.lijn([(voor_l[0] + 4, 124), (achter_l[0] + 1, 76)], ORANJE)   # licht op de linkerrand
    for t in (0.05, 0.35, 0.62, 0.85):                           # palen in het water
        x = voor_r[0] + (achter_r[0] - voor_r[0]) * t
        y = 124 - (124 - 76) * t
        h = 10 - 7 * t
        dk.rect(x - 1, y, x + 1, y + h, DGRIJS)
        dk.lijn([(x - 2, y + h), (x + 2, y + h)], LBLAUW)        # een kringetje water
    # de belpaal aan het eind
    dk.rect(106, 48, 108, 77, BRUIN)
    dk.lijn([(105, 48), (105, 77)], ZWART)
    dk.lijn([(109, 48), (109, 77)], ZWART)
    dk.lijn([(106, 50), (116, 50)], BRUIN, 2)                    # de arm
    dk.lijn([(106, 52), (110, 50)], ZWART)
    dk.lijn([(114, 51), (114, 53)], GRIJS)                       # touwtje
    dk.poly([(111, 59), (112, 54), (116, 54), (117, 59)], GEEL, ZWART)   # de bel
    dk.px(114, 60, ORANJE)
    dk.lijn([(114, 60), (112, 72)], LGRIJS)                      # het trektouw


def boot(dk):
    """de patch: in de verte een bootje met een lampje"""
    dk.poly([(24, 59), (26, 62), (38, 62), (40, 59)], BRUIN, ZWART)
    dk.lijn([(32, 59), (32, 50)], ZWART)                          # de mast
    dk.poly([(33, 51), (33, 58), (38, 58)], LGRIJS)               # het zeil
    dk.rect(26, 56, 27, 58, GEEL)                                 # het lampje
    dk.px(25, 55, ORANJE)
    dk.px(28, 55, ORANJE)
    for x in range(22, 44, 3):                                    # schijnsel op het water
        dk.px(x, 62 + (x % 2), GEEL if 24 < x < 30 else LBLAUW)


def teken(met_boot=False):
    rnd = random.Random(42)
    dk = Doek()
    lucht(dk, rnd)
    zee(dk, rnd)
    eiland(dk)
    if met_boot:
        boot(dk)
    oever(dk, rnd)
    steiger(dk)
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    kleuren_per_vakje(dk.im)
    return dk.im


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    for naam, b in (("oever", False), ("oever_boot", True)):
        im = teken(b)
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[oever] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))


if __name__ == "__main__":
    main()
