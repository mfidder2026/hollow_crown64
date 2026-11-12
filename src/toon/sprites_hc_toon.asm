// sprites_hc_toon.asm — laat de sprites uit sprites_hc.asm zien, twee keer zo groot, met lopende Eldric.
// Elke 4 seconden een andere pagina. Bouw: ./build.sh sprites_hc_toon.asm   (sprites_hc.asm komt uit sprites_hc.py)
.const PAGINAS = 3
        BasicUpstart2(begin)
        *=$0810 "Code"
begin:  jsr $e544               // scherm leeg
        sei
        lda #0
        sta $d020
        lda #5                  // groen, als gras
        sta $d021
        lda #$ff
        sta $d01c               // multicolor
        sta $d017               // dubbel hoog
        sta $d01d               // dubbel breed
        lda #HC_MC1
        sta $d025
        lda #HC_MC2
        sta $d026
        lda #0
        sta $d010
        sta pagina
        sta stap
        sta tik
        sta tel
        sta tel+1
        jsr zet_pagina
lus:    lda $d012               // wacht op een nieuw beeld
        cmp #250
        bne lus
!w:     lda $d012
        cmp #250
        beq !w-
        inc tik
        lda tik
        and #15
        bne !geenstap+
        lda stap
        clc
        adc #1
        and #3
        sta stap
!geenstap:
        inc tel
        bne !+
        inc tel+1
!:      lda tel+1               // 200 + 256*... : na 240 beelden (~5 s) de volgende pagina
        bne !volgende+
        lda tel
        cmp #240
        bcc !teken+
!volgende:
        lda #0
        sta tel
        sta tel+1
        inc pagina
        lda pagina
        cmp #PAGINAS
        bcc !+
        lda #0
        sta pagina
!:      jsr zet_pagina
!teken: jsr zet_pointers
        jmp lus

// kleuren, posities en welke sprites aan staan, voor de huidige pagina
zet_pagina:
        lda pagina
        asl
        asl
        asl
        tay                     // Y = pagina * 8
        ldx #0
!l:     lda pg_col,y
        sta $d027,x
        lda pg_x,y
        pha
        txa
        asl
        tax
        pla
        sta $d000,x
        lda pg_y,y
        sta $d001,x
        txa
        lsr
        tax
        iny
        inx
        cpx #8
        bne !l-
        ldx pagina
        lda pg_mask,x
        sta $d015
        rts

// sprite-pointers voor pagina en animatiestap: pg_ptr + (pagina * 4 + stap) * 8
zet_pointers:
        lda pagina
        asl
        asl
        clc
        adc stap
        asl
        asl
        asl
        tay
        ldx #0
!l:     lda pg_ptr,y
        sta $07f8,x
        iny
        inx
        cpx #8
        bne !l-
        rts

pagina: .byte 0
stap:   .byte 0
tik:    .byte 0
tel:    .word 0

