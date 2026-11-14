// taalmenu.asm — het taalmenu van de cartridge: een aardmannetje voor zijn hol vraagt welke taal je spreekt.
//
// src/crtboot.asm haalt dit uit de cartridge naar $4400 en roept MENU_START aan; terug komt X = de taal (0 nl, 1 en,
// 2 de, 3 fr). Het plaatje en de tabellen maakt tools/teken_taalmenu.py (build/gen/taalmenu_data.asm).
//
// Kiezen: met de muis (1351, poort 1) of de joystick (poort 2) een vlag aanwijzen en klikken/vuren, of meteen 1-4.
// Wat er beweegt: de ogen van het aardmannetje volgen de pijl (de pupillen zijn sprite 2) en knipperen af en toe; zijn
// mond beweegt als hij praat; de ballon vraagt het om de beurt in elke taal; een aangewezen vlag krijgt een
// knipperende rand en hij zegt iets in die taal; na het kiezen zegt hij "Goed zo!" met een deuntje.
//
// Alles zonder interrupts (sei): het menu wacht zelf op de onderrand. Geheugen: de code op $4400, de sprites op $5800,
// het scherm op $5C00, de bitmap op $6000 (VIC-bank 1); het kleur-RAM staat achter de bitmap en wordt gekopieerd.

.const SCHERM   = $5c00
.const BITMAP   = $6000
.const SPRITES  = $5800
.const SPR_PTR  = SCHERM + $3f8
.const ZP1      = $fb                   // wijzers (de boot gebruikt ze ook, maar niet zolang het menu loopt)
.const ZP2      = $fd
.const ZP3      = $02

.const KLEUR_RAND   = 11                // donkergrijs: een vlag die niet aangewezen is
.const HUID         = 9                 // bruin: dichte ogen, dichte mond
.const OOG          = 7                 // geel
.const MOND_OPEN    = 2                 // rood
.const PAUZE        = 170               // zo lang (beelden) blijft een zin staan als niemand iets aanwijst
.const NA_KIEZEN    = 110               // zo lang praat hij nog na het kiezen

.file [name="taalmenu.prg", segments="Menu,MenuData,Plaatje"]
.segmentdef Menu     [start=$4400, max=$57ff]
.segmentdef MenuData [startAfter="Menu", max=$57ff]
.segmentdef Plaatje  [start=BITMAP]

.segment MenuData                       // eerst: de constanten erin gebruikt de code
#import "../build/gen/lettertype_info.asm"     // CURSOR_MIDDEN_X/Y: de cursor van het spel (tools/lettertype.py)
cursor_data:
        .import binary "../build/gen/cursor.bin"
cursor_kleuren: .byte 1, 15, 12, 11, 0, 11, 12, 15     // zoals in het spel (cursor.asm)
#import "../build/gen/taalmenu_data.asm"

.segment Menu
MENU_START:
        sei
        cld
        jsr klaarzetten
lus:    jsr wacht_onderrand
        jsr invoer
        jsr pijl_zetten
        jsr aanwijzen
        jsr ogen
        jsr mond
        jsr randen
        jsr geluid
        inc beeld
        lda gekozen
        bmi lus
        lda nog                         // na het kiezen: nog even praten en flitsen, dan weg
        beq weg
        dec nog
        jmp lus
weg:    jsr opruimen
        ldx gekozen
        cli
        rts

