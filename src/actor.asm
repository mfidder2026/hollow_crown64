// actor.asm — Eldric (§6.5): twee multicolor-sprites boven elkaar, lopen langs een route van loopvakken.
//
// Positie = waar de voeten staan: act_x in schermpixels (0-319), act_y in kamerrijen (0-127).
// Lopen: in rechte lijnen (Bresenham), 1 pixel per beeld langs de lange as; een stap elke 8 beelden.
// Richting volgt de lange as van het stuk dat hij loopt; aan het eind blijft hij zo staan.
// Diepte: hoe hoger in de kamer (kleinere y), hoe kleiner (maat 0-3, grenzen uit SCHAAL in het script) en
// hoe trager (een kleine figuur die 1 pixel per beeld loopt, lijkt te rennen).
// Hoofdstuk 2: alleen Eldric. NPC's als actor komen in hoofdstuk 7.
//
// Sprites: 2 (boven) en 3 (onder) in sprite-vak 0 en 1. Sprite 0 is de cursor, sprite 1 de voorgrond
// (voorgrond.asm): een lager nummer komt vóór een hoger, zo staat het torentje vóór Eldric.

.const ACT_VAK        = 0               // sprite-vak van de bovenste helft; de onderste in het volgende
.const ACT_PTR        = (SPRITE_VAKKEN - SCHERM) / 64 + ACT_VAK
.const ACT_SPRITES    = %00001100       // sprite 2 en 3
.const STAP_BEELDEN   = 8
.const R_VOOR = 0
.const R_RUG = 1
.const R_RECHTS = 2
.const R_LINKS = 3

.segment Code
actor_start:
        lda #<BEGIN_X
        sta act_x
        lda #>BEGIN_X
        sta act_x + 1
        lda #BEGIN_Y
        sta act_y
        lda #BEGIN_RICHTING
        sta act_richting
        lda #0
        sta act_fase
        sta act_lopen
        lda #$ff
        sta act_pose                    // nog geen pose in de vakken
        lda #HC_MC1
        sta $d025
        lda #HC_MC2
        sta $d026
        lda #ELDRIC_KB
        sta $d029
        lda #ELDRIC_KO
        sta $d02a
        lda #ACT_PTR
        sta SPRITE_PTR + 2
        lda #ACT_PTR + 1
        sta SPRITE_PTR + 3
        lda $d01c
        ora #ACT_SPRITES                // multicolor
        sta $d01c
        lda $d01b
        and #~ACT_SPRITES               // voor de kamer (achter iets langs: hoofdstuk 8)
        sta $d01b
        lda $d015
        ora #ACT_SPRITES
        sta $d015
        jsr actor_pose
        jmp actor_plaatsen

// actor_loop_naar: loop naar (p_x, p_y), of het dichtstbijzijnde punt in een loopvak
actor_loop_naar: {
        jsr dichtstbij
        lda d_vak
        sta bfs_naar
        lda d_x
        sta doel_x
        lda d_x + 1
        sta doel_x + 1
        lda d_y
        sta doel_y
        lda act_x                       // in welk vak staat hij nu?
        sta p_x
        lda act_x + 1
        sta p_x + 1
        lda act_y
        sta p_y
        jsr vak_van_punt
        cmp #GEEN_VAK
        bne !+
        jsr dichtstbij                  // (hoort niet te gebeuren) dan het dichtstbijzijnde vak
        lda d_vak
!:      sta bfs_van
        jsr bfs
        bcc klaar                       // geen pad: blijf staan
        lda #0
        sta route_pos
        sta stap_teller
        sta stap_index                  // elke wandeling begint bij de eerste pas
        lda #1
        sta act_lopen
        jsr volgend_punt
klaar:  rts
}

// volgend_punt: het volgende punt om naartoe te lopen: de deur naar het volgende vak, of het doel
volgend_punt: {
lus:    ldx route_pos
        inx
        cpx route_lengte
        bcc deur
        lda doel_x                      // in het laatste vak: naar het doel
        sta wp_x
        lda doel_x + 1
        sta wp_x + 1
        lda doel_y
        sta wp_y
        lda #1
        sta wp_laatste
        jmp stuk
deur:   lda route,x                     // volgende vak
        tay
        dex
        lda route,x                     // huidige vak
        tax
        jsr deur_maken                  // vak VAK_DEUR = overlap
        lda act_x
        sta p_x
        lda act_x + 1
        sta p_x + 1
        lda act_y
        sta p_y
        ldx #VAK_DEUR
        jsr klem_in_vak                 // het dichtstbijzijnde punt in de deur
        lda k_x
        sta wp_x
        lda k_x + 1
        sta wp_x + 1
        lda k_y
        sta wp_y
        inc route_pos
        lda #0
        sta wp_laatste
stuk:   jsr stuk_begin
        lda seg_n                       // al op dat punt?
        ora seg_n + 1
        bne klaar
        lda wp_laatste
        beq lus
        lda #0                          // aangekomen
        sta act_lopen
klaar:  rts
}

