#!/usr/bin/env python3
"""teken_taalmenu.py — het taalmenu van de cartridge: een aardmannetje voor zijn hol, een spreekballon en vier vlaggen.

    python3 tools/teken_taalmenu.py <uitmap>    schrijft <uitmap>/taalmenu_data.asm (voor src/taalmenu.asm)
                                                 en build/proef/taalmenu.png (zo ziet het eruit)

Een multicolor bitmap van 160 x 200, met de hand getekend (geen FLUX), in de stijl van de rest van het spel: textuur,
licht, een nachtlucht met de zon en de twee manen. De achtergrond ($d021) is zwart: zwarte pixels zijn code %00.

Wat src/taalmenu.asm ervan nodig heeft:
  - de bitmap, het scherm-RAM en het kleur-RAM;
  - "effecten": per effect de plekken (scherm-RAM hoog/laag nibble, of kleur-RAM) waar één kleur zit, zodat het menu die
    kleur kan veranderen: de ogen (knipperen), de mond (praten), de rand om elke vlag (oplichten);
  - een klein lettertype (3 x 5, dubbel hoog) en de zinnen van het aardmannetje, per taal;
  - waar de ogen staan (voor de pupillen, een sprite) en waar de vlaggen staan (aanwijzen met de muis).
"""
import os, random, sys, math

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c64beeld as cb   # noqa: E402

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B, H = 160, 200
(ZWART, WIT, ROOD, CYAAN, PAARS, GROEN, BLAUW, GEEL, ORANJE, BRUIN, ROZE, DGRIJS, GRIJS, LGROEN, LBLAUW,
 LGRIJS) = range(16)

# ---- het lettertype: 3 breed, 5 hoog (op het scherm dubbel hoog: 10 rijen), alleen hoofdletters ----------------------
FONT = {
    " ": ["...", "...", "...", "...", "..."],
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"], "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"], "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#.#", "###", "###", "#.#", "#.#"], "N": ["##.", "#.#", "#.#", "#.#", "#.#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."], "P": ["##.", "#.#", "##.", "#..", "#.."],
    "Q": [".#.", "#.#", "#.#", "##.", ".##"], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"], "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#.#", "#.#", "###", "###", "#.#"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], "Z": ["###", "..#", ".#.", "#..", "###"],
    "Ä": ["#.#", ".#.", "#.#", "###", "#.#"], "Ç": [".##", "#..", "#..", ".##", ".#."],
    "!": [".#.", ".#.", ".#.", "...", ".#."], "?": ["##.", "..#", ".#.", "...", ".#."],
    "'": [".#.", ".#.", "...", "...", "..."], ",": ["...", "...", "...", ".#.", "#.."],
    ".": ["...", "...", "...", "...", ".#."], "-": ["...", "...", "###", "...", "..."],
    "1": [".#.", "##.", ".#.", ".#.", "###"], "2": ["##.", "..#", ".#.", "#..", "###"],
    "3": ["##.", "..#", ".#.", "..#", "##."], "4": ["#.#", "#.#", "###", "..#", "..#"],
}
TEKENS = list(FONT)

# ---- wat het aardmannetje zegt (2 regels van hooguit 26 tekens) ---------------------------------------------------------
# per taal (nl, en, de, fr): wachten (hij vraagt het om de beurt in elke taal), aanwijzen (die vlag), gekozen
ZINNEN = {
    "wacht": [("HOI! WELKE TAAL", "SPREEK JIJ?"),
              ("HELLO! WHAT DO YOU", "SPEAK, HUMAN?"),
              ("HALLO! WELCHE SPRACHE", "SPRICHST DU, MENSCH?"),
              ("SALUT ! QUELLE LANGUE", "PARLES-TU, HUMAIN ?")],
    "wijs": [("NEDERLANDS?", "PRIMA KEUZE!"),
             ("ENGLISH?", "JOLLY GOOD!"),
             ("DEUTSCH?", "WUNDERBAR!"),
             ("FRANÇAIS ?", "MAGNIFIQUE !")],
    "kies": [("GOED ZO!", "DAAR GAAN WE!"),
             ("SPLENDID!", "OFF WE GO!"),
             ("SEHR GUT!", "LOS GEHT'S!"),
             ("TRÈS BIEN !", "C'EST PARTI !")],
}
FONT["È"] = ["#..", ".#.", "###", "##.", "###"]
TEKENS = list(FONT)

