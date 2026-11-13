// schijf.asm — laden van de diskette (§6.7). Eén laadroutine, via de Kernal; een snellader kan later.
//
// Tijdens het laden: de raster-IRQ's uit (de Kernal zet de IRQ's tijdens elke byte toch uit, en dan
// verspringen de naden), het hele scherm in tekstmodus, de kamer leeg (zwart), de sprites uit en "Laden..."
// in de balk. Muziek en geluid stil (geluid.asm, hoofdstuk 9/10). Daarna alles weer aan.
// De laadtijd meten we met de klok (TOD) van CIA 1: die loopt door zonder IRQ's.
// Tienden van seconden in laadtijd; laad_fout = de Kernal-fout (0 = goed).

.const SETNAM = $ffbd
.const SETLFS = $ffba
.const LOAD   = $ffd5

.segment Code
// tod_start: de klok van CIA 1 op 50 Hz zetten en laten lopen (bij het begin van het spel)
tod_start:
        lda $dc0e
        ora #%10000000                  // 50 Hz (PAL)
        sta $dc0e
        lda $dc0f
        and #%01111111                  // schrijven = de klok zetten (niet het alarm)
        sta $dc0f
        lda #0
        sta $dc0b                       // uren (stopt de klok)
        sta $dc0a
        sta $dc09
        sta $dc08                       // tienden: de klok loopt weer
        rts

// tod_lezen: -> tod_nu (woord) = minuten * 600 + seconden * 10 + tienden (minder dan een uur)
tod_lezen: {
        lda $dc0b                       // uren: houdt de rest vast tot de tienden gelezen zijn
        lda $dc0a
        jsr bcd
        sta min
        lda $dc09
        jsr bcd
        sta sec
        lda $dc08                       // tienden (laat de klok weer los)
        and #$0f
        sta tod_nu
        lda #0
        sta tod_nu + 1
        ldx sec                         // + seconden * 10
!:      cpx #0
        beq !+
        lda tod_nu
        clc
        adc #10
        sta tod_nu
        bcc *+5
        inc tod_nu + 1
        dex
        jmp !-
!:      ldx min                         // + minuten * 600
!:      cpx #0
        beq klaar
        lda tod_nu
        clc
        adc #<600
        sta tod_nu
        lda tod_nu + 1
        adc #>600
        sta tod_nu + 1
        dex
        jmp !-
klaar:  rts
bcd:    pha                             // BCD -> getal
        and #$70
        lsr
        sta tien
        lsr
        lsr
        clc
        adc tien                        // (hoog / 16) * 10 = hoog/2 + hoog/8
        sta tien
        pla
        and #$0f
        clc
        adc tien
        rts
min:    .byte 0
sec:    .byte 0
tien:   .byte 0
}

// laad_kamer: het bestand van kamer X naar KAMER_BUF laden en het plaatje neerzetten
laad_kamer: {
        stx kamer
        jsr laden_begin
opnieuw:
        jsr tod_lezen
        lda tod_nu
        sta begin
        lda tod_nu + 1
        sta begin + 1
        ldx kamer
        lda kamer_bestand_len,x
        pha
        ldy kamer_bestand_hi,x
        lda kamer_bestand_lo,x
        tax
        pla
        jsr SETNAM
        lda #1                          // logisch bestand 1, apparaat 8, secundair adres 0: laad op X/Y
        ldx #8
        ldy #0
        jsr SETLFS
        lda #0                          // 0 = laden (niet vergelijken)
        ldx #<KAMER_BUF
        ldy #>KAMER_BUF
        jsr LOAD
        bcc !+
        ldx kamer                       // niet gevonden: de verkeerde diskette? Vraag om de goede en probeer opnieuw
        jsr diskette_vragen
        jmp opnieuw
!:      lda #0
        sta laad_fout
        ldx kamer                       // de scripts van de kamer (<KAMER>.S) erachter, op KAMER_SCRIPTS
        lda kamer_sbestand_len,x
        pha
        ldy kamer_sbestand_hi,x
        lda kamer_sbestand_lo,x
        tax
        pla
        jsr SETNAM
        lda #1
        ldx #8
        ldy #0
        jsr SETLFS
        lda #0
        ldx #<KAMER_SCRIPTS
        ldy #>KAMER_SCRIPTS
        jsr LOAD
        bcc !+
        lda #2                          // 2: het scriptbestand ontbreekt
        sta laad_fout
!:
        jsr tod_lezen                   // laadtijd in tienden
        lda tod_nu
        sec
        sbc begin
        sta laadtijd
        lda tod_nu + 1
        sbc begin + 1
        sta laadtijd + 1
        inc laad_teller
        jsr kamer_tonen
        jmp laden_einde
kamer:  .byte 0
begin:  .word 0
}

