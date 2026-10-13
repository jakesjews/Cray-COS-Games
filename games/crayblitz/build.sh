#!/bin/sh
# Build Cray Blitz for COS on the CRAY X-MP: build/blitz.abs, to go on the
# expander disk as BIN/BLITZ, and its opening book build/book, to go there
# as BIN/BOOK.
#
#   docker build -t cray-ack -f Cray-XMP_MiSTer/tools/ack/Dockerfile Cray-XMP_MiSTer/tools
#   games/crayblitz/build.sh
#
# The first line is done once, for the cross-compilers: tools/ack is in the
# core's repository, github.com/jakesjews/Cray-XMP_MiSTer.
#
# The program's sources are not in this repository.  They are taken from
# BLITZ_SRC if that names them, or else fetched from
# https://github.com/swenson/cray-blitz (the release Robert Hyatt put on
# craftychess.com) into build/.
#
# The book is made the way the program's authors made it: their two
# programs, bookp and books, are built with the game and run on the 2,458
# games of book.source.  bookp enters the first 25 moves of each game by
# its position, books gives every position its score.  They are CRAY
# programs: cray-xmp-job, which is in the image, runs them on the model of
# the CPU.  That takes some minutes, and is done again only when a file
# here that the book depends on has changed.
#
# KFTC=/path/to/kftc compiles the FORTRAN with that compiler on this
# machine instead of the one in the image (for work on the compiler).
set -e
cd "$(dirname "$0")"
mkdir -p build/src build/obj
SRC=${BLITZ_SRC:-build/cray-blitz}
if [ ! -f "$SRC/main.f" ]; then
  SRC=build/cray-blitz
  if [ ! -f $SRC/main.f ]; then
    git clone -q https://github.com/swenson/cray-blitz $SRC
    git -C $SRC checkout -q 78a009e
  fi
fi
python3 blitz2cray.py $SRC build/src
cp -p $SRC/book.source build/book.source

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

# The book is as old as what it is made from.
BOOK=yes
if [ -f build/book ] && [ -z "$(find blitz2cray.py build.sh lib build/book.source -newer build/book)" ]; then
  BOOK=no
fi

docker run --rm -v "$PWD":/work cray-ack sh -c '
  set -e
  '"$KFTC_STEP"'
  cd build/obj
  for c in *.cal; do cal -x -o ${c%.cal}.o -l - -i $c > /dev/null; done
  # the assembly language routines and what joins them to the FORTRAN, as a
  # library: each program takes the ones it calls
  rm -rf cal blitzcal.lib
  CALLIB=
  if ls ../src/cal/*.cal > /dev/null 2>&1; then
    mkdir cal
    for c in ../src/cal/*.cal; do
      n=$(basename ${c%.cal})
      cal -x -o cal/$n.o -l cal/$n.lst -i $c > cal/$n.log || { cat cal/$n.log; exit 1; }
    done
    lib -o blitzcal.lib cal/*.o
    CALLIB=blitzcal.lib
  fi
  ack -mcos -c -o blitz_lib.o ../../lib/blitz.c
  F=/usr/local/share/ack/cos/fortran
  C=/usr/local/share/ack/cos
  LIBS="$CALLIB $F/libio.lib $F/librt.lib $F/libintf.lib $C/libem.a $C/libsys.a $C/libc.a"
  objs() { for u in $*; do printf "%s.o " $u; done; }
  ldr -o ../blitz.abs -m ../blitz.map $(objs '"$UNITS"') blitz_lib.o $LIBS
  ldr -o ../bookp.abs -m ../bookp.map $(objs '"$BOOKP"') blitz_lib.o $LIBS
  ldr -o ../books.abs -m ../books.map $(objs '"$BOOKS"') blitz_lib.o $LIBS
  cd ..
  if [ '"$BOOK"' = yes ]; then
    echo "making the opening book (some minutes)"
    rm -f book
    printf "BOOK\nBOOKSRC\n3000\n" > bookp.in
    cray-xmp-job bookp.abs --quiet --in bookp.in --text BOOKSRC=book.source --ds BOOK=book > bookp.log
    tail -1 bookp.log
    printf "BOOK\n" > books.in
    cray-xmp-job books.abs --quiet --in books.in --ds BOOK=book > books.log
  fi
'
ls -l build/blitz.abs build/book
