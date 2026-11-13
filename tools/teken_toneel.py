#!/usr/bin/env python3
"""teken_toneel.py — het toneel van de verhaalanimatie, met de hand getekend als C64-pixelart (geen FLUX).

    python3 tools/teken_toneel.py            schrijft data/plaatjes/toneel.png (640 x 256) en build/proef/toneel_*.png

Rechtstreeks in kamerpixels (160 x 128, multicolor: elke pixel 2 breed) en alleen C64-kleuren, met dikke zwarte
lijnen zoals het plein. Per vakje van 4 x 8 mogen er 3 kleuren + zwart zijn: het script telt de vakjes met te veel
kleuren (die kiest de omzetter dan zelf), zodat je ziet waar het plaatje op de C64 anders wordt.

Het toneel: Aethermoor onder de zon. Links een bos en een molentje op de heuvels, in het dal Dawnhaven met scheve
huisjes, rieten daken en rokende schoorstenen, rechts de rotsige berg van Grom met een donkere grot (daar komen de
aardmannetjes uit). De zon staat midden in de lucht: daar schuiven de manen
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
    dk.ovaal(cx - 9, cy - 9, cx + 9, cy + 9, GEEL, ORANJE)       # helemaal gevuld (geen wit gat in het midden)
    for x, y in ((cx + 4, cy + 6), (cx + 5, cy + 5), (cx + 6, cy + 4), (cx + 3, cy + 7), (cx + 7, cy + 2)):
        dk.px(x, y, ORANJE)                                      # schaduw rechtsonder: hij is rond
    dk.rect(cx - 5, cy - 6, cx - 3, cy - 5, WIT)                 # een klein glimlicht linksboven
    dk.px(cx - 6, cy - 4, WIT)


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
    # de poort: een boog die netjes op de voet van de muur eindigt, met houten deuren en ijzeren nagels
    dk.ovaal(25, 43, 35, 51, ZWART, ZWART)
    dk.rect(25, 47, 35, 54, ZWART)
    dk.ovaal(26, 44, 34, 50, BRUIN, BRUIN)
    dk.rect(26, 47, 34, 53, BRUIN)
    dk.lijn([(30, 45), (30, 53)], ZWART)                         # de naad tussen de deuren
    for x in (27, 33):
        for y in (48, 51):
            dk.px(x, y, DGRIJS)
    dk.lijn([(10, 54), (50, 54)], ZWART)
    # een pad van de poort de heuvel af
    dk.poly([(27, 55), (33, 55), (40, 70), (46, 86), (36, 86), (30, 70)], GEEL, ORANJE)


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


# ---- het toneel van het verhaal (na de opmerkingen: minder klinisch, geen recht kasteel, Groms berg met een grot) ----
import math


def golf(x1, x2, y, amp, rnd, stap=3, fase=0.0, freq=0.15):
    """een organische lijn: punten van x1 tot x2 rond hoogte y (een golf met wat toeval)"""
    return [(x, y + amp * math.sin(fase + x * freq) + rnd.uniform(-amp / 3, amp / 3)) for x in range(x1, x2 + 1, stap)]


def dither(dk, pts_vlak, kleur, dicht, rnd, vlak):
    """een lichtere vlek in een vlak: om en om pixels (de C64-manier van verlopen)"""
    x1, y1, x2, y2 = pts_vlak
    for y in range(y1, y2):
        for x in range(x1 + (y % 2), x2, 2):
            if dk.im.getpixel((x, y)) == vlak and rnd.random() < dicht:
                dk.px(x, y, kleur)


def verre_bergen(dk, rnd):
    pts = [(0, 76)] + golf(0, 159, 50, 7, rnd, stap=4, freq=0.09) + [(159, 76)]
    dk.poly(pts, GRIJS, DGRIJS)
    for x, y in pts[1:-1:5]:                                     # lichte flanken (licht van links)
        dk.lijn([(x, y + 2), (x - 6, y + 14)], LGRIJS)


def bos_links(dk, rnd):
    """een bos op de heuvels links: ronde kruinen, achteraan donker, vooraan lichter"""
    dk.poly([(0, 92)] + golf(0, 64, 64, 4, rnd, stap=4, freq=0.12) + [(64, 92)], GROEN, GROEN)
    for rij, (y, r) in enumerate(((60, 5), (66, 6), (72, 6))):
        for x in range(-2, 60, 8 + rij):
            xx, rr = x + rnd.randint(-2, 2), r + rnd.randint(-1, 1)
            dk.ovaal(xx - rr, y - rr, xx + rr, y + rr * 0.8, GROEN)
            dk.ovaal(xx - rr * 0.6, y - rr * 0.8, xx, y - rr * 0.2, LGROEN, LGROEN)
    # een molentje op de heuvel
    mx, my = 30, 58
    dk.poly([(mx - 4, my), (mx - 3, my - 14), (mx + 3, my - 14), (mx + 4, my)], LGRIJS)
    dk.poly([(mx - 4, my - 14), (mx, my - 19), (mx + 4, my - 14)], BRUIN)
    dk.rect(mx - 1, my - 5, mx + 1, my, BRUIN)
    for a in (0.6, 2.17, 3.74, 5.31):                            # de wieken, een beetje scheef
        ex, ey = mx + 12 * math.cos(a), my - 14 + 10 * math.sin(a)
        dk.lijn([(mx, my - 14), (ex, ey)], BRUIN)
        dk.lijn([(mx + (ex - mx) * 0.4, my - 14 + (ey - my + 14) * 0.4), (ex, ey)], LGRIJS)


def groms_berg(dk, rnd):
    """de berg van Grom, rechts: rotsvlakken (licht links, schaduw rechts), barsten, een donkere grot met oogjes"""
    rand = [(98, 104), (106, 84), (112, 68), (118, 52), (124, 42), (130, 32), (136, 26), (142, 31), (148, 27),
            (154, 35), (159, 39), (159, 106)]
    dk.poly(rand, GRIJS)
    # rotsvlakken: een schaduwkant rechts van de top, en lichte vlakken aan de linkerflank
    dk.poly([(136, 27), (142, 32), (148, 28), (154, 36), (159, 40), (159, 104), (146, 104), (144, 84), (140, 60)],
            DGRIJS, DGRIJS)
    for pts in ([(118, 53), (124, 43), (127, 46), (121, 60), (116, 62)],
                [(108, 82), (112, 69), (116, 66), (113, 80)],
                [(126, 40), (131, 33), (134, 36), (128, 48)]):
        dk.poly(pts, LGRIJS, LGRIJS)
    dk.lijn(rand[:-1], ZWART)                                    # de rand van de berg
    for x, y, lx, ly in ((128, 50, 3, 6), (150, 50, -2, 7), (118, 76, 2, 5), (152, 80, 2, 6), (134, 92, -3, 5)):
        dk.lijn([(x, y), (x + lx, y + ly), (x + lx + 2, y + ly + 3)], ZWART)
    for x, y in ((114, 84), (150, 66), (156, 92)):              # een paar bergdennen
        dk.poly([(x - 3, y), (x, y - 9), (x + 3, y)], GROEN, ZWART)
        dk.lijn([(x, y - 6), (x - 1, y - 2)], LGROEN)
    # de grot: een donkere, onregelmatige mond
    mond = [(124, 84), (123, 74), (126, 66), (131, 62), (137, 63), (141, 68), (142, 76), (141, 84)]
    dk.poly(mond, ZWART, DGRIJS)
    for x, y in ((129, 72), (132, 72), (135, 78), (138, 78)):    # oogjes in het donker
        dk.px(x, y, ROOD)


def scheef_huisje(dk, x, y, b, h, hel, rnd):
    """een huisje uit Dawnhaven, een beetje scheef: vakwerk, rieten dak, rook, een warm raampje (x, y = linksonder)"""
    dk.poly([(x, y), (x + hel, y - h), (x + b + hel, y - h), (x + b, y)], LGRIJS)
    dk.lijn([(x + b // 2, y), (x + b // 2 + hel, y - h)], BRUIN)          # vakwerk
    dk.lijn([(x, y - h // 2), (x + b, y - h // 2)], BRUIN)
    top = (x + b // 2 + hel + rnd.randint(-1, 1), y - h - b // 2 - 3)
    dk.poly([(x - 3 + hel, y - h + 1), top, (x + b + 3 + hel, y - h + 1)], ORANJE)
    for i in range(2, b // 2 + 2, 2):                           # het riet
        dk.lijn([(top[0] - i, top[1] + i + 1), (top[0] + i, top[1] + i + 1)], BRUIN if i % 4 else ORANJE)
    sx = x + b - 3 + hel
    dk.rect(sx, y - h - 6, sx + 2, y - h - 1, DGRIJS)
    for i in range(4):
        dk.ovaal(sx - i - 1, y - h - 11 - 4 * i, sx + 2 - i + i // 2, y - h - 9 - 4 * i, LGRIJS, LGRIJS)
    dk.rect(x + 2, y - 5, x + 4, y - 1, BRUIN)
    dk.rect(x + b - 5, y - 6, x + b - 3, y - 4, GEEL)


def dorp(dk, rnd):
    for x in range(44, 106, 7):                                  # bomen achter het dorp
        boom(dk, x + rnd.randint(-2, 2), 82, rnd.randint(4, 6), rnd)
    for x, y, b, h, hel in ((48, 92, 12, 8, 1), (64, 88, 12, 8, -1), (80, 94, 13, 8, 1), (95, 90, 11, 7, 0),
                            (58, 102, 14, 9, -1)):
        scheef_huisje(dk, x, y, b, h, hel, rnd)


def weide(dk, rnd):
    dk.poly([(0, 92)] + golf(0, 159, 92, 2, rnd, stap=8) + [(159, 106), (159, 126), (0, 126)], GROEN, GROEN)
    dk.poly([(100, 104), (130, 100), (159, 104), (159, 110), (100, 110)], GROEN, GROEN)   # het gras aan de voet van de berg
    dither(dk, (0, 96, 159, 126), LGROEN, 0.3, rnd, GROEN)       # licht op het gras
    # het pad: slingert van voren naar het dorp
    links = [(72, 102), (70, 108), (66, 114), (68, 120), (74, 126)]
    rechts = [(80, 102), (82, 108), (80, 114), (86, 120), (94, 126)]
    dk.poly(links + rechts[::-1], GEEL, ORANJE)
    for _ in range(30):
        dk.px(rnd.randint(68, 90), rnd.randint(104, 125), ORANJE)
    # een scheef hekje, struiken, bloemen en steentjes
    for i, x in enumerate(range(4, 50, 7)):
        y = 98 + i % 2
        dk.rect(x, y, x + 1, y + 5 + i % 3, BRUIN)
    dk.lijn([(3, 100), (50, 101)], BRUIN)
    for x, y, w in ((8, 116, 9), (26, 121, 7), (100, 119, 7), (44, 124, 6)):
        dk.ovaal(x - w, y - 6, x + w, y + 6, GROEN)
        dk.ovaal(x - w // 2, y - 5, x - w // 4, y - 2, LGROEN, LGROEN)
    for _ in range(26):
        x, y = rnd.randint(2, 104), rnd.randint(98, 124)
        if dk.im.getpixel((x, y)) in (GROEN, LGROEN):
            dk.px(x, y, rnd.choice((GEEL, ROOD, WIT, GEEL)))


def teken():
    rnd = random.Random(8)
    dk = Doek()
    lucht(dk, rnd)
    zon(dk)
    verre_bergen(dk, rnd)
    bos_links(dk, rnd)
    groms_berg(dk, rnd)
    weide(dk, rnd)
    dorp(dk, rnd)
    for x, v, r in ((108, 104, 6), (4, 86, 6)):                  # een paar bomen vooraan
        boom(dk, x, v, r, rnd)
    dk.rect(0, 0, B - 1, 0, ZWART)
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
