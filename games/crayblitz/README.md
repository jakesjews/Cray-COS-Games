# Cray Blitz for COS

Cray Blitz, the chess program by Robert Hyatt, Albert Gower and Harry Nelson
that was world computer chess champion in 1983 and 1986 on CRAY X-MP
machines, built for COS 1.17 on the CRAY X-MP. You play it in an interactive
session at the station: it prints its thinking and its move, and reads your
move at the `?` prompt. It plays the opening from its book, and it searches
with the assembly language routines it had on a CRAY.

The sources are version 49h of 1991 as Robert Hyatt released them, kept at
[swenson/cray-blitz](https://github.com/swenson/cray-blitz). They are not in
this repository; the build fetches them.

## Building

The [setup steps](../../README.md#setup) build the game and put it on the
core's expander disk. `build.sh` leaves the program in `build/blitz.abs` and
its opening book in `build/book`.

## Playing

1. Open a session at the station (**F2**) as the core's README says under
   [Working at the station](https://github.com/jakesjews/Cray-XMP_MiSTer#working-at-the-station), up to the `ACCOUNT`
   statement.
2. Type `FETCH,DN=BOOK,MF=AP,TEXT=BIN/BOOK.` and wait for
   `SS004 - DATASET RECEIVED FROM FRONT END`.
3. Type `FETCH,DN=BLITZ,MF=AP,TEXT=BIN/BLITZ.`, wait for the same answer (the
   program is large), then type `BLITZ.`
4. Give your name, then answer `n` twice: you are not continuing a game
   (that does not work here), and the program plays black.
5. Type a move at each `?`: `e4`, `Nf3`, `exd5`, `o-o`.

**Pieces are capital letters and files are small ones**: `Nf3`, not `nf3`.
A pawn move is the square alone.

In the opening the program answers at once, with `book` where the depth of
its search would be. After that it takes half a minute for a move. `st=10`
makes that ten seconds, and `sd=4` has it search to a depth of four however
long that takes. On a DE10-Nano it looks at about 5,000 positions a second;
the line under its thinking has the count (`nps`).

Other commands, typed at the same prompt:

- `d` shows the board. The program's pieces are doubled letters (`NN`).
- `h` lists the moves of the game, `?` repeats the program's last move.
- `pl` changes sides, `go` lets the program move.
- `sc` shows how the program scores the position.
- `he` lists all commands.
- `end` leaves the program.

`SAVE,DN=BOOK.` and `SAVE,DN=BLITZ.` keep the two on the Cray's own drive.
In a later session `ACCESS,DN=BOOK.` and `ACCESS,DN=BLITZ.` then take the
place of steps 2 and 3.

## Troubleshooting

- `BOOK: No such file or directory` and `AB025 - USER PROGRAM REQUESTED ABORT`
  when the program starts: the book is not there. Do step 2.

## What differs from the program as it ran then

- One processor. The source as released has the multiprocessing search
  switched off, and with it thinking on your time.
- A game cannot be continued. The program keeps its history, the saved game
  and a log in the datasets `A`, `B` and `L` followed by the first six
  letters of your name, but it cannot add to the log of an earlier run.
- `SCORES: No such file or directory` at the start is the program looking
  for scoring parameters of your own, which it does without.
- The program looks in three books, of which its authors made the two it
  looks in first as copies of the third. Here all three are the dataset
  `BOOK`.

`build.sh` makes the book with the authors' own two programs from their
collection of games, `book.source`: 2,458 games, of which the first 25 moves
each go in. `blitz2cray.py` has the few changes the sources get before they
are compiled and assembled, and what joins the assembly language routines to
the FORTRAN. `lib/blitz.c` is what the program takes from the Cray library:
the random number generator and the clocks.
