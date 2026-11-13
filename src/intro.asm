// intro.asm — het introscherm (§9): titelplaatje, logo met kleurenloop, scrolltekst en het thema.
//
//   rij 0-1    leeg
//   rij 2-17   het titelplaatje (bestand "titel", hetzelfde formaat als een kamer: tools/kamer.py)
//   rij 18     leeg: op de eerste lijn van rij 18 schakelt de IRQ van bitmap naar tekst (lijn 195); daar zou de
//              bovenste pixelrij van het logo half in de verkeerde stand komen (een witte streep). Gewone letters hebben
//              daarom pixelrij 0 leeg; het logo gebruikt alle 8 rijen, dus begint het een rij lager.
//   rij 19-21  HOLLOW CROWN in het logo-lettertype (tools/logo.py: tekens $80.. in het lettertype)
//   rij 22     "Druk op spatie of vuur"      rij 23 leeg (daar begint de scroll-IRQ)
//   rij 24     de scrolltekst, vloeiend: een extra raster-IRQ op lijn 241 zet XSCROLL (38 kolommen) en de
//              onderrand zet hem weer terug (irq.asm).
// Spatie of vuur start het spel; F1 zet de muziek aan of uit. Daarna: muziek stil, de SID leeg, de IRQ's weer
// zoals in het spel, rij 18-24 leeg.
// In een AUTOTEST-build draait het intro alleen als de band met INTRO begint (anders meteen het spel).

#import "../build/gen/logo.asm"

.const RIJ_LOGO      = 19
.const RIJ_DRUK      = 22
.const RIJ_SCROLL    = 24
.const KLEURSTAP     = 3                // beelden per stap van de kleurenloop
.const KLEUR_DRUK    = 15               // lichtgrijs
.const KLEUR_SCROLL  = 14               // lichtblauw

.segment Code
intro: {
#if AUTOTEST
!:      lda band_status                 // wacht tot vicetest de band heeft geladen
        beq !-
        ldy #0
        lda (zp_band),y
        cmp #$0a                        // BAND_OP_INTRO (autotest.asm, dat later komt)
        beq !+
        rts                             // geen INTRO: meteen het spel
!:      inc zp_band                     // de INTRO-opdracht is gedaan
        bne !+
        inc zp_band + 1
!:
#endif
        lda $d015                       // de cursor (sprite 0) staat al aan: straks weer
        sta sprites_spel
        // het titelplaatje laden (zoals een kamer: "Laden...", de IRQ's daarna aan)
        jsr laden_begin
        lda #titel_naam_lengte
        ldx #<titel_naam
        ldy #>titel_naam
        jsr SETNAM
        lda #1
        ldx #8
        ldy #0
        jsr SETLFS
        lda #0
        ldx #<KAMER_BUF
        ldy #>KAMER_BUF
        jsr turbo_vergeet               // (turbo.asm: de drive gebruikt nu zijn buffers)
        jsr LOAD
        lda #0
        bcc !+
        lda #1
!:      sta laad_fout
        inc laad_teller
        jsr kamer_tonen
        jsr laden_einde
        lda #0
        sta $d015                       // geen sprites (ook geen cursor)
        // de logotekens in het lettertype
        ldx #0
!:      lda logo_tegels,x
        sta LETTERTYPE + LOGO_EERSTE * 8,x
        lda logo_tegels + 256,x
        sta LETTERTYPE + LOGO_EERSTE * 8 + 256,x
        inx
        bne !-
        // rij 0-1 en 18-24 leeg, het logo, de tekst
        ldy #0
        lda #0
        jsr rij_wissen
        ldy #1
        lda #0
        jsr rij_wissen
        ldy #RIJ_ZIN                    // rij 18-24 leeg
!:      tya
        pha
        lda #0
        jsr rij_wissen
        pla
        tay
        iny
        cpy #25
        bne !-
        ldx #0
!:      lda logo_kaart,x
        sta SCHERM + RIJ_LOGO * 40,x
        lda logo_kaart + 40,x
        sta SCHERM + (RIJ_LOGO + 1) * 40,x
        lda logo_kaart + 80,x
        sta SCHERM + (RIJ_LOGO + 2) * 40,x
        inx
        cpx #40
        bne !-
        lda #<tekst_druk
        sta zp_ptr
        lda #>tekst_druk
        sta zp_ptr + 1
        ldx #(40 - tekst_druk_lengte) / 2
        ldy #RIJ_DRUK
        lda #KLEUR_DRUK
        jsr tekst_schrijf
        ldy #RIJ_SCROLL
        lda #KLEUR_SCROLL
        jsr rij_wissen
        lda #<tekst_scroll
        sta intro_scroll_ptr
        lda #>tekst_scroll
        sta intro_scroll_ptr + 1
        lda #7
        sta intro_xscroll
        lda #0
        sta intro_kleur
        sta intro_tik
        sta invoer_vorig
        lda toets_rij0
        and #%00010000
        sta f1_vorig
        jsr kleuren_loop
        lda #1
        sta intro_actief                // de IRQ zet nu ook de scroll-split (irq.asm)
        lda #LIED_THEMA
        jsr muziek_start

lus:    lda beelden
!:      cmp beelden
        beq !-
#if AUTOTEST
        lda band_markering              // vicetest kijkt: alles staat stil
        bne lus
#endif
        jsr invoer_lees
        // F1: muziek aan/uit
        lda toets_rij0
        and #%00010000
        tax
        eor f1_vorig
        and toets_rij0
        stx f1_vorig
        and #%00010000
        beq !+
        jsr muziek_f1
!:      // de kleurenloop door het logo
        inc intro_tik
        lda intro_tik
        cmp #KLEURSTAP
        bcc !+
        lda #0
        sta intro_tik
        inc intro_kleur
        jsr kleuren_loop
!:      jsr scroll_stap
#if AUTOTEST
        jsr band_stap
#endif
        lda invoer_vuur                 // spatie of vuur: het spel begint
        bne klaar
        jmp lus

klaar:  jsr muziek_stop
        jsr geluid_stil                 // alle stemmen en het volume op 0: geen hangende toon
        lda #0
        sta intro_actief
        lda beelden                     // één beeld wachten: de IRQ's lopen weer zoals in het spel
!:      cmp beelden
        beq !-
        ldy #RIJ_ZIN                    // rij 18-24 leeg
!:      tya
        pha
        lda #0
        jsr rij_wissen
        pla
        tay
        iny
        cpy #25
        bne !-
        lda sprites_spel
        sta $d015
        inc intro_gedaan
        rts
}

