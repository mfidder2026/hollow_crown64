// main.asm — Hollow Crown, hoofdbestand van de motor.
// Bouwen: ./build.sh (gewoon) of ./build.sh --autotest (met invoerband voor tools/vicetest.py).
//
// Hoofdstuk 1 (het scherm): gesplitst scherm met berichtregels, kamer (Dawnhaven 160x128) en balk;
// werkwoorden en een lege inventaris getekend; de cursor beweegt met joystick, muis of toetsen.
// Hoofdstuk 2 (Eldric loopt): klik op de vloer en Eldric loopt erheen, via de loopvakken (BFS).

#import "geheugen.asm"
#import "../build/gen/lettertype_info.asm"     // cursor-midden en pijltekens (tools/lettertype.py)
#import "teksten_nl.asm"                       // eerst: de constanten erin gebruikt de balk
#import "../build/gen/spel.asm"                 // loopvakken en BEGIN_* (tools/scriptc.py)
#import "../build/gen/costumes.asm"            // poses van Eldric (tools/costume.py)

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
        lda #<begin_loopvakken
        sta zp_ptr
        lda #>begin_loopvakken
        sta zp_ptr + 1
        jsr loopvakken_laden
        lda #<begin_schaal
        sta zp_ptr
        lda #>begin_schaal
        sta zp_ptr + 1
        jsr schaal_laden
        jsr actor_start
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
#if AUTOTEST
        lda band_markering              // vicetest kijkt: de wereld staat stil (een echte momentopname)
        bne hoofdlus
#endif
        jsr invoer_lees
        jsr cursor_beweeg
        jsr cursor_muis
#if AUTOTEST
        jsr band_na_beweging
#endif
        jsr klik
        jsr actor_beweeg
        jsr actor_plaatsen
        jsr cursor_plaatsen
#if AUTOTEST
        jsr band_controle
        jsr band_stap
#endif
        jmp hoofdlus

// klik: vuur in de kamer = "Ga naar" die plek (voorwerpen en werkwoorden: hoofdstuk 3)
klik:   lda invoer_vuur
        beq !+
        lda cursor_y
        cmp #RIJ_KAMER * 8
        bcc !+
        cmp #(RIJ_KAMER + KAMER_RIJEN) * 8
        bcs !+
        sec
        sbc #RIJ_KAMER * 8
        sta p_y
        lda cursor_x
        sta p_x
        lda cursor_x + 1
        sta p_x + 1
        jmp actor_loop_naar
!:      rts

// ---------------------------------------------------------------------------------------------
#import "irq.asm"
#import "scherm.asm"
#import "inpak.asm"
#import "kamer.asm"
#import "loopvak.asm"
#import "actor.asm"
#import "balk.asm"
#import "invoer.asm"
#import "cursor.asm"
#import "status.asm"
#import "autotest.asm"

// Controle aan het eind, als alle segments gevuld zijn
.segment Buffers
buffers_eind:
.assert "programma en buffers blijven onder $C000", buffers_eind <= PRG_EIND, true
