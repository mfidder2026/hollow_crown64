// balk.asm — de balk onder de kamer (§4): zinregel, werkwoorden, inventaris, hoofdstuknaam.
//
//   rij 18     zinregel ("Ga naar")
//   rij 19-21  werkwoorden: 3 rijen x 4 kolommen (kolom 0, 10, 20, 30)
//   rij 22-23  inventaris: 2 x 2 namen (kolom 0-17 en 22-39), pijlen in kolom 18-21
//   rij 24     naam van het hoofdstuk
// De zinregel en de kleur van het gekozen werkwoord houdt zin.asm bij.

.const KLEUR_ZIN        = 3             // cyaan
.const KLEUR_WERKWOORD  = 5             // groen
.const KLEUR_INVENTARIS = 4             // paars
.const KLEUR_PIJL_UIT   = 11            // donkergrijs: niets om te schuiven
.const KLEUR_PIJL_AAN   = 1
.const KLEUR_HOOFDSTUK  = 12            // grijs
.const KOLOM_PIJL       = 19

.segment Code
balk_tekenen: {
        ldy #RIJ_ZIN                    // rij 18-24 leeg
!:      tya
        pha
        lda #KLEUR_WERKWOORD
        jsr rij_wissen
        pla
        tay
        iny
        cpy #25
        bne !-

        // zinregel: het standaardwerkwoord
        lda werkwoorden_lo
        sta zp_ptr
        lda werkwoorden_hi
        sta zp_ptr + 1
        ldx #0
        ldy #RIJ_ZIN
        lda #KLEUR_ZIN
        jsr tekst_schrijf

        // werkwoorden
        ldx #0
ww:     stx teller
        lda werkwoorden_lo,x
        sta zp_ptr
        lda werkwoorden_hi,x
        sta zp_ptr + 1
        txa
        lsr
        lsr
        clc
        adc #RIJ_WERKWOORD
        tay
        txa
        and #3
        tax
        lda kolommen,x
        tax
        lda #KLEUR_WERKWOORD
        jsr tekst_schrijf
        ldx teller
        inx
        cpx #AANTAL_WERKWOORDEN
        bne ww

        // inventaris: inventaris.asm tekent hem (inventaris_anders staat bij het begin op 1)
        // hoofdstuk
        lda #<tekst_hoofdstuk
        sta zp_ptr
        lda #>tekst_hoofdstuk
        sta zp_ptr + 1
        ldx #(40 - tekst_hoofdstuk_lengte) / 2
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jmp tekst_schrijf

kolommen: .byte 0, 10, 20, 30
teller:   .byte 0
}
