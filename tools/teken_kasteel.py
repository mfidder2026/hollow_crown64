#!/usr/bin/env python3
"""teken_kasteel.py — het Vergeten Kasteel (hoofdstuk 6): de plaatjes van het laatste hoofdstuk, met de hand getekend.

    python3 tools/teken_kasteel.py [naam ...]  schrijft data/plaatjes/<naam>.png (en patches), build/proef/<naam>_groot.png

  kerker     een cel van steen, stro, een raampje hoog in de muur, tralies (patch tralies_open)
  poort      de binnenpoort: een hoge deur boven een trap, vier spookridders ervoor (patches ridders_l/ridders_r:
             in stukken; poort_open: de deur open)
  troonzaal  een hal met zuilen; Grom op zijn troon van rots (zonder kroon), aardmannetjes in de nissen
  maankamer  de Holle Kroon op een sokkel onder een open koepel, met oma's zonnesteen ernaast; spiegels eromheen
             (patches kroon_weg, steen_weg). Verblindend wit tot de spiegels beslagen zijn: dat doet het script (KLEUR)
  dak        het dak van het kasteel bij de laatste schemer: kantelen, en een grote zon (de manen zijn figuren: ze
             schuiven er in de slotscène vanaf)
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from teken_toneel import (Doek, rgb, te_veel_kleuren, golf, dither, ZWART, WIT, ROOD, CYAAN, PAARS, GROEN,   # noqa: E402
                          BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW, LGRIJS, B, H)
from teken_bospad import kleuren_per_vakje   # noqa: E402
from teken_zee import nachtlucht, verduisterde_zon, rand   # noqa: E402
import teken_grot   # noqa: E402
import rijk   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stenen_muur(dk, y1, y2, kleur=DGRIJS, voeg=ZWART, licht=GRIJS, rnd=None):
    dk.rect(0, y1, B - 1, y2, kleur)
    for i, y in enumerate(range(y1, y2 + 1, 7)):
        dk.lijn([(0, y), (B - 1, y)], voeg)
        for x in range((i % 2) * 8, B, 16):
            dk.lijn([(x, y), (x, min(y + 6, y2))], voeg)
            dk.lijn([(x + 1, y + 1), (x + 6, y + 1)], licht)


def harnas(dk, x, y, kapot=False):
    """een spookridder: een leeg harnas, x = midden, y = voeten"""
    if kapot:
        dk.poly([(x - 6, y), (x - 4, y - 5), (x + 4, y - 6), (x + 7, y - 1)], LGRIJS, ZWART)
        dk.ovaal(x + 3, y - 9, x + 9, y - 4, LGRIJS, ZWART)
        dk.lijn([(x + 4, y - 7), (x + 8, y - 7)], ZWART)
        dk.rect(x - 9, y - 2, x - 6, y, GRIJS)
        return
    dk.rect(x - 3, y - 16, x - 2, y, DGRIJS)                     # benen, lang en dun
    dk.rect(x + 2, y - 16, x + 3, y, DGRIJS)
    dk.rect(x - 4, y - 1, x - 1, y, DGRIJS)                      # ijzeren schoenen
    dk.rect(x + 1, y - 1, x + 4, y, DGRIJS)
    dk.poly([(x - 4, y - 16), (x - 6, y - 30), (x + 6, y - 30), (x + 4, y - 16)], LGRIJS, ZWART)   # borst
    dk.lijn([(x - 2, y - 28), (x - 2, y - 18)], WIT)             # licht op het metaal
    dk.lijn([(x - 4, y - 18), (x + 4, y - 18)], GRIJS)           # de riem
    dk.ovaal(x - 8, y - 32, x - 4, y - 27, GRIJS, ZWART)         # schouderstukken
    dk.ovaal(x + 4, y - 32, x + 8, y - 27, GRIJS, ZWART)
    dk.lijn([(x - 7, y - 27), (x - 7, y - 16)], DGRIJS)          # armen
    dk.lijn([(x + 7, y - 27), (x + 7, y - 16)], DGRIJS)
    dk.lijn([(x + 8, y - 34), (x + 8, y - 8)], LBLAUW)           # een zwaard, de punt op de grond
    dk.poly([(x - 3, y - 31), (x - 4, y - 38), (x - 2, y - 42), (x + 2, y - 42), (x + 4, y - 38), (x + 3, y - 31)],
            LGRIJS, ZWART)                                       # de helm: smal en hoog
    dk.lijn([(x - 3, y - 37), (x + 3, y - 37)], ZWART)           # het vizier: leeg en donker
    dk.lijn([(x, y - 43), (x - 2, y - 47)], ROOD)                # een pluim


# ---- de kerker ----------------------------------------------------------------------------------------------------
TRALIES = (112, 24, 40, 80)      # patch tralies_open: de tralies uit hun sponning (uitgepakt 1000 bytes)


def kerker(open_=False):
    rnd = random.Random(171)
    dk = Doek()
    stenen_muur(dk, 1, 84)
    dk.rect(24, 12, 44, 30, ZWART)                               # een raampje hoog in de muur, met de zwarte zon
    dk.rect(25, 13, 43, 29, PAARS)
    verduisterde_zon(dk, 34, 21, 5)
    for x in (30, 34, 38):
        dk.lijn([(x, 13), (x, 29)], ZWART)
    dk.lijn([(10, 40), (14, 52), (12, 60)], LGRIJS)              # een ketting aan de muur
    dk.ovaal(9, 58, 15, 64, None, LGRIJS)
    # de vloer met stro
    dk.rect(0, 85, B - 1, 125, BRUIN)
    for _ in range(60):
        x, y = rnd.randint(0, 100), rnd.randint(90, 124)
        dk.lijn([(x, y), (x + rnd.randint(2, 5), y + rnd.randint(-1, 1))], GEEL if rnd.random() < 0.6 else ORANJE)
    dk.lijn([(0, 85), (B - 1, 85)], ZWART)
    # de deur van tralies rechts
    dk.rect(110, 24, 152, 100, ZWART)
    dk.rect(112, 26, 150, 100, DGRIJS)                           # de gang erachter, schemerig
    for y in range(30, 100, 9):
        dk.lijn([(112, y), (150, y)], ZWART)
    if open_:
        for i, x in enumerate(range(116, 150, 6)):               # losgerammelde tralies, scheef op de vloer
            dk.lijn([(x, 100), (x + 10 - i * 3, 70 + i * 4)], GRIJS)
        dk.lijn([(112, 26), (150, 26)], GRIJS)
    else:
        for x in range(116, 150, 6):
            dk.rect(x, 26, x + 1, 100, GRIJS)
            dk.px(x, 26, LGRIJS)
        dk.rect(112, 58, 150, 60, GRIJS)                         # een dwarsbalk met een slot
        dk.rect(138, 60, 142, 66, GEEL)
    rijk.verrijk(dk, 171, lichten=[(34, 36, 30, 40, 0.5, {DGRIJS: GRIJS, BRUIN: ORANJE, GRIJS: LGRIJS}),
                                   (132, 60, 26, 40, 0.4, {DGRIJS: BRUIN, GRIJS: ORANJE})], sluit=(PAARS,),
                 textuur_=0.0)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de poort -----------------------------------------------------------------------------------------------------
RIDDERS_L = (28, 48, 52, 56)     # patches: de linker en rechter twee ridders in stukken (elk 91 vakjes)
RIDDERS_R = (80, 48, 52, 56)
POORT = (52, 8, 56, 48)          # patch poort_open


def poort(stand=None):
    rnd = random.Random(181)
    dk = Doek()
    nachtlucht(dk, rnd, 20)
    stenen_muur(dk, 8, 104, kleur=GRIJS, voeg=DGRIJS, licht=GRIJS)   # (zonder lichte randjes: past beter)
    # de hoge poort boven een trap
    dk.poly([(54, 56), (54, 22), (60, 16), (80, 12), (100, 16), (106, 22), (106, 56)], DGRIJS, ZWART)
    if stand == "open":
        dk.poly([(58, 56), (58, 24), (64, 18), (80, 15), (96, 18), (102, 24), (102, 56)], ZWART, ZWART)
        dk.lijn([(70, 54), (90, 54)], DGRIJS)                    # een gang naar binnen
    else:
        dk.poly([(58, 56), (58, 24), (64, 18), (80, 15), (96, 18), (102, 24), (102, 56)], BRUIN, ZWART)
        dk.lijn([(80, 15), (80, 56)], ZWART)
        for y in (26, 40, 52):
            dk.lijn([(58, y), (102, y)], DGRIJS)
        dk.ovaal(76, 34, 84, 42, GEEL, ZWART)                    # het slot: een schubvormig gat
        dk.ovaal(78, 36, 82, 40, ZWART, ZWART)
    for i, y in enumerate(range(56, 66, 3)):                     # de trap
        dk.rect(50 - i * 4, y, 110 + i * 4, y + 3, LGRIJS)
        dk.lijn([(50 - i * 4, y + 3), (110 + i * 4, y + 3)], DGRIJS)
    # de binnenplaats
    dk.rect(0, 104, B - 1, 125, DGRIJS)
    for x in range(0, B, 12):
        dk.lijn([(x, 104), (x - 6, 125)], ZWART)
    for y in (110, 118):
        dk.lijn([(0, y), (B - 1, y)], ZWART)
    for i, x in enumerate((40, 64, 96, 120)):
        harnas(dk, x, 100, kapot=(stand in ("kapot", "open")))   # (voeten op 100: alles blijft in de vakken van de patches)
    for x in (6, 152):                                           # fakkels aan de muur
        dk.rect(x - 1, 50, x + 1, 62, BRUIN)
        dk.poly([(x - 3, 50), (x, 42), (x + 3, 50)], ORANJE, ROOD)
    rijk.verrijk(dk, 181, lichten=[(6, 50, 18, 22, 0.5, {GRIJS: ORANJE, DGRIJS: BRUIN, LGRIJS: GEEL}),
                                   (152, 50, 18, 22, 0.5, {GRIJS: ORANJE, DGRIJS: BRUIN, LGRIJS: GEEL})],
                 sluit=(PAARS,), textuur_=0.0, randlicht=False)
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de troonzaal -------------------------------------------------------------------------------------------------
def troonzaal():
    rnd = random.Random(191)
    dk = Doek()
    dk.rect(0, 1, B - 1, 125, BLAUW)
    for y in range(1, 112):                                      # een donkere hal, koud licht van boven
        for x in range((y % 2), B, 2):
            if rnd.random() < 0.55:
                dk.px(x, y, ZWART)
    for x in (12, 148):                                          # zuilen
        dk.rect(x - 6, 1, x + 6, 112, DGRIJS)
        dk.lijn([(x - 6, 1), (x - 6, 112)], ZWART)
        dk.lijn([(x + 6, 1), (x + 6, 112)], ZWART)
        dk.lijn([(x - 3, 1), (x - 3, 112)], GRIJS)
    for x, y in ((26, 50), (26, 74), (134, 50), (134, 74)):     # nissen met aardmannetjes die kijken
        dk.ovaal(x - 6, y - 5, x + 6, y + 7, ZWART, DGRIJS)
        dk.px(x - 2, y + 1, GEEL)
        dk.px(x + 2, y + 1, GEEL)
    for x in (34, 126):                                          # banieren met een maan
        dk.poly([(x - 6, 6), (x + 6, 6), (x + 6, 34), (x, 30), (x - 6, 34)], PAARS, ZWART)
        dk.ovaal(x - 3, 12, x + 3, 18, LGRIJS, ZWART)
    dk.rect(0, 112, B - 1, 125, DGRIJS)                          # de vloer
    for x in range(0, B, 16):
        dk.lijn([(x, 112), (x - 8, 125)], ZWART)
    teken_grot.troon(dk)                                         # Grom op zijn troon, zonder kroon (die staat boven)
    teken_grot.grom(dk)
    rijk.verrijk(dk, 191, lichten=[(80, 10, 70, 60, 0.35, {BLAUW: LBLAUW, DGRIJS: GRIJS})])
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- de maankamer -------------------------------------------------------------------------------------------------
KROON = (68, 48, 24, 24)         # patch kroon_weg: de kroon is van de sokkel
STEEN = (92, 56, 12, 16)         # patch steen_weg: oma's zonnesteen is opgepakt


def maankamer(kroon=True, steen=True):
    rnd = random.Random(201)
    dk = Doek()
    # de open koepel: een cirkel hemel met de zon en de manen
    dk.rect(0, 1, B - 1, 125, DGRIJS)
    dk.ovaal(40, -30, 120, 40, PAARS, ZWART)
    verduisterde_zon(dk, 80, 14, 7)
    for a in range(200, 341, 20):                                # de ribben van de koepel
        r = math.radians(a)
        dk.lijn([(80 + 40 * math.cos(r), 5 + 35 * math.sin(r) + 30), (80 + 70 * math.cos(r), 40 + 60 * math.sin(r))],
                ZWART)
    # spiegels in een kring rondom
    for x in (18, 46, 114, 142):
        dk.ovaal(x - 10, 46, x + 10, 96, LBLAUW, ZWART)
        dk.ovaal(x - 7, 50, x + 7, 92, WIT, LBLAUW)
        dk.lijn([(x - 3, 54), (x - 5, 70)], LBLAUW)
    # de sokkel met de kroon
    dk.poly([(66, 110), (70, 72), (90, 72), (94, 110)], GRIJS, ZWART)
    dk.rect(64, 70, 96, 74, LGRIJS)
    dk.lijn([(64, 74), (96, 74)], ZWART)
    if kroon:
        y0 = 70
        pts = [(80 - 10, y0), (80 - 11, y0 - 7), (80 - 8, y0 - 4), (80 - 6, y0 - 11), (80 - 3, y0 - 5), (80, y0 - 13),
               (80 + 3, y0 - 5), (80 + 6, y0 - 11), (80 + 8, y0 - 4), (80 + 11, y0 - 7), (80 + 10, y0)]
        dk.poly(pts, ZWART, ZWART)
        dk.lijn(pts[1:-1], LGRIJS)
        for r in (-1, 1):
            dk.ovaal(80 + r * 6 - 2, y0 - 8, 80 + r * 6 + 2, y0 - 3, LBLAUW, ZWART)
            dk.px(80 + r * 6 - 1, y0 - 7, WIT)
    if steen:
        dk.ovaal(94, 64, 100, 70, GEEL, ORANJE)                  # oma's steentje, naast de kroon
        dk.px(96, 66, WIT)
    dk.rect(0, 110, B - 1, 125, GRIJS)                           # de vloer
    for x in range(0, B, 16):
        dk.lijn([(x, 110), (x - 8, 125)], DGRIJS)
    dk.poly([(0, 110), (0, 90), (6, 86), (12, 90), (12, 110)], ZWART, GRIJS)   # de deur terug
    rijk.verrijk(dk, 201, lichten=[(80, 20, 60, 50, 0.4, {DGRIJS: GRIJS, GRIJS: LGRIJS})], sluit=(PAARS,))
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


# ---- het dak ------------------------------------------------------------------------------------------------------
def dak():
    rnd = random.Random(211)
    dk = Doek()
    dk.rect(0, 1, B - 1, 90, PAARS)                              # de hemel (de slotscène kleurt hem: KLEUR)
    dk.ovaal(66, 10, 94, 38, GEEL, ORANJE)                       # de zon zelf (de manen ervoor zijn figuren)
    dk.ovaal(70, 14, 90, 34, GEEL, GEEL)
    for x, y in ((20, 20), (140, 12), (120, 40), (34, 50)):
        dk.px(x, y, WIT)
    # ver weg de bergen, met op de verste top het baken: een witte bundel
    dk.poly([(0, 90), (20, 70), (40, 80), (64, 64), (90, 78), (118, 60), (140, 72), (159, 66), (159, 90)],
            DGRIJS, ZWART)                                       # (niet blauw: de slotscène kleurt het blauw van de lucht)
    dk.lijn([(118, 60), (118, 40)], WIT)
    # het dak: kantelen vooraan, stenen vloer
    dk.rect(0, 90, B - 1, 125, GRIJS)
    for x in range(0, B, 20):
        dk.rect(x, 86, x + 10, 98, LGRIJS)
        dk.lijn([(x, 86), (x + 10, 86)], ZWART)
        dk.lijn([(x, 86), (x, 98)], ZWART)
        dk.lijn([(x + 10, 86), (x + 10, 98)], ZWART)
    dk.lijn([(0, 98), (B - 1, 98)], ZWART)
    for y in range(104, 126, 7):
        dk.lijn([(0, y), (B - 1, y)], DGRIJS)
    rijk.verrijk(dk, 211, sluit=(PAARS, GEEL, ORANJE))
    rand(dk)
    kleuren_per_vakje(dk.im)
    return dk.im


PLAATJES = {"kerker": kerker, "kerker_open": lambda: kerker(True),
            "poort": poort, "poort_kapot": lambda: poort("kapot"), "poort_open": lambda: poort("open"),
            "troonzaal": troonzaal,
            "maankamer": maankamer, "maankamer_zonder_kroon": lambda: maankamer(kroon=False),
            "maankamer_zonder_steen": lambda: maankamer(steen=False),
            "dak": dak}
PATCHES = {"kerker_open": ("kerker", TRALIES),
           "maankamer_zonder_kroon": ("maankamer", KROON), "maankamer_zonder_steen": ("maankamer", STEEN)}
# (poort_kapot en poort_open raken twee vakken; data/kamers.txt knipt ze in ridders_l, ridders_r en poort_open)


def main():
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    namen = sys.argv[1:] or list(PLAATJES)
    gemaakt = {}
    for naam in namen:
        im = gemaakt[naam] = PLAATJES[naam]()
        rgb(im).save(os.path.join(WORTEL, "data", "plaatjes", naam + ".png"))
        rgb(im, 8, 4).save(os.path.join(WORTEL, "build", "proef", naam + "_groot.png"))
        print("[kasteel] data/plaatjes/%s.png; vakjes met meer dan 3 kleuren + zwart: %d" % (naam, te_veel_kleuren(im)))
        if naam in PATCHES:
            basis_naam, (px, py, pb, ph) = PATCHES[naam]
            basis = gemaakt.get(basis_naam) or PLAATJES[basis_naam]()
            buiten = sum(1 for y in range(H) for x in range(B) if basis.getpixel((x, y)) != im.getpixel((x, y))
                         and not (px <= x < px + pb and py <= y < py + ph))
            if buiten or px % 4 or pb % 4 or py % 8 or ph % 8 or (pb // 4) * (ph // 8) * 10 > 1024:
                raise SystemExit("[kasteel] patch %s: %d pixels buiten het vak %s (of niet op vakjes, of te groot)"
                                 % (naam, buiten, (px, py, pb, ph)))
    for naam, (px, py, pb, ph) in (("poort_kapot", RIDDERS_L), ("poort_kapot", RIDDERS_R), ("poort_open", POORT)):
        if naam in gemaakt:                                      # ook deze vakken: niet op vakjes of te groot?
            if px % 4 or pb % 4 or py % 8 or ph % 8 or (pb // 4) * (ph // 8) * 10 > 1024:
                raise SystemExit("[kasteel] vak %s van %s klopt niet" % ((px, py, pb, ph), naam))
    if "poort_kapot" in gemaakt or "poort_open" in gemaakt:
        for naam, basis_naam, vakken in (("poort_kapot", "poort", (RIDDERS_L, RIDDERS_R)),
                                         ("poort_open", "poort_kapot", (POORT,))):   # (open komt na de ridders)
            basis = gemaakt.get(basis_naam) or PLAATJES[basis_naam]()
            im = gemaakt.get(naam) or PLAATJES[naam]()
            buiten = sum(1 for y in range(H) for x in range(B) if basis.getpixel((x, y)) != im.getpixel((x, y))
                         and not any(px <= x < px + pb and py <= y < py + ph for px, py, pb, ph in vakken))
            if buiten:
                raise SystemExit("[kasteel] %s: %d pixels buiten zijn vakken" % (naam, buiten))


if __name__ == "__main__":
    main()
