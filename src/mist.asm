// mist.asm — de Zee van Vergetelheid (scenario hoofdstuk 3): in een kamer met MIST vergeet Eldric elke halve minuut de
// naam van een voorwerp in zijn inventaris. Daar staat dan "???", ook op de zinregel ("Gebruik ??? met zee").
// Bekijk het voorwerp en de naam komt terug (het script van Bekijk zegt dan wat het is). Welke namen vergeten zijn, staat
// in de spelstatus (st_vergeten: een bit per voorwerp), dus ook terugdraaien en opslaan nemen het mee.

.const MIST_TIJD = 1500                 // beelden: 30 seconden (PAL)

.segment Code
// naam_ptr: zp_ptr = de naam van voorwerp X, of "???" als Eldric hem vergeten is (X en Y blijven: de zinregel houdt
// zijn lengte in Y)
naam_ptr: {
        sty bewaar_y
        cpx #AANTAL_DYN                 // vast decor zit nooit in de inventaris: dat vergeet hij niet
        bcs weet
        jsr vergeten_bit
        and st_vergeten,y
        bne vergeten
weet:   lda vw_naam_lo,x
        sta zp_ptr
        lda vw_naam_hi,x
        sta zp_ptr + 1
        ldy bewaar_y
        rts
vergeten:
        lda #<tekst_vergeten
        sta zp_ptr
        lda #>tekst_vergeten
        sta zp_ptr + 1
        ldy bewaar_y
        rts
bewaar_y: .byte 0
}

// vergeten_bit: Y = byte in st_vergeten, A = het bit van voorwerp X (X blijft)
vergeten_bit:
        txa
        lsr
        lsr
        lsr
        tay
        txa
        and #7
        sty vb_y
        tay
        lda bits8,y                     // opslaan.asm
        ldy vb_y
        rts
vb_y:   .byte 0

// vlag_bit: Y = byte in st_vlaggen, A = het bit van vlag X
vlag_bit:
        txa
        lsr
        lsr
        lsr
        tay
        txa
        and #7
        tax
        lda bits8,x
        rts

// vergeten_weg: Eldric weet de naam van voorwerp X weer (bij Bekijk)
vergeten_weg: {
        cpx #AANTAL_DYN                 // (vast decor heeft geen bit in st_vergeten)
        bcs klaar
        jsr vergeten_bit
        and st_vergeten,y
        beq klaar
        eor st_vergeten,y               // het bit stond aan: uit
        sta st_vergeten,y
        lda #1
        sta inventaris_anders
klaar:  rts
}

// mist_beeld: elk beeld. In een kamer met MIST telt de klok af; bij 0 vergeet hij een naam.
mist_beeld: {
        ldx st_kamer
        lda kamer_mist,x
        beq geen
        cmp #$ff                        // $ff: altijd mist
        beq !+
        sec                             // anders: mist tot vlag A - 1 staat (MIST TOT vlag)
        sbc #1
        tax
        jsr vlag_bit
        and st_vlaggen,y
        beq !+
        jmp opgetrokken                 // de mist is weg: alles wat hij vergat, weet hij weer
geen:   lda #<MIST_TIJD                 // geen mist: de klok staat klaar voor de volgende keer
        sta klok
        lda #>MIST_TIJD
        sta klok + 1
        rts
!:      lda vm_scene                    // niet midden in een tussenscène
        bne klaar
        lda klok
        bne !+
        dec klok + 1
!:      dec klok
        lda klok
        ora klok + 1
        bne klaar
        lda #<MIST_TIJD
        sta klok
        lda #>MIST_TIJD
        sta klok + 1
        // het volgende voorwerp in de inventaris dat hij nog weet
        lda inv_aantal
        beq klaar
        sta teller
zoek:   inc volgende
        lda volgende
        cmp inv_aantal
        bcc !+
        lda #0
        sta volgende
!:      ldy volgende
        ldx inv_items,y
        jsr vergeten_bit
        sta bit
        and st_vergeten,y
        beq vergeet
        dec teller
        bne zoek
        rts                             // alles al vergeten
vergeet:
        lda bit
        ora st_vergeten,y
        sta st_vergeten,y
        inc mist_teller
        lda #1
        sta inventaris_anders
klaar:  rts
opgetrokken:
        ldx #MAX_VOORWERPEN / 8 - 1
        lda #0
!:      ora st_vergeten,x
        dex
        bpl !-
        tax
        beq geen                        // er was niets vergeten
        ldx #MAX_VOORWERPEN / 8 - 1
        lda #0
!:      sta st_vergeten,x
        dex
        bpl !-
        lda #1
        sta inventaris_anders
        jmp geen
klok:   .word MIST_TIJD
volgende: .byte $ff
teller: .byte 0
bit:    .byte 0
}

.segment Data
mist_teller: .byte 0                    // hoe vaak er een naam vergeten is (voor de tests)
.encoding "screencode_mixed"
tekst_vergeten: .text "???"
        .byte 0
