// loopvak.asm — waar je mag lopen (§5): rechthoeken per kamer en welke aan elkaar grenzen.
// Pad zoeken: BFS over de graaf van loopvakken, in de motor (zodat vakken later aan en uit kunnen).
//
// Coördinaten: x in schermpixels (0-319, 16 bits), y in kamerrijen (0-127). Vakken komen uit
// build/gen/spel.asm (tools/scriptc.py). Twee vakken zijn buren als ze overlappen; het punt waar je
// overstapt ligt in die overlap ("deur"), het dichtst bij waar je staat.

.const MAX_LOOPVAKKEN = 16
.const VAK_DEUR       = MAX_LOOPVAKKEN  // vak 16 is kladruimte: de overlap van twee vakken
.const GEEN_VAK       = $ff

.segment Code
// loopvakken_laden: de tabel op (zp_ptr) — aantal, dan 8 rijen van <aantal> bytes — naar lv_velden
loopvakken_laden: {
        ldy #0
        lda (zp_ptr),y
        sta lv_aantal
        jsr bron_verder                 // inpak.asm: zp_ptr + 1
        lda #<lv_velden
        sta zp_ptr2
        lda #>lv_velden
        sta zp_ptr2 + 1
        ldx #8                          // 8 velden
veld:   ldy #0
!:      cpy lv_aantal
        beq klaar
        lda (zp_ptr),y
        sta (zp_ptr2),y
        iny
        bne !-
klaar:  tya                             // zp_ptr += aantal
        clc
        adc zp_ptr
        sta zp_ptr
        bcc !+
        inc zp_ptr + 1
!:      lda zp_ptr2                     // zp_ptr2 += 17 (een veld is 17 breed: 16 + het deurvak)
        clc
        adc #MAX_LOOPVAKKEN + 1
        sta zp_ptr2
        bcc !+
        inc zp_ptr2 + 1
!:      dex
        bne veld
        ldx #MAX_LOOPVAKKEN - 1         // vakken die bestaan staan aan
!:      lda #0
        cpx lv_aantal
        bcs !+
        lda #1
!:      sta lv_aan,x
        dex
        bpl !--
        rts
}

// punt_in_vak: ligt (p_x, p_y) in vak X? C = 1 ja
punt_in_vak: {
        lda p_x                         // p_x >= x1
        cmp lv_x1_lo,x
        lda p_x + 1
        sbc lv_x1_hi,x
        bcc nee
        lda lv_x2_lo,x                  // x2 >= p_x
        cmp p_x
        lda lv_x2_hi,x
        sbc p_x + 1
        bcc nee
        lda p_y                         // p_y >= y1
        cmp lv_y1,x
        bcc nee
        lda lv_y2,x                     // y2 >= p_y
        cmp p_y
        bcc nee
        sec
        rts
nee:    clc
        rts
}

// vak_van_punt: het eerste vak (dat aan staat) waar (p_x, p_y) in ligt; A = vak of GEEN_VAK
vak_van_punt: {
        ldx #0
!:      cpx lv_aantal
        beq geen
        lda lv_aan,x
        beq volgende
        jsr punt_in_vak
        bcs ja
volgende:
        inx
        bne !-
geen:   lda #GEEN_VAK
        rts
ja:     txa
        rts
}

// klem_in_vak: het punt van vak X dat het dichtst bij (p_x, p_y) ligt -> (k_x, k_y),
// en de afstand |dx| + |dy| -> afstand (16 bits). X blijft.
klem_in_vak: {
        lda p_x                         // k_x = p_x, maar binnen x1..x2
        cmp lv_x1_lo,x
        lda p_x + 1
        sbc lv_x1_hi,x
        bcs !+
        lda lv_x1_lo,x
        sta k_x
        lda lv_x1_hi,x
        sta k_x + 1
        jmp y
!:      lda lv_x2_lo,x
        cmp p_x
        lda lv_x2_hi,x
        sbc p_x + 1
        bcs !+
        lda lv_x2_lo,x
        sta k_x
        lda lv_x2_hi,x
        sta k_x + 1
        jmp y
!:      lda p_x
        sta k_x
        lda p_x + 1
        sta k_x + 1
y:      lda p_y                         // k_y = p_y, maar binnen y1..y2
        cmp lv_y1,x
        bcs !+
        lda lv_y1,x
        jmp zet_y
!:      lda lv_y2,x
        cmp p_y
        bcs !+
        lda lv_y2,x
        jmp zet_y
!:      lda p_y
zet_y:  sta k_y
        // afstand = |k_x - p_x| + |k_y - p_y|
        sec
        lda k_x
        sbc p_x
        sta afstand
        lda k_x + 1
        sbc p_x + 1
        sta afstand + 1
        bpl !+
        lda #0                          // negatief: omdraaien
        sec
        sbc afstand
        sta afstand
        lda #0
        sbc afstand + 1
        sta afstand + 1
!:      lda k_y
        sec
        sbc p_y
        bcs !+
        eor #$ff
        adc #1                          // C = 0 hier: + 1 maakt het positief
!:      clc
        adc afstand
        sta afstand
        bcc !+
        inc afstand + 1
!:      rts
}

// dichtstbij: het dichtstbijzijnde punt in een loopvak (dat aan staat) bij (p_x, p_y)
// -> d_vak, d_x, d_y. Ligt het punt in een vak, dan is dat het punt zelf (afstand 0).
dichtstbij: {
        lda #$ff
        sta beste
        sta beste + 1
        ldx #0
lus:    cpx lv_aantal
        beq klaar
        lda lv_aan,x
        beq volgende
        jsr klem_in_vak
        lda afstand                     // afstand < beste?
        cmp beste
        lda afstand + 1
        sbc beste + 1
        bcs volgende
        lda afstand
        sta beste
        lda afstand + 1
        sta beste + 1
        stx d_vak
        lda k_x
        sta d_x
        lda k_x + 1
        sta d_x + 1
        lda k_y
        sta d_y
volgende:
        inx
        bne lus
klaar:  rts
beste:  .word 0
}

