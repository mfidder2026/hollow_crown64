// menu.asm — de menubalk bovenaan (rij 0-1): Bestand (Opslaan, Laden, Exit), Score en Bosskey.
//
// Rij 0-1 is de plek van de berichten (wat iemand zegt). Zolang er niemand praat, er geen script, gesprek of toneel
// loopt, verschijnt de menubalk zodra de cursor in rij 0-1 komt; gaat de cursor weer naar beneden, dan verdwijnt hij.
//   rij 0:  Bestand   Score   Bosskey            (het woord onder de cursor licht op)
//   rij 1:  Opslaan   Laden   Exit               (na een klik op Bestand)
//           Lichtpunten: 25 van 250              (na een klik op Score)
// Een klik in de menubalk is voor het menu: klik (zin.asm) krijgt hem niet meer (invoer_vuur := 0).

.const MENU_KOL1 = 1                    // de woorden: kolom 1, 11, 21 (cursor-x / 8)
.const MENU_KOL2 = 11
.const MENU_KOL3 = 21
.const KLEUR_MENU      = 15             // lichtgrijs
.const KLEUR_MENU_AAN  = 7              // geel: onder de cursor
.const MENU_GEEN   = 0
.const MENU_BALK   = 1                  // alleen rij 0
.const MENU_BESTAND = 2                 // rij 1: Opslaan Laden Exit
.const MENU_SCORE  = 3                  // rij 1: de score

.segment Code
// menu_beeld: elk beeld, vóór klik
menu_beeld: {
        lda toneel_aan                  // wanneer mag het menu er zijn?
        ora vm_pc + 1
        ora gs_actief
        ora bericht_actief
        bne weg
        lda cursor_y
        cmp #16                         // rij 0-1
        bcs weg
        lda menu_stand
        bne !+
        lda #MENU_BALK
        sta menu_stand
!:      jsr menu_tekenen
        lda invoer_vuur                 // een klik in de menubalk
        beq klaar
        lda #0
        sta invoer_vuur                 // (klik in zin.asm krijgt hem niet)
        jmp menu_klik
weg:    lda menu_stand
        beq klaar
        lda #MENU_GEEN
        sta menu_stand
        lda bericht_actief              // een bericht heeft rij 0-1 al overschreven
        bne klaar
        ldy #0
        lda #0
        jsr rij_wissen
        ldy #1
        lda #0
        jmp rij_wissen
klaar:  rts
}

// menu_woord: A = het woord onder de cursor in deze rij (0-2), of $ff
menu_woord: {
        lda cursor_x + 1
        bne niets
        lda cursor_x
        lsr
        lsr
        lsr                             // kolom
        cmp #MENU_KOL1 - 1
        bcc niets
        cmp #MENU_KOL2 - 1
        bcc een
        cmp #MENU_KOL3 - 1
        bcc twee
        cmp #MENU_KOL3 + 9
        bcc drie
niets:  lda #$ff
        rts
een:    lda #0
        rts
twee:   lda #1
        rts
drie:   lda #2
        rts
}

// menu_tekenen: rij 0 (en rij 1 bij Bestand of Score), met het woord onder de cursor in geel
menu_tekenen: {
        lda #$ff                        // welk woord licht op: alleen in de rij waar de cursor is
        sta aan0
        sta aan1
        jsr menu_woord
        ldx cursor_y
        cpx #8
        bcs !+
        sta aan0
        jmp teken
!:      sta aan1
teken:  ldy #0
        lda #0
        jsr rij_wissen
        ldx #0
w0:     stx nr
        lda menu_rij0_lo,x
        sta zp_ptr
        lda menu_rij0_hi,x
        sta zp_ptr + 1
        lda menu_kolom,x
        tax
        lda #KLEUR_MENU
        ldy nr
        cpy aan0
        bne !+
        lda #KLEUR_MENU_AAN
!:      ldy #0
        jsr tekst_schrijf
        ldx nr
        inx
        cpx #3
        bne w0
        ldy #1                          // rij 1
        lda #0
        jsr rij_wissen
        lda menu_stand
        cmp #MENU_BESTAND
        beq bestand
        cmp #MENU_SCORE
        bne klaar
        jmp score_tekenen
bestand:
        ldx #0
w1:     stx nr
        lda menu_rij1_lo,x
        sta zp_ptr
        lda menu_rij1_hi,x
        sta zp_ptr + 1
        lda menu_kolom,x
        tax
        lda #KLEUR_MENU
        ldy nr
        cpy aan1
        bne !+
        lda #KLEUR_MENU_AAN
!:      ldy #1
        jsr tekst_schrijf
        ldx nr
        inx
        cpx #3
        bne w1
klaar:  rts
nr:     .byte 0
aan0:   .byte 0
aan1:   .byte 0
}

