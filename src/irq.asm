// irq.asm — het gesplitste scherm (§6.3): drie raster-IRQ's per beeld.
//
// YSCROLL=3: tekenrij r begint op rasterlijn 51 + 8r. Rij 2 op lijn 67, rij 18 op lijn 195.
// $d018 blijft altijd $0E (zie geheugen.asm); alleen $d011 en $d016 wisselen. $d021 is altijd zwart.
//
//   lijn 65 -> wacht tot 66, dan tegen het eind van lijn 66 (rechterrand): multicolor bitmap.
//              Komt dat te laat (sprite-DMA), dan toont lijn 67 even tekstmodus met als tekens de
//              kleurbytes van de kamer: pixelrij 0 van elk teken is leeg en de bovenste kamerrij is
//              zwart, dus je ziet niets.
//   lijn 194 -> wacht tot 195 (rij 18, pixelrij 0): tekstmodus. Ervoor toont de VIC bitmaprij 18
//              (nul = zwart), erna pixelrij 0 van de tekens (leeg): op welke cyclus het ook valt, zwart.
//   lijn 252 -> onderrand: tekstmodus voor rij 0-1 van het volgende beeld, beelden tellen, joystick,
//              toetsen en muis lezen (invoer.asm), één keer per beeld naar de Kernal ($EA31).
//
// Gemeten (VICE 3.10, watchpoint op $d011, alleen de cursor als sprite): kamer op lijn 66 cyclus 62 of
// lijn 67 cyclus 0; balk op lijn 195 cyclus 9 of 56 (na de badline); onderrand op lijn 252.
// Nog niet gemeten met 8 sprites op de naad (hoofdstuk 2+): valt de kamerwissel dan na cyclus ~14 van
// lijn 67, dan wacht de CPU tot cyclus 55 en is lijn 67 zwart — wat de bovenste kamerrij toch al is.

.const IRQ_KAMER     = 65
.const IRQ_BALK      = 194
.const IRQ_ONDERRAND = 252
.const IRQ_SCROLL    = 241              // alleen in het intro

.const D011_TEKST    = $1b              // scherm aan, 25 rijen, YSCROLL 3
.const D011_BITMAP   = $3b
.const D016_TEKST    = $c8              // hires, 40 kolommen
.const D016_KAMER    = $d8              // multicolor

.segment Code
// irq_start: CIA-IRQ uit, raster-IRQ aan. Aanroepen met de IRQ's uit (SEI).
irq_start:
        lda #$7f
        sta $dc0d                       // CIA 1: geen IRQ's meer
        sta $dd0d                       // CIA 2: geen NMI's meer
        lda $dc0d                       // wachtende verzoeken wissen
        lda $dd0d
        lda #<irq_onderrand
        sta $0314
        lda #>irq_onderrand
        sta $0315
        lda #IRQ_ONDERRAND
        sta $d012
        lda d011_tekst                 // bit 7 = 0: bit 8 van de rasterlijn; scherm weer aan
        sta $d011
        lda #%00000001
        sta $d01a                       // raster-IRQ aan
        sta $d019                       // en een eventueel wachtend verzoek wissen
        rts

// Lijn 65: naar de kamer
irq_kamer:
        lda #%00000001
        sta $d019
        lda #IRQ_KAMER + 1
!:      cmp $d012                       // wacht op lijn 66 (hooguit 7 cycli later gezien)
        bne !-
        ldx #9                          // ~45 cycli: naar de rechterrand van lijn 66
!:      dex
        bne !-
        lda baas_actief                 // de baas-toets: het hele scherm blijft tekst (baas.asm)
        bne !+
        lda #D016_KAMER                 // eerst multicolor (tekst in kleur 0-7 blijft gewoon)
        sta $d016
        lda d011_kamer 
        sta $d011
!:      lda #IRQ_BALK
        sta $d012
        lda #<irq_balk
        sta $0314
        lda #>irq_balk
        sta $0315
        jmp $ea81                       // registers terug, RTI

// Lijn 194: naar de balk
irq_balk:
        lda #%00000001
        sta $d019
        lda #IRQ_BALK + 1
!:      cmp $d012                       // wacht op lijn 195
        bne !-
        lda d011_tekst
        sta $d011
        lda #D016_TEKST
        sta $d016
        lda #POORT1_POTS                // de SID meet vanaf nu de muis in poort 1 (invoer.asm)
        sta $dc00
        lda intro_actief                // het intro: eerst nog de scroll-split (rij 24)
        beq !+
        lda #IRQ_SCROLL
        sta $d012
        lda #<irq_scroll
        sta $0314
        lda #>irq_scroll
        sta $0315
        jmp $ea81
!:      lda #IRQ_ONDERRAND
        sta $d012
        lda #<irq_onderrand
        sta $0314
        lda #>irq_onderrand
        sta $0315
        jmp $ea81

// Lijn 241 (alleen in het intro): rij 24 vloeiend scrollen. Rij 23 is leeg, dus waar op de lijn dit valt maakt
// niet uit. 38 kolommen: de tekens die in- en uitschuiven verdwijnen achter de rand.
irq_scroll:
        lda #%00000001
        sta $d019
        lda intro_xscroll
        ora #%11000000                  // (bit 3 = 0: 38 kolommen)
        sta $d016
        lda #IRQ_ONDERRAND
        sta $d012
        lda #<irq_onderrand
        sta $0314
        lda #>irq_onderrand
        sta $0315
        jmp $ea81

// Lijn 252: onderrand
irq_onderrand:
        lda #%00000001
        sta $d019
        lda d011_tekst
        sta $d011
        lda #D016_TEKST
        sta $d016
        inc beelden
        bne !+
        inc beelden + 1
!:
        jsr geluid_beeld                // geluidseffecten (geluid.asm)
        jsr muziek_beeld                // het thema (muziek.asm)
#if !AUTOTEST
        jsr invoer_hardware             // joystick, toetsen, muis (invoer.asm), vóór de Kernal-scan
#endif
        lda #IRQ_KAMER
        sta $d012
        lda #<irq_kamer
        sta $0314
        lda #>irq_kamer
        sta $0315
        jmp $ea31                       // Kernal: toetsenbord, klok

// scherm_uit / scherm_aan: het beeld zwart (bit 4 van $d011 = 0) terwijl er iets wordt opgebouwd, zonder rommel
// (de baas-toets: terug van het rekenblad). De IRQ's schrijven $d011 uit deze twee variabelen.
scherm_uit:
        inc scherm_uit_teller
        lda #D011_TEKST & %11101111
        sta d011_tekst
        lda #D011_BITMAP & %11101111
        sta d011_kamer
        rts
scherm_aan:
        lda #D011_TEKST
        sta d011_tekst
        lda #D011_BITMAP
        sta d011_kamer
        rts

.segment Data
d011_tekst:   .byte D011_TEKST
d011_kamer:   .byte D011_BITMAP
scherm_uit_teller: .byte 0              // hoe vaak het beeld even zwart was (voor de tests)
beelden:      .word 0                  // beeldteller, telt op in de IRQ
