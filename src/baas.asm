// baas.asm — de baas-toets (menu Bosskey): in één klap een rekenblad in plaats van het spel.
//
// Terug: eerst het beeld zwart (scherm_uit, irq.asm), dan alles herstellen, en pas als BINNENKOMST klaar is weer aan:
// zo zie je nooit de letters van het rekenblad als kleuren in de kamer.
// Het hele scherm wordt tekst (de IRQ schakelt niet meer naar de bitmap: irq.asm kijkt naar baas_actief), witte
// achtergrond, geen sprites, de muziek stil. Het rekenblad komt uit tools/baas.py. Een toets, de joystick of de muis
// brengt het spel terug, precies zoals het was: het plaatje uit de kamerbuffer, BINNENKOMST (patches, muziek), de balk.

#import "../build/gen/baas.asm"

.segment Code
baas_aan: {
        lda $d015                       // de sprites straks terug (zoals bij het laden: schijf.asm)
        sta sprites_aan
        lda #0
        sta $d015
        jsr muziek_uit                  // stil; BINNENKOMST zet de muziek straks weer aan
        jsr geluid_stil
        lda #1
        sta baas_actief                 // vanaf nu blijft het hele scherm tekst (irq.asm)
        lda $d020
        sta rand_was
        lda #12                         // grijze rand, witte achtergrond
        sta $d020
        lda #1
        sta $d021
        lda #<baas_ingepakt             // het rekenblad: 1000 schermcodes, ingepakt (tools/baas.py)
        sta zp_ptr
        lda #>baas_ingepakt
        sta zp_ptr + 1
        lda #<SCHERM
        sta zp_ptr2
        lda #>SCHERM
        sta zp_ptr2 + 1
        jsr uitpak
        ldx #0                          // de kleur: één per rij
rij:    lda rij_lo,x
        sta zp_ptr3
        lda rij_hi,x
        clc
        adc #>KLEUR_OFFSET
        sta zp_ptr3 + 1
        lda baas_kleur,x
        ldy #39
!:      sta (zp_ptr3),y
        dey
        bpl !-
        inx
        cpx #25
        bne rij
        lda #1                          // eerst alles los, dan een nieuwe toets
        sta baas_los_nodig
        inc baas_teller
        rts
}

// baas_beeld: elk beeld (main.asm); zolang het rekenblad er staat doet het spel verder niets
baas_beeld: {
        lda #0                          // geen sprites (in het beeld van de klik zette de hoofdlus ze nog aan)
        sta $d015
        jsr invoer_lees
        lda invoer_stick                // iets ingedrukt? (stick, vuur, cursortoetsen, spatie, muisknop)
        ora toets_rij0
        ora toets_rij1
        ora toets_rij6
        ora toets_rij7
        ldx baas_los_nodig
        beq !+
        cmp #0                          // wacht eerst tot alles los is (de klik op Bosskey zelf)
        bne klaar
        lda #0
        sta baas_los_nodig
        rts
!:      cmp #0
        beq klaar
        jmp baas_uit
klaar:  rts
}

baas_uit:
        jsr scherm_uit                  // eerst zwart: geen rekenblad-letters als kleuren tijdens het herstellen
        lda beelden                     // één beeld wachten: de IRQ's hebben het nu uitgezet
!:      cmp beelden
        beq !-
        lda #1
        sta baas_terug                  // main.asm zet het beeld weer aan als BINNENKOMST klaar is
        lda #0
        sta baas_actief
        sta $d021
        lda rand_was
        sta $d020
        ldy #0                          // rij 0-1 en de balk weer zoals in het spel
        lda #0
        jsr rij_wissen
        ldy #1
        lda #0
        jsr rij_wissen
        jsr balk_tekenen
        lda #1
        sta inventaris_anders
        lda #$fe
        sta zin_ww
        jmp kamer_terug                 // opslaan.asm: plaatje, IRQ's, sprites, BINNENKOMST

.segment Data
baas_actief:    .byte 0                 // 1: het rekenblad staat er (voor irq.asm en de tests)
baas_los_nodig: .byte 0
baas_teller:    .byte 0                 // hoe vaak de baas-toets gebruikt is (voor de tests)
baas_terug:     .byte 0                 // 1: het spel wordt hersteld; het beeld blijft zwart tot het klaar is
rand_was:       .byte 0
