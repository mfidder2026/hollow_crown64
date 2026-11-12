---
name: c64-kickassembler
description: Commodore 64 Assembler-programmeren met Kick Assembler 5.x op macOS: 12+1 harde regels, geteste toolchain (KickAss.jar, syntax checker, build.sh, VICE-c64run.py), 21 recepten en 28 praktijklessen uit C64_KICKASS_SKILL.md, plus een getest bouwpakket voor tekstadventures (motor, plaatjes, sprites, muziek), een schermlezende autocoureur om spellen uit te spelen, FLUX-afbeeldingen omzetten naar exacte C64-bitmaps (Koala, hires) en sprites (multicolor, hires), bekende muziek (MIDI of HVSC-SID) op de SID, een intro-pakket: plaatje, titel, scrolltekst en muziek in één commando, een geteste motor voor rollenspellen en Zelda-achtige avonturen (scrollende wereld, kaarten, mensen, tekstvenster, menu, gevechten, opslaan), en netwerk voor twee C64's (C64 Ultimate, WiC64, RR-Net; lockstep zoals BB-LAN).
platform: macos
---
Gebruik deze skill ALTIJD als de gebruiker 6502/6510-machinecode wil voor de Commodore 64 (Kick Assembler), of als bestaande `.asm` nagekeken of gerepareerd moet worden. Doelplatform: echte C64 / VICE, PAL, Kick Assembler 5.x. Schrijft de gebruiker BASIC, gebruik dan de skill `c64-basic-v2`.

**Een intro, titelscherm of demo met een plaatje, tekst en muziek? Gebruik het intro-pakket (§14): één commando**
(`intro/intro.py`) maakt het plaatje met FLUX, zet de muziek om, bouwt en test alles, in ±1,5 minuut. Schrijf zo'n
intro NIET zelf: geen tekst in een bitmap stempelen, geen eigen muziekspeler, geen kleurcellen opmeten. Daar ging in
de Terminator-intro (11 nov 2026) 3,5 uur in zitten zonder dat het werkte.

**Een groot spel (verhaal, strategie, meerdere schermen, laden van diskette)? Lees eerst §15** en
`dune64/DUNE64.md`: hoe ASHKARA (dune64), een werkend C64-spel van de eigenaar, in elkaar zit en waarom het lukte.

**Een rollenspel, een Zelda-achtig avontuur of een ander spel met een wereld om in rond te lopen? Begin met de motor
in §16** (`rpg/c64red/`): een scrollende wereld, kaarten als data, mensen en borden, een tekstvenster, een menu,
gevechten en opslaan, getest op deze Mac. Kopieer hem en verander eerst de data; schrijf geen eigen scrollmotor.

**Twee C64's samen over het netwerk (C64 Ultimate, WiC64, VICE)? Zie §17** (`netwerk/`): één set routines voor alle drie
de soorten hardware, een testserver en een geteste test met twee VICE's. Stuur alleen de invoer (lockstep).

**Een tekstadventure of keuzespel? Begin met het bouwpakket in §11** (`avontuur/`): een geteste motor met intro,
vliegende sprites, muziek, kamers met plaatjes, keuzes en voorwerpen. Je schrijft dan alleen het verhaal en tekent
de plaatjes; geen eigen motor.

**Een plaatje op het hele scherm of sprites van het beeldmodel (FLUX)? Zie §12**: `flux.py` maakt het
plaatje, `c64beeld.py` maakt er exacte C64-data van. Een getitst volledig titelscherm (tekstscherm + Koala-bitmap +
randkleur-cyclius) staat als sjabloon in §12.4.

Dit document bevat de werkwijze en de harde regels. Het volledige naslagwerk (3725 regels: syntax, scripttaal, segments, 21 recepten, checklists, 28 praktijklessen) staat naast dit bestand en wordt geraadpleegd met `sed` (zie §5). Verzin nooit directives, mnemonics of opties die nergens in het naslagwerk staan. Kan iets niet, zeg dat expliciet.

## 0. Skill-map — alles staat hier, altijd bij de hand

```bash
S="$HOME/Library/Application Support/MacAIMagic/Skills/c64-kickassembler"
ls "$S"
```

| Bestand | Rol |
|---|---|
| `KickAss.jar` | Kick Assembler 5.14 (Mads Nielsen) — de assembler zelf |
| `KickAss.cfg` | Standaardopties (`-showmem -symbolfile`); KickAss leest dit automatisch uit zijn eigen map |
| `KickAss3To4Converter.jar` | Zet oude 3.x-broncode om naar 4.x/5.x-syntax |
| `c64_ka_syntax_checker.py` | Statische checker — VERPLICHT vóór elke build |
| `build.sh` | macOS-buildscript: check → assembleren → prg in `build/` (getest op deze Mac) |
| `C64_KICKASS_SKILL.md` | Naslagwerk §0–§19 + appendix A/B — raadpleeg vóór je schrijft (§5) |
| `KickAssembler.pdf` | Officiële handleiding |
| `README.md` | Overzicht van de toolkit |
| `avontuur/` | Bouwpakket tekstadventure: `motor.asm`, `verhaal.asm` (voorbeeld), `scenes.py` + `teken.py` (plaatjes, 40 onderdelen), `voorbeelden.py` (10 scènes), `build.sh` — §11 |
| `flux.py` | Laat het beeldmodel (FLUX.2 Klein) een scène of sprite maken in een stijl die de C64 aankan — §12 |
| `c64beeld.py` | Afbeelding → exacte C64-data: multicolor/hires bitmap, multicolor/hires sprites, sprites voor het bouwpakket — §12 |
| `beeld-voorbeeld/` | Getest: een FLUX-kasteel als bitmap met een FLUX-spook en twee vleermuizen erover (`demo.asm`, `demo.png`) — §12 |
| `muziek.py` | Muziek: een MIDI-bestand → drie SID-stemmen (`info`, `omzetten`), een HVSC-SID nakijken (`sid`), opnemen in VICE en de tonen tonen (`opnemen`, `luister`) — §13 |
| `sidspeler.asm` | De speler die `muziek.py omzetten` in `muziek.asm` zet (3 stemmen, drums, geen zeropage) — §13 |
| `dune64/` | Samenvatting van ASHKARA (github.com/mfidder2026/dune64), een werkend groot C64-spel: `DUNE64.md`, plus getest in Kick Assembler `split_bank3.asm` (bitmap boven, tekst onder, bank 3, pratende patch) en `kleurcyclus.asm` (beweging zonder de bitmap aan te raken) — §15 |
| `rpg/` | De motor voor rollenspellen en actie-avonturen: `RPG.md` (de kern, een nieuw spel beginnen, de Zelda-variant), `c64red/` (het hele spel van de eigenaar met `bouw.sh` voor de Mac) — §16 |
| `netwerk/` | Netwerk voor twee C64's: `net.asm` (C64 Ultimate/UDP, WiC64/TCP, RR-Net/Ethernet achter `net_init`/`net_connect`/`net_send`/`net_recv`), `nettest.asm`, `server.py` (testserver), `duo.py` (twee VICE's), `NETWERK.md` (protocol en lockstep) — §17 |
| `intro/` | Het intro-pakket: `intro.py` maakt in één commando een intro met plaatje, titel, ondertitel, scrolltekst, muziek en effecten (`intro.asm` is getest en blijft ongewijzigd) — §14 |

## 1. Werkvolgorde — bij ELKE opdracht

1. Lees de harde regels (§2) en het relevante deel van het naslagwerk (§5).
2. Kopieer het skelet (§7) naar de werkmap en pas aan. Een **tekstadventure of keuzespel: gebruik het bouwpakket
   (§11)**. Ander groot programma (een spel, eigen charset of sprites)? Lees dan eerst **§10** en leg de geheugenkaart
   en de zeropage vast vóór je code schrijft. Muziek: **§13**. Een intro of titelscherm: **§14**, niet zelf schrijven.
   **Binnen drie stappen moet er iets zijn dat bouwt en draait**; maak het pas daarna mooier.
3. **Groei in kleine stappen.** Eerst één ding dat werkt (één kamer op het scherm), dan het volgende (invoer, de
   volgende kamer, het plaatje). Bouw en draai na hooguit ±100 nieuwe regels. Wie 1500 regels in één keer schrijft,
   krijgt tien fouten tegelijk en raakt de draad kwijt.
4. Draai `build.sh` (§3): syntax-check met **0 ERRORs** en assembleren met **0 errors** zijn verplicht. Los de
   **eerste** fout op, bouw opnieuw; niet vijf fouten tegelijk. `build.sh` noemt de foute regel letterlijk
   (`[build] FOUT in … regel N`, met een hint): verander alleen die regel (§2.15).
5. Draai de prg in VICE met `c64run.py` (§4) en bekijk het screenshot met `view_image`. Pas dán is het af.
6. Lever code + korte uitleg; zeg wat je getest hebt en wat het scherm liet zien.

## 2. De harde regels (veroorzaken ~90% van alle AI-fouten)

1. **`//` is commentaar, `;` is een statement-scheider.** `lda #0 ; set border` voert `set` uit als commando → error.
2. **`[ ]` groepeert, `( )` is indirect.** `lda (2+5)*2` wordt indirect adresseren. Wil je rekenen: `lda #[2+5]*2`.
3. **Elk programma begint met `*=` of een `.segmentdef`/`.file`** — anders weet de assembler niet waar code hoort.
4. **Labels: `loop:` bij definitie, `loop` bij gebruik.**
5. **Illegale opcodes staan standaard aan** (`.cpu _6502` is default). Wil je ze uit: `_6502NoIllegals`.
6. **Immediate-waarden passen in één byte**: `lda #$100` is fout — gebruik `#<label` / `#>label`.
7. **`.var` declareert, `.eval` wijzigt.** `.eval x=1` zonder eerder `.var x` is fout.
8. **Mutabele waarden buiten hun `.define`-blok zijn vergrendeld** (`.lock()`).
9. **Macro's/functies/pseudocommands mogen ná hun aanroep gedefinieerd worden**; alleen `.var`/`.const` moeten vóór het gebruik staan.
10. **Eén sprite = 63 bytes**; de pointer in `$07ff` bevat adres/64.
11. **Zeropage-variabelen: `.label teller = $fb`** ($fb–$fe zijn vrij, §10.2), of een blok met accolades:
    `.zp { teller: .byte 0 }` (getest). `.zp` zonder accolades geeft `Invalid token`.
12. **Laat de assembler rekenen, niet jezelf**: `.fill`/`[i*40]`-tabellen i.p.v. handmatige tabellen.
13. **De index komt na een komma, nooit met `+`.** `lda tekst,x` en `sta $0400+5*40+15,x` werken gewoon:
    absolute,X op het adres + X (getest, ook met `.text`-data). `sta $0400+40*10+x` faalt met `Unknown symbol 'x'`,
    want `+x` is een optelling. `lda label,x` is nooit indirect; indirect is alleen met haakjes: `lda ($fd),y`.
