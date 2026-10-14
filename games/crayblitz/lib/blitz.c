/* What Cray Blitz takes from the Cray FORTRAN library and from COS: the
   random number generator, the clocks and the break key.  (The bit
   functions, AND, OR, XOR and ISHFT, the kit's compiler does in line.)
   FORTRAN passes every argument as the word address of its value and takes
   the result from S7, where a C function leaves it. */

#define WORD(a) ((long *)((a) << 3))
#define IVAL(a) (*WORD(a))

/* ---- room for the heap ----
   The opening book is a direct access file, which the FORTRAN runtime
   holds in memory while it is open: 3,000 records of 100 words.  The
   startup code asks COS for this many words for the heap and the stack. */

long _heapwds = 380000;

extern long _irtc(void);        /* the real-time clock, in clock periods */
extern double _cputim(void);    /* the job's CPU time, in seconds */

/* ---- RANF: a random number between 0 and 1 ----
   The generator is the kind the Cray library's RANF is, with its
   multiplier: x(n+1) = 44485709377909 x(n) mod 2**48, and the result is
   x / 2**48.  The seed is an odd number of this file's own, so the hash
   keys the program draws are not those of a real Cray. */

static unsigned long ranx = 04510112377116321UL;

double RANF(void) {
    ranx = (ranx * 44485709377909UL) & 0xFFFFFFFFFFFFUL;
    return (double)ranx / 281474976710656.0;
}

/* ---- CPTIME(rsecs, msecs): the clocks, in hundredths of a second ----
   Real time from the real-time clock, whose period the job communication
   block gives in picoseconds (JCCYCL); CPU time from COS's accounting. */

void CPTIME(unsigned long r, unsigned long m) {
    unsigned long jccycl = ((unsigned long *)0)[0105];
    long ps = (long)((jccycl >> 43) & 0xFFFF);
    if (ps == 0) ps = 9500;                          /* 105 MHz */
    *WORD(r) = (_irtc() / 1000000) * ps / 10000;     /* periods * ps / 1e10 */
    *WORD(m) = (long)(_cputim() * 100.0);
}

/* ---- ONATTN(flag): the break key ----
   The station's attention (/ATTENTION, or BREAK) sets flag to -1 and the
   program goes on, as a signal set it on UNIX.  The program watches the
   flag in its search: while it thinks on the opponent's time it then reads
   the opponent's move, otherwise a command.  The C library catches the
   attention with COS's reprieve. */

extern int _onattn(long *flag);

void ONATTN(unsigned long flag) {
    _onattn(WORD(flag));
}
