// opslaan.asm — opslaan (F5) en laden (F7) van de spelstatus (§6.4, §6.7).
//
// Opslaan: eerst scratchen ("S0:HCSAVE" op kanaal 15), dan SAVE. Nooit "@0:": bekende fout in de 1541.
// Laden: LOAD naar opslag_buf; alleen met de juiste magic ("HC") en versie wordt het de spelstatus; dan naar de
// kamer uit de spelstatus (laden van de diskette). Tijdens de diskette: zoals bij het laden van een kamer
// (schijf.asm). Na opslaan staat dezelfde kamer er weer (plaatje uit de kamerbuffer + BINNENKOMST voor de patches).

.const SAVE   = $ffd8
.const OPEN   = $ffc0
.const CLOSE  = $ffc3

.segment Code
opslaan: {
        lda act_x                       // de plek van nu in de spelstatus
        sta st_x
        lda act_x + 1
        sta st_x + 1
        lda act_y
        sta st_y
        lda #<tekst_opslaan
        ldx #>tekst_opslaan
        ldy #tekst_opslaan_lengte
        jsr schijf_begin
        // scratchen: OPEN 15,8,15,"S0:HCSAVE" en CLOSE 15
        lda #naam_scratch_lengte
        ldx #<naam_scratch
        ldy #>naam_scratch
        jsr SETNAM
        lda #15
        ldx #8
        ldy #15
        jsr SETLFS
        jsr OPEN
        lda #15
        jsr CLOSE
        // SAVE "HCSAVE",8: van spelstatus tot spelstatus_eind
        lda #naam_opslag_lengte
        ldx #<naam_opslag
        ldy #>naam_opslag
        jsr SETNAM
        lda #1
        ldx #8
        ldy #1
        jsr SETLFS
        lda #<spelstatus
        sta zp_ptr
        lda #>spelstatus
        sta zp_ptr + 1
        lda #zp_ptr                     // A = de zeropage-plek met het beginadres
        ldx #<spelstatus_eind
        ldy #>spelstatus_eind
        jsr SAVE
        lda #0
        bcc !+
        lda #1
!:      sta opslag_fout
        inc opslag_teller
        jsr kamer_terug
        lda opslag_fout
        bne fout
        lda #<tekst_opgeslagen
        ldx #>tekst_opgeslagen
        jmp melding
fout:   lda #<tekst_opslaan_fout
        ldx #>tekst_opslaan_fout
        jmp melding
}

laden_spel: {
        lda #<tekst_spel_laden
        ldx #>tekst_spel_laden
        ldy #tekst_spel_laden_lengte
        jsr schijf_begin
        lda #naam_opslag_lengte
        ldx #<naam_opslag
        ldy #>naam_opslag
        jsr SETNAM
        lda #1
        ldx #8
        ldy #0
        jsr SETLFS
        lda #0
        ldx #<opslag_buf
        ldy #>opslag_buf
        jsr LOAD
        bcs niets
        lda opslag_buf                  // magic en versie
        cmp #'H'
        bne niets
        lda opslag_buf + 1
        cmp #'C'
        bne niets
        lda opslag_buf + 2
        cmp #STATUS_VERSIE
        bne niets
        ldx #0                          // het wordt de spelstatus (meer dan 128 bytes: optellen, geen bpl)
!:      lda opslag_buf,x
        sta spelstatus,x
        inx
        cpx #STATUS_GROOTTE
        bne !-
        inc opslag_teller
        jsr laden_einde
        lda st_x                        // naar de opgeslagen kamer en plek
        sta kw_x
        lda st_x + 1
        sta kw_x + 1
        lda st_y
        sta kw_y
        lda #0
        sta kw_richting
        lda #1
        sta inventaris_anders
        lda st_kamer
        jsr kamer_wissel
        lda #<tekst_geladen
        ldx #>tekst_geladen
        jmp melding_na
niets:  jsr kamer_terug
        lda #<tekst_niets_opgeslagen
        ldx #>tekst_niets_opgeslagen
        jmp melding
}

// kamer_terug: na de diskette dezelfde kamer weer tonen (plaatje uit de kamerbuffer, BINNENKOMST voor de patches)
kamer_terug:
        jsr kamer_tonen
        jsr laden_einde
        ldx st_kamer
        lda kamer_binnen_hi,x
        beq !+
        pha
        lda kamer_binnen_lo,x
        tay
        pla
        tax
        tya
        jmp vm_start
