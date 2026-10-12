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

Needs Docker and the cross-compilers of `tools/ack`:

```sh
docker build -t cray-ack tools/ack
software/crayblitz/build.sh
```

`build/blitz.abs` is the program and `build/mkbook.abs` a small program that
makes the three opening books it opens, empty.

## Playing

1. Put both programs on the expander disk of the SD card and start the core
   (`docs/DEVELOPMENT.md` has the tool):

   ```sh
   python3 tools/py/expdisk.py put exp_disk.img BIN/BLITZ software/crayblitz/build/blitz.abs
   python3 tools/py/expdisk.py put exp_disk.img BIN/MKBOOK software/crayblitz/build/mkbook.abs
   ```

2. Open a session at the station as the README says (`IAIOP LOG` on the
   operator's console, `IAC`, `/LOGON`, `ACCOUNT,AC=CRAY,US=SYSTEM.`).
3. Type `FETCH,DN=MKBOOK,MF=AP,TEXT=BIN/MKBOOK.` then `MKBOOK.`
4. Type `FETCH,DN=BLITZ,MF=AP,TEXT=BIN/BLITZ.`, wait for the `!` (the program
   is large), then `BLITZ.`
5. Give your name, then answer `n` twice: you are not continuing a game
   (that does not work here), and the program plays black.
6. Type a move at each `?`: `e4`, `Nf3`, `exd5`, `o-o`.

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
