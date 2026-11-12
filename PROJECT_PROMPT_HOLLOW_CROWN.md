# Project: Hollow Crown, een point-and-click adventure voor de Commodore 64

Je bent de developer van dit project. Lees dit hele document voordat je iets bouwt. Het is een zelfstandig
project: alles wat je nodig hebt, staat in deze map of hieronder.

## 1. Wat we maken

Een **point-and-click adventure** in de stijl van de C64-versies van *Maniac Mansion* en *Zak McKracken and the Alien
Mindbenders*:
- bovenaan in beeld de kamer;
- onderaan een vaste balk met de werkwoorden, een zinregel en de inventaris;
- de speler wijst met een cursor en bouwt zinnen als **"Gebruik kruik met vat"**.

Het verhaal, de wereld en de karakters zijn van ons (Hollow Crown, zie §3). Van de oude spellen nemen we alleen het
**genre en de manier van bedienen** over, niet hun code, plaatjes, teksten of muziek.

Het vorige plan (een RPG met gevechten) vervalt. Puzzels, voorwerpen en gesprekken komen in de plaats van gevechten.

**Techniek:**
- 6502-assembler met **Kick Assembler 5.x**;
- hulpprogramma's in **Python 3**;
- testen in **VICE 3.10** (`x64sc`, PAL);
- één D64-diskette als eindproduct.

## 2. Wat er al is (in deze map)

| Bestand | Wat | Gebruik |
|---|---|---|
| `sprites_hc.py` | De karakters als tekst getekend (`k` zwart, `s` huid, `c` eigen kleur). Maakt `sprites_hc.asm` en `sprites_hc.png` | Basis voor de "costumes" (§6.5). Breid hem uit; verander de tekening, niet de .asm |
| `sprites_hc.asm` | 34 sprites. Eldric: 12 poses (voor, rug, rechts, links; elk staan en twee looppasjes), elk 2 multicolor-sprites boven elkaar (12×42). Daarnaast Mira, Baron Vex, de Hollow King, een spookridder en een wolf (2 sprites naast elkaar) | Eldric en de NPC's |
| `sprites_hc_toon.asm` | Kijkprogramma: alle karakters dubbel zo groot, Eldric loopt | Controle na een wijziging |
| `hollowcrown.asm` | De huidige demo: Eldric loopt (joystick 2 / WASD) over het plaatje van Dawnhaven; Mira in de herberg | Voorbeeld van poses kopiëren naar sprite-vakken. **De motor bouw je opnieuw** (§6) |
| `dawnhaven_flux.png`, `dawnhaven.kla` | Het dorpsplein (FLUX-plaatje en Koala 160×200) | Eerste kamer; opnieuw omzetten naar 160×128 (§6.2) |
| `eldric.png`, `mira.png` | FLUX-ontwerpen. Let op: `mira.png` toont een oude tovenaar met baard; Mira is een **jonge blinde heks** (zo staat ze in `sprites_hc.py`) | Alleen als inspiratie |
| `hollowcrown_oud.asm`, `figuren*.asm`, `sprites.bin`, `mira_sprites.bin`, `shot*.png` | Oude probeersels | Verplaats naar `oud/`; niet meer gebruiken |
| `build.sh` | Oud buildscript, werkt niet zelfstandig | **Vervang hem** door een eigen buildscript (§7) |

**Eigenschappen van de sprites:**
- Elk karakter is twee multicolor-sprites boven elkaar; de onderste staat 21 pixels lager, op dezelfde X.
- Zwart (`$d025`) en huidkleur (`$d026`, lichtrood) zijn gedeeld door alle sprites.
- De bovenste en de onderste sprite hebben elk hun eigen kleur (`<naam>_kb` en `<naam>_ko`).
- Zet de karakters nooit op een zwarte achtergrond, anders verdwijnen omlijning en haar.

## 3. Het verhaal (Hollow Crown)

**Aethermoor** leefde onder de Eeuwige Zon. Op de dag van de dubbele maansverduistering kwam de **Hollow King** uit de
aarde. Hij stal het zonlicht en nam het troonkasteel in, en sindsdien hangt er een eeuwige schemering.