TEKST_X1, TEKST_X2 = 13, 38          # het tekstvak in de ballon: vakjes 13-38 (26 tekens), pixelrijen 32-55
TEKST_Y1, TEKST_Y2 = 32, 55
REGEL_Y = (33, 46)                   # de twee regels (elk 10 rijen hoog)

VLAG_X = (13, 20, 27, 34)            # vakjes; elke vlag 6 vakjes breed (24 mc-pixels), 4 vakjes hoog (32 rijen)
VLAG_Y = 104
VLAG_B, VLAG_H = 24, 32

OGEN = ((19, 133), (27, 133))        # de middens van de ogen (mc-pixels, rijen)
MOND = (20, 146, 26, 148)            # x1, y1, x2, y2


PIJL = [                             # de muispijl: de punt is linksboven (0, 0)
    "#.........",
    "##........",
    "#.#.......",
    "#..#......",
    "#...#.....",
    "#....#....",
    "#.....#...",
    "#......#..",
    "#.......#.",
    "#....#####",
    "#..#.#....",
    "#.#..#....",
    "##....#...",
    "#.....#...",
    ".......#..",
    ".......#..",
]
PIJL = [r.replace(".", "o") if False else r for r in PIJL]
# de pijl wordt gevuld: alles binnen de omtrek is ook wit
_gevuld = []
for _r in PIJL:
    _i = [i for i, t in enumerate(_r) if t == "#"]
    _gevuld.append("".join("#" if _i and min(_i) <= i <= max(_i) else "." for i in range(len(_r))))
PIJL = _gevuld


class Doek:
    def __init__(self):
        self.p = [[ZWART] * B for _ in range(H)]

    def px(self, x, y, k):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < B and 0 <= y < H:
            self.p[y][x] = k

    def get(self, x, y):
        return self.p[y][x] if 0 <= x < B and 0 <= y < H else None

    def rect(self, x1, y1, x2, y2, k):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.px(x, y, k)

    def ovaal(self, x1, y1, x2, y2, vul, rand=None):
        cx, cy, rx, ry = (x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1) / 2 + 0.5, (y2 - y1) / 2 + 0.5
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1:
                    self.px(x, y, rand if rand is not None and d > 0.72 else vul)

    def poly(self, pts, vul):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(math.ceil(a)), int(math.floor(b)) + 1):
                    self.px(x, y, vul)

    def lijn(self, pts, k):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            n = int(max(abs(x2 - x1), abs(y2 - y1))) or 1
            for i in range(n + 1):
                self.px(x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n, k)

    def tekst(self, x, y, s, k):
        """x in vakjes (elk teken 1 vakje: 3 pixels + 1 tussenruimte), y in rijen; dubbel hoog"""
        for i, c in enumerate(s):
            for r, regel in enumerate(FONT[c]):
                for j, t in enumerate(regel):
                    if t == "#":
                        self.px((x + i) * 4 + j, y + 2 * r, k)
                        self.px((x + i) * 4 + j, y + 2 * r + 1, k)


def lucht(dk, rnd):
    # nacht: van boven diep blauw (om en om) naar zwart; sterren
    for y in range(0, 96):
        for x in range(B):
            t = y / 96
            if t < 0.35:
                k = BLAUW if (x + y) % 2 == 0 or rnd.random() < 0.5 - t else ZWART
            elif t < 0.7:
                k = BLAUW if (x + y) % 4 == 0 and rnd.random() < 0.8 - t else ZWART
            else:
                k = ZWART
            dk.px(x, y, k)
    for _ in range(70):
        x, y = rnd.randrange(B), rnd.randrange(96)
        if ((x - 22) / 24) ** 2 + ((y - 40) / 22) ** 2 > 1:
            dk.px(x, y, WIT if rnd.random() < 0.4 else LGRIJS)
    # de zon met de twee manen ervoor (zoals overal in het spel), linksboven
    zx, zy = 22, 40
    for y in range(zy - 20, zy + 20):                            # rond de zon geen blauw (te veel kleuren per vakje)
        for x in range(zx - 22, zx + 24):
            if dk.get(x, y) == BLAUW and ((x - zx) / 22) ** 2 + ((y - zy) / 20) ** 2 < 1:
                dk.px(x, y, ZWART)
    for a in range(0, 360, 15):
        r = math.radians(a)
        for d in (13, 15):
            if rnd.random() < 0.7:
                dk.px(zx + d * math.cos(r), zy + d * math.sin(r) * 0.9, ORANJE if d == 15 else GEEL)
    dk.ovaal(zx - 11, zy - 10, zx + 11, zy + 10, GEEL)
    dk.ovaal(zx - 9, zy - 8, zx + 9, zy + 8, ORANJE)
    dk.ovaal(zx - 8, zy - 6, zx, zy + 6, DGRIJS)
    dk.ovaal(zx, zy - 6, zx + 8, zy + 6, DGRIJS)


