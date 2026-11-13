// turbo.asm — een eigen snellader (turboloader) voor de 1541 (§6.7: "een snellader kan later").
//
// Per lading stuurt het spel een klein programma naar de drive (M-W, in stukjes van 32 bytes) en start het (M-E).
// Dat programma zoekt het bestand in de directory (spoor 18), leest de sectoren met de jobqueue van de drive en
// stuurt elke byte over de DATA-lijn, bit voor bit. De C64 bepaalt het tempo: hij wisselt de CLK-lijn, de drive zet
// het volgende bit op DATA, de C64 leest na een korte wachttijd. Een badline of een sprite kan de C64 alleen
// vertragen (dan leest hij later, het bit staat er nog): het werkt dus zonder het scherm uit te zetten.
//
// Per sector: de drive meldt "klaar" door DATA laag te trekken; daarna stuurt hij eerst een lengtebyte (het aantal
// databytes, 1-254; 0 = het bestand is niet gevonden of een leesfout), dan de bytes, dan of er nog een sector komt.
//
// Valt er iets tegen (geen echte drive, zoals de virtuele drive van VICE in de tests; geen antwoord binnen een halve
// seconde; het bestand bestaat niet), dan geeft turbo_laden C = 1 terug en laadt schijf.asm gewoon via de Kernal
// (die vraagt dan ook om de andere diskette). Na een mislukking zonder antwoord blijft de turbo uit (turbo_uit).

.const TURBO_NAAM   = $0700             // in de drive: de bestandsnaam (16 tekens, met $a0 aangevuld)
.const TURBO_CODE   = $0500             // in de drive: het programma (buffer 2 en 3)

.segment Code
// turbo_vergeet: na een gewone Kernal-schijfactie (opslaan, laden): het drive-programma opnieuw sturen
turbo_vergeet:
        lda #0
        sta code_in_drive
        rts

