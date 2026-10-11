/* Lines from the job's input dataset through COS's circular I/O, which
   works on an interactive dataset where the kit's buffered I/O does not.
   The dataset is $IN as the kit's runtime opened it (descriptor 0).

   The buffer holds the COS blocked format: a block control word at the
   start of each 512-word block, data words, and a record control word
   (mode 10 octal end of record, 16 end of file, 17 end of data) behind
   every record.  Interactive input leaves the forward index of a record
   control word at zero, so the words are told apart by their own bits: a
   record control word has its top bit set, a block control word begins
   with a zero byte, and a word of text has neither. */
#include <stdio.h>
extern void *_ftPtr(int fd);
extern unsigned long _getdsp(void *entry);
extern unsigned long COSRDC(unsigned long dspw);

static unsigned long *dsp;      /* the DSP, as a C (byte) pointer */
static unsigned long dspw;      /* its word address */
static int eod;
int cos_debug;

#define ADDR(w) ((w) & 0xFFFFFF)
#define WORD(a) ((unsigned long *)((a) << 3))

static int cos_fill(void) {
    unsigned long w1;
    w1 = COSRDC(dspw);
    if (cos_debug) { fprintf(stderr, " fill: w1=%lo in=%lo out=%lo\n", w1, ADDR(dsp[2]), ADDR(dsp[3])); fflush(stderr); }
    if ((w1 >> 62) & 1) { eod = 1; return 0; }      /* DPEOI: end of data */
    if ((w1 >> 51) & 0xFFF) {                         /* other error flags */
        fprintf(stderr, " cosio: read error %lo\n", (w1 >> 51) & 0xFFF);
        fflush(stderr);
        eod = 1;
        return 0;
    }
    return 1;
}

static int cos_word(unsigned long *out) {
    unsigned long in, outp, lmt;
    if (dsp == NULL) {
        dsp = (unsigned long *)_getdsp(_ftPtr(0));
        dspw = (unsigned long)dsp >> 3;
    }
    in = ADDR(dsp[2]);
    outp = ADDR(dsp[3]);
    while (in == outp) {                          /* empty: ask for more, as often as it takes */
        if (eod || !cos_fill()) return 0;
        in = ADDR(dsp[2]);
        outp = ADDR(dsp[3]);
    }
    *out = *WORD(outp);
    if (cos_debug) { fprintf(stderr, " w@%lo=%lo in=%lo\n", outp, *out, in); fflush(stderr); }
    outp += 1;
    lmt = ADDR(dsp[4]);
    if (outp >= lmt) outp = ADDR(dsp[1]);
    dsp[3] = (dsp[3] & ~0xFFFFFFUL) | outp;
    return 1;
}

/* The next record as a line: its length, or -1 at the end of data. */
int cos_readline(char *buf, int max) {
    unsigned long w;
    int n = 0, i, ubc, mode;
    for (;;) {
        if (!cos_word(&w)) { buf[0] = 0; return -1; }
        if (w >> 63) {                                /* a record control word */
            mode = (int)(w >> 60);
            if (mode == 017) { eod = 1; buf[0] = 0; return -1; }
            if (mode != 010) continue;                /* end of file: nothing to a line */
            ubc = (int)((w >> 54) & 0x3F);
            n -= ubc / 8;
            if (n < 0) n = 0;
            if (n > max - 1) n = max - 1;
            buf[n] = 0;
            return n;
        }
        if ((w >> 56) == 0) continue;                 /* a block control word */
        for (i = 0; i < 8; i++) {
            if (n < max - 1) buf[n] = (char)(w >> (56 - 8 * i));
            n += 1;
        }
    }
}
