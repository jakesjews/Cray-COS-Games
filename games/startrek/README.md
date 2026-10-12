# Super Star Trek for COS

The University of Texas Super Star Trek, the 1970s FORTRAN game by David
Matuszek and Paul Reynolds with additions by Don Smith, George T. Shotwell,
Norm Wheeler and Jack Merritt Cramer, built for COS 1.17 on the CRAY X-MP. It
is played in an interactive session at the station: the game prints a line at
a time and reads what you type at the `?` prompt.

The sources in `prime/` are the Prime FTN version of 1983 (rev. 19.1, "GGR
version"), as kept in [Mike Arnautov's archive of Prime games](https://mipmip.org/prime_games/),
with its manual `startrek.runi`. The authors permit copying, distribution,
modification and use for recreational purposes, provided all references to
them are retained; not for sale or profit. Nothing in `prime/` is changed.

## Building

The [setup steps](../../README.md#setup) build the game and put it on the
core's expander disk. `build.sh` leaves the program for COS in
`build/trek.abs`. `prime2cray.py` turns the Prime source into FORTRAN 77 the
kit's compiler takes in Hollerith mode, and `lib/` holds the Primos routines
the game calls, written for COS: the terminal output and input calls, the
random number generator and the delay.

## Playing

1. Open a session at the station (**F2**) as the core's README says under
   [Working at the station](https://github.com/jakesjews/Cray-XMP_MiSTer#working-at-the-station), up to the `ACCOUNT`
   statement.
2. Type `FETCH,DN=TREK,MF=AP,TEXT=BIN/TREK.` and wait for
   `SS004 - DATASET RECEIVED FROM FRONT END`, then type `TREK.`
3. Answer the questions: `REGULAR`, `SHORT`, `NOVICE`, a password. Commands
   are words such as `SRSCAN`, `LRSCAN`, `CHART`, `STATUS`, `MOVE`, `PHASERS`,
   `SHIELDS`, `DOCK`, `REST`, `QUIT`; `HELP` lists them. Type one at each `?`.

The game asks its questions one at a time when a command lacks its parameters,
so `MOVE` then `MANUAL` then `0 -1` works as well as `MOVE MANUAL 0 -1`.

## What differs from the Prime version

- Freezing a game to a file and thawing it are not there.
- The citation for winning is a few lines, not the picture of the ship that
  went to a file.
- A prompt without a line end is shown as a line of its own, since the
  station shows whole lines.
- `SLEEP$` delays are COS delays; `TIMDAT`, `GCHAR` and `SCHAR` are not needed.
