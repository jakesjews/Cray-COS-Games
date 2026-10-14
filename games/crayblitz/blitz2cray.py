#!/usr/bin/env python3
"""Prepare the Cray Blitz sources for the kit's FORTRAN compiler (kftc -H)
and its assembler: blitz2cray.py SRC DST.

The sources are the 1991 program as Robert Hyatt released it, brought to a
modern FORTRAN compiler by him; what is changed here is what that port left
behind and what the kit's compiler and COS want, nothing of the game:

  - a statement that ends in a semicolon (a C habit in driver.f) loses it;
  - mplib.f, the port's stand-ins for the Cray multitasking library, no
    longer prints about memory requests, and says the machine is a CRAY X-MP;
  - setup.f declares RANF, the Cray random number generator, real (the
    program declares everything integer unless said otherwise, and the
    compiler does not know RANF);
  - the datasets the program opens get COS names: SCORES for
    default.scores, TMODE and BMODE for the commands it can take at the
    start of tournament and blitz mode (default.tm, default.bm), AGAME
    for a game it analyses; BOOK for all three opening books (the two
    the program looks in first, bookw and bookb, are copies of the third
    as its authors built them, and the FORTRAN runtime holds a dataset
    that is opened more than once in memory once); and the three it
    names after the player (the game's history, the saved game and the
    log) are A, B and L with the first six letters and digits of the
    name, in capitals;
  - the hash tables (htable, blank common in global.f) get one word more:
    the last entry of the second pawn table is the word after the 971,776
    the port declares, which leave out the word the tables keep free
    between the king safety and the pawn tables.  The original asked COS
    for its memory and wrote into what COS gives beyond it; here the word
    after was a flag of the search (abort), which a pawn hash entry then
    set, or the heap;
  - setup.f takes the 16 bits for a hash key from where a Cray number has
    them (the port took them from where an IEEE number does, where a Cray
    number has the top of its fraction, whose first bit is always one);
  - the search looks at the clock every 400 positions instead of every
    20,000 (and every 100 instead of 1,500 before the first iteration is
    done).  20,000 positions are about four seconds on the core, and the
    program ran that far past its time for a move;
  - main.f has the station's attention (/ATTENTION, the BREAK key) set the
    flag the search watches for one (broke), with ONATTN in lib/blitz.c:
    while the program thinks on the opponent's time that is how a move is
    typed, as the program's comments say for COS (later a task of the
    multitasking version read the terminal and set it).

cptime.f (the clocks) and asyncio.f (an input task of the multitasking
version) are left out: lib/blitz.c has the clocks.

The assembly language routines (SRC/CAL), which are what the program ran
with on a CRAY, take the place of their FORTRAN versions: the search, the
move generator, making and unmaking a move, the scoring and the hash
tables.  They go to DST/cal, one module a file, as the kit's assembler
wants them:

  - an INCLUDE is put in, and the COMMON blocks of the two included files
    are written as sections;
  - a file's modules are taken apart;
  - the letters that belong to an operator (*F, /H, ,Z) are capitals, a
    constant with a binary scale (3S31) is written out, the length of a
    jump is given as the 2 parcels it is, and ALIGN is left out.

The routines were written to be called by Cray's FORTRAN compiler: they
take what registers they like, find the program's task common through
B60, and the functions among them take their arguments in S1 and S2 and
give their result in S1.  The kit's compiler keeps its stack, frame and
heap pointers in A7, A6 and A5, passes the addresses of arguments on the
stack and expects a result in S7.  So between the two there is a small
routine for every name that is called across (DST/cal/g*.cal): one way
it keeps the three pointers in B20 to B22 over the call, the other way it
brings them back for the FORTRAN routine.  Neither side uses those
registers.  The FORTRAN versions of the routines are dropped from the
sources, and main.f gets back the line that sets B60.

BLITZ_CAL names the modules to take from SRC/CAL (for trying one at a
time); none takes none, and without it all are taken.
"""
import os
import re
import sys

LEFT_OUT = {'cptime.f', 'asyncio.f', 'intrpt.f'}

DSNAME = '''      subroutine dsname(name,tname)
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

# The station's attention sets the flag the search watches for a line
# typed while it runs (ONATTN, lib/blitz.c).
MAIN_OLD = '''      call mpcopy
'''
MAIN_NEW = '''      call mpcopy
      call onattn(broke)