!:      rts

// melding: een korte tekst van Eldric (A/X = tekst, schermcodes, 0 aan het eind)
melding:
        sta zp_ptr
        stx zp_ptr + 1
        lda #120
        sta bericht_tijd
        lda #0
        sta bericht_tijd + 1
        lda spreker_kleur               // in de kleur van de eerste spreker (Eldric)
        jmp bericht_zeg
// melding_na: zoals melding, maar pas als BINNENKOMST klaar is (het script zou de tekst anders weghalen)
melding_na:
        sta melding_wacht
        stx melding_wacht + 1
        rts

// melding_beeld: elk beeld; een uitgestelde melding tonen als er geen script meer loopt
melding_beeld:
        lda melding_wacht + 1
        beq !+
        lda vm_pc + 1
        bne !+
        lda melding_wacht
        ldx melding_wacht + 1
        ldy #0
        sty melding_wacht + 1
        jmp melding
!:      rts

// functietoetsen: F1 muziek aan/uit; F5 opslaan, F7 laden (alleen als je mag klikken: geen script, gesprek of tussenscène)
functietoetsen: {
        lda toets_rij0                  // F1 (kolom 4): muziek aan/uit, altijd
        and #%00010000
        tax
        eor f1_vorig
        and toets_rij0
        stx f1_vorig
        and #%00010000
        beq !+
        jsr muziek_f1
!:      lda toets_rij0
        and #%01001000                  // F5 = kolom 6, F7 = kolom 3
        tax
        eor ft_vorig
        and toets_rij0                  // nieuw ingedrukt
        stx ft_vorig
        sta nieuw
        beq klaar
        lda vm_pc + 1
        ora gs_actief
        ora act_lopen
        bne klaar
        lda nieuw
        and #%01000000
        beq !+
        jmp opslaan
!:      lda nieuw
        and #%00001000
        beq klaar
        jmp laden_spel
klaar:  rts
nieuw:  .byte 0
}

.segment Code
// voltooid_beeld: staat de doelvlag van dit hoofdstuk, dan één keer "Hoofdstuk n voltooid" onderaan en het klaar-geluid
voltooid_beeld: {
        lda voltooid
        bne klaar
        ldy st_hoofdstuk
        lda hoofdstuk_doel,y            // de vlag: byte vlag / 8, bit vlag & 7
        pha
        lsr
        lsr
        lsr
        tax
        pla
        and #7
        tay
        lda st_vlaggen,x
        and bits8,y
        beq klaar
        lda vm_pc + 1                   // pas als het laatste script klaar is
        bne klaar
        inc voltooid
        ldy #RIJ_ONDER
        lda #KLEUR_HOOFDSTUK
        jsr rij_wissen
        ldy st_hoofdstuk
        lda hoofdstuk_klaar_lo,y
        sta zp_ptr
        lda hoofdstuk_klaar_hi,y
        sta zp_ptr + 1
        lda #40
        sec
        sbc hoofdstuk_klaar_lengte,y
        lsr
        tax
        ldy #RIJ_ONDER
        lda #KLEUR_VOLTOOID
        jsr tekst_schrijf
        lda #GL_KLAAR
        jmp geluid_speel
klaar:  rts
}
bits8: .byte 1, 2, 4, 8, 16, 32, 64, 128
voltooid: .byte 0                       // 1: het hoofdstuk is uitgespeeld (voor de tests)

.segment Data
.encoding "petscii_upper"
naam_scratch: .text "S0:HCSAVE"
.label naam_scratch_lengte = * - naam_scratch
naam_opslag:  .text "HCSAVE"
.label naam_opslag_lengte = * - naam_opslag
.encoding "screencode_mixed"
opslag_fout:   .byte 0
opslag_teller: .byte 0                  // hoe vaak er opgeslagen of geladen is (voor de tests)
ft_vorig:      .byte 0
melding_wacht: .word 0

.segment Buffers
.segment Hoog                           // $C800-$CFFF (geheugen.asm)
opslag_buf:    .fill 256, 0                // (de spelstatus past in 1 pagina: status.asm)
.segment Buffers
