// hollowcrown.asm — Hollow Crown: Eldric loopt door Dawnhaven, Mira wacht in de herberg.
// Bouw: ./build.sh hollowcrown.asm   (de sprites: python3 sprites_hc.py -> sprites_hc.asm)
// De vorige versie staat in hollowcrown_oud.asm.
//
// Besturing: joystick in poort 2 of W A S D = lopen, H = herberg, B = bos, SPATIE = verder / terug.
//
// Geheugen (VIC-bank 0, $0000-$3fff):
//   $0400-$07e7  tekstscherm (herberg, bos)       $0840-$093f  4 sprite-vakken die de VIC toont
//   $0c00-$0fe7  kleuren van het Koala-plaatje    $2000-$3f3f  bitmap van het plaatje
//   $1c00-$1fe7  bron voor kleur-RAM ($d800)      $4000-       code, daarna de sprites van sprites_hc.asm
// De sprites van sprites_hc.asm staan buiten het zicht van de VIC; de pose die Eldric nu heeft wordt naar
// zijn twee vakken gekopieerd (128 bytes, alleen als de pose verandert).
.encoding "screencode_upper"
.var pic_dawn = LoadBinary("../../data/dawnhaven.kla", BF_KOALA)

.const VAK_ELDRIC = $0840               // boven, onder op $0880
.const VAK_MIRA   = $08c0               // boven, onder op $0900
.const PTR_TEKST  = $07f8               // sprite-pointers bij scherm $0400
.const PTR_BITMAP = $0ff8               // sprite-pointers bij scherm $0c00
.const SCHERM     = $0400

// richtingen
.const VOOR = 0
.const RUG = 1
.const RECHTS = 2
.const LINKS = 3

// toetsen zoals de KERNAL ze in $c5 zet (64 = geen toets)
.const K_W = 9
.const K_A = 10
.const K_S = 13
.const K_D = 18
.const K_H = 29
.const K_B = 28
.const K_SPATIE = 60
.const K_GEEN = 64

.const bron = $fb                       // 2 bytes, vrij voor programma's
.const doel = $fd

        BasicUpstart2(start)

        *=$4000 "Code"
start:  lda #0
        sta $d020
        lda #$ff
        sta vorige_toets
        lda #160
        sta px
        lda #150
        sta py
        lda #VOOR
        sta richting
        lda #$ff
        sta pose_nu
        // de twee vakken van Mira vullen (zij staat stil)
        lda #<mira_boven
        sta bron
        lda #>mira_boven
        sta bron+1
        lda #<VAK_MIRA
        sta doel
        lda #>VAK_MIRA
        sta doel+1
        jsr kopieer128
        // gedeelde sprite-kleuren en multicolor voor sprite 0-3
        lda #HC_MC1
        sta $d025
        lda #HC_MC2
        sta $d026
        lda #%00001111
        sta $d01c
        lda #0
        sta $d017
        sta $d01d
        sta $d010
        sta $d01b               // sprites voor het plaatje
        lda #eldric_voor_kb
        sta $d027
        lda #eldric_voor_ko
        sta $d028
        lda #mira_kb
        sta $d029
        lda #mira_ko
        sta $d02a
        jmp scr_dawn

// ========= SCHERM 0: DAWNHAVEN (het Koala-plaatje) =========
scr_dawn:
        lda #0
        sta $d015
        lda #pic_dawn.getBackgroundColor()
        sta $d021
        ldx #0
!cl:
        .for (var i = 0; i < 4; i++) {
            lda kleurRam + i * $100,x
            sta $d800 + i * $100,x
        }
        inx
        bne !cl-
        lda #$38                // scherm $0c00, bitmap $2000
        sta $d018
        lda #$d8                // multicolor
        sta $d016
        lda #$3b                // bitmap aan
        sta $d011
        lda #(VAK_ELDRIC / 64)
        sta PTR_BITMAP
        lda #(VAK_ELDRIC / 64) + 1
        sta PTR_BITMAP + 1
        lda #%00000011
        sta $d015

dawn_loop:
        jsr wacht_beeld
        jsr loop_eldric
        jsr nieuwe_toets
        cmp #K_H
        beq to_herb
        cmp #K_B
        beq to_bos
        jmp dawn_loop

to_herb:
        lda #0
        sta dlg
        jmp scr_herb
to_bos:
        jmp scr_bos

// Joystick 2 of WASD: Eldric loopt 1 pixel per beeld, kijkt in de looprichting en zet een stap per 8 beelden.
loop_eldric:
        lda #0
        sta beweegt
        lda $dc00
        sta joy
        lda $c5
        sta toets_nu
        // omhoog
        lda joy
        and #1
        beq !op+
        lda toets_nu
        cmp #K_W
        bne !geenop+
