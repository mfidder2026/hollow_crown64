// geheugen.asm — de geheugenkaart van Hollow Crown (projectprompt §6.1), VIC-bank 3.
//
//   $0801-$9FFF  programma: motor, costumes, scripts, voorwerpen, buffers
//   $A000-$BFFF  kamerbuffer: het kamerbestand van de diskette (plaatje ingepakt, voorgrond, patches);
//                RAM onder het BASIC-ROM, dat uit staat ($01 = $36)
//   $C000-$C3E7  scherm-RAM (rij 2-17: kleuren van de bitmap, de andere rijen: tekst)
//   $C3F8-$C3FF  sprite-pointers
//   $C400-$C7FF  16 sprite-vakken (vak 0-1 Eldric, 2-5 twee NPC's, 6 de cursor)
//   $C800-$CFFF  vrij (zie hieronder)
//   $D800        kleur-RAM
//   $E000-$FF3F  bitmap, onder de Kernal-ROM (schrijven altijd, lezen alleen met SEI en $01=$35)
//   $F800-$FFFF  eigen lettertype, ook onder de Kernal-ROM
//
// AFWIJKING van §6.1 (hoofdstuk 1): het lettertype staat op $F800 in plaats van $C800.
//   Reden: dan is $d018 voor tekst en voor de bitmap dezelfde waarde ($0E: scherm $C000, tekens $F800,
//   bitmap $E000). Op de naden wisselen alleen $d011 en $d016, en een paar cycli te laat is daar
//   onschadelijk (zwarte randrijen in de kamer, lege bovenste pixelrij in elk teken). Een te late $d018
//   gaf juist verdwaalde pixels. Het lettertype overlapt de bitmap alleen vanaf bitmaprij 19
//   ($F800 = $E000 + 19,2 x 320): die rijen zijn nooit bitmap op het scherm.
//   De kamer zelf (bitmaprij 2-17) en rij 0-1 en 18 van de bitmap (die op de naden even zichtbaar
//   kunnen zijn) blijven nul.
//   Bijkomend: $C800-$CFFF (2 KB) komt vrij.
//
// De segments hieronder bewaken die kaart: past iets niet, dan mislukt de build (max=, .assert;
// build.sh behandelt een mislukte .assert als fout).

// ---------------------------------------------------------------------------------------------
// Vaste adressen
// ---------------------------------------------------------------------------------------------
.const SCHERM        = $c000
.const SPRITE_PTR    = SCHERM + $3f8
.const SPRITE_VAKKEN = $c400
.const LETTERTYPE    = $f800
.const KLEUR_RAM     = $d800
.const BITMAP        = $e000
.const KLEUR_OFFSET  = KLEUR_RAM - SCHERM   // van een schermadres naar het kleuradres

.const KAMER_BUF     = $a000            // het kamerbestand (tools/kamer.py: zelfde adres)
.const KAMER_BUF_GROOTTE = $2000
.const KAMER_SCRIPTS = $b400            // de scripts van de kamer (<KAMER>.S, tools/scriptc.py): $B400-$BFFF
.const KAMER_SCRIPTS_EIND = KAMER_BUF + KAMER_BUF_GROOTTE - 1   // het plaatje van de kamer blijft dus onder $B400
.const PRG_EIND      = KAMER_BUF        // het programma (ook buffers) moet hieronder blijven

// De schermindeling (§4), in tekenrijen
.const RIJ_BERICHT   = 0                // rij 0-1
.const RIJ_KAMER     = 2                // rij 2-17
.const KAMER_RIJEN   = 16
.const RIJ_ZIN       = 18
.const RIJ_WERKWOORD = 19               // rij 19-21
.const RIJ_INVENTARIS = 22              // rij 22-23
.const RIJ_ONDER     = 24

.const KAMER_BITMAP  = BITMAP + RIJ_KAMER * 320
.const KAMER_SCHERM  = SCHERM + RIJ_KAMER * 40
.const KAMER_KLEUR   = KLEUR_RAM + RIJ_KAMER * 40

// Waarden voor de VIC (§6.3): één $d018 voor alles
.const D018_ALLES    = ((SCHERM - $c000) / $400) << 4 | ((LETTERTYPE - $c000) / $800) << 1 | ((BITMAP - $c000) / $2000) << 3
.const DD00_BANK3    = %00              // bits 0-1 van $DD00: %00 = bank 3 ($C000-$FFFF)

.assert "D018 = $0E (tekens $F800, bitmap $E000)", D018_ALLES, $0e
.assert "kamer en bitmaprij 18 vallen voor het lettertype", BITMAP + (RIJ_ZIN + 1) * 320 <= LETTERTYPE, true
.assert "cursorvak binnen de sprite-vakken", SPRITE_VAKKEN + 7 * 64 <= $c800, true

// $DC00 tussen de invoerscans: bit 7 laag, bit 6 hoog = de SID meet de potmeters van poort 1 (de muis);
// daarmee is ook toetsenbordrij 7 gekozen, wat de joystick in poort 2 niet stoort
.const POORT1_POTS   = %01111111

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
.label zp_ptr3       = $08              // derde pointer (2 bytes)
.label zp_vm         = $0a              // de script-VM: de opdracht die nu draait (2 bytes)
.label zp_muz        = $0c              // de muziekspeler (in de IRQ: een eigen pointer, 2 bytes)
.label zp_vrij       = $0e              // eerste vrije zeropage-byte

.assert "zeropage binnen $02-$8F", zp_vrij <= ZP_EIND + 1, true

// ---------------------------------------------------------------------------------------------
// Segments
// ---------------------------------------------------------------------------------------------
.segmentdef Basic   [start=$0801, max=$080f]
.segmentdef Code    [start=$0810, max=PRG_EIND - 1]
.segmentdef Data    [startAfter="Code", max=PRG_EIND - 1]
// Buffers: geen bytes in de prg, wel ruimte onder $C000 (kamerbuffer, invoerband, ...)
.segmentdef Buffers [startAfter="Data", max=PRG_EIND - 1, virtual]
.segmentdef Kamerbuffer [start=KAMER_BUF, max=KAMER_BUF + KAMER_BUF_GROOTTE - 1, virtual]

// Het VIC-gebied: alleen ter controle, er komen geen bytes uit in de prg
.segmentdef Scherm     [start=SCHERM, max=SCHERM + $3e7, virtual]
.segmentdef Sprites    [start=SPRITE_VAKKEN, max=$c7ff, virtual]
.segmentdef Bitmap     [start=BITMAP, max=LETTERTYPE - 1, virtual]
.segmentdef Lettertype [start=LETTERTYPE, max=$ffff, virtual]
