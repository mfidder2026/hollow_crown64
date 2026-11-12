// status.asm — de spelstatus in één blok (§6.4). Opslaan = dit blok naar de diskette schrijven.
// tools/vicetest.py leest deze labels via build/.../hollowcrown.vs; hernoem ze dus niet zomaar.

.const STATUS_VERSIE   = 1
.const MAX_VLAGGEN     = 256            // bits
.const MAX_VOORWERPEN  = 64

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
spelstatus_eind:

.const STATUS_GROOTTE = spelstatus_eind - spelstatus
.assert "spelstatus past in 1 pagina", STATUS_GROOTTE <= 256, true
