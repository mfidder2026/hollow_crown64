// main.asm — Hollow Crown, hoofdbestand van de motor.
// Bouwen: ./build.sh (gewoon) of ./build.sh --autotest (met invoerband voor tools/vicetest.py).
//
// Hoofdstuk 1 (het scherm): gesplitst scherm met berichtregels, kamer (Dawnhaven 160x128) en balk;
// werkwoorden en een lege inventaris getekend; de cursor beweegt met joystick, muis of toetsen.
// Hoofdstuk 2 (Eldric loopt): klik op de vloer en Eldric loopt erheen, via de loopvakken (BFS).
// Voorgrond (uit hoofdstuk 8, vervroegd): achter de fontein staat het torentje vóór hem.
// Hoofdstuk 3 (voorwerpen en zinregel): "Bekijk fontein" -> Eldric loopt erheen en zegt iets (VM: ZEG).

#import "geheugen.asm"
#import "../build/gen/lettertype_info.asm"     // cursor-midden en pijltekens (tools/lettertype.py)
#import "teksten_nl.asm"                       // eerst: de constanten erin gebruikt de balk
#import "../build/gen/spel.asm"                 // loopvakken en BEGIN_* (tools/scriptc.py)
#import "../build/gen/costumes.asm"            // poses van Eldric (tools/costume.py)
#import "../build/gen/kamer_plein_voorgrond.asm" // de voorgrond-sprite van het plein (tools/kamer.py)

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

        jsr status_begin
        jsr scherm_start
        lda #<kamer_plein
        sta zp_ptr
        lda #>kamer_plein
        sta zp_ptr + 1
        jsr kamer_tonen
        jsr balk_tekenen
        ldx st_kamer
        jsr kamer_gegevens
        jsr actor_start
        jsr cursor_start
        jsr irq_start                   // zet ook het scherm aan
#if AUTOTEST
        jsr band_begin
#endif
        cli
        jmp hoofdlus

// kamer_gegevens: loopvakken, schaal en ACHTER van kamer X (tabellen uit build/gen/spel.asm)
kamer_gegevens:
        stx kamer_nu
        lda kamer_loopvakken_lo,x
        sta zp_ptr
        lda kamer_loopvakken_hi,x
        sta zp_ptr + 1
        jsr loopvakken_laden
        ldx kamer_nu
        lda kamer_schaal_lo,x
        sta zp_ptr
        lda kamer_schaal_hi,x
        sta zp_ptr + 1
        jsr schaal_laden
        ldx kamer_nu
        lda kamer_achter_lo,x
        sta zp_ptr
        lda kamer_achter_hi,x
        sta zp_ptr + 1
        jmp voorgrond_start

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
        jsr klik                        // zin.asm
        jsr actie_beeld
        jsr vm_stap
        jsr bericht_beeld
        jsr zin_beeld
        jsr actor_beweeg
        jsr actor_plaatsen
        jsr voorgrond_bij
        jsr cursor_plaatsen
#if AUTOTEST
        jsr band_controle
        jsr band_stap
#endif
        jmp hoofdlus



kamer_nu: .byte 0

// ---------------------------------------------------------------------------------------------
#import "irq.asm"
#import "scherm.asm"
#import "inpak.asm"
#import "kamer.asm"
#import "loopvak.asm"
#import "actor.asm"
#import "voorgrond.asm"
#import "bericht.asm"
#import "vm.asm"
#import "balk.asm"                              // vóór zin.asm: de kleuren van de balk
#import "zin.asm"
#import "invoer.asm"
#import "cursor.asm"
#import "status.asm"
#import "autotest.asm"

// Controle aan het eind, als alle segments gevuld zijn
.segment Buffers
buffers_eind:
.assert "programma en buffers blijven onder $C000", buffers_eind <= PRG_EIND, true