def heuvels(dk, rnd):
    # bergen in de verte (donkerblauw) en de heuvel waar alles op staat
    for x in range(B):
        top = 92 + int(8 * math.sin(x * 0.07) + 4 * math.sin(x * 0.19))
        for y in range(top, 104):
            dk.px(x, y, BLAUW if (x + y) % 2 or y > top + 3 else ZWART)
    for x in range(B):
        top = 150 + int(5 * math.sin(x * 0.05 + 1) + 2 * math.sin(x * 0.23))
        for y in range(top, H):
            t = (y - top) / max(1, H - top)
            k = GROEN if rnd.random() > t * 0.9 else (ZWART if (x + y) % 2 else GROEN)
            dk.px(x, y, k)
        dk.px(x, top, LGROEN)
        if rnd.random() < 0.3:
            dk.px(x, top - 1, LGROEN)
    for _ in range(90):                                         # sprietjes en bloempjes
        x, y = rnd.randrange(B), rnd.randrange(156, H)
        dk.px(x, y, LGROEN if rnd.random() < 0.8 else GEEL)


def hol(dk, rnd):
    # het hol van het aardmannetje: een donkere opening in een bult aarde, met wortels
    dk.ovaal(0, 100, 43, 196, DGRIJS)
    for y in range(100, 197):
        for x in range(0, 47):
            if dk.get(x, y) == DGRIJS and rnd.random() < 0.3:
                dk.px(x, y, ZWART)
    dk.ovaal(3, 108, 40, 192, ZWART)
    dk.lijn([(4, 112), (10, 120), (8, 128)], ZWART)
    dk.lijn([(40, 110), (37, 118), (41, 124)], ZWART)
    for x in range(0, 46, 3):                                    # gras over de rand
        dk.px(x, 103 + (x * 7) % 3, LGROEN)
        dk.px(x + 1, 104, GROEN)


