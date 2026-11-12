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
// Een onbekende opcode: band_status := $ff en band_fout := de opcode.
//
// In een AUTOTEST-build leest invoer.asm de joystick niet: band_invoer maakt de stand van de stick.

#if AUTOTEST

.const BAND_GROOTTE   = 1024
.const BAND_WACHT     = 0               // band_status: wacht tot vicetest de band heeft geladen
.const BAND_LOOPT     = 1
.const BAND_KLAAR     = 2
.const BAND_FOUT      = $ff

.segment Code
band_begin:
        lda #<band
        sta zp_band
        lda #>band
        sta zp_band + 1
        rts

// band_invoer: de stick voor dit beeld (zelfde bits als invoer_stick: 0 op, 1 neer, 2 links, 3 rechts, 4 vuur)
band_invoer: {
        lda #0
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

// Eén stap per beeld; aanroepen vanuit de hoofdlus.
band_stap: {
        lda band_status
        cmp #BAND_LOOPT
        bne klaar
        lda band_markering              // wacht vicetest nog op een markering?
        ora band_doel                   // of is de cursor nog onderweg?
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
        beq einde
        cmp #$01
        beq wacht
        cmp #$02
        beq markeer
        cmp #$03
        beq cursor
        cmp #$04
        beq vuur
        sta band_fout                   // onbekend
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

.segment Buffers
band:           .fill BAND_GROOTTE, 0

#endif
