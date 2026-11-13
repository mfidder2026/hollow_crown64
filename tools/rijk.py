#!/usr/bin/env python3
"""rijk.py — tekenstukken voor rijke C64-pixelart (textuur, licht, schaduw), voor tools/teken_*.py.

Geen vlakke, klinische vlakken: elk vlak krijgt textuur of een verloop (om en om pixels, de C64-manier), elke kamer
een lichtbron die warm of koud op de dingen valt, en de dingen hebben slijtage: nerven, scheuren, mos, roest.
Alle functies werken op een Doek (tools/teken_toneel.py) in kamerpixels (160 x 128, kleurnummers 0-15).
"""
import math, random

from teken_toneel import (ZWART, WIT, ROOD, CYAAN, PAARS, GROEN, BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS,
                          LGROEN, LBLAUW, LGRIJS, B, H, golf)


def binnen(x, y):
    return 0 <= x < B and 0 <= y < H


def verloop(dk, x1, y1, x2, y2, kleuren, rnd, richting="v", ruis=0.15):
    """een verloop over een rechthoek door de kleuren heen (boven naar onder, of links naar rechts), met om en om
    pixels op de overgangen (en een beetje ruis, zodat het niet als strepen oogt)"""
    n = len(kleuren) - 1
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            t = (y - y1) / max(1, y2 - y1) if richting == "v" else (x - x1) / max(1, x2 - x1)
            f = t * n + rnd.uniform(-ruis, ruis)
            i = int(max(0, min(n, f)))
            rest = f - i
            k = kleuren[i]
            if i < n and (x + y) % 2 == 0 and rest > 0.5:
                k = kleuren[i + 1]
            elif i < n and rest > 0.8:
                k = kleuren[i + 1]
            dk.px(x, y, k)


def textuur(dk, vlak, kleuren, rnd, dicht=0.25, vorm="spik", gebied=None):
    """strooi textuur over alle pixels met kleur vlak: spikkels, streepjes (nerven) of klodders"""
    x1, y1, x2, y2 = gebied or (0, 0, B - 1, H - 1)
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if dk.im.getpixel((x, y)) != vlak or rnd.random() > dicht:
                continue
            k = rnd.choice(kleuren)
            if vorm == "spik":
                dk.px(x, y, k)
            elif vorm == "nerf":                                 # liggende streepjes: hout
                for i in range(rnd.randint(2, 5)):
                    if binnen(x + i, y) and dk.im.getpixel((x + i, y)) == vlak:
                        dk.px(x + i, y, k)
            elif vorm == "staand":                               # staande streepjes: schors, regen
                for i in range(rnd.randint(2, 4)):
                    if binnen(x, y + i) and dk.im.getpixel((x, y + i)) == vlak:
                        dk.px(x, y + i, k)


def licht(dk, cx, cy, rx, ry, kaart, rnd, kracht=1.0, gebied=None):
    """een lichtvlek rond (cx, cy): pixels met een kleur uit kaart worden lichter (kaart: van -> naar), sterk in het
    midden, met om en om pixels naar de rand (zo valt het licht van een lantaarn of een vuur op de dingen)"""
    x1, y1, x2, y2 = gebied or (int(cx - rx), int(cy - ry), int(cx + rx), int(cy + ry))
    for y in range(max(0, y1), min(H - 1, y2) + 1):
        for x in range(max(0, x1), min(B - 1, x2) + 1):
            d = math.hypot((x - cx) / rx, (y - cy) / ry)
            if d >= 1:
                continue
            k = dk.im.getpixel((x, y))
            if k not in kaart:
                continue
            p = (1 - d) * kracht
            if p > 0.6 or ((x + y) % 2 == 0 and rnd.random() < p * 1.4):
                dk.px(x, y, kaart[k])


