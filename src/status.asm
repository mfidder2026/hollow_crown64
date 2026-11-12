// status.asm — de spelstatus in één blok (§6.4). Opslaan = dit blok naar de diskette schrijven.
// tools/vicetest.py leest deze labels via build/.../hollowcrown.vs; hernoem ze dus niet zomaar.

.const STATUS_VERSIE   = 1
.const MAX_VLAGGEN     = 256            // bits
.const MAX_VOORWERPEN  = 64
.const MAX_NPC         = 16

.segment Data
spelstatus:
st_magic:     .byte 'H', 'C'           // magic: "HC" (PETSCII $48,$43)
st_versie:    .byte STATUS_VERSIE
st_kamer:     .byte 0                  // nummer van de huidige kamer
st_x:         .word 0                  // positie van Eldric (schermpixels)
st_y:         .byte 0
st_vlaggen:   .fill MAX_VLAGGEN / 8, 0
st_eigenaar:  .fill MAX_VOORWERPEN, 0  // per voorwerp: kamer, of $ff = inventaris
st_stand:     .fill MAX_VOORWERPEN, 0  // per voorwerp: stand (bv. open/dicht)
st_npc:       .fill MAX_NPC, 0         // per figuur: 1 = zichtbaar
spelstatus_eind:

.const STATUS_GROOTTE = spelstatus_eind - spelstatus
.assert "alle voorwerpen passen in de spelstatus", AANTAL_VW <= MAX_VOORWERPEN, true
.assert "alle vlaggen passen in de spelstatus", AANTAL_VLAGGEN <= MAX_VLAGGEN, true
.assert "alle figuren passen in de spelstatus", AANTAL_NPC <= MAX_NPC, true

.segment Code
// status_begin: de spelstatus van een nieuw spel (uit build/gen/spel.asm)
status_begin:
        ldx #MAX_VLAGGEN / 8 - 1
        lda #0
!:      sta st_vlaggen,x
        dex
        bpl !-
        ldx #AANTAL_VW - 1
!:      lda vw_eigenaar_begin,x
        sta st_eigenaar,x
        lda vw_stand_begin,x
        sta st_stand,x
        dex
        bpl !-
        ldx #AANTAL_NPC - 1
        bmi !++
!:      lda npc_zichtbaar_begin,x
        sta st_npc,x
        dex
        bpl !-
!:      lda #BEGIN_KAMER
        sta st_kamer
        lda #<BEGIN_X
        sta st_x
        lda #>BEGIN_X
        sta st_x + 1
        lda #BEGIN_Y
        sta st_y
        rts
.assert "spelstatus past in 1 pagina", STATUS_GROOTTE <= 256, true
