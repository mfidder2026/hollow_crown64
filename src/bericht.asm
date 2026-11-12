// bericht.asm — wat een karakter zegt, op rij 0-1 in de kleur van de spreker (§4, §6.6).
// Een tekst komt van tools/scriptc.py: schermcodes, $FE = verder op de tweede regel, 0 = einde.
// Hij blijft staan tot zijn tijd om is (1 s + 1 s per 20 tekens, berekend door de compiler) of tot vuur.

.const NIEUWE_REGEL = $fe

.segment Code
// bericht_zeg: tekst op (zp_ptr) in kleur A; de tijd (beelden) staat al in bericht_tijd
bericht_zeg: {
        sta kleur
        jsr bericht_weg                 // eerst leeg
        lda #<(SCHERM + RIJ_BERICHT * 40)
        sta zp_ptr2
        sta zp_ptr3
        lda #>(SCHERM + RIJ_BERICHT * 40)
        sta zp_ptr2 + 1
        clc
        adc #>KLEUR_OFFSET
        sta zp_ptr3 + 1
        ldy #0                          // positie in de tekst
        ldx #0                          // kolom
lus:    lda (zp_ptr),y
        beq klaar
        cmp #NIEUWE_REGEL
        bne teken
        lda zp_ptr2                     // naar de tweede regel: schermadressen + 40 - kolom
        clc
        adc #40
        sta zp_ptr2
        sta zp_ptr3
        bcc !+
        inc zp_ptr2 + 1
        inc zp_ptr3 + 1
!:      ldx #0
        iny
        jmp lus
teken:  sty bron
        stx doel
        ldy doel
        sta (zp_ptr2),y
        lda kleur
        sta (zp_ptr3),y
        ldy bron
        inx
        iny
        bne lus
klaar:  lda #1
        sta bericht_actief
        rts
kleur:  .byte 0
bron:   .byte 0
doel:   .byte 0
}

// bericht_beeld: elk beeld; haalt de tekst weg als zijn tijd om is
bericht_beeld:
        lda bericht_actief
        beq !++
        lda bericht_tijd
        bne !+
        dec bericht_tijd + 1
!:      dec bericht_tijd
        lda bericht_tijd
        ora bericht_tijd + 1
        bne !+
        jmp bericht_weg
!:      rts

// bericht_weg: rij 0-1 leeg
bericht_weg:
        lda #0
        sta bericht_actief
        ldy #RIJ_BERICHT
        lda #0
        jsr rij_wissen
        ldy #RIJ_BERICHT + 1
        lda #0
        jmp rij_wissen

.segment Data
bericht_actief: .byte 0
bericht_tijd:   .word 0