// diskette_vragen: "Plaats diskette N en druk op vuur." (N = de diskette van kamer X) en wachten. In de testbuild
// wacht hij tot tools/vicetest.py de goede diskette in VICE heeft gestopt (die zet schijf_nodig weer op 0).
diskette_vragen: {
        lda kamer_schijf,x
        sta schijf_nodig
        clc
        adc #'0'
        sta tekst_diskette_nr
        inc diskette_teller
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jsr rij_wissen
        lda #<tekst_diskette
        sta zp_ptr
        lda #>tekst_diskette
        sta zp_ptr + 1
        ldx #(40 - tekst_diskette_lengte) / 2
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jsr tekst_schrijf
#if AUTOTEST
!:      lda schijf_nodig                // vicetest stopt de diskette erin
        bne !-
#else
!:      jsr vuur_nu                     // eerst loslaten, dan indrukken
        bne !-
!:      jsr vuur_nu
        beq !-
!:      jsr vuur_nu
        bne !-
        lda #0
        sta schijf_nodig
#endif
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jsr rij_wissen
        lda #<tekst_laden
        sta zp_ptr
        lda #>tekst_laden
        sta zp_ptr + 1
        ldx #(40 - tekst_laden_lengte) / 2
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jmp tekst_schrijf
}

// vuur_nu: A != 0 als vuur (joystick 2), spatie of de linker muisknop nu ingedrukt is (zonder IRQ's: direct uit de CIA)
vuur_nu: {
        lda #$7f                        // rij 7 van het toetsenbord: spatie is bit 4
        sta $dc00
        lda $dc01
        and #$10
        beq ja
        lda #$ff                        // geen toetsen: dan is $dc00 de joystick in poort 2 (vuur = bit 4)
        sta $dc00
        lda $dc00
        and #$10
        beq ja
        lda $dc01                       // poort 1: de muisknop (links = bit 4)
        and #$10
        beq ja
        lda #0
        rts
ja:     lda #1
        rts
}

// laden_begin: raster-IRQ's uit, tekstmodus, kamer leeg, sprites uit, "Laden..."
laden_begin:
        lda #<tekst_laden
        ldx #>tekst_laden
        ldy #tekst_laden_lengte
// schijf_begin: hetzelfde met een andere tekst (A/X = tekst, Y = lengte), bv. "Opslaan..."
schijf_begin: {
        sta tekst
        stx tekst + 1
        sty lengte
        sei
        lda #0
        sta $d01a                       // geen raster-IRQ's meer
        lda #$ff
        sta $d019
        lda $d015
        sta sprites_aan
        lda #0
        sta $d015
        lda #D011_TEKST
        sta $d011
        lda #D016_TEKST
        sta $d016
        cli
        jsr muziek_stop                 // de muziek staat stil (muziek.asm); een kamer zet hem zelf weer aan
        jsr geluid_stil                 // geen hangende toon (geluid.asm)
        ldy #RIJ_KAMER                  // rij 2-17: leeg (in tekstmodus zie je anders de kleuren als tekens)
!:      tya
        pha
        lda #0
        jsr rij_wissen
        pla
        tay
        iny
        cpy #RIJ_KAMER + KAMER_RIJEN
        bne !-
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jsr rij_wissen
        lda tekst
        sta zp_ptr
        lda tekst + 1
        sta zp_ptr + 1
        lda #40                         // in het midden
        sec
        sbc lengte
        lsr
        tax
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jmp tekst_schrijf
tekst:  .word 0
lengte: .byte 0
}

// laden_einde: de hoofdstuknaam terug, sprites en raster-IRQ's weer aan
laden_einde:
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jsr rij_wissen
        jsr balk_tekenen.hoofdstuk_tekenen   // balk.asm
        lda sprites_aan
        sta $d015
        jsr geluid_aan
        sei
        jsr irq_start
        cli
        rts

.segment Data
tod_nu:      .word 0
laadtijd:    .word 0                    // tienden van seconden (de laatste keer)
laad_fout:   .byte 0
laad_teller: .byte 0                    // hoe vaak er geladen is (voor de tests)
schijf_nodig: .byte 0                   // welke diskette het spel nu vraagt (0: geen); tools/vicetest.py leest dit
diskette_teller: .byte 0                // hoe vaak er om een diskette gevraagd is (voor de tests)
.encoding "screencode_mixed"
tekst_diskette: .text "Plaats diskette "
tekst_diskette_nr: .text "2 en druk op vuur."
.label tekst_diskette_lengte = * - tekst_diskette
        .byte 0
sprites_aan: .byte 0