pg_ptr:
        .byte (eldric_voor_boven / 64) & $ff, (eldric_voor_onder / 64) & $ff, (eldric_rechts_boven / 64) & $ff, (eldric_rechts_onder / 64) & $ff, (eldric_rug_boven / 64) & $ff, (eldric_rug_onder / 64) & $ff, (eldric_links_boven / 64) & $ff, (eldric_links_onder / 64) & $ff
        .byte (eldric_voor_l_boven / 64) & $ff, (eldric_voor_l_onder / 64) & $ff, (eldric_rechts_1_boven / 64) & $ff, (eldric_rechts_1_onder / 64) & $ff, (eldric_rug_l_boven / 64) & $ff, (eldric_rug_l_onder / 64) & $ff, (eldric_links_1_boven / 64) & $ff, (eldric_links_1_onder / 64) & $ff
        .byte (eldric_voor_boven / 64) & $ff, (eldric_voor_onder / 64) & $ff, (eldric_rechts_boven / 64) & $ff, (eldric_rechts_onder / 64) & $ff, (eldric_rug_boven / 64) & $ff, (eldric_rug_onder / 64) & $ff, (eldric_links_boven / 64) & $ff, (eldric_links_onder / 64) & $ff
        .byte (eldric_voor_r_boven / 64) & $ff, (eldric_voor_r_onder / 64) & $ff, (eldric_rechts_2_boven / 64) & $ff, (eldric_rechts_2_onder / 64) & $ff, (eldric_rug_r_boven / 64) & $ff, (eldric_rug_r_onder / 64) & $ff, (eldric_links_2_boven / 64) & $ff, (eldric_links_2_onder / 64) & $ff
        .byte (mira_boven / 64) & $ff, (mira_onder / 64) & $ff, (vex_boven / 64) & $ff, (vex_onder / 64) & $ff, (king_boven / 64) & $ff, (king_onder / 64) & $ff, (spook_boven / 64) & $ff, (spook_onder / 64) & $ff
        .byte (mira_boven / 64) & $ff, (mira_onder / 64) & $ff, (vex_boven / 64) & $ff, (vex_onder / 64) & $ff, (king_boven / 64) & $ff, (king_onder / 64) & $ff, (spook_boven / 64) & $ff, (spook_onder / 64) & $ff
        .byte (mira_boven / 64) & $ff, (mira_onder / 64) & $ff, (vex_boven / 64) & $ff, (vex_onder / 64) & $ff, (king_boven / 64) & $ff, (king_onder / 64) & $ff, (spook_boven / 64) & $ff, (spook_onder / 64) & $ff
        .byte (mira_boven / 64) & $ff, (mira_onder / 64) & $ff, (vex_boven / 64) & $ff, (vex_onder / 64) & $ff, (king_boven / 64) & $ff, (king_onder / 64) & $ff, (spook_boven / 64) & $ff, (spook_onder / 64) & $ff
        .byte (eldric_rechts_boven / 64) & $ff, (eldric_rechts_onder / 64) & $ff, (wolf_links / 64) & $ff, (wolf_rechts / 64) & $ff, (eldric_links_boven / 64) & $ff, (eldric_links_onder / 64) & $ff, 0, 0
        .byte (eldric_rechts_1_boven / 64) & $ff, (eldric_rechts_1_onder / 64) & $ff, (wolf_links / 64) & $ff, (wolf_rechts / 64) & $ff, (eldric_links_1_boven / 64) & $ff, (eldric_links_1_onder / 64) & $ff, 0, 0
        .byte (eldric_rechts_boven / 64) & $ff, (eldric_rechts_onder / 64) & $ff, (wolf_links / 64) & $ff, (wolf_rechts / 64) & $ff, (eldric_links_boven / 64) & $ff, (eldric_links_onder / 64) & $ff, 0, 0
        .byte (eldric_rechts_2_boven / 64) & $ff, (eldric_rechts_2_onder / 64) & $ff, (wolf_links / 64) & $ff, (wolf_rechts / 64) & $ff, (eldric_links_2_boven / 64) & $ff, (eldric_links_2_onder / 64) & $ff, 0, 0
pg_col:
        .byte eldric_voor_kb, eldric_voor_ko, eldric_rechts_kb, eldric_rechts_ko, eldric_rug_kb, eldric_rug_ko, eldric_links_kb, eldric_links_ko
        .byte mira_kb, mira_ko, vex_kb, vex_ko, king_kb, king_ko, spook_kb, spook_ko
        .byte eldric_rechts_kb, eldric_rechts_ko, wolf_k, wolf_k, eldric_links_kb, eldric_links_ko, 0, 0
pg_x:
        .byte 40, 40, 108, 108, 176, 176, 244, 244
        .byte 40, 40, 108, 108, 176, 176, 244, 244
        .byte 40, 40, 98, 146, 176, 176, 0, 0
pg_y:
        .byte 80, 122, 80, 122, 80, 122, 80, 122
        .byte 80, 122, 80, 122, 80, 122, 80, 122
        .byte 80, 122, 120, 120, 80, 122, 0, 0
pg_mask: .byte $ff, $ff, $3f

        *=$2000 "Sprites"
#import "../sprites_hc.asm"
