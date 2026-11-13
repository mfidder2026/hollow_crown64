#!/usr/bin/env python3
"""teken_grot.py — de grot van Grom: het toneel van de tussenscène na hoofdstuk 1 ("Ondertussen, diep onder de berg").

    python3 tools/teken_grot.py      schrijft data/plaatjes/grot.png (640 x 256) en build/proef/grot_groot.png

Een hoge grot onder de berg. Boven in het gewelf een schacht naar de hemel: daar zie je de verduisterde zon (een zwarte
schijf met een dunne stralenkrans) en de twee manen die ervoor vastgezet zijn. Een bundel koud licht valt naar beneden,
op Grom: een reusachtige tovertrol, voorovergebogen op een troon van rots, met rode ogen, slagtanden en grote vuisten.
Op zijn kop de Holle Kroon, een zwarte ijzeren kroon met twee maanstenen: zolang hij die draagt, kunnen de manen niet
verder (de Schemerspreuk). De maanstenen pulseren (FLAKKER in scripts/grot.hcs). Grom staat in het plaatje zelf: een
sprite is veel te klein voor hem. Het aardmannetje dat binnenkruipt is wel een figuur.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import kleuren_per_vakje   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GX = 80                            # het midden van Grom
SCHACHT = (64, 96)                 # de schacht in het gewelf (x van, tot)


def licht(x, y):
    """hoeveel van het koude licht uit de schacht hier valt (0 = niets, 1 = vol): een kegel naar beneden"""
    breedte = 14 + y * 0.45
    return max(0.0, 1 - abs(x - GX) / breedte) * max(0.0, 1 - y / 150)


def grot(dk, rnd):
    """de wanden: donkerblauwe rots, naar de kegel van licht toe grijzer, met barsten en druipstenen"""
    for y in range(1, 126):
        for x in range(B):
            l = licht(x, y)                                  # (alleen blauw en zwart: Grom is grijs, hij moet loskomen)
            k = ZWART
            if l > 0.3:
                k = BLAUW
            elif l > 0.08:
                k = BLAUW if (x + y) % 2 else ZWART
            elif (x * 7 + y * 3) % 5 < 1 + (y > 40):
                k = BLAUW
            dk.px(x, y, k)
    for _ in range(40):                                          # rotsbulten met een koude lichtrand
        x, y = rnd.randint(0, B - 1), rnd.randint(22, 96)
        b, h = rnd.randint(4, 9), rnd.randint(4, 8)
        rand = LBLAUW if licht(x, y) > 0.2 else BLAUW
        dk.lijn([(x - b + 1, y + 2), (x - b // 2, y), (x + b // 2, y), (x + b - 1, y + 2)], rand)
        dk.lijn([(x + b, y + h), (x - b // 2, y + h + 1), (x - b, y + h)], ZWART)
    # het gewelf met druipstenen, en de schacht naar de hemel
    rand = golf(0, B - 1, 12, 5, rnd, stap=4, freq=0.2)
    dk.poly([(0, 0)] + rand + [(B - 1, 0)], ZWART, ZWART)
    for x in range(2, B, 6):
        if SCHACHT[0] - 4 < x < SCHACHT[1] + 4:
            continue
        y0 = 10 + int(5 * math.sin(x * 0.2))
        h = rnd.randint(6, 24)
        dk.poly([(x - 3, y0), (x + 3, y0), (x, y0 + h)], ZWART, ZWART)
        dk.lijn([(x - 1, y0 + 1), (x, y0 + h - 3)], BLAUW)


def hemel(dk):
    """door een gekarteld gat in het gewelf: de schemerhemel, de zwarte zon met een stralenkrans, de twee manen ervoor"""
    x1, x2 = SCHACHT
    gat = [(x1, 0), (x2, 0), (x2 - 2, 6), (x2 - 6, 9), (x2 - 5, 15), (x2 - 10, 19), (x1 + 12, 20), (x1 + 6, 16),
           (x1 + 5, 10), (x1 + 1, 6)]
    dk.poly(gat, PAARS, ZWART)
    cx, cy = (x1 + x2) // 2, 9
    dk.ovaal(cx - 9, cy - 7, cx + 9, cy + 7, GEEL, GEEL)        # de stralenkrans
    dk.ovaal(cx - 7, cy - 5, cx + 7, cy + 5, ZWART, ZWART)      # de zwarte zon
    dk.ovaal(cx - 8, cy - 4, cx, cy + 4, DGRIJS, ZWART)         # maan 1 ...
    dk.ovaal(cx, cy - 4, cx + 8, cy + 4, DGRIJS, ZWART)         # ... en maan 2, er vlak voor
    dk.px(cx - 5, cy - 2, GRIJS)
    dk.px(cx + 3, cy - 2, GRIJS)


def bundel(dk, rnd):
    """de bundel koud licht uit de schacht (lichtblauwe stofjes)"""
    for _ in range(140):
        y = rnd.randint(24, 100)
        x = GX + rnd.randint(-int(10 + y * 0.3), int(10 + y * 0.3))
        if dk.im.getpixel((x, y)) in (ZWART, BLAUW) and (x + y) % 2 == 0:
            dk.px(x, y, LBLAUW)


def troon(dk):
    """een troon van ruwe rots achter Grom, net zichtbaar naast zijn schouders"""
    dk.poly([(38, 112), (36, 62), (44, 44), (52, 38), (108, 38), (116, 44), (124, 62), (122, 112)], ZWART, BLAUW)
    dk.lijn([(44, 45), (52, 39), (108, 39), (116, 45)], LBLAUW)  # de bovenrand vangt het licht
    for x1, y1, x2, y2 in ((40, 64, 44, 96), (120, 64, 116, 96), (56, 40, 60, 46), (104, 40, 100, 46)):
        dk.lijn([(x1, y1), (x2, y2)], BLAUW)


def grom(dk):
    """Grom: een berg van een trol, voorovergebogen op zijn vuisten. Bijna helemaal schaduw; alleen de bovenkant
    vangt het koude licht uit de schacht. Rode ogen, een grommende bek met slagtanden."""
    lijf, rand, rand2 = DGRIJS, LBLAUW, GRIJS
    # de romp: brede borst, een hangende buik, smal naar de heupen
    romp = [(GX - 12, 52), (GX - 24, 46), (GX - 31, 50), (GX - 30, 62), (GX - 26, 74), (GX - 24, 88), (GX - 20, 102),
            (GX - 14, 110), (GX + 14, 110), (GX + 20, 102), (GX + 24, 88), (GX + 26, 74), (GX + 30, 62), (GX + 31, 50),
            (GX + 24, 46), (GX + 12, 52)]
    dk.poly(romp, lijf, ZWART)
    for r in (-1, 1):                                            # borstspieren met licht van boven
        dk.ovaal(GX + r * 12 - 10, 58, GX + r * 12 + 10, 74, lijf, ZWART)
        dk.lijn([(GX + r * 12 - 7 * r, 59), (GX + r * 12 + 6 * r, 60)], rand2)
    for y in range(76, 110):                                     # de buik: schaduw naar onder
        for x in range(GX - 25, GX + 26):
            if dk.im.getpixel((x, y)) == lijf and (x + y) % 2 == 0 and (y > 92 or abs(x - GX) > 14):
                dk.px(x, y, ZWART)
    dk.ovaal(GX - 2, 84, GX + 1, 87, ZWART, ZWART)               # navel
    dk.rect(GX - 18, 104, GX + 18, 108, BRUIN)                   # een lendendoek van huid
    dk.lijn([(GX - 18, 108), (GX + 18, 108)], ZWART)
    dk.lijn([(GX - 18, 104), (GX + 18, 104)], ZWART)
    for r in (-1, 1):                                            # gehurkte benen, voeten met klauwen
        dk.poly([(GX + r * 14, 108), (GX + r * 26, 104), (GX + r * 28, 114), (GX + r * 12, 114)], lijf, ZWART)
        for t in range(3):
            dk.px(GX + r * (14 + 5 * t), 115, WIT)
    # de armen: los van de romp (er zit grot tussen), als pilaren naar de vuisten op de grond
    for r in (-1, 1):
        arm = [(GX + r * 26, 46), (GX + r * 38, 44), (GX + r * 46, 52), (GX + r * 48, 68), (GX + r * 46, 84),
               (GX + r * 47, 100), (GX + r * 36, 100), (GX + r * 35, 84), (GX + r * 34, 68), (GX + r * 30, 58)]
        dk.poly(arm, lijf, ZWART)
        dk.lijn([(GX + r * 27, 46), (GX + r * 38, 45), (GX + r * 45, 52), (GX + r * 47, 66)], rand)
        dk.lijn([(GX + r * 46, 70), (GX + r * 45, 84)], rand2)
        dk.lijn([(GX + r * 36, 76), (GX + r * 42, 82)], ZWART)   # de elleboog
        vx = GX + r * 41                                         # de vuist, op de grond
        dk.ovaal(vx - 9, 98, vx + 9, 113, lijf, ZWART)
        dk.lijn([(vx - 6, 99), (vx + 5, 99)], rand2)
        for t in range(4):
            dk.lijn([(vx - 6 + 4 * t, 103), (vx - 6 + 4 * t, 110)], ZWART)   # vingers
            dk.px(vx - 5 + 4 * t, 113, WIT)                      # klauwen
    # de kop: laag tussen de schouders, naar voren gestoken
    kop = [(GX - 12, 64), (GX - 14, 52), (GX - 11, 42), (GX + 11, 42), (GX + 14, 52), (GX + 12, 64), (GX + 6, 68),
           (GX - 6, 68)]
    dk.poly(kop, lijf, ZWART)
    dk.lijn([(GX - 13, 51), (GX - 10, 43), (GX + 10, 43), (GX + 13, 51)], rand)   # licht op de schedel
    for r in (-1, 1):                                            # oren: plat naar achteren, gescheurd
        dk.poly([(GX + r * 13, 48), (GX + r * 24, 40), (GX + r * 20, 47), (GX + r * 22, 50), (GX + r * 14, 54)],
                lijf, ZWART)
        dk.lijn([(GX + r * 14, 47), (GX + r * 23, 41)], rand)
    # boze wenkbrauwen in een V, en daaronder de gloeiende ogen
    for r in (-1, 1):
        dk.lijn([(GX + r * 11, 46), (GX + r * 2, 51)], ZWART, 2)
        dk.rect(GX + r * 6 - 2, 51, GX + r * 6 + 1, 52, ROOD)
        dk.px(GX + r * 6 - (r < 0), 51, WIT)
    dk.poly([(GX - 3, 53), (GX + 3, 53), (GX + 5, 58), (GX - 5, 58)], ZWART, ZWART)    # een platte, brede neus
    dk.lijn([(GX - 2, 57), (GX - 1, 57)], rand2)
    # de bek: open, een grauw; slagtanden van onder omhoog
    dk.poly([(GX - 8, 60), (GX + 8, 60), (GX + 6, 65), (GX - 6, 65)], ZWART, ZWART)
    dk.lijn([(GX - 6, 63), (GX + 6, 63)], ROOD)                  # een tong in het donker
    for r in (-1, 1):
        dk.poly([(GX + r * 5, 66), (GX + r * 6, 58), (GX + r * 8, 66)], WIT, ZWART)
    for x in (GX - 3, GX, GX + 3):
        dk.px(x, 60, WIT)                                        # tanden


def kroon(dk):
    """de Holle Kroon: zwart ijzer, scherpe punten, en twee maanstenen die koud gloeien"""
    y0 = 43
    pts = [(GX - 10, y0), (GX - 11, y0 - 7), (GX - 8, y0 - 4), (GX - 6, y0 - 11), (GX - 3, y0 - 5), (GX, y0 - 13),
           (GX + 3, y0 - 5), (GX + 6, y0 - 11), (GX + 8, y0 - 4), (GX + 11, y0 - 7), (GX + 10, y0)]
    dk.poly(pts, ZWART, ZWART)
    dk.lijn(pts[1:-1], LGRIJS)                                   # koud licht op de punten
    for r in (-1, 1):                                            # de twee maanstenen, in de punten
        mx = GX + r * 6
        dk.ovaal(mx - 2, y0 - 8, mx + 2, y0 - 3, LBLAUW, ZWART)
        dk.px(mx - 1, y0 - 7, WIT)
    dk.ovaal(GX - 1, y0 - 9, GX + 1, y0 - 6, DGRIJS, ZWART)      # midden: hol


def vloer(dk, rnd):
    rand = golf(0, B - 1, 108, 2, rnd, stap=5, freq=0.15)
    dk.poly([(0, 126)] + rand + [(B - 1, 126)], BLAUW, ZWART)
    for y in range(110, 126):                                    # naar de randen donkerder
        for x in range(B):
            if dk.im.getpixel((x, y)) == BLAUW and licht(x, 60) < 0.1 and (x + y) % 2 == 0:
                dk.px(x, y, ZWART)
    for _ in range(20):
        x, y = rnd.randint(2, B - 6), rnd.randint(112, 123)
        dk.lijn([(x, y + 1), (x + 3, y + 1)], ZWART)
        dk.lijn([(x, y), (x + 2, y)], LBLAUW if licht(x, 60) > 0.1 else DGRIJS)
    # botten bij de troon: een trol in een grot
    for x, y in ((30, 118), (124, 120)):
        dk.lijn([(x, y), (x + 6, y - 2)], LGRIJS)
        dk.px(x - 1, y - 1, LGRIJS)
        dk.px(x + 7, y - 3, LGRIJS)
    dk.ovaal(112, 114, 118, 119, LGRIJS, ZWART)                  # een schedeltje
    dk.px(114, 116, ZWART)


def gangen(dk):
    """twee gangen in de wanden: daar komen de aardmannetjes vandaan"""
    for pts in ([(136, 112), (134, 92), (138, 82), (146, 80), (154, 84), (156, 92), (156, 112)],
                [(4, 112), (4, 90), (8, 82), (16, 80), (22, 86), (24, 112)]):
        dk.poly(pts, ZWART, ZWART)
    for x, y in ((142, 96), (145, 96), (11, 94), (14, 94)):      # oogjes in het donker
        dk.px(x, y, GEEL)


def teken():
    rnd = random.Random(7)
    dk = Doek()
    grot(dk, rnd)
    hemel(dk)
    bundel(dk, rnd)
    gangen(dk)
    vloer(dk, rnd)
    troon(dk)
    grom(dk)
    kroon(dk)
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    kleuren_per_vakje(dk.im)
    return dk.im


def main():
    im = teken()
    rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", "grot.png"))
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", "grot_groot.png"))
    print("[grot] data/plaatjes/grot.png; vakjes met meer dan 3 kleuren + zwart: %d" % te_veel_kleuren(im))


if __name__ == "__main__":
    main()
