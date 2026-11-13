#!/usr/bin/env python3
"""thema.py — de muziek van Hollow Crown: eigen, originele stukken voor de SID (§9), één per plek.

    python3 tools/thema.py build/gen
        schrijft build/gen/muziek.asm (frequentietabel, akkoorden, de stukken voor src/muziek.asm) en
        build/gen/muziek.json (dezelfde noten als tijdlijn: tools/vicetest.py vergelijkt daarmee de SID, "zonder oren").

Aan de muziek hoor je waar je bent: het thema (titel en verhaal) is episch, het plein vrolijk, de herberg een zachte
speelse wals, de kelder geheimzinnig, de smit stoer met hamerslagen, de bosrand spannend. In een script: MUZIEK naam
(de namen staan in LIEDEREN, in deze volgorde; MUZIEK stil = uit).

Drie stemmen; stem 3 wijkt voor de geluidseffecten van het spel:
  stem 1  melodie        stem 2  bas
  stem 3  "akkoord": het akkoord als arpeggio (elke 2 beelden een toon)   of   "noten": gewone noten
          (een begeleiding, druppels, hamerslagen met ruis)

Notatie: "D5:2" = de D in octaaf 5, 2 tellen; "-:1" = rust; b = mol, # = kruis. Een tel = TEL beelden (per stuk).
Per stuk de klank van elke stem: golfvorm, attack/decay, sustain/release (de sustain bepaalt hoe hard: zachte stukken
hebben een lage sustain), pulsbreedte. Elke stem moet even lang zijn; daarna begint het stuk opnieuw.

Data per stem: paren (noot, beelden): noot 0 = rust, anders het MIDI-nummer; bij "akkoord" het akkoordnummer + 1.
$FF = terug naar het begin. In het laatste beeld van elke noot gaat de gate uit.
"""
import json, os, sys

PAL_CLOCK = 985248
NAMEN = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# akkoorden (drieklanken): gedeeld door alle stukken
AKKOORDEN = {
    "Dm": ["D4", "F4", "A4"], "Bb": ["Bb3", "D4", "F4"], "C": ["C4", "E4", "G4"], "Am": ["A3", "C4", "E4"],
    "Gm": ["G3", "Bb3", "D4"], "A": ["A3", "C#4", "E4"], "F": ["F3", "A3", "C4"],
    "G": ["G3", "B3", "D4"], "D": ["D4", "F#4", "A4"], "Em": ["E4", "G4", "B4"],
    "Bdim": ["B3", "D4", "F4"], "B": ["B3", "D#4", "F#4"],
}
GRONDTOON = {"Dm": "D", "Bb": "Bb", "C": "C", "Am": "A", "Gm": "G", "A": "A", "F": "F", "G": "G", "D": "D",
             "Em": "E", "Bdim": "B", "B": "B"}
KWINT = {"Dm": "A", "Bb": "F", "C": "G", "Am": "E", "Gm": "D", "A": "E", "F": "C", "G": "D", "D": "A", "Em": "B",
         "Bdim": "F", "B": "F#"}


def bas_patroon(schema, patroon, octaaf=2):
    """per akkoord een basfiguur: patroon = [(soort, tellen)], soort g/k/o (grondtoon, kwint, octaaf) of - (rust)"""
    uit = []
    for a in schema:
        g, k = GRONDTOON[a], KWINT[a]
        for soort, t in patroon:
            if soort == "-":
                uit.append("-:%s" % t)
            else:
                noot, o = {"g": (g, octaaf), "k": (k, octaaf), "o": (g, octaaf + 1)}[soort]
                uit.append("%s%d:%s" % (noot, o, t))
    return " ".join(uit)