// stuk_begin: een recht stuk van (act_x, act_y) naar (wp_x, wp_y)
stuk_begin: {
        sec                             // dx = wp_x - act_x
        lda wp_x
        sbc act_x
        sta seg_dx
        lda wp_x + 1
        sbc act_x + 1
        sta seg_dx + 1
        ldx #1
        lda seg_dx + 1                  // negatief?
        bpl !+
        ldx #$ff
        lda #0
        sec
        sbc seg_dx
        sta seg_dx
        lda #0
        sbc seg_dx + 1
        sta seg_dx + 1
!:      stx seg_sx
        lda #0
        sta seg_dy + 1
        ldx #1
        lda wp_y                        // dy = wp_y - act_y
        sec
        sbc act_y
        bcs !+
        ldx #$ff
        eor #$ff
        adc #1
!:      sta seg_dy
        stx seg_sy
        lda seg_dx                      // lange as: X als dx >= dy
        cmp seg_dy
        lda seg_dx + 1
        sbc seg_dy + 1
        lda #0
        bcs !+
        lda #1
!:      sta seg_major
        bne as_y
        lda seg_dx                      // n = dx, fout = dx / 2
        sta seg_n
        lda seg_dx + 1
        sta seg_n + 1
        jmp richting
as_y:   lda seg_dy
        sta seg_n
        lda #0
        sta seg_n + 1
richting:
        lda seg_n + 1                   // fout = n / 2
        lsr
        sta seg_fout + 1
        lda seg_n
        ror
        sta seg_fout
        lda seg_n                       // n = 0: richting blijft
        ora seg_n + 1
        beq klaar
        lda seg_major
        bne ry
        lda #R_RECHTS
        ldx seg_sx
        bpl zet
        lda #R_LINKS
        bne zet
ry:     lda #R_VOOR
        ldx seg_sy
        bpl zet
        lda #R_RUG
zet:    sta act_richting
klaar:  rts
}

// actor_beweeg: één beeld
actor_beweeg: {
        lda act_lopen
        bne loopt
        lda #0
        sta act_fase
        jmp actor_pose
loopt:  inc traag_teller                 // trager op afstand: in sommige beelden niet bewegen
        lda traag_teller
        and #7
        tax
        lda bits,x
        ldx act_maat
        and maat_tempo,x
        bne beweeg
        jmp anim
beweeg: lda seg_major
        bne y_lang
        jsr stap_x                      // lange as X
        lda seg_dy
        ldx seg_dy + 1
        jsr fout_erbij
        bcc !+
        jsr stap_y
!:      jmp verder
y_lang: jsr stap_y                      // lange as Y
        lda seg_dx
        ldx seg_dx + 1
        jsr fout_erbij
        bcc verder
        jsr stap_x
verder: lda seg_n                       // n - 1
        bne !+
        dec seg_n + 1
!:      dec seg_n
        lda seg_n
        ora seg_n + 1
        bne anim
        lda wp_laatste                  // punt bereikt
        beq !+
        lda #0
        sta act_lopen
        sta act_fase
        jmp actor_pose
!:      jsr volgend_punt
anim:   inc stap_teller
        lda stap_teller
        and #STAP_BEELDEN - 1
        bne !+
        inc stap_index
!:      lda stap_index
        and #3
        tax
        lda stappen,x
        sta act_fase
        lda act_lopen
        bne !+
        lda #0                          // net aangekomen in volgend_punt
        sta act_fase
!:      jmp actor_pose

// fout += A/X (de korte as); C = 1 als fout >= de lange as (en dan fout -= lange as)
fout_erbij:
        clc
        adc seg_fout
        sta seg_fout
        txa
        adc seg_fout + 1
        sta seg_fout + 1
        lda seg_major
        bne lang_y
        lda seg_fout                    // vergelijk met dx
        cmp seg_dx
        lda seg_fout + 1
        sbc seg_dx + 1
        bcc !+
        lda seg_fout
        sbc seg_dx
        sta seg_fout
        lda seg_fout + 1
        sbc seg_dx + 1
        sta seg_fout + 1
        sec
!:      rts
lang_y: lda seg_fout                    // vergelijk met dy
        cmp seg_dy
        lda seg_fout + 1
        sbc seg_dy + 1
        bcc !+
        lda seg_fout
        sbc seg_dy
        sta seg_fout
        lda seg_fout + 1
        sbc seg_dy + 1
        sta seg_fout + 1
        sec
!:      rts

stap_x: lda seg_sx
        bmi !+
        inc act_x
        bne klaar_x
        inc act_x + 1
        rts
!:      lda act_x
        bne !+
        dec act_x + 1
!:      dec act_x
klaar_x:
        rts

stap_y: lda seg_sy
        bmi !+
        inc act_y
        rts
!:      dec act_y
        rts
}

