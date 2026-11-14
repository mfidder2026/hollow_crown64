#!/usr/bin/env python3
"""teken_woud2.py — de weg van de spookbrug naar Groms jachthut (hoofdstuk 2), met de hand getekend als C64-pixelart.

    python3 tools/teken_woud2.py [naam ...]   schrijft data/plaatjes/<naam>.png en build/proef/<naam>_groot.png

  diepwoud  achter de brug: het hart van het Duisterwoud. Een eeuwenoude boom met een holte (en twee gele ogen: een
            uil), een omgevallen stam vol gloeizwammen die blauw licht geven, mos dat uit de kruinen hangt, een
            spinnenweb, vuurvliegjes. Het pad komt links binnen en kronkelt naar rechts, dieper het bos in.
  wolfspad  een open plek: in de modder enorme voetsporen (Grom is een reus), een roestige klem naast het pad, een
            waarschuwingspaal met een schedel met gewei. Achteraan tussen de stammen: rook en een oranje gloed.
  huterf    het erf van Groms jachthut: een blokhut op reuzenmaat, een stenen schoorsteen die rookt, een raam met
            oranje licht dat op het erf valt, een deur twee keer zo hoog als Eldric met een gewei erboven, een rek
            met huiden, een hakblok met een bijl, een stapel brandhout en een ketel op een driepoot.

Licht: overal het paarse schemerlicht van boven, en per kamer één warme of koude lichtbron (gloeizwammen, de gloed
van de hut, het raam). Kamerpixels 160 x 128, C64-kleuren, per 4 x 8 vakje 3 kleuren + zwart.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import lucht_en_achtergrond, bladerdak, stam, kleuren_per_vakje, mist   # noqa: E402
import rijk   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- gedeeld ------------------------------------------------------------------------------------------------------
def bosgrond(dk, rnd, y0=84):
    dk.poly([(0, y0 - 2)] + golf(0, B - 1, y0, 2, rnd, stap=6) + [(B - 1, 126), (0, 126)], DGRIJS, DGRIJS)
    dither(dk, (0, y0, B, 126), GROEN, 0.5, rnd, DGRIJS)
    for _ in range(40):                                          # varens en sprieten
        x, y = rnd.randint(0, B - 1), rnd.randint(y0 + 4, 125)
        dk.lijn([(x, y), (x - 1, y - 3)], LGROEN)
        dk.lijn([(x, y), (x + 2, y - 2)], GROEN)


def kronkelpad(dk, rnd, links, rechts, steen=BRUIN):
    """een pad als veelhoek (links-rand + rechts-rand), met een lichter uitgesleten midden en steentjes"""
    dk.poly(links + rechts, BRUIN, ZWART)
    midden = [((a[0] * 3 + b[0]) / 4, (a[1] * 3 + b[1]) / 4) for a, b in zip(links, rechts[::-1])]
    midden2 = [((a[0] + b[0] * 3) / 4, (a[1] + b[1] * 3) / 4) for a, b in zip(links, rechts[::-1])]
    dk.poly(midden + midden2[::-1], ORANJE, ORANJE)
    for _ in range(70):
        x, y = rnd.randint(0, B - 1), rnd.randint(80, 126)
        if dk.im.getpixel((x, y)) == ORANJE:
            dk.px(x, y, steen)


def kruispad(dk, rnd):
    """het doolhof: een open plek met vier uitgangen: links, rechts en twee paden naar achteren (links en rechts van
    het midden). Eén vorm (masker), zwart omlijnd, met een lichter uitgesleten midden en steentjes."""
    from PIL import Image, ImageDraw, ImageFilter
    m = Image.new("L", (B, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((8, 102, 152, 126), fill=255)                      # de open plek
    d.polygon([(0, 106), (24, 104), (24, 121), (0, 123)], fill=255)          # links
    d.polygon([(136, 103), (159, 101), (159, 119), (136, 121)], fill=255)    # rechts
    d.polygon([(22, 108), (32, 92), (34, 80), (40, 80), (44, 92), (52, 108)], fill=255)        # achter links
    d.polygon([(108, 108), (116, 92), (120, 80), (126, 80), (130, 92), (138, 108)], fill=255)  # achter rechts
    binnen = m.filter(ImageFilter.MinFilter(5))
    for y in range(1, H - 2):
        for x in range(B):
            if not m.getpixel((x, y)):
                continue
            rand = any(not m.getpixel((min(B - 1, max(0, x + dx)), y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if rand and 0 < x < B - 1:
                dk.px(x, y, ZWART)
            elif binnen.getpixel((x, y)) and rijk.ruis(x, y, 7) < 0.8:
                dk.px(x, y, ORANJE if rijk.ruis(x, y, 8) > 0.06 else BRUIN)
            else:
                dk.px(x, y, BRUIN)
    for cx in (37, 123):                                         # achteraan: een donkere opening tussen de struiken
        dk.ovaal(cx - 9, 66, cx + 9, 84, ZWART, ZWART)
        for y in range(66, 84):
            for x in range(cx - 9, cx + 10):
                if dk.im.getpixel((x, y)) == ZWART and (x + y) % 2 == 0 and abs(x - cx) > 5 + (84 - y) // 6:
                    dk.px(x, y, DGRIJS)
        for i in range(10):                                      # struiken als een poort eromheen
            a = math.pi * (0.9 + 1.2 * i / 9)
            bx, by = cx + 11 * math.cos(a), 76 + 12 * math.sin(a)
            dk.ovaal(bx - 3, by - 2, bx + 3, by + 2, GROEN, ZWART)
            dk.px(bx - 1, by - 1, LGROEN)
    for y in range(80, 96):                                      # de paden lopen de schemer in
        for x in range(B):
            if m.getpixel((x, y)) and (x + y) % 2 == 0 and y < 88:
                dk.px(x, y, DGRIJS)


def hangmos(dk, rnd, n, y_max=40):
    for _ in range(n):
        x = rnd.randint(2, B - 3)
        y = rnd.randint(4, 12)
        lengte = rnd.randint(8, y_max)
        for i in range(lengte):
            xx = x + int(1.5 * math.sin(i * 0.4 + x))
            dk.px(xx, y + i, GROEN if i % 3 else LGROEN)
            if i % 4 == 0 and i > 2:
                dk.px(xx + 1, y + i, GROEN)


def vuurvliegjes(dk, rnd, n, gebied):
    x1, y1, x2, y2 = gebied
    for _ in range(n):
        x, y = rnd.randint(x1, x2), rnd.randint(y1, y2)
        dk.px(x, y, GEEL)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if dk.im.getpixel((x + dx, y + dy)) in (PAARS, BLAUW, DGRIJS, ZWART):
                dk.px(x + dx, y + dy, ORANJE if rnd.random() < 0.3 else dk.im.getpixel((x + dx, y + dy)))


def gloeizwam(dk, x, y, r=2):
    dk.rect(x, y - r, x, y, LGRIJS)
    dk.ovaal(x - r - 1, y - r - 2, x + r + 1, y - r + 1, CYAAN, ZWART)
    dk.px(x - r, y - r - 1, WIT)


def afmaken(dk):
    dk.rect(0, 0, B - 1, 0, ZWART)
    dk.rect(0, 126, B - 1, 127, ZWART)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- diepwoud -----------------------------------------------------------------------------------------------------
def oerboom(dk, rnd):
    """de oude boom in het midden: breed, knoestig, met kronkelende wortels en een holte met twee gele ogen"""
    x, top, voet = 70, 2, 92
    pts_l, pts_r = [], []
    for y in range(top, voet + 1, 3):
        w = 9 + (y - top) * 0.06 + (6 if y > voet - 14 else 0) * (y - (voet - 14)) / 14
        dx = 3 * math.sin(y * 0.07)
        pts_l.append((x + dx - w, y))
        pts_r.append((x + dx + w, y))
    dk.poly(pts_l + pts_r[::-1], BRUIN)
    dk.lijn(pts_l, ZWART)
    dk.lijn(pts_r, ZWART)
    for y in range(top + 4, voet, 2):                            # diepe schorsgroeven, golvend
        for g in (-6, -2, 3, 7):
            gx = x + 3 * math.sin(y * 0.07) + g + 1.5 * math.sin(y * 0.2 + g)
            if rnd.random() < 0.8:
                dk.px(gx, y, DGRIJS)
    for y in range(top + 2, voet):                               # rechts de schaduwkant
        gx = x + 3 * math.sin(y * 0.07) + 7
        dk.px(gx, y, DGRIJS)
        dk.px(gx + 1, y, ZWART if y % 2 else DGRIJS)
    for y in range(top + 2, voet, 1):                            # links randlicht van de schemer
        gx = x + 3 * math.sin(y * 0.07) - 8 - (y - top) * 0.06
        if y % 3:
            dk.px(gx, y, ORANJE)
    # de wortels: dikke kronkels over de grond
    for (ex, ey, r) in ((40, 100, -1), (50, 108, -1), (98, 102, 1), (90, 110, 1), (64, 104, 0)):
        bx = x + (r * 10)
        dk.lijn([(bx, voet - 6), ((bx + ex) / 2, voet + 2 + r), (ex, ey)], ZWART, 4)
        dk.lijn([(bx, voet - 7), ((bx + ex) / 2, voet + 1 + r), (ex, ey - 1)], BRUIN, 2)
        dk.lijn([(bx, voet - 8), ((bx + ex) / 2, voet + r)], ORANJE)
    # de holte, met de uil erin: twee gele ogen en een snavel
    dk.ovaal(62, 40, 76, 58, ZWART, ZWART)
    dk.lijn([(61, 42), (61, 56)], DGRIJS)                        # de rand van de holte, binnenkant
    dk.ovaal(65, 45, 68, 48, GEEL, GEEL)
    dk.ovaal(70, 45, 73, 48, GEEL, GEEL)
    dk.px(66, 46, ZWART)
    dk.px(71, 46, ZWART)
    dk.px(69, 49, ORANJE)
    dk.lijn([(64, 44), (66, 43)], DGRIJS)                        # oorpluimen
    dk.lijn([(74, 44), (72, 43)], DGRIJS)
    # takken naar het dak
    for (ty, lengte, r) in ((24, 30, -1), (30, 34, 1), (14, 22, 1)):
        sx = x + r * 8
        dk.lijn([(sx, ty), (sx + r * lengte // 2, ty - 8), (sx + r * lengte, ty - 12)], ZWART, 4)
        dk.lijn([(sx, ty - 1), (sx + r * lengte // 2, ty - 9)], BRUIN, 2)


def spinnenweb(dk, cx, cy, r):
    for i in range(8):
        a = i * math.pi / 4 + 0.2
        dk.lijn([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a) * 0.8)], LGRIJS)
    for ring in (r * 0.35, r * 0.65, r * 0.95):
        pts = []
        for i in range(9):
            a = i * math.pi / 4 + 0.2
            pts.append((cx + ring * math.cos(a), cy + ring * math.sin(a) * 0.8))
        dk.lijn(pts, GRIJS)
    dk.px(cx + 2, cy + 3, ZWART)                                 # de spin
    dk.px(cx + 3, cy + 3, ZWART)
    dk.px(cx + 2, cy + 4, ROOD)


def omgevallen_stam(dk, rnd):
    """rechts vooraan een omgevallen, bemoste stam vol gloeizwammen"""
    # achter rechts, tussen het rechterpad en de rand: de stam ligt schuin het bos in
    pts = [(132, 98), (159, 88), (159, 99), (134, 104)]
    dk.poly(pts, BRUIN, ZWART)
    dk.ovaal(128, 96, 138, 106, ORANJE, ZWART)                   # de afgezaagde kant: jaarringen
    dk.ovaal(131, 99, 135, 103, BRUIN, BRUIN)
    dk.px(133, 101, ORANJE)
    for x in range(138, 159, 2):                                 # mos bovenop
        y = 98 - (x - 132) * 10 / 27
        for d in range(rnd.randint(1, 2)):
            dk.px(x, y + d, GROEN if d else LGROEN)
    for (x, y, r) in ((142, 96, 2), (148, 93, 1), (154, 92, 2), (145, 101, 1), (152, 98, 1)):
        gloeizwam(dk, x, y, r)
    for (x, y) in ((6, 100), (12, 102), (156, 124), (150, 125), (60, 124)):   # en vooraan, langs de rand
        gloeizwam(dk, x, y, 1)


def diepwoud():
    rnd = random.Random(301)
    dk = Doek()
    lucht_en_achtergrond(dk, rnd)
    bosgrond(dk, rnd, 86)
    mist(dk, rnd)
    stam(dk, 18, 6, 4, 90, rnd, takken=((28, 16, 1), (46, 12, -1)))
    stam(dk, 128, 6, 6, 88, rnd, takken=((34, 18, -1), (20, 14, 1)))
    stam(dk, 152, 5, 2, 86, rnd)
    oerboom(dk, rnd)
    kruispad(dk, rnd)
    voetspoor(dk, 64, 118, 0.7, True)                            # ook hier de sporen van Grom
    voetspoor(dk, 92, 113, 0.6, False)
    bladerdak(dk, rnd)
    hangmos(dk, rnd, 16)
    spinnenweb(dk, 30, 54, 10)
    omgevallen_stam(dk, rnd)
    vuurvliegjes(dk, rnd, 14, (4, 30, 155, 84))
    rijk.verrijk(dk, 311, lichten=[
        (148, 96, 24, 14, 0.8, {DGRIJS: BLAUW, GROEN: CYAAN, BRUIN: LBLAUW, ORANJE: LBLAUW, LGROEN: CYAAN}),   # zwammen
        (69, 47, 9, 7, 0.5, {BRUIN: ORANJE, DGRIJS: BRUIN}),                                                     # de ogen
    ], sluit=(PAARS, CYAAN, GEEL))
    return afmaken(dk)


# ---- wolfspad -----------------------------------------------------------------------------------------------------
def voetspoor(dk, x, y, s=1.0, links=True):
    """een reuzenvoetafdruk in de modder: een diepe hiel, een bal en vier tenen, met een opgeduwde rand"""
    r = 1 if links else -1
    dk.ovaal(x - 5 * s, y - 2 * s, x + 5 * s, y + 3 * s, BRUIN, ZWART)
    dk.ovaal(x - 4 * s, y - 1 * s, x + 4 * s, y + 2 * s, DGRIJS, DGRIJS)
    dk.ovaal(x - 4 * s + r * 9 * s, y - 4 * s, x + 4 * s + r * 9 * s, y + 1 * s, BRUIN, ZWART)
    dk.ovaal(x - 3 * s + r * 9 * s, y - 3 * s, x + 3 * s + r * 9 * s, y, DGRIJS, DGRIJS)
    for i in range(4):
        tx = x + r * (15 + i * 2) * s
        ty = y - 4 * s + i * 2 * s
        dk.ovaal(tx - 1.5 * s, ty - 1.2 * s, tx + 1.5 * s, ty + 1.2 * s, DGRIJS, ZWART)
    dk.lijn([(x - 5 * s, y - 3 * s), (x + 4 * s, y - 3 * s)], ORANJE)   # de opgeduwde rand vangt licht


def klem(dk, x, y):
    """een grote roestige klem (dichtgeklapt), met een ketting naar een paal"""
    dk.ovaal(x - 12, y - 3, x + 12, y + 4, DGRIJS, ZWART)        # de plaat
    dk.ovaal(x - 10, y - 2, x + 10, y + 2, GRIJS, GRIJS)
    for i in range(-10, 11, 3):                                  # de tanden, in elkaar gehaakt
        dk.poly([(x + i, y - 2), (x + i + 1, y - 8), (x + i + 2, y - 2)], LGRIJS, ZWART)
    dk.lijn([(x - 12, y - 2), (x - 9, y - 9), (x + 9, y - 9), (x + 12, y - 2)], GRIJS, 2)   # de beugel
    dk.lijn([(x - 9, y - 10), (x + 9, y - 10)], LGRIJS)
    for i in range(0, 14, 2):                                    # roest
        dk.px(x - 8 + i, y - 9, BRUIN if i % 4 else ORANJE)
    pts = [(x + 12, y), (x + 17, y + 2), (x + 22, y + 1), (x + 26, y - 2)]   # ketting naar het paaltje
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dk.ovaal(min(ax, bx), min(ay, by) - 1, max(ax, bx), max(ay, by) + 1, GRIJS, ZWART)
    dk.rect(x + 26, y - 8, x + 28, y + 1, BRUIN)
    dk.lijn([(x + 26, y - 8), (x + 26, y + 1)], ZWART)
    dk.lijn([(x + 29, y - 8), (x + 29, y + 1)], ZWART)


def waarschuwingspaal(dk, x, voet):
    """een paal met een schedel met een groot gewei, veren en botjes aan touwtjes"""
    dk.rect(x - 2, voet - 52, x + 2, voet, BRUIN)
    dk.lijn([(x - 3, voet - 52), (x - 3, voet)], ZWART)
    dk.lijn([(x + 3, voet - 52), (x + 3, voet)], ZWART)
    dk.lijn([(x - 2, voet - 50), (x - 2, voet)], ORANJE)
    for y in range(voet - 48, voet, 5):
        dk.px(x + 1, y, DGRIJS)
    # gewei
    for r in (-1, 1):
        dk.lijn([(x + 2 * r, voet - 58), (x + 10 * r, voet - 66), (x + 14 * r, voet - 76)], LGRIJS, 2)
        dk.lijn([(x + 8 * r, voet - 64), (x + 6 * r, voet - 74)], LGRIJS, 2)
        dk.lijn([(x + 12 * r, voet - 70), (x + 18 * r, voet - 72)], LGRIJS)
        dk.lijn([(x + 11 * r, voet - 66), (x + 16 * r, voet - 62)], LGRIJS)
    # schedel
    dk.ovaal(x - 5, voet - 62, x + 5, voet - 52, WIT, ZWART)
    dk.poly([(x - 3, voet - 54), (x + 3, voet - 54), (x + 2, voet - 48), (x - 2, voet - 48)], LGRIJS, ZWART)
    dk.ovaal(x - 4, voet - 60, x - 1, voet - 57, ZWART, ZWART)
    dk.ovaal(x + 1, voet - 60, x + 4, voet - 57, ZWART, ZWART)
    dk.px(x, voet - 53, ZWART)
    # touwtjes met veren en botjes
    for dx, l, k in ((-6, 10, ROOD), (6, 14, LGRIJS), (-3, 18, WIT)):
        dk.lijn([(x + dx, voet - 52), (x + dx, voet - 52 + l)], BRUIN)
        dk.ovaal(x + dx - 1, voet - 52 + l, x + dx + 1, voet - 48 + l, k, ZWART)


def wolfspad():
    rnd = random.Random(401)
    dk = Doek()
    lucht_en_achtergrond(dk, rnd)
    # achteraan, tussen de stammen: een vreemd groen schijnsel (dwaallichtjes)
    for x, y in ((30, 70), (124, 66), (142, 74)):
        rijk.gloed(dk, x, y, 4, (LGROEN, GROEN), rnd)
        dk.px(x, y, WIT)
    bosgrond(dk, rnd, 84)
    mist(dk, rnd)
    stam(dk, 10, 7, 2, 92, rnd, takken=((30, 18, 1),))
    stam(dk, 58, 5, 6, 86, rnd, takken=((40, 12, -1),))
    stam(dk, 98, 4, 8, 82, rnd)
    stam(dk, 154, 8, 2, 94, rnd, takken=((26, 20, -1), (48, 12, -1)))
    kruispad(dk, rnd)
    # een modderplas midden op de open plek, met de voetsporen van Grom
    dk.poly([(52, 110), (82, 106), (108, 110), (102, 120), (66, 122), (48, 117)], BRUIN, ZWART)
    dither(dk, (48, 106, 108, 122), DGRIJS, 0.25, rnd, BRUIN)
    voetspoor(dk, 60, 117, 0.8, True)
    voetspoor(dk, 84, 111, 0.7, False)
    klem(dk, 124, 122)
    waarschuwingspaal(dk, 80, 96)
    bladerdak(dk, rnd)
    hangmos(dk, rnd, 8, 28)
    for x, y in ((140, 100), (146, 104), (6, 112)):              # rode paddenstoelen
        dk.rect(x, y - 2, x, y, LGRIJS)
        dk.ovaal(x - 2, y - 5, x + 2, y - 2, ROOD, ZWART)
        dk.px(x - 1, y - 4, WIT)
    vuurvliegjes(dk, rnd, 8, (4, 30, 100, 84))
    rijk.verrijk(dk, 411, lichten=[
        (80, 50, 30, 22, 0.5, {DGRIJS: GRIJS, BLAUW: PAARS}),   # het schemerlicht valt op de open plek
    ], sluit=(GEEL,))
    return afmaken(dk)


# ---- huterf -------------------------------------------------------------------------------------------------------
def blokhut(dk, rnd):
    """Groms hut op reuzenmaat: liggende boomstammen, een plankendak met mos, een stenen schoorsteen"""
    x1, x2, y_dak, y_muur, y_voet = 56, 159, 36, 50, 100
    # de muur van liggende stammen
    for y in range(y_muur, y_voet, 6):
        dk.rect(x1, y, x2, y + 5, BRUIN)
        dk.lijn([(x1, y), (x2, y)], ZWART)
        dk.lijn([(x1, y + 1), (x2, y + 1)], ORANJE)
        for x in range(x1 + 2, x2, 7):                           # nerven
            if rnd.random() < 0.7:
                dk.lijn([(x, y + 3), (x + rnd.randint(2, 4), y + 3)], DGRIJS)
        dk.ovaal(x1 - 3, y, x1 + 3, y + 5, ORANJE, ZWART)       # de koppen van de stammen op de hoek
        dk.px(x1, y + 2, BRUIN)
    # het dak: schuin, planken, overstek, mos en een paar losse planken
    dak = [(x1 - 10, y_muur + 2), (104, y_dak - 8), (x2 + 4, y_dak - 8), (x2 + 4, y_muur + 2)]
    dk.poly(dak, DGRIJS, ZWART)
    for i in range(0, 60, 4):                                    # planken in de lengte van het dak
        t = i / 60
        ya = y_muur + 2 - (y_muur + 2 - (y_dak - 8)) * t
        xa = x1 - 10 + (104 - (x1 - 10)) * t
        dk.lijn([(xa, ya), (x2 + 4, ya)], ZWART if i % 8 == 0 else BRUIN)
    for _ in range(140):                                         # mos op het dak
        x, y = rnd.randint(x1 - 8, x2), rnd.randint(y_dak - 8, y_muur)
        if dk.im.getpixel((x, y)) in (DGRIJS, GRIJS):
            dk.px(x, y, GROEN if rnd.random() < 0.7 else LGROEN)
    dk.lijn([(x1 - 10, y_muur + 2), (104, y_dak - 8)], ORANJE)   # de dakrand vangt het schemerlicht
    for x in range(x1 - 8, x2 + 4, 3):                           # de onderrand van het dak: overstekende planken
        dk.lijn([(x, y_muur + 2), (x, y_muur + 4)], BRUIN)
        dk.px(x, y_muur + 5, ZWART)
    # de schoorsteen van ruwe stenen
    rijk.stenen_muur(dk, 134, 12, 148, y_dak - 4, rnd, mos=GROEN, hoog=5, breed=6)
    dk.lijn([(133, 12), (133, y_dak - 4)], ZWART)
    dk.lijn([(149, 12), (149, y_dak - 4)], ZWART)
    dk.rect(132, 9, 150, 11, DGRIJS)
    dk.lijn([(132, 8), (150, 8)], ZWART)
    dk.ovaal(136, 6, 146, 10, ORANJE, ZWART)                    # gloed in de schoorsteen
    # de rook: dikke plukken die naar links waaien, door de lucht
    for i in range(16):
        x = 138 - i * 5 + 3 * math.sin(i * 0.7)
        y = 5 - i * 0.2 + 2 * math.sin(i * 0.9)
        r = 2 + i // 4
        dk.ovaal(x - r - 1, y - 2, x + r + 1, y + 2, LGRIJS if i < 4 else GRIJS, GRIJS if i < 8 else DGRIJS)


def deur(dk):
    """de reuzendeur: zware planken, ijzeren banden, een ring als klink, erboven een schedel met gewei"""
    x1, x2, y1, y2 = 100, 124, 52, 100
    dk.rect(x1 - 3, y1 - 4, x2 + 3, y2, DGRIJS)                  # de deurpost
    dk.lijn([(x1 - 3, y1 - 4), (x2 + 3, y1 - 4)], ZWART)
    dk.rect(x1, y1, x2, y2, BRUIN)
    for x in range(x1, x2, 6):
        dk.lijn([(x, y1), (x, y2)], ZWART)
        dk.lijn([(x + 1, y1), (x + 1, y2)], ORANJE)
    for y in (y1 + 8, y2 - 10):                                  # ijzeren banden met nagels
        dk.rect(x1, y, x2, y + 2, GRIJS)
        dk.lijn([(x1, y), (x2, y)], LGRIJS)
        for x in range(x1 + 2, x2, 5):
            dk.px(x, y + 1, ZWART)
    dk.ovaal(x2 - 7, 74, x2 - 2, 80, GRIJS, ZWART)               # de ring
    dk.ovaal(x2 - 6, 75, x2 - 3, 79, BRUIN, BRUIN)
    # boven de deur: een schedel met gewei (zoals bij de paal, maar groter)
    cx, cy = 112, 42
    for r in (-1, 1):
        dk.lijn([(cx + 3 * r, cy), (cx + 12 * r, cy - 6), (cx + 18 * r, cy - 14)], LGRIJS, 2)
        dk.lijn([(cx + 10 * r, cy - 5), (cx + 9 * r, cy - 13)], LGRIJS, 2)
        dk.lijn([(cx + 15 * r, cy - 10), (cx + 21 * r, cy - 11)], LGRIJS)
    dk.ovaal(cx - 5, cy - 4, cx + 5, cy + 6, WIT, ZWART)
    dk.ovaal(cx - 4, cy - 2, cx - 1, cy + 1, ZWART, ZWART)
    dk.ovaal(cx + 1, cy - 2, cx + 4, cy + 1, ZWART, ZWART)


def raam(dk):
    """links van de deur een raam met oranje licht en een kruis, een luik dat scheef hangt"""
    x1, x2, y1, y2 = 70, 90, 60, 78
    dk.rect(x1 - 2, y1 - 2, x2 + 2, y2 + 2, DGRIJS)
    dk.rect(x1, y1, x2, y2, ORANJE)
    dk.rect(x1 + 2, y1 + 2, x2 - 2, y2 - 6, GEEL)
    dk.rect(x1 + 6, y1 + 4, x2 - 6, y2 - 10, WIT)
    dk.lijn([((x1 + x2) // 2, y1), ((x1 + x2) // 2, y2)], ZWART, 2)
    dk.lijn([(x1, (y1 + y2) // 2), (x2, (y1 + y2) // 2)], ZWART, 2)
    dk.poly([(x1 - 12, y1 - 1), (x1 - 3, y1 - 2), (x1 - 3, y2 + 2), (x1 - 13, y2 + 4)], BRUIN, ZWART)   # het luik
    for y in range(y1 + 2, y2, 4):
        dk.lijn([(x1 - 12, y), (x1 - 4, y - 1)], DGRIJS)
    # het licht valt naar buiten op het erf: een trapezium oranje
    dk.poly([(x1, y2 + 22), (x2 + 2, y2 + 22), (x2 + 18, y2 + 44), (x1 - 8, y2 + 44)], BRUIN, BRUIN)


def huidenrek(dk, rnd):
    """links een rek van takken met twee gespannen huiden"""
    for x in (8, 46):
        dk.lijn([(x, 102), (x + 1, 48)], ZWART, 3)
        dk.lijn([(x, 102), (x + 1, 48)], BRUIN)
    dk.lijn([(4, 50), (52, 48)], ZWART, 3)
    dk.lijn([(4, 49), (52, 47)], BRUIN)
    for (hx, hy, k, d) in ((14, 52, BRUIN, DGRIJS), (32, 52, ORANJE, BRUIN)):
        huid = [(hx, hy), (hx + 12, hy), (hx + 14, hy + 8), (hx + 11, hy + 14), (hx + 13, hy + 26), (hx + 7, hy + 30),
                (hx + 1, hy + 26), (hx + 3, hy + 14), (hx - 1, hy + 8)]
        dk.poly(huid, k, ZWART)
        for _ in range(30):
            x, y = rnd.randint(hx, hx + 12), rnd.randint(hy + 1, hy + 28)
            if dk.im.getpixel((x, y)) == k:
                dk.px(x, y, d)
        for px_, py_ in ((hx, hy), (hx + 12, hy), (hx + 7, hy + 30)):   # touwtjes naar het rek
            dk.lijn([(px_, py_), (px_, py_ - 3)], LGRIJS)


def hakblok(dk, x, y):
    dk.rect(x - 8, y - 10, x + 8, y, BRUIN)
    dk.lijn([(x - 9, y - 10), (x - 9, y)], ZWART)
    dk.lijn([(x + 9, y - 10), (x + 9, y)], ZWART)
    dk.ovaal(x - 9, y - 13, x + 9, y - 7, ORANJE, ZWART)
    dk.ovaal(x - 5, y - 11, x + 5, y - 9, BRUIN, BRUIN)
    for i in range(-6, 7, 4):
        dk.lijn([(x + i, y - 7), (x + i, y - 1)], DGRIJS)
    # de bijl, schuin in het blok
    dk.lijn([(x + 2, y - 11), (x + 12, y - 30)], ZWART, 3)
    dk.lijn([(x + 2, y - 12), (x + 12, y - 30)], ORANJE)
    dk.poly([(x - 2, y - 14), (x + 6, y - 12), (x + 5, y - 6), (x - 4, y - 8)], LGRIJS, ZWART)
    dk.lijn([(x - 3, y - 9), (x + 5, y - 7)], WIT)
    # spaanders
    for dx, dy in ((-14, 0), (-11, 2), (13, 1), (16, -1), (-6, 3)):
        dk.lijn([(x + dx, y + dy), (x + dx + 2, y + dy - 1)], ORANJE)


def houtstapel(dk, rnd):
    """tegen de hut, rechts vooraan: een stapel gekloofd hout"""
    for rij, y in enumerate(range(98, 74, -6)):
        for i in range(5 - rij // 2):
            x = 136 + i * 5 + (rij % 2) * 2
            dk.ovaal(x, y - 5, x + 5, y, ORANJE, ZWART)
            dk.px(x + 2, y - 3, BRUIN)
            dk.px(x + 3, y - 2, BRUIN)


def ketel(dk, x, y):
    """een grote zwarte ketel aan een driepoot, met een smeulend vuurtje"""
    for (a, b) in (((x - 14, y + 6), (x, y - 26)), ((x + 14, y + 6), (x, y - 26)), ((x + 3, y + 8), (x, y - 26))):
        dk.lijn([a, b], ZWART, 3)
        dk.lijn([a, b], BRUIN)
    dk.lijn([(x, y - 26), (x, y - 14)], GRIJS)                   # de ketting
    dk.ovaal(x - 9, y - 16, x + 9, y + 2, DGRIJS, ZWART)
    dk.ovaal(x - 8, y - 16, x + 8, y - 12, ZWART, ZWART)
    dk.lijn([(x - 7, y - 11), (x - 7, y - 3)], GRIJS)            # glans
    dk.ovaal(x - 7, y + 2, x + 7, y + 7, DGRIJS, ZWART)          # de as en kooltjes
    for dx in (-4, -1, 2, 5):
        dk.px(x + dx, y + 4, ROOD)
        dk.px(x + dx - 1, y + 3, ORANJE)
    dk.px(x, y + 2, GEEL)


def huterf():
    rnd = random.Random(501)
    dk = Doek()
    rijk.lucht_met_wolken(dk, rnd, 84, kleuren=(ZWART, BLAUW, PAARS), sterren=16, wolken=3)
    # verre boomtoppen tegen de lucht (de open plek ligt in het bos)
    rand = golf(0, B - 1, 46, 6, rnd, stap=3, freq=0.4)
    dk.poly([(0, 84)] + rand + [(B - 1, 84)], ZWART, ZWART)
    for x, y in rand[::3]:
        dk.poly([(x - 3, y + 2), (x, y - 6), (x + 3, y + 2)], ZWART, ZWART)
    dk.poly([(0, 84)] + golf(0, B - 1, 60, 4, rnd, stap=4) + [(B - 1, 84)], BLAUW, BLAUW)
    dither(dk, (0, 56, B, 84), DGRIJS, 0.5, rnd, BLAUW)
    # het erf: aangestampte aarde met gras langs de randen
    dk.poly([(0, 92), (B - 1, 92), (B - 1, 126), (0, 126)], BRUIN, BRUIN)
    dither(dk, (0, 92, B, 126), ORANJE, 0.25, rnd, BRUIN)
    for _ in range(60):
        x, y = rnd.randint(0, B - 1), rnd.randint(94, 125)
        if x < 30 or y > 118:
            dk.lijn([(x, y), (x - 1, y - 3)], GROEN)
            dk.lijn([(x, y), (x + 1, y - 2)], LGROEN)
    stam(dk, 4, 5, 0, 94, rnd, takken=((20, 14, 1),))
    blokhut(dk, rnd)
    raam(dk)
    deur(dk)
    houtstapel(dk, rnd)
    huidenrek(dk, rnd)
    hakblok(dk, 36, 118)
    ketel(dk, 70, 112)
    # stenen langs het pad naar de deur
    for x, y in ((92, 106), (100, 112), (110, 118), (98, 122), (120, 108)):
        dk.ovaal(x - 3, y - 2, x + 3, y + 2, GRIJS, ZWART)
        dk.px(x - 1, y - 1, LGRIJS)
    rijk.verrijk(dk, 511, lichten=[
        (82, 98, 36, 22, 0.85, {BRUIN: ORANJE, DGRIJS: BRUIN, GRIJS: LGRIJS, ORANJE: GEEL, GROEN: LGROEN}),   # het raam
        (70, 116, 14, 8, 0.6, {BRUIN: ORANJE, DGRIJS: BRUIN, ORANJE: GEEL}),                                  # het vuurtje
    ], sluit=(PAARS, BLAUW, WIT))
    return afmaken(dk)


KAMERS = {"diepwoud": diepwoud, "wolfspad": wolfspad, "huterf": huterf}


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
