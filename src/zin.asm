// zin.asm — voorwerpen en de zinregel (§4, §5): "Bekijk fontein".
//
// - Onder de cursor: het eerste voorwerp waarvan het klikvak de cursor bevat (in de kamer).
// - De zinregel (rij 18) toont het werkwoord en dat voorwerp; tijdens een actie de zin die wordt uitgevoerd.
// - Klik op een werkwoord (rij 19-21): dat wordt het werkwoord (geel).
// - Klik in de kamer op een voorwerp: Eldric loopt naar het LOOP-punt, kijkt in de richting van het voorwerp,
//   en dan draait het script van dat voorwerp voor dat werkwoord, of anders het standaardantwoord.
//   Klik op de vloer: Ga naar. Na elke klik in de kamer is het werkwoord weer "Ga naar".
// - Vuur terwijl er een tekst staat: de tekst weg (en verder niets).

.const MAX_KAMER_VW    = 16             // per kamer (status.asm: MAX_VOORWERPEN in het hele spel)
.const GEEN_VOORWERP   = $ff
.const WW_GA_NAAR      = 0
.const WW_WAT_IS       = 11
.const KLEUR_GEKOZEN   = 7              // geel: het gekozen werkwoord
.const VW_VELDEN       = 14

.segment Code
// voorwerpen_laden: de tabel op (zp_ptr) — aantal, dan 14 rijen van <aantal> bytes — naar vw_velden
voorwerpen_laden: {
        ldy #0
        lda (zp_ptr),y
        sta vw_aantal
        jsr bron_verder
        lda #<vw_velden
        sta zp_ptr2
        lda #>vw_velden
        sta zp_ptr2 + 1
        ldx #VW_VELDEN
veld:   ldy #0
!:      cpy vw_aantal
        beq klaar
        lda (zp_ptr),y
        sta (zp_ptr2),y
        iny
        bne !-
klaar:  tya
        clc
        adc zp_ptr
        sta zp_ptr
        bcc !+
        inc zp_ptr + 1
!:      lda zp_ptr2
        clc
        adc #MAX_KAMER_VW
        sta zp_ptr2
        bcc !+
        inc zp_ptr2 + 1
!:      dex
        bne veld
        lda #WW_GA_NAAR
        sta werkwoord
        lda #$fe                        // zinregel en werkwoordkleuren opnieuw tekenen
        sta zin_ww
        sta ww_kleur
        rts
}

// voorwerp_onder: welk voorwerp ligt onder de cursor? -> vw_onder (of GEEN_VOORWERP)
voorwerp_onder: {
        lda #GEEN_VOORWERP
        sta vw_onder
        lda cursor_y
        sec
        sbc #RIJ_KAMER * 8
        bcc klaar                       // boven de kamer
        cmp #KAMER_RIJEN * 8
        bcs klaar                       // eronder
        sta p_y
        ldx #0
lus:    cpx vw_aantal
        beq klaar
        lda cursor_x                    // x1 <= cursor_x <= x2
        cmp vw_x1_lo,x
        lda cursor_x + 1
        sbc vw_x1_hi,x
        bcc volgende
        lda vw_x2_lo,x
        cmp cursor_x
        lda vw_x2_hi,x
        sbc cursor_x + 1
        bcc volgende
        lda p_y                         // y1 <= y <= y2
        cmp vw_y1,x
        bcc volgende
        lda vw_y2,x
        cmp p_y
        bcc volgende
        stx vw_onder
        rts
volgende:
        inx
        bne lus
klaar:  rts
}

// zin_beeld: elk beeld; tekent de zinregel en de kleuren van de werkwoorden als er iets veranderd is
zin_beeld: {
        jsr voorwerp_onder
        lda werkwoord                   // wat moet er staan?
        ldx vw_onder
        ldy actie_bezig                 // tijdens een actie: de zin die wordt uitgevoerd
        beq !+
        lda actie_ww
        ldx actie_vw
!:      cmp zin_ww
        bne teken
        cpx zin_vw
        beq kleuren
teken:  sta zin_ww
        stx zin_vw
        ldy #RIJ_ZIN
        lda #KLEUR_ZIN
        jsr rij_wissen
        ldx zin_ww                      // het werkwoord
        lda werkwoorden_lo,x
        sta zp_ptr
        lda werkwoorden_hi,x
        sta zp_ptr + 1
        ldx #0
        ldy #RIJ_ZIN
        lda #KLEUR_ZIN
        jsr tekst_schrijf               // Y = lengte
        ldx zin_vw
        cpx #GEEN_VOORWERP
        beq kleuren
        iny                             // een spatie, dan de naam
        tya
        pha
        lda vw_naam_lo,x
        sta zp_ptr
        lda vw_naam_hi,x
        sta zp_ptr + 1
        pla
        tax
        ldy #RIJ_ZIN
        lda #KLEUR_ZIN
        jsr tekst_schrijf

kleuren:
        lda werkwoord
        cmp ww_kleur
        beq klaar
        sta ww_kleur
        ldx #AANTAL_WERKWOORDEN - 1     // alle werkwoorden groen, het gekozen geel
!:      txa
        pha
        lsr
        lsr
        tay
        lda kleur_rij_lo,y
        sta zp_ptr3
        lda kleur_rij_hi,y
        sta zp_ptr3 + 1
        txa
        and #3
        tay
        lda kolommen,y
        tay
        lda #KLEUR_WERKWOORD
        cpx werkwoord
        bne !+
        lda #KLEUR_GEKOZEN
!:      ldx #9
!:      sta (zp_ptr3),y
        iny
        dex
        bne !-
        pla
        tax
        dex
        bpl !---
klaar:  rts
kolommen: .byte 0, 10, 20, 30
}

