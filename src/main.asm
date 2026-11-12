// main.asm — Hollow Crown, hoofdbestand van de motor.
// Bouwen: ./build.sh (gewoon) of ./build.sh --autotest (met invoerband voor tools/vicetest.py).
//
// Hoofdstuk 0 (opzet): VIC-bank 3, ROM-lettertype als tijdelijk lettertype, een IRQ die de beelden
// telt, en (AUTOTEST) de invoerband. Het scherm toont alleen een titel en de beeldteller.

#import "geheugen.asm"

.file [name="hollowcrown.prg", segments="Basic,Code,Data"]

.const KLEUR_RAND        = 11           // donkergrijs
.const KLEUR_ACHTERGROND = 6            // blauw (nooit zwart: §2)
.const KLEUR_TEKST       = 1            // wit
.label TELLER_PLEK       = SCHERM + 40 * 24 + 36

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

        jsr vic_bank3
        jsr lettertype_rom
        jsr scherm_wissen
        jsr titel_tekenen
        jsr irq_start
#if AUTOTEST
        jsr band_begin
#endif
        cli

// De hoofdlus: één ronde per beeld.
hoofdlus:
        lda beelden
!:      cmp beelden                     // wacht op het volgende beeld
        beq !-
        jsr teller_tekenen
#if AUTOTEST
        jsr band_stap
#endif
        jmp hoofdlus

// ---------------------------------------------------------------------------------------------
// VIC naar bank 3, tekstmodus. $DD00 met lezen-wijzigen-schrijven: bits 2-7 zijn de seriële bus.
vic_bank3:
        lda $dd02
        ora #%00000011                  // bits 0-1 als uitgang
        sta $dd02
        lda $dd00
        and #%11111100
        ora #DD00_BANK3
        sta $dd00
        lda #D018_TEKST
        sta $d018
        lda #$1b                        // tekst, 25 rijen, YSCROLL 3
        sta $d011
        lda #$c8                        // hires, 40 kolommen
        sta $d016
        lda #$c0                        // de Kernal-schermeditor kijkt ook naar $C000
        sta $0288
        lda #1
        sta $cc                         // geen knipperende cursor
        rts

// Tijdelijk: kopieer de kleine-letterset uit de teken-ROM ($D800) naar $C800.
// In hoofdstuk 1 komt hier het eigen lettertype.
lettertype_rom:
        lda #$33                        // teken-ROM zichtbaar op $D000 (IRQ's staan uit)
        sta $01
        lda #<$d800
        sta zp_ptr
        lda #>$d800
        sta zp_ptr + 1
        lda #<LETTERTYPE
        sta zp_ptr2
        lda #>LETTERTYPE
        sta zp_ptr2 + 1
        ldx #8                          // 8 pagina's = 2 KB
        ldy #0
!:      lda (zp_ptr),y
        sta (zp_ptr2),y
        iny
        bne !-
        inc zp_ptr + 1
        inc zp_ptr2 + 1
        dex
        bne !-
        lda #CPU_NORMAAL
        sta $01
        rts

scherm_wissen:
        lda #KLEUR_RAND
        sta $d020
        lda #KLEUR_ACHTERGROND
        sta $d021
        ldx #0
!:      lda #$20
        sta SCHERM,x
        sta SCHERM + $100,x
        sta SCHERM + $200,x
        sta SCHERM + $2e8,x
        lda #KLEUR_TEKST
        sta KLEUR_RAM,x
        sta KLEUR_RAM + $100,x
        sta KLEUR_RAM + $200,x
        sta KLEUR_RAM + $2e8,x
        inx
        bne !-
        rts

titel_tekenen:
        ldx #titel_lengte - 1
!:      lda titel,x
        sta SCHERM + 40 * 0 + (40 - titel_lengte) / 2,x
        dex
        bpl !-
        ldx #ondertitel_lengte - 1
!:      lda ondertitel,x
        sta SCHERM + 40 * 2 + (40 - ondertitel_lengte) / 2,x
        dex
        bpl !-
        rts

// De beeldteller als 4 hexcijfers rechtsonder: zo verschillen screenshots op verschillende momenten.
teller_tekenen:
        lda beelden + 1
        ldx #0
        jsr hex_tekenen
        lda beelden
        ldx #2
        jmp hex_tekenen

// A als 2 hexcijfers op TELLER_PLEK + X
hex_tekenen:
        pha
        lsr
        lsr
        lsr
        lsr
        tay
        lda hex_cijfers,y
        sta TELLER_PLEK,x
        pla
        and #$0f
        tay
        lda hex_cijfers,y
        sta TELLER_PLEK + 1,x
        rts

.segment Data
.encoding "screencode_mixed"
titel:        .text "Hollow Crown"
.label titel_lengte = * - titel
ondertitel:   .text "hoofdstuk 0: opzet"
.label ondertitel_lengte = * - ondertitel
hex_cijfers:  .text "0123456789ABCDEF"

// ---------------------------------------------------------------------------------------------
#import "irq.asm"
#import "status.asm"
#import "autotest.asm"

// Controle aan het eind, als alle segments gevuld zijn
.segment Buffers
buffers_eind:
.assert "programma en buffers blijven onder $C000", buffers_eind <= PRG_EIND, true
