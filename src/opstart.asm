// opstart.asm — code die alleen bij het starten loopt. Hij staat in het bestand op $B000 (segment Opstart, in de
// kamerbuffer) en niet in het hoofdprogramma: de eerste kamer overschrijft hem, en dan is hij ook niet meer nodig.
// Let op: niets hier mag kamer_wissel aanroepen (dan wordt de code onder zijn eigen voeten overschreven).

.const TAAL_BEWAAR = $c200              // de spelstatus bij een taalwissel (cartridge.asm taal_kiezen): de boot en het
                                        // taalmenu raken $C200-$C2FF niet (src/crtboot.asm: $C000-$C1FF, het menu $4400-$870F)

.segment Opstart
// figuren_onder_io: de figuren van $A000 (zo staan ze in het bestand) naar het RAM onder de I/O ($D000)
figuren_onder_io: {
        php
        sei
        lda #$34                        // alleen RAM
        sta $01
        lda #<KAMER_BUF
        sta zp_ptr
        lda #>KAMER_BUF
        sta zp_ptr + 1
        lda #$00
        sta zp_ptr2
        lda #$d0
        sta zp_ptr2 + 1
        ldx #ONDER_IO_PAGINAS
        ldy #0
!:      lda (zp_ptr),y
        sta (zp_ptr2),y
        iny
        bne !-
        inc zp_ptr + 1
        inc zp_ptr2 + 1
        dex
        bne !-
        lda #CPU_NORMAAL
        sta $01
        plp
        rts
}

#if CRT
// taal_terug: staat er op TAAL_BEWAAR een spelstatus van deze versie (magic "HC" en STATUS_VERSIE), dan wordt dat de
// spelstatus en is taal_terug_gedaan 1. De magic wordt gewist: een reset begint daarna gewoon opnieuw.
taal_terug: {
        lda #0
        sta taal_terug_gedaan
        ldx #2
!:      lda TAAL_BEWAAR,x
        cmp spelstatus,x
        bne klaar
        dex
        bpl !-
        ldx #0
!:      lda TAAL_BEWAAR,x
        sta spelstatus,x
        inx
        cpx #STATUS_GROOTTE
        bne !-
        lda #0
        sta TAAL_BEWAAR
        lda #1
        sta taal_terug_gedaan
klaar:  rts
}

// taal_verder: de balk, en Eldric terug waar hij stond; A = de kamer (main.asm roept daarna kamer_wissel aan)
taal_verder: {
        jsr balk_tekenen
        lda st_x
        sta kw_x
        lda st_x + 1
        sta kw_x + 1
        lda st_y
        sta kw_y
        lda #0
        sta kw_richting
        lda #1
        sta inventaris_anders
        lda st_kamer
        rts
}
taal_terug_gedaan: .byte 0
#endif
