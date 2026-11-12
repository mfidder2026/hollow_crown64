#!/usr/bin/env python3
"""thema.py — het thema van Hollow Crown: eigen, originele muziek voor de SID (§9), in D-mineur.

    python3 tools/thema.py build/gen
        schrijft build/gen/muziek.asm (frequentietabel + noten voor src/muziek.asm) en build/gen/muziek.json
        (dezelfde noten als tijdlijn: tools/vicetest.py vergelijkt daarmee de SID-registers, "zonder oren").

Drie stemmen (zo blijft stem 3 vrij voor de geluidseffecten van het spel; een effect onderbreekt alleen het arpeggio):
  stem 1  melodie   (puls, met langzame pulsbreedte-modulatie)
  stem 2  bas       (zaagtand)
  stem 3  akkoorden als arpeggio: elke 2 beelden de volgende toon van het akkoord

Notatie: "D5:2" = de D in octaaf 5, 2 tellen; "-:1" = 1 tel rust; b = mol (Bb), # = kruis (C#).
Een tel = TEL beelden (PAL, 50 per seconde). Elke stem moet even lang zijn; daarna begint alles opnieuw.

Data per stem: paren (noot, beelden). noot 0 = rust, anders het MIDI-nummer; voor stem 3 het akkoordnummer + 1.
$FF = terug naar het begin. In het laatste beeld van elke noot gaat de gate uit (dan begint de volgende opnieuw).
"""
import json, os, sys

TEL = 30                     # beelden per tel: 100 slagen per minuut
PAL_CLOCK = 985248
NAMEN = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# ---- de akkoorden (drieklanken, rond octaaf 3-4) ----
AKKOORDEN = {
    "Dm": ["D4", "F4", "A4"],
    "Bb": ["Bb3", "D4", "F4"],
    "C":  ["C4", "E4", "G4"],
    "Am": ["A3", "C4", "E4"],
    "Gm": ["G3", "Bb3", "D4"],
    "A":  ["A3", "C#4", "E4"],     # A groot: de C# (harmonisch mineur) trekt terug naar D
    "F":  ["F3", "A3", "C4"],
}
# per maat (4 tellen) een akkoord: A-deel en B-deel
SCHEMA = ["Dm", "Bb", "C", "Am", "Dm", "Gm", "A", "A",
          "Bb", "F", "Gm", "Dm", "Bb", "C", "A", "Dm"]

MELODIE = """
    D5:2 F5:1 A5:1 | Bb5:1.5 A5:0.5 G5:1 F5:1 | E5:2 G5:1 E5:1 | A4:3 -:1
    D5:1 E5:1 F5:1 G5:1 | A5:1.5 Bb5:0.5 A5:1 G5:1 | E5:1 F5:0.5 E5:0.5 C#5:2 | A4:4
    F5:2 Bb5:2 | A5:1 G5:1 F5:1 C5:1 | D5:1 G5:1 Bb5:1 A5:1 | F5:3 -:1
    D6:2 C6:1 Bb5:1 | C6:1.5 Bb5:0.5 A5:1 G5:1 | A5:1 G5:0.5 F5:0.5 E5:1 C#5:1 | D5:4
"""
# de bas: per akkoord grondtoon (2 tellen), kwint (1), octaaf (1)
BAS_NOTEN = {"Dm": ("D2", "A2", "D3"), "Bb": ("Bb1", "F2", "Bb2"), "C": ("C2", "G2", "C3"), "Am": ("A1", "E2", "A2"),
             "Gm": ("G1", "D2", "G2"), "A": ("A1", "E2", "A2"), "F": ("F1", "C2", "F2")}


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


def lees(tekst):
    uit = []
    for maat in tekst.replace("\n", "|").split("|"):
        tellen = 0
        for w in maat.split():
            noot, duur = w.split(":")
            beelden = round(float(duur) * TEL)
            assert beelden == float(duur) * TEL, "duur %s past niet in hele beelden" % w
            uit.append((0 if noot == "-" else midi(noot), beelden))
            tellen += float(duur)
        assert tellen in (0, 4), "maat telt %s tellen: %s" % (tellen, maat)
    return uit


def maak():
    melodie = lees(MELODIE)
    bas = []
    for a in SCHEMA:
        g, k, o = BAS_NOTEN[a]
        bas += [(midi(g), 2 * TEL), (midi(k), TEL), (midi(o), TEL)]
    namen = list(AKKOORDEN)
    arp = [(namen.index(a) + 1, 4 * TEL) for a in SCHEMA]
    stemmen = [melodie, bas, arp]
    lengtes = [sum(d for _, d in s) for s in stemmen]
    assert len(set(lengtes)) == 1, "de stemmen zijn niet even lang: %s" % lengtes
    for s in stemmen:
        assert all(1 < d < 256 for _, d in s) and len(s) * 2 + 1 < 256
    akk = [[midi(n) for n in AKKOORDEN[a]] for a in namen]
    return stemmen, akk, lengtes[0]


def main():
    uitmap = sys.argv[1]
    os.makedirs(uitmap, exist_ok=True)
    stemmen, akk, lengte = maak()
    L = ["// gemaakt door tools/thema.py — niet met de hand wijzigen. Het thema: D-mineur, %d beelden (%.1f s)."
         % (lengte, lengte / 50),
         ".const MUZ_TEL = %d" % TEL,
         ".segment Data",
         "muz_freq_lo: .byte " + ", ".join(str(freq(m) & 255) for m in range(96)),
         "muz_freq_hi: .byte " + ", ".join(str(freq(m) >> 8) for m in range(96)),
         "// akkoorden (stem 3): 3 MIDI-noten per akkoord; nummer 1 = de eerste"]
    L.append("muz_akkoord: .byte 0, 0, 0, " + ", ".join(str(n) for a in akk for n in a))
    for i, (naam, s) in enumerate(zip(["melodie", "bas", "arpeggio"], stemmen)):
        assert all(n < 96 for n, _ in s) or i == 2
        L.append("muz_stem%d:    // %s" % (i + 1, naam))
        for j in range(0, len(s), 8):
            L.append("        .byte " + ", ".join("%d, %d" % p for p in s[j:j + 8]))
        L.append("        .byte $ff")
    open(os.path.join(uitmap, "muziek.asm"), "w").write("\n".join(L) + "\n")
    json.dump({"tel": TEL, "lengte": lengte, "stemmen": stemmen, "akkoorden": akk,
               "freq": [freq(m) for m in range(96)]}, open(os.path.join(uitmap, "muziek.json"), "w"))
    print("[thema] D-mineur, 3 stemmen, %d beelden (%.1f s), %d noten" % (
        lengte, lengte / 50, sum(len(s) for s in stemmen)))


if __name__ == "__main__":
    main()
