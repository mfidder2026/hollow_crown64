#!/usr/bin/env python3
"""scriptc.py — de compiler voor de scripts van Hollow Crown (scripts/*.hcs, §6.4).

    python3 tools/scriptc.py scripts build/gen      schrijft build/gen/spel.asm

Tot nu toe: KAMER, LOOPVAK, SCHAAL, BEGIN (hoofdstuk 2), en VOORWERP, STANDAARD, SPREKER en ZEG (hoofdstuk 3).
De rest van de taal (ALS, ZET, GEEF, LOOP, ...) komt in hoofdstuk 4; onbekende woorden zijn tot dan een fout,
zodat er niets stilletjes wordt overgeslagen.

    KAMER naam
      LOOPVAK x1,y1 x2,y2        rechthoek in kamercoördinaten: x 0-159 (multicolor-pixels), y 0-127
      LOOPKLEUREN kleur ...      de kleuren waar de voeten op mogen (standaard: groen lichtgroen geel). Elk
                                 LOOPVAK moet daar (bijna) helemaal op liggen: zie tools/loopkaart.py.
      VRIJ x1,y1 x2,y2           hier geldt de kleurcontrole niet (bv. de waterstraal van de fontein boven het gras,
                                 of later een geheime doorgang). Zet er een opmerking bij waarom.
      ACHTER x1,y1 x2,y2         staan Eldric's voeten hier, dan komt de voorgrond van de kamer (data/kamers.txt,
                                 voorgrond=...) vóór hem: hij loopt achter het torentje langs. Hooguit één per kamer.
      SCHAAL y1 y2 ...           diepte: voeten op y >= y1 = maat 0 (groot), >= y2 = maat 1, ...; daarachter
                                 de volgende maat. Aflopend, hooguit 4 grenzen (5 maten in tools/costume.py).
      VOORWERP naam "naam op het scherm" VAK x,y b,h LOOP x,y richting
                                 klikvak (linkerbovenhoek + breedte, hoogte) en waar Eldric gaat staan, kijkend
                                 in de richting. Daaronder per werkwoord een script:
        BEKIJK:
          ZEG eldric "tekst"     (de compiler breekt de tekst over 2 regels van 40)
    BEGIN kamer x,y richting      waar Eldric begint (richting: VOOR RUG RECHTS LINKS)
    SPREKER naam kleur            wie kan praten, in welke kleur (berichten op rij 0-1)
    STANDAARD werkwoord:          het antwoord als een voorwerp geen script voor dat werkwoord heeft
      ZEG eldric "Dat kan ik niet openen."
Werkwoorden: GA_NAAR PAK GEBRUIK OPEN BEKIJK PRAAT GEEF SLUIT DUW TREK LEES WAT_IS (de volgorde van de balk).

Controles: vakken binnen de kamer en niet leeg; vakken op de loopkleuren van het kamerplaatje
(build/gen/kamer_<naam>.bin, dus de kamers worden eerst omgezet); hooguit 16 per kamer; elk vak bereikbaar vanuit elk ander
(anders kan de speler vast komen te zitten); BEGIN staat in een loopvak.

In de uitvoer zijn x-waarden schermpixels (x * 2, rechterrand x2 * 2 + 1): zo rekent de motor.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

KAMER_B, KAMER_H = 160, 128
MAX_VAKKEN = 16
MAX_SCHAAL = 4           # grenzen; de motor heeft MATEN = 5 maten (tools/costume.py)
MAX_VOORWERPEN = 16      # per kamer
WERKWOORDEN = ["GA_NAAR", "PAK", "GEBRUIK", "OPEN", "BEKIJK", "PRAAT", "GEEF", "SLUIT", "DUW", "TREK", "LEES", "WAT_IS"]
OP_STOP, OP_ZEG = 0, 1   # bytecode: gelijk houden met src/vm.asm
REGEL = 40               # tekens per berichtregel
NIEUWE_REGEL = 0xFE      # in een tekst: verder op de tweede regel
RICHTINGEN = {"VOOR": 0, "RUG": 1, "RECHTS": 2, "LINKS": 3}


class Fout(Exception):
    pass


def punt(tekst, waar):
    m = re.fullmatch(r"(\d+),(\d+)", tekst)
    if not m:
        raise Fout("%s: verwacht x,y, niet %r" % (waar, tekst))
    return int(m.group(1)), int(m.group(2))


def splits(regel, waar):
    """Woorden van een regel; tekst tussen aanhalingstekens is één woord (als ("tekst", ...)); '#' daarbuiten
    begint een opmerking."""
    uit, i = [], 0
    while i < len(regel):
        c = regel[i]
        if c == "#":
            break
        if c.isspace():
            i += 1
        elif c == '"':
            j = regel.find('"', i + 1)
            if j < 0:
                raise Fout("%s: tekst zonder sluitend aanhalingsteken" % waar)
            uit.append(("tekst", regel[i + 1:j]))
            i = j + 1
        else:
            j = i
            while j < len(regel) and not regel[j].isspace() and regel[j] not in '"#':
                j += 1
            uit.append(regel[i:j])
            i = j
    return uit


def lees(bestanden):
    kamers, volgorde, begin = {}, [], None
    sprekers, standaard = {}, {}
    for pad in bestanden:
        kamer = None
        script = None                  # de lijst waar opdrachten in komen (een werkwoordblok)
        voorwerp = None
        for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
            waar = "%s:%d" % (pad, nr)
            woorden = splits(regel, waar)
            if not woorden:
                continue
            w = woorden[0]
            if not isinstance(w, str):
                raise Fout("%s: een regel begint niet met een tekst" % waar)
            # een werkwoordblok: "BEKIJK:" (onder een VOORWERP) of "STANDAARD BEKIJK:"
            if w.endswith(":") and w[:-1] in WERKWOORDEN and len(woorden) == 1:
                if voorwerp is None:
                    raise Fout("%s: %s hoort onder een VOORWERP (of: STANDAARD %s)" % (waar, w, w))
                if w[:-1] in voorwerp["scripts"]:
                    raise Fout("%s: %s staat al bij dit voorwerp" % (waar, w))
                script = voorwerp["scripts"][w[:-1]] = []
                continue
            if w == "STANDAARD":
                if len(woorden) != 2 or not isinstance(woorden[1], str) or woorden[1][:-1] not in WERKWOORDEN \
                        or not woorden[1].endswith(":"):
                    raise Fout("%s: STANDAARD werkwoord:  (bv. STANDAARD OPEN:)" % waar)
                ww = woorden[1][:-1]
                if ww in standaard:
                    raise Fout("%s: STANDAARD %s staat er al" % (waar, ww))
                script = standaard[ww] = []
                voorwerp = None
                continue
            if w == "ZEG":
                if script is None:
                    raise Fout("%s: ZEG hoort in een script (onder BEKIJK: enz.)" % waar)
                if len(woorden) != 3 or not isinstance(woorden[1], str) or not isinstance(woorden[2], tuple):
                    raise Fout('%s: ZEG spreker "tekst"' % waar)
                script.append(("ZEG", woorden[1], woorden[2][1], waar))
                continue
            if any(isinstance(x, tuple) for x in woorden) and w not in ("VOORWERP",):
                raise Fout("%s: %s kent geen tekst tussen aanhalingstekens" % (waar, w))
            script = None
            if w == "VOORWERP":
                if kamer is None:
                    raise Fout("%s: VOORWERP buiten een KAMER" % waar)
                if len(woorden) != 9 or not isinstance(woorden[1], str) or not isinstance(woorden[2], tuple) \
                        or woorden[3] != "VAK" or woorden[6] != "LOOP" or woorden[8] not in RICHTINGEN:
                    raise Fout('%s: VOORWERP naam "naam" VAK x,y b,h LOOP x,y richting' % waar)
                (x, y), (b, h), (lx, ly) = punt(woorden[4], waar), punt(woorden[5], waar), punt(woorden[7], waar)
                if b < 1 or h < 1 or x + b > KAMER_B or y + h > KAMER_H:
                    raise Fout("%s: het VAK van het voorwerp valt buiten de kamer" % waar)
                if any(v["naam"] == woorden[1] for v in kamers[kamer]["voorwerpen"]):
                    raise Fout("%s: voorwerp %s bestaat al in deze kamer" % (waar, woorden[1]))
                voorwerp = {"naam": woorden[1], "tekst": woorden[2][1], "vak": (x, y, x + b - 1, y + h - 1),
                            "loop": (lx, ly), "richting": RICHTINGEN[woorden[8]], "scripts": {}, "waar": waar}
                kamers[kamer]["voorwerpen"].append(voorwerp)
                continue
            if w == "SPREKER":
                if len(woorden) != 3:
                    raise Fout("%s: SPREKER naam kleur" % waar)
                sprekers[woorden[1]] = (woorden[2], waar)
                continue
            if w == "KAMER":
                if len(woorden) != 2:
                    raise Fout("%s: KAMER naam" % waar)
                kamer = woorden[1]
                if kamer in kamers:
                    raise Fout("%s: kamer %s bestaat al" % (waar, kamer))
                kamers[kamer] = {"vakken": [], "waar": waar, "schaal": [], "kleuren": None, "vrij": [], "achter": None,
                                 "voorwerpen": []}
                voorwerp = None
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
    return kamers, volgorde, begin, sprekers, standaard


def tekst_codes(tekst, waar, regels_max=2):
    """Tekst -> schermcodes van het eigen lettertype, afgebroken over regels van 40 (NIEUWE_REGEL ertussen)."""
    import lettertype
    regels = [""]
    for woord in tekst.split():
        if len(woord) > REGEL:
            raise Fout("%s: het woord %r is langer dan een regel" % (waar, woord))
        if not regels[-1]:
            regels[-1] = woord
        elif len(regels[-1]) + 1 + len(woord) <= REGEL:
            regels[-1] += " " + woord
        else:
            regels.append(woord)
    if len(regels) > regels_max:
        raise Fout("%s: tekst te lang: past niet op %d regel%s van %d tekens: %r" % (
            waar, regels_max, "s" if regels_max > 1 else "", REGEL, tekst))
    codes = []
    for i, r in enumerate(regels):
        if i:
            codes.append(NIEUWE_REGEL)
        for ch in r:
            try:
                c = lettertype.code_van(ch)
            except KeyError:
                raise Fout("%s: het teken %r zit niet in het lettertype (tools/lettertype.py)" % (waar, ch))
            if c == 0 or c >= NIEUWE_REGEL:
                raise Fout("%s: het teken %r kan niet in een tekst" % (waar, ch))
            codes.append(c)
    return codes, len(tekst)


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


def controleer_scripts(kamers, sprekers, standaard):
    import c64beeld
    for naam, (kleur, waar) in sprekers.items():
        if kleur not in c64beeld.NAMEN:
            raise Fout("%s: onbekende kleur %s" % (waar, kleur))
    alle = [s for k in kamers.values() for v in k["voorwerpen"] for s in v["scripts"].values()] + list(standaard.values())
    for script in alle:
        for opdracht in script:
            if opdracht[0] == "ZEG":
                _, spreker, tekst, waar = opdracht
                if spreker not in sprekers:
                    raise Fout("%s: onbekende spreker %s (zet hem in een SPREKER-regel)" % (waar, spreker))
                tekst_codes(tekst, waar)
    for knaam, k in kamers.items():
        if len(k["voorwerpen"]) > MAX_VOORWERPEN:
            raise Fout("%s: kamer %s heeft meer dan %d voorwerpen" % (k["waar"], knaam, MAX_VOORWERPEN))
        for v in k["voorwerpen"]:
            lx, ly = v["loop"]
            if not any(a[0] <= lx <= a[2] and a[1] <= ly <= a[3] for a in k["vakken"]):
                raise Fout("%s: het LOOP-punt van %s ligt niet in een loopvak" % (v["waar"], v["naam"]))
            langste = max(len(w) for w in ("Ga naar", "Pak", "Gebruik", "Open", "Bekijk", "Praat met", "Geef",
                                           "Sluit", "Duw", "Trek", "Lees", "Wat is"))
            if langste + 1 + len(v["tekst"]) > REGEL:
                raise Fout("%s: de naam %r is te lang voor de zinregel" % (v["waar"], v["tekst"]))
            tekst_codes(v["tekst"], v["waar"], 1)


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


def script_asm(label, script, sprekers, L, teksten):
    """Bytecode van een script: ZEG = OP_ZEG spreker tekst(lo, hi) duur(lo, hi); daarna OP_STOP."""
    volgorde = list(sprekers)
    L.append("%s:" % label)
    for opdracht in script:
        if opdracht[0] == "ZEG":
            _, spreker, tekst, waar = opdracht
            codes, n = tekst_codes(tekst, waar)
            t = "t_%d" % len(teksten)
            teksten.append((t, codes, tekst))
            duur = min(65535, 50 + (n * 5 + 1) // 2)     # 1 s + 1 s per 20 tekens (50 beelden per seconde)
            L.append("        .byte %d, %d, <%s, >%s, %d, %d    // ZEG %s" % (
                OP_ZEG, volgorde.index(spreker), t, t, duur & 255, duur >> 8, spreker))
    L.append("        .byte %d    // STOP" % OP_STOP)


def schrijf(kamers, volgorde, begin, pad, sprekers, standaard):
    import c64beeld
    L = ["// spel.asm — gemaakt door tools/scriptc.py uit scripts/*.hcs; niet met de hand wijzigen",
         ".segment Data"]
    teksten = []
    L.append("// sprekers: kleur per nummer")
    for i, sp in enumerate(sprekers):
        L.append(".const SPREKER_%s = %d" % (sp.upper(), i))
    L.append("spreker_kleur: .byte %s" % ", ".join(str(c64beeld.NAMEN.index(k)) for k, _ in sprekers.values()))
    L.append("// standaardantwoorden: per werkwoord een script (0 = geen)")
    for ww in WERKWOORDEN:
        if ww in standaard:
            script_asm("std_%s" % ww.lower(), standaard[ww], sprekers, L, teksten)
    L.append("standaard_scripts:")
    L.append("        .word %s" % ", ".join("std_%s" % ww.lower() if ww in standaard else "0" for ww in WERKWOORDEN))
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
        vw = kamers[naam]["voorwerpen"]
        for v in vw:
            n = "%s_%s" % (naam, v["naam"])
            codes, _ = tekst_codes(v["tekst"], v["waar"], 1)
            L.append("naam_%s: .byte %s, 0    // %s" % (n, ", ".join("$%02x" % c for c in codes), v["tekst"]))
            for ww in WERKWOORDEN:
                if ww in v["scripts"]:
                    script_asm("s_%s_%s" % (n, ww.lower()), v["scripts"][ww], sprekers, L, teksten)
            L.append("scripts_%s: .word %s" % (n, ", ".join(
                "s_%s_%s" % (n, ww.lower()) if ww in v["scripts"] else "0" for ww in WERKWOORDEN)))
        L.append("// voorwerpen: aantal, dan per veld een rij van <aantal> bytes (x in schermpixels)")
        L.append("voorwerpen_%s:" % naam)
        L.append("        .byte %d" % len(vw))
        if vw:
            nm = ["%s_%s" % (naam, v["naam"]) for v in vw]
            velden = [
                ("x1 lo", ["$%02x" % ((v["vak"][0] * 2) & 255) for v in vw]),
                ("x1 hi", ["$%02x" % ((v["vak"][0] * 2) >> 8) for v in vw]),
                ("x2 lo", ["$%02x" % ((v["vak"][2] * 2 + 1) & 255) for v in vw]),
                ("x2 hi", ["$%02x" % ((v["vak"][2] * 2 + 1) >> 8) for v in vw]),
                ("y1", [str(v["vak"][1]) for v in vw]), ("y2", [str(v["vak"][3]) for v in vw]),
                ("loop x lo", ["$%02x" % ((v["loop"][0] * 2) & 255) for v in vw]),
                ("loop x hi", ["$%02x" % ((v["loop"][0] * 2) >> 8) for v in vw]),
                ("loop y", [str(v["loop"][1]) for v in vw]), ("richting", [str(v["richting"]) for v in vw]),
                ("naam lo", ["<naam_%s" % n for n in nm]), ("naam hi", [">naam_%s" % n for n in nm]),
                ("scripts lo", ["<scripts_%s" % n for n in nm]), ("scripts hi", [">scripts_%s" % n for n in nm]),
            ]
            for wat, rij in velden:
                L.append("        .byte %s    // %s" % (", ".join(rij), wat))
        sch = kamers[naam]["schaal"]
        L.append("schaal_%s:    // aantal grenzen, dan de grenzen (aflopend): y >= grens -> grotere maat" % naam)
        L.append("        .byte %d%s" % (len(sch), "".join(", %d" % g for g in sch)))
    kamer, (x, y), r, _ = begin
    L += [".const BEGIN_KAMER = KAMER_%s" % kamer.upper(), ".const BEGIN_X = %d    // schermpixels" % (x * 2),
          ".const BEGIN_Y = %d" % y, ".const BEGIN_RICHTING = %d" % r,
          ".label begin_loopvakken = loopvakken_%s" % kamer, ".label begin_schaal = schaal_%s" % kamer,
          ".label begin_achter = achter_%s" % kamer, ".label begin_voorwerpen = voorwerpen_%s" % kamer]
    L.append("// teksten (schermcodes; $%02x = tweede regel, 0 = einde)" % NIEUWE_REGEL)
    for t, codes, tekst in teksten:
        L.append("%s: .byte %s, 0    // %s" % (t, ", ".join("$%02x" % c for c in codes), tekst[:60]))
    open(pad, "w").write("\n".join(L) + "\n")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    bestanden = sorted(glob.glob(os.path.join(sys.argv[1], "*.hcs")))
    os.makedirs(sys.argv[2], exist_ok=True)
    try:
        kamers, volgorde, begin, sprekers, standaard = lees(bestanden)
        controleer(kamers, begin)
        controleer_scripts(kamers, sprekers, standaard)
    except Fout as e:
        print("[scriptc] FOUT: %s" % e, file=sys.stderr)
        sys.exit(1)
    schrijf(kamers, volgorde, begin, os.path.join(sys.argv[2], "spel.asm"), sprekers, standaard)
    print("[scriptc] %d bestanden, %d kamers, %d loopvakken, %d voorwerpen, %d standaardantwoorden" % (
        len(bestanden), len(kamers), sum(len(k["vakken"]) for k in kamers.values()),
        sum(len(k["voorwerpen"]) for k in kamers.values()), len(standaard)))


if __name__ == "__main__":
    main()
