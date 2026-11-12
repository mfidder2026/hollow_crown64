// irq.asm — raster-IRQ's (§6.3).
// Hoofdstuk 0: alleen de IRQ op de onderrand (lijn 252), die de beelden telt en de Kernal laat
// doorlopen. De split voor kamer en balk (lijn 66 en 194) komt in hoofdstuk 1.

.const IRQ_ONDERRAND = 252

.segment Code
// irq_start: CIA-IRQ uit, raster-IRQ aan. Aanroepen met de IRQ's uit (SEI).
irq_start:
        lda #$7f
        sta $dc0d                       // CIA 1: geen IRQ's meer
        sta $dd0d                       // CIA 2: geen NMI's meer
        lda $dc0d                       // wachtende verzoeken wissen
        lda $dd0d
        lda #<irq_onderrand
        sta $0314
        lda #>irq_onderrand
        sta $0315
        lda #IRQ_ONDERRAND
        sta $d012
        lda $d011
        and #%01111111                  // bit 8 van de rasterlijn = 0
        sta $d011
        lda #%00000001
        sta $d01a                       // raster-IRQ aan
        sta $d019                       // en een eventueel wachtend verzoek wissen
        rts

// Lijn 252: beelden tellen, daarna de Kernal (toetsenbord, klok) via $EA31.
irq_onderrand:
        lda #%00000001
        sta $d019
        inc beelden
        bne !+
        inc beelden + 1
!:      jmp $ea31

.segment Data
beelden:      .word 0                  // beeldteller, telt op in de IRQ
