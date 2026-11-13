#!/usr/bin/env python3
"""teken_jachthut.py — Groms jachthut (hoofdstuk 2), met de hand getekend als C64-pixelart.

    python3 tools/teken_jachthut.py   schrijft data/plaatjes/jachthut.png, jachthut_vuur_uit.png, jachthut_kooi_open.png

Scenario hoofdstuk 2: Grom is weg. Aan de muur een kaart met de zee en een vuurtoren, in een kooi een aardmannetje
(een jong, bang, met gloeiende oogjes), een tafel met papieren (de brief van Grom) en een haardvuur. Twee patches:
het vuur uit (de helm dooft de haard) en de kooi open en leeg (het aardmannetje is gevlucht; de gloeischub ligt er).
Links de deur terug naar de spookbrug, rechts de achterdeur naar de oever. Binnen loopt Eldric op volle grootte, dus
de muren zijn hoog genoeg en de deuren groot.
"""
import os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import kleuren_per_vakje   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VUUR = (68, 56, 28, 24)          # patch vuur_uit: x, y, breedte, hoogte (kamerpixels, op vakjes van 4 x 8)
KOOI = (108, 40, 36, 56)         # patch kooi_open


def dak(dk):
    dk.rect(0, 1, B - 1, 9, DGRIJS)
    dk.lijn([(0, 9), (B - 1, 9)], ZWART)
    for x in range(10, B, 30):                                   # dikke dakbalken
        dk.rect(x, 1, x + 5, 9, BRUIN)
        dk.lijn([(x - 1, 1), (x - 1, 9)], ZWART)
        dk.lijn([(x + 6, 1), (x + 6, 9)], ZWART)


def blokwand(dk, rnd):
    """een wand van liggende boomstammen: elke stam bruin met een lichte bovenkant en een zwarte voeg"""
    for y in range(10, 82, 8):
        dk.rect(0, y, B - 1, y + 7, BRUIN)
        dk.lijn([(0, y + 1), (B - 1, y + 1)], ORANJE)
        dk.lijn([(0, y + 7), (B - 1, y + 7)], ZWART)
        for _ in range(2):                                       # nerven en kwasten
            x = rnd.randint(0, B - 8)
            dk.lijn([(x, y + 4), (x + rnd.randint(4, 9), y + 4)], DGRIJS)
    for x in (2, B - 3):                                         # de stamkoppen in de hoeken
        for y in range(10, 82, 8):
            dk.ovaal(x - 2, y, x + 2, y + 6, ORANJE, ZWART)
    dk.lijn([(0, 81), (B - 1, 81)], ZWART)


