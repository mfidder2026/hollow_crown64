// kamer.asm — een kamer op het scherm zetten (§6.2).
// Een kamerbestand (tools/kamer.py): ingepakt bitmap (16 rijen x 320) | scherm-RAM (640) | kleur-RAM (640).
// Hoofdstuk 1: de kamer zit nog in het programma. Laden van de diskette komt in hoofdstuk 6.

.segment Code
// kamer_tonen: pak de kamer op (zp_ptr) uit naar bitmap, scherm-RAM en kleur-RAM (rij 2-17).
kamer_tonen:
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

.segment Data
kamer_plein:
        .import binary "../build/gen/kamer_plein.bin"
