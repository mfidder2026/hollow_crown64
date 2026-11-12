# Logboek Hollow Crown

## 2026-11-12 — Voorbereiding (vóór hoofdstuk 0)

**Ontwikkelstack gecontroleerd:**
- Java: OpenJDK 27.0.1 (`/opt/homebrew/opt/openjdk/bin/java`). `/usr/bin/java` is de macOS-stub en werkt niet.
- Kick Assembler v5.14 (`tools/KickAss.jar`).
- VICE 3.10: `/Applications/vice-arm64-gtk3-3.10/bin/x64sc` en `c1541`. (VICE 3.9 staat er ook nog naast.)
- Python 3.9.6 met Pillow 11.3 en numpy 2.0.
- Syntaxchecker `tools/c64_ka_syntax_checker.py`: 0 fouten op de oude demo en het kijkprogramma.

**Getest:** de oude demo (`oud/demo/hollowcrown.asm`) geassembleerd, met `c1541` op een D64 gezet en in x64sc
(PAL, eigen procesgroep, `-limitcycles` + `-exitscreenshot`) automatisch gestart: Dawnhaven met Eldric verschijnt.
`tools/sprites_hc.py` maakt na de verhuizing een identieke `src/sprites_hc.asm`.

**Mappen opgeruimd** volgens §7: oude probeersels, het oude `build.sh`, de oude build en screenshots naar `oud/`;
FLUX-plaatjes naar `data/flux/`; Koala naar `data/`; KickAss-documentatie naar `docs/referentie/`.

**Open / opgemerkt:**
- In de prompt heet het plaatje `dawnhaven_flux.png`; het bestand is `data/flux/dawnhaven.png`.
- `tools/KickAss.cfg` schrijft .sym-bestanden naast de bron; het nieuwe `build.sh` moet `-symbolfiledir build` geven.
- Laden vanaf D64 met echte drive-emulatie kost ~30-60 M cycli; `vicetest.py` moet daar rekening mee houden.
- Geen git-repository.

## 2026-11-12 — Hoofdstuk 0: opzet ✅

**Klaar als:** `./build.sh` maakt `build/hollowcrown.d64`; de test start VICE en maakt een screenshot. **Gehaald.**

**Wat er is:**
- `src/geheugen.asm`: de geheugenkaart van §6.1 als constanten en segments (`Basic`, `Code`, `Data`, `Buffers`
  onder `$C000`; `Scherm`, `Sprites`, `Lettertype`, `Bitmap` virtueel ter controle) met `max=` en `.assert`'s.
- `src/main.asm`: VIC-bank 3 (`$DD00` lezen-wijzigen-schrijven), tekstmodus, ROM-lettertype tijdelijk naar `$C800`,
  hoofdlus op de beeldteller. `src/irq.asm`: één raster-IRQ op lijn 252 (CIA-IRQ uit, `jmp $EA31`).
- `src/status.asm`: de spelstatus in één blok (magic "HC", versie 1, kamer, positie, 256 vlaggen, 64 voorwerpen).
- `src/autotest.asm` (alleen met `-define AUTOTEST`): de invoerband met opcodes EINDE, WACHT, MARKEER.
  CURSOR en VUUR zijn gereserveerd voor hoofdstuk 1; het spel meldt ze nu als onbekend.
- `build.sh`: scripts → kamers/costumes → syntaxcheck + assembleren → D64. Stopt bij de eerste fout met
  bestand:regel. `--autotest` bouwt naar `build/autotest/`.
- `tools/vicetest.py`: start VICE (eigen procesgroep, vrije poort voor de remote monitor), wacht op magic "HC",
  schrijft de band in het geheugen, maakt screenshots op de markeringen (de C64 wacht daarop), en vergelijkt
  het geheugen met `tests/<naam>.verwacht`.

**Gemeten / getest:**
- `tests/wacht.band` (50 + 250 beelden, 2 screenshots): GESLAAGD in 1,6 s (warp); beeldteller 473 aan het eind.
  Screenshots `wacht_begin.png` ($0084) en `wacht_eind.png` ($01A6) verschillen.
- Ook met `--echte-drive` (1541-emulatie): GESLAAGD, spel draait na 1,3 s (warp, dus geen echte laadtijd).
- Negatieve proeven: verkeerde verwachte waarde → MISLUKT (exitcode 1); band met `vuur` → "opcode $04 onbekend";
  een te grote spelstatus → mislukte `.assert` → build stopt met exitcode 1.
- Na elke test draait er geen x64sc meer.

**Beslissingen:**
- Kick Assembler gaat bij een mislukte `.assert` door met exitcode 0. `build.sh` zoekt daarom zelf naar
  `ERROR IN ASSERTION` en stopt.
- Standaard test zonder echte drive-emulatie (snel). `--echte-drive` is er voor laadtijden (hoofdstuk 6).
- Het tijdelijke lettertype is de kleine-letterset uit de ROM; het eigen lettertype komt in hoofdstuk 1.

**Open:** de split (lijn 66/194), de balk en de cursor: hoofdstuk 1.
