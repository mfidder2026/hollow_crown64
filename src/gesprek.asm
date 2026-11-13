// gesprek.asm — praten (§4, hoofdstuk 7): de werkwoorden maken plaats voor hooguit 4 keuzes (rij 19-22).
//
// Een gesprek (tools/scriptc.py): aantal keuzes; per keuze einde, soort voorwaarde, argument, tekst, script.
// Er staan alleen keuzes waarvan de voorwaarde klopt (de eerste 4). De keuze onder de cursor is geel.
// Klik: het script van die keuze draait (de keuzes zijn dan weg); daarna staan ze er weer, of — als de keuze
// EINDE had — is het gesprek voorbij en komen de werkwoorden en de inventaris terug.

.const GS_MAX_ZICHTBAAR = 4
.const GS_RIJ           = RIJ_WERKWOORD // rij 19-22

.segment Code
// gesprek_start: gesprek op A (laag) / X (hoog)
gesprek_start:
        sta gs_ptr
        stx gs_ptr + 1
        lda #1
        sta gs_actief
        lda #0
        sta gs_getoond
        sta gs_einde_na
        jsr vm_rijen_leeg
        rts

// gesprek_beeld: elk beeld (vanuit zin_beeld)
gesprek_beeld: {
        lda vm_pc + 1                   // er loopt een script (een keuze): niets tonen
        ora bericht_actief
        beq !+
        rts
!:      lda gs_einde_na                 // de keuze met EINDE is klaar: het gesprek is voorbij
        beq !+
        jmp gesprek_stop
!:      lda gs_getoond
        bne hover
        jsr keuzes_tonen
hover:  lda #$ff                        // welke rij is geel?
        ldx cursor_y
        cpx #GS_RIJ * 8
        bcc !+
        txa
        lsr
        lsr
        lsr
        sec
        sbc #GS_RIJ
        cmp gs_aantal
        bcc !+
        lda #$ff
!:      cmp gs_geel
        beq klaar
        sta gs_geel
        ldy #0                          // kleuren van de keuzerijen
kl:     cpy gs_aantal
        beq klaar
        lda rij_kleur_lo,y
        sta zp_ptr3
        lda rij_kleur_hi,y
        sta zp_ptr3 + 1
        lda #KLEUR_WERKWOORD
        cpy gs_geel
        bne !+
        lda #KLEUR_GEKOZEN
!:      sty hulp
        ldy #39
!:      sta (zp_ptr3),y
        dey
        bpl !-
        ldy hulp
        iny
        jmp kl
klaar:  rts
hulp:   .byte 0
}

