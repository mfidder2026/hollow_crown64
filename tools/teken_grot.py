#!/usr/bin/env python3
"""teken_grot.py — de grot van Grom: het toneel van de tussenscène na hoofdstuk 1 ("Ondertussen, diep in de berg").

    python3 tools/teken_grot.py      schrijft data/plaatjes/grot.png (640 x 256) en build/proef/grot_groot.png

Een hoge grot onder de berg. In het midden, op een stenen zuil, de Holle Kroon: een gouden kroon waarin het
gevangen zonlicht gloeit (de motor laat de gloed flakkeren: FLAKKER in scripts/grot.hcs). Het licht valt warm op de
rotsen eromheen; verder is het donker, met druipstenen, een ondergronds stroompje en gangen waar de aardmannetjes
uit komen. Grom en de aardmannetjes zijn figuren (sprites), geen deel van dit plaatje.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import kleuren_per_vakje   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KX, KY = 80, 62                    # het midden van de kroon
GLOED = (68, 48, 24, 24)           # de vakjes met de kroon: daar flakkert de gloed (x, b veelvoud van 4; y, h van 8)


TINTEN = [GEEL, ORANJE, BRUIN, DGRIJS, ZWART]    # licht van de kroon, van dichtbij naar ver


def licht(x, y):
    """hoe ver weg van de kroon (0 = in de kroon, 1 = de rand van het licht): een ovaal, breder dan hoog"""
    return math.hypot((x - KX) / 105, (y - KY) / 85)


def tint(x, y, rnd, extra=0.0):
    """de rotskleur op x,y: de lichttint, met om en om pixels (dither) tussen twee tinten"""
    d = min(licht(x, y) * 3.2 + extra, 2.6 + (licht(x, y) > 1.15) * 0.8)   # tot donkergrijs; alleen de hoeken zwart
    i = int(d)
    if (x + y) % 2 == 0 and rnd.random() < d - i:
        i += 1
    return TINTEN[max(0, min(len(TINTEN) - 1, i + 1))]


def wanden(dk, rnd):
    """de achterwand: rots met barsten en bulten, warm verlicht door de kroon, naar de randen zwart"""
    for y in range(1, 126):
        for x in range(B):
            dk.px(x, y, tint(x, y, rnd, 0.35))
    for _ in range(34):                                          # bulten: een lichte bovenrand, een zwarte onderrand
        x, y = rnd.randint(0, B - 1), rnd.randint(20, 90)
        b, h = rnd.randint(4, 9), rnd.randint(4, 8)
        pts = [(x - b, y + h), (x - b + 1, y + 2), (x - b // 2, y), (x + b // 2, y), (x + b - 1, y + 2), (x + b, y + h)]
        dk.lijn(pts[1:5], tint(x, y - 1, rnd, -0.6))             # een ronde bovenkant in het licht
        dk.lijn([pts[4], pts[5], (x - b // 2, y + h + 1), pts[0]], ZWART)   # en een schaduw eronder
    for _ in range(18):                                          # barsten
        x, y = rnd.randint(0, B - 1), rnd.randint(18, 96)
        pts = [(x, y)]
        for _ in range(4):
            x, y = x + rnd.randint(-3, 3), y + rnd.randint(2, 5)
            pts.append((x, y))
        dk.lijn(pts, ZWART)
    # het gewelf: zwart bovenaan, met lange druipstenen die aan de kant van de kroon oplichten
    rand = golf(0, B - 1, 10, 5, rnd, stap=4, freq=0.2)
    dk.poly([(0, 0)] + rand + [(B - 1, 0)], ZWART, ZWART)
    for x in range(2, B, 6):
        y0 = 8 + int(5 * math.sin(x * 0.2))
        h = rnd.randint(6, 26 if abs(x - KX) > 20 else 12)
        dk.poly([(x - 3, y0), (x + 3, y0), (x, y0 + h)], DGRIJS, ZWART)
        kant = 1 if x < KX else -1                               # de kant naar de kroon toe vangt licht
        dk.lijn([(x + kant, y0 + 1), (x + kant // 2, y0 + h - 3)], tint(x, y0 + h, rnd, -0.5))


def gangen(dk):
    """twee gangen in de wanden: daar komen de aardmannetjes vandaan"""
    for pts in ([(126, 104), (124, 84), (128, 74), (136, 70), (144, 74), (148, 84), (148, 104)],
                [(8, 100), (6, 84), (12, 74), (20, 76), (24, 88), (24, 100)]):
        dk.poly(pts, ZWART, ZWART)
    for x, y in ((132, 88), (135, 88), (14, 88), (17, 88)):      # oogjes in het donker
        dk.px(x, y, GEEL)


def vloer(dk, rnd):
    rand = golf(0, B - 1, 102, 2, rnd, stap=5, freq=0.15)
    for y in range(101, 126):
        for x in range(B):
            if y > rand[min(len(rand) - 1, x // 5)][1]:
                dk.px(x, y, tint(x, (y - 100) * 3 + KY, rnd, 0.35))   # de vloer: iets donkerder dan de wand
    dk.lijn(rand, ZWART)
    dk.lijn([(x, y + 1) for x, y in rand], BRUIN)
    for _ in range(30):                                          # stenen en gruis: lichte bovenkant, zwarte schaduw
        x, y = rnd.randint(2, B - 6), rnd.randint(105, 123)
        b = rnd.randint(2, 4)
        dk.lijn([(x, y + 1), (x + b, y + 1)], ZWART)
        dk.lijn([(x, y), (x + b - 1, y)], tint(x, y, rnd, -0.8))
    stroom = [(B - 1, 112), (140, 116), (120, 121), (100, 124), (88, 125)]   # een stroompje dat het licht vangt
    dk.lijn(stroom, ZWART, 3)
    dk.lijn([(x, y) for x, y in stroom], BLAUW)
    for x, y in stroom[2:]:
        dk.px(x, y, LBLAUW)


def zuil(dk, rnd):
    """de stenen zuil waar de kroon op staat, de voorkant verlicht, met runen"""
    dk.poly([(KX - 9, 110), (KX - 7, 80), (KX + 7, 80), (KX + 9, 110)], BRUIN, ZWART)
    dk.poly([(KX - 6, 110), (KX - 5, 82), (KX + 2, 82), (KX + 3, 110)], ORANJE, ORANJE)   # het licht van boven
    dk.lijn([(KX + 6, 82), (KX + 7, 108)], DGRIJS)               # schaduwkant
    dk.rect(KX - 12, 76, KX + 12, 80, ORANJE)                    # de plaat bovenop
    dk.lijn([(KX - 12, 76), (KX + 12, 76)], GEEL)
    dk.lijn([(KX - 12, 80), (KX + 12, 80)], ZWART)
    for y in (86, 94, 102):                                      # runen
        dk.lijn([(KX - 3, y), (KX - 1, y + 3), (KX + 1, y), (KX + 3, y + 3)], BRUIN)
    dk.rect(KX - 13, 108, KX + 13, 111, BRUIN)                   # de voet
    dk.lijn([(KX - 13, 108), (KX + 13, 108)], ORANJE)
    dk.lijn([(KX - 13, 111), (KX + 13, 111)], ZWART)


def kroon(dk):
    """de Holle Kroon: goud, hol van binnen, en daaruit het gevangen zonlicht"""
    for a in range(-170, 10, 20):                                # stralen omhoog en opzij
        r = math.radians(a)
        dk.lijn([(KX + 11 * math.cos(r), KY + 2 + 9 * math.sin(r)),
                 (KX + 22 * math.cos(r), KY + 2 + 15 * math.sin(r))], GEEL)
    dk.ovaal(KX - 10, KY - 14, KX + 10, KY + 4, GEEL, GEEL)       # het licht dat uit de kroon opstijgt
    dk.ovaal(KX - 6, KY - 12, KX + 6, KY - 3, WIT, WIT)
    # de kroon: een gouden ring met vijf punten
    punten = [(KX - 11, KY + 12), (KX - 11, KY + 1), (KX - 8, KY + 5), (KX - 6, KY - 3), (KX - 3, KY + 4),
              (KX, KY - 5), (KX + 3, KY + 4), (KX + 6, KY - 3), (KX + 8, KY + 5), (KX + 11, KY + 1), (KX + 11, KY + 12)]
    dk.poly(punten, GEEL, ZWART)
    dk.poly([(KX - 11, KY + 9), (KX + 11, KY + 9), (KX + 11, KY + 12), (KX - 11, KY + 12)], ORANJE, ZWART)   # de band
    for x in (KX - 6, KX, KX + 6):
        dk.rect(x - 1, KY + 10, x, KY + 11, ROOD)                # robijntjes
    for x, y in ((KX - 6, KY - 1), (KX, KY - 3), (KX + 6, KY - 1)):
        dk.px(x, y, WIT)                                         # glimmende punten


def teken():
    rnd = random.Random(7)
    dk = Doek()
    wanden(dk, rnd)
    gangen(dk)
    vloer(dk, rnd)
    zuil(dk, rnd)
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
