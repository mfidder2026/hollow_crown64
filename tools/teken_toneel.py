#!/usr/bin/env python3
"""teken_toneel.py — het toneel van de verhaalanimatie, met de hand getekend als C64-pixelart (geen FLUX).

    python3 tools/teken_toneel.py            schrijft data/plaatjes/toneel.png (640 x 256) en build/proef/toneel_*.png

Rechtstreeks in kamerpixels (160 x 128, multicolor: elke pixel 2 breed) en alleen C64-kleuren, met dikke zwarte
lijnen zoals het plein. Per vakje van 4 x 8 mogen er 3 kleuren + zwart zijn: het script telt de vakjes met te veel
kleuren (die kiest de omzetter dan zelf), zodat je ziet waar het plaatje op de C64 anders wordt.

Het toneel: Aethermoor onder de Eeuwige Zon. Links het kasteel op een heuvel, in het dal Dawnhaven met rieten daken en
rokende schoorstenen, rijen ronde bomen, rechts de Rotskloof. De zon staat midden in de lucht: daar schuiven de manen
als sprites overheen. De lucht is één kleur (lichtblauw) met witte wolkjes: de animatie maakt hem met kleurwissels
donkerder, tot de paarse schemer van het plein.
"""
import os, random, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c64beeld as cb    # noqa: E402  (het C64-palet zoals VICE het toont: hetzelfde als de omzetter)

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B, H = 160, 128
ZWART, WIT, ROOD, CYAAN, PAARS, GROEN, BLAUW, GEEL = range(8)
ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS = range(8, 16)


class Doek:
    def __init__(self):
        self.im = Image.new("L", (B, H), ZWART)
        self.d = ImageDraw.Draw(self.im)

    def px(self, x, y, k):
        if 0 <= x < B and 0 <= y < H:
            self.im.putpixel((int(x), int(y)), k)

    def rect(self, x1, y1, x2, y2, k):
        self.d.rectangle([x1, y1, x2, y2], fill=k)

    def poly(self, pts, k, rand=ZWART):
        self.d.polygon(pts, fill=k, outline=rand)

    def ovaal(self, x1, y1, x2, y2, k, rand=ZWART):
        self.d.ellipse([x1, y1, x2, y2], fill=k, outline=rand)

    def lijn(self, pts, k, w=1):
        self.d.line(pts, fill=k, width=w)


