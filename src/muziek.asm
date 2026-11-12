// muziek.asm — een eigen kleine SID-speler voor het thema (§9). De noten komen uit tools/thema.py.
//
// muziek_beeld draait 50 keer per seconde in de IRQ op de onderrand (irq.asm). Per stem: (noot, beelden)-paren;
// in het laatste beeld van een noot gaat de gate uit, zodat de volgende opnieuw aanslaat. Stem 3 speelt het
// akkoord als arpeggio (elke 2 beelden de volgende toon) en wijkt voor een geluidseffect (geluid.asm).
// Alles wat de speler naar de SID schrijft, staat ook in muz_* (de SID kun je niet teruglezen): de tests lezen die.
//
//   muziek_start  het thema van voren af aan (als de muziek mag: F1)
//   muziek_stop   stil; de gates uit (geen hangende toon)
//   muz_gevraagd  1: deze kamer (of het intro) wil muziek; F1 zet hem dan weer aan

#import "../build/gen/muziek.asm"

.segment Code
muziek_start: {
        lda #1
        sta muz_gevraagd
        lda muz_mag
        bne !+
        rts
!:      lda #0
        sta muz_aan                     // de IRQ even niet
        sta muz_beelden
        sta muz_beelden + 1
        ldx #2
lus:    lda stem_begin_lo,x
        sta muz_ptr_lo,x
        lda stem_begin_hi,x
        sta muz_ptr_hi,x
        lda #1                          // het eerste beeld haalt de eerste noot
        sta muz_teller,x
        lda #0
        sta muz_noot,x
        sta muz_ctrl,x
        dex
        bpl lus
        lda #$00                        // pulsbreedte stem 1 (melodie) begint smal
        sta muz_pw
        lda #$04
        sta muz_pw + 1
        lda #SID_VOLUME
        sta $d418
        lda #1
        sta muz_aan
        rts
}

muziek_stop: {
        lda #0
        sta muz_aan
        sta muz_gevraagd
        // en dan net als bij F1:
}
muziek_uit:
        lda #0
        sta muz_aan
        sta muz_ctrl
        sta muz_ctrl + 1
        sta $d404                       // gates en golfvormen uit
        sta $d40b
        sta muz_ctrl + 2
        lda gl_teller                   // stem 3 alleen als er geen effect klinkt
        bne !+
        lda #0
        sta $d412
!:      rts

// muziek_f1: muziek aan/uit (F1). Uit: meteen stil. Aan: alleen als de kamer (of het intro) muziek wil.
muziek_f1:
        lda muz_mag
        eor #1
        sta muz_mag
        beq muziek_uit
        lda muz_gevraagd
        beq !+
        jmp muziek_start
!:      rts

