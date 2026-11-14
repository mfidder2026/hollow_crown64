// cartridge.asm — laden uit een EasyFlash-cartridge (1 MB; build.sh, build/hollowcrown.crt, tools/crt.py).
//
// De cartridge: $DE00 = de bank (0-63), $DE02 = de stand ($04 uit: gewoon RAM; $07 16K: ROML op $8000-$9FFF, ROMH op
// $A000-$BFFF; $05 Ultimax: zo start hij). Per bank 16 KB, van $8000 tot $BFFF. Bank 0: de talentabel ($8000), de
// inhoudsopgave (CRT_INHOUD) en aan het eind van ROMH het opstarten (src/crtboot.asm). Inhoudsopgave: per bestand
// 16 tekens naam (aangevuld met $a0), bank, adres (lo, hi), lengte (lo, hi); een 0 als eerste teken = het einde. De
// bestanden staan zonder hun laadadres achter elkaar, over de banken heen. Elke taal heeft een eigen programma en
// eigen kamerscripts (<kamer>.S, .E, .D, .F); de plaatjes zijn voor alle talen gelijk.
//
// En: de ROM van de cartridge is alleen zichtbaar met LORAM en HIRAM aan ($01 = $37); het spel draait met $36.
// Tijdens het lezen dus $37 (de interrupts staan dan uit), daarna weer $36.
//
// LET OP: zolang de cartridge aan staat, ziet de processor op $8000-$9FFF de ROM, niet het programma. Deze code en
// alles wat ze leest staan daarom onder $8000 (segment Code), en de interrupts staan uit (de IRQ leest daar wel).
// Om de 256 bytes gaat de cartridge even uit, zodat de IRQ (muziek, de splitsing van het scherm) door kan.

.const CRT_BANK    = $de00
.const CRT_MODUS   = $de02
.const CRT_UIT     = $04
.const CRT_16K     = $07
.const CRT_ULTIMAX = $05
.const CRT_INHOUD  = $8100
.const CRT_REGEL   = 21                 // 16 naam + bank + adres (2) + lengte (2)
.label crt_bron    = $fb                // eigen wijzers (de IRQ gebruikt zp_ptr en zp_ptr2: tussen de pagina's door
.label crt_doel    = $fd                //  mag hij lopen, dus die kunnen we hier niet gebruiken)

.segment Code
// cart_laden: zoals turbo_laden (turbo.asm): bestand (naam op zp_ptr3, lengte A) naar adres X/Y (lo/hi), zonder de
// laadadresbytes. C = 0 goed, C = 1 niet gevonden.
cart_laden: {
        php                             // (de IRQ mag zp_ptr3 niet veranderen terwijl we de naam overnemen)
        sei
        sta lengte
        stx crt_doel
        sty crt_doel + 1
        ldy #0                          // de naam naar hier (onder $8000), aangevuld met $a0
!:      cpy lengte
        bcs vul
        lda (zp_ptr3),y
        sta naam,y
        iny
        bne !-
vul:    lda #$a0
!:      cpy #16
        bcs zoek
        sta naam,y
        iny
        bne !-
zoek:   lda #$37                        // de ROM van de cartridge zichtbaar (zie boven)
        sta $01
        lda #0                          // bank 0: de inhoudsopgave
        sta CRT_BANK
        lda #CRT_16K
        sta CRT_MODUS
        lda #<CRT_INHOUD
        sta crt_bron
        lda #>CRT_INHOUD
        sta crt_bron + 1
regel:  ldy #0
        lda (crt_bron),y
        beq niet
!:      lda (crt_bron),y
        cmp naam,y
        bne volgende
        iny
        cpy #16
        bne !-
        lda (crt_bron),y                // gevonden: bank, adres, lengte
        sta bank
        iny
        lda (crt_bron),y
        pha
        iny
        lda (crt_bron),y
        tax
        iny
        lda (crt_bron),y
        sta teller
        iny
        lda (crt_bron),y
        sta teller + 1
        stx crt_bron + 1
        pla
        sta crt_bron
        jmp kopieer
volgende:
        lda crt_bron
        clc
        adc #CRT_REGEL
        sta crt_bron
        bcc regel
        inc crt_bron + 1
        jmp regel
niet:   lda #CRT_UIT
        sta CRT_MODUS
        lda #CPU_NORMAAL
        sta $01
        plp
        sec
        rts

kopieer:
        lda teller                      // lengte 0? klaar
        ora teller + 1
        beq klaar
        lda bank
        sta CRT_BANK
        ldy #0
        lda (crt_bron),y
        sta (crt_doel),y
        inc crt_bron                    // de bron: aan het eind van een bank verder in de volgende
        bne !+
        inc crt_bron + 1
        lda crt_bron + 1
        cmp #$c0                        // 16 KB per bank: na $BFFF verder in de volgende
        bne !+
        lda #$80
        sta crt_bron + 1
        inc bank
!:      lda teller
        bne !+
        dec teller + 1
!:      dec teller
        inc crt_doel
        bne kopieer
        inc crt_doel + 1
        lda #CRT_UIT                    // een pagina klaar: even de cartridge uit en de IRQ laten gaan (muziek, de
        sta CRT_MODUS                   //  splitsing van het scherm); hij gebruikt crt_bron en crt_doel niet
        lda #CPU_NORMAAL
        sta $01
        plp
        php
        sei
        lda #$37
        sta $01
        lda #CRT_16K
        sta CRT_MODUS
        jmp kopieer
klaar:  lda #CRT_UIT
        sta CRT_MODUS
        lda #CPU_NORMAAL
        sta $01
        plp
        clc
        rts

lengte: .byte 0
bank:   .byte 0
teller: .word 0
.segment Laag                           // $0400-$07FF (geheugen.asm): onder $8000, elke keer opnieuw gevuld
naam:   .fill 16, 0
.segment Code
}

// taal_kiezen: terug naar het taalmenu van de cartridge (src/crtboot.asm): bank 0, de Ultimax-stand, en dan via de
// resetvector van de cartridge. In de Ultimax-stand is alleen $0000-$0FFF RAM: het laatste stukje staat daarom op $0340.
taal_kiezen: {
        sei
        lda #0                          // eerst het beeld zwart en stil (anders rommel op het scherm tijdens de wissel)
        sta $d015
        sta $d01a
        lda #$0b
        sta $d011
        jsr geluid_stil
        lda act_x                       // de spelstatus bewaren (opstart.asm taal_terug haalt hem terug)
        sta st_x
        lda act_x + 1
        sta st_x + 1
        lda act_y
        sta st_y
        ldx #0
!:      lda spelstatus,x
        sta TAAL_BEWAAR,x
        inx
        cpx #STATUS_GROOTTE
        bne !-
        ldx #stukje_eind - stukje - 1
!:      lda stukje,x
        sta $0340,x
        dex
        bpl !-
        jmp $0340
stukje:
.pseudopc $0340 {
        lda #0
        sta CRT_BANK
        lda #CRT_ULTIMAX
        sta CRT_MODUS
        jmp ($fffc)
}
stukje_eind:
}