**Karakters:**
- **Eldric**, de speler: de laatste Wachter van de Lichte Kroon. In zijn zwaard zit het laatste lichtfragment.
- **Mira**: een blinde heks in Dawnhaven, die paden "ziet".
- **Baron Vex**: de eerste dienaar van de Hollow King, heer van het Duisterwoud.
- **De Hollow King**: de eindbaas.
- Vijanden zoals schaduwwolven en spookridders zijn hier hindernissen die je met een puzzel oplost, geen gevechten.

**De wereld, als hoofdstukken:**
1. Dawnhaven (het startdorp)
2. Duisterwoud
3. Zee van Vergetelheid
4. Rotskloof
5. IJstop
6. Het Vergeten Kasteel

**Voorstel voor hoofdstuk 1, "Dawnhaven"** (4 kamers). Werk het uit en verbeter het gerust, maar houd het klein:
- **Kamers:** het dorpsplein (met fontein), de herberg, de smidse en de bosrand.
- **Doel:** het Duisterwoud in. De schaduwwolven bij de bosrand laten niemand door; ze zijn bang voor licht.
- **De puzzelketen:**
  1. Mira kan je niet helpen: haar ziensteen is weg. Hij ligt onder een tafel in de herberg ("Duw tafel"). Geef hem
     terug, en Mira vertelt dat de wolven licht vrezen en dat smid Bram een lantaarn heeft.
  2. Het smidsvuur is uit sinds de zon weg is. "Gebruik zwaard met smidsvuur": het lichtfragment ontsteekt het vuur.
     Bram geeft je een lege lantaarn.
  3. In de keuken van de herberg staat een kruik; in de kelder een vat lampolie. Met "Gebruik kruik met vat" en dan
     "Gebruik kruik met lantaarn" vul je de lantaarn. "Gebruik zwaard met lantaarn" steekt hem aan.
  4. Bij de bosrand: "Gebruik lantaarn met wolven". Ze vluchten, en het pad gaat open. In een korte tussenscène staat
     het silhouet van Baron Vex tussen de bomen. Einde van hoofdstuk 1.
- **Regels voor puzzels:**
  - elke puzzel heeft een hint in een "Bekijk"-tekst of een gesprek;
  - je kunt nooit vast komen te zitten (geen doodlopende stand);
  - geen dood in hoofdstuk 1.

**Teksten:** in het Nederlands, kort en met wat humor, zoals de oude Lucasfilm-spellen. Maak het zo dat een tweede taal
(Engels) later kan (§6.6).

## 4. Hoe het eruitziet: het scherm

Afgekeken van de C64-versie van Zak McKracken. ScummVM gebruikt voor Zak op de C64 deze verdeling: tekst op pixelrij
0-16, de kamer op 17-145 (128 pixels), daaronder de werkwoorden en de inventaris. Wij nemen het per tekenrij over (40×25):

```
rij  0-1   berichtregels: wat een karakter zegt (hires tekst, in de kleur van de spreker)
rij  2-17  de kamer: multicolor bitmap, 160 × 128 pixels
rij 18     zinregel:  "Gebruik kruik met vat"  (wat de cursor nu zou doen)
rij 19-21  werkwoorden, 3 rijen × 4 kolommen (kolom 0, 10, 20, 30; hooguit 9 tekens)
rij 22-23  inventaris: 2 rijen × 2 kolommen namen (kolom 0-17 en 22-39), pijlen ↑ ↓ in kolom 18-21
rij 24     leeg, of de naam van het hoofdstuk
```

**Werkwoorden** (voorstel, 12 vakken):

```
Ga naar     Pak         Gebruik     Open
Bekijk      Praat met   Geef        Sluit
Duw         Trek        Lees        Wat is
```

**Hoe de speler bedient:**
- **Cursor:** een hires sprite (kruisje), met de joystick in poort 2. Hij versnelt als je de joystick vasthoudt.
- **Vuur:**
  - op een werkwoord: kiezen;
  - op een voorwerp of persoon: de zin uitvoeren;
  - op de vloer: "Ga naar".
- **Standaardwerkwoord:** "Ga naar", net als in SCUMM. Na een actie springt hij daarop terug.
- **Zinnen met twee voorwerpen** (zoals bij SCUMM: werkwoord → voorwerp → voorzetsel → voorwerp):
  - "Gebruik X **met** Y";
  - "Geef X **aan** Y".
