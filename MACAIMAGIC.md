# Notities voor MacAIMagic

Het model leest dit bestand bij elk bericht in deze werkmap. Schrijf hier zelf instructies voor het model, bijvoorbeeld hoe het een emulator start. Onder Geleerd zet de app wat het model tijdens gesprekken leert, zodat het fouten niet twee keer maakt. Je mag daar alles aanpassen of weghalen.

## Sprites van Hollow Crown
- De karakters staan in `tools/sprites_hc.py` als tekeningen van tekst (k zwart, s huid, c eigen kleur). `python3 tools/sprites_hc.py` maakt daaruit `src/sprites_hc.asm` en `data/sprites_hc.png`. Verander de tekening, niet de .asm.
- Elk karakter is 2 multicolor-sprites boven elkaar: de onderste staat 21 pixels lager, op dezelfde X. Labels: `<naam>_boven`, `<naam>_onder`, kleuren `<naam>_kb` en `<naam>_ko`; `$d025 = HC_MC1`, `$d026 = HC_MC2` voor alle sprites.
- Eldric heeft 12 poses: voor, rug, rechts, links, elk staan en twee looppasjes (`pose_lo`/`pose_hi` in de oude demo `oud/demo/hollowcrown.asm`).
- Oude demo: sprites vanaf $4000, pose gekopieerd naar $0840/$08c0, plaatje op $2000. De nieuwe motor gebruikt VIC-bank 3: sprite-vakken $C400-$C7FF (vak 6 = cursor), bitmap $E000, lettertype $F800 (niet $C800: zie src/geheugen.asm).
- Zwarte omlijning: geen zwarte achtergrond achter de karakters.
- Kijkprogramma met alle karakters: `src/toon/sprites_hc_toon.asm`.

## Mappen en gereedschap
- Indeling volgens §7 van `PROJECT_PROMPT_HOLLOW_CROWN.md`: src/ scripts/ data/ tools/ tests/ build/ docs/ oud/.
- Kick Assembler 5.14: `tools/KickAss.jar`. Java: `/opt/homebrew/opt/openjdk/bin/java` (`/usr/bin/java` is een stub die faalt).
- VICE 3.10: `/Applications/vice-arm64-gtk3-3.10/bin/` (x64sc, c1541, petcat).
- `tools/KickAss.cfg` zet `-symbolfile`: zonder `-symbolfiledir build` komt de .sym naast de bron.
- Laden van D64 met echte drive-emulatie duurt lang: geef VICE in tests genoeg cycli (60M met -warp werkt).
- Referentie: `docs/referentie/` (C64_KICKASS_SKILL.md, KickAssembler.pdf).
- Testen: `python3 tools/vicetest.py tests/*.band` (bouwt zelf). `scherm = ideaal` in een .verwacht vergelijkt elke screenshot pixel voor pixel met het geheugen.
- Kick Assembler: een `.const` moet vóór gebruik staan (anders "not yet defined"); een mislukte `.assert` geeft exitcode 0 (build.sh vangt dat af).
- `$d018` bit 0 leest altijd als 1: maskeer met `& $FE` bij vergelijken.
- Lettertype (tools/lettertype.py): pixelrij 0 van ALLE tekens leeg, anders vuile naden.
- Invoer: lees $DC00/$DC01 alleen in de onderrand-IRQ vóór de Kernal-scan (invoer_hardware). De Kernal-scan laat $DC00 op 0 staan: wie daarna $DC00 leest, ziet alle richtingen + vuur.
- Muis 1351 in VICE: `-controlport1device 3`. De SID meet de muis alleen als $DC00 = $7F (POORT1_POTS) >512 cycli staat.

## Geleerd
<!-- macaimagic:lessons -->