// turbo_laden: laad bestand (naam op zp_ptr3, lengte A) naar adres X/Y (lo/hi), de laadadresbytes van het bestand
// overgeslagen. C = 0 goed, C = 1 lukt niet (laad dan via de Kernal).
turbo_laden: {
        sta lengte
        stx doel
        sty doel + 1
        lda turbo_uit
        beq !+
        sec
        rts
!:      // de naam in de drive zetten, aangevuld met $a0 (zoals in de directory)
        ldy #0
!:      cpy lengte
        bcs vul
        lda (zp_ptr3),y
        sta naam,y
        iny
        bne !-
vul:    lda #$a0
!:      cpy #16
        bcs !+
        sta naam,y
        iny
        bne !-
!:      jsr kanaal_open                  // OPEN 15,8,15
        bcc !+
        jmp mislukt
!:      lda code_in_drive                // staat het programma al in de drive? dan alleen de naam
        beq !+
        jmp alleen_naam
!:
        lda #<naam                       // de naam: M-W $0700, 16 bytes
        sta zp_ptr2
        lda #>naam
        sta zp_ptr2 + 1
        lda #<TURBO_NAAM
        ldx #>TURBO_NAAM
        ldy #16
        jsr mw
        jmp code_sturen
alleen_naam:
        lda #<naam
        sta zp_ptr2
        lda #>naam
        sta zp_ptr2 + 1
        lda #<TURBO_NAAM
        ldx #>TURBO_NAAM
        ldy #16
        jsr mw
        jmp start
code_sturen:
        lda #<drive_code                 // het programma: M-W in stukjes van 32
        sta zp_ptr2
        lda #>drive_code
        sta zp_ptr2 + 1
        lda #<TURBO_CODE
        sta adres
        lda #>TURBO_CODE
        sta adres + 1
        lda #<drive_code_lengte
        sta rest
        lda #>drive_code_lengte
        sta rest + 1
stuk:   lda rest + 1
        bne vol
        lda rest
        beq start
        cmp #32
        bcc !+
vol:    lda #32
!:      tay
        sty n
        lda adres
        ldx adres + 1
        jsr mw
        lda zp_ptr2
        clc
        adc n
        sta zp_ptr2
        bcc !+
        inc zp_ptr2 + 1
!:      lda adres
        clc
        adc n
        sta adres
        bcc !+
        inc adres + 1
!:      lda rest
        sec
        sbc n
        sta rest
        bcs stuk
        dec rest + 1
        jmp stuk
start:  lda #1                           // (vanaf nu staat het programma in de drive)
        sta code_in_drive
        ldx #15                          // M-E $0500: het programma start als de drive de opdracht krijgt
        jsr $ffc9                        // CHKOUT
        ldx #0
!:      lda me_opdracht,x
        jsr $ffd2
        inx
        cpx #5
        bne !-
        jsr $ffcc                        // CLRCHN: UNLISTEN, de drive voert de opdracht uit
        // nu het eigen protocol: interrupts uit, wachten tot de drive "klaar" zegt (DATA laag)
        sei
        lda #DD00_BANK3                  // CLK, DATA en ATN loslaten (hoog)
        sta $dd00
        sta atn_stand
        lda doel
        sta zp_ptr2
        lda doel + 1
        sta zp_ptr2 + 1
        lda #2                           // de eerste twee databytes (het laadadres) overslaan
        sta overslaan
        lda #1
        sta eerste
sector: jsr wacht_klaar
        bcs geen_antwoord
        jsr byte_lezen                   // de lengte van deze sector (0 = niet gevonden / fout)
        sta n
        bne !+
        jsr bevestig
        jmp niet_gevonden
!:
lus:    jsr byte_lezen
        ldx overslaan
        beq !+
        dec overslaan
        jmp verder
!:      ldy #0
        sta (zp_ptr2),y
        inc zp_ptr2
        bne verder
        inc zp_ptr2 + 1
verder: dec n
        bne lus
        jsr byte_lezen                   // komt er nog een sector?
        pha
        jsr bevestig                     // "gelezen": dan laat de drive DATA los
        pla
        bne sector
        lda #DD00_BANK3
        sta $dd00
        cli
        jsr kanaal_dicht
        inc turbo_teller
        clc
        rts
niet_gevonden:
        lda #DD00_BANK3
        sta $dd00
        cli
        jsr kanaal_dicht
        sec                              // (de turbo zelf werkt: probeer via de Kernal, die vraagt om de diskette)
        rts
geen_antwoord:
        lda #DD00_BANK3
        sta $dd00
        cli
        lda #1                           // geen echte drive: de turbo blijft voortaan uit
        sta turbo_uit
mislukt:
        jsr kanaal_dicht
        sec
        rts
lengte: .byte 0
doel:   .word 0
adres:  .word 0
rest:   .word 0
n:      .byte 0
overslaan: .byte 0
}

// wacht_klaar: wacht tot de drive DATA eerst loslaat en dan laag trekt (klaar met een sector). Een 1541 moet soms
// eerst de motor laten aanlopen en de kop verplaatsen: we wachten tot ~5 seconden. C = 1 bij geen antwoord.
wacht_klaar: {
        lda #0
        sta t
        sta t + 1
        lda #4
        sta t + 2
        lda eerste                       // de eerste sector: de drive kan al klaar zijn (DATA al laag)
        beq hoog
        lda #0
        sta eerste
        beq laag
hoog:   lda $dd00                        // daarna: eerst DATA los (de drive heeft de vorige sector afgesloten)
        bmi laag
        jsr tel
        bcc hoog
        rts
laag:   lda $dd00
        bpl klaar                        // bit 7 = DATA in: 0 = laag = klaar
        jsr tel
        bcc laag
        rts
klaar:  clc
        rts
tel:    inc t                            // 4 x 65536 rondjes van ~20 cycli: ~5 s. C = 1 als de tijd om is
        bne !+
        inc t + 1
        bne !+
        dec t + 2
        bne !+
        sec
        rts
!:      clc
        rts
t:      .byte 0, 0, 0
}
eerste: .byte 0

// bevestig: nog één keer ATN wisselen: "ik heb het laatste bit"; de drive laat dan DATA en CLK los
bevestig:
        lda atn_stand
        eor #%00001000                   // bit 3 = ATN uit
        sta atn_stand
        sta $dd00
        rts

