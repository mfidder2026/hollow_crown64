#!/usr/bin/env python3
"""flux_patches.py — kleine bewerkingen op de FLUX-kamerplaatjes, en de patches die daaruit volgen.

    python3 tools/flux_patches.py herberg

Een patch moet hetzelfde plaatje zijn met één kleine verandering op precies dezelfde plek. Daarom maken we hem hier
uit het kamerplaatje zelf, met Pillow, in plaats van FLUX een nieuw plaatje te laten maken (dat past nooit precies).

Coördinaten in bronpixels van het FLUX-plaatje (1024 x 640). Een kamerpixel (x, y) is bron (x * 6.4, 115 + y * 3.2)
bij boven=115 (zie docs/FLUX_PROMPT.md).

herberg:  data/flux/herberg_bron.png (zoals FLUX hem maakte) ->
    herberg.png              de kruik (rechts aan de muur) grijs steengoed in plaats van een cyaan fles
    herberg_zonder_kruik.png zonder de kruik: de plankenmuur erachter
    herberg_tafel_weg.png    de tafel (met de rechterkruk) opzij geschoven; waar hij stond ligt de ziensteen
"""
import os, sys
from PIL import Image, ImageDraw

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLUX = os.path.join(WORTEL, "data", "flux")

KRUIK = (898, 205, 946, 266)
MUUR_Y = 145                          # vanaf hier is de muur boven de kruik schoon (onder de donkere rand bij de balk)          # de vierde fles aan de muur (kamer VAK 139,28 8,20)
TAFEL = (348, 398, 572, 460)          # tafelblad en poten
KRUK_R = (572, 421, 626, 472)         # de rechterkruk
OPZIJ = 60                            # zoveel bronpixels schuift de tafel naar rechts (≈ 9 kamerpixels)
VLOER_SCHOON = (640, 900)             # x-bereik met alleen vloerplanken (rechts van de kruk, links van de emmer)
VLOER_RIJEN = (502, 522)              # rijen met alleen vloer over de hele breedte (voor het licht per kolom)
STEEN = (378, 444, 414, 466)          # de ziensteen (kamer VAK 58,103 8,7)


def kruik_grijs(im):
    """Cyaan -> grijs steengoed: de helderheid blijft, de kleur gaat eraf (zwarte lijnen blijven zwart)."""
    px = im.load()
    x1, y1, x2, y2 = KRUIK
    for y in range(y1, y2):
        for x in range(x1, x2):
            r, g, b = px[x, y]
            if b > r + 30 and g > r + 20:                   # cyaan / lichtblauw
                v = (r + g + b) // 3
                px[x, y] = (v, v, min(255, v + 8))
    return im


def zonder_kruik(im):
    """Elke kolom van de kruik krijgt de muur erboven (zelfde kolom: de plankenlijnen lopen door)."""
    x1, y1, x2, y2 = KRUIK
    stuk = im.crop((x1, MUUR_Y, x2, MUUR_Y + y2 - y1))
    im.paste(stuk, (x1, y1))
    return im


def vloerlicht(im, y1, y2):
    """De gemiddelde kleur per kolom van een stuk lege vloer (het vuur maakt de vloer links lichter)."""
    stuk = im.crop((0, y1, im.width, y2)).load()
    uit = []
    for x in range(im.width):
        som = [0, 0, 0]
        for y in range(y2 - y1):
            for c in range(3):
                som[c] += stuk[x, y][c]
        uit.append([max(1, v / (y2 - y1)) for v in som])
    return uit


def verlicht(p, van, naar):
    return tuple(min(255, int(p[c] * naar[c] / van[c])) for c in range(3))


