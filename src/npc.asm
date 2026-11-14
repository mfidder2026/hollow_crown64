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
        bcs tweede
        lda st_npc,x                    // alleen wie zichtbaar is
        beq volgende
        lda npc_vliegt,x                // vliegers pas daarna (tweede)
        bne volgende
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
        bcs tweede
        txa
        sta slot_npc,y
        jsr kostuum_naar_slot           // X = figuur, Y = slot
        inc vrij
volgende:
        inx
        jmp lus
tweede: ldx #0                          // de vliegers (versiering): in het hoogste vrije slot, dan blijft slot 0
lus2:   cpx #AANTAL_NPC                 // voor wie later verschijnt (Tik)
        bcs klaar
        lda npc_vliegt,x
        beq volgende2
        lda st_npc,x
        beq volgende2
        lda npc_kamer,x
        cmp st_kamer
        bne volgende2
        ldy #NPC_SLOTS - 1
!:      lda slot_npc,y
        cmp #NPC_GEEN
        beq !+
        dey
        bpl !-
        bmi klaar
!:      txa
        sta slot_npc,y
        jsr kostuum_naar_slot
volgende2:
        inx
        jmp lus2
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
        stx bewaar                      // geen slot vrij: een vlieger maakt plaats (hij vliegt onzichtbaar verder)
        ldy #NPC_SLOTS - 1
!:      lda slot_npc,y
        tax
        lda npc_vliegt,x
        bne wijkt
        dey
        bpl !-
        ldx bewaar
        lda #VM_FOUT_SLOTS              // geen slot vrij
        sta vm_fout
        rts
wijkt:  ldx bewaar
vrij:   txa
        sta slot_npc,y
        jsr kostuum_naar_slot
        jsr volger_bij_eldric           // een volger verschijnt vlak achter Eldric
        jmp npc_sprites
klaar:  rts
bewaar: .byte 0
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

// zet_kant_vlieger: zoals zet_kant, maar ook voor een vlieger (0 vleugels op naar rechts, 1 neer naar rechts, 2 neer
// naar links, 3 op naar links)
.label zet_kant_vlieger = zet_kant.zet

// zet_kant: figuur X kijkt naar kant A (0 voor, 1 rechts, 2 links); alleen een figuur die ook van opzij getekend is
// (npc_zij). Verandert hij, en staat hij in een slot, dan komt de nieuwe houding in de sprite-vakken (X blijft).
zet_kant: {
        ldy npc_vliegt,x                // een vlieger kiest zijn houding zelf (vlieg_stap), een oog ook (oog_stap)
        bne klaar
        ldy npc_zij,x
        cpy #2
        beq klaar
zet:    ldy npc_zij,x
        beq klaar
        cmp npc_kant,x
        beq klaar
        sta npc_kant,x
        ldy #0
!:      txa
        cmp slot_npc,y
        beq gevonden
        iny
        cpy #NPC_SLOTS
        bne !-
klaar:  rts
gevonden:
        jmp kostuum_naar_slot
}

