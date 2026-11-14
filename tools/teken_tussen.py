#!/usr/bin/env python3
"""teken_tussen.py — de loopschermen tussen de kamers (de reis: lopen door het bos, varen, door de grotten, de bergen
en het kasteel), met de hand getekend als C64-pixelart.

    python3 tools/teken_tussen.py [naam ...]   schrijft data/plaatjes/<naam>.png en build/proef/<naam>_groot.png

Twee vaste vormen, zodat de scripts en de testbanden voor elk loopscherm hetzelfde zijn:
  diep   een pad van vooraan (onder, x 60-100) naar achteren (x 80, y ~84): je komt onderaan binnen en loopt de
         diepte in, of andersom.  Uitgangen: VAK 60,118 40,8 (terug, onder) en 72,68 16,18 (verder, achter).
  zij    een pad van links naar rechts (y ~104-122).  Uitgangen: VAK 0,100 6,24 (links) en 154,100 6,24 (rechts).
Per scherm één lichtbron, textuur, randlicht (tools/rijk.py) en wat te bekijken.

  dorpsweg   hoofdstuk 1: van het plein naar de bosrand (diep). Akkers in de schemer, een vogelverschrikker, de
             molen, een hek; achteraan wacht het donkere bos.
  beekdal    hoofdstuk 2: van de achterdeur van de jachthut naar de oever (zij). Een beek met een bruggetje van
             een boomstam, varens, een reiger, in de verte het meer.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import bladerdak, stam, kleuren_per_vakje, mist   # noqa: E402
from teken_zee import verduisterde_zon, zee, roeiboot, vuurtoren_ver, meeuw   # noqa: E402
from teken_kloof import rotswand, zwam   # noqa: E402
from teken_ijs import berg, sneeuw, den   # noqa: E402
import rijk   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def afmaken(dk):
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    kleuren_per_vakje(dk.im)
    return dk.im


def pad_diep(dk, rnd, basis=BRUIN, midden=ORANJE, steen=BRUIN, rand=ZWART, achter_x=80, achter_y=84, krom=10):
    """het pad van vooraan (onder) naar achteren: breed vooraan, smal achteraan, met een bocht"""
    links, rechts = [], []
    for i in range(11):
        t = i / 10                                               # 0 = vooraan (y 127), 1 = achteraan
        y = 127 - (127 - achter_y) * t
        mx = 80 + (achter_x - 80) * t + krom * math.sin(t * math.pi)
        half = 22 * (1 - t) + 3 * t
        links.append((mx - half, y))
        rechts.append((mx + half, y))
    dk.poly(links + rechts[::-1], basis, rand)
    mid = [((a[0] * 2 + b[0]) / 3, a[1]) for a, b in zip(links, rechts)]
    mid2 = [((a[0] + b[0] * 2) / 3, a[1]) for a, b in zip(links, rechts)]
    dk.poly(mid + mid2[::-1], midden, midden)
    for _ in range(60):
        x, y = rnd.randint(40, 120), rnd.randint(achter_y, 126)
        if dk.im.getpixel((x, y)) == midden:
            dk.px(x, y, steen)
    for t in (0.15, 0.4):                                        # karrensporen
        for a, b in zip(links, rechts):
            pass
    return links, rechts


def pad_zij(dk, rnd, basis=BRUIN, midden=ORANJE, steen=BRUIN, y1=104, y2=122):
    """een pad van links naar rechts, licht golvend"""
    boven = [(x, y1 + 2 * math.sin(x * 0.05)) for x in range(0, B, 8)] + [(B - 1, y1)]
    onder = [(x, y2 + 2 * math.sin(x * 0.07 + 1)) for x in range(0, B, 8)] + [(B - 1, y2)]
    dk.poly(boven + onder[::-1], basis, ZWART)
    m1 = [(x, y + 4) for x, y in boven]
    m2 = [(x, y - 4) for x, y in onder]
    dk.poly(m1 + m2[::-1], midden, midden)
    for _ in range(70):
        x, y = rnd.randint(0, B - 1), rnd.randint(y1, y2)
        if dk.im.getpixel((x, y)) == midden:
            dk.px(x, y, steen)


# ---- hoofdstuk 1: de dorpsweg -------------------------------------------------------------------------------------
def molen(dk, x, voet):
    dk.poly([(x - 5, voet), (x - 3, voet - 22), (x + 3, voet - 22), (x + 5, voet)], DGRIJS, ZWART)
    dk.poly([(x - 4, voet - 22), (x, voet - 28), (x + 4, voet - 22)], BRUIN, ZWART)
    dk.rect(x - 1, voet - 6, x + 1, voet, ZWART)                 # deurtje
    dk.px(x, voet - 14, GEEL)                                    # een raampje met licht
    for a in (0.5, 2.07, 3.64, 5.21):                            # de wieken, stil
        ex, ey = x + 16 * math.cos(a), voet - 23 + 16 * math.sin(a) * 0.9
        dk.lijn([(x, voet - 23), (ex, ey)], ZWART, 2)
        dk.lijn([(x + 2 * math.cos(a + 0.3), voet - 23 + 2 * math.sin(a + 0.3)),
                 (ex + 3 * math.cos(a + 1.2), ey + 3 * math.sin(a + 1.2))], GRIJS)


def vogelverschrikker(dk, x, voet):
    dk.lijn([(x, voet), (x, voet - 34)], BRUIN, 2)
    dk.lijn([(x - 12, voet - 24), (x + 12, voet - 26)], BRUIN, 2)
    dk.poly([(x - 6, voet - 26), (x + 6, voet - 27), (x + 5, voet - 12), (x - 5, voet - 12)], ROOD, ZWART)   # jas
    for y in range(voet - 24, voet - 12, 3):
        dk.px(x - 2, y, BRUIN)                                   # een lap
    dk.ovaal(x - 4, voet - 36, x + 4, voet - 28, ORANJE, ZWART)  # een zak als hoofd
    dk.px(x - 2, voet - 33, ZWART)
    dk.px(x + 2, voet - 33, ZWART)
    dk.lijn([(x - 2, voet - 30), (x + 2, voet - 30)], ZWART)
    dk.poly([(x - 7, voet - 35), (x + 7, voet - 35), (x + 3, voet - 42), (x - 3, voet - 42)], DGRIJS, ZWART)   # hoed
    for dx in (-13, -11, 11, 13):                               # stro uit de mouwen
        dk.lijn([(x + dx, voet - 25), (x + dx + (1 if dx > 0 else -1), voet - 21)], GEEL)
    dk.ovaal(x + 9, voet - 33, x + 13, voet - 30, ZWART, ZWART)  # een kraai op zijn arm
    dk.px(x + 13, voet - 32, ORANJE)


def akker(dk, rnd, pts, kleur, rij):
    dk.poly(pts, kleur, ZWART)
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)) + 2, int(max(ys)), rij):        # voren
        for x in range(0, B, 1):
            if dk.im.getpixel((x, y)) == kleur and rnd.random() < 0.8:
                dk.px(x, y, BRUIN if kleur != BRUIN else DGRIJS)


def hek(dk, x1, x2, y, rnd):
    for x in range(x1, x2, 9):
        h = rnd.randint(8, 10)
        dk.rect(x, y - h, x + 1, y, BRUIN)
        dk.lijn([(x - 1, y - h), (x - 1, y)], ZWART)
    dk.lijn([(x1, y - 6), (x2, y - 7)], BRUIN, 1)
    dk.lijn([(x1, y - 3), (x2, y - 4)], BRUIN, 1)


def heg(dk, rnd, pts):
    """een heg van struiken langs een lijn (van achter naar voren groter)"""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        n = int(max(abs(x2 - x1), abs(y2 - y1)) / 3) + 1
        for i in range(n):
            t = i / n
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            r = 1.5 + (y - 70) / 14
            dk.ovaal(x - r, y - r * 1.4, x + r, y + r * 0.4, GROEN, ZWART)
            dk.px(x - r / 2, y - r, LGROEN)


def dorpsweg():
    rnd = random.Random(601)
    dk = Doek()
    rijk.lucht_met_wolken(dk, rnd, 70, kleuren=(BLAUW, PAARS, ROZE), sterren=8, wolken=3)
    verduisterde_zon(dk, 124, 20, 8)
    dk.poly([(0, 72)] + golf(0, B - 1, 64, 4, rnd, stap=6, freq=0.08) + [(B - 1, 72)], BLAUW, BLAUW)   # verre heuvels
    dither(dk, (0, 58, B, 72), PAARS, 0.25, rnd, BLAUW)
    molen(dk, 26, 70)
    # de grond: gras, dan de akkers in perspectief (voren naar het verdwijnpunt achter op de weg)
    vx, vy = 80, 68
    dk.rect(0, 70, B - 1, 126, DGRIJS)
    dither(dk, (0, 70, B, 126), GROEN, 0.55, rnd, DGRIJS)
    akkers = [([(0, 76), (52, 74), (30, 100), (0, 106)], GEEL),
              ([(0, 108), (28, 102), (8, 127), (0, 127)], ORANJE),
              ([(108, 74), (159, 76), (159, 100), (126, 98)], GROEN),
              ([(130, 102), (159, 104), (159, 127), (148, 127)], BRUIN)]
    for pts, k in akkers:
        dk.poly(pts, k, k)
        ys = [p[1] for p in pts]
        for x in range(-200, 360, 7):                            # voren: lijnen van het verdwijnpunt naar onder
            for y in range(int(min(ys)), int(max(ys)) + 1):
                fx = vx + (x - vx) * (y - vy) / (127 - vy)
                if 0 <= fx < B and dk.im.getpixel((int(fx), y)) == k:
                    dk.px(int(fx), y, {GEEL: ORANJE, ORANJE: BRUIN, GROEN: DGRIJS, BRUIN: DGRIJS}[k])
    for _ in range(70):                                          # aren in het graan, kool op de groene akker
        x, y = rnd.randint(0, 50), rnd.randint(78, 126)
        if dk.im.getpixel((x, y)) in (GEEL, ORANJE):
            dk.lijn([(x, y), (x, y - 2 - (y - 70) // 20)], ORANJE)
            dk.px(x, y - 3 - (y - 70) // 20, GEEL)
    for _ in range(30):
        x, y = rnd.randint(112, 158), rnd.randint(78, 98)
        if dk.im.getpixel((x, y)) in (GROEN, DGRIJS):
            r = 1 + (y - 70) // 12
            dk.ovaal(x - r, y - r // 2 - 1, x + r, y + r // 2, LGROEN, GROEN)
    heg(dk, rnd, [(54, 74), (32, 102), (12, 126)])
    heg(dk, rnd, [(106, 74), (128, 100), (150, 126)])
    # het bos achteraan, waar de weg in verdwijnt
    rand = golf(44, 116, 60, 4, rnd, stap=3, freq=0.6)
    dk.poly([(44, 76)] + rand + [(116, 76)], ZWART, ZWART)
    for x, y in rand[::2]:
        dk.poly([(x - 3, y + 3), (x, y - 8), (x + 3, y + 3)], ZWART, ZWART)
    for x in range(48, 114, 9):
        dk.lijn([(x, 70), (x, 76)], DGRIJS)
    links, rechts = pad_diep(dk, rnd, achter_x=80, achter_y=76, krom=8)
    for x, y in ((74, 116), (86, 98), (70, 104)):                # plassen: de schemerlucht weerspiegeld
        r = 2 + (y - 76) // 10
        dk.ovaal(x - r * 2, y - r // 2 - 1, x + r * 2, y + r // 2, PAARS, BRUIN)
        dk.lijn([(x - r, y - 1), (x + r // 2, y - 1)], ROZE)
    hek(dk, 112, 156, 104, rnd)
    vogelverschrikker(dk, 138, 116)
    dk.rect(104, 94, 105, 114, BRUIN)                            # een wegwijzer: "Duisterwoud"
    dk.lijn([(103, 94), (103, 114)], ZWART)
    dk.poly([(98, 92), (116, 91), (119, 94), (116, 97), (98, 97)], ORANJE, ZWART)
    dk.lijn([(101, 94), (112, 94)], BRUIN)
    rijk.verrijk(dk, 611, lichten=[(124, 20, 40, 30, 0.6, {PAARS: ROZE, BLAUW: PAARS}),
                                   (26, 56, 10, 8, 0.5, {DGRIJS: GRIJS, BRUIN: ORANJE})], sluit=(GEEL,))
    return afmaken(dk)


# ---- hoofdstuk 2: het beekdal -------------------------------------------------------------------------------------
def reiger(dk, x, voet):
    dk.lijn([(x - 1, voet), (x - 1, voet - 10)], ORANJE)
    dk.lijn([(x + 1, voet), (x + 1, voet - 10)], ORANJE)
    dk.ovaal(x - 5, voet - 18, x + 4, voet - 9, LGRIJS, ZWART)
    dk.lijn([(x + 3, voet - 16), (x + 5, voet - 24), (x + 4, voet - 28)], LGRIJS, 2)   # de hals
    dk.ovaal(x + 2, voet - 31, x + 7, voet - 27, WIT, ZWART)
    dk.lijn([(x + 7, voet - 29), (x + 13, voet - 28)], GEEL)     # de snavel
    dk.px(x + 5, voet - 30, ZWART)
    dk.lijn([(x - 5, voet - 14), (x - 2, voet - 11)], GRIJS)     # vleugel


def beekdal():
    rnd = random.Random(701)
    dk = Doek()
    rijk.lucht_met_wolken(dk, rnd, 60, kleuren=(BLAUW, PAARS, PAARS), sterren=6, wolken=2)
    # in de verte: het meer met de mist erboven
    dk.poly([(60, 60), (159, 58), (159, 74), (70, 74)], BLAUW, BLAUW)
    for y in range(60, 74, 3):
        for x in range(66, 159, 7):
            dk.lijn([(x + (y % 5), y), (x + 3 + (y % 5), y)], LBLAUW)
    for y in range(56, 66):
        for x in range(60, B, 2):
            if (x + y) % 3 == 0 and rnd.random() < 0.4:
                dk.px(x, y, LGRIJS)
    # heuvels en bomen
    dk.poly([(0, 84), (0, 54), (30, 50), (64, 62), (70, 84)], DGRIJS, ZWART)
    dither(dk, (0, 50, 70, 84), GROEN, 0.45, rnd, DGRIJS)
    dk.poly([(0, 84)] + golf(0, B - 1, 80, 3, rnd, stap=5) + [(B - 1, 126), (0, 126)], DGRIJS, DGRIJS)
    dither(dk, (0, 80, B, 126), GROEN, 0.5, rnd, DGRIJS)
    stam(dk, 14, 6, 2, 96, rnd, takken=((24, 16, 1), (40, 12, 1)))
    stam(dk, 146, 7, 4, 98, rnd, takken=((30, 16, -1), (46, 14, -1)))
    for x, y, r in ((6, 18, 14), (26, 10, 12), (138, 14, 14), (156, 26, 10), (120, 6, 10), (44, 4, 8)):   # kruinen
        for _ in range(14):
            bx, by = x + rnd.randint(-r, r), y + rnd.randint(-r // 2, r // 2)
            dk.ovaal(bx - 4, by - 3, bx + 4, by + 3, GROEN, ZWART)
            dk.px(bx - 1, by - 2, LGROEN)
    for x, y in ((40, 98), (58, 96), (128, 98), (24, 100)):     # struiken langs het pad
        for _ in range(5):
            bx, by = x + rnd.randint(-6, 6), y + rnd.randint(-3, 2)
            dk.ovaal(bx - 4, by - 3, bx + 4, by + 2, GROEN, ZWART)
            dk.px(bx - 1, by - 2, LGROEN)
    # de beek: van achter links naar vooraan, onder het pad door
    beek = [(78, 80), (90, 80), (98, 96), (104, 112), (112, 127), (84, 127), (82, 112), (80, 96)]
    dk.poly(beek, BLAUW, ZWART)
    for y in range(82, 126, 3):                                  # stroming
        for x in range(80, 112, 5):
            if dk.im.getpixel((x, y)) == BLAUW and rnd.random() < 0.6:
                dk.lijn([(x, y), (x + 2, y + 1)], LBLAUW)
    for x, y in ((88, 100), (96, 118), (86, 88)):               # stenen in de beek
        dk.ovaal(x - 3, y - 2, x + 3, y + 2, GRIJS, ZWART)
        dk.px(x - 1, y - 1, LGRIJS)
    pad_zij(dk, rnd, y1=104, y2=121)
    # het bruggetje: een omgezaagde boomstam over de beek, met een leuning van een tak
    dk.rect(78, 104, 112, 112, BRUIN)
    dk.lijn([(78, 104), (112, 104)], ORANJE)
    dk.lijn([(78, 113), (112, 113)], ZWART)
    for x in range(80, 112, 6):
        dk.lijn([(x, 107), (x + 3, 107)], DGRIJS)
    dk.lijn([(80, 104), (80, 94), (110, 92), (110, 104)], BRUIN, 1)
    dk.lijn([(80, 94), (110, 92)], ORANJE)
    reiger(dk, 120, 124)
    for x in (30, 40, 52, 132):                                  # varens
        for a in (-0.9, -0.4, 0.4, 0.9):
            dk.lijn([(x, 102), (x + 8 * math.sin(a), 102 - 8 * math.cos(a))], LGROEN)
    for x, y in ((24, 120), (60, 124)):                          # paddenstoelen
        dk.rect(x, y - 2, x, y, LGRIJS)
        dk.ovaal(x - 2, y - 5, x + 2, y - 2, ROOD, ZWART)
    mist(dk, rnd)
    rijk.verrijk(dk, 711, lichten=[(120, 64, 40, 14, 0.5, {BLAUW: LBLAUW, DGRIJS: GRIJS})], sluit=(PAARS,))
    return afmaken(dk)


# ---- hoofdstuk 3: varen langs de klippen (een toneel: Eldric en Mira zitten in de boot) en het klippad ----------
def zeerotsen():
    rnd = random.Random(801)
    dk = Doek()
    rijk.lucht_met_wolken(dk, rnd, 62, kleuren=(ZWART, BLAUW, PAARS), sterren=18, wolken=2)
    verduisterde_zon(dk, 30, 18, 7)
    zee(dk, rnd, 62, 125)
    rijk.golven(dk, 0, 64, B - 1, 125, rnd)
    # klippen: hoge zuilen uit zee, met meeuwen en nesten
    for pts in ([(96, 125), (100, 40), (108, 30), (118, 34), (124, 60), (128, 125)],
                [(130, 125), (136, 56), (146, 50), (152, 64), (159, 70), (159, 125)],
                [(0, 125), (0, 44), (10, 38), (20, 54), (26, 125)]):
        rotswand(dk, rnd, pts)
    for x, y in ((104, 30), (142, 48), (8, 36)):                 # meeuwen op de toppen
        meeuw(dk, x, y)
    for x in range(98, 126, 3):                                  # schuim waar de golven breken
        dk.px(x, 120 + rnd.randint(-2, 2), WIT)
        dk.px(x + 1, 122 + rnd.randint(-1, 1), LBLAUW)
    for x in range(132, 158, 3):
        dk.px(x, 118 + rnd.randint(-2, 2), WIT)
    vuurtoren_ver(dk, 74, 62)
    # de roeiboot met Olm, Eldric en Mira, tussen de klippen door
    roeiboot(dk, 40, 100, 44, 9, naam=True)
    for x, kl in ((50, ROOD), (62, BLAUW), (74, PAARS)):         # drie figuurtjes in de boot
        dk.ovaal(x - 3, 92, x + 3, 100, kl, ZWART)
        dk.ovaal(x - 2, 87, x + 2, 92, ROZE, ZWART)
    dk.lijn([(46, 96), (34, 106)], BRUIN, 2)                     # een riem
    dk.lijn([(80, 96), (92, 108)], BRUIN, 2)
    for x in range(38, 90, 2):                                   # het kielzog
        dk.px(x, 110 + (x % 4 == 0), LBLAUW)
    rijk.verrijk(dk, 811, lichten=[(30, 18, 20, 16, 0.5, {PAARS: ROZE, BLAUW: PAARS})], sluit=(WIT, ZWART))
    return afmaken(dk)


def klippad():
    rnd = random.Random(821)
    dk = Doek()
    rijk.lucht_met_wolken(dk, rnd, 70, kleuren=(ZWART, BLAUW, PAARS), sterren=14, wolken=2)
    zee(dk, rnd, 70, 100)
    vuurtoren_ver(dk, 140, 70)
    # het klif: het pad loopt over de rand, links rotsen omhoog, rechts naar beneden de zee
    rotswand(dk, rnd, [(0, 40), (14, 30), (30, 44), (48, 60), (64, 100), (0, 100)])
    dk.poly([(0, 100), (B - 1, 96), (B - 1, 126), (0, 126)], DGRIJS, ZWART)
    dither(dk, (0, 96, B, 126), GROEN, 0.45, rnd, DGRIJS)
    pad_zij(dk, rnd, basis=GRIJS, midden=LGRIJS, steen=GRIJS, y1=104, y2=121)
    for x in range(10, 150, 18):                                 # een touw als leuning, aan paaltjes
        dk.rect(x, 96, x + 1, 106, BRUIN)
    rijk.touw(dk, [(x + 1, 98 + 2 * ((x // 18) % 2)) for x in range(10, 150, 18)])
    for x, y in ((40, 124), (90, 125), (120, 123)):              # pollen gras en zeekraal
        for a in (-0.7, 0, 0.7):
            dk.lijn([(x, y), (x + 4 * math.sin(a), y - 4)], LGROEN)
    meeuw(dk, 110, 84)
    rijk.verrijk(dk, 831, lichten=[(140, 66, 30, 20, 0.6, {BLAUW: LBLAUW, DGRIJS: GRIJS, PAARS: ROZE})],
                 sluit=(ZWART,))
    return afmaken(dk)


# ---- hoofdstuk 4: de grotgang en de ondergrondse rivier ---------------------------------------------------------
def grotgang():
    rnd = random.Random(901)
    dk = Doek()
    dk.rect(0, 0, B - 1, 127, ZWART)
    rotswand(dk, rnd, [(0, 0), (B - 1, 0), (B - 1, 30), (120, 40), (80, 34), (40, 42), (0, 32)], kleur=DGRIJS,
             licht=GRIJS, schaduw=ZWART)
    rotswand(dk, rnd, [(0, 32), (40, 42), (30, 100), (0, 104)], kleur=DGRIJS, licht=GRIJS, schaduw=ZWART)
    rotswand(dk, rnd, [(B - 1, 30), (120, 40), (134, 98), (B - 1, 102)], kleur=DGRIJS, licht=GRIJS, schaduw=ZWART)
    for y in range(46, 100):                                     # de gang loopt verder de diepte in: schemer
        for x in range(36, 126):
            d = math.hypot((x - 80) / 44, (y - 100) / 54)
            if d < 1 and dk.im.getpixel((x, y)) == ZWART and (x + y) % 2 == 0 and rijk.ruis(x, y, 5) < (1 - d) * 0.9:
                dk.px(x, y, DGRIJS)
    for x in range(44, 118, 6):                                  # druipsteen
        lengte = rnd.randint(4, 14)
        dk.poly([(x - 2, 38), (x + 2, 38), (x, 38 + lengte)], GRIJS, ZWART)
    for x, y in ((50, 46), (64, 44), (90, 48), (104, 44), (76, 42)):   # gloeiwormen: blauwe stipjes aan het plafond
        dk.px(x, y, CYAAN)
        dk.px(x + 3, y + 2, LBLAUW)
    dk.poly([(0, 104), (30, 100), (134, 98), (B - 1, 102), (B - 1, 126), (0, 126)], BRUIN, ZWART)
    pad_zij(dk, rnd, basis=BRUIN, midden=ORANJE, steen=DGRIJS, y1=104, y2=121)
    for x, y, r in ((20, 100, 2), (140, 100, 3), (60, 124, 1)):  # lichtzwammetjes
        zwam(dk, x, y, r, CYAAN, WIT)
    for x in (34, 128):                                          # stalagmieten
        dk.poly([(x - 4, 104), (x, 84), (x + 4, 104)], GRIJS, ZWART)
    rijk.verrijk(dk, 911, lichten=[(78, 46, 40, 14, 0.5, {DGRIJS: GRIJS, ZWART: DGRIJS}),
                                   (140, 100, 18, 12, 0.6, {BRUIN: LBLAUW, DGRIJS: BLAUW, ORANJE: LBLAUW})])
    return afmaken(dk)


def rivier():
    rnd = random.Random(921)
    dk = Doek()
    dk.rect(0, 0, B - 1, 127, ZWART)
    rotswand(dk, rnd, [(0, 0), (B - 1, 0), (B - 1, 50), (100, 30), (60, 36), (0, 54)], kleur=DGRIJS,
             licht=GRIJS, schaduw=ZWART)
    # de rivier: zwart-blauw water van links achter naar rechts voor, onder het pad; stapstenen
    dk.poly([(0, 60), (B - 1, 54), (B - 1, 100), (0, 102)], BLAUW, ZWART)
    for y in range(60, 100, 3):
        for x in range(rnd.randint(0, 8), B, 9):
            if dk.im.getpixel((x, y)) == BLAUW:
                dk.lijn([(x, y), (x + 3, y)], ZWART if (x + y) % 2 else LBLAUW)
    for x, y in ((20, 70), (60, 66), (100, 74), (140, 64)):     # kristallen in de wand: ze geven licht
        dk.poly([(x - 3, y), (x, y - 12), (x + 3, y)], CYAAN, ZWART)
        dk.lijn([(x - 1, y - 2), (x, y - 10)], WIT)
    dk.poly([(0, 102), (B - 1, 100), (B - 1, 126), (0, 126)], DGRIJS, ZWART)
    pad_zij(dk, rnd, basis=GRIJS, midden=LGRIJS, steen=DGRIJS, y1=104, y2=121)
    for x in range(8, 156, 22):                                  # stapstenen langs de oever
        dk.ovaal(x - 4, 98, x + 4, 103, GRIJS, ZWART)
        dk.px(x - 2, 99, LGRIJS)
    for x, y in ((30, 124), (110, 125)):
        zwam(dk, x, y, 1, CYAAN, WIT)
    rijk.verrijk(dk, 931, lichten=[(60, 66, 60, 20, 0.6, {BLAUW: LBLAUW, DGRIJS: GRIJS, ZWART: BLAUW})])
    return afmaken(dk)


# ---- hoofdstuk 5: het sneeuwveld en de bergkam -------------------------------------------------------------------
def sneeuwveld():
    rnd = random.Random(1001)
    dk = Doek()
    rijk.lucht_met_wolken(dk, rnd, 60, kleuren=(ZWART, BLAUW, PAARS), sterren=20, wolken=2)
    berg(dk, [(0, 70), (30, 30), (60, 52), (96, 18), (130, 46), (159, 34), (159, 70)], zaad=3)
    dk.poly([(0, 70), (B - 1, 66), (B - 1, 126), (0, 126)], WIT, ZWART)
    dither(dk, (0, 66, B, 126), LBLAUW, 0.25, rnd, WIT)
    for x, h in ((12, 26), (24, 20), (140, 28), (152, 22), (70, 14)):
        den(dk, x, 96 if x != 70 else 74, h)
    pad_zij(dk, rnd, basis=LBLAUW, midden=WIT, steen=LGRIJS, y1=104, y2=121)
    for x in range(14, 150, 12):                                 # voetstappen in de sneeuw
        dk.px(x, 112 + (x // 12) % 2 * 3, GRIJS)
        dk.px(x + 1, 112 + (x // 12) % 2 * 3, GRIJS)
    sneeuw(dk, rnd, 80, 2, 100)
    rijk.verrijk(dk, 1011, lichten=[(96, 20, 50, 30, 0.4, {PAARS: ROZE, BLAUW: PAARS})], sluit=(WIT,))
    return afmaken(dk)


def bergkam():
    rnd = random.Random(1021)
    dk = Doek()
    rijk.lucht_met_wolken(dk, rnd, 90, kleuren=(ZWART, BLAUW, PAARS), sterren=24, wolken=3)
    verduisterde_zon(dk, 128, 22, 9)
    # diep beneden: een zee van wolken en verre toppen
    berg(dk, [(0, 96), (20, 70), (44, 86), (70, 64), (98, 88), (124, 72), (159, 90), (159, 96)], zaad=7)
    dk.rect(0, 92, B - 1, 100, LGRIJS)
    for x in range(0, B, 6):
        dk.ovaal(x - 4, 88 + (x % 12) // 4, x + 4, 96, WIT, LGRIJS)
    # de kam: een smalle richel met rotsen, het pad erover
    dk.poly([(0, 102), (B - 1, 100), (B - 1, 126), (0, 126)], GRIJS, ZWART)
    rotswand(dk, rnd, [(0, 102), (B - 1, 100), (B - 1, 126), (0, 126)])
    pad_zij(dk, rnd, basis=WIT, midden=WIT, steen=LBLAUW, y1=104, y2=121)
    for x in range(0, B, 20):                                    # opgewaaide sneeuw langs de rand
        dk.ovaal(x, 100, x + 12, 106, WIT, LBLAUW)
    sneeuw(dk, rnd, 60, 2, 90)
    rijk.verrijk(dk, 1031, lichten=[(128, 22, 30, 24, 0.6, {PAARS: ROZE, BLAUW: PAARS})], sluit=(WIT,))
    return afmaken(dk)


# ---- hoofdstuk 6: de kerkergang en de wenteltrap -----------------------------------------------------------------
def fakkel(dk, x, y):
    dk.rect(x - 1, y, x + 1, y + 8, BRUIN)
    dk.ovaal(x - 2, y - 6, x + 2, y, ORANJE, ROOD)
    dk.ovaal(x - 1, y - 4, x + 1, y - 1, GEEL, GEEL)


def kerkergang():
    rnd = random.Random(1101)
    dk = Doek()
    rijk.stenen_muur(dk, 0, 0, B - 1, 104, rnd, basis=DGRIJS, donker=ZWART, licht_=GRIJS, mos=GROEN, hoog=7, breed=12)
    for x in (30, 80, 130):                                      # bogen: zwarte nissen met tralies
        dk.poly([(x - 12, 104), (x - 12, 54), (x, 44), (x + 12, 54), (x + 12, 104)], ZWART, ZWART)
        for tx in range(x - 9, x + 10, 4):
            dk.lijn([(tx, 52), (tx, 104)], GRIJS)
        dk.lijn([(x - 12, 70), (x + 12, 70)], GRIJS)
    for x in (55, 105):
        fakkel(dk, x, 50)
    dk.poly([(0, 104), (B - 1, 104), (B - 1, 126), (0, 126)], DGRIJS, ZWART)
    rijk.planken_vloer(dk, [(0, 104), (B - 1, 104), (B - 1, 126), (0, 126)], rnd, basis=GRIJS, donker=DGRIJS,
                       licht_=LGRIJS, plank=6, spijkers=False)
    dk.lijn([(18, 34), (22, 40), (20, 46)], GRIJS)               # een ketting aan de muur
    for i in range(6):
        dk.ovaal(150, 30 + i * 4, 153, 33 + i * 4, GRIJS, ZWART)
    dk.ovaal(108, 116, 116, 122, WIT, ZWART)                     # een schedel in de hoek
    dk.px(110, 118, ZWART)
    dk.px(113, 118, ZWART)
    rijk.verrijk(dk, 1111, lichten=[(55, 46, 26, 30, 0.8, None), (105, 46, 26, 30, 0.8, None)])
    return afmaken(dk)


def wenteltrap():
    rnd = random.Random(1121)
    dk = Doek()
    rijk.stenen_muur(dk, 0, 0, B - 1, 126, rnd, basis=GRIJS, donker=DGRIJS, licht_=LGRIJS, mos=None, hoog=8, breed=14)
    dk.rect(0, 104, B - 1, 125, DGRIJS)
    pad_zij(dk, rnd, basis=GRIJS, midden=LGRIJS, steen=DGRIJS, y1=104, y2=121)
    # de trap: achter het pad klimmen de treden van links naar rechts omhoog, de toren in
    for i in range(12):
        x = 4 + i * 13
        y = 94 - i * 5
        dk.poly([(x, y), (x + 14, y), (x + 14, y + 5), (x, y + 5)], LGRIJS, ZWART)
        dk.lijn([(x + 1, y + 1), (x + 13, y + 1)], WIT)
        dk.rect(x, y + 5, x + 14, 103, DGRIJS)
        dk.lijn([(x, y + 5), (x, 103)], ZWART)
    for x in (40, 120):                                          # smalle ramen: maanlicht valt naar binnen
        dk.poly([(x - 4, 60), (x - 4, 30), (x, 24), (x + 4, 30), (x + 4, 60)], BLAUW, ZWART)
        dk.lijn([(x, 26), (x, 60)], ZWART)
        dk.px(x - 2, 34, WIT)

    fakkel(dk, 80, 46)
    dk.lijn([(4, 90), (160, 30)], BRUIN, 2)                      # een leuning van touw langs de trap
    dk.lijn([(4, 89), (160, 29)], ORANJE)
    rijk.verrijk(dk, 1131, lichten=[(80, 42, 26, 24, 0.7, None)])
    return afmaken(dk)


KAMERS = {"dorpsweg": dorpsweg, "beekdal": beekdal, "zeerotsen": zeerotsen, "klippad": klippad,
          "grotgang": grotgang, "rivier": rivier, "sneeuwveld": sneeuwveld, "bergkam": bergkam,
          "kerkergang": kerkergang, "wenteltrap": wenteltrap}


def main():
    namen = sys.argv[1:] or list(KAMERS)
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    for naam in namen:
        im = KAMERS[naam]()
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[%s] data/plaatjes/%s.png; vakjes met te veel kleuren: %d" % (naam, naam, te_veel_kleuren(im)))


if __name__ == "__main__":
    main()