def akkoord_noten(schema, patroon, octaaf_plus=0):
    """per akkoord akkoordtonen als gewone noten (bv. de 'pah-pah' van een wals): patroon = [(toon 0-2 of -, tellen)]"""
    uit = []
    for a in schema:
        for toon, t in patroon:
            if toon == "-":
                uit.append("-:%s" % t)
            else:
                n = AKKOORDEN[a][toon]
                uit.append("%s%d:%s" % (n[:-1], int(n[-1]) + octaaf_plus, t))
    return " ".join(uit)


# ---- de stukken ---------------------------------------------------------------------------------------------------
# klank: (golf, ad, sr, pulsbreedte)
LIEDEREN = {}

# Het thema (titel, verhaal): D-mineur, episch. 16 maten, 100 slagen per minuut.
_s = ["Dm", "Bb", "C", "Am", "Dm", "Gm", "A", "A", "Bb", "F", "Gm", "Dm", "Bb", "C", "A", "Dm"]
LIEDEREN["thema"] = dict(
    tel=30, stem3="akkoord", schema=_s,
    melodie="""D5:2 F5:1 A5:1 | Bb5:1.5 A5:0.5 G5:1 F5:1 | E5:2 G5:1 E5:1 | A4:3 -:1
               D5:1 E5:1 F5:1 G5:1 | A5:1.5 Bb5:0.5 A5:1 G5:1 | E5:1 F5:0.5 E5:0.5 C#5:2 | A4:4
               F5:2 Bb5:2 | A5:1 G5:1 F5:1 C5:1 | D5:1 G5:1 Bb5:1 A5:1 | F5:3 -:1
               D6:2 C6:1 Bb5:1 | C6:1.5 Bb5:0.5 A5:1 G5:1 | A5:1 G5:0.5 F5:0.5 E5:1 C#5:1 | D5:4""",
    bas=bas_patroon(_s, [("g", 2), ("k", 1), ("o", 1)]),
    klank=[(0x40, 0x29, 0xa9, 0x0800), (0x20, 0x08, 0xa6, 0), (0x40, 0x00, 0x70, 0x0800)])

# Het plein: vrolijk dorpsdeuntje in G-groot, 6/8 (een tel = een achtste), een fluitje (driehoek), licht en luchtig.
_s = ["G", "C", "D", "G", "Em", "C", "D", "G", "C", "G", "Am", "D", "G", "Em", "D", "G"]
LIEDEREN["plein"] = dict(
    tel=9, stem3="akkoord", schema=_s,
    melodie="""D5:2 B4:1 G4:2 B4:1 | C5:2 E5:1 G5:3 | F#5:2 E5:1 D5:2 A4:1 | B4:3 G4:3
               E5:2 G5:1 B5:2 G5:1 | A5:2 G5:1 E5:2 C5:1 | D5:1 E5:1 F#5:1 A5:2 F#5:1 | G5:5 -:1
               E5:3 D5:3 | B4:2 D5:1 G5:3 | C5:2 E5:1 A5:3 | F#5:3 D5:3
               G5:2 B5:1 D6:2 B5:1 | G5:2 E5:1 B4:3 | C5:1 E5:1 G5:1 F#5:2 A5:1 | G5:5 -:1""",
    bas=bas_patroon(_s, [("g", 3), ("k", 3)]),
    klank=[(0x10, 0x09, 0x66, 0), (0x40, 0x06, 0x44, 0x0600), (0x40, 0x00, 0x40, 0x0300)])