// score_tekenen: "Lichtpunten: 25 van 250" in rij 1
score_tekenen: {
        lda #<tekst_lichtpunten
        sta zp_ptr
        lda #>tekst_lichtpunten
        sta zp_ptr + 1
        ldx #MENU_KOL1
        ldy #1
        lda #KLEUR_MENU_AAN
        jsr tekst_schrijf               // Y = aantal tekens
        tya
        clc
        adc #MENU_KOL1 + 1
        tax                             // kolom van het getal (na een spatie)
        lda st_score                    // drie cijfers, zonder voorloopnullen
        ldy #0
        sty voorloop
honderd:
        cmp #100
        bcc !+
        sbc #100
        iny
        jmp honderd
!:      pha
        tya
        jsr cijfer
        pla
        ldy #0
tien:   cmp #10
        bcc !+
        sbc #10
        iny
        jmp tien
!:      pha
        tya
        jsr cijfer
        pla
        inc voorloop                    // het laatste cijfer altijd
        jsr cijfer
        inx
        lda #<tekst_van_max
        sta zp_ptr
        lda #>tekst_van_max
        sta zp_ptr + 1
        ldy #1
        lda #KLEUR_MENU
        jmp tekst_schrijf
// cijfer: A (0-9) op rij 1, kolom X (X++); voorloopnullen niet
cijfer: bne !+
        ldy voorloop
        bne !+
        rts
!:      inc voorloop
        clc
        adc #'0'
        sta SCHERM + 40,x
        lda #KLEUR_MENU_AAN
        sta KLEUR_RAM + 40,x
        inx
        rts
voorloop: .byte 0
}

// menu_klik: de cursor staat in rij 0 of 1
menu_klik: {
        jsr menu_woord
        cmp #$ff
        beq klaar
        sta woord
        lda cursor_y
        cmp #8
        bcs rij1
        lda woord                       // rij 0: Bestand / Score / Bosskey
        bne !+
        lda #MENU_BESTAND
        sta menu_stand
        rts
!:      cmp #1
        bne !+
        lda #MENU_SCORE
        sta menu_stand
        rts
!:      jsr menu_dicht
        jmp baas_aan                    // baas.asm
rij1:   lda menu_stand
        cmp #MENU_BESTAND
        bne klaar
        jsr menu_dicht
        lda woord
        bne !+
        jmp opslaan                     // opslaan.asm
!:      cmp #1
        bne !+
        jmp laden_spel
!:      jmp naar_basic                  // basic.asm
klaar:  rts
woord:  .byte 0
}

// menu_dicht: de balk weg (vóór opslaan, laden, de baas-toets)
menu_dicht:
        lda #MENU_GEEN
        sta menu_stand
        ldy #0
        lda #0
        jsr rij_wissen
        ldy #1
        lda #0
        jmp rij_wissen

.segment Data
menu_stand:  .byte 0                    // MENU_GEEN, MENU_BALK, MENU_BESTAND, MENU_SCORE (voor de tests)
menu_kolom:  .byte MENU_KOL1, MENU_KOL2, MENU_KOL3
menu_rij0_lo: .byte <tekst_bestand, <tekst_score, <tekst_bosskey
menu_rij0_hi: .byte >tekst_bestand, >tekst_score, >tekst_bosskey
menu_rij1_lo: .byte <tekst_opslaan_menu, <tekst_laden_menu, <tekst_exit
menu_rij1_hi: .byte >tekst_opslaan_menu, >tekst_laden_menu, >tekst_exit
