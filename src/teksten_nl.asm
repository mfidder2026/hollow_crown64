// teksten_nl.asm — de vaste teksten van de motor, in het Nederlands (§6.6).
// Een andere taal krijgt een eigen bestand met dezelfde labels (teksten_en.asm).
// De teksten van het spel zelf komen later uit scripts/*.hcs.
// Tekens buiten screencode_mixed (↑ ↓ ë ...): zie EXTRA in tools/lettertype.py.

.segment Data
.encoding "screencode_mixed"

// De 12 werkwoorden, in de volgorde van de balk (3 rijen x 4 kolommen), elk hooguit 9 tekens
ww_ga_naar:   .text "Ga naar";   .byte 0
ww_pak:       .text "Pak";       .byte 0
ww_gebruik:   .text "Gebruik";   .byte 0
ww_open:      .text "Open";      .byte 0
ww_bekijk:    .text "Bekijk";    .byte 0
ww_praat:     .text "Praat met"; .byte 0
ww_geef:      .text "Geef";      .byte 0
ww_sluit:     .text "Sluit";     .byte 0
ww_duw:       .text "Duw";       .byte 0
ww_trek:      .text "Trek";      .byte 0
ww_lees:      .text "Lees";      .byte 0
ww_wat_is:    .text "Wat is";    .byte 0

werkwoorden_lo: .byte <ww_ga_naar, <ww_pak, <ww_gebruik, <ww_open, <ww_bekijk, <ww_praat
                .byte <ww_geef, <ww_sluit, <ww_duw, <ww_trek, <ww_lees, <ww_wat_is
werkwoorden_hi: .byte >ww_ga_naar, >ww_pak, >ww_gebruik, >ww_open, >ww_bekijk, >ww_praat
                .byte >ww_geef, >ww_sluit, >ww_duw, >ww_trek, >ww_lees, >ww_wat_is
.const AANTAL_WERKWOORDEN = 12

// voorzetsels voor zinnen met twee voorwerpen: "Gebruik kruik met vat", "Geef steen aan Mira"
vz_met:       .text "met";       .byte 0
vz_aan:       .text "aan";       .byte 0
vz_geen:      .byte 0
voorzetsel_lo: .byte <vz_geen, <vz_geen, <vz_met, <vz_geen, <vz_geen, <vz_geen
               .byte <vz_aan, <vz_geen, <vz_geen, <vz_geen, <vz_geen, <vz_geen
voorzetsel_hi: .byte >vz_geen, >vz_geen, >vz_met, >vz_geen, >vz_geen, >vz_geen
               .byte >vz_aan, >vz_geen, >vz_geen, >vz_geen, >vz_geen, >vz_geen

tekst_laden:     .text "Laden..."
.label tekst_laden_lengte = * - tekst_laden
                 .byte 0
tekst_opslaan:   .text "Opslaan..."
.label tekst_opslaan_lengte = * - tekst_opslaan
                 .byte 0
tekst_spel_laden: .text "Spel laden..."
.label tekst_spel_laden_lengte = * - tekst_spel_laden
                 .byte 0
// meldingen (rij 0-1, zoals Eldric praat)
tekst_opgeslagen:       .text "Het spel is opgeslagen."; .byte 0
tekst_opslaan_fout:     .text "Opslaan lukte niet. Zit de diskette erin?"; .byte 0
tekst_geladen:          .text "Daar ben ik weer."; .byte 0
tekst_niets_opgeslagen: .text "Er is geen opgeslagen spel."; .byte 0
tekst_voltooid:  .text "Hoofdstuk 1 voltooid"
.label tekst_voltooid_lengte = * - tekst_voltooid
                 .byte 0
// de menubalk (menu.asm)
tekst_bestand:      .text "Bestand"; .byte 0
tekst_score:        .text "Score"; .byte 0
tekst_bosskey:      .text "Bosskey"; .byte 0
tekst_opslaan_menu: .text "Opslaan"; .byte 0
tekst_laden_menu:   .text "Laden"; .byte 0
tekst_exit:         .text "Exit"; .byte 0
tekst_lichtpunten:  .text "Lichtpunten:"; .byte 0
tekst_van_max:      .text "van 250"; .byte 0
// het intro (intro.asm)
tekst_druk:      .text "Druk op spatie of vuur"
.label tekst_druk_lengte = * - tekst_druk
                 .byte 0
tekst_scroll:
        .text "Hollow Crown ... Het rijk Aethermoor leefde onder de Eeuwige Zon, tot de nacht van de dubbele "
        .text "maansverduistering. Toen kroop de Holle Koning uit de aarde, stal het zonlicht en nam het kasteel. "
        .text "Sindsdien is het overal schemer. Eldric, de laatste Wachter van de Lichte Kroon, draagt het "
        .text "laatste lichtfragment in zijn zwaard. Help hem het licht terug te brengen ... "
        .text "Bediening: joystick in poort 2, 1351-muis in poort 1, of de cursortoetsen met spatie als vuur. "
        .text "F1 muziek aan/uit, F5 opslaan, F7 laden ... "
        .text "Een point-and-click-avontuur voor de Commodore 64, gemaakt met Kick Assembler, Python en VICE. "
        .text "Muziek: een eigen thema in D-mineur. Plaatjes: FLUX. ... "
        .text "Groeten aan iedereen die nog een C64 aanzet!          "
        .byte 0
tekst_hoofdstuk: .text "Hoofdstuk 1: Dawnhaven"
.label tekst_hoofdstuk_lengte = * - tekst_hoofdstuk
                 .byte 0
