// autotest.asm — de invoerband (§7, "Testen zonder handen"). Alleen in een build met -define AUTOTEST.
//
// tools/vicetest.py schrijft de band in `band`, zet `band_status` op 1 en laat de C64 lopen.
// Elk beeld voert band_stap hoogstens één stap uit. Opcodes (moet gelijk blijven aan vicetest.py):
//   $00             EINDE      band_status := 2
//   $01 lo hi       WACHT n    n beelden niets doen
//   $02 k           MARKEER k  band_markering := k; wacht tot vicetest hem weer op 0 zet
//                               (vicetest maakt dan een screenshot of leest het geheugen)
//   $03 xl xh y     CURSOR     (hoofdstuk 1)
//   $04             VUUR       (hoofdstuk 1)
// Een onbekende opcode: band_status := $ff en band_fout := de opcode.

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

// Eén stap per beeld; aanroepen vanuit de hoofdlus.
band_stap:
        lda band_status
        cmp #BAND_LOOPT
        bne klaar
        lda band_markering              // wacht vicetest nog op een markering?
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
        sta band_fout                   // onbekend, of nog niet gebouwd
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

verder: clc                             // zp_band += A
        adc zp_band
        sta zp_band
        bcc !+
        inc zp_band + 1
!:      rts

.segment Data
band_status:    .byte BAND_WACHT
band_markering: .byte 0
band_fout:      .byte 0
band_wacht:     .word 0

.segment Buffers
band:           .fill BAND_GROOTTE, 0

#endif