// keuzes_tonen: de keuzes waarvan de voorwaarde klopt (hooguit 4) op rij 19-22
keuzes_tonen: {
        jsr vm_rijen_leeg
        lda gs_ptr
        sta zp_ptr3
        lda gs_ptr + 1
        sta zp_ptr3 + 1
        ldy #0
        lda (zp_ptr3),y
        sta totaal
        lda #0
        sta k
        sta gs_aantal
lus:    lda k
        cmp totaal
        beq klaar
        lda gs_aantal
        cmp #GS_MAX_ZICHTBAAR
        beq klaar
        lda k                           // keuze k begint op 1 + 7k
        asl
        asl
        asl
        sec
        sbc k
        clc
        adc #1
        sta plek
        jsr voorwaarde                  // C = 1: tonen
        bcc volgende
        ldx gs_aantal
        lda k
        sta gs_keuze,x
        ldy plek                        // tekst
        iny
        iny
        iny
        lda (zp_ptr3),y
        sta zp_ptr
        iny
        lda (zp_ptr3),y
        sta zp_ptr + 1
        lda gs_aantal
        clc
        adc #GS_RIJ
        tay
        ldx #0
        lda #KLEUR_WERKWOORD
        jsr tekst_schrijf
        inc gs_aantal
        lda gs_ptr                      // tekst_schrijf gebruikt zp_ptr3: terugzetten
        sta zp_ptr3
        lda gs_ptr + 1
        sta zp_ptr3 + 1
volgende:
        inc k
        jmp lus
klaar:  lda #1
        sta gs_getoond
        lda #$fe
        sta gs_geel
        rts

// voorwaarde van de keuze op plek: soort 0 geen, 1 vlag, 2 NIET vlag, 3 HEEFT, 4 NIET HEEFT
voorwaarde:
        ldy plek
        iny
        lda (zp_ptr3),y                 // soort
        beq ja
        sta soort
        iny
        lda (zp_ptr3),y                 // argument
        ldx soort
        cpx #3
        bcs heeft
        pha                             // vlag: byte = arg / 8, bit = arg & 7
        lsr
        lsr
        lsr
        tax
        pla
        and #7
        tay
        lda st_vlaggen,x
        and bits,y
        beq uit
        lda #1                          // staat
uit:    ldx soort
        cpx #2
        bne !+
        eor #1                          // NIET (A is 0 of de bit; maak er 0/1 van)
!:      jmp uitkomst
heeft:  tax                             // HEEFT: 1 als het voorwerp bij Eldric is
        jsr eigenaar_van                // status.asm (X blijft)
        tay
        lda #0
        cpy #EIGENAAR_ELDRIC
        bne !+
        lda #1
!:      ldx soort
        cpx #4
        bne uitkomst
        eor #1                          // NIET HEEFT
uitkomst:
        cmp #0
        beq nee
ja:     sec
        rts
nee:    clc
        rts
totaal: .byte 0
k:      .byte 0
plek:   .byte 0
soort:  .byte 0
}

// gesprek_klik: vuur tijdens een gesprek
gesprek_klik: {
        lda gs_getoond
        beq klaar
        lda cursor_y
        cmp #GS_RIJ * 8
        bcc klaar
        lsr
        lsr
        lsr
        sec
        sbc #GS_RIJ
        cmp gs_aantal
        bcs klaar
        tax
        lda gs_keuze,x                  // plek in de tabel: 1 + 7k
        sta k
        asl
        asl
        asl
        sec
        sbc k
        clc
        adc #1
        tay
        lda gs_ptr
        sta zp_ptr3
        lda gs_ptr + 1
        sta zp_ptr3 + 1
        lda (zp_ptr3),y                 // einde?
        sta gs_einde_na
        tya
        clc
        adc #5
        tay
        lda (zp_ptr3),y                 // script
        pha
        iny
        lda (zp_ptr3),y
        tax
        pla
        jsr vm_start
        lda #0
        sta gs_getoond
        jsr vm_rijen_leeg
klaar:  rts
k:      .byte 0
}

// gesprek_stop: werkwoorden, zinregel en inventaris terug
gesprek_stop:
        lda #0
        sta gs_actief
        sta gs_einde_na
        jsr balk_tekenen
        lda #1
        sta inventaris_anders
        lda #$fe
        sta ww_kleur
        sta zin_ww
        rts

// vm_rijen_leeg: rij 18-23 leeg (zinregel, werkwoorden, inventaris)
vm_rijen_leeg: {
        ldy #RIJ_ZIN
!:      tya
        pha
        lda #KLEUR_WERKWOORD
        jsr rij_wissen
        pla
        tay
        iny
        cpy #RIJ_INVENTARIS + 2
        bne !-
        rts
}

.segment Data
gs_actief:   .byte 0
gs_ptr:      .word 0
gs_getoond:  .byte 0
gs_aantal:   .byte 0
gs_geel:     .byte $fe
gs_einde_na: .byte 0
gs_keuze:    .fill GS_MAX_ZICHTBAAR, 0
rij_kleur_lo: .fill GS_MAX_ZICHTBAAR, <(KLEUR_RAM + (GS_RIJ + i) * 40)
rij_kleur_hi: .fill GS_MAX_ZICHTBAAR, >(KLEUR_RAM + (GS_RIJ + i) * 40)
