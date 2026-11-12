// vm.asm — de script-VM (§6.4). Voert de bytecode van tools/scriptc.py uit, één opdracht per beeld.
// Hoofdstuk 3: alleen ZEG en STOP. De andere opcodes komen in hoofdstuk 4.
//
//   $00                         STOP
//   $01 spreker tekst(2) duur(2) ZEG: tekst op rij 0-1 in de kleur van de spreker; wacht tot hij weg is
// Een onbekende opcode stopt het script en zet vm_fout (voor de tests).

.const OP_STOP = $00
.const OP_ZEG  = $01

.segment Code
// vm_start: script op A (laag) / X (hoog) starten
vm_start:
        sta vm_pc
        stx vm_pc + 1
        rts

// vm_stap: elk beeld
vm_stap: {
        lda vm_pc + 1                   // 0 = er loopt geen script
        bne !+
        rts
!:      lda bericht_actief              // ZEG wacht tot de tekst weg is
        beq !+
        rts
!:      lda vm_pc
        sta zp_ptr
        lda vm_pc + 1
        sta zp_ptr + 1
        ldy #0
        lda (zp_ptr),y
        beq stop
        cmp #OP_ZEG
        beq zeg
        sta vm_fout                     // onbekend
stop:   lda #0
        sta vm_pc
        sta vm_pc + 1
        rts

zeg:    ldy #1
        lda (zp_ptr),y                  // spreker -> kleur
        tax
        lda spreker_kleur,x
        pha
        ldy #4
        lda (zp_ptr),y
        sta bericht_tijd
        iny
        lda (zp_ptr),y
        sta bericht_tijd + 1
        ldy #2
        lda (zp_ptr),y
        tax
        iny
        lda (zp_ptr),y
        stx zp_ptr                      // zp_ptr = de tekst
        sta zp_ptr + 1
        lda vm_pc                       // pc += 6
        clc
        adc #6
        sta vm_pc
        bcc !+
        inc vm_pc + 1
!:      pla
        jmp bericht_zeg
}

.segment Data
vm_pc:   .word 0
vm_fout: .byte 0