- **Onder de cursor:** de zinregel toont de naam van het voorwerp of de persoon, zoals "Ga naar fontein".
- **Inventaris:** een voorwerp uit de inventaris klik je net zo aan als een voorwerp in de kamer. De pijlen schuiven per
  2 voorwerpen.
- **Toetsen:**
  - een vaste letter per werkwoord;
  - **F1** muziek aan/uit;
  - **F5** opslaan;
  - **F7** laden;
  - **spatie** slaat de tekst of de tussenscène over.
- **Een 1351-muis in poort 1** is een uitbreiding voor later.

**Praten:** bij "Praat met" maken de werkwoorden plaats voor hooguit 4 keuzezinnen (rij 19-22). Een keuze kan een
vlag zetten, een voorwerp geven, of het gesprek beëindigen.

## 5. De motor: een eigen "SCUMM-achtige" engine

ScummVM is een vertaler voor de originele spelbestanden. Wij bouwen zelf een kleine motor voor de C64 met hetzelfde
idee: **de motor is algemeen, het spel is data en scripts.** Dit zijn de bouwstenen, naar het model van SCUMM:

| Bouwsteen | Wat | Hoe bij ons |
|---|---|---|
| **Kamer** | Plaatje, uitgangen, loopgebied, voorwerpen, scripts | Een bestand per kamer op de diskette: ingepakt (§6.2), geladen in een vaste buffer |
| **Voorwerp** | Naam, klikvak, loop-naar-punt + kijkrichting, stand (bv. open/dicht), eigenaar (kamer of inventaris), een script per werkwoord | Een tabel per kamer; stand en eigenaar in de spelstatus |
| **Actor / costume** | Een karakter met poses en loopanimatie | Eldric en NPC's als paren van 2 sprites (al gemaakt in `sprites_hc.py`) |
| **Loopgebied (walkboxes)** | Waar je mag lopen | Rechthoeken per kamer met een tabel welke aan elkaar grenzen; pad zoeken over die graaf (BFS), lopen in rechte stappen naar het punt op de gedeelde rand |
| **Zinregel** | Werkwoord → voorwerp → voorzetsel → voorwerp | Zoals in §4 |
| **Scripts** | Wat er gebeurt bij een zin, bij binnenkomst, tussenscènes | Een tekstscript, door een Python-compiler naar bytecode, uitgevoerd door een VM in de motor (§6.4) |
| **Standaardantwoorden** | "Dat kan ik niet openen." | Per werkwoord een standaardscript als het voorwerp er geen heeft |

**Bekende C64-oplossingen die je mag gebruiken (beschreven in de bronnen van §10):**
- Maniac Mansion op de C64 maakt kamers van een multicolor tekenset met een schermkaart, plus een aparte maskerset voor
  voor- en achtergrond.
- Maniac Mansion bewaart van karakters alleen voor, achter en rechts. Links is gespiegeld via een tabel.
- *Caren and the Tangled Tentacles* (C64, 2015-2018) heeft een eigen scripttaal die naar 6502-assembler wordt vertaald,
  met pathfinding en veel parallelle threads.

Lees die bronnen voor de ideeën. **Kopieer geen code** uit disassemblies of uit ScummVM; dat is code van anderen (en de
licentie van de disassembly is onbekend).

## 6. Technisch ontwerp (begin hiermee; wijk alleen af met een reden die je opschrijft)

### 6.1 Geheugenkaart (VIC-bank 3)

| Bereik | Inhoud |
|---|---|
| `$0801-$BFFF` | programma: motor, costumes, de scripts en objecten van de kamer, buffers |
| `$C000-$C3E7` | scherm-RAM: rij 2-17 de kleuren van de bitmap, de andere rijen de tekens van de tekst |
| `$C3F8-$C3FF` | sprite-pointers |
| `$C400-$C7FF` | 16 sprite-vakken: Eldric 2, NPC 2+2, cursor 1, rest vrij |
| `$C800-$CFFF` | eigen lettertype voor de balk en de berichten (met ↑ ↓) |
| `$D800` | kleur-RAM |
| `$E000-$FF3F` | bitmap, onder de Kernal-ROM: schrijven kan altijd, lezen alleen met `SEI` en `$01=$35` |

