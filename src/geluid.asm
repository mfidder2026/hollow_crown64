// geluid.asm — de SID (§9, hoofdstuk 9/10). Nu alleen: alles stil (vóór het laden: geen hangende toon).

.segment Code
// geluid_stil: alle drie de stemmen uit en het volume op 0
geluid_stil:
        ldx #$18
        lda #0
!:      sta $d400,x
        dex
        bpl !-
        rts
