#!/usr/bin/env python3
"""flakker_proef.py — laat zien wat de FLAKKER-animaties van een kamer doen, zonder te bouwen.

    python3 tools/flakker_proef.py kamer [kamer ...]   schrijft build/proef/flakker_<kamer>.png

Per FLAKKER-regel in scripts/<kamer>.hcs: het gebied uitvergroot, eerst zoals het is, dan na elke stap (elke kleur uit
de rij wordt de volgende, zoals src/flakker.asm het doet). Eronder: hoeveel pixels van elke kleur uit de rij er in
het gebied staan, zodat je ziet of er per ongeluk ook iets anders mee verkleurt. Gebruikt het plaatje zoals de C64 het
toont (de rechterhelft van build/gen/kamer_<kamer>.png, dus eerst één keer bouwen).
"""
import os, re, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c64beeld as cb   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def kamerbeeld(naam):
    im = Image.open(os.path.join(WORTEL, "build", "gen", "kamer_%s.png" % naam)).convert("RGB")
    rechts = im.crop((im.width - 640, 0, im.width, 256)).resize((160, 128), Image.NEAREST)
    pal = [tuple(int(v) for v in cb.RGB[i]) for i in range(16)]
    idx = [[min(range(16), key=lambda k: sum((a - b) ** 2 for a, b in zip(pal[k], rechts.getpixel((x, y)))))
            for x in range(160)] for y in range(128)]
    return idx, pal


def flakkers(naam):
    uit = []
    for r in open(os.path.join(WORTEL, "scripts", naam + ".hcs"), encoding="utf-8"):
        r = r.split("#", 1)[0].split()
        if r[:1] == ["FLAKKER"]:
            x, y = map(int, r[1].split(","))
            b, h = map(int, r[2].split(","))
            kleuren = []
            for w in r[3:]:
                if w in ("TEMPO", "RUST") or w.isdigit():
                    continue
                kleuren.append(cb.NAMEN.index(w))
            uit.append((x, y, b, h, kleuren, " ".join(r[1:])))
    return uit


def main():
    for naam in sys.argv[1:]:
        idx, pal = kamerbeeld(naam)
        fl = flakkers(naam)
        Z = 6
        rijen = []
        for x, y, b, h, kl, tekst in fl:
            stappen = []
            cur = [row[x:x + b] for row in idx[y:y + h]]
            for s in range(len(kl) + 1):
                stappen.append([r[:] for r in cur])
                cur = [[kl[(kl.index(c) + 1) % len(kl)] if c in kl else c for c in r] for r in cur]
            tel = {cb.NAMEN[k]: sum(r.count(k) for r in stappen[0]) for k in kl}
            rijen.append((tekst, stappen, tel, b, h))
        breed = max([(b * Z + 8) * len(st) for _, st, _, b, _ in rijen] + [640])
        hoog = 128 * 3 + sum(h * Z + 40 for *_, h in rijen) + 10
        out = Image.new("RGB", (breed + 20, hoog), (30, 30, 30))
        d = ImageDraw.Draw(out)
        heel = Image.new("RGB", (160, 128))
        heel.putdata([pal[c] for row in idx for c in row])
        heel = heel.resize((640, 384), Image.NEAREST)
        g = ImageDraw.Draw(heel)
        for x, y, b, h, *_ in fl:
            g.rectangle([x * 4, y * 3, (x + b) * 4 - 1, (y + h) * 3 - 1], outline=(255, 255, 0))
        out.paste(heel, (10, 5))
        oy = 128 * 3 + 15
        for tekst, stappen, tel, b, h in rijen:
            d.text((10, oy), "FLAKKER %s   pixels: %s" % (tekst, tel), fill=(255, 255, 0))
            for i, st in enumerate(stappen):
                im = Image.new("RGB", (b, h))
                im.putdata([pal[c] for row in st for c in row])
                out.paste(im.resize((b * Z, h * Z // 2), Image.NEAREST), (10 + i * (b * Z + 8), oy + 14))
            oy += h * Z // 2 + 40
        os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
        pad = os.path.join(WORTEL, "build", "proef", "flakker_%s.png" % naam)
        out.save(pad)
        print("[flakker] %s: %d gebieden -> %s" % (naam, len(fl), os.path.relpath(pad, WORTEL)))


if __name__ == "__main__":
    main()
