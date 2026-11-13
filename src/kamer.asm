// kamer.asm — een kamer op het scherm zetten en van kamer wisselen (§6.2, hoofdstuk 6).
//
// Een kamerbestand (tools/kamer.py) staat na het laden op KAMER_BUF:
//   +0 woord: plek van het voorgrondblok (0 = geen)     +2 woord: plek van de patchtabel
//   +4 ingepakt: bitmap (16 rijen x 320) | scherm-RAM (640) | kleur-RAM (640)
//   patchtabel: aantal; per patch kolom, rij, breedte, hoogte (vakjes), plek (woord) van zijn ingepakte data
//   (per vakjesrij de bitmapbytes, dan alle schermbytes, dan alle kleurbytes)

.const PATCH_GROOTTE = 1024

.segment Code
// kamer_tonen: pak het plaatje in de kamerbuffer uit naar bitmap, scherm-RAM en kleur-RAM (rij 2-17)
kamer_tonen:
        lda #<(KAMER_BUF + 4)
        sta zp_ptr
        lda #>(KAMER_BUF + 4)
        sta zp_ptr + 1
        lda #<KAMER_BITMAP
        sta zp_ptr2
        lda #>KAMER_BITMAP
        sta zp_ptr2 + 1
        jsr uitpak
        lda #<KAMER_SCHERM
        sta zp_ptr2
        lda #>KAMER_SCHERM
        sta zp_ptr2 + 1
        jsr uitpak
        lda #<KAMER_KLEUR
        sta zp_ptr2
        lda #>KAMER_KLEUR
        sta zp_ptr2 + 1
        jmp uitpak

// kamer_wissel: naar kamer A, Eldric op (kw_x, kw_y) kijkend in kw_richting.
// Laadt het kamerbestand, zet het plaatje neer, laadt loopvakken/schaal/voorgrond, en start BINNENKOMST.
kamer_wissel: {
        sta st_kamer
        jsr vm_stop
        lda kw_x
        sta st_x
        sta act_x
        lda kw_x + 1
        sta st_x + 1
        sta act_x + 1
        lda kw_y
        sta st_y
        sta act_y
        lda kw_richting
        sta act_richting
        lda #0
        sta act_lopen
        sta actie_bezig
        lda #$ff
        sta act_pose
        lda #$ff                        // GEEN_VOORWERP (zin.asm)
        sta zin_eerste
        lda #$fe                        // zinregel opnieuw
        sta zin_ww
        ldx st_kamer
        jsr laad_kamer                  // schijf.asm: scherm leeg, "Laden...", laden, alles weer aan
        ldx st_kamer
        jsr kamer_gegevens              // main.asm: loopvakken, schaal, ACHTER + voorgrond
        jsr npc_kamer_in                // de figuren van deze kamer
        ldx st_kamer
        jsr toneel_kamer                // TONEEL: geen balk, cursor, Eldric (toneel.asm)
        ldx st_kamer                    // BINNENKOMST
        lda kamer_binnen_hi,x
        beq !+
        tay
        lda kamer_binnen_lo,x
        tax
        tya
        stx hulp
        tax
        lda hulp
        jmp vm_start
!:      rts
hulp:   .byte 0
}

// patch_zetten: patch A van de huidige kamer (uit de kamerbuffer) over het scherm leggen
patch_zetten: {
        sta nummer
        lda KAMER_BUF + 2               // de patchtabel
        sta zp_ptr3
        lda KAMER_BUF + 3
        clc
        adc #>KAMER_BUF
        sta zp_ptr3 + 1
        lda zp_ptr3                     // (de plek is vanaf het begin van het bestand: + KAMER_BUF)
        clc
        adc #<KAMER_BUF
        sta zp_ptr3
        bcc !+
        inc zp_ptr3 + 1
!:      ldy #0
        lda nummer
        cmp (zp_ptr3),y
        bcc !+
        rts                             // zo'n patch heeft deze kamer niet
!:      asl                             // * 6 + 1
        sta hulp
        asl
        clc
        adc hulp
        tay
        iny
        lda (zp_ptr3),y
        sta kol
        iny
        lda (zp_ptr3),y
        sta rij
        iny
        lda (zp_ptr3),y
        sta breed
        iny
        lda (zp_ptr3),y
        sta hoog
        iny
        lda (zp_ptr3),y
        clc
        adc #<KAMER_BUF
        sta zp_ptr
        iny
        lda (zp_ptr3),y
        adc #>KAMER_BUF
        sta zp_ptr + 1
        lda #<patch_buf                 // uitpakken naar patch_buf
        sta zp_ptr2
        lda #>patch_buf
        sta zp_ptr2 + 1
        jsr uitpak
        lda #<patch_buf
        sta zp_ptr
        lda #>patch_buf
        sta zp_ptr + 1
        // bitmap: per vakjesrij breed * 8 bytes naar KAMER_BITMAP + (rij * 320) + kol * 8
        lda #0
        sta r
bm:     lda r
        clc
        adc rij
        tax
        lda kol                         // kol * 8 (kol < 40: past in 16 bits)
        sta zp_ptr2
        lda #0
        sta zp_ptr2 + 1
        asl zp_ptr2
        rol zp_ptr2 + 1
        asl zp_ptr2
        rol zp_ptr2 + 1
        asl zp_ptr2
        rol zp_ptr2 + 1
        lda zp_ptr2
        clc
        adc bitmap_rij_lo,x
        sta zp_ptr2
        lda zp_ptr2 + 1
        adc bitmap_rij_hi,x
        sta zp_ptr2 + 1
        lda breed                       // breed * 8 bytes
        asl
        asl
        asl
        sta n
        ldy #0
!:      lda (zp_ptr),y
        sta (zp_ptr2),y
        iny
        cpy n
        bne !-
        jsr bron_n
        inc r
        lda r
        cmp hoog
        bne bm
        // scherm-RAM en kleur-RAM: per rij breed bytes
        lda #0
        sta wat
sk:     lda #0
        sta r
rij_l:  lda r
        clc
        adc rij
        adc #RIJ_KAMER
        tax
        lda rij_lo,x
        clc
        adc kol
        sta zp_ptr2
        lda rij_hi,x
        adc #0
        ldy wat
        beq !+
        clc
        adc #>KLEUR_OFFSET
!:      sta zp_ptr2 + 1
        lda breed
        sta n
        ldy #0
!:      lda (zp_ptr),y
        sta (zp_ptr2),y
        iny
        cpy n
        bne !-
        jsr bron_n
        inc r
        lda r
        cmp hoog
        bne rij_l
        inc wat
        lda wat
        cmp #2
        bne sk
        rts
// zp_ptr += n
bron_n: lda zp_ptr
        clc
        adc n
        sta zp_ptr
        bcc !+
        inc zp_ptr + 1
!:      rts
nummer: .byte 0
hulp:   .byte 0
kol:    .byte 0
rij:    .byte 0
breed:  .byte 0
hoog:   .byte 0
r:      .byte 0
n:      .byte 0
wat:    .byte 0
}

.segment Data
kw_x:         .word 0                   // KAMER: waar Eldric komt te staan
kw_y:         .byte 0
kw_richting:  .byte 0
bitmap_rij_lo: .fill KAMER_RIJEN, <(KAMER_BITMAP + i * 320)
bitmap_rij_hi: .fill KAMER_RIJEN, >(KAMER_BITMAP + i * 320)

.segment Buffers
patch_buf:    .fill PATCH_GROOTTE, 0