# De herberg: een zachte, speelse wals in F-groot (3/4): bas op 1, "pah-pah" op 2 en 3, een driehoek-melodie.
_s = ["F", "C", "Dm", "Bb", "F", "C", "F", "F", "Bb", "F", "Gm", "C", "Am", "Dm", "C", "F"]
LIEDEREN["herberg"] = dict(
    tel=16, stem3="noten", schema=_s,
    melodie="""F5:1 A5:1 C6:1 | E5:2 G5:1 | D5:1 F5:1 A5:1 | Bb5:2 G5:1 | A5:1 G5:1 F5:1 | E5:1 D5:1 C5:1
               F5:1 A5:1 G5:1 | F5:2 -:1
               D6:2 C6:1 | A5:2 F5:1 | Bb5:1 A5:1 G5:1 | E5:2 C5:1 | C6:1 A5:1 E5:1 | F5:1 D5:1 A5:1
               G5:1 Bb5:1 E5:1 | F5:2 -:1""",
    bas=bas_patroon(_s, [("g", 1), ("-", 2)]),
    stem3_noten=akkoord_noten(_s, [("-", 1), (1, 1), (2, 1)]),
    klank=[(0x10, 0x08, 0x58, 0), (0x10, 0x06, 0x30, 0), (0x40, 0x04, 0x00, 0x0400)])

# De kelder: geheimzinnig, A-mineur, langzaam; een lage bas, een paar losse tonen en af en toe een druppel.
_s = ["Am", "F", "Dm", "E", "Am", "Dm", "E", "Am"]
AKKOORDEN["E"] = ["E4", "G#4", "B4"]
GRONDTOON["E"], KWINT["E"] = "E", "B"
LIEDEREN["kelder"] = dict(
    tel=24, stem3="noten", schema=_s,
    melodie="""E5:2 -:1 C5:1 | A4:3 -:1 | D5:1 F5:1 E5:2 | G#4:3 -:1 | A4:1 C5:1 E5:2 | F5:2 D5:2 | B4:2 G#4:2
               A4:3 -:1""",
    bas=bas_patroon(_s, [("g", 4)]),
    stem3_noten="""-:3.5 A6:0.5 | -:4 | -:2 E6:0.5 -:1.5 | -:3.5 B6:0.5 | -:4 | -:1 A6:0.5 -:2.5 | -:4
                   -:3 E6:0.5 -:0.5""",
    klank=[(0x10, 0x2a, 0x6a, 0), (0x10, 0x0a, 0x8a, 0), (0x10, 0x03, 0x00, 0)])

# De smit: stoer en ritmisch, D-dorisch; hamerslagen op het aambeeld (ruis op 1 en 3), een stampende bas.
_s = ["Dm", "Dm", "C", "C", "Bb", "C", "Dm", "Dm"]
LIEDEREN["smit"] = dict(
    tel=20, stem3="noten", schema=_s,
    melodie="""D5:1 F5:1 G5:1 A5:1 | A5:2 G5:1 F5:1 | E5:1 G5:1 C6:2 | G5:3 -:1 | F5:1 G5:1 Bb5:1 D6:1
               C6:2 E5:2 | F5:1 E5:1 D5:1 C5:1 | D5:3 -:1""",
    bas=bas_patroon(_s, [("g", 1), ("k", 1), ("g", 1), ("o", 1)]),
    stem3_noten=" | ".join(["C6:0.5 -:1.5 C6:0.5 -:1.5"] * 8),
    klank=[(0x40, 0x08, 0x88, 0x0800), (0x20, 0x06, 0x66, 0), (0x80, 0x08, 0x00, 0)])

# De bosrand: spannend, E-mineur; een kloppende lage bas, een trillend akkoord en een dreigende, trage melodie.
_s = ["Em", "Em", "C", "Em", "C", "B", "Em", "Em"]
LIEDEREN["bosrand"] = dict(
    tel=12, stem3="akkoord", schema=_s,
    melodie="""-:4 B4:4 | C5:6 -:2 | B4:4 G4:4 | B4:8 | -:4 G4:4 | F#4:6 -:2 | E4:8 | -:8""",
    bas=bas_patroon(_s, [("g", 1)] * 8),
    klank=[(0x20, 0x4a, 0x7a, 0), (0x40, 0x04, 0x20, 0x0400), (0x40, 0x00, 0x30, 0x0200)])

