#!/usr/bin/env python3
"""c64beeld.py — maakt van een gewone afbeelding (van FLUX of waar dan ook) exacte C64-graphics.

Wat eruit komt houdt zich aan de regels van de VIC-II, dus het kan niet anders dan kloppen op een echte C64:

  python3 c64beeld.py bitmap foto.png naam            multicolor bitmap 160x200: per 4x8 pixels 3 kleuren + 1 achtergrond
  python3 c64beeld.py bitmap foto.png naam --hires    hires bitmap 320x200: per 8x8 pixels 2 kleuren
      -> naam.kla (Koala) of naam.hir (bitmap + scherm), naam_toon.asm (programma dat het laat zien), naam_c64.png

  python3 c64beeld.py sprites naam a.png b.png ...            multicolor sprites 12x21 (dubbel brede pixels)
  python3 c64beeld.py sprites naam a.png b.png ... --hires    hires sprites 24x21, één kleur
      -> naam.asm (.byte-data, kleuren, voorbeeld in tekst), naam_toon.asm, naam_c64.png
  python3 c64beeld.py sprites naam a.png ... --kit            hires sprites als SPRITEREGELs voor het bouwpakket
      -> naam.asm om in verhaal.asm onder sprites: te plakken (VLIEGER kan dezelfde vorm twee keer krijgen)

Opties:
  --raster fs|geen   fs (standaard) mengt kleuren met Floyd-Steinberg binnen de kleuren van elk vakje; geen = vlak
  --sterkte 0.5      hoe sterk fs mengt (0-1); hoger = zachtere overgangen maar meer korrel
  --kleur 1.5        verzadiging vooraf: de C64-kleuren zijn fel, een FLUX-plaatje (zeker 's nachts) is dat niet
  --licht 1.0        helderheid vooraf (1.2 = lichter: donkere delen krijgen dan nog kleur)
  --zonder-auto      bitmap: het contrast niet eerst oprekken
  --achter N         sprites: de schermkleur waartegen ze staan (standaard 0, zwart). Pixels die daar het dichtst bij
                     liggen worden doorzichtig, zoals een zwarte rand. --achter geen: alleen de achtergrond van de
                     afbeelding wordt doorzichtig.
  --mc1 N --mc2 N    sprites: de twee gedeelde multicolor-kleuren ($d025/$d026) zelf kiezen, anders gekozen voor alle
                     sprites samen
De afbeelding voor een sprite heeft één effen achtergrondkleur (vraag FLUX om "on a plain solid magenta background");
die wordt vanaf de rand weggehaald.
"""
import argparse, itertools, os, sys
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

# kleuren zoals VICE 3.9 ze laat zien (gemeten, dezelfde als teken.py)
RGB = np.array([(0, 0, 0), (255, 255, 255), (175, 60, 88), (126, 243, 214), (170, 64, 245), (98, 213, 50),
                (44, 61, 236), (255, 255, 70), (183, 99, 30), (119, 83, 0), (238, 123, 149), (98, 98, 98),
                (148, 148, 148), (183, 255, 134), (115, 133, 255), (205, 205, 205)], dtype=np.float32)
NAMEN = ["zwart", "wit", "rood", "cyaan", "paars", "groen", "blauw", "geel", "oranje", "bruin", "roze",
         "donkergrijs", "grijs", "lichtgroen", "lichtblauw", "lichtgrijs"]


def lab(rgb):
    """sRGB (0-255) naar CIE Lab: afstanden daarin lijken op wat het oog ziet"""
    c = np.asarray(rgb, dtype=np.float32) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], dtype=np.float32)
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


PAL = lab(RGB)


def afstanden(beeld_lab):
    """(.., 16): kwadratische afstand van elke pixel tot elke C64-kleur"""
    return ((beeld_lab[..., None, :] - PAL) ** 2).sum(-1)


