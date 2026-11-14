// npc.asm — figuren in een kamer (NPC's, hoofdstuk 7): Mira, de wolven, het silhouet van Vex.
//
// Een figuur heeft één pose (2 sprites, uit tools/costume.py): boven elkaar (vorm 0) of naast elkaar (vorm 1).
// Twee slots: slot 0 = sprite 4 en 5 (vak 2, 3), slot 1 = sprite 6 en 7 (vak 4, 5). Een figuur heeft alleen een slot
// zolang hij zichtbaar is: VERBERG maakt zijn slot vrij, TOON pakt een vrij slot (zo kan Mira binnenkomen als de wolf
// weg is). Een kamer mag dus meer figuren hebben, maar er staan er hooguit 2 tegelijk. Geen slot vrij bij TOON:
// vm_fout = VM_FOUT_SLOTS (de tests letten daarop).
// Eldric (sprite 2, 3) komt vóór de figuren (lager nummer). Zichtbaar of niet staat in de spelstatus (st_npc).
// LOOP <figuur> x,y: in een rechte lijn, 1 pixel per beeld per as.

.const NPC_SLOTS = 2
.const NPC_GEEN  = $ff
.const NPC_OVERAL = 255                 // npc_kamer: een figuur die overal mee kan (ACTOR buiten een KAMER)
.const VOLG_AFSTAND = 24                // zo ver (schermpixels) loopt een volger achter Eldric
.const VM_FOUT_SLOTS = $fe              // vm_fout: TOON, maar beide slots zijn bezet

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
        lda #0
        sta vrij                        // het volgende vrije slot
        ldx #0
lus:    cpx #AANTAL_NPC
        bcs klaar
        lda st_npc,x                    // alleen wie zichtbaar is
        beq volgende
        lda npc_kamer,x
        cmp #NPC_OVERAL                 // een figuur die overal mee kan (Tik, Mira die volgt)
        bne !+
        ldy st_kamer                    // (niet op een toneel)
        lda kamer_toneel,y
        bne volgende
        jsr volger_bij_eldric           // volgt hij Eldric, dan staat hij vlak achter hem
        jmp in_slot
!:      cmp st_kamer
        bne volgende
in_slot:
        ldy vrij
        cpy #NPC_SLOTS
        bcs klaar
        txa
        sta slot_npc,y
        jsr kostuum_naar_slot           // X = figuur, Y = slot
        inc vrij
volgende:
        inx
        jmp lus
klaar:  jmp npc_sprites
vrij:   .byte 0
}

// volger_bij_eldric: volgt figuur X Eldric, dan zet hem vlak achter Eldric (X blijft)
volger_bij_eldric: {
        lda npc_volgt,x
        beq klaar
        jsr volg_doel
        lda npc_dx_lo,x
        sta npc_px_lo,x
        lda npc_dx_hi,x
        sta npc_px_hi,x
        lda npc_dy,x
        sta npc_py,x
        lda #0
        sta npc_lopen,x
klaar:  rts
}

// volg_doel: het doel van een volger X: een stukje achter Eldric (links van hem, of rechts als hij naar links kijkt);
// buiten niet hoger dan de eerste SCHAAL-grens (een figuur wordt niet kleiner: achteraan zou hij een reus zijn)
volg_doel: {
        lda act_richting
        cmp #3                          // LINKS: erachter is rechts
        beq rechts
        lda act_x
        sec
        sbc #VOLG_AFSTAND
        sta npc_dx_lo,x
        lda act_x + 1
        sbc #0
        sta npc_dx_hi,x
        bcs y                           // (niet voorbij de linkerrand)
        lda #0
        sta npc_dx_lo,x
        sta npc_dx_hi,x
        jmp y
rechts: lda act_x
        clc
        adc #VOLG_AFSTAND
        sta npc_dx_lo,x
        lda act_x + 1
        adc #0
        sta npc_dx_hi,x
y:      lda schaal_aantal               // buiten (SCHAAL): een figuur heeft maar één maat, dus hij gaat niet
        beq !+                          // dieper de kamer in dan de grootste maat; daar wacht hij op Eldric
        lda act_y
        cmp schaal_grens                // (de eerste grens: tot daar is Eldric ook op zijn grootst)
        bcs !++
        lda schaal_grens
        bcc !++
!:      lda act_y
!:      sta npc_dy,x
        rts
}