# Het Duisterwoud (bospad, spookbrug): G-mineur, traag en mistig; een fluit die dwaalt, een lage bas, en af en toe
# een uil (hoge tonen op stem 3).
AKKOORDEN["Cm"], AKKOORDEN["Eb"] = ["C4", "Eb4", "G4"], ["Eb4", "G4", "Bb4"]
GRONDTOON["Cm"], KWINT["Cm"], GRONDTOON["Eb"], KWINT["Eb"] = "C", "G", "Eb", "Bb"
_s = ["Gm", "Gm", "Eb", "D", "Gm", "Cm", "D", "D"]
LIEDEREN["woud"] = dict(
    tel=26, stem3="noten", schema=_s,
    melodie="""D5:3 Eb5:1 | D5:2 Bb4:2 | G4:2 Bb4:1 C5:1 | A4:4 | Bb4:1 D5:1 G5:2 | Eb5:2 C5:2
               D5:1 C5:1 Bb4:1 A4:1 | D5:3 -:1""",
    bas=bas_patroon(_s, [("g", 2), ("k", 2)]),
    stem3_noten="""-:3 D6:0.5 -:0.5 | -:4 | -:4 | -:2 D6:0.5 -:0.5 Bb5:1 | -:4 | -:4 | -:3 D6:0.5 -:0.5 | -:4""",
    klank=[(0x10, 0x2a, 0x7a, 0), (0x10, 0x0a, 0x8a, 0), (0x10, 0x03, 0x00, 0)])

# De oever: D-groot in 6/8, rustig en hoopvol; golven in de bas, een trillend akkoord, de zee na het donkere bos.
_s = ["D", "G", "D", "A", "G", "D", "Em", "A"]
LIEDEREN["zee"] = dict(
    tel=12, stem3="akkoord", schema=_s,
    melodie="""A4:3 D5:3 | B4:2 D5:1 G5:3 | F#5:3 E5:2 D5:1 | C#5:6 | B4:2 D5:1 G5:3 | F#5:2 E5:1 D5:3
               E5:2 G5:1 B5:3 | A5:6""",
    bas=bas_patroon(_s, [("g", 3), ("k", 3)]),
    klank=[(0x10, 0x1a, 0x8a, 0), (0x10, 0x0c, 0x6a, 0), (0x40, 0x00, 0x40, 0x0300)])

LIEDNAMEN = list(LIEDEREN)


def midi(naam):
    """'C#4' -> 61 (C4 = 60)."""
    stam, rest = naam[0], naam[1:]
    n = NAMEN[stam]
    while rest and rest[0] in "#b":
        n += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return n + 12 * (int(rest) + 1)


def freq(m):
    hz = 440.0 * 2 ** ((m - 69) / 12)
    return min(0xFFFF, round(hz * 16777216 / PAL_CLOCK))


def lees(tekst, tel, naam):
    uit = []
    for w in tekst.replace("|", " ").split():
        noot, duur = w.split(":")
        beelden = round(float(duur) * tel)
        assert abs(beelden - float(duur) * tel) < 1e-9, "%s: duur %s past niet in hele beelden" % (naam, w)
        uit.append((0 if noot == "-" else midi(noot), beelden))
    # lange noten/rusten in stukken van hooguit 250 beelden (een byte)
    klein = []
    for n, d in uit:
        while d > 250:
            klein.append((n, 250))
            d -= 250
        klein.append((n, d))
    return klein