**Regels bij deze kaart:**
- `$DD00` (de VIC-bank) altijd met lezen-wijzigen-schrijven: de andere bits zijn de seriële bus.
- Laat de prg niet tot `$C000` doorlopen. Zet gegevens achter de code en kopieer ze bij het starten.
- Leg de kaart vast in `src/geheugen.asm`, met `.segment`'s en `.assert`'s, zodat de build mislukt als iets niet past.
- **Costumes:** de poses staan in het programma. De motor kopieert de pose van dat moment naar het sprite-vak
  (128 bytes per karakter, alleen als de pose verandert). Zo doet `hollowcrown.asm` het nu al.
- **Sprites:** zonder multiplexen kunnen er 8 tegelijk. Dat is genoeg voor Eldric, twee NPC's en de cursor.

### 6.2 Kamers en plaatjes

**Een kamer is één scherm** (160×128 multicolor bitmap) met uitgangen naar andere kamers. Kamers die scrollen
(breder dan het scherm) komen pas na hoofdstuk 1, en alleen als het nodig is.

**Van FLUX-plaatje naar kamer:** `tools/kamer.py` zet een FLUX-plaatje om naar een kamerbestand.
1. Snijd een brede strook uit, in de verhouding 5:2: 320×128 schermpixels, dus 160×128 multicolor-pixels.
2. Houd je aan de C64-regels: per 4×8-vak de achtergrondkleur plus 3 kleuren.
3. Pak het in (RLE of een eenvoudige LZ; een eigen uitpakker in asm).
4. Schrijf `kamer_<naam>.png` als controle: de C64-pixels naast de bron.

**Regels voor de kunst:**
- de onderste 2 pixelrijen van elke kamer zijn donker of zwart, voor de naad met de balk;
- er staan geen zwarte vlakken waar karakters lopen.

**Lopen achter iets langs (voorgrond):**
- Met `$d01b` gaat een sprite achter de bitmappixels met kleur `%10` en `%11`.
- Per kamer geef je zones op (rechthoek + Y-grens): staat Eldric met zijn voeten boven die grens, dan gaat hij erachter.
- Teken voorgrond (een pilaar, de fontein) daarom in de kleuren van scherm-RAM en kleur-RAM.
- Dit hoort bij hoofdstuk 8 van de bouwvolgorde.

**Veranderingen in een kamer** (deur open, vuur aan): patches. Een patch is een rechthoek van cellen met de bitmap,
het scherm-RAM en het kleur-RAM, en wordt over de kamer gekopieerd.

### 6.3 Het scherm splitsen

Met `$d011` YSCROLL=3 begint tekenrij r op rasterlijn 51 + 8r: rij 2 op lijn 67, rij 18 op lijn 195. Er zijn drie
raster-IRQ's per beeld:
- **Lijn 66, net voor rij 2:** bitmapmodus. `$d011=$3b`, `$d016=$d8`, `$d018=$08` (scherm `$C000`, bitmap `$E000`).
- **Lijn 194, net voor rij 18:** tekstmodus voor de balk. `$d011=$1b`, `$d016=$c8` (hires tekst), `$d018=$02`
  (scherm `$C000`, tekens `$C800`).
- **Lijn 252, de onderrand:**
  - zet de tekstmodus voor rij 0-1 van het volgende beeld;
  - speelt de muziek en het geluid af en telt de beelden;
  - springt één keer per beeld naar `jmp $EA31`.
- Schakel de CIA-IRQ uit.

Komt een IRQ een paar cycli te laat, dan zie je een rafel in de naad. Daarom de kunstregel uit §6.2, en de tekens van
rij 18 met een lege bovenste pixelrij.

### 6.4 Scripts en VM

Schrijf de scripts in tekstbestanden (`scripts/*.hcs`). `tools/scriptc.py` maakt er bytecode en de objecttabellen van,
in het formaat dat de motor leest. Een voorbeeld van de vorm (verbeter gerust):

```text
KAMER plein "data/kamer_plein.png"
  LOOPVAK 4,96 156,127
  LOOPVAK 60,80 100,96
  UITGANG herberg  AAN 20,90  NAAR herberg 140,120 RUG

VOORWERP fontein "fontein" VAK 64,70 32,24 LOOP 80,100 RUG
  BEKIJK:
    ZEG eldric "Het water is zwart sinds de zon weg is."
  GEBRUIK kruik:
    ZEG eldric "Hier zit geen olie in."

VOORWERP herbergdeur "deur" VAK 16,60 16,32 LOOP 24,94 RUG
  OPEN:
    ALS NIET vlag deur_open
      ZET deur_open
      PATCH deur_open
    EINDE
  GA_NAAR:
    ALS vlag deur_open
      KAMER herberg 140,120
    ANDERS
      ZEG eldric "De deur is dicht."
    EINDE
```

