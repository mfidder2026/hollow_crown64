// flakker.asm — kleine animaties (hoofdstuk 8): kleuren die rondschuiven in een paar vakjes (vuur).
//
// Per kamer hooguit 4 gebieden (FLAKKER in scripts/*.hcs). Elk gebied heeft een eigen tempo (beelden per stap) en
// een rust (extra beelden na een heel rondje). Per stap krijgt elke kleur in die vakjes — in alle drie de
// kleurplekken: scherm-RAM hoog en laag, kleur-RAM — de volgende uit de rij (bv. rood -> oranje -> geel -> rood).
// Andere kleuren blijven. Na een rondje is alles weer het origineel. Zo: vuur (rood oranje geel, tempo 6), knipperende
// ogen (geel zwart, tempo 4, rust 180), ogen die opzij kijken (de pupillen in twee kleuren die ruilen), twinkelende
// sterren, glinsterend water.

.const FLAKKER_REC   = 4 + 16 + 3       // kolom, rij, breedte, hoogte, tabel, tempo, rust, aantal kleuren
.const FLAKKER_MAX   = 4

.segment Code
// flakker_laden: de gebieden van kamer X (ze staan bij de scripts van de kamer, op KAMER_SCRIPTS: tools/scriptc.py);
// elk gebied begint met zijn tempo plus zijn rust (ogen knipperen niet meteen bij binnenkomst)
flakker_laden: {
        lda kamer_flakker_lo,x
        sta fl_ptr
        sta zp_ptr3
        lda kamer_flakker_hi,x
        sta fl_ptr + 1
        sta zp_ptr3 + 1
        ldy #0
        lda (zp_ptr3),y
        beq klaar
        tax                             // X = aantal
        inc zp_ptr3
        bne !+
        inc zp_ptr3 + 1
!:      ldy #0
        sty i
lus:    ldy #20                         // tempo + rust
        lda (zp_ptr3),y
        iny
        clc
        adc (zp_ptr3),y
        ldy i
        sta fl_teller,y
        lda #0
        sta fl_stap,y
        inc i
        lda zp_ptr3
        clc
        adc #FLAKKER_REC
        sta zp_ptr3
        bcc !+
        inc zp_ptr3 + 1
!:      dex
        bne lus
klaar:  rts
i:      .byte 0
}

// flakker_beeld: elk beeld; elk gebied op zijn eigen tempo: elke stap krijgt elke kleur in die vakjes (scherm-RAM hoog
// en laag, kleur-RAM) de volgende uit de rij; na een rondje (alle kleuren) is alles weer het origineel, en dan de rust
flakker_beeld: {
        lda fl_ptr
        sta zp_ptr3
        lda fl_ptr + 1
        sta zp_ptr3 + 1
        ldy #0
        lda (zp_ptr3),y
        bne !+
        rts
!:      sta gebieden
        sty i
        inc zp_ptr3                     // naar het eerste gebied
        bne gebied
        inc zp_ptr3 + 1
gebied: ldx i
        dec fl_teller,x
        beq stap
        jmp volgende
stap:   ldy #20                         // de volgende stap over tempo beelden; na een rondje: tempo + rust
        lda (zp_ptr3),y
        sta fl_teller,x
        inc fl_stap,x
        lda fl_stap,x
        ldy #22
        cmp (zp_ptr3),y
        bcc !+
        lda #0
        sta fl_stap,x
        ldy #21
        lda (zp_ptr3),y
        clc
        adc fl_teller,x
        sta fl_teller,x
!:      inc fl_stappen                  // (voor de tests: hoeveel stappen er geweest zijn)
        ldy #0
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
volgende:
        lda zp_ptr3                     // volgend gebied
        clc
        adc #FLAKKER_REC
        sta zp_ptr3
        bcc !+
        inc zp_ptr3 + 1
!:      inc i
        dec gebieden
        beq klaar
        jmp gebied
klaar:  rts
gebieden: .byte 0
i:      .byte 0
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
fl_teller:  .fill FLAKKER_MAX, 0
fl_stap:    .fill FLAKKER_MAX, 0
geen_flakker: .byte 0
