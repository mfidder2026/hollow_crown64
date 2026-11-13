#!/usr/bin/env python3
"""teken_bospad.py — het bospad in het Duisterwoud (hoofdstuk 2), met de hand getekend als C64-pixelart.

    python3 tools/teken_bospad.py     schrijft data/plaatjes/bospad.png (640 x 256) en build/proef/bospad_groot.png

Scenario hoofdstuk 2: links een moeras (daar zakt Eldric weg: de eerste dood, met Tik), rechts loopt het pad verder het
bos in (naar de spookbrug), en aan de takken hangen holle kokers (Pak koker). Achteraan, onder de rand, het pad terug
naar de bosrand. Donker, mistig, in de schemer: paars tussen de kruinen, zwarte stammen, een paar gloeiende
paddenstoelen. Kamerpixels (160 x 128), alleen C64-kleuren, dikke zwarte lijnen.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)

import c64beeld as cb    # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lucht_en_achtergrond(dk, rnd):
    dk.rect(0, 1, B - 1, 80, PAARS)                             # schemer tussen de kruinen
    for y in range(52, 80):                                      # naar onderen: blauwe nevel
        for x in range(y % 2, B, 2):
            if rnd.random() < (y - 52) / 30:
                dk.px(x, y, BLAUW)
    # verre stammen: blauw, iets dichterbij donkergrijs (diepte zonder bergen)
    for x in range(4, B, 13):
        xx = x + rnd.randint(-3, 3)
        dk.rect(xx, 10, xx + 1 + rnd.randint(0, 1), 84, BLAUW)
    for x in range(10, B, 23):
        xx = x + rnd.randint(-4, 4)
        b = rnd.randint(2, 3)
        dk.poly([(xx - b, 86), (xx - 1, 10), (xx + 1, 10), (xx + b, 86)], DGRIJS, DGRIJS)
        ty = rnd.randint(30, 60)                                 # een kale tak
        r = rnd.choice((-1, 1))
        dk.lijn([(xx, ty), (xx + 7 * r, ty - 6), (xx + 10 * r, ty - 5)], DGRIJS)


def bladerdak(dk, rnd):
    """bovenaan een zwart bladerdak met gerafelde randen en hier en daar donkergroen blad"""
    rand = golf(0, B - 1, 12, 5, rnd, stap=3, freq=0.33)
    dk.poly([(0, 0)] + rand + [(B - 1, 0)], ZWART, ZWART)
    for x, y in rand:                                            # hangende blaadjes en slierten
        if rnd.random() < 0.5:
            dk.lijn([(x, y), (x + rnd.randint(-1, 1), y + rnd.randint(2, 7))], ZWART)
    for _ in range(26):
        x, y = rnd.randint(0, B - 1), rnd.randint(1, 12)
        dk.ovaal(x - 3, y - 2, x + 3, y + 2, GROEN, ZWART)
        dk.px(x - 1, y - 1, LGROEN)


def stam(dk, x, breed, top, voet, rnd, takken=()):
    """een knoestige, iets kromme boomstam met wortels, zwart omlijnd en schors in donkergrijs"""
    krom = [(x + int(2 * math.sin(y * 0.09 + x)), y) for y in range(top, voet + 1, 4)]
    links = [(cx - breed + (voet - cy) // 40, cy) for cx, cy in krom]
    rechts = [(cx + breed - (voet - cy) // 40, cy) for cx, cy in krom]
    dk.poly(links + rechts[::-1], BRUIN)
    dk.lijn(links, ZWART, 1)
    dk.lijn(rechts, ZWART, 1)
    for cx, cy in krom[1:-1]:                                   # schors: korte donkere streepjes
        if rnd.random() < 0.7:
            ox = rnd.randint(-breed + 2, breed - 2)
            dk.lijn([(cx + ox, cy), (cx + ox, cy + rnd.randint(2, 4))], DGRIJS)
    rx = x + int(2 * math.sin(voet * 0.09 + x)) + breed - 2      # rechts een schaduwrand
    dk.lijn([(rx, top + 2), (rx, voet)], DGRIJS)
    for dx in (-breed - 6, breed + 6):                          # wortels
        dk.poly([(x + dx // 3, voet - 4), (x + dx, voet + 2), (x + dx // 2, voet + 2)], BRUIN, ZWART)
    dk.ovaal(x - 2, (top + voet) // 2, x + 1, (top + voet) // 2 + 5, ZWART, ZWART)   # een knoest
    for (ty, lengte, r) in takken:                               # takken naar het bladerdak
        sx = x + r * (breed - 1)
        dk.lijn([(sx, ty), (sx + r * lengte // 2, ty - 6), (sx + r * lengte, ty - 8)], ZWART, 3)
        dk.lijn([(sx, ty - 1), (sx + r * lengte // 2, ty - 7)], BRUIN)


def tak_met_kokers(dk, x1, y1, x2, y2, kokers):
    dk.lijn([(x1, y1), (x2, y2)], ZWART, 3)
    dk.lijn([(x1, y1 - 1), (x2, y2 - 1)], BRUIN)
    for kx, touw in kokers:                                      # holle kokers aan een touwtje
        ky = y1 + (y2 - y1) * (kx - x1) / (x2 - x1)
        dk.lijn([(kx, ky + 1), (kx, ky + touw)], LGRIJS)
        top = ky + touw
        dk.poly([(kx - 2, top), (kx + 2, top), (kx + 3, top + 4), (kx + 3, top + 12), (kx + 2, top + 14),
                 (kx - 2, top + 14), (kx - 3, top + 12), (kx - 3, top + 4)], GRIJS)
        dk.lijn([(kx - 2, top + 2), (kx - 2, top + 12)], LGRIJS)      # licht van links
        dk.ovaal(kx - 1, top + 5, kx + 1, top + 8, ZWART, ZWART)       # het gat waar de wind door fluit
        dk.lijn([(kx - 2, top + 10), (kx + 2, top + 10)], DGRIJS)     # een bandje


def moeras(dk, rnd):
    """links vooraan: zwart water met kroos, riet, bellen en een rotte stronk"""
    rand = [(0, 84)] + golf(0, 58, 88, 3, rnd, stap=4, freq=0.2) + [(64, 100), (60, 112), (44, 122), (0, 124)]
    dk.poly(rand, BRUIN, ZWART)                                 # modderrand
    dk.poly([(0, 90)] + golf(2, 54, 93, 2, rnd, stap=4, freq=0.25) + [(56, 104), (48, 116), (30, 121), (0, 122)],
            ZWART, ZWART)
    for _ in range(90):                                          # kroos: dun groen spul op het water
        x, y = rnd.randint(1, 54), rnd.randint(94, 121)
        if dk.im.getpixel((x, y)) == ZWART:
            dk.rect(x, y, x + rnd.randint(1, 2), y, GROEN)
    for x, y in ((14, 104), (31, 111), (40, 99), (22, 116)):    # bellen
        dk.px(x, y, LGROEN)
        dk.px(x + 1, y - 1, LGROEN)
    for y in range(96, 122, 3):                                  # een lichte rimpel
        x = 6 + (y * 7) % 40
        if dk.im.getpixel((x, y)) == ZWART:
            dk.lijn([(x, y), (x + 3, y)], DGRIJS)
    for x in (3, 7, 11, 49, 54, 59, 62):                         # riet met lisdodden
        h = rnd.randint(12, 20)
        voet = 96 if x < 30 else 100
        top = (x + rnd.randint(-2, 2), voet - h)
        dk.lijn([(x, voet), top], LGROEN if x % 2 else GROEN)
        dk.rect(top[0], top[1], top[0] + 1, top[1] + 4, BRUIN)
    dk.poly([(26, 98), (27, 88), (29, 86), (31, 89), (33, 87), (34, 98)], DGRIJS)   # rotte stronk in het water
    dk.lijn([(28, 90), (28, 96)], GRIJS)


def pad(dk, rnd):
    """het pad: van onder (terug naar de bosrand) naar rechts, het bos in (naar de spookbrug)"""
    links = [(74, 127), (76, 116), (86, 106), (102, 98), (126, 91), (159, 87)]
    rechts = [(159, 95), (132, 101), (116, 108), (108, 117), (112, 127)]
    dk.poly(links + rechts, BRUIN, ZWART)
    dk.poly([(80, 127), (82, 117), (92, 108), (108, 101), (130, 95), (159, 91), (159, 92), (130, 98),
             (112, 105), (100, 114), (98, 127)], ORANJE, ORANJE)   # het uitgesleten midden is lichter
    for _ in range(50):                                          # steentjes
        x, y = rnd.randint(78, 158), rnd.randint(88, 126)
        if dk.im.getpixel((x, y)) == ORANJE:
            dk.px(x, y, BRUIN)


def bodem(dk, rnd):
    dk.poly([(0, 82)] + golf(0, B - 1, 84, 2, rnd, stap=6) + [(B - 1, 126), (0, 126)], DGRIJS, DGRIJS)
    dither(dk, (0, 84, B, 126), GROEN, 0.55, rnd, DGRIJS)        # mos op de bosgrond
    for _ in range(30):                                          # varens en grassprietjes
        x, y = rnd.randint(60, 158), rnd.randint(88, 125)
        dk.lijn([(x, y), (x - 1, y - 3)], LGROEN)
        dk.lijn([(x, y), (x + 2, y - 2)], GROEN)


def paddenstoelen(dk, rnd):
    for x, y in ((122, 116), (127, 118), (68, 98), (150, 108), (144, 111)):
        dk.rect(x, y - 2, x, y, LGRIJS)
        dk.ovaal(x - 2, y - 5, x + 2, y - 2, ROOD, ZWART)
        dk.px(x - 1, y - 4, WIT)


def mist(dk, rnd):
    for y in range(70, 92):                                      # een flard mist tussen de stammen
        dicht = 0.45 - abs(y - 80) * 0.04
        for x in range((y % 2), B, 2):
            if rnd.random() < dicht and dk.im.getpixel((x, y)) in (DGRIJS, BLAUW, PAARS, GROEN):
                dk.px(x, y, LGRIJS)


def kleuren_per_vakje(im):
    """de omzetter mag per 4 x 8 vakje 3 kleuren + zwart: een vierde kleur wordt de meest voorkomende buur"""
    for cy in range(0, H, 8):
        for cx in range(0, B, 4):
            tel = {}
            for y in range(cy, cy + 8):
                for x in range(cx, cx + 4):
                    k = im.getpixel((x, y))
                    if k != ZWART:
                        tel[k] = tel.get(k, 0) + 1
            if len(tel) <= 3:
                continue
            houden = sorted(tel, key=lambda k: -tel[k])[:3]
            for y in range(cy, cy + 8):
                for x in range(cx, cx + 4):
                    k = im.getpixel((x, y))
                    if k != ZWART and k not in houden:
                        im.putpixel((x, y), min(houden, key=lambda h: sum((a - b) ** 2 for a, b in
                                                                            zip(cb.RGB[h], cb.RGB[k]))))


def teken():
    rnd = random.Random(21)
    dk = Doek()
    lucht_en_achtergrond(dk, rnd)
    bodem(dk, rnd)
    mist(dk, rnd)
    stam(dk, 22, 7, 4, 86, rnd, takken=((30, 16, 1), (44, 14, -1)))
    stam(dk, 92, 5, 8, 88, rnd, takken=((52, 12, 1),))
    stam(dk, 142, 8, 2, 90, rnd, takken=((38, 18, -1),))
    tak_met_kokers(dk, 96, 30, 132, 20, ((106, 4), (118, 8)))     # de kokers: kamer x ~100-122, y ~25-50
    tak_met_kokers(dk, 88, 26, 62, 36, ((74, 6),))
    bladerdak(dk, rnd)
    moeras(dk, rnd)
    pad(dk, rnd)
    paddenstoelen(dk, rnd)
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    kleuren_per_vakje(dk.im)
    return dk.im


def main():
    im = teken()
    rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", "bospad.png"))
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", "bospad_groot.png"))
    print("[bospad] data/plaatjes/bospad.png; vakjes met meer dan 3 kleuren + zwart: %d" % te_veel_kleuren(im))


if __name__ == "__main__":
    main()
