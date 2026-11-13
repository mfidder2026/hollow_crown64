#!/usr/bin/env python3
"""teken_kloof.py — de Rotskloof (hoofdstuk 4): de plaatjes van dat hoofdstuk, met de hand getekend als C64-pixelart.

    python3 tools/teken_kloof.py [naam ...]   schrijft data/plaatjes/<naam>.png (en patches), build/proef/<naam>_groot.png

  kloof      de ingang van de kloof: steile rotswanden, een smalle reep schemerhemel, de zwarte mond van de grot
  donker     de donkere grot: bijna alles zwart (patch pad: het pad gloeit op waar Mira het ziet, met het trilkristal)
  zwamgrot   een grot vol gloeiende paddenstoelen; Pad de zwamhoeder, een padde zo groot als een koe, op een stronk
  aardstad   de stad van de aardmannetjes: rijen nissen met slapers, Moeder Aard op een verhoging, de eierkamer
  spreukzaal een kring van staande stenen, de zwartgebrande vloer, een lessenaar met het spreukenboek, een lege nis
Per vakje van 4 x 8 hooguit 3 kleuren + zwart; patches veranderen niets buiten hun vak (main controleert dat).
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import kleuren_per_vakje   # noqa: E402
from teken_zee import verduisterde_zon, rand   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rotswand(dk, rnd, pts, kleur=GRIJS, licht=LGRIJS, schaduw=DGRIJS, lichtkant=1):
    """een rotswand als veelhoek, met barsten, een lichte rand (aan de lichtkant) en schaduwvlakken"""
    dk.poly(pts, kleur, ZWART)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for _ in range(int((max(xs) - min(xs)) * (max(ys) - min(ys)) / 60)):
        x, y = rnd.randint(min(xs), max(xs)), rnd.randint(min(ys), max(ys))
        if dk.im.getpixel((min(max(x, 0), B - 1), min(max(y, 0), H - 1))) != kleur:
            continue
        lengte = rnd.randint(3, 8)
        dk.lijn([(x, y), (x + rnd.randint(-2, 2), y + lengte)], ZWART)
        dk.lijn([(x + lichtkant, y), (x + lichtkant + rnd.randint(-1, 1), y + lengte - 1)], licht)
        if rnd.random() < 0.4:
            dk.lijn([(x - lichtkant, y + 1), (x - lichtkant, y + lengte)], schaduw)


# ---- de kloofingang -----------------------------------------------------------------------------------------------
def kloof(stand=None):
    rnd = random.Random(81)
    dk = Doek()
    dk.rect(0, 1, B - 1, 40, PAARS)                              # een smalle reep hemel tussen de wanden
    verduisterde_zon(dk, 84, 12, 5)
    rotswand(dk, rnd, [(0, 1), (54, 1), (60, 30), (52, 70), (58, 100), (40, 104), (0, 104)],
             kleur=DGRIJS, licht=GRIJS, schaduw=BLAUW, lichtkant=1)
    rotswand(dk, rnd, [(159, 1), (104, 1), (98, 26), (108, 60), (100, 96), (120, 104), (159, 104)],
             kleur=DGRIJS, licht=GRIJS, schaduw=BLAUW, lichtkant=-1)
    # achterwand met de mond van de grot
    dk.poly([(52, 70), (60, 30), (98, 26), (108, 60), (100, 96), (58, 100)], DGRIJS, ZWART)
    for y in range(27, 100):                                     # de achterwand ligt dieper: om en om donker
        for x in range(52, 109):
            if dk.im.getpixel((x, y)) == DGRIJS and (x + y) % 2:
                dk.px(x, y, ZWART)
    dk.poly([(66, 98), (64, 76), (70, 62), (80, 58), (90, 62), (96, 76), (94, 98)], ZWART, ZWART)
    for x, y in ((74, 74), (77, 74), (86, 80), (89, 80)):        # ogen in het donker van de grot
        dk.px(x, y, ROOD)
    # de bodem: een pad van gruis tussen rotsblokken
    dk.poly([(0, 126), (0, 102), (58, 98), (100, 96), (159, 104), (159, 126)], BRUIN, ZWART)
    dk.poly([(60, 126), (70, 100), (90, 98), (110, 126)], ORANJE, ORANJE)
    for _ in range(40):
        x, y = rnd.randint(0, B - 4), rnd.randint(102, 123)
        dk.ovaal(x, y, x + rnd.randint(2, 5), y + 2, DGRIJS if dk.im.getpixel((x, y)) == BRUIN else BRUIN, ZWART)
    for x, y, r in ((14, 110, 9), (140, 112, 10), (34, 120, 6)):  # rotsblokken
        dk.ovaal(x - r, y - r * 0.7, x + r, y + r * 0.7, GRIJS, ZWART)
        dk.lijn([(x - r + 2, y - r * 0.5), (x, y - r * 0.7 + 1)], LGRIJS)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de donkere grot ----------------------------------------------------------------------------------------------
PAD = (0, 80, 160, 48)           # patches pad1-3 (elk 16 hoog): het pad gloeit, het trilkristal


def donker(pad=False):
    """bijna zwart: alleen hier en daar een vage rand van rots. Met Mira's ziensteen gloeit het pad op."""
    rnd = random.Random(91)
    dk = Doek()
    for _ in range(26):                                          # vage randen van rots in het donker
        x, y = rnd.randint(0, B - 10), rnd.randint(4, 110)
        dk.lijn([(x, y), (x + rnd.randint(3, 9), y + rnd.randint(-2, 2))], DGRIJS)
    for x, y in ((40, 30), (120, 22)):                           # druppels die glinsteren
        dk.px(x, y, BLAUW)
    if pad:
        punten = [(4, 112), (24, 108), (40, 100), (60, 98), (80, 104), (100, 110), (120, 104), (140, 96), (156, 92)]
        for (xa, ya), (xb, yb) in zip(punten, punten[1:]):       # een lint van licht, met rafelige randen
            for t in range(0, 11):
                x = xa + (xb - xa) * t / 10
                y = ya + (yb - ya) * t / 10
                dk.ovaal(x - 3, y - 2, x + 3, y + 2, GROEN, GROEN)
        for (xa, ya), (xb, yb) in zip(punten, punten[1:]):
            dk.lijn([(xa, ya), (xb, yb)], LGROEN)
        for _ in range(60):                                      # vonkjes langs het pad
            x, y = rnd.randint(0, B - 1), rnd.randint(86, 118)
            if dk.im.getpixel((x, y)) == ZWART and rnd.random() < 0.5:
                dk.px(x, y, GROEN)
        # links en rechts: de afgrond, nu zichtbaar als donkere randen
        for x in range(0, B, 2):
            dk.px(x, 120, DGRIJS)
        dk.ovaal(96, 82, 104, 90, LBLAUW, WIT)                   # iets dat niet stil wil liggen: het trilkristal
        dk.px(100, 86, WIT)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de zwamgrot --------------------------------------------------------------------------------------------------