// ---- klaarzetten en opruimen -----------------------------------------------------------------------------------------
klaarzetten: {
        lda #0
        sta $d015
        sta $d020
        sta $d021
        lda #$0b                        // scherm uit terwijl we kopiëren
        sta $d011
        ldx #0                          // scherm-RAM en kleur-RAM
!:      lda plaatje_scherm,x
        sta SCHERM,x
        lda plaatje_scherm + $100,x
        sta SCHERM + $100,x
        lda plaatje_scherm + $200,x
        sta SCHERM + $200,x
        lda plaatje_scherm + $2e8,x
        sta SCHERM + $2e8,x
        lda plaatje_kleur,x
        sta $d800,x
        lda plaatje_kleur + $100,x
        sta $d900,x
        lda plaatje_kleur + $200,x
        sta $da00,x
        lda plaatje_kleur + $2e8,x
        sta $dae8,x
        inx
        bne !-
        ldx #63                         // de sprites
!:      lda cursor_data,x
        sta SPRITES,x
        lda sprite_pupil,x
        sta SPRITES + 128,x
        dex
        bpl !-
        lda #(SPRITES - $4000) / 64
        sta SPR_PTR
        lda #(SPRITES - $4000) / 64 + 1
        sta SPR_PTR + 1
        lda #(SPRITES - $4000) / 64 + 2
        sta SPR_PTR + 2
        lda #1                          // de cursor wit (hij wisselt van kleur, zoals in het spel), de pupillen zwart
        sta $d027
        lda #0
        sta $d029
        sta $d01c
        sta $d017
        sta $d01d
        sta $d01b
        sta $d010
        lda $dd00                       // VIC-bank 1 ($4000-$7FFF)
        and #%11111100
        ora #%00000010
        sta $dd00
        lda #$78                        // scherm $5C00, bitmap $6000
        sta $d018
        lda #$18                        // multicolor
        sta $d016
        lda #$ff                        // het toetsenbord: alle lijnen uit; dan de potmeters van poort 1
        sta $dc02
        lda #0
        sta $dc03
        lda #$7f
        sta $dc00
        ldx #$18                        // de SID stil, volume vol
!:      lda #0
        sta $d400,x
        dex
        bpl !-
        lda #$0f
        sta $d418
        lda #160                        // de pijl begint midden rechts
        sta pijl_x
        lda #0
        sta pijl_x + 1
        lda #90
        sta pijl_y
        lda #$ff
        sta gekozen
        sta wijst
        sta muis_oud
        lda #0
        sta wacht_taal
        jsr nieuwe_wachtzin
        lda #140
        sta knipper
        jsr wacht_onderrand
        lda #$3b                        // bitmap aan
        sta $d011
        lda #%00000101
        sta $d015
        rts
}

opruimen: {
        jsr wacht_onderrand
        lda #0
        sta $d015
        sta $d418
        sta $d404
        lda #$1b
        sta $d011
        lda #$c8
        sta $d016
        lda #$15
        sta $d018
        lda $dd00                       // VIC-bank 0, zoals de Kernal hem achterliet
        ora #%00000011
        sta $dd00
        lda #$7f
        sta $dc00
        rts
}

wacht_onderrand: {
!:      lda $d011                       // eerst uit de onderrand weg (rasterlijn < 256)
        bmi !-
!:      lda $d012
        cmp #251
        bne !-
        rts
}

