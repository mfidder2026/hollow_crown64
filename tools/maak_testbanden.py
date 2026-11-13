#!/usr/bin/env python3
"""maak_testbanden.py — maakt testbanden uit de scripts zelf, zodat nieuwe kamers en voorwerpen vanzelf getest worden.

    python3 tools/maak_testbanden.py      schrijft tests/scripts/proef_kamers.hcs en tests/alle_voorwerpen.band

alle_voorwerpen.band gaat elke kamer langs (een proefscript zet Eldric erin) en wijst elk voorwerp aan dat daar ligt.
Per voorwerp: elk werkwoord met een "veilig" script (alleen praten, kijken, wachten, een vlag zetten: niets wat de
kamer, de inventaris of het plaatje verandert), en anders in elk geval Bekijk. De band controleert de zinregel
("Bekijk kaart": zo blijkt dat het vak op die plek ook echt dat voorwerp is, en niet een buurman die eroverheen ligt)
en dat de VM zonder fout klaar is. Het punt binnen een vak wordt zo gekozen dat het niet in een ander vak valt.
"""
import glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scriptc   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WW_TEKST = {"GA_NAAR": "Ga naar", "PAK": "Pak", "GEBRUIK": "Gebruik", "OPEN": "Open", "BEKIJK": "Bekijk",
            "PRAAT": "Praat met", "GEEF": "Geef", "SLUIT": "Sluit", "DUW": "Duw", "TREK": "Trek", "LEES": "Lees",
            "WAT_IS": "Wat is"}
# de werkwoordenbalk: 3 rijen van 4 (src/balk.asm), schermpixels van het midden van elk woord
WW_PLEK = {ww: (20 + 80 * (i % 4), 156 + 8 * (i // 4)) for i, ww in enumerate(scriptc.WERKWOORDEN)}
VEILIG = {"ZEG", "ALS", "ANDERS", "EINDE", "KIJK", "WACHT", "GELUID", "ZET", "STOP"}


def veilig(script):
    return all(o[0] in VEILIG for o in script)


def punt_in(v, anderen):
    """een punt (kamerpixels) binnen het vak van v, niet in een ander vak, zo dicht mogelijk bij het midden"""
    x1, y1, x2, y2 = v["vak"]                    # (scriptc: x1, y1, x2, y2, randen inbegrepen)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    kandidaten = sorted(((px, py) for px in range(x1 + 1, x2) for py in range(y1 + 1, y2)),
                        key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2)
    for px, py in kandidaten:
        if not any(a[0] - 1 <= px <= a[2] + 1 and a[1] - 1 <= py <= a[3] + 1 for a in anderen):
            return px, py
    return None


def main():
    bestanden = sorted(glob.glob(os.path.join(WORTEL, "scripts", "*.hcs")))
    spel = scriptc.lees(bestanden)
    scriptc.stand_vooraan(spel)                 # dezelfde nummering als het spel: bij overlap wint het laagste nummer
    volgorde = {n: i for i, n in enumerate(spel.vw_volgorde)}
    kamers = [k for k in spel.kamer_volgorde if not spel.kamers[k]["toneel"] and spel.kamers[k]["vakken"]]

    hcs = ["# proef_kamers.hcs — gemaakt door tools/maak_testbanden.py: per kamer een script dat Eldric erin zet.", ""]
    band = ["# alle_voorwerpen.band — gemaakt door tools/maak_testbanden.py (niet met de hand bewerken).",
            "# Elke kamer, elk voorwerp: de zinregel klopt en de veilige scripts lopen zonder fout.", "wacht 3"]
    overgeslagen = []
    for k in kamers:
        x1, y1, x2, y2, _ = spel.kamers[k]["vakken"][0]
        hcs += ["SCRIPT proef_kamer_%s:" % k, "  KAMER %s %d,%d VOOR" % (k, (x1 + x2) // 2, (y1 + y2) // 2), ""]
        band += ["", "# ---- %s ----" % k, "start_script proef_kamer_%s" % k, "wacht_op_script", "wacht 3",
                 "wacht_op_script", "wacht 3", "verwacht_kamer %s" % k]
        hier = sorted((v for v in spel.voorwerpen.values() if v["eigenaar"] == k and v["vak"]),
                      key=lambda v: volgorde[v["naam"]])
        for i, v in enumerate(hier):
            anderen = [a["vak"] for a in hier[:i]]
            p = punt_in(v, anderen)
            if p is None:
                overgeslagen.append("%s (%s): geen vrij punt in het vak" % (v["naam"], k))
                continue
            sx, sy = p[0] * 2, p[1] + 16
            werkwoorden = [ww for ww, s in v["scripts"].items() if veilig(s)] or ["BEKIJK"]
            for ww in werkwoorden:
                wx, wy = WW_PLEK[ww]
                band += ["cursor %d,%d" % (wx, wy), "vuur", "cursor %d,%d" % (sx, sy), "wacht 2",
                         'verwacht_tekst 18 "%s %s"' % (WW_TEKST[ww], v["tekst"]), "vuur", "wacht_tot_stil",
                         "wacht_op_script", "verwacht vm_fout = 0"]
        band.append("screenshot %s" % k)
    with open(os.path.join(WORTEL, "tests", "scripts", "proef_kamers.hcs"), "w") as f:
        f.write("\n".join(hcs) + "\n")
    with open(os.path.join(WORTEL, "tests", "alle_voorwerpen.band"), "w") as f:
        f.write("\n".join(band) + "\n")
    with open(os.path.join(WORTEL, "tests", "alle_voorwerpen.verwacht"), "w") as f:
        f.write("band_status = 2\nband_fout = 0\nvm_fout = 0\nlaad_fout = 0\nscherm = ideaal\n")
    n = sum(1 for r in band if r.startswith("verwacht_tekst"))
    print("[testbanden] %d kamers, %d aanwijzingen; overgeslagen: %s" % (len(kamers), n, "; ".join(overgeslagen) or "geen"))


if __name__ == "__main__":
    main()
