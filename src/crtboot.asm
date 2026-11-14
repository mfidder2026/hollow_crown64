// crtboot.asm — het opstarten van de EasyFlash-cartridge (tools/crt.py zet het aan het eind van ROMH, bank 0).
// Assembleren: build.sh, met :autotaal=0 (het taalmenu) of 1-4 (de testbuild: meteen die taal, zonder te vragen).
//
// Een EasyFlash start in de Ultimax-stand: ROMH van bank 0 staat op $E000-$FFFF, het RAM alleen op $0000-$0FFF.
//   A ($FE00, uit de ROM): kopieer B en C naar $0800 en ga daarheen.
//   B ($0800): de cartridge uit ($DE02 = $04: overal RAM, Kernal en I/O); kopieer C naar $C000 en ga daarheen.
//   C ($C000): de C64 klaarzetten (zoals de Kernal bij een reset), het taalmenu (src/taalmenu.asm: het aardmannetje
//      met de vlaggen) uit de cartridge naar $4400 halen en aanroepen, en dan het programma van de gekozen taal
//      (16K-stand: $8000-$BFFF per bank) naar $0801; de cartridge uit; het spel starten.
// De tabel op $8000 in bank 0 (tools/crt.py): per taal (en daarna het menu) bank, adres (lo, hi), lengte (lo, hi),
// start (lo, hi), en 1 als hij er is.

.const AUTOTAAL  = cmdLineVars.get("autotaal").asNumber()
.const EF_BANK   = $de00
.const EF_MODUS  = $de02
.const EF_UIT    = $04                 // geen cartridge: gewoon RAM, Kernal en I/O
.const EF_16K    = $07                 // ROML $8000-$9FFF, ROMH $A000-$BFFF
.const TABEL     = $8000
.const REGEL     = 8
.const BRON      = $fb
.const DOEL      = $fd
.const MENU_ADRES = $4400             // src/taalmenu.asm
.const MENU_REGEL = 4                   // in de talentabel: de regel na de vier talen (tools/crt.py)

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
} else {
        lda #<MENU_ADRES                // het taalmenu (src/taalmenu.asm) uit de cartridge, en aanroepen: X = de taal
        sta DOEL
        lda #>MENU_ADRES
        sta DOEL + 1
        ldy #MENU_REGEL * REGEL
        jsr kopieer
        jsr MENU_ADRES
}
gekozen:
        txa                             // de regel van die taal in de tabel
        asl
        asl
        asl
        tay
        lda #<$0801
        sta DOEL
        lda #>$0801
        sta DOEL + 1
        jsr kopieer
        jmp (start)

// kopieer: regel Y van de tabel (bank, adres, lengte, start) naar DOEL; daarna staat de cartridge uit
kopieer:
        lda #EF_16K
        sta EF_MODUS
        lda #0
        sta EF_BANK
        lda #$37                        // LORAM en HIRAM: de ROM van de cartridge zichtbaar
        sta $01
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
        ldy #0
lus:    lda bank
        sta EF_BANK
        lda (BRON),y
        sta (DOEL),y                    // (onder de ROM van de cartridge ligt RAM: daar komt het terecht)
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
        rts

bank:   .byte 0
rest:   .word 0
start:  .word 0
}

nmi:
irq:    rti
        * = $fffa
        .word nmi, reset, irq