// ---- invoer: muis (poort 1), joystick (poort 2), toetsen 1-4 ---------------------------------------------------------
invoer: {
        lda #0
        sta dx
        sta dx + 1
        sta dy
        sta klik
        // de joystick in poort 2 (nu staat $dc00 nog op $7f: de lijnen 0-4 zijn hoog)
        lda $dc00
        eor #$1f
        and #$1f
        sta joy
        // poort 1 alleen (geen kolom van het toetsenbord): muisknop links = vuur
        lda #$ff
        sta $dc00
        lda $dc01
        eor #$ff
        sta poort1
        // het toetsenbord: de Kernal leest het (SCNKEY, GETIN), zoals elk programma; 1-4 kiest meteen
        jsr $ff9f                       // SCNKEY
        lda #$7f                        // terug: poort 1 op de potmeters
        sta $dc00
        jsr $ffe4                       // GETIN: A = de toets (PETSCII) of 0
        sec
        sbc #'1'
        cmp #4
        bcs vuur
        tax
toets:  stx wijst_toets
        jmp kies
vuur:   lda joy                         // vuur (joystick of muis), alleen als het net ingedrukt is
        ora poort1
        and #$10
        tax
        eor vuur_oud
        and #$10
        and #$10
        beq !+
        txa
        beq !+
        inc klik
!:      stx vuur_oud
        // joystick: bewegen, sneller als je hem vasthoudt
        lda joy
        and #$0f
        bne !+
        lda #1
        sta snel
        jmp muis
!:      lda snel
        cmp #6
        bcs !+
        inc snel
!:      lda joy
        lsr
        bcc !+
        lda #0                          // omhoog
        sec
        sbc snel
        sta dy
!:      lda joy
        and #2
        beq !+
        lda snel
        sta dy
!:      lda joy
        and #4
        beq !+
        lda #0                          // links
        sec
        sbc snel
        sta dx
        lda #$ff
        sta dx + 1
!:      lda joy
        and #8
        beq muis
        lda snel
        sta dx
muis:   // de 1351: de potmeters tellen in bits 1-6; beide $ff = geen muis
        lda $d419
        and $d41a
        cmp #$ff
        beq klaar
        lda $d419
        lsr
        and #$3f
        tax
        lda muis_oud
        bmi eerste
        txa
        sec
        sbc muis_oud
        and #$3f
        cmp #$20
        bcc !+
        ora #$c0                        // negatief
!:      asl
        sta ZP3
        stx muis_oud
        lda $d41a
        lsr
        and #$3f
        tax
        sec
        sbc muis_oud_y
        and #$3f
        cmp #$20
        bcc !+
        ora #$c0
!:      asl
        stx muis_oud_y
        eor #$ff                        // de muis telt omhoog, het scherm omlaag
        clc
        adc #1
        clc
        adc dy
        sta dy
        lda ZP3
        clc
        adc dx
        sta dx
        lda ZP3
        bpl klaar
        lda #$ff
        sta dx + 1
klaar:  rts
eerste: stx muis_oud
        lda $d41a
        lsr
        and #$3f
        sta muis_oud_y
        rts
}

// ---- de pijl -------------------------------------------------------------------------------------------------------
pijl_zetten: {
        lda pijl_x                      // x += dx (16 bits), binnen 0-319
        clc
        adc dx
        sta pijl_x
        lda pijl_x + 1
        adc dx + 1
        sta pijl_x + 1
        bpl !+
        lda #0
        sta pijl_x
        sta pijl_x + 1
!:      lda pijl_x + 1
        beq !+
        lda pijl_x
        cmp #<316
        bcc !+
        lda #<316
        sta pijl_x
!:      lda dy                          // y += dy, binnen 0-196
        bmi omhoog
        clc
        adc pijl_y
        cmp #197
        bcc zet
        lda #196
        jmp zet
omhoog: clc
        adc pijl_y
        bcs zet
        lda #0
zet:    sta pijl_y
        lda pijl_x                      // de cursor van het spel (sprite 0): het midden op de plek
        clc
        adc #24 - CURSOR_MIDDEN_X
        sta $d000
        lda pijl_x + 1
        adc #0
        and #1
        sta ZP3
        lda $d010
        and #%11111110
        ora ZP3
        sta $d010
        lda pijl_y
        clc
        adc #50 - CURSOR_MIDDEN_Y
        sta $d001
        lda beeld                       // de kleur wisselt elke 4 beelden
        lsr
        lsr
        and #7
        tax
        lda cursor_kleuren,x
        sta $d027
        rts
}

