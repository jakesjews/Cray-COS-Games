*  A COS request the C library of the kit does not make.
*
*  void COSDLY(long ms)
*    Delay the job ms milliseconds (F$DLY).
*
         entry     @COSDLY

text:    section   code

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
