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

## 2026-11-12 — Eldric wordt kleiner op afstand (aanvulling op hoofdstuk 2)

**Gevraagd:** Eldric was te groot voor de deuren. Gekozen voor optie c: vooraan groot, verder weg kleiner.

**Opgemeten** (voet van de deur → hoogte): huizen achteraan y~66 → 14-16 rijen; smidse y~78 → ~20;
herberg y~84 → ~26. Eldric zelf: 34 rijen (haar t/m laarzen).

**Wat er is:**
- `tools/costume.py`: 4 maten per pose (34, 26, 20, 14 rijen) in hetzelfde sprite-vak, voeten op dezelfde rij.
  26 en 20 worden verkleind uit de tekening (kleur met het meeste oppervlak, voorrang voor omlijning en huid;
  kleine maten relatief breder, zoals in pixelkunst). 14 is met de hand getekend (6 x 14, met ogen, handen,
  benen en laarzen): verkleinen gaf daar een klodder. Controle: `build/gen/costume_maten.png`.
- `SCHAAL 104 88 76` in `scripts/plein.hcs` (compiler controleert: aflopend, 1-3 grenzen).
- Motor: maat uit de diepte van de voeten; pose = maat * 12 + richting * 3 + fase (48 poses, 6 KB).
  Op afstand ook trager: maat 2 beweegt in 6 van de 8 beelden, maat 3 in 4 van de 8.

**Getest:** `tests/lopen.band` controleert ook de maat: vooraan 0, links (y 84) 2, achteraan (y 66) 3,
fontein (y 96) 1, vooraan 0. Alle screenshots pixel voor pixel gelijk; 4 van 4 tests geslaagd.
Foute SCHAAL (oplopend) wordt geweigerd.

**Opgemerkt:** de kleine maten staan geheel of grotendeels in de onderste sprite, en die heeft maar één eigen
kleur (blauw): het lichtblauwe harnas wordt daar blauw. Wisselt van maat met een sprong (4 maten); meer maten
kan door MATEN in costume.py en SCHAAL uit te breiden.

## 2026-11-12 — Loopvakken alleen op gras en pad; vuur op spatie/Control

**Gevraagd:** Eldric liep door huizen en door de fontein. Regel: de voeten mogen alleen groen of geel raken.
Achter de fontein langs mag. Vuur niet op Enter (twee handen rechts), maar spatie of linker Control.

**Wat er is:**
- `tools/loopkaart.py`: maakt uit de kamer (zoals de VIC hem toont) een kaart van de loopkleuren; controleert
  een vak (≥ 97% loopkleur, geen gat > 3 pixels op een rij of kolom); `krimp` maakt een fout vak kleiner;
  `--toon` tekent de vakken op de kamer (`build/gen/loopkaart_plein.png`).
- `tools/scriptc.py` controleert elk LOOPVAK op het plaatje en stopt anders, met een kleiner voorstel.
  Nieuw: `LOOPKLEUREN` en `VRIJ x1,y1 x2,y2` (gebied zonder kleurcontrole). De build zet nu eerst de kamers om,
  dan pas de scripts (de compiler heeft het plaatje nodig).
- `scripts/plein.hcs`: 6 nieuwe vakken, met de hand gelegd en door de controle goedgekeurd. Het gras naast de
  herberg is te versnipperd (struik) en doet niet mee. `VRIJ 76,62 81,76`: de witte waterstraal van de fontein
  staat op het gras erachter; daardoor kan Eldric er achterlangs.
- Geheime doorgangen later: geen uitzondering in de motor nodig. De motor kent alleen loopvakken (kleuren niet),
  en een loopvak kan al aan/uit (`lv_aan`); een geheime gang = een vak dat een script aanzet.
- Vuur: SPATIE (rij 7, kolom 4) en CTRL (rij 7, kolom 2; in VICE op de Mac de linker Control) naast RETURN.

**Getest:** `tests/lopen.band` herschreven (6 klikken: links, achter de fontein links via een hoek, achter de
fontein langs door de waterstraal, de fontein zelf, een dak, voor): plek, richting en maat kloppen, 0 beelden
buiten de vakken. `tests/invoer.band`: spatie en ctrl tellen als vuur (5 x). 4 van 4 geslaagd.

**Open:** de gebruiker meldt dat de pijltjes in VICE omgekeerd werken en vuur niet reageert. Een log in VICE
(de matrix uitlezen terwijl de gebruiker drukt) liet omhoog en omlaag correct zien: CRSR ⇓ + rechter SHIFT →
omhoog. Rechts, links en de vuurtoetsen wachten nog op een tweede log. Eldric wordt achter de fontein nog vóór de
waterstraal getekend: voorgrond is hoofdstuk 8.

## 2026-11-12 — Eldric loopt achter het torentje van de fontein (voorgrond, uit hoofdstuk 8 vervroegd)

**Gevraagd:** Eldric liep vóór het torentje langs als hij erachter stond.

**Eerste poging, $d01b (zoals §6.2):** sprite achter bitmapcode %10/%11. Werkte in principe, maar rond het
torentje moest elke achtergrondpixel %00/%01 zijn: per vakje zwart + 1 kleur. Daar zit gras, het gele pad, de
waterdamp en de lichte doorkijk tussen de huizen: het pad en de damp verdwenen, er kwamen zwarte vlekken. Ook
met een kleiner gebied (alleen waar Eldric kan zijn) bleef het zichtbaar slechter. Verworpen.

**Gekozen, voorgrond-sprite:** het torentje is óók sprite 1. Een lager spritenummer komt vóór een hoger, en
Eldric is nu sprite 2-3 (cursor 0). Sprite 1 staat alleen aan als Eldric's voeten in het ACHTER-vak staan
(`ACHTER 72,69 86,75` in `scripts/plein.hcs`); vóór de fontein staat hij uit. `tools/kamer.py` geeft de
torentjes-pixels in de bitmap precies de kleuren van de sprite (zwart + grijs, `KLEUR grijs` in
`data/plein_voorgrond.txt`), dus aan/uit zie je niet. De rest van de kamer houdt al zijn kleuren; alleen het
torentje verliest zijn cyaan randjes. Kost op dit scherm één sprite (er staan hier geen andere figuren).
`VRIJ` uitgebreid naar x 82: achter het torentje staan de voeten op de (verstopte) zuil.

**Ook:** `tools/vicetest.py` tekent nu de sprites mee in het ideale scherm (multicolor/hires, volgorde, $d01b),
in plaats van ze weg te laten. Elke screenshot klopt pixel voor pixel mét cursor en Eldric (pose, maat,
voorgrond). Proef: de sprites in de verkeerde volgorde tekenen → 50 foute pixels achter het torentje: gevonden.

**Getest:** `tests/lopen.band` met een stap precies achter het torentje (act_achter = 1, alleen hoofd en
schouders zichtbaar) en een vóór de fontein (act_achter = 0). 4 van 4 tests geslaagd.

