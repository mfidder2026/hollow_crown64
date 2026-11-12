// invoer.asm — joystick (poort 2), 1351-muis (poort 1) en toetsenbord (§4). Alle drie werken tegelijk,
// zodat je ook zonder joystick kunt spelen, op een echte C64 en in VICE.
//
// Toetsen (zoals de C64 ze kent; in VICE op de Mac doen de pijltjestoetsen precies dit):
//   CRSR ⇓          omlaag          SHIFT + CRSR ⇓   omhoog
//   CRSR ⇒          rechts          SHIFT + CRSR ⇒   links
//   SPATIE of CTRL  vuur (links op het toetsenbord; in VICE op de Mac: spatiebalk of linker Control)
//   RETURN          ook vuur
// Muis (1351 in poort 1): bewegen = de cursor; linkerknop = vuur; rechterknop: gelezen, nog geen taak.
// Een joystick in poort 1 werkt ook voor vuur.
//
// Twee stappen:
//   1. invoer_hardware (in de IRQ op de onderrand): de ruwe standen lezen — joystick, matrixrijen,
//      muisknoppen en de twee potmeters. Alleen daar, want de Kernal-scan zet $DC00 tussendoor op 0
//      (wie dan $DC00 leest, ziet "alle richtingen + vuur": gevonden met echte toetsen in VICE).
//   2. invoer_lees (in de hoofdlus): de ruwe standen omzetten naar invoer_stick en muisbeweging.
// In een AUTOTEST-build vult de band de ruwe standen (autotest.asm), dus stap 2 wordt ook getest.

// Plaatsen in de toetsenbordmatrix: rij = bit in $DC00 (laag = gekozen), kolom = bit in $DC01
.const TOETS_RIJ0_RETURN   = %00000010  // rij 0, kolom 1
.const TOETS_RIJ0_CRSR_LR  = %00000100  // rij 0, kolom 2 (CRSR ⇒)
.const TOETS_RIJ0_CRSR_OB  = %10000000  // rij 0, kolom 7 (CRSR ⇓)
.const TOETS_RIJ1_LSHIFT   = %10000000  // rij 1, kolom 7 (ook SHIFT LOCK)
.const TOETS_RIJ6_RSHIFT   = %00010000  // rij 6, kolom 4
.const TOETS_RIJ7_CTRL     = %00000100  // rij 7, kolom 2
.const TOETS_RIJ7_SPATIE   = %00010000  // rij 7, kolom 4
.const MUIS_LINKS          = %00010000  // $DC01 bit 4 (zelfde als vuur van joystick 1)
.const MUIS_RECHTS         = %00000001  // $DC01 bit 0
// POORT1_POTS staat in geheugen.asm (irq.asm gebruikt hem ook)

.segment Code
// invoer_hardware: in de IRQ op de onderrand. De potmeters zijn dan al >3500 cycli op poort 1
// (irq_balk zet POORT1_POTS op lijn 195; de SID heeft 512 cycli nodig per meting).
invoer_hardware:
        lda $d419                       // muis X (1351: bits 1-6)
        sta pot_x
        lda $d41a                       // muis Y
        sta pot_y
        lda #$ff                        // geen rij gekozen
        sta $dc00
        lda $dc01                       // alleen poort 1: muisknoppen of joystick 1
        eor #$ff
        sta poort1_stand
        lda $dc00                       // joystick 2, actief laag
        eor #%00011111
        and #%00011111
        sta joy_stand
        lda #%11111110                  // rij 0
        sta $dc00
        lda $dc01
        eor #$ff
        sta toets_rij0
        lda #%11111101                  // rij 1
        sta $dc00
        lda $dc01
        eor #$ff
        sta toets_rij1
        lda #%10111111                  // rij 6
        sta $dc00
        lda $dc01
        eor #$ff
        sta toets_rij6
        lda #%01111111                  // rij 7
        sta $dc00
        lda $dc01
        eor #$ff
        sta toets_rij7
        lda #POORT1_POTS
        sta $dc00
        // Kolommen die poort 1 (muis/joystick 1) al laag trekt zijn geen toetsen
        lda poort1_stand
        eor #$ff
        tax
        and toets_rij0
        sta toets_rij0
        txa
        and toets_rij1
        sta toets_rij1
        txa
        and toets_rij6
        sta toets_rij6
        txa
        and toets_rij7
        sta toets_rij7
        rts

// invoer_lees: zet invoer_stick (1 = ingedrukt; bit 0 op, 1 neer, 2 links, 3 rechts, 4 vuur),
// muis_dx/muis_dy (beweging in pixels, met teken) en invoer_vuur (1 alleen in het beeld waarin vuur
// wordt ingedrukt).
invoer_lees:
#if AUTOTEST
        jsr band_invoer                 // stick van de band (cursor x,y / vuur) en de ruwe standen
#else
        lda #0
        sta invoer_stick
