// npc.asm — figuren in een kamer (NPC's, hoofdstuk 7): Mira, de wolven, het silhouet van Vex.
//
// Een figuur heeft één pose (2 sprites, uit tools/costume.py): boven elkaar (vorm 0) of naast elkaar (vorm 1).
// Hooguit 2 per kamer: slot 0 = sprite 4 en 5 (vak 2, 3), slot 1 = sprite 6 en 7 (vak 4, 5).
// Eldric (sprite 2, 3) komt vóór de figuren (lager nummer). Zichtbaar of niet staat in de spelstatus (st_npc).
// LOOP <figuur> x,y: in een rechte lijn, 1 pixel per beeld per as.

.const NPC_SLOTS = 2
.const NPC_GEEN  = $ff

.segment Code
// npc_begin: posities uit de tabel (bij het begin van het spel)
npc_begin:
        ldx #AANTAL_NPC - 1
        bmi !++
!:      lda npc_x_lo,x
        sta npc_px_lo,x
        lda npc_x_hi,x
        sta npc_px_hi,x
        lda npc_y,x
        sta npc_py,x
        lda #0
        sta npc_lopen,x
        dex
        bpl !-
!:      rts

// npc_kamer_in: de figuren van deze kamer in de slots zetten (na het laden van een kamer)
npc_kamer_in: {
        lda #NPC_GEEN
        sta slot_npc
        sta slot_npc + 1
        ldy #0                          // het volgende vrije slot
        ldx #0
lus:    cpx #AANTAL_NPC
        bcs klaar
        lda npc_kamer,x
        cmp st_kamer
        bne volgende
        cpy #NPC_SLOTS
        bcs klaar
        txa
        sta slot_npc,y
        jsr kostuum_naar_slot           // X = figuur, Y = slot
        iny
volgende:
        inx
        jmp lus
klaar:  jmp npc_sprites
}

// kostuum_naar_slot: het kostuum van figuur X naar de vakken van slot Y; kleuren en multicolor (X, Y blijven)
kostuum_naar_slot: {
        stx fig
        sty slot
        lda npc_data_lo,x
        sta zp_ptr
        lda npc_data_hi,x
        sta zp_ptr + 1
        lda slot                        // vak 2 + 2 * slot: SPRITE_VAKKEN + 128 + slot * 128
        lsr
        lda #0
        ror                             // slot 1 -> $80
        clc
        adc #<(SPRITE_VAKKEN + 128)
        sta zp_ptr2
        lda #>(SPRITE_VAKKEN + 128)
        adc slot
        sta zp_ptr2 + 1
        ldy #127
!:      lda (zp_ptr),y
        sta (zp_ptr2),y
        dey
        bpl !-
        ldy slot
        lda slot_ptr,y                  // sprite-pointers
        ldx slot_sprite,y
        sta SPRITE_PTR,x
        clc
        adc #1
        sta SPRITE_PTR + 1,x
        ldx fig
        lda npc_kb,x                    // kleuren: $d027 + spritenummer
        pha
        lda npc_ko,x
        ldx slot_sprite,y
        sta $d028,x
        pla
        sta $d027,x
        lda $d01c
        ora slot_bits,y                 // multicolor
        sta $d01c
        lda $d01b
        and slot_niet,y
        sta $d01b
        ldx fig
        ldy slot
        rts
fig:    .byte 0
slot:   .byte 0
}

