// invoer.asm — joystick in poort 2 (§4). In een AUTOTEST-build komt de invoer van de band.
// Muis (1351, poort 1) en toetsen per werkwoord komen later.

.segment Code
// invoer_lees: zet invoer_stick (1 = ingedrukt; bit 0 op, 1 neer, 2 links, 3 rechts, 4 vuur)
// en invoer_vuur (1 alleen in het beeld waarin vuur wordt ingedrukt).
invoer_lees:
#if AUTOTEST
        jsr band_invoer
#else
        lda $dc00                       // CIA 1 poort A: joystick 2, actief laag
        eor #%00011111
        and #%00011111
        sta invoer_stick
#endif
        lda invoer_stick
        and #%10000
        tax
        eor invoer_vorig                // nieuw ingedrukt = nu aan en vorig beeld uit
        and invoer_stick
        lsr
        lsr
        lsr
        lsr
        sta invoer_vuur
        stx invoer_vorig
        beq !+
        inc invoer_vuur_teller
!:      rts

.segment Data
invoer_stick:       .byte 0
invoer_vorig:       .byte 0
invoer_vuur:        .byte 0
invoer_vuur_teller: .byte 0             // telt het aantal keer vuur (voor de tests)
