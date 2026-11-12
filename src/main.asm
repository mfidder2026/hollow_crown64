// main.asm — Hollow Crown, hoofdbestand van de motor.
// Bouwen: ./build.sh (gewoon) of ./build.sh --autotest (met invoerband voor tools/vicetest.py).
//
// Hoofdstuk 1 (het scherm): gesplitst scherm met berichtregels, kamer (Dawnhaven 160x128) en balk;
// werkwoorden en een lege inventaris getekend; de cursor beweegt met de joystick (of de band).

#import "geheugen.asm"
#import "../build/gen/lettertype_info.asm"     // cursor-midden en pijltekens (tools/lettertype.py)
#import "teksten_nl.asm"                       // eerst: de constanten erin gebruikt de balk

.file [name="hollowcrown.prg", segments="Basic,Code,Data"]

.segment Basic
BasicUpstart2(start)

.segment Code
start:
        sei
        lda #CPU_NORMAAL
        sta $01
        cld
        ldx #$ff
        txs

        jsr scherm_start
        lda #<kamer_plein
        sta zp_ptr
        lda #>kamer_plein
        sta zp_ptr + 1
        jsr kamer_tonen
        jsr balk_tekenen
        jsr bericht_proef
        jsr cursor_start
        jsr irq_start                   // zet ook het scherm aan
#if AUTOTEST
        jsr band_begin
#endif
        cli

// De hoofdlus: één ronde per beeld.
hoofdlus:
        lda beelden
!:      cmp beelden                     // wacht op het volgende beeld
        beq !-
        jsr invoer_lees
        jsr cursor_beweeg
        jsr cursor_muis
#if AUTOTEST
        jsr band_na_beweging
#endif
        jsr cursor_plaatsen
#if AUTOTEST
        jsr band_stap
#endif
        jmp hoofdlus

// ---------------------------------------------------------------------------------------------
#import "irq.asm"
#import "scherm.asm"
#import "inpak.asm"
#import "kamer.asm"
#import "balk.asm"
#import "invoer.asm"
#import "cursor.asm"
#import "status.asm"
#import "autotest.asm"

// Controle aan het eind, als alle segments gevuld zijn
.segment Buffers
buffers_eind:
.assert "programma en buffers blijven onder $C000", buffers_eind <= PRG_EIND, true
