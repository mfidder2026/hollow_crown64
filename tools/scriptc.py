#!/usr/bin/env python3
"""scriptc.py — de compiler voor de scripts van Hollow Crown (scripts/*.hcs, §6.4).

    python3 tools/scriptc.py scripts build/gen      schrijft build/gen/spel.asm

Hoofdstuk 2: alleen KAMER, LOOPVAK, SCHAAL en BEGIN. De rest van de taal (VOORWERP, ZEG, ALS, ...) komt in hoofdstuk 4;
onbekende woorden zijn tot dan een fout, zodat er niets stilletjes wordt overgeslagen.

    KAMER naam
      LOOPVAK x1,y1 x2,y2        rechthoek in kamercoördinaten: x 0-159 (multicolor-pixels), y 0-127
      LOOPKLEUREN kleur ...      de kleuren waar de voeten op mogen (standaard: groen lichtgroen geel). Elk
                                 LOOPVAK moet daar (bijna) helemaal op liggen: zie tools/loopkaart.py.
      VRIJ x1,y1 x2,y2           hier geldt de kleurcontrole niet (bv. de waterstraal van de fontein boven het gras,
                                 of later een geheime doorgang). Zet er een opmerking bij waarom.
      ACHTER x1,y1 x2,y2         staan Eldric's voeten hier, dan komt de voorgrond van de kamer (data/kamers.txt,
                                 voorgrond=...) vóór hem: hij loopt achter het torentje langs. Hooguit één per kamer.
      SCHAAL y1 y2 ...           diepte: voeten op y >= y1 = maat 0 (groot), >= y2 = maat 1, ...; daarachter
                                 de volgende maat. Aflopend, hooguit 3 grenzen (4 maten in tools/costume.py).
    BEGIN kamer x,y richting      waar Eldric begint (richting: VOOR RUG RECHTS LINKS)

Controles: vakken binnen de kamer en niet leeg; vakken op de loopkleuren van het kamerplaatje
(build/gen/kamer_<naam>.bin, dus de kamers worden eerst omgezet); hooguit 16 per kamer; elk vak bereikbaar vanuit elk ander
(anders kan de speler vast komen te zitten); BEGIN staat in een loopvak.

In de uitvoer zijn x-waarden schermpixels (x * 2, rechterrand x2 * 2 + 1): zo rekent de motor.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

KAMER_B, KAMER_H = 160, 128
MAX_VAKKEN = 16
MAX_SCHAAL = 3           # grenzen; de motor heeft MATEN = 4 maten (tools/costume.py)
RICHTINGEN = {"VOOR": 0, "RUG": 1, "RECHTS": 2, "LINKS": 3}


class Fout(Exception):
    pass


def punt(tekst, waar):
    m = re.fullmatch(r"(\d+),(\d+)", tekst)
    if not m:
        raise Fout("%s: verwacht x,y, niet %r" % (waar, tekst))
    return int(m.group(1)), int(m.group(2))


def lees(bestanden):
    kamers, volgorde, begin = {}, [], None
    for pad in bestanden:
        kamer = None
        for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
            waar = "%s:%d" % (pad, nr)
            woorden = regel.split("#", 1)[0].split()
            if not woorden:
                continue
            w = woorden[0]
            if w == "KAMER":
                if len(woorden) != 2:
                    raise Fout("%s: KAMER naam" % waar)
                kamer = woorden[1]
                if kamer in kamers:
                    raise Fout("%s: kamer %s bestaat al" % (waar, kamer))
                kamers[kamer] = {"vakken": [], "waar": waar, "schaal": [], "kleuren": None, "vrij": [], "achter": None}
                volgorde.append(kamer)
            elif w == "LOOPVAK":
                if kamer is None:
                    raise Fout("%s: LOOPVAK buiten een KAMER" % waar)
                if len(woorden) != 3:
                    raise Fout("%s: LOOPVAK x1,y1 x2,y2" % waar)
                (x1, y1), (x2, y2) = punt(woorden[1], waar), punt(woorden[2], waar)
                if not (x1 <= x2 < KAMER_B and y1 <= y2 < KAMER_H):
                    raise Fout("%s: loopvak buiten de kamer (0-%d, 0-%d) of leeg" % (waar, KAMER_B - 1, KAMER_H - 1))
                kamers[kamer]["vakken"].append((x1, y1, x2, y2, waar))
            elif w == "ACHTER":
                if kamer is None or len(woorden) != 3:
                    raise Fout("%s: ACHTER x1,y1 x2,y2 (binnen een KAMER)" % waar)
                if kamers[kamer]["achter"]:
                    raise Fout("%s: hooguit één ACHTER per kamer" % waar)
                (x1, y1), (x2, y2) = punt(woorden[1], waar), punt(woorden[2], waar)
                if not (x1 <= x2 < KAMER_B and y1 <= y2 < KAMER_H):
                    raise Fout("%s: ACHTER-vak buiten de kamer of leeg" % waar)
                kamers[kamer]["achter"] = (x1, y1, x2, y2, waar)
            elif w == "VRIJ":
                if kamer is None or len(woorden) != 3:
                    raise Fout("%s: VRIJ x1,y1 x2,y2 (binnen een KAMER)" % waar)
                (x1, y1), (x2, y2) = punt(woorden[1], waar), punt(woorden[2], waar)
                if not (x1 <= x2 < KAMER_B and y1 <= y2 < KAMER_H):
                    raise Fout("%s: VRIJ-gebied buiten de kamer of leeg" % waar)
                kamers[kamer]["vrij"].append((x1, y1, x2, y2))
            elif w == "LOOPKLEUREN":
                if kamer is None or len(woorden) < 2:
                    raise Fout("%s: LOOPKLEUREN kleur ... (binnen een KAMER)" % waar)
                kamers[kamer]["kleuren"] = (woorden[1:], waar)
            elif w == "SCHAAL":
                if kamer is None:
                    raise Fout("%s: SCHAAL buiten een KAMER" % waar)
                try:
                    grenzen = [int(g) for g in woorden[1:]]
                except ValueError:
                    raise Fout("%s: SCHAAL y1 y2 ... (getallen)" % waar)
                if not 1 <= len(grenzen) <= MAX_SCHAAL or any(not 0 < g < KAMER_H for g in grenzen) \
                        or grenzen != sorted(grenzen, reverse=True) or len(set(grenzen)) != len(grenzen):
                    raise Fout("%s: SCHAAL: 1 tot %d grenzen tussen 1 en %d, aflopend" % (waar, MAX_SCHAAL, KAMER_H - 1))
                kamers[kamer]["schaal"] = grenzen
            elif w == "BEGIN":
                if len(woorden) != 4 or woorden[3] not in RICHTINGEN:
                    raise Fout("%s: BEGIN kamer x,y richting" % waar)
                begin = (woorden[1], punt(woorden[2], waar), RICHTINGEN[woorden[3]], waar)
            else:
                raise Fout("%s: %s kent de compiler nog niet (de rest van de taal komt in hoofdstuk 4)" % (waar, w))
    return kamers, volgorde, begin


def buren(vakken):
    n = len(vakken)
    b = [0] * n
    for i in range(n):
        for j in range(n):
            if i != j:
                a, c = vakken[i], vakken[j]
                if a[0] <= c[2] and c[0] <= a[2] and a[1] <= c[3] and c[1] <= a[3]:
                    b[i] |= 1 << j
    return b


def controleer(kamers, begin):
    for naam, k in kamers.items():
        v = k["vakken"]
        if not v:
            raise Fout("%s: kamer %s heeft geen loopvak" % (k["waar"], naam))
        if len(v) > MAX_VAKKEN:
            raise Fout("%s: kamer %s heeft %d loopvakken, hooguit %d" % (k["waar"], naam, len(v), MAX_VAKKEN))
        b = buren(v)
        gezien, rij = {0}, [0]
        while rij:
            i = rij.pop()
            for j in range(len(v)):
                if b[i] >> j & 1 and j not in gezien:
                    gezien.add(j)
                    rij.append(j)
        for j in range(len(v)):
            if j not in gezien:
                raise Fout("%s: dit loopvak raakt de andere niet (geen overlap): je kunt er niet komen" % v[j][4])
        k["buren"] = b
        # de voeten alleen op de loopkleuren
        import loopkaart
        kleuren, kwaar = k["kleuren"] or (loopkaart.STANDAARD_KLEUREN, k["waar"])
        try:
            m = loopkaart.masker(naam, kleuren, k["vrij"])
        except ValueError as e:
            raise Fout("%s: %s" % (kwaar, e))
        except OSError:
            raise Fout("%s: geen build/gen/kamer_%s.bin: staat de kamer in data/kamers.txt?" % (k["waar"], naam))
        for x1, y1, x2, y2, vwaar in v:
            uitleg = loopkaart.controleer_vak(m, x1, y1, x2, y2)
            if uitleg:
                voorstel = loopkaart.krimp(m, x1, y1, x2, y2)
                raise Fout("%s: dit loopvak %s. Kleiner dat wel past: %s (controleplaatje: python3 tools/loopkaart.py %s --toon)"
                           % (vwaar, uitleg, "LOOPVAK %d,%d %d,%d" % tuple(voorstel) if voorstel else "geen", naam))
        if k["achter"]:
            import kamer as kamermod
            lijst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kamers.txt")
            opties = {n: o for n, _, o, _ in kamermod.lees_lijst(lijst)}
            if not (opties.get(naam) or {}).get("voorgrond"):
                raise Fout("%s: ACHTER, maar de kamer heeft geen voorgrond (voorgrond=... in data/kamers.txt)" % k["achter"][4])
    if begin is None:
        raise Fout("geen BEGIN in de scripts")
    kamer, (x, y), _, waar = begin
    if kamer not in kamers:
        raise Fout("%s: onbekende kamer %s" % (waar, kamer))
    if not any(a[0] <= x <= a[2] and a[1] <= y <= a[3] for a in kamers[kamer]["vakken"]):
        raise Fout("%s: het beginpunt staat niet in een loopvak" % waar)


def schrijf(kamers, volgorde, begin, pad):
    L = ["// spel.asm — gemaakt door tools/scriptc.py uit scripts/*.hcs; niet met de hand wijzigen",
         ".segment Data"]
    for nr, naam in enumerate(volgorde):
        v, b = kamers[naam]["vakken"], kamers[naam]["buren"]
        L.append(".const KAMER_%s = %d" % (naam.upper(), nr))
        L.append("// loopvakken: aantal, dan per veld een rij van <aantal> bytes (x in schermpixels)")
        L.append("loopvakken_%s:" % naam)
        L.append("        .byte %d" % len(v))
        velden = [
            ("x1 lo", [(a[0] * 2) & 255 for a in v]), ("x1 hi", [(a[0] * 2) >> 8 for a in v]),
            ("x2 lo", [(a[2] * 2 + 1) & 255 for a in v]), ("x2 hi", [(a[2] * 2 + 1) >> 8 for a in v]),
            ("y1", [a[1] for a in v]), ("y2", [a[3] for a in v]),
            ("buren lo", [x & 255 for x in b]), ("buren hi", [x >> 8 for x in b]),
        ]
        for wat, rij in velden:
            L.append("        .byte %s    // %s" % (", ".join("$%02x" % x for x in rij), wat))
        ach = kamers[naam]["achter"]
        L.append("achter_%s:    // ACHTER: aantal (0/1), x1 lo, x1 hi, x2 lo, x2 hi, y1, y2 (x in schermpixels)" % naam)
        if ach:
            x1, y1, x2, y2, _ = ach
            L.append("        .byte 1, %d, %d, %d, %d, %d, %d" % ((x1 * 2) & 255, (x1 * 2) >> 8, (x2 * 2 + 1) & 255,
                                                               (x2 * 2 + 1) >> 8, y1, y2))
        else:
            L.append("        .byte 0, 0, 0, 0, 0, 0, 0")
        sch = kamers[naam]["schaal"]
        L.append("schaal_%s:    // aantal grenzen, dan de grenzen (aflopend): y >= grens -> grotere maat" % naam)
        L.append("        .byte %d%s" % (len(sch), "".join(", %d" % g for g in sch)))
    kamer, (x, y), r, _ = begin
    L += [".const BEGIN_KAMER = KAMER_%s" % kamer.upper(), ".const BEGIN_X = %d    // schermpixels" % (x * 2),
          ".const BEGIN_Y = %d" % y, ".const BEGIN_RICHTING = %d" % r,
          ".label begin_loopvakken = loopvakken_%s" % kamer, ".label begin_schaal = schaal_%s" % kamer,
          ".label begin_achter = achter_%s" % kamer]
    open(pad, "w").write("\n".join(L) + "\n")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    bestanden = sorted(glob.glob(os.path.join(sys.argv[1], "*.hcs")))
    os.makedirs(sys.argv[2], exist_ok=True)
    try:
        kamers, volgorde, begin = lees(bestanden)
        controleer(kamers, begin)
    except Fout as e:
        print("[scriptc] FOUT: %s" % e, file=sys.stderr)
        sys.exit(1)
    schrijf(kamers, volgorde, begin, os.path.join(sys.argv[2], "spel.asm"))
    print("[scriptc] %d bestanden, %d kamers, %d loopvakken" % (
        len(bestanden), len(kamers), sum(len(k["vakken"]) for k in kamers.values())))


if __name__ == "__main__":
    main()
