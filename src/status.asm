// status.asm — de spelstatus in één blok (§6.4). Opslaan = dit blok naar de diskette schrijven.
// tools/vicetest.py leest deze labels via build/.../hollowcrown.vs; hernoem ze dus niet zomaar.

.const STATUS_VERSIE   = 6              // 2: score; 3: hoofdstuk; 4: 128 voorwerpen; 5: vergeten namen; 6: decor vast
.const MAX_VLAGGEN     = 256            // bits
.const MAX_VOORWERPEN  = 128
.const MAX_MET_STAND   = 32             // alleen de eerste 32 voorwerpen hebben een stand (scriptc.py zet ze vooraan)
.const MAX_NPC         = 16

.segment Data
spelstatus:
st_magic:     .byte 'H', 'C'           // magic: "HC" (PETSCII $48,$43)
st_versie:    .byte STATUS_VERSIE
st_kamer:     .byte 0                  // nummer van de huidige kamer
st_x:         .word 0                  // positie van Eldric (schermpixels)
st_y:         .byte 0
st_vlaggen:   .fill MAX_VLAGGEN / 8, 0
st_eigenaar:  .fill MAX_VOORWERPEN, 0  // per voorwerp dat kan verhuizen: kamer, of $ff = inventaris (eigenaar_van)
st_stand:     .fill MAX_MET_STAND, 0   // per voorwerp met een stand: stand (bv. open/dicht)
st_npc:       .fill MAX_NPC, 0         // per figuur: 1 = zichtbaar
st_score:     .byte 0                  // lichtpunten (hooguit SCORE_MAX)
st_hoofdstuk: .byte 0                  // het hoofdstuk van nu (0 = hoofdstuk 1)
st_vergeten:  .fill MAX_VOORWERPEN / 8, 0   // per voorwerp een bit: Eldric is de naam vergeten (mist.asm)
spelstatus_eind:

.const STATUS_GROOTTE = spelstatus_eind - spelstatus
.assert "alle verhuisbare voorwerpen passen in de spelstatus", AANTAL_DYN <= MAX_VOORWERPEN, true
.assert "voorwerpnummers onder GEEN_VOORWERP", AANTAL_VW < 255, true
.assert "alle vlaggen passen in de spelstatus", AANTAL_VLAGGEN <= MAX_VLAGGEN, true
.assert "alle figuren passen in de spelstatus", AANTAL_NPC <= MAX_NPC, true

.segment Code
// eigenaar_van: A = waar voorwerp X is (een kamer, EIGENAAR_ELDRIC of EIGENAAR_NERGENS); X en Y blijven.
// Alleen voorwerpen die kunnen verhuizen (de eerste AANTAL_DYN) staan in de spelstatus; vast decor (een rots, de zee)
// ligt altijd in zijn kamer: dat staat in vw_eigenaar_begin.
eigenaar_van: {
        cpx #AANTAL_DYN
        bcs vast
        lda st_eigenaar,x
        rts
vast:   lda vw_eigenaar_begin,x
        rts
}

// status_begin: de spelstatus van een nieuw spel (uit build/gen/spel.asm)
status_begin:
        ldx #MAX_VLAGGEN / 8 - 1
        lda #0
!:      sta st_vlaggen,x
        dex
        bpl !-
        ldx #AANTAL_DYN - 1
!:      lda vw_eigenaar_begin,x
        sta st_eigenaar,x
        dex
        bpl !-
        ldx #AANTAL_MET_STAND - 1
!:      lda vw_stand_begin,x
        sta st_stand,x
        dex
        bpl !-
        ldx #AANTAL_NPC - 1
        bmi !++
!:      lda npc_zichtbaar_begin,x
        sta st_npc,x
        dex
        bpl !-
!:      ldx #MAX_VOORWERPEN / 8 - 1
        lda #0
!:      sta st_vergeten,x
        dex
        bpl !-
        sta st_score
        sta st_hoofdstuk
        lda #BEGIN_KAMER
        sta st_kamer
        lda #<BEGIN_X
        sta st_x
        lda #>BEGIN_X
        sta st_x + 1
        lda #BEGIN_Y
        sta st_y
        rts
.assert "spelstatus past in 1 pagina", STATUS_GROOTTE <= 256, true
