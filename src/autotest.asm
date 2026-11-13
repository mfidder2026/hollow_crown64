// autotest.asm — de invoerband (§7, "Testen zonder handen"). Alleen in een build met -define AUTOTEST.
//
// tools/vicetest.py schrijft de band in `band`, zet `band_status` op 1 en laat de C64 lopen.
// Elk beeld voert band_stap hoogstens één stap uit. Opcodes (moet gelijk blijven aan vicetest.py):
//   $00             EINDE      band_status := 2
//   $01 lo hi       WACHT n    n beelden niets doen
//   $02 k           MARKEER k  band_markering := k; wacht tot vicetest hem weer op 0 zet
//                               (vicetest maakt dan een screenshot of leest het geheugen)
//   $03 xl xh y     CURSOR     beweeg de cursor naar x,y, met de gewone joystickcode (dus met versnellen);
//                               de band wacht tot hij er is
//   $04             VUUR       één beeld de vuurknop
//   $05 j r0 r1 r6 r7 p1 n  RUW  n beelden deze ruwe standen (joystick 2, toetsenbordrijen 0/1/6/7, poort 1);
//                               zo gaan joystick, toetsen en muisknoppen door de gewone omzetcode
//   $06 px py       MUIS       de potmeters van de muis worden px/py (zoals een 1351 ze zou geven)
//   $07             WACHT_STIL wacht tot Eldric stilstaat
//   $08 lo hi       START      start het script op dat adres (vicetest zoekt scr_<naam> op)
//   $09             WACHT_VM   wacht tot er geen script meer loopt
//   $0A             INTRO      (alleen als eerste opdracht) het intro draait; zonder: meteen het spel
// Elk beeld telt band_controle de beelden waarin Eldric buiten alle loopvakken staat (band_buiten).
// Een onbekende opcode: band_status := $ff en band_fout := de opcode.
//
// In een AUTOTEST-build leest invoer.asm de joystick niet: band_invoer maakt de stand van de stick.

#if AUTOTEST

.const BAND_GROOTTE   = 4096
.const BAND_WACHT     = 0               // band_status: wacht tot vicetest de band heeft geladen
.const BAND_LOOPT     = 1
.const BAND_KLAAR     = 2
.const BAND_FOUT      = $ff
.const BAND_OP_INTRO  = $0a             // INTRO: alleen als eerste opdracht; dan draait het intro (intro.asm)

.segment Code
band_begin:
        lda #<band
        sta zp_band
        lda #>band
        sta zp_band + 1
        rts

// band_invoer: de stick voor dit beeld (zelfde bits als invoer_stick: 0 op, 1 neer, 2 links, 3 rechts, 4 vuur)
band_invoer: {
        lda band_ruw_teller             // ruwe standen: nog n beelden, of weer leeg
        beq leeg
        dec band_ruw_teller
        jmp stick
leeg:   lda #0
        sta joy_stand
        sta toets_rij0
        sta toets_rij1
        sta toets_rij6
        sta toets_rij7
        sta poort1_stand
stick:  lda #0
        sta invoer_stick
        lda band_doel
        beq vuur
        // x: 16 bits vergelijken
        lda cursor_x + 1
        cmp band_doel_x + 1
        bne !+
        lda cursor_x
        cmp band_doel_x
!:      beq y
        bcc rechts
        lda #%0100                      // links
        bne zet
rechts: lda #%1000
zet:    sta invoer_stick
y:      lda cursor_y
        cmp band_doel_y
        beq vuur
        bcc neer
        lda #%0001
        bne zet2
neer:   lda #%0010
zet2:   ora invoer_stick
        sta invoer_stick
vuur:   lda band_vuur
        beq klaar
        lda invoer_stick
        ora #%10000
        sta invoer_stick
        lda #0
        sta band_vuur
klaar:  rts
}

// band_na_beweging: niet voorbij het doel schieten; is de cursor er, dan is de stap klaar.
band_na_beweging: {
        lda cursor_snelheid             // voor de test: de hoogste snelheid onthouden
        cmp band_hoogste_snelheid
        bcc !+
        sta band_hoogste_snelheid
!:      lda band_doel
        beq klaar
        lda invoer_stick
        and #%1000                      // naar rechts: x hooguit doel_x
        beq !+
        jsr x_voorbij
        bcc !+
        jsr x_is_doel
!:      lda invoer_stick
        and #%0100                      // naar links: x minstens doel_x
        beq !+
        jsr x_voorbij
        bcs !+
        jsr x_is_doel
!:      lda invoer_stick
        and #%0010                      // neer: y hooguit doel_y
        beq !+
        lda cursor_y
        cmp band_doel_y
        bcc !+
        lda band_doel_y
        sta cursor_y
!:      lda invoer_stick
        and #%0001                      // op: y minstens doel_y
        beq !+
        lda cursor_y
        cmp band_doel_y
        bcs !+
        lda band_doel_y
        sta cursor_y
!:      lda cursor_x                    // aangekomen?
        cmp band_doel_x
        bne klaar
        lda cursor_x + 1
        cmp band_doel_x + 1
        bne klaar
        lda cursor_y
        cmp band_doel_y
        bne klaar
        lda #0
        sta band_doel
klaar:  rts

// C = 1 als cursor_x >= doel_x
x_voorbij:
        lda cursor_x
        cmp band_doel_x
        lda cursor_x + 1
        sbc band_doel_x + 1
        rts
x_is_doel:
        lda band_doel_x
        sta cursor_x
        lda band_doel_x + 1
        sta cursor_x + 1
        rts
}

