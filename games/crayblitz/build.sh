#!/bin/sh
# Build Cray Blitz for COS on the CRAY X-MP: build/blitz.abs, to go on the
# expander disk as BIN/BLITZ, with build/mkbook.abs, which makes the empty
# opening books the program opens, and the book builders build/bookp.abs
# and build/books.abs.
#
#   docker build -t cray-ack tools/ack      once, for the cross-compilers
#   software/crayblitz/build.sh
#
# The program's sources are not in this repository.  They are taken from
# BLITZ_SRC, or from research/source/cray-blitz if that is there, or else
# fetched from https://github.com/swenson/cray-blitz (the release Robert
# Hyatt put on craftychess.com) into build/.
#
# KFTC=/path/to/kftc compiles the FORTRAN with that compiler on this
# machine instead of the one in the image (for work on the compiler).
set -e
cd "$(dirname "$0")"
mkdir -p build/src build/obj
SRC=${BLITZ_SRC:-../../research/source/cray-blitz}
if [ ! -f "$SRC/main.f" ]; then
  SRC=build/cray-blitz
  if [ ! -f $SRC/main.f ]; then
    git clone -q https://github.com/swenson/cray-blitz $SRC
    git -C $SRC checkout -q 78a009e
  fi
fi
python3 blitz2cray.py $SRC build/src

# The program's units, as its Makefile lists them, less the clocks and the
# input task of the multitasking version (lib/blitz.c has the clocks).
UNITS="attack backup bdata book illegal castle ccmnd check command control
copy fail dcmnd draw driver dupchk extrct fcmnd forsythe hcmnd boolean inform
input iterate killer locate lookup main make match mater merge mover movgen
options output pawn pgcmnd phase piece playbw pmvmkr pocmnd ponder prescore
query rcmnd reduce repeat ripoff saver sbcmnd scan score search select setclk
setgb setio setup share sortply1 split srcmnd stats store test typenode umover
unmake unsplit mplib"
# The book builders: bookp makes the book from a text of games, books scores it.
BOOKP="attack bdata bookp castle check command copy dcmnd extrct input locate
mplib make movgen pawn piece prescore ripoff score setgb setup unmake boolean"
BOOKS="attack bdata books castle copy extrct locate mplib make movgen pawn
piece prescore ripoff score setgb setup unmake boolean"

UNITS=$(echo $UNITS); BOOKP=$(echo $BOOKP); BOOKS=$(echo $BOOKS)

compile() {
  for u in $UNITS bookp books; do
    $1 -H -o ../obj/$u.cal $u.f
  done
}
if [ -n "$KFTC" ]; then
  (cd build/src && compile "$KFTC")
  KFTC_STEP=true
else
  KFTC_STEP='cd build/src && for u in '"$UNITS bookp books"'; do kftc -H -o ../obj/$u.cal $u.f; done && cd ../..'
fi

docker run --rm -v "$PWD":/work cray-ack sh -c '
  set -e
  '"$KFTC_STEP"'
  cd build/obj
  for c in *.cal; do cal -x -o ${c%.cal}.o -l - -i $c > /dev/null; done
  ack -mcos -c -o blitz_lib.o ../../lib/blitz.c
  cal -x -o bits.o -l - -i ../../lib/bits.cal > /dev/null
  F=/usr/local/share/ack/cos/fortran
  C=/usr/local/share/ack/cos
  LIBS="$F/libio.lib $F/librt.lib $F/libintf.lib $C/libem.a $C/libsys.a $C/libc.a"
  objs() { for u in $*; do printf "%s.o " $u; done; }
  ldr -o ../blitz.abs -m ../blitz.map $(objs '"$UNITS"') blitz_lib.o bits.o $LIBS
  ldr -o ../bookp.abs -m ../bookp.map $(objs '"$BOOKP"') blitz_lib.o bits.o $LIBS
  ldr -o ../books.abs -m ../books.map $(objs '"$BOOKS"') blitz_lib.o bits.o $LIBS
  kftc -o mkbook.cal ../../mkbook.f && cal -x -o mkbook.o -l - -i mkbook.cal > /dev/null
  ldr -o ../mkbook.abs -m ../mkbook.map mkbook.o $LIBS
'
ls -l build/blitz.abs build/mkbook.abs build/bookp.abs build/books.abs