// ---- welke vlag wijst de pijl aan? -----------------------------------------------------------------------------------
aanwijzen: {
        lda gekozen
        bpl klaar                       // al gekozen: niets meer
        ldx #$ff
        lda pijl_y
        cmp #VLAG_Y1
        bcc gevonden
        cmp #183                        // tot onder het bordje met het cijfer
        bcs gevonden
        lda pijl_x + 1                  // x / 2 (mc-pixels)
        lsr
        lda pijl_x
        ror
        sta ZP3
        ldx #3
!:      lda ZP3
        cmp vlag_x1,x
        bcc volgende
        cmp vlag_x2,x
        bcc gevonden
        beq gevonden
volgende:
        dex
        bpl !-
gevonden:
        cpx wijst
        beq zelfde
        stx wijst
        cpx #$ff
        beq zelfde
        lda zinnen_wijs_lo,x            // een andere vlag: hij zegt er iets over, in die taal
        ldy zinnen_wijs_hi,x
        jsr zeg
        lda #0
        sta wacht_taal_teller
        jsr piep
zelfde: lda klik
        beq geen_klik
        ldx wijst
        bmi geen_klik
        stx wijst_toets
        jmp kies
geen_klik:
        lda wijst                       // niemand wijst iets aan: om de zoveel tijd de vraag in de volgende taal
        bpl klaar
        inc wacht_taal_teller
        lda wacht_taal_teller
        cmp #PAUZE
        bcc klaar
        lda #0
        sta wacht_taal_teller
        inc wacht_taal
        lda wacht_taal
        and #3
        sta wacht_taal
        jmp nieuwe_wachtzin
klaar:  rts
}

nieuwe_wachtzin: {
        ldx wacht_taal
        lda zinnen_wacht_lo,x
        ldy zinnen_wacht_hi,x
        jmp zeg
}

// kies: taal wijst_toets is gekozen (van een toets of een klik)
kies: {
        lda gekozen
        bpl klaar
        ldx wijst_toets
        stx gekozen
        stx wijst
        lda zinnen_kies_lo,x
        ldy zinnen_kies_hi,x
        jsr zeg
        lda #NA_KIEZEN
        sta nog
        sta praat
        jsr deuntje
klaar:  rts
}

// ---- de ballon: zeg (A/Y = een zin: x1, n1, tekens, x2, n2, tekens) ---------------------------------------------------
zeg: {
        sta ZP1
        sty ZP1 + 1
        // het tekstvak leeg: elke rij vakjes 26 x 8 bytes $ff (wit)
        ldx #0
rij:    lda vak_lo,x
        sta ZP2
        lda vak_hi,x
        sta ZP2 + 1
        ldy #(TEKST_X2 - TEKST_X1 + 1) * 8 - 1
        lda #$ff
!:      sta (ZP2),y
        dey
        cpy #$ff
        bne !-
        inx
        cpx #3
        bne rij
        lda #0                          // regel 1, dan regel 2
        sta regel
volgende_regel:
        ldy #0
        lda (ZP1),y                     // x (vakje)
        sta tx
        iny
        lda (ZP1),y                     // aantal tekens
        sta tn
        lda ZP1                         // ZP1 naar het eerste teken
        clc
        adc #2
        sta ZP1
        bcc !+
        inc ZP1 + 1
!:      lda tn
        bne teken
        jmp regel_klaar
teken:  ldy #0
        lda (ZP1),y                     // het teken: font + 10 * teken
        sta ZP3
        lda #0
        sta ZP3 + 1
        asl ZP3                         // * 2
        rol ZP3 + 1
        lda ZP3
        ldx ZP3 + 1
        asl ZP3                         // * 8
        rol ZP3 + 1
        asl ZP3
        rol ZP3 + 1
        clc
        adc ZP3                         // * 2 + * 8
        sta ZP3
        txa
        adc ZP3 + 1
        sta ZP3 + 1
        lda ZP3
        clc
        adc #<font
        sta ZP3
        lda ZP3 + 1
        adc #>font
        sta ZP3 + 1
        lda tx                          // x * 8 (16 bits) in tx8
        asl
        sta tx8
        lda #0
        rol
        sta tx8 + 1
        asl tx8
        rol tx8 + 1
        asl tx8
        rol tx8 + 1
        ldx regel                       // 10 rijen: de rij-adressen van deze regel uit de tabel
        lda regel_begin,x
        tax
        ldy #0
rijen:  lda rij_lo,x
        clc
        adc tx8
        sta ZP2
        lda rij_hi,x
        adc tx8 + 1
        sta ZP2 + 1
        lda (ZP3),y
        sty ZP3 - 0 + 4                 // (bewaren: ZP3+4 = $06)
        ldy #0
        sta (ZP2),y
        ldy ZP3 + 4
        iny
        inx
        cpy #10
        bne rijen
        inc tx
        lda ZP1
        clc
        adc #1
        sta ZP1
        bcc !+
        inc ZP1 + 1
!:      dec tn
        beq regel_klaar
        jmp teken
regel_klaar:
        inc regel
        lda regel
        cmp #2
        beq !+
        jmp volgende_regel
!:      lda #60                         // hij praat
        cmp praat
        bcc !+
        sta praat
!:      rts
}