// band_controle: elk beeld. Telt beelden buiten het loopgebied; houdt WACHT_STIL bij.
band_controle: {
        lda act_x
        sta p_x
        lda act_x + 1
        sta p_x + 1
        lda act_y
        sta p_y
        jsr vak_van_punt
        cmp #GEEN_VAK
        bne !+
        inc band_buiten
        bne !+
        inc band_buiten + 1
!:      lda act_lopen
        bne !+
        sta band_wacht_stil             // staat stil: niet meer wachten
!:      lda vm_pc + 1
        bne !+
        sta band_wacht_vm               // geen script meer
!:      rts
}

// Eén stap per beeld; aanroepen vanuit de hoofdlus.
band_stap: {
        lda band_status
        cmp #BAND_LOOPT
        bne klaar
        lda band_markering              // wacht vicetest nog op een markering?
        ora band_doel                   // of is de cursor nog onderweg?
        ora band_ruw_teller             // of lopen er nog ruwe standen?
        ora band_wacht_stil             // of wachten we tot Eldric stilstaat?
        ora band_wacht_vm               // of tot het script klaar is?
        bne klaar
        lda band_wacht
        ora band_wacht + 1
        beq lees
        lda band_wacht                  // band_wacht - 1
        bne !+
        dec band_wacht + 1
!:      dec band_wacht
klaar:  rts

lees:   ldy #0
        lda (zp_band),y
        bne !+
        jmp einde
!:      cmp #$01
        bne !+
        jmp wacht
!:      cmp #$02
        bne !+
        jmp markeer
!:      cmp #$03
        bne !+
        jmp cursor
!:      cmp #$04
        bne !+
        jmp vuur
!:      cmp #$05
        bne !+
        jmp ruw
!:      cmp #$06
        bne !+
        jmp muis
!:      cmp #$07
        bne !+
        lda #1
        sta band_wacht_stil
        jmp verder                      // A = 1
!:      cmp #$08
        bne !+
        iny
        lda (zp_band),y
        pha
        iny
        lda (zp_band),y
        tax
        pla
        jsr vm_start
        lda #3
        jmp verder
!:      cmp #$09
        bne !+
        lda #1
        sta band_wacht_vm
        jmp verder
!:      cmp #BAND_OP_INTRO              // (intro.asm leest hem al; verderop doet hij niets)
        bne !+
        lda #1
        jmp verder
!:      sta band_fout                   // onbekend
        lda #BAND_FOUT
        sta band_status
        rts

einde:  lda #BAND_KLAAR
        sta band_status
        rts

wacht:  iny
        lda (zp_band),y
        sta band_wacht
        iny
        lda (zp_band),y
        sta band_wacht + 1
        lda #3
        jmp verder

markeer:
        iny
        lda (zp_band),y
        sta band_markering
        lda #2
        jmp verder

cursor: iny
        lda (zp_band),y
        sta band_doel_x
        iny
        lda (zp_band),y
        sta band_doel_x + 1
        iny
        lda (zp_band),y
        sta band_doel_y
        lda #1
        sta band_doel
        lda #4
        jmp verder

ruw:    ldx #0
!:      iny
        lda (zp_band),y
        sta ruw_doel_waarden,x
        inx
        cpx #6
        bne !-
        lda ruw_doel_waarden
        sta joy_stand
        lda ruw_doel_waarden + 1
        sta toets_rij0
        lda ruw_doel_waarden + 2
        sta toets_rij1
        lda ruw_doel_waarden + 3
        sta toets_rij6
        lda ruw_doel_waarden + 4
        sta toets_rij7
        lda ruw_doel_waarden + 5
        sta poort1_stand
        iny
        lda (zp_band),y
        sta band_ruw_teller
        lda #8
        jmp verder

muis:   iny
        lda (zp_band),y
        sta pot_x
        iny
        lda (zp_band),y
        sta pot_y
        lda #3
        jmp verder

vuur:   lda #1
        sta band_vuur

verder: clc                             // zp_band += A (bij VUUR: A = 1)
        adc zp_band
        sta zp_band
        bcc !+
        inc zp_band + 1
!:      rts
}

.segment Data
band_status:    .byte BAND_WACHT
band_markering: .byte 0
band_fout:      .byte 0
band_wacht:     .word 0
band_doel:      .byte 0                 // 1: de cursor is onderweg naar band_doel_x/y
band_doel_x:    .word 0
band_doel_y:    .byte 0
band_vuur:      .byte 0
band_hoogste_snelheid: .byte 0         // hoogste cursorsnelheid tot nu toe
band_ruw_teller: .byte 0                // RUW: nog zoveel beelden
band_wacht_stil: .byte 0                // WACHT_STIL loopt
band_wacht_vm:   .byte 0                // WACHT_VM loopt
band_buiten:     .word 0                // beelden waarin Eldric buiten alle loopvakken stond
ruw_doel_waarden: .fill 6, 0

.segment Buffers
band:           .fill BAND_GROOTTE, 0

#endif