def lucht(dk, rnd):
    dk.rect(0, 1, B - 1, 72, CYAAN)
    for cx, cy, w in ((118, 8, 10), (142, 20, 9), (58, 30, 6)):   # wolkjes
        dk.ovaal(cx - w, cy - 3, cx + w, cy + 3, WIT, CYAAN)
        dk.ovaal(cx - w // 2, cy - 6, cx + w // 2, cy + 1, WIT, CYAAN)


def zon(dk):
    cx, cy = 80, 20                                              # het midden: daar komen de manen
    for i in range(12):                                          # stralen
        import math
        a = i * math.pi / 6
        dk.lijn([(cx + 12 * math.cos(a), cy + 12 * math.sin(a) * 0.9),
                 (cx + 16 * math.cos(a), cy + 16 * math.sin(a) * 0.9)], GEEL)
    dk.ovaal(cx - 9, cy - 9, cx + 9, cy + 9, GEEL, ORANJE)
    dk.ovaal(cx - 5, cy - 5, cx + 5, cy + 5, WIT, WIT)


def bergen(dk):
    dk.poly([(0, 64), (16, 46), (30, 56), (48, 40), (70, 60), (98, 44), (122, 58), (142, 42), (159, 52),
             (159, 76), (0, 76)], GRIJS, DGRIJS)
    for (x, y) in ((48, 40), (98, 44), (142, 42), (16, 46)):     # sneeuw op de toppen
        dk.poly([(x - 4, y + 4), (x, y), (x + 4, y + 4), (x + 1, y + 3), (x - 1, y + 4)], WIT, WIT)


def boom(dk, x, voet, r, rnd, kruin=GROEN, licht=LGROEN):
    """een ronde boom zoals op het plein: stam, drie bollen met een zwarte rand, lichtere toppen"""
    dk.rect(x - 1, voet - r, x + 1, voet, BRUIN)
    dk.px(x - 1, voet, ZWART)
    for dx, dy, rr in ((-r * 0.6, -r * 1.3, r * 0.8), (r * 0.6, -r * 1.3, r * 0.8), (0, -r * 2, r * 0.9)):
        cx, cy = x + dx, voet + dy
        dk.ovaal(cx - rr, cy - rr * 0.9, cx + rr, cy + rr * 0.9, kruin)
    for dx, dy, rr in ((-r * 0.6, -r * 1.3, r * 0.8), (0, -r * 2, r * 0.9)):     # kleine lichte plekjes
        cx, cy = x + dx, voet + dy
        dk.ovaal(cx - rr * 0.5, cy - rr * 0.6, cx - rr * 0.1, cy - rr * 0.3, licht, licht)


def heuvel_en_kasteel(dk):
    dk.poly([(0, 84), (0, 60), (10, 54), (52, 54), (62, 70), (70, 86)], GROEN)
    dk.lijn([(12, 56), (50, 56)], LGROEN)
    # de muur met kantelen
    dk.rect(12, 38, 48, 54, LGRIJS)
    dk.lijn([(12, 38), (12, 54)], ZWART)
    dk.lijn([(48, 38), (48, 54)], ZWART)
    for x in range(12, 49, 4):
        dk.rect(x, 35, x + 1, 37, LGRIJS)
        dk.px(x, 34, ZWART)
    for y in range(41, 54, 4):                                   # voegen
        dk.lijn([(13, y), (47, y)], GRIJS)
    # drie torens met spitse daken en vlaggetjes
    for x, top in ((10, 24), (26, 18), (42, 24)):
        dk.rect(x, top, x + 8, 54, LGRIJS)
        dk.lijn([(x, top), (x, 54)], ZWART)
        dk.lijn([(x + 8, top), (x + 8, 54)], ZWART)
        dk.poly([(x - 1, top), (x + 4, top - 10), (x + 9, top)], ROOD)
        dk.lijn([(x + 4, top - 10), (x + 4, top - 15)], ZWART)
        dk.poly([(x + 5, top - 15), (x + 9, top - 13), (x + 5, top - 11)], GEEL, GEEL)
        dk.rect(x + 3, top + 5, x + 5, top + 8, ZWART)
        dk.px(x + 4, top + 7, GEEL)
    dk.ovaal(26, 46, 34, 58, ZWART, ZWART)                       # de poort
    dk.rect(26, 52, 34, 54, ZWART)
    dk.lijn([(10, 54), (50, 54)], ZWART)


def huisje(dk, x, y, b, h, rnd):
    """een huisje uit Dawnhaven: stenen muur, rieten dak, schoorsteen met rook (x, y = linksonder)"""
    dk.rect(x, y - h, x + b, y, LGRIJS)
    dk.lijn([(x, y - h), (x, y)], ZWART)
    dk.lijn([(x + b, y - h), (x + b, y)], ZWART)
    for yy in range(y - h + 2, y, 3):
        for xx in range(x + 1 + (yy % 2) * 2, x + b, 4):
            dk.px(xx, yy, GRIJS)
    dk.poly([(x - 3, y - h), (x + b // 2, y - h - b // 2 - 2), (x + b + 3, y - h)], ORANJE)
    for i in range(2, b // 2, 3):                                # rietstrepen
        dk.lijn([(x + b // 2 - i, y - h - b // 2 + i), (x + b // 2 + i, y - h - b // 2 + i)], BRUIN)
    sx = x + b - 3                                               # schoorsteen en rook
    dk.rect(sx, y - h - b // 2 - 2, sx + 2, y - h - 2, GRIJS)
    dk.lijn([(sx, y - h - b // 2 - 3), (sx + 2, y - h - b // 2 - 3)], ZWART)
    for i in range(4):
        dk.ovaal(sx - i - 1, y - h - b // 2 - 7 - 4 * i, sx + 2 - i, y - h - b // 2 - 5 - 4 * i, LGRIJS, LGRIJS)
    dk.rect(x + 2, y - 5, x + 4, y, BRUIN)                      # deur
    dk.lijn([(x + 2, y - 6), (x + 4, y - 6)], ZWART)
    dk.rect(x + b - 5, y - 6, x + b - 3, y - 4, GEEL)           # raam met licht
    dk.lijn([(x - 1, y), (x + b + 1, y)], ZWART)


def kloof(dk, rnd):
    dk.poly([(112, 74), (124, 62), (159, 58), (159, 125), (104, 125)], GRIJS)
    for i, y in enumerate(range(68, 124, 7)):                    # rotslagen en barsten
        dk.lijn([(108 + i % 2 * 3, y + 6), (159, y)], DGRIJS)
        x = 142 + (i * 5) % 14
        dk.lijn([(x, y), (x + 2, y + 4)], ZWART)
    dk.lijn([(112, 74), (124, 62), (159, 58)], ZWART)
    dk.poly([(128, 66), (138, 63), (136, 80), (140, 96), (134, 125), (118, 125), (124, 100), (122, 82)], ZWART, ZWART)
    dk.lijn([(122, 82), (124, 100), (118, 125)], BRUIN)            # de rand van de kloof


def voorgrond(dk, rnd):
    dk.rect(0, 84, 111, 125, GROEN)
    dk.poly([(0, 84), (70, 86), (110, 80), (106, 125), (0, 125)], GROEN, GROEN)
    for _ in range(140):                                         # grasplukjes
        x, y = rnd.randint(0, 108), rnd.randint(86, 124)
        dk.px(x, y, LGROEN)
        dk.px(x, y - 1, LGROEN)
    # een houten hek langs de voet van de heuvel
    for x in range(2, 56, 6):
        dk.rect(x, 88 + x // 12, x + 1, 93 + x // 12, BRUIN)
        dk.px(x, 87 + x // 12, ZWART)
    dk.lijn([(0, 90), (56, 94)], BRUIN)
    # het pad van voren naar het dorp, slingerend
    dk.poly([(76, 98), (82, 98), (88, 106), (84, 114), (96, 125), (62, 125), (70, 114), (72, 106)], GEEL, ORANJE)
    for _ in range(26):
        dk.px(rnd.randint(68, 90), rnd.randint(104, 124), ORANJE)
    # struiken en bloemetjes vooraan
    for x, y, w in ((8, 114, 10), (26, 120, 8), (100, 120, 7)):
        dk.ovaal(x - w, y - 7, x + w, y + 7, GROEN)
        dk.ovaal(x - w // 2, y - 5, x - w // 4, y - 3, LGROEN, LGROEN)
    for _ in range(22):
        x, y = rnd.randint(4, 60), rnd.randint(96, 122)
        dk.px(x, y, rnd.choice((GEEL, ROOD, WIT)))


def teken():
    rnd = random.Random(5)
    dk = Doek()
    lucht(dk, rnd)
    zon(dk)
    bergen(dk)
    for x in range(56, 116, 8):                                  # bomen achter het dorp
        boom(dk, x + rnd.randint(-2, 2), 80, rnd.randint(5, 6), rnd, kruin=GROEN, licht=LGROEN)
    heuvel_en_kasteel(dk)
    for x, v, r in ((4, 66, 6), (60, 72, 5), (104, 80, 6)):
        boom(dk, x, v, r, rnd)
    voorgrond(dk, rnd)
    for x, y, b, h in ((60, 94, 12, 8), (78, 90, 12, 8), (92, 96, 12, 8), (68, 104, 14, 9)):
        huisje(dk, x, y, b, h, rnd)
    kloof(dk, rnd)
    for x, v, r in ((116, 72, 6), (152, 66, 6), (150, 98, 7)):
        boom(dk, x, v, r, rnd, kruin=GROEN, licht=LGROEN)
    dk.rect(0, 0, B - 1, 0, ZWART)                               # bovenste rij en onderste 2 rijen zwart
    dk.rect(0, 126, B - 1, 127, ZWART)
    return dk.im


def rgb(im, sx=4, sy=2):
    uit = Image.new("RGB", (B, H))
    uit.putdata([tuple(int(v) for v in cb.RGB[k]) for k in im.getdata()])
    return uit.resize((B * sx, H * sy), Image.NEAREST)


def te_veel_kleuren(im):
    fout = 0
    for cy in range(0, H, 8):
        for cx in range(0, B, 4):
            kl = {im.getpixel((x, y)) for x in range(cx, cx + 4) for y in range(cy, cy + 8)} - {ZWART}
            fout += len(kl) > 3
    return fout


def main():
    im = teken()
    rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", "toneel.png"))
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", "toneel_groot.png"))
    print("[toneel] data/plaatjes/toneel.png; vakjes met meer dan 3 kleuren + zwart: %d van %d"
          % (te_veel_kleuren(im), (B // 4) * (H // 8)))


if __name__ == "__main__":
    main()
