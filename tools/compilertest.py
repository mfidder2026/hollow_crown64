#!/usr/bin/env python3
"""compilertest.py — controleert dat tools/scriptc.py foute scripts weigert (hoofdstuk 4).

    python3 tools/compilertest.py

Elk bestand tests/compiler/<naam>.hcs begint met '# verwacht: <stuk van de foutmelding>'. Het wordt samen met
scripts/*.hcs gecompileerd (dus met het echte spel erbij); de compiler moet weigeren met die melding.
Daarna: de echte scripts zonder fout bestand moeten wél compileren.
"""
import glob, os, shutil, sys, tempfile

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "tools"))
import scriptc   # noqa: E402


def main():
    goed = fout = 0
    with tempfile.TemporaryDirectory() as tmp:
        uit = os.path.join(tmp, "uit")
        try:
            scriptc.compileer([os.path.join(WORTEL, "scripts")], uit)
            print("[compiler] ok   de echte scripts compileren")
            goed += 1
        except scriptc.Fout as e:
            print("[compiler] FOUT de echte scripts compileren niet: %s" % e)
            fout += 1
        for pad in sorted(glob.glob(os.path.join(WORTEL, "tests", "compiler", "*.hcs"))):
            naam = os.path.basename(pad)[:-4]
            verwacht = open(pad, encoding="utf-8").readline().split("verwacht:", 1)[1].strip()
            map_ = os.path.join(tmp, naam)
            os.makedirs(map_)
            for s in glob.glob(os.path.join(WORTEL, "scripts", "*.hcs")):
                shutil.copy(s, map_)
            shutil.copy(pad, os.path.join(map_, "zz_proef.hcs"))
            try:
                scriptc.compileer([map_], uit)
                print("[compiler] FOUT %-26s werd niet geweigerd (verwacht: %s)" % (naam, verwacht))
                fout += 1
            except scriptc.Fout as e:
                if verwacht in str(e):
                    print("[compiler] ok   %-26s %s" % (naam, str(e).split(": ", 1)[-1][:70]))
                    goed += 1
                else:
                    print("[compiler] FOUT %-26s andere melding: %s (verwacht: %s)" % (naam, e, verwacht))
                    fout += 1
    print("[compiler] %d van %d goed" % (goed, goed + fout))
    return 1 if fout else 0


if __name__ == "__main__":
    sys.exit(main())
