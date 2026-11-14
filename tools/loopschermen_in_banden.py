#!/usr/bin/env python3
"""loopschermen_in_banden.py — zet de loopschermen (tools/teken_tussen.py) in de testbanden.

    python3 tools/loopschermen_in_banden.py tests/*.band tests/*_stappen.txt

Waar een band van kamer A naar kamer B loopt (een 'verwacht_kamer A', dan een zet met 'vuur', dan 'verwacht_kamer B')
en er nu een loopscherm tussen A en B zit, komen vóór 'verwacht_kamer B' de stappen door dat loopscherm: de uitgang
aanklikken en wachten. Een band die met start_script ergens anders begint, blijft zoals hij is. Twee keer draaien
doet niets extra (de stappen staan er dan al: na 'verwacht_kamer A' komt eerst het loopscherm).
"""
import sys

# (van, naar): de loopschermen ertussen, met de schermplek van de uitgang die je aanklikt (None: een toneel, vanzelf)
LINKS, RECHTS, ACHTER, VOOR = "6,126", "314,126", "160,86", "160,138"
OVERGANGEN = {
    ("plein", "bosrand"): [("dorpsweg", ACHTER)], ("bosrand", "plein"): [("dorpsweg", VOOR)],
    ("jachthut", "oever"): [("beekdal", RECHTS)], ("oever", "jachthut"): [("beekdal", LINKS)],
    ("boot", "eiland"): [("zeerotsen", None), ("klippad", RECHTS)], ("eiland", "boot"): [("klippad", LINKS)],
    ("kloof", "donker"): [("grotgang", RECHTS)],
    ("donker", "zwamgrot"): [("rivier", RECHTS)],
    ("bergpad", "hut"): [("sneeuwveld", RECHTS)], ("hut", "bergpad"): [("sneeuwveld", LINKS)],
    ("hut", "ijsbrug"): [("bergkam", RECHTS)], ("ijsbrug", "hut"): [("bergkam", LINKS)],
    ("kerker", "poort"): [("kerkergang", RECHTS)], ("poort", "kerker"): [("kerkergang", LINKS)],
    ("troonzaal", "dak"): [("wenteltrap", LINKS)],
}


def stappen(schermen):
    uit = []
    for naam, plek in schermen:
        if plek is None:                                     # een toneel: het script gaat vanzelf verder
            uit += ["wacht_op_script", "wacht 3"]
            continue
        uit += ["verwacht_kamer %s                # loopscherm (tools/loopschermen_in_banden.py)" % naam,
                "cursor %s" % plek, "wacht 2", "vuur", "wacht_tot_stil", "wacht_op_script", "wacht 3"]
    return uit


def verwerk(pad):
    regels = open(pad, encoding="utf-8").read().split("\n")
    uit, kamer, bewogen, n = [], None, False, 0
    for r in regels:
        kaal = r.split("#", 1)[0].strip()
        w = kaal.split()
        if w[:1] == ["start_script"] or w[:1] == ["voeg_in"]:
            kamer, bewogen = None, False
        elif w[:1] == ["vuur"]:
            bewogen = True
        elif w[:1] == ["verwacht_kamer"] and len(w) == 2:
            naar = w[1]
            if kamer and bewogen and (kamer, naar) in OVERGANGEN:
                uit += stappen(OVERGANGEN[(kamer, naar)])
                n += 1
            kamer, bewogen = naar, False
        uit.append(r)
    if n:
        open(pad, "w", encoding="utf-8").write("\n".join(uit))
    print("[loopschermen] %s: %d overgangen" % (pad, n))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        verwerk(p)