def kies_vakjes(D, vw, vh, vast, n):
    """Kies per vakje van vw x vh pixels de n kleuren (naast de vaste) die het minst afwijken.
    D: (H, W, 16). Geeft (rijen, kolommen, n) en de totale afwijking."""
    H, W, _ = D.shape
    R, C = H // vh, W // vw
    Dv = D.reshape(R, vh, C, vw, 16).transpose(0, 2, 1, 3, 4).reshape(R * C, vh * vw, 16)
    basis = Dv[:, :, vast].min(-1) if vast else np.full(Dv.shape[:2], np.inf, dtype=np.float32)
    combos = np.array(list(itertools.combinations(range(16), n)))
    beste = np.full(R * C, np.inf, dtype=np.float32)
    keuze = np.zeros((R * C, n), dtype=np.int64)
    for s in range(0, len(combos), 80):
        deel = combos[s:s + 80]
        m = np.broadcast_to(basis[:, :, None], basis.shape + (len(deel),))
        for j in range(n):
            m = np.minimum(m, Dv[:, :, deel[:, j]])
        kosten = m.sum(1)
        i = kosten.argmin(1)
        k = kosten[np.arange(len(i)), i]
        beter = k < beste
        beste[beter] = k[beter]
        keuze[beter] = deel[i[beter]]
    return keuze.reshape(R, C, n), float(beste.sum())


def pixels_kiezen(beeld_lab, kleuren_van, raster, sterkte):
    """Per pixel een C64-kleur uit de toegestane kleuren van zijn vakje; met fs gaat de afwijking naar de buren."""
    H, W, _ = beeld_lab.shape
    uit = np.zeros((H, W), dtype=np.int64)
    werk = beeld_lab.astype(np.float64).copy()
    for y in range(H):
        for x in range(W):
            mag = kleuren_van(y, x)
            v = werk[y, x]
            d = ((PAL[mag] - v) ** 2).sum(-1)
            k = mag[int(d.argmin())]
            uit[y, x] = k
            if raster == "fs":
                fout = (v - PAL[k]) * sterkte
                if x + 1 < W: werk[y, x + 1] += fout * 7 / 16
                if y + 1 < H:
                    if x > 0: werk[y + 1, x - 1] += fout * 3 / 16
                    werk[y + 1, x] += fout * 5 / 16
                    if x + 1 < W: werk[y + 1, x + 1] += fout * 1 / 16
    return uit


def laad(pad):
    return np.asarray(Image.open(pad).convert("RGB"), dtype=np.float32)


def voorbewerk(beeld, kleur=1.5, licht=1.0, auto=True):
    """contrast oprekken (zonder de tint te veranderen), lichter of donkerder, meer verzadiging"""
    img = Image.fromarray(beeld.astype(np.uint8))
    if auto: img = ImageOps.autocontrast(img, cutoff=1, preserve_tone=True)
    if licht != 1: img = ImageEnhance.Brightness(img).enhance(licht)
    if kleur != 1: img = ImageEnhance.Color(img).enhance(kleur)
    return np.asarray(img, dtype=np.float32)


