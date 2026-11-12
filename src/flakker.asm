// flakker.asm — kleine animaties (hoofdstuk 8): kleuren die rondschuiven in een paar vakjes (vuur).
//
// Per kamer hooguit 2 gebieden (FLAKKER in scripts/*.hcs). Elke FLAKKER_TEMPO beelden krijgt elke kleur in die
// vakjes — in alle drie de kleurplekken: scherm-RAM hoog en laag, kleur-RAM — de volgende uit de rij
// (bv. rood -> oranje -> geel -> rood). Andere kleuren blijven. Na een rondje is alles weer het origineel.

.const FLAKKER_TEMPO = 6
.const FLAKKER_REC   = 4 + 16           // kolom, rij, breedte, hoogte, tabel

.segment Code
// flakker_laden: de gebieden van kamer X
flakker_laden:
        lda kamer_flakker_lo,x
        sta fl_ptr
        lda kamer_flakker_hi,x
        sta fl_ptr + 1
        rts

// flakker_beeld: elk beeld
flakker_beeld: {
        dec teller
        bmi !+
        rts
!:      lda #FLAKKER_TEMPO - 1
        sta teller
        inc fl_stappen                  // (voor de tests: hoeveel stappen er geweest zijn)
        lda fl_ptr
        sta zp_ptr3
        lda fl_ptr + 1
        sta zp_ptr3 + 1
        ldy #0
        lda (zp_ptr3),y
        sta gebieden
        bne !+
        rts
!:      inc zp_ptr3                     // naar het eerste gebied
        bne !+
        inc zp_ptr3 + 1
!:
gebied: ldy #0
        lda (zp_ptr3),y
        sta kol
        iny
        lda (zp_ptr3),y
        sta rij
        iny
        lda (zp_ptr3),y
        sta breed
        iny
        lda (zp_ptr3),y
        sta hoog
        ldy #19                         // de tabel (byte 4-19) naar een vaste plek
!:      lda (zp_ptr3),y
        sta tabel - 4,y
        dey
        cpy #3
        bne !-
        lda #0
        sta r
rijen:  lda r
        clc
        adc rij
        adc #RIJ_KAMER
        tax
        lda rij_lo,x
        clc
        adc kol
        sta zp_ptr2
        lda rij_hi,x
        adc #0
        sta zp_ptr2 + 1
        ldy breed
        dey
vak:    lda (zp_ptr2),y                 // scherm-RAM: twee kleuren
        pha
        and #$0f
        tax
        lda tabel,x
        sta laag
        pla
        lsr
        lsr
        lsr
        lsr
        tax
        lda tabel,x
        asl
        asl
        asl
        asl
        ora laag
        sta (zp_ptr2),y
        lda zp_ptr2 + 1                 // kleur-RAM
        pha
        clc
        adc #>KLEUR_OFFSET
        sta zp_ptr2 + 1
        lda (zp_ptr2),y
        and #$0f
        tax
        lda tabel,x
        sta (zp_ptr2),y
        pla
        sta zp_ptr2 + 1
        dey
        bpl vak
        inc r
        lda r
        cmp hoog
        bne rijen
        lda zp_ptr3                     // volgend gebied
        clc
        adc #FLAKKER_REC
        sta zp_ptr3
        bcc !+
        inc zp_ptr3 + 1
!:      dec gebieden
        beq klaar
        jmp gebied
klaar:  rts
teller:   .byte 0
gebieden: .byte 0
kol:    .byte 0
rij:    .byte 0
breed:  .byte 0
hoog:   .byte 0
r:      .byte 0
laag:   .byte 0
tabel:  .fill 16, 0
}

.segment Data
fl_ptr: .word geen_flakker
fl_stappen: .byte 0
geen_flakker: .byte 0
