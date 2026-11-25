# -*- coding: utf-8 -*-
"""mcfunction(점수판 명령만) → C 로 옮긴다. 검증·성능 계산용.

지원: scoreboard players set/add/remove/operation, execute if|unless score ... run,
      function, return 0, return run <명령>. data/tellraw/title 등 점수와 무관한 명령은 건너뛴다.
각 명령은 CMDS 카운터를 1 올린다(게임 안에서 실행되는 명령 수 추정).
"""
import os
import re
import sys

SKIP = ('data ', 'tellraw ', 'title ', 'playsound ', 'particle ', 'dialog ', 'bossbar ', 'advancement ', 'tag ',
        'item ', 'give ', 'clear ', 'effect ', 'tp ', 'say ', 'schedule ', 'xp ', 'kill ', 'summon ', 'setblock ', 'fill ')


def cname(name, obj):
    s = name + '__' + obj
    s = s.replace('#', 'G_').replace('@s', 'P').replace('.', '_').replace('-', 'm')
    return re.sub(r'[^A-Za-z0-9_]', '_', s)


def fname(path):
    return 'f_' + re.sub(r'[^A-Za-z0-9_]', '_', path)


class T:
    def __init__(self):
        self.vars = set()
        self.funcs = {}
        self.called = set()

    def var(self, name, obj):
        c = cname(name, obj)
        self.vars.add(c)
        return c

    def rng(self, v, r):
        if '..' in r:
            lo, hi = r.split('..')
            cs = []
            if lo != '':
                cs.append('%s >= %s' % (v, lo))
            if hi != '':
                cs.append('%s <= %s' % (v, hi))
            return '(' + ' && '.join(cs) + ')' if cs else '1'
        return '(%s == %s)' % (v, r)

    def cmd(self, s, infn):
        """한 명령 → C 문장 (세미콜론 포함)"""
        s = s.strip()
        tk = s.split(' ')
        if s.startswith('execute '):
            conds = []
            i = 1
            while tk[i] != 'run':
                neg = tk[i] == 'unless'
                assert tk[i] in ('if', 'unless'), s
                assert tk[i + 1] == 'score', s
                a = self.var(tk[i + 2], tk[i + 3])
                if tk[i + 4] == 'matches':
                    c = self.rng(a, tk[i + 5])
                    i += 6
                else:
                    op = tk[i + 4]
                    b = self.var(tk[i + 5], tk[i + 6])
                    cop = {'=': '==', '<': '<', '<=': '<=', '>': '>', '>=': '>='}[op]
                    c = '(%s %s %s)' % (a, cop, b)
                    i += 7
                conds.append(('!' + c) if neg else c)
            rest = ' '.join(tk[i + 1:])
            return 'if (%s) { %s }' % (' && '.join(conds), self.cmd(rest, infn))
        if s.startswith('scoreboard players set '):
            return '%s = %s;' % (self.var(tk[3], tk[4]), tk[5])
        if s.startswith('scoreboard players add '):
            return '%s += %s;' % (self.var(tk[3], tk[4]), tk[5])
        if s.startswith('scoreboard players remove '):
            return '%s -= %s;' % (self.var(tk[3], tk[4]), tk[5])
        if s.startswith('scoreboard players operation '):
            a = self.var(tk[3], tk[4])
            op = tk[5]
            b = self.var(tk[6], tk[7])
            if op in ('=', '+=', '-=', '*='):
                return '%s %s %s;' % (a, op, b)
            if op == '/=':
                return '%s = fdiv(%s, %s);' % (a, a, b)
            if op == '%=':
                return '%s = fmod_(%s, %s);' % (a, a, b)
            if op == '<':
                return 'if (%s < %s) %s = %s;' % (b, a, a, b)
            if op == '>':
                return 'if (%s > %s) %s = %s;' % (b, a, a, b)
            raise ValueError(s)
        if s.startswith('scoreboard players reset '):
            return '%s = 0;' % self.var(tk[3], tk[4])
        if s.startswith('function '):
            p = tk[1]
            assert len(tk) == 2, 'macro call not supported: ' + s
            self.called.add(p)
            return '%s();' % fname(p)
        if s.startswith('return run '):
            rest = s[len('return run '):]
            assert not rest.startswith('execute'), 'return run execute 금지: ' + s
            return '%s return;' % self.cmd(rest, infn)
        if s.startswith('return '):
            return 'return;'
        if s.startswith(SKIP):
            return ';'
        raise ValueError('unsupported: ' + s)

    def add(self, path, lines):
        body = []
        for ln in lines:
            ln = ln.strip()
            if not ln or ln.startswith('#'):
                continue
            assert not ln.startswith('$'), 'macro line in %s' % path
            body.append('  CMDS++; ' + self.cmd(ln, path))
        self.funcs[path] = body

    def emit(self):
        out = ['#include <stdio.h>', '#include <string.h>', 'static long CMDS = 0;',
               'static inline int fdiv(int a, int b) { if (b == 0) return a; int q = a / b; if ((a % b != 0) && ((a < 0) != (b < 0))) q--; return q; }',
               'static inline int fmod_(int a, int b) { if (b == 0) return a; int r = a % b; if (r != 0 && ((r < 0) != (b < 0))) r += b; return r; }']
        for v in sorted(self.vars):
            out.append('static int %s = 0;' % v)
        for p in sorted(self.funcs):
            out.append('static void %s(void);' % fname(p))
        missing = self.called - set(self.funcs)
        for p in sorted(missing):
            out.append('static void %s(void) { }  /* 없는 함수 */' % fname(p))
        for p in sorted(self.funcs):
            out.append('static void %s(void) {' % fname(p))
            out.extend(self.funcs[p])
            out.append('}')
        return '\n'.join(out) + '\n', missing


def load_dir(root, ns, sub):
    """data/<ns>/function/<sub>/** 을 읽는다 → {ns:path: lines}"""
    base = os.path.join(root, 'data', ns, 'function')
    res = {}
    top = os.path.join(base, sub)
    for dp, dn, fns in os.walk(top):
        for f in fns:
            if f.endswith('.mcfunction'):
                full = os.path.join(dp, f)
                rel = os.path.relpath(full, base)[:-len('.mcfunction')].replace(os.sep, '/')
                res['%s:%s' % (ns, rel)] = open(full, encoding='utf-8').read().split('\n')
    return res


if __name__ == '__main__':
    root, out = sys.argv[1], sys.argv[2]
    t = T()
    for sub in sys.argv[3:]:
        for p, lines in load_dir(root, 'jb', sub).items():
            if any(l.strip().startswith('$') for l in lines):
                continue
            t.add(p, lines)
    code, missing = t.emit()
    open(out, 'w').write(code)
    if missing:
        sys.stderr.write('missing: %s\n' % sorted(missing))