// byte_lezen: 4 stappen van 2 bits: ATN wisselen, even wachten, dan DATA (bit 7) en CLK (bit 6) lezen. De eerste stap
// wacht langer: dan rekent de drive de volgende byte nog uit.
byte_lezen: {
        lda atn_stand
        eor #%00001000
        sta atn_stand
        sta $dd00
        ldy #24                          // ~120 cycli: de drive pakt eerst de volgende byte
!:      dey
        bne !-
        jsr twee_bits
        ldx #3
stap:   lda atn_stand
        eor #%00001000
        sta atn_stand
        sta $dd00
        ldy #9                           // ~45 cycli (een badline maakt het alleen langer)
!:      dey
        bne !-
        jsr twee_bits
        dex
        bne stap
        lda byte
        rts
twee_bits:
        lda $dd00                        // bit 7 = DATA, bit 6 = CLK
        asl
        rol byte
        asl
        rol byte
        rts
byte:   .byte 0
}

// mw: M-W naar de drive: A/X = adres in de drive, Y = aantal bytes, data op zp_ptr2
mw: {
        sta lo
        stx hi
        sty aantal
        ldx #15
        jsr $ffc9                        // CHKOUT
        lda #$4d                         // "M-W" in PETSCII
        jsr $ffd2
        lda #$2d
        jsr $ffd2
        lda #$57
        jsr $ffd2
        lda lo
        jsr $ffd2
        lda hi
        jsr $ffd2
        lda aantal
        jsr $ffd2
        ldy #0
!:      lda (zp_ptr2),y
        jsr $ffd2
        iny
        cpy aantal
        bne !-
        jmp $ffcc                        // CLRCHN: de drive voert het uit
lo:     .byte 0
hi:     .byte 0
aantal: .byte 0
}

kanaal_open: {
        lda #15
        ldx #8
        ldy #15
        jsr $ffba                        // SETLFS 15,8,15
        lda #0
        jsr $ffbd                        // SETNAM (geen naam)
        jmp $ffc0                        // OPEN (C = 1 bij een fout)
}

kanaal_dicht:
        jsr $ffcc
        lda #15
        jmp $ffc3                        // CLOSE 15

.segment Data
turbo_uit:    .byte 0                    // 1: geen echte drive (of er kwam geen antwoord): altijd via de Kernal
turbo_teller: .byte 0                    // hoe vaak de turbo gelukt is (voor de tests)
code_in_drive: .byte 0                   // 1: het drive-programma staat nog in de drive ($0500); 0 na een gewone
                                         //    Kernal-schijfactie (die kan de buffers van de drive gebruiken)
atn_stand:    .byte 0
me_opdracht:  .byte $4d, $2d, $45, <TURBO_CODE, >TURBO_CODE   // "M-E" $0500
naam:         .fill 16, 0