def aardmannetje(dk, rnd):
    """een vriendelijk aardmannetje: rond, aardebruin, grote gloeiende ogen, een dikke neus, puntoren, een plukje mos"""
    cx = 23
    # lijf (een bolletje) en voetjes
    dk.ovaal(cx - 13, 150, cx + 13, 184, BRUIN)
    for y in range(150, 185):
        for x in range(cx - 13, cx + 14):
            if dk.get(x, y) == BRUIN:
                if x < cx - 8 and (x + y) % 2 == 0:
                    dk.px(x, y, ZWART)                           # schaduw links (het licht komt van rechts)
                elif x > cx + 6 and (x + y) % 3 == 0 and y < 176:
                    dk.px(x, y, ORANJE)
    dk.ovaal(cx - 11, 182, cx - 3, 188, BRUIN, ZWART)
    dk.ovaal(cx + 3, 182, cx + 11, 188, BRUIN, ZWART)
    # een buikje met een lapje
    dk.ovaal(cx - 5, 162, cx + 5, 172, ORANJE)
    dk.lijn([(cx - 2, 164), (cx + 2, 168)], BRUIN)
    # arm rechts: zwaait naar de ballon
    dk.lijn([(cx + 11, 158), (cx + 18, 150), (cx + 22, 140)], BRUIN)
    dk.lijn([(cx + 12, 159), (cx + 19, 151), (cx + 23, 141)], BRUIN)
    dk.ovaal(cx + 20, 134, cx + 26, 141, ORANJE)
    for i in range(3):
        dk.px(cx + 20 + 2 * i, 133, ORANJE)
    # arm links: op de heup
    dk.lijn([(cx - 12, 158), (cx - 16, 166), (cx - 12, 172)], BRUIN)
    # hoofd: groot en rond
    dk.ovaal(cx - 14, 118, cx + 14, 152, BRUIN)
    for y in range(118, 153):
        for x in range(cx - 14, cx + 15):
            if dk.get(x, y) == BRUIN and x < cx - 10 and (x + y) % 2 == 0:
                dk.px(x, y, ZWART)
            elif dk.get(x, y) == BRUIN and x > cx + 7 and (x + y) % 3 == 0:
                dk.px(x, y, ORANJE)
    # puntoren
    dk.poly([(cx - 13, 128), (cx - 22, 118), (cx - 12, 134)], BRUIN)
    dk.poly([(cx + 13, 128), (cx + 22, 118), (cx + 12, 134)], BRUIN)
    dk.px(cx - 19, 120, ORANJE)
    dk.px(cx + 19, 120, ORANJE)
    # een plukje mos op het hoofd
    for i, (dx, dy) in enumerate(((-3, 117), (-1, 115), (1, 116), (3, 114), (5, 117), (0, 113))):
        dk.px(cx + dx, dy, LGROEN if i % 2 else GROEN)
        dk.px(cx + dx, dy + 1, GROEN)
    # ogen: groot, geel en gloeiend (de pupillen zijn een sprite: ze kijken naar de cursor)
    for ox, oy in OGEN:
        dk.ovaal(ox - 3, oy - 4, ox + 3, oy + 4, GEEL)
        dk.px(ox - 3, oy - 5, ZWART)
    # wenkbrauwen
    dk.lijn([(OGEN[0][0] - 3, 126), (OGEN[0][0] + 2, 125)], ZWART)
    dk.lijn([(OGEN[1][0] - 2, 125), (OGEN[1][0] + 3, 126)], ZWART)
    # een dikke neus
    dk.ovaal(cx - 3, 136, cx + 3, 142, ORANJE)
    dk.px(cx + 1, 137, GEEL)
    # de mond: een zwarte lijn met rood erin (open), dicht wordt het rood bruin (src/taalmenu.asm)
    x1, y1, x2, y2 = MOND
    dk.lijn([(x1 - 1, y1 - 1), (x1, y1), (x2, y1), (x2 + 1, y1 - 1)], ZWART)
    dk.rect(x1 + 1, y1 + 1, x2 - 1, y2, ROOD)
    dk.lijn([(x1, y1 + 1), (x1 + 1, y2 + 1), (x2 - 1, y2 + 1), (x2, y1 + 1)], ZWART)


def ballon(dk):
    # een witte spreekballon met een zwarte rand en een staartje naar de mond
    x1, y1, x2, y2 = 48, 24, 158, 63
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            hoek = min(x - x1, x2 - x) < 3 and min(y - y1, y2 - y) < 3
            if hoek and (min(x - x1, x2 - x) + min(y - y1, y2 - y)) < 3:
                continue
            dk.px(x, y, WIT)
    dk.poly([(50, 62), (57, 62), (36, 122)], WIT)
    dk.lijn([(50, 63), (36, 122), (57, 63)], ZWART)