// npc_sprites: elk beeld: de sprites van de slots aan/uit en op hun plek
npc_sprites: {
        ldy #0
lus:    lda slot_npc,y
        cmp #NPC_GEEN
        bne !+
        jmp uit
!:      tax
        lda st_npc,x
        bne !+
        jmp uit
!:      lda $d015
        ora slot_bits,y
        sta $d015
        // X: voeten - 12 (vorm 0) of - 24 (vorm 1), + 24 rand
        lda npc_vorm,x
        bne naast
        lda npc_px_lo,x
        clc
        adc #12
        sta x1
        lda npc_px_hi,x
        adc #0
        sta x1 + 1
        lda x1
        sta x2
        lda x1 + 1
        sta x2 + 1
        lda npc_py,x                    // Y boven = y + 16 + 50 - voeten, onder = + 21
        clc
        adc #RIJ_KAMER * 8 + 50
        sec
        sbc npc_voeten,x
        sta y1
        clc
        adc #21
        sta y2
        jmp zet
naast:  lda npc_px_lo,x
        sta x1
        lda npc_px_hi,x
        sta x1 + 1
        lda x1
        clc
        adc #24
        sta x2
        lda x1 + 1
        adc #0
        sta x2 + 1
        lda npc_py,x
        clc
        adc #RIJ_KAMER * 8 + 50
        sec
        sbc npc_voeten,x
        sta y1
        sta y2
zet:    ldx slot_sprite,y               // sprite n: $d000 + 2n
        txa
        asl
        tax
        lda x1
        sta $d000,x
        lda y1
        sta $d001,x
        lda x2
        sta $d002,x
        lda y2
        sta $d003,x
        lda $d010                       // bit 8 van X
        and slot_niet,y
        sta hulp
        lda x1 + 1
        beq !+
        lda slot_bits,y
        and #%01010000                  // de eerste sprite van het slot
        ora hulp
        sta hulp
!:      lda x2 + 1
        beq !+
        lda slot_bits,y
        and #%10100000                  // de tweede
        ora hulp
        sta hulp
!:      lda hulp
        sta $d010
        jmp volgende
uit:    lda $d015
        and slot_niet,y
        sta $d015
volgende:
        iny
        cpy #NPC_SLOTS
        beq !+
        jmp lus
!:      rts
x1:     .word 0
x2:     .word 0
y1:     .byte 0
y2:     .byte 0
hulp:   .byte 0
}

// npc_beweeg: elk beeld: figuren die lopen een stap dichter bij hun doel
npc_beweeg: {
        ldx #AANTAL_NPC - 1
        bmi klaar
lus:    lda npc_lopen,x
        beq volgende
        lda npc_px_lo,x                 // x naar het doel (16 bits, 1 per beeld)
        cmp npc_dx_lo,x
        bne !+
        lda npc_px_hi,x
        cmp npc_dx_hi,x
        beq y
!:      lda npc_px_lo,x
        cmp npc_dx_lo,x
        lda npc_px_hi,x
        sbc npc_dx_hi,x
        bcs links
        inc npc_px_lo,x
        bne y
        inc npc_px_hi,x
        jmp y
links:  lda npc_px_lo,x
        bne !+
        dec npc_px_hi,x
!:      dec npc_px_lo,x
y:      lda npc_py,x
        cmp npc_dy,x
        beq klaar_y
        bcs op
        inc npc_py,x
        jmp klaar_y
op:     dec npc_py,x
klaar_y:
        lda npc_px_lo,x                 // er?
        cmp npc_dx_lo,x
        bne volgende
        lda npc_px_hi,x
        cmp npc_dx_hi,x
        bne volgende
        lda npc_py,x
        cmp npc_dy,x
        bne volgende
        lda #0
        sta npc_lopen,x
volgende:
        dex
        bpl lus
klaar:  rts
}

.segment Data
slot_npc:     .byte NPC_GEEN, NPC_GEEN
slot_sprite:  .byte 4, 6
slot_bits:    .byte %00110000, %11000000
slot_niet:    .byte %11001111, %00111111
slot_ptr:     .byte (SPRITE_VAKKEN - SCHERM) / 64 + 2, (SPRITE_VAKKEN - SCHERM) / 64 + 4
npc_px_lo:    .fill MAX_NPC, 0          // waar de figuur nu staat (voeten, schermpixels)
npc_px_hi:    .fill MAX_NPC, 0
npc_py:       .fill MAX_NPC, 0
npc_dx_lo:    .fill MAX_NPC, 0          // LOOP: het doel
npc_dx_hi:    .fill MAX_NPC, 0
npc_dy:       .fill MAX_NPC, 0
npc_lopen:    .fill MAX_NPC, 0
