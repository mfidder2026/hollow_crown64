// hollowcrown.asm - Eerste werkende versie
.encoding "screencode_upper"
.var pic_dawn = LoadBinary("dawnhaven.kla", BF_KOALA)
        BasicUpstart2(start)

.zp {
        px:        .byte 0
        py:        .byte 0
        scr:       .byte 0
        mir_x:     .byte 0
        mir_y:     .byte 0
        dlg:       .byte 0
}

*=$0812 "Code"
start:  sei
        cli
        ldx #0
        stx $c6
        stx scr
        stx dlg
        lda #$88
        sta px
        lda #$e0
        sta py
        lda #$40
        sta mir_x
        lda #$c0
        sta mir_y
        lda #$00
        sta scr
        jmp scr_dawn

// ========= SCREEN 0: DAWNHAVEN =========
scr_dawn:
        lda #pic_dawn.getBackgroundColor()
        sta $d021
        lda #$38
        sta $d018
        lda #$d8
        sta $d016
        lda #$3b
        sta $d011
        ldx #0
!cl:
        .for (var i = 0; i < 4; i++) {
            lda kleurRam + i * $100,x
            sta $d800 + i * $100,x
        }
        inx
        bne !cl-
        ldx #0
        txa
        asl
        tay
        lda px
        sta $d000,y
        lda py
        sta $d001,y
        lda #$0f
        sta $d027
        lda #3
        sta $d025
        lda #14
        sta $d026
        lda #$c0
        sta $0ff8
        lda #$01
        sta $d015
        ldx #0
!txt_loop:
        lda txt_dawn,x
        beq !txt_done++
        sta $0400+20*40+10,x
        inx
        cpx #27
        bne !txt_loop-
!txt_done++:
        ldx #0
!col_loop:
        lda $d800+20*40+10,x
        beq !col_done+
        sta $d800+20*40+10,x
        inx
        cpx #27
        bne !col_loop-
!col_done+:
        jmp dawn_loop

dawn_loop:
        ldx px
        stx $d000
        ldx py
        stx $d001
        ldx px
        lsr
        lsr
        lsr
        lsr
        lsr
        lsr
        sta $d010
        lda $c6
        beq !wn+
        sta $c6
        lda $0277
        and #$0f
        cmp #$08
        beq to_herb
        cmp #$10
        beq to_bos
        jmp dawn_loop
!wn+:
        jmp dawn_loop

to_herb:
        lda #$01
        sta scr
        lda #$1b
        sta $d011
        jmp scr_herb

to_bos:
        lda #$02
        sta scr
        lda #$1b
        sta $d011
        jmp scr_bos

// ========= SCREEN 1: HERBERG =========
scr_herb:
        lda #$00
        sta $d021
        lda #$1b
        sta $d011
        lda #$08
        sta $d016
        lda #$17
        sta $d018
        ldx #0
!htxt_loop:
        lda txt_herb,x
        beq !htxt_done+
        sta $0400+2*40+12,x
        inx
        cpx #7
        bne !htxt_loop-
!htxt_done+:
        ldx #2
        txa
        asl
        tay
        lda mir_x
        sta $d002,y
        lda mir_y
        sta $d003,y
        lda #$0f
        sta $d029
        lda #2
        sta $d025
        lda #4
        sta $d026
        lda #$c1
        sta $0ffa
        lda #$04
        sta $d015
        lda dlg
        beq !nodlg+
        cmp #$01
        beq d1_1
        cmp #$02
        beq d2_1
        cmp #$03
        beq d3_1
        jmp !nodlg+
d1_1:
        ldx #0
d1_1_loop:
        lda txt_d1,x
        beq d1_1_done+
        sta $0400+10*40+10,x
        inx
        cpx #14
        bne d1_1_loop-
d1_1_done+:
        ldx #0
d1_1c_loop:
        lda $d800+10*40+10,x
        beq d1_1c_done+
        sta $d800+10*40+10,x
        inx
        cpx #14
        bne d1_1c_loop-
d1_1c_done+:
        jmp !nodlg+
d2_1:
        ldx #0
d2_1_loop:
        lda txt_d2,x
        beq d2_1_done+
        sta $0400+12*40+8,x
        inx
        cpx #22
        bne d2_1_loop-
d2_1_done+:
        ldx #0
