// cursor.asm — de cursor: hires sprite 0 (bovenop alle andere sprites), sprite-vak 6.
// Positie in schermpixels: x 0-319, y 0-199. Versnelt als je de joystick vasthoudt (§4).

// CURSOR_MIDDEN_X/Y: uit build/gen/lettertype_info.asm (tools/lettertype.py), geïmporteerd in main.asm

.const CURSOR_VAK      = 6
.const CURSOR_PTR      = (SPRITE_VAKKEN - SCHERM) / 64 + CURSOR_VAK
.const CURSOR_KLEUR    = 1              // wit (daarna wisselend, zie cursor_kleuren)
.const CURSOR_MAX      = 4              // hoogste snelheid, pixels per beeld
.const CURSOR_SNELLER  = 8              // elke 8 beelden vasthouden: 1 sneller

.segment Code
cursor_start:
        ldx #63
!:      lda cursor_data,x
        sta SPRITE_VAKKEN + CURSOR_VAK * 64,x
        dex
        bpl !-
        lda #CURSOR_PTR
        sta SPRITE_PTR + 0
        lda #CURSOR_KLEUR
        sta $d027
        lda $d01c
        and #%11111110                  // hires
        sta $d01c
        lda $d01b
        and #%11111110                  // voor de achtergrond
        sta $d01b
        lda $d015
        ora #%00000001
        sta $d015
        jmp cursor_plaatsen

// cursor_beweeg: één beeld bewegen volgens invoer_stick
cursor_beweeg: {
        lda invoer_stick
        and #%1111
        bne vast
        lda #1
        sta cursor_snelheid
        lda #0
        sta cursor_vast
        rts
vast:   inc cursor_vast
        lda cursor_vast
        and #CURSOR_SNELLER - 1
        bne !+
        lda cursor_snelheid
        cmp #CURSOR_MAX
        bcs !+
        inc cursor_snelheid
!:
        lda invoer_stick                // op
        and #%0001
        beq !+
        lda cursor_y
        sec
        sbc cursor_snelheid
        bcs zet_op
        lda #0
zet_op: sta cursor_y
!:      lda invoer_stick                // neer
        and #%0010
        beq !+
        lda cursor_y
        clc
        adc cursor_snelheid
        cmp #200
        bcc zet_neer
        lda #199
zet_neer:
        sta cursor_y
!:      lda invoer_stick                // links
        and #%0100
        beq !+
        lda cursor_x
        sec
        sbc cursor_snelheid
        sta cursor_x
        lda cursor_x + 1
        sbc #0
        sta cursor_x + 1
        bpl !+
        lda #0
        sta cursor_x
        sta cursor_x + 1
!:      lda invoer_stick                // rechts
        and #%1000
        beq klaar
        lda cursor_x
        clc
        adc cursor_snelheid
        sta cursor_x
        lda cursor_x + 1
        adc #0
        sta cursor_x + 1
        lda cursor_x                    // hooguit 319
        cmp #<320
        lda cursor_x + 1
        sbc #>320
        bcc klaar
        lda #<319
        sta cursor_x
        lda #>319
        sta cursor_x + 1
klaar:  rts
}

// cursor_plaatsen: sprite 0 op cursor_x/y, met het midden van de tekening op dat punt
cursor_plaatsen:
        lda cursor_x
        clc
        adc #24 - CURSOR_MIDDEN_X
        sta $d000
        lda cursor_x + 1
        adc #0
        and #1
        sta cursor_hulp
        lda $d010
        and #%11111110
        ora cursor_hulp
        sta $d010
        lda cursor_y
        clc
        adc #50 - CURSOR_MIDDEN_Y
        sta $d001
        lda beelden                     // kleur wisselt elke 4 beelden: zichtbaar op elke ondergrond
        lsr
        lsr
        and #7
        tax
        lda cursor_kleuren,x
        sta $d027
        rts

.segment Data
cursor_x:        .word 160
cursor_y:        .byte 100
cursor_snelheid: .byte 1
cursor_vast:     .byte 0
cursor_hulp:     .byte 0
cursor_kleuren:  .byte 1, 15, 12, 11, 0, 11, 12, 15
cursor_data:
        .import binary "../build/gen/cursor.bin"
.assert "cursor is 64 bytes", * - cursor_data, 64
