#!/usr/bin/env python3
"""lettertype.py — het eigen lettertype (§6.6) en de cursor, getekend als tekst.

    python3 tools/lettertype.py build/gen

    build/gen/lettertype.bin    256 tekens x 8 bytes, op de plek van de schermcodes ("screencode_mixed")
    build/gen/cursor.bin        hires sprite van 64 bytes (24 x 21), het midden is (CURSOR_X, CURSOR_Y)
    build/gen/lettertype.png    controle: alle tekens, 4x vergroot

Regels voor de tekens (voor schone naden, §6.3):
    - pixelrij 0 is bij ALLE 256 tekens leeg. Op de naden kan de VIC een paar pixels in tekstmodus tonen
      met de kleurbytes van de kamer als tekencodes: dan zie je rij 0, dus zwart;
    - hoofdletters en cijfers staan in rij 1-6, kleine letters in rij 3-6 (met stokken vanaf rij 1),
      staartjes (g j p q y , ;) in rij 7.
Een teken is hieronder 7 regels (pixelrij 1-7) van hooguit 6 tekens breed: kolom 1-6 van het teken.
"""
import os, struct, sys, zlib

# Plekken die niet uit "screencode_mixed" komen: de compiler van de scripts gebruikt deze tabel ook.
EXTRA = {"↑": 0x1E, "↓": 0x1F, "é": 0x5B, "ë": 0x5C, "ï": 0x5D, "ö": 0x5E, "ü": 0x5F}


def code_van(t):
    """Schermcode van een teken (zoals Kick Assembler met .encoding "screencode_mixed")."""
    if t in EXTRA:
        return EXTRA[t]
    if "a" <= t <= "z":
        return ord(t) - ord("a") + 1
    if "A" <= t <= "Z":
        return ord(t) - ord("A") + 0x41
    if " " <= t <= "?":
        return ord(t)
    if t == "@":
        return 0
    raise KeyError(t)


