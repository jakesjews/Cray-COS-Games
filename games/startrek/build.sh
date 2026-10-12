#!/bin/sh
# Build the University of Texas Super Star Trek for COS on the CRAY X-MP:
# build/trek.abs, to go on the expander disk as BIN/TREK.
#
#   docker build -t cray-ack Cray-XMP_MiSTer/tools/ack     once, for the cross-compilers
#   games/startrek/build.sh
#
# tools/ack is in the core's repository, github.com/jakesjews/Cray-XMP_MiSTer.
set -e
cd "$(dirname "$0")"
mkdir -p build
python3 prime2cray.py prime/startrek.ftn prime/startrek.ins.ftn build/startrek.f
docker run --rm -v "$PWD":/work cray-ack sh -c '
  set -e
  cd build
  kftc -H -l startrek.lst -o startrek.cal -s startrek.f
  cal -x -o startrek.o -l - -i startrek.cal > startrek.callst
  ack -mcos -c -o cosdly.o ../lib/cosdly.s
  ack -mcos -c -o prime.o ../lib/prime.c
  F=/usr/local/share/ack/cos/fortran
  C=/usr/local/share/ack/cos
  ldr -o trek.abs -m trek.map startrek.o prime.o cosdly.o \
      $F/libio.lib $F/librt.lib $F/libintf.lib $C/libem.a $C/libsys.a $C/libc.a
'
ls -l build/trek.abs
