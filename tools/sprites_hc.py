#!/usr/bin/env python3
"""Hollow Crown: de sprites van de karakters, getekend als tekst, en daaruit sprites_hc.asm en sprites_hc.png.

Elk karakter is 2 multicolor-sprites boven elkaar: 12 x 42 pixels (op het scherm 24 x 42).
  .  doorzichtig
  k  zwart          gedeeld door alle sprites ($d025 = HC_MC1)
  s  huid           gedeeld door alle sprites ($d026 = HC_MC2)
  c  eigen kleur    per sprite ($d027+n): de bovenste sprite (regel 0-20) en de onderste (21-41) hebben elk hun eigen kleur
De wolf is 2 sprites naast elkaar (24 x 21).

    python3 tools/sprites_hc.py  schrijft src/sprites_hc.asm en data/sprites_hc.png (voorbeeld, 4x vergroot)
"""
import struct, zlib, os

MC1, MC2 = 0, 10          # zwart, lichtrood (huid)

def mirror(rows):
    return [r[::-1] for r in rows]

def sym(half):            # linkerhelft (6 breed) -> symmetrisch 12 breed
    return [h + h[::-1] for h in half]

def pad(rows, n=42):
    rows = list(rows)
    for r in rows:
        assert len(r) == 12, (len(r), r)
    return rows + ["." * 12] * (n - len(rows))

# ---------------------------------------------------------------- Eldric
# vooraanzicht, linkerhelft (kolom 5 grenst aan het midden); gespiegeld tot 12 breed
E_HEAD = [
    "......",   # 0
    "...kkk",   # 1 haar
    "..kkkk",
    "..kkkk",
    "..kkkk",
    "..kkks",   # 5 pony
    "..ksss",   # 6 voorhoofd
    "..ksks",   # 7 ogen
    "..ksss",
    "..ksss",
    "...kss",   # 10
    "....kk",   # 11 kin
    "....ks",   # 12 hals
]
E_BODY = [
    ".kkkkk",   # 13 schouders
    "kcccck",   # 14 schouderstukken (lichtblauw harnas)
    "kccckc",
    "kccckc",
    "kkkkcc",
    "kcckcc",   # 18 armen
    "kcckcc",
    "kcckkk",   # 20 laatste regel van de bovenste sprite
    "kcckks",   # 21 riem met gesp (onderste sprite: blauw)
    "ksskcc",   # 22 handen
    "ksskcc",
    ".kkkcc",
    "..kccc",
    "..kcck",   # 26 split in de tuniek
    "..kkkk",   # 27 zoom
]
E_LEGS = [
    "...kck",
    "...kck",
    "...kck",
    "...kck",
    "...kck",
    "..kkkk",   # 33 laarzen
    ".kkkkk",
]
def check(rows, w):
    for r in rows:
        assert len(r) == w, (len(r), r)
    return rows
check(E_HEAD + E_BODY + E_LEGS, 6)
def put(rows, pts):
    rows = [list(r) for r in rows]
    for y, x, ch in pts:
        rows[y][x] = ch
    return ["".join(r) for r in rows]
# lopen (voor en achter): één voet opgetild
WALK_FRONT = check([
    "...kckkck...",
    "...kckkck...",
    "..kkkkkck...",
    "...kkkkck...",
    "......kck...",
    "......kkkk..",
    "......kkkkk.",
], 12)
# gevest van het zwaard boven zijn schouder
HILT = [(9, 0, "k"), (10, 0, "k"), (10, 1, "k"), (11, 0, "c"), (11, 1, "k"), (12, 0, "k"), (12, 1, "c"), (12, 2, "k")]
front_a = sym(E_HEAD + E_BODY + E_LEGS)
front_b = front_a[:28] + WALK_FRONT
front_c = front_a[:28] + mirror(WALK_FRONT)