# Elk teken: 7 regels, pixelrij 1 t/m 7. Lege regels mogen weg aan het eind.
TEKENS = {
    " ": [],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#"],
    "B": ["####.", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "###..", "#..#.", "#...#", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#.."],
    "Z": ["#####", "...#.", "..#..", ".#...", "#....", "#####"],
    "a": ["", "", ".####", "#...#", "#...#", ".####"],
    "b": ["#....", "#....", "####.", "#...#", "#...#", "####."],
    "c": ["", "", ".####", "#....", "#....", ".####"],
    "d": ["....#", "....#", ".####", "#...#", "#...#", ".####"],
    "e": ["", "", ".###.", "#####", "#....", ".####"],
    "f": ["..##.", ".#...", "###..", ".#...", ".#...", ".#..."],
    "g": ["", "", ".####", "#...#", ".####", "....#", ".###."],
    "h": ["#....", "#....", "####.", "#...#", "#...#", "#...#"],
    "i": ["..#..", "", ".##..", "..#..", "..#..", ".###."],
    "j": ["...#.", "", "..##.", "...#.", "...#.", "#..#.", ".##.."],
    "k": ["#....", "#....", "#..#.", "###..", "#..#.", "#...#"],
    "l": [".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "m": ["", "", "##.#.", "#.#.#", "#.#.#", "#.#.#"],
    "n": ["", "", "####.", "#...#", "#...#", "#...#"],
    "o": ["", "", ".###.", "#...#", "#...#", ".###."],
    "p": ["", "", "####.", "#...#", "####.", "#....", "#...."],
    "q": ["", "", ".####", "#...#", ".####", "....#", "....#"],
    "r": ["", "", "#.##.", "##...", "#....", "#...."],
    "s": ["", "", ".####", "##...", "...##", "####."],
    "t": [".#...", ".#...", "####.", ".#...", ".#...", "..##."],
    "u": ["", "", "#...#", "#...#", "#...#", ".####"],
    "v": ["", "", "#...#", "#...#", ".#.#.", "..#.."],
    "w": ["", "", "#...#", "#.#.#", "#.#.#", ".#.#."],
    "x": ["", "", "#...#", ".#.#.", ".#.#.", "#...#"],
    "y": ["", "", "#...#", "#...#", ".####", "....#", ".###."],
    "z": ["", "", "#####", "...#.", ".#...", "#####"],
    "é": ["...#.", "..#..", ".###.", "#####", "#....", ".####"],
    "ë": [".#.#.", "", ".###.", "#####", "#....", ".####"],
    "ï": [".#.#.", "", ".##..", "..#..", "..#..", ".###."],
    "ö": [".#.#.", "", ".###.", "#...#", "#...#", ".###."],
    "ü": [".#.#.", "", "#...#", "#...#", "#...#", ".####"],
    "0": [".###.", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "..##.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "####."],
    "6": [".###.", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#..."],
    "8": [".###.", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", ".###."],
    "!": ["..#..", "..#..", "..#..", "..#..", "", "..#.."],
    '"': [".#.#.", ".#.#."],
    "'": ["..#..", "..#.."],
    "(": ["...#.", "..#..", "..#..", "..#..", "..#..", "...#."],
    ")": [".#...", "..#..", "..#..", "..#..", "..#..", ".#..."],
    ",": ["", "", "", "", "", "..#..", ".#..."],
    "-": ["", "", "", ".###."],
    ".": ["", "", "", "", "", "..#.."],
    "/": ["....#", "...#.", "..#..", "..#..", ".#...", "#...."],
    ":": ["", "", "..#..", "", "", "..#.."],
    ";": ["", "", "..#..", "", "", "..#..", ".#..."],
    "?": [".###.", "#...#", "...#.", "..#..", "", "..#.."],
    "+": ["", "..#..", "..#..", "#####", "..#..", "..#.."],
    "=": ["", "", "#####", "", "#####"],
    "*": ["", "#.#.#", ".###.", "#####", ".###.", "#.#.#"],
    "%": ["##..#", "##.#.", "..#..", ".#...", "#.##.", "#..##"],
    "&": [".##..", "#..#.", ".##..", "#..##", "#..#.", ".##.#"],
    "#": [".#.#.", "#####", ".#.#.", ".#.#.", "#####", ".#.#."],
    "↑": ["..#..", ".###.", "#.#.#", "..#..", "..#..", "..#.."],
    "↓": ["..#..", "..#..", "..#..", "#.#.#", ".###.", "..#.."],
}

# De cursor: hires, 24 x 21. Het midden (de plek waar hij wijst) is kolom CURSOR_X, rij CURSOR_Y.
CURSOR_X, CURSOR_Y = 11, 10
CURSOR = [
    "...........#............",
    "...........#............",
    "...........#............",
    "...........#............",
    "...........#............",
    "...........#............",
    "........................",
    "........................",
    "........................",
    "........................",
    "######.........######...",
    "........................",
    "........................",
    "........................",
    "........................",
    "...........#............",
    "...........#............",
    "...........#............",
    "...........#............",
    "...........#............",
    "...........#............",
]


def teken_bytes(regels):
    if len(regels) > 7:
        raise ValueError("hooguit 7 regels (pixelrij 1-7)")
    b = [0]                                  # pixelrij 0: altijd leeg
    for r in range(7):
        s = regels[r] if r < len(regels) else ""
        if len(s) > 6:
            raise ValueError("hooguit 6 breed: %r" % s)
        v = 0
        for i, ch in enumerate(s):
            if ch == "#":
                v |= 0x80 >> (i + 1)
            elif ch != ".":
                raise ValueError("alleen # en .: %r" % s)
        b.append(v)
    return b


def lettertype():
    data = bytearray(256 * 8)
    gezien = {}
    for t, regels in TEKENS.items():
        c = code_van(t)
        if c in gezien:
            raise SystemExit("teken %r en %r hebben dezelfde code $%02x" % (t, gezien[c], c))
        gezien[c] = t
        try:
            data[c * 8:c * 8 + 8] = bytes(teken_bytes(regels))
        except ValueError as e:
            raise SystemExit("teken %r: %s" % (t, e))
    assert all(data[c * 8] == 0 for c in range(256)), "pixelrij 0 moet leeg zijn"
    return bytes(data)


def cursor():
    assert len(CURSOR) == 21 and all(len(r) == 24 for r in CURSOR)
    data = bytearray()
    for r in CURSOR:
        v = int(r.replace("#", "1").replace(".", "0"), 2)
        data += v.to_bytes(3, "big")
    return bytes(data) + b"\x00"


def png(font, pad, schaal=4):
    W, H = 16 * 8, 16 * 8
    rijen = []
    for y in range(H):
        rij = bytearray()
        for x in range(W):
            c = (y // 8) * 16 + x // 8
            aan = font[c * 8 + y % 8] & (0x80 >> (x % 8))
            kleur = (255, 255, 255) if aan else ((30, 30, 30) if (x // 8 + y // 8) % 2 else (0, 0, 0))
            rij += bytes(kleur) * schaal
        rijen += [bytes(rij)] * schaal
    raw = b"".join(b"\x00" + r for r in rijen)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(pad, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W * schaal, H * schaal, 8, 2, 0, 0, 0))
                          + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    uit = sys.argv[1]
    os.makedirs(uit, exist_ok=True)
    font = lettertype()
    open(os.path.join(uit, "lettertype.bin"), "wb").write(font)
    open(os.path.join(uit, "cursor.bin"), "wb").write(cursor())
    png(font, os.path.join(uit, "lettertype.png"))
    with open(os.path.join(uit, "lettertype_info.asm"), "w") as f:
        f.write("// gemaakt door tools/lettertype.py — niet met de hand wijzigen\n")
        f.write(".const CURSOR_MIDDEN_X = %d\n.const CURSOR_MIDDEN_Y = %d\n" % (CURSOR_X, CURSOR_Y))
        f.write(".const TEKEN_PIJL_OP = $%02x\n.const TEKEN_PIJL_NEER = $%02x\n" % (EXTRA["↑"], EXTRA["↓"]))
    print("[letters] %d tekens, cursor 24x21" % len(TEKENS))


if __name__ == "__main__":
    main()
