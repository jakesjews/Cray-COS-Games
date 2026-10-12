#!/usr/bin/env python3
"""Prepare the Cray Blitz sources for the kit's FORTRAN compiler (kftc -H):
blitz2cray.py SRC DST.

The sources are the 1991 program as Robert Hyatt released it, brought to a
modern FORTRAN compiler by him; what is changed here is what that port left
behind and what the kit's compiler and COS want, nothing of the game:

  - a statement that ends in a semicolon (a C habit in driver.f) loses it;
  - mplib.f, the port's stand-ins for the Cray multitasking library, no
    longer prints about memory requests, and says the machine is a CRAY X-MP;
  - setup.f declares RANF, the Cray random number generator, real (the
    program declares everything integer unless said otherwise, and the
    compiler does not know RANF);
  - the datasets the program opens get COS names: BOOK, BOOKW, BOOKB and
    SCORES (for default.scores), and the three it names after the player
    (the game's history, the saved game and the log) are A, B and L with
    the first six letters and digits of the name, in capitals;
  - setup.f takes the 16 bits for a hash key from where a Cray number has
    them (the port took them from where an IEEE number does, where a Cray
    number has the top of its fraction, whose first bit is always one);
  - the search looks at the clock every 400 positions instead of every
    20,000 (and every 100 instead of 1,500 before the first iteration is
    done).  20,000 was a fifth of a second on the machine with the search
    in assembly language; it is most of a minute with this build, and the
    program ran that far past its time for a move.

cptime.f (the clocks) and asyncio.f (an input task of the multitasking
version) are left out: lib/blitz.c has the clocks.
"""
import os
import re
import sys

LEFT_OUT = {'cptime.f', 'asyncio.f', 'intrpt.f'}

MPLIB = '''      subroutine memory(par,number)
c     the hash tables stay the size they are declared (htable in global.f)
      implicit integer (a-z)
      return
      end
      subroutine mpcopy
      implicit integer (a-z)
      common /pdata/ pdata(8100)
      common /task/ tdata(8100)
      do 100 i=1,8100
          tdata(i)=pdata(i)
100   continue
      return
      end
      integer function tst124(i)
c     the machine type: 2 to 4 is a CRAY X-MP
      tst124=2
      return
      end
      subroutine dsname(name,tname)
c     the first six letters and digits of a name, in capitals: what a
c     COS dataset name can be made of
      character*20 name, tname
      integer i, n, k
      tname=' '
      n=0
      do 100 i=1,20
          k=ichar(name(i:i))
          if(k.ge.97 .and. k.le.122) k=k-32
          if((k.ge.65 .and. k.le.90) .or.
     *       (k.ge.48 .and. k.le.57)) then
              if(n.lt.6) then
                  n=n+1
                  tname(n:n)=char(k)
              endif
          endif
100   continue
      if(n.eq.0) tname='PLAYER'
      return
      end
'''

SETIO_OLD = '''      tname=name
      fname1='a'//tname
      fname2='b'//tname
      fname3=name
'''
SETIO_NEW = '''      call dsname(name,tname)
      fname1='A'//tname
      fname2='B'//tname
      fname3='L'//tname
'''

NAMES = {"'bookw'": "'BOOKW'", "'bookb'": "'BOOKB'", "'book'": "'BOOK'",
         "'default.scores'": "'SCORES'"}


def convert(name, text):
    if name == 'mplib.f':
        return MPLIB
    if name == 'setio.f':
        assert text.count(SETIO_OLD) == 1
        text = text.replace(SETIO_OLD, SETIO_NEW)
    if name == 'iterate.f':
        assert text.count('dnodes=20000') == 1
        text = text.replace('dnodes=20000', 'dnodes=400')
    if name == 'bdata.f':
        assert text.count('data dnodes, xnodes / 1500, 1500 /') == 1
        text = text.replace('data dnodes, xnodes / 1500, 1500 /', 'data dnodes, xnodes / 100, 100 /')
    if name == 'setup.f':
        assert text.count('tran=and(ishft(tran,-32), 65535)') == 1
        text = text.replace('tran=and(ishft(tran,-32), 65535)', 'tran=and(ishft(tran,-16), 65535)')
    out = []
    for line in text.split('\n'):
        if line[:1] in ('c', 'C', '*'):
            out.append(line)
            continue
        line = re.sub(r';\s*$', '', line)
        for old, new in NAMES.items():
            line = line.replace(old, new)
        out.append(line)
        if name == 'setup.f' and line.strip() == 'implicit integer (a-z)':
            out.append('      real ranf')
    return '\n'.join(out)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if not name.endswith('.f') or name in LEFT_OUT:
            continue
        with open(os.path.join(src, name)) as f:
            text = f.read()
        with open(os.path.join(dst, name), 'w') as f:
            f.write(convert(name, text))


if __name__ == '__main__':
    main()
