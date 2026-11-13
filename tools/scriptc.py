#!/usr/bin/env python3
"""scriptc.py — de compiler voor de scripts van Hollow Crown (scripts/*.hcs, §6.4).

    python3 tools/scriptc.py scripts build/gen [extra-map ...]
        schrijft build/gen/spel.asm, build/gen/spel.json (namen -> nummers, voor de tests) en
        build/gen/puzzelstappen.txt. Een extra map (bv. tests/scripts) komt erbij (alleen de testbuild).

DE TAAL (een regel per opdracht; '#' begint een opmerking; tekst staat tussen aanhalingstekens)

  Bovenaan:
    BEGIN kamer x,y richting          waar Eldric begint (richting: VOOR RUG RECHTS LINKS)
    SPREKER naam kleur                wie kan praten, in welke kleur (berichten op rij 0-1)
    DOEL vlag                         het einde van het hoofdstuk: de compiler controleert dat het te halen is
    STANDAARD werkwoord:              antwoord als een voorwerp geen script heeft voor dat werkwoord
    SCRIPT naam:                      een los script (voor tests, of om aan te roepen)

  KAMER naam                          een kamer; daaronder:
    LOOPVAK x1,y1 x2,y2               waar de voeten mogen staan (x 0-159 multicolor-pixels, y 0-127)
    LOOPKLEUREN kleur ...             de kleuren onder de voeten (standaard groen lichtgroen geel); de build
                                      controleert elk LOOPVAK op het kamerplaatje
    VRIJ x1,y1 x2,y2                  daar geldt de kleurcontrole niet (zet erbij waarom)
    ACHTER x1,y1 x2,y2                voeten hier: de voorgrond van de kamer komt vóór Eldric
    SCHAAL y1 y2 ...                  diepte: y >= y1 maat 0 (groot), >= y2 maat 1 ... (hooguit 4 grenzen)
    BINNENKOMST:                      script als Eldric de kamer binnenkomt
    FLAKKER x,y b,h kleur kleur ...   een kleine animatie (hoofdstuk 8): in die vakjes (x, b veelvoud van 4; y, h van 8)
                                      schuiven deze kleuren rond (bv. vuur: rood oranje geel). Hooguit 2 per kamer.
    ACTOR naam KOSTUUM k OP x,y [VERBORGEN]
                                      een figuur (NPC) in de kamer, met een kostuum uit tools/costume.py
                                      (mira, vex, wolf); OP = waar de voeten staan. Hooguit 2 per kamer.

  GESPREK naam                        een gesprek; daaronder keuzes (hooguit 8; er staan er hooguit 4 tegelijk):
    KEUZE "zin" [ALS [NIET] vlag v | ALS [NIET] HEEFT voorwerp] [EINDE]
                                      met daaronder het script van die keuze; EINDE: daarna is het gesprek klaar

  VOORWERP naam "naam" [VAK x,y b,h LOOP x,y richting] [BIJ eldric | NERGENS] [STAND n]
                                      Onder een KAMER ligt het voorwerp in die kamer (tenzij BIJ eldric of
                                      NERGENS: dan begint het in de inventaris of nergens; PLAATS zet het later
                                      neer). Daaronder scripts per werkwoord:
    BEKIJK:                           één voorwerp: "Bekijk fontein"
    GEBRUIK kruik:                    twee voorwerpen: "Gebruik kruik met <dit voorwerp>"
    GEEF ziensteen:                   "Geef ziensteen aan <dit voorwerp>"
    GA_NAAR:                          draait als Eldric bij het voorwerp is (bv. een deur)

  Werkwoorden: GA_NAAR PAK GEBRUIK OPEN BEKIJK PRAAT GEEF SLUIT DUW TREK LEES WAT_IS (de volgorde van de balk).

  Opdrachten in een script:
    ZEG spreker "tekst"               rij 0-1; de compiler breekt hem over 2 regels van 40; wacht tot hij weg is
    ALS [NIET] vlag naam              ... [ANDERS ...] EINDE
    ALS [NIET] HEEFT voorwerp         (in de inventaris)
    ALS [NIET] STAND voorwerp n
    ZET vlag / WIS vlag
    GEEF voorwerp                     naar de inventaris
    NEEM voorwerp                     weg (nergens)
    PLAATS voorwerp kamer             neerzetten in een kamer (bv. de ziensteen onder de tafel)
    STAND voorwerp n                  stand van een voorwerp (open/dicht, vol/leeg, ...)
    KAMER naam x,y richting           naar een andere kamer (laden van de diskette); het script houdt op,
                                      daarna draait BINNENKOMST van die kamer
    PATCH naam                        een patch van de kamer zetten (data/kamers.txt: patch=naam:...); in een
                                      andere kamer dan de huidige doet hij niets (zet hem dan in BINNENKOMST)
    LOOP eldric x,y                   lopen en wachten tot hij er is
    KIJK eldric richting
    WACHT n                           n beelden
    PRAAT gesprek                     een gesprek beginnen (de werkwoorden maken plaats voor de keuzes)
    TOON naam / VERBERG naam          een figuur (ACTOR) tonen of weghalen
    MUZIEK thema / MUZIEK stil        het thema (tools/thema.py) aan of uit; bij het laden van een kamer stopt het
                                      (zet MUZIEK thema dus in BINNENKOMST). F1 zet de muziek voor de speler uit.
    GELUID naam                       een geluidseffect op stem 3 (deur munt vuur wolf klaar klik); wacht niet
    LOOP naam x,y                     een figuur in een rechte lijn laten lopen (wacht tot hij er is)
    TUSSENSCENE / EINDE_TUSSENSCENE   geen invoer daartussen; vuur of spatie slaat over
    STOP                              het script eindigt

CONTROLES: onbekende woorden, kamers, voorwerpen, sprekers; te lange teksten en tekens die niet in het lettertype
zitten; loopvakken (binnen de kamer, op de loopkleuren, allemaal bereikbaar); LOOP-punten in een loopvak;
ALS/ANDERS/EINDE in balans; vlaggen die getest maar nergens gezet worden; en of DOEL te halen is (alle
benodigde vlaggen en voorwerpen ergens te krijgen). puzzelstappen.txt zegt wat waar te krijgen is.
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAMER_B, KAMER_H = 160, 128
MAX_VAKKEN = 16
MAX_SCHAAL = 4           # grenzen; de motor heeft MATEN = 5 maten (tools/costume.py)
MAX_VOORWERPEN = 64      # in het hele spel (src/status.asm)
MAX_VLAGGEN = 256
MAX_NAAM = 13            # "Gebruik <naam> met <naam>" moet op de zinregel passen
RICHTINGEN = {"VOOR": 0, "RUG": 1, "RECHTS": 2, "LINKS": 3}
WERKWOORDEN = ["GA_NAAR", "PAK", "GEBRUIK", "OPEN", "BEKIJK", "PRAAT", "GEEF", "SLUIT", "DUW", "TREK", "LEES", "WAT_IS"]
TWEE = {"GEBRUIK": "met", "GEEF": "aan"}         # werkwoorden met een tweede voorwerp
EIGENAAR_ELDRIC, EIGENAAR_NERGENS = 0xFF, 0xFE
REGEL = 40
NIEUWE_REGEL = 0xFE

# bytecode: gelijk houden met src/vm.asm
OP = {"STOP": 0x00, "ZEG": 0x01, "SPRING": 0x02, "ALS_VLAG": 0x03, "ALS_NIET_VLAG": 0x04, "ALS_HEEFT": 0x05,
      "ALS_NIET_HEEFT": 0x06, "ALS_STAND": 0x07, "ALS_NIET_STAND": 0x08, "ZET": 0x09, "WIS": 0x0A, "GEEF": 0x0B,
      "NEEM": 0x0C, "STAND": 0x0D, "PLAATS": 0x0E, "LOOP": 0x0F, "KIJK": 0x10, "WACHT": 0x11,
      "TUSSENSCENE": 0x12, "EINDE_TUSSENSCENE": 0x13, "PATCH": 0x14, "KAMER": 0x15, "PRAAT": 0x16,
      "TOON": 0x17, "VERBERG": 0x18, "NPC_LOOP": 0x19, "GELUID": 0x1A, "MUZIEK": 0x1B}
# geluidseffecten: gelijk houden met de GL_-nummers in src/geluid.asm
GELUIDEN = ["deur", "munt", "vuur", "wolf", "klaar", "klik"]
MAX_NPC_KAMER = 2
MAX_KEUZES = 8
OPDRACHTEN = {"ZEG", "ALS", "ANDERS", "EINDE", "ZET", "WIS", "GEEF", "NEEM", "PLAATS", "STAND", "LOOP", "KIJK",
              "WACHT", "TUSSENSCENE", "EINDE_TUSSENSCENE", "STOP", "PATCH", "PRAAT", "TOON", "VERBERG", "GELUID", "MUZIEK"}


class Fout(Exception):
    pass


def punt(tekst, waar):
    m = re.fullmatch(r"(\d+),(\d+)", tekst) if isinstance(tekst, str) else None
    if not m:
        raise Fout("%s: verwacht x,y, niet %r" % (waar, tekst))
    return int(m.group(1)), int(m.group(2))


def getal(tekst, waar, laag=0, hoog=255):
    if not isinstance(tekst, str) or not re.fullmatch(r"\d+", tekst) or not laag <= int(tekst) <= hoog:
        raise Fout("%s: verwacht een getal %d-%d, niet %r" % (waar, laag, hoog, tekst))
    return int(tekst)


def splits(regel, waar):
    """Woorden van een regel; tekst tussen aanhalingstekens is één woord ("tekst", ...); '#' daarbuiten begint
    een opmerking."""
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


def is_tekst(w):
    return isinstance(w, tuple)


# ---------------------------------------------------------------------------------------------------
# Lezen
# ---------------------------------------------------------------------------------------------------
class Spel:
    def __init__(self):
        self.kamers, self.kamer_volgorde = {}, []
        self.voorwerpen, self.vw_volgorde = {}, []
        self.sprekers, self.standaard, self.losse = {}, {}, {}
        self.actors, self.actor_volgorde = {}, []
        self.gesprekken = {}
        self.begin, self.doel = None, None


def lees(bestanden):
    spel = Spel()
    for pad in bestanden:
        kamer = voorwerp = gesprek = None
        blok = None
        for nr, regel in enumerate(open(pad, encoding="utf-8"), 1):
            waar = "%s:%d" % (os.path.relpath(pad, WORTEL) if os.path.abspath(pad).startswith(WORTEL) else pad, nr)
            w = splits(regel, waar)
            if not w:
                continue
            kop = w[0]
            if is_tekst(kop):
                raise Fout("%s: een regel begint niet met een tekst" % waar)

            # ---- koppen van scriptblokken ----
            if len(w) == 1 and kop.endswith(":") and kop[:-1] in WERKWOORDEN:      # BEKIJK:
                if voorwerp is None:
                    raise Fout("%s: %s hoort onder een VOORWERP (of: STANDAARD %s)" % (waar, kop, kop))
                if kop[:-1] in voorwerp["scripts"]:
                    raise Fout("%s: %s staat al bij %s" % (waar, kop, voorwerp["naam"]))
                blok = nieuw_blok(blok, voorwerp["scripts"], kop[:-1], waar)
                continue
            if len(w) == 1 and kop == "BINNENKOMST:":
                if kamer is None:
                    raise Fout("%s: BINNENKOMST: hoort onder een KAMER" % waar)
                blok = nieuw_blok(blok, spel.kamers[kamer], "binnenkomst", waar)
                voorwerp = None
                continue
            if len(w) == 2 and kop in TWEE and isinstance(w[1], str) and w[1].endswith(":"):  # GEBRUIK kruik:
                if voorwerp is None:
                    raise Fout("%s: %s %s hoort onder een VOORWERP" % (waar, kop, w[1]))
                sleutel = (kop, w[1][:-1])
                if sleutel in voorwerp["paren"]:
                    raise Fout("%s: %s %s staat al bij %s" % (waar, kop, w[1], voorwerp["naam"]))
                blok = nieuw_blok(blok, voorwerp["paren"], sleutel, waar)
                continue
            if kop == "STANDAARD":
                if len(w) != 2 or not isinstance(w[1], str) or not w[1].endswith(":") or w[1][:-1] not in WERKWOORDEN:
                    raise Fout("%s: STANDAARD werkwoord:  (bv. STANDAARD OPEN:)" % waar)
                if w[1][:-1] in spel.standaard:
                    raise Fout("%s: STANDAARD %s staat er al" % (waar, w[1]))
                blok = nieuw_blok(blok, spel.standaard, w[1][:-1], waar)
                voorwerp = None
                continue
            if kop == "GESPREK":
                if len(w) != 2 or not re.fullmatch(r"[a-z_][a-z0-9_]*", w[1]):
                    raise Fout("%s: GESPREK naam" % waar)
                if w[1] in spel.gesprekken:
                    raise Fout("%s: GESPREK %s bestaat al" % (waar, w[1]))
                if blok is not None:
                    sluit_blok(blok)
                    blok = None
                gesprek = spel.gesprekken[w[1]] = {"naam": w[1], "keuzes": [], "waar": waar}
                voorwerp = None
                continue
            if kop == "KEUZE":
                if gesprek is None or len(w) < 2 or not is_tekst(w[1]):
                    raise Fout('%s: KEUZE "zin" hoort onder een GESPREK' % waar)
                rest, einde, cond = list(w[2:]), False, None
                if rest and rest[-1] == "EINDE":
                    einde, rest = True, rest[:-1]
                if rest:
                    if rest[0] != "ALS":
                        raise Fout('%s: KEUZE "zin" [ALS [NIET] vlag v | ALS [NIET] HEEFT voorwerp] [EINDE]' % waar)
                    r = rest[1:]
                    niet = bool(r) and r[0] == "NIET"
                    r = r[1:] if niet else r
                    if len(r) == 2 and r[0] == "vlag":
                        cond = (niet, ("vlag", r[1]))
                    elif len(r) == 2 and r[0] == "HEEFT":
                        cond = (niet, ("heeft", r[1]))
                    else:
                        raise Fout('%s: KEUZE ... ALS [NIET] vlag v | ALS [NIET] HEEFT voorwerp' % waar)
                keuze = {"tekst": w[1][1], "einde": einde, "cond": cond, "waar": waar}
                gesprek["keuzes"].append(keuze)
                if len(gesprek["keuzes"]) > MAX_KEUZES:
                    raise Fout("%s: hooguit %d keuzes in een gesprek" % (waar, MAX_KEUZES))
                blok = nieuw_blok(blok, keuze, "script", waar)
                continue
            if kop == "ACTOR":
                if kamer is None or len(w) not in (6, 7) or w[2] != "KOSTUUM" or w[4] != "OP" \
                        or (len(w) == 7 and w[6] != "VERBORGEN"):
                    raise Fout("%s: ACTOR naam KOSTUUM kostuum OP x,y [VERBORGEN] (binnen een KAMER)" % waar)
                if w[1] in spel.actors or w[1] == "eldric":
                    raise Fout("%s: actor %s bestaat al" % (waar, w[1]))
                x, y = punt(w[5], waar)
                spel.actors[w[1]] = {"naam": w[1], "kostuum": w[3], "kamer": kamer, "x": x, "y": y,
                                     "zichtbaar": len(w) == 6, "waar": waar}
                spel.actor_volgorde.append(w[1])
                if blok is not None:
                    sluit_blok(blok)
                    blok = None
                continue
            if kop == "SCRIPT":
                if len(w) != 2 or not isinstance(w[1], str) or not re.fullmatch(r"\w+:", w[1]):
                    raise Fout("%s: SCRIPT naam:" % waar)
                if w[1][:-1] in spel.losse:
                    raise Fout("%s: SCRIPT %s bestaat al" % (waar, w[1][:-1]))
                blok = nieuw_blok(blok, spel.losse, w[1][:-1], waar)
                voorwerp = None
                continue

            # ---- opdrachten in een script (KAMER met 4 woorden is de opdracht, met 2 de kamer zelf) ----
            if kop in OPDRACHTEN or (kop == "KAMER" and len(w) == 4):
                if blok is None:
                    raise Fout("%s: %s hoort in een script (onder BEKIJK: enz.)" % (waar, kop))
                opdracht(blok, kop, w, waar)
                continue

            # ---- declaraties ----
            if blok is not None:
                sluit_blok(blok)
                blok = None
            if any(is_tekst(x) for x in w) and kop != "VOORWERP":
                raise Fout("%s: %s kent geen tekst tussen aanhalingstekens" % (waar, kop))
            if kop == "KAMER":
                if len(w) != 2:
                    raise Fout("%s: KAMER naam" % waar)
                kamer, voorwerp, gesprek = w[1], None, None
                if kamer in spel.kamers:
                    if spel.kamers[kamer]["bestand"] == pad:
                        raise Fout("%s: kamer %s bestaat al" % (waar, kamer))
                    continue                   # in een ander bestand: verder met dezelfde kamer
                spel.kamers[kamer] = {"bestand": pad, "flakker": [], "naam": kamer, "vakken": [], "waar": waar, "schaal": [], "kleuren": None,
                                      "vrij": [], "achter": None}
                spel.kamer_volgorde.append(kamer)
            elif kop == "VOORWERP":
                voorwerp = lees_voorwerp(spel, w, kamer, waar)
                gesprek = None
            elif kop in ("LOOPVAK", "ACHTER", "VRIJ"):
                if kamer is None or len(w) != 3:
                    raise Fout("%s: %s x1,y1 x2,y2 (binnen een KAMER)" % (waar, kop))
                (x1, y1), (x2, y2) = punt(w[1], waar), punt(w[2], waar)
                if not (x1 <= x2 < KAMER_B and y1 <= y2 < KAMER_H):
                    raise Fout("%s: %s buiten de kamer (0-%d, 0-%d) of leeg" % (waar, kop, KAMER_B - 1, KAMER_H - 1))
                k = spel.kamers[kamer]
                if kop == "LOOPVAK":
                    k["vakken"].append((x1, y1, x2, y2, waar))
                elif kop == "VRIJ":
                    k["vrij"].append((x1, y1, x2, y2))
                else:
                    if k["achter"]:
                        raise Fout("%s: hooguit één ACHTER per kamer" % waar)
                    k["achter"] = (x1, y1, x2, y2, waar)
            elif kop == "FLAKKER":
                if kamer is None or len(w) < 5:
                    raise Fout("%s: FLAKKER x,y b,h kleur kleur ... (binnen een KAMER)" % waar)
                (x, y), (b, h) = punt(w[1], waar), punt(w[2], waar)
                if x % 4 or b % 4 or y % 8 or h % 8 or b < 4 or h < 8 or x + b > KAMER_B or y + h > KAMER_H:
                    raise Fout("%s: FLAKKER: x en b veelvoud van 4, y en h van 8, binnen de kamer" % waar)
                import c64beeld
                for kl in w[3:]:
                    if kl not in c64beeld.NAMEN:
                        raise Fout("%s: onbekende kleur %s" % (waar, kl))
                k = spel.kamers[kamer]
                k["flakker"].append((x, y, b, h, [c64beeld.NAMEN.index(kl) for kl in w[3:]], waar))
                if len(k["flakker"]) > 2:
                    raise Fout("%s: hooguit 2 keer FLAKKER per kamer" % waar)
            elif kop == "LOOPKLEUREN":
                if kamer is None or len(w) < 2:
                    raise Fout("%s: LOOPKLEUREN kleur ... (binnen een KAMER)" % waar)
                spel.kamers[kamer]["kleuren"] = (w[1:], waar)
            elif kop == "SCHAAL":
                if kamer is None:
                    raise Fout("%s: SCHAAL buiten een KAMER" % waar)
                grenzen = [getal(g, waar, 1, KAMER_H - 1) for g in w[1:]]
                if not 1 <= len(grenzen) <= MAX_SCHAAL or grenzen != sorted(grenzen, reverse=True) \
                        or len(set(grenzen)) != len(grenzen):
                    raise Fout("%s: SCHAAL: 1 tot %d grenzen tussen 1 en %d, aflopend" % (waar, MAX_SCHAAL, KAMER_H - 1))
                spel.kamers[kamer]["schaal"] = grenzen
            elif kop == "BEGIN":
                if len(w) != 4 or w[3] not in RICHTINGEN:
                    raise Fout("%s: BEGIN kamer x,y richting" % waar)
                spel.begin = (w[1], punt(w[2], waar), RICHTINGEN[w[3]], waar)
            elif kop == "SPREKER":
                if len(w) != 3:
                    raise Fout("%s: SPREKER naam kleur" % waar)
                spel.sprekers[w[1]] = (w[2], waar)
            elif kop == "DOEL":
                if len(w) != 2:
                    raise Fout("%s: DOEL vlag" % waar)
                spel.doel = (w[1], waar)
            else:
                raise Fout("%s: onbekend woord %s" % (waar, kop))
        if blok is not None:
            sluit_blok(blok)
    return spel


def lees_voorwerp(spel, w, kamer, waar):
    if len(w) < 3 or not isinstance(w[1], str) or not is_tekst(w[2]):
        raise Fout('%s: VOORWERP naam "naam" [VAK x,y b,h LOOP x,y richting] [BIJ eldric | NERGENS] [STAND n]' % waar)
    naam = w[1]
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", naam):
        raise Fout("%s: een voorwerpnaam is kleine letters, cijfers en _ (%r)" % (waar, naam))
    if naam in spel.voorwerpen:
        raise Fout("%s: voorwerp %s bestaat al (%s)" % (waar, naam, spel.voorwerpen[naam]["waar"]))
    v = {"naam": naam, "tekst": w[2][1], "vak": None, "loop": None, "richting": 0, "scripts": {}, "paren": {},
         "waar": waar, "kamer": kamer, "eigenaar": kamer, "stand": 0}
    i = 3
    while i < len(w):
        if w[i] == "VAK" and i + 2 < len(w):
            (x, y), (b, h) = punt(w[i + 1], waar), punt(w[i + 2], waar)
            if b < 1 or h < 1 or x + b > KAMER_B or y + h > KAMER_H:
                raise Fout("%s: het VAK van %s valt buiten de kamer" % (waar, naam))
            v["vak"] = (x, y, x + b - 1, y + h - 1)
            i += 3
        elif w[i] == "LOOP" and i + 2 < len(w) and w[i + 2] in RICHTINGEN:
            v["loop"], v["richting"] = punt(w[i + 1], waar), RICHTINGEN[w[i + 2]]
            i += 3
        elif w[i] == "BIJ" and i + 1 < len(w) and w[i + 1] == "eldric":
            v["eigenaar"] = "eldric"
            i += 2
        elif w[i] == "NERGENS":
            v["eigenaar"] = None
            i += 1
        elif w[i] == "STAND" and i + 1 < len(w):
            v["stand"] = getal(w[i + 1], waar)
            i += 2
        else:
            raise Fout('%s: VOORWERP: %r begrijp ik niet (VAK x,y b,h / LOOP x,y richting / BIJ eldric / NERGENS / STAND n)'
                       % (waar, w[i]))
    if (v["vak"] is None) != (v["loop"] is None):
        raise Fout("%s: VAK en LOOP horen bij elkaar" % waar)
    if v["vak"] is not None and kamer is None:
        raise Fout("%s: een VAK kan alleen bij een voorwerp in een KAMER" % waar)
    if v["eigenaar"] == kamer and kamer is not None and v["vak"] is None:
        raise Fout("%s: %s ligt in kamer %s maar heeft geen VAK en LOOP" % (waar, naam, kamer))
    if kamer is None and v["eigenaar"] is None and False:
        pass
    if kamer is None and v["eigenaar"] not in ("eldric", None):
        raise Fout("%s: een voorwerp buiten een KAMER is BIJ eldric of NERGENS" % waar)
    if len(v["tekst"]) > MAX_NAAM:
        raise Fout("%s: de naam %r is te lang (hooguit %d tekens: 'Gebruik x met y' moet op de zinregel passen)"
                   % (waar, v["tekst"], MAX_NAAM))
    spel.voorwerpen[naam] = v
    spel.vw_volgorde.append(naam)
    return v


def nieuw_blok(oud, waarin, sleutel, waar):
    if oud is not None:
        sluit_blok(oud)
    lijst = []
    waarin[sleutel] = lijst
    return {"lijst": lijst, "stapel": [], "waar": waar}


def sluit_blok(blok):
    if blok["stapel"]:
        raise Fout("%s: ALS zonder EINDE" % blok["stapel"][-1][1])


def opdracht(blok, kop, w, waar):
    L = blok["lijst"]
    n = len(w)
    if kop == "ZEG":
        if n != 3 or not isinstance(w[1], str) or not is_tekst(w[2]):
            raise Fout('%s: ZEG spreker "tekst"' % waar)
        L.append(("ZEG", w[1], w[2][1], waar))
        return
    if any(is_tekst(x) for x in w):
        raise Fout("%s: %s kent geen tekst tussen aanhalingstekens" % (waar, kop))
    if kop == "ALS":
        rest = list(w[1:])
        niet = bool(rest) and rest[0] == "NIET"
        if niet:
            rest = rest[1:]
        if len(rest) == 2 and rest[0] == "vlag":
            cond = ("vlag", rest[1])
        elif len(rest) == 2 and rest[0] == "HEEFT":
            cond = ("heeft", rest[1])
        elif len(rest) == 3 and rest[0] == "STAND":
            cond = ("stand", rest[1], getal(rest[2], waar))
        else:
            raise Fout("%s: ALS [NIET] vlag naam | ALS [NIET] HEEFT voorwerp | ALS [NIET] STAND voorwerp n" % waar)
        L.append(("ALS", niet, cond, waar))
        blok["stapel"].append(("ALS", waar))
    elif kop == "ANDERS":
        if n != 1 or not blok["stapel"] or blok["stapel"][-1][0] != "ALS":
            raise Fout("%s: ANDERS zonder ALS" % waar)
        blok["stapel"][-1] = ("ANDERS", waar)
        L.append(("ANDERS", waar))
    elif kop == "EINDE":
        if n != 1 or not blok["stapel"]:
            raise Fout("%s: EINDE zonder ALS" % waar)
        blok["stapel"].pop()
        L.append(("EINDE", waar))
    elif kop in ("ZET", "WIS", "GEEF", "NEEM"):
        if n != 2:
            raise Fout("%s: %s %s" % (waar, kop, "vlag" if kop in ("ZET", "WIS") else "voorwerp"))
        L.append((kop, w[1], waar))
    elif kop == "PLAATS":
        if n != 3:
            raise Fout("%s: PLAATS voorwerp kamer" % waar)
        L.append(("PLAATS", w[1], w[2], waar))
    elif kop == "STAND":
        if n != 3:
            raise Fout("%s: STAND voorwerp n" % waar)
        L.append(("STAND", w[1], getal(w[2], waar), waar))
    elif kop == "LOOP":
        if n != 3:
            raise Fout("%s: LOOP eldric x,y  of  LOOP figuur x,y" % waar)
        x, y = punt(w[2], waar)
        if not (x < KAMER_B and y < KAMER_H):
            raise Fout("%s: LOOP buiten de kamer" % waar)
        if w[1] == "eldric":
            L.append(("LOOP", x, y, waar))
        else:
            L.append(("NPC_LOOP", w[1], x, y, waar))
    elif kop in ("PRAAT", "TOON", "VERBERG"):
        if n != 2:
            raise Fout("%s: %s naam" % (waar, kop))
        L.append((kop, w[1], waar))
    elif kop == "MUZIEK":
        if n != 2 or w[1] not in ("thema", "stil"):
            raise Fout("%s: MUZIEK thema  of  MUZIEK stil" % waar)
        L.append(("MUZIEK", 1 if w[1] == "thema" else 0, waar))
    elif kop == "GELUID":
        if n != 2 or w[1] not in GELUIDEN:
            raise Fout("%s: GELUID naam  (een van: %s)" % (waar, " ".join(GELUIDEN)))
        L.append(("GELUID", GELUIDEN.index(w[1]), waar))
    elif kop == "KIJK":
        if n != 3 or w[1] != "eldric" or w[2] not in RICHTINGEN:
            raise Fout("%s: KIJK eldric richting" % waar)
        L.append(("KIJK", RICHTINGEN[w[2]], waar))
    elif kop == "WACHT":
        if n != 2:
            raise Fout("%s: WACHT beelden" % waar)
        L.append(("WACHT", getal(w[1], waar, 1, 65535), waar))
    elif kop in ("TUSSENSCENE", "EINDE_TUSSENSCENE", "STOP"):
        if n != 1:
            raise Fout("%s: %s (zonder meer)" % (waar, kop))
        L.append((kop, waar))
    elif kop == "PATCH":
        if n != 2:
            raise Fout("%s: PATCH naam" % waar)
        L.append(("PATCH", w[1], waar))
    elif kop == "KAMER":
        if w[3] not in RICHTINGEN:
            raise Fout("%s: KAMER naam x,y richting" % waar)
        x, y = punt(w[2], waar)
        L.append(("KAMER", w[1], x, y, RICHTINGEN[w[3]], waar))


def patches_van_kamers():
    """naam -> (kamer, nummer) uit data/kamers.txt"""
    import kamer as kamermod
    uit = {}
    for knaam, _, o, _ in kamermod.lees_lijst(os.path.join(WORTEL, "data", "kamers.txt")):
        for i, (pnaam, _, _) in enumerate(o["patches"]):
            if pnaam in uit:
                raise Fout("data/kamers.txt: patch %s bestaat in twee kamers" % pnaam)
            uit[pnaam] = (knaam, i)
    return uit


# ---------------------------------------------------------------------------------------------------
# Controleren
# ---------------------------------------------------------------------------------------------------
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


def in_loopvak(k, x, y):
    return any(a[0] <= x <= a[2] and a[1] <= y <= a[3] for a in k["vakken"])


def controleer_kamers(spel, kleurcontrole=True):
    import loopkaart
    for naam, k in spel.kamers.items():
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
        if not kleurcontrole:
            continue
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
            opties = {n: o for n, _, o, _ in kamermod.lees_lijst(os.path.join(WORTEL, "data", "kamers.txt"))}
            if not (opties.get(naam) or {}).get("voorgrond"):
                raise Fout("%s: ACHTER, maar de kamer heeft geen voorgrond (voorgrond=... in data/kamers.txt)" % k["achter"][4])
    if spel.begin is None:
        raise Fout("geen BEGIN in de scripts")
    kamer, (x, y), _, waar = spel.begin
    if kamer not in spel.kamers:
        raise Fout("%s: onbekende kamer %s" % (waar, kamer))
    if not in_loopvak(spel.kamers[kamer], x, y):
        raise Fout("%s: het beginpunt staat niet in een loopvak" % waar)


def alle_scripts(spel):
    """(script, omschrijving, voorwerp of None, tweede voorwerp of None)."""
    for ww, s in spel.standaard.items():
        yield s, "STANDAARD %s" % ww, None, None
    for naam, s in spel.losse.items():
        yield s, "SCRIPT %s" % naam, None, None
    for k in spel.kamers.values():
        if "binnenkomst" in k:
            yield k["binnenkomst"], "BINNENKOMST %s" % k["naam"], None, None
    for g in spel.gesprekken.values():
        for i, k in enumerate(g["keuzes"]):
            yield k["script"], "GESPREK %s: %s" % (g["naam"], k["tekst"][:24]), None, None
    for v in spel.voorwerpen.values():
        for ww, s in v["scripts"].items():
            yield s, "%s %s" % (ww, v["naam"]), v["naam"], None
        for (ww, ander), s in v["paren"].items():
            yield s, "%s %s %s %s" % (ww, ander, TWEE[ww], v["naam"]), v["naam"], ander


def controleer_scripts(spel):
    import c64beeld
    patches = patches_van_kamers()
    for naam in spel.kamers:
        import kamer as kamermod
        if naam not in {n for n, *_ in kamermod.lees_lijst(os.path.join(WORTEL, "data", "kamers.txt"))}:
            raise Fout("%s: kamer %s heeft geen plaatje in data/kamers.txt" % (spel.kamers[naam]["waar"], naam))
    for naam, (kleur, waar) in spel.sprekers.items():
        if kleur not in c64beeld.NAMEN:
            raise Fout("%s: onbekende kleur %s" % (waar, kleur))
    gezet = {o[1] for s, *_ in alle_scripts(spel) for o in s if o[0] == "ZET"}
    getest = []
    for v in spel.voorwerpen.values():
        tekst_codes(v["tekst"], v["waar"], 1)
        if v["kamer"] is not None and v["loop"] is not None and not in_loopvak(spel.kamers[v["kamer"]], *v["loop"]):
            raise Fout("%s: het LOOP-punt van %s ligt niet in een loopvak" % (v["waar"], v["naam"]))
        for (ww, ander) in v["paren"]:
            if ander not in spel.voorwerpen:
                raise Fout("%s: %s %s: onbekend voorwerp %s" % (v["waar"], ww, ander, ander))
    for s, wie, eig, ander in alle_scripts(spel):
        for o in s:
            waar = o[-1]
            k = o[0]
            if k == "ZEG":
                if o[1] not in spel.sprekers:
                    raise Fout("%s: onbekende spreker %s (zet hem in een SPREKER-regel)" % (waar, o[1]))
                tekst_codes(o[2], waar)
            elif k == "ALS":
                cond = o[2]
                if cond[0] == "vlag":
                    getest.append((cond[1], waar))
                elif cond[1] not in spel.voorwerpen:
                    raise Fout("%s: onbekend voorwerp %s" % (waar, cond[1]))
            elif k in ("GEEF", "NEEM", "STAND") and o[1] not in spel.voorwerpen:
                raise Fout("%s: onbekend voorwerp %s" % (waar, o[1]))
            elif k == "PLAATS":
                if o[1] not in spel.voorwerpen:
                    raise Fout("%s: onbekend voorwerp %s" % (waar, o[1]))
                if o[2] not in spel.kamers:
                    raise Fout("%s: onbekende kamer %s" % (waar, o[2]))
                if spel.voorwerpen[o[1]]["vak"] is None or spel.voorwerpen[o[1]]["kamer"] != o[2]:
                    raise Fout("%s: %s kan alleen in de kamer waar zijn VAK bij hoort" % (waar, o[1]))
            elif k == "PRAAT":
                if o[1] not in spel.gesprekken:
                    raise Fout("%s: onbekend gesprek %s" % (waar, o[1]))
            elif k in ("TOON", "VERBERG", "NPC_LOOP"):
                if o[1] not in spel.actors:
                    raise Fout("%s: onbekende figuur %s (ACTOR in een KAMER)" % (waar, o[1]))
            elif k == "PATCH":
                if o[1] not in patches:
                    raise Fout("%s: onbekende patch %s (zet hem in data/kamers.txt: patch=%s:x,y,b,h:plaatje)"
                               % (waar, o[1], o[1]))
            elif k == "KAMER":
                if o[1] not in spel.kamers:
                    raise Fout("%s: onbekende kamer %s" % (waar, o[1]))
                if not in_loopvak(spel.kamers[o[1]], o[2], o[3]):
                    raise Fout("%s: KAMER %s %d,%d: dat punt ligt niet in een loopvak van die kamer" % (waar, *o[1:4]))
            elif k in ("ZET", "WIS") and not re.fullmatch(r"[a-z_][a-z0-9_]*", o[1]):
                raise Fout("%s: een vlagnaam is kleine letters, cijfers en _ (%r)" % (waar, o[1]))
    import json
    kostuums = json.load(open(os.path.join(WORTEL, "build", "gen", "kostuums.json")))
    per_kamer = {}
    for a in spel.actors.values():
        if a["kostuum"] not in kostuums:
            raise Fout("%s: onbekend kostuum %s (tools/costume.py: %s)" % (a["waar"], a["kostuum"], ", ".join(kostuums)))
        if a["zichtbaar"]:
            per_kamer.setdefault(a["kamer"], []).append(a["naam"])
        if len(per_kamer.get(a["kamer"], [])) > MAX_NPC_KAMER:
            raise Fout("%s: hooguit %d figuren tegelijk zichtbaar per kamer (de sprites zijn op); zet de rest "
                       "VERBORGEN en TOON ze later" % (a["waar"], MAX_NPC_KAMER))
    for g in spel.gesprekken.values():
        if not g["keuzes"]:
            raise Fout("%s: GESPREK %s heeft geen keuzes" % (g["waar"], g["naam"]))
        if not any(k["einde"] for k in g["keuzes"]):
            raise Fout("%s: GESPREK %s heeft geen keuze met EINDE: je komt er nooit uit" % (g["waar"], g["naam"]))
        for k in g["keuzes"]:
            tekst_codes(k["tekst"], k["waar"], 1)
            if k["cond"]:
                c = k["cond"][1]
                if c[0] == "vlag":
                    getest.append((c[1], k["waar"]))
                elif c[1] not in spel.voorwerpen:
                    raise Fout("%s: onbekend voorwerp %s" % (k["waar"], c[1]))
    for vlag, waar in getest:
        if vlag not in gezet:
            raise Fout("%s: vlag %s wordt getest maar nergens gezet (ZET %s)" % (waar, vlag, vlag))
    if len(gezet) > MAX_VLAGGEN:
        raise Fout("meer dan %d vlaggen" % MAX_VLAGGEN)
    if len(spel.voorwerpen) > MAX_VOORWERPEN:
        raise Fout("meer dan %d voorwerpen" % MAX_VOORWERPEN)
    if spel.doel and spel.doel[0] not in gezet:
        raise Fout("%s: DOEL %s wordt nergens gezet" % (spel.doel[1], spel.doel[0]))


def uitspeelbaar(spel):
    """Kan DOEL gehaald worden? Vanaf het begin: welke vlaggen en voorwerpen kun je krijgen, en welke voorwerpen
    liggen ergens (en zijn dus aan te klikken)? Een script telt mee als zijn voorwerp(en) bereikbaar zijn en de
    ALS-voorwaarden erboven al te halen zijn (NIET-voorwaarden tellen als waar te maken). Geeft (gehaald, stappen)."""
    vlaggen = set()
    in_bezit = {n for n, v in spel.voorwerpen.items() if v["eigenaar"] == "eldric"}
    liggend = {n for n, v in spel.voorwerpen.items() if v["eigenaar"] not in ("eldric", None)}
    stappen = []

    def effecten(script):
        uit, stapel = [], []
        for o in script:
            if o[0] == "ALS":
                stapel.append(None if o[1] else o[2])
            elif o[0] == "ANDERS":
                stapel[-1] = None
            elif o[0] == "EINDE":
                stapel.pop()
            elif o[0] in ("ZET", "GEEF", "PLAATS", "PRAAT"):
                uit.append((o, [c for c in stapel if c]))
        return uit

    def voldaan(c):
        if c[0] == "vlag":
            return c[1] in vlaggen
        if c[0] == "heeft":
            return c[1] in in_bezit
        return True

    # wat je kunt oppakken (ooit GEEF, of begint bij Eldric): daarmee iets doen kan pas als je het hebt
    draagbaar = set(in_bezit) | {o[1] for sc, *_ in alle_scripts(spel) for o in sc if o[0] == "GEEF"}
    gesprekken = set()
    keuze_van = {}
    for g in spel.gesprekken.values():
        for k in g["keuzes"]:
            keuze_van[id(k["script"])] = (g["naam"], k["cond"])
    veranderd = True
    while veranderd:
        veranderd = False
        for s, wie, eig, ander in alle_scripts(spel):
            if id(s) in keuze_van:                 # een keuze: het gesprek moet begonnen zijn, en zijn ALS klopt
                gnaam, cond = keuze_van[id(s)]
                if gnaam not in gesprekken or (cond and not cond[0] and not voldaan(cond[1])):
                    continue
            if eig is not None and eig not in liggend and eig not in in_bezit:
                continue
            if ander is not None and ander not in in_bezit and (ander in draagbaar or ander not in liggend):
                continue
            for o, eisen in effecten(s):
                if not all(voldaan(c) for c in eisen):
                    continue
                if o[0] == "ZET" and o[1] not in vlaggen:
                    vlaggen.add(o[1])
                    stappen.append("%-44s -> vlag %s" % (wie, o[1]))
                    veranderd = True
                elif o[0] == "GEEF" and o[1] not in in_bezit:
                    in_bezit.add(o[1])
                    stappen.append("%-44s -> krijgt %s" % (wie, o[1]))
                    veranderd = True
                elif o[0] == "PRAAT" and o[1] not in gesprekken:
                    gesprekken.add(o[1])
                    veranderd = True
                elif o[0] == "PLAATS" and o[1] not in liggend:
                    liggend.add(o[1])
                    stappen.append("%-44s -> %s ligt in %s" % (wie, o[1], o[2]))
                    veranderd = True
    return (spel.doel is None or spel.doel[0] in vlaggen), stappen


# ---------------------------------------------------------------------------------------------------
# Schrijven
# ---------------------------------------------------------------------------------------------------
class Uitvoer:
    def __init__(self, spel):
        self.spel, self.L, self.teksten, self.vlaggen, self.nummer = spel, [], [], {}, 0
        self.vw = {n: i for i, n in enumerate(spel.vw_volgorde)}
        self.km = {n: i for i, n in enumerate(spel.kamer_volgorde)}
        self.patches = patches_van_kamers()

    def vlag(self, naam):
        if naam not in self.vlaggen:
            self.vlaggen[naam] = len(self.vlaggen)
        return self.vlaggen[naam]

    def label(self):
        self.nummer += 1
        return "l_%d" % self.nummer

    def script(self, label, script):
        L, vw, km, sp = self.L, self.vw, self.km, list(self.spel.sprekers)
        L.append("%s:" % label)
        stapel = []
        for o in script:
            k = o[0]
            if k == "ZEG":
                codes, n = tekst_codes(o[2], o[3])
                t = "t_%d" % len(self.teksten)
                self.teksten.append((t, codes, o[2]))
                duur = min(65535, 50 + (n * 5 + 1) // 2)        # 1 s + 1 s per 20 tekens
                L.append("        .byte $%02x, %d, <%s, >%s, %d, %d    // ZEG %s" % (
                    OP["ZEG"], sp.index(o[1]), t, t, duur & 255, duur >> 8, o[1]))
            elif k == "ALS":
                niet, cond = o[1], o[2]
                anders = self.label()
                stapel.append([anders, None])
                # de opcode springt als de voorwaarde NIET klopt
                if cond[0] == "vlag":
                    L.append("        .byte $%02x, %d, <%s, >%s    // ALS %svlag %s" % (
                        OP["ALS_NIET_VLAG" if niet else "ALS_VLAG"], self.vlag(cond[1]), anders, anders,
                        "NIET " if niet else "", cond[1]))
                elif cond[0] == "heeft":
                    L.append("        .byte $%02x, %d, <%s, >%s    // ALS %sHEEFT %s" % (
                        OP["ALS_NIET_HEEFT" if niet else "ALS_HEEFT"], vw[cond[1]], anders, anders,
                        "NIET " if niet else "", cond[1]))
                else:
                    L.append("        .byte $%02x, %d, %d, <%s, >%s    // ALS %sSTAND %s %d" % (
                        OP["ALS_NIET_STAND" if niet else "ALS_STAND"], vw[cond[1]], cond[2], anders, anders,
                        "NIET " if niet else "", cond[1], cond[2]))
            elif k == "ANDERS":
                einde = self.label()
                L.append("        .byte $%02x, <%s, >%s    // ANDERS" % (OP["SPRING"], einde, einde))
                L.append("%s:" % stapel[-1][0])
                stapel[-1][1] = einde
            elif k == "EINDE":
                anders, einde = stapel.pop()
                L.append("%s:    // EINDE" % (einde or anders))
            elif k in ("ZET", "WIS"):
                L.append("        .byte $%02x, %d    // %s %s" % (OP[k], self.vlag(o[1]), k, o[1]))
            elif k in ("GEEF", "NEEM"):
                L.append("        .byte $%02x, %d    // %s %s" % (OP[k], vw[o[1]], k, o[1]))
            elif k == "PLAATS":
                L.append("        .byte $%02x, %d, %d    // PLAATS %s %s" % (OP[k], vw[o[1]], km[o[2]], o[1], o[2]))
            elif k == "STAND":
                L.append("        .byte $%02x, %d, %d    // STAND %s %d" % (OP[k], vw[o[1]], o[2], o[1], o[2]))
            elif k == "LOOP":
                x = o[1] * 2
                L.append("        .byte $%02x, %d, %d, %d    // LOOP eldric %d,%d" % (OP[k], x & 255, x >> 8, o[2], o[1], o[2]))
            elif k == "MUZIEK":
                L.append("        .byte $%02x, %d    // MUZIEK %s" % (OP[k], o[1], "thema" if o[1] else "stil"))
            elif k == "GELUID":
                L.append("        .byte $%02x, %d    // GELUID %s" % (OP[k], o[1], GELUIDEN[o[1]]))
            elif k == "KIJK":
                L.append("        .byte $%02x, %d    // KIJK eldric" % (OP[k], o[1]))
            elif k == "WACHT":
                L.append("        .byte $%02x, %d, %d    // WACHT %d" % (OP[k], o[1] & 255, o[1] >> 8, o[1]))
            elif k in ("TUSSENSCENE", "EINDE_TUSSENSCENE", "STOP"):
                L.append("        .byte $%02x    // %s" % (OP[k], k))
            elif k == "PATCH":
                pk, pn = self.patches[o[1]]
                L.append("        .byte $%02x, %d, %d    // PATCH %s (%s)" % (OP[k], km[pk], pn, o[1], pk))
            elif k == "PRAAT":
                L.append("        .byte $%02x, <gesprek_%s, >gesprek_%s    // PRAAT %s" % (OP[k], o[1], o[1], o[1]))
            elif k in ("TOON", "VERBERG"):
                L.append("        .byte $%02x, %d    // %s %s" % (OP[k], self.spel.actor_volgorde.index(o[1]), k, o[1]))
            elif k == "NPC_LOOP":
                x = o[2] * 2
                L.append("        .byte $%02x, %d, %d, %d, %d    // LOOP %s %d,%d" % (
                    OP[k], self.spel.actor_volgorde.index(o[1]), x & 255, x >> 8, o[3], o[1], o[2], o[3]))
            elif k == "KAMER":
                x = o[2] * 2
                L.append("        .byte $%02x, %d, %d, %d, %d, %d    // KAMER %s %d,%d" % (
                    OP[k], km[o[1]], x & 255, x >> 8, o[3], o[4], o[1], o[2], o[3]))
        L.append("        .byte $%02x    // einde" % OP["STOP"])


def schrijf(spel, pad, json_pad):
    import c64beeld
    u = Uitvoer(spel)
    L, vw, km = u.L, u.vw, u.km
    L += ["// spel.asm — gemaakt door tools/scriptc.py uit scripts/*.hcs; niet met de hand wijzigen",
          ".segment Data"]
    for i, sp in enumerate(spel.sprekers):
        L.append(".const SPREKER_%s = %d" % (sp.upper(), i))
    L.append("spreker_kleur: .byte %s" % ", ".join(str(c64beeld.NAMEN.index(k)) for k, _ in spel.sprekers.values()))
    for ww in WERKWOORDEN:
        if ww in spel.standaard:
            u.script("std_%s" % ww.lower(), spel.standaard[ww])
    L.append("standaard_scripts: .word %s" % ", ".join(
        "std_%s" % ww.lower() if ww in spel.standaard else "0" for ww in WERKWOORDEN))
    for naam, s in spel.losse.items():
        u.script("scr_%s" % naam, s)
    # gesprekken: aantal keuzes; per keuze: einde, soort voorwaarde, argument, tekst (lo, hi), script (lo, hi)
    #   soort: 0 geen, 1 vlag, 2 NIET vlag, 3 HEEFT, 4 NIET HEEFT
    for g in spel.gesprekken.values():
        for i, k in enumerate(g["keuzes"]):
            codes, _ = tekst_codes(k["tekst"], k["waar"], 1)
            L.append("kz_%s_%d: .byte %s, 0    // %s" % (g["naam"], i, ", ".join("$%02x" % c for c in codes), k["tekst"]))
            u.script("ks_%s_%d" % (g["naam"], i), k["script"])
        L.append("gesprek_%s: .byte %d" % (g["naam"], len(g["keuzes"])))
        for i, k in enumerate(g["keuzes"]):
            soort, arg = 0, 0
            if k["cond"]:
                niet, c = k["cond"]
                if c[0] == "vlag":
                    soort, arg = (2 if niet else 1), u.vlag(c[1])
                else:
                    soort, arg = (4 if niet else 3), vw[c[1]]
            L.append("        .byte %d, %d, %d, <kz_%s_%d, >kz_%s_%d, <ks_%s_%d, >ks_%s_%d" % (
                1 if k["einde"] else 0, soort, arg, g["naam"], i, g["naam"], i, g["naam"], i, g["naam"], i))
    # figuren (NPC's)
    import json
    kostuums = json.load(open(os.path.join(WORTEL, "build", "gen", "kostuums.json")))
    acts = [spel.actors[a] for a in spel.actor_volgorde]
    L.append(".const AANTAL_NPC = %d" % len(acts))
    for i, a in enumerate(acts):
        L.append(".const NPC_%s = %d" % (a["naam"].upper(), i))

    def nrij(label, waarden):
        L.append("%s: .byte %s" % (label, ", ".join(waarden) if waarden else "0"))
    nrij("npc_kamer", [str(km[a["kamer"]]) for a in acts])
    nrij("npc_x_lo", [str((a["x"] * 2) & 255) for a in acts])
    nrij("npc_x_hi", [str((a["x"] * 2) >> 8) for a in acts])
    nrij("npc_y", [str(a["y"]) for a in acts])
    nrij("npc_zichtbaar_begin", ["1" if a["zichtbaar"] else "0" for a in acts])
    nrij("npc_kb", [str(kostuums[a["kostuum"]]["kb"]) for a in acts])
    nrij("npc_ko", [str(kostuums[a["kostuum"]]["ko"]) for a in acts])
    nrij("npc_vorm", [str(kostuums[a["kostuum"]]["vorm"]) for a in acts])
    nrij("npc_voeten", [str(kostuums[a["kostuum"]]["voeten"]) for a in acts])
    nrij("npc_data_lo", ["<npc_%s" % a["kostuum"] for a in acts])
    nrij("npc_data_hi", [">npc_%s" % a["kostuum"] for a in acts])
    # per voorwerp: 12 scripts (werkwoorden), dan paren (werkwoord, ander voorwerp, script), $ff
    for naam in spel.vw_volgorde:
        v = spel.voorwerpen[naam]
        codes, _ = tekst_codes(v["tekst"], v["waar"], 1)
        L.append("naam_%s: .byte %s, 0    // %s" % (naam, ", ".join("$%02x" % c for c in codes), v["tekst"]))
        for ww, s in v["scripts"].items():
            u.script("s_%s_%s" % (naam, ww.lower()), s)
        for (ww, ander), s in v["paren"].items():
            u.script("p_%s_%s_%s" % (naam, ww.lower(), ander), s)
        L.append("scripts_%s: .word %s" % (naam, ", ".join(
            "s_%s_%s" % (naam, ww.lower()) if ww in v["scripts"] else "0" for ww in WERKWOORDEN)))
        for (ww, ander) in v["paren"]:
            L.append("        .byte %d, %d, <p_%s_%s_%s, >p_%s_%s_%s    // %s %s" % (
                WERKWOORDEN.index(ww), vw[ander], naam, ww.lower(), ander, naam, ww.lower(), ander, ww, ander))
        L.append("        .byte $ff")
    L.append(".const AANTAL_VW = %d" % len(spel.vw_volgorde))
    for naam in spel.vw_volgorde:
        L.append(".const VW_%s = %d" % (naam.upper(), vw[naam]))
    vs = [spel.voorwerpen[x] for x in spel.vw_volgorde]

    def eigenaar(v):
        return EIGENAAR_ELDRIC if v["eigenaar"] == "eldric" else EIGENAAR_NERGENS if v["eigenaar"] is None \
            else km[v["eigenaar"]]

    def rij(label, waarden):
        L.append("%s: .byte %s" % (label, ", ".join(waarden) if waarden else "0"))
    leeg = (0, 0, 0, 0)
    rij("vw_eigenaar_begin", [str(eigenaar(v)) for v in vs])
    rij("vw_stand_begin", [str(v["stand"]) for v in vs])
    rij("vw_x1_lo", ["$%02x" % (((v["vak"] or leeg)[0] * 2) & 255) for v in vs])
    rij("vw_x1_hi", ["$%02x" % (((v["vak"] or leeg)[0] * 2) >> 8) for v in vs])
    rij("vw_x2_lo", ["$%02x" % ((v["vak"][2] * 2 + 1) & 255) if v["vak"] else "0" for v in vs])
    rij("vw_x2_hi", ["$%02x" % ((v["vak"][2] * 2 + 1) >> 8) if v["vak"] else "0" for v in vs])
    rij("vw_y1", [str((v["vak"] or leeg)[1]) for v in vs])
    rij("vw_y2", [str((v["vak"] or leeg)[3]) for v in vs])
    rij("vw_loop_x_lo", ["$%02x" % (((v["loop"] or (0, 0))[0] * 2) & 255) for v in vs])
    rij("vw_loop_x_hi", ["$%02x" % (((v["loop"] or (0, 0))[0] * 2) >> 8) for v in vs])
    rij("vw_loop_y", [str((v["loop"] or (0, 0))[1]) for v in vs])
    rij("vw_richting", [str(v["richting"]) for v in vs])
    rij("vw_heeft_vak", ["1" if v["vak"] else "0" for v in vs])
    rij("vw_naam_lo", ["<naam_%s" % v["naam"] for v in vs])
    rij("vw_naam_hi", [">naam_%s" % v["naam"] for v in vs])
    rij("vw_scripts_lo", ["<scripts_%s" % v["naam"] for v in vs])
    rij("vw_scripts_hi", [">scripts_%s" % v["naam"] for v in vs])

    for naam in spel.kamer_volgorde:
        k = spel.kamers[naam]
        v, b = k["vakken"], k["buren"]
        L.append(".const KAMER_%s = %d" % (naam.upper(), km[naam]))
        L.append("loopvakken_%s:    // aantal, dan per veld een rij van <aantal> bytes (x in schermpixels)" % naam)
        L.append("        .byte %d" % len(v))
        velden = [
            ("x1 lo", [(a[0] * 2) & 255 for a in v]), ("x1 hi", [(a[0] * 2) >> 8 for a in v]),
            ("x2 lo", [(a[2] * 2 + 1) & 255 for a in v]), ("x2 hi", [(a[2] * 2 + 1) >> 8 for a in v]),
            ("y1", [a[1] for a in v]), ("y2", [a[3] for a in v]),
            ("buren lo", [x & 255 for x in b]), ("buren hi", [x >> 8 for x in b])]
        for wat, r in velden:
            L.append("        .byte %s    // %s" % (", ".join("$%02x" % x for x in r), wat))
        ach = k["achter"]
        L.append("achter_%s:    // ACHTER: aantal (0/1), x1 lo, x1 hi, x2 lo, x2 hi, y1, y2" % naam)
        if ach:
            x1, y1, x2, y2, _ = ach
            L.append("        .byte 1, %d, %d, %d, %d, %d, %d" % ((x1 * 2) & 255, (x1 * 2) >> 8, (x2 * 2 + 1) & 255,
                                                               (x2 * 2 + 1) >> 8, y1, y2))
        else:
            L.append("        .byte 0, 0, 0, 0, 0, 0, 0")
        sch = k["schaal"]
        L.append("schaal_%s: .byte %d%s" % (naam, len(sch), "".join(", %d" % g for g in sch)))
        L.append("flakker_%s: .byte %d    // aantal; per gebied kolom, rij, breedte, hoogte (vakjes), 16 bytes kleur -> volgende" % (
            naam, len(k["flakker"])))
        for x, y, b, h, kleuren, _ in k["flakker"]:
            tabel = list(range(16))
            for i, kl in enumerate(kleuren):
                tabel[kl] = kleuren[(i + 1) % len(kleuren)]
            L.append("        .byte %d, %d, %d, %d, %s" % (x // 4, y // 8, b // 4, h // 8, ", ".join(str(t) for t in tabel)))
        if "binnenkomst" in k:
            u.script("binnen_%s" % naam, k["binnenkomst"])
    L.append(".const AANTAL_KAMERS = %d" % len(spel.kamer_volgorde))
    for veld in ("loopvakken", "achter", "schaal", "flakker"):
        L.append("kamer_%s_lo: .byte %s" % (veld, ", ".join("<%s_%s" % (veld, n) for n in spel.kamer_volgorde)))
        L.append("kamer_%s_hi: .byte %s" % (veld, ", ".join(">%s_%s" % (veld, n) for n in spel.kamer_volgorde)))
    for n in spel.kamer_volgorde:            # de bestandsnaam op de diskette (PETSCII: hoofdletters)
        L.append("bestand_%s: .byte %s    // %s" % (n, ", ".join("$%02x" % ord(c) for c in n.upper()), n))
    L.append("kamer_bestand_lo: .byte %s" % ", ".join("<bestand_%s" % n for n in spel.kamer_volgorde))
    L.append("kamer_bestand_hi: .byte %s" % ", ".join(">bestand_%s" % n for n in spel.kamer_volgorde))
    L.append("kamer_bestand_len: .byte %s" % ", ".join(str(len(n)) for n in spel.kamer_volgorde))
    L.append("kamer_binnen_lo: .byte %s" % ", ".join(
        "<binnen_%s" % n if "binnenkomst" in spel.kamers[n] else "0" for n in spel.kamer_volgorde))
    L.append("kamer_binnen_hi: .byte %s" % ", ".join(
        ">binnen_%s" % n if "binnenkomst" in spel.kamers[n] else "0" for n in spel.kamer_volgorde))
    kamer, (x, y), r, _ = spel.begin
    L += [".const BEGIN_KAMER = KAMER_%s" % kamer.upper(), ".const BEGIN_X = %d    // schermpixels" % (x * 2),
          ".const BEGIN_Y = %d" % y, ".const BEGIN_RICHTING = %d" % r]
    L.append(".const DOEL_VLAG = %d    // %s" % ((u.vlag(spel.doel[0]), spel.doel[0]) if spel.doel else (255, "geen")))
    L.append(".const AANTAL_VLAGGEN = %d" % len(u.vlaggen))
    L.append("// teksten (schermcodes; $%02x = tweede regel, 0 = einde)" % NIEUWE_REGEL)
    for t, codes, tekst in u.teksten:
        L.append("%s: .byte %s, 0    // %s" % (t, ", ".join("$%02x" % c for c in codes), tekst[:60]))
    open(pad, "w").write("\n".join(L) + "\n")
    json.dump({"vlaggen": u.vlaggen, "voorwerpen": vw, "kamers": km, "figuren": spel.actor_volgorde,
               "eigenaar": {"eldric": EIGENAAR_ELDRIC, "nergens": EIGENAAR_NERGENS},
               "werkwoorden": WERKWOORDEN, "losse_scripts": list(spel.losse)},
              open(json_pad, "w"), indent=1)


def compileer(mappen, uitmap, kleurcontrole=True):
    bestanden = []
    for m in mappen:
        bestanden += sorted(glob.glob(os.path.join(m, "*.hcs")))
    spel = lees(bestanden)
    controleer_kamers(spel, kleurcontrole)
    controleer_scripts(spel)
    gehaald, stappen = uitspeelbaar(spel)
    if not gehaald:
        raise Fout("%s: DOEL %s is niet te halen. Wel te krijgen:\n  %s" % (
            spel.doel[1], spel.doel[0], "\n  ".join(stappen) or "(niets)"))
    os.makedirs(uitmap, exist_ok=True)
    schrijf(spel, os.path.join(uitmap, "spel.asm"), os.path.join(uitmap, "spel.json"))
    with open(os.path.join(uitmap, "puzzelstappen.txt"), "w") as f:
        f.write("# puzzelstappen — gemaakt door tools/scriptc.py: wat er te krijgen is, in een volgorde die kan\n")
        f.write("\n".join(stappen) + "\n")
        f.write(("# DOEL %s: te halen\n" % spel.doel[0]) if spel.doel else "# geen DOEL\n")
    return spel, bestanden, stappen


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    mappen = [sys.argv[1]] + sys.argv[3:]
    try:
        spel, bestanden, stappen = compileer(mappen, sys.argv[2])
    except Fout as e:
        print("[scriptc] FOUT: %s" % e, file=sys.stderr)
        sys.exit(1)
    print("[scriptc] %d bestanden, %d kamers, %d voorwerpen, %d loopvakken, %d puzzelstappen%s" % (
        len(bestanden), len(spel.kamers), len(spel.voorwerpen), sum(len(k["vakken"]) for k in spel.kamers.values()),
        len(stappen), ", DOEL te halen" if spel.doel else ""))


if __name__ == "__main__":
    main()
