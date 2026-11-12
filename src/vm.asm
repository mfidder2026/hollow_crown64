// vm.asm — de script-VM (§6.4). Voert de bytecode van tools/scriptc.py uit.
// Per beeld lopen opdrachten door tot er een wacht (ZEG, LOOP, WACHT) of het script stopt (hooguit 32).
//
//   $00                           STOP
//   $01 spreker tekst(2) duur(2)  ZEG: tekst op rij 0-1 in de kleur van de spreker; wacht tot hij weg is
//   $02 adres(2)                  SPRING
//   $03 vlag adres(2)             ALS_VLAG: spring als de vlag NIET staat   ($04 ALS_NIET_VLAG: als hij wel staat)
//   $05 vw adres(2)               ALS_HEEFT: spring als Eldric het voorwerp NIET heeft   ($06: als hij het wel heeft)
//   $07 vw n adres(2)             ALS_STAND: spring als de stand NIET n is   ($08: als hij wel n is)
//   $09 vlag / $0A vlag           ZET / WIS
//   $0B vw / $0C vw               GEEF (naar de inventaris) / NEEM (weg)
//   $0D vw n                      STAND
//   $0E vw kamer                  PLAATS
//   $0F x(2) y                    LOOP eldric (wacht tot hij er is)
//   $10 richting                  KIJK eldric
//   $11 n(2)                      WACHT n beelden
//   $12 / $13                     TUSSENSCENE / EINDE_TUSSENSCENE (geen invoer; vuur slaat over)
//   $14 kamer n                   PATCH n van die kamer (alleen als we daar zijn)
//   $15 kamer x(2) y richting     KAMER: laden en erheen; dit script houdt op, BINNENKOMST begint
// Een onbekende opcode stopt het script en zet vm_fout (voor de tests).

.const OP_STOP = $00
.const OP_LAATSTE = $15
.const EIGENAAR_ELDRIC = $ff
.const EIGENAAR_NERGENS = $fe

.segment Code
// vm_start: script op A (laag) / X (hoog) starten
vm_start:
        sta vm_pc
        stx vm_pc + 1
        lda #0
        sta vm_wacht
        sta vm_wacht + 1
        sta vm_loopt
        rts