!op:    lda py
        cmp #52
        bcc !geenop+
        dec py
        lda #RUG
        sta richting
        inc beweegt
!geenop:
        lda joy
        and #2
        beq !neer+
        lda toets_nu
        cmp #K_S
        bne !geenneer+
!neer:  lda py
        cmp #206
        bcs !geenneer+
        inc py
        lda #VOOR
        sta richting
        inc beweegt
!geenneer:
        lda joy
        and #4
        beq !links+
        lda toets_nu
        cmp #K_A
        bne !geenlinks+
!links: lda px
        cmp #26
        bcc !geenlinks+
        dec px
        lda #LINKS
        sta richting
        inc beweegt
!geenlinks:
        lda joy
        and #8
        beq !rechts+
        lda toets_nu
        cmp #K_D
        bne !geenrechts+
!rechts:
        lda px
        cmp #230
        bcs !geenrechts+
        inc px
        lda #RECHTS
        sta richting
        inc beweegt
!geenrechts:
        // stap: 0 staan, 1 voet, 0 staan, 2 andere voet
        lda beweegt
        bne !+
        lda #0
        sta stap
        sta teller
        jmp !pose+
!:      inc teller
        lda teller
        and #7
        bne !pose+
        inc stap
!pose:  lda stap
        and #3
        tax
        lda stappen,x
        sta frame
        lda richting            // pose = richting * 3 + frame
        asl
        clc
        adc richting
        adc frame
        cmp pose_nu
        beq !zet+
        sta pose_nu
        tax
        lda pose_lo,x
        sta bron
        lda pose_hi,x
        sta bron+1
        lda #<VAK_ELDRIC
        sta doel
        lda #>VAK_ELDRIC
        sta doel+1
        jsr kopieer128
!zet:   lda px
        sta $d000
        sta $d002
        lda py
        sta $d001
        clc
        adc #21
        sta $d003
        rts

stappen: .byte 0, 1, 0, 2

// ========= SCHERM 1: DE HERBERG (tekst) =========
scr_herb:
        jsr tekstscherm
        lda #9                  // bruin hout: op zwart verdwijnen het zwarte haar en de omlijning
        sta $d021
        ldx #<txt_herb
        ldy #>txt_herb
        lda #2
        jsr print_regel
        // Eldric links naar rechts kijkend, Mira rechts
        lda #RECHTS * 3
        jsr zet_pose
        lda #(VAK_ELDRIC / 64)
        sta PTR_TEKST
        lda #(VAK_ELDRIC / 64) + 1
        sta PTR_TEKST + 1
        lda #(VAK_MIRA / 64)
        sta PTR_TEKST + 2
        lda #(VAK_MIRA / 64) + 1
        sta PTR_TEKST + 3
        lda #120
        sta $d000
        sta $d002
        lda #200
        sta $d004
        sta $d006
        lda #110
        sta $d001
        sta $d005
        lda #131
        sta $d003
        sta $d007
        lda #%00001111
        sta $d015
        ldx #<txt_prompt
        ldy #>txt_prompt
        lda #22
        jsr print_regel

herb_loop:
        jsr wacht_beeld
        jsr nieuwe_toets
        cmp #K_SPATIE
        bne herb_loop
        lda dlg
        cmp #3
        beq !terug+
        inc dlg
        asl
        tax
        lda dialoog,x
        pha
        lda dialoog+1,x
        tay
        pla
        tax
        lda dlg
        asl
        clc
        adc #10                 // zin 1, 2, 3 op regel 12, 14, 16
        jsr print_regel
        lda dlg
        cmp #3
        bne herb_loop
        ldx #<txt_terug
        ldy #>txt_terug
        lda #22
        jsr print_regel
        jmp herb_loop
!terug: jmp scr_dawn

dialoog: .word txt_d1, txt_d2, txt_d3

// ========= SCHERM 2: HET BOS (tekst) =========
scr_bos:
        jsr tekstscherm
        lda #0
        sta $d015
        ldx #<txt_bos
        ldy #>txt_bos
        lda #2
        jsr print_regel
        ldx #<txt_terug
        ldy #>txt_terug
        lda #20
        jsr print_regel
bos_loop:
        jsr wacht_beeld
        jsr nieuwe_toets
        cmp #K_SPATIE
        bne bos_loop
        jmp scr_dawn

// ========= hulproutines =========
// tekstmodus, scherm $0400 leeg (wit op zwart)
tekstscherm:
        lda #0
        sta $d015
        sta $d021
        lda #$1b
        sta $d011
        lda #$c8
        sta $d016
        lda #$15                // scherm $0400, hoofdletters
        sta $d018
        ldx #0
