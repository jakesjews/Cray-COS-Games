# Cray Blitz for COS

Cray Blitz, the chess program by Robert Hyatt, Albert Gower and Harry Nelson
that was world computer chess champion in 1983 and 1986 on CRAY X-MP
machines, built for COS 1.17 on the CRAY X-MP. You play it in an interactive
session at the station: it prints its thinking and its move, and reads your
move at the `?` prompt.

The sources are version 49h of 1991 as Robert Hyatt released them, kept at
[swenson/cray-blitz](https://github.com/swenson/cray-blitz). They are not in
this repository; the build fetches them.

## Building

The [setup steps](../../README.md#setup) build the game and put it on the
core's expander disk. `build.sh` leaves the program in `build/blitz.abs` and
in `build/mkbook.abs` a small program that makes the three opening books it
opens, empty.

## Playing

1. Open a session at the station (**F2**) as the core's README says under
   [Working at the station](https://github.com/jakesjews/Cray-XMP_MiSTer#working-at-the-station), up to the `ACCOUNT`
   statement.
2. Type `FETCH,DN=MKBOOK,MF=AP,TEXT=BIN/MKBOOK.` then `MKBOOK.` It answers
   `made BOOK`, `made BOOKW` and `made BOOKB`.
3. Type `FETCH,DN=BLITZ,MF=AP,TEXT=BIN/BLITZ.`, wait for the `!` (the program
   is large), then `BLITZ.`
4. Give your name, then answer `n` twice: you are not continuing a game
   (that does not work here), and the program plays black.
5. Type a move at each `?`: `e4`, `Nf3`, `exd5`, `o-o`.

**Pieces are capital letters and files are small ones**: `Nf3`, not `nf3`.
A pawn move is the square alone.

The program takes half a minute for a move. `st=10` makes that ten seconds,
and `sd=4` has it search to a depth of four however long that takes.

Other commands, typed at the same prompt:

- `d` shows the board. The program's pieces are doubled letters (`NN`).
- `h` lists the moves of the game, `?` repeats the program's last move.
- `pl` changes sides, `go` lets the program move.
- `sc` shows how the program scores the position.
- `he` lists all commands.
- `end` leaves the program.

## What differs from the program as it ran then

- One processor. The source as released has the multiprocessing search
  switched off, and with it thinking on your time.
- The search is the FORTRAN one. The assembly language versions of its inner
  routines (`CAL/` in the sources) are not built, so it sees far fewer
  positions a second than it did.
- No opening book: the books `MKBOOK` makes are empty. The book builders
  `bookp` and `books` are built too (`build/bookp.abs`, `build/books.abs`),
  but a book of the size they make does not fit in the memory a program's
  files get here, and that has not been tried.
- A game cannot be continued. The program keeps its history, the saved game
  and a log in the datasets `A`, `B` and `L` followed by the first six
  letters of your name, but it cannot add to the log of an earlier run.
- `SCORES: No such file or directory` at the start is the program looking
  for scoring parameters of your own, which it does without.

`blitz2cray.py` has the few changes the sources get before they are
compiled, and `lib/` what the program takes from the Cray library: the bit
functions, the random number generator and the clocks.
