// inventaris.asm — wat Eldric bij zich heeft (§4): rij 22-23, 2 x 2 namen, pijlen ↑ ↓ in het midden.
//
//   kolom 0-17 en 22-39: namen; kolom 19: ↑ (rij 22) en ↓ (rij 23). Een pijl licht op als er iets te schuiven is.
//   De pijlen schuiven per 2 voorwerpen (een rij). Volgorde: zoals de voorwerpen in de scripts staan.
// Een voorwerp is in de inventaris als st_eigenaar = EIGENAAR_ELDRIC. GEEF/NEEM/PLAATS zetten
// inventaris_anders; dan wordt de lijst opnieuw gemaakt en getekend.

.const INV_KOLOM_R  = 22
.const INV_PIJL_X1  = 18 * 8             // cursor-x van de pijlen: kolom 18-21
.const INV_PIJL_X2  = 22 * 8
.const INV_GEEN     = 0
.const INV_OP       = 1
.const INV_NEER     = 2

.segment Code
// inv_bijwerken: elk beeld; maakt de lijst opnieuw en tekent als er iets veranderd is
inv_bijwerken: {
        lda inventaris_anders
        bne !+
        rts
!:      lda #0
        sta inventaris_anders
        ldx #0                          // de lijst: alle voorwerpen bij Eldric
        ldy #0
lus:    cpx #AANTAL_VW
        beq klaar
        jsr eigenaar_van                // status.asm
        cmp #EIGENAAR_ELDRIC
        bne !+
        txa
        sta inv_items,y
        iny
!:      inx
        bne lus
klaar:  sty inv_aantal
        // inv_begin binnen de lijst houden (even, en niet voorbij het eind)
!:      lda inv_begin
        beq inv_tekenen
        cmp inv_aantal
        bcc inv_tekenen
        sec
        sbc #2
        sta inv_begin
        jmp !-
}

// inv_tekenen: rij 22-23 opnieuw
inv_tekenen: {
        ldy #RIJ_INVENTARIS
        lda #KLEUR_INVENTARIS
        jsr rij_wissen
        ldy #RIJ_INVENTARIS + 1
        lda #KLEUR_INVENTARIS
        jsr rij_wissen
        lda #0
        sta vak
lus:    lda vak
        clc
        adc inv_begin
        cmp inv_aantal
        bcs pijlen
        tax
        lda inv_items,x
        tax
        jsr naam_ptr                    // mist.asm: de naam, of "???"
        lda vak
        lsr
        clc
        adc #RIJ_INVENTARIS
        tay
        ldx #0
        lda vak
        and #1
        beq !+
        ldx #INV_KOLOM_R
!:      lda #KLEUR_INVENTARIS
        jsr tekst_schrijf
        inc vak
        lda vak
        cmp #4
        bne lus
pijlen: lda #TEKEN_PIJL_OP
        sta SCHERM + RIJ_INVENTARIS * 40 + KOLOM_PIJL
        lda #TEKEN_PIJL_NEER
        sta SCHERM + (RIJ_INVENTARIS + 1) * 40 + KOLOM_PIJL
        ldx #KLEUR_PIJL_UIT             // ↑: alleen als er iets boven is
        lda inv_begin
        beq !+
        ldx #KLEUR_PIJL_AAN
!:      stx KLEUR_RAM + RIJ_INVENTARIS * 40 + KOLOM_PIJL
        ldx #KLEUR_PIJL_AAN             // ↓: alleen als er meer is dan er staat
        lda inv_begin
        clc
        adc #4
        cmp inv_aantal
        bcc !+
        ldx #KLEUR_PIJL_UIT
!:      stx KLEUR_RAM + (RIJ_INVENTARIS + 1) * 40 + KOLOM_PIJL
        rts
vak:    .byte 0
}

// inv_onder: de cursor in de inventaris? A = voorwerp (of GEEN_VOORWERP); inv_pijl = INV_OP / INV_NEER / INV_GEEN
inv_onder: {
        lda #INV_GEEN
        sta inv_pijl
        lda cursor_y
        cmp #RIJ_INVENTARIS * 8
        bcc geen
        cmp #(RIJ_INVENTARIS + 2) * 8
        bcs geen
        sec
        sbc #RIJ_INVENTARIS * 8
        lsr
        lsr
        lsr
        asl                             // rij * 2
        sta vak
        lda cursor_x + 1                // kolom: links (< 144), pijlen (144-175), rechts (>= 176)
        bne rechts
        lda cursor_x
        cmp #INV_PIJL_X1
        bcc links
        cmp #INV_PIJL_X2
        bcs rechts
        lda vak                         // een pijl
        lsr
        clc
        adc #INV_OP
        sta inv_pijl
geen:   lda #GEEN_VOORWERP
        rts
rechts: inc vak
links:  lda vak
        clc
        adc inv_begin
        cmp inv_aantal
        bcs geen
        tax
        lda inv_items,x
        rts
vak:    .byte 0
}

// inv_schuif: een pijl aangeklikt
inv_schuif: {
        lda inv_pijl
        cmp #INV_OP
        bne neer
        lda inv_begin
        beq klaar
        sec
        sbc #2
        sta inv_begin
        jmp inv_tekenen
neer:   lda inv_begin
        clc
        adc #4
        cmp inv_aantal
        bcs klaar
        lda inv_begin
        clc
        adc #2
        sta inv_begin
        jmp inv_tekenen
klaar:  rts
}

.segment Data
inv_items:  .fill MAX_VOORWERPEN, 0
inv_aantal: .byte 0
inv_begin:  .byte 0                     // het eerste voorwerp dat je ziet (even)
inv_pijl:   .byte 0
