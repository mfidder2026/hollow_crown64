// geheugen.asm — de geheugenkaart van Hollow Crown (projectprompt §6.1), VIC-bank 3.
//
//   $0801-$BFFF  programma: motor, costumes, scripts en objecten van de kamer, buffers
//   $C000-$C3E7  scherm-RAM (rij 2-17: kleuren van de bitmap, de andere rijen: tekst)
//   $C3F8-$C3FF  sprite-pointers
//   $C400-$C7FF  16 sprite-vakken
//   $C800-$CFFF  eigen lettertype
//   $D800        kleur-RAM
//   $E000-$FF3F  bitmap, onder de Kernal-ROM (schrijven altijd, lezen alleen met SEI en $01=$35)
//
// De segments hieronder bewaken die kaart: past iets niet, dan mislukt de build (max=, .assert;
// build.sh behandelt een mislukte .assert als fout).

// ---------------------------------------------------------------------------------------------
// Vaste adressen
// ---------------------------------------------------------------------------------------------
.const SCHERM        = $c000
.const SPRITE_PTR    = SCHERM + $3f8
.const SPRITE_VAKKEN = $c400
.const LETTERTYPE    = $c800
.const KLEUR_RAM     = $d800
.const BITMAP        = $e000

.const PRG_EIND      = $c000            // het programma (ook buffers) moet hieronder blijven

// Waarden voor de VIC (§6.3): scherm $C000, tekens $C800, bitmap $E000 — binnen bank 3
.const D018_TEKST    = ((SCHERM - $c000) / $400) << 4 | ((LETTERTYPE - $c000) / $800) << 1
.const D018_BITMAP   = ((SCHERM - $c000) / $400) << 4 | ((BITMAP - $c000) / $2000) << 3
.const DD00_BANK3    = %00              // bits 0-1 van $DD00: %00 = bank 3 ($C000-$FFFF)

.assert "D018 tekst = $02", D018_TEKST, $02
.assert "D018 bitmap = $08", D018_BITMAP, $08

// Geheugenconfiguratie ($01): BASIC uit, Kernal en I/O aan
.const CPU_NORMAAL   = $36

// ---------------------------------------------------------------------------------------------
// Zeropage: $02-$8F is vrij omdat BASIC niet draait; de Kernal gebruikt $90-$FF
// ---------------------------------------------------------------------------------------------
.const ZP_BEGIN      = $02
.const ZP_EIND       = $8f
.label zp_ptr        = $02              // algemene pointer (2 bytes)
.label zp_ptr2       = $04              // tweede pointer (2 bytes)
.label zp_band       = $06              // AUTOTEST: positie in de invoerband (2 bytes)
.label zp_vrij       = $08              // eerste vrije zeropage-byte

.assert "zeropage binnen $02-$8F", zp_vrij <= ZP_EIND + 1, true

// ---------------------------------------------------------------------------------------------
// Segments
// ---------------------------------------------------------------------------------------------
.segmentdef Basic   [start=$0801, max=$080f]
.segmentdef Code    [start=$0810, max=PRG_EIND - 1]
.segmentdef Data    [startAfter="Code", max=PRG_EIND - 1]
// Buffers: geen bytes in de prg, wel ruimte onder $C000 (kamerbuffer, invoerband, ...)
.segmentdef Buffers [startAfter="Data", max=PRG_EIND - 1, virtual]

// Het VIC-gebied: alleen ter controle, er komen geen bytes uit in de prg
.segmentdef Scherm     [start=SCHERM, max=SCHERM + $3e7, virtual]
.segmentdef Sprites    [start=SPRITE_VAKKEN, max=LETTERTYPE - 1, virtual]
.segmentdef Lettertype [start=LETTERTYPE, max=$cfff, virtual]
.segmentdef Bitmap     [start=BITMAP, max=$ff3f, virtual]