// npc_toon: figuur X zichtbaar; staat hij in deze kamer, dan krijgt hij een vrij slot
npc_toon: {
        lda #1
        sta st_npc,x
        lda npc_kamer,x
        cmp #NPC_OVERAL
        beq !+
        cmp st_kamer
        bne klaar
!:
        txa                             // heeft hij al een slot?
        cmp slot_npc
        beq klaar
        cmp slot_npc + 1
        beq klaar
        ldy #0
!:      lda slot_npc,y
        cmp #NPC_GEEN
        beq vrij
        iny
        cpy #NPC_SLOTS
        bne !-
        lda #VM_FOUT_SLOTS              // geen slot vrij
        sta vm_fout
        rts
vrij:   txa
        sta slot_npc,y
        jsr kostuum_naar_slot
        jsr volger_bij_eldric           // een volger verschijnt vlak achter Eldric
        jmp npc_sprites
klaar:  rts
}

// npc_verberg: figuur X weg; zijn slot komt vrij (npc_sprites zet de sprites uit)
npc_verberg: {
        lda #0
        sta st_npc,x
        ldy #0
!:      txa
        cmp slot_npc,y
        bne !+
        lda #NPC_GEEN
        sta slot_npc,y
!:      iny
        cpy #NPC_SLOTS
        bne !--
        jmp npc_sprites
}

// kostuum_naar_slot: het kostuum van figuur X naar de vakken van slot Y; kleuren en multicolor (X, Y blijven)
kostuum_naar_slot: {
        stx fig
        sty slot
        lda npc_data_lo,x
        sta zp_ptr
        lda npc_data_hi,x
        sta zp_ptr + 1
        ldy slot                        // vak 2 + 2 * slot: SPRITE_VAKKEN + 128 + slot * 128
        lda slot_vak_lo,y
        sta zp_ptr2
        lda slot_vak_hi,y
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
        // X: voeten - 12 (vorm 0) of - 24 (vorm 1), + 24 rand; vorm 2 (een reus): dubbel groot
        lda $d017                       // eerst: niet vergroot (alleen een reus wel)
        and slot_niet,y
        sta $d017
        lda $d01d
        and slot_niet,y
        sta $d01d
        lda npc_vorm,x
        beq gewoon
        cmp #2
        bne naast
        jmp reus
gewoon:
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
        // een reus (vorm 2): de sprites dubbel zo breed en hoog. X: voeten - 24 + 24 rand = voeten;
        // Y boven = y + 16 + 50 - 2 * voeten - 1, onder = + 42
reus:   lda $d017
        ora slot_bits,y
        sta $d017
        lda $d01d
        ora slot_bits,y
        sta $d01d
        lda npc_px_lo,x
        sta x1
        sta x2
        lda npc_px_hi,x
        sta x1 + 1
        sta x2 + 1
        lda npc_voeten,x
        asl
        sta hulp
        lda npc_py,x
        clc
        adc #RIJ_KAMER * 8 + 50 - 1
        sec
        sbc hulp
        sta y1
        clc
        adc #42
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
lus:    lda npc_volgt,x                 // een volger: elk beeld een doel vlak achter Eldric
        beq !+
        lda st_npc,x
        beq volgende
        jsr volg_doel
        lda #1
        sta npc_lopen,x
!:      lda npc_lopen,x
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
slot_vak_lo:  .byte <(SPRITE_VAKKEN + 128), <(SPRITE_VAKKEN + 256)
slot_vak_hi:  .byte >(SPRITE_VAKKEN + 128), >(SPRITE_VAKKEN + 256)
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
