// toneel.asm — een toneel (de verhaalanimatie na het titelscherm) en de opdracht KLEUR.
//
// Een kamer met TONEEL (scripts/*.hcs) laat alleen het plaatje en de tekst van de verteller zien: geen Eldric (tot
// TOON eldric), geen cursor, geen balk (rij 18-24 leeg). Gaat het script daarna met KAMER naar een gewone kamer, dan
// komen de balk, de inventaris, de cursor en Eldric terug.
//
// KLEUR kol rij breed hoog van naar (vakjes, zoals FLAKKER): in die vakjes wordt kleur `van` overal `naar`: in het
// scherm-RAM (hoog en laag nibble) en in het kleur-RAM. Zo wordt de lucht stap voor stap donkerder.

.segment Code
// toneel_kamer: na het laden van kamer X (kamer.asm)
toneel_kamer: {
        lda kamer_toneel,x
        beq gewoon
        lda #0
        sta act_zichtbaar
        lda #1
        sta toneel_aan
        ldy #RIJ_ZIN                    // rij 18-24 leeg en zwart
!:      tya
        pha
        lda #0
        jsr rij_wissen
        pla
        tay
        iny
        cpy #25
        bne !-
        rts
gewoon: lda #1
        sta act_zichtbaar
        lda toneel_aan
        beq !+
        lda #0
        sta toneel_aan
        jsr balk_tekenen                // de balk terug (balk.asm), de inventaris en de zinregel
        lda #1
        sta inventaris_anders
        lda #$fe                        // zinregel opnieuw (zoals bij kamer_wissel)
        sta zin_ww
!:      rts
}

// kleur_wissel: de opdracht KLEUR; zp_vm wijst naar de opcode (+1 kol, +2 rij, +3 breed, +4 hoog, +5 van, +6 naar)
kleur_wissel: {
        ldy #5
        lda (zp_vm),y
        sta van
        asl
        asl
        asl
        asl
        sta van_hoog
        iny
        lda (zp_vm),y
        sta naar
        asl
        asl
        asl
        asl
        sta naar_hoog
        ldy #2
        lda (zp_vm),y
        clc
        adc #RIJ_KAMER
        sta rij
        ldy #4
        lda (zp_vm),y
        sta rijen
rijlus: ldx rij
        lda rij_lo,x
        ldy #1
        clc
        adc (zp_vm),y                   // + kolom
        sta zp_ptr
        sta zp_ptr2
        lda rij_hi,x
        adc #0
        sta zp_ptr + 1
        clc
        adc #>KLEUR_OFFSET
        sta zp_ptr2 + 1
        ldy #3
        lda (zp_vm),y
        tay
        dey                             // Y = breed - 1 .. 0
vak:    lda (zp_ptr),y                  // scherm-RAM: hoog nibble
        and #$f0
        cmp van_hoog
        bne !+
        lda (zp_ptr),y
        and #$0f
        ora naar_hoog
        sta (zp_ptr),y
!:      lda (zp_ptr),y                  // laag nibble
        and #$0f
        cmp van
        bne !+
        lda (zp_ptr),y
        and #$f0
        ora naar
        sta (zp_ptr),y
!:      lda (zp_ptr2),y                 // kleur-RAM (alleen de onderste 4 bits tellen)
        and #$0f
        cmp van
        bne !+
        lda naar
        sta (zp_ptr2),y
!:      dey
        bpl vak
        inc rij
        dec rijen
        bne rijlus
        inc kleur_teller
        rts
van:       .byte 0
naar:      .byte 0
van_hoog:  .byte 0
naar_hoog: .byte 0
rij:       .byte 0
rijen:     .byte 0
}

.segment Data
toneel_aan:    .byte 0                  // 1: een TONEEL-kamer (geen balk, cursor, Eldric)
act_zichtbaar: .byte 1                  // 0: Eldric staat er niet (TONEEL, of VERBERG eldric)
kleur_teller:  .byte 0                  // hoe vaak KLEUR draaide (voor de tests)
