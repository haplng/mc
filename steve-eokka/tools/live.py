"""Drive the real 26.3 test server: step ticks, read scores and entity data, and collect what the server logs.

The server runs frozen; `step(n)` sprints n ticks and waits until it is frozen again, so runs are repeatable.
"""
import os, re, sys, time
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rcon import connect

LOG = ROOT + '/server/run/logs/latest.log'
NOISE = ('Services Discovery', 'Saving chunks', 'Saving the game', 'Saved the game', 'RCON', 'Rcon', 'Thread RCON', 'Automatic saving')


class Live:
    def __init__(self):
        self.r = connect()
        self.pos = os.path.getsize(LOG) if os.path.exists(LOG) else 0
        self.r.cmd('tick freeze')

    def cmd(self, c): return self.r.cmd(c)

    def step(self, n=1):
        self.r.cmd(f'tick sprint {n}')
        for _ in range(4000):
            q = self.r.cmd('tick query')
            if 'sprinting' not in q: return
            time.sleep(0.01)
        raise RuntimeError('sprint did not finish')

    def score(self, name, obj='ek'): return self.r.score(name, obj)

    def scores(self, *names): return {n: self.score('#' + n) for n in names}

    def data(self, sel, path=''):
        t = self.r.cmd(f'data get entity {sel} {path}'.strip())
        m = re.search(r'entity data: (.*)$', t, re.S)
        return m.group(1) if m else t

    def pos_of(self, sel):
        t = self.data(sel, 'Pos')
        m = re.findall(r'(-?\d+\.?\d*(?:E-?\d+)?)d', t)
        return tuple(float(x) for x in m[:3]) if len(m) >= 3 else None

    def count(self, sel):
        t = self.r.cmd(f'execute if entity {sel}')
        m = re.search(r'Count: (\d+)', t)
        return int(m.group(1)) if m else 0

    def block(self, x, y, z, block):
        return 'passed' in self.r.cmd(f'execute if block {x} {y} {z} {block}')

    def log(self):
        """New log lines since the last call, without routine noise."""
        if not os.path.exists(LOG): return []
        with open(LOG, encoding='utf-8', errors='replace') as f:
            f.seek(self.pos); txt = f.read(); self.pos = f.tell()
        out = []
        for line in txt.split('\n'):
            if not line.strip() or any(n in line for n in NOISE): continue
            out.append(line)
        return out

    def problems(self):
        """Log lines that look like trouble (warnings, errors, stack traces, codec complaints)."""
        return [l for l in self.log() if re.search(r'/(WARN|ERROR|FATAL)\]|Exception|Failed to|Serialization errors|^\s+at |^: ', l)]


if __name__ == '__main__':
    L = Live()
    print(L.scores('state', 'stage', 'built'))
    for l in L.log()[-20:]: print(l[:300])