**Opcodes**, eerste set (houd het klein):
- tekst: `ZEG` (spreker, tekst; wacht tot de tekst weg is of op spatie);
- lopen: `LOOP` (actor naar x,y), `KIJK` (richting);
- inventaris: `GEEF` / `NEEM` (voorwerp naar of uit de inventaris);
- vlaggen: `ZET` / `WIS`;
- voorwaarden: `ALS` (vlag, heeft voorwerp, stand van een voorwerp; met `NIET`), `ANDERS`, `EINDE`;
- de kamer: `STAND` (voorwerp krijgt stand n), `PATCH`, `KAMER` (wissel van kamer: naam, x, y);
- de rest: `GELUID`, `PRAAT` (gesprek met keuzes), `TUSSENSCENE` / `EINDE_TUSSENSCENE` (geen invoer, spatie slaat over),
  `WACHT` (aantal beelden), `STOP`.

**Wat de compiler controleert:**
- onbekende vlaggen, voorwerpen en kamers;
- tekst die te lang is (hij breekt de tekst over 2 regels van 40);
- een kamer die groter is dan zijn buffer.

Hij schrijft ook een lijst van alle puzzelstappen, en controleert of hoofdstuk 1 uit te spelen is: elke benodigde vlag
en elk benodigd voorwerp moet ergens te krijgen zijn.

**De spelstatus** staat in één blok: kamer, positie, vlaggen (256 bits), voorwerpen (eigenaar en stand), met een
magic en een versie. Opslaan is dat blok naar de diskette schrijven.

### 6.5 Karakters

`tools/costume.py` maakt van de tekeningen in `sprites_hc.py`:
- per karakter de poses, met een tabel per richting (staan, stap 1, stap 2);
- het spreken: een tweede bovenste sprite met de mond open, of een mond die de motor erin tekent.

**Lopen:**
- 1 pixel per beeld horizontaal (een multicolor-pixel per 2 beelden mag ook);
- 1 pixel verticaal;
- een stap elke 8 beelden;
- aan het eind van de route kijkt de actor zoals het voorwerp vraagt.

### 6.6 Tekst en talen

- **Eigen lettertype** op `$C800`, met hoofd- en kleine letters, cijfers, leestekens, ↑ en ↓.
- **Berichten** komen op rij 0-1 en blijven staan: ongeveer 1 seconde plus 1 seconde per 20 tekens, of tot spatie.
- **Strings** staan in de scriptbestanden. De compiler kan per taal een eigen bestand maken met dezelfde bytecode en
  andere strings. Engels komt later.

### 6.7 Diskette en laden

- Eén D64, gemaakt met `c1541` (zit bij VICE) of met de `.disk`-directive van Kick Assembler.
- Bestanden: het spel, een bestand per kamer, de muziek, en de opslag.
- Eén laadroutine (`laad`). Begin met de Kernal. Een snellader kan later, zonder dat de rest verandert.
- **Opslaan:**
  - eerst scratchen (`S0:naam` op kanaal 15), dan schrijven;
  - **nooit `@0:`**, want dat is een bekende fout in de 1541.
- **Tijdens het laden:**
  - de muziek staat stil;
  - zet alle SID-stemmen uit, anders blijft er een toon hangen;
  - laat een "Laden..."-tekst zien in de balk.

## 7. Werkwijze en gereedschap

**De mappen:**

```
src/        motor (*.asm): main, irq, invoer, balk, kamer, actor, lopen, voorwerp, vm, tekst, gesprek, schijf, geluid
scripts/    het spel (*.hcs)
data/       FLUX-plaatjes, kamers, muziek
tools/      kamer.py, costume.py, scriptc.py, inpak.py, schijf.sh, vicetest.py
tests/      invoerbanden en verwachte uitkomsten
build/      alles wat de build maakt (niet met de hand wijzigen)
oud/        de oude probeersels
```

