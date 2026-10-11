#!/usr/bin/env python3
"""The University of Texas Super Star Trek, from Prime FTN to FORTRAN 77 for
COS on the CRAY X-MP (COS-Tools' kftc in Hollerith mode).

    prime2cray.py startrek.ftn startrek.ins.ftn startrek.f

What changes: the common block insert is inlined; octal constants :NNN
become decimal; $ leaves the names of library routines; alternate returns
($label) become a flag the caller tests; the routines that read tokens,
freeze and thaw a game, print the citation and hash the clock are replaced
(the Primos file and terminal services they use are not here); the star
lines are literals, since an INTEGER*2 array here holds a word a cell."""
import re
import sys

STARS61 = '*' * 61
STARS54 = '*' * 54

SCAN = '''      SUBROUTINE SCAN(AITEM,KEY)
$INSERT STARTREK.INS.FTN
      REAL VAL
      INTEGER IEOL,ISNUM,IHOL
      KEY='EL'
      AITEM=0
      IF (.NOT.EOL) GOTO 10
      CALL COMANL
      EOL=.FALSE.
10    CALL RDTOK(IEOL,ISNUM,VAL,IHOL)
      EOL=IEOL.NE.0
      IF (EOL) RETURN
      IF (ISNUM.EQ.0) GOTO 20
      AITEM=VAL
      KEY='RE'
      RETURN
20    KEY='AL'
      CALL IMOVE(IHOL,AITEM,1)
      RETURN
      END
'''
MATCH = '''      LOGICAL FUNCTION MATCH(S1,S2)
      INTEGER S1,S2
      LOGICAL COMEQV
      MATCH=S1.EQ.S2
      IF (MATCH) RETURN
      MATCH=COMEQV(S1,S2)
      RETURN
      END
'''
FREEZE = '''      SUBROUTINE FREEZE(IALT)
      CALL TNOU('Freezing a game is not available on this machine.',50)
      RETURN
      END
'''
THAW = '''      SUBROUTINE THAW
$INSERT STARTREK.INS.FTN
      CALL TNOU('There are no frozen games on this machine.',42)
      PASSWD=0
      RETURN
      END
'''
PLAQUE = '''      SUBROUTINE PLAQUE(ISCORE,PERDAT,ISKILL)
      CALL TONL
      CALL TNOU('*** C I T A T I O N ***',23)
      CALL TNOUA('Your score: ',12)
      CALL TODEC(ISCORE)
      CALL TONL
      CALL TNOUA('Klingons per stardate: ',23)
      CALL PRTNUM(PERDAT,6,2)
      CALL TONL
      RETURN
      END
'''
REPLACED = {'SCAN': SCAN, 'MATCH': MATCH, 'FREEZE': FREEZE, 'THAW': THAW, 'PLAQUE': PLAQUE,
            'HASH': '', 'MAKNAM': ''}
ALTRET = {'FREEZE': 'IALT', 'NOTIME': 'IALT', 'IFEVNT': 'IALT', 'RAM': 'IARRAM'}
STAR_LINES = {
    'CALL TNOU(ASTRS,INTS(61))': ("      CALL TNOU('" + '*' * 55, '     +' + '*' * 6 + "',61)"),
    'CALL TNOU(ASTRS,54)': ("      CALL TNOU('" + STARS54 + "'", '     +,54)'),
    'CALL TNOUA(ASTRS,3)': ("      CALL TNOUA('***',3)", None),
}


def split_code(line):
    """A fixed-form line as (label, body) with the comment part untouched."""
    return line[:6], line[6:72].rstrip('\n'), line[72:].rstrip('\n')


def outside_strings(text, fn):
    """fn applied to the parts of text that are not inside quotes."""
    out = []
    i = 0
    while i < len(text):
        j = text.find("'", i)
        if j < 0:
            out.append(fn(text[i:]))
            break
        out.append(fn(text[i:j]))
        k = j + 1
        while k < len(text):
            if text[k] == "'":
                if k + 1 < len(text) and text[k + 1] == "'":
                    k += 2
                    continue
                break
            k += 1
        out.append(text[j:k + 1])
        i = k + 1
    return ''.join(out)


def octal(text):
    return re.sub(r':([0-7]+)', lambda m: str(int(m.group(1), 8)), text)


