#!/usr/bin/env python3
"""loopkaart.py — waar de voeten mogen staan: de pixels van de kamer in de loopkleuren (groen, geel, ...).

    python3 tools/loopkaart.py plein                 voorstel voor LOOPVAK-regels + build/gen/loopkaart_plein.png
    python3 tools/loopkaart.py plein --toon          alleen het controleplaatje met de vakken uit de scripts

Wordt ook gebruikt door tools/scriptc.py: elk LOOPVAK moet (bijna) helemaal op loopkleuren liggen, anders
stopt de build. Zo kan Eldric niet meer door een huis of door de fontein lopen.

Een loopvak is een rechthoek waar zijn voeten (één punt) mogen staan. Kleine vlekjes in het gras (pollen,
schaduw) mogen: een vak moet voor minstens MIN_DEEL op loopkleuren liggen, en geen rij of kolom van het vak mag
meer dan MAX_GAT pixels op een rij missen.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inpak, kamer, c64beeld   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STANDAARD_KLEUREN = ["groen", "lichtgroen", "geel"]
MIN_DEEL = 0.97
MAX_GAT = 3


def kleurnummers(namen):
    uit = []
    for n in namen:
        if n not in c64beeld.NAMEN:
            raise ValueError("onbekende kleur %r (kies uit: %s)" % (n, ", ".join(c64beeld.NAMEN)))
        uit.append(c64beeld.NAMEN.index(n))
    return uit


def pixels(naam):
    """De kamer zoals de VIC hem toont: 128 x 160 kleurnummers (uit build/gen/kamer_<naam>.bin)."""
    pad = os.path.join(WORTEL, "build", "gen", "kamer_%s.bin" % naam)
    d = open(pad, "rb").read()
    a, i = inpak.uitpak(d)
    b, i = inpak.uitpak(d, i)
    c, i = inpak.uitpak(d, i)
    return kamer.lees_terug(a, b, c)


def masker(naam, kleuren=STANDAARD_KLEUREN, vrij=()):
    """True waar de voeten mogen staan: de loopkleuren, plus de VRIJ-gebieden uit het script."""
    m = np.isin(pixels(naam), kleurnummers(kleuren))
    for x1, y1, x2, y2 in vrij:
        m[y1:y2 + 1, x1:x2 + 1] = True
    return m


def langste_gat(rij):
    beste = n = 0
    for v in rij:
        n = 0 if v else n + 1
        beste = max(beste, n)
    return beste


def controleer_vak(m, x1, y1, x2, y2):
    """None als het vak goed ligt, anders een uitleg."""
    deel = m[y1:y2 + 1, x1:x2 + 1]
    aandeel = deel.mean()
    if aandeel < MIN_DEEL:
        slecht = np.argwhere(~deel)
        y, x = slecht[len(slecht) // 2]
        return "ligt maar voor %d%% op loopkleuren (bijvoorbeeld niet op %d,%d)" % (aandeel * 100, x1 + x, y1 + y)
    for y in range(deel.shape[0]):
        if langste_gat(deel[y]) > MAX_GAT:
            return "rij y=%d heeft een stuk van meer dan %d pixels zonder loopkleur" % (y1 + y, MAX_GAT)
    for x in range(deel.shape[1]):
        if langste_gat(deel[:, x]) > MAX_GAT:
            return "kolom x=%d heeft een stuk van meer dan %d pixels zonder loopkleur" % (x1 + x, MAX_GAT)
    return None


def goed(m, x1, y1, x2, y2):
    return controleer_vak(m, x1, y1, x2, y2) is None


def krimp(m, x1, y1, x2, y2):
    """Maak een vak kleiner tot het goed ligt: steeds de rand eraf met de meeste pixels zonder loopkleur."""
    v = [x1, y1, x2, y2]
    while v[0] <= v[2] and v[1] <= v[3] and not goed(m, *v):
        x1, y1, x2, y2 = v
        slecht = {0: (~m[y1:y2 + 1, x1]).sum(), 1: (~m[y1, x1:x2 + 1]).sum(),
                  2: (~m[y1:y2 + 1, x2]).sum(), 3: (~m[y2, x1:x2 + 1]).sum()}
        kant = max(slecht, key=lambda k: slecht[k])
        v[kant] += 1 if kant < 2 else -1
    return v if v[0] <= v[2] and v[1] <= v[3] else None


def voorstel(m, max_vakken=16, min_breed=3, min_hoog=3):
    """Gulzig: steeds het grootste goede vak dat nog veel onbedekt loopgebied pakt; daarna groeien tot overlap."""
    H, W = m.shape
    bedekt = np.zeros_like(m)
    vakken = []
    while len(vakken) < max_vakken:
        beste = None
        for y1 in range(0, H, 2):
            for x1 in range(0, W, 2):
                if not m[y1, x1] or bedekt[y1, x1]:
                    continue
                # vergroot naar rechts en naar onder zolang het goed blijft
                x2 = x1
                while x2 + 1 < W and goed(m, x1, y1, x2 + 1, y1):
                    x2 += 1
                y2 = y1
                while y2 + 1 < H and goed(m, x1, y1, x2, y2 + 1):
                    y2 += 1
                if x2 - x1 + 1 < min_breed or y2 - y1 + 1 < min_hoog:
                    continue
                nieuw = int((~bedekt[y1:y2 + 1, x1:x2 + 1] & m[y1:y2 + 1, x1:x2 + 1]).sum())
                if beste is None or nieuw > beste[0]:
                    beste = (nieuw, x1, y1, x2, y2)
        if beste is None or beste[0] < 40:
            break
        _, x1, y1, x2, y2 = beste
        vakken.append([x1, y1, x2, y2])
        bedekt[y1:y2 + 1, x1:x2 + 1] = True
    # groeien: elke kant 1 pixel zolang het goed blijft, zodat buren overlappen
    for v in vakken:
        for _ in range(2):
            for kant in range(4):
                p = list(v)
                p[kant] += -1 if kant < 2 else 1
                if 0 <= p[0] and 0 <= p[1] and p[2] < W and p[3] < H and goed(m, *p):
                    v[:] = p
    return vakken


def plaatje(naam, m, vakken, pad, schaal=4):
    from PIL import Image, ImageDraw
    pix = pixels(naam)
    img = Image.fromarray(c64beeld.RGB[pix].astype(np.uint8)).resize((160 * schaal, 128 * schaal), Image.NEAREST)
    donker = Image.new("RGB", img.size, (0, 0, 0))
    grijs = Image.fromarray(((~m) * 255).astype(np.uint8)).resize(img.size, Image.NEAREST)
    img = Image.composite(Image.blend(img, donker, 0.6), img, grijs)
    d = ImageDraw.Draw(img)
    for i, (x1, y1, x2, y2) in enumerate(vakken):
        d.rectangle([x1 * schaal, y1 * schaal, (x2 + 1) * schaal - 1, (y2 + 1) * schaal - 1], outline=(255, 0, 255))
        d.text((x1 * schaal + 2, y1 * schaal + 1), str(i), fill=(255, 255, 255))
    img.save(pad)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    naam = sys.argv[1]
    m = masker(naam)
    pad = os.path.join(WORTEL, "build", "gen", "loopkaart_%s.png" % naam)
    if "--toon" in sys.argv:
        import scriptc
        kamers, _, _ = scriptc.lees(sorted(__import__("glob").glob(os.path.join(WORTEL, "scripts", "*.hcs"))))
        vakken = [list(v[:4]) for v in kamers[naam]["vakken"]]
        m = masker(naam, vrij=kamers[naam]["vrij"])
    else:
        vakken = voorstel(m)
        for i, (x1, y1, x2, y2) in enumerate(vakken):
            print("  LOOPVAK %d,%d %d,%d      # %d" % (x1, y1, x2, y2, i))
    plaatje(naam, m, vakken, pad)
    print("controle:", os.path.relpath(pad, WORTEL))


if __name__ == "__main__":
    main()
