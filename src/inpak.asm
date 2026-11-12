// inpak.asm — uitpakker voor het RLE-formaat van tools/inpak.py:
//   $00-$7F n: n+1 letterlijke bytes;  $80-$FE n: herhaal de volgende byte n-$7E keer;  $FF: einde.

.segment Code
// uitpak: van (zp_ptr) naar (zp_ptr2). Na afloop wijst zp_ptr net voorbij het einde-teken, zodat
// een volgende uitpak het volgende stuk leest.
uitpak: {
        ldy #0
lus:    lda (zp_ptr),y
        jsr bron_verder
        cmp #$ff
        beq klaar
        cmp #$80
        bcs herhaal
        tax                             // letterlijk: n+1 bytes
        inx
!:      lda (zp_ptr),y
        sta (zp_ptr2),y
        jsr bron_verder
        jsr doel_verder
        dex
        bne !-
        jmp lus
herhaal:
        sec
        sbc #$7e                        // aantal: 2..128
        tax
        lda (zp_ptr),y
        jsr bron_verder
!:      sta (zp_ptr2),y
        jsr doel_verder
        dex
        bne !-
        jmp lus
klaar:  rts
}

bron_verder:
        inc zp_ptr
        bne !+
        inc zp_ptr + 1
!:      rts

doel_verder:
        inc zp_ptr2
        bne !+
        inc zp_ptr2 + 1
!:      rts