// ---- het programma in de drive (6502, op $0500 in de 1541) ------------------------------------------------------
// $1800 (VIA 1, poort B): bit 0 DATA in, bit 1 DATA uit, bit 2 CLK in, bit 3 CLK uit (uit: 1 = trek laag).
// Jobqueue: job 0 op $00 (buffer $0300), spoor/sector op $06/$07; $80 = lezen; klaar als $00 < $80 (1 = goed).
drive_code:
drv: {                                   // (eigen namen: niet botsen met de rest van het spel)
.pseudopc TURBO_CODE {
d_start:
        lda #18                          // de directory: spoor 18, sector 1
        sta $06
        lda #1
        sta $07
d_dir:  jsr d_lees
        bcc !+
        jmp d_fout
!:
        ldx #2                           // 8 namen per sector, elk 32 bytes: type op +0, spoor/sector +1/+2, naam +3
d_naam: lda $0300,x
        and #$07                         // een gewoon bestand (PRG, gesloten): type $82
        cmp #$02
        bne d_volgende
        ldy #0
!:      lda $0303,x
        cmp TURBO_NAAM,y
        bne d_volgende
        inx
        iny
        cpy #16
        bne !-
        txa                              // gevonden: x wees 16 verder; spoor/sector staan op -16+1 en -16+2
        sec
        sbc #16
        tax
        lda $0301,x
        sta $06
        lda $0302,x
        sta $07
        jmp d_bestand
d_volgende:
        txa
        and #$e0
        clc
        adc #$22
        tax
        bcc d_naam                        // (na de achtste naam loopt x over: volgende directorysector)
        lda $0300                        // de volgende directorysector
        bne !+
        jmp d_fout                       // (spoor 0: het einde van de directory: niet gevonden)
!:
        sta $06
        lda $0301
        sta $07
        jmp d_dir

d_bestand:
        jsr d_lees
        bcc !+
        jmp d_fout
!:
        ldx #254                         // hoeveel databytes: 254, of (laatste sector) byte 1 - 1
        lda $0300
        bne !+
        ldx $0301
        dex
!:      stx d_n
        jsr d_klaar                      // DATA laag: "er komt een sector"
        lda d_n
        jsr d_stuur
        ldx #2
!:      lda $0300,x
        stx d_x
        jsr d_stuur
        ldx d_x
        inx
        dec d_n
        bne !-
        lda $0300                        // nog een sector? (spoor != 0)
        jsr d_stuur
        jsr d_los
        lda $0300
        beq d_einde
        sta $06
        lda $0301
        sta $07
        jmp d_bestand
d_einde:
        lda $1800                        // alles los (ATNA gelijk aan ATN)
        and #$80
        lsr
        lsr
        lsr
        sta $1800
        lda $1801                        // de ATN-vlag van ons protocol wissen
        cli
        rts                              // terug naar de DOS
d_fout: jsr d_klaar
        lda #0                           // lengte 0: niet gevonden of een leesfout
        jsr d_stuur
        jsr d_los
        jmp d_einde

// d_lees: lees spoor $06 sector $07 in $0300 (met de jobqueue; interrupts aan, die doen het werk). C = 1 bij een fout
d_lees: lda $1801                        // (een ATN-flank van ons protocol mag de DOS niet storen: vlag wissen)
        cli
        lda #$80
        sta $00
!:      lda $00
        bmi !-
        sei
        cmp #1
        beq !+
        sec
        rts
!:      clc
        rts

// d_klaar: trek DATA laag ("klaar"); ATNA (bit 4) gelijk aan ATN (bit 7), anders trekt de 1541 zelf DATA laag
d_klaar:
        sei
        lda $1800
        and #$80
        sta d_atn
        lsr
        lsr
        lsr
        ora #%00000010                   // DATA laag
        sta $1800
        rts

// d_stuur: verstuur A in 4 stappen van 2 bits (hoogste eerst): het eerste bit van een paar op DATA, het tweede op CLK.
// Per stap: wacht tot de C64 ATN wisselt, zet dan meteen de lijnen (met ATNA gelijk aan de nieuwe stand van ATN).
// Uit-bits zijn omgekeerd: 1 = trek laag = de C64 leest 0.
d_stuur:
        sta d_byte
        ldx #4
d_stap: ldy #0                           // het volgende paar klaarzetten, nog vóór het wachten:
        asl d_byte
        bcs !+
        ldy #%00000010                   // eerste bit 0: DATA laag
!:      asl d_byte
        bcs !+
        tya
        ora #%00001000                   // tweede bit 0: CLK laag
        tay
!:      sty d_paar
!:      lda $1800                        // wacht op een wissel van ATN
        eor d_atn
        bpl !-
        lda d_atn
        eor #$80
        sta d_atn
        lsr
        lsr
        lsr
        ora d_paar                       // de twee bits, met ATNA gelijk aan ATN
        sta $1800
        dex
        bne d_stap
        rts

// d_los: wacht op de bevestiging van de C64 (nog een ATN-wissel), laat dan DATA en CLK los
d_los:  lda $1800
        eor d_atn
        bpl d_los
        lda d_atn
        eor #$80
        sta d_atn
        lsr
        lsr
        lsr
        sta $1800
        rts

d_paar: .byte 0
d_n:    .byte 0
d_x:    .byte 0
d_atn:  .byte 0
d_byte: .byte 0
}
}
.label drive_code_lengte = * - drive_code
.assert "het drive-programma past in buffer 2 en 3 ($0500-$06FF)", drive_code_lengte <= $200, true