// vm_stap: elk beeld
vm_stap: {
        lda #32
        sta teller
lus:    lda vm_pc + 1                   // 0 = er loopt geen script
        bne !+
        rts
!:      lda bericht_actief              // ZEG wacht tot de tekst weg is
        beq !+
        lda vm_overslaan                // tussenscène overslaan: tekst meteen weg
        beq wacht
        jsr bericht_weg
!:      lda vm_loopt                    // LOOP wacht tot Eldric er is
        beq !+
        lda act_lopen
        beq !+
        lda vm_overslaan
        beq wacht
        jsr act_er_meteen
!:      lda #0
        sta vm_loopt
        lda vm_wacht                    // WACHT
        ora vm_wacht + 1
        beq voer_uit
        lda vm_overslaan
        bne klaar_wachten
        lda vm_wacht
        bne !+
        dec vm_wacht + 1
!:      dec vm_wacht
wacht:  rts
klaar_wachten:
        lda #0
        sta vm_wacht
        sta vm_wacht + 1

voer_uit:
        dec teller
        beq wacht
        lda vm_pc
        sta zp_vm
        lda vm_pc + 1
        sta zp_vm + 1
        ldy #0
        lda (zp_vm),y
        cmp #OP_LAATSTE + 1
        bcc !+
        sta vm_fout
        jmp vm_stop
!:      asl
        tax
        lda sprongen + 1,x
        pha
        lda sprongen,x
        pha
        rts                             // naar de opdracht (adres - 1 op de stapel)

// ---- de opdrachten. Y = 0, zp_vm wijst naar de opcode. Ze eindigen met "jmp verder" (pc += A) ----
op_stop:
        jmp vm_stop

op_zeg: ldy #1
        lda (zp_vm),y                   // spreker -> kleur
        tax
        lda spreker_kleur,x
        pha
        ldy #4
        lda (zp_vm),y
        sta bericht_tijd
        iny
        lda (zp_vm),y
        sta bericht_tijd + 1
        ldy #2
        lda (zp_vm),y
        sta zp_ptr
        iny
        lda (zp_vm),y
        sta zp_ptr + 1
        pla
        jsr bericht_zeg
        lda #6
        jmp verder

op_spring:
        ldy #1
spring_y:                               // spring naar het adres op (zp_vm),y
        lda (zp_vm),y
        tax
        iny
        lda (zp_vm),y
        stx vm_pc
        sta vm_pc + 1
        jmp lus

op_als_vlag:
        jsr vlag_lezen                  // Z = 1 als de vlag niet staat
        beq spring_3
        lda #4
        jmp verder
op_als_niet_vlag:
        jsr vlag_lezen
        bne spring_3
        lda #4
        jmp verder
spring_3:
        ldy #2
        jmp spring_y

op_als_heeft:
        ldy #1
        lda (zp_vm),y
        tax
        lda st_eigenaar,x
        cmp #EIGENAAR_ELDRIC
        bne spring_3
        lda #4
        jmp verder
op_als_niet_heeft:
        ldy #1
        lda (zp_vm),y
        tax
        lda st_eigenaar,x
        cmp #EIGENAAR_ELDRIC
        beq spring_3
        lda #4
        jmp verder

op_als_stand:
        jsr stand_gelijk                // Z = 1 als gelijk
        bne spring_4
        lda #5
        jmp verder
op_als_niet_stand:
        jsr stand_gelijk
        beq spring_4
        lda #5
        jmp verder
spring_4:
        ldy #3
        jmp spring_y

op_zet: jsr vlag_adres
        lda st_vlaggen,x
        ora bits,y
        sta st_vlaggen,x
        lda #2
        jmp verder
op_wis: jsr vlag_adres
        lda bits,y
        eor #$ff
        and st_vlaggen,x
        sta st_vlaggen,x
        lda #2
        jmp verder

op_geef:
        lda #EIGENAAR_ELDRIC
        bne eigenaar_zetten
op_neem:
        lda #EIGENAAR_NERGENS
eigenaar_zetten:
        pha
        ldy #1
        lda (zp_vm),y
        tax
        pla
        sta st_eigenaar,x
        inc inventaris_anders           // de inventaris opnieuw tekenen (inventaris.asm)
        lda #2
        jmp verder

op_stand:
        ldy #1
        lda (zp_vm),y
        tax
        iny
        lda (zp_vm),y
        sta st_stand,x
        lda #3
        jmp verder

op_plaats:
        ldy #1
        lda (zp_vm),y
        tax
        iny
        lda (zp_vm),y
        sta st_eigenaar,x
        inc inventaris_anders
        lda #3
        jmp verder

op_loop:
        ldy #1
        lda (zp_vm),y
        sta p_x
        iny
        lda (zp_vm),y
        sta p_x + 1
        iny
        lda (zp_vm),y
        sta p_y
        jsr actor_loop_naar
        lda #1
        sta vm_loopt
        lda #4
        jmp verder

op_kijk:
        ldy #1
        lda (zp_vm),y
        sta act_richting
        lda #2
        jmp verder

op_wacht:
        ldy #1
        lda (zp_vm),y
        sta vm_wacht
        iny
        lda (zp_vm),y
        sta vm_wacht + 1
        lda #3
        jmp verder

op_tussenscene:
        lda #1
        sta vm_scene
        lda #0
        sta vm_overslaan
        lda #1
        jmp verder
op_einde_tussenscene:
        lda #0
        sta vm_scene
        sta vm_overslaan
        lda #1
        jmp verder

op_patch:
        ldy #1
        lda (zp_vm),y
        cmp st_kamer
        bne !+
        iny
        lda (zp_vm),y
        jsr patch_zetten
!:      lda #3
        jmp verder

op_kamer:
        ldy #2
        lda (zp_vm),y
        sta kw_x
        iny
        lda (zp_vm),y
        sta kw_x + 1
        iny
        lda (zp_vm),y
        sta kw_y
        iny
        lda (zp_vm),y
        sta kw_richting
        ldy #1
        lda (zp_vm),y
        jsr kamer_wissel                // stopt dit script; start eventueel BINNENKOMST
        jmp lus

// pc += A, en door met de volgende opdracht
verder: clc
        adc vm_pc
        sta vm_pc
        bcc !+
        inc vm_pc + 1
!:      jmp lus

// vlag uit (zp_vm),1: X = byte in st_vlaggen, Y = bit (0-7)
vlag_adres:
        ldy #1
        lda (zp_vm),y
        pha
        lsr
        lsr
        lsr
        tax
        pla
        and #7
        tay
        rts
// Z = 1 als de vlag niet staat
vlag_lezen:
        jsr vlag_adres
        lda st_vlaggen,x
        and bits,y
        rts
// Z = 1 als st_stand[(zp_vm),1] == (zp_vm),2
stand_gelijk:
        ldy #1
        lda (zp_vm),y
        tax
        iny
        lda (zp_vm),y
        cmp st_stand,x
        rts

teller: .byte 0
sprongen:
        .word op_stop - 1, op_zeg - 1, op_spring - 1, op_als_vlag - 1, op_als_niet_vlag - 1
        .word op_als_heeft - 1, op_als_niet_heeft - 1, op_als_stand - 1, op_als_niet_stand - 1
        .word op_zet - 1, op_wis - 1, op_geef - 1, op_neem - 1, op_stand - 1, op_plaats - 1
        .word op_loop - 1, op_kijk - 1, op_wacht - 1, op_tussenscene - 1, op_einde_tussenscene - 1
        .word op_patch - 1, op_kamer - 1
.assert "een sprong per opcode", (* - sprongen) / 2, OP_LAATSTE + 1
}

// vm_stop: het script is klaar (ook een tussenscène houdt dan op)
vm_stop:
        lda #0
        sta vm_pc
        sta vm_pc + 1
        sta vm_scene
        sta vm_overslaan
        sta vm_loopt
        rts

// vm_bezig: A != 0 als er een script loopt
vm_bezig:
        lda vm_pc + 1
        rts

// act_er_meteen: (tussenscène overslaan) Eldric staat meteen op het doel
act_er_meteen:
        lda doel_x
        sta act_x
        lda doel_x + 1
        sta act_x + 1
        lda doel_y
        sta act_y
        lda #0
        sta act_lopen
        rts

.segment Data
vm_pc:        .word 0
vm_fout:      .byte 0
vm_wacht:     .word 0
vm_loopt:     .byte 0                   // LOOP: wacht tot Eldric stilstaat
vm_scene:     .byte 0                   // 1: tussenscène (geen invoer)
vm_overslaan: .byte 0                   // 1: vuur in een tussenscène: alles meteen afmaken
