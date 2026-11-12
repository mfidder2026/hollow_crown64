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

## 2026-11-12 — Invoer: joystick, muis en toetsenbord ✅ (aanvulling op hoofdstuk 1)

**Gevraagd:** alles moet werken, ook op een echte C64 zonder joystick.

**Wat er is (`src/invoer.asm`):**
- Joystick in poort 2; 1351-muis in poort 1 (bewegen, linkerknop = vuur, rechterknop gelezen);
  toetsenbord: CRSR ⇓ / CRSR ⇒, met SHIFT omhoog/links, RETURN = vuur. Alle drie tegelijk.
- `invoer_hardware` leest alles in de IRQ op de onderrand, vóór de Kernal-scan. `irq_balk` zet op lijn 195
  `$DC00 = $7F`, zodat de SID ~3600 cycli de muis in poort 1 meet (nodig: 512).
- Kolommen die poort 1 (muis/joystick 1) al laag trekt, tellen niet als toets: geen spooktoetsen.
- De muis begint pas te tellen na een eerste meting, en opnieuw als hij er (weer) in komt (potmeters $FF).

**Twee fouten gevonden door in VICE te kijken (niet door de bandtests):**
1. De joystick las `$DC00` in de hoofdlus. Na de Kernal-scan staat `$DC00` soms op 0, en dan las het spel
   "alle richtingen + vuur": de cursor liep vanzelf weg en vuur telde 7 keer. Nu alleen in de IRQ gelezen.
2. Met een 1351 in poort 1 sprong de cursor bij het starten naar 129,131 (één sprong van -31/+31): de eerste
   meting werd met een willekeurige beginwaarde vergeleken. Nu is de eerste meting het beginpunt.

**Getest:**
- `tests/invoer.band` (nieuw): ruwe joystick-, toets-, muisknop- en muisstappen gaan door de gewone
  omzetcode. Eindstand precies zoals vooraf berekend (x 154, y 95, 3 x vuur), ook met een muis die op een
  willekeurige stand begint. `scherm` en `wacht` slagen nog.
- In VICE (gewone build, 1351 in poort 1): cursor staat stil zonder invoer (160,100, vuur 0); de potmeters
  lezen $40, dus de SID meet poort 1.

**Niet getest:** echte toetsaanslagen en echte muisbewegingen in VICE (toegang tot het VICE-venster geweigerd),
en een echte C64. De band test de omzetcode, niet het lezen van de CIA zelf.

## 2026-11-12 — Hoofdstuk 2: Eldric loopt ✅

**Klaar als:** band met klikken op 3 plekken (één achter een hoek); Eldric komt aan binnen het loopgebied en
kijkt de goede kant op (geheugen + screenshot). **Gehaald**, met 4 klikken.

**Wat er is:**
- `scripts/plein.hcs`: 3 loopvakken (voor, links naar de smidse, rechts omhoog); de fontein ligt ertussen.
  `scripts/spel.hcs`: `BEGIN plein 60,112 VOOR`.
- `tools/scriptc.py` (begin van de compiler): KAMER, LOOPVAK, BEGIN. Controleert: vak binnen de kamer, ≤16
  vakken, alle vakken bereikbaar (overlap), begin in een vak. Onbekende woorden zijn een fout. Proeven met
  een los vak, begin buiten een vak, vak buiten de kamer, onbekend woord en onbekende kamer: alle 5 geweigerd.
- `tools/costume.py`: de 12 poses van Eldric (richting × staan/stap/stap) uit `sprites_hc.py`; voeten op rij 34.
- `src/loopvak.asm`: punt-in-vak, dichtstbijzijnde punt, overlap van twee vakken ("deur"), BFS in de motor.
- `src/actor.asm`: lopen in rechte lijnen (Bresenham), 1 pixel per beeld; via het dichtstbijzijnde punt in
  de deur naar het volgende vak; een pas per 8 beelden; richting volgt de lange as van het laatste stuk.
- Klik in de kamer = "Ga naar" (ook buiten het loopgebied: dan het dichtstbijzijnde punt).

**Beslissingen:**
- Coördinaten in de motor: x in schermpixels (0-319), y in kamerrijen; in de scripts x in multicolor-pixels
  (0-159), zoals het voorbeeld in §6.4. De compiler rekent om.
- BFS draait in de motor, niet vooraf in de compiler: dan kunnen vakken later aan/uit (het pad bij de wolven).
- Alleen Eldric is nu een actor; NPC's als actor komen in hoofdstuk 7. Links wordt (nog) niet gespiegeld via
  een tabel: de 12 poses kosten 1,5 KB en er is ruimte.
- AUTOTEST: zolang vicetest een markering afhandelt staat de hele wereld stil. Zonder dat liep Eldric tussen
  twee controles verder (gemeten: 14 en 20 pasjes) en waren controles onderweg toeval.

**Getest (`tests/lopen.band`):** begin 120,112 voor → links (60,84, kijkt links) → rechts boven om de fontein
heen (220,66, rug) → klik op de fontein (naar 160,96, kijkt links) → voor (160,120, voor). Onderweg: loopt,
5 pasjes na 40 beelden, screenshot met Eldric halverwege een pas. 0 beelden buiten de loopvakken. Alle 6
screenshots pixel voor pixel gelijk aan het geheugen (ook met 3 sprites). De andere 3 tests slagen nog.

**Niet getest:** klikken met echte muis/joystick in VICE (zelfde code als de band, maar het indrukken zelf
niet); naden met meer dan 3 sprites.
