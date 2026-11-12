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

tekst_hoofdstuk: .text "Hoofdstuk 1: Dawnhaven"
.label tekst_hoofdstuk_lengte = * - tekst_hoofdstuk
                 .byte 0

// Proeftekst voor rij 0-1 (hoofdstuk 1): met staartjes (g, j, p, y), zodat je de naad ziet als hij fout is
tekst_proef1: .text "Zo stil was het plein nog nooit."; .byte 0
tekst_proef2: .text "De fontein lijkt te wachten. Op mij?"; .byte 0
.assert "proeftekst past op een regel", * - tekst_proef2 - 1 <= 40, true
