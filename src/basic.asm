// basic.asm — menu Bestand, Exit: terug naar BASIC (READY.), en lukt dat niet, een reset.
//
// Het spel heeft alles naar zijn hand gezet: eigen raster-IRQ's, VIC-bank 3, BASIC-ROM uit ($01 = $36), de SID.
// Terug: de raster-IRQ uit, de SID stil, de ROM's aan ($37), en dan de Kernal zelf alles laten opzetten zoals na het
// aanzetten: IOINIT (de CIA's, ook VIC-bank 0 en de klok-IRQ), RESTOR (de vectoren, ook $0314), CINT (VIC en scherm:
// het gewone scherm op $0400 met de gewone letters). Dan de warme start van BASIC: "READY.". Het programma staat nog
// in het geheugen: RUN start het spel opnieuw.

.segment Code
naar_basic: {
        sei
        lda #0
        sta $d01a                       // geen raster-IRQ meer
        lda #$ff
        sta $d019
        sta naar_basic_gedaan           // (voor de tests)
        lda #0
        sta $d015                       // geen sprites
        jsr geluid_stil                 // de SID helemaal stil
        lda #$37                        // BASIC, Kernal en I/O aan
        sta $01
#if AUTOTEST
        lda #2                          // BAND_KLAAR (autotest.asm): vicetest kijkt straks naar het BASIC-scherm
        sta band_status
        lda #0
        sta band_markering
#endif
        jsr $fda3                       // IOINIT
        jsr $fd15                       // RESTOR
        jsr $ff5b                       // CINT
        cli
        jmp ($a002)                     // BASIC warme start: READY.
}

.segment Data
naar_basic_gedaan: .byte 0