# achteraanzicht: haar tot in de nek, oren, het zwaard schuin over de rug (lichtblauw lemmet tussen zwarte randen)
B_HEAD = check([
    "......",
    "...kkk",
    "..kkkk",
    "..kkkk",
    "..kkkk",
    "..kkkk",
    ".skkkk",   # 6 oor
    ".skkkk",
    "..kkkk",
    "..kkkk",
    "...kkk",
    "....kk",
    "....ks",
], 6)
back_a = sym(B_HEAD + E_BODY + E_LEGS)
pts = [(9, 11, "k"), (10, 11, "k"), (10, 10, "k"), (11, 11, "c"), (11, 10, "k"), (12, 11, "k"), (12, 10, "c"), (12, 9, "k")]
for i, y in enumerate(range(13, 21)):        # lemmet van rechtsboven naar linksonder
    x = 9 - i
    pts += [(y, x + 1, "k"), (y, x, "c"), (y, x - 1, "k")] if x - 1 >= 0 else [(y, x, "c")]
back_a = put(back_a, pts)
back_b = back_a[:28] + WALK_FRONT
back_c = back_a[:28] + mirror(WALK_FRONT)

# zijaanzicht, naar rechts
side_a = check([
    "............",   # 0
    "....kkkk....",
    "...kkkkkk...",
    "..kkkkkkkk..",
    "..kkkkkkkk..",
    "..kkkkkkks..",   # 5
    "..kkkkksssk.",
    "..kkkkssksk.",   # 7 oog
    "..kskkssssk.",   # 8 oor
    "..kkksssssk.",
    "...kksssk...",   # 10
    "....kkkkk...",
    ".....kssk...",   # 12 hals
    "...kkkkkk...",   # 13
    "..kccccccck.",
    "..kcckkkcck.",   # 15 schouderstuk
    "..kcckccck..",
    "..kcckccck..",
    "..kcckccck..",
    "..kccckcck..",
    "..kcccckk...",   # 20
    "..kkkkssk...",   # 21 riem, hand
    "..kcckssk...",
    "..kccckkk...",
    "..kcccccck..",
    "..kcccccck..",
    "..kccccccck.",
    "..kkkkkkkk..",   # 27
    "....kcck....",
    "....kcck....",
    "....kcck....",
    "....kcck....",
    "....kcck....",
    "....kkkkk...",   # 33
    "....kkkkkk..",
], 12)
# gevest achter de schouder
side_b = side_a[:28] + check([
    "...kccck....",
    "...kckkcck..",
    "..kck..kck..",
    "..kck...kck.",
    ".kck....kck.",
    ".kkk....kkkk",
    "kkk......kkk",
], 12)
side_c = side_a[:28] + check([
    "....kcck....",
    "....kcck....",
    "....kcck....",
    "...kckck....",
    "...kckkck...",
    "...kkkkkkk..",
    "..kkk..kkkk.",
], 12)

# ---------------------------------------------------------------- Mira, de blinde heks (lang zwart haar, paarse hoed en blinddoek)
mira = sym(check([
    "......",   # 0
    ".....k",
    "....kc",
    "....kc",
    "...kcc",
    "...kcc",
    "..kccc",
    "kkkkkk",   # 7 rand van de hoed
    ".kkkkk",
    ".kksss",   # 9
    ".kkccc",   # 10 blinddoek
    ".kksss",
    ".kksss",
    ".kkksk",   # 13 mond
    ".kkkkk",
    ".kkkcc",   # 15 omslagdoek
    "kkcccc",
    "kcckcc",
    "kcckcc",
    "kccckc",
    "kssskc",   # 20 handen
    "kksskk",   # 21 jurk (onderste sprite: blauw)
    ".kcccc",
    ".kcccc",
    ".kcccc",
    ".kcckc",
    "kcccck",
    "kcccck",
    "kcccck",
    "kcccck",
    "kcccck",
    "kcccck",
    "kcccck",
    "kkkkkk",
    "..kk..",
], 6))
mira = put(mira, [(y, 11, "k") for y in range(5, 34)] + [(2, 10, "k"), (2, 11, "k"), (3, 10, "k"), (4, 10, "k")])