def schaduw(dk, pts, kaart, rnd, dicht=0.6):
    """een schaduw onder of naast iets: binnen de veelhoek pts worden kleuren donkerder (kaart: van -> naar)"""
    from PIL import Image, ImageDraw
    masker = Image.new("1", (B, H), 0)
    ImageDraw.Draw(masker).polygon(pts, fill=1)
    for y in range(H):
        for x in range(B):
            if masker.getpixel((x, y)) and dk.im.getpixel((x, y)) in kaart:
                if (x + y) % 2 == 0 or rnd.random() < dicht - 0.5:
                    dk.px(x, y, kaart[dk.im.getpixel((x, y))])


def planken_vloer(dk, pts, rnd, basis=BRUIN, donker=DGRIJS, licht_=ORANJE, plank=5, spijkers=True):
    """een vloer of steiger van planken binnen de veelhoek pts: nerven, naden, spijkers, een paar kapotte plekken"""
    dk.poly(pts, basis, ZWART)
    ys = [p[1] for p in pts]
    xs = [p[0] for p in pts]
    for y in range(min(ys) + plank, max(ys), plank):              # de naden tussen de planken
        for x in range(min(xs), max(xs) + 1):
            if binnen(x, y) and dk.im.getpixel((x, y)) == basis:
                dk.px(x, y, ZWART)
            if binnen(x, y + 1) and dk.im.getpixel((x, y + 1)) == basis and x % 2 == 0:
                dk.px(x, y + 1, licht_)                          # de bovenrand van elke plank vangt licht
    textuur(dk, basis, [donker], rnd, 0.06, "nerf", (min(xs), min(ys), max(xs), max(ys)))
    if spijkers:
        for y in range(min(ys) + plank // 2, max(ys), plank):
            for x in range(min(xs) + rnd.randint(2, 9), max(xs), rnd.randint(14, 24)):
                if binnen(x, y) and dk.im.getpixel((x, y)) == basis:
                    dk.px(x, y, LGRIJS)
                    if binnen(x + 1, y):
                        dk.px(x + 1, y, ZWART)


def stenen_muur(dk, x1, y1, x2, y2, rnd, basis=GRIJS, donker=DGRIJS, licht_=LGRIJS, mos=None, hoog=7, breed=12):
    """een muur van ongelijke stenen: elke steen eigen breedte, een lichte bovenrand, een donkere onderrand, barsten,
    hier en daar een donkere of lichte steen, en (als je wilt) mos in de voegen"""
    dk.rect(x1, y1, x2, y2, ZWART)
    for rij, y in enumerate(range(y1, y2 + 1, hoog)):
        x = x1 - rnd.randint(0, breed)
        while x <= x2:
            b = breed + rnd.randint(-4, 4)
            k = basis
            if rnd.random() < 0.15:
                k = donker
            sx1, sx2 = max(x1, x + 1), min(x2, x + b - 1)
            sy1, sy2 = y + 1, min(y2, y + hoog - 1)
            if sx2 > sx1 and sy2 >= sy1:
                dk.rect(sx1, sy1, sx2, sy2, k)
                dk.lijn([(sx1, sy1), (sx2 - 1, sy1)], licht_ if k == basis else basis)
                if sy2 > sy1:
                    dk.lijn([(sx1 + 1, sy2), (sx2, sy2)], donker if k == basis else ZWART)
                if rnd.random() < 0.25:                          # een barst
                    bx = rnd.randint(sx1, sx2)
                    dk.lijn([(bx, sy1), (bx + rnd.randint(-2, 2), sy2)], ZWART)
                if mos is not None and rnd.random() < 0.3:      # mos onderaan de steen
                    for mx in range(sx1, sx2, 2):
                        if rnd.random() < 0.5:
                            dk.px(mx, sy2 + 1 if sy2 + 1 <= y2 else sy2, mos)
            x += b


def golven(dk, x1, y1, x2, y2, rnd, basis=BLAUW, donker=ZWART, kam=LBLAUW, schuim=WIT):
    """water: de basiskleur met donkere golfdalen en lichte golfkammen, dichterbij langer en verder uit elkaar"""
    dk.rect(x1, y1, x2, y2, basis)
    for y in range(y1 + 1, y2 + 1, 2):
        diep = (y - y1) / max(1, y2 - y1)
        lengte = 2 + int(diep * 6)
        stap = 7 + int(diep * 10)
        for x in range(x1 + rnd.randint(0, stap), x2, stap):
            dk.lijn([(x, y), (x + lengte, y)], donker if rnd.random() < 0.55 else basis)
            if rnd.random() < 0.45:
                dk.lijn([(x + 1, y - 1), (x + lengte - 1, y - 1)], kam)
            if diep > 0.6 and rnd.random() < 0.12:
                dk.px(x + lengte // 2, y - 1, schuim)


def weerschijn(dk, x, y1, y2, kleuren, rnd, breed=1.0):
    """een gebroken streep licht op het water onder een lamp of de maan"""
    for y in range(y1, y2, 2):
        b = int(1 + (y - y1) / 10 * breed)
        xx = x + rnd.randint(-2, 2)
        if rnd.random() < 0.8:
            dk.lijn([(xx - b, y), (xx + b, y)], kleuren[(y // 2) % len(kleuren)])


def gloed(dk, cx, cy, r, kleuren, rnd):
    """een gloed (halo) rond een lamp: ringen om en om pixels, van binnen naar buiten door de kleuren"""
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r * 1.6), int(cx + r * 1.6) + 1):
            if not binnen(x, y):
                continue
            d = math.hypot((x - cx) / 1.6, y - cy) / r
            if d >= 1:
                continue
            i = int(d * len(kleuren))
            if (x + y) % 2 == 0 or d < 0.35:
                if rnd.random() < 1.1 - d:
                    dk.px(x, y, kleuren[min(i, len(kleuren) - 1)])


def lucht_met_wolken(dk, rnd, tot, kleuren=(ZWART, BLAUW, PAARS), wolk=(DGRIJS, GRIJS), sterren=10, wolken=4):
    """een nachtelijke schemerlucht: een verloop, sterren, en een paar uitgerekte wolkenbanken met een lichte rand"""
    verloop(dk, 0, 1, B - 1, tot, list(kleuren), rnd)
    for _ in range(sterren):
        x, y = rnd.randint(1, B - 2), rnd.randint(2, tot // 2)
        dk.px(x, y, WIT if rnd.random() < 0.6 else LGRIJS)
    for _ in range(wolken):
        x, y = rnd.randint(-20, B - 20), rnd.randint(6, tot - 10)
        lengte = rnd.randint(30, 60)
        pts = [(x, y)] + golf(x, x + lengte, y - 2, 2, rnd, stap=5, freq=0.4) + [(x + lengte, y), (x + lengte - 6, y + 3),
                                                                                  (x + 6, y + 3)]
        dk.poly(pts, wolk[0], wolk[0])
        dk.lijn([(p[0], p[1] + 1) for p in pts[1:-3]], wolk[1])


def touw(dk, punten, kleur=BRUIN, licht_=ORANJE):
    """een touw tussen punten, met een gedraaid patroon"""
    dk.lijn(punten, kleur)
    (xa, ya), (xb, yb) = punten[0], punten[-1]
    n = max(2, int(math.hypot(xb - xa, yb - ya) / 2))
    for i in range(0, n, 2):
        t = i / n
        dk.px(xa + (xb - xa) * t, ya + (yb - ya) * t, licht_)


# ---- afwerken: een plaatje rijker maken, met ruis die alleen van de plek afhangt ----------------------------------
# (geen toevalsreeks: dan veranderen een plaatje en zijn patch alleen daar waar ze echt verschillen)
def ruis(x, y, zaad=0):
    """een vast getal 0..1 per pixel (een hash van x, y en het zaad)"""
    h = (x * 374761393 + y * 668265263 + zaad * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


LICHTER = {ZWART: DGRIJS, DGRIJS: GRIJS, GRIJS: LGRIJS, LGRIJS: WIT, BRUIN: ORANJE, ORANJE: GEEL, ROOD: ORANJE,
           BLAUW: LBLAUW, PAARS: ROZE, GROEN: LGROEN, LBLAUW: WIT, ROZE: WIT, GEEL: WIT, CYAAN: WIT, LGROEN: WIT}
DONKERDER = {WIT: LGRIJS, LGRIJS: GRIJS, GRIJS: DGRIJS, DGRIJS: ZWART, ORANJE: BRUIN, GEEL: ORANJE, BRUIN: DGRIJS,
             LBLAUW: BLAUW, BLAUW: ZWART, ROZE: ROOD, ROOD: BRUIN, LGROEN: GROEN, GROEN: DGRIJS, PAARS: BLAUW,
             CYAAN: LBLAUW}
TEXTUUR = {   # kleur: (kans, kleuren, vorm)   vorm: spik (spikkel), nerf (liggend streepje), staand
    BRUIN: (0.10, (DGRIJS,), "nerf"), ORANJE: (0.06, (BRUIN,), "nerf"),
    GRIJS: (0.10, (DGRIJS, LGRIJS), "spik"), DGRIJS: (0.07, (GRIJS, ZWART), "spik"),
    LGRIJS: (0.08, (GRIJS, WIT), "spik"), GROEN: (0.12, (LGROEN, DGRIJS), "staand"),
    WIT: (0.06, (LGRIJS, LBLAUW), "spik"), LBLAUW: (0.06, (WIT, BLAUW), "spik"),
}


def verrijk(dk, zaad, lichten=(), randlicht=True, textuur_=True, sluit=()):
    """werkt een plaatje af:
      textuur per materiaal (TEXTUUR), randlicht (een pixel met een zwarte rand erboven wordt lichter, met een zwarte
      rand eronder donkerder: volume), en lichtpoelen: lichten = [(cx, cy, rx, ry, kracht, kaart)], kaart van -> naar
      (None = LICHTER). sluit = kleuren die blijven zoals ze zijn (bv. de lucht)."""
    im = dk.im
    oud = im.copy()
    for y in range(1, H - 2):
        for x in range(B):
            k = oud.getpixel((x, y))
            if k == ZWART or k in sluit:
                continue
            nieuw = k
            if randlicht:
                if oud.getpixel((x, y - 1)) == ZWART and k in LICHTER and ruis(x, y, zaad + 1) < 0.85:
                    nieuw = LICHTER[k]
                elif y + 1 < H and oud.getpixel((x, y + 1)) == ZWART and k in DONKERDER and ruis(x, y, zaad + 2) < 0.6:
                    nieuw = DONKERDER[k]
            if nieuw == k and textuur_ and k in TEXTUUR:
                kans, kleuren, vorm = TEXTUUR[k]
                kans *= float(textuur_)                          # (True = 1: de gewone dichtheid; 0.5 = de helft)
                rx = x // 3 if vorm == "nerf" else x
                ry = y // 3 if vorm == "staand" else y
                if ruis(rx, ry, zaad + 3) < kans:
                    nieuw = kleuren[int(ruis(rx, ry, zaad + 4) * len(kleuren))]
            if nieuw != k:
                im.putpixel((x, y), nieuw)
    for cx, cy, rx, ry, kracht, kaart in lichten:
        kaart = kaart or LICHTER
        for y in range(max(1, int(cy - ry)), min(H - 2, int(cy + ry)) + 1):
            for x in range(max(0, int(cx - rx)), min(B - 1, int(cx + rx)) + 1):
                d = math.hypot((x - cx) / rx, (y - cy) / ry)
                k = im.getpixel((x, y))
                if d >= 1 or k not in kaart or k in sluit:
                    continue
                p = (1 - d) * kracht
                if p > 0.65 or ((x + y) % 2 == 0 and ruis(x, y, zaad + 5) < p * 1.5):
                    im.putpixel((x, y), kaart[k])