14. **`!`-labels: een naam van letters, cijfers en `_`, en elke verwijzing heeft een richting.** `!lus:` mag vaker
    voorkomen; `bne !lus-` springt naar het vorige `!lus`, `beq !klaar+` naar het volgende (getest).
    - `!t1-done:` is fout: KickAss leest `!t1-` (het vorige `!t1`) en dan `done` → `Syntax error` op de sprong en
      `Invalid token` op het label. Hierop liep de Terminator-intro 10 keer vast (11 nov 2026).
    - `bne !lus` zonder `-` of `+` → `Unknown symbol 'lus'`; de verkeerde richting → `Unknown symbol '!lus-'`.
    - In een macro of over een lange afstand: een gewoon label (`t1_klaar:`, `randOk:`).
15. **Een bouwfout: verander alleen de regel die `build.sh` noemt.** Bij een fout schrijft `build.sh`
    `[build] FOUT in bestand regel N, kolom K`, de regel zelf met een `^` eronder, en vaak een `hint:`. Pas die ene
    regel aan met `edit_file` en bouw opnieuw. Herschrijf het bestand niet en "repareer" geen regels eromheen: in de
    Terminator-intro zat de fout in `beq !t1-done`, terwijl het model de regel erboven verdacht (`lda tekst,x`) en
    het hele bestand 14 keer herschreef. Elke herschrijving bracht nieuwe fouten.
16. **De SID zit op `$d400`–`$d41c`, de VIC op `$d000`–`$d02e`: ze overlappen niet.** Een "SID/VIC-botsing" bestaat
    niet. Wie de SID op `$d000` zoekt, zet met zijn "muziek" sprites aan (`$d015`), het scherm uit (`$d011`) en de
    geheugenwijzers om (`$d018`); zo liep de Terminator-intro twee uur vast (11 nov 2026). Het volume staat in
    `$d418`, nooit in `$d018`. Alle SID-registers staan in §6.

Extra struikelblok: **`.const` schrijf je MET punt** — `const X=1` is de gemaakte typefout nr. 1.

## 3. Bouwen op deze Mac (alles getest 10 nov 2026)

Java: **`/usr/bin/java` is op deze Mac een defecte stub** — gebruik `/opt/homebrew/opt/openjdk/bin/java` (OpenJDK 27). `build.sh` zoekt zelf een werkende Java en vindt de jar en checker ook in deze skill-map, dus je hebt alleen `build.sh` zelf nodig in de werkmap.

```bash
S="$HOME/Library/Application Support/MacAIMagic/Skills/c64-kickassembler"
cd <werkmap> && cp "$S/build.sh" . && chmod +x build.sh
./build.sh main.asm                 # syntax-check + assembleren; prg + .vs in build/
./build.sh main.asm --vice          # ... en start zichtbare VICE
./build.sh                          # 1 .asm in map wordt automatisch gekozen
./build.sh main.asm -define DEBUG   # rest gaat rechtstreeks naar KickAss
./build.sh --check-only main.asm    # alleen de checker
```

Handmatig (dezelfde stappen):

```bash
python3 "$S/c64_ka_syntax_checker.py" main.asm     # exit 0 = ok (warnings mogen)
/opt/homebrew/opt/openjdk/bin/java -jar "$S/KickAss.jar" \
    -vicesymbols -showmem -o build/main.prg main.asm
```

Checker-exitcodes: `0` = 0 ERRORs (bouw mag), `1` = ERRORs (eerst repareren), `2` = usage-fout. De checker vangt o.a.: `;`-commentaar (als warning), `(`-indirectie, onbekende directives/mnemonics, verkeerde adresseringsmodi, waarden >255 in byte-context, `.for`-kop zonder dubbele puntkomma's, dubbele labels, ontbrekende `#import`-bestanden, raster-IRQ zonder `$d019`-bevestiging, vector die eindigt via de kernal. NIET gecheckt (assembleren blijft verplicht): branch-afstand ±127, memory-overlaps, zeropage-keuze, én regel 13 hierboven — daar gaf de checker `0 errors, 0 warning(s)` op.

**Valstrik (getest):** een `.file [name="x.prg", ...]` in de bron negeert `-o` en schrijft zijn prg naast de bron. `build.sh` verzamelt daarom alle vers geschreven `.prg`-bestanden in `build/`.

## 4. Testen in VICE (verplicht — de checker is geen emulator)

