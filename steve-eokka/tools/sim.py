"""A small mcfunction interpreter: enough of Minecraft to dry-run the whole game loop headlessly."""
import os, re, math, random, json, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import read_tok, parse_snbt, split_top

PASS = set()

class Ent:
    n = 0
    def __init__(s, typ, pos, tags=(), rot=(0.0, 0.0)):
        Ent.n += 1; s.id = Ent.n; s.type = typ; s.pos = list(pos); s.rot = list(rot); s.tags = set(tags); s.data = {}
    def eye(s): return 25.9 if s.type == 'player' else (1.62 if s.type == 'mannequin' else 1.5)

class Ctx:
    __slots__ = ('ent', 'pos', 'rot')
    def __init__(s, ent=None, pos=(0.0, 0.0, 0.0), rot=(0.0, 0.0)): s.ent = ent; s.pos = tuple(pos); s.rot = tuple(rot)
    def w(s, **k): return Ctx(k.get('ent', s.ent), k.get('pos', s.pos), k.get('rot', s.rot))

class Return(Exception):
    def __init__(s, v): s.v = v

def toks(line):
    out = []; i = 0
    while i < len(line):
        j = read_tok(line, i)
        if j is None: j = len(line)
        out.append(line[i:j]); i = j + 1
    return out

def in_range(v, r):
    if '..' in r:
        a, b = r.split('..')
        return (a == '' or v >= float(a)) and (b == '' or v <= float(b))
    return v == float(r)