def deuren(dk):
    for x0, x1 in ((6, 26), (146, 158)):                          # links naar de brug, rechts naar de oever
        dk.rect(x0 - 1, 33, x1 + 1, 81, ZWART)
        dk.rect(x0, 34, x1, 81, DGRIJS)
        dk.poly([(x0, 34), (x0 + (x1 - x0) // 2, 30), (x1, 34)], DGRIJS, ZWART)   # een spitse bovenkant
        for x in range(x0 + 5, x1, 5):
            dk.lijn([(x, 33), (x, 81)], GRIJS)
        for y in (42, 70):                                       # ijzeren banden
            dk.rect(x0, y, x1, y + 1, ZWART)
    dk.rect(22, 58, 23, 60, GEEL)                                # de klink links
    dk.rect(148, 58, 149, 60, GEEL)


def kaart(dk):
    """de kaart: zee, een kustlijn, een vuurtoren zonder licht"""
    dk.rect(30, 16, 58, 38, ZWART)
    dk.rect(31, 17, 57, 37, GEEL)
    dk.poly([(31, 17), (44, 17), (42, 22), (46, 27), (40, 33), (41, 37), (31, 37)], LBLAUW, LBLAUW)   # de zee
    dk.lijn([(44, 17), (42, 22), (46, 27), (40, 33), (41, 37)], BRUIN)
    for x, y in ((34, 22), (37, 28), (33, 32)):                  # golfjes
        dk.lijn([(x, y), (x + 2, y)], BLAUW)
    dk.rect(48, 22, 49, 30, BRUIN)                               # de vuurtoren
    dk.px(48, 21, ZWART)
    dk.px(49, 21, ZWART)
    dk.lijn([(51, 33), (55, 25)], BRUIN)                         # een pad over land
    dk.px(54, 33, ROOD)                                          # een kruisje: hier zijn wij
    dk.px(55, 34, ROOD)
    dk.px(55, 32, ROOD)
    dk.px(53, 34, ROOD)
    for x, y in ((31, 16), (57, 16)):
        dk.px(x, y, LGRIJS)                                      # spijkertjes


def gewei(dk):
    """een groot gewei boven de haard: een jachthut"""
    dk.ovaal(78, 12, 86, 20, LGRIJS)                             # schedel
    dk.px(80, 15, ZWART)
    dk.px(84, 15, ZWART)
    for r in (-1, 1):
        c = 82 + r * 4
        dk.lijn([(c, 14), (c + r * 8, 10), (c + r * 13, 12)], LGRIJS, 2)
        dk.lijn([(c + r * 6, 11), (c + r * 7, 17)], LGRIJS)
        dk.lijn([(c + r * 10, 11), (c + r * 12, 16)], LGRIJS)


def haard(dk, rnd, aan):
    dk.poly([(62, 81), (64, 24), (100, 24), (102, 81)], GRIJS)    # de stenen schouw tot het dak
    for y in range(26, 81, 6):
        dk.lijn([(63, y), (101, y)], DGRIJS)
        for x in range(64 + (y // 6 % 2) * 5, 100, 10):
            dk.lijn([(x, y), (x, y + 5)], DGRIJS)
    dk.lijn([(62, 81), (64, 24)], ZWART)
    dk.lijn([(102, 81), (100, 24)], ZWART)
    dk.rect(60, 50, 104, 54, BRUIN)                              # de schoorsteenmantel
    dk.lijn([(60, 50), (104, 50)], ZWART)
    dk.lijn([(60, 54), (104, 54)], ZWART)
    dk.rect(70, 58, 94, 80, ZWART)                               # de stookplaats
    dk.lijn([(70, 58), (94, 58)], DGRIJS)
    dk.rect(72, 75, 92, 77, BRUIN)                               # houtblokken
    dk.lijn([(72, 77), (92, 77)], ZWART)
    if aan:
        for x0, top in ((74, 64), (78, 60), (82, 59), (86, 61), (90, 65)):
            dk.poly([(x0 - 3, 75), (x0, top), (x0 + 3, 75)], ROOD, ROOD)
            dk.poly([(x0 - 2, 75), (x0, top + 4), (x0 + 2, 75)], ORANJE, ORANJE)
            dk.poly([(x0 - 1, 75), (x0, top + 8), (x0 + 1, 75)], GEEL, GEEL)
    else:
        for x0 in (76, 82, 88):                                  # rook, en een paar kolen
            dk.lijn([(x0, 74), (x0 - 1, 68), (x0 + 1, 63)], DGRIJS)
        for _ in range(6):
            dk.px(rnd.randint(73, 91), rnd.randint(73, 74), ROOD)
    dk.rect(66, 80, 98, 81, DGRIJS)                              # de haardsteen


def kooi(dk, open_):
    """een kooi van takken en ijzer, met (dicht) een bang aardmannetje met gloeiende oogjes"""
    x0, y0, x1, y1 = 112, 46, 138, 92
    dk.rect(x0 - 1, y0 - 2, x1 + 1, y0, DGRIJS)                  # bovenkant
    dk.lijn([(x0 - 1, y0 - 2), (x1 + 1, y0 - 2)], ZWART)
    dk.lijn([(125, y0 - 6), (125, y0 - 2)], GRIJS)               # de ring waaraan hij hangt
    dk.ovaal(123, y0 - 9, 127, y0 - 5, None, GRIJS)
    dk.rect(x0 - 1, y1, x1 + 1, y1 + 2, DGRIJS)                  # bodem
    dk.lijn([(x0 - 1, y1 + 2), (x1 + 1, y1 + 2)], ZWART)
    dk.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, ZWART)             # het donker in de kooi
    if not open_:
        dk.ovaal(119, 70, 131, 90, BRUIN, ZWART)                 # het aardmannetje, ineengedoken
        dk.ovaal(120, 62, 130, 73, BRUIN, ZWART)                 # het hoofd
        dk.poly([(120, 66), (114, 61), (121, 64)], BRUIN, ZWART) # puntoren
        dk.poly([(130, 66), (136, 61), (129, 64)], BRUIN, ZWART)
        dk.rect(122, 67, 123, 68, GEEL)                          # gloeiende oogjes
        dk.rect(127, 67, 128, 68, GEEL)

        dk.lijn([(121, 82), (124, 77), (127, 77), (130, 82)], ZWART)   # armpjes om de knieen
        staven = range(x0, x1 + 1, 4)
    else:
        staven = [x for x in range(x0, x1 + 1, 4) if not 118 < x < 134]
        for x in (100, 104):                                     # het deurtje staat open, naar links
            dk.lijn([(x + 8, y0 + 2), (x + 8, y1 - 2)], LGRIJS)
        dk.lijn([(108, y0 + 4), (118, y0 + 2)], LGRIJS)
        dk.lijn([(108, y1 - 4), (118, y1 - 2)], LGRIJS)
    for x in staven:
        dk.lijn([(x, y0 + 1), (x, y1 - 1)], LGRIJS)
    dk.lijn([(x0, y0 + 16), (x1, y0 + 16)], GRIJS)               # dwarsband
    dk.rect(134, 66, 136, 70, GEEL)                              # het slot


def vloer(dk, rnd, aan):
    dk.rect(0, 82, B - 1, 125, BRUIN)
    for y in range(86, 126, 6):                                  # planken
        dk.lijn([(0, y), (B - 1, y)], DGRIJS)
        for x in range((y * 7) % 23, B, 37):
            dk.lijn([(x, y - 5), (x, y)], DGRIJS)
    if False:                                                    # (geen schijnsel: dat blijft liggen als het vuur uit is)
        for _ in range(150):                                     # schijnsel van het vuur vlak voor de haard
            x, y = rnd.randint(60, 104), rnd.randint(82, 96)
            if dk.im.getpixel((x, y)) == BRUIN and abs(x - 82) / 22 + (y - 82) / 14 < 1:
                dk.px(x, y, ORANJE)
    dk.ovaal(30, 106, 58, 116, ORANJE, ZWART)                    # een berenvel voor de tafel
    dk.ovaal(24, 108, 32, 114, ORANJE, ZWART)
    dk.px(26, 110, ZWART)


def tafel(dk):
    """de tafel met de brief en de papieren; ernaast een troll-grote stoel"""
    dk.rect(30, 92, 34, 106, BRUIN)                              # poten
    dk.rect(58, 92, 62, 106, BRUIN)
    dk.lijn([(30, 106), (34, 106)], ZWART)
    dk.lijn([(58, 106), (62, 106)], ZWART)
    dk.poly([(26, 92), (30, 86), (64, 86), (66, 92)], ORANJE)    # het blad
    dk.rect(26, 92, 66, 95, BRUIN)
    dk.lijn([(26, 95), (66, 95)], ZWART)
    dk.poly([(36, 89), (38, 87), (46, 87), (45, 90)], WIT)       # de brief
    dk.lijn([(39, 88), (44, 88)], GRIJS)
    dk.poly([(48, 90), (50, 87), (58, 88), (57, 91)], LGRIJS)    # papieren
    dk.rect(60, 84, 62, 88, LGRIJS)                              # een kaarsstompje, uit
    dk.px(61, 83, ZWART)
    # een stapel brandhout naast de haard
    for i, (x, y) in enumerate(((44, 76), (52, 76), (48, 71))):
        dk.ovaal(x, y, x + 8, y + 5, BRUIN, ZWART)
        dk.ovaal(x + 1, y + 1, x + 4, y + 4, ORANJE, ORANJE)


def teken(aan=True, open_=False):
    rnd = random.Random(14)
    dk = Doek()
    dak(dk)
    blokwand(dk, rnd)
    deuren(dk)
    kaart(dk)
    haard(dk, random.Random(4), aan)
    gewei(dk)
    vloer(dk, rnd, aan)
    kooi(dk, open_)
    tafel(dk)
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    kleuren_per_vakje(dk.im)
    return dk.im


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    for naam, aan, open_ in (("jachthut", True, False), ("jachthut_vuur_uit", False, False),
                             ("jachthut_kooi_open", False, True)):
        im = teken(aan, open_)
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[jachthut] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))


if __name__ == "__main__":
    main()