'''

NAMES = {"'bookw'": "'BOOK'", "'bookb'": "'BOOK'", "'book'": "'BOOK'",
         "'default.scores'": "'SCORES'", "'default.tm'": "'TMODE'",
         "'default.bm'": "'BMODE'", "'agame'": "'AGAME'"}


def mplib(text):
    """mplib.f with MEMORY left empty (the hash tables stay the size they are
    declared, htable in global.f), TST124 answering 2 (2 to 4 is a CRAY X-MP;
    the port says 8) and DSNAME added."""
    out = []
    unit = ''
    kept = 0
    for line in text.split('\n'):
        code = line.strip()
        m = re.match(r'(?:integer\s+function|subroutine)\s+(\w+)', code)
        if m:
            unit = m.group(1)
        if unit == 'memory':
            if not re.match(r'(subroutine\b|implicit\b|return$|end$)', code):
                continue
            kept += 1
        if unit == 'tst124' and code == 'tst124=8':
            line = line.replace('tst124=8', 'tst124=2')
            kept += 1
        out.append(line)
    assert kept == 5
    return '\n'.join(out).rstrip('\n') + '\n' + DSNAME


def convert(name, text):
    if name == 'mplib.f':
        return mplib(text)
    if name == 'setio.f':
        assert text.count(SETIO_OLD) == 1
        text = text.replace(SETIO_OLD, SETIO_NEW)
    if name == 'global.f':
        assert text.count('common htable(971776)') == 1
        text = text.replace('common htable(971776)', 'common htable(971777)')
    if name == 'iterate.f':
        assert text.count('dnodes=20000') == 1
        text = text.replace('dnodes=20000', 'dnodes=400')
    if name == 'main.f':
        assert text.count(MAIN_OLD) == 1
        text = text.replace(MAIN_OLD, MAIN_NEW)
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


# ---- the assembly language routines

# The modules taken from SRC/CAL, and the FORTRAN routines each replaces
# where that is not the one of its own name.  PAWNEP is the whole move
# generator.  Left where they are: the locks and the machine test of the
# multitasking version, and two routines for looking at registers.
CAL_MODULES = ('attack checkg checki killer1 killer2 lookup make mater mover '
               'mover1 pawnep phase2 phase3 phase4 repeat ripoff score score1 '
               'scoredv scorekm scorekp scorep scoretrd search searche searcho '
               'select store1 store2 umover umover1 unmake').split()
REPLACES = {'pawnep': ['pawnep', 'piece', 'pawn']}

# Functions called with their arguments in registers, and how many.
BY_VALUE = {'ATTACK%': 2, 'CHECKG%': 1, 'CHECKI%': 1, 'REPEAT%': 1,
            'RIPOFF%': 1, 'SETB60%': 1}
# FORTRAN functions the assembly routines call, each with a dummy argument.
FUNCTIONS = ('CHECKGU', 'CHECKIU')

UNIT = re.compile(r'\s+(?:integer\s+function|function|subroutine|program)\s+(\w+)', re.I)


def without_units(text, names):
    """A FORTRAN source without the program units named."""
    out, unit, name, found = [], [], None, set()
    for line in text.split('\n'):
        unit.append(line)
        m = None if line[:1] in ('c', 'C', '*') else UNIT.match(line)
        if m and name is None:
            name = m.group(1).lower()
        if name is not None and re.match(r'\s+end\s*$', line, re.I):
            if name in names:
                found.add(name)
            else:
                out += unit
            unit, name = [], None
    return '\n'.join(out + unit), found


def cal_line(line):
    if line[:1] == '*' or not line.strip():
        return line
    m = re.match(r'(\S*)(\s+)(\S+)(\s*)(\S*)(.*)', line)
    if not m:
        return line
    loc, s1, res, s2, opnd, rest = m.groups()
    low = res.lower()
    if low == 'align':
        return '*' + line[1:]
    if opnd == 'parceln-parcel1':
        # the length of a jump in a jump table: two parcels on an X-MP (the
        # kit's assembler takes the difference of two labels for an address)
        opnd = '2'
    if low == 'con':
        opnd = re.sub(r'^(\d+)s(\d+)$', lambda g: "o'%o" % (int(g.group(1)) << int(g.group(2))), opnd, flags=re.I)
    elif low not in ('ident', 'entry', 'ext', 'bss', 'bssz', 'vwd', 'end', '=', 'common'):
        opnd = re.sub(r'([*/+\-])([fhir])(?=[sv][0-7]|$)', lambda g: g.group(1) + g.group(2).upper(), opnd)
        opnd = re.sub(r',([znpm])$', lambda g: ',' + g.group(1).upper(), opnd)
    return loc + s1 + res + s2 + opnd + rest


def cal_file(directory, name):
    out = []
    with open(os.path.join(directory, name)) as f:
        for line in f.read().split('\n'):
            m = re.match(r"\s+include\s+'(\w+)'", line)
            if m:
                out += cal_file(directory, m.group(1))
            else:
                out.append(cal_line(line.rstrip()))
    return out


def cal_sections(lines):
    out, inside = [], False
    for line in lines:
        m = re.match(r'\s+common\b\s*(\w*)', line, re.I)
        if m and line[:1] != '*':
            if inside:
                out.append('         SECTION   *')
            out.append('%-8s SECTION   COMMON' % m.group(1))
            inside = True
            continue
        if inside and re.match(r'\s+end\s*$', line, re.I):
            out.append('         SECTION   *')
            inside = False
        out.append(line)
    return out


def cal_modules(directory):
    """Every module of SRC/CAL by its name: its lines, entries and externals."""
    modules = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith('.s'):
            continue
        # what stands before a file's first IDENT is for all its modules
        module, pending, ident, shared = [], [], None, None
        for line in cal_file(directory, name):
            if re.match(r'\s+ident\s', line, re.I) and line[:1] != '*':
                ident = line.split()[1].lower()
                if shared is None:
                    shared = pending
                    pending = []
                module = [line] + shared + pending
                pending = []
            elif ident:
                module.append(line)
                if re.match(r'\s+end\s*$', line, re.I):
                    words = [l.split() for l in module if l[:1] != '*' and l.strip()]
                    modules[ident] = (cal_sections(module),
                                      [w[1] for w in words if w[0].lower() == 'entry'],
                                      [w[1] for w in words if w[0].lower() == 'ext'])
                    ident = None
            else:
                pending.append(line)
    return modules


def kftc_name(name):
    """The external name the kit's compiler gives a routine."""
    text = '@' + name.upper()
    if len(text) > 8:
        h = 0x811c9dc5
        for c in text.encode():
            h = ((h ^ c) * 0x01000193) & 0xffffffff
        text = text[:4] + '%04x' % (h & 0xffff)
    return text


def glue(number, lines):
    return ['         IDENT     GLUE%03d' % number, 'TEXT     SECTION   CODE'] + lines + \
           ['         SECTION   *', '         END']


def to_cal(number, entry):
    """A routine of the assembly called from FORTRAN."""
    name = kftc_name(entry.rstrip('%'))
    out = ['         ENTRY     ' + name, '         EXT       ' + entry,
           '%-8s BSS       0' % name,
           '         A7        A7-1', '         A0        B00', '         ,A7       A0']
    for n in range(BY_VALUE.get(entry, 0)):
        out += ['         A1        %d,A7' % (n + 1), '         S%d        ,A1' % (n + 1)]
    out += ['         B20       A7', '         B21       A6', '         B22       A5',
            '         R         ' + entry]
    if entry in BY_VALUE:
        out.append('         S7        S1')
    out += ['         A7        B20', '         A6        B21', '         A5        B22',
            '         A0        ,A7', '         A7        A7+1', '         B00       A0',
            '         J         B00']
    return glue(number, out)


def to_fortran(number, entry):
    """A FORTRAN routine called from the assembly."""
    name = kftc_name(entry.rstrip('%'))
    values = BY_VALUE.get(entry, 0)
    out = ['         ENTRY     ' + entry, '         EXT       ' + name,
           '%-8s BSS       0' % entry,
           '         A7        B20', '         A6        B21', '         A5        B22',
           '         A7        A7-1', '         A0        B00', '         ,A7       A0']
    if entry in FUNCTIONS:      # the address of a dummy argument: its own
        out += ['         A7        A7-1', '         A1        A7', '         ,A7       A1']
        words = 1
    else:                       # the values, then their addresses
        for n in range(values, 0, -1):
            out += ['         A7        A7-1', '         ,A7       S%d' % n]
        for n in range(values, 0, -1):
            out += ['         A1        %d' % (values - 1), '         A1        A7+A1',
                    '         A7        A7-1', '         ,A7       A1']
        words = 2 * values
    out.append('         R         ' + name)
    if words:
        out += ['         A1        %d' % words, '         A7        A7+A1']
    if values or entry in FUNCTIONS:
        out.append('         S1        S7')
    out += ['         A0        ,A7', '         A7        A7+1', '         B00       A0',
            '         B20       A7', '         B21       A6', '         B22       A5',
            '         J         B00']
    return glue(number, out)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(dst, 'cal'), exist_ok=True)
    wanted = os.environ.get('BLITZ_CAL', ' '.join(CAL_MODULES)).split()
    wanted = [] if wanted == ['none'] else wanted
    dropped, missing = set(), set()
    if wanted:
        modules = cal_modules(os.path.join(src, 'CAL'))
        for name in wanted:
            missing |= set(REPLACES.get(name, [name]))
        dropped = set(missing)
        wanted.append('setb60')
    for name in sorted(os.listdir(src)):
        if not name.endswith('.f') or name in LEFT_OUT:
            continue
        with open(os.path.join(src, name)) as f:
            text = convert(name, f.read())
        if dropped:
            text, found = without_units(text, dropped)
            missing -= found
            text = text.replace('c     tdata(1)=setb60(loc(tdata(1)))',
                                '      tdata(1)=setb60(loc(tdata(1)))')
        with open(os.path.join(dst, name), 'w') as f:
            f.write(text)
    assert not missing, missing
    for name in os.listdir(os.path.join(dst, 'cal')):
        os.remove(os.path.join(dst, 'cal', name))
    if not wanted:
        return
    entries, externals = [], []
    for name in wanted:
        lines, e, x = modules[name]
        entries += e
        externals += x
        with open(os.path.join(dst, 'cal', name + '.cal'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
    number = 0
    for entry in entries:
        number += 1
        with open(os.path.join(dst, 'cal', 'g%03d.cal' % number), 'w') as f:
            f.write('\n'.join(to_cal(number, entry)) + '\n')
    for entry in sorted(set(externals) - set(entries)):
        number += 1
        with open(os.path.join(dst, 'cal', 'g%03d.cal' % number), 'w') as f:
            f.write('\n'.join(to_fortran(number, entry)) + '\n')


if __name__ == '__main__':
    main()