def naar_scherm(beeld, w, h):
    """bijsnijden tot de verhouding van het C64-scherm (320x200) en verkleinen naar w x h C64-pixels"""
    img = Image.fromarray(beeld.astype(np.uint8))
    bw, bh = img.size
    if bw / bh > 1.6:
        nw = int(bh * 1.6); img = img.crop(((bw - nw) // 2, 0, (bw - nw) // 2 + nw, bh))
    else:
        nh = int(bw / 1.6); img = img.crop((0, (bh - nh) // 2, bw, (bh - nh) // 2 + nh))
    return np.asarray(img.resize((w, h), Image.LANCZOS), dtype=np.float32)


# ---------- bitmap ----------

def bitmap_multicolor(beeld, raster, sterkte, achter=None):
    klein = naar_scherm(beeld, 160, 200)
    L = lab(klein)
    D = afstanden(L)
    if achter is None:      # de achtergrondkleur geldt voor het hele scherm: probeer ze alle 16
        beste = None
        for b in range(16):
            keuze, k = kies_vakjes(D, 4, 8, [b], 3)
            if beste is None or k < beste[0]:
                beste = (k, b, keuze)
        _, achter, keuze = beste
    else:
        keuze, _ = kies_vakjes(D, 4, 8, [achter], 3)
    toegestaan = {}
    def kleuren_van(y, x):
        r, c = y // 8, x // 4
        if (r, c) not in toegestaan:
            toegestaan[(r, c)] = np.array([achter] + list(keuze[r, c]))
        return toegestaan[(r, c)]
    pix = pixels_kiezen(L, kleuren_van, raster, sterkte)
    # coderen: 00 = achtergrond $d021, 01 = scherm hoog, 10 = scherm laag, 11 = kleur-RAM
    bitmap = bytearray(8000); scherm = bytearray(1000); kleur = bytearray(1000)
    for r in range(25):
        for c in range(40):
            k1, k2, k3 = (int(v) for v in keuze[r, c])
            scherm[r * 40 + c] = (k1 << 4) | k2
            kleur[r * 40 + c] = k3
            code = {achter: 0, k1: 1, k2: 2, k3: 3} if achter not in (k1, k2, k3) else None
            for y in range(8):
                v = 0
                for x in range(4):
                    p = int(pix[r * 8 + y, c * 4 + x])
                    b = 0 if p == achter else (1 if p == k1 else 2 if p == k2 else 3)
                    v |= b << (6 - 2 * x)
                bitmap[(r * 40 + c) * 8 + y] = v
    return bytes([0x00, 0x60]) + bytes(bitmap) + bytes(scherm) + bytes(kleur) + bytes([achter])


def bitmap_hires(beeld, raster, sterkte):
    klein = naar_scherm(beeld, 320, 200)
    L = lab(klein)
    keuze, _ = kies_vakjes(afstanden(L), 8, 8, [], 2)
    pix = pixels_kiezen(L, lambda y, x: keuze[y // 8, x // 8], raster, sterkte)
    # 1 = scherm hoog (voorgrond), 0 = scherm laag (achtergrond)
    bitmap = bytearray(8000); scherm = bytearray(1000)
    for r in range(25):
        for c in range(40):
            v1, v0 = (int(v) for v in keuze[r, c])
            scherm[r * 40 + c] = (v1 << 4) | v0
            for y in range(8):
                v = 0
                for x in range(8):
                    if int(pix[r * 8 + y, c * 8 + x]) == v1 and v1 != v0:
                        v |= 0x80 >> x
                bitmap[(r * 40 + c) * 8 + y] = v
    return bytes(bitmap) + bytes(scherm)


def lees_koala(data):
    """Zoals de VIC-II het leest: uit de bytes terug naar 320x200 schermpixels (los van de code hierboven)."""
    bm, sc, kl, bg = data[2:8002], data[8002:9002], data[9002:10002], data[10002]
    uit = np.zeros((200, 320), dtype=np.int64)
    for r in range(25):
        for c in range(40):
            kleuren = [bg & 15, sc[r * 40 + c] >> 4, sc[r * 40 + c] & 15, kl[r * 40 + c] & 15]
            for y in range(8):
                b = bm[(r * 40 + c) * 8 + y]
                for x in range(4):
                    k = kleuren[(b >> (6 - 2 * x)) & 3]
                    uit[r * 8 + y, c * 8 + 2 * x] = uit[r * 8 + y, c * 8 + 2 * x + 1] = k
    return uit


def lees_hires(data):
    bm, sc = data[:8000], data[8000:9000]
    uit = np.zeros((200, 320), dtype=np.int64)
    for r in range(25):
        for c in range(40):
            for y in range(8):
                b = bm[(r * 40 + c) * 8 + y]
                for x in range(8):
                    uit[r * 8 + y, c * 8 + x] = sc[r * 40 + c] >> 4 if b & (0x80 >> x) else sc[r * 40 + c] & 15
    return uit


def toon_bitmap_asm(naam, hires):
    if hires:
        laden = f'.var pic = LoadBinary("{naam}.hir", "Bitmap=0, ScreenRam=8000")'
        d016, kleur = "$c8", ""
    else:
        laden = f'.var pic = LoadBinary("{naam}.kla", BF_KOALA)'
        d016 = "$d8"
        kleur = """        lda #pic.getBackgroundColor()
        sta $d021
        ldx #0
!lus:   .for (var i = 0; i < 4; i++) {
            lda kleurRam + i * $100,x
            sta $d800 + i * $100,x
        }
        inx
        bne !lus-
"""
    deel_kleur = "" if hires else """        *=$1c00 "Kleur-RAM"
kleurRam:
        .fill pic.getColorRamSize(), pic.getColorRam(i)
"""
    return f"""// {naam}_toon.asm — laat {naam} zien; gemaakt door c64beeld.py. Bouw: ./build.sh {naam}_toon.asm
{laden}
        BasicUpstart2(begin)
        *=$0810
begin:  sei
        lda #$38
        sta $d018           // bitmap op $2000, scherm op $0c00
        lda #{d016}
        sta $d016
        lda #$3b
        sta $d011           // bitmapmodus
        lda #0
        sta $d020
{kleur}        jmp *

        *=$0c00 "Scherm"
        .fill pic.getScreenRamSize(), pic.getScreenRam(i)
{deel_kleur}        *=$2000 "Bitmap"
        .fill pic.getBitmapSize(), pic.getBitmap(i)
"""


# ---------- sprites ----------

def los_van_achtergrond(beeld):
    """Masker van het figuur. De achtergrond groeit vanaf de rand zolang buurpixels weinig verschillen en de kleur
    in de buurt van de randkleur blijft: zo gaat een zacht verloop mee en stopt hij bij de rand van het figuur.
    Daarna blijven alleen de grote stukken over (losse vlekjes in de achtergrond vallen weg)."""
    L = lab(beeld)
    rand = np.concatenate([L[:3].reshape(-1, 3), L[-3:].reshape(-1, 3), L[:, :3].reshape(-1, 3), L[:, -3:].reshape(-1, 3)])
    d = np.sqrt(((L - np.median(rand, 0)) ** 2).sum(-1))
    lijkt = d < 70
    stap_x = np.sqrt(((L[:, 1:] - L[:, :-1]) ** 2).sum(-1)) < 7     # tussen (y, x) en (y, x+1)
    stap_y = np.sqrt(((L[1:] - L[:-1]) ** 2).sum(-1)) < 7           # tussen (y, x) en (y+1, x)
    achter = np.zeros_like(lijkt)
    achter[0, :] = lijkt[0, :]; achter[-1, :] = lijkt[-1, :]; achter[:, 0] = lijkt[:, 0]; achter[:, -1] = lijkt[:, -1]
    achter &= d < 20
    while True:
        groei = achter.copy()
        groei[1:] |= achter[:-1] & stap_y; groei[:-1] |= achter[1:] & stap_y
        groei[:, 1:] |= achter[:, :-1] & stap_x; groei[:, :-1] |= achter[:, 1:] & stap_x
        groei &= lijkt
        if (groei == achter).all():
            break
        achter = groei
    masker = ~(achter | (d < 12))
    # grote stukken houden: op een raster van 4x4 pixels de samenhangende delen tellen
    H, W = masker.shape
    grof = masker[:H // 4 * 4, :W // 4 * 4].reshape(H // 4, 4, W // 4, 4).mean((1, 3)) > 0.5
    label = np.zeros(grof.shape, dtype=np.int64); maten = [0]
    for y0, x0 in zip(*np.nonzero(grof)):
        if label[y0, x0]:
            continue
        n = len(maten); label[y0, x0] = n; stapel = [(y0, x0)]; maat = 0
        while stapel:
            y, x = stapel.pop(); maat += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < grof.shape[0] and 0 <= xx < grof.shape[1] and grof[yy, xx] and not label[yy, xx]:
                    label[yy, xx] = n; stapel.append((yy, xx))
        maten.append(maat)
    groot = np.array([m >= 0.1 * max(maten) for m in maten]); groot[0] = False
    houd = np.repeat(np.repeat(groot[label], 4, 0), 4, 1)
    uit = np.zeros_like(masker); uit[:houd.shape[0], :houd.shape[1]] = houd
    # de eigen rand van het figuur terug: binnen 1 grof vakje van wat we houden
    rond = uit.copy()
    for dy in (-4, 0, 4):
        for dx in (-4, 0, 4):
            rond |= np.roll(np.roll(uit, dy, 0), dx, 1)
    return masker & rond


def sprite_raster(beeld, breed, kleur, licht, fijn=4):
    """Figuur bijsnijden en in 24x21 passen (hires) of 12x21 dubbel brede pixels (multicolor). Geeft het figuur op
    fijn x zo veel pixels: (21*fijn, breed*fijn) kleuren in Lab en welke pixels bij het figuur horen."""
    masker = los_van_achtergrond(beeld)
    ys, xs = np.nonzero(masker)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    deel = voorbewerk(beeld[y0:y1, x0:x1], kleur, licht, auto=False)
    m = masker[y0:y1, x0:x1]
    h, w = deel.shape[:2]
    schaal = min(24 / w, 21 / h)                       # op het scherm is een sprite 24 x 21 vierkante pixels
    tw, th = max(1, round(w * schaal * breed / 24)), max(1, round(h * schaal))
    # NEAREST: geen mengkleuren, elke fijne pixel is een echte pixel van het figuur
    fd = np.asarray(Image.fromarray(deel.astype(np.uint8)).resize((tw * fijn, th * fijn), Image.NEAREST), dtype=np.float32)
    fm = np.asarray(Image.fromarray(m.astype(np.uint8) * 255).resize((tw * fijn, th * fijn), Image.NEAREST)) > 127
    L = np.zeros((21 * fijn, breed * fijn, 3), dtype=np.float32); vol = np.zeros((21 * fijn, breed * fijn), dtype=bool)
    oy, ox = (21 - th) * fijn, (breed - tw) // 2 * fijn    # onderaan, midden: een figuur staat op de grond
    L[oy:oy + th * fijn, ox:ox + tw * fijn] = lab(fd)
    vol[oy:oy + th * fijn, ox:ox + tw * fijn] = fm
    return L, vol


def stem(codes, fijn, n):
    """per sprite-pixel de code die het vaakst voorkomt onder zijn fijn x fijn pixels"""
    H, W = codes.shape[0] // fijn, codes.shape[1] // fijn
    blok = codes.reshape(H, fijn, W, fijn).transpose(0, 2, 1, 3).reshape(H, W, fijn * fijn)
    tel = np.stack([(blok == c).sum(-1) for c in range(n)], -1)
    return tel.argmax(-1)


def sprites(paden, hires, achter, mc1, mc2, kleur=1.5, licht=1.0):
    breed = 24 if hires else 12
    figuren = []
    for p in paden:
        L, vol = sprite_raster(laad(p), breed, kleur, licht)
        label = "".join(ch if ch.isalnum() else "_" for ch in os.path.splitext(os.path.basename(p))[0])
        if not label[0].isalpha(): label = "s_" + label
        figuren.append((label, afstanden(L), vol))
    leeg = [] if achter is None else [achter]

    def kosten(D, vol, kleuren):
        return float(D[vol][:, kleuren].min(-1).sum()) if vol.any() else 0.0

    if hires:
        # aan is wat duidelijk afsteekt tegen de schermkleur; de kleur is die van het meeste daarvan
        eigen = []
        for _, D, vol in figuren:
            aan = vol & (np.sqrt(D[..., achter]) > 30) if achter is not None else vol
            eigen.append(min(range(16), key=lambda k: kosten(D, aan, [k]) if k != achter else np.inf))
        gedeeld = (None, None)
    else:
        paren = [(mc1, mc2)] if mc1 is not None and mc2 is not None else list(itertools.combinations(range(16), 2))
        beste = None
        for a, b in paren:
            tot, eig = 0.0, []
            for _, D, vol in figuren:
                k = min(range(16), key=lambda k: kosten(D, vol, leeg + [a, b, k]))
                eig.append(k); tot += kosten(D, vol, leeg + [a, b, k])
            if beste is None or tot < beste[0]:
                beste = (tot, (a, b), eig)
        _, gedeeld, eigen = beste
    uit = []
    for (naam, D, vol), k in zip(figuren, eigen):
        if hires:
            fijn = vol & (np.sqrt(D[..., achter]) > 30) if achter is not None else vol
            codes = stem(fijn.astype(np.int64), 4, 2)
        else:
            # 0 = doorzichtig (de schermkleur); 1 = $d025, 2 = eigen kleur ($d027+n), 3 = $d026
            kl = [achter if achter is not None else -1, gedeeld[0], k, gedeeld[1]]
            Dk = np.stack([D[..., c] if c >= 0 else np.full(D.shape[:2], np.inf, dtype=np.float32) for c in kl], -1)
            fijn = np.where(vol, Dk.argmin(-1), 0)
            codes = stem(fijn, 4, 4)
        uit.append((naam, k, codes))
    return gedeeld, uit


def sprite_bytes(codes, hires):
    data = bytearray()
    for y in range(21):
        for b in range(3):
            v = 0
            if hires:
                for i in range(8):
                    if codes[y, b * 8 + i]: v |= 0x80 >> i
            else:
                for i in range(4):
                    v |= int(codes[y, b * 4 + i]) << (6 - 2 * i)
            data.append(v)
    return bytes(data) + b"\x00"


def lees_sprite(data, hires, kleuren, achter):
    """terug van bytes naar 21 x 24 schermpixels, zoals de VIC-II het tekent; -1 = doorzichtig"""
    uit = np.full((21, 24), -1, dtype=np.int64)
    for y in range(21):
        for b in range(3):
            v = data[y * 3 + b]
            for i in range(8 if hires else 4):
                if hires:
                    if v & (0x80 >> i): uit[y, b * 8 + i] = kleuren[1]
                else:
                    c = (v >> (6 - 2 * i)) & 3
                    if c: uit[y, b * 8 + 2 * i] = uit[y, b * 8 + 2 * i + 1] = kleuren[c]
    return uit


def schrijf_sprites(naam, hires, achter, gedeeld, figuren, kit=False):
    regels = [f"// {naam}.asm — gemaakt door c64beeld.py: {'hires 24x21' if hires else 'multicolor 12x21'}, {len(figuren)} sprite(s)"]
    if not hires:
        regels += [f"// multicolor: zet $d01c, en voor ALLE sprites samen $d025 = {gedeeld[0]} ({NAMEN[gedeeld[0]]}), $d026 = {gedeeld[1]} ({NAMEN[gedeeld[1]]})",
                   f".label {naam}_mc1 = {gedeeld[0]}      // $d025, in de tekening '1'",
                   f".label {naam}_mc2 = {gedeeld[1]}      // $d026, in de tekening '3'"]
    if achter is not None:
        regels.append(f"// gemaakt voor schermkleur {achter} ({NAMEN[achter]}): doorzichtige pixels laten die zien")
    regels.append(".align 64")
    if kit:
        regels = [f"// {naam}.asm — gemaakt door c64beeld.py --kit: plak dit in verhaal.asm onder sprites:",
                  "// gebruik: VLIEGER(label, label, KLEUR, rij, snelheid) met de kleur hieronder"]
        for fnaam, k, codes in figuren:
            regels.append(f"// {fnaam}: kleur {NAMEN[k].upper()}")
            for y in range(21):
                rij = "".join("#" if c else "." for c in codes[y])
                regels.append(f'{(fnaam + ":") if y == 0 else "":<8}SPRITEREGEL("{rij}")')
            regels.append("        SPRITE_EINDE()")
        return "\n".join(regels) + "\n"
    for fnaam, k, codes in figuren:
        data = sprite_bytes(codes, hires)
        regels.append(f".label {fnaam}_kleur = {k}      // $d027+n ({NAMEN[k]}), in de tekening {'#' if hires else '2'}")
        regels.append(f"{fnaam}:")
        teken = ".#" if hires else ".123"
        for y in range(21):
            rij = "".join(teken[int(c)] for c in codes[y])
            regels.append(f"        .byte ${data[y*3]:02x}, ${data[y*3+1]:02x}, ${data[y*3+2]:02x}      // {rij}")
        regels.append("        .byte 0")
    return "\n".join(regels) + "\n"


def toon_sprites_asm(naam, hires, gedeeld, figuren, achter):
    n = len(figuren)
    zet = []
    for i, (fnaam, k, _) in enumerate(figuren):
        x = 40 + i * (300 // max(1, n))
        zet += [f"        lda #({fnaam} / 64)", f"        sta $07f8 + {i}", f"        lda #{fnaam}_kleur", f"        sta $d027 + {i}",
                f"        lda #<{x}", f"        sta $d000 + {i} * 2", f"        lda #120", f"        sta $d001 + {i} * 2"]
        if x > 255:
            zet += [f"        lda $d010", f"        ora #{1 << i}", f"        sta $d010"]
    mc = "" if hires else f"""        lda #$ff
        sta $d01c
        lda #{naam}_mc1
        sta $d025
        lda #{naam}_mc2
        sta $d026
"""
    return f"""// {naam}_toon.asm — laat de sprites uit {naam}.asm zien, twee keer zo groot. Bouw: ./build.sh {naam}_toon.asm
        BasicUpstart2(begin)
        *=$0810
begin:  sei
        lda #{achter if achter is not None else 0}
        sta $d020
        sta $d021
        lda #$93
        jsr $ffd2           // scherm leeg
        lda #{(1 << n) - 1}
        sta $d015
        sta $d017
        sta $d01d           // twee keer zo hoog en breed
{mc}""" + "\n".join(zet) + f"""
        jmp *

        *=$2000 "Sprites"
#import "{naam}.asm"
"""


def png_bitmap(pix, bron, pad):
    """links de C64-pixels zoals de bytes ze geven, rechts de bron; drie keer vergroot"""
    c64 = Image.fromarray(RGB[pix].astype(np.uint8)).resize((960, 600), Image.NEAREST)
    b = Image.fromarray(naar_scherm(bron, 320, 200).astype(np.uint8)).resize((960, 600), Image.LANCZOS)
    vel = Image.new("RGB", (1940, 600), (40, 40, 40)); vel.paste(c64, (0, 0)); vel.paste(b, (980, 0)); vel.save(pad)


def png_sprites(beelden, pad, achter):
    vel = Image.new("RGB", (len(beelden) * 216 + 8, 184), tuple(int(v) for v in RGB[achter if achter is not None else 0]))
    for i, pix in enumerate(beelden):
        a = np.where(pix[..., None] >= 0, RGB[np.maximum(pix, 0)], RGB[achter if achter is not None else 0])
        vel.paste(Image.fromarray(a.astype(np.uint8)).resize((192, 168), Image.NEAREST), (8 + i * 216, 8))
    vel.save(pad)


def kleurgetal(s):
    return None if s in (None, "geen") else int(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("soort", choices=["bitmap", "sprites"])
    ap.add_argument("rest", nargs="+")
    ap.add_argument("--hires", action="store_true")
    ap.add_argument("--kit", action="store_true")
    ap.add_argument("--raster", choices=["fs", "geen"], default="fs")
    ap.add_argument("--sterkte", type=float, default=0.5)
    ap.add_argument("--kleur", type=float, default=1.5)
    ap.add_argument("--licht", type=float, default=1.0)
    ap.add_argument("--zonder-auto", action="store_true")
    ap.add_argument("--achter", default=None)
    ap.add_argument("--mc1", type=int); ap.add_argument("--mc2", type=int)
    a = ap.parse_args()
    if a.soort == "bitmap":
        bron, naam = a.rest
        beeld = voorbewerk(laad(bron), a.kleur, a.licht, not a.zonder_auto)
        if a.hires:
            data = bitmap_hires(beeld, a.raster, a.sterkte)
            open(naam + ".hir", "wb").write(data)
            pix = lees_hires(data)
        else:
            data = bitmap_multicolor(beeld, a.raster, a.sterkte, kleurgetal(a.achter))
            open(naam + ".kla", "wb").write(data)
            pix = lees_koala(data)
            print(f"{naam}.kla: achtergrond {data[-1]} ({NAMEN[data[-1]]})")
        open(naam + "_toon.asm", "w").write(toon_bitmap_asm(os.path.basename(naam), a.hires))
        png_bitmap(pix, beeld, naam + "_c64.png")
        print(f"klaar: {naam}{'.hir' if a.hires else '.kla'}, {naam}_toon.asm, {naam}_c64.png (links C64, rechts de bron)")
    else:
        naam, paden = a.rest[0], a.rest[1:]
        if not paden:
            sys.exit("sprites: geef een naam en minstens één afbeelding")
        if len(paden) > 8:
            sys.exit("hooguit 8 sprites tegelijk op een rij")
        achter = 0 if a.achter is None else kleurgetal(a.achter)
        if a.kit:
            a.hires = True
        gedeeld, figuren = sprites(paden, a.hires, achter, a.mc1, a.mc2, a.kleur, a.licht)
        open(naam + ".asm", "w").write(schrijf_sprites(os.path.basename(naam), a.hires, achter, gedeeld, figuren, a.kit))
        if not a.kit:
            open(naam + "_toon.asm", "w").write(toon_sprites_asm(os.path.basename(naam), a.hires, gedeeld, figuren, achter))
        beelden = []
        for _, k, codes in figuren:
            kl = [None, k] if a.hires else [None, gedeeld[0], k, gedeeld[1]]
            beelden.append(lees_sprite(sprite_bytes(codes, a.hires), a.hires, kl, achter))
        png_sprites(beelden, naam + "_c64.png", achter)
        for fnaam, k, _ in figuren:
            print(f"{fnaam}: eigen kleur {k} ({NAMEN[k]})")
        if not a.hires:
            print(f"gedeeld: $d025 = {gedeeld[0]} ({NAMEN[gedeeld[0]]}), $d026 = {gedeeld[1]} ({NAMEN[gedeeld[1]]})")
        print(f"klaar: {naam}.asm{'' if a.kit else ', ' + naam + '_toon.asm'}, {naam}_c64.png")


if __name__ == "__main__":
    main()