!l:     lda #$20
        sta SCHERM,x
        sta SCHERM + $100,x
        sta SCHERM + $200,x
        sta SCHERM + $2e8,x
        lda #1
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $dae8,x
        inx
        bne !l-
        rts

// tekst op adres X (laag) / Y (hoog), eindigt met 0, gecentreerd op regel A
print_regel:
        stx bron
        sty bron+1
        tax
        lda regel_lo,x
        sta doel
        lda regel_hi,x
        sta doel+1
        ldy #0                  // lengte tellen
!n:     lda (bron),y
        beq !+
        iny
        bne !n-
!:      tya
        eor #$ff
        sec
        adc #40                 // 40 - lengte
        lsr
        clc
        adc doel
        sta doel
        bcc !+
        inc doel+1
!:      ldy #0
!l:     lda (bron),y
        beq !klaar+
        sta (doel),y
        iny
        bne !l-
!klaar: rts

regel_lo: .fill 25, <(SCHERM + i * 40)
regel_hi: .fill 25, >(SCHERM + i * 40)

// pose A (richting * 3 + frame) in de vakken van Eldric zetten
zet_pose:
        sta pose_nu
        tax
        lda pose_lo,x
        sta bron
        lda pose_hi,x
        sta bron+1
        lda #<VAK_ELDRIC
        sta doel
        lda #>VAK_ELDRIC
        sta doel+1
        // valt door naar kopieer128

// 128 bytes van (bron) naar (doel): de bovenste en de onderste sprite
kopieer128:
        ldy #127
!l:     lda (bron),y
        sta (doel),y
        dey
        bpl !l-
        rts

// wacht tot de straal onder het beeld is (één keer per beeld)
wacht_beeld:
!w:     lda $d012
        cmp #250
        bne !w-
!w2:    lda $d012
        cmp #250
        beq !w2-
        rts

// A = een toets die net is ingedrukt (anders K_GEEN); de toetsenbordbuffer blijft leeg
nieuwe_toets:
        lda #0
        sta $c6
        lda $c5
        cmp vorige_toets
        beq !zelfde+
        sta vorige_toets
        rts
!zelfde:
        lda #K_GEEN
        rts

// de 12 poses van Eldric: per richting staan, voet, andere voet
pose_lo: .byte <eldric_voor_boven,   <eldric_voor_l_boven,   <eldric_voor_r_boven
         .byte <eldric_rug_boven,    <eldric_rug_l_boven,    <eldric_rug_r_boven
         .byte <eldric_rechts_boven, <eldric_rechts_1_boven, <eldric_rechts_2_boven
         .byte <eldric_links_boven,  <eldric_links_1_boven,  <eldric_links_2_boven
pose_hi: .byte >eldric_voor_boven,   >eldric_voor_l_boven,   >eldric_voor_r_boven
         .byte >eldric_rug_boven,    >eldric_rug_l_boven,    >eldric_rug_r_boven
         .byte >eldric_rechts_boven, >eldric_rechts_1_boven, >eldric_rechts_2_boven
         .byte >eldric_links_boven,  >eldric_links_1_boven,  >eldric_links_2_boven

px:           .byte 0
py:           .byte 0
richting:     .byte 0
stap:         .byte 0
frame:        .byte 0
teller:       .byte 0
beweegt:      .byte 0
pose_nu:      .byte 0
joy:          .byte 0
toets_nu:     .byte 0
vorige_toets: .byte 0
dlg:          .byte 0

txt_herb:   .text "DE HERBERG"
            .byte 0
txt_d1:     .text "MIRA: HALLO ELDRIC."
            .byte 0
txt_d2:     .text "DE KONING IS VERDWENEN."
            .byte 0
txt_d3:     .text "GA NAAR HET DUISTERWOUD."
            .byte 0
txt_prompt: .text "SPATIE: PRATEN MET MIRA"
            .byte 0
txt_terug:  .text "SPATIE: TERUG NAAR HET DORP"
            .byte 0
txt_bos:    .text "HET DUISTERWOUD"
            .byte 0

        .align 64
#import "../../src/sprites_hc.asm"

// ================ HET PLAATJE ================
*=$0c00 "Scherm"
        .fill pic_dawn.getScreenRamSize(), pic_dawn.getScreenRam(i)
*=$1c00 "KleurBron"
kleurRam:
        .fill pic_dawn.getColorRamSize(), pic_dawn.getColorRam(i)
*=$2000 "Bitmap"
        .fill pic_dawn.getBitmapSize(), pic_dawn.getBitmap(i)
