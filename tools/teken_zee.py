#!/usr/bin/env python3
"""teken_zee.py — de Zee van Vergetelheid (hoofdstuk 3): gedeelde tekenstukken en de plaatjes van dat hoofdstuk.

    python3 tools/teken_zee.py      schrijft data/plaatjes/{veerman,steiger,boot,eiland,vuurtoren}.png (en patches)
                                     en build/proef/<naam>_groot.png

Allemaal met de hand getekend als C64-pixelart (160 x 128, per vakje van 4 x 8 hooguit 3 kleuren + zwart):
  veerman    tussenscène na hoofdstuk 2: Olm roeit zijn boot door de mist, een lantaarn aan de boeg
  steiger    het eind van de steiger, de boot van Olm ernaast (met OLM op de zijkant), Olm erin
  boot       in de boot op zee, in de mist; Olm roeit achterin (patch straal: de vuurtoren brandt)
  eiland     het vuurtoreneiland: de deur van de toren, een rots met meeuwen (patches: deur open, meeuwen op de honing)
  vuurtoren  de lampkamer bovenin: de dode lamp met een lege lenshouder, Kapitein Nul met zijn rug naar je toe
             (patches: Nul omgedraaid, de lamp aan)
Overal hangt de verduisterde zon: een zwarte schijf met een dunne stralenkrans en de twee manen ervoor.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import kleuren_per_vakje   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- gedeelde stukken ---------------------------------------------------------------------------------------------
def nachtlucht(dk, rnd, tot, sterren=True):
    """de schemerhemel: paars, naar de kim blauwer"""
    dk.rect(0, 1, B - 1, tot, PAARS)
    for y in range(tot // 2, tot + 1):
        for x in range(y % 2, B, 2):
            if rnd.random() < (y - tot / 2) / (tot / 2 + 4):
                dk.px(x, y, BLAUW)
    if sterren:
        for _ in range(8):
            x, y = rnd.randint(2, B - 3), rnd.randint(2, tot // 2)
            if dk.im.getpixel((x, y)) == PAARS:
                dk.px(x, y, WIT)


def verduisterde_zon(dk, cx, cy, r=7):
    """de zon met de twee manen ervoor: een zwarte schijf met een dunne gele stralenkrans"""
    dk.ovaal(cx - r - 2, cy - r, cx + r + 2, cy + r, GEEL, GEEL)
    dk.ovaal(cx - r, cy - r + 2, cx + r, cy + r - 2, ZWART, ZWART)
    dk.ovaal(cx - r - 1, cy - r + 3, cx + 1, cy + r - 3, DGRIJS, ZWART)
    dk.ovaal(cx - 1, cy - r + 3, cx + r + 1, cy + r - 3, DGRIJS, ZWART)


def zee(dk, rnd, kim, tot=125, licht_x=None):
    """de zee: donkerblauw, golfjes die dichterbij langer worden, en een weerschijn onder een licht"""
    dk.rect(0, kim, B - 1, tot, BLAUW)
    dk.lijn([(0, kim), (B - 1, kim)], DGRIJS)
    for y in range(kim + 2, tot + 1, 3):
        lengte = 2 + (y - kim) // 9
        for x in range(rnd.randint(0, 9), B, 11 + (y - kim) // 6):
            dk.lijn([(x, y), (x + lengte, y)], ZWART if rnd.random() < 0.5 else DGRIJS)
    if licht_x is not None:
        for y in range(kim + 2, tot, 2):
            b = 1 + (y - kim) // 16
            x = licht_x + rnd.randint(-2, 2)
            dk.lijn([(x - b, y), (x + b, y)], GEEL if y % 4 else ORANJE)


def mist(dk, rnd, y1, y2, dicht=0.35, kleuren=(LGRIJS, GRIJS)):
    """mistbanken: om en om pixels in grijs, dichter in het midden van de band"""
    midden = (y1 + y2) / 2
    for y in range(y1, y2):
        d = dicht * (1 - abs(y - midden) / ((y2 - y1) / 2 + 1))
        for x in range(y % 2, B, 2):
            if rnd.random() < d:
                dk.px(x, y, kleuren[0] if rnd.random() < 0.6 else kleuren[1])


def vuurtoren_ver(dk, x, kim, brandt=False):
    """ver weg op een rots: een vuurtoren, donker (of met licht en een straal)"""
    dk.poly([(x - 14, kim + 1), (x - 8, kim - 5), (x + 2, kim - 7), (x + 10, kim - 4), (x + 15, kim + 1)], DGRIJS, ZWART)
    dk.poly([(x - 2, kim - 6), (x - 1, kim - 24), (x + 2, kim - 24), (x + 3, kim - 6)], LGRIJS, ZWART)
    dk.lijn([(x - 1, kim - 13), (x + 2, kim - 13)], ROOD)
    dk.lijn([(x - 1, kim - 19), (x + 2, kim - 19)], ROOD)
    dk.rect(x - 2, kim - 28, x + 3, kim - 25, GEEL if brandt else DGRIJS)
    dk.poly([(x - 3, kim - 28), (x + 1, kim - 32), (x + 4, kim - 28)], ZWART)


def roeiboot(dk, x, y, lengte, hoogte, naam=False):
    """een roeiboot van opzij: bruine planken, een donkere rand; x, y = linksboven van de romp"""
    romp = [(x, y), (x + lengte, y), (x + lengte - hoogte, y + hoogte), (x + hoogte, y + hoogte)]
    dk.poly(romp, BRUIN, ZWART)
    for i in range(1, 3):                                        # planken
        yy = y + i * hoogte // 3
        dk.lijn([(x + i * hoogte // 3, yy), (x + lengte - i * hoogte // 3, yy)], DGRIJS)
    dk.lijn([(x + 1, y + 1), (x + lengte - 1, y + 1)], ORANJE)   # de rand vangt licht
    dk.lijn([(x, y), (x + lengte, y)], ZWART)
    if naam:                                                     # OLM, in blokletters op de zijkant
        lx, ly = x + lengte // 2 - 6, y + hoogte // 3 + 1
        letters = {"O": ["111", "101", "101", "101", "111"], "L": ["100", "100", "100", "100", "111"],
                   "M": ["101", "111", "111", "101", "101"]}
        for i, ch in enumerate("OLM"):
            for ry, rij in enumerate(letters[ch]):
                for rx, c in enumerate(rij):
                    if c == "1":
                        dk.px(lx + i * 4 + rx, ly + ry, WIT)


def olm(dk, x, y, groot=1.0, roeit=True):
    """Olm de veerman: een oude man met een lange grijze baard, een kap over zijn hoofd, een roeispaan.
    x, y = het midden van zijn heupen (op de bank van de boot)"""
    g = groot
    # de mantel: een wijde, versleten kap tot over de bank
    dk.poly([(x - 9 * g, y), (x - 7 * g, y - 14 * g), (x - 4 * g, y - 22 * g), (x + 4 * g, y - 22 * g),
             (x + 7 * g, y - 14 * g), (x + 9 * g, y)], DGRIJS, ZWART)
    dk.lijn([(x - 4 * g, y - 21 * g), (x - 7 * g, y - 13 * g)], GRIJS)   # licht op de plooien
    dk.lijn([(x + 1 * g, y - 12 * g), (x + 2 * g, y - 2 * g)], ZWART)
    # het gezicht onder de kap, en de baard tot op zijn buik
    dk.ovaal(x - 3 * g, y - 20 * g, x + 3 * g, y - 15 * g, ROZE, ZWART)
    dk.px(x - 1 * g, y - 18 * g, ZWART)
    dk.px(x + 1 * g, y - 18 * g, ZWART)
    dk.poly([(x - 3 * g, y - 16 * g), (x + 3 * g, y - 16 * g), (x + 2 * g, y - 7 * g), (x, y - 5 * g),
             (x - 2 * g, y - 7 * g)], LGRIJS, GRIJS)
    dk.poly([(x - 5 * g, y - 23 * g), (x, y - 27 * g), (x + 5 * g, y - 23 * g), (x + 4 * g, y - 20 * g),
             (x - 4 * g, y - 20 * g)], DGRIJS, ZWART)                     # de punt van de kap
    if roeit:                                                    # handen aan de roeispaan, schuin het water in
        dk.lijn([(x - 10 * g, y - 9 * g), (x + 18 * g, y + 10 * g)], BRUIN, 2)
        dk.ovaal(x - 7 * g, y - 11 * g, x - 3 * g, y - 7 * g, ROZE, ZWART)
        dk.ovaal(x - 1 * g, y - 8 * g, x + 3 * g, y - 4 * g, ROZE, ZWART)


def lantaarn_paal(dk, x, y, h, aan=True):
    """een paal met een scheepslantaarn eraan"""
    dk.lijn([(x, y), (x, y - h)], BRUIN, 2)
    dk.lijn([(x, y - h), (x + 4, y - h)], BRUIN)
    dk.rect(x + 3, y - h + 1, x + 6, y - h + 5, GEEL if aan else DGRIJS)
    dk.lijn([(x + 3, y - h + 1), (x + 6, y - h + 1)], ZWART)
    dk.lijn([(x + 3, y - h + 5), (x + 6, y - h + 5)], ZWART)


def rand(dk):
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)


# ---- de plaatjes --------------------------------------------------------------------------------------------------
def veerman():
    """tussenscène: de boot van Olm komt door de mist aanroeien; groot in beeld, een lantaarn aan de boeg"""
    rnd = random.Random(31)
    dk = Doek()
    nachtlucht(dk, rnd, 58)
    verduisterde_zon(dk, 124, 18)
    zee(dk, rnd, 58, licht_x=22)
    mist(dk, rnd, 44, 70, 0.45)
    vuurtoren_ver(dk, 140, 58)
    mist(dk, rnd, 52, 64, 0.3)
    # de boot, groot, schuin naar ons toe; de boeg links met de lantaarn
    roeiboot(dk, 24, 92, 96, 18, naam=True)
    dk.poly([(24, 92), (14, 84), (20, 92)], BRUIN, ZWART)        # de boeg steekt omhoog
    lantaarn_paal(dk, 18, 86, 22)
    olm(dk, 84, 92, 1.6)
    dk.lijn([(108, 108), (124, 118)], BRUIN, 2)                  # het blad van de roeispaan in het water
    dk.ovaal(120, 114, 132, 121, LBLAUW, None)                   # een rimpel
    mist(dk, rnd, 104, 126, 0.25)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


def steiger(met=None):
    """het eind van de steiger van dichtbij: planken over de hele breedte, de boot van Olm ernaast met OLM op de zijkant,
    Olm erin; de paal met de bel, en ver weg het donkere eiland met de vuurtoren"""
    rnd = random.Random(41)
    dk = Doek()
    nachtlucht(dk, rnd, 50)
    verduisterde_zon(dk, 104, 14)
    zee(dk, rnd, 50)
    vuurtoren_ver(dk, 44, 50)
    mist(dk, rnd, 40, 62, 0.35)
    # de boot: rechts naast de steiger, half achter de planken
    roeiboot(dk, 70, 80, 88, 16, naam=True)
    olm(dk, 128, 82, 1.4, roeit=False)
    dk.lijn([(118, 74), (150, 66)], BRUIN, 2)                    # de roeispanen rusten op de rand
    lantaarn_paal(dk, 154, 80, 26)
    # de steiger: dikke planken van links naar rechts, vooraan
    dk.poly([(0, 96), (110, 96), (118, 124), (0, 124)], BRUIN, ZWART)
    for y in range(100, 124, 5):
        dk.lijn([(0, y), (110 + (y - 96) * 8 // 28, y)], DGRIJS)
    for x in range(14, 110, 22):                                 # spijkers en naden
        dk.lijn([(x, 96), (x + 2, 124)], ZWART)
    dk.lijn([(0, 97), (110, 97)], ORANJE)
    for x, y in ((8, 124), (60, 124), (112, 124)):               # palen in het water
        dk.rect(x, y - 30, x + 3, y, DGRIJS)
        dk.lijn([(x, y - 30), (x, y)], ZWART)
    # de paal met de bel (dezelfde als op de oever)
    dk.rect(92, 52, 95, 96, BRUIN)
    dk.lijn([(91, 52), (91, 96)], ZWART)
    dk.lijn([(96, 52), (96, 96)], ZWART)
    dk.lijn([(92, 54), (102, 54)], BRUIN, 2)
    dk.poly([(97, 64), (98, 58), (102, 58), (103, 64)], GEEL, ZWART)
    dk.lijn([(100, 64), (98, 80)], LGRIJS)
    dk.lijn([(70, 84), (90, 92)], LGRIJS)                        # het touw van de boot aan de paal
    mist(dk, rnd, 110, 126, 0.15)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


STRAAL = (0, 16, 72, 40)        # patch boot_straal: de vuurtoren brandt en er schiet een straal door de mist


def boot(brandt=False):
    """in de boot op zee: je kijkt naar achteren, waar Olm roeit; de bodem van de boot is waar Eldric staat"""
    rnd = random.Random(51)
    dk = Doek()
    nachtlucht(dk, rnd, 52, sterren=False)
    verduisterde_zon(dk, 128, 14)
    zee(dk, rnd, 52)
    vuurtoren_ver(dk, 26, 52, brandt=brandt)
    if brandt:                                                   # een straal door de mist, schuin naar rechts
        for i in range(0, 40):
            y = 25 - i * 0.05
            dk.lijn([(30 + i, y - i * 0.08), (30 + i, y + 2 + i * 0.12)], GEEL if i % 3 else WIT)   # (x tot 69)
    mist(dk, rnd, 38, 62, 0.4)
    # de boot: de bodem als een trapezium, breed vooraan, smal achteraan bij Olm
    bodem = [(8, 125), (52, 88), (108, 88), (152, 125)]
    dk.poly(bodem, BRUIN, ZWART)
    for i in range(1, 6):                                        # de planken lopen naar achteren
        xa = 8 + (52 - 8) * i / 6
        dk.lijn([(80 + (xa - 80) * 0.2, 88), (xa + (80 - xa) * 0.0 - 0, 125)], DGRIJS)
    for i in range(1, 6):
        xb = 152 - (152 - 108) * i / 6
        dk.lijn([(80 + (xb - 80) * 0.2, 88), (xb, 125)], DGRIJS)
    for y in (100, 112):                                         # spanten dwars
        t = (y - 88) / 37
        dk.lijn([(52 - 44 * t, y), (108 + 44 * t, y)], DGRIJS)
    # de zijkanten: een dikke rand links en rechts, met licht op de bovenkant
    for (xa, ya, xb, yb) in ((0, 118, 48, 84), (160, 118, 112, 84)):
        dk.lijn([(xa, ya), (xb, yb)], BRUIN, 5)
        dk.lijn([(xa, ya - 3), (xb, yb - 3)], ORANJE)
        dk.lijn([(xa, ya + 3), (xb, yb + 3)], ZWART)
    # de achterbank en Olm erop, de riemen opzij het water in
    dk.rect(56, 84, 104, 88, BRUIN)
    dk.lijn([(56, 84), (104, 84)], ORANJE)
    dk.lijn([(56, 88), (104, 88)], ZWART)
    olm(dk, 80, 84, 1.7, roeit=False)
    for r in (-1, 1):
        dk.lijn([(80 + r * 8, 74), (80 + r * 56, 92)], BRUIN, 2)
        dk.ovaal(80 + r * 9 - 2, 72, 80 + r * 9 + 2, 76, ROZE, ZWART)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


DEUR = (52, 64, 20, 40)          # patch deur_open
ROTS = (96, 48, 44, 64)          # patch honing: de meeuwen op de honing, de sleutel gevallen
SLEUTEL = (128, 104, 12, 8)      # patch geen_sleutel (na honing): de sleutel is opgepakt


def meeuw(dk, x, y, kijk=1, pikt=False):
    """een meeuw: wit lijf, grijze vleugel, gele snavel"""
    dk.ovaal(x - 3, y - 2, x + 3, y + 2, WIT, ZWART)
    dk.lijn([(x - 2, y - 1), (x + 1, y - 1)], GRIJS)
    hy = y - 3 + (2 if pikt else 0)
    dk.ovaal(x + kijk * 2 - 1, hy - 1, x + kijk * 2 + 1, hy + 1, WIT, ZWART)
    dk.px(x + kijk * 4, hy + (1 if pikt else 0), GEEL)
    dk.px(x - 1, y + 3, GEEL)


def eiland(stand="dicht"):
    """het vuurtoreneiland: de voet van de toren met de deur, een rots met meeuwen die aan iets glimmends pikken,
    rotsen en de boot van Olm aan de kant (rechtsonder)"""
    rnd = random.Random(61)
    dk = Doek()
    nachtlucht(dk, rnd, 70)
    verduisterde_zon(dk, 128, 14)
    zee(dk, rnd, 70)
    mist(dk, rnd, 60, 80, 0.35)
    # de toren: wit met rode banden, loopt boven het beeld uit
    dk.poly([(44, 104), (48, 1), (76, 1), (80, 104)], LGRIJS, ZWART)
    for y in (14, 44):
        dk.poly([(47, y), (77, y), (77, y + 8), (47, y + 8)], ROOD, ZWART)
    dk.lijn([(72, 2), (76, 102)], GRIJS)                         # schaduwkant
    dk.rect(56, 24, 62, 32, DGRIJS)                              # een raampje
    dk.lijn([(59, 24), (59, 32)], ZWART)
    # de deur in een stenen boog
    dk.poly([(54, 104), (54, 76), (57, 70), (62, 68), (67, 70), (70, 76), (70, 104)], GRIJS, ZWART)
    if stand == "open":
        dk.poly([(56, 104), (56, 77), (58, 72), (62, 70), (66, 72), (68, 77), (68, 104)], ZWART, ZWART)
        dk.poly([(56, 104), (56, 77), (52, 79), (52, 106)], BRUIN, ZWART)   # de deur open, naar binnen gedraaid
        for y in range(80, 104, 6):
            dk.lijn([(60, y), (66, y)], DGRIJS)                  # een trap naar boven, in het donker
    else:
        dk.poly([(56, 104), (56, 77), (58, 72), (62, 70), (66, 72), (68, 77), (68, 104)], BRUIN, ZWART)
        for x in (59, 62, 65):
            dk.lijn([(x, 73), (x, 104)], DGRIJS)
        dk.rect(57, 80, 67, 81, ZWART)                           # ijzeren banden
        dk.rect(57, 96, 67, 97, ZWART)
        dk.rect(65, 88, 66, 90, GEEL)                            # het slot
    # de grond: rotsen en gras
    dk.poly([(0, 126), (0, 100), (30, 96), (44, 102), (82, 102), (98, 104), (106, 112), (110, 126)], DGRIJS, ZWART)
    for _ in range(30):
        x, y = rnd.randint(2, 96), rnd.randint(104, 123)
        dk.lijn([(x, y), (x + 3, y)], GRIJS)
        dk.lijn([(x, y + 1), (x + 3, y + 1)], ZWART)
    for x in range(4, 44, 5):                                    # pollen gras in de wind
        dk.lijn([(x, 100), (x + 2, 96)], GROEN)
    # de rots met de meeuwen
    dk.poly([(98, 104), (102, 80), (110, 64), (124, 58), (138, 60), (148, 72), (152, 104)], GRIJS, ZWART)
    dk.poly([(130, 60), (138, 61), (148, 73), (152, 104), (138, 104), (136, 80)], DGRIJS, DGRIJS)
    for x, y in ((112, 76), (126, 70), (140, 86)):
        dk.lijn([(x, y), (x + 6, y + 3)], ZWART)
    for x, y in ((106, 92), (118, 96), (144, 98)):               # witte vlekken: meeuwenpoep
        dk.px(x, y, WIT)
        dk.px(x + 1, y, WIT)
    if stand in ("dicht", "open"):
        dk.px(124, 58, GEEL)                                     # iets glimmends, bovenop de rots
        meeuw(dk, 118, 56, 1, pikt=True)
        meeuw(dk, 130, 55, -1, pikt=True)
        meeuw(dk, 124, 52, 1)
    else:                                                        # de honing op de flank, de meeuwen eromheen
        dk.ovaal(104, 84, 112, 90, GEEL, ORANJE)
        meeuw(dk, 100, 82, 1, pikt=True)
        meeuw(dk, 114, 80, -1, pikt=True)
        meeuw(dk, 108, 76, 1, pikt=True)
        if stand == "honing":
            dk.lijn([(132, 108), (137, 108)], GEEL)              # de sleutel, gevallen aan de voet van de rots
            dk.ovaal(129, 106, 132, 110, None, GEEL)
            dk.px(136, 109, GEEL)
    # de boot van Olm, aan de kant rechtsonder
    roeiboot(dk, 112, 112, 46, 10)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


NUL = (104, 40, 40, 72)          # patch nul_om: Kapitein Nul heeft zich omgedraaid
LAMP = (56, 24, 40, 48)          # patch lamp_aan: de zonnesteen in de lenshouder, de lamp brandt


def vuurtoren(nul_om=False, aan=False):
    """de lampkamer bovenin de vuurtoren: rondom ramen (de nacht en de zee), in het midden de dode lamp op een koperen
    voet met een lege lenshouder, rechts Kapitein Nul in een jas tot de grond, links het trapgat naar beneden"""
    rnd = random.Random(71)
    dk = Doek()
    # de ramen: drie grote ruiten met de nacht erin
    nachtlucht(dk, rnd, 60)
    zee(dk, rnd, 60, tot=84)
    verduisterde_zon(dk, 26, 16, 6)
    for x in (0, 52, 106, 159):                                  # de stijlen tussen de ruiten
        dk.rect(x - 3, 1, x + 3, 84, DGRIJS)
        dk.lijn([(x - 3, 1), (x - 3, 84)], ZWART)
        dk.lijn([(x + 3, 1), (x + 3, 84)], ZWART)
        dk.lijn([(x - 1, 1), (x - 1, 84)], GRIJS)
    dk.rect(0, 1, B - 1, 4, DGRIJS)
    dk.rect(0, 84, B - 1, 90, DGRIJS)                            # de vensterbank
    dk.lijn([(0, 84), (B - 1, 84)], ZWART)
    dk.lijn([(0, 85), (B - 1, 85)], GRIJS)
    # de vloer: ijzeren platen, het trapgat links
    dk.rect(0, 91, B - 1, 125, GRIJS)
    for y in range(96, 126, 7):
        dk.lijn([(0, y), (B - 1, y)], DGRIJS)
    for x in range(10, B, 24):
        dk.lijn([(x, 91), (x - 4, 125)], DGRIJS)
    dk.poly([(4, 108), (30, 108), (34, 124), (0, 124)], ZWART, ZWART)   # het trapgat
    dk.lijn([(4, 108), (30, 108)], LGRIJS)
    for y in (112, 117, 122):
        dk.lijn([(8, y), (28, y)], DGRIJS)                       # treden in het donker
    # de lamp: koperen voet, een ring (de lenshouder), glazen kap
    dk.poly([(66, 110), (70, 72), (82, 72), (86, 110)], ORANJE, ZWART)
    dk.lijn([(72, 74), (70, 108)], GEEL)
    dk.rect(62, 108, 90, 112, BRUIN)
    dk.lijn([(62, 112), (90, 112)], ZWART)
    dk.ovaal(62, 34, 90, 66, LBLAUW if not aan else GEEL, ZWART)   # de glazen kap
    dk.ovaal(66, 38, 86, 62, DGRIJS if not aan else WIT, ZWART)
    dk.ovaal(70, 44, 82, 56, ORANJE, ZWART)                      # de lenshouder: een koperen ring
    if aan:
        dk.ovaal(73, 47, 79, 53, GEEL, ORANJE)                   # oma's steentje in de ring
        dk.px(75, 49, WIT)
        for a in range(0, 360, 30):                              # stralen tot op de ruiten
            r = math.radians(a)
            dk.lijn([(76 + 16 * math.cos(r), 50 + 16 * math.sin(r)), (76 + 19 * math.cos(r), 50 + 21 * math.sin(r))],
                    GEEL)
    else:
        dk.ovaal(73, 47, 79, 53, ZWART, ZWART)                   # leeg
    dk.poly([(66, 34), (76, 26), (86, 34)], ORANJE, ZWART)       # het dakje van de kap
    # Kapitein Nul
    nx = 124
    dk.poly([(nx - 10, 112), (nx - 8, 66), (nx - 5, 58), (nx + 5, 58), (nx + 8, 66), (nx + 11, 112)], BLAUW, ZWART)
    dk.lijn([(nx - 7, 68), (nx - 9, 110)], LBLAUW)               # licht op de jas
    dk.poly([(nx - 9, 58), (nx - 6, 48), (nx + 6, 48), (nx + 9, 58)], BLAUW, ZWART)   # de kraag, hoog opgezet
    dk.poly([(nx - 8, 48), (nx - 6, 41), (nx + 6, 41), (nx + 8, 48)], ZWART, ZWART)   # de pet
    dk.lijn([(nx - 9, 48), (nx + 9, 48)], DGRIJS)                # de klep
    dk.rect(nx - 2, 43, nx + 2, 45, GEEL)                        # het embleem
    if nul_om:                                                   # omgedraaid: een aardmannetje onder de pet
        dk.ovaal(nx - 6, 46, nx + 6, 58, BRUIN, ZWART)
        dk.rect(nx - 3, 51, nx - 2, 52, GEEL)                    # gloeiende oogjes
        dk.rect(nx + 2, 51, nx + 3, 52, GEEL)
        dk.lijn([(nx - 2, 55), (nx + 2, 55)], ZWART)
        dk.poly([(nx - 6, 50), (nx - 12, 46), (nx - 6, 53)], BRUIN, ZWART)   # puntoren
        dk.poly([(nx + 6, 50), (nx + 12, 46), (nx + 6, 53)], BRUIN, ZWART)
        for y in (70, 80, 90, 100):                              # knopen op de voorkant van de jas
            dk.px(nx, y, GEEL)
        dk.lijn([(nx, 60), (nx, 110)], ZWART)
    else:
        dk.ovaal(nx - 6, 48, nx + 6, 57, BLAUW, ZWART)           # de rug: alleen kraag en pet
        dk.lijn([(nx, 62), (nx, 110)], ZWART)                    # de naad in de rug
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


PLAATJES = {"veerman": veerman, "steiger": steiger, "boot": boot, "boot_straal": lambda: boot(True),
            "eiland": eiland, "eiland_deur_open": lambda: eiland("open"), "eiland_honing": lambda: eiland("honing"),
            "eiland_honing_leeg": lambda: eiland("honing_leeg"),
            "vuurtoren": vuurtoren, "vuurtoren_nul_om": lambda: vuurtoren(nul_om=True),
            "vuurtoren_lamp_aan": lambda: vuurtoren(aan=True)}
# patches: naam -> (basisplaatje, vak); main controleert dat een patch buiten zijn vak niets verandert
PATCHES = {"boot_straal": ("boot", STRAAL), "eiland_deur_open": ("eiland", DEUR), "eiland_honing": ("eiland", ROTS),
           "eiland_honing_leeg": ("eiland_honing", SLEUTEL), "vuurtoren_nul_om": ("vuurtoren", NUL),
           "vuurtoren_lamp_aan": ("vuurtoren", LAMP)}


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    namen = sys.argv[1:] or list(PLAATJES)
    gemaakt = {}
    for naam in namen:
        im = gemaakt[naam] = PLAATJES[naam]()
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[zee] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))
        if naam in PATCHES:
            basis_naam, (px, py, pb, ph) = PATCHES[naam]
            basis = gemaakt.get(basis_naam) or PLAATJES[basis_naam]()
            buiten = sum(1 for y in range(H) for x in range(B) if basis.getpixel((x, y)) != im.getpixel((x, y))
                         and not (px <= x < px + pb and py <= y < py + ph))
            if buiten or px % 4 or pb % 4 or py % 8 or ph % 8:
                raise SystemExit("[zee] patch %s: %d pixels buiten het vak %s (of een vak niet op vakjes)"
                                 % (naam, buiten, (px, py, pb, ph)))


if __name__ == "__main__":
    main()
