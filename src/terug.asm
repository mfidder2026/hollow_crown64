// terug.asm — Tik de Terugdraaier (scenario §2): het ankerpunt en terugdraaien.
//
// Bij het binnenkomen van elke kamer bewaart de motor een kopie van de spelstatus (anker_zetten, vanuit kamer.asm):
// dat is het ankerpunt. Gaat Eldric dood, dan zegt Tik iets droogs en biedt hij aan: "Terugdraaien?". De opdracht
// TERUG zet de spelstatus terug op het ankerpunt en begint de kamer opnieuw, zonder te laden: het plaatje en de
// scripts staan nog in de kamerbuffer. Vlaggen, voorwerpen, de stand van de figuren: alles zoals bij binnenkomst.

.segment Code
// anker_zetten: de spelstatus van nu is het ankerpunt (bij binnenkomst van een kamer)
anker_zetten: {
        ldx #0
!:      lda spelstatus,x
        sta anker_buf,x
        inx
        cpx #STATUS_GROOTTE
        bne !-
        lda kw_richting
        sta anker_richting
        rts
}

// terug_naar_anker: alles terug zoals bij binnenkomst van deze kamer, en BINNENKOMST opnieuw
terug_naar_anker: {
        jsr vm_stop
        lda gs_actief                   // een gesprek (het "Terugdraaien?" van Tik) is voorbij
        beq !+
        jsr gesprek_stop
!:      ldx #0
!:      lda anker_buf,x
        sta spelstatus,x
        inx
        cpx #STATUS_GROOTTE
        bne !-
        jsr kamer_tonen                 // het plaatje uit de kamerbuffer (zonder patches: BINNENKOMST zet ze)
        ldx st_kamer
        jsr kamer_gegevens
        jsr npc_begin                   // de figuren op hun beginplek
        lda st_x                        // Eldric op zijn plek van binnenkomst
        sta act_x
        lda st_x + 1
        sta act_x + 1
        lda st_y
        sta act_y
        lda anker_richting
        sta act_richting
        lda #1
        sta act_zichtbaar               // (een dood kan hem verborgen hebben: VERBERG eldric)
        lda #0
        sta act_lopen
        sta actie_bezig
        lda #$ff
        sta act_pose
        sta zin_eerste                  // (GEEN_VOORWERP)
        lda #$fe
        sta zin_ww
        lda #1
        sta inventaris_anders
        jsr vergeet_laatst              // zin.asm
        jsr npc_kamer_in
        inc terug_teller
        ldx st_kamer                    // BINNENKOMST
        lda kamer_binnen_hi,x
        beq klaar
        pha
        lda kamer_binnen_lo,x
        tay
        pla
        tax
        tya
        jmp vm_start
klaar:  rts
}

.segment Data
anker_richting: .byte 0
terug_teller:   .byte 0                 // hoe vaak er teruggedraaid is (voor de tests)

.segment Buffers
.segment Hoog                           // $C800-$CFFF (geheugen.asm)
anker_buf:      .fill 256, 0            // de spelstatus bij binnenkomst (past in 1 pagina: status.asm)
.segment Buffers