def dollars(text):
    text = text.replace('TOVFD$', 'TOVFD').replace('SLEEP$', 'SLEEPP')
    return re.sub(r'([A-Z][A-Z0-9]*)\$+', r'\1', text)


def routines(lines):
    """The source as a list of (name, lines) program units."""
    units = []
    cur = []
    name = 'MAIN'
    for line in lines:
        if not line.startswith('C') and not line.startswith('*'):
            m = re.match(r'\s*(?:SUBROUTINE|(?:LOGICAL |INTEGER |REAL )?FUNCTION)\s+([A-Z0-9]+)', line[6:], re.I)
            if m and not line[:5].strip() and line[5] == ' ':
                if cur and any(l.strip() and not l.startswith('C') for l in cur):
                    units.append((name, cur))
                cur = []
                name = m.group(1).upper()
        cur.append(line)
    units.append((name, cur))
    return units


def convert(src, ins):
    ins_lines = [l for l in ins.split('\n') if l.strip() not in ('NOLIST', 'LIST', '')]
    lines = src.split('\n')
    out = []
    for name, body in routines(lines):
        if name in REPLACED:
            text = REPLACED[name]
            for line in text.rstrip('\n').split('\n'):
                if line.startswith('$INSERT STARTREK.INS.FTN'):
                    out.extend(ins_lines)
                else:
                    out.append(line)
            continue
        altvar = ALTRET.get(name)
        pending_alt = False
        for line in body:
            if line.startswith('$INSERT STARTREK.INS.FTN'):
                # the function JA is declared by the insert too
                out.extend([l.replace('LOGICAL EOL,JA', 'LOGICAL EOL') if name == 'JA' else l for l in ins_lines])
                continue
            if line.startswith('$INSERT'):
                continue
            if line.startswith('C') or line.startswith('*') or not line.strip():
                out.append(line)
                continue
            label, code, tail = split_code(line)
            stripped = code.strip()
            if stripped in STAR_LINES:
                a, b = STAR_LINES[stripped]
                out.append(label.rstrip() + a[len(label):] if label.strip() else a)
                if b:
                    out.append(b)
                continue
            code = outside_strings(code, lambda t: re.sub(r'/\*.*$', '', t))
            code = outside_strings(code, octal)
            code = outside_strings(code, dollars)
            if name == 'MAIN' and stripped == 'SUBROUTINE MAIN':
                code = 'PROGRAM STARTREK'
            code = code.replace('IMOVE(DATE,SNPSHT,229)', 'IMOVE(DATE,SNPSHT,226)')
            code = code.replace('IMOVE(SNPSHT,DATE,229)', 'IMOVE(SNPSHT,DATE,226)')
            code = code.replace('CALL RND(NMBR)', 'QQQQ=RND(NMBR)')
            code = re.sub(r'^(\s*INTEGER)\*[24]\b', r'\1', code)
            m = re.match(r'^(\s*)PARAMETER\s+([A-Z].*)$', code)
            if m:
                code = '%sPARAMETER (%s)' % (m.group(1), m.group(2))
            # an alternate return in a call: a flag the caller tests
            m = re.match(r'^\s*CALL\s+([A-Z0-9]+)\s*\((.*?)\$(\d+)\)\s*$', code)
            if m:
                args = m.group(2)
                out.append(label + 'IALTR=0')
                out.append('      CALL %s(%sIALTR)' % (m.group(1), args))
                out.append('      IF (IALTR.NE.0) GOTO %s' % m.group(3))
                continue
            if altvar:
                m = re.match(r'^\s*GOTO\s+%s\s*$' % altvar, code)
                if m:
                    out.append(label + '%s=1' % altvar)
                    out.append('      RETURN')
                    continue
                if re.search(r'\bGOTO\s+%s\s*$' % altvar, code):
                    code = re.sub(r'\bGOTO\s+%s\s*$' % altvar, 'GOTO 9990', code)
                    pending_alt = True
                if stripped == 'END' and pending_alt:
                    out.append('9990  %s=1' % altvar)
                    out.append('      RETURN')
            out.append((label + code).rstrip() + ('' if not tail.strip() else tail))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    src = open(sys.argv[1]).read()
    ins = open(sys.argv[2]).read()
    open(sys.argv[3], 'w').write(convert(src, ins))