// kleuren_loop: kolom k van het logo krijgt kleur logo_kleuren[(k + intro_kleur) & 15]
kleuren_loop: {
        ldx #0
!:      txa
        clc
        adc intro_kleur
        and #15
        tay
        lda logo_kleuren,y
        sta KLEUR_RAM + RIJ_LOGO * 40,x
        sta KLEUR_RAM + (RIJ_LOGO + 1) * 40,x
        sta KLEUR_RAM + (RIJ_LOGO + 2) * 40,x
        inx
        cpx #40
        bne !-
        rts
}

// scroll_stap: 1 pixel per beeld naar links; na 8 pixels de rij een teken opschuiven en een nieuw teken erbij
scroll_stap: {
        dec intro_xscroll
        bpl klaar
        lda #7
        sta intro_xscroll
        ldx #0
!:      lda SCHERM + RIJ_SCROLL * 40 + 1,x
        sta SCHERM + RIJ_SCROLL * 40,x
        inx
        cpx #39
        bne !-
        lda intro_scroll_ptr
        sta zp_ptr
        lda intro_scroll_ptr + 1
        sta zp_ptr + 1
        ldy #0
        lda (zp_ptr),y
        bne !+
        lda #<tekst_scroll              // einde: van voren af aan
        sta intro_scroll_ptr
        lda #>tekst_scroll
        sta intro_scroll_ptr + 1
        lda #' '
        jmp zet
!:      inc intro_scroll_ptr
        bne zet
        inc intro_scroll_ptr + 1
zet:    sta SCHERM + RIJ_SCROLL * 40 + 39
        inc intro_scroll_tekens
klaar:  rts
}

.segment Data
.encoding "petscii_upper"
titel_naam:   .text "TITEL"
.label titel_naam_lengte = * - titel_naam
.encoding "screencode_mixed"
// de kleurenloop: goud en vuur, dan koud zilver (16 stappen, kolom voor kolom verschoven)
logo_kleuren: .byte 9, 2, 8, 10, 7, 1, 7, 10, 8, 2, 9, 11, 12, 15, 12, 11
intro_actief:        .byte 0            // 1: het intro loopt (irq.asm: de scroll-split)
intro_gedaan:        .byte 0            // 1: het intro is afgelopen (voor de tests)
intro_xscroll:       .byte 7
intro_kleur:         .byte 0
intro_tik:           .byte 0
intro_scroll_ptr:    .word 0
intro_scroll_tekens: .word 0            // hoeveel tekens er ingeschoven zijn (voor de tests)
f1_vorig:            .byte 0            // F1 vorig beeld (ook in het spel: opslaan.asm)
sprites_spel:        .byte 0