#endif
        lda invoer_stick
        ora joy_stand
        sta invoer_stick
        jsr toetsen_naar_stick
        lda poort1_stand                // muisknop links (of vuur van joystick 1)
        and #MUIS_LINKS
        beq !+
        lda invoer_stick
        ora #%10000
        sta invoer_stick
!:      lda poort1_stand
        and #MUIS_RECHTS
        sta muis_rechts
        jsr muis_beweging

        lda invoer_stick
        and #%10000
        tax
        eor invoer_vorig                // nieuw ingedrukt = nu aan en vorig beeld uit
        and invoer_stick
        lsr
        lsr
        lsr
        lsr
        sta invoer_vuur
        stx invoer_vorig
        beq !+
        inc invoer_vuur_teller
!:      rts

// toetsen_naar_stick: CRSR-toetsen, SPATIE, CTRL en RETURN erbij in invoer_stick
toetsen_naar_stick: {
        lda toets_rij1
        and #TOETS_RIJ1_LSHIFT
        sta shift
        lda toets_rij6
        and #TOETS_RIJ6_RSHIFT
        ora shift
        sta shift                       // niet 0 = een SHIFT is ingedrukt

        lda toets_rij0
        and #TOETS_RIJ0_CRSR_OB
        beq !+
        lda #%0010                      // CRSR ⇓: neer
        ldx shift
        beq zet1
        lda #%0001                      // met SHIFT: op
zet1:   ora invoer_stick
        sta invoer_stick
!:      lda toets_rij0
        and #TOETS_RIJ0_CRSR_LR
        beq !+
        lda #%1000                      // CRSR ⇒: rechts
        ldx shift
        beq zet2
        lda #%0100                      // met SHIFT: links
zet2:   ora invoer_stick
        sta invoer_stick
!:      lda toets_rij7
        and #TOETS_RIJ7_SPATIE | TOETS_RIJ7_CTRL
        bne vuur
        lda toets_rij0
        and #TOETS_RIJ0_RETURN
        beq klaar
vuur:   lda invoer_stick
        ora #%10000
        sta invoer_stick
klaar:  rts
shift:  .byte 0
}

// muis_beweging: uit de potmeters van de 1351 de beweging sinds het vorige beeld.
// De 1351 telt in bits 1-6 (64 standen, rondlopend); bit 0 is ruis. Zonder muis staan de
// potmeters stil (meestal $FF) en is de beweging 0.
muis_beweging: {
        lda pot_x                       // beide $FF: geen muis. Komt er (weer) een, dan is de eerste
        and pot_y                       // meting alleen het beginpunt
        cmp #$ff
        bne !+
        lda #0
        sta muis_begonnen
        sta muis_dx
        sta muis_dy
        rts
!:      lda muis_begonnen               // de eerste meting is alleen het beginpunt: anders springt
        bne !+                          // de cursor bij het starten (gezien in VICE met een 1351)
        inc muis_begonnen
        lda pot_x
        and #%01111110
        sta muis_oud_x
        lda pot_y
        and #%01111110
        sta muis_oud_y
        lda #0
        sta muis_dx
        sta muis_dy
        rts
!:      lda pot_x
        ldy muis_oud_x
        jsr verschil
        sty muis_oud_x
        sta muis_dx
        lda pot_y
        ldy muis_oud_y
        jsr verschil
        sty muis_oud_y
        eor #$ff                        // Y van de muis loopt omhoog, het scherm omlaag: omkeren
        clc
        adc #1
        sta muis_dy
        rts

// A = nieuwe potwaarde, Y = oude. Terug: A = verschil in tellen (met teken), Y = nieuwe waarde.
verschil:
        and #%01111110
        sta nieuw
        sty oud
        sec
        sbc oud
        and #%01111111                  // rondlopend over 64 standen (x2)
        cmp #%01000000
        bcs negatief
        lsr                             // 0..31
        ldy nieuw
        rts
negatief:
        ora #%10000000                  // -64..-1 (x2), dan delen door 2 met teken
        sec
        ror
        ldy nieuw
        rts
nieuw:  .byte 0
oud:    .byte 0
}

.segment Data
invoer_stick:       .byte 0
invoer_vorig:       .byte 0
invoer_vuur:        .byte 0
invoer_vuur_teller: .byte 0             // telt het aantal keer vuur (voor de tests)
// ruwe standen, 1 = ingedrukt (gevuld door invoer_hardware, of in AUTOTEST door de band)
joy_stand:          .byte 0             // joystick 2
toets_rij0:         .byte 0             // matrixrijen
toets_rij1:         .byte 0
toets_rij6:         .byte 0
toets_rij7:         .byte 0
poort1_stand:       .byte 0             // muisknoppen / joystick 1
pot_x:              .byte $ff           // potmeters ($D419/$D41A), zoals gelezen
pot_y:              .byte $ff
// muis
muis_oud_x:         .byte $7e
muis_oud_y:         .byte $7e
muis_dx:            .byte 0             // beweging dit beeld, met teken
muis_dy:            .byte 0
muis_rechts:        .byte 0
muis_begonnen:      .byte 0             // 0 tot de eerste meting