class Sim:
    def __init__(s, root, ns='ek', seed=1):
        s.ns = ns; s.fns = {}; s.scores = {}; s.ents = []; s.blocks = {}; s.storage = {}; s.sched = []; s.t = 0
        s.unknown = Counter(); s.log = []; s.rnd = random.Random(seed); s.cache = {}; s.missing = Counter(); s.cmds = 0
        fdir = os.path.join(root, 'data', ns, 'function')
        for d, _, fs in os.walk(fdir):
            for f in fs:
                name = os.path.relpath(os.path.join(d, f), fdir)[:-11].replace(os.sep, '/')
                s.fns[name] = [l.rstrip('\n') for l in open(os.path.join(d, f), encoding='utf-8') if l.strip() and not l.startswith('#')]
        tag = json.load(open(os.path.join(root, 'data', ns, 'tags', 'block', 'pass.json')))
        PASS.update(v.replace('minecraft:', '') for v in tag['values'])

    # ---------------- helpers
    def sc(s, holder, obj, ctx):
        if holder.startswith('@'):
            es = s.select(holder, ctx)
            return [(e.id, obj) for e in es]
        return [(holder, obj)]
    def get(s, name): return s.scores.get(('#' + name, 'ek'))
    def block(s, x, y, z): return s.blocks.get((math.floor(x), math.floor(y), math.floor(z)), 'air')
    def coord(s, tk, base):
        if tk.startswith('~'): return base + (float(tk[1:]) if len(tk) > 1 else 0.0)
        return float(tk)
    def pos(s, t3, ctx, block=False):
        if t3[0].startswith('^'):
            l, u, f = [float(t[1:]) if len(t) > 1 else 0.0 for t in t3]
            yaw, pitch = ctx.rot
            a = math.radians(yaw + 90); f1, g1 = math.cos(a), math.sin(a)
            h, i = math.cos(math.radians(-pitch)), math.sin(math.radians(-pitch))
            j, k = math.cos(math.radians(-pitch + 90)), math.sin(math.radians(-pitch + 90))
            fw = (f1 * h, i, g1 * h); up = (f1 * j, k, g1 * j)
            lf = (-(fw[1] * up[2] - fw[2] * up[1]), -(fw[2] * up[0] - fw[0] * up[2]), -(fw[0] * up[1] - fw[1] * up[0]))
            return tuple(ctx.pos[n] + fw[n] * f + up[n] * u + lf[n] * l for n in range(3))
        out = []
        for n in range(3):
            v = s.coord(t3[n], ctx.pos[n])
            if not t3[n].startswith('~') and '.' not in t3[n] and n != 1 and not block: v += 0.5
            out.append(v)
        return tuple(out)
    def facing(s, frm, to):
        dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
        return (math.degrees(math.atan2(dz, dx)) - 90.0, -math.degrees(math.atan2(dy, math.hypot(dx, dz))))

    def select(s, sel, ctx):
        m = re.match(r'^@([aeprsn])(\[(.*)\])?$', sel, re.S)
        if not m: return []
        kind = m.group(1); args = []
        if m.group(3):
            for p in split_top(m.group(3)):
                k, v = p.split('=', 1); args.append((k.strip(), v.strip()))
        if kind == 's': pool = [ctx.ent] if ctx.ent is not None and ctx.ent in s.ents else []
        elif kind in 'ap': pool = [e for e in s.ents if e.type == 'player']
        else: pool = list(s.ents)
        limit = None; sort = 'nearest' if kind in 'pn' else None
        if kind in 'pn': limit = 1
        for k, v in args:
            if k == 'tag':
                pool = [e for e in pool if (v[1:] not in e.tags if v.startswith('!') else v in e.tags)]
            elif k == 'type':
                vv = v.replace('minecraft:', '')
                pool = [e for e in pool if (e.type != vv[1:] if vv.startswith('!') else e.type == vv)]
            elif k == 'limit': limit = int(v)
            elif k == 'sort': sort = v
            elif k == 'distance':
                pool = [e for e in pool if in_range(math.dist(e.pos, ctx.pos), v)]
            elif k == 'scores':
                for kv in split_top(v[1:-1]):
                    o, r = kv.split('=')
                    pool = [e for e in pool if (e.id, o) in s.scores and in_range(s.scores[(e.id, o)], r)]
            else: s.unknown['selector:' + k] += 1
        if sort == 'nearest': pool.sort(key=lambda e: math.dist(e.pos, ctx.pos))
        elif sort == 'random': s.rnd.shuffle(pool)
        if limit is not None: pool = pool[:limit]
        return pool

    def match_block(s, pred, x, y, z):
        b = s.block(x, y, z).split('[')[0]
        if pred.startswith('#'): return b in PASS
        return pred.replace('minecraft:', '').split('[')[0] == b

    # ---------------- functions
    def run_fn(s, name, ctx, args=None):
        if name not in s.fns:
            s.missing[name] += 1; return 0
        try:
            for line in s.fns[name]:
                if line.startswith('$'):
                    line = re.sub(r'\$\((\w+)\)', lambda m: str((args or {}).get(m.group(1), '?')), line[1:])
                s.run_line(line, ctx)
        except Return as r:
            return r.v
        return 1

    def run_line(s, line, ctx):
        tk = s.cache.get(line)
        if tk is None:
            tk = toks(line); s.cache[line] = tk
        return s.cmd(tk, 0, ctx, line)

    def snbt_plain(s, v):
        if isinstance(v, tuple):
            m = re.match(r'^(-?\d+(\.\d+)?)[bBsSlLfFdD]?$', v[1])
            if m: return float(m.group(1)) if '.' in m.group(1) else int(m.group(1))
            return v[1]
        if isinstance(v, dict): return {k: s.snbt_plain(x) for k, x in v.items()}
        if isinstance(v, list): return [s.snbt_plain(x) for x in v]
        return v

    def cmd(s, tk, i, ctx, line):
        s.cmds += 1
        c = tk[i]
        if c == 'execute': return s.execute(tk, i + 1, [ctx], line)
        if c == 'function':
            name = tk[i + 1].split(':', 1)[1]; args = None
            if len(tk) > i + 2:
                if tk[i + 2] == 'with':
                    d = s.storage
                    for part in tk[i + 5].split('.'): d = d.get(part, {}) if isinstance(d, dict) else {}
                    args = d
                else: args = s.snbt_plain(parse_snbt(tk[i + 2]))
            return s.run_fn(name, ctx, args)
        if c == 'return':
            if tk[i + 1] == 'run': raise Return(s.cmd(tk, i + 2, ctx, line))
            if tk[i + 1] == 'fail': raise Return(0)
            raise Return(int(tk[i + 1]))
        if c == 'scoreboard':
            if tk[i + 1] == 'objectives': return 1
            op = tk[i + 2]
            if op in ('set', 'add', 'remove'):
                for key in s.sc(tk[i + 3], tk[i + 4], ctx):
                    v = int(tk[i + 5])
                    s.scores[key] = v if op == 'set' else s.scores.get(key, 0) + (v if op == 'add' else -v)
                return 1
            if op == 'reset':
                for key in s.sc(tk[i + 3], tk[i + 4], ctx): s.scores.pop(key, None)
                return 1
            if op == 'get':
                key = s.sc(tk[i + 3], tk[i + 4], ctx)
                return s.scores.get(key[0], 0) if key else 0
            if op == 'operation':
                a = s.sc(tk[i + 3], tk[i + 4], ctx); b = s.sc(tk[i + 6], tk[i + 7], ctx); o = tk[i + 5]
                if not a or not b: return 0
                bv = s.scores.get(b[0], 0); av = s.scores.get(a[0], 0)
                if o == '=': av = bv
                elif o == '+=': av += bv
                elif o == '-=': av -= bv
                elif o == '*=': av *= bv
                elif o == '/=': av = av // bv if bv else av
                elif o == '%=': av = av % bv if bv else av
                elif o == '<': av = min(av, bv)
                elif o == '>': av = max(av, bv)
                s.scores[a[0]] = av; return av
        if c == 'random':
            a, b = tk[i + 2].split('..'); return s.rnd.randint(int(a), int(b))
        if c in ('tp', 'teleport'):
            targets = s.select(tk[i + 1], ctx); rest = tk[i + 2:]
            if not rest: return 0
            p = s.pos(rest[:3], ctx); rot = None
            if len(rest) >= 5 and rest[3] == 'facing':
                if rest[4] == 'entity':
                    es = s.select(rest[5], ctx)
                    if es:
                        tgt = list(es[0].pos)
                        if len(rest) > 6 and rest[6] == 'eyes': tgt[1] += es[0].eye()
                        rot = ('face', tgt)
                else: rot = ('face', s.pos(rest[4:7], ctx))
            elif len(rest) >= 5:
                rot = ('abs', (s.coord(rest[3], ctx.rot[0]), s.coord(rest[4], ctx.rot[1])))
            for e in targets:
                e.pos = list(p)
                if rot:
                    e.rot = list(s.facing(p, rot[1])) if rot[0] == 'face' else list(rot[1])
            return len(targets)
        if c == 'summon':
            typ = tk[i + 1].replace('minecraft:', ''); p = s.pos(tk[i + 2:i + 5], ctx) if len(tk) > i + 4 else ctx.pos
            e = Ent(typ, p)
            if len(tk) > i + 5:
                d = s.snbt_plain(parse_snbt(tk[i + 5]))
                e.tags = set(d.get('Tags', []));
                if 'Rotation' in d: e.rot = [float(x) for x in d['Rotation']]
            s.ents.append(e); return 1
        if c == 'kill':
            es = [e for e in s.select(tk[i + 1], ctx) if e.type != 'player']
            for e in es: s.ents.remove(e)
            return len(es)
        if c == 'tag':
            es = s.select(tk[i + 1], ctx)
            for e in es: (e.tags.add if tk[i + 2] == 'add' else e.tags.discard)(tk[i + 3])
            return len(es)
        if c == 'setblock':
            x, y, z = [math.floor(v) for v in s.pos(tk[i + 1:i + 4], ctx, True)]
            b = tk[i + 4].replace('minecraft:', ''); mode = tk[i + 5] if len(tk) > i + 5 else ''
            if mode == 'keep' and s.block(x, y, z) != 'air': return 0
            if b == 'air': s.blocks.pop((x, y, z), None)
            else: s.blocks[(x, y, z)] = b
            return 1
        if c == 'fill':
            a = [math.floor(v) for v in s.pos(tk[i + 1:i + 4], ctx, True)]; b = [math.floor(v) for v in s.pos(tk[i + 4:i + 7], ctx, True)]
            blk = tk[i + 7].replace('minecraft:', ''); flt = None
            if len(tk) > i + 9 and tk[i + 8] == 'replace': flt = tk[i + 9]
            n = 0
            for x in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
                for y in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                    for z in range(min(a[2], b[2]), max(a[2], b[2]) + 1):
                        if flt and not s.match_block(flt, x, y, z): continue
                        if blk == 'air': s.blocks.pop((x, y, z), None)
                        else: s.blocks[(x, y, z)] = blk
                        n += 1
            return n
        if c == 'data':
            if tk[i + 1] == 'get' and tk[i + 2] == 'entity':
                es = s.select(tk[i + 3], ctx)
                if not es: raise KeyError('nodata')
                path = tk[i + 4]; scale = float(tk[i + 5]) if len(tk) > i + 5 else 1
                if path.startswith('Pos['): return math.floor(es[0].pos[int(path[4])] * scale)
                if path == 'SelectedItemSlot': return es[0].data.get('slot', 0)
                return 0
            if tk[i + 1] == 'modify' and tk[i + 2] == 'storage':
                d = s.storage; parts = tk[i + 4].split('.')
                for part in parts[:-1]: d = d.setdefault(part, {})
                d[parts[-1]] = s.snbt_plain(parse_snbt(tk[i + 7]))
                return 1
            return 1
        if c == 'schedule':
            s.sched.append((s.t + int(tk[i + 3].rstrip('t')), tk[i + 2].split(':', 1)[1])); return 1
        if c == 'tellraw':
            try:
                v = s.snbt_plain(parse_snbt(tk[i + 2]))
                def flat_text(v):
                    if isinstance(v, str): return v
                    if isinstance(v, list): return ''.join(flat_text(x) for x in v)
                    if isinstance(v, dict):
                        base = v.get('text', '')
                        if 'score' in v: base = str(s.scores.get((v['score']['name'], v['score']['objective']), '?'))
                        if 'nbt' in v: base = str(s.storage.get(v['nbt'], '?'))
                        return str(base) + flat_text(v.get('extra', []))
                    return str(v)
                s.log.append((s.t, flat_text(v).strip()))
            except Exception as ex: s.log.append((s.t, 'TELLRAW-ERR ' + str(ex)))
            return 1
        if c in ('particle', 'playsound', 'title', 'bossbar', 'item', 'effect', 'attribute', 'gamemode', 'clear', 'time', 'weather',
                 'swing', 'damage', 'forceload', 'gamerule', 'xp', 'stopsound'):
            return 1
        s.unknown[c] += 1
        return 0

    def execute(s, tk, i, ctxs, line):
        store = []
        while i < len(tk):
            sub = tk[i]
            if sub == 'run':
                res = 0
                for ctx in ctxs:
                    try:
                        res = s.cmd(tk, i + 1, ctx, line)
                    except KeyError:
                        res = 0
                    for kind, a, b, cx in store:
                        if kind == 'score':
                            for key in s.sc(a, b, cx): s.scores[key] = int(res)
                        elif kind == 'storage':
                            d = s.storage; parts = b.split('.')
                            for part in parts[:-1]: d = d.setdefault(part, {})
                            d[parts[-1]] = int(res)
                return res
            if sub == 'as':
                ctxs = [c.w(ent=e) for c in ctxs for e in s.select(tk[i + 1], c)]; i += 2
            elif sub == 'at':
                ctxs = [c.w(pos=tuple(e.pos), rot=tuple(e.rot)) for c in ctxs for e in s.select(tk[i + 1], c)]; i += 2
            elif sub == 'positioned':
                if tk[i + 1] == 'as':
                    ctxs = [c.w(pos=tuple(e.pos)) for c in ctxs for e in s.select(tk[i + 2], c)]; i += 3
                else:
                    ctxs = [c.w(pos=s.pos(tk[i + 1:i + 4], c)) for c in ctxs]; i += 4
            elif sub == 'rotated':
                ctxs = [c.w(rot=(s.coord(tk[i + 1], c.rot[0]), s.coord(tk[i + 2], c.rot[1]))) for c in ctxs]; i += 3
            elif sub == 'facing':
                if tk[i + 1] == 'entity':
                    new = []
                    for c in ctxs:
                        es = s.select(tk[i + 2], c)
                        if es:
                            tgt = list(es[0].pos)
                            if tk[i + 3] == 'eyes': tgt[1] += es[0].eye()
                            new.append(c.w(rot=s.facing(c.pos, tgt)))
                    ctxs = new; i += 4
                else:
                    ctxs = [c.w(rot=s.facing(c.pos, s.pos(tk[i + 1:i + 4], c))) for c in ctxs]; i += 4
            elif sub in ('if', 'unless'):
                want = sub == 'if'; kind = tk[i + 1]; new = []
                if kind == 'score':
                    if tk[i + 4] == 'matches':
                        for c in ctxs:
                            key = s.sc(tk[i + 2], tk[i + 3], c)
                            ok = bool(key) and key[0] in s.scores and in_range(s.scores[key[0]], tk[i + 5])
                            if ok == want: new.append(c)
                        i += 6
                    else:
                        for c in ctxs:
                            ka = s.sc(tk[i + 2], tk[i + 3], c); kb = s.sc(tk[i + 5], tk[i + 6], c)
                            ok = False
                            if ka and kb and ka[0] in s.scores and kb[0] in s.scores:
                                a, b = s.scores[ka[0]], s.scores[kb[0]]
                                ok = {'<': a < b, '<=': a <= b, '=': a == b, '>=': a >= b, '>': a > b}[tk[i + 4]]
                            if ok == want: new.append(c)
                        i += 7
                elif kind == 'entity':
                    new = [c for c in ctxs if bool(s.select(tk[i + 2], c)) == want]; i += 3
                elif kind == 'block':
                    for c in ctxs:
                        p = s.pos(tk[i + 2:i + 5], c, True)
                        if s.match_block(tk[i + 5], *p) == want: new.append(c)
                    i += 6
                elif kind == 'loaded':
                    new = ctxs if want else []; i += 5
                elif kind == 'predicate':
                    new = [] if want else ctxs; i += 3
                else:
                    s.unknown['if ' + kind] += 1; return 0
                ctxs = new
            elif sub == 'store':
                if tk[i + 2] == 'score': store.append(('score', tk[i + 3], tk[i + 4], ctxs[0] if ctxs else Ctx())); i += 5
                elif tk[i + 2] == 'storage': store.append(('storage', tk[i + 3], tk[i + 4], None)); i += 7
                elif tk[i + 2] == 'bossbar': i += 5
                else: s.unknown['store ' + tk[i + 2]] += 1; return 0
            else:
                s.unknown['execute ' + sub] += 1; return 0
            if not ctxs: return 0
        return 1

    def step(s):
        due = [f for (tt, f) in s.sched if tt <= s.t]; s.sched = [(tt, f) for (tt, f) in s.sched if tt > s.t]
        for f in due: s.run_fn(f, Ctx())
        s.run_fn('tick', Ctx()); s.t += 1