def tafel_weg(im):
    bron = im.copy()
    px, b = im.load(), bron.load()
    licht = vloerlicht(bron, *VLOER_RIJEN)
    # eerst de tafel en de rechterkruk weg: elke rij vol vloer uit het schone stuk (de planken lopen horizontaal),
    # met het licht van de plek zelf
    w = VLOER_SCHOON[1] - VLOER_SCHOON[0]
    for y in range(TAFEL[1], KRUK_R[3]):
        for x in range(TAFEL[0] - 4, KRUK_R[2] + 2):
            xs = VLOER_SCHOON[0] + (x - TAFEL[0]) % w
            px[x, y] = verlicht(b[xs, y], licht[xs], licht[x])
    # dan tafel en kruk een stuk naar rechts, met het licht van hun nieuwe plek
    for vak in (TAFEL, KRUK_R):
        x1, y1, x2, y2 = vak
        for y in range(y1, y2):
            for x in range(x1, x2):
                px[x + OPZIJ, y] = verlicht(b[x, y], licht[x], licht[x + OPZIJ])
    # de ziensteen (kamer VAK 58,103 8,7)


def kruik_grijs(im):
    """Cyaan -> grijs steengoed: de helderheid blijft, de kleur gaat eraf (zwarte lijnen blijven zwart)."""
    px = im.load()
    x1, y1, x2, y2 = KRUIK
    for y in range(y1, y2):
        for x in range(x1, x2):
            r, g, b = px[x, y]
            if b > r + 30 and g > r + 20:                   # cyaan / lichtblauw
                v = (r + g + b) // 3
                px[x, y] = (v, v, min(255, v + 8))
    return im


def zonder_kruik(im):
    """Elke kolom van de kruik krijgt de muur erboven (zelfde kolom: de plankenlijnen lopen door)."""
    x1, y1, x2, y2 = KRUIK
    stuk = im.crop((x1, MUUR_Y, x2, MUUR_Y + y2 - y1))
    im.paste(stuk, (x1, y1))
    return im


def tafel_weg(im):
    bron = im.copy()
    px, b = im.load(), bron.load()
    # eerst de tafel en de rechterkruk weg: elke rij vol vloer uit het schone stuk (de planken lopen horizontaal)
    w = VLOER_SCHOON[1] - VLOER_SCHOON[0]
    for y in range(TAFEL[1], KRUK_R[3]):
        for x in range(TAFEL[0] - 4, KRUK_R[2] + 2):
            px[x, y] = b[VLOER_SCHOON[0] + (x - TAFEL[0]) % w, y]
    # dan tafel en kruk een stuk naar rechts (met hun eigen stukje vloer: dezelfde rijen, dus het past)
    im.paste(bron.crop(TAFEL), (TAFEL[0] + OPZIJ, TAFEL[1]))
    im.paste(bron.crop(KRUK_R), (KRUK_R[0] + OPZIJ, KRUK_R[1]))
    # de ziensteen: een gladde grijze steen met een gat erin en een glimlichtje
    d = ImageDraw.Draw(im)
    x1, y1, x2, y2 = STEEN
    d.ellipse((x1, y1, x2, y2), fill=(150, 150, 160), outline=(0, 0, 0), width=3)
    d.ellipse((x1 + 13, y1 + 7, x1 + 23, y1 + 15), fill=(20, 20, 30), outline=(0, 0, 0))
    d.rectangle((x1 + 6, y1 + 4, x1 + 9, y1 + 6), fill=(240, 240, 255))
    return im


def herberg():
    bron = Image.open(os.path.join(FLUX, "herberg_bron.png")).convert("RGB")
    basis = kruik_grijs(bron.copy())
    basis.save(os.path.join(FLUX, "herberg.png"))
    zonder_kruik(basis.copy()).save(os.path.join(FLUX, "herberg_zonder_kruik.png"))
    tafel_weg(basis.copy()).save(os.path.join(FLUX, "herberg_tafel_weg.png"))
    print("[patches] herberg: herberg.png, herberg_zonder_kruik.png, herberg_tafel_weg.png")


if __name__ == "__main__":
    {"herberg": herberg}[sys.argv[1]]()