# ---------------------------------------------------------------- Baron Vex: zwart harnas, rode mantel, sik
vex = sym(check([
    "......",
    "...kkk",
    "..kkkk",
    "..kkkk",
    "..ksss",   # 4 voorhoofd
    "..ksss",
    "..ksks",   # 6 ogen
    "..ksss",
    "..kskk",   # 8 snor
    "...ksk",
    "....kk",   # 10 sik
    "kc.kkk",   # 11 kraag van de mantel
    "kckkkk",
    "kcckcc",
    "kcckcc",
    "kcckck",
    "kcckck",
    "kcckck",
    "kcckck",
    "kcksck",
    "kckssk",   # 20
    "kckkkk",   # 21 (onderste sprite: donkergrijs)
    "kckkcc",
    "kckkcc",
    "kckkcc",
    "kckkcc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    ".kcckk",
    "..kckk",
    "..kkkk",
    ".kkkkk",
], 6))

# ---------------------------------------------------------------- Baron Vex met de Lichte Kroon (verhaalanimatie)
vex_kroon = sym(check([
    "...c.c",   # de Lichte Kroon
    "..cccc",
    "..kkkk",
    "..kkkk",
    "..ksss",   # 4 voorhoofd
    "..ksss",
    "..ksks",   # 6 ogen
    "..ksss",
    "..kskk",   # 8 snor
    "...ksk",
    "....kk",   # 10 sik
    "kc.kkk",   # 11 kraag van de mantel
    "kckkkk",
    "kcckcc",
    "kcckcc",
    "kcckck",
    "kcckck",
    "kcckck",
    "kcckck",
    "kcksck",
    "kckssk",   # 20
    "kckkkk",   # 21 (onderste sprite: donkergrijs)
    "kckkcc",
    "kckkcc",
    "kckkcc",
    "kckkcc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    ".kcckk",
    "..kckk",
    "..kkkk",
    ".kkkkk",
], 6))

# ---------------------------------------------------------------- de Hollow King: holle kroon, gele ogen in een zwart gezicht
king = sym(check([
    "...k.k",
    "..kckc",
    "..kckc",
    "..kccc",
    "..kccc",   # 4 kroon (geel)
    "..kkkk",
    ".kkkkk",
    ".kkcck",   # 7 ogen
    ".kkkkk",
    ".kkkkk",
    "..kkkk",
    ".kkkkk",
    "kkkkkk",
    "kckkkk",
    "kckkkk",
    "kckkkk",
    "kckkkk",
    "kcckkk",
    "kcckkk",
    "kcccck",
    "kccccc",   # 20
    "kccccc",   # 21 mantel (donkergrijs)
    "kccccc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kccckc",
    "kcccck",
    "kcccck",
    "kcccck",
    "kccccc",
    ".kcccc",
    "..kckc",
    "...k.k",
], 6))

# ---------------------------------------------------------------- Bram de smit: breed, rode baard, blote armen, leren schort
bram = sym(check([
    "......",
    "...kkk",   # 1 haar
    "..kccc",
    ".kcccc",
    ".kssss",   # 4 voorhoofd
    ".kssks",   # 5 ogen
    ".kssss",
    ".kcssc",   # 7 de baard begint
    ".kcccc",
    "..kccc",
    "...kcc",   # 10 baardpunt
    ".kkkcc",   # 11 brede schouders
    "kssccc",
    "kssccc",   # 13 blote armen
    "kssccc",
    "ksskcc",
    "ksskcc",
    "ksskcc",
    "kss.kc",
    "kkk.kc",   # 19 vuisten
    "....kc",
    "...kcc",   # 21 het leren schort (onderste sprite: bruin)
    "..kccc",
    "..kccc",
    "..kccc",
    "..kccc",
    "..kccc",
    "..kkkk",
    "...kck",   # 28 benen
    "...kck",
    "...kck",
    "...kck",
    "..kkck",
    ".kkkkk",   # 33 laarzen
], 6))
bram = put(bram, [(20, 9, "k"), (20, 10, "k"), (20, 11, "k"), (21, 9, "k"), (21, 10, "k"), (21, 11, "k"),
                  (22, 10, "k"), (22, 11, "k")])   # de hamerkop onder zijn rechtervuist

# ---------------------------------------------------------------- een maan (verhaalanimatie): een schijf die voor de zon schuift
maan = pad(sym(check([
    "....kk",
    "..kkcc",
    ".kcccc",
    ".kcccc",
    "kccccc",
    "kccccc",
    "kccccc",
    "kccccc",
    ".kcccc",
    ".kcccc",
    "..kkcc",
    "....kk",
], 6)))

