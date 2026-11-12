// zin.asm — voorwerpen, inventaris en de zinregel (§4, §5): "Bekijk fontein", "Gebruik kruik met vat".
//
// - Onder de cursor: een voorwerp in de kamer (eigenaar = deze kamer, met klikvak) of in de inventaris.
// - Zinregel (rij 18): werkwoord [eerste voorwerp + voorzetsel] [voorwerp onder de cursor];
//   tijdens een actie de zin die wordt uitgevoerd.
// - Klik op een werkwoord (rij 19-21): dat wordt het werkwoord (geel).
// - Klik op een voorwerp:
//     Gebruik/Geef met iets uit de inventaris -> "Gebruik kruik met ..." en wacht op het tweede voorwerp;
//     anders (of met het tweede voorwerp) de zin uitvoeren: in de kamer eerst erheen lopen en het aankijken.
//   Na een zin is het werkwoord weer "Ga naar". Klik op de vloer: Ga naar.
// - Het script: twee voorwerpen -> eerst bij het tweede (GEBRUIK kruik: onder het vat), dan (Gebruik) bij het
//   eerste, anders het standaardantwoord. Eén voorwerp -> zijn script, anders het standaardantwoord.
// - Vuur terwijl er een tekst staat: de tekst weg. In een tussenscène: overslaan.

.const GEEN_VOORWERP   = $ff
.const WW_GA_NAAR      = 0
.const WW_GEBRUIK      = 2
.const WW_GEEF         = 6
.const WW_WAT_IS       = 11
.const KLEUR_GEKOZEN   = 7              // geel: het gekozen werkwoord
.const ZIN_LENGTE      = 40

