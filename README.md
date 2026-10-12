# Cray COS Games

These ports were developed using AI.

Super Star Trek and Cray Blitz for the [CRAY X-MP core for MiSTer](https://github.com/jakesjews/Cray-XMP_MiSTer),
built to run under its COS 1.17. You play them in an interactive session at the station
(**F2**): the game prints its lines and reads what you type at the `?` prompt.

- [Super Star Trek](games/startrek/README.md): the University of Texas game by David Matuszek
  and Paul Reynolds, in its Prime FORTRAN version of 1983.
- [Cray Blitz](games/crayblitz/README.md): the chess program by Robert Hyatt, Albert Gower and
  Harry Nelson that was world computer chess champion in 1983 and 1986 on CRAY X-MP machines,
  version 49h of 1991.

## What you need

- A MiSTer with the [Cray-XMP core](https://github.com/jakesjews/Cray-XMP_MiSTer#setup) set up.
- A computer with [Docker](https://docs.docker.com/get-started/get-docker/),
  [Python 3](https://www.python.org/downloads/) and [git](https://git-scm.com/downloads), to
  build the games and put them on the core's expander disk.

## Setup

1. Get this repository and the core's, next to each other:

   ```sh
   git clone https://github.com/jakesjews/Cray-COS-Games
   git clone https://github.com/jakesjews/Cray-XMP_MiSTer
   ```

2. Build the cross-compilers for COS. This is needed once.

   ```sh
   docker build -t cray-ack Cray-XMP_MiSTer/tools/ack
   ```

3. Build the games:

   ```sh
   Cray-COS-Games/games/startrek/build.sh
   Cray-COS-Games/games/crayblitz/build.sh
   ```

4. Copy `exp_disk.img` from `games/Cray-XMP` on the SD card to the computer and put the
   programs on it:

   ```sh
   python3 Cray-XMP_MiSTer/tools/py/expdisk.py put exp_disk.img BIN/TREK Cray-COS-Games/games/startrek/build/trek.abs
   python3 Cray-XMP_MiSTer/tools/py/expdisk.py put exp_disk.img BIN/MKBOOK Cray-COS-Games/games/crayblitz/build/mkbook.abs
   python3 Cray-XMP_MiSTer/tools/py/expdisk.py put exp_disk.img BIN/BLITZ Cray-COS-Games/games/crayblitz/build/blitz.abs
   ```

5. Copy `exp_disk.img` back to `games/Cray-XMP` on the SD card.

## Playing

Start COS as the core's README says under
[Starting COS](https://github.com/jakesjews/Cray-XMP_MiSTer#starting-cos), then follow the
game's own page:

- [Super Star Trek](games/startrek/README.md#playing)
- [Cray Blitz](games/crayblitz/README.md#playing)

**After `exp_disk.img` was replaced, start Cray-XMP from the Computer menu again**, not with
Reset: COS stops with `CRAY HALT` during start-up otherwise.

## Troubleshooting

- `expdisk: there is a file BIN/TREK already; rm it first`: the disk has an earlier build.
  Take it off with `python3 Cray-XMP_MiSTer/tools/py/expdisk.py rm exp_disk.img BIN/TREK`,
  then put the new one.

## Credits

- David Matuszek and Paul Reynolds for Super Star Trek, Don Smith, George T. Shotwell,
  Norm Wheeler and Jack Merritt Cramer for their additions to it, and Mike Arnautov for
  [keeping the Prime version](https://mipmip.org/prime_games/). Its source is
  in `games/startrek/prime`, unchanged, under its authors' terms: copying, distribution,
  modification and use for recreational purposes, with all references to the authors kept, and
  not for sale or profit.
- Robert Hyatt, Albert Gower and Harry Nelson for Cray Blitz, and
  [swenson](https://github.com/swenson) for [keeping its sources](https://github.com/swenson/cray-blitz).
  They are not in this repository: the build fetches them.
- [kej715](https://github.com/kej715) for [COS-Tools](https://github.com/kej715/COS-Tools) and the
  [compiler kit for COS](https://github.com/kej715/ack), which the games are built with.