// ---- de ogen: pupillen naar de pijl, en af en toe knipperen -----------------------------------------------------------
ogen: {
        // dx: -3 .. +3 naar waar de pijl is (t.o.v. het midden tussen de ogen)
        ldx #0
        lda pijl_x + 1
        bne rechts_ver
        lda pijl_x
        cmp #OOG_L_X + OOG_AFSTAND / 2 + 100
        bcs rechts_ver
        cmp #OOG_L_X + OOG_AFSTAND / 2 + 16
        bcs rechts
        cmp #OOG_L_X + OOG_AFSTAND / 2 - 16
        bcs y_
        cmp #OOG_L_X + OOG_AFSTAND / 2 - 30
        bcs links
        ldx #$fd
        jmp y_
links:  ldx #$fe
        jmp y_
rechts: ldx #2
        jmp y_
rechts_ver:
        ldx #3
y_:     stx ZP3
        ldy #0
        lda pijl_y
        cmp #OOG_Y - 50
        bcs !+
        ldy #$fd
        jmp zet
!:      cmp #OOG_Y - 12
        bcs !+
        ldy #$fe
        jmp zet
!:      cmp #OOG_Y + 20
        bcc zet
        ldy #2
zet:    tya
        clc
        adc #OOG_Y - 2 + 50
        sta $d005
        lda ZP3
        clc
        adc #OOG_L_X - 2 + 24
        sta $d004
        // knipperen
        dec knipper
        bne !+
        lda $d012                       // de volgende keer over 100-227 beelden
        eor beeld
        and #$7f
        clc
        adc #100
        sta knipper
        lda #7
        sta dicht
!:      lda dicht
        beq open
        dec dicht
        lda $d015                       // dicht: geen pupillen, het geel wordt huid
        and #%11111011
        sta $d015
        ldx #0
        lda #HUID
        jmp effect_kleur
open:   lda $d015
        ora #%00000100
        sta $d015
        ldx #0
        lda #OOG
        jmp effect_kleur
}

// ---- de mond: open en dicht zolang hij praat --------------------------------------------------------------------------
mond: {
        lda praat
        beq dicht
        dec praat
        and #%00000100
        beq dicht
        ldx #1
        lda #MOND_OPEN
        jmp effect_kleur
dicht:  ldx #1
        lda #HUID
        jmp effect_kleur
}

// ---- de randen om de vlaggen: de aangewezen (of gekozen) vlag knippert geel/wit ------------------------------------
randen: {
        ldx #3
lus:    stx ZP3 + 2
        lda #KLEUR_RAND
        cpx wijst
        bne !+
        lda beeld
        and #%00001000
        beq geel
        lda #1
        bne !+
geel:   lda #7
!:      pha
        txa
        clc
        adc #2
        tax
        pla
        jsr effect_kleur
        ldx ZP3 + 2
        dex
        bpl lus
        rts
}

// effect_kleur: effect X (0 ogen, 1 mond, 2-5 de randen) krijgt kleur A
effect_kleur: {
        sta kleur
        asl
        asl
        asl
        asl
        sta kleur_hoog
        lda effect_lo,x
        sta ZP2
        lda effect_hi,x
        sta ZP2 + 1
        ldy #0
        lda (ZP2),y
        beq klaar
        sta aantal
        inc ZP2
        bne lus
        inc ZP2 + 1
lus:    ldy #0
        lda (ZP2),y
        sta ZP1
        iny
        lda (ZP2),y
        sta ZP1 + 1
        iny
        lda (ZP2),y                     // 0 hoog, 1 laag, 2 kleur-RAM
        ldy #0
        cmp #1
        beq laag
        bcs kram
        lda (ZP1),y                     // hoog nibble
        and #$0f
        ora kleur_hoog
        sta (ZP1),y
        jmp verder
laag:   lda (ZP1),y
        and #$f0
        ora kleur
        sta (ZP1),y
        jmp verder
kram:   lda kleur
        sta (ZP1),y
verder: lda ZP2
        clc
        adc #3
        sta ZP2
        bcc !+
        inc ZP2 + 1
!:      dec aantal
        bne lus
klaar:  rts
}