// deur_maken: vak VAK_DEUR = de overlap van vak X en vak Y
deur_maken: {
        stx va
        sty vb
        lda lv_x1_lo,x                  // x1 = max(x1a, x1b)
        cmp lv_x1_lo,y
        lda lv_x1_hi,x
        sbc lv_x1_hi,y
        bcs !+
        tya
        tax
!:      lda lv_x1_lo,x
        sta lv_x1_lo + VAK_DEUR
        lda lv_x1_hi,x
        sta lv_x1_hi + VAK_DEUR
        ldx va
        lda lv_x2_lo,x                  // x2 = min(x2a, x2b)
        cmp lv_x2_lo,y
        lda lv_x2_hi,x
        sbc lv_x2_hi,y
        bcc !+
        tya
        tax
!:      lda lv_x2_lo,x
        sta lv_x2_lo + VAK_DEUR
        lda lv_x2_hi,x
        sta lv_x2_hi + VAK_DEUR
        ldx va
        lda lv_y1,x                     // y1 = max
        cmp lv_y1,y
        bcs !+
        lda lv_y1,y
!:      sta lv_y1 + VAK_DEUR
        lda lv_y2,x                     // y2 = min
        cmp lv_y2,y
        bcc !+
        lda lv_y2,y
!:      sta lv_y2 + VAK_DEUR
        ldx va
        ldy vb
        rts
va:     .byte 0
vb:     .byte 0
}

// bfs: kortste rij vakken van bfs_van naar bfs_naar (breedte eerst) -> route[0..route_lengte-1],
// met route[0] = bfs_van. C = 1 gevonden, C = 0 geen pad.
bfs: {
        ldx #MAX_LOOPVAKKEN - 1
        lda #GEEN_VAK
!:      sta ouder,x
        dex
        bpl !-
        ldx bfs_van
        txa
        sta ouder,x
        sta rij
        lda #1
        sta rij_eind
        lda #0
        sta rij_begin
lus:    ldy rij_begin
        cpy rij_eind
        bne !+
        clc                             // rij leeg: geen pad
        rts
!:      lda rij,y
        sta v
        inc rij_begin
        cmp bfs_naar
        beq gevonden
        ldx #0
buur:   cpx lv_aantal
        beq lus
        lda ouder,x                     // al gezien?
        cmp #GEEN_VAK
        bne volgende
        lda lv_aan,x
        beq volgende
        ldy v
        cpx #8
        bcs hoog
        lda lv_buren_lo,y
        and bits,x
        beq volgende
        jmp erbij
hoog:   lda lv_buren_hi,y
        and bits - 8,x
        beq volgende
erbij:  lda v
        sta ouder,x
        txa
        ldy rij_eind
        sta rij,y
        inc rij_eind
volgende:
        inx
        jmp buur

gevonden:                               // terug van bfs_naar naar bfs_van, dan omdraaien
        ldy #0
        lda bfs_naar
!:      sta omgekeerd,y
        iny
        tax
        cpx bfs_van
        beq !+
        lda ouder,x
        jmp !-
!:      sty route_lengte
        ldx #0
!:      dey
        lda omgekeerd,y
        sta route,x
        inx
        cpy #0
        bne !-
        sec
        rts
v:      .byte 0
rij_begin: .byte 0
rij_eind:  .byte 0
}

.segment Data
bits:         .byte 1, 2, 4, 8, 16, 32, 64, 128
lv_aantal:    .byte 0
// 8 velden van 17 bytes (16 vakken + het deurvak), in de volgorde van build/gen/spel.asm
lv_velden:    .fill 8 * (MAX_LOOPVAKKEN + 1), 0
.label lv_x1_lo    = lv_velden + 0 * (MAX_LOOPVAKKEN + 1)
.label lv_x1_hi    = lv_velden + 1 * (MAX_LOOPVAKKEN + 1)
.label lv_x2_lo    = lv_velden + 2 * (MAX_LOOPVAKKEN + 1)
.label lv_x2_hi    = lv_velden + 3 * (MAX_LOOPVAKKEN + 1)
.label lv_y1       = lv_velden + 4 * (MAX_LOOPVAKKEN + 1)
.label lv_y2       = lv_velden + 5 * (MAX_LOOPVAKKEN + 1)
.label lv_buren_lo = lv_velden + 6 * (MAX_LOOPVAKKEN + 1)
.label lv_buren_hi = lv_velden + 7 * (MAX_LOOPVAKKEN + 1)
lv_aan:       .fill MAX_LOOPVAKKEN, 0
p_x:          .word 0                   // invoer van de routines hierboven
p_y:          .byte 0
k_x:          .word 0                   // klem_in_vak
k_y:          .byte 0
afstand:      .word 0
d_vak:        .byte 0                   // dichtstbij
d_x:          .word 0
d_y:          .byte 0
bfs_van:      .byte 0
bfs_naar:     .byte 0
ouder:        .fill MAX_LOOPVAKKEN, 0
rij:          .fill MAX_LOOPVAKKEN, 0
omgekeerd:    .fill MAX_LOOPVAKKEN, 0
route:        .fill MAX_LOOPVAKKEN, 0
route_lengte: .byte 0
