#!/usr/bin/env python3
"""taal.py — vertalingen van Hollow Crown: de Nederlandse teksten eruit halen, en vertaalde kopieën maken.

    python3 tools/taal.py extract                  schrijft tools/taal/bron.json (alle teksten die vertaald worden)
    python3 tools/taal.py maak en build/gen/taal/en
                                                   vertaalde kopieën: <uit>/scripts/*.hcs en <uit>/teksten.asm
    python3 tools/taal.py controleer en            welke teksten ontbreken of te lang zijn

Vertaald wordt (scripts/*.hcs): ZEG "...", KEUZE "...", de naam van een VOORWERP ("..."), HOOFDSTUK n "...";
(src/teksten_nl.asm): elke .text "..." behalve bestandsnamen. Een vertaling staat in tools/taal/<taal>.json:
    {"zeg": {"<nl>": "<vertaling>", ...}, "naam": {...}, "keuze": {...}, "hoofdstuk": {...}, "ui": {...}}
Regels: een zin (ZEG) past op 2 regels van 40 tekens (woorden worden niet afgebroken), een keuze op 1 regel van 40, een
naam hooguit 13 tekens, een werkwoord hooguit 9; alleen tekens die het lettertype kent (tools/lettertype.py).
"""
import json, os, re, sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAALMAP = os.path.join(WORTEL, "tools", "taal")
TALEN = {"nl": "Nederlands", "en": "English", "de": "Deutsch", "fr": "Français"}

R_ZEG = re.compile(r'^(\s*ZEG\s+\w+\s+)"([^"]*)"(.*)$')
R_KEUZE = re.compile(r'^(\s*KEUZE\s+)"([^"]*)"(.*)$')
R_VW = re.compile(r'^(VOORWERP\s+\w+\s+)"([^"]*)"(.*)$')
R_HS = re.compile(r'^(HOOFDSTUK\s+\d+\s+)"([^"]*)"(.*)$')
R_TEXT = re.compile(r'^(\s*(?:\w+:\s*)?\.text\s+)"([^"]*)"(.*)$')
GEEN_VERTALING = {"TITEL", "HCSAVE", "S0:HCSAVE", "Bosskey", "Exit"}     # bestandsnamen en wat in elke taal gelijk is
MAX = {"zeg": 80, "keuze": 40, "naam": 13, "hoofdstuk": 28}
WERKWOORDEN = {"Ga naar", "Pak", "Gebruik", "Open", "Bekijk", "Praat met", "Geef", "Sluit", "Duw", "Trek", "Lees",
               "Wat is"}


def regels_hcs():
    for naam in sorted(os.listdir(os.path.join(WORTEL, "scripts"))):
        if naam.endswith(".hcs"):
            pad = os.path.join(WORTEL, "scripts", naam)
            for nr, r in enumerate(open(pad, encoding="utf-8"), 1):
                yield naam, nr, r.rstrip("\n")


def soort_van(regel):
    for soort, rx in (("zeg", R_ZEG), ("keuze", R_KEUZE), ("naam", R_VW), ("hoofdstuk", R_HS)):
        m = rx.match(regel)
        if m:
            return soort, m
    return None, None