// muziek_beeld: elke 1/50 s (IRQ)
muziek_beeld: {
        lda muz_aan
        bne !+
        rts
!:
#if AUTOTEST
        lda band_markering              // vicetest kijkt: de muziek staat ook stil (een echte momentopname)
        beq !+
        rts
!:
#endif
        inc muz_beelden
        bne !+
        inc muz_beelden + 1
!:      ldx #0
stem:   dec muz_teller,x
        beq nieuw
        lda muz_teller,x                // laatste beeld van de noot: gate uit
        cmp #1
        bne verder
        lda muz_ctrl,x
        and #$fe
        sta muz_ctrl,x
        jsr ctrl_schrijven
        jmp verder
nieuw:  jsr volgende_noot
verder: inx
        cpx #3
        bne stem
        // stem 3: arpeggio (elke 2 beelden de volgende toon van het akkoord)
        lda muz_noot + 2
        beq pwm
        inc muz_arp
        lda muz_arp
        cmp #6
        bcc !+
        lda #0
        sta muz_arp
!:      ldx #2
        jsr arp_freq
        // stem 1: langzame pulsbreedte-modulatie (de melodie "ademt")
pwm:    lda muz_pw
        clc
        adc #$10
        sta muz_pw
        lda muz_pw + 1
        adc #0
        and #$0f
        cmp #$0c
        bcc !+
        lda #$04
!:      sta muz_pw + 1
        lda muz_pw
        sta $d402
        lda muz_pw + 1
        sta $d403
        rts

// de volgende (noot, beelden) van stem X
volgende_noot:
        lda muz_ptr_lo,x
        sta zp_muz
        lda muz_ptr_hi,x
        sta zp_muz + 1
        ldy #0
        lda (zp_muz),y
        cmp #$ff                        // einde: van voren af aan
        bne !+
        lda stem_begin_lo,x
        sta muz_ptr_lo,x
        sta zp_muz
        lda stem_begin_hi,x
        sta muz_ptr_hi,x
        sta zp_muz + 1
        lda (zp_muz),y
!:      sta muz_noot,x
        iny
        lda (zp_muz),y
        sta muz_teller,x
        lda muz_ptr_lo,x
        clc
        adc #2
        sta muz_ptr_lo,x
        bcc !+
        inc muz_ptr_hi,x
!:      lda muz_noot,x
        bne aan
        lda stem_golf,x                 // rust: gate uit
        sta muz_ctrl,x
        jmp ctrl_schrijven
aan:    cpx #2
        bne !+
        lda #0                          // nieuw akkoord: bij de eerste toon beginnen
        sta muz_arp
        jsr arp_freq
        jmp gate
!:      ldy muz_noot,x
        lda muz_freq_lo,y
        sta muz_flo,x
        lda muz_freq_hi,y
        sta muz_fhi,x
        jsr freq_schrijven
gate:   lda stem_golf,x
        ora #1
        sta muz_ctrl,x
        // klank: ADSR (en pulsbreedte van stem 2 en 3) bij elke noot opnieuw: een effect kan ze veranderd hebben
        cpx #2
        bne !+
        lda gl_teller
        bne klaar
!:      ldy sid_stem,x
        lda stem_ad,x
        sta $d405,y
        lda stem_sr,x
        sta $d406,y
        lda #$00
        sta $d402,y
        lda #$08
        sta $d403,y
        jmp ctrl_schrijven
klaar:  rts

// frequentie van stem 3 uit het akkoord: toon (muz_arp / 2) van akkoord muz_noot+2
arp_freq:
        lda muz_noot + 2                // akkoord n (1..): MIDI-noten op muz_akkoord + 3n
        sta hulp
        asl
        clc
        adc hulp
        ldy muz_arp
        clc
        adc arp_toon,y
        tay
        lda muz_akkoord,y
        tay
        lda muz_freq_lo,y
        sta muz_flo + 2
        lda muz_freq_hi,y
        sta muz_fhi + 2
// freq_schrijven: muz_flo/fhi,x naar de SID (stem 3 niet tijdens een effect)
freq_schrijven:
        cpx #2
        bne !+
        lda gl_teller
        bne !++
!:      ldy sid_stem,x
        lda muz_flo,x
        sta $d400,y
        lda muz_fhi,x
        sta $d401,y
!:      rts
// ctrl_schrijven: muz_ctrl,x naar de SID (stem 3 niet tijdens een effect)
ctrl_schrijven:
        cpx #2
        bne !+
        lda gl_teller
        bne !++
!:      ldy sid_stem,x
        lda muz_ctrl,x
        sta $d404,y
!:      rts
hulp:   .byte 0
}

.segment Data
//              melodie     bas          arpeggio
stem_begin_lo: .byte <muz_stem1, <muz_stem2, <muz_stem3
stem_begin_hi: .byte >muz_stem1, >muz_stem2, >muz_stem3
stem_golf:     .byte $40,        $20,        $40
stem_ad:       .byte $29,        $08,        $00
stem_sr:       .byte $a9,        $a6,        $70
sid_stem:      .byte 0,          7,          14
arp_toon:      .byte 0, 0, 1, 1, 2, 2

muz_aan:      .byte 0                   // 1: de speler loopt
muz_mag:      .byte 1                   // F1: 0 = muziek uit
muz_gevraagd: .byte 0
muz_beelden:  .word 0                   // beelden sinds muziek_start (voor de tests)
muz_ptr_lo:   .fill 3, 0
muz_ptr_hi:   .fill 3, 0
muz_teller:   .fill 3, 0
muz_noot:     .fill 3, 0                // MIDI-noot (stem 3: akkoord + 1); 0 = rust
muz_flo:      .fill 3, 0                // wat er in de SID staat (frequentie, besturing)
muz_fhi:      .fill 3, 0
muz_ctrl:     .fill 3, 0
muz_arp:      .byte 0
muz_pw:       .word 0