// ---- geluid: een piepje bij aanwijzen, een deuntje bij kiezen ---------------------------------------------------------
piep: {
        lda #<piep_noten
        ldy #>piep_noten
        jmp speel
}
deuntje: {
        lda #<deuntje_noten
        ldy #>deuntje_noten
        jmp speel
}
speel: {
        sta noot
        sty noot + 1
        lda #1
        sta noot_tijd
        rts
}
// elk beeld: de volgende noot als de tijd om is. Een noot: frequentie hoog, lengte (beelden); lengte 0 = einde
geluid: {
        lda noot_tijd
        beq klaar
        dec noot_tijd
        bne klaar
        lda #$40                        // gate uit (pulsgolf)
        sta $d404
        lda noot
        sta ZP1
        lda noot + 1
        sta ZP1 + 1
        ldy #1
        lda (ZP1),y
        beq klaar
        sta noot_tijd
        dey
        lda (ZP1),y
        sta $d401
        lda #0
        sta $d400
        lda #$08
        sta $d403                       // pulsbreedte 50%
        lda #$09
        sta $d405                       // aanslag snel, verval kort
        lda #$00
        sta $d406
        lda #$41                        // puls, gate aan
        sta $d404
        lda noot
        clc
        adc #2
        sta noot
        bcc klaar
        inc noot + 1
klaar:  rts
}
piep_noten:    .byte $30, 4, 0, 0
deuntje_noten: .byte $22, 6, $2b, 6, $33, 6, $44, 14, 0, 0

// ---- tabellen ------------------------------------------------------------------------------------------------------
// de drie rijen vakjes van het tekstvak (bitmap-adres van vakje TEKST_X1)
vak_lo: .fill 3, <(BITMAP + (TEKST_Y1 / 8 + i) * 320 + TEKST_X1 * 8)
vak_hi: .fill 3, >(BITMAP + (TEKST_Y1 / 8 + i) * 320 + TEKST_X1 * 8)
// per pixelrij van de twee regels het bitmap-adres van vakje 0
rij_lo: .fill 10, <(BITMAP + ((REGEL1_Y + i) >> 3) * 320 + ((REGEL1_Y + i) & 7))
        .fill 10, <(BITMAP + ((REGEL2_Y + i) >> 3) * 320 + ((REGEL2_Y + i) & 7))
rij_hi: .fill 10, >(BITMAP + ((REGEL1_Y + i) >> 3) * 320 + ((REGEL1_Y + i) & 7))
        .fill 10, >(BITMAP + ((REGEL2_Y + i) >> 3) * 320 + ((REGEL2_Y + i) & 7))
regel_begin: .byte 0, 10

beeld:      .byte 0
gekozen:    .byte $ff
wijst:      .byte $ff
wijst_toets: .byte 0
nog:        .byte 0
praat:      .byte 0
knipper:    .byte 0
dicht:      .byte 0
wacht_taal: .byte 0
wacht_taal_teller: .byte 0
pijl_x:     .word 0
pijl_y:     .byte 0
dx:         .word 0
dy:         .byte 0
klik:       .byte 0
joy:        .byte 0
poort1:     .byte 0
vuur_oud:   .byte 0
snel:       .byte 1
muis_oud:   .byte $ff
muis_oud_y: .byte 0
regel:      .byte 0
tx:         .byte 0
tn:         .byte 0
tx8:        .word 0
kleur:      .byte 0
kleur_hoog: .byte 0
aantal:     .byte 0
noot:       .word 0
noot_tijd:  .byte 0