**Gereedschap:**
- **Java:** een JDK van versie 17 of nieuwer (controleer met `java -version`).
- **Kick Assembler 5.x:** `KickAss.jar` hoort in `tools/` van dit project. Haal hem van de officiële site
  (<http://theweb.dk/KickAssembler/>).
- **VICE 3.10 of nieuwer:** `x64sc` voor de C64 en `c1541` voor de diskette. Zet de paden in één instelling bovenin
  `build.sh` en `tools/vicetest.py`, niet verspreid door de scripts.
  - VICE wil absolute paden.
  - Op macOS start het programma in `bin/` een kindproces. Start VICE daarom als eigen procesgroep, en stop alleen die groep.
    Nooit alle VICE's tegelijk afsluiten.
- **`build.sh`** (nieuw, eigen):
  1. scripts compileren;
  2. kamers en costumes omzetten;
  3. assembleren;
  4. de D64 maken;
  5. stoppen bij de eerste fout, met het bestand en de regel.

**Testen zonder handen.** De remote monitor van VICE kan wel geheugen lezen en schrijven en screenshots maken, maar kan
**geen joystick of toets ingedrukt houden**. Bouw daarom vanaf het begin een testmodus in:
- `-define AUTOTEST` leest de invoer uit een **invoerband** in plaats van uit joystick en toetsenbord.
- De band is een lijst stappen: "cursor naar x,y", "vuur", "wacht n beelden".
- `tools/vicetest.py`:
  1. start VICE met `-remotemonitor`;
  2. laat de band lopen;
  3. maakt op afgesproken momenten screenshots (`screenshot "pad" 2`);
  4. leest aan het eind de spelstatus uit het geheugen (kamer, vlaggen, inventaris);
  5. vergelijkt die met `tests/*.verwacht`.
- **Een test slaagt alleen als de status klopt.** Een screenshot alleen is geen bewijs.

**Hoe je werkt:**
- Werk in kleine stappen. Bouw na elke wijziging, en test in VICE voordat je zegt dat iets werkt.
- Zeg eerlijk wat je getest hebt en wat niet.
- Data hoort buiten de code: plaatjes, teksten, puzzels en loopvakken staan in data en scripts, niet in de asm van de motor.
- Elke fase eindigt met een screenshot of testuitslag, en een korte notitie in `docs/LOGBOEK.md`: wat werkt, wat
  gemeten is, en wat nog open staat.
- Commentaar en teksten schrijf je in het Nederlands.

## 8. Bouwvolgorde (elk hoofdstuk heeft een "klaar als")

| # | Hoofdstuk | Klaar als |
|---|---|---|
| 0 | **Opzet**: mappen, `build.sh`, geheugenkaart met asserts, lege D64, `vicetest.py` met een band die alleen wacht | `./build.sh` maakt `build/hollowcrown.d64`; de test start VICE en maakt een screenshot |
| 1 | **Het scherm**: split met berichtregels, kamer (Dawnhaven als 160×128) en balk; werkwoorden en lege inventaris getekend; de cursor beweegt | 3 screenshots op verschillende momenten: schone naden (geen verdwaalde pixels in rij 1/2 en 17/18), cursor op een andere plek |
| 2 | **Eldric loopt**: costumes uit `sprites_hc.py`, loopvakken, pad zoeken, 4 richtingen met looppasjes | Band: klik op 3 plekken (één achter een hoek van het loopgebied). Eldric komt aan binnen het loopgebied, en kijkt in de goede richting (geheugen + screenshot) |
| 3 | **Voorwerpen en zinregel**: klikvakken, namen onder de cursor, werkwoord kiezen, "Bekijk" toont tekst op rij 0-1 | "Bekijk fontein": de juiste tekst staat op rij 0-1 (schermgeheugen lezen) |
| 4 | **Script-VM en compiler**: de opcodes van §6.4, standaardantwoorden | Scripttests: elke opcode één keer, plus fouten die de compiler moet weigeren |
| 5 | **Inventaris**: pakken, gebruiken met, geven, schuiven met de pijlen | Band: pak kruik, gebruik kruik met fontein (standaardantwoord); de inventaris klopt in het geheugen |
| 6 | **Meer kamers en de diskette**: uitgangen, laden van de D64, patches (deur open) | Band: van het plein naar de herberg en terug; laadtijd gemeten en genoteerd |
| 7 | **Praten**: gesprek met Mira met keuzes, NPC's als actor | Band: het hele gesprek, met de juiste vlag aan het eind |
| 8 | **Voorgrond en kleine animaties**: achter de fontein langs, smidsvuur dat flakkert (kleurcyclus of patch) | Screenshot: Eldric half achter de fontein |
| 9 | **Hoofdstuk 1 uitspeelbaar**: alle puzzels van §3, tussenscène Baron Vex, opslaan en laden, geluidseffecten | Band met de hele oplossing eindigt met "hoofdstuk 1 voltooid". Een tweede band slaat halverwege op, laadt, en speelt verder |
| 10 | **Het intro** (laatste hoofdstuk, §9) | Intro → spel start; muziek speelt (SID-registers veranderen volgens de noten); geen hangende toon na het intro |

Hoofdstuk 2 tot en met 6 van het verhaal komen pas nadat hoofdstuk 1 af is. Ze gebruiken dezelfde motor; ze vragen
alleen nieuwe kamers en scripts.

## 9. Het laatste hoofdstuk: een gaaf introscherm met muziek

**Het beeld:**
- **Een titelplaatje** (FLUX): de holle kroon boven een donker kasteel, met Eldric in silhouet. Het is een multicolor
  bitmap, met daaronder **HOLLOW CROWN** in een eigen logo-lettertype.
- **Een kleurenloop** door het logo.
- **Een scrolltekst** met het verhaal en de makers.
- **Optioneel:** sterren of vallende as als sprites, of een bliksemflits (achtergrondkleur) op de maat.

**De muziek:**
- **Eigen, originele muziek** voor de SID: een somber fantasythema in een mineurtoonsoort, drie stemmen (bas, akkoorden of
  arpeggio, melodie).
- **Twee manieren:**
  - componeer in een tracker (bijvoorbeeld GoatTracker 2) en exporteer de speler met de data;
  - schrijf de noten in een Python-bestand en maak er data voor een eigen kleine speler in de IRQ van.
- **Gebruik geen bestaande nummers** zonder toestemming van de eigenaar.
- **Controle zonder oren:** lees in VICE elke paar beelden de SID-registers (`$D400-$D418`) en vergelijk de toonhoogtes
  met de noten.
- Het thema keert in het spel terug, in de herberg en bij de titel van elk hoofdstuk. **F1** zet het uit.

**Afsluiten:** spatie of vuur start het spel. Zet daarna de IRQ's en de SID netjes terug, en laat geen toon hangen.

## 10. Bronnen (om te lezen, niet om te kopiëren)

- ScummVM, de werkwoorden en de schermindeling van de C64-versies: [engines/scumm/verbs.cpp](https://github.com/scummvm/scummvm/blob/master/engines/scumm/verbs.cpp)
  en [engines/scumm/scumm.cpp](https://github.com/scummvm/scummvm/blob/master/engines/scumm/scumm.cpp) (`initScreens`).
  - **Werkwoorden:** 3 rijen in kolommen 0/8/15/24/32 (Maniac Mansion).
  - **Inventaris:** 2 rijen × 2 kolommen, met pijlen in het midden (pixels 144-176).
  - **Zinregel:** bovenaan de balk.
  - **Zak C64:** de kamer op pixelrij 17-145.
- *The Mansion – Technical Aspects* (C64 Maniac Mansion: charset-kamers, maskers, multiplex-sprites, 82 opcodes, laden
  in stappen): <https://www.pagetable.com/?p=603>
- *mm-explained*, een becommentarieerde disassembly van Maniac Mansion op de C64. Lees hem voor de opbouw (zinsysteem,
  walkboxes, raster-IRQ-sprites); de licentie is onbekend, dus kopieer niets: <https://github.com/pditincho/mm-explained>
- *Caren and the Tangled Tentacles*, een modern C64-adventure (eigen 6502-motor, scripttaal naar asm, pathfinding,
  bediening met één knop): <https://www.astro.physik.uni-potsdam.de/~mwendt/caren>
- *Zak McKracken and the Alien Mindbenders*, C64: <https://www.c64-wiki.com/wiki/Zak_McKracken_and_the_Alien_Mindbenders>
- ScummVM-tickets over de C64-schermindeling (pixeloffsets van de balk): <https://bugs.scummvm.org/ticket/11971>
- SCUMM in het algemeen: <https://en.wikipedia.org/wiki/SCUMM>
