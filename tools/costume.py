#!/usr/bin/env python3
"""costume.py — maakt van de tekeningen in tools/sprites_hc.py de costumes voor de motor (§6.5).

    python3 tools/costume.py build/gen      schrijft build/gen/costumes.asm

Een costume = de poses van één karakter, elk 128 bytes (bovenste sprite 64 + onderste sprite 64), in de
volgorde richting * 3 + fase:
    richting 0 voor (loopt naar beneden), 1 rug (naar boven), 2 rechts, 3 links
    fase     0 staan, 1 stap, 2 andere stap
De motor kopieert de pose van het moment naar de sprite-vakken (alleen als hij verandert).

Ook: VOETEN_RIJ, de onderste rij met pixels van de staande pose (daar staat de actor op zijn positie),
en de kleuren. Spreken (mond open) komt met de gesprekken (hoofdstuk 7).
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites_hc as hc   # noqa: E402

RICHTINGEN = ["voor", "rug", "rechts", "links"]
# naam van de pose in sprites_hc.CHARS per (richting, fase)
ELDRIC = {
    ("voor", 0): "eldric_voor", ("voor", 1): "eldric_voor_l", ("voor", 2): "eldric_voor_r",
    ("rug", 0): "eldric_rug", ("rug", 1): "eldric_rug_l", ("rug", 2): "eldric_rug_r",
    ("rechts", 0): "eldric_rechts", ("rechts", 1): "eldric_rechts_1", ("rechts", 2): "eldric_rechts_2",
    ("links", 0): "eldric_links", ("links", 1): "eldric_links_1", ("links", 2): "eldric_links_2",
}


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    tekening = {naam: (rijen, boven, onder) for naam, rijen, boven, onder in hc.CHARS}
    rijen0, kb, ko = tekening["eldric_voor"]
    rijen0 = hc.pad(rijen0)
    voeten = max(i for i, r in enumerate(rijen0) if r.strip("."))
    L = ["// costumes.asm — gemaakt door tools/costume.py uit tools/sprites_hc.py; niet met de hand wijzigen",
         ".const HC_MC1 = %d    // $d025, gedeeld: %s" % (hc.MC1, hc.NAMES[hc.MC1]),
         ".const HC_MC2 = %d    // $d026, gedeeld: %s" % (hc.MC2, hc.NAMES[hc.MC2]),
         ".const VOETEN_RIJ = %d    // onderste rij met pixels (van 0-41)" % voeten,
         ".const ELDRIC_KB = %d    // kleur bovenste sprite: %s" % (kb, hc.NAMES[kb]),
         ".const ELDRIC_KO = %d    // kleur onderste sprite: %s" % (ko, hc.NAMES[ko]),
         ".segment Data",
         "costume_eldric:    // 12 poses x 128 bytes: richting * 3 + fase"]
    for r in RICHTINGEN:
        for f in range(3):
            naam = ELDRIC[(r, f)]
            rijen, b, o = tekening[naam]
            if (b, o) != (kb, ko):
                raise SystemExit("pose %s heeft andere kleuren dan eldric_voor" % naam)
            boven, onder = hc.halves(rijen)
            L.append("        // %s (%s, fase %d)" % (naam, r, f))
            for deel in (boven, onder):
                data = hc.sprite_bytes(deel)
                for i in range(0, 64, 16):
                    L.append("        .byte " + ", ".join("$%02x" % x for x in data[i:i + 16]))
    L.append(".assert \"costume_eldric is 12 x 128 bytes\", * - costume_eldric, 12 * 128")
    os.makedirs(sys.argv[1], exist_ok=True)
    open(os.path.join(sys.argv[1], "costumes.asm"), "w").write("\n".join(L) + "\n")
    print("[costume] eldric: 12 poses, voeten op rij %d" % voeten)


if __name__ == "__main__":
    main()
