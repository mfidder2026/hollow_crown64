#!/usr/bin/env python3
"""scriptc.py — de compiler voor de scripts van Hollow Crown (scripts/*.hcs, §6.4).

    python3 tools/scriptc.py scripts build/gen      schrijft build/gen/spel.asm

Hoofdstuk 2: alleen KAMER, LOOPVAK en BEGIN. De rest van de taal (VOORWERP, ZEG, ALS, ...) komt in hoofdstuk 4;
onbekende woorden zijn tot dan een fout, zodat er niets stilletjes wordt overgeslagen.

    KAMER naam
      LOOPVAK x1,y1 x2,y2        rechthoek in kamercoördinaten: x 0-159 (multicolor-pixels), y 0-127
    BEGIN kamer x,y richting      waar Eldric begint (richting: VOOR RUG RECHTS LINKS)

Controles: vakken binnen de kamer en niet leeg; hooguit 16 per kamer; elk vak bereikbaar vanuit elk ander
(anders kan de speler vast komen te zitten); BEGIN staat in een loopvak.

In de uitvoer zijn x-waarden schermpixels (x * 2, rechterrand x2 * 2 + 1): zo rekent de motor.
"""
import glob, os, re, sys

KAMER_B, KAMER_H = 160, 128
MAX_VAKKEN = 16
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
                kamers[kamer] = {"vakken": [], "waar": waar}
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
    kamer, (x, y), r, _ = begin
    L += [".const BEGIN_KAMER = KAMER_%s" % kamer.upper(), ".const BEGIN_X = %d    // schermpixels" % (x * 2),
          ".const BEGIN_Y = %d" % y, ".const BEGIN_RICHTING = %d" % r,
          ".label begin_loopvakken = loopvakken_%s" % kamer]
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
