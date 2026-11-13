#!/usr/bin/env python3
"""costume.py — maakt van de tekeningen in tools/sprites_hc.py de costumes voor de motor (§6.5).

    python3 tools/costume.py build/gen      schrijft build/gen/costumes.asm

Een costume = de poses van één karakter, elk 128 bytes (bovenste sprite 64 + onderste sprite 64), in de
volgorde richting * 3 + fase:
    richting 0 voor (loopt naar beneden), 1 rug (naar boven), 2 rechts, 3 links
    fase     0 staan, 1 stap, 2 andere stap
De motor kopieert de pose van het moment naar de sprite-vakken (alleen als hij verandert).

Verkleind (voor diepte, §6.5 uitgebreid): de motor kiest per kamer een maat bij de diepte (y) van de voeten
(SCHAAL in scripts/*.hcs). Hier maken we de maten uit dezelfde tekeningen: de figuur wordt verkleind binnen
hetzelfde sprite-vak, met de voeten op dezelfde rij, zodat het plaatsen niet verandert. Volgorde van de poses:
maat * 12 + richting * 3 + fase (maat 0 = de grootste). Het verkleinen kiest per nieuwe pixel de kleur die
het meeste oppervlak heeft, met voorrang voor omlijning (k) en huid (s): zo blijven gezicht en rand heel.
Wil je een maat met de hand bijwerken, teken hem dan in sprites_hc.py en zet hem in HANDWERK hieronder.

Ook: VOETEN_RIJ, de onderste rij met pixels van de staande pose (daar staat de actor op zijn positie),
en de kleuren. Spreken (mond open) komt met de gesprekken (hoofdstuk 7).
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites_hc as hc   # noqa: E402

RICHTINGEN = ["voor", "rug", "rechts", "links"]
NPCS = [("mira", 0), ("wolf", 1), ("maan", 0), ("hol", 0), ("bram", 0), ("grom", 0), ("tik", 0)]          # (naam, vorm) — zie hieronder
# hoogte van de figuur per maat, in pixelrijen (de grootste = de tekening zelf). Afgemeten aan de deuren van
# het plein: achteraan ~14-16 hoog, de smidse ~20, de herberg ~26 (zie docs/LOGBOEK.md).
MATEN = [None, 26, 20, 14, 10]   # 10: helemaal bovenaan het dorp
GEWICHT = {".": 1.0, "c": 1.0, "k": 1.45, "s": 1.35}
# De kleinste maat is met de hand getekend: zo klein werkt verkleinen niet meer (gezicht en benen verdwijnen).
# 6 breed x 14 hoog; staat in kolom 3-8, voeten op rij 34. Helemaal in de onderste sprite, dus 'c' = blauw.
KLEIN = {
    "voor": [
        "..kk..", ".kkkk.", "kkkkkk", "kssssk", "skssks", ".ssss.", "kcccck",
        "kcccck", "scccсs".replace("с", "c"), ".cccc.", ".kkkk.", ".k..k.", ".k..k.", "kk..kk"],
    "rug": [
        "..kk..", ".kkkk.", "kkkkkk", "kkkkkk", "kkkkkk", ".kkkk.", "kcccck",
        "kcccck", "scccсs".replace("с", "c"), ".cccc.", ".kkkk.", ".k..k.", ".k..k.", "kk..kk"],
    "rechts": [
        ".kkk..", "kkkkk.", "kkkss.", "kksks.", ".ksss.", "..ss..", ".cccc.",
        ".cccc.", ".ccsc.", ".cccc.", ".kkkk.", "..kk..", "..kk..", "..kkk."],
}
KLEIN_BENEN = {          # de laatste 3 rijen per (richting, fase); fase 0 = zoals hierboven
    ("voor", 1): [".k..k.", "kk..k.", "....kk"], ("voor", 2): [".k..k.", ".k..kk", "kk...."],
    ("rug", 1): [".k..k.", "kk..k.", "....kk"], ("rug", 2): [".k..k.", ".k..kk", "kk...."],
    ("rechts", 1): [".k.k..", "k...k.", "k...kk"], ("rechts", 2): ["..k.k.", ".k..k.", ".kk.kk"],
}


# De allerkleinste: 4 breed x 10 hoog, kolom 4-7, voeten op rij 34.
KLEINST = {
    "voor":   [".kk.", "kkkk", "ssss", ".ss.", "cccc", "sccs", "cccc", ".kk.", "k..k", "k..k"],
    "rug":    [".kk.", "kkkk", "kkkk", ".kk.", "cccc", "sccs", "cccc", ".kk.", "k..k", "k..k"],
    "rechts": [".kk.", "kkss", ".kss", "..s.", ".cc.", ".cs.", ".cc.", ".kk.", ".kk.", ".kkk"],
}
KLEINST_BENEN = {        # de laatste 2 rijen per (richting, fase)
    ("voor", 1): ["k..k", "kk.."], ("voor", 2): ["k..k", "..kk"],
    ("rug", 1): ["k..k", "kk.."], ("rug", 2): ["k..k", "..kk"],
    ("rechts", 1): ["k.k.", "k..k"], ("rechts", 2): [".kk.", "kk.."],
}
HANDGETEKEND = {14: (KLEIN, KLEIN_BENEN, 6), 10: (KLEINST, KLEINST_BENEN, 4)}


def klein(richting, fase, hoogte=14):
    tekening, benen, breed = HANDGETEKEND[hoogte]
    spiegel = richting == "links"
    basis = "rechts" if spiegel else richting
    rijen = list(tekening[basis])
    if fase:
        n = len(benen[(basis, fase)])
        rijen[-n:] = benen[(basis, fase)]
    if spiegel:
        rijen = [r[::-1] for r in rijen]
    assert len(rijen) == hoogte and all(len(r) == breed for r in rijen), (richting, fase, hoogte)
    leeg = "." * 12
    links = (12 - breed) // 2
    return [leeg] * (35 - hoogte) + ["." * links + r + "." * (12 - links - breed) for r in rijen] + [leeg] * 7


HANDWERK = {}            # (maat, posenaam) -> 42 rijen van 12, als een verkleinde pose met de hand beter is
# naam van de pose in sprites_hc.CHARS per (richting, fase)
ELDRIC = {
    ("voor", 0): "eldric_voor", ("voor", 1): "eldric_voor_l", ("voor", 2): "eldric_voor_r",
    ("rug", 0): "eldric_rug", ("rug", 1): "eldric_rug_l", ("rug", 2): "eldric_rug_r",
    ("rechts", 0): "eldric_rechts", ("rechts", 1): "eldric_rechts_1", ("rechts", 2): "eldric_rechts_2",
    ("links", 0): "eldric_links", ("links", 1): "eldric_links_1", ("links", 2): "eldric_links_2",
}


def verklein(rijen, hoogte):
    """De figuur (rij 'boven' t/m de voeten) verkleind tot <hoogte> rijen, voeten op dezelfde rij, gecentreerd."""
    rijen = hc.pad(rijen)
    gevuld = [i for i, r in enumerate(rijen) if r.strip(".")]
    boven, voeten = gevuld[0], gevuld[-1]
    H = voeten - boven + 1
    if hoogte is None or hoogte >= H:
        return rijen
    sy = hoogte / H
    # kleine figuren relatief breder (zoals in pixelkunst): bij de helft van de hoogte ~1,25 x zo breed
    w = min(12, max(6, 2 * round(6 * sy * (1 + 0.5 * (1 - sy)))))   # even: symmetrisch rond het midden
    sx = w / 12
    links = (12 - w) // 2
    uit = [["."] * 12 for _ in range(42)]
    N = 6                                    # 6 x 6 meetpunten per nieuwe pixel
    for tj in range(hoogte):
        for ti in range(w):
            telling = {}
            for a in range(N):
                for b in range(N):
                    y = boven + int((tj + (a + .5) / N) / sy)
                    x = int((ti + (b + .5) / N) / sx)
                    ch = rijen[min(y, voeten)][min(x, 11)]
                    telling[ch] = telling.get(ch, 0) + 1
            beste = max(telling, key=lambda ch: telling[ch] * GEWICHT[ch])
            uit[voeten - hoogte + 1 + tj][links + ti] = beste
    return ["".join(r) for r in uit]


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
         ".const MATEN = %d" % len(MATEN),
         "costume_eldric:    // MATEN x 12 poses x 128 bytes: maat * 12 + richting * 3 + fase"]
    voorbeeld = []
    for m, hoogte in enumerate(MATEN):
        for r in RICHTINGEN:
            for f in range(3):
                naam = ELDRIC[(r, f)]
                rijen, b, o = tekening[naam]
                if (b, o) != (kb, ko):
                    raise SystemExit("pose %s heeft andere kleuren dan eldric_voor" % naam)
                if hoogte in HANDGETEKEND:
                    rijen = klein(r, f, hoogte)
                else:
                    rijen = HANDWERK.get((m, naam)) or verklein(rijen, hoogte)
                voorbeeld.append((m, r, f, rijen))
                boven, onder = hc.halves(rijen)
                L.append("        // %s, maat %d (%s, fase %d)" % (naam, m, r, f))
                for deel in (boven, onder):
                    data = hc.sprite_bytes(deel)
                    for i in range(0, 64, 16):
                        L.append("        .byte " + ", ".join("$%02x" % x for x in data[i:i + 16]))
    L.append(".assert \"costume_eldric is MATEN x 12 x 128 bytes\", * - costume_eldric, MATEN * 12 * 128")
    # NPC's (hoofdstuk 7): één pose, 2 sprites (128 bytes). vorm 0 = boven elkaar (de onderste 21 lager),
    # vorm 1 = naast elkaar (de rechter 24 schermpixels verder). voeten = de onderste rij met pixels.
    import json
    info = {}
    for naam, vorm in NPCS:
        if naam == "wolf":
            rijen, kb, ko = hc.wolf, 11, 11
            delen = [[r[:12] for r in rijen], [r[12:] for r in rijen]]
        else:
            rijen, kb, ko = tekening[naam]
            delen = list(hc.halves(rijen))
        rijen_v = delen[0] + delen[1] if vorm == 0 else delen[0]
        voeten_n = max(i for i, r in enumerate(rijen_v) if r.strip("."))
        L.append("npc_%s:    // %s, %s" % (naam, "boven elkaar" if vorm == 0 else "naast elkaar", hc.NAMES[kb]))
        for deel in delen:
            data = hc.sprite_bytes(deel)
            for i in range(0, 64, 16):
                L.append("        .byte " + ", ".join("$%02x" % x for x in data[i:i + 16]))
        info[naam] = {"vorm": vorm, "kb": kb, "ko": ko, "voeten": voeten_n}
    json.dump(info, open(os.path.join(sys.argv[1], "kostuums.json"), "w"), indent=1)
    voorbeeld_png(voorbeeld, kb, ko, os.path.join(sys.argv[1], "costume_maten.png"))
    os.makedirs(sys.argv[1], exist_ok=True)
    open(os.path.join(sys.argv[1], "costumes.asm"), "w").write("\n".join(L) + "\n")
    print("[costume] eldric: %d maten x 12 poses, voeten op rij %d" % (len(MATEN), voeten))


def voorbeeld_png(poses, kb, ko, pad, schaal=4):
    """Controle: per maat (rij) alle 12 poses, in de echte kleuren (boven/onder-sprite)."""
    from PIL import Image
    W, H = 12 * 28, len(MATEN) * 44
    img = Image.new("RGB", (W, H), (70, 140, 60))
    for m, r, f, rijen in poses:
        ox, oy = (RICHTINGEN.index(r) * 3 + f) * 28 + 2, m * 44 + 1
        for y, rij in enumerate(rijen):
            for x, ch in enumerate(rij):
                if ch == ".":
                    continue
                kleur = {"k": hc.PALETTE[hc.MC1], "s": hc.PALETTE[hc.MC2], "c": hc.PALETTE[kb if y < 21 else ko]}[ch]
                img.putpixel((ox + 2 * x, oy + y), kleur)
                img.putpixel((ox + 2 * x + 1, oy + y), kleur)
    img.resize((W * schaal, H * schaal), Image.NEAREST).save(pad)


if __name__ == "__main__":
    main()
