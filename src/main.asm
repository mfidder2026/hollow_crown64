// main.asm — Hollow Crown, hoofdbestand van de motor.
// Bouwen: ./build.sh (gewoon) of ./build.sh --autotest (met invoerband voor tools/vicetest.py).
//
// Hoofdstuk 1 (het scherm): gesplitst scherm met berichtregels, kamer (Dawnhaven 160x128) en balk;
// werkwoorden en een lege inventaris getekend; de cursor beweegt met joystick, muis of toetsen.
// Hoofdstuk 2 (Eldric loopt): klik op de vloer en Eldric loopt erheen, via de loopvakken (BFS).
// Voorgrond (uit hoofdstuk 8, vervroegd): achter de fontein staat het torentje vóór hem.
// Hoofdstuk 3 (voorwerpen en zinregel): "Bekijk fontein" -> Eldric loopt erheen en zegt iets (VM: ZEG).
// Hoofdstuk 7: figuren (NPC's) en gesprekken met keuzes.
// Hoofdstuk 4 (VM): alle opdrachten, voorwerpen met eigenaar en stand. Hoofdstuk 5: inventaris, "Gebruik x met y".

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

        jsr status_begin
        jsr npc_begin
        jsr tod_start
        jsr scherm_start
        jsr actor_start
        jsr cursor_start
#if AUTOTEST
        jsr band_begin                  // vóór het intro: de band kan het intro bedienen
#endif
        jsr intro                       // titel, logo, scrolltekst en muziek tot spatie of vuur (intro.asm)
        jsr balk_tekenen
        lda intro_gedaan                // na het titelscherm eerst het verhaal (VERHAAL in spel.hcs, toneel.asm)
        beq begin
        lda #VERHAAL_KAMER
        cmp #255
        beq begin
        lda #<VERHAAL_X
        sta kw_x
        lda #>VERHAAL_X
        sta kw_x + 1
        lda #VERHAAL_Y
        sta kw_y
        lda #VERHAAL_RICHTING
        sta kw_richting
        lda #VERHAAL_KAMER
        jsr kamer_wissel
        cli
        jmp hoofdlus
begin:  lda #<BEGIN_X                   // de eerste kamer, van de diskette (laden_einde zet de IRQ's aan)
        sta kw_x
        lda #>BEGIN_X
        sta kw_x + 1
        lda #BEGIN_Y
        sta kw_y
        lda #BEGIN_RICHTING
        sta kw_richting
        lda #BEGIN_KAMER
        jsr kamer_wissel
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
        jsr flakker_laden
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
        lda baas_actief                 // de baas-toets: alleen het rekenblad (baas.asm)
        beq !+
        jsr baas_beeld
#if AUTOTEST
        jsr band_stap
#endif
        jmp hoofdlus
!:
        jsr invoer_lees
        jsr cursor_beweeg
        jsr cursor_muis
#if AUTOTEST
        jsr band_na_beweging
#endif
        jsr menu_beeld                  // de menubalk in rij 0-1 (menu.asm); een klik daar is voor het menu
        jsr klik                        // zin.asm
        jsr actie_beeld
        jsr vm_stap
        lda baas_terug                  // terug van het rekenblad: het beeld aan als alles hersteld is (baas.asm)
        beq !+
        lda vm_pc + 1
        bne !+
        lda #0
        sta baas_terug
        jsr scherm_aan
!:
        jsr bericht_beeld
        jsr zin_beeld
        jsr actor_beweeg
        jsr actor_plaatsen
        jsr npc_beweeg
        jsr npc_sprites
        jsr flakker_beeld
        jsr mist_beeld                  // mist.asm
        jsr voorgrond_bij
        jsr cursor_plaatsen
        jsr functietoetsen              // F5 opslaan, F7 laden (opslaan.asm)
        jsr melding_beeld
        jsr voltooid_beeld
#if AUTOTEST
        jsr band_controle
        jsr band_stap
#endif
        jmp hoofdlus



kamer_nu: .byte 0

// ---------------------------------------------------------------------------------------------
#import "status.asm"                            // vroeg: MAX_VOORWERPEN e.d.
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
#import "npc.asm"
#import "gesprek.asm"
#import "flakker.asm"
#import "inventaris.asm"
#import "schijf.asm"
#import "turbo.asm"
#import "geluid.asm"
#import "opslaan.asm"
#import "muziek.asm"
#import "intro.asm"
#import "toneel.asm"
#import "terug.asm"
#import "mist.asm"
#import "menu.asm"
#import "baas.asm"
#import "basic.asm"
#import "invoer.asm"
#import "cursor.asm"
#import "autotest.asm"

// Controle aan het eind, als alle segments gevuld zijn
.segment Buffers
buffers_eind:
.assert "programma en buffers blijven onder de kamerbuffer ($A000)", buffers_eind <= PRG_EIND, true
