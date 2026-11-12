// dawnhaven_toon.asm — laat dawnhaven zien; gemaakt door c64beeld.py. Bouw: ./build.sh dawnhaven_toon.asm
.var pic = LoadBinary("../data/dawnhaven.kla", BF_KOALA)
        BasicUpstart2(begin)
        *=$0810
begin:  sei
        lda #$38
        sta $d018           // bitmap op $2000, scherm op $0c00
        lda #$d8
        sta $d016
        lda #$3b
        sta $d011           // bitmapmodus
        lda #0
        sta $d020
        lda #pic.getBackgroundColor()
        sta $d021
        ldx #0
!lus:   .for (var i = 0; i < 4; i++) {
            lda kleurRam + i * $100,x
            sta $d800 + i * $100,x
        }
        inx
        bne !lus-
        jmp *

        *=$0c00 "Scherm"
        .fill pic.getScreenRamSize(), pic.getScreenRam(i)
        *=$1c00 "Kleur-RAM"
kleurRam:
        .fill pic.getColorRamSize(), pic.getColorRam(i)
        *=$2000 "Bitmap"
        .fill pic.getBitmapSize(), pic.getBitmap(i)