def vlaggen(dk):
    for i, vx in enumerate(VLAG_X):
        x0, y0 = vx * 4, VLAG_Y
        # de stok, in de grond
        dk.rect(x0 - 2, y0 - 6, x0 - 2, 166, BRUIN)
        # de rand (oplichten bij aanwijzen): in de vakjes om de vlag heen
        for x in range(x0 - 1, x0 + VLAG_B + 1):
            dk.px(x, y0 - 1, LGRIJS)
            dk.px(x, y0 + VLAG_H, LGRIJS)
        for y in range(y0 - 1, y0 + VLAG_H + 1):
            dk.px(x0 + VLAG_B, y, LGRIJS)
        # de vlag zelf
        if i == 0:                                              # Nederland: rood, wit, blauw
            for y in range(VLAG_H):
                k = ROOD if y < 11 else (WIT if y < 21 else BLAUW)
                dk.rect(x0, y0 + y, x0 + VLAG_B - 1, y0 + y, k)
        elif i == 1:                                            # het Verenigd Koninkrijk
            dk.rect(x0, y0, x0 + VLAG_B - 1, y0 + VLAG_H - 1, BLAUW)
            for y in range(VLAG_H):
                for x in range(VLAG_B):
                    u, v = x / (VLAG_B - 1), y / (VLAG_H - 1)
                    d1, d2 = abs(u - v), abs(u - (1 - v))
                    if d1 < 0.09 or d2 < 0.09:
                        dk.px(x0 + x, y0 + y, WIT)
                    if (d1 < 0.035 and (u < 0.5) == (v < 0.5) and u < v) or \
                            (d1 < 0.035 and (u > 0.5) and u > v) or \
                            (d2 < 0.035 and ((u < 0.5 and u + v < 1) or (u > 0.5 and u + v > 1))):
                        dk.px(x0 + x, y0 + y, ROOD)
            dk.rect(x0 + 9, y0, x0 + 14, y0 + VLAG_H - 1, WIT)
            dk.rect(x0, y0 + 12, x0 + VLAG_B - 1, y0 + 19, WIT)
            dk.rect(x0 + 10, y0, x0 + 13, y0 + VLAG_H - 1, ROOD)
            dk.rect(x0, y0 + 14, x0 + VLAG_B - 1, y0 + 17, ROOD)
        elif i == 2:                                            # Duitsland: zwart, rood, goud
            for y in range(VLAG_H):
                k = ZWART if y < 11 else (ROOD if y < 21 else GEEL)
                dk.rect(x0, y0 + y, x0 + VLAG_B - 1, y0 + y, k)
            dk.lijn([(x0, y0), (x0 + VLAG_B - 1, y0)], DGRIJS)  # (zwart op zwart: een randje)
        else:                                                   # Frankrijk: blauw, wit, rood
            for x in range(VLAG_B):
                k = BLAUW if x < 8 else (WIT if x < 16 else ROOD)
                dk.rect(x0 + x, y0, x0 + x, y0 + VLAG_H - 1, k)
        # het cijfer eronder, op een bordje
        bx = vx + 2
        dk.rect(bx * 4 - 2, 168, bx * 4 + 9, 182, BRUIN)
        dk.rect(bx * 4 - 1, 169, bx * 4 + 8, 181, ZWART)
        dk.tekst(bx + 0, 171, " %d" % (i + 1) if False else str(i + 1), GEEL)


def titel(dk):
    s = "HOLLOW CROWN"
    x = (40 - len(s)) // 2 + 2
    dk.tekst(x, 6, s, GEEL)
    for i in range(len(s) * 4):
        if dk.get(x * 4 + i, 17) == ZWART:
            pass


def teken():
    rnd = random.Random(64)
    dk = Doek()
    lucht(dk, rnd)
    heuvels(dk, rnd)
    hol(dk, rnd)
    vlaggen(dk)
    aardmannetje(dk, rnd)
    ballon(dk)
    titel(dk)
    # het tekstvak leeg (wit): de tekst schrijft het menu er zelf in
    for y in range(TEKST_Y1, TEKST_Y2 + 1):
        for x in range(TEKST_X1 * 4, (TEKST_X2 + 1) * 4):
            dk.px(x, y, WIT)
    return dk


# ---- omzetten naar C64-gegevens --------------------------------------------------------------------------------------
def omzetten(dk):
    """per vakje (4 x 8): zwart = %00; de andere kleuren (hooguit 3) naar %01 (scherm hoog), %10 (scherm laag),
    %11 (kleur-RAM). Wit in het tekstvak staat vast op %11 (de tekst wordt erin geschreven als %00 op %11)."""
    bitmap = bytearray(8000)
    scherm = bytearray(1000)
    kleur = bytearray(1000)
    plek = {}                                   # (vakje, kleur) -> 0 hoog, 1 laag, 2 kleur-RAM
    fouten = []
    for cy in range(25):
        for cx in range(40):
            v = cy * 40 + cx
            pix = [dk.p[cy * 8 + y][cx * 4 + x] for y in range(8) for x in range(4)]
            tel = {}
            for k in pix:
                if k != ZWART:
                    tel[k] = tel.get(k, 0) + 1
            if len(tel) > 3:
                fouten.append("vakje %d,%d: %d kleuren %s" % (cx, cy, len(tel), [cb.NAMEN[k] for k in tel]))
                for k in sorted(tel, key=lambda k: tel[k])[:len(tel) - 3]:
                    del tel[k]
            codes = {}
            vrij = [1, 2, 3]
            tekstvak = TEKST_X1 <= cx <= TEKST_X2 and TEKST_Y1 // 8 <= cy <= TEKST_Y2 // 8
            if tekstvak and WIT in tel:
                codes[WIT] = 3
                vrij.remove(3)
            for k in sorted(tel, key=lambda k: -tel[k]):
                if k not in codes:
                    codes[k] = vrij.pop(0)
            hoog = laag = km = 0
            for k, c in codes.items():
                if c == 1:
                    hoog = k
                elif c == 2:
                    laag = k
                else:
                    km = k
                plek[(v, k)] = c - 1
            scherm[v] = hoog << 4 | laag
            kleur[v] = km
            for y in range(8):
                b = 0
                for x in range(4):
                    k = dk.p[cy * 8 + y][cx * 4 + x]
                    b = b << 2 | (0 if k == ZWART else codes.get(k, 0))
                bitmap[(cy * 40 + cx) * 8 + y] = b
    return bitmap, scherm, kleur, plek, fouten


