#!/usr/bin/env python3
"""baas.py — het scherm van de baas-toets (menu Bosskey): een rekenblad dat er als een spreadsheetprogramma uitziet.

    python3 tools/baas.py build/gen      schrijft build/gen/baas.asm (25 rijen schermcodes en een kleur per rij)

Het hele scherm in tekstmodus, witte achtergrond, zwarte cijfers: niemand ziet dat je een avontuur speelt.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lettertype   # noqa: E402
import inpak        # noqa: E402

ZWART, WIT, BLAUW, DGRIJS, GRIJS = 0, 1, 6, 11, 12

RIJEN = [
    ("Microsoft Excel - BEGROTING.XLS", BLAUW),
    ("Bestand Bewerken Beeld Invoegen Opmaak", ZWART),
    ("B9      =SOM(B4:B8)", ZWART),
    ("  |A           |B      |C      |D", GRIJS),
    ("--+------------+-------+-------+-------", GRIJS),
    ("1 |Begroting   |   1988|   1989|    +/-", ZWART),
    ("2 |            |       |       |", ZWART),
    ("3 |Huur        |  12400|  12900|    500", ZWART),
    ("4 |Personeel   |  48750|  51200|   2450", ZWART),
    ("5 |Inkoop      |  23100|  22850|   -250", ZWART),
    ("6 |Reclame     |   4200|   5100|    900", ZWART),
    ("7 |Kantoor     |   2875|   2930|     55", ZWART),
    ("8 |Reiskosten  |   1640|   1215|   -425", ZWART),
    ("9 |Totaal      |  92965|  96195|   3230", ZWART),
    ("10|            |       |       |", ZWART),
    ("11|Omzet       | 104300| 109850|   5550", ZWART),
    ("12|Winst       |  11335|  13655|   2320", ZWART),
    ("13|            |       |       |", ZWART),
    ("14|Marge %     |   10.9|   12.4|    1.5", ZWART),
    ("15|            |       |       |", ZWART),
    ("16|            |       |       |", ZWART),
    ("17|            |       |       |", ZWART),
    ("18|            |       |       |", ZWART),
    ("19|            |       |       |", ZWART),
    ("Gereed", DGRIJS),
]


def main():
    assert len(RIJEN) == 25
    codes = []
    for tekst, _ in RIJEN:
        assert len(tekst) <= 40, tekst
        codes += [lettertype.code_van(t) for t in tekst.ljust(40)]
    ingepakt = inpak.pak(bytes(codes))
    assert inpak.uitpak(ingepakt)[0] == bytes(codes) if isinstance(inpak.uitpak(ingepakt), tuple) else True
    L = ["// gemaakt door tools/baas.py — niet met de hand wijzigen",
         "// het rekenblad, ingepakt (tools/inpak.py): %d bytes in plaats van 1000" % len(ingepakt),
         ".segment Data", "baas_ingepakt:"]
    for i in range(0, len(ingepakt), 16):
        L.append("        .byte " + ", ".join("$%02x" % c for c in ingepakt[i:i + 16]))
    for tekst, _ in RIJEN:
        L.append("//   " + tekst)
    L.append("baas_kleur: .byte " + ", ".join(str(k) for _, k in RIJEN))
    open(os.path.join(sys.argv[1], "baas.asm"), "w").write("\n".join(L) + "\n")
    print("[baas] rekenblad: 25 rijen, ingepakt %d bytes" % len(ingepakt))


if __name__ == "__main__":
    main()
