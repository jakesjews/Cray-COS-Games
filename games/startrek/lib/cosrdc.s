*  COS requests the C library of the kit does not make.
*
*  long COSRDC(unsigned long dsp)
*    Read circular (F$RDC) with automatic recall into the buffer of the
*    dataset whose DSP word address is dsp, then recall until the busy
*    flag is clear.  Returns word 1 of the DSP (busy, error flags).
*
*  void COSDLY(long ms)
*    Delay the job ms milliseconds (F$DLY).
*
         entry     @COSRDC
         entry     @COSDLY

text:    section   code

@COSRDC: bss       0
         a0        b00
         a7        a7-1
         ,a7       a0             ; save the return address
         s1        1,a7           ; DSP word address
         s2        1
         s2        s2<63          ; bit 0: automatic recall
         s1        s1!s2
         s0        O'022          ; F$RDC
         ex
rdc1:    s1        1,a7
         a1        s1
         s0        1,a1           ; DPBSY is bit 0 of word 1
         jsp       rdc2           ; not busy
         s0        O'005          ; F$RCL
         ex
         j         rdc1
rdc2:    s7        1,a1
         a0        ,a7
         a7        a7+1
         b00       a0
         j         b00

@COSDLY: bss       0
         a0        b00
         a7        a7-1
         ,a7       a0
         s1        1,a7           ; the count
         a7        a7-1
         ,a7       s1             ; F$DLY wants its address
         s1        a7
         s0        O'035          ; F$DLY
         ex
         a7        a7+1
         a0        ,a7
         a7        a7+1
         b00       a0
         j         b00

         end
