// figuren_toon.asm — laat de sprites uit figuren.asm zien, twee keer zo groot. Bouw: ./build.sh figuren_toon.asm
        BasicUpstart2(begin)
        *=$0810
begin:  sei
        lda #0
        sta $d020
        sta $d021
        lda #$93
        jsr $ffd2           // scherm leeg
        lda #1
        sta $d015
        sta $d017
        sta $d01d           // twee keer zo hoog en breed
        lda #$ff
        sta $d01c
        lda #figuren_mc1
        sta $d025
        lda #figuren_mc2
        sta $d026
        lda #(eldric / 64)
        sta $07f8 + 0
        lda #eldric_kleur
        sta $d027 + 0
        lda #<40
        sta $d000 + 0 * 2
        lda #120
        sta $d001 + 0 * 2
        jmp *

        *=$2000 "Sprites"
#import "figuren.asm"
