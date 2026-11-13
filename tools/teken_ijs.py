#!/usr/bin/env python3
"""teken_ijs.py — de IJstop (hoofdstuk 5): de plaatjes van dat hoofdstuk, met de hand getekend als C64-pixelart.

    python3 tools/teken_ijs.py [naam ...]   schrijft data/plaatjes/<naam>.png (en patches), build/proef/<naam>_groot.png

  bergpad   een besneeuwd bergpad in de nacht; boven het pad hangt een sneeuwveld (patch lawine: het is gevallen)
  hut       de hut van Oma Rijm: een warme haard, een raam met sneeuw, een tafel met haar boek, Oma in haar schommelstoel
  ijsbrug   een gebarsten brug van ijs over een kloof; diep beneden de rijmwurm (patch wurm_weg: hij dook weg)
  baken     het zonnebaken op de top: een oude toren van spiegels met een lege houder (patch baken_aan: het brandt);
            hier staat de zwarte zon het dichtst bij, met een felle stralenkrans
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import kleuren_per_vakje   # noqa: E402
from teken_zee import nachtlucht, verduisterde_zon, rand   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sneeuw(dk, rnd, n, y1, y2):
    for _ in range(n):
        x, y = rnd.randint(0, B - 1), rnd.randint(y1, y2)
        if dk.im.getpixel((x, y)) in (PAARS, BLAUW):
            dk.px(x, y, WIT)


def berg(dk, pts, licht=WIT, schaduw=LBLAUW, rots=DGRIJS):
    """een besneeuwde berg: wit, de schaduwkant lichtblauw, onderaan rots"""
    dk.poly(pts, licht, ZWART)
    top = min(pts, key=lambda p: p[1])
    rechts = [p for p in pts if p[0] >= top[0]]
    dk.poly([top] + rechts[1:] + [(top[0] + 2, max(p[1] for p in pts))], schaduw, None)
    dk.lijn(pts, ZWART)


# ---- het bergpad --------------------------------------------------------------------------------------------------
LAWINE = (100, 32, 48, 64)       # patch lawine: het sneeuwveld is gevallen (uitgepakt 960 bytes)


def bergpad(gevallen=False):
    rnd = random.Random(131)
    dk = Doek()
    nachtlucht(dk, rnd, 70)
    verduisterde_zon(dk, 30, 16, 6)
    berg(dk, [(0, 70), (30, 30), (52, 50), (70, 26), (96, 60), (110, 70)])
    dk.poly([(0, 68), (110, 68), (110, 100), (0, 100)], WIT, None)   # een besneeuwde vlakte achter het pad
    for y in range(70, 100, 4):
        dk.lijn([(rnd.randint(0, 20), y), (rnd.randint(40, 100), y)], LBLAUW)
    # de helling rechts: rots met bovenaan het overhangende sneeuwveld
    dk.poly([(80, 126), (96, 40), (130, 18), (159, 10), (159, 126)], DGRIJS, ZWART)
    for _ in range(30):
        x, y = rnd.randint(100, 156), rnd.randint(30, 120)
        if dk.im.getpixel((x, y)) == DGRIJS:
            dk.lijn([(x, y), (x + 3, y + 2)], GRIJS)
    if not gevallen:
        dk.poly([(102, 52), (112, 38), (130, 34), (146, 40), (144, 56), (136, 62), (120, 64), (106, 62)], WIT, ZWART)
        dk.lijn([(108, 58), (120, 60), (138, 56)], LBLAUW)        # de onderkant, in de schaduw
        dk.lijn([(110, 46), (118, 50), (126, 48), (134, 52)], LGRIJS)   # een barst: het hangt
        for x in (110, 122, 134):
            dk.lijn([(x, 62), (x, 66)], LBLAUW)                   # ijspegels
    else:
        dk.poly([(104, 92), (110, 82), (124, 78), (140, 82), (146, 92)], WIT, ZWART)   # de berg sneeuw naast het pad
        dk.lijn([(108, 90), (142, 90)], LBLAUW)
        for x, y in ((116, 76), (132, 74), (126, 70)):
            dk.ovaal(x - 2, y - 1, x + 2, y + 1, WIT, ZWART)
    # het pad: van linksonder schuin omhoog naar rechts, onder het sneeuwveld door
    dk.poly([(0, 126), (0, 100), (40, 96), (80, 92), (110, 84), (159, 76), (159, 90), (120, 98), (84, 108), (40, 116),
             (20, 126)], LGRIJS, ZWART)
    for _ in range(40):
        x, y = rnd.randint(0, 158), rnd.randint(78, 124)
        if dk.im.getpixel((x, y)) == LGRIJS:
            dk.px(x, y, WIT)
    dk.poly([(0, 126), (20, 126), (40, 116), (84, 108), (120, 98), (159, 90), (159, 126)], WIT, ZWART)   # sneeuw vooraan
    for x in range(4, 80, 9):                                    # voetstappen in de sneeuw (van Oma?)
        dk.px(x, 106 - x // 10, GRIJS)
    sneeuw(dk, rnd, 40, 2, 68)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de hut van Oma Rijm -------------------------------------------------------------------------------------------
def hut():
    rnd = random.Random(141)
    dk = Doek()
    dk.rect(0, 1, B - 1, 9, BRUIN)                               # balken
    dk.lijn([(0, 9), (B - 1, 9)], ZWART)
    for y in range(10, 82, 8):                                   # een wand van planken, warm van de haard
        dk.rect(0, y, B - 1, y + 7, ORANJE if y < 50 else BRUIN)
        dk.lijn([(0, y + 7), (B - 1, y + 7)], ZWART)
    for x in range(12, B, 26):
        dk.lijn([(x, 10), (x, 81)], BRUIN)
    # een raam met sneeuw en de nacht
    dk.rect(18, 20, 46, 46, ZWART)
    dk.rect(19, 21, 45, 45, PAARS)
    dk.lijn([(32, 21), (32, 45)], ZWART)
    dk.lijn([(19, 33), (45, 33)], ZWART)
    for _ in range(14):
        dk.px(rnd.randint(20, 44), rnd.randint(22, 44), WIT)
    dk.rect(19, 42, 45, 45, WIT)                                 # sneeuw op de vensterbank
    # de haard rechts met een vuur (FLAKKER in scripts/hut.hcs)
    dk.poly([(104, 81), (106, 24), (140, 24), (142, 81)], GRIJS, ZWART)
    for y in range(28, 81, 6):
        dk.lijn([(105, y), (141, y)], DGRIJS)
    dk.rect(112, 56, 134, 80, ZWART)
    for x0, top in ((116, 64), (120, 60), (124, 58), (128, 61), (131, 66)):
        dk.poly([(x0 - 3, 78), (x0, top), (x0 + 3, 78)], ROOD, ROOD)
        dk.poly([(x0 - 2, 78), (x0, top + 4), (x0 + 2, 78)], ORANJE, ORANJE)
        dk.poly([(x0 - 1, 78), (x0, top + 8), (x0 + 1, 78)], GEEL, GEEL)
    dk.rect(102, 50, 144, 53, BRUIN)                             # de schoorsteenmantel
    dk.lijn([(102, 50), (144, 50)], ZWART)
    dk.ovaal(110, 42, 118, 50, LBLAUW, ZWART)                    # een kruikje en een kaars op de mantel
    dk.rect(130, 42, 132, 50, WIT)
    dk.px(131, 41, GEEL)
    # de vloer
    dk.rect(0, 82, B - 1, 125, BRUIN)
    for y in range(88, 126, 6):
        dk.lijn([(0, y), (B - 1, y)], DGRIJS)
    dk.ovaal(60, 104, 124, 120, ROOD, ZWART)                     # een kleed
    dk.ovaal(66, 106, 118, 118, ORANJE, ROOD)
    # de tafel met het boek van Oma
    dk.rect(20, 92, 24, 108, BRUIN)
    dk.rect(48, 92, 52, 108, BRUIN)
    dk.poly([(14, 92), (18, 86), (54, 86), (58, 92)], ORANJE, ZWART)
    dk.rect(14, 92, 58, 95, BRUIN)
    dk.lijn([(14, 95), (58, 95)], ZWART)
    dk.poly([(26, 88), (34, 86), (42, 88), (42, 90), (34, 89), (26, 90)], WIT, ZWART)   # het boek, open
    dk.lijn([(34, 86), (34, 89)], GRIJS)
    # Oma Rijm in haar schommelstoel, naast de haard
    ox, oy = 90, 104
    dk.lijn([(ox - 12, oy + 4), (ox + 8, oy + 6)], BRUIN, 2)     # de schommelpoten
    dk.poly([(ox + 4, oy), (ox + 6, oy - 30), (ox + 10, oy - 30), (ox + 9, oy)], BRUIN, ZWART)   # de rugleuning
    dk.poly([(ox - 8, oy), (ox - 7, oy - 18), (ox + 5, oy - 18), (ox + 6, oy)], PAARS, ZWART)  # haar jurk
    dk.poly([(ox - 9, oy - 14), (ox - 2, oy - 20), (ox + 6, oy - 14), (ox + 4, oy - 10), (ox - 7, oy - 10)],
            ROZE, ZWART)                                                                     # een omslagdoek
    dk.ovaal(ox - 5, oy - 28, ox + 3, oy - 19, ROZE, ZWART)       # het gezicht
    dk.ovaal(ox - 6, oy - 31, ox + 4, oy - 25, LGRIJS, ZWART)     # grijs haar, een knotje
    dk.ovaal(ox - 2, oy - 34, ox + 2, oy - 30, LGRIJS, ZWART)
    dk.lijn([(ox - 4, oy - 24), (ox - 2, oy - 24)], ZWART)       # een brilletje
    dk.lijn([(ox, oy - 24), (ox + 2, oy - 24)], ZWART)
    dk.lijn([(ox - 8, oy - 8), (ox - 2, oy - 6)], GEEL)          # breiwerk
    # deuren: links terug naar het pad, rechts verder naar de ijsbrug
    for x0, x1 in ((2, 14), (146, 158)):
        dk.rect(x0, 40, x1, 81, DGRIJS)
        dk.lijn([(x0, 40), (x0, 81)], ZWART)
        dk.lijn([(x1, 40), (x1, 81)], ZWART)
        dk.lijn([(x0, 40), (x1, 40)], ZWART)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de ijsbrug ---------------------------------------------------------------------------------------------------
WURM = (40, 88, 80, 32)          # patch wurm_weg: de rijmwurm is de diepte in gedoken (uitgepakt 800 bytes)


def ijsbrug(wurm=True):
    rnd = random.Random(151)
    dk = Doek()
    nachtlucht(dk, rnd, 40)
    verduisterde_zon(dk, 130, 14, 6)
    # twee ijswanden met een kloof ertussen
    berg(dk, [(0, 126), (0, 40), (20, 30), (36, 48), (44, 126)], licht=LBLAUW, schaduw=BLAUW)
    berg(dk, [(116, 126), (122, 50), (140, 34), (159, 44), (159, 126)], licht=LBLAUW, schaduw=BLAUW)
    dk.rect(44, 41, 115, 125, ZWART)
    for y in range(41, 126):                                     # de kloof: donkerblauw naar zwart
        for x in range(44 + (y % 2), 116, 2):
            if rnd.random() < max(0.0, 0.5 - (y - 40) / 120):
                dk.px(x, y, BLAUW)
    if wurm:                                                     # de rijmwurm, opgerold in de diepte
        for i in range(9):
            a = i * 0.7
            x, y = 80 + 26 * math.cos(a) * (1 - i * 0.06), 106 + 9 * math.sin(a)
            dk.ovaal(x - 7, y - 6, x + 7, y + 6, ROZE, ZWART)
            dk.lijn([(x - 4, y - 4), (x + 4, y - 4)], WIT)
            dk.lijn([(x - 6, y + 2), (x + 6, y + 2)], BRUIN)      # ringen
        dk.ovaal(94, 90, 114, 106, ROZE, ZWART)                  # de kop
        dk.rect(100, 96, 102, 97, ROOD)                          # oogjes: hij slaapt licht
        dk.rect(106, 96, 108, 97, ROOD)
        dk.lijn([(99, 101), (109, 101)], ZWART)
    # de brug van ijs: dun, gebarsten
    dk.poly([(36, 84), (124, 80), (124, 86), (36, 90)], WIT, ZWART)
    dk.lijn([(36, 89), (124, 85)], LBLAUW)
    for x, y in ((60, 83), (82, 82), (100, 81)):                 # barsten
        dk.lijn([(x, y), (x + 3, y + 3), (x + 1, y + 6)], ZWART)
    for x in range(44, 120, 9):                                  # ijspegels onder de brug
        y = 89 - (x - 36) * 4 // 88
        dk.poly([(x - 1, y), (x + 1, y), (x, y + rnd.randint(3, 7))], LBLAUW, None)
    # de grond aan weerszijden, waar je staat
    dk.poly([(0, 126), (0, 94), (40, 92), (44, 126)], WIT, ZWART)
    dk.poly([(116, 126), (120, 88), (159, 86), (159, 126)], WIT, ZWART)
    for x, y in ((10, 110), (24, 120), (132, 104), (146, 116)):
        dk.lijn([(x, y), (x + 4, y)], LBLAUW)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- het zonnebaken -----------------------------------------------------------------------------------------------
BAKEN = (56, 0, 48, 64)          # patch baken_aan: het kristal brandt, een bundel naar boven (uitgepakt 960 bytes)


def baken(aan=False):
    rnd = random.Random(161)
    dk = Doek()
    nachtlucht(dk, rnd, 80)
    dk.ovaal(112, 4, 152, 34, GEEL, GEEL)                        # de zwarte zon, dichtbij, met een felle krans
    dk.ovaal(116, 7, 148, 31, WIT, WIT)
    dk.ovaal(119, 9, 145, 29, ZWART, ZWART)
    dk.ovaal(117, 11, 133, 27, DGRIJS, ZWART)                    # de twee manen ervoor
    dk.ovaal(131, 11, 147, 27, DGRIJS, ZWART)
    # wolken onder de top: de schemer ligt beneden
    dk.rect(0, 72, B - 1, 96, GRIJS)                             # een wolkendek: de schemer ligt beneden
    for y in range(72, 96, 3):
        for x in range(rnd.randint(0, 6), B, 9):
            dk.lijn([(x, y), (x + 5, y)], LGRIJS)
    dk.lijn(golf(0, B - 1, 72, 2, rnd, stap=6), LGRIJS)
    # het platform van de top
    dk.poly([(0, 126), (0, 98), (30, 94), (130, 94), (159, 98), (159, 126)], LGRIJS, ZWART)
    for x in range(10, 150, 16):
        dk.lijn([(x, 96), (x - 4, 125)], GRIJS)
    dk.rect(0, 112, B - 1, 125, WIT)                             # sneeuw vooraan
    dk.lijn([(0, 112), (B - 1, 112)], LGRIJS)
    # de toren van spiegels: een stenen voet, een frame, vier ronde spiegels, de houder in het midden
    dk.poly([(66, 96), (68, 64), (92, 64), (94, 96)], GRIJS, ZWART)
    dk.lijn([(70, 66), (69, 94)], LGRIJS)
    dk.rect(62, 60, 98, 64, DGRIJS)
    dk.lijn([(62, 60), (98, 60)], ZWART)
    dk.lijn([(80, 60), (80, 16)], DGRIJS, 2)
    for (mx, my) in ((64, 30), (96, 30), (64, 50), (96, 50)):
        dk.lijn([(80, my), (mx, my)], DGRIJS)
        r = 7
        dk.ovaal(mx - r, my - r + 1, mx + r, my + r - 1, LBLAUW if not aan else WIT, ZWART)
        dk.lijn([(mx - 3, my - 3), (mx, my - 4)], WIT)
    dk.ovaal(74, 34, 86, 46, DGRIJS, ZWART)                      # de houder
    if aan:
        dk.ovaal(76, 36, 84, 44, WIT, GEEL)                      # het bakenkristal brandt
        dk.rect(78, 0, 82, 35, WIT)                              # een witte bundel, de hemel in
        dk.lijn([(77, 0), (77, 35)], GEEL)
        dk.lijn([(83, 0), (83, 35)], GEEL)
    else:
        dk.ovaal(77, 37, 83, 43, ZWART, ZWART)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


PLAATJES = {"bergpad": bergpad, "bergpad_lawine": lambda: bergpad(True), "hut": hut,
            "ijsbrug": ijsbrug, "ijsbrug_leeg": lambda: ijsbrug(False),
            "baken": baken, "baken_aan": lambda: baken(True)}
PATCHES = {"bergpad_lawine": ("bergpad", LAWINE), "ijsbrug_leeg": ("ijsbrug", WURM), "baken_aan": ("baken", BAKEN)}


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    namen = sys.argv[1:] or list(PLAATJES)
    gemaakt = {}
    for naam in namen:
        im = gemaakt[naam] = PLAATJES[naam]()
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[ijs] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))
        if naam in PATCHES:
            basis_naam, (px, py, pb, ph) = PATCHES[naam]
            basis = gemaakt.get(basis_naam) or PLAATJES[basis_naam]()
            buiten = sum(1 for y in range(H) for x in range(B) if basis.getpixel((x, y)) != im.getpixel((x, y))
                         and not (px <= x < px + pb and py <= y < py + ph))
            if buiten or px % 4 or pb % 4 or py % 8 or ph % 8 or (pb // 4) * (ph // 8) * 10 > 1024:
                raise SystemExit("[ijs] patch %s: %d pixels buiten het vak %s (of een vak niet op vakjes, of te groot)"
                                 % (naam, buiten, (px, py, pb, ph)))


if __name__ == "__main__":
    main()