// klik: vuur. Tekst weg, werkwoord kiezen, of een zin beginnen in de kamer.
klik: {
        lda invoer_vuur
        bne !+
        rts
!:      lda bericht_actief              // eerst: een tekst wegklikken
        beq !+
        jmp bericht_weg
!:      lda cursor_y                    // in de werkwoorden?
        cmp #RIJ_WERKWOORD * 8
        bcc kamer
        cmp #(RIJ_WERKWOORD + 3) * 8
        bcs geen
        lsr                             // rij = y / 8 - 19
        lsr
        lsr
        sec
        sbc #RIJ_WERKWOORD
        asl
        asl
        sta werkwoord
        ldx #0                          // kolom: x / 80
        lda cursor_x + 1
        bne !+                          // >= 256: kolom 3
        lda cursor_x
        cmp #80
        bcc kol
        inx
        cmp #160
        bcc kol
        inx
        cmp #240
        bcc kol
!:      ldx #3
kol:    txa
        clc
        adc werkwoord
        sta werkwoord
geen:   rts

kamer:  cmp #RIJ_KAMER * 8
        bcc geen
        cmp #(RIJ_KAMER + KAMER_RIJEN) * 8
        bcs geen                        // de zinregel
        lda #0                          // een nieuwe klik breekt een lopend script af
        sta vm_pc
        sta vm_pc + 1
        ldx vw_onder
        cpx #GEEN_VOORWERP
        beq vloer
        stx actie_vw                    // naar het voorwerp, dan de zin
        lda werkwoord
        sta actie_ww
        lda #1
        sta actie_bezig
        lda vw_loop_x_lo,x
        sta p_x
        lda vw_loop_x_hi,x
        sta p_x + 1
        lda vw_loop_y,x
        sta p_y
        jmp verder
vloer:  lda #0
        sta actie_bezig
        lda cursor_x
        sta p_x
        lda cursor_x + 1
        sta p_x + 1
        lda cursor_y
        sec
        sbc #RIJ_KAMER * 8
        sta p_y
verder: lda #WW_GA_NAAR
        sta werkwoord
        jmp actor_loop_naar
}

// actie_beeld: elk beeld. Is Eldric bij het voorwerp, dan kijkt hij het aan en start het script.
actie_beeld: {
        lda actie_bezig
        beq klaar
        lda act_lopen
        bne klaar
        lda #0
        sta actie_bezig
        ldx actie_vw
        lda vw_richting,x
        sta act_richting
        lda actie_ww
        cmp #WW_GA_NAAR
        beq klaar
        cmp #WW_WAT_IS
        beq klaar
        asl                             // het script van het voorwerp voor dit werkwoord
        tay
        lda vw_scripts_lo,x
        sta zp_ptr
        lda vw_scripts_hi,x
        sta zp_ptr + 1
        lda (zp_ptr),y
        tax
        iny
        lda (zp_ptr),y
        bne start
        dey                             // geen: het standaardantwoord
        lda standaard_scripts,y
        tax
        lda standaard_scripts + 1,y
        beq klaar
start:  sta hoog
        txa
        ldx hoog
        jmp vm_start
klaar:  rts
hoog:   .byte 0
}

.segment Data
vw_aantal:    .byte 0
vw_velden:    .fill VW_VELDEN * MAX_KAMER_VW, 0
.label vw_x1_lo     = vw_velden + 0 * MAX_KAMER_VW
.label vw_x1_hi     = vw_velden + 1 * MAX_KAMER_VW
.label vw_x2_lo     = vw_velden + 2 * MAX_KAMER_VW
.label vw_x2_hi     = vw_velden + 3 * MAX_KAMER_VW
.label vw_y1        = vw_velden + 4 * MAX_KAMER_VW
.label vw_y2        = vw_velden + 5 * MAX_KAMER_VW
.label vw_loop_x_lo = vw_velden + 6 * MAX_KAMER_VW
.label vw_loop_x_hi = vw_velden + 7 * MAX_KAMER_VW
.label vw_loop_y    = vw_velden + 8 * MAX_KAMER_VW
.label vw_richting  = vw_velden + 9 * MAX_KAMER_VW
.label vw_naam_lo   = vw_velden + 10 * MAX_KAMER_VW
.label vw_naam_hi   = vw_velden + 11 * MAX_KAMER_VW
.label vw_scripts_lo = vw_velden + 12 * MAX_KAMER_VW
.label vw_scripts_hi = vw_velden + 13 * MAX_KAMER_VW
vw_onder:     .byte GEEN_VOORWERP
werkwoord:    .byte WW_GA_NAAR
zin_ww:       .byte $fe                 // wat er nu op de zinregel staat
zin_vw:       .byte $fe
ww_kleur:     .byte $fe                 // welk werkwoord nu geel is
actie_bezig:  .byte 0
actie_ww:     .byte 0
actie_vw:     .byte 0
kleur_rij_lo: .fill 3, <(KLEUR_RAM + (RIJ_WERKWOORD + i) * 40)
kleur_rij_hi: .fill 3, >(KLEUR_RAM + (RIJ_WERKWOORD + i) * 40)
