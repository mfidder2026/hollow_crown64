// sidspeler.asm — de speler die muziek.py in muziek.asm zet (Kick Assembler 5, PAL)
// muziek_init: één keer.  muziek_play: 50 keer per seconde (raster-IRQ).  Gebruikt A, X, Y; geen zeropage.
// Een stem leest paren van twee bytes: duur (beelden), noot. Noot 0 = rust, 12-106 = MIDI-noot, $7f = doorklinken,
// $80+k = drum k (1 kick, 2 snare, 3 tom, 4 open hihat, 5 hihat). Duur 0 = einde: noot 0 opnieuw, 1 stoppen.
// Verwacht van muziek.py: MUZIEK_GOLFn, _ADn, _SRn, _PWn, _PWMn (n = 1-3), MUZIEK_VOLUME, muziek_stem1..3.
// muziek_slag: de drum die het laatst viel (1 kick, 2 snare, 3 tom, 4 open, 5 hihat). Lees hem na muziek_play en zet
// hem zelf op 0: zo laat je de rand of een sprite op de maat meeknipperen.

muziek_init:
        lda #0
        ldx #$18
!wis:   sta $d400,x
        dex
        bpl !wis-
        ldx #2
!stem:  lda muz_beginLo,x
        sta muz_ptrLo,x
        lda muz_beginHi,x
        sta muz_ptrHi,x
        lda #1
        sta muz_teller,x
        lda #0
        sta muz_drum,x
        sta muz_richting,x
        ldy muz_sid,x
        lda muz_ad,x
        sta $d405,y
        lda muz_sr,x
        sta $d406,y
        lda muz_pwLo,x
        sta muz_pwnuLo,x
        sta $d402,y
        lda muz_pwHi,x
        sta muz_pwnuHi,x
        sta $d403,y
        dex
        bpl !stem-
        lda #MUZIEK_VOLUME
        sta $d418
        rts

muziek_play:
        ldx #2
!stem:  ldy muz_sid,x               // Y = de registers van deze stem: 0, 7 of 14
        dec muz_teller,x
        bne !loopt+
        jsr muz_lees                // een nieuwe noot, rust of drum
        jmp !effect+
!loopt: lda muz_teller,x
        cmp #1
        bne !effect+
        lda muz_drum,x              // een drum zet zijn gate zelf uit
        bne !effect+
        lda #1
        jsr muz_byte                // het laatste beeld van een noot: gate uit, zodat de volgende opnieuw aanslaat,
        cmp #$7f                    // behalve als die doorklinkt
        beq !effect+
        lda muz_golf,x
        and #$fe
        sta $d404,y
!effect:
        jsr muz_effect
        dex
        bpl !stem-
        rts

// A = byte op muz_ptr + A van stem X; Y blijft
muz_byte:
        sty muz_ybewaar
        tay
        lda muz_ptrLo,x
        sta muz_adres+1
        lda muz_ptrHi,x
        sta muz_adres+2
muz_adres:
        lda $ffff,y
        ldy muz_ybewaar
        and #$ff                    // de vlaggen weer van A: ldy zette ze naar Y (0 bij stem 1)
        rts

muz_lees:
        lda #0
        jsr muz_byte                // duur
        bne !gewoon+
        lda #1
        jsr muz_byte
        bne !stop+
        lda muz_beginLo,x           // einde, noot 0: opnieuw vanaf het begin
        sta muz_ptrLo,x
        lda muz_beginHi,x
        sta muz_ptrHi,x
        jmp muz_lees
!stop:  lda #1                      // einde, noot 1: blijft hier staan, stil
        sta muz_teller,x
        lda muz_golf,x
        and #$fe
        sta $d404,y
        rts
!gewoon:
        sta muz_teller,x
        lda #1
        jsr muz_byte                // noot
        pha
        clc
        lda muz_ptrLo,x
        adc #2
        sta muz_ptrLo,x
        bcc !+
        inc muz_ptrHi,x
!:      pla
        beq muz_rust
        cmp #$7f
        beq muz_klaar
        bcs muz_drumbegin
        sec                         // een noot: frequentie uit de tabel, dan gate aan
        sbc #12
        stx muz_xbewaar
        tax
        lda muz_freqLo,x
        sta $d400,y
        lda muz_freqHi,x
        sta $d401,y
        ldx muz_xbewaar
        lda muz_golf,x
        ora #1
        sta $d404,y
        rts
muz_rust:
        lda muz_golf,x
        and #$fe
        sta $d404,y
muz_klaar:
        rts