def maak():
    akk_namen = list(AKKOORDEN)
    stukken = []
    for naam in LIEDNAMEN:
        l = LIEDEREN[naam]
        tel = l["tel"]
        mel, bas = lees(l["melodie"], tel, naam), lees(l["bas"], tel, naam)
        if l["stem3"] == "akkoord":
            maat = sum(d for _, d in bas) // len(l["schema"])
            s3 = [(akk_namen.index(a) + 1, maat) for a in l["schema"]]
        else:
            s3 = lees(l["stem3_noten"], tel, naam)
        stemmen = [mel, bas, s3]
        lengtes = [sum(d for _, d in s) for s in stemmen]
        assert len(set(lengtes)) == 1, "%s: de stemmen zijn niet even lang: %s" % (naam, lengtes)
        for s in stemmen:
            assert all(1 < d < 256 for _, d in s), "%s: een noot van 0, 1 of meer dan 255 beelden" % naam
            assert len(s) * 2 + 1 < 256, "%s: te veel noten in een stem" % naam
        assert all(n < 96 for s in (mel, bas) for n, _ in s), naam
        stukken.append(dict(naam=naam, tel=tel, lengte=lengtes[0], stemmen=stemmen,
                            arp=l["stem3"] == "akkoord", klank=l["klank"]))
    akk = [[midi(n) for n in AKKOORDEN[a]] for a in akk_namen]
    return stukken, akk


def main():
    uitmap = sys.argv[1]
    os.makedirs(uitmap, exist_ok=True)
    stukken, akk = maak()
    L = ["// gemaakt door tools/thema.py — niet met de hand wijzigen. De stukken: %s." % ", ".join(LIEDNAMEN),
         ".const MUZ_STUKKEN = %d" % len(stukken)]
    for i, s in enumerate(stukken):
        L.append(".const LIED_%s = %d    // %d beelden (%.1f s)" % (s["naam"].upper(), i, s["lengte"], s["lengte"] / 50))
    L += [".segment Data",
          "muz_freq_lo: .byte " + ", ".join(str(freq(m) & 255) for m in range(96)),
          "muz_freq_hi: .byte " + ", ".join(str(freq(m) >> 8) for m in range(96)),
          "// akkoorden (stem 3): 3 MIDI-noten per akkoord; nummer 1 = de eerste",
          "muz_akkoord: .byte 0, 0, 0, " + ", ".join(str(n) for a in akk for n in a),
          "// per stuk: per stem (3 achter elkaar) het begin, de golfvorm, attack/decay, sustain/release, pulsbreedte"]
    for veld, f in (("begin_lo", lambda i, v: "<lied%d_stem%d" % (i, v + 1)),
                    ("begin_hi", lambda i, v: ">lied%d_stem%d" % (i, v + 1)),
                    ("golf", lambda i, v: "$%02x" % stukken[i]["klank"][v][0]),
                    ("ad", lambda i, v: "$%02x" % stukken[i]["klank"][v][1]),
                    ("sr", lambda i, v: "$%02x" % stukken[i]["klank"][v][2]),
                    ("pw_hi", lambda i, v: "$%02x" % (stukken[i]["klank"][v][3] >> 8))):
        L.append("lied_%s: .byte %s" % (veld, ", ".join(f(i, v) for i in range(len(stukken)) for v in range(3))))
    L.append("lied_arp: .byte %s    // 1: stem 3 speelt akkoorden als arpeggio" %
             ", ".join("1" if s["arp"] else "0" for s in stukken))
    for i, s in enumerate(stukken):
        for v, stem in enumerate(s["stemmen"]):
            L.append("lied%d_stem%d:    // %s, %s" % (i, v + 1, s["naam"], ["melodie", "bas", "stem 3"][v]))
            for j in range(0, len(stem), 8):
                L.append("        .byte " + ", ".join("%d, %d" % p for p in stem[j:j + 8]))
            L.append("        .byte $ff")
    open(os.path.join(uitmap, "muziek.asm"), "w").write("\n".join(L) + "\n")
    json.dump({"stukken": [{k: s[k] for k in ("naam", "tel", "lengte", "stemmen", "arp")} for s in stukken],
               "akkoorden": akk, "freq": [freq(m) for m in range(96)]},
              open(os.path.join(uitmap, "muziek.json"), "w"))
    print("[thema] %d stukken: %s" % (len(stukken), ", ".join("%s %.0f s" % (s["naam"], s["lengte"] / 50)
                                                              for s in stukken)))


if __name__ == "__main__":
    main()