def zwam(dk, x, y, r, hoed, licht, steel=LGRIJS):
    dk.rect(x - max(1, r // 4), y - r, x + max(1, r // 4), y, steel)
    dk.ovaal(x - r, y - r * 1.6, x + r, y - r * 0.6, hoed, ZWART)
    dk.lijn([(x - r + 2, y - r * 1.4), (x + r - 3, y - r * 1.4)], licht)


def zwamgrot(stand=None):
    rnd = random.Random(101)
    dk = Doek()
    dk.rect(0, 1, B - 1, 125, BLAUW)
    for y in range(1, 100):                                      # het gewelf: blauw, naar boven zwart
        for x in range((y % 2), B, 2):
            if rnd.random() < (1.2 - y / 110):
                dk.px(x, y, ZWART)
    for x in range(0, B, 9):                                     # druipstenen
        h = rnd.randint(6, 20)
        dk.poly([(x - 3, 0), (x + 3, 0), (x, h)], ZWART, ZWART)
    dk.poly([(0, 126), (0, 98)] + golf(0, B - 1, 98, 2, rnd, stap=8) + [(B - 1, 126)], DGRIJS, ZWART)
    for _ in range(30):
        x, y = rnd.randint(0, B - 4), rnd.randint(102, 123)
        dk.lijn([(x, y), (x + 3, y)], BLAUW)
    # gloeiende paddenstoelen, groot en klein, langs de wanden
    for x, y, r, k, l in ((10, 100, 7, CYAAN, WIT), (26, 98, 4, LGROEN, WIT), (40, 100, 3, ROZE, WIT),
                          (150, 102, 8, CYAAN, WIT), (134, 100, 4, LGROEN, WIT), (122, 100, 3, ROZE, WIT),
                          (60, 98, 2, CYAAN, WIT), (100, 98, 2, LGROEN, WIT)):
        zwam(dk, x, y, r, k, l)
    # de zwarte zwam (niet eten!), apart op een richel
    zwam(dk, 70, 112, 4, DGRIJS, GRIJS, steel=GRIJS)
    dk.px(70, 105, ROOD)
    # Pad: een padde zo groot als een koe, op een omgevallen stronk
    dk.poly([(88, 104), (92, 96), (132, 96), (136, 104)], BRUIN, ZWART)          # de stronk
    dk.lijn([(92, 97), (132, 97)], ORANJE)
    px, py = 112, 80
    dk.ovaal(px - 20, py - 12, px + 20, py + 16, GROEN, ZWART)                  # het lijf
    dk.ovaal(px - 14, py - 22, px + 14, py - 2, GROEN, ZWART)                   # de kop
    for dx in (-8, 8):                                                           # uitpuilende ogen
        dk.ovaal(px + dx - 4, py - 26, px + dx + 4, py - 18, GEEL, ZWART)
        dk.rect(px + dx - 1, py - 23, px + dx + 1, py - 21, ZWART)
    dk.lijn([(px - 10, py - 8), (px + 10, py - 8)], ZWART)                       # de brede bek
    dk.lijn([(px - 9, py - 7), (px + 9, py - 7)], BRUIN)
    for _ in range(18):                                                          # wratten
        a, rr = rnd.random() * math.tau, rnd.random()
        x, y = px + math.cos(a) * 16 * rr, py + 2 + math.sin(a) * 11 * rr
        dk.px(x, y, LGROEN if rnd.random() < 0.5 else BRUIN)
    for dx in (-18, 16):                                                         # pootjes
        dk.ovaal(px + dx - 3, py + 12, px + dx + 5, py + 17, GROEN, ZWART)
    # zijn kraam: een mand met lichtzwammen
    dk.poly([(56, 100), (58, 92), (76, 92), (78, 100)], ORANJE, ZWART)
    for x in (62, 67, 72):
        zwam(dk, x, 92, 2, GEEL, WIT)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de aardstad --------------------------------------------------------------------------------------------------
EI = (124, 48, 24, 24)           # patch ei_gloeit: het laatste ei in de eierkamer gloeit (als Mira's steen het ziet)


def aardstad(ei_gloeit=False):
    rnd = random.Random(111)
    dk = Doek()
    dk.rect(0, 1, B - 1, 125, BRUIN)
    for y in range(1, 125):                                      # aarde, naar boven donker
        for x in range((y % 2), B, 2):
            if rnd.random() < max(0.0, 0.7 - y / 120):
                dk.px(x, y, ZWART)
    # rijen nissen als een honingraat, in elke nis een slaper (een bruin bolletje met dichte ogen)
    for rij, y in enumerate((14, 34, 54)):
        for i, x in enumerate(range(8 + (rij % 2) * 9, 120, 18)):
            if 50 < x < 100 and rij == 2:
                continue                                         # daar staat Moeder Aard
            dk.ovaal(x - 7, y - 6, x + 7, y + 8, ZWART, DGRIJS)
            dk.ovaal(x - 4, y - 1, x + 4, y + 7, ORANJE if (i + rij) % 3 else BRUIN, ZWART)
            dk.lijn([(x - 2, y + 2), (x - 1, y + 2)], ZWART)    # dichte oogjes
            dk.lijn([(x + 1, y + 2), (x + 2, y + 2)], ZWART)
    # de eierkamer rechts: een grotere nis met lege kuiltjes en één ei
    dk.ovaal(122, 40, 154, 76, ZWART, GRIJS)
    for x, y in ((128, 66), (136, 70), (146, 66), (142, 58)):
        dk.ovaal(x - 3, y - 2, x + 3, y + 2, DGRIJS, ZWART)      # lege kuiltjes
    dk.ovaal(132, 54, 140, 64, LBLAUW if ei_gloeit else GRIJS, ZWART)   # het laatste ei
    if ei_gloeit:
        dk.px(136, 58, WIT)
        for a in range(0, 360, 45):
            r = math.radians(a)
            dk.px(136 + 7 * math.cos(r), 59 + 7 * math.sin(r), LBLAUW)
    # de vloer en een verhoging met Moeder Aard
    dk.poly([(0, 126), (0, 96), (160, 96), (160, 126)], BRUIN, ZWART)
    for _ in range(30):
        x, y = rnd.randint(0, B - 4), rnd.randint(98, 123)
        dk.lijn([(x, y), (x + 2, y)], ORANJE)
    dk.poly([(52, 96), (56, 84), (100, 84), (104, 96)], GRIJS, ZWART)
    dk.lijn([(56, 85), (100, 85)], LGRIJS)
    mx, my = 78, 84                                              # Moeder Aard: oud, wit haar, een omslagdoek
    dk.poly([(mx - 9, my), (mx - 7, my - 16), (mx + 7, my - 16), (mx + 9, my)], PAARS, ZWART)
    dk.ovaal(mx - 6, my - 26, mx + 6, my - 14, BRUIN, ZWART)
    dk.poly([(mx - 7, my - 22), (mx, my - 30), (mx + 7, my - 22), (mx + 5, my - 25), (mx - 5, my - 25)], WIT, LGRIJS)
    dk.rect(mx - 3, my - 21, mx - 2, my - 20, GEEL)              # gloeiende oogjes, open
    dk.rect(mx + 2, my - 21, mx + 3, my - 20, GEEL)
    for r in (-1, 1):
        dk.poly([(mx + r * 6, my - 22), (mx + r * 11, my - 26), (mx + r * 6, my - 18)], BRUIN, ZWART)
    dk.lijn([(mx - 6, my - 12), (mx + 6, my - 12)], ROZE)        # de omslagdoek
    dk.lijn([(mx + 10, my - 18), (mx + 12, my)], BRUIN)          # een wandelstok
    # een gang naar rechts (naar de spreukzaal) en een naar links (terug)
    dk.poly([(150, 96), (150, 82), (156, 78), (159, 78), (159, 96)], ZWART, ZWART)
    dk.poly([(0, 96), (0, 80), (4, 78), (10, 82), (10, 96)], ZWART, ZWART)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de spreukzaal ------------------------------------------------------------------------------------------------
BOEK = (20, 72, 28, 24)          # patch boek_open: het spreukenboek opengeslagen, een gloed erboven


def spreukzaal(boek_open=False):
    rnd = random.Random(121)
    dk = Doek()
    dk.rect(0, 1, B - 1, 125, DGRIJS)
    for y in range(1, 90):
        for x in range((y % 2), B, 2):
            if rnd.random() < max(0.0, 0.8 - y / 90):
                dk.px(x, y, ZWART)
    # de achterwand met de lege nis waar de Holle Kroon stond, en maantekens eromheen
    dk.poly([(66, 72), (66, 40), (70, 32), (80, 28), (90, 32), (94, 40), (94, 72)], ZWART, GRIJS)
    for x, y in ((60, 36), (100, 36)):
        dk.ovaal(x - 4, y - 4, x + 4, y + 4, LGRIJS, ZWART)
        dk.ovaal(x - 2, y - 4, x + 5, y + 4, DGRIJS, DGRIJS)     # sikkels
    dk.lijn([(70, 72), (90, 72)], LGRIJS)
    # de vloer en de kring van staande stenen, het midden zwartgeblakerd
    dk.poly([(0, 126), (0, 84), (160, 84), (160, 126)], GRIJS, ZWART)
    for y in range(86, 126, 6):
        dk.lijn([(0, y), (B - 1, y)], DGRIJS)
    dk.ovaal(48, 94, 112, 120, ZWART, DGRIJS)                    # zwartgebrand: hier stond Grom
    for a in range(0, 360, 45):                                  # de stenen van de kring
        r = math.radians(a + 22)
        x, y = 80 + 36 * math.cos(r), 107 + 15 * math.sin(r)
        h = 14 + 4 * math.sin(r)
        dk.poly([(x - 3, y), (x - 2, y - h), (x + 2, y - h - 1), (x + 3, y)], LGRIJS, ZWART)
        dk.lijn([(x + 1, y - h), (x + 2, y - 1)], GRIJS)
        dk.px(x, y - h / 2, LBLAUW)                              # een rune
    # de lessenaar met het boek
    dk.poly([(30, 110), (32, 90), (36, 90), (38, 110)], BRUIN, ZWART)
    dk.poly([(22, 90), (46, 90), (42, 82), (26, 82)], BRUIN, ZWART)
    if boek_open:
        dk.poly([(24, 84), (34, 80), (44, 84), (44, 88), (34, 86), (24, 88)], WIT, ZWART)
        dk.lijn([(34, 80), (34, 86)], GRIJS)
        for y in (83, 85):
            dk.lijn([(26, y), (32, y - 1)], DGRIJS)
            dk.lijn([(36, y - 1), (42, y)], DGRIJS)
        for a in range(200, 341, 35):                            # een gloed uit de bladzijden
            r = math.radians(a)
            dk.lijn([(34 + 6 * math.cos(r), 80 + 5 * math.sin(r)), (34 + 11 * math.cos(r), 80 + 8 * math.sin(r))],
                    LBLAUW)
    else:
        dk.poly([(26, 86), (42, 86), (40, 82), (28, 82)], ROOD, ZWART)   # dicht: een rode band
        dk.lijn([(29, 84), (39, 84)], GEEL)
    # een gang terug, links achter
    dk.poly([(0, 84), (0, 60), (6, 56), (12, 60), (12, 84)], ZWART, GRIJS)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


PLAATJES = {"kloof": kloof, "donker": donker, "donker_pad": lambda: donker(True), "zwamgrot": zwamgrot,
            "aardstad": aardstad, "aardstad_ei": lambda: aardstad(True),
            "spreukzaal": spreukzaal, "spreukzaal_boek": lambda: spreukzaal(True)}
PATCHES = {"donker_pad": ("donker", PAD), "aardstad_ei": ("aardstad", EI), "spreukzaal_boek": ("spreukzaal", BOEK)}


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    namen = sys.argv[1:] or list(PLAATJES)
    gemaakt = {}
    for naam in namen:
        im = gemaakt[naam] = PLAATJES[naam]()
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[kloof] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))
        if naam in PATCHES:
            basis_naam, (px, py, pb, ph) = PATCHES[naam]
            basis = gemaakt.get(basis_naam) or PLAATJES[basis_naam]()
            buiten = sum(1 for y in range(H) for x in range(B) if basis.getpixel((x, y)) != im.getpixel((x, y))
                         and not (px <= x < px + pb and py <= y < py + ph))
            if buiten or px % 4 or pb % 4 or py % 8 or ph % 8:
                raise SystemExit("[kloof] patch %s: %d pixels buiten het vak %s (of een vak niet op vakjes)"
                                 % (naam, buiten, (px, py, pb, ph)))


if __name__ == "__main__":
    main()
