#!/usr/bin/env python3
"""teken_spookbrug.py — de spookbrug in het Duisterwoud (hoofdstuk 2), met de hand getekend als C64-pixelart.

    python3 tools/teken_spookbrug.py     schrijft data/plaatjes/spookbrug.png (640 x 256) en build/proef/spookbrug_groot.png

Scenario hoofdstuk 2: een touwbrug over een kloof, en aan het begin ervan staat de spookridder (een figuur, geen deel
van dit plaatje) die niemand overlaat. Links komt het pad uit het bospad binnen; de brug loopt naar rechts de mist in.
In de kloof: nevel, scherpe rotsen, ver beneden een beekje. Boven de kloof is het bladerdak open: de schemerlucht
met de maan erin.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import stam, bladerdak, kleuren_per_vakje   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLOOF = 64           # hier begint de kloof (kamer-x); de brug loopt van hier naar de rechterrand


def lucht(dk, rnd):
    dk.rect(0, 1, B - 1, 90, PAARS)
    for y in range(40, 90):                                     # naar onderen: de nevel uit de kloof
        for x in range(y % 2, B, 2):
            if rnd.random() < (y - 40) / 55:
                dk.px(x, y, BLAUW)
    dk.ovaal(112, 12, 128, 28, LGRIJS, LGRIJS)                  # de maan, half achter een wolk
    dk.ovaal(118, 14, 129, 26, PAARS, PAARS)
    dk.ovaal(112, 12, 128, 28, None, GRIJS)
    for x1, y, x2 in ((96, 24, 140), (104, 28, 150), (20, 18, 52)):   # wolkenslierten
        dk.lijn([(x1, y), (x2, y)], GRIJS)
        dk.lijn([(x1 + 6, y + 1), (x2 - 8, y + 1)], DGRIJS)


def overkant(dk, rnd):
    """de overkant van de kloof: een grillige rotswand met dennen, half in de mist"""
    top = golf(KLOOF + 26, B - 1, 60, 5, rnd, stap=3, freq=0.27)
    wand = [(KLOOF + 26, 92), (KLOOF + 24, 74), (KLOOF + 28, 66)] + top + [(B - 1, 92)]
    dk.poly(wand, DGRIJS, ZWART)
    for x in range(KLOOF + 32, B, 5):                            # rotsvlakken: schaduw rechts van elke rib
        y0 = 62 + rnd.randint(0, 4)
        dk.lijn([(x, y0), (x + rnd.randint(-2, 2), 90)], ZWART)
        dk.lijn([(x - 1, y0 + 2), (x - 1, y0 + 7)], GRIJS)
    for x in range(KLOOF + 30, B + 6, 7):                        # dennen als silhouet op de rand
        y = 61 + rnd.randint(-2, 2)
        h = rnd.randint(12, 22)
        dk.poly([(x, y - h), (x - 4, y - h // 2), (x - 2, y - h // 2), (x - 6, y + 2), (x + 6, y + 2),
                 (x + 2, y - h // 2), (x + 4, y - h // 2)], BLAUW, ZWART)


def kloof(dk, rnd):
    """de kloof: steile wanden, nevel, ver beneden een smalle beek"""
    dk.poly([(KLOOF, 126), (KLOOF, 84), (B - 1, 84), (B - 1, 126)], ZWART, ZWART)
    for y in range(84, 126):                                    # nevel die naar onderen verdwijnt
        dicht = max(0.0, 0.55 - (y - 84) * 0.02)
        for x in range(KLOOF + (y % 2), B, 2):
            if rnd.random() < dicht:
                dk.px(x, y, BLAUW)
    dk.lijn(golf(KLOOF + 20, B - 1, 120, 1.5, rnd, stap=3, freq=0.4), LBLAUW)   # de beek, ver beneden
    # de wand aan deze kant: rotsblokken, licht van links
    for x0, y0, x1, y1 in ((KLOOF - 8, 90, KLOOF + 6, 102), (KLOOF - 14, 100, KLOOF + 2, 112),
                           (KLOOF - 22, 110, KLOOF + 8, 126), (KLOOF - 2, 104, KLOOF + 10, 116)):
        dk.poly([(x0, y1), (x0 + 2, y0 + 2), (x0 + (x1 - x0) // 2, y0), (x1, y0 + 3), (x1 - 1, y1)], GRIJS)
        dk.lijn([(x0 + 2, y0 + 3), (x0 + 3, y1 - 1)], LGRIJS)
        dk.lijn([(x1 - 2, y0 + 4), (x1 - 2, y1 - 1)], DGRIJS)
    # rotspunten in de diepte
    for x, h in ((96, 14), (104, 9), (130, 16), (146, 10)):
        dk.poly([(x - 5, 126), (x, 126 - h), (x + 4, 126)], DGRIJS, ZWART)
        dk.lijn([(x, 126 - h), (x - 2, 124)], GRIJS)


def grond(dk, rnd):
    """deze kant: bosgrond met het pad uit het bospad"""
    rand = [(0, 82)] + golf(0, KLOOF - 4, 86, 2, rnd, stap=5) + [(KLOOF - 2, 92), (KLOOF - 30, 126), (0, 126)]
    dk.poly(rand, DGRIJS, DGRIJS)
    dither(dk, (0, 84, KLOOF, 126), GROEN, 0.55, rnd, DGRIJS)
    links = [(0, 100), (20, 98), (40, 96), (56, 94), (64, 93)]
    rechts = [(64, 99), (50, 104), (30, 110), (0, 114)]
    dk.poly(links + rechts, BRUIN, ZWART)                        # het pad naar de brug
    dk.poly([(0, 104), (24, 102), (46, 99), (62, 96), (62, 97), (40, 102), (0, 109)], ORANJE, ORANJE)
    for _ in range(20):
        x, y = rnd.randint(60, 62) - rnd.randint(0, 58), rnd.randint(86, 124)
        dk.lijn([(x, y), (x - 1, y - 3)], LGROEN)


def brug(dk):
    """de touwbrug: dikke palen, een doorhangende plankenvloer die naar rechts dunner wordt, touwen als leuning"""
    def doorhang(x1, y1, x2, y2, zak, n=48):
        return [(x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n + zak * math.sin(math.pi * i / n)) for i in range(n + 1)]
    vloer = doorhang(KLOOF - 2, 94, B + 4, 72, 10)
    voor = doorhang(KLOOF + 8, 74, B + 4, 58, 7)                 # leuning aan de voorkant
    achter = doorhang(KLOOF - 4, 70, B + 4, 54, 7)               # leuning aan de achterkant
    dk.lijn(achter, GRIJS)
    for j in range(2, len(achter), 3):                           # touwtjes van de achterleuning naar de vloer
        lx, ly = achter[j]
        vx, vy = vloer[j]
        dk.lijn([(lx, ly), (vx, vy - 1)], DGRIJS)
    for i in range(len(vloer) - 1):                              # de planken: dik vooraan, dun achteraan
        x, y = vloer[i]
        dik = max(2, round(6 - i * 0.09))
        dk.rect(x, y - dik, x + 2, y, BRUIN)
        dk.lijn([(x, y - dik), (x + 2, y - dik)], ORANJE)
        if i % 2:
            dk.lijn([(x + 2, y - dik), (x + 2, y)], ZWART)
    dk.lijn([(x, y + 1) for x, y in vloer], ZWART)
    for j in range(1, len(voor), 3):                             # touwtjes van de voorleuning naar de vloer
        lx, ly = voor[j]
        vx, vy = min(vloer, key=lambda p: abs(p[0] - lx))
        dk.lijn([(lx, ly), (vx, vy)], GRIJS)
    dk.lijn(voor, LGRIJS)
    for px, top, voet in ((KLOOF - 6, 66, 96), (KLOOF + 8, 70, 100)):   # de palen aan deze kant
        dk.rect(px - 2, top, px + 2, voet, BRUIN)
        dk.lijn([(px - 2, top), (px - 2, voet)], ZWART)
        dk.lijn([(px + 2, top), (px + 2, voet)], ZWART)
        dk.lijn([(px + 1, top + 1), (px + 1, voet - 1)], DGRIJS)
        dk.rect(px - 2, top - 1, px + 2, top, ORANJE)
        dk.lijn([(px - 2, top - 1), (px + 2, top - 1)], ZWART)
        dk.lijn([(px - 2, top + 4), (px + 2, top + 5)], LGRIJS)  # touw om de paal


def spinrag(dk):
    """spinnenweb tussen de stam en de paal: het is een spookbrug"""
    cx, cy = 40, 60
    for a in range(0, 360, 45):
        r = math.radians(a)
        dk.lijn([(cx, cy), (cx + 9 * math.cos(r), cy + 7 * math.sin(r))], LGRIJS)
    for rr in (3, 6, 9):
        pts = [(cx + rr * math.cos(math.radians(a)), cy + rr * 0.78 * math.sin(math.radians(a))) for a in range(0, 361, 45)]
        dk.lijn(pts, GRIJS)


def harnas(dk, helm):
    """het harnas in stukken op de rotsen (na de honing): borstplaat, een handschoen, een scheen, en de helm"""
    dk.poly([(28, 108), (30, 102), (38, 101), (40, 107), (35, 110)], LGRIJS, ZWART)   # borstplaat, op zijn kant
    dk.lijn([(31, 104), (37, 103)], GRIJS)
    dk.lijn([(33, 106), (38, 105)], GRIJS)
    dk.poly([(40, 110), (42, 108), (45, 109), (44, 111)], GRIJS, ZWART)               # een handschoen
    dk.rect(26, 110, 31, 111, GRIJS)                                                   # een scheen
    dk.lijn([(26, 109), (31, 109)], ZWART)
    if helm:
        dk.ovaal(34, 96, 42, 103, LGRIJS, ZWART)                                       # de helm
        dk.lijn([(35, 99), (41, 99)], ZWART)                                           # het vizier
        dk.px(38, 96, GRIJS)


def pot(dk, kever):
    """de honingpot die Eldric neerzette, met (nog) het kevertje erop"""
    dk.poly([(15, 110), (14, 104), (16, 101), (20, 101), (22, 104), (21, 110)], LGRIJS, ZWART)
    dk.lijn([(16, 101), (20, 101)], GRIJS)
    dk.lijn([(17, 102), (19, 102)], GEEL)                                              # de honing
    dk.px(15, 105, GRIJS)
    if kever:
        dk.ovaal(17, 98, 20, 101, ZWART, ZWART)                                        # het kevertje
        dk.px(18, 99, GEEL)
        dk.px(16, 98, ZWART)
        dk.px(21, 98, ZWART)


def teken(stukken=None):
    rnd = random.Random(33)
    dk = Doek()
    lucht(dk, rnd)
    overkant(dk, rnd)
    grond(dk, rnd)
    kloof(dk, rnd)
    stam(dk, 14, 8, 2, 90, rnd, takken=((32, 18, 1),))
    stam(dk, 50, 4, 20, 86, rnd, takken=((40, 10, -1),))
    brug(dk)
    rnd2 = random.Random(5)
    bladerdak(dk, rnd2)
    dk.rect(KLOOF + 20, 0, B - 1, 0, ZWART)
    for x in range(KLOOF + 16, B):                               # boven de kloof is het dak open: haal het weg
        for y in range(1, 20):
            if dk.im.getpixel((x, y)) in (ZWART, GROEN, LGROEN) and y > 1 + (B - x) // 14:
                dk.px(x, y, PAARS)
    dk.ovaal(112, 12, 128, 28, LGRIJS, LGRIJS)                  # de maan opnieuw (het dak lag eroverheen)
    dk.ovaal(118, 14, 129, 26, PAARS, PAARS)
    dk.lijn([(96, 24), (140, 24)], GRIJS)
    if stukken:
        stukken(dk)
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    kleuren_per_vakje(dk.im)
    return dk.im


PATCHES = {                       # naam: tekening (de vakken staan in data/kamers.txt)
    "spookbrug_harnas_helm": lambda dk: harnas(dk, True),
    "spookbrug_harnas": lambda dk: harnas(dk, False),
    "spookbrug_pot_kever": lambda dk: pot(dk, True),
}


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    for naam, f in [("spookbrug", None)] + list(PATCHES.items()):
        im = teken(f)
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        print("[spookbrug] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))
    alles = teken(lambda dk: (harnas(dk, True), pot(dk, True)))
    rgb(alles, 8, 4).save(os.path.join(WORTEL, "build", "proef", "spookbrug_stukken_groot.png"))


if __name__ == "__main__":
    main()
