#!/usr/bin/env python3
"""maak_kamers.py — VOORLOPIGE kamerplaatjes voor hoofdstuk 1 van Hollow Crown, getekend met eenvoudige vormen.

    python3 tools/maak_kamers.py          schrijft data/plaatjes/*.png (640 x 256, verhouding 5:2)

Er zijn (nog) geen FLUX-plaatjes voor de herberg, de smidse en de bosrand. Deze plaatjes houden de plek warm:
maak je een FLUX-plaatje, zet het dan in data/kamers.txt en de rest (loopvakken, klikvakken) pas je daarop aan.
Elk plaatje komt in twee versies waar een patch nodig is (bv. de tafel verschoven, het smidsvuur aan).
Ook: plein_deur_open.png, het FLUX-plein met de herbergdeur open (voor de patch op het plein).

Coördinaten hieronder zijn in kamerpixels (160 x 128, zoals in de scripts) en worden x4 / x2 getekend.
"""
import os, random
from PIL import Image, ImageDraw, ImageFilter

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UIT = os.path.join(WORTEL, "data", "plaatjes")
W, H = 640, 256
# kleuren dicht bij het C64-palet (zie tools/c64beeld.py)
ZWART, WIT = (0, 0, 0), (255, 255, 255)
BRUIN, ORANJE, GEEL = (119, 83, 0), (183, 99, 30), (255, 255, 70)
DGRIJS, GRIJS, LGRIJS = (98, 98, 98), (148, 148, 148), (205, 205, 205)
GROEN, LGROEN = (98, 213, 50), (183, 255, 134)
ROOD, ROZE = (175, 60, 88), (238, 123, 149)
BLAUW, LBLAUW, CYAAN, PAARS = (44, 61, 236), (115, 133, 255), (126, 243, 214), (170, 64, 245)


def k(x, y):
    """kamerpixel -> tekenpixel (linkerboven)"""
    return x * 4, y * 2


def rect(d, x1, y1, x2, y2, kleur):
    d.rectangle([x1 * 4, y1 * 2, x2 * 4 + 3, y2 * 2 + 1], fill=kleur)


def vlekken(d, x1, y1, x2, y2, kleur, dicht, rnd):
    for _ in range(int((x2 - x1 + 1) * (y2 - y1 + 1) * dicht)):
        x, y = rnd.randint(x1, x2), rnd.randint(y1, y2)
        rect(d, x, y, x, y, kleur)


def planken_muur(d, x1, y1, x2, y2, rnd):
    rect(d, x1, y1, x2, y2, BRUIN)
    for x in range(x1, x2 + 1, 8):
        rect(d, x, y1, x, y2, ZWART if x % 16 == 0 else DGRIJS)
    vlekken(d, x1, y1, x2, y2, ORANJE, 0.06, rnd)


def stenen_muur(d, x1, y1, x2, y2, rnd, basis=DGRIJS, voeg=ZWART, licht=GRIJS):
    rect(d, x1, y1, x2, y2, basis)
    for i, y in enumerate(range(y1, y2 + 1, 6)):
        rect(d, x1, y, x2, y, voeg)
        for x in range(x1 + (4 if i % 2 else 0), x2 + 1, 10):
            rect(d, x, y, x, min(y + 5, y2), voeg)
    vlekken(d, x1, y1, x2, y2, licht, 0.05, rnd)


def vloer_planken(d, x1, y1, x2, y2, rnd):
    rect(d, x1, y1, x2, y2, ORANJE)
    for y in range(y1, y2 + 1, 5):
        rect(d, x1, y, x2, y, BRUIN)
    vlekken(d, x1, y1, x2, y2, BRUIN, 0.04, rnd)