**Open:** er zijn 8 sprites; elke voorgrond kost er één zolang hij aan staat. In kamers met NPC's moet dat
passen (cursor 1 + Eldric 2 + 2 NPC's 4 = 7: één voorgrond tegelijk).

## 2026-11-12 — Vijfde maat: helemaal bovenaan het dorp

**Gevraagd:** bovenaan het dorp mag Eldric nog een maat kleiner.

- Twee nieuwe loopvakken bovenaan, tussen de fontein en de huizen achteraan (`73,65 94,69` en `84,64 94,71`),
  goedgekeurd door de kleurcontrole. Eldric komt nu tot y 64.
- Maat 4: 10 rijen hoog, 4 breed, met de hand getekend (`KLEINST` in `tools/costume.py`), 4 richtingen met pasjes.
  `SCHAAL 104 88 76 69`: onder y 69 de kleinste. Trager: 3 van de 8 beelden. 5 maten x 12 poses = 7,5 KB.
- `ACHTER` loopt nu van y 62: ook bovenaan staat het torentje vóór hem als hij erachter is.

**Getest:** `tests/lopen.band` loopt naar 176,65 (via 3 → 4 → 6), kijkt rechts, maat 4; screenshot pixel voor
pixel gelijk, met sprites. 4 van 4 tests geslaagd.

## 2026-11-12 — Hoofdstuk 3: voorwerpen en zinregel ✅

**Klaar als:** "Bekijk fontein": de juiste tekst staat op rij 0-1 (schermgeheugen lezen). **Gehaald.**

**Wat er is:**
- `tools/scriptc.py`: `VOORWERP naam "naam" VAK x,y b,h LOOP x,y richting` met werkwoordblokken (`BEKIJK:` ...),
  `STANDAARD werkwoord:`, `SPREKER naam kleur`, `ZEG spreker "tekst"`. Teksten naar het eigen lettertype
  (é ë enz.), afgebroken over 2 regels van 40, met de duur erbij (1 s + 1 s per 20 tekens). Controles: te lange
  tekst, teken dat niet in het lettertype zit, onbekende spreker, LOOP-punt buiten een loopvak, naam te lang
  voor de zinregel. Bytecode: `ZEG` en `STOP`.
- `scripts/plein.hcs`: fontein, smidse, herberg, huizen (met teksten); `scripts/spel.hcs`: 10 standaardantwoorden.
- `src/vm.asm` (ZEG, STOP), `src/bericht.asm` (rij 0-1 in de kleur van de spreker, tijd of vuur),
  `src/zin.asm` (voorwerp onder de cursor, zinregel, werkwoord kiezen in geel, klik → loop naar het LOOP-punt →
  kijk → script of standaardantwoord → werkwoord terug naar Ga naar).
- `tools/vicetest.py`: `verwacht_tekst <rij> "..."` leest een tekenrij terug met het eigen lettertype.

**Getest (`tests/bekijk.band`, 24 tussencontroles):** zinregel "Ga naar" / "Ga naar fontein" / "Bekijk" /
"Bekijk fontein"; tijdens de actie blijft de zin staan; Eldric staat op 160,100 met zijn rug naar ons; rij 0-1 =
"Het water is zwart sinds de zon weg is." / "Er glinstert iets op de bodem."; vuur haalt de tekst weg; Duw
fontein → standaardantwoord, dat na 98 beelden vanzelf verdwijnt; Pak fontein (met é); Bekijk herberg loopt naar
de herberg en kijkt rechts. Screenshots pixel voor pixel gelijk. 5 van 5 tests geslaagd.

**Opgemerkt en opgelost:** het klikvak van de fontein besloeg eerst ook het gras erachter: dan werd elke klik
daar "Ga naar fontein" en kon Eldric er niet meer achter. Klikvak = alleen de bak.

**Afspraken van de gebruiker:**
- "Pak fontein" geeft een gouden muntje in de inventaris. Nu alleen de tekst; `GEEF munt` + een vlag (één
  keer) komt met hoofdstuk 4, de inventaris in beeld met hoofdstuk 5. Staat als opmerking in `scripts/plein.hcs`.
- Talen: eerst de Nederlandse versie afmaken; Engels en Frans later als eigen D64 uit dezelfde motor.

**Open:** een vaste letter per werkwoord (§4) is er nog niet; "Wat is" doet bij klikken nog niets extra.

## 2026-11-12 — Hoofdstuk 4: script-VM en compiler ✅

**Klaar als:** scripttests (elke opcode één keer) en fouten die de compiler moet weigeren. **Gehaald.**

**Compiler (`tools/scriptc.py`, herschreven):** de taal staat bovenin het bestand. Nieuw: voorwerpen globaal
genummerd (hooguit 64) met een eigenaar (kamer / Eldric / nergens) en een stand; `BIJ eldric`, `NERGENS`,
`STAND n`; scripts voor twee voorwerpen (`GEBRUIK kruik:` onder het vat = "Gebruik kruik met vat", `GEEF x:`);
`SCRIPT naam:`, `BINNENKOMST:`, `DOEL vlag`; opdrachten ZEG, ALS [NIET] vlag/HEEFT/STAND, ANDERS, EINDE, ZET, WIS,
GEEF, NEEM, PLAATS, STAND, LOOP, KIJK, WACHT, TUSSENSCENE, EINDE_TUSSENSCENE, STOP. Een KAMER mag in een ander
bestand opnieuw geopend worden (testscripts). Uitvoer: `spel.asm`, `spel.json` (namen → nummers voor de tests),
`puzzelstappen.txt`. **Uitspeelbaarheid:** vanaf het begin rekent de compiler uit welke vlaggen en voorwerpen te
krijgen zijn (een script telt als zijn voorwerpen bereikbaar zijn en zijn ALS-voorwaarden te halen); is DOEL
niet te halen, dan stopt de build met de lijst van wat wél kan.

**VM (`src/vm.asm`):** 20 opcodes via een sprongtabel; per beeld lopen opdrachten door tot er een wacht (ZEG,
LOOP, WACHT). Tussenscène: geen invoer, de cursor weg; vuur = overslaan (tekst weg, LOOP meteen klaar, WACHT
voorbij). Spelstatus wordt bij het begin gevuld uit de tabellen van de compiler.

**Het muntje (wens van de gebruiker):** "Pak fontein" → GEEF munt + vlag munt_gepakt; de tweede keer: "Eén is
genoeg. De rest is voor andermans wensen." Eldric begint met zijn zwaard (BIJ eldric).

**Tests:**
- `tests/vm.band` + `tests/scripts/proef.hcs` (alleen in de testbuild): alle opcodes, ook ALS NIET, ANDERS, STOP
  (daarna gebeurt niets), LOOP/KIJK/WACHT, tussenscène overslaan; en het echte "Pak fontein" twee keer.
  33 tussencontroles (nieuw: `verwacht_vlag`, `verwacht_eigenaar`, `verwacht_stand`, `start_script`,
  `wacht_op_script`). GESLAAGD.
- `tools/compilertest.py` + `tests/compiler/*.hcs`: 19 foute scripts (onbekend woord, opdracht buiten een
  script, te lange tekst, teken niet in het lettertype, onbekende spreker/voorwerp/kamer, ALS zonder EINDE,
  ANDERS/EINDE zonder ALS, vlag nergens gezet, DOEL niet te halen, LOOP-punt buiten een loopvak, loopvak niet
  op gras, los loopvak, dubbel voorwerp, te lange naam, werkwoord zonder voorwerp, foute richting): alle 19
  geweigerd met de juiste melding; de echte scripts compileren.
- `./tests/alles.sh` draait alles: 20/20 compiler, 6/6 banden.

## 2026-11-12 — Hoofdstuk 5: inventaris ✅

**Klaar als:** band: pak kruik, gebruik kruik met fontein (standaardantwoord); de inventaris klopt in het geheugen.
**Gehaald** (met een proefkruik op het plein; de echte kruik komt in de herberg, hoofdstuk 6/9).

**Wat er is:**
- `src/inventaris.asm`: lijst van alles met eigenaar Eldric (in scriptvolgorde), rij 22-23 met 2 x 2 namen,
  pijlen ↑ ↓ (wit als je kunt schuiven, grijs als niet), schuiven per 2.
- `src/zin.asm` herschreven: voorwerpen onder de cursor in kamer én inventaris; zinregel met twee voorwerpen
  ("Gebruik kruik met fontein", "Geef kruik aan fontein"); inventaris aanklikken zonder te lopen; Gebruik/Geef met
  iets uit de inventaris wacht op het tweede voorwerp; script eerst bij het tweede voorwerp, bij Gebruik ook
  andersom, anders het standaardantwoord. Voorzetsels in `src/teksten_nl.asm`.

**Getest (`tests/inventaris.band`, 29 tussencontroles):** zwaard in de inventaris bij het begin; Pak kruik →
kruik rechts in de inventaris; Gebruik kruik met fontein → loopt erheen, standaardantwoord; Bekijk zwaard uit de
inventaris zonder te lopen; Gebruik zwaard met kruik én Gebruik kruik met zwaard → beide het eigen script ("Tink.");
Geef kruik aan fontein → standaardantwoord; 6 spullen: pijl omlaag schuift 2, nog eens omlaag kan niet, omhoog
terug. 3 screenshots pixel voor pixel. Alle tests: 20/20 compiler, 7/7 banden.

## 2026-11-13 — Hoofdstuk 6: meer kamers, de diskette en patches ✅

**Klaar als:** band van het plein naar de herberg en terug; laadtijd gemeten en genoteerd. **Gehaald.**

**Wat er is:**
- Vier kamers: plein (FLUX), herberg, smidse, bosrand. Voor die drie zijn er **geen FLUX-plaatjes**: ze zijn
  voorlopig getekend door `tools/maak_kamers.py` (eenvoudige vormen in C64-kleuren) naar `data/plaatjes/`.
  Vervang ze door FLUX-plaatjes; daarna loopvakken en klikvakken aanpassen (de build controleert de loopvakken).
- `tools/kamer.py` maakt per kamer een kamerbestand (`build/gen/kamer_<naam>.prg`, laadadres $A000): ingepakt
  plaatje, voorgrond-sprite, patches (`patch=naam:x,y,b,h:plaatje` in `data/kamers.txt`). Patches: plein
  deur_open, herberg tafel_weg en kruik_weg, smidse vuur_aan.
- `src/schijf.asm`: één laadroutine via de Kernal (SETNAM/SETLFS/LOAD naar $A000). Tijdens het laden:
  raster-IRQ's uit, tekstmodus, kamer leeg, sprites uit, SID stil, "Laden..." in de balk. Laadtijd met de
  TOD-klok van CIA 1 (loopt door zonder IRQ's), in tienden van seconden.
- `src/kamer.asm`: kamer_wissel (laden, plaatje, loopvakken, schaal, voorgrond, BINNENKOMST), patch_zetten.
  Het plein zit niet meer in het programma (scheelt 4,5 KB); het programma moet onder $A000 blijven (assert).
- Compiler: `KAMER naam x,y richting` (opdracht), `PATCH naam`, controles (kamer met plaatje, punt in een
  loopvak, bekende patch). Scripts voor herberg, smidse en bosrand met uitgangen, en de puzzelstukken die geen
  gesprek nodig hebben (tafel duwen → ziensteen, kruik, vat lampolie, smidsvuur → lantaarn van Bram, lantaarn
  vullen en aansteken).

**Gemeten:** laadtijd herberg (4920 bytes, 20 blokken) met echte 1541-emulatie en de Kernal: **14,0 s**
(emulatietijd). Met het virtuele apparaat van VICE: 6,7 s. Een snellader kan later in `laad_kamer`, zonder dat de
rest verandert (§6.7).

**Een fout die de tests eerst níet zagen (en nu wel):** sinds het plein van de diskette komt, laadde het in de
tests niet ("device not present": VICE zonder echte drive heeft `-busdevice8` nodig). Alle tests slaagden toch,
want ze vergeleken het scherm alleen met het geheugen — en een zwarte kamer klopt ook met het geheugen. Nu:
vicetest start met `-busdevice8`, stopt meteen bij een laadfout, en controleert bij elke screenshot dat de
kamerbuffer byte voor byte het kamerbestand van de huidige kamer is.

**Getest (`tests/kamers.band`):** Open herberg (patch), Ga naar herberg (laden 2), Duw tafel (patch, ziensteen
ligt er), terug naar het plein (laden 3, deur nog open), weer naar binnen (tafel nog weg). 5 screenshots pixel
voor pixel + kamerbuffer. Ook met `--echte-drive` geslaagd. Alle tests: 20/20 compiler, 8/8 banden.

**Open:** snellader; FLUX-plaatjes voor herberg, smidse, bosrand; tijdens het laden staat het spel ~14 s stil.

## 2026-11-13 — Hoofdstuk 7: praten ✅

**Klaar als:** band: het hele gesprek, met de juiste vlag aan het eind. **Gehaald.**

**Werkwijze-opmerking:** de app MacAIMagic werkt sinds 23:23 in `~/Development/Hollow_Crown` op een eigen branch
(`docs/script-walkthrough`, een verhaal-/walkthroughdocument). Mijn commit van hoofdstuk 6 kwam daardoor eerst
op die branch, mét hun document. Hersteld: hoofdstuk 6 opnieuw op main gezet zonder hun bestand, hun branch
teruggezet (hun document weer niet vastgelegd, verder onaangeroerd). Ik werk sindsdien in een eigen worktree:
`~/Development/Hollow_Crown_motor` (branch main). Hun document heb ik niet gebruikt: hoofdstuk 1 volgt de prompt.

**Wat er is:**
- `tools/costume.py`: NPC-kostuums (mira, vex, wolf) + `build/gen/kostuums.json`.
- Compiler: `ACTOR naam KOSTUUM k OP x,y [VERBORGEN]`, `GESPREK naam` met `KEUZE "zin" [ALS [NIET] vlag/HEEFT]
  [EINDE]`, opdrachten `PRAAT`, `TOON`, `VERBERG`, `LOOP figuur x,y`. Controles: kostuum bestaat, hooguit 2
  figuren per kamer, elk gesprek heeft een uitweg (EINDE), keuzetekst op één regel. Uitspeelbaarheid rekent
  gesprekken mee (een keuze telt pas als het gesprek ergens begint); "Gebruik/Geef X" telt pas als je X hebt.
- `src/npc.asm`: twee slots (sprite 4-5, 6-7), zichtbaarheid in de spelstatus, rechte lijn lopen.
- `src/gesprek.asm`: keuzes op rij 19-22 (alleen die waarvan de voorwaarde klopt), gele keuze onder de cursor,
  na een keuze terug naar de keuzes of (EINDE) terug naar werkwoorden en inventaris.
- Mira (herberg): BEKIJK, PRAAT (gesprek met 4 keuzes), GEEF ziensteen (→ ziensteen_terug, hint_wolven),
  GEEF munt. Bosrand: een schaduwwolf en Vex (verborgen, voor de tussenscène).

**Getest (`tests/gesprek.band`, 26 tussencontroles):** Praat met Mira → 3 keuzes; keuze 2 → hint over de tafel,
vlag mira_zoekt; keuze 1; keuze 3 (EINDE) → werkwoorden en inventaris terug; Duw tafel, Pak ziensteen, Geef
ziensteen aan Mira → ziensteen weg, vlaggen ziensteen_terug en hint_wolven; opnieuw praten → keuze 2 is nu "Hoe
kom ik langs de wolven?". 3 screenshots pixel voor pixel. Alle tests: 20/20 compiler, 9/9 banden.

## 2026-11-13 — Hoofdstuk 8: voorgrond en kleine animaties ✅

**Klaar als:** screenshot: Eldric half achter de fontein. **Gehaald** (de voorgrond-sprite van eerder; nu ook als
eigen test met act_achter = 1 en maat 3).

**Kleine animaties:** `FLAKKER x,y b,h kleur kleur ...` per kamer (hooguit 2). `src/flakker.asm` laat elke 6 beelden
in die vakjes elke kleur uit de rij de volgende worden, in alle drie de kleurplekken (scherm-RAM hoog/laag,
kleur-RAM). Vuur: rood → oranje → geel. Het haardvuur in de herberg flakkert altijd; het smidsvuur ook, maar
zolang het uit is staat er alleen grijs in die vakjes en verandert er niets — geen extra voorwaarde nodig.

**Getest (`tests/voorgrond.band`):** Eldric achter het torentje (screenshot pixel voor pixel); in de herberg drie
keer: de kleur van een haardvakje is precies zoveel plekken in de rij opgeschoven als er flakkerstappen waren
(de motor telt ze: fl_stappen). Eerst controleerde de test "één stap verder" en faalde soms: tussen twee
controles zaten soms 2 stappen. Nu exact. Alle tests: 20/20 compiler, 10/10 banden.

## 2026-11-13 — Hoofdstuk 9: hoofdstuk 1 helemaal speelbaar ✅

**Klaar als:** band met de volledige oplossing eindigt op "Hoofdstuk 1 voltooid"; band die halverwege opslaat,
laadt en verdergaat. **Beide gehaald.**

**Geluid (`src/geluid.asm`):** effecten op stem 3 (stem 1 en 2 blijven voor de muziek van hoofdstuk 10). Een
effect = golfvorm, ADSR, beginfrequentie, frequentiestap per beeld, pulsbreedte en duur; `geluid_beeld` draait in
de IRQ op de onderrand. Nieuwe opdracht `GELUID naam` (opcode $1A; deur munt vuur wolf klaar klik). Gebruikt bij
de herbergdeur, de munt uit de fontein, het smidsvuur, de wolven; "klaar" klinkt bij het einde van het hoofdstuk.
Tijdens het laden is de SID stil (volume 0), daarna weer aan.

**Opslaan/laden (`src/opslaan.asm`):** F5 slaat op, F7 laadt (alleen als er geen script, gesprek of lopen bezig is).
Opslaan: eerst `S0:HCSAVE` scratchen via kanaal 15, dan SAVE van het spelstatusblok (183 bytes) — nooit `@0:`.
Laden: naar een aparte buffer; alleen met magic "HC" en de juiste versie wordt het de spelstatus, dan naar de
opgeslagen kamer en plek. Geen opgeslagen spel → een melding, er verandert niets. Na opslaan staat dezelfde kamer
er weer (plaatje uit de kamerbuffer, BINNENKOMST zet de patches terug). Meldingen in Eldrics kleur op rij 0-1.

**Finale (bosrand):** "Gebruik lantaarn met wolven" met een brandende lantaarn → tussenscène: de wolf loopt weg,
Baron Vex verschijnt tussen de bomen, praat, en verdwijnt het bos in. Vlaggen wolven_weg en hoofdstuk1_klaar
(`DOEL hoofdstuk1_klaar` in spel.hcs; de compiler bevestigt: te halen). De motor toont dan onderaan "Hoofdstuk 1
voltooid" in geel. Wolven/pad reageren daarna anders.

**Gevonden fouten:**
- Figuurslot 1 (sprite 6-7) kreeg zijn kostuum op $C600 i.p.v. $C500 (carry telde dubbel): Vex was een
  rood-wit gestreept blok. Tot nu toe stond er nooit een tweede figuur in een kamer. Nu een tabel, en de
  oplossingsband controleert Vex in slot 1 en vergelijkt het scherm pixel voor pixel (met sprites).
- De spelstatus kopiëren met `ldx #182 ... dex / bpl` stopt meteen (182 is "negatief"): laden zette maar één byte
  terug. Nu optellend. De opslaanband vond dit.
- De testdiskette: opslaan schrijft op de D64. vicetest werkt nu per band op een eigen kopie (build/test/<band>.d64),
  zodat een test geen HCSAVE achterlaat voor de volgende. Toetsen f1/f5/f7 erbij in de banden.

**Getest:** `tests/oplossing.band` (37 tussencontroles: herberg open, kruik pakken en vullen, smidsvuur aan →
lantaarn, olie erin, aansteken, naar de bosrand, de tussenscène met Vex, "Hoofdstuk 1 voltooid", geluid "klaar").
`tests/opslaan.band` (28: F7 zonder opslag, munt, F5, verder naar de herberg, F7 → terug bij de fontein met de munt
en de deur dicht, verder spelen, nog eens F5 → er blijft één HCSAVE op de diskette, nagekeken met c1541).
Alle tests: 21/21 compiler, 12/12 banden.

**Nog open:** de geluiden zijn alleen op registerniveau getest (welk effect, volume), niet beluisterd. Op een
echte 1541 duurt opslaan/laden net als een kamer enkele seconden (Kernal; geen snellader).

## 2026-11-13 — Hoofdstuk 10: het intro ✅

**Klaar als:** intro → spel start; muziek speelt (SID-registers veranderen volgens de noten); geen hangende toon na
het intro. **Gehaald.**

**Het beeld (`src/intro.asm`):**
- Titelplaatje met FLUX (`data/flux/titel.png`, gekozen uit 3 versies): een gebroken gouden kroon boven een donker
  kasteel met één verlicht raam, Eldric als silhouet. Het is een "kamer" in `data/kamers.txt` (bestand TITEL op de
  diskette), dus dezelfde omzetter, hetzelfde laden en dezelfde rastersplit als het spel.
- Logo HOLLOW CROWN in een eigen logo-lettertype (`tools/logo.py`): letters van 10 x 12 blokjes van 2 x 2 pixels,
  met een zwarte "chroom"-snede; 46 tegels als tekens $80-$AD in het lettertype op $F800 (het spel gebruikt alleen
  codes onder $80). Kleurenloop: elke 3 beelden schuift een rij van 16 kleuren (goud/vuur, dan zilver) een kolom op.
- Scrolltekst op rij 24 met het verhaal, de bediening en de makers: vloeiend (1 pixel per beeld) met een extra
  raster-IRQ op lijn 241 die XSCROLL zet in 38-kolommenmodus; de onderrand zet hem terug. Alleen tijdens het intro.
- Spatie of vuur start het spel: muziek stil, de SID helemaal leeg, de IRQ's zoals in het spel, de cursor terug.

**De muziek (`tools/thema.py`, `src/muziek.asm`):** een eigen thema in D-mineur, 16 maten op 100 slagen per minuut
(38,4 s, dan opnieuw). Stem 1 melodie (puls met langzame pulsbreedte-modulatie), stem 2 bas (zaagtand: grondtoon,
kwint, octaaf), stem 3 akkoorden als arpeggio (elke 2 beelden een toon). Akkoorden: Dm Bb C Am Dm Gm A A | Bb F Gm
Dm Bb C A Dm; de A groot (C#, harmonisch mineur) trekt telkens terug naar D. Eigen kleine speler in de IRQ op de
onderrand. Stem 3 wijkt voor een geluidseffect (geluid.asm), dus effecten en muziek gaan samen.
Het thema keert terug in de herberg (`MUZIEK thema` in BINNENKOMST; nieuwe opdracht `MUZIEK thema|stil`, opcode
$1B). Bij het laden van een kamer stopt de muziek. F1 zet de muziek uit en aan (in het intro en in het spel).

**Getest zonder oren:** de SID kun je niet teruglezen, dus de speler houdt bij wat hij schreef (muz_flo/fhi/ctrl).
`verwacht_muziek` in vicetest rekent uit `build/gen/muziek.json` uit welke noot er op dit beeld moet klinken (en
of de gate aan of uit moet: uit in het laatste beeld van een noot en in rusten; voor het arpeggio welke toon van
het akkoord) en vergelijkt. Tijdens een controle staat de muziek stil (AUTOTEST), zodat het een echte momentopname
is. `tests/intro.band`: titel, logo (kleurenloop in alle 120 logovakjes), 7 muziekcontroles over 400 beelden, de
scrolltekst, F1 uit (alle gates 0) en weer aan (van voren af), spatie → het plein, geen gate meer aan.
`tests/kamers.band`: het thema speelt in de herberg en stopt op het plein.
Daarnaast met oren (van de computer): VICE opgenomen als WAV (echte build, zonder warp) en met
`tools/muziek.py luister` de toonhoogtes eruit gehaald: D5 F5 A5 | Bb5 A5 G5 F5 | E5 G5 E5 | A4, met de bas
D2 A2 D3 | Bb1 F2 Bb2 ... — precies het thema.

**In AUTOTEST-builds** draait het intro alleen als een band met `intro` begint (nieuwe bandopcode $0A); alle andere
banden beginnen dus nog steeds direct in het spel.

**Verhaal rechtgetrokken:** de scrolltekst en Vex volgen nu het verhaal van de README (de Holle Koning stal het
zonlicht; Eldric draagt het laatste lichtfragment; Vex dient de Holle Koning).

**Getest:** 22/22 compiler, 13/13 banden.

**Nog open (voor later):** het thema "bij de titel van elk hoofdstuk" (er is nu één hoofdstuk); een snellader
(laden via de Kernal duurt op een echte 1541 ~14 s per kamer); FLUX-plaatjes voor herberg, smidse en bosrand;
invoer op echte hardware (joystick, 1351-muis, toetsenbord) is alleen in VICE getest; Engels en Frans als aparte D64.

## 2026-11-13 — FLUX-plaatjes: de herberg ✅

De voorlopige herberg is opnieuw getekend in de stijl van het plein, met behoud van de indeling en de verhoudingen
(Eldric naast de deur klopt). Eerst nieuwe FLUX-plaatjes zonder voorbeeld geprobeerd: mooi, maar de verhouding
klopte niet (meubels veel te groot voor Eldric). Wat werkte: FLUX.2 met twee referentiebeelden, ons eigen plaatje
(de indeling) en het plein (de stijl), met "Redraw the first image in exactly the art style of the second image,
keep the composition". `--init` met `--sterkte` doet niets bij dit model (0,55 en 0,65 gaven hetzelfde beeld).

- `docs/FLUX_PROMPT.md`: de vaste prompt (stijl, camera, uitsnede, schaal) en hoe je een plaatje maakt.
- `tools/flux.py`: `--ref` (referentiebeeld, mag vaker), `--init`, `--masker`, `--sterkte`.
- `tools/flux_patches.py herberg`: van `herberg_bron.png` (zoals FLUX hem maakte) naar het kamerplaatje (de kruik
  grijs steengoed, zodat hij op de bruine muur zichtbaar blijft) en de twee patches, gemaakt uit het plaatje zelf:
  zonder kruik (de muur erboven doorgetrokken) en de tafel opzij (vloer per rij aangevuld, met het licht van het vuur
  per kolom) met de ziensteen waar hij stond. Zo passen de patches pixel voor pixel.
- Omzetten: `boven=115 kleur=1.5 licht=1.0 sterkte=0` (geen menging: vlakke kleuren, zoals het plein).
- `tools/loopkaart.py`: een lijn van 1 pixel hoog met vloer erboven en eronder telt als vloer (de voegen tussen de
  planken). Een tafelpoot of kruk is hoger en telt nog steeds niet.
- herberg.hcs: nieuwe loopvakken (om de tafel heen, niet door de oven), klikvakken; Mira staat nu bij de toog
  (bij de haard stond ze voor de deur). `tests/gesprek.band`: Mira op cursor 264,100.

**Getest:** 22/22 compiler, 13/13 banden (oplossing, kamers, gesprek en opslaan lopen door de nieuwe herberg).
Volgende: de smidse en de bosrand, op dezelfde manier.

**Hernoemd (2026-11-13):** de kamer heet nu overal "smit" in plaats van "smidse" (scripts/smit.hcs, KAMER smit,
bestand SMIT op de diskette, data/plaatjes/smit*.png, tests). Op verzoek van de gebruiker.

## 2026-11-13 — Hoofdstuk 1 volgens het scenario (deel 1)

Het scenario van MacAIMagic (`~/Development/Hollow_Crown/docs/SCRIPT_HOLLOW_CROWN.md`, nog niet vastgelegd op hun
branch) is nu leidend voor hoofdstuk 1. Afgesproken met de gebruiker: de kelder komt er nu bij, de verhaalanimatie
na het titelscherm wordt één toneel met spriteanimatie, en Mira komt aan het eind erbij (motor uitgebreid).

- Teksten: fontein ("Het water is zwart sinds de zon weg is. Er glimt iets."), Mira ("De steen is warm. Hij is
  altijd warm. Rare steen."), Bram ("Vuur uit, lantaarn leeg, hoofd vol.").
- Nieuw voorwerp **vuursteen**: Geef munt aan Bram (als het vuur brandt) → vuursteen (nodig in hoofdstuk 4).
- **Figuren krijgen een slot bij TOON** (`npc_toon`/`npc_verberg` in npc.asm): VERBERG maakt het slot vrij. Een kamer
  mag nu meer figuren hebben, er staan er hooguit 2 tegelijk (de compiler telt de zichtbare bij binnenkomst; is er
  bij TOON geen slot vrij, dan vm_fout = $FE).
- **Finale bosrand**: de wolf vlucht, Vex fluistert "Kom maar, Wachter. Ik heb een kroon voor je." en verdwijnt,
  Mira komt aanlopen: "Het pad vraagt om mij." Ze reist mee (in de herberg is ze weg). De oplossingsband controleert
  Vex en daarna Mira in het vrijgekomen slot, met screenshots pixel voor pixel.

**Getest:** 22/22 compiler, 13/13 banden.

## 2026-11-13 — De kelder (scenario hoofdstuk 1)

- Eigen voorlopig plaatje (`maak_kamers.py kelder()`, trap links, vat met kraan, planken met de honingpot, rooster,
  kisten), daarna FLUX in de stijl van het plein (2 referentiebeelden); de gebruiker koos versie 2.
- `tools/flux_patches.py kelder`: `kelder_bron.png` → `kelder.png` en `kelder_zonder_honingpot.png` (de bakstenen
  muur van ernaast op de plek van de pot). Patch `honingpot_weg:140,40,16,16`.
- `scripts/kelder.hcs`: trap (terug naar de herberg), vat lampolie (Gebruik kruik met vat), honingpot (Pak; "Voor
  de bijen die er niet meer zijn."), planken, kisten, raampje. LOOPKLEUREN oranje bruin rood (rood: een vlek olie).
- Herberg: een luik rechtsvoor in de vloer (getekend in `flux_patches.py herberg`, licht hout met ijzeren banden; de
  randen donkerbruin zodat de loopvakcontrole klopt). Het vat in de herberg is nu een leeg biervat.
- De honingpot komt in de inventaris vóór het zwaard (kelder.hcs vóór spel.hcs): de oplossingsband is daarop aangepast
  en loopt nu via de kelder.

**Getest:** 22/22 compiler, 13/13 banden.

## 2026-11-13 — De bosrand als FLUX-plaatje, met drie wolven

- FLUX in de stijl van het plein uit ons eigen voorlopige plaatje (2 referentiebeelden). De donkere boomkruinen
  werden bij het omzetten zwart; met `kleur=1.8 licht=1.4` blijven ze grijs, blauw en groen.
- Drie schaduwwolven (scenario): de figuur `wolf` op het pad, en twee wolven in het plaatje zelf, pixel voor pixel uit
  dezelfde tekening als de figuur (`tools/flux_patches.py bosrand`, de rechter gespiegeld). De patch `wolven_weg`
  (24,72,88,24) is het FLUX-plaatje zonder wolven; bij de lantaarn vluchten ze alle drie.
- bosrand.hcs: nieuwe loopvakken (het gras begint lager), klikvakken, SCHAAL 104 94, BINNENKOMST zet de patch terug.

**Getest:** 22/22 compiler, 13/13 banden. Alle vijf kamers zijn nu FLUX-plaatjes in dezelfde stijl, behalve de smit.

## 2026-11-13 — De verhaalanimatie na het titelscherm

Na het titelscherm (spatie of vuur) vertelt één toneel het verhaal zoals het volk het kent (scenario: de waarheid
komt later), geïnspireerd op het openingsfilmpje van de oude avonturen, met eigen beeld en eigen verhaal.

- **Het toneel is met de hand getekend** (`tools/teken_toneel.py`), niet met FLUX: de FLUX-versies pasten niet bij de
  sfeer van het dorp (kaal, geen bomen). Rechtstreeks in 160 x 128 kamerpixels, alleen C64-kleuren (het palet van de
  omzetter, zoals VICE ze toont), dikke zwarte lijnen. Het script telt de vakjes van 4 x 8 met meer dan 3 kleuren +
  zwart (nu 42 van 640). `tools/kamer.py` kreeg `exact=1`: een plaatje dat al in C64-kleuren staat niet oprekken of
  verzadigen (anders werd cyaan grijs en groen lichtgroen).
- **De scènes** (`scripts/verhaal.hcs`): de Eeuwige Zon; twee manen schuiven voor de zon (dubbele
  maansverduistering) terwijl de lucht met KLEUR van cyaan via lichtblauw en blauw naar het paars van het plein gaat en
  de zon dooft; twee Holen klimmen uit de Rotskloof; Vex bij het kasteel ("De Holle Koning stal jullie zon! Alleen ik
  kan jullie beschermen."); Eldric loopt het pad op. Daarna naar het plein. Het thema speelt mee. Vuur slaat over.
- **Motor:** kamerinstelling `TONEEL` (geen Eldric, cursor, balk; `src/toneel.asm`), opdracht `KLEUR x,y b,h van naar`
  (opcode $1C: een kleur wisselen in scherm- en kleur-RAM), `TOON eldric` / `VERBERG eldric`, en `VERHAAL kamer x,y
  richting` in spel.hcs (na het titelscherm eerst daarheen). Nieuwe figuren: maan en Hol (tools/sprites_hc.py).
- In een AUTOTEST-build alleen als de band met `intro` begint, net als het titelscherm.
- `tools/flux.py`: vindt de engine ook als de app niet draait; met sommige zaden faalt de engine meteen: dan een
  ander zaad.

**Getest:** `tests/verhaal.band` (de scènes, manen en Holen in de figuurslots, alle 7 kleurwissels, daarna het plein
met balk, inventaris en cursor terug; screenshots pixel voor pixel met de sprites), `tests/intro.band` (vuur slaat
het verhaal over, geen hangende toon). 23/23 compiler, 14/14 banden.

**Logo (2026-11-13):** de bovenste pixelrij van HOLLOW CROWN gaf een witte streep: rij 18 begint op de rasterlijn waar de
IRQ van bitmap naar tekst schakelt (lijn 195), en het logo gebruikt alle 8 pixelrijen. Het logo staat nu op rij 19-21,
rij 18 blijft leeg.

## 2026-11-13 — Verbeteringen aan het toneel (na de eerste keer kijken)

- De zon is helemaal geel gevuld (geen wit gat), met een klein glimlicht en schaduw rechtsonder.
- De kasteelpoort: een boog met houten deuren die op de voet van de muur eindigt (was een zwarte ovaal die in het gras
  uitstak), en een pad de heuvel af.
- Vex was moeilijk te zien voor het grijze kasteel: nu komt hij na een flits uit de poort en loopt de heuvel af tot hij
  tegen het groene gras staat, met de Lichte Kroon (eigen kostuum vex_kroon: boven goud, onder donkergrijs).

## 2026-11-13 — De smit opnieuw: zelf getekend, Bram als figuur

- `tools/teken_smit.py`: de smit met de hand getekend als C64-pixelart, in de sfeer van het plein: stenen smidsvuur met
  kap en schoorsteen, blaasbalg, gereedschap en hoefijzers aan de muur, houten palen, een schild met twee zwaarden,
  raampje met schemer, deur, aambeeld op een boomstronk, watervat, warm licht van het vuur op de aarden vloer. Ook
  smit_vuur.png (vlammentongen) voor de patch vuur_aan (64,56,32,16).
- In de koude haard gloeien een paar kolen (rood/oranje): FLAKKER laat ze zacht nagloeien; aan flakkeren de vlammen.
- Bram is geen deel van het plaatje meer (dat leek een stoel) maar een figuur: rode baard, blote armen, leren schort,
  hamer (tools/sprites_hc.py bram). Nieuwe voorwerpen: blaasbalg, gereedschap, schild.
- vicetest: `verwacht_slot 0 bram` (de figuur bij naam, niet bij nummer: nummers verschuiven als er figuren bijkomen).
- LOOPKLEUREN smit: ook geel, grijs, donkergrijs (stro, steentjes, een hoefijzer op de vloer: je loopt eroverheen).

**Getest:** de oplossingsband maakt nu screenshots in de smit (koud en met vuur), pixel voor pixel met Bram. 23/23, 14/14.

## 2026-11-13 — Muziek per plek

`tools/thema.py` is nu een muziekboekje met zes eigen stukken; aan de muziek hoor je waar je bent:
- **thema** (titel, verhaal): episch, D-mineur (zoals eerst).
- **plein**: vrolijk dorpsdeuntje, G-groot, 6/8, een fluitje (driehoek), 16 maten.
- **herberg**: zachte, speelse wals in F-groot: bas op 1, "pah-pah" op 2 en 3, lage sustain (zachter).
- **kelder**: geheimzinnig, A-mineur, langzaam; af en toe een hoge "druppel".
- **smit**: stoer en ritmisch, D-dorisch; hamerslagen met ruis op 1 en 3.
- **bosrand**: spannend, E-mineur; een kloppende lage bas, een trillend akkoord, een trage dreigende melodie.

De speler (`src/muziek.asm`) neemt per stuk de klank van elke stem over (golfvorm, ADSR, pulsbreedte) en weet of
stem 3 akkoorden als arpeggio speelt of gewone noten. `MUZIEK naam` in BINNENKOMST van elke kamer (opcode $1B: 0 =
stil, n = stuk n-1). vicetest `verwacht_muziek` leest welk stuk speelt (muz_lied) en controleert dat noot voor noot.

**Getest:** in elke kamer het juiste stuk, noot voor noot (kamers, oplossing, intro). Nog niet met oren beluisterd
(de WAV-opname werkt alleen zonder warp en het titelscherm wacht op een toets).

## 2026-11-13 — Menubalk, lichtpunten, baas-toets en Exit

- **Menubalk** (`src/menu.asm`): komt de cursor in rij 0-1 (en praat er niemand, loopt er geen script, gesprek of
  toneel), dan staat daar **Bestand – Score – Bosskey**; het woord onder de cursor licht geel op. Bestand opent in rij 1
  **Opslaan – Laden – Exit**; Score toont "Lichtpunten: 25 van 250". Een klik in de balk is voor het menu.
- **Lichtpunten**: opcode `PUNTEN n` ($1D), `st_score` in de spelstatus (STATUS_VERSIE 2: oude opslag laadt niet meer).
  Hoofdstuk 1 heeft er 100: munt 5, kruik 5, ziensteen gevonden 10, ziensteen terug 10, honingpot 5, smidsvuur 15,
  vuursteen 5, olie in de lantaarn 10, lantaarn aan 10, wolven verjaagd 25. Alleen waar iets één keer kan; olie in een
  lantaarn die al olie heeft kan niet meer (dat doofde hem eerst weer).
- **Bosskey** (`src/baas.asm`, `tools/baas.py`): het hele scherm wordt tekst (de IRQ schakelt niet meer naar de
  bitmap), witte achtergrond, een rekenblad met een begroting; geen sprites, muziek stil. Een toets/stick/muisknop:
  het spel komt precies terug (plaatje uit de kamerbuffer, BINNENKOMST, balk). Nieuw teken `|` in het lettertype.
- **Exit** (`src/basic.asm`): raster-IRQ uit, SID stil, ROM's aan, dan IOINIT, RESTOR, CINT van de Kernal en de warme
  start van BASIC: READY. (RUN start het spel opnieuw.) De reset als terugval was niet nodig.
- **Geheugen**: het programma paste niet meer onder $A000. Het rekenblad (1000 → 694 bytes) en het lettertype
  (2048 → 673 bytes) staan nu ingepakt in het programma en worden bij gebruik uitgepakt.

**Getest:** `tests/menu.band` (balk verschijnt en verdwijnt, opslaan via het menu, score 0 en na de munt 5, het
rekenblad en terug: scherm pixel voor pixel), `tests/basic.band` (Exit: READY. op het BASIC-scherm, ROM's aan).
23/23 compiler, 16/16 banden.

## 2026-11-13 — Het verhaal opnieuw: Grom de tovertrol, Eldric een gewone jongen

Afgesproken met de gebruiker; het scenario (`~/Development/Hollow_Crown/docs/SCRIPT_HOLLOW_CROWN.md`, van MacAIMagic)
is daarop aangepast (niet vastgelegd: hun bestand, hun branch; een kopie van de oude versie staat in de scratchpad).
- **Grom de tovertrol** (geen koning) sprak in de nacht van de dubbele maansverduistering de Schemerspreuk: het zonlicht
  zit in de Holle Kroon, zodat zijn volk, de **aardmannetjes** (die geen licht verdragen), boven de grond kan leven.
  Hij is niet slecht om het slecht zijn; aan het eind wordt hij een bondgenoot. Baron Vex valt weg.
- **Eldric** is een gewone jongen met een goed hart, geen Wachter. Hij draagt geen zwaard maar de **zonnesteen** van
  zijn oma ("Er zit nog een beetje zon in, zei ze."). Bram en Mira noemen hem "jongen".
- Hoofdstuk 1: het zwaard is de zonnesteen geworden (scripts en tests); aan de bosrand verschijnt Grom na de wolven:
  "Een jongen met een stukje zon in zijn hand... Interessant. Heel interessant." Nieuwe figuur `grom`
  (tools/sprites_hc.py); de kostuums van Vex zijn eruit.
- **Het toneel opnieuw getekend**, minder klinisch: links een bos en een molentje op de heuvels, in het dal Dawnhaven
  met scheve vakwerkhuisjes, rechts Groms rotsige berg met een grot (rotsvlakken licht/schaduw, barsten, oogjes in het
  donker), een slingerend pad door de wei. Het verhaal: aardmannetje bij de grot, Grom, de spreuk (flits), de manen,
  de schemer, de aardmannetjes komen naar boven, Eldric. Ook de scrolltekst van het titelscherm.
- **Binnen geen diepte meer**: in de herberg, kelder en smit blijft Eldric overal even groot (de grootste maat; geen
  SCHAAL). Buiten (plein, bosrand) wel.
- **De bosrand had geen zichtbare uitgang**: het "dorp" was een onzichtbaar vakje in de hoek rechtsonder. Nu is het
  gele pad onderaan (waar je vandaan komt) de weg terug. Nieuwe band `tests/bos_terug.band`.

**Getest:** 23/23 compiler, 17/17 banden.

**Toneel (2026-11-13):** Eldric draait zich aan het eind van het verhaal om naar het publiek (KIJK eldric VOOR); hij
stond met zijn rug naar je toe. De zon in de schemer was niet helemaal gevuld: het witte glimlicht maakte van één
vakje van 4 x 8 vier kleuren (lucht, geel, oranje, wit), de omzetter liet er een weg en dat werd later paars. Het
glimlicht is eruit, en de kleurwissels van de zon gelden nu ook voor de punten van de stralen (x 60-99).

## 2026-11-13 — Ziensteen weg na Pak, nette terugkeer van de baas-toets, tests zonder venster

- **De ziensteen bleef op de vloer liggen** na Pak: de patch tafel_weg tekent hem. Nu een kleine patch `steen_weg`
  (56,96,12,16; `herberg_zonder_steen.png`) bij Pak ziensteen en in BINNENKOMST (na tafel_weg). Daarbij
  `tools/flux_patches.py` opgeruimd: er stonden twee versies van tafel_weg in (Python nam de laatste, zonder de
  lichtcorrectie van de vloer); nu één, met de lichtcorrectie, met of zonder steen.
- **Terug van het rekenblad was het scherm even rommel** (de letters van het rekenblad als kleuren, tot de kamer weer
  uitgepakt was). Nu gaat het beeld eerst op zwart (`scherm_uit`: de IRQ's schrijven $d011 uit twee variabelen,
  bit 4 uit), wordt alles hersteld, en pas als BINNENKOMST klaar is gaat het beeld weer aan.
- **De tests draaien VICE zonder venster** (`-console`): ze pakken de focus niet meer af en na afloop spring je niet
  meer naar het bureaublad. De screenshots werken gewoon (pixel voor pixel). Met `--houd-open` krijg je het venster.

**Getest:** gesprek.band (Pak ziensteen, opzij lopen, screenshot: de vloer is leeg), menu.band (scherm_uit_teller = 1
bij de terugkeer, daarna weer aan). 23/23 compiler, 17/17 banden.

## 2026-11-13 — Eén map: ~/Development/hollow_crown64

Alles staat nu in één map, `~/Development/hollow_crown64` (dezelfde naam als de repository op GitHub), met een eigen
git-kopie op branch main. De oude gedeelde map `~/Development/Hollow_Crown` (waar ook MacAIMagic werkte, met een eigen
branch) is naar de prullenbak; daar stond niets meer dat niet ook hier of op GitHub staat. Het scenario staat in
`docs/SCRIPT_HOLLOW_CROWN.md` (met Grom, de aardmannetjes en de zonnesteen). Verwijzingen hierboven naar
`Hollow_Crown` en `Hollow_Crown_motor` zijn geschiedenis.

## 2026-11-13 — Slimme zinregel

Het voorwerp waar de cursor even op bleef staan (10 beelden, 0,2 s: zo telt een voorwerp waar je alleen overheen
schiet niet) wordt onthouden. Kies je daarna een werkwoord, dan staat dat voorwerp er al achter ("Pak kruik"); klik je
nog eens op hetzelfde werkwoord, dan wordt de zin uitgevoerd. Een ander voorwerp aanwijzen gaat gewoon voor. Bij
Gebruik/Geef met iets uit de inventaris wordt het het eerste deel ("Gebruik zonnesteen met ..."). Bij een andere kamer
is het onthouden voorwerp vergeten (`src/zin.asm`: onthouden, laatst_geldig, vergeet_laatst).

**Getest:** `tests/slim.band` (Bekijk fontein via het onthouden voorwerp, een ander voorwerp gaat voor, Gebruik
zonnesteen met fontein); `tests/bekijk.band` aangepast (na het kiezen van Bekijk staat de fontein er al achter).
23/23 compiler, 18/18 banden.

## 2026-11-13 — Scripts per kamer van de diskette (ruimte voor hoofdstuk 2 en verder)

Het geheugen onder de kamerbuffer was op (nog ~800 bytes vrij in de testversie); alleen de scripts en teksten van
hoofdstuk 1 waren al ruim 9 KB. Nu werkt het zoals de oude avonturen: **de scripts van een kamer worden met die kamer
van de diskette geladen**, als tweede bestand `<kamer>.s`, op `KAMER_SCRIPTS` ($B400-$BFFF). Het plaatje van een
kamer (met patches) moet daarom onder $B400 blijven (5 KB; tools/kamer.py controleert dat).

- `tools/scriptc.py` verdeelt alles over segmenten: een voorwerp dat in een kamer begint en nooit verplaatst wordt
  (geen GEEF/NEEM/PLAATS), hoort bij die kamer: zijn naam, scripts en teksten gaan in segment `Kamer_<naam>`. Ook
  BINNENKOMST, en een gesprek dat alleen vanuit één kamer begint. Wat je kunt meenemen, standaardantwoorden en losse
  scripts blijven vast in het geheugen. Kick Assembler schrijft elk segment naar `scr_<kamer>.prg`; build.sh zet die
  op de diskette als `<kamer>.s`.
- `src/schijf.asm` laadt na het plaatje het scriptbestand (laad_fout = 2 als het ontbreekt).
- Resultaat: het hoofdprogramma van 137 naar 109 blokken; vrij onder $A000 nu ~10 KB in plaats van 0,8 KB.

Later, als de diskette vol raakt (rond 25 kamers): meerdere diskettes ("Plaats diskette 2"); met elke kamer en zijn
scripts als eigen bestanden is dat eenvoudig.

**Getest:** 23/23 compiler, 18/18 banden (de oplossingsband speelt alle kamers met hun scripts van de diskette).

## 2026-11-13 — Motor voor hoofdstuk 2: hoofdstukken, Tik, Mira loopt mee

- **Hoofdstukken**: in spel.hcs `HOOFDSTUK n "naam" doelvlag` (1 Dawnhaven, 2 Duisterwoud). De titel onderaan en
  "Hoofdstuk n voltooid" komen uit een tabel; `st_hoofdstuk` staat in de spelstatus (STATUS_VERSIE 3). In een script
  begint `HOOFDSTUK n` het hoofdstuk (opcode $1E).
- **Tik en terugdraaien**: bij binnenkomst van elke kamer bewaart de motor een kopie van de spelstatus (het
  ankerpunt, `src/terug.asm`). `TERUG` (opcode $1F) zet alles terug en begint de kamer opnieuw zonder te laden.
  Tik is een figuur die overal mee kan (wit eitje met één oog); na een dood: `TOON tik`, zijn regel, `PRAAT
  tik_vraag` ("Ja, terugdraaien.").
- **Figuren die overal mee kunnen**: een ACTOR buiten een KAMER (in spel.hcs). Met `VOLGT` loopt hij achter Eldric aan
  (24 pixels erachter, aan de kant waar Eldric niet heen kijkt). Mira (`mira_mee`) loopt mee vanaf het eind van
  hoofdstuk 1.

**Getest:** `tests/tik.band` (dood met Tik, terugdraaien: vlag en munt terug, Eldric op zijn plek van binnenkomst;
Mira verschijnt en loopt mee). 23/23 compiler, 19/19 banden.

## 2026-11-13 — Hoofdstuk 2: het Duisterwoud

- **Vier kamers, met de hand getekend** (elk plaatje los goedgekeurd): `tools/teken_bospad.py` (moeras links, holle
  kokers aan de takken, het pad naar rechts), `teken_spookbrug.py` (touwbrug over een kloof, maan, dennen aan de
  overkant; patches: het harnas in stukken met/zonder helm, de honingpot met/zonder kever), `teken_jachthut.py`
  (blokhut met kaart, gewei, haard, kooi met aardmannetje, tafel met brief; patches vuur_uit en kooi_open) en
  `teken_oever.py` (steiger met bel, donkere vuurtoren op een eiland; patch: een bootje met een lampje).
  `teken_bospad.kleuren_per_vakje` houdt elk vakje op 3 kleuren + zwart, zodat de omzetter niets verandert.
- **Scripts** `scripts/bospad.hcs`, `spookbrug.hcs`, `jachthut.hcs`, `oever.hcs` volgens het scenario: Ga naar moeras
  ☠ (eerste dood, Tik legt het uit), Pak kokers, Gebruik honingpot met spookridder (het harnas valt in stukken),
  Gebruik koker met kever → fluisterkever, Pak helm, Lees brief, Open kooi bij brandend vuur ☠ (Grom komt binnen),
  Gebruik fluisterkever met aardmannetje, Gebruik helm met haard, Open kooi → gloeischub, Trek bel → een boot:
  hoofdstuk 2 voltooid. Het pad op de bosrand begint hoofdstuk 2. De spookridder is een figuur (kostuum `spook`).
- Bij een dood verbergt het script Mira even (er zijn maar 2 figuurslots: spookridder of Grom, plus Tik); TERUG zet
  haar terug, en maakt Eldric weer zichtbaar (`act_zichtbaar`).
- **Meer voorwerpen**: hoofdstuk 2 bracht het spel op 64 voorwerpen, het maximum. Nu 128: elk voorwerp heeft een
  eigenaar, maar alleen de eerste 32 een stand. `scriptc.py` zet de voorwerpen die STAND gebruiken vooraan
  (STATUS_VERSIE 4; de spelstatus blijft binnen één pagina). Gevolg: de volgorde in de inventaris veranderde.
- Bij overlappende vakken wint het voorwerp dat eerst staat: het aardmannetje staat dus voor de kooi, de brief voor de
  tafel; het vak van de spookridder ligt boven de helm en de kever.
- **Muziek**: twee nieuwe stukken in `tools/thema.py`: `woud` (G-mineur, traag, een dwalende fluit en een uil) voor het
  bospad en de spookbrug, en `zee` (D-groot in 6/8, hoopvol) voor de oever. De jachthut gebruikt de kelder.

**Getest:** `tests/hoofdstuk2.band` speelt het hele hoofdstuk, met beide doden en terugdraaien, en controleert vlaggen,
voorwerpen, muziek en "Hoofdstuk 2 voltooid". 23/23 compiler, 20/20 banden.

## 2026-11-13 — Alles testen: het hele spel, elk voorwerp, elke uitgang

- `tools/maak_testbanden.py` maakt `tests/alle_voorwerpen.band` uit de scripts zelf: elke kamer, elk voorwerp, elk
  "veilig" werkwoord (alleen praten/kijken; anders Bekijk). De zinregel moet het goede voorwerp noemen (het punt wordt
  gekozen buiten de vakken van voorwerpen die voorrang hebben), en de VM moet zonder fout klaar zijn. 76 aanwijzingen
  in 9 kamers. Draai het opnieuw na nieuwe kamers.
- `tests/hele_spel.band` speelt hoofdstuk 1 en 2 achter elkaar (`voeg_in oplossing.band`: nieuw in vicetest.py), met
  wat Eldric echt bij zich heeft, drie doden met terugdraaien en de inventaris die moet schuiven (5+ voorwerpen).
- `tests/rondje_woud.band`: alle uitgangen van hoofdstuk 2 heen en terug, Mira overal mee, de steiger op over de trap
  van loopvakken, opslaan en laden in de jachthut (hoofdstuk, vlaggen, Mira komen terug).
- De testband mag nu 4 KB zijn (was 1 KB; alleen in de testbuild).
- **Gevonden en opgelost:**
  - Mira (een figuur heeft maar één maat) liep mee tot het eind van de steiger en stond daar als reus boven het water.
    Een volger gaat buiten nu niet dieper dan de eerste SCHAAL-grens: daar wacht ze op Eldric (`volg_doel`).
  - Het vak van de zee lag over het eind van de steiger: klikken om daar te lopen werd "Ga naar zee". Nu rechts ervan.

**Getest:** 23/23 compiler, 23/23 banden.

## 2026-11-13 — Tussenscène: de grot van Grom

- Na hoofdstuk 1, de eerste keer het bos in: *"Ondertussen, diep onder de berg..."*. Een toneel (`scripts/grot.hcs`,
  plaatje `tools/teken_grot.py`): de Holle Kroon op een stenen zuil, het gevangen zonlicht flakkert (FLAKKER geel wit
  oranje) en kleurt de rotsen warm, naar de randen donker. Grom komt uit de gang links, een aardmannetje uit de gang
  rechts ("Meester... wij hebben honger."). Grom weet van de jongen met het stukje zon en laat de brug en de vuurtoren
  bewaken. Daarna begint hoofdstuk 2 op het bospad. Vuur of spatie slaat de scène over.
- Nieuw muziekstuk `grot` (D-mineur, zwaar: een stampende bas als trollenstappen). Nieuwe spreker `aardmannetje` (roze).
- vicetest: `npc_py+@mira_mee` — het nummer van een figuur bij naam (de nummers verschuiven als er figuren bijkomen).

**Getest:** `tests/grot.band` (de scène, de muziek, de figuren, geen Eldric; daarna hoofdstuk 2 op het bospad; de
tweede keer geen scène meer). 23/23 compiler, 24/24 banden.

## 2026-11-13 — De grot opnieuw: Grom als reus, de Holle Kroon met maanstenen

Feedback: Grom zag eruit als een lief poppetje, en "de zon in een kom" gelooft niemand: het is donker door de
maansverduistering. Nieuw (ook in het scenario): de **Schemerspreuk zet de twee manen vast vóór de zon**. De spreuk zit
in de **Holle Kroon**, een zwarte ijzeren kroon met twee **maanstenen** (één per maan; in het midden hol). Zolang Grom
haar draagt, staan de manen stil. Het einde: Grom neemt één maansteen uit de kroon, die maan schuift door en het licht
komt in één golf terug (het zonnebaken vangt het op); de andere maan blijft staan boven het dal van de aardmannetjes.
"Zonnekamer" heet nu "Maankamer".

- `tools/teken_grot.py`: Grom staat nu in het plaatje zelf (een sprite is te klein): een reus voorovergebogen op zijn
  vuisten, donkergrijs met koud randlicht, rode ogen, slagtanden, de kroon met twee lichtblauwe maanstenen (die
  pulseren: FLAKKER). Door een gat in het gewelf: de zwarte zon met een stralenkrans en de twee manen ervoor. Alleen
  blauw en zwart in de achtergrond, zodat hij loskomt. Zijn ogen vlammen geel op als hij "Stil!" brult (KLEUR).
- `scripts/grot.hcs`: nieuwe teksten ("Twee manen voor de zon. Mijn kroon houdt ze vast."); alleen het aardmannetje
  is nog een figuur.

**Getest:** 23/23 compiler, 24/24 banden.

## 2026-11-13 (nacht) — Hoofdstuk 3 en 4: de Zee van Vergetelheid en de Rotskloof

Op verzoek van de gebruiker werk ik zelfstandig door ("maak er wat moois van"). De plaatjes keurde ik zelf; zie de
lijst onderaan om morgen samen naar te kijken.

**Ruimte**
- Eldric ingepakt: zijn 60 poses staan per pose RLE-ingepakt (`tools/costume.py`) en `actor_pose` pakt een pose uit als
  hij verandert. 7,5 KB → 4 KB. Hoofdprogramma nu ruim 6 KB onder $A000 vrij.
- Testbanden mogen 4 KB zijn; de markeringen tellen rond (1..255), zodat één band het hele spel kan spelen.

**Motor**
- `src/mist.asm`: `MIST [TOT vlag]` in een kamer. Elke 30 seconden vergeet Eldric de naam van een voorwerp: in de
  inventaris en op de zinregel staat "???". Bekijk geeft de naam terug. Met TOT vlag verdwijnt de mist zodra die vlag
  staat (de straal van de vuurtoren) en weet hij alles weer. `st_vergeten` (een bit per voorwerp) staat in de
  spelstatus (STATUS_VERSIE 5).
- Fout gevonden: `naam_ptr` gebruikte Y, maar de zinregel houdt daar zijn lengte in ("Ga naa boot"). Nu bewaard.
- Fout gevonden: een patch breder dan 31 vakjes (meer dan 255 bytes per rij) werd verkeerd gekopieerd; het pad in de
  donkere grot (de volle breedte) bleef onzichtbaar. `patch_zetten` telt nu in 16 bits.
- Fout gevonden: de patchbuffer is 1 KB; een patch van de halve kamer liep erover heen (de testband raakte stuk).
  `tools/kamer.py` weigert nu een patch die uitgepakt groter is; het pad is in drie stukken gezet.

**Hoofdstuk 2, bijgewerkt**: de honingpot gaat weer mee als Eldric de kever vangt (de meeuwen en Pad willen hem nog).

**Hoofdstuk 3, Zee van Vergetelheid** (`tools/teken_zee.py`, scripts veerman/steiger/boot/eiland/vuurtoren):
- Tussenscène *de veerman*: Olm roeit door de mist ("Wie ben ik eigenlijk?"). Daarna de steiger: OLM staat op de boot
  (Lees boot), "Je heet Olm." ☠ "Je heet Bram." → de Rots van de Zekere Dood.
- De boot in de mist (MIST TOT vuurtoren_brandt): Mira voelt dat de steen naar links trekt; zeewater in de kruik
  (nodig in hoofdstuk 6); ☠ Pak zee (drinken).
- Het eiland: honing op de rots, de meeuwen laten de sleutel vallen; de deur (de sleutel blijft in het slot).
- De vuurtoren: Kapitein Nul draait zich om met de fluisterkever (een aardmannetje: "een beetje licht doet geen pijn");
  oma's steentje in de lenshouder → de lamp brandt, de sterrenkaart; Pak lamp → het steentje terug. ⛔ De lantaarn in
  de lamp: Tik meteen ("wie verlicht straks jouw weg in de kloof?").
- Terug in de boot: "Volg de straal!" → hoofdstuk 3 voltooid; "Aan land, Olm." → hoofdstuk 4.

**Hoofdstuk 4, Rotskloof** (`tools/teken_kloof.py`, scripts kloof/donker/zwamgrot/aardstad/spreukzaal):
- Tweede grotscène (hetzelfde plaatje, een tweede BINNENKOMST): Grom ziet de vuurtoren branden, "NUL!", stuurt zijn
  wolven naar de kloof.
- Kloofingang: de lantaarn jaagt de wolven weg maar lekt leeg (stand 3); de gloeischub erin: zwak licht (4), genoeg.
  ☠ zonder licht de grot in.
- Donkere grot: alles zwart, elke stap zelf is de afgrond ☠. Praat met Mira → zij leidt (het pad gloeit op: patches
  pad1-3), onderweg het trilkristal.
- Zwamgrot: Pad de zwamhoeder ruilt twee lichtzwammen voor de honingpot. ☠ de zwarte zwam. Een lichtzwam in de
  lantaarn (5: fel). Naar de stad: Mira waarschuwt ("maak je klein, maak je donker"), Sluit lantaarn (6) — anders ☠.
- Aardstad: Moeder Aard (met de kever) vertelt hoe het echt zit, het laatste ei gloeit (zoals Mira's steen), de
  sleutelschub. "Praat met Grom. Niet vechten. Praten."
- Spreukzaal: Lees spreukenboek (met de sterrenkaart): een maansteen uit de kroon, en het licht moet naar het zonnebaken
  op de IJstop. Het trilkristal in de kring → bakenkristal → hoofdstuk 4 voltooid. ☠ zonder het boek.

**Getest:** `tests/hoofdstuk3.band`, `tests/hoofdstuk4.band` (met alle doden), `tests/hele_spel.band` speelt nu
hoofdstuk 1 t/m 4 achter elkaar; `alle_voorwerpen.band` wijst 124 voorwerpen aan in 18 kamers.

**Om morgen samen te bekijken (zelf gekozen):** de plaatjes van hoofdstuk 3 en 4 (Olm, Nul, Pad als vriendelijke
reuzenpadde, Moeder Aard, de stenen kring); het dodenspoor in de donkere grot (elke klik in het donker is dood: streng,
maar Mira zegt het meteen); de mist (verdwijnt als de vuurtoren brandt).

## 2026-11-13 (nacht) — Twee diskettes, decor buiten de spelstatus, hoofdstuk 5: de IJstop

**Twee diskettes**: in `data/kamers.txt` heeft een kamer `schijf=2` (of `schijf=beide`: de grot, die tussen elk
hoofdstuk terugkomt). `build.sh` maakt `hollowcrown.d64` (het spel, hoofdstuk 1-3) en `hollowcrown_2.d64` (hoofdstuk
4-6). Kan `laad_kamer` een kamer niet vinden, dan staat onderaan "Plaats diskette N en druk op vuur." (vuur, spatie
of muisknop) en probeert hij opnieuw. In de testbuild wacht hij tot `tools/vicetest.py` de goede diskette in VICE stopt
(de monitor: `attach`), dus de tests wisselen zelf.

**Ruimte**
- Voorwerpen: het spel heeft er nu meer dan 128. Alleen voorwerpen die kunnen verhuizen (GEEF/NEEM/PLAATS, of met een
  stand) staan in de spelstatus; vast decor heeft altijd zijn eigen kamer (`eigenaar_van` in `status.asm`).
  STATUS_VERSIE 6. Gevonden: de mist-bits liepen voor decor (nummer > 128) buiten hun tabel ("Pak ???"); nu
  overgeslagen.
- De patchbuffer, het ankerpunt en de opslagbuffer staan nu in $C800-$CFFF (segment Hoog: vrij sinds het lettertype
  op $F800 staat). Daarmee past de testbuild weer.

**Hoofdstuk 5, IJstop** (`tools/teken_ijs.py`; scripts bergpad, hut, ijsbrug, baken):
- Bergpad: het sneeuwveld hangt boven het pad. ☠ eronderdoor. Praat met sneeuwveld ("HALLOOO!") → de lawine valt
  vóór je.
- Hut: Oma Rijm ("Mijn gewone jongen"), de nacht van het steentje, "omdat jij lief bent", de wollen want.
- IJsbrug: de rijmwurm eet licht. ☠ met de lantaarn open de brug op. De laatste lichtzwam in de kloof → hij duikt
  erachteraan, je steekt over.
- Zonnebaken: ☠ het kristal met blote handen ("het baken bijt"). Gebruik want met bakenkristal, dan in de houder:
  een witte bundel boven de schemer. Hoofdstuk 5 voltooid. Op de trap: de derde grotscène (Grom ziet het baken,
  stuurt de spookridders).
- De spreukzaal leidt na hoofdstuk 4 omhoog naar de IJstop.

**Getest:** 27/27 banden (`hoofdstuk5.band`; `hele_spel.band` speelt nu hoofdstuk 1 t/m 5, met de diskettewissel).

## 2026-11-14 (nacht) — Hoofdstuk 6: het Vergeten Kasteel, de slotscène; rijkere plaatjes; Oma's tussenscène

**Hoofdstuk 6** (`tools/teken_kasteel.py`; scripts kerker, poort, troonzaal, maankamer, dak). Het spel is nu helemaal
uit te spelen, tot "Dawnhaven. De eerste ochtend."
- Kerker: Eldric wordt wakker zonder steentje, lantaarn en Mira. De fluisterkever neuriet de tralies los.
- Poort: vier spookridders (de kever praat met de kevers in de helmen: ze vallen uiteen); ☠ erlangs zonder; de
  sleutelschub opent de poort.
- Troonzaal: Grom op zijn troon (groot in het plaatje, zoals in de grot), Mira naast hem. ☠ "Ja, het licht moet terug".
  "Ik wil dat iedereen kan leven" → "Woorden. Laat me iets zien." Drie dingen: de kroon terug (in de helm), de
  aardmannetjes die het zelf zeggen (de kever), het jong met de gloeischub. Dan: "Laat één maan gaan." ☠ "Geef de
  kroon, of ik breek hem!"
- Maankamer: verblindend wit (KLEUR: alle kleuren naar wit) tot de natte kruik de spiegels beslaat (de kamer laadt
  opnieuw, zonder schittering). Oma's steentje terug; ☠ de kroon met blote handen; de kroon in de helm.
- Het dak (slotscène, een toneel): de manen zijn figuren voor de zon in het plaatje. De eerste maan schuift opzij, de
  lucht wordt blauw, rood, oranje, lichtblauw; de tweede blijft staan boven het dal van de aardmannetjes. Mira's steen
  barst: Tik ("Hallo, ik."). Einde.

**Plaatjes**: de gebruiker vond de nieuwe kamers "veel te clinisch". Zelf opnieuw getekend, rijker (geen FLUX):
- `tools/rijk.py`: verloop, textuur, licht, schaduw, planken, stenen muren, golven, weerschijn, gloed; en `verrijk()`
  die elk plaatje afwerkt: textuur per materiaal, randlicht (volume) en lichtpoelen. De ruis hangt af van de plek
  (een hash), niet van een toevalsreeks: zo blijven een plaatje en zijn patches gelijk buiten het vak.
- Steiger en veerman helemaal opnieuw (Olm met plooien en baard, lantaarnlicht op planken en water); de andere kamers
  van hoofdstuk 3-6 afgewerkt met eigen lichtbronnen; bergen met schaduwvlakken en dennen; een nieuwe rijmwurm; de
  spreukzaal met een stenen muur, kaarsen, een sterrenkaart en runen.
- Textuur pakt slecht in (RLE): per kamer is de dichtheid afgestemd zodat hij past. De kamerbuffer is anders
  verdeeld: plaatje tot $B5FF (5,5 KB), scripts van de kamer $B600-$BFFF (2,5 KB; de troonzaal is de grootste, 2,3 KB).

**Tussenscène na hoofdstuk 4** (`oma`): Oma Rijm in de deur van haar hut op de IJstop, met een lantaarn; ver beneden
een klein lichtje: "Dat is het steentje. Dat is mijn jongen." Nu zit er tussen elk hoofdstuk een tussenscène.

**Testen**: de testband is een ring van 2 KB die `tools/vicetest.py` achter de leeskop bijvult (een band mag nu zo lang
zijn als het hele spel); de standaard tijdslimiet is 10 minuten. 24 figuren in de spelstatus (STATUS_VERSIE 7).
`tests/hoofdstuk6.band` speelt het laatste hoofdstuk met vijf doden; `hele_spel.band` het hele spel.

## 2026-11-14 (nacht) — Een eigen snellader (turboloader)

`src/turbo.asm`, met eigen code (geen bestaande loader nagebouwd):
- Het spel stuurt een klein programma naar de 1541 (M-W in stukjes van 32 bytes, één keer: daarna blijft het in de
  drive staan tot er een gewone Kernal-schijfactie is: opslaan, laden of terugvallen) en start het per bestand met
  M-W van de naam en M-E. Het drive-programma zoekt de naam in de directory (spoor 18), leest de sectoren met de
  jobqueue van de DOS en stuurt elke byte in 4 stappen van 2 bits: het eerste bit op DATA, het tweede op CLK.
- De C64 bepaalt het tempo met ATN: hij wisselt ATN, wacht even, leest DATA en CLK. Een badline of sprite kan de C64
  alleen vertragen, dus het werkt met het scherm aan. De drive zet ATNA steeds gelijk aan ATN (anders trekt de 1541
  zelf DATA laag), en wist de ATN-vlag van de VIA voordat hij de interrupts weer aanzet (de DOS mag ons protocol niet
  als een busopdracht zien).
- Per sector: de drive meldt "klaar" (DATA laag), stuurt een lengtebyte (0 = niet gevonden of leesfout), de bytes, en
  of er nog een sector komt; de C64 bevestigt met nog een ATN-wissel.
- Terugvallen: komt er binnen ~5 s geen "klaar" (geen echte drive, zoals de virtuele drive van VICE in de tests), dan
  laadt het spel via de Kernal en blijft de turbo uit. Niet gevonden: ook via de Kernal (die vraagt dan om de andere
  diskette).

Fouten onderweg: het drive-programma was soms al klaar voordat de C64 ging wachten (dan wachtte de C64 eerst op een
"los" dat nooit kwam); het vooraf uitrekenen van vier bitparen duurde zo lang dat de C64 al twee keer van ATN wisselde
(twee wissels heffen elkaar op: drive en C64 liepen uit de pas). Nu rekent de drive per stap één paar uit, vóór hij
wacht. En in de tests: met de echte drive laadt VICE het hoofdprogramma langzaam, terwijl "HC" al in de prg staat;
vicetest wacht nu tot de processor echt in het spel staat.

**Diskettes**: `tools/d64.py` maakt de D64's zelf (BAM, directory, bestanden) met een tussenruimte naar keuze; c1541
valideert ze zonder iets te veranderen. Gemeten (een kamer, VICE met echte 1541): de Kernal 16,1 s; de snellader 8,0 s
bij tussenruimte 2-3 (die is nu standaard). Dat een grotere tussenruimte niet helpt, wijst op een vaste vertraging
per sector in de jobqueue van de DOS: een eigen sectorlezer in de drive (zonder jobqueue) kan later nog sneller.

**Testen**: `tests/turbo.band` (met de regel `echte_drive`: die band draait altijd met de 1541-emulatie) laadt
kamers met de snellader en vergelijkt het scherm pixel voor pixel met het geheugen. De andere banden draaien zonder
echte drive: daar valt de turbo terug op de Kernal, en zo is dat pad ook getest. Bij een time-out meldt vicetest nu
waar de processor staat (met het dichtstbijzijnde label) en de tellers van de turbo. De testband is een ring van 1,5 KB.

Laatste fout voor de commit: `turbo_vergeet` stond in opslaan.asm tussen het klaarzetten van de registers en de
Kernal-SAVE, en maakte A nul. Daardoor las SAVE het beginadres uit $00/$01 en schreef 77 blokken onzin (een goed
opslagbestand is 1 blok); laden daarvan liet het spel hangen. Nu staat de aanroep vóór SETNAM. Daarna: 29 van 29
banden geslaagd, compiler 23 van 23.

## 2026-11-14 — Het doolhof achter de spookbrug, en meekijken

Op verzoek van de gebruiker: na de brug stond Eldric meteen binnen in de jachthut. Nu loop je eerst door het
Duisterwoud: een doolhof van vier schermen (om en om twee getekende plaatjes, `diepwoud` en `wolfspad`, zodat het op
diskette 1 past), elk met vier uitgangen (pad links, pad rechts, tunnel links, tunnel rechts). Eén route brengt je bij
de hut: tunnel links, rechts, tunnel rechts, links. Elke andere afslag eindigt weer bij de brug ("We liepen in een
rondje!"). De aanwijzing: de voetsporen van Grom (Bekijk sporen). Daarna het erf (`huterf`): een blokhut op
reuzenmaat met een rokende schoorsteen, een raam met oranje licht, huiden, een bijl in het hakblok, een ketel. Pas
dan door de deur naar binnen. Is de hut eenmaal gevonden, dan gaat de brug meteen naar het erf.
- Getekend in `tools/teken_woud2.py` (gloeizwammen als lichtbron, een uil in een holle boom, een waarschuwingspaal
  met gewei, een klem; het kruispad als één masker met een zwarte rand).
- Tests: `tests/doolhof.band` (twee keer verdwalen, dan de goede route, terug, en weer over de brug), de route als
  `tests/doolhof_stappen.txt` in hoofdstuk2.band en hele_spel.band; rondje_woud.band via het erf.
- De testring is nu 1 KB (het autotest-programma paste niet meer onder $A000).

Meekijken: `python3 tools/vicetest.py --kijk tests/kijken/kijk.band` speelt het intro, het openingsverhaal en het
hele spel op normale snelheid, met geluid en de echte 1541 (de snellader). Twee fouten daarbij opgelost: vicetest
begon al terwijl het spel nog laadde (nu moet de processor zes keer achter elkaar in het spel staan), en de
geheugenblikken (20 per seconde, elk zet de emulatie even stil) lieten het geluid haperen: in de kijkstand nu één
keer per seconde.

Testronde: 30 van 30 banden, compiler 23 van 23.

## 2026-11-14 — Grom als eng poppetje, en een reus

De gebruiker: in de tussenscène is Grom eng, maar als poppetje leek hij een lief groen beertje, in andere kleuren.
Nu: een nieuwe tekening (tools/sprites_hc.py) met hoorns, boze rode ogen onder een V-wenkbrauw, een bek met
slagtanden, brede schouders, armen met klauwen, een lendendoek en kromme benen; helemaal grijs zoals de stenen reus
in de grot. En hij is een reus: een nieuwe NPC-vorm 2 (tools/costume.py) laat de VIC zijn twee sprites dubbel zo
breed en hoog tekenen ($d017/$d01d, src/npc.asm; kost geen geheugen). vicetest tekent vergrote sprites nu ook na.
Grom staat in de bosrand iets lager en loopt zijwaarts weg (in de diepte zou hij boven de kamer uitsteken); in de
jachthut iets meer naar links (anders valt hij half buiten beeld). Testronde: 30 van 30, compiler 23 van 23.

## 2026-11-14 — Meekijken op dubbele snelheid; de diskettewissel met de echte 1541

`vicetest.py --kijk --stil --snelheid 200 tests/kijken/kijk.band`: het hele spel in een venster, dubbel zo snel,
zonder geluid (21 minuten, geslaagd). Onderweg bleef het spel hangen bij "Plaats diskette 2": met de echte 1541 las
het spel direct na de wissel nog de oude diskette, vroeg opnieuw, en vicetest stopte diskette 2 er telkens opnieuw in
(waarmee de drive weer van voren af begon). Nu: in de testbuild wacht diskette_vragen na de wissel ~2 s (een
tijdlus: tijdens het laden staan de interrupts uit, dus een beeldteller loopt niet), zoals een speler die op vuur
drukt; en vicetest stopt een diskette die er al in zit niet opnieuw in. Getest: hoofdstuk4.band en het hele spel met
de echte drive. Testronde: 30 van 30.

## 2026-11-14 — Alles op één diskette: de D71 voor de 1571

build.sh maakt nu ook build/hollowcrown.d71: het spel en alle kamers op één dubbelzijdige diskette (982 blokken,
346 vrij), met c1541. Geen wissel: elke kamer is er, dus het spel vraagt nooit om diskette 2. vicetest kan hem testen
met `--d71` (een 1571 in VICE; met `--echte-drive` de echte 1571-emulatie).

De snellader op de 1571, twee fouten:
- Op kant 2 bleef een leesopdracht in de jobqueue hangen (spoor 41) zolang de 1571 in de 1541-stand stond. Nu stuurt
  het spel eerst "U0>M1": de 1571 in zijn eigen stand. Een 1541 kent alleen U0 (de gebruikerssprongen terugzetten):
  onschuldig; turbo.band op de 1541 slaagt nog.
- In zijn eigen stand gebruikt de 1571 zelf $0700, waar de bestandsnaam voor het drive-programma stond: dan vond hij
  niets en laadde het spel alles via de Kernal. De naam staat nu op $06E0, direct achter het programma.
Om dit te vinden meldt vicetest bij een time-out met de echte drive nu ook waar de processor van de drive staat
(monitor `device 8:`) en zijn zeropage (de jobqueue).

Getest: turbo.band op de 1541 en de 1571, hoofdstuk5.band en hele_spel.band op de D71 met de echte 1571 (het hele
spel in 160 s warp, alles met de snellader), testronde 30 van 30.

## 2026-11-14 — Loopschermen door het hele spel; drie diskettes; de wolf

De gebruiker: "je gaat te snel van de ene kamer naar de andere". Nu zitten er tien loopschermen tussen (met de hand
getekend, tools/teken_tussen.py):
- hoofdstuk 1: dorpsweg (plein - bosrand; diep: akkers in perspectief, molen, vogelverschrikker, plassen)
- hoofdstuk 2: beekdal (jachthut - oever; een beek met een boomstambrug en een reiger)
- hoofdstuk 3: zeerotsen (varen tussen de klippen: een toneel, gaat vanzelf) en klippad (boot - eiland)
- hoofdstuk 4: grotgang (kloof - donker; gloeiwormen) en rivier (donker - zwamgrot; kristallen)
- hoofdstuk 5: sneeuwveld (bergpad - hut) en bergkam (hut - ijsbrug; een zee van wolken)
- hoofdstuk 6: kerkergang (kerker - poort) en wenteltrap (troonzaal - dak)
Vaste vormen (diep: onder terug, achter verder; zij: links en rechts), zodat scripts en tests overal hetzelfde
zijn. tools/loopschermen_in_banden.py zet de stappen door de loopschermen in de testbanden (waar een band van A naar
B loopt).

Ruimte: 1541 nu drie diskettes (schijf=1/2/3/alle in kamers.txt; de grot staat op alle drie); de D71 heeft nog 120
blokken vrij. Het testprogramma paste niet meer onder $A000: anker_buf en opslag_buf staan nu in de ongebruikte
sprite-vakken 8-15 ($C600-$C7FF) en de invoerband (768 bytes) achter patch_buf in $C800-$CFFF.

De wolf (bosrand en rotskloof) was stuk sinds Grom een reus werd: de code voor vorm 1 (twee sprites naast elkaar)
liep door in de reus-code en vergrootte de wolf. Opgelost (één jmp), en vicetest controleert bij elke schermafdruk
dat alleen een reus vergrote sprites heeft.

Testronde: 30 van 30, compiler 23 van 23.
