#!/usr/bin/env python3
"""inpak.py — eenvoudige RLE voor kamers en andere data (§6.2). De uitpakker in asm staat in src/inpak.asm.

Formaat, een reeks blokken:
    $00-$7F n       n+1 letterlijke bytes volgen
    $80-$FE n       herhaal de volgende byte (n - $80 + 2) keer: 2..128 keer
    $FF             einde
"""
import sys

EINDE = 0xFF


def pak(data):
    data = bytes(data)
    uit = bytearray()
    los = bytearray()

    def spoel():
        while los:
            stuk = los[:128]
            uit.append(len(stuk) - 1)
            uit.extend(stuk)
            del los[:128]

    i = 0
    while i < len(data):
        n = 1
        while i + n < len(data) and data[i + n] == data[i] and n < 128:
            n += 1
        if n >= 3 or (n == 2 and not los):
            spoel()
            uit += bytes([0x80 + n - 2, data[i]])
            i += n
        else:
            los.append(data[i])
            i += 1
            if len(los) == 128:
                spoel()
    spoel()
    uit.append(EINDE)
    return bytes(uit)


def uitpak(data, start=0):
    """Geeft (uitgepakte bytes, positie na het einde-teken)."""
    uit = bytearray()
    i = start
    while True:
        c = data[i]
        i += 1
        if c == EINDE:
            return bytes(uit), i
        if c < 0x80:
            uit += data[i:i + c + 1]
            i += c + 1
        else:
            uit += bytes([data[i]]) * (c - 0x80 + 2)
            i += 1


if __name__ == "__main__":
    # zelftest
    import random
    random.seed(1)
    for proef in [b"", b"a", b"aa", b"aaa", bytes(300), bytes(range(256)) * 3,
                  bytes(random.choice(b"aab") for _ in range(5000))]:
        p = pak(proef)
        assert uitpak(p)[0] == proef, proef[:20]
    print("inpak.py: zelftest goed")
    sys.exit(0)