// kostuum_naar_slot: het kostuum van figuur X naar de vakken van slot Y; kleuren en multicolor (X, Y blijven)
kostuum_naar_slot: {
        stx fig
        sty slot
        lda npc_data_lo,x
        sta zp_ptr
        lda npc_data_hi,x
        sta zp_ptr + 1
        lda npc_kant,x                  // een figuur van opzij: + 128 (kant 1), + 256 (2) of + 384 (3)
        beq !++
        cmp #2
        bcc !+                          // 1: + 128
        inc zp_ptr + 1                  // 2 en 3: + 256
        cmp #3
        bne !++
!:      lda zp_ptr
        eor #$80                        // + 128 (de houdingen staan op 128 bytes na elkaar; data begint op een
        sta zp_ptr                      //  veelvoud van 128: zie costume.py)
        bmi !+
        inc zp_ptr + 1
!:      ldy slot                        // vak 2 + 2 * slot: SPRITE_VAKKEN + 128 + slot * 128
        lda slot_vak_lo,y
        sta zp_ptr2
        lda slot_vak_hi,y
        sta zp_ptr2 + 1
        ldy #127                        // de figuren staan onder de I/O ($D000): per byte even alleen RAM, met
!:      php                             // de interrupts maar een paar cycli uit (128 bytes in één keer: ~27
        sei                             // rasterregels zonder IRQ, dan komen de naden te laat en flikkert alles;
        ldx #$34                        // een vlieger wisselt om de 8 beelden van houding)
        stx $01
        lda (zp_ptr),y
        ldx #CPU_NORMAAL
        stx $01
        plp
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
        lda npc_zij,x                   // een oog (Tik) zweeft op en neer (oog_stap)
        cmp #2
        bne !+
        lda y1
        clc
        adc oog_zweef
        sta y1
!:      lda y1
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
        jmp zet                         // (vorm 1 is klaar: niet doorlopen in de reus hieronder)
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

// oog_stap: een oog (kostuum met zij 2: Tik), elk beeld. Houding 0/1: vleugels omhoog/omlaag (om de 4 beelden), 2 half
// dicht, 3 dicht: eens in de 256 beelden (~5 s) knippert hij (half, dicht, half). oog_zweef: een paar pixels op en neer
// (npc_sprites telt het op bij de hoogte). X blijft.
oog_stap: {
        lda beelden
        and #$fc                        // (knipperen: beeld 0-11 van elke 256)
        bne !+
        lda #2                          // 0-3: half
        jmp zet
!:      lda beelden
        cmp #8
        bcs !+
        lda #3                          // 4-7: dicht
        jmp zet
!:      cmp #12
        bcs !+
        lda #2                          // 8-11: half
        jmp zet
!:      lsr                             // fladderen
        lsr
        and #1
zet:    pha
        lda beelden                     // zweven: om de 8 beelden een stap in de golf
        lsr
        lsr
        lsr
        and #7
        tay
        lda zweef_golf,y
        sta oog_zweef
        pla
        jmp zet_kant_vlieger
zweef_golf: .byte 0, 1, 2, 2, 1, 0, $ff, $ff
}
oog_zweef: .byte 0

// vlieg_stap: vlieger X (elk beeld): aangekomen? dan naar het andere punt (OP of VLIEGT); om de 8 beelden een
// vleugelslag; de houding naar de kant waar hij heen vliegt. X blijft.
vlieg_stap: {
        lda npc_lopen,x
        bne vleugels
        lda npc_dx_lo,x                 // het doel was het beginpunt? dan nu het andere punt
        cmp npc_x_lo,x
        bne naar_begin
        lda npc_dx_hi,x
        cmp npc_x_hi,x
        bne naar_begin
        ldy npc_vliegt,x                // (1 + de plek in de vlieg_heen-rijen)
        lda vlieg_heen_lo - 1,y
        sta npc_dx_lo,x
        lda vlieg_heen_hi - 1,y
        sta npc_dx_hi,x
        lda vlieg_heen_y - 1,y
        sta npc_dy,x
        jmp gaan
naar_begin:
        lda npc_x_lo,x
        sta npc_dx_lo,x
        lda npc_x_hi,x
        sta npc_dx_hi,x
        lda npc_y,x
        sta npc_dy,x
gaan:   lda #1
        sta npc_lopen,x
vleugels:
        lda beelden                     // om de 8 beelden: op (0) of neer (1)
        lsr
        lsr
        lsr
        and #1
        sta slag
        lda npc_px_lo,x                 // naar rechts (doel > plek) of naar links
        cmp npc_dx_lo,x
        lda npc_px_hi,x
        sbc npc_dx_hi,x
        bcs links
        lda slag                        // rechts: 0 (op) of 1 (neer)
        jmp zet_kant_vlieger
links:  lda slag                        // links: 3 (op) of 2 (neer)
        eor #3
        jmp zet_kant_vlieger
slag:   .byte 0
}

// npc_beweeg: elk beeld: figuren die lopen een stap dichter bij hun doel
npc_beweeg: {
        ldx #AANTAL_NPC - 1
        bpl lus
        jmp klaar
lus:    lda npc_vliegt,x                // een vlieger: heen en weer, met slaande vleugels
        beq !+
        lda st_npc,x
        beq !+
        jsr vlieg_stap
!:      lda npc_zij,x                   // een oog (Tik): fladderen, knipperen, zweven
        cmp #2
        bne !+
        lda st_npc,x
        beq !+
        jsr oog_stap
!:      lda npc_volgt,x                 // een volger: elk beeld een doel vlak achter Eldric
        beq geen_volger
        lda st_npc,x
        bne !+
        jmp volgende
!:      jsr volg_doel
        lda #1
        sta npc_lopen,x
geen_volger:
        lda npc_lopen,x
        bne !+
        jmp volgende
!:      lda npc_px_lo,x                 // x naar het doel (16 bits, 1 per beeld)
        cmp npc_dx_lo,x
        bne !+
        lda npc_px_hi,x
        cmp npc_dx_hi,x
        bne !+
        lda #0                          // niet opzij: naar voren kijken
        jsr zet_kant
        jmp y
!:      lda npc_px_lo,x
        cmp npc_dx_lo,x
        lda npc_px_hi,x
        sbc npc_dx_hi,x
        bcs links
        lda #1                          // naar rechts
        jsr zet_kant
        inc npc_px_lo,x
        bne y
        inc npc_px_hi,x
        jmp y
links:  lda #2                          // naar links
        jsr zet_kant
        lda npc_px_lo,x
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
        bmi klaar
        jmp lus
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
.segment Laag                           // $0400-$07FF (geheugen.asm): npc_begin zet ze bij het begin
npc_px_lo:    .fill MAX_NPC, 0          // waar de figuur nu staat (voeten, schermpixels)
npc_px_hi:    .fill MAX_NPC, 0
npc_py:       .fill MAX_NPC, 0
npc_dx_lo:    .fill MAX_NPC, 0          // LOOP: het doel
npc_dx_hi:    .fill MAX_NPC, 0
npc_dy:       .fill MAX_NPC, 0
npc_lopen:    .fill MAX_NPC, 0
.segment Data