# ---------------------------------------------------------------- een Hol (verhaalanimatie): hol, mager, gloeiende ogen
hol = pad(sym(check([
    "......",
    "....kk",
    "...kcc",
    "..kccc",
    ".kcccc",
    ".kcssk",   # 5 de ogen gloeien
    ".kcssk",
    ".kcccc",
    "..kccc",
    "...kcc",
    "..kkcc",
    ".kcccc",   # 11 schouders
    "kccccc",
    "kckccc",
    "kckccc",
    "kckccc",
    "kc.kcc",
    "kc.kcc",
    "k..kcc",
    "...kcc",
    "...kck",
    "...kck",   # 21
    "...kck",
    "...kck",
    "..kkck",
    "..kkkk",
], 6)))

# ---------------------------------------------------------------- spookridder: een harnas zonder iemand erin, vervaagt naar onder
ghost = sym(check([
    "......",
    "....kk",
    "...kcc",
    "..kccc",
    "..kccc",
    "..kckk",   # 5 vizier
    "..kccc",
    "..kckk",
    "..kccc",
    "...kkk",
    ".kkkcc",
    "kccckc",
    "kcckcc",
    "kcckcc",
    "kcckkc",
    "kcckcc",
    "kcckcc",
    ".kkkkk",
    ".kckcc",
    ".kckcc",
    ".kkkkk",   # 20
    "..kccc",   # 21
    "..kccc",
    "..kcck",
    "..kccc",
    "..kcck",
    "...kcc",
    "...kck",
    "...kcc",
    "....kc",
    "....k.",
    "....kc",
    ".....k",
], 6))

# ---------------------------------------------------------------- schaduwwolf: 2 sprites naast elkaar (24 x 21), naar rechts
wolf = check([
    "........................",
    "........................",
    "........................",
    "..................k..k..",
    ".................kck.kck",
    ".................kccccck",
    "......kkkkkkkkkkkcccsckk",   # 6 oog (huidkleur = rood gloeiend)
    "k...kkccccccccccccccccck",
    "kk.kcccccccccccccccckkk.",
    ".kkccccccccccccccccck...",
    "..kcccccccccccccccck....",
    "..kccccccccccccccck.....",
    "...kkcccckkkkkcccck.....",
    "...kcck.kck..kcck.......",
    "...kck..kck..kck........",
    "..kck...kck..kck........",
    "..kck....kck..kck.......",
    ".kkk....kkk..kkk........",
    "........................",
    "........................",
    "........................",
], 24)

# ---------------------------------------------------------------- kleuren en volgorde
# naam, rijen, kleur boven, kleur onder
CHARS = [
    ("eldric_voor",   front_a, 14, 6),
    ("eldric_voor_l", front_b, 14, 6),
    ("eldric_voor_r", front_c, 14, 6),
    ("eldric_rug",    back_a,  14, 6),
    ("eldric_rug_l",  back_b,  14, 6),
    ("eldric_rug_r",  back_c,  14, 6),
    ("eldric_rechts",   side_a, 14, 6),
    ("eldric_rechts_1", side_b, 14, 6),
    ("eldric_rechts_2", side_c, 14, 6),
    ("eldric_links",    mirror(side_a), 14, 6),
    ("eldric_links_1",  mirror(side_b), 14, 6),
    ("eldric_links_2",  mirror(side_c), 14, 6),
    ("mira",  mira,  4, 6),
    ("vex",   vex,   2, 11),
    ("king",  king,  7, 11),
    ("spook", ghost, 15, 12),
    ("maan",  maan,  12, 12),
    ("bram",  bram,  8, 9),          # boven oranje (baard, haar, hemd), onder bruin (schort)
    ("vex_kroon", vex_kroon, 7, 11),      # boven goud (kroon en schouders), onder donkergrijs
    ("hol",   hol,   11, 11),
]

PALETTE = [(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189), (139, 63, 150), (85, 160, 73), (64, 49, 141),
           (191, 206, 114), (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80), (120, 120, 120), (148, 224, 137),
           (120, 105, 196), (159, 159, 159)]
NAMES = ["zwart", "wit", "rood", "cyaan", "paars", "groen", "blauw", "geel", "oranje", "bruin", "lichtrood",
         "donkergrijs", "grijs", "lichtgroen", "lichtblauw", "lichtgrijs"]