.segment Code
// voorwerp_onder: welk voorwerp ligt onder de cursor? -> vw_onder (of GEEN_VOORWERP)
voorwerp_onder: {
        jsr inv_onder                   // in de inventaris?
        sta vw_onder
        cmp #GEEN_VOORWERP
        bne klaar
        lda cursor_y
        sec
        sbc #RIJ_KAMER * 8
        bcc klaar                       // boven de kamer
        cmp #KAMER_RIJEN * 8
        bcs klaar                       // eronder
        sta p_y
        ldx #0
lus:    cpx #AANTAL_VW
        beq klaar
        lda st_eigenaar,x
        cmp st_kamer
        bne volgende
        lda vw_heeft_vak,x
        beq volgende
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

// zin_beeld: elk beeld; inventaris bijwerken, zinregel en werkwoordkleuren tekenen als er iets veranderd is
zin_beeld: {
        lda gs_actief                   // tijdens een gesprek: de keuzes in plaats van zinregel en werkwoorden
        beq !+
        jmp gesprek_beeld
!:      jsr inv_bijwerken
        jsr voorwerp_onder
        lda werkwoord                   // wat moet er staan?
        sta nu_ww
        lda zin_eerste
        sta nu_eerste
        lda vw_onder
        sta nu_vw
        lda actie_bezig                 // tijdens een actie: de zin die wordt uitgevoerd
        beq !+
        lda actie_ww
        sta nu_ww
        lda actie_eerste
        sta nu_eerste
        lda actie_vw
        sta nu_vw
!:      lda nu_ww
        cmp zin_ww
        bne teken
        lda nu_eerste
        cmp zin_eerste_getoond
        bne teken
        lda nu_vw
        cmp zin_vw
        bne teken
        jmp kleuren
teken:  lda nu_ww
        sta zin_ww
        lda nu_eerste
        sta zin_eerste_getoond
        lda nu_vw
        sta zin_vw
        // de zin in zin_buf: werkwoord [eerste voorzetsel] [voorwerp]
        ldy #0
        ldx zin_ww
        lda werkwoorden_lo,x
        sta zp_ptr
        lda werkwoorden_hi,x
        sta zp_ptr + 1
        jsr erbij
        ldx zin_eerste_getoond
        cpx #GEEN_VOORWERP
        beq tweede
        jsr naam_erbij
        ldx zin_ww                      // het voorzetsel
        lda voorzetsel_lo,x
        sta zp_ptr
        lda voorzetsel_hi,x
        sta zp_ptr + 1
        jsr spatie_erbij
tweede: ldx zin_vw
        cpx #GEEN_VOORWERP
        beq af
        cpx zin_eerste_getoond          // niet twee keer hetzelfde
        beq af
        jsr naam_erbij
af:     lda #0
        sta zin_buf,y
        ldy #RIJ_ZIN
        lda #KLEUR_ZIN
        jsr rij_wissen
        lda #<zin_buf
        sta zp_ptr
        lda #>zin_buf
        sta zp_ptr + 1
        ldx #0
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

// naam van voorwerp X erbij (met een spatie ervoor)
naam_erbij:
        lda vw_naam_lo,x
        sta zp_ptr
        lda vw_naam_hi,x
        sta zp_ptr + 1
spatie_erbij:
        lda #$20
        sta zin_buf,y
        iny
// de tekst op (zp_ptr) achter zin_buf,Y (Y wordt de nieuwe lengte; nooit langer dan de regel)
erbij:  sty doel
        ldy #0
!:      lda (zp_ptr),y
        beq !+
        sty bron
        ldy doel
        cpy #ZIN_LENGTE
        bcs !+
        sta zin_buf,y
        iny
        sty doel
        ldy bron
        iny
        bne !-
!:      ldy doel
        rts
kolommen: .byte 0, 10, 20, 30
bron:   .byte 0
doel:   .byte 0
nu_ww:  .byte 0
nu_eerste: .byte 0
nu_vw:  .byte 0
}

// klik: vuur. Tekst weg, overslaan, werkwoord kiezen, inventaris, of een zin in de kamer.
klik: {
        lda invoer_vuur
        bne !+
        rts
!:      lda vm_scene                    // tussenscène: vuur = overslaan, verder niets
        beq !+
        lda #1
        sta vm_overslaan
        rts
!:      lda bericht_actief              // eerst: een tekst wegklikken
        beq !+
        jmp bericht_weg
!:      lda gs_actief                   // gesprek: een keuze
        beq !+
        jmp gesprek_klik
!:      lda cursor_y
        cmp #RIJ_WERKWOORD * 8
        bcc kamer
        cmp #(RIJ_WERKWOORD + 3) * 8
        bcs inventaris
        lsr                             // werkwoord: rij = y / 8 - 19, kolom = x / 80
        lsr
        lsr
        sec
        sbc #RIJ_WERKWOORD
        asl
        asl
        sta werkwoord
        ldx #0
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
        lda #GEEN_VOORWERP              // een nieuw werkwoord begint een nieuwe zin
        sta zin_eerste
geen:   rts

inventaris:
        jsr inv_onder
        cmp #GEEN_VOORWERP
        bne !+
        lda inv_pijl
        beq geen
        jmp inv_schuif
!:      tax
        lda #1
        jmp voorwerp_klik

kamer:  cmp #RIJ_KAMER * 8
        bcc geen
        cmp #(RIJ_KAMER + KAMER_RIJEN) * 8
        bcs geen                        // de zinregel
        ldx vw_onder
        cpx #GEEN_VOORWERP
        beq vloer
        lda #0
        jmp voorwerp_klik
vloer:  jsr vm_stop                     // Ga naar die plek; een halve zin vervalt
        lda #0
        sta actie_bezig
        lda #GEEN_VOORWERP
        sta zin_eerste
        lda #WW_GA_NAAR
        sta werkwoord
        lda cursor_x
        sta p_x
        lda cursor_x + 1
        sta p_x + 1
        lda cursor_y
        sec
        sbc #RIJ_KAMER * 8
        sta p_y
        jmp actor_loop_naar
}

// voorwerp_klik: voorwerp X aangeklikt; A = 1 in de inventaris, 0 in de kamer
voorwerp_klik: {
        sta in_inv
        stx vw
        lda zin_eerste
        cmp #GEEN_VOORWERP
        beq geen_eerste
        cmp vw                          // hetzelfde voorwerp nog eens: de halve zin vervalt
        bne !+
        lda #GEEN_VOORWERP
        sta zin_eerste
        rts
!:      sta actie_eerste                // het tweede voorwerp: de zin is af
        jmp uitvoeren
geen_eerste:
        lda werkwoord
        cmp #WW_GA_NAAR                 // Ga naar iets in de inventaris: niets
        bne !+
        lda in_inv
        beq !+
        rts
!:      lda werkwoord
        cmp #WW_GEBRUIK
        beq twee
        cmp #WW_GEEF
        bne een
twee:   lda in_inv                      // Gebruik/Geef met iets uit de inventaris: wacht op het tweede
        beq een
        lda vw
        sta zin_eerste
        rts
een:    lda #GEEN_VOORWERP
        sta actie_eerste
uitvoeren:
        jsr vm_stop                     // een nieuwe zin breekt een lopend script af
        lda vw
        sta actie_vw
        lda werkwoord
        sta actie_ww
        lda in_inv
        sta actie_in_inv
        lda #1
        sta actie_bezig
        lda #WW_GA_NAAR
        sta werkwoord
        lda #GEEN_VOORWERP
        sta zin_eerste
        lda in_inv                      // in de kamer: eerst erheen
        bne klaar
        ldx vw
        lda vw_loop_x_lo,x
        sta p_x
        lda vw_loop_x_hi,x
        sta p_x + 1
        lda vw_loop_y,x
        sta p_y
        jmp actor_loop_naar
klaar:  rts
in_inv: .byte 0
vw:     .byte 0
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
        lda actie_in_inv                // alleen voorwerpen in de kamer kijkt hij aan
        bne !+
        lda vw_richting,x
        sta act_richting
!:      lda actie_ww
        cmp #WW_WAT_IS
        beq klaar
        lda actie_eerste
        cmp #GEEN_VOORWERP
        bne paar
        // één voorwerp: zijn script voor dit werkwoord
        jsr scripts_van_x
        lda actie_ww
        asl
        tay
        lda (zp_ptr),y
        tax
        iny
        lda (zp_ptr),y
        bne start
        jmp standaard
paar:   // twee voorwerpen: bij het tweede (actie_vw) zoeken naar (werkwoord, eerste)
        ldx actie_vw
        lda actie_eerste
        jsr paar_zoeken
        bcs start
        lda actie_ww                    // Gebruik: ook andersom
        cmp #WW_GEBRUIK
        bne standaard
        ldx actie_eerste
        lda actie_vw
        jsr paar_zoeken
        bcs start
standaard:
        lda actie_ww
        asl
        tay
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

// zp_ptr = de scripttabel van voorwerp X
scripts_van_x:
        lda vw_scripts_lo,x
        sta zp_ptr
        lda vw_scripts_hi,x
        sta zp_ptr + 1
        rts

// paar_zoeken: in de paren van voorwerp X naar (actie_ww, A). C = 1 gevonden: X = laag, A = hoog
paar_zoeken:
        sta ander
        jsr scripts_van_x
        ldy #24                         // na de 12 werkwoorden
!:      lda (zp_ptr),y
        cmp #$ff
        beq niet
        cmp actie_ww
        bne volgende
        iny
        lda (zp_ptr),y
        dey
        cmp ander
        bne volgende
        iny
        iny
        lda (zp_ptr),y
        tax
        iny
        lda (zp_ptr),y
        sec
        rts
volgende:
        iny
        iny
        iny
        iny
        bne !-
niet:   clc
        rts
ander:  .byte 0
}

.segment Data
vw_onder:     .byte GEEN_VOORWERP
werkwoord:    .byte WW_GA_NAAR
zin_eerste:   .byte GEEN_VOORWERP       // "Gebruik kruik met ...": het eerste voorwerp
zin_ww:       .byte $fe                 // wat er nu op de zinregel staat
zin_vw:       .byte $fe
zin_eerste_getoond: .byte $fe
ww_kleur:     .byte $fe                 // welk werkwoord nu geel is
actie_bezig:  .byte 0
actie_ww:     .byte 0
actie_vw:     .byte 0
actie_eerste: .byte GEEN_VOORWERP
actie_in_inv: .byte 0
inventaris_anders: .byte 1              // GEEF/NEEM/PLAATS: de inventaris opnieuw tekenen (1: meteen bij het begin)
zin_buf:      .fill ZIN_LENGTE + 1, 0
kleur_rij_lo: .fill 3, <(KLEUR_RAM + (RIJ_WERKWOORD + i) * 40)
kleur_rij_hi: .fill 3, >(KLEUR_RAM + (RIJ_WERKWOORD + i) * 40)