def deur(d, x1, y1, x2, y2, open_=False):
    rect(d, x1 - 1, y1 - 1, x2 + 1, y2, ZWART)
    if open_:
        rect(d, x1, y1, x2, y2, GEEL)
        rect(d, x1, y1, x1 + (x2 - x1) // 3, y2, ORANJE)
    else:
        rect(d, x1, y1, x2, y2, BRUIN)
        for x in range(x1 + 2, x2, 3):
            rect(d, x, y1, x, y2, ORANJE)
        rect(d, x2 - 2, (y1 + y2) // 2, x2 - 2, (y1 + y2) // 2, GEEL)


def vat(d, x1, y1, x2, y2):
    rect(d, x1 - 1, y1 - 1, x2 + 1, y2, ZWART)
    rect(d, x1, y1, x2, y2, BRUIN)
    rect(d, x1 + 1, y1 + 1, x2 - 1, y2 - 1, ORANJE)
    for y in (y1 + 2, (y1 + y2) // 2, y2 - 2):
        rect(d, x1, y, x2, y, DGRIJS)


def kruik(d, x, y):
    rect(d, x + 1, y, x + 2, y + 1, LGRIJS)
    rect(d, x, y + 2, x + 3, y + 7, LGRIJS)
    rect(d, x + 1, y + 3, x + 2, y + 6, WIT)


def tafel(d, x1, y, x2):
    rect(d, x1 - 1, y - 1, x2 + 1, y + 4, ZWART)
    rect(d, x1, y, x2, y + 3, BRUIN)
    rect(d, x1 + 1, y, x2 - 1, y, DGRIJS)
    rect(d, x1 + 1, y + 4, x1 + 3, y + 14, ZWART)
    rect(d, x2 - 3, y + 4, x2 - 1, y + 14, ZWART)
    rect(d, x1 + 2, y + 4, x1 + 2, y + 13, BRUIN)
    rect(d, x2 - 2, y + 4, x2 - 2, y + 13, BRUIN)


def kruk(d, x, y):
    rect(d, x - 1, y - 1, x + 6, y + 2, ZWART)
    rect(d, x, y, x + 5, y + 1, BRUIN)
    rect(d, x + 1, y + 2, x + 1, y + 8, ZWART)
    rect(d, x + 4, y + 2, x + 4, y + 8, ZWART)


def vuur(d, x1, y1, x2, y2, rnd, aan=True):
    if not aan:
        rect(d, x1, y1, x2, y2, DGRIJS)
        vlekken(d, x1, y1, x2, y2, GRIJS, 0.3, rnd)
        return
    rect(d, x1, y1, x2, y2, ROOD)
    for _ in range((x2 - x1 + 1) * 3):
        x = rnd.randint(x1, x2)
        top = rnd.randint(y1, y2 - 2)
        rect(d, x, top, x, y2, ORANJE)
        rect(d, x, min(y2, top + 3), x, y2, GEEL)


def herberg(tafel_weg=False, met_kruik=True):
    rnd = random.Random(7)
    img = Image.new("RGB", (W, H), ZWART)
    d = ImageDraw.Draw(img)
    rect(d, 0, 1, 159, 6, DGRIJS)                       # balken in het plafond
    planken_muur(d, 0, 7, 159, 79, rnd)
    for x in (0, 40, 80, 120, 159):
        rect(d, x, 7, x + 1, 79, ZWART)
    # haard links, met vuur (warmte: Mira zit ernaast)
    stenen_muur(d, 4, 34, 34, 79, rnd)
    rect(d, 10, 52, 28, 79, ZWART)
    vuur(d, 12, 66, 26, 79, rnd)
    rect(d, 2, 30, 36, 34, GRIJS)
    # raam met schemering
    rect(d, 52, 22, 70, 42, ZWART)
    rect(d, 54, 24, 68, 40, PAARS)
    rect(d, 60, 24, 61, 40, ZWART)
    rect(d, 54, 31, 68, 32, ZWART)
    # toog rechts met plank en kruik
    rect(d, 104, 30, 156, 31, BRUIN)
    rect(d, 104, 44, 156, 45, BRUIN)
    for x in (110, 120, 132):
        rect(d, x, 36, x + 3, 43, GROEN if x == 120 else ROOD)
    if met_kruik:
        kruik(d, 142, 36)
    rect(d, 99, 57, 159, 79, ZWART)                   # de toog, met een zwarte rand
    rect(d, 100, 58, 158, 61, LGRIJS)
    rect(d, 100, 62, 158, 79, DGRIJS)
    for x in range(102, 158, 8):
        rect(d, x, 64, x + 5, 77, BRUIN)
    # vat lampolie bij de achterdeur
    vat(d, 88, 60, 98, 79)
    rect(d, 92, 56, 94, 59, LGRIJS)
    # deur naar het plein (links in de achterwand)
    deur(d, 40, 46, 50, 79)
    # vloer
    vloer_planken(d, 0, 80, 159, 125, rnd)
    rect(d, 0, 126, 159, 127, ZWART)
    # tafel met krukken (DUW tafel: hij schuift naar rechts en de ziensteen ligt eronder)
    tx = 72 if tafel_weg else 56
    tafel(d, tx, 90, tx + 30)
    kruk(d, tx - 8, 98)
    kruk(d, tx + 33, 98)
    if tafel_weg:
        rect(d, 60, 106, 63, 108, CYAAN)                # de ziensteen glinstert
        rect(d, 61, 105, 62, 105, WIT)
    return img


def smidse(vuur_aan=False):
    rnd = random.Random(11)
    img = Image.new("RGB", (W, H), ZWART)
    d = ImageDraw.Draw(img)
    stenen_muur(d, 0, 1, 159, 83, rnd)
    # vloer: aangestampte aarde
    rect(d, 0, 84, 159, 125, BRUIN)
    vlekken(d, 0, 84, 159, 125, ORANJE, 0.08, rnd)
    rect(d, 0, 126, 159, 127, ZWART)
    # het smidsvuur: grote haard in het midden achter
    rect(d, 52, 20, 104, 30, GRIJS)
    rect(d, 60, 8, 96, 20, DGRIJS)                      # de kap
    stenen_muur(d, 50, 30, 106, 83, rnd, basis=GRIJS, voeg=DGRIJS, licht=LGRIJS)
    rect(d, 60, 50, 96, 74, ZWART)
    vuur(d, 62, 56, 94, 74, rnd, aan=vuur_aan)
    # aambeeld
    rect(d, 112, 86, 136, 90, DGRIJS)
    rect(d, 118, 91, 130, 100, DGRIJS)
    rect(d, 114, 101, 134, 104, DGRIJS)
    rect(d, 112, 86, 136, 86, GRIJS)
    # gereedschap aan de muur
    for i, x in enumerate((14, 22, 30)):
        rect(d, x, 20, x + 1, 44, BRUIN)
        rect(d, x - 2, 44, x + 3, 48, DGRIJS if i != 1 else GRIJS)
    # Bram de smit (een figuur in het plaatje; hij praat via zijn voorwerp). Zo groot als Eldric vooraan.
    bx, by = 22, 56
    rect(d, bx + 2, by - 1, bx + 11, by + 9, ZWART)
    rect(d, bx + 3, by, bx + 10, by + 8, ROZE)           # hoofd
    rect(d, bx + 3, by, bx + 10, by + 2, ORANJE)         # rood haar
    rect(d, bx + 3, by + 6, bx + 10, by + 8, ORANJE)     # baard
    rect(d, bx + 5, by + 4, bx + 5, by + 4, ZWART)
    rect(d, bx + 8, by + 4, bx + 8, by + 4, ZWART)
    rect(d, bx, by + 9, bx + 13, by + 26, ZWART)
    rect(d, bx + 1, by + 10, bx + 12, by + 25, BRUIN)    # leren schort
    rect(d, bx + 4, by + 12, bx + 9, by + 24, ORANJE)
    rect(d, bx - 1, by + 11, bx, by + 20, ROZE)          # armen
    rect(d, bx + 13, by + 11, bx + 14, by + 20, ROZE)
    rect(d, bx + 2, by + 26, bx + 5, by + 34, DGRIJS)    # benen
    rect(d, bx + 8, by + 26, bx + 11, by + 34, DGRIJS)
    # deur naar het plein, rechts
    deur(d, 140, 50, 152, 83)
    return img


def bosrand():
    rnd = random.Random(23)
    img = Image.new("RGB", (W, H), ZWART)
    d = ImageDraw.Draw(img)
    # schemerlucht
    for y in range(1, 40):
        rect(d, 0, y, 159, y, PAARS if y < 20 else BLAUW)
    # donkere bomen: stammen met ronde kruinen, achteraan donkerder
    for laag, (kruin, stam) in enumerate(((ZWART, ZWART), (DGRIJS, BRUIN), ((40, 90, 30), BRUIN))):
        for i in range(9 - laag * 2):
            x = rnd.randint(-6, 156)
            if 60 < x < 96 and laag:
                continue                                   # het pad blijft vrij
            top = rnd.randint(4, 24) + laag * 6
            rect(d, x + 4, top + 14, x + 6, 80, stam)
            d.ellipse([x * 4, top * 2, (x + 12) * 4, (top + 22) * 2], fill=kruin)
            d.ellipse([(x - 3) * 4, (top + 10) * 2, (x + 15) * 4, (top + 30) * 2], fill=kruin)
    # het pad het Duisterwoud in (achteraan midden), donker
    d.polygon([k(70, 70), k(90, 70), k(110, 125), k(50, 125)], fill=BRUIN)
    d.polygon([k(75, 60), k(85, 60), k(90, 70), k(70, 70)], fill=DGRIJS)
    # gras
    rect(d, 0, 76, 159, 125, GROEN)
    vlekken(d, 0, 76, 159, 125, LGROEN, 0.05, rnd)
    d.polygon([k(72, 72), k(88, 72), k(104, 125), k(56, 125)], fill=GEEL)
    vlekken(d, 56, 76, 104, 125, ORANJE, 0.04, rnd)
    rect(d, 0, 126, 159, 127, ZWART)
    # een wegwijzer
    rect(d, 120, 70, 121, 96, BRUIN)
    rect(d, 112, 72, 132, 78, ORANJE)
    return img


def plein_deur_open():
    """Het FLUX-plein met de herbergdeur open: een warm verlicht deurgat (alleen voor de patch)."""
    img = Image.open(os.path.join(WORTEL, "data", "flux", "dawnhaven.png")).convert("RGB")
    d = ImageDraw.Draw(img)
    # de herbergdeur, in bronpixels: kamer x 136-141 (x 6,4), y 56-82 (190 + y x 3,2)
    x1, x2, y1, y2 = 866, 902, 372, 448
    d.rectangle([x1, y1, x2, y2], fill=(40, 20, 0))
    d.rectangle([x1 + 6, y1 + 6, x2 - 4, y2], fill=(255, 210, 90))
    d.rectangle([x1 + 6, y1 + 6, x1 + 14, y2], fill=(200, 120, 40))
    return img


def main():
    os.makedirs(UIT, exist_ok=True)
    plaatjes = {"herberg.png": herberg(), "herberg_tafel_weg.png": herberg(tafel_weg=True),
                "herberg_zonder_kruik.png": herberg(met_kruik=False),
                "smidse.png": smidse(), "smidse_vuur.png": smidse(vuur_aan=True),
                "bosrand.png": bosrand(), "plein_deur_open.png": plein_deur_open()}
    for naam, img in plaatjes.items():
        img.save(os.path.join(UIT, naam))
    print("[plaatjes] %s" % ", ".join(plaatjes))


if __name__ == "__main__":
    main()
