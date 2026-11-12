// voorgrond.asm — iets in de kamer dat vóór Eldric komt als hij erachter staat (§6.2, hoofdstuk 8 vervroegd).
//
// Hoe: de voorgrond (het torentje van de fontein) is óók een sprite, nummer 1. Een sprite met een lager nummer
// komt vóór een sprite met een hoger nummer, en Eldric is sprite 2 en 3. Staan zijn voeten in het ACHTER-vak
// van de kamer (scripts/*.hcs), dan gaat sprite 1 aan; anders uit (vóór de fontein moet hij erover lopen).
// tools/kamer.py geeft die pixels in de bitmap precies dezelfde kleuren als de sprite: aan of uit zie je niet.
//
// Gekozen boven $d01b (sprite achter bitmapcodes %10/%11): dat dwong rond het torentje alle achtergrond in
// zwart + 1 kleur per vakje, en dan verdwenen het pad en de waterdamp (zie docs/LOGBOEK.md).

.const VG_SPRITE  = %00000010           // sprite 1
.const VG_VAK     = 7                   // sprite-vak 7
.const VG_PTR     = (SPRITE_VAKKEN - SCHERM) / 64 + VG_VAK
.assert "voorgrond-vak binnen de sprite-vakken", SPRITE_VAKKEN + (VG_VAK + 1) * 64 <= $c800, true

.segment Code
// voorgrond_start: de voorgrond van de kamer (uit de kamerbuffer) neerzetten, uit; en zijn ACHTER-vak laden
// van (zp_ptr). Zonder voorgrondblok in het kamerbestand: nooit erachter.
voorgrond_start: {
        ldy #6
!:      lda (zp_ptr),y
        sta achter_vak,y
        dey
        bpl !-
        lda $d015
        and #~VG_SPRITE
        sta $d015
        lda KAMER_BUF                   // plek van het voorgrondblok (0 = geen)
        ora KAMER_BUF + 1
        bne !+
        lda #0
        sta achter_vak
        rts
!:      lda KAMER_BUF
        clc
        adc #<KAMER_BUF
        sta zp_ptr
        lda KAMER_BUF + 1
        adc #>KAMER_BUF
        sta zp_ptr + 1
        ldy #66                         // x, y, kleur, 64 bytes: de sprite naar vak 7
!:      lda (zp_ptr),y
        sta SPRITE_VAKKEN + VG_VAK * 64 - 3,y
        dey
        cpy #2
        bne !-
        lda #VG_PTR
        sta SPRITE_PTR + 1
        ldy #0
        lda (zp_ptr),y                  // x: 24 + 2 * x (kan boven 255)
        asl
        sta hulp
        lda #0
        rol
        sta hulp + 1
        lda hulp
        clc
        adc #24
        sta $d002
        lda hulp + 1
        adc #0
        beq !+
        lda #VG_SPRITE
!:      sta hulp
        lda $d010
        and #~VG_SPRITE
        ora hulp
        sta $d010
        ldy #1
        lda (zp_ptr),y
        clc
        adc #50 + RIJ_KAMER * 8
        sta $d003
        iny
        lda (zp_ptr),y
        sta $d028
        lda $d01c
        ora #VG_SPRITE                  // multicolor: zwart ($d025) en de eigen kleur
        sta $d01c
        lda $d01b
        and #~VG_SPRITE
        sta $d01b
        rts
hulp:   .word 0
}

// voorgrond_bij: elk beeld. Voeten van Eldric in het ACHTER-vak -> sprite 1 aan, anders uit.
voorgrond_bij: {
        lda #0
        sta act_achter
        lda achter_vak                  // aantal: 0 = geen
        beq zet
        lda act_x                       // x1 <= act_x <= x2
        cmp achter_vak + 1
        lda act_x + 1
        sbc achter_vak + 2
        bcc zet
        lda achter_vak + 3
        cmp act_x
        lda achter_vak + 4
        sbc act_x + 1
        bcc zet
        lda act_y                       // y1 <= act_y <= y2
        cmp achter_vak + 5
        bcc zet
        lda achter_vak + 6
        cmp act_y
        bcc zet
        inc act_achter
zet:    lda $d015
        and #~VG_SPRITE
        ldx act_achter
        beq !+
        ora #VG_SPRITE
!:      sta $d015
        rts
}

.segment Data
achter_vak:   .fill 7, 0                // aantal, x1 lo, x1 hi, x2 lo, x2 hi, y1, y2
act_achter:   .byte 0                   // 1: Eldric staat achter de voorgrond