d2_1c_loop:
        lda $d800+12*40+8,x
        beq d2_1c_done+
        sta $d800+12*40+8,x
        inx
        cpx #22
        bne d2_1c_loop-
d2_1c_done+:
        jmp !nodlg+
d3_1:
        ldx #0
d3_1_loop:
        lda txt_d3,x
        beq d3_1_done+
        sta $0400+14*40+10,x
        inx
        cpx #15
        bne d3_1_loop-
d3_1_done+:
        ldx #0
d3_1c_loop:
        lda $d800+14*40+10,x
        beq d3_1c_done+
        sta $d800+14*40+10,x
        inx
        cpx #15
        bne d3_1c_loop-
d3_1c_done+:
        jmp !nodlg+
!nodlg+:
        ldx #0
!prompt_loop:
        lda txt_prompt,x
        beq !prompt_done+
        sta $0400+22*40+10,x
        inx
        cpx #17
        bne !prompt_loop-
!prompt_done+:
        ldx #0
!blink_loop:
        lda $d800+22*40+10,x
        beq !blink_done+
        lda $a2
        and #$10
        beq !blink_white+
        lda #$06
        jmp !blink_store+
!blink_white+:
        lda #$01
!blink_store+:
        sta $d800+22*40+10,x
        inx
        cpx #17
        bne !blink_loop-
!blink_done+:
        jmp herb_loop

herb_loop:
        ldx mir_x
        stx $d002
        ldx mir_y
        stx $d003
        ldx mir_x
        lsr
        lsr
        lsr
        lsr
        lsr
        lsr
        sta $d011
        lda $c6
        beq !wn+2
        sta $c6
        lda $0277
        and #$0f
        cmp #$08
        beq !ka+
        cmp #$10
        beq !kb+
        jmp herb_loop
!ka+:
        lda dlg
        inc dlg
        cmp #$04
        beq !rdlg+
        jmp herb_loop
!kb+:
        lda #$00
        sta scr
        lda #$3b
        sta $d011
        jmp scr_dawn
!rdlg+:
        stx dlg
        jmp herb_loop
!wn+2:
        jmp herb_loop

// ========= SCREEN 2: BOS =========
scr_bos:
        lda #$00
        sta $d021
        lda #$1b
        sta $d011
        lda #$08
        sta $d016
        lda #$17
        sta $d018
        ldx #0
!bt_loop:
        lda txt_bos,x
        beq !bt_done+
        sta $0400+2*40+10,x
        inx
        cpx #13
        bne !bt_loop-
!bt_done+:
        ldx #0
!bp_loop:
        lda txt_ret,x
        beq !bp_done+
        sta $0400+20*40+12,x
        inx
        cpx #17
        bne !bp_loop-
!bp_done+:
        ldx #0
!bc_loop:
        lda $d800+20*40+12,x
        beq !bc_done+
        sta $d800+20*40+12,x
        inx
        cpx #17
        bne !bc_loop-
!bc_done+:
        jmp bos_loop

bos_loop:
        lda $c6
        beq !wn+3
        sta $c6
        lda $0277
        and #$0f
        cmp #$08
        beq !todb+
        jmp bos_loop
!todb+:
        lda #$00
        sta scr
        lda #$3b
        sta $d011
        jmp scr_dawn
!wn+3:
        jmp bos_loop

// ================ DATA ================
*=$0c00 "Scherm"
        .fill pic_dawn.getScreenRamSize(), pic_dawn.getScreenRam(i)
*=$1c00 "KleurBron"
kleurRam:
        .fill pic_dawn.getColorRamSize(), pic_dawn.getColorRam(i)
*=$2000 "Bitmap"
        .fill pic_dawn.getBitmapSize(), pic_dawn.getBitmap(i)
*=$3000 "Sprites"
        .import binary "sprites.bin"
*=$3040 "Mira"
        .import binary "mira_sprites.bin"

txt_dawn: .text "Druk op A=herberg, B=bos"
          .byte 0

txt_herb: .text "HERBERG"
          .byte 0

txt_d1: .text "HALLO ELDRIC"
        .byte 0

txt_d2: .text "DE KONING IS VERDWENEN"
        .byte 0

txt_d3: .text "GA NAAR HET BOS"
        .byte 0

txt_prompt: .text "DRUK OP EEN TOETS"
            .byte 0

txt_bos: .text "DUISTERWoud"
         .byte 0

txt_ret: .text "DRUK OP EEN TOETS"
         .byte 0