def effect(plek, gebied, k):
    """alle plekken van kleur k in de vakjes van gebied (x1, y1, x2, y2 in mc-pixels)"""
    x1, y1, x2, y2 = gebied
    uit = []
    for cy in range(y1 // 8, y2 // 8 + 1):
        for cx in range(x1 // 4, x2 // 4 + 1):
            v = cy * 40 + cx
            if (v, k) in plek:
                uit.append((v, plek[(v, k)]))
    return uit


def proef(dk, pad):
    im = Image.new("RGB", (B, H))
    pal = [tuple(int(c) for c in cb.RGB[i]) for i in range(16)]
    im.putdata([pal[k] for r in dk.p for k in r])
    im.resize((B * 4, H * 2), Image.NEAREST).save(pad)


def main():
    uit = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORTEL, "build", "gen")
    dk = teken()
    bitmap, scherm, kleur, plek, fouten = omzetten(dk)
    if fouten:
        print("\n".join(fouten[:20]))
        raise SystemExit("[taalmenu] %d vakjes met te veel kleuren" % len(fouten))
    ox = [(OGEN[0][0] - 4, OGEN[0][1] - 5, OGEN[1][0] + 4, OGEN[1][1] + 5)]
    effecten = [("ogen", effect(plek, ox[0], GEEL)),
                ("mond", effect(plek, MOND, ROOD))]
    for i, vx in enumerate(VLAG_X):
        effecten.append(("rand%d" % i, effect(plek, (vx * 4 - 1, VLAG_Y - 1, vx * 4 + VLAG_B, VLAG_Y + VLAG_H), LGRIJS)))
    L = ["// gemaakt door tools/teken_taalmenu.py — niet met de hand veranderen", ""]

    def rij(label, data):
        L.append("%s:" % label)
        for i in range(0, len(data), 32):
            L.append("        .byte " + ", ".join("$%02x" % b for b in data[i:i + 32]))
    L.append(".const OOG_L_X = %d" % (OGEN[0][0] * 2 + 1))     # in hires-pixels (het midden van het oog)
    L.append(".const OOG_Y = %d" % OGEN[0][1])
    L.append(".const OOG_AFSTAND = %d" % ((OGEN[1][0] - OGEN[0][0]) * 2))
    L.append(".const TEKST_X1 = %d" % TEKST_X1)
    L.append(".const TEKST_X2 = %d" % TEKST_X2)
    L.append(".const TEKST_Y1 = %d" % TEKST_Y1)
    L.append(".const TEKST_Y2 = %d" % TEKST_Y2)
    L.append(".const REGEL1_Y = %d" % REGEL_Y[0])
    L.append(".const REGEL2_Y = %d" % REGEL_Y[1])
    L.append(".const VLAG_Y1 = %d" % VLAG_Y)
    L.append(".const VLAG_Y2 = %d" % (VLAG_Y + VLAG_H - 1))
    L.append("vlag_x1: .byte %s     // hires-pixels / 2 (0-159)" % ", ".join(str(v * 4) for v in VLAG_X))
    L.append("vlag_x2: .byte %s" % ", ".join(str(v * 4 + VLAG_B - 1) for v in VLAG_X))
    # effecten: per effect een rij van (adres lo, adres hi, soort) met soort 0 = scherm hoog, 1 = laag, 2 = kleur-RAM;
    # adres is de plek in het scherm-RAM (SCHERM + v) of het kleur-RAM ($D800 + v)
    L.append("effect_lo: .byte %s" % ", ".join("<effect_%s" % n for n, _ in effecten))
    L.append("effect_hi: .byte %s" % ", ".join(">effect_%s" % n for n, _ in effecten))
    for n, lijst in effecten:
        L.append("effect_%s: .byte %d" % (n, len(lijst)))
        for v, s in lijst:
            L.append("        .word %s + %d" % ("$d800" if s == 2 else "SCHERM", v))
            L.append("        .byte %d" % s)
    # het lettertype: per teken 10 bytes (5 rijen, elk twee keer), %00 = inkt (zwart), %11 = wit
    font = bytearray()
    for c in TEKENS:
        for r in FONT[c]:
            b = 0
            for j in range(4):
                t = r[j] if j < 3 else "."
                b = b << 2 | (0 if t == "#" else 3)
            font += bytes([b, b])
    rij("font", font)
    # de zinnen: per zin x1, n1, tekens..., x2, n2, tekens...
    namen = []
    for soort in ("wacht", "wijs", "kies"):
        for t, (r1, r2) in enumerate(ZINNEN[soort]):
            data = []
            for r in (r1, r2):
                if len(r) > TEKST_X2 - TEKST_X1 + 1:
                    raise SystemExit("[taalmenu] te lang: %r" % r)
                data += [TEKST_X1 + (TEKST_X2 - TEKST_X1 + 1 - len(r)) // 2, len(r)] + [TEKENS.index(c) for c in r]
            n = "zin_%s_%d" % (soort, t)
            namen.append(n)
            L.append("%s: .byte %s" % (n, ", ".join(str(b) for b in data)))
    for soort in ("wacht", "wijs", "kies"):
        L.append("zinnen_%s_lo: .byte %s" % (soort, ", ".join("<zin_%s_%d" % (soort, t) for t in range(4))))
        L.append("zinnen_%s_hi: .byte %s" % (soort, ", ".join(">zin_%s_%d" % (soort, t) for t in range(4))))
    # sprites (hires, 24 x 21): de pijl (wit), zijn zwarte rand (de pijl een pixel dikker), en de pupillen
    pijl = [r.ljust(24, ".") for r in PIJL] + ["." * 24] * (21 - len(PIJL))
    rand = []
    for y in range(21):
        rij_ = ""
        for x in range(24):
            buur = any(0 <= y + dy < 21 and 0 <= x + dx < 24 and pijl[y + dy][x + dx] == "#"
                       for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            rij_ += "#" if buur else "."
        rand.append(rij_)
    pupil = ["." * 24 for _ in range(21)]
    vorm = [".##.", "#.##", "####", ".##."]                    # met een lichtpuntje (daar schijnt het geel door)
    for y, r in enumerate(vorm):
        for links in (0, (OGEN[1][0] - OGEN[0][0]) * 2):
            pupil[y] = pupil[y][:links] + r + pupil[y][links + 4:]
    for naam, vorm_ in (("sprite_pupil", pupil),):
        data = bytearray()
        for r in vorm_:
            data += int(r.replace("#", "1").replace(".", "0"), 2).to_bytes(3, "big")
        rij(naam, data + b"\0")
    L.append("")
    L.append(".segment Plaatje")
    rij("plaatje_bitmap", bitmap)
    rij("plaatje_scherm", scherm)
    rij("plaatje_kleur", kleur)
    os.makedirs(uit, exist_ok=True)
    open(os.path.join(uit, "taalmenu_data.asm"), "w").write("\n".join(L) + "\n")
    os.makedirs(os.path.join(WORTEL, "build", "proef"), exist_ok=True)
    proef(dk, os.path.join(WORTEL, "build", "proef", "taalmenu.png"))
    print("[taalmenu] %s; effecten: %s" % (os.path.relpath(os.path.join(uit, "taalmenu_data.asm"), WORTEL),
                                            ", ".join("%s %d" % (n, len(l)) for n, l in effecten)))


if __name__ == "__main__":
    main()
