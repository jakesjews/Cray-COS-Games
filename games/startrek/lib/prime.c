/* The Primos library routines the University of Texas Super Star Trek
   calls, for COS on the X-MP.  FORTRAN passes every argument as the word
   address of the value; a character string is the bytes of the words from
   that address on.  Output goes to the job's logfile a line at a time
   (the kit's runtime sends stderr there), which the station shows; input
   comes from the interactive input dataset through cosio.c. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

extern int cos_readline(char *buf, int max);
extern void COSDLY(long ms);
extern long _irtc(void);

#define WORD(a) ((long *)((a) << 3))
#define BYTES(a) ((char *)((a) << 3))
#define IVAL(a) (*WORD(a))

/* ---- output: a line is gathered and sent when it is complete ---- */

static char line[200];
static int linelen;

static void flush_line(void) {
    int n = linelen;
    while (n > 0 && line[n - 1] == ' ') n -= 1;   /* the logfile keeps no trailing blanks anyway */
    line[n] = 0;
    fprintf(stderr, " %s\n", line);
    fflush(stderr);
    linelen = 0;
}

static void put_char(int c) {
    c &= 0x7F;                                  /* Prime ASCII has the parity bit set */
    if (c == '\n') { flush_line(); return; }
    if (c == '\r' || c == 0) return;
    if (linelen >= 79) flush_line();           /* a logfile message holds 80 characters */
    line[linelen++] = (char)c;
}

static void put_text(const char *s, long n) {
    while (n-- > 0) put_char(*s++);
}

void TONL(void) { put_char('\n'); }
void TNOUA(unsigned long s, unsigned long n) { put_text(BYTES(s), IVAL(n)); }
void TNOU(unsigned long s, unsigned long n) { put_text(BYTES(s), IVAL(n)); put_char('\n'); }
void T1OU(unsigned long c) { put_char((int)IVAL(c)); }

void TOVFD(unsigned long i) {               /* decimal, as many digits as it takes */
    char b[32];
    sprintf(b, "%ld", IVAL(i));
    put_text(b, strlen(b));
}

void TODEC(unsigned long i) {               /* decimal in a field of six */
    char b[32];
    sprintf(b, "%6ld", IVAL(i));
    put_text(b, strlen(b));
}

/* ---- input: a line, then its tokens ---- */

static char inbuf[200];
static char *inpos;
static int ineof;

void COMANL(void) {
    int n;
    if (linelen > 0) flush_line();              /* a prompt without its new line */
    n = cos_readline(inbuf, sizeof inbuf);
    if (n < 0) { ineof = 1; inbuf[0] = 0; }
    inpos = inbuf;
}

/* The next token of the line read last: IEOL = 1 at its end; else ISNUM = 1
   and VAL the value of a number, or ISNUM = 0 and IHOL the first four
   characters, in capitals, as a Hollerith word. */
void RDTOK(unsigned long ieol, unsigned long isnum, unsigned long val, unsigned long ihol) {
    char tok[64], *e;
    int n = 0;
    unsigned long h;
    double d;
    int i;
    if (inpos == NULL) inpos = inbuf;
    while (*inpos == ' ' || *inpos == ',' || *inpos == '\t') inpos++;
    if (*inpos == 0) { IVAL(ieol) = 1; return; }
    while (*inpos && *inpos != ' ' && *inpos != ',' && *inpos != '\t') {
        if (n < 63) tok[n++] = (char)toupper((unsigned char)*inpos);
        inpos++;
    }
    tok[n] = 0;
    IVAL(ieol) = 0;
    d = strtod(tok, &e);
    if (e != tok && *e == 0) {
        IVAL(isnum) = 1;
        *(double *)WORD(val) = d;
        return;
    }
    IVAL(isnum) = 0;
    h = 0;
    for (i = 0; i < 8; i++) h = (h << 8) | (unsigned char)(i < n && i < 4 ? tok[i] : ' ');
    *(unsigned long *)WORD(ihol) = h;
}

/* Command equivalence as the game uses it: A is an abbreviation of B
   (both Hollerith words of up to four characters). */
long COMEQV(unsigned long a, unsigned long b) {
    unsigned long x = *(unsigned long *)WORD(a), y = *(unsigned long *)WORD(b);
    int i, n = 0;
    for (i = 0; i < 4; i++) {
        int ca = (int)(x >> (56 - 8 * i)) & 0xFF, cb = (int)(y >> (56 - 8 * i)) & 0xFF;
        if (ca == ' ') break;
        if (ca != cb) return 0;
        n++;
    }
    return n > 0;
}

/* ---- random numbers: Park and Miller's minimal standard generator ----
   (the kit's integer multiply traps on a product that does not fit, so
   nothing here is allowed to overflow) */

static long seed = 12345;

double RND(unsigned long arg) {
    long a = IVAL(arg);
    if (a != 0) seed = (a & 0x7FFFFFFF) % 2147483646 + 1;
    seed = (seed * 48271) % 2147483647;
    return (double)seed / 2147483647.0;
}

/* A game number from the clock. */
void HASH(unsigned long nmbr) {
    long t = _irtc();
    long n = (t / 1000) & 077777;
    if (n == 0) n = 1;
    IVAL(nmbr) = n;
}

void SLEEPP(unsigned long ms) {
    COSDLY(IVAL(ms));
}

