#!/usr/bin/env python3
"""d64.py — maakt een D64 (een 1541-diskette) met een eigen tussenruimte (interleave) tussen de sectoren van een bestand.

    python3 tools/d64.py uit.d64 "hollow crown,hc" bron.prg:NAAM [bron2.prg:NAAM2 ...] [--interleave N]

Waarom zelf: c1541 legt de sectoren van een bestand altijd 10 sectoren uit elkaar. Voor onze snellader
(src/turbo.asm) is gemeten (een kamer heen en terug, VICE met echte 1541-emulatie): tussenruimte 1: 10,6 s,
2: 8,0 s, 3: 8,1 s, 5: 8,7 s, 7: 9,2 s, 10: 9,5 s, 14: 10,2 s, 20: 11,1 s (de Kernal: 16,1 s). Standaard dus 3.
(Dat een grote tussenruimte niet helpt, wijst op een vaste vertraging per sector in de jobqueue van de DOS: een
eigen sectorlezer in de drive zou nog sneller zijn.) De Kernal
merkt er niets van (die is toch langzamer); opslaan (F5) werkt gewoon, want de BAM klopt.

Indeling zoals de DOS van de 1541: spoor 18 is de directory (sector 0 de BAM, de namen vanaf sector 1, elke 3e
sector); bestanden beginnen bij spoor 17 en gaan dan naar buiten (17, 19, 16, 20, ...).
"""
import sys

SPOREN = 35


def sectoren(spoor):
    return 21 if spoor <= 17 else 19 if spoor <= 24 else 18 if spoor <= 30 else 17


def plek(spoor, sector):
    """byte-offset van een sector in het D64-bestand"""
    return (sum(sectoren(s) for s in range(1, spoor)) + sector) * 256


def petscii(tekst, lengte):
    b = tekst.upper().encode("ascii")[:lengte]
    return b + bytes([0xa0]) * (lengte - len(b))


class D64:
    def __init__(self, naam, id_, interleave=0):
        self.data = bytearray(plek(SPOREN + 1, 0))
        self.vrij = {s: set(range(sectoren(s))) for s in range(1, SPOREN + 1)}
        self.interleave = interleave
        self.vrij[18] -= {0, 1}                                   # BAM en de eerste directorysector
        self.dir = [(18, 1)]                                      # directorysectoren, in volgorde
        self.entries = []
        self.naam, self.id = naam, id_

    def sector(self, spoor, sector):
        p = plek(spoor, sector)
        return self.data, p

    def tussen(self, spoor):
        """de tussenruimte op dit spoor: vast, of (auto) zo dat er steeds ~150 ms tussen twee sectoren zit (een
        omwenteling is 200 ms; buiten 21 sectoren per spoor, binnen 17: daar duurt een sector langer)"""
        if self.interleave:
            return self.interleave
        return {21: 17, 19: 15, 18: 14, 17: 13}[sectoren(spoor)]

    def volgende_vrij(self, spoor, vanaf):
        n = sectoren(spoor)
        for i in range(n):
            s = (vanaf + i) % n
            if s in self.vrij[spoor]:
                return s
        return None

    def spoorvolgorde(self):
        uit = []
        for d in range(1, 18):                                   # 17, 19, 16, 20, ... (dicht bij de directory)
            for s in (18 - d, 18 + d):
                if 1 <= s <= SPOREN:
                    uit.append(s)
        return uit

    def schrijf_bestand(self, naam, inhoud):
        blokken = [inhoud[i:i + 254] for i in range(0, len(inhoud), 254)] or [b""]
        ketting = []
        sporen = self.spoorvolgorde()
        ti, sector = 0, 0
        for _ in blokken:
            while True:
                spoor = sporen[ti]
                s = self.volgende_vrij(spoor, sector)
                if s is not None:
                    break
                ti += 1
                sector = 0
                if ti >= len(sporen):
                    raise SystemExit("d64: de diskette is vol (%s)" % naam)
            self.vrij[spoor].discard(s)
            ketting.append((spoor, s))
            sector = s + self.tussen(spoor)                       # de volgende: een eind verder op hetzelfde spoor
        for i, (blok, (spoor, s)) in enumerate(zip(blokken, ketting)):
            p = plek(spoor, s)
            if i + 1 < len(ketting):
                self.data[p], self.data[p + 1] = ketting[i + 1]
            else:
                self.data[p], self.data[p + 1] = 0, len(blok) + 1  # laatste sector: de index van de laatste byte
            self.data[p + 2:p + 2 + len(blok)] = blok
        self.entries.append((naam, ketting[0], len(blokken)))

    def afmaken(self):
        # directory: 8 namen per sector; nieuwe directorysectoren op spoor 18, elke 3e sector
        for i, (naam, (t, s), blokken) in enumerate(self.entries):
            ds = i // 8
            while ds >= len(self.dir):
                vorige = self.dir[-1][1]
                nieuw = self.volgende_vrij(18, vorige + 3)
                self.vrij[18].discard(nieuw)
                self.dir.append((18, nieuw))
            p = plek(*self.dir[ds]) + (i % 8) * 32
            self.data[p + 2] = 0x82                               # PRG, gesloten
            self.data[p + 3], self.data[p + 4] = t, s
            self.data[p + 5:p + 21] = petscii(naam, 16)
            self.data[p + 30], self.data[p + 31] = blokken & 0xff, blokken >> 8
        for i, (t, s) in enumerate(self.dir):                    # de ketting van de directory
            p = plek(t, s)
            if i + 1 < len(self.dir):
                self.data[p], self.data[p + 1] = self.dir[i + 1]
            else:
                self.data[p], self.data[p + 1] = 0, 0xff
        # de BAM
        p = plek(18, 0)
        self.data[p:p + 4] = bytes([18, 1, 0x41, 0])
        for spoor in range(1, SPOREN + 1):
            q = p + 4 * spoor
            bits = 0
            for s in self.vrij[spoor]:
                bits |= 1 << s
            self.data[q] = len(self.vrij[spoor])
            self.data[q + 1:q + 4] = bytes([bits & 0xff, (bits >> 8) & 0xff, (bits >> 16) & 0xff])
        self.data[p + 0x90:p + 0xa0] = petscii(self.naam, 16)
        self.data[p + 0xa0:p + 0xa2] = b"\xa0\xa0"
        self.data[p + 0xa2:p + 0xa4] = petscii(self.id, 2)
        self.data[p + 0xa4] = 0xa0
        self.data[p + 0xa5:p + 0xa7] = b"2A"
        self.data[p + 0xa7:p + 0xab] = b"\xa0\xa0\xa0\xa0"
        return bytes(self.data)


def main():
    args = sys.argv[1:]
    interleave = 3                                               # gemeten: het snelst met de snellader (0 = per spoor)
    if "--interleave" in args:
        i = args.index("--interleave")
        interleave = int(args[i + 1])
        del args[i:i + 2]
    if len(args) < 2:
        raise SystemExit(__doc__)
    uit, kop, bestanden = args[0], args[1], args[2:]
    naam, _, id_ = kop.partition(",")
    d = D64(naam, id_ or "hc", interleave)
    for b in bestanden:
        bron, _, doel = b.rpartition(":")
        d.schrijf_bestand(doel, open(bron, "rb").read())
    open(uit, "wb").write(d.afmaken())


if __name__ == "__main__":
    main()