// actor_maat: de maat bij de diepte van de voeten: het aantal SCHAAL-grenzen waar act_y onder ligt
actor_maat: {
        ldx #0
        ldy schaal_aantal
        beq klaar
!:      lda act_y
        cmp schaal_grens - 1,y
        bcs !+
        inx
!:      dey
        bne !--
klaar:  stx act_maat
        rts
}

// schaal_laden: de SCHAAL van een kamer op (zp_ptr): aantal, dan de grenzen (aflopend)
schaal_laden:
        ldy #0
        lda (zp_ptr),y
        sta schaal_aantal
        tax
        beq !++
!:      iny
        lda (zp_ptr),y
        sta schaal_grens - 1,y
        dex
        bne !-
!:      rts

// actor_pose: de pose van nu (maat * 12 + richting * 3 + fase) in de sprite-vakken, als hij veranderd is
actor_pose: {
        jsr actor_maat
        lda act_maat                    // maat * 12 = maat * 8 + maat * 4
        asl
        asl
        sta hulp
        asl
        clc
        adc hulp
        sta hulp
        lda act_richting
        asl
        adc act_richting                // * 3 (C = 0: richting < 4)
        adc act_fase
        adc hulp
        cmp act_pose
        beq klaar
        sta act_pose
        lsr                             // pose * 128: hoog = pose / 2, laag = (pose & 1) * 128
        tax
        lda #0
        ror
        clc
        adc #<costume_eldric
        sta zp_ptr
        txa
        adc #>costume_eldric
        sta zp_ptr + 1
        ldy #127
!:      lda (zp_ptr),y
        sta SPRITE_VAKKEN + ACT_VAK * 64,y
        dey
        bpl !-
klaar:  rts
hulp:   .byte 0
}

// actor_plaatsen: sprites 2 en 3 op de plek van de voeten
actor_plaatsen:
        lda act_x                       // X = act_x + 24 - 12
        clc
        adc #12
        sta $d004
        sta $d006
        lda act_x + 1
        adc #0
        beq !+
        lda #ACT_SPRITES
!:      sta act_hulp
        lda $d010
        and #~ACT_SPRITES
        ora act_hulp
        sta $d010
        lda act_y                       // Y boven = act_y + 16 (kamer begint op pixelrij 16) + 50 - VOETEN_RIJ
        clc
        adc #16 + 50 - VOETEN_RIJ
        sta $d005
        adc #21
        sta $d007
        rts

.segment Data
act_x:        .word 0
act_y:        .byte 0
act_richting: .byte 0
act_fase:     .byte 0
act_pose:     .byte $ff
act_lopen:    .byte 0
act_hulp:     .byte 0
stap_teller:  .byte 0
stap_index:   .byte 0
stappen:      .byte 0, 1, 0, 2          // staan, voet, staan, andere voet
act_maat:     .byte 0                   // 0 = groot ... MATEN - 1 = het kleinst
traag_teller: .byte 0
maat_tempo:   .byte %11111111, %11111111, %01110111, %01010101   // per maat: in welke van 8 beelden hij beweegt
.assert "maat_tempo heeft een waarde per maat", MATEN, 4
schaal_aantal: .byte 0
schaal_grens:  .fill 3, 0
doel_x:       .word 0
doel_y:       .byte 0
route_pos:    .byte 0
wp_x:         .word 0
wp_y:         .byte 0
wp_laatste:   .byte 0
seg_dx:       .word 0
seg_dy:       .word 0
seg_sx:       .byte 0
seg_sy:       .byte 0
seg_major:    .byte 0                   // 0 = X is de lange as, 1 = Y
seg_fout:     .word 0
seg_n:        .word 0
