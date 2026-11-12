// geluid.asm — de SID (§6.7, §9). Geluidseffecten op stem 3; stem 1 en 2 blijven vrij voor muziek.
//
// Een effect: golfvorm, attack/decay, sustain/release, beginfrequentie, frequentiestap per beeld (met teken),
// pulsbreedte, duur (beelden). geluid_beeld (in de IRQ op de onderrand) schuift de frequentie op en zet aan het
// eind de gate uit. Effectnummers: gelijk houden met GELUIDEN in tools/scriptc.py.

.const GL_DEUR  = 0
.const GL_MUNT  = 1
.const GL_VUUR  = 2
.const GL_WOLF  = 3
.const GL_KLAAR = 4
.const GL_KLIK  = 5
.const GL_AANTAL = 6
.const SID_VOLUME = $0f

.segment Code
// geluid_stil: alle drie de stemmen uit en het volume op 0 (vóór het laden: geen hangende toon)
geluid_stil:
        ldx #$18
        lda #0
!:      sta $d400,x
        dex
        bpl !-
        sta gl_teller
        rts

// geluid_aan: volume aan (na het laden)
geluid_aan:
        lda #SID_VOLUME
        sta $d418
        rts

// geluid_speel: effect A op stem 3
geluid_speel:
        sta gl_laatste
        tax
        lda #0
        sta $d412                       // gate uit: het effect begint opnieuw
        lda gl_ad,x
        sta $d413
        lda gl_sr,x
        sta $d414
        lda gl_pw,x
        sta $d411
        lda #0
        sta $d410
        lda gl_f_lo,x
        sta gl_freq
        sta $d40e
        lda gl_f_hi,x
        sta gl_freq + 1
        sta $d40f
        lda gl_d_lo,x
        sta gl_stap
        lda gl_d_hi,x
        sta gl_stap + 1
        lda gl_duur,x
        sta gl_teller
        lda gl_golf,x
        sta gl_golf_nu
        ora #1                          // gate aan
        sta $d412
        lda #SID_VOLUME
        sta $d418
        rts

// geluid_beeld: elke 1/50 s (IRQ op de onderrand)
geluid_beeld:
        lda gl_teller
        beq !+
        lda gl_freq
        clc
        adc gl_stap
        sta gl_freq
        sta $d40e
        lda gl_freq + 1
        adc gl_stap + 1
        sta gl_freq + 1
        sta $d40f
        dec gl_teller
        bne !+
        lda gl_golf_nu                  // klaar: gate uit (de release klinkt nog even na)
        sta $d412
!:      rts

.segment Data
//              deur    munt    vuur    wolf    klaar   klik
gl_golf: .byte $81,    $41,    $81,    $21,    $11,    $41
gl_ad:   .byte $08,    $09,    $1a,    $28,    $0a,    $00
gl_sr:   .byte $00,    $00,    $00,    $a0,    $a8,    $00
gl_pw:   .byte $00,    $08,    $00,    $00,    $00,    $08
gl_f_lo: .byte <$0800, <$2800, <$1200, <$0600, <$1800, <$2000
gl_f_hi: .byte >$0800, >$2800, >$1200, >$0600, >$1800, >$2000
gl_d_lo: .byte <-$10,  <$0200, <-$40,  <-$08,  <$0060, 0
gl_d_hi: .byte >-$10,  >$0200, >-$40,  >-$08,  >$0060, 0
gl_duur: .byte 12,     10,     30,     40,     50,     2
gl_teller:  .byte 0
gl_freq:    .word 0
gl_stap:    .word 0
gl_golf_nu: .byte 0
gl_laatste: .byte $ff                   // het laatste effect (voor de tests)
