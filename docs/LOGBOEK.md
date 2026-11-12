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

## 2026-11-12 — Hoofdstuk 1: het scherm ✅

**Klaar als:** 3 screenshots op verschillende momenten, schone naden (rij 1/2 en 17/18), cursor op een andere
plek. **Gehaald**, en strenger getest: elke screenshot wordt pixel voor pixel vergeleken met het scherm zoals het
uit het geheugen hoort te zijn (`scherm = ideaal` in `tests/scherm.verwacht`); alleen sprites tellen niet mee.

**Wat er is:**
- `tools/kamer.py` + `data/kamers.txt`: FLUX-plaatje → strook 5:2 → 160×128 multicolor (gebruikt de omzetter
  van `tools/c64beeld.py`), achtergrond zwart, bovenste rij en onderste 2 rijen zwart. Ingepakt met
  `tools/inpak.py` (RLE, zelftest): plein 4508 bytes (ongepakt 6400). Controle: `build/gen/kamer_plein.png`.
- `tools/lettertype.py`: eigen lettertype (88 tekens, met ↑ ↓ é ë ï ö ü), pixelrij 0 altijd leeg; de cursor.
- `src/irq.asm`: drie raster-IRQ's (65→66, 194→195, 252). `src/scherm.asm`, `inpak.asm`, `kamer.asm`,
  `balk.asm` (zinregel, 12 werkwoorden, lege inventaris met pijlen, hoofdstuknaam), `invoer.asm` (joystick 2),
  `cursor.asm` (sprite 0, versnelt tot 4 px/beeld, wisselt van kleur om zichtbaar te blijven).
- `src/teksten_nl.asm`: de vaste teksten apart van de motor (Engels later in een eigen bestand).
- Band: `cursor x,y` beweegt de cursor met dezelfde joystickcode (versnellen inbegrepen), `vuur` drukt één beeld.

**Beslissing (afwijking van §6.1):** lettertype op `$F800` i.p.v. `$C800`. Dan is `$d018` altijd `$0E` en wisselen
op de naden alleen `$d011`/`$d016`. Een te late wissel valt dan weg tegen zwarte randrijen en lege pixelrij 0.
De reden staat ook in `src/geheugen.asm`. `$C800-$CFFF` komt vrij. `$d021` is overal zwart.

**Gemeten** (watchpoint op `$d011`): kamerwissel op lijn 66 cyclus 62 / lijn 67 cyclus 0; balkwissel op lijn 195
cyclus 9 of 56; onderrand lijn 252.

**Getest:**
- `tests/scherm.band`: 5 screenshots (midden, linksboven, cursor óp naad 1/2, óp naad 17/18, in de balk): alle 5
  pixel voor pixel gelijk. Cursor eindigt op 250,180, hoogste snelheid 4, vuur 1 keer geteld. GESLAAGD.
- `tests/wacht.band`: nog steeds GESLAAGD.
- Kan de test een vuile naad zien? Met opzet stukgemaakt: wachtlus weg → 5 pixels fout op pixelrij 15
  (staartjes van j/p in rij 1); balkwissel op lijn 193 → 3 pixels fout op pixelrij 143. Beide gevonden.
  (Balkwissel op lijn 194 valt in de rechterrand en is echt onzichtbaar: terecht geen fout.)

**Niet getest:**
- De echte joystick (`$DC00`): de band vervangt die in een AUTOTEST-build en VICE's monitor kan geen stick
  vasthouden. Alleen de leesregel verschilt; de beweegcode is dezelfde.
- Naden met 8 sprites tegelijk op de naadlijnen (komt met Eldric en NPC's in hoofdstuk 2/7).

**Open:** de kamer is nog wat korrelig (Floyd-Steinberg in de lucht); afstemmen kan in `data/kamers.txt`.
De cursor is in zijn zwarte fase onzichtbaar op zwart; prima voor nu.
