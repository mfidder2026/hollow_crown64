// crtboot.asm — het opstarten van de EasyFlash-cartridge (tools/crt.py zet het aan het eind van ROMH, bank 0).
// Assembleren: build.sh, met :autotaal=0 (het taalmenu) of 1-4 (de testbuild: meteen die taal, zonder te vragen).
//
// Een EasyFlash start in de Ultimax-stand: ROMH van bank 0 staat op $E000-$FFFF, het RAM alleen op $0000-$0FFF.
//   A ($FE00, uit de ROM): kopieer B en C naar $0800 en ga daarheen.
//   B ($0800): de cartridge uit ($DE02 = $04: overal RAM, Kernal en I/O); kopieer C naar $C000 en ga daarheen.
//   C ($C000): de C64 klaarzetten (zoals de Kernal bij een reset), het taalmenu, en het programma van die taal uit
//      de cartridge halen (16K-stand: $8000-$BFFF per bank) naar $0801; de cartridge uit; het spel starten.
// De talen: een tabel op $8000 in bank 0 (tools/crt.py): per taal bank, adres (lo, hi), lengte (lo, hi), start
// (lo, hi), en 1 als de taal er is.

.const AUTOTAAL  = cmdLineVars.get("autotaal").asNumber()
.const EF_BANK   = $de00
.const EF_MODUS  = $de02
.const EF_UIT    = $04                 // geen cartridge: gewoon RAM, Kernal en I/O
.const EF_16K    = $07                 // ROML $8000-$9FFF, ROMH $A000-$BFFF
.const TABEL     = $8000
.const REGEL     = 8
.const BRON      = $fb
.const DOEL      = $fd
.const CHROUT    = $ffd2
.const GETIN     = $ffe4

.file [name="crtboot.bin", type="bin", segments="Boot"]
.segmentdef Boot [start=$fe00, min=$fe00, max=$ffff, fill]
.segment Boot
reset:  sei
        ldx #$ff
        txs
        cld
        ldx #0
!:      lda stub,x                      // B en C naar $0800 (in de Ultimax-stand is daar RAM)
        sta $0800,x
        lda stub + $100,x
        sta $0900,x
        inx
        bne !-
        jmp $0800

stub:
.pseudopc $0800 {
        lda #EF_UIT                     // B: de cartridge uit
        sta EF_MODUS
        ldx #0
!:      lda c_bron,x
        sta $c000,x
        lda c_bron + $100,x
        sta $c100,x
        inx
        bne !-
        jmp $c000
c_bron:
}
.pseudopc $c000 {
        jsr $fda3                       // C: IOINIT, RAMTAS, RESTOR, CINT
        jsr $fd50
        jsr $fd15
        jsr $ff5b
.if (AUTOTAAL > 0) {
        ldx #AUTOTAAL - 1
        jmp gekozen
} else {
        lda #0                          // zwart scherm, witte letters
        sta $d020
        sta $d021
        ldx #0
!:      lda menu_tekst,x
        beq wacht
        jsr CHROUT
        inx
        bne !-
wacht:  jsr GETIN                       // een toets 1-4
        sec
        sbc #'1'
        cmp #4
        bcs wacht
        tax
        jsr er                          // (is die taal er?)
        beq wacht
}
gekozen:
        lda #EF_16K
        sta EF_MODUS
        lda #0
        sta EF_BANK
        lda #$37                        // LORAM en HIRAM: de ROM van de cartridge zichtbaar
        sta $01
        txa                             // de regel van die taal in de tabel
        asl
        asl
        asl
        tay
        lda TABEL,y
        sta bank
        lda TABEL + 1,y
        sta BRON
        lda TABEL + 2,y
        sta BRON + 1
        lda TABEL + 3,y
        sta rest
        lda TABEL + 4,y
        sta rest + 1
        lda TABEL + 5,y
        sta start
        lda TABEL + 6,y
        sta start + 1
        lda #<$0801
        sta DOEL
        lda #>$0801
        sta DOEL + 1
        ldy #0
lus:    lda bank
        sta EF_BANK
        lda (BRON),y
        sta (DOEL),y
        inc BRON
        bne !+
        inc BRON + 1
        lda BRON + 1
        cmp #$c0                        // aan het eind van een bank (16 KB): de volgende
        bne !+
        lda #$80
        sta BRON + 1
        inc bank
!:      inc DOEL
        bne !+
        inc DOEL + 1
!:      lda rest
        bne !+
        dec rest + 1
!:      dec rest
        lda rest
        ora rest + 1
        bne lus
        lda #EF_UIT
        sta EF_MODUS
        jmp (start)

// er: is taal X er? (Z = 0: ja). X blijft.
er:     lda #EF_16K
        sta EF_MODUS
        lda #0
        sta EF_BANK
        lda #$37
        sta $01
        txa
        asl
        asl
        asl
        tay
        lda TABEL + 7,y
        pha
        lda #EF_UIT
        sta EF_MODUS
        pla
        rts

bank:   .byte 0
rest:   .word 0
start:  .word 0
.encoding "petscii_mixed"
menu_tekst:
        .byte $93, $05, $0e             // scherm wissen, wit, kleine letters
        .text "             HOLLOW CROWN"
        .byte $0d, $0d, $0d
        .text "  Taal / Language / Sprache / Langue"
        .byte $0d, $0d, $0d
        .text "      1  Nederlands"
        .byte $0d, $0d
        .text "      2  English"
        .byte $0d, $0d
        .text "      3  Deutsch"
        .byte $0d, $0d
        .text "      4  Francais"
        .byte $0d, 0
}

nmi:
irq:    rti
        * = $fffa
        .word nmi, reset, irq