muz_drumbegin:
        and #$7f
        sta muziek_slag             // voor het programma: welke drum er net viel
        stx muz_xbewaar
        tax
        lda muz_drumAD,x
        sta $d405,y
        lda muz_drumSR,x
        sta $d406,y
        lda muz_drumStart,x
        ldx muz_xbewaar
        sta muz_drum,x
        rts

// per beeld: de volgende stap van een drum, of de pulsbreedte die heen en weer loopt
muz_effect:
        lda muz_drum,x
        beq !pw+
        stx muz_xbewaar
        tax
        lda muz_drumData,x          // golfvorm; 0 = de drum is klaar
        beq !uit+
        sta muz_tmp
        lda muz_drumData+1,x
        ldx muz_xbewaar
        sta $d401,y
        lda #0
        sta $d400,y
        lda muz_tmp
        sta $d404,y
        inc muz_drum,x
        inc muz_drum,x
        rts
!uit:   ldx muz_xbewaar
        lda #0
        sta muz_drum,x
        rts
!pw:    lda muz_pwm,x
        beq !klaar+
        lda muz_richting,x
        bne !omlaag+
        clc
        lda muz_pwnuLo,x
        adc muz_pwm,x
        sta muz_pwnuLo,x
        lda muz_pwnuHi,x
        adc #0
        sta muz_pwnuHi,x
        cmp #$0e
        bcc !zet+
        inc muz_richting,x
        bne !zet+
!omlaag:
        sec
        lda muz_pwnuLo,x
        sbc muz_pwm,x
        sta muz_pwnuLo,x
        lda muz_pwnuHi,x
        sbc #0
        sta muz_pwnuHi,x
        cmp #$02
        bcs !zet+
        lda #0
        sta muz_richting,x
!zet:   lda muz_pwnuLo,x
        sta $d402,y
        lda muz_pwnuHi,x
        sta $d403,y
!klaar: rts

// frequenties voor MIDI-noot 12 (C0) tot 106 (A#7), PAL
muz_freqLo:   .fill 95, <round(440 * pow(2, (i - 57) / 12) * 16777216 / 985248)
muz_freqHi:   .fill 95, >round(440 * pow(2, (i - 57) / 12) * 16777216 / 985248)

muz_sid:      .byte 0, 7, 14
muz_beginLo:  .byte <muziek_stem1, <muziek_stem2, <muziek_stem3
muz_beginHi:  .byte >muziek_stem1, >muziek_stem2, >muziek_stem3
muz_golf:     .byte MUZIEK_GOLF1, MUZIEK_GOLF2, MUZIEK_GOLF3
muz_ad:       .byte MUZIEK_AD1, MUZIEK_AD2, MUZIEK_AD3
muz_sr:       .byte MUZIEK_SR1, MUZIEK_SR2, MUZIEK_SR3
muz_pwLo:     .byte <MUZIEK_PW1, <MUZIEK_PW2, <MUZIEK_PW3
muz_pwHi:     .byte >MUZIEK_PW1, >MUZIEK_PW2, >MUZIEK_PW3
muz_pwm:      .byte MUZIEK_PWM1, MUZIEK_PWM2, MUZIEK_PWM3

// drums: per beeld golfvorm + frequentie (hoog); de laatste stap heeft gate uit, dan 0
//                    -    kick  snare tom   open  hihat
muz_drumAD:   .byte 0,   $00,  $00,  $00,  $00,  $00
muz_drumSR:   .byte 0,   $f4,  $f5,  $f6,  $f7,  $f1
muz_drumStart:.byte 0,   muz_dKick - muz_drumData, muz_dSnare - muz_drumData, muz_dTom - muz_drumData
              .byte      muz_dOpen - muz_drumData, muz_dHat - muz_drumData
muz_drumData: .byte 0
muz_dKick:    .byte $81,$0c, $11,$0a, $11,$08, $11,$06, $11,$05, $11,$04, $10,$03, 0
muz_dSnare:   .byte $81,$20, $11,$0e, $81,$1c, $81,$18, $80,$14, 0
muz_dTom:     .byte $81,$10, $11,$0c, $11,$0b, $11,$0a, $11,$09, $10,$08, 0
muz_dOpen:    .byte $81,$f0, $81,$f0, $81,$e0, $80,$e0, 0
muz_dHat:     .byte $81,$f0, $80,$f0, 0

muz_ptrLo:    .byte 0, 0, 0
muz_ptrHi:    .byte 0, 0, 0
muz_teller:   .byte 0, 0, 0
muz_drum:     .byte 0, 0, 0
muz_pwnuLo:   .byte 0, 0, 0
muz_pwnuHi:   .byte 0, 0, 0
muz_richting: .byte 0, 0, 0
muziek_slag:  .byte 0
muz_xbewaar:  .byte 0
muz_ybewaar:  .byte 0
muz_tmp:      .byte 0
