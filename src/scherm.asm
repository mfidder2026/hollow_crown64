// scherm.asm — de VIC instellen, scherm en bitmap leegmaken, het lettertype op zijn plek, en tekst schrijven.

.segment Code
// scherm_start: aanroepen met de IRQ's uit. Laat het scherm uit ($d011 bit 4); irq_start zet het aan.
scherm_start:
        lda #$0b                        // scherm uit tijdens het opbouwen
        sta $d011
        lda $dd02
        ora #%00000011                  // bits 0-1 als uitgang
        sta $dd02
        lda $dd00                       // lezen-wijzigen-schrijven: bits 2-7 zijn de seriële bus
        and #%11111100
        ora #DD00_BANK3
        sta $dd00
        lda #D018_ALLES
        sta $d018
        lda #0
        sta $d020
        sta $d021                       // zwart, overal (zie irq.asm)
        sta $d015                       // geen sprites
        lda #$c0                        // de Kernal-schermeditor kijkt ook naar $C000
        sta $0288
        lda #1
        sta $cc                         // geen knipperende cursor van de Kernal

        // scherm-RAM: spaties; kleur-RAM: zwart
        ldx #0
!:      lda #$20
        sta SCHERM,x
        sta SCHERM + $100,x
        sta SCHERM + $200,x
        sta SCHERM + $2e8,x
        lda #0
        sta KLEUR_RAM,x
        sta KLEUR_RAM + $100,x
        sta KLEUR_RAM + $200,x
        sta KLEUR_RAM + $2e8,x
        inx
        bne !-

        // bitmap $E000-$F7FF op nul (schrijven onder de Kernal-ROM gaat altijd naar het RAM)
        lda #<BITMAP
        sta zp_ptr
        lda #>BITMAP
        sta zp_ptr + 1
        ldx #>(LETTERTYPE - BITMAP)
        lda #0
        tay
!:      sta (zp_ptr),y
        iny
        bne !-
        inc zp_ptr + 1
        dex
        bne !-

        // lettertype naar $F800 (2 KB)
        lda #<lettertype_data
        sta zp_ptr
        lda #>lettertype_data
        sta zp_ptr + 1
        lda #<LETTERTYPE
        sta zp_ptr2
        lda #>LETTERTYPE
        sta zp_ptr2 + 1
        ldx #8
        ldy #0
!:      lda (zp_ptr),y
        sta (zp_ptr2),y
        iny
        bne !-
        inc zp_ptr + 1
        inc zp_ptr2 + 1
        dex
        bne !-

        // $FFFA-$FFFF in het RAM (teken 255, rij 2-7, nooit op het scherm): veilige vectoren, voor als
        // de Kernal-ROM ooit even weg is ($01=$35) en er een NMI (RESTORE) komt
        ldx #5
!:      lda vectoren,x
        sta $fffa,x
        dex
        bpl !-
        rts

nmi_leeg:
        rti

// tekst_schrijf: schrijf de tekst op (zp_ptr), afgesloten met 0, naar rij Y, kolom X, in kleur A.
// Gebruikt zp_ptr2 (scherm) en zp_ptr3 (kleur-RAM). Na afloop: Y = aantal geschreven tekens.
tekst_schrijf:
        sta tekst_kleur
        txa
        clc
        adc rij_lo,y
        sta zp_ptr2
        sta zp_ptr3
        lda rij_hi,y
        adc #0
        sta zp_ptr2 + 1
        clc
        adc #>KLEUR_OFFSET
        sta zp_ptr3 + 1
        ldy #0
!:      lda (zp_ptr),y
        beq !+
        sta (zp_ptr2),y
        lda tekst_kleur
        sta (zp_ptr3),y
        iny
        bne !-
!:      rts

// rij_wissen: tekenrij Y vol spaties, kleur A
rij_wissen:
        sta tekst_kleur
        lda rij_lo,y
        sta zp_ptr2
        sta zp_ptr3
        lda rij_hi,y
        sta zp_ptr2 + 1
        clc
        adc #>KLEUR_OFFSET
        sta zp_ptr3 + 1
        ldy #39
!:      lda #$20
        sta (zp_ptr2),y
        lda tekst_kleur
        sta (zp_ptr3),y
        dey
        bpl !-
        rts

.segment Data
tekst_kleur:  .byte 0
vectoren:     .word nmi_leeg, $fce2, $ff48   // NMI, RESET, IRQ (zoals de Kernal)
rij_lo:       .fill 25, <(SCHERM + i * 40)
rij_hi:       .fill 25, >(SCHERM + i * 40)
.assert "KLEUR_OFFSET is een veelvoud van $100", <KLEUR_OFFSET, 0

lettertype_data:
        .import binary "../build/gen/lettertype.bin"
.assert "lettertype is 2 KB", * - lettertype_data, $800
