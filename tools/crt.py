#!/usr/bin/env python3
"""crt.py — maakt een EasyFlash-cartridge (CRT, hardwaretype 32, 1 MB) van het hele spel, in alle talen.

    python3 tools/crt.py uit.crt crtboot.bin TAAL=nl:prog.prg:START [TAAL=en:...] bestand.prg:NAAM [...]

TAAL=xx:programma:start (start in hex) mag tot vier keer, in de volgorde nl, en, de, fr van het taalmenu.
MENU=taalmenu.prg: het taalmenu (src/taalmenu.asm), dat src/crtboot.asm naar zijn eigen adres haalt.
Indeling (src/crtboot.asm en src/cartridge.asm lezen dit zo):
  bank 0, ROML $8000   de talentabel: per taal (nl, en, de, fr) en daarna het taalmenu 8 bytes: bank, adres (lo, hi),
                       lengte (lo, hi), start (lo, hi), 1 als hij er is
  bank 0, ROML $8100   de inhoudsopgave: per bestand 16 tekens naam ($a0-aangevuld, PETSCII hoofdletters), bank,
                       adres (lo, hi, $8000-$BFFF), lengte (lo, hi); een 0 als eerste teken is het einde
  bank 0, ROMH         aan het eind (vanaf $1E00, in de Ultimax-stand $FE00) het opstarten met de resetvector
  bank 1 en verder     alles achter elkaar zonder laadadres, 16 KB per bank (ROML $8000-$9FFF, dan ROMH $A000-$BFFF)
"""
import struct, sys

HELFT = 0x2000
BANK = 0x4000
MAX_BANKEN = 64                        # EasyFlash: 1 MB
TALEN = ["nl", "en", "de", "fr"]


def petscii(naam):
    b = naam.upper().encode("ascii")[:16]
    return b + bytes([0xa0]) * (16 - len(b))


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    uit, boot = sys.argv[1:3]
    boot = open(boot, "rb").read()
    if len(boot) != 0x200:
        raise SystemExit("crt: het opstarten moet precies 512 bytes zijn ($FE00-$FFFF), niet %d" % len(boot))
    data = bytearray()                                     # vanaf bank 1

    def erbij(inhoud_):
        plek = BANK + len(data)
        bank, adres = plek // BANK, 0x8000 + plek % BANK
        data.extend(inhoud_)
        return bank, adres

    tabel = bytearray(8 * (len(TALEN) + 1))
    inhoud = bytearray()
    talen = []
    for arg in sys.argv[3:]:
        if arg.startswith("MENU="):
            p = open(arg[5:], "rb").read()
            laad = p[0] | p[1] << 8
            bank, adres = erbij(p[2:])
            i = len(TALEN) * 8
            tabel[i:i + 8] = bytes([bank, adres & 255, adres >> 8, (len(p) - 2) & 255, (len(p) - 2) >> 8,
                                    laad & 255, laad >> 8, 1])
        elif arg.startswith("TAAL="):
            taal, prog, start = arg[5:].split(":")
            p = open(prog, "rb").read()[2:]
            bank, adres = erbij(p)
            i = TALEN.index(taal) * 8
            tabel[i:i + 8] = bytes([bank, adres & 255, adres >> 8, len(p) & 255, len(p) >> 8,
                                    int(start, 16) & 255, int(start, 16) >> 8, 1])
            talen.append(taal)
        else:
            bron, _, naam = arg.rpartition(":")
            b = open(bron, "rb").read()[2:]
            bank, adres = erbij(b)
            inhoud += petscii(naam) + bytes([bank, adres & 255, adres >> 8, len(b) & 255, len(b) >> 8])
    inhoud += b"\0"
    if 0x100 + len(inhoud) > HELFT:
        raise SystemExit("crt: de inhoudsopgave past niet in bank 0")
    bank0 = bytearray(BANK)
    bank0[:len(tabel)] = tabel
    bank0[0x100:0x100 + len(inhoud)] = inhoud
    bank0[BANK - 0x200:] = boot                          # ROMH, $1E00-$1FFF: in de Ultimax-stand $FE00-$FFFF
    rom = bank0 + data
    banken = (len(rom) + BANK - 1) // BANK
    if banken > MAX_BANKEN:
        raise SystemExit("crt: %d banken, de cartridge heeft er hooguit %d" % (banken, MAX_BANKEN))
    rom += bytes([0xff]) * (banken * BANK - len(rom))
    kop = (b"C64 CARTRIDGE   " + struct.pack(">IHHBB", 0x40, 0x0100, 32, 1, 0) + bytes(6)
           + b"HOLLOW CROWN".ljust(32, b"\0"))
    uitdata = bytearray(kop)
    for b in range(banken):
        for helft, laad in ((0, 0x8000), (1, 0xA000)):
            stuk = rom[b * BANK + helft * HELFT:b * BANK + (helft + 1) * HELFT]
            uitdata += b"CHIP" + struct.pack(">IHHHH", 0x2010, 2, b, laad, HELFT) + stuk
    open(uit, "wb").write(uitdata)
    print("[crt] %s: EasyFlash, %d banken (%d KB), talen %s, %d bestanden, %d KB vrij" % (
        uit, banken, banken * 16, "/".join(talen), sum(1 for a in sys.argv[3:] if not a.startswith(("TAAL=", "MENU="))),
        (MAX_BANKEN * BANK - len(rom.rstrip(b"\xff"))) // 1024))


if __name__ == "__main__":
    main()