CODE = {".": 0, "k": 1, "c": 2, "s": 3}   # %01 = $d025, %10 = $d027+n, %11 = $d026


def sprite_bytes(rows21):
    out = []
    for r in rows21:
        bits = 0
        for ch in r:
            bits = bits << 2 | CODE[ch]
        out += [bits >> 16 & 255, bits >> 8 & 255, bits & 255]
    return out + [0]


def halves(rows):
    rows = pad(rows)
    return rows[:21], rows[21:]


def write_asm(path):
    L = ["// sprites_hc.asm — gemaakt door sprites_hc.py, niet met de hand wijzigen: pas de tekening daar aan.",
         "// Elk karakter = 2 multicolor-sprites boven elkaar: zet de onderste 21 pixels lager (Y + 21), zelfde X.",
         f"// Voor ALLE sprites samen: $d01c = de bits van deze sprites, $d025 = HC_MC1 ({NAMES[MC1]}), $d026 = HC_MC2 ({NAMES[MC2]}).",
         "// Per karakter: <naam>_boven en <naam>_onder (64 bytes elk) en hun kleur <naam>_kb / <naam>_ko voor $d027+n.",
         "// De sprite-pointer is adres / 64: lda #(eldric_voor_boven / 64) & $ff (VIC-bank 0: $0000-$3fff).",
         f".label HC_MC1 = {MC1}",
         f".label HC_MC2 = {MC2}",
         ".align 64",
         "hc_sprites:"]
    for name, rows, top, bottom in CHARS:
        a, b = halves(rows)
        L.append(f".label {name}_kb = {top}      // {NAMES[top]}")
        L.append(f".label {name}_ko = {bottom}      // {NAMES[bottom]}")
        for part, rr in (("boven", a), ("onder", b)):
            data = sprite_bytes(rr)
            L.append(f"{name}_{part}:")
            for i, r in enumerate(rr):
                L.append("        .byte " + ", ".join(f"${v:02x}" for v in data[i * 3:i * 3 + 3]) + "      // " + r)
            L.append("        .byte 0")
    # wolf
    L.append(".label wolf_k = 11      // donkergrijs, beide helften")
    for part, sl in (("links", slice(0, 12)), ("rechts", slice(12, 24))):
        rr = [r[sl] for r in wolf]
        data = sprite_bytes(rr)
        L.append(f"wolf_{part}:")
        for i, r in enumerate(rr):
            L.append("        .byte " + ", ".join(f"${v:02x}" for v in data[i * 3:i * 3 + 3]) + "      // " + r)
        L.append("        .byte 0")
    L.append(".label hc_sprites_eind = *")
    open(path, "w").write("\n".join(L) + "\n")


def png(path, scale=4, bg=(70, 140, 60)):
    # elk karakter in een vak van 14 x 44 multicolor-pixels (een multicolor-pixel is 2 schermpixels breed)
    cells = [(n, pad(r), t, b) for n, r, t, b in CHARS] + [("wolf", wolf, 11, 11)]
    cw, ch = 30, 46
    cols = 8
    W, H = cols * cw, ((len(cells) + cols - 1) // cols) * ch
    img = [[bg] * W for _ in range(H)]
    for i, (n, rows, t, b) in enumerate(cells):
        ox, oy = (i % cols) * cw + 2, (i // cols) * ch + 2
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c == ".":
                    continue
                col = {"k": PALETTE[MC1], "s": PALETTE[MC2], "c": PALETTE[t if y < 21 else b]}[c]
                for dx in range(2):
                    img[oy + y][ox + 2 * x + dx] = col
    raw = b"".join(b"\0" + bytes(v for px in row for _ in range(scale) for v in px) for row in img for _ in range(scale))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W * scale, H * scale, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    # tools/ -> projectmap: de asm gaat naar src/, het controleplaatje naar data/
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    write_asm(os.path.join(root, "src", "sprites_hc.asm"))
    png(os.path.join(root, "data", "sprites_hc.png"))
    print("sprites_hc.asm en sprites_hc.png geschreven:", len(CHARS) * 2 + 2, "sprites,", (len(CHARS) * 2 + 2) * 64, "bytes")
