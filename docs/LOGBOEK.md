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