def extract():
    bron = {"zeg": {}, "keuze": {}, "naam": {}, "hoofdstuk": {}, "ui": {}}
    for naam, nr, r in regels_hcs():
        soort, m = soort_van(r)
        if soort:
            info = bron[soort].setdefault(m.group(2), {"waar": [], "max": MAX[soort]})
            info["waar"].append("%s:%d" % (naam, nr))
            if soort == "zeg":
                info.setdefault("spreker", r.split()[1])
    for nr, r in enumerate(open(os.path.join(WORTEL, "src", "teksten_nl.asm"), encoding="utf-8"), 1):
        m = R_TEXT.match(r)
        if m and m.group(2) not in GEEN_VERTALING:
            maxlen = 9 if m.group(2) in WERKWOORDEN else (5 if m.group(2) in ("met", "aan") else 40)
            if len(m.group(2)) > 40:
                maxlen = 0                                     # (de scrolltekst van het intro: geen grens)
            bron["ui"].setdefault(m.group(2), {"waar": ["teksten_nl.asm:%d" % nr], "max": maxlen})
    os.makedirs(TAALMAP, exist_ok=True)
    json.dump(bron, open(os.path.join(TAALMAP, "bron.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[taal] tools/taal/bron.json: %s" % ", ".join("%d %s" % (len(v), k) for k, v in bron.items()))


def laad(taal):
    return json.load(open(os.path.join(TAALMAP, taal + ".json"), encoding="utf-8"))


def vertaal(vt, soort, tekst, waar, fouten):
    if soort == "ui" and tekst in GEEN_VERTALING:
        return tekst
    t = vt.get(soort, {}).get(tekst)
    if t is None:
        fouten.append("%s: geen vertaling (%s): %r" % (waar, soort, tekst))
        return tekst
    return t


def maak(taal, uit):
    vt = laad(taal) if taal != "nl" else {}
    fouten = []
    os.makedirs(os.path.join(uit, "scripts"), exist_ok=True)
    for naam in sorted(os.listdir(os.path.join(WORTEL, "scripts"))):
        if not naam.endswith(".hcs"):
            continue
        regels = []
        for nr, r in enumerate(open(os.path.join(WORTEL, "scripts", naam), encoding="utf-8"), 1):
            r = r.rstrip("\n")
            soort, m = soort_van(r)
            if soort and taal != "nl":
                r = m.group(1) + '"' + vertaal(vt, soort, m.group(2), "%s:%d" % (naam, nr), fouten) + '"' + m.group(3)
            regels.append(r)
        open(os.path.join(uit, "scripts", naam), "w", encoding="utf-8").write("\n".join(regels) + "\n")
    # de vaste teksten: elke .text "..." wordt .byte met de codes van ons lettertype (dan kunnen ook ä, ß, ç erin)
    sys.path.insert(0, os.path.join(WORTEL, "tools"))
    import lettertype
    regels = []
    for nr, r in enumerate(open(os.path.join(WORTEL, "src", "teksten_nl.asm"), encoding="utf-8"), 1):
        r = r.rstrip("\n")
        m = R_TEXT.match(r)
        if m and m.group(2) not in GEEN_VERTALING:
            t = m.group(2) if taal == "nl" else vertaal(vt, "ui", m.group(2), "teksten_nl.asm:%d" % nr, fouten)
            try:
                codes = [lettertype.code_van(c) for c in t]
            except KeyError as e:
                fouten.append("teksten_nl.asm:%d: teken %s niet in het lettertype" % (nr, e))
                codes = []
            label = re.match(r"^(\s*\w+:)", m.group(1))
            rest = m.group(3).strip().lstrip(";").strip()       # wat achter de tekst stond (bv. ".byte 0")
            r = (label.group(1) if label else "")
            if codes:
                r += "        .byte " + ", ".join("$%02x" % c for c in codes) + "    // " + t.replace("//", "/ /")
            if rest:
                r += "\n        " + rest
        regels.append(r)
    open(os.path.join(uit, "teksten.asm"), "w", encoding="utf-8").write("\n".join(regels) + "\n")
    if fouten:
        print("\n".join(fouten[:40]))
        raise SystemExit("[taal] %s: %d fouten" % (taal, len(fouten)))
    print("[taal] %s: vertaalde kopieën in %s" % (taal, os.path.relpath(uit, WORTEL)))


def controleer(taal):
    sys.path.insert(0, os.path.join(WORTEL, "tools"))
    import lettertype
    bron, vt = json.load(open(os.path.join(TAALMAP, "bron.json"), encoding="utf-8")), laad(taal)
    fouten = 0
    for soort, teksten in bron.items():
        for nl, info in teksten.items():
            t = vt.get(soort, {}).get(nl)
            if t is None:
                print("ontbreekt (%s): %r" % (soort, nl)); fouten += 1; continue
            for c in t:
                try:
                    lettertype.code_van(c)
                except KeyError:
                    print("teken %r niet in het lettertype (%s): %r" % (c, soort, t)); fouten += 1
            if info["max"] and soort == "zeg":
                regels, r = 1, 0
                for w in t.split():
                    r = len(w) if r == 0 else r + 1 + len(w)
                    if r > 40:
                        regels, r = regels + 1, len(w)
                if regels > 2:
                    print("te lang (2 regels van 40): %r" % t); fouten += 1
            elif info["max"] and len(t) > info["max"]:
                print("te lang (%s, max %d): %r" % (soort, info["max"], t)); fouten += 1
    print("[taal] %s: %d fouten" % (taal, fouten))
    return fouten


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["extract"]:
        extract()
    elif a[:1] == ["maak"] and len(a) == 3:
        maak(a[1], a[2])
    elif a[:1] == ["controleer"] and len(a) == 2:
        sys.exit(1 if controleer(a[1]) else 0)
    else:
        raise SystemExit(__doc__)