VICE staat in `/Applications/vice-arm64-gtk3-3.9`. Gebruik `c64run.py` uit de BASIC-skill (werkt ook voor machinecode-prg's): startt VICE verstopt (warp, geen geluid), typt invoer, print het C64-scherm als tekst, meldt BASIC-fouten als `FOUT: ...`, sluit VICE zelf af.

```bash
R="$HOME/Library/Application Support/MacAIMagic/Skills/c64-basic-v2/c64run.py"
python3 "$R" build/main.prg --wait 3 --max 30 --shot main.png
```

**De tekst van `c64run.py` is in kleine letters**, ook waar het scherm HOOFDLETTERS toont: `ready.` en `terminator`
staan op het C64-scherm als READY. en TERMINATOR (getest 11 nov 2026). `aaaa` is dus schermcode 1 (A), geen ASCII of
PETSCII $61. Een rij `aaaa` waar tekst hoort, betekent meestal dat er een kleurwaarde 1 (wit) in het scherm-RAM is
geschreven in plaats van in het kleur-RAM ($d800).

Bekijk `main.png` altijd met `view_image` (moet dafür binnen de werkmap staan): bitmap, sprites en kleuren zie je alleen op het scherm. Een programma dat in een `jmp *`-lus hangt is OK — `c64run.py` sluit na `--max` netjes af. Wil de gebruiker het zelf zien:
`open -a "/Applications/vice-arm64-gtk3-3.9/x64sc.app" --args -autostart "$PWD/build/main.prg"`.

**Eigen monitor-scripts** (als c64run.py niet genoeg is): kies een vrije poort zoals `c64run.py` (socket op poort 0)
en laat `Monitor(port)` tot 20× opnieuw verbinden met 1 s tussenpoos. VICE pakt maar één monitorverbinding tegelijk.
**Nooit `pkill -f x64sc` of `killall x64sc`**: dat sluit ook de VICE van de gebruiker en van andere tests af (gezien
11 nov 2026). Sluit alleen je eigen VICE: start hem met `start_new_session=True` en stop hem met `os.killpg`, zoals
`c64run.py` doet; `c64run.py` zelf sluit zijn VICE altijd.

## 5. Naslagwerk raadplegen — per deel, nooit alles tegelijk

`C64_KICKASS_SKILL.md` is 3725 regels; lees het gewenste deel met `sed -n`:

```bash
sed -n '31,49p' "$S/C64_KICKASS_SKILL.md"   # §1 harde regels (uitgebreid)
```

| Paragraaf | Regels | Onderwerp |
|---|---|---|
| §0–§2 | 17–149 | werkwijze, harde regels, toolchain + checker-opties |
| §3 | 150–299 | syntax: mnemonics, adresseringsmodi, getallen, labels, zeropage |
| §4 | 300–501 | `*=`, data, encodings, binary-import, console |
| §5 | 502–751 | scripttaal: variabelen, types, math, strings, lijsten/structs |
| §6 | 752–891 | functies, macro's, pseudocommands |
| §7 | 892–946 | preprocessor `#if`/`#import`/`#define` |
| §8 | 947–1114 | scopes en namespaces |
| §9 | 1115–1356 | segments (definiëren, uitvoer, grenzen, modifiers) |
| §10 | 1357–1397 | `.file` en `.disk` (prg/d64) |
| §11 | 1398–1543 | commandline-variabelen, binary/SID/gfx-import, label-export |
| §12 | 1544–1626 | BasicUpstart, opcode- en kleurconstanten |
| §13 | 1627–2620 | **21 recepten**: raster-IRQ (1631), kernal overnemen (1689), sprites (1743), SID (1804), Koala (1840), PAL/NTSC-detect (2385), kernal-routines (2456) … |
| §14 | 2621–2675 | koppeling met de BASIC-pipeline |
| §15–§16 | 2676–2778 | veelgemaakte fouten + verificatiechecklist |
| §17 | 2779–2922 | twee complete templates |
| App. A/B | 2923–3011 | adresseringsmodi per mnemonic; directive-overzicht |
| §18 | 3012–3456 | 16 praktijklessen (Captain Cock) |
| §19 | 3457–3725 | 12 praktijklessen (Super Pong) |

## 6. Belangrijkste praktijklessen (volledig in §18/§19)

- **Zeropage-conflict is DÉ klassieke valstrik** (§18.2): de kernal overschrijft je eigen zp-variabelen. Welke bytes vrij zijn staat in **§10.2**.
- **Screencode vs PETSCII** (§18.3/§18.4): direct naar `$0400` = screen codes (`.encoding "screencode_mixed"`), via kernal `$ffd2` = PETSCII. Verkeerd gekozen = scherm vol groene staafjes. Let op: `.encoding` geldt per bestand/segment — zet hem vóór je `.text`-regels.
- **`BasicUpstart2(main)` zonder eigen `*=$0801`** (§18.8).
- **Sprite x-hi bits niet wissen bij update** (§19.3): met `and`/`ora` maskeren, anders glitch sprites aan de schermrand.
- **Branch ±127 bytes** (§19.10): de checker ziet het niet; gebruik de pseudocommands uit **§10.3** (`jeq`, `jne`, …).
- **Raster-IRQ always ack**: bij binnenkomst eerst `asl $d019`, bij het einde `jmp $ea31` (of zelf het raster-bit zetten en `rti`).
- **Na elke build de geheugenkaart lezen** (output `-showmem`): controleer segmentgrenzen en dat code/data niet botsen.
- **Eigen klok in een snelle lus: NOOIT `inc $a2`** (getest, titelscherm nov 2026). De lus draait duizenden keren
  per beeldveld; `and #$1f` is dan elke scanlijn waar en een `sta $d020` daarachter geeft een ruitjes-rand i.p.v. een
  kleurcyclius. Gebruik de **kernal-jiffies** met een rand-detectie, één keer per jiffy:
  ```asm
  rand:   lda $a2          // telt vanzelf, 60 per seconde (cli + kernal-IRQ!)
          cmp $fc          // al een nieuwe jiffy?
          beq toets
          sta $fc
          inc $fe          // deler: pas elke 16 jiffy's echt iets doen
          lda $fe
          and #$0f
          bne toets
          ...kleur wijzigen...
  ```
- **Toetsenbuffer = `$0277`, aantal toetsen in `$c6`** — `$cb` is de JOY-counter (alleen niet-nul bij een
  gamepad-toets). Wachten op om het even welke toets: `lda $c6; bne ...`. Poken via de monitor in één sessie:
  `> 0277 0d` + `> 00c6 01`. Na `autostart` van een prg kan de buffer al RESTEN bevatten; `sta $c6` bij het begin.
- **$d018 in bitmapmodus** heeft de ROM-charset nodig als je geen eigen charset kopieert: `#$38` (bitmap $2000,
  scherm $0c00, rom-tekens) werkt in RAM-bank $4000 zonder kopie — de VIC haalt teken-data uit de ROM-view $d000.
- **Een bekend nummer als muziek? Gebruik §13** (een HVSC-SID of een MIDI met `muziek.py`), niet een eigen speler.
- **De SID zelf aansturen: alles op `$d400`–`$d41c`** (§2.16). Proef in VICE (11 nov 2026): na het voorbeeld
  hieronder stonden `$d011`, `$d015` en `$d018` nog op hun beginwaarde, er ging geen sprite aan, en `$d41b` gaf bij
  elke keer lezen een andere ruiswaarde. Elke stem heeft 7 registers: stem 2 = stem 1 + 7, stem 3 = stem 1 + 14.

  | Stem 1 | Stem 2 | Stem 3 | Inhoud |
  |---|---|---|---|
  | `$d400`/`$d401` | `$d407`/`$d408` | `$d40e`/`$d40f` | frequentie laag/hoog (PAL: Hz × 17,03; A4 = 440 Hz = `$1d45`) |
  | `$d402`/`$d403` | `$d409`/`$d40a` | `$d410`/`$d411` | pulsbreedte laag / hoog (bits 0–3) |
  | `$d404` | `$d40b` | `$d412` | besturing: bit 0 gate, 1 sync, 2 ringmodulatie, 4 driehoek, 5 zaagtand, 6 puls, 7 ruis |
  | `$d405` | `$d40c` | `$d413` | attack (bits 4–7), decay (bits 0–3) |
  | `$d406` | `$d40d` | `$d414` | sustain (bits 4–7), release (bits 0–3) |

  Voor alle stemmen samen: `$d415`/`$d416` filterfrequentie (laagste 3 bits / hoogste 8 bits), `$d417` resonantie
  (bits 4–7) en welke stemmen door het filter gaan (bits 0–2), `$d418` volume (bits 0–3) en filtermodus (bit 4
  laag-, 5 band-, 6 hoogdoorlaat; bit 7 zet stem 3 stil). Teruglezen kan alleen `$d41b` (oscillator 3; met ruis een
  toevalsgetal) en `$d41c` (envelope 3); van de andere registers houd je de waarde zelf bij.

  ```asm
          lda #$0f
          sta $d418       // volume 15, geen filter
          lda #$45        // stem 1: A4
          sta $d400
          lda #$1d
          sta $d401
          lda #$09
          sta $d405       // attack 0, decay 9
          lda #$a9
          sta $d406       // sustain 10, release 9
          lda #$21
          sta $d404       // zaagtand + gate: de toon begint
          // ... later:
          lda #$20
          sta $d404       // gate uit: de release begint
  ```

## 7. Kleinste werkend programma (checker 0/0, KickAss 5.14: 0 errors, getest in VICE)

```asm
// main.asm — rand en achtergrond zwart
:BasicUpstart2(main)

main:
    lda #0
    sta $d020
    sta $d021

halt:
    jmp halt
```

Volledig skelet met segments, tekst op scherm en raster-IRQ: `sed -n '2784,2870p' "$S/C64_KICKASS_SKILL.md"` (§17.1 — getest in VICE: toont tekst in lichtblauw en een knipperende rand via raster-IRQ). Bibliotheekbestand: regels 2870–2922.

## 8. Oudere broncode (KickAss 3.x)

```bash
/opt/homebrew/opt/openjdk/bin/java -jar "$S/KickAss3To4Converter.jar" -conv old.asm
```

## 9. Opleverchecklist

- [ ] `//`-commentaar, `[ ]`-groepering, `.const`/`.var`/`.eval`/`.label .zp` correct gebruikt (§2)
- [ ] Adres-expressies met index: `.const POS` + `POS,x` of `[$expr],x`, nooit `$expr+x` (regel 13)
- [ ] `build.sh`: checker **0 ERRORs** en assembleren **0 errors** (§3)
- [ ] Geheugenkaart uit `-showmem` nagelopen: geen overlaps, segmentgrenzen kloppen
- [ ] `c64run.py`: programma draait, geen `FOUT:`, screenshot met `view_image` bekeken (§4)
- [ ] Niet verzonnen: elke directive/mnemonic komt uit §3–§12, App. A/B of het PDF
- [ ] Zeropage alleen uit §10.2 (nooit `$90`–`$fa` naast de kernal); `.errorif`-grenzen uit §10.1 staan in de bron
- [ ] Tekst in `.text`/`REGEL`: zuivere ASCII (geen é, ë, —) en overal ≤ de maximale breedte (met een kort Python-controle-script vóór de build tellen; de melding van de assembler noemt alleen het record, niet de regel)
- [ ] Keuzespel: winroute én één doodroute uitgespeeld met de autocoureur (§11.5)
- [ ] Les gevonden? Voeg hem toe aan deze skill (create_skill) én aan `MACAIMAGIC.md` onder Geleerd

## 10. Grote programma's — wat misging bij "spookslot" (10 nov 2026)

Een tekstadventure van 1500 regels werd in één keer geschreven en daarna anderhalf uur gerepareerd: Python-scripts
die de bron herschreven en stil niets deden, een verhaal dat niet meer onder `$2000` paste, branches te ver,
`.byte` met tekst, en zeropage-adressen die de kernal overschrijft. Doe het zo:

### 10.1 Geheugenkaart eerst — en laat de assembler hem bewaken

De VIC ziet maar 16 KB tegelijk (bank 0 = `$0000`–`$3fff`), en in bank 0 ziet hij op `$1000`–`$1fff` de ROM-tekens:
een eigen charset of sprites daar zijn onzichtbaar. Code mag er wel staan. Tekst die alleen de CPU leest, mag overal
tot `$9fff` (vanaf `$a000` ligt de BASIC-ROM over het RAM). Getest (KickAss 5.14 + VICE: eigen teken uit `$3800`
en tekst uit `$4000` op het scherm):

```asm
.encoding "screencode_upper"
.const SCRN     = $0400
.const CODE_END = $3000          // $0801-$2fff: BASIC-regel, code, tabellen, variabelen (~10 KB)
.const SPRITES  = $3000          // $3000-$37ff: 32 sprites van 64 bytes (pointer = (adres&$3fff)/64)
.const CHARSET  = $3800          // $3800-$3fff: eigen charset (2 KB)
.const DATA     = $4000          // $4000-$9fff: verhaal en teksten, alleen voor de CPU (24 KB)
.const DATA_END = $a000
.function toD018(s,c) { .return (((s&$3fff)/$400)<<4) | (((c&$3fff)/$800)<<1) }

        BasicUpstart2(main)
main:   lda #toD018(SCRN, CHARSET)
        sta $d018
        // ... alle code en variabelen hier ...
        .errorif * > CODE_END, "code loopt over de sprites heen: $" + toHexString(*)

        *= SPRITES "Sprites"
        .import binary "sprites.bin"
        *= CHARSET "Charset"
        .import binary "charset.bin"
        *= DATA "Verhaal"
        #import "story.asm"      // de .encoding van hierboven geldt ook in story.asm (getest)
        .errorif * > DATA_END, "verhaal loopt de BASIC-ROM in: $" + toHexString(*)
```

Botst toch iets, dan meldt KickAss zelf `the memoryblock 'X' overlaps 'Y'` (getest). Zet géén tweede `*= * "Code"`
na het verhaal: alle code staat in het eerste blok.

### 10.2 Zeropage naast de kernal

Draait de kernal mee (IRQ via `jmp $ea31`, `GETIN` `$ffe4`, `CHROUT` `$ffd2`, `CLRSCR` `$e544`), dan:

| Adressen | Vrij? |
|---|---|
| `$fb`–`$fe` | **vrij** — twee pointerparen |
| `$02`–`$8f` | **vrij** zolang het programma nooit terug naar BASIC gaat (BASIC-werkruimte; de kernal schrijft er niet, nagekeken in kernal 901227-03) |
| `$90`–`$fa` | **nooit**: kernal-werkruimte. `$c5`/`$c6`/`$cb` toetsenbord, `$d1`–`$d6` cursor, `$d9`–`$f2` regeltabel (`CLRSCR` herschrijft hem), `$f3`/`$f4` kleurpointer, **`$f5`/`$f6` schrijft de toetsenbordscan elke IRQ zodra er een toets is ingedrukt** (`$ea9d`/`$eaa1`) |

Valkuil: `c64run.py` typt via de toetsenbuffer (`$0277`/`$c6`), niet via de toetsenmatrix. Een variabele op `$f5`
blijft in de test dus heel; pas als iemand echt een toets indrukt, gaat hij stuk. Een test die slaagt bewijst hier niets.

### 10.3 Verre branches: pseudocommands (getest, checker 0/0)

```asm
.pseudocommand jeq doel {
        bne !+
        jmp doel
!:
}
.pseudocommand jne doel {
        beq !+
        jmp doel
!:
}
// zo ook jcc (bcs !+), jcs (bcc !+), jpl (bmi !+), jmi (bpl !+)
```

Gebruik: `jeq verWeg` in plaats van `beq verWeg`. Kost 3 bytes extra, werkt altijd.

### 10.4 Bronbestanden wijzigen

- Wijzig `.asm` met **`edit_file`**: die zegt het als de oude tekst niet bestaat. Een Python-script met
  `s.replace(oud, nieuw)` doet dan stil niets, en daarna weet je niet meer wat er in het bestand staat.
- Moet het toch met een script, controleer elke vervanging: `assert s.count(oud) == 1, oud[:40]`. En in Python is
  `#` commentaar, niet `//`.
- Twijfel over wat er nu in het bestand staat: lees het stuk opnieuw (`sed -n '120,160p' x.asm`), niet uit je geheugen.

### 10.5 Data met tekst

`.byte` neemt alleen getallen, `.text` alleen tekst. Een record met beide is een macro (zo werkte het in spookslot):

```asm
.macro LINE(rij, kleur, tekst) {
        .byte rij, kleur
        .text tekst
        .byte 0
}
        LINE(3, 1, "DE KASTEELPOORT")
```

### 10.6 Twee keer fout? Zoek op, gok niet

Werkt een directive of schrijfwijze twee keer niet, zoek hem dan op in plaats van een derde variant te proberen:
`grep -n "namespace" "$S/C64_KICKASS_SKILL.md" | head`, dan dat stuk lezen met `sed -n`. Scopes: §8,
segments: §9, macro's en pseudocommands: §6.

**Twee keer dezelfde fout op dezelfde regel?** Dan klopt je idee over de oorzaak niet. Maak een testbestand van
vijf regels met alleen die ene constructie, bouw het (`./build.sh test.asm`) en verander er telkens één ding aan.
Pas als het testbestand bouwt, verander je het echte bestand, en alleen op die regel.

## 11. Tekstadventure in een paar stappen — het bouwpakket `avontuur/`

Getest 10 nov 2026: KickAss 5.14 + checker 0/0, en in VICE uitgespeeld tot gewonnen en tot dood ("Het Spookslot"
3 kamers en "Graaf Draculesti" 9 kamers, beide in eigen werkmap).

| Scherm | Wat |
|---|---|
| intro | plaatje + titel (rij 0-23), sprites vliegen erdoor (achter het plaatje langs), muziek, "Druk op een toets" |
| rij 0-8 | plaatje van de kamer (kleurenblokjes uit `scenes.py`, of tekens) |
| rij 9 | streep |
| rij 10-17 | kamertekst, of een melding (tot rij 22) |
| rij 18-23 | keuzes `A)`-`F)`; alleen die nu kunnen (vlaggen) |
| rij 24 | `I = wat je draagt` |

### 11.1 De stappen

1. **Kopieer en bouw het voorbeeld** — zo weet je dat alles werkt vóór je iets verandert:
   ```bash
   S="$HOME/Library/Application Support/MacAIMagic/Skills/c64-kickassembler"
   cp -R "$S/avontuur/." . && python3 scenes.py && ./build.sh spel.asm
   ```
2. **Plan het verhaal in je antwoord**: kamers (tot ~25), vlaggen en voorwerpen (16), welke keuze wat nodig heeft,
   hoe je wint en hoe je doodgaat. Elke kamer heeft een uitweg; er is een route naar `GEWONNEN`.
3. **Schrijf `verhaal.asm`**: vervang het voorbeeld kamer voor kamer en bouw na elke 2-3 kamers. Teksten en
   kamers zoek je op internet als de gebruiker dat vraagt; de vorm blijft die van de macro's hieronder.
4. **Teken de plaatjes in `scenes.py`** (§11.3): bekijk eerst `catalogus.png` en `voorbeelden.png`, neem de scène
   die het dichtst bij je kamer ligt als begin, draai `python3 scenes.py` tot er geen `LET OP` meer staat, en
   bekijk `plaatjes.png` met `view_image`.
5. **Speel het uit** met de autocoureur (§11.5): de hele route naar winst, één dood, en een screenshot per penting scherm.
6. Hernoem `spel.asm` gerust (`spookslot.asm` → `build/spookslot.prg`).

`motor.asm` pas je niet aan. Kan de motor iets niet (een parser met werkwoorden, een tweede speler), zeg dat de
gebruiker en vraag of je hem moet uitbreiden, in plaats van hem stilletjes om te bouwen.

### 11.2 `verhaal.asm` in het kort (uitleg staat ook bovenin het bestand)

| Macro | Betekenis |
|---|---|
| `.const LAMP = 1 << 0` | vlag (16 stuks); `VOORWERP("een lamp")` nummer n geeft vlag 1<<n een naam, `VOORWERP("")` = geheime vlag |
| `poort: KAMER(plaatje, tekst, keuzes)` | een kamer; plaatje mag `GEEN` |
| `REGEL("...")` / `KLEURREGEL(GEEL, "...")` | tekstregel, max 40; blok sluiten met `TEKST_EINDE()` (max 8) of `MELDING_EINDE()` (max 13) |
| `KEUZE(tekst, nodig, verberg, zet, melding, naar)` | tekst max 37; zichtbaar als alle `nodig` aan staan en geen `verberg`; zet `zet`; toont `melding`; gaat `naar` een kamer, `BLIJF`, `GEWONNEN` of `DOOD`. Lijst sluiten met `KEUZES_EINDE()` (max 6) |
| `PLAATJE_POORT()` + `PRENT_EINDE()` | het plaatje uit `scenes.py` |
| `PRENTK("tekst", "kleuren")` | 40 tekens met per teken een kleur (`0`-`f`); handig voor een titel |
| `SPRITEREGEL("....##....")` ×21 + `SPRITE_EINDE()` | sprite 24×21, `#` = aan |
| `VLIEGER(vorm1, vorm2, kleur, rij, snelheid)` | sprite in de intro op tekstrij `rij`; wisselt van vorm (vleugels op/neer) |
| `KLANK(golf, ad, sr)`, `NOOT(midi, duur)`, `MUZIEK_EINDE()` | muziek in de intro; 60 = C4, 69 = A4; duur in 1/60 s |

Patronen: **voorwerp pakken** `KEUZE("Pak de lamp", GEEN, LAMP, LAMP, mLamp, BLIJF)` (verdwijnt daarna).
**Deur op slot**: `KEUZE("Open de deur", GEEN, SLEUTEL, GEEN, mOpSlot, BLIJF)` én `KEUZE("Open de deur", SLEUTEL,
GEEN, GEEN, GEEN, kelder)`. **Eenmalig iets** (vampier verzwakt): zet een geheime vlag en verberg de keuze erop.
**Ritueel in vaste volgorde** (kruis → water → staak): elkaaris `nodig`/`verberg` laten controleren, één keuze per
stap, elke stap zijn eigen geheime vlag; de slotkeuze-eis alle vlaggen.

Elke fout zegt de assembler in gewone taal: te lange regel, te veel keuzes, een teken zonder kleur, een onbekende
kleur, een oneven aantal pixelregels. Lees de melding en pas precies dat aan.

### 11.3 Mooie plaatjes — waarom ze "net niet" waren, en hoe het wel moet

Wat er misging in eerdere spellen: ASCII-art van internet met `\ _ | ~ ^ { }` (bestaan niet of zijn `£ ← ↑` op de
C64; in spookslot waren `[ \ ] ^ _` zelfs omgebouwd tot kasteeltjes en kistjes), één kleur per regel (plat),
regels die niet even breed waren (kolommen verschoven), en een screenshot van 384×272 dat "wel goed" leek.

Teken daarom met **`scenes.py`**: een doek van 80×18 pixels (kamer, rij 0-8) of 80×28 (intro, rij 0-13). Elk
blokje van 2×2 pixels wordt één teken met één kleur tegen zwart.

**Begin met kijken** — dan weet je wat er kan:
```bash
python3 teken.py --catalogus     # catalogus.png: elk onderdeel zoals de C64 het laat zien
python3 voorbeelden.py           # voorbeelden.png: tien complete scènes (kerkhof, bos, dorp, bibliotheek,
                                 # kerker, torenkamer, meer, eetzaal, crypte, kasteel) — bekijk met view_image
```
Kies de scène die het dichtst bij je kamer ligt, kopieer die regels uit `voorbeelden.py` naar `scenes.py`, en pas
aan. Zo zijn ook de plaatjes van het voorbeeldspel gemaakt. (Een voorbeeld ongewijzigd gebruiken kan ook:
`#import "voorbeelden.asm"` bovenin `verhaal.asm` en `VOORBEELD_KERKHOF()` als plaatje.)

**Onderdelen** (`x` = het midden, `voet` = de rij waar het op staat; standaard net boven de grond). Ze zetten
zichzelf op het raster van 2×2, dus ramen, vlammen en ogen vallen nooit weg:

| Buiten | Binnen | Wezens en dingen |
|---|---|---|
| `lucht(sterren)`, `maan(x, y, r, sikkel=)` | `binnen(vloer=, plint=, stenen=)` | `spook(x, y)`, `vleermuis(x, y)` |
| `bergen(top)`, `wolk(x, y, breedte)` | `raam(x, top, breedte, hoogte, maan=)` | `ogen(x, y, kleur)` (gloeiend in het donker) |
| `grond(kleur)`, `heuvel(hoogte, golf, kleur)`, `water(top)` | `deur(x, breedte=, hoogte=, kleur=, open=)` | `skelet(x)`, `vampier(x)` |
| `boom(x, soort="dood"/"den"/"loof")`, `bos(x0, x1)` | `trap(x0, treden=)`, `pilaar(x)`, `gewelf(x0, x1)` | `doodskist(x, open=, vampier=)` |
| `toren(x, breedte, top, dak=)`, `muur(x0, x1, top)` | `kaars(x, voet)`, `kandelaar(x)`, `kroonluchter(x, breedte)` | `schatkist(x, open=)` |
| `huis(x, breedte=, muur=, dak=)`, `kerk(x)` | `schilderij(x, top)`, `tralies(x0, x1, top=)` | `blok(x, y, kleur)`: één eigen blokje |
| `grafsteen(x, kruis=)`, `hek(x0, x1, hoogte=)`, `brug(x0, x1, y)` | | en vrij: `rechthoek cirkel ovaal lijn driehoek dak boog` |

Kleuren: `ZWART` (= achtergrond) `WIT ROOD CYAAN PAARS GROEN BLAUW GEEL ORANJE BRUIN ROZE DONKERGRIJS GRIJS
LICHTGROEN LICHTBLAUW LICHTGRIJS`.

**Het recept voor elke scène** (in deze volgorde tekenen; wat later komt ligt ervoor):
1. **lucht of muur**: `lucht()` buiten, `binnen()` binnen.
2. **verte**: maan, bergen, bos, wolken.
3. **het onderwerp**, groot: kasteel, kerk, boekenkasten, haard, doodskisten.
4. **voorgrond**: `grond()`, hek, grafstenen, tafel.
5. **lichtpunten en wezens**: verlichte ramen, kaarsen, rode ogen, een vleermuis. Die maken de sfeer.

**Compositie** — hier ging het in de proef het vaakst mis:
- Geef elk ding een **eigen plek in de breedte**: links (x 0-25), midden (26-53), rechts (54-79), met zwart ertussen.
  Dingen over elkaar heen (een kandelaar voor een schilderij, kaarsen voor een raam) worden een rommelige vlek.
- Eén onderwerp in het midden, bijzaken links en rechts. Niet meer dan 5-6 dingen per scène.
- Een bewuste overlap mag: een kale boom vóór de maan, een toren die half achter de maan zit.
- Zwart is de achtergrond. Een klein detail op een gekleurd vlak (raam in een toren, ogen in een gezicht) alleen met
  `blok()` of een onderdeel dat het al goed doet.
- 3 tot 5 kleuren per scène; donker (grijs, bruin) voor grote vlakken, fel (geel, rood, wit) voor de lichtpunten.
- Teken het scherm ALLEEN wat er in die kamer nog is: een keuzelijst van de motor (rij 18-23) mag niet door het
  plaatje heen; ogen van slapende/weggelopen wezens wegtekenen als de tekst ze niet meer noemt (past de scène bij
  de tekst, dan is het één).

**Kijk na elke wijziging**: `python3 scenes.py` zegt `alles komt goed op de C64`, of noemt elk detail dat
wegvalt (`LET OP POORT: een geel ding bij x=.., y=.. is op de C64 WEG`). Bekijk daarna `plaatjes.png`: links
staat wat de C64 laat zien, rechts je tekening. Ziet het er rommelig uit, verschuif dan dingen. Teken het niet
nóg voller.

### 11.4 Intro en sprites

- Intro = `PLAATJE_INTRO()` (doek van 28 hoog = rij 0-13) + titel met `PRENTK` + 2-3 regels; samen max 24 rijen.
- Sprites vliegen **achter** het plaatje langs (achter torens en maan: mooi), dus zet een `VLIEGER` op een rij met
  lucht, anders zie je hem niet. Geef hem twee vormen (vleugels op en neer).
- In warp beweegt alles te snel om te zien: test de intro met `--nowarp` en maak screenshots met een andere
  `--wait`. `--sprites` ziet de intro-sprites in warp níet (de monitor-stops verstoren de animatie); één screenshot
  `--nowarp --wait 6` (één VICE tegelijk) bewijst dat ze vliegen.

### 11.5 Testen en uitspelen — de autocoureur

`c64run.py` is goed voor één scherm, maar een vaste lijst `--type`-toetsen is foutgevoelig: keuzes verdwijnen zodra
je een voorwerp pakt, letters verschuiven, en `petscii()` van c64run voegt ALTIJD een RETURN toe — die sluit een
melding meteen af, waardoor alles één stap achterloopt. **Gebruik daarom een schermlezende autocoureur** (`speel.py`,
in de werkmap zetten; sjabloon hieronder). Planbestand: per regel een tekstfragment uit de gewenste keuzeregel of
`ENTER`. De coureur leest het C64-scherm via de VICE-monitor, zoekt de regel `X) ...fragment...` en drukt die letter.

**Harde lessen over toetsen naar VICE (getest nov 2026):**
- Pook de toets in ÉÉN gestopte monitor-sessie: `mon.run(["> 0277 <hex>", "> 00c6 01", "m 00c6 00c6"])`.
  Poke en `m 00c6` in twee aparte `mon.run`-sessies: de C64 hervat ertussen en de buffer is alweer leeg (GETIN heeft
  hem op). Laat de dump ín dezelfde sessie zien dat `00c6=01` blijft staan.
- Stuur de keuzetoets als PETSCII-hoofdletter `ord('A')`=65=$41 (de motor rekent met `sbc #$41`). `chr`-waarden
  `-32` of een kleine letter (=$61) lezen als verkeerde toets; `petscii()` doet die -32 zelf al, dus nooit zelf ook.
- Na een keuze met melding: de RETURN pas nádat het meldingsscherm gestabiliseerd is (wacht op verandering, dan op
  stilstand, anders eet je de volgende al).
- Wacht patroon per stap: poll tot het scherm verandert (max ~20 s), daarna tot het 0,5 s stilstaat.

Sjabloon (`speel.py`, werkt samen met c64run.py uit de BASIC-skill):

```python
#!/usr/bin/env python3
"""speel.py plan.txt shot.png — lees het scherm, druk de juiste letter."""
import os, re, sys, time, signal, subprocess
sys.path.insert(0, os.path.expanduser("~/Library/Application Support/MacAIMagic/Skills/c64-basic-v2"))
from c64run import Monitor, screen_text, free_port, close
VICE = "/Applications/vice-arm64-gtk3-3.9/bin/x64sc"
prg, planfile, shot = sys.argv[1], sys.argv[2], sys.argv[3]
plan = [l.strip() for l in open(planfile) if l.strip()]
port = free_port()
vice = subprocess.Popen([VICE, "-default", "+sound", "-warp", "-logfile", os.path.abspath("vice_speel.log"),
    "-remotemonitor", "-remotemonitoraddress", f"ip4://127.0.0.1:{port}", "-autostart", os.path.abspath(prg)],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
group = os.getpgid(vice.pid)
mon = Monitor(port)
def stop(*_):
    close(vice, group, mon); sys.exit(1)
signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
def read_screen(old=None):
    if old is not None:
        for _ in range(40):
            s = screen_text(mon.run(["m 0400 07e7"]))
            if s != old: break
            time.sleep(0.6)
    s = screen_text(mon.run(["m 0400 07e7"]))
    for _ in range(8):
        time.sleep(0.5)
        a = screen_text(mon.run(["m 0400 07e7"]))
        if a == s: break
        s = a
    return s
def druk(text):
    keys = [13] if text == "" else [ord(text[0].upper())]   # hoofdletter $41-'F'; RETURN = 13
    mon.run(["> 0277 " + " ".join(f"{k:02x}" for k in keys), f"> 00c6 {len(keys):02x}", "m 00c6 00c6"])
time.sleep(6)
screen = read_screen()
for stap in plan:
    letter = ""
    if stap.upper() != "ENTER":
        letter = next((m.group(1) for l in screen.splitlines()
                       if (m := re.match(r"\s*([A-F])\)\s+(.*)", l)) and stap.lower() in m.group(2).lower()), None)
        if not letter:
            print(f"!! keuze niet gevonden: {stap!r}\n{screen}"); break
    druk(letter)
    screen = read_screen(old=screen)
    print(f"\n=== {letter or 'RETURN'} ({stap}) ===\n{screen}")
    if "Einde" in screen: break
mon.run([f'screenshot "{os.path.abspath(shot)}" 2']); time.sleep(0.5)
close(vice, group, mon)
```

```bash
python3 speel.py build/spel.prg plan.txt win.png      # winroute; plan_dood.txt voor een doodroute
# losse schermen en screenshots kunnen ook eenvoudig met c64run.py:
R="$HOME/Library/Application Support/MacAIMagic/Skills/c64-basic-v2/c64run.py"
python3 "$R" build/spel.prg --wait 3 --type "" --type "b" --shot hal.png
python3 teken.py --vergroot hal.png                   # -> hal_x3.png, bekijk met view_image
```

Laat de autocoureur het winscherm ("JE HEBT GEWONNEN") en het dodescherm ("Einde - druk een toets") in de log
tonen; dat is het bewijs. Draai VICE's altijd één voor één (meer tegelijk = tragere start, toetsen te vroeg).
Geen spatie in het pad van `--shot`.

## 12. Plaatjes en sprites van het beeldmodel (FLUX) — exact voor de C64

FLUX kent de C64 niet: het maakt 512-1024 pixels met duizenden kleuren, zonder raster. `c64beeld.py` maakt daar
échte C64-data van: 16 kleuren, de kleuren per vakje (multicolor 3 + achtergrond per 4x8, hires 2 per 8x8), sprites
van 24x21. Wat eruit komt klopt dus altijd; getest 11 nov 2026: VICE-screenshots 0 pixels anders dan berekend.
Gebruik het voor een titelscherm, een plaatje op het hele scherm, of sprites. **Niet voor de kamerplaatjes van het
bouwpakket** (§11): die strook van 80 blokjes is te grof voor een FLUX-plaatje (getest, onherkenbaar); teken die met
`teken.py`. Sprites voor het bouwpakket kunnen wel (`--kit`).

### 12.1 De stappen

```bash
S="$HOME/Library/Application Support/MacAIMagic/Skills/c64-kickassembler"
R="$HOME/Library/Application Support/MacAIMagic/Skills/c64-basic-v2/c64run.py"
python3 "$S/flux.py" scene "a beautiful sunset over a calm sea" zon.png            # ~40 s
python3 "$S/c64beeld.py" bitmap zon.png zon             # multicolor; --hires = 320x200, 2 kleuren per 8x8
"$S/build.sh" zon_toon.asm
python3 "$R" build/zon_toon.prg --nowarp --wait 4 --shot zon_vice.png
python3 "$S/flux.py" sprite "a ghost with two big eyes far apart" spook.png --aantal 3       # ~20 s per stuk
python3 "$S/c64beeld.py" sprites figuren spook_2.png vleermuis.png     # multicolor; --hires = 24 breed, 1 kleur
```

1. **Beschrijf alleen het onderwerp, in het Engels.** `flux.py` zet de C64-stijl er zelf achter (pixelart, vlakke
   kleuren, contrast, geen tekst; bij een sprite: heel simpel, grove pixels, effen magenta achtergrond; `--groen`
   voor iets paars of roze). Eén onderwerp, grote vormen, weinig dingen.
2. **Kijk naar `naam_c64.png`** (links de C64-pixels, rechts de bron). Niet mooi? Neem een ander zaad (`--aantal 3` en kies) of een andere beschrijving.
3. **Bouw `naam_toon.asm`** (laat het plaatje of de sprites zien) en kijk in VICE. Begin je eigen programma daarmee.
4. Zegt `flux.py` dat er te weinig geheugen is, vraag het plaatje dan met **`make_image`** (de app maakt eerst
   ruimte; zet de stijlwoorden van `flux.py` dan zelf in de prompt). Het komt vierkant binnen en je kunt pas in je
   volgende beurt verder: `ls -t ~/Pictures/MacAIMagic/*.png | head -1`. `c64beeld.py` snijdt het midden eruit
   (320:200), dus vraag om een breed onderwerp met ruimte erboven en eronder.

### 12.2 Wat eruit komt

| Bestand | Gebruik |
|---|---|
| `naam.kla` | Koala multicolor: `LoadBinary("naam.kla", BF_KOALA)`, zie `naam_toon.asm` (bitmap $2000, scherm $0c00, kleur-RAM met een lus naar $d800, `$d016=$d8`, `$d011=$3b`) |
| `naam.hir` | hires: 8000 bytes bitmap + 1000 scherm: `LoadBinary("naam.hir", "Bitmap=0, ScreenRam=8000")`, `$d016=$c8` |
| `figuren.asm` | `.align 64`, per sprite een label + 64 bytes en `label_kleur` (voor $d027+n). Multicolor: ook `figuren_mc1`/`figuren_mc2` voor $d025/$d026 — die gelden voor ALLE multicolor-sprites, dus zet alle sprites die samen op het scherm komen in één aanroep; en zet $d01c |
| `--kit` | hires sprites als `SPRITEREGEL`s: plak ze in `verhaal.asm` onder `sprites:` (geef ze een eigen naam), `VLIEGER(spook, spook, WIT, 3, 1)`; de kleur staat erboven |
| `naam_toon.asm` | een klein werkend programma dat het laat zien |

**Indeling van een `.kla`-bestand** (10.003 bytes; nagemeten aan `c64beeld.py` en een echt bestand, 11 nov 2026).
Gebruik deze offsets als je het plaatje in Python leest of aanpast (bijvoorbeeld tekst erin tekenen); `lees_koala`
in `c64beeld.py` doet het voor. Raad ze niet: een model rekende met bitmap op 0 en kleur op 2000, en later 8192.

| Offset | Lengte | Inhoud |
|---|---|---|
| 0 | 2 | laadadres `$00 $60` ($6000) |
| 2 | 8000 | bitmap: per vakje van 8×8 schermpunten 8 bytes onder elkaar, 40 vakjes per rij; vakje (kolom k, rij r) begint op `2 + (r*40 + k)*8` |
| 8002 | 1000 | scherm-RAM, één byte per vakje: hoge nibble = kleur voor bits `01`, lage nibble = kleur voor bits `10` |
| 9002 | 1000 | kleur-RAM, één byte per vakje (lage nibble): kleur voor bits `11` |
| 10002 | 1 | achtergrond ($d021): kleur voor bits `00` |

Elke byte van de bitmap is 4 multicolor-pixels van 2 bits, de linker in bit 7–6. Een vakje heeft dus 4×8 pixels en
hoogstens 4 kleuren: de achtergrond (voor het hele scherm), 2 uit het scherm-RAM en 1 uit het kleur-RAM.

**Bitmap én sprites samen** (getest, `beeld-voorbeeld/demo.asm`, zie `demo.png`): code $0810, sprites $0900-$0bff
(wijzer = adres/64, dus $24 ...), scherm $0c00 (sprite-wijzers op $0ff8-$0fff), kleur-RAM-bron $1c00, bitmap
$2000-$3f3f. Sprites nooit in $1000-$1fff: daar ziet de VIC de ROM-tekens.
- **Geheugen:** een Koala-plaatje is 10 KB. Meer dan twee of drie plaatjes passen niet tegelijk; laad ze dan van
  diskette.
- **Tekst:** een bitmapscherm heeft geen tekst. Tekst ónder een plaatje vraagt een rastersplitsing (bitmap boven,
  tekst onder): bouw die apart en test hem. Tekst vóór of ná het plaatje (wisselende schermen) kan gewoon: zet
  `$d011/$d016/$d018` terug als voor de tekst (zie §12.4).

### 12.3 Wat werkt en wat niet (getest)

- Scènes in de stijl van `flux.py` worden mooi: bos met huisje, kerker, kasteel. Een gewone illustratie (`--rauw`)
  geeft zichtbare vakjes en korrel.
- **Gradients zijn de vijand** (getest, zonsondergang nov 2026): zachte luchtverlopen worden op de C64 korrelige
  dither-vlekken en strookjes. Vraag expliciet om `wide flat horizontal bands of solid color, posterized, sharp
  edges, no gradients, no dithering, minimal` en zet bij c64beeld.py `--raster geen` (vlakke kleuren, geen
  fakedithering). Dan worden het strakke C64-kleurvlakken. (`--raster` is van c64beeld.py; flux.py kent die vlag niet.)
- FLUX zet soms nep-tekst op bordjes en in hoeken: neem een ander zaad.
- Sprites: één simpel figuur gaat goed (spook, vleermuis). Een ridder met zwaard en schild is te veel voor 24x21.
- Multicolor-sprites zijn half zo breed (12 pixels): twee ogen vlak naast elkaar worden één streep. Vraag "eyes far
  apart" of neem `--hires`.
- Pixels die op de schermkleur lijken (zwarte rand, zwarte ogen) worden doorzichtig: goed op zwart. Voor een ander
  scherm `--achter N`; boven een bitmap `--achter geen`.
- Het C64-rood is roze-achtig, dus een FLUX-rood wordt vaak oranje.
- Twee standen van hetzelfde figuur (animatie) maakt FLUX niet betrouwbaar: elk zaad geeft een ander figuur. Maak de
  tweede stand met `--kit` en pas de SPRITEREGELs met de hand aan.
- `--kleur` (verzadiging, standaard 1.5) en `--licht` (1.2 = lichter) helpen bij donkere nachtscènes. `--raster geen`
  geeft vlakke kleuren zonder menging.

### 12.4 Getest titelscherm-sjabloon (nov 2026, "Zonsondergang")

Tekstscherm met titel + knipperende prompt → toets → Koala-bitmap op het hele scherm met een langzaam door
de avond kleurende rand → toets → terug. Alles in één bestand, prg past onder $4000, geen eigen charset nodig.

```asm
        .encoding "screencode_upper"
.var pic = LoadBinary("plaatje.kla", BF_KOALA)
        BasicUpstart2(start)
*=$0810 "Code"
start:  cli                             // kernal-IRQ aan: $a2 en toetsscan
        ldx #0
        stx $c6                         // toetsenbuffer leeg (RESTEN na autostart!)
        lda #$1b
        sta $d011                       // tekstmodus aan
        lda #$08
        sta $d016
        lda #$17
        sta $d018                       // scherm $0400, rom-tekens: $17 kleine letters, $15 HOOFDLETTERS
        // ... tekst: ldx #0 / lda titel,x / beq titel_klaar / sta $0400+rij*40+kolom,x / inx / bne ...
        //     (titel: .text "..." + .byte 0; een gewoon label voor het einde, geen !titel-klaar, §2.14);
        //     kleur: sta $d800+...; titel paars (3), prompt wit (1)/lichtblauw (6) ...
wacht:  lda $c6
        bne bitmap
        // knipperen: lda $a2; and #$10; dan de promptkleur 1 of 6 opnieuw zetten
        jmp wacht
bitmap: lda #0
        sta $c6
        sta $d011                       // tekstmodus uit
        lda #pic.getBackgroundColor()
        sta $d021
        // kleur-RAM-bron $1c00 -> $d800 met .for-lus x4 pagina's, X=0..255 (zie naam_toon.asm, §12.2)
        lda #$38
        sta $d018                       // bitmap $2000, scherm $0c00, rom-tekens (GEEN charset-kopie nodig)
        lda #$d8
        sta $d016
        lda #$3b
        sta $d011
        // randcyclius: jiffy-rand-detectie op $a2 + teller $fe (zie §6, NOOIT inc $a2)
        // toets: lda $c6; bne start
*=$0c00 "Scherm"
        .fill pic.getScreenRamSize(), pic.getScreenRam(i)
*=$1c00 "KleurBron"
        .fill pic.getColorRamSize(), pic.getColorRam(i)
*=$2000 "Bitmap"
        .fill pic.getBitmapSize(), pic.getBitmap(i)
```

Randcyclius-kleuren voor een avond: `.byte 13,2,8,7,8,2` (roze, rood, oranje, geel, oranje, rood).

## 13. Muziek: een bekend nummer op de SID (getest 11 nov 2026, met Axel F)

**Voor een intro: gebruik §14.** `intro.py` doet de stappen hieronder zelf (`--midi` of `--sid`).

Er zijn twee routes. Kijk eerst of er al een C64-versie bestaat (§13.1). Is die er niet, of past die niet in je
geheugenkaart, zet dan een MIDI-bestand om (§13.2). Download alleen wat de gebruiker vraagt, en zeg waar het vandaan
komt. De muziek blijft van de makers: prima voor een eigen intro, niet om te verkopen.

Een werkend voorbeeld van beide routes staat in `~/Development/Kick Assembler/Axel-F-voorbeeld/`: `axel_intro.asm`
(route B, met een rand die op de kick flitst) en `hulsbeck.asm` (route A), allebei met een opname (`.m4a`).

### 13.1 Route A: een kant-en-klare SID uit de HVSC

De High Voltage SID Collection heeft tienduizenden C64-tunes, ook covers van bekende nummers. In de lijst
`Songlengths.md5` (4,4 MB) staat elke tune als `; /MAP/Naam.sid`; zoek erin op naam:

```bash
H=https://hafnium.prg.dtu.dk/HVSC/C64Music
curl -s $H/DOCUMENTS/Songlengths.md5 | grep -i "axel"        # o.a. ; /MUSICIANS/H/Huelsbeck_Chris/Axel_F.sid
curl -sfLo Axel_F.sid $H/MUSICIANS/H/Huelsbeck_Chris/Axel_F.sid
python3 "$S/muziek.py" sid Axel_F.sid                        # geheugen, init/play, timing, waarschuwingen
```

`muziek.py sid` gaf voor deze tune: `$a000-$cbd3`, init `$c000`, play `$c020`, CIA-timer, PAL, 6581. Zo bouw je hem
in (getest in VICE):

```asm
.var muziek = LoadSid("Axel_F.sid")
BasicUpstart2(start)
*=$0810
start:  sei
        lda #$36
        sta $01                 // BASIC-ROM uit: de tune ligt deels op $a000-$bfff; de kernal blijft aan
        lda #muziek.startSong-1
        jsr muziek.init         // zet bij een CIA-tune zelf het tempo van de timer
        lda #<irq
        sta $0314
        lda #>irq
        sta $0315
        cli
        jmp *
irq:    jsr muziek.play         // de kernal-IRQ komt van CIA-timer A: het tempo van de tune
        jmp $ea31
*=muziek.location "Muziek"
        .fill muziek.size, muziek.getData(i)
```

- **Een SID staat op een vast adres.** Bouw je programma eromheen; verplaatsen kan niet zonder relocator. Past het
  niet, neem dan route B. Deze prg is 50 KB, omdat KickAss het gat tussen `$0850` en `$a000` opvult.
- **"CIA-timer"** in `muziek.py sid`: roep play aan vanuit de kernal-IRQ, zoals hierboven, en laat de CIA-IRQ aan.
  **"50 Hz"**: vanuit een raster-IRQ, zoals §13.4 van het naslagwerk.
- **RSID** wil de hele C64 voor zich: niet bruikbaar in een intro.
- **Gemeten:** de opname van dit programma in VICE en die van VICE's eigen SID-speler (vsid) vallen samen. De luidheid
  per 10 ms correleert 0,96 en de spectra per 0,1 s 0,97 (mediaan): dezelfde noten in hetzelfde tempo.

### 13.2 Route B: een MIDI-bestand omzetten met `muziek.py`

MIDI's van bekende nummers vind je op bitmidi.com: `https://bitmidi.com/search?q=axel+f` geeft o.a. `/axel-f-1-mid`,
en op die pagina staat de link `/uploads/8686.mid`. Download die met `curl -sfLo Axel-F-1.mid https://bitmidi.com/uploads/8686.mid`.

```bash
python3 "$S/muziek.py" info Axel-F-1.mid
```
```
 spoor kanaal  noten  bereik      gem.  tegelijk  begint   instrument / naam
     1       2    443  C1-D#3     C2           2   20.3 s   synthbas / SYNBASS 1
     7       9    248  F1-C6      A4           5    4.1 s   synthlead / SAW WAVE
     8      10   2180  -                       4    4.1 s   DRUMS / DRUMS
```

Kies uit die lijst:
- **`--melodie`** (stem 1): de partij met de bekende melodie, meestal synthlead, fluit of zang. Bij akkoorden speelt
  de speler de hoogste noot.
- **`--bas`** (stem 2): synthbas of bas. Bij akkoorden speelt de speler de laagste noot.
- **`--drums`** (stem 3): kanaal 10. Wil je een derde melodische partij, gebruik dan `--derde`.
- **`--van` / `--tot`**: seconden in het origineel, zoals `info` ze toont. Kies voor een intro 20 tot 40 seconden, het
  liefst hele maten. Bij Axel F is 4,09 tot 36,6 s precies 16 maten: twee keer de melodie, de laatste acht maten met
  de bas.

```bash
python3 "$S/muziek.py" omzetten Axel-F-1.mid -o muziek.asm --melodie 7 --bas 1 --drums 8 --van 4.09 --tot 36.6
```

Inbouwen. De volledige startcode staat in `axel_intro.asm`: `jsr muziek_init`, CIA-IRQ uit, raster-IRQ aan, `cli`.

```asm
irq:    asl $d019
        jsr muziek_play         // 50 keer per seconde (PAL)
        lda muziek_slag         // de drum die net viel: 1 kick, 2 snare, 3 tom, 4 open hihat, 5 hihat
        // ... bijvoorbeeld de rand laten flitsen op 1 en 2; daarna zelf weer 0 maken:
        lda #0
        sta muziek_slag
        jmp $ea31
*=$1000 "Muziek"                // waar het past; de speler gebruikt geen zeropage
#import "muziek.asm"
```

| Optie | Wat het doet |
|---|---|
| `--rooster 6` | een zestiende noot is precies 6 beelden (125 bpm): strak ritme. Zonder deze optie houdt de speler het echte tempo (118 bpm = 6,36 beelden), met afwisselend 6 en 7 beelden. |
| `--snelheid 1.1` | 10% sneller (zonder `--rooster`) |
| `--transponeer -12` | een octaaf lager; noten buiten C0–A#7 schuift de speler zelf een octaaf op |
| `--klank1 puls` | klank per stem: `puls` (met pulsbreedte-modulatie, standaard voor stem 1), `pulskort`, `zaag`, `zaagkort` (standaard voor stem 2), `driehoek`, `fluit`, of zelf `golf:ad:sr:pulsbreedte:modulatie` in hex |
| `--eenmaal` | één keer spelen en dan stil; zonder deze optie herhaalt de muziek |
| `--volume 12` | het volume in `$d418` (0–15) |

**Wat de speler doet:**
- 3 stemmen en 5 drumklanken (kick, snare/klap, tom, open hihat/bekken, hihat);
- elke andere GM-percussie (maracas, shaker, tamboerijn) tikt als hihat;
- pulsbreedte-modulatie voor de typische C64-klank;
- PAL, 50 keer per seconde.

**Geheugen:** ongeveer 0,7 KB voor de speler en 2 bytes per noot. Axel F (32,5 s, 349 noten en drums) gebruikt
`$1000`–`$165f`.

**Wat verloren gaat:** per stem klinkt één noot tegelijk, er klinken nooit meer dan drie partijen, en de drums zijn
eenvoudiger dan in het origineel.

### 13.3 Controleren zonder oren

```bash
python3 "$S/muziek.py" opnemen build/intro.prg -o intro.wav --sec 20   # VICE op echte snelheid: 20 s muziek duurt ±24 s
python3 "$S/muziek.py" luister intro.wav --stap 0.125                   # per 1/8 s: luidheid en de sterkste tonen
```

**Getest met Axel F.** `luister` liet zien:
- de melodie noot voor noot zoals in de MIDI: F4 G#4 F4 F4 A#4 F4 D#4 · F4 C5 F4 F4 C#5 C5 G#4 · F4 C5 F5 F4 D#4 D#4
  C4 G4 F4;
- de bas: F1 F2 D#2 D#3 C1 C2;
- de drums tussen de zinnen.

**Hoe je de uitvoer leest:**
- "stil" waar je muziek verwacht: de speler draait niet (wordt `muziek_init` aangeroepen, en de IRQ?).
- Boventonen en arpeggio's, zoals in HVSC-tunes, geven rommeliger regels.
- De gebruiker kan de WAV zelf afspelen. Zeg waar hij staat.

**Lessen van het bouwen van de speler:**
- **Vlaggen na het herstellen van een register:** een subroutine die aan het eind `ldy`/`ldx`/`pla` doet, geeft de
  vlaggen van dát register terug, niet die van A. Een `bne` erna keek naar Y (0 bij stem 1), en de speler hing in een
  eindeloze lus. Zet `and #$ff` of `cmp #0` vóór de `rts`.
- **`$d020` en `$d021` alleen schrijven als de kleur verandert.** Elke schrijfactie kan een grijze stip in de rand geven
  (gezien in VICE).

## 14. Een intro in één commando — het intro-pakket `intro/` (getest 11 nov 2026)

**Waarom.** In de Terminator-intro (Qwen3.8, 11 nov 2026) ging 3,5 uur op aan zelf een intro schrijven:
- de titel pixel voor pixel in de bitmap stempelen, met een geraden lettertype;
- kleurcellen opmeten om de ogen te laten knipperen;
- een eigen muziekspeler met de SID op het verkeerde adres;
- het hele programma 13 keer opnieuw schrijven, en twee uur lang niet bouwen.

Het werkte daarna nog steeds niet. Met dit pakket is het één commando, en het duurde in de proef 92 seconden,
inclusief FLUX.

### 14.1 Wat het maakt

| Rij | Inhoud |
|---|---|
| 0–18 | het plaatje: een multicolor bitmap, van FLUX of een eigen plaatje (breed, 320×152) |
| 19 | zwart: de naad waar de raster-IRQ naar tekst omschakelt |
| 20 | de titel; de kleuren lopen erdoorheen (`--palet`) |
| 22 | de ondertitel |
| 24 | een scrolltekst die vloeiend rondloopt |

- **Muziek:** een MIDI, omgezet met `muziek.py` (§13.2), of een HVSC-SID die op 50 Hz loopt.
- **De rand** flitst op de kick (rood) en de snare (oranje). Dat werkt alleen met `--midi`.
- **Bliksem** (`--bliksem aan`): af en toe een witte dubbele flits achter het plaatje.

**Getest in VICE:**
- de naden zijn schoon: 0 verdwaalde pixels in rij 19, 21 en 23 en in de rand, op 3 momenten;
- de scrolltekst loopt;
- de melodie klinkt noot voor noot (`luister`);
- de flits volgde kick en snare (31 keer geteld);
- de bliksem kleurt de achtergrond;
- een SID op 50 Hz speelt;
- een SID met CIA-timing wordt met uitleg geweigerd.

### 14.2 De stappen

1. **Muziek kiezen.**
   - Een MIDI van bitmidi.com (§13.2): bekijk de sporen met `python3 "$S/muziek.py" info liedje.mid`.
   - Of een HVSC-SID (§13.1). `python3 "$S/muziek.py" sid x.sid` moet "50 Hz" zeggen.
2. **Eén commando** in de werkmap:
   ```bash
   S="$HOME/Library/Application Support/MacAIMagic/Skills/c64-kickassembler"
   python3 "$S/intro/intro.py" --flux "a red 1980s sports car on a palm tree boulevard in front of a sunset city" \
       --titel "A X E L   F" --ondertitel "EEN INTRO IN EEN COMMANDO" --scroll "DEZE INTRO IS ..." \
       --midi Axel-F-1.mid --melodie 7 --bas 1 --drums 8 --van 4.09 --tot 36.6 --palet vuur --opnemen 10
   ```
3. **Kijken en luisteren.** Bekijk `intro.png` met `view_image` en lees de regels van `luister`. Klopt het, dan ben
   je klaar. Noem de gebruiker dan `build/intro.prg`, `intro.png` en `intro.wav`.
4. **Aanpassen.** Geef alleen de optie op die anders moet. Al het andere blijft zoals het was: het plaatje, de muziek,
   de teksten, de kleuren en de effecten (`intro_opties.json`). Bijvoorbeeld:
   - `--palet chroom`;
   - `--bliksem aan`;
   - `--uitsnede boven`;
   - `--flux "..."` voor een nieuw plaatje;
   - `--midi ... --tot 20` voor een korter stuk.

| Optie | Wat |
|---|---|
| `--flux "onderwerp"` / `--plaatje x.png` | het plaatje (FLUX: Engels, alleen het onderwerp; `flux.py` zet de C64-stijl erachter) |
| `--uitsnede boven\|midden\|onder` | welk deel van een hoog plaatje blijft |
| `--midi` + `--melodie --bas --drums --van --tot` (+ `--rooster --transponeer --klank1..3`) | muziek uit een MIDI, als in §13.2 |
| `--sid x.sid` / `--geen-muziek` | een HVSC-SID (50 Hz, op `$1000-$1fff` of `$5000-$cfff`) / stil |
| `--titel`, `--ondertitel` | hoogstens 40 tekens; hoofdletters, cijfers, leestekens (accenten vallen weg) |
| `--scroll`, `--scroll-snelheid 1\|2` | de scrolltekst (tot 1800 tekens) |
| `--palet vuur\|ijs\|goud\|groen\|chroom\|regenboog` | de lopende kleuren van de titel |
| `--kleur-onder N`, `--kleur-scroll N` | kleur van de ondertitel en de scrolltekst (0–15) |
| `--flits aan\|uit`, `--flitskleuren 2,8` | de rand op kick en snare |
| `--bliksem aan\|uit` | witte flitsen achter het plaatje |
| `--opnemen 10` | 10 s geluid opnemen (`intro.wav`) en de tonen tonen |

### 14.3 Regels

- **Pas `intro.asm` niet aan; alles gaat via de opties.** `intro.py` zet bij elke run een verse kopie neer.
- **Wil de gebruiker iets wat het pakket niet kan,** zoals sprites of een andere indeling? Zeg dat.
  - Bouw het daarna in kleine stappen bovenop een werkende intro.
  - Kopieer `intro.asm` daarvoor naar een eigen naam en verander één ding per keer.
  - Bouw na elke wijziging met `./build.sh` en kijk met `c64run.py`.
- **Geheugen:**

  | Adres | Inhoud |
  |---|---|
  | `$0400` | tekstscherm |
  | `$0c00` | kleuren van het plaatje |
  | `$1000`–`$1fff` | vrij voor een SID |
  | `$2000` | bitmap |
  | `$4000`–`$4bff` | code en teksten |
  | `$4c00` | kleur-RAM-bron |
  | `$5000` | muziek van `muziek.py` |

  Een SID die daar niet past, of op CIA-timing loopt, weigert `intro.py` met uitleg. Neem dan een andere versie, of
  `--midi`.
- **Als iets misgaat,** zegt `intro.py` wat er misging, met een regel die met `[intro] FOUT:` begint. Lukt alleen de
  schermafdruk niet, draai `intro.py` dan zonder opties opnieuw.
- **Nooit `pkill -f x64sc`** (§4): dat sluit ook de VICE van `intro.py` af.

## 15. Een groot spel dat werkt: ASHKARA (dune64)

ASHKARA ([github.com/mfidder2026/dune64](https://github.com/mfidder2026/dune64)) is een avontuur- en strategiespel
van de eigenaar, en het werkt van begin tot eind:
- vijf hoofdstukken, twee eindes, Nederlands en Engels;
- muziek, een snellader en opslaan, op één diskette.

Het is geschreven in C (cc65), met ca65-assembler en Python. De technieken zijn ook in Kick Assembler te maken.
**Lees `dune64/DUNE64.md` voordat je een groot spel opzet.** Het beschrijft de werkwijze, het scherm, de geheugenkaart,
patches, kleurcycli, de verhaal-VM, laden en opslaan, muziek en de valkuilen.

**De lessen die het meest uitmaakten:**
1. **Eerst een ontwerp**: schermindeling, geheugenkaart, bestandsformaten. Werk daarna in fases met een meetbaar
   "klaar als": eerst één scherm, dan één speelbaar hoofdstuk, dan de rest.
2. **Data buiten de code.**
   - Het verhaal staat in scripts die een compiler naar bytecode zet, en een kleine VM voert die uit.
   - Plaatjes gaan door een converter die de C64-regels afdwingt.
   - De build weigert alles wat niet in zijn buffer past.
3. **Vaste buffers en een geheugenkaart die de build bewaakt.**
   - VIC-bank 3 (`$C000-$FFFF`, met de bitmap onder de Kernal-ROM) laat `$0801-$BFFF` vrij voor het programma.
4. **Bitmap boven, tekst onder**, met twee raster-IRQ's (lijn 186 en 252):
   - zwarte randen in de art vangen een te late IRQ op;
   - `jmp $EA31` één keer per beeld.
5. **Animatie zonder de bitmap te veranderen:**
   - patches (rechthoeken van cellen) voor een pratende mond of een veranderde scène;
   - kleurcycli voor beweging over een hele scène.
6. **Testen in VICE met een vaste toetsenreeks**, zodat elk verloop hetzelfde is. Elke test levert screenshots op.

| Getest in Kick Assembler (VICE 3.9, 11 nov 2026) | Wat er gemeten is |
|---|---|
| `dune64/split_bank3.asm` | 0 verdwaalde pixels in de naad en de lege rijen; de mond wisselt (open: 48 rode pixels, dicht: 0) |
| `dune64/kleurcyclus.asm` | bij een nieuwe fase verandert elke grondpixel van kleur en geen enkele luchtpixel; geen scheur in 5 screenshots (elk kleurvak overal één kleur) |

**Opbouw van de prg.** Laat de prg niet zelf tot `$C000` of `$E000` doorlopen: dan neemt hij het hele gat mee en laadt
hij over I/O heen. `split_bank3.asm` zet de gegevens achter de code en kopieert ze bij het starten naar `$C000`, `$D800`
en `$E000`. De prg is daardoor 8 KB in plaats van 48 KB.

## 16. Een rollenspel of actie-avontuur: de motor van c64red

c64red ([github.com/mfidder2026/c64red](https://github.com/mfidder2026/c64red)) is een rollenspel van de eigenaar in Kick
Assembler: 33 kaarten in een vloeiend scrollende wereld, mensen en borden, een tekstvenster dat letter voor letter
uitrolt, een menu, gevechten in beurten, een laad- en titelscherm, en opslaan op de diskette. Een kopie staat in
`rpg/c64red/`. **Lees `rpg/RPG.md` voordat je begint**: hoe de motor werkt, hoe je er een eigen spel van maakt, en wat er
verandert voor een Zelda-achtig spel met kamers, vijanden en een zwaard.

1. **Kopieer de motor naar de werkmap en bouw hem eerst ongewijzigd**: `./bouw.sh --direct` (testbouw die meteen in de
   wereld start), dan `c64run.py build/c64red.d64 --wait 25 --shot scherm.png` en kijk naar de PNG (het spel tekent
   in bank 1; de tekstuitvoer is het oude BASIC-scherm). Het spel leest de toetsen zelf, dus `--type` komt niet aan:
   zonder `--direct` blijft een test op het titelscherm. Lever op met `./bouw.sh` zonder `--direct`.
2. **Verander eerst de data, dan pas de code**: teksten in `data/texts.json`, kaarten in `data/maps/*.json`, pixelart in
   `tools/gfx_gen.py`. De generators maken de `.asm`; bewerk de gegenereerde `.asm` nooit.
3. **De code klein en op ankers**, met `docs/ARCHITECTURE.md` §5 ernaast (welke registers elke routine sloopt).
4. **Eigen inhoud**: geen namen, figuren, kaarten of teksten uit bestaande spellen.

| Getest op deze Mac (12 nov 2026) | Uitkomst |
|---|---|
| `./bouw.sh` op een schone kopie | checker 0 fouten, `build/c64red.d64` en `build/main.prg` |
| `./bouw.sh` in VICE (`c64run.py`, 25 s) | laadscherm, dan het titelscherm ("DRUK OP EEN KNOP") |
| `./bouw.sh --direct` in VICE, 3 keer | elke keer meteen het eerste dorp: huizen, pad, speler, buurman, kaartnaam |
| Een opslag op de d64, dan opnieuw bouwen | de opslag staat er byte voor byte weer op |
| Niet gedraaid | `tools/verify_*.py`, de kaarteditor, lopen/praten/vechten (een test kan het spel niet besturen), de Zelda-variant |

**Uit c64red ook in de rest van deze skill:**
- De checker heeft er tien controles bij gekregen, onder andere:
  - het branch-bereik met de afstand erbij;
  - een `jsr` die X of Y sloopt binnen een lus op dat register;
  - een sprong naar een label dat niet bestaat;
  - werkgeheugen dat gelezen maar nooit gezet wordt;
  - grafiek in het ROM-schaduwgebied;
  - een indirecte pointer buiten de zeropage.

  Dezelfde uitkomst als de oude checker op 219 van de 221 `.asm`-bestanden op deze Mac. De twee andere geven nu een
  terechte waarschuwing.
- De praktijklessen van de scrollende wereld staan in `C64_KICKASS_SKILL.md` §20.

## 17. Netwerk: twee C64's samen (uit BB-LAN)

BB-LAN ([github.com/mfidder2026/BB-Lan](https://github.com/mfidder2026/BB-Lan)) van de eigenaar maakt van Bubble Bobble
een spel voor twee C64's over het LAN, met elke combinatie van C64 Ultimate, WiC64, VICE met WiC64 en VICE met RR-Net.
Het netwerkdeel staat nu in Kick Assembler in `netwerk/`. **Lees `netwerk/NETWERK.md`**: de routines, het protocol
van de server, en hoe je een spel voor twee machines maakt.

1. **`#import "net.asm"`** achter je code. `net_init` zoekt de hardware (Ultimate, RR-Net, WiC64), `net_connect`,
   dan `net_send` (bericht in `net_tx`, lengte in A) en `net_recv` (A = lengte in `net_rx`, 0 = niets).
2. **Herhaal wat een antwoord nodig heeft**: UDP en Ethernet raken berichten kwijt.
3. **Een spel: lockstep.** Stuur alleen de joystick per tik, met een input delay, en herhaal de laatste inputs in elk
   bericht. Beide C64's rekenen hetzelfde spel uit. Dat vraagt een spel zonder logica in de IRQ en zonder toeval uit
   timers, en een checksum om de 64 tikken (NETWERK.md §4).
4. **Testen met `duo.py`**: de testserver en twee VICE's met WiC64 tegelijk. **VICE 3.10 of nieuwer**: 3.9 crasht op
   deze Mac bij elk WiC64-commando. `c64run.py` zet geen WiC64 aan.

| Getest op deze Mac (12 nov 2026) | Uitkomst |
|---|---|
| Twee C64's met WiC64 in VICE 3.10 + `server.py` | beide aangemeld, START met slot 0 en 1, elkaars tick en joystick op het scherm, 16,7 berichten/s per richting |
| Zonder netwerkhardware | "NETWERK: GEEN", niets hangt |
| `server.py` met een UDP- en een TCP-speler | WELCOME, START, game-berichten heen en terug, PONG |
| Niet getest | C64 Ultimate (niet in VICE), RR-Net (VICE crasht hier bij de netwerkkaart zonder root), echte WiC64, de C#-server van BB-LAN |

**Kick Assembler kent geen `.encoding "ascii"`** (5.14: "Invalid encoding"). Voor een IP-adres of een naam in ASCII:
`.encoding "petscii_upper"` geeft voor hoofdletters, cijfers en leestekens dezelfde bytes.

## 20. Lessen RetroWebShop-advertentie-intro (11 nov 2026, `intro_rws.asm` + sprites bovenop §14)

Getest in VICE: acht vliegende multicolor-sprites boven het FLUX-plaatje, Commando-tune (HVSC) op 50 Hz.

1. **Sprite-posities staan TWEE bytes uit elkaar** ($d000/$d001, $d002/$d003, ...). `sta $d000,x` met X =
   spritemummer is FOUT (dan staan y van sprite 0 in x van sprite 1). Doe `txa / asl / tay` en schrijf
   `sta $d000,y` + `sta $d001,y`. Zelfde les geldt voor $d027-kleuren: die staan wél byte per byte.
2. **Sprite-wijzers bestaan twee keer**: $07f8 bij tekstschermbasis $0400 en $0ff8 bij $0c00. Een intro met
   raster-split vult beide, anders zijn de sprites in de tekststand weg.
3. **`.byte`-tabellen via `#import` alleen binnen je eigen segment** (na `*=$4000 "Code"`). Boven in het
   bestand vallen ze in het Default-segment en botsen met $080e (Basic End) of $2000 (Bitmap).
4. **`.fill` heeft altijd twee argumenten**: `.fill NSPR, 0`.
5. **HVSC online**: `DOCUMENTS/Songlengths.md5` werkt, `Songlengths.txt` komt leeg binnen. De echte
   Commando-tune = `/MUSICIANS/H/Hubbard_Rob/Commando.sid` ($5000-$5f9f, 50 Hz) — past in het vrije
   $5000-gebied van `intro.py`; `--sid` accepteert hem zonder klagen.
6. **Simpele waren** (shirt, boek, cartridge, diskette): een handgetekende 12×21 multicolor-tekening in een
   python-script (`.`/`1`/`2`/`3` → 63 bytes + 1 byte vulling tot blok van 64, eigen PNG-preview) is scherper
   dan een FLUX-sprite. FLUX is hier wel sterk in: het winkelplaatje (scene).
7. **Botsingseffect**: $d01e lezen wist de bits; bewaar het masker, keers alleen die richtingen om,
   flits $d020 een aantal frames en zet hem daarna terug op 0 (nooit elke beeldveld schrijven).
8. **Willekeurige "duw"** voor spanning: verhoog om de ~250 beelden een sprite naar tempo 4 en zet na 32
   beelden alle tempo's terug uit een tabel — anders raast alles binnen een minuut weg.

## 21. Les Terminator-intro (12 nov 2026, `intro.py` met --bliksem en --flits)

1. **Flitseffecten van 1-2 beeldvelden bewijs je via de registers, niet via screenshots.** In VICE-warp is een
   flits van 2 beeldvelden op 30 screenshots niet te vangen (alle 30 shots identiek, 1,5% witte pixels —
   vals-negatief, terwijl het effect 64 keer sloeg). Poll in plaats daarvan in ÉÉN monitor-sessie het
   VIC-register waar het effect naar schrijft (`m d020 d021`, ±3000 steekproeven in ~14 s echte tijd) en
   check de verdeling van de kleurwaarden tegen de reeks/tabel uit de bron: bij de Terminator-intro stond
   de rand 81× rood + 48× oranje (kick/snare-flits, kleuren 2 en 8) en de achtergrond 48× kleur 1 + 16× wit
   — precies de bliksemreeks 1,1,0,0,15,1,0 met de juiste 3:1-verhouding. Wil je er ook een plaatje van:
   laat het poll-script meteen `screenshot` nemen zodra het register een flitswaarde heeft.
