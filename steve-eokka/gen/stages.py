"""The seven dioramas and Steve's scripted run through each of them."""
import math, random
from core import *
from terrain import Grid, oak_tree, ellipse, X0, X1, Z0, Z1
from engine import FLAGS

TS = 2.4
def sct(v, ts): return max(1, int(round(v * ts)))

class Beat:
    def __init__(s, label, at=None, st_='', wst=None, flags='', wflags='', alen=20, facing=None, hold_=None,
                 on_act=(), ticks=None, every=(), raw=(), on_end=(), back=None, ts=None):
        ts = TS if ts is None else ts
        s.back = back; s.label = label; s.at = at; s.st = st_; s.wst = wst or st_; s.flags = flags.split(); s.wflags = wflags.split()
        s.alen = sct(alen, ts); s.facing = facing; s.hold = hold_; s.on_act = flat(on_act)
        s.ticks = {}
        for k, v in (ticks or {}).items(): s.ticks.setdefault(sct(k, ts), []).extend(flat(v))
        s.every = [(e[0], e[1], (sct(e[2][0], ts), sct(e[2][1], ts))) if len(e) > 2 else e for e in every]
        s.raw = flat(raw); s.on_end = flat(on_end)
        assert not s.raw or ts == 1, label
        for f in s.flags + s.wflags: assert f in FLAGS, f

class Stage:
    def __init__(s, n, name):
        s.n = n; s.name = name; s.g = Grid(); s.ents = []; s.beats = []; s.init = []; s.spawn = (0, 0)
        s.tick = []; s.evclean = []; s.idx = {}; s.gear = []; s.extra = set()
    def beat(s, label, **kw):
        assert label not in s.idx, label
        s.idx[label] = len(s.beats); b = Beat(label, **kw); s.beats.append(b); return b
    def via(s, label, at, wst='이동 중', wflags=''):
        return s.beat(label, at=at, st_=wst, wst=wst, wflags=wflags, flags=wflags, alen=1, ts=1)
    def ent(s, kind, x, y, z, tags, nbt=''):
        tg = ','.join('"%s"' % a for a in ['ek.stg'] + tags)
        s.ents.append('summon minecraft:%s %s %s %s {Tags:[%s],NoAI:1b,PersistenceRequired:1b,Invulnerable:1b,Silent:1b%s}' % (kind, x, y, z, tg, nbt))
    def spawn_y(s): return s.g.stand(*s.spawn)

    def emit(s):
        n = s.n; g = s.g
        P.fn(f's{n}/build', g.cmds(), s.ents)
        P.fn(f's{n}/init', sset('blen', len(s.beats)), s.init)
        sx, sz = s.spawn
        P.fn(f's{n}/spawn', f'execute positioned {sx + 0.5} {s.spawn_y()} {sz + 0.5} run function ek:steve/summon', s.gear)
        if s.tick: P.fn(f's{n}/tick', s.tick)
        if s.evclean: P.fn(f's{n}/evclean', s.evclean)
        d_start, d_act, d_tick, d_end = [], [], [], []
        L = len(s.beats); eff = None
        backs = [iff('beat', i, 'return run ' + sset('beat', s.idx[b.back])) for i, b in enumerate(s.beats) if b.back]
        P.fn(f's{n}/restart', backs or ['return 0'])
        for i, b in enumerate(s.beats):
            pct = int(100 * i / L)
            start = [bstatus(b.wst), [sset('f_' + f, 1) for f in b.wflags], sset('prog', pct)]
            eff = b.at or eff
            if eff:
                x, z = eff
                start += [f'tp @e[tag=ek.tgt,limit=1] {x + 0.5} {g.stand(x, z)} {z + 0.5}', sset('tx', x * 100 + 50), sset('tz', z * 100 + 50)]
            else:
                start.append('function ek:beat/arrive')
            P.fn(f's{n}/b{i}_start', start)
            d_start.append(iff('beat', i, f'return run function ek:s{n}/b{i}_start'))
            act = [bstatus(b.st), 'function ek:beat/flags_clear', [sset('f_' + f, 1) for f in b.flags], sset('alen', b.alen)]
            if b.facing: act.append(face(*b.facing))
            if b.hold: act.append(hold(b.hold))
            act += b.on_act
            P.fn(f's{n}/b{i}_act', act)
            d_act.append(iff('beat', i, f'return run function ek:s{n}/b{i}_act'))
            tk = []
            for tt in sorted(b.ticks):
                tk += [iff('at', tt, c) for c in b.ticks[tt]]
            for ev in b.every:
                p, cmds = ev[0], flat(ev[1])
                rng = 'if score #at ek matches %d..%d ' % ev[2] if len(ev) > 2 else ''
                tk += ['execute %sif score #m%d ek matches 0 run %s' % (rng, p, c) for c in cmds]
            tk += b.raw
            if tk:
                P.fn(f's{n}/b{i}_tick', tk)
                d_tick.append(iff('beat', i, f'return run function ek:s{n}/b{i}_tick'))
            if b.on_end:
                P.fn(f's{n}/b{i}_end', b.on_end)
                d_end.append(iff('beat', i, f'return run function ek:s{n}/b{i}_end'))
        P.fn(f's{n}/start', d_start); P.fn(f's{n}/act', d_act)
        P.fn(f's{n}/tick_beat', d_tick or ['return 0']); P.fn(f's{n}/end', d_end or ['return 0'])

    def check_paths(s):
        issues = []; routes = []; pts = []
        cur = s.spawn
        for b in s.beats:
            if b.at and b.label not in s.extra:
                iss, _ = s.g.walk(cur, b.at, f's{s.n}:{b.label}')
                issues += iss; routes.append((cur, b.at)); cur = b.at; pts.append(b.at)
            elif b.at:
                routes.append((cur, b.at)); cur = b.at; pts.append(b.at)
        return issues, routes, pts

    def duration(s):
        tot = 0; cur = s.spawn
        for b in s.beats:
            if b.at:
                tot += math.hypot(b.at[0] - cur[0], b.at[1] - cur[1]) / 0.17; cur = b.at
            tot += b.alen
        return tot / 20.0

# ---------------------------------------------------------------- beat helpers
HIT = {'oak_log': 'block.wood.hit', 'stone': 'block.stone.hit', 'coal_ore': 'block.stone.hit', 'iron_ore': 'block.stone.hit',
       'deepslate': 'block.deepslate.hit', 'deepslate_diamond_ore': 'block.deepslate.hit', 'obsidian': 'block.stone.hit',
       'spawner': 'block.stone.hit', 'iron_bars': 'block.stone.hit'}

def mine(st, label, at, blocks, btype, te, pops=None, **kw):
    te = sct(te, TS)
    ticks = {k: flat(v) for k, v in kw.pop('ticks', {}).items()}; raw = list(kw.pop('raw', []))
    for k, (x, y, z) in enumerate(blocks):
        a, b = k * te + 1, (k + 1) * te
        ticks.setdefault(a, []).append(face(x + 0.5, y + 0.5, z + 0.5))
        raw.append('execute if score #at ek matches %d..%d if score #m6 ek matches 0 run %s' % (a, b, bpart(btype, x, y, z)))
        ticks.setdefault(b, []).append(f'setblock {x} {y} {z} minecraft:air destroy')
        if pops: ticks[b].append(popup(pops[k], 'aqua'))
    every = list(kw.pop('every', [])) + [(6, [swing(), snd(HIT[btype], 1, 0.6)])]
    return st.beat(label, at=at, alen=len(blocks) * te + 2, ticks=ticks, raw=raw, every=every, ts=1, **kw)

def looker(n=10):
    return (n, [S('tp @s ~ ~ ~ ~50 ~')])

def sprinkle(g, rnd, top, items):
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            ty = g.top(x, z)
            if g.get(x, ty, z) == top and g.get(x, ty + 1, z) == 'air':
                r = rnd.random(); acc = 0
                for blk, p in items:
                    acc += p
                    if r < acc: g.set(x, ty + 1, z, blk); break

# ================================================================ 1 & 4: plains
def plains(st, camp):
    g = st.g; rnd = random.Random(11)
    g.fill(-14, 58, -14, 14, 59, 14, 'stone'); g.fill(-14, 60, -14, 14, 60, 14, 'dirt'); g.fill(-14, 61, -14, 14, 61, 14, 'grass_block')
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            h = int(round(max(0.0, 3.6 - 0.72 * math.hypot(x - 9, z + 9))))
            if h > 0:
                g.col(x, z, 60, 61 + h - 1, 'stone'); g.set(x, 61 + h, z, 'grass_block')
    pond = set(ellipse(-9, 8, 3.2, 2.6))
    for (x, z) in ellipse(-9, 8, 4.5, 3.9):
        if (x, z) not in pond: g.set(x, 61, z, 'sand')
    for (x, z) in pond: g.set(x, 61, z, 'water'); g.set(x, 60, z, 'sand')
    g.fill(-4, 61, 11, -2, 61, 12, 'gravel')
    trees = [(-11, -10, 5), (2, 9, 4), (-3, -12, 4), (11, 7, 5)]
    t1 = None
    if not camp:
        t1 = oak_tree(g, -6, -6, 4)
        g.set(5, 62, -8, 'stone'); g.set(5, 63, -8, 'stone'); g.set(5, 62, -7, 'stone')
    for x, z, h in trees: oak_tree(g, x, z, h)
    if camp:
        g.fill(-4, 62, -6, 0, 63, -6, 'oak_planks')
        g.set(-3, 62, -5, 'crafting_table'); g.set(-2, 62, -5, 'furnace[facing=south]'); g.set(-1, 62, -5, 'chest[facing=south]')
        g.set(2, 62, 1, 'red_bed[part=foot,facing=east]'); g.set(3, 62, 1, 'red_bed[part=head,facing=east]'); g.set(1, 62, 2, 'torch')
        g.fill(3, 61, -4, 5, 61, -2, 'farmland[moisture=7]'); g.set(4, 61, -3, 'water')
        for x in (3, 4, 5):
            for z in (-4, -3, -2):
                if (x, z) != (4, -3): g.set(x, 62, z, 'wheat[age=7]')
    sprinkle(g, rnd, 'grass_block', [('short_grass', 0.16), ('dandelion', 0.02), ('poppy', 0.02)])
    return t1

def stage1():
    st = Stage(1, '1단계: 나무와 돌')
    t1 = plains(st, False)
    st.spawn = (0, 0)
    for i, (x, z, r) in enumerate(((7, 3, 200), (9, 5, 90), (6, 6, 300))):
        st.ent('sheep', x + 0.5, 62, z + 0.5, ['ek.sheep'], ',Rotation:[%df,0f]' % r)
    st.init = [sset('armor', 0)]
    NB = 'nobed'
    st.beat('look', st_='두리번거리는 중', alen=40, ticks={5: say1('오 스폰 좋은데? 일단 나무부터')}, every=[looker()])
    mine(st, 'chop', (-5, -6), t1, 'oak_log', 15, st_='나무 캐는 중', wst='나무로 가는 중', flags='busy', hold_='air')
    st.beat('table', at=(-3, -4), st_='조합 중', wst='조합대 놓을 자리 찾는 중', flags='busy', alen=30, facing=(-2.5, 62.5, -4.5),
            on_act=['setblock -3 62 -5 minecraft:crafting_table', snd('block.wood.place')],
            every=[(10, [swing(), snd('block.wood.hit', 1.4, 0.5)])], on_end=[hold('wooden_pickaxe'), popup('나무 곡괭이', 'aqua')])
    mine(st, 'stone', (4, -8), [(5, 63, -8), (5, 62, -8), (5, 62, -7)], 'stone', 18, st_='돌 캐는 중', wst='돌 찾으러 가는 중',
         flags='busy mine', hold_='wooden_pickaxe')
    st.beat('table2', at=(-3, -4), st_='돌 장비 조합 중', wst='조합대로 돌아가는 중', flags='busy', alen=30, facing=(-2.5, 62.5, -4.5),
            every=[(10, [swing(), snd('block.wood.hit', 1.4, 0.5)])], on_end=[hold('stone_sword'), popup('돌 곡괭이 · 돌 검', 'aqua')])
    st.beat('sheep', at=(7, 5), st_='양 잡는 중', wst='양 찾으러 가는 중', flags='busy fight ' + NB, wflags=NB, alen=56, hold_='stone_sword',
            on_act=[say1('침대 만들 양털 3개만')],
            every=[(8, [swing(), snd('entity.sheep.hurt', 1, 0.6), S('tp @s ~ ~ ~ facing entity @e[tag=ek.sheep,limit=1,sort=nearest] feet')])],
            ticks={t_: ['execute as @e[tag=ek.sheep,limit=1,sort=nearest] at @s run particle minecraft:poof ~ ~0.5 ~ 0.3 0.3 0.3 0.02 12 force',
                        'execute as @e[tag=ek.sheep,limit=1,sort=nearest] run function ek:fx/vanish', popup('양털 +1', 'white')] for t_ in (18, 36, 54)})
    st.beat('hill', at=(9, -9), st_='언덕 위에서 둘러보는 중', wst='언덕 올라가는 중', flags='high ' + NB, wflags=NB, alen=60,
            ticks={8: say1('저쪽에 동굴 있네. 내일은 철이다')}, every=[looker()])
    st.beat('bed', at=(1, 1), st_='잠자리 만드는 중', wst='잘 곳 찾는 중', flags='busy ' + NB, wflags=NB, alen=40, facing=(2.5, 62, 1.5),
            ticks={15: ['setblock 2 62 1 minecraft:red_bed[part=foot,facing=east]', 'setblock 3 62 1 minecraft:red_bed[part=head,facing=east]', snd('block.wood.place'), swing()],
                   30: ['setblock 1 62 2 minecraft:torch', snd('block.wood.place'), swing()]})
    st.beat('sleep', ts=1, st_='자는 중', alen=130,
            on_act=[say1('첫날은 이 정도면 됐지. 잔다')],
            raw=['execute if score #at ek matches 1..30 run time add 300'],
            ticks={32: [sset('snap', 0), f'tp {STEVE} 3.0 62.6 1.5 90 0', pose('sleeping')],
                   50: popup('Zzz', 'gray'), 85: popup('Zzz', 'gray'), 112: 'time set 6000'},
            on_end=[pose('standing'), f'tp {STEVE} 1.5 62 1.5', sset('snap', 1), say1('굿모닝. 철 캐러 간다')])
    return st

def stage4():
    st = Stage(4, '4단계: 네더 포탈')
    plains(st, True)
    st.spawn = (0, 0)
    for x, z, r in ((7, 6, 120), (9, 7, 250)):
        st.ent('sheep', x + 0.5, 62, z + 0.5, ['ek.sheep'], ',Rotation:[%df,0f]' % r)
    st.init = [sset('armor', 2), 'execute store result score #flint ek run random value 1..2', sset('gk', 0)]
    st.gear = [hold('diamond_pickaxe')]
    st.beat('home', st_='집 도착', alen=30, ticks={5: say1('집 도착. 포탈부터 짓자')}, every=[looker()])
    st.beat('chest', at=(-1, -4), st_='상자에서 흑요석 꺼내는 중', wst='상자로 가는 중', flags='busy', alen=30, facing=(-0.5, 62.5, -4.5),
            on_act=[snd('block.chest.open')], on_end=[hold('obsidian')])
    frame = [(9, 62, 2), (10, 62, 2), (8, 63, 2), (11, 63, 2), (8, 64, 2), (11, 64, 2), (8, 65, 2), (11, 65, 2), (9, 66, 2), (10, 66, 2)]
    st.beat('frame', at=(9, 4), st_='포탈 틀 쌓는 중', wst='포탈 지을 자리로 가는 중', flags='busy frame', wflags='frame', alen=len(frame) * 10 + 4,
            facing=(10, 64, 2.5), hold_='obsidian',
            ticks={(k + 1) * 10: [f'setblock {x} {y} {z} minecraft:obsidian', snd('block.stone.place', 0.8), swing()] for k, (x, y, z) in enumerate(frame)},
            on_end=[say1('틀 완성. 아 부싯돌이 없네')])
    gcells = [(-4, 11), (-3, 11), (-2, 11), (-4, 12), (-3, 12), (-2, 12)]
    P.fn('s4/dig',
         [iff('gk', k, f'setblock {x} 61 {z} minecraft:air destroy') for k, (x, z) in enumerate(gcells)],
         sadd('gk', 1),
         iff('gk', 6, 'fill -4 61 11 -2 61 12 minecraft:gravel'), iff('gk', 6, snd('block.gravel.break', 0.7)), iff('gk', 6, sset('gk', 0)),
         'execute if score #flint ek matches 1.. run return run function ek:s4/flint_miss',
         popup('부싯돌!', 'green'), snd('entity.item.pickup'))
    P.fn('s4/flint_miss', ssub('flint', 1), sset('at', 0), popup('자갈...', 'gray'),
         'execute store result score #r ek run random value 1..4',
         iff('r', 1, say(['부싯돌 왜 안 나와', '자갈만 몇 개째야', '확률 10%가 이렇게 낮았나'])))
    st.beat('gravel', at=(-3, 10), st_='부싯돌 나올 때까지 자갈 캐는 중', wst='자갈 찾으러 가는 중', flags='busy gravel', alen=22,
            facing=(-2.5, 61.5, 11.5), hold_='diamond_pickaxe',
            every=[(6, [swing(), snd('block.gravel.break', 1, 0.5)])], ticks={20: 'function ek:s4/dig'})
    st.beat('fs', at=(-3, -4), st_='부싯돌과 부시 만드는 중', wst='조합대로 가는 중', flags='busy', alen=25, facing=(-2.5, 62.5, -4.5),
            every=[(10, [swing(), snd('block.wood.hit', 1.4, 0.5)])], on_end=[hold('flint_and_steel'), popup('부싯돌과 부시', 'aqua')])
    st.beat('food', at=(4, -1), st_='식량 챙기는 중', wst='밭으로 가는 중', flags='busy', alen=40, facing=(4.5, 62.5, -1.5),
            every=[(8, [swing()])],
            ticks={10: 'setblock 3 62 -2 minecraft:air destroy', 20: 'setblock 4 62 -2 minecraft:air destroy', 30: 'setblock 5 62 -2 minecraft:air destroy',
                   38: [snd('entity.generic.eat'), popup('빵 +3', 'white')]})
    st.beat('light', at=(9, 4), st_='포탈 점화!', wst='포탈로 가는 중', flags='frame', alen=40, facing=(10, 64, 2.5), hold_='flint_and_steel',
            ticks={8: [swing(), snd('item.flintandsteel.use'), 'fill 9 63 2 10 65 2 minecraft:nether_portal[axis=x]', snd('block.portal.trigger', 1, 0.5)],
                   16: [say1('네더 가즈아')] + heal_once('lit', 6)})
    st.beat('enter', at=(9, 2), st_='포탈 타는 중', wst='포탈로 들어가는 중', alen=30,
            ticks={5: snd('block.portal.travel', 1.2, 0.4), 28: at_s('particle minecraft:portal ~ ~1 ~ 0.3 0.6 0.3 0.5 60 force')})
    st.extra.add('enter')
    return st

# ================================================================ 2: iron cave
def cave_mass(g, rnd, blk, top, mats):
    g.fill(-14, 58, -14, 14, top, 14, blk)
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            r = rnd.random()
            if r < 0.30: g.set(x, top + 1, z, blk)
            if r < 0.09: g.set(x, top + 2, z, blk)
    for (x, y, z), b in list(g.b.items()):
        r = rnd.random(); acc = 0
        for m, p in mats:
            acc += p
            if r < acc: g.b[(x, y, z)] = m; break

def carve(g, cells, floor):
    for (x, z) in cells:
        for y in range(floor + 1, 87): g.set(x, y, z, None)

def stage2():
    st = Stage(2, '2단계: 철 캐기'); g = st.g; rnd = random.Random(22)
    cave_mass(g, rnd, 'stone', 64, [('andesite', 0.10), ('cobblestone', 0.07), ('tuff', 0.04)])
    for x in range(X0, X1 + 1):
        for z in range(11, 15):
            carve(g, [(x, z)], 64); g.set(x, 63, z, 'dirt'); g.set(x, 64, z, 'grass_block')
    for z, top in ((12, 63), (11, 62), (10, 61), (9, 60), (8, 59)):
        for x in (-1, 0, 1):
            carve(g, [(x, z)], top); g.set(x, top, z, 'cobblestone')
    rooms = set(ellipse(0, 2, 7.5, 5.2)) | set(ellipse(-10, 1, 2.6, 2.6)) | set(ellipse(10, 0, 2.6, 3.0)) | set(ellipse(1, -9, 5.5, 3.2))
    rooms |= {(x, z) for x in (-1, 0, 1) for z in range(-6, -2)}
    rooms |= {(x, z) for x in range(5, 10) for z in (0, 1, 2)} | {(x, z) for x in range(-9, -5) for z in (0, 1, 2, 3)}
    carve(g, rooms, 59)
    for (x, z) in rooms:
        r = rnd.random()
        g.set(x, 59, z, 'cobblestone' if r < 0.15 else ('gravel' if r < 0.22 else 'stone')); g.set(x, 58, z, 'stone')
    coal = [(-13, 61, 1), (-13, 60, 1), (-13, 60, 0)]
    iron = [(13, 61, 0), (13, 60, 0), (13, 60, -1), (13, 60, 1)]
    iron2 = [(1, 61, -13), (1, 60, -13), (0, 60, -13)]
    for c in coal: g.set(*c, 'coal_ore')
    for c in iron + iron2: g.set(*c, 'iron_ore')
    for c in ((-13, 60, 2), (12, 61, -3), (6, 60, -13), (-8, 60, 7)): g.set(*c, 'copper_ore')
    g.fill(-4, 59, -10, -3, 59, -9, 'lava')
    for c in ((3, 60, 6), (6, 60, 5), (-4, 60, -1), (5, 60, -8)): g.set(*c, 'pointed_dripstone[thickness=tip,vertical_direction=up]')
    st.spawn = (0, 13)
    st.init = [sset('armor', 0)]; st.gear = [hold('stone_pickaxe')]
    D = 'dark'
    st.beat('enter', st_='동굴 입구', alen=25, ticks={5: say1('동굴 입장. 철 나와라')}, every=[looker()])
    st.beat('down', at=(0, 7), st_='횃불 꽂는 중', wst='동굴로 내려가는 중', wflags=D, flags=D, alen=12,
            ticks={6: ['setblock 2 60 7 minecraft:torch', snd('block.wood.place'), swing()]})
    st.via('v0', (-4, 3), '석탄 발견', 'dark maze')
    mine(st, 'coal', (-12, 1), coal, 'coal_ore', 16, st_='석탄 캐는 중', wst='석탄 발견', flags='busy mine dark', wflags='dark maze', hold_='stone_pickaxe')
    st.beat('torch', at=(-5, 2), st_='횃불 만드는 중', wst='돌아 나오는 중', wflags='dark maze', flags='busy dark', alen=16,
            ticks={8: ['setblock -6 60 3 minecraft:torch', 'setblock 6 60 1 minecraft:torch', 'setblock 0 60 -4 minecraft:torch', snd('block.wood.place'), swing(), say1('횃불 넉넉하다')]})
    mine(st, 'iron', (12, 0), iron, 'iron_ore', 20, st_='철 캐는 중', wst='철 찾는 중', flags='busy mine dark', wflags='dark maze', hold_='stone_pickaxe',
         ticks={1: say1('철이다! 4개')})
    st.via('v1', (0, 1), '더 안쪽으로 가는 중', 'dark maze'); st.via('v2', (0, -6), '더 안쪽으로 가는 중', 'dark maze')
    mine(st, 'iron2', (1, -12), iron2, 'iron_ore', 20, st_='용암 옆에서 철 캐는 중', wst='더 안쪽으로 가는 중', flags='busy mine dark', wflags='dark maze', hold_='stone_pickaxe',
         ticks={1: say1('용암 옆이네. 조심조심')})
    st.via('v3', (0, -6), '넓은 곳으로 돌아가는 중', 'dark maze')
    st.beat('smelt', at=(0, 3), st_='철 굽는 중', wst='화로 놓을 자리로 가는 중', wflags='dark maze', flags='busy dark', alen=80, facing=(1.5, 60.5, 2.5),
            on_act=['setblock 1 60 2 minecraft:furnace[facing=south,lit=true]', 'setblock -1 60 2 minecraft:crafting_table', snd('block.stone.place')],
            every=[(10, ['particle minecraft:flame 1.5 60.6 3.1 0.1 0.1 0.05 0.01 3 force', snd('block.furnace.fire_crackle', 1, 0.6)])])
    st.beat('gear', st_='철 장비 조합 중', flags='busy dark', alen=30, facing=(-0.5, 60.5, 2.5),
            every=[(10, [swing(), snd('block.wood.hit', 1.4, 0.5)])],
            on_end=[hold('iron_pickaxe'), sset('armor', 1), 'function ek:steve/equip', popup('철 곡괭이 · 철 흉갑 · 양동이', 'aqua'), say1('철 장비 완성. 이제 다이아')] + heal_once('iron', 6))
    st.via('v4', (0, -6), '더 깊은 굴을 찾는 중', 'dark maze')
    st.beat('deeper', at=(5, -11), st_='더 깊이 내려가는 중', wst='더 깊은 굴을 찾는 중', wflags='dark maze', flags=D, alen=10)
    return st

# ================================================================ 3: diamonds
def stage3():
    st = Stage(3, '3단계: 다이아'); g = st.g; rnd = random.Random(33)
    cave_mass(g, rnd, 'deepslate', 63, [('cobbled_deepslate', 0.10), ('tuff', 0.06), ('deepslate_redstone_ore', 0.012), ('deepslate_gold_ore', 0.008), ('deepslate_lapis_ore', 0.008)])
    for z, top in ((12, 62), (11, 61), (10, 60), (9, 59)):
        for x in (-1, 0, 1):
            carve(g, [(x, z)], top); g.set(x, top, z, 'cobbled_deepslate')
    room = set(ellipse(0, 0, 11.5, 8.5))
    carve(g, room, 59)
    for (x, z) in room: g.set(x, 59, z, 'cobbled_deepslate' if rnd.random() < 0.18 else 'deepslate'); g.set(x, 58, z, 'deepslate')
    lake = set(ellipse(6, -2, 4.6, 3.6))
    keep = {(x, -2) for x in range(1, 7)} | {(x, z) for x in (5, 6, 7) for z in (-3, -2, -1)}
    for (x, z) in lake - keep: g.set(x, 59, z, 'lava'); g.set(x, 58, z, 'lava')
    d1 = [(-12, 61, 0), (-12, 60, 0), (-12, 60, -1)]
    d2 = [(7, 60, -3), (7, 60, -2)]
    for c in d1 + d2: g.set(*c, 'deepslate_diamond_ore')
    br1 = [(-9, 61, 6), (-9, 60, 6), (-10, 60, 6)]; br2 = [(-9, 61, -6), (-9, 60, -6)]
    for c in br1 + br2: g.set(*c, 'deepslate')
    obs = [(9, 60, 3), (10, 60, 3), (9, 60, 2)]
    for c in obs: g.set(*c, 'obsidian')
    g.set(10, 59, 4, 'obsidian'); g.set(9, 59, 4, 'obsidian'); g.fill(8, 59, 6, 9, 59, 6, 'water')
    st.spawn = (0, 13)
    st.init = [sset('armor', 1)]; st.gear = [hold('iron_pickaxe')]
    D = 'dark'
    st.beat('arrive', st_='깊은 동굴 도착', alen=25, ticks={5: say1('여기가 다이아 층. 나와라 다이아')}, every=[looker()])
    st.via('v1', (0, 7), '깊은 동굴로 내려가는 중', 'dark')
    mine(st, 'branch1', (-8, 6), br1, 'deepslate', 16, st_='가지 캐기 중', wst='캘 자리 찾는 중', flags='busy mine dark', wflags=D, hold_='iron_pickaxe',
         on_end=[say1('없네...')])
    mine(st, 'branch2', (-8, -6), br2, 'deepslate', 16, st_='가지 캐기 중', wst='다른 벽으로 가는 중', flags='busy mine dark', wflags=D, hold_='iron_pickaxe')
    mine(st, 'dia1', (-11, 0), d1, 'deepslate_diamond_ore', 28, pops=['다이아 +1', '다이아 +1', '다이아 +1'], st_='다이아 캐는 중', wst='반짝이는 걸 발견',
         flags='busy mine dark lavaspot', wflags=D, hold_='iron_pickaxe', ticks={1: [say1('다이아!!!!')] + heal_once('dia', 8)})
    st.beat('pen', at=(1, -2), st_='용암 호수 앞', wst='호수 쪽으로 가는 중', wflags=D, flags=D, alen=12, ticks={3: say1('호수 한가운데에 다이아가 더 있네')})
    mine(st, 'dia2', (6, -2), d2, 'deepslate_diamond_ore', 28, pops=['다이아 +1', '다이아 +1'], st_='용암 한가운데서 다이아 캐는 중', wst='용암 사이 길을 건너는 중',
         flags='busy mine dark lavaspot bridge', wflags='dark bridge', hold_='iron_pickaxe')
    st.beat('back', at=(1, -2), st_='호수에서 나옴', wst='용암 사이 길로 돌아오는 중', wflags='dark bridge', flags=D, alen=4)
    st.beat('craft', at=(-2, 4), st_='다이아 장비 조합 중', wst='조합대 놓을 자리로 가는 중', wflags=D, flags='busy dark', alen=40, facing=(-1.5, 60.5, 3.5),
            on_act=['setblock -2 60 3 minecraft:crafting_table', snd('block.wood.place')],
            every=[(10, [swing(), snd('block.wood.hit', 1.4, 0.5)])],
            on_end=[hold('diamond_pickaxe'), sset('armor', 2), 'function ek:steve/equip', popup('다이아 곡괭이 · 철 풀셋', 'aqua'), say1('다이아 곡 완성. 흑요석 캐러')] + heal_once('diapick', 4))
    mine(st, 'obs', (8, 3), obs, 'obsidian', 50, pops=['흑요석 3/10', '흑요석 6/10', '흑요석 10/10'], st_='흑요석 캐는 중 (한참 걸림)', wst='흑요석 캐러 가는 중',
         flags='busy mine dark lavaspot obs', wflags=D, hold_='diamond_pickaxe')
    st.via('v2', (0, 8), '출구로 가는 중', 'dark')
    st.beat('exit', at=(0, 11), st_='지상으로 올라가는 중', wst='출구로 가는 중', wflags=D, flags=D, alen=10, ticks={3: say1('흑요석 10개. 네더 가자')})
    return st

# ================================================================ 5: nether
PORTAL5 = 'fill -9 62 10 -8 64 10 minecraft:nether_portal[axis=x]'
PIGS = [(8, 9), (10, 8), (9, 11)]
def stage5():
    st = Stage(5, '5단계: 네더'); g = st.g; rnd = random.Random(55)
    g.fill(-14, 58, -14, 14, 60, 14, 'netherrack')
    g.fill(-12, 59, -3, 12, 60, 3, 'lava')
    for x in range(-12, 13):
        for z in (-4, 4):
            if rnd.random() < 0.3: g.set(x, 60, z, 'magma_block')
    g.fill(-13, 60, 5, -10, 60, 8, 'soul_sand')
    for (x, z) in ellipse(8, 9, 4.6, 3.6): g.set(x, 60, z, 'crimson_nylium')
    for (x, z, h) in ((4, 10, 4), (12, 11, 5)):
        g.col(x, z, 61, 60 + h, 'crimson_stem')
        g.fill(x - 1, 61 + h, z - 1, x + 1, 61 + h, z + 1, 'nether_wart_block'); g.set(x, 62 + h, z, 'nether_wart_block'); g.set(x + 1, 60 + h, z, 'shroomlight')
    sprinkle(g, rnd, 'crimson_nylium', [('crimson_roots', 0.2), ('crimson_fungus', 0.06)])
    g.fill(-10, 61, 10, -7, 65, 10, 'obsidian'); g.fill(-9, 62, 10, -8, 64, 10, 'nether_portal[axis=x]')
    g.fill(-6, 61, -12, 6, 61, -6, 'nether_bricks')
    g.fill(-6, 62, -12, 6, 62, -12, 'nether_brick_fence'); g.fill(-6, 62, -11, -6, 62, -6, 'nether_brick_fence'); g.fill(6, 62, -11, 6, 62, -6, 'nether_brick_fence')
    g.set(0, 62, -10, 'spawner')
    g.col(-11, -9, 61, 66, 'basalt'); g.set(-11, 67, -9, 'glowstone'); g.set(-10, 66, -9, 'glowstone'); g.set(-12, 66, -9, 'glowstone')
    for (x, z) in ((11, -8), (12, -10), (-13, -3), (13, 12), (-4, 12)):
        g.set(x, 61, z, 'netherrack')
    for i, (x, y, z) in enumerate(((-2.5, 64.5, -9.5), (2.5, 64, -8.5), (0.5, 65.5, -10.5))):
        st.ent('blaze', x, y, z, ['ek.blaze'])
    for i, (x, z) in enumerate(PIGS):
        st.ent('piglin', x + 0.5, 61, z + 0.5, ['ek.pig', 'ek.pig%d' % i], ',IsImmuneToZombification:1b,Rotation:[%df,0f],equipment:{mainhand:{id:"minecraft:golden_sword",count:1}}' % (60 + 90 * i))
    st.spawn = (-6, 12)
    st.init = [sset('armor', 2), sset('rods', 0), sset('rmiss', 0), sset('pearls', 0), sset('bmiss', 0)]
    st.gear = [hold('diamond_pickaxe')]
    st.evclean = ['execute as @e[tag=ek.pig] run tag @s remove ek.chase'] + ['tp @e[tag=ek.pig%d,limit=1] %s 61 %s' % (i, x + 0.5, z + 0.5) for i, (x, z) in enumerate(PIGS)]
    st.beat('arrive', st_='네더 도착', alen=25, ticks={5: say1('네더 도착. 요새 어디야')}, every=[looker()])
    st.beat('shore', at=(-2, 5), st_='용암 바다 앞', wst='요새를 찾는 중', alen=15, facing=(-1.5, 62, -8), ticks={3: say1('바다 건너에 요새다. 다리 놓는다')})
    for k in range(7):
        z = 4 - k
        st.beat('br%d' % k, at=(-2, z), st_='용암 위에 다리 놓는 중', wst='용암 위에 다리 놓는 중', flags='bridge busy', wflags='bridge', alen=8,
                facing=(-1.5, 60.5, z - 0.5), hold_='cobblestone', on_act=[pose('crouching')],
                ticks={4: [f'setblock -2 60 {z - 1} minecraft:cobblestone', snd('block.stone.place', 0.9), swing()]})
        if k > 0: st.extra.add('br%d' % k)
    st.beat('far', at=(-2, -4), st_='용암 바다를 건넘', wst='용암 위에 다리 놓는 중', wflags='bridge', alen=6, on_act=[pose('standing')])
    st.extra.add('far')
    st.beat('fort', at=(0, -7), st_='요새 도착', wst='요새로 가는 중', alen=15, ticks={3: say1('블레이즈 스포너다. 막대 6개만')})
    P.fn('s5/rod',
         'execute as @e[tag=ek.blaze,limit=1,sort=random] at @s run particle minecraft:large_smoke ~ ~0.8 ~ 0.3 0.4 0.3 0.02 20 force', snd('entity.blaze.death', 1, 0.6),
         'execute if score #rmiss ek matches 1.. run return run function ek:s5/rod_miss',
         sadd('rods', 1), [iff('rods', i, popup('막대 %d/6' % i, 'gold')) for i in range(1, 7)], snd('entity.item.pickup'),
         iff('rods', '..5', sset('at', 0)))
    P.fn('s5/rod_miss', ssub('rmiss', 1), sset('at', 0), popup('막대 없음', 'gray'),
         'execute store result score #r ek run random value 1..3',
         iff('r', 1, say(['막대 왜 안 줘', '또 빈손이네', '약탈 검이 없어서 그런가'])))
    st.beat('blaze', at=(0, -8), st_='블레이즈 잡는 중', wst='스포너 앞으로 가는 중', flags='busy fight', alen=32, hold_='diamond_sword', facing=(0.5, 65, -10.5),
            every=[(6, [swing(), snd('entity.blaze.hurt', 1, 0.5)])], ticks={30: 'function ek:s5/rod'})
    st.beat('back1', at=(-2, -4), st_='다리 앞', wst='피글린한테 가는 중', alen=2)
    st.beat('back2', at=(-2, 5), st_='다리를 건넘', wst='다리 건너는 중', wflags='bridge', alen=2)
    st.extra.add('back2')
    st.beat('pig', at=(7, 8), st_='피글린 앞', wst='피글린한테 가는 중', alen=12, hold_='gold_ingot', ticks={3: say1('금 줄게 진주 줘')})
    junk = ['자갈 12개', '가죽 3개', '영혼 과속 책', '우는 흑요석', '네더 석영 8개']
    P.fn('s5/barter',
         snd('entity.piglin.admiring_item', 1, 0.7),
         'execute if score #bmiss ek matches 1.. run return run function ek:s5/barter_junk',
         'execute store result score #r ek run random value 1..3',
         iff('r', 1, 'return run function ek:s5/barter_junk'),
         sadd('pearls', 3), [iff('pearls', i, popup_at(8.5, 64, 9.5, '진주 %d/12' % i, 'dark_aqua')) for i in (3, 6, 9, 12)], snd('entity.item.pickup'),
         iff('pearls', '..11', sset('at', 0)))
    P.fn('s5/barter_junk', iff('bmiss', '1..', ssub('bmiss', 1)), sset('at', 0),
         'execute store result score #r ek run random value 1..%d' % len(junk),
         [iff('r', i + 1, popup_at(8.5, 64, 9.5, j, 'gray')) for i, j in enumerate(junk)],
         'execute store result score #r ek run random value 1..4',
         iff('r', 1, say(['아니 진주를 달라고', '또 꽝이야', '금이 아깝다'])))
    st.beat('barter', st_='피글린이랑 교환 중', flags='busy barter', alen=26, facing=(8.5, 62, 9.5), hold_='gold_ingot',
            ticks={3: [swing(), popup_at(8.5, 63.2, 9.5, '금괴', 'yellow', '2')], 24: 'function ek:s5/barter'})
    st.beat('toportal', at=(-8, 11), st_='포탈 앞', wst='포탈로 돌아가는 중', wflags='portal', flags='portal', alen=3)
    P.fn('s5/relight', PORTAL5, snd('item.flintandsteel.use'), snd('block.portal.trigger', 1, 0.5), say1('포탈 꺼져 있었네. 다시 켜고'))
    st.beat('enter', at=(-8, 10), st_='포탈 타는 중', wst='포탈로 들어가는 중', alen=34,
            on_act=['execute unless block -8 62 10 minecraft:nether_portal run function ek:s5/relight'],
            ticks={8: say1('막대 6개 진주 12개. 완벽'), 14: snd('block.portal.travel', 1.2, 0.4)})
    st.extra.add('enter')
    return st

# ================================================================ 6: stronghold
FRAMES = ([(x, -11, 'south') for x in (-1, 0, 1)] + [(2, z, 'west') for z in (-10, -9, -8)] +
          [(x, -7, 'north') for x in (1, 0, -1)] + [(-2, z, 'east') for z in (-8, -9, -10)])
PREFILLED = {(-1, -11), (2, -9)}
def stage6():
    st = Stage(6, '6단계: 요새'); g = st.g; rnd = random.Random(66)
    g.fill(-14, 58, -14, 14, 61, 8, 'stone_bricks')
    g.fill(-14, 62, 7, 14, 62, 8, 'stone_bricks'); g.fill(-14, 63, 8, 14, 63, 8, 'stone_bricks')
    g.fill(-14, 58, 9, 14, 62, 14, 'stone'); g.fill(-14, 63, 9, 14, 63, 14, 'dirt'); g.fill(-14, 64, 9, 14, 64, 14, 'grass_block')
    for z, top in ((5, 60), (4, 59), (3, 58)):
        for x in (-1, 0, 1): carve(g, [(x, z)], top)
    rooms = {(x, z) for x in range(-9, 10) for z in (1, 2, 3)} | {(x, z) for x in range(-12, -8) for z in range(-3, 4)}
    rooms |= {(x, z) for x in range(9, 13) for z in range(0, 4)} | {(x, z) for x in (-1, 0, 1) for z in range(-3, 1)}
    rooms |= {(x, z) for x in range(-6, 7) for z in range(-13, -3)}
    carve(g, rooms, 58)
    for (x, y, z), b in list(g.b.items()):
        if b == 'stone_bricks':
            r = rnd.random()
            if r < 0.14: g.b[(x, y, z)] = 'mossy_stone_bricks'
            elif r < 0.24: g.b[(x, y, z)] = 'cracked_stone_bricks'
    for z in range(-3, 4): g.col(-13, z, 59, 60, 'bookshelf')
    g.set(-12, 59, 3, 'chest[facing=east]'); g.set(-12, 59, -3, 'cobweb'); g.set(12, 59, 1, 'chest[facing=west]')
    g.fill(-2, 59, -11, 2, 59, -7, 'stone_bricks'); g.fill(-1, 59, -10, 1, 59, -8, 'lava')
    for (x, z, f) in FRAMES:
        g.set(x, 60, z, 'end_portal_frame[facing=%s,eye=%s]' % (f, 'true' if (x, z) in PREFILLED else 'false'))
    g.fill(-1, 59, -6, 1, 59, -6, 'stone_bricks')
    g.set(4, 59, -5, 'spawner')
    for c in ((-6, 59, -13), (6, 59, -13), (-6, 59, -4), (6, 59, -4), (-9, 59, 3), (9, 59, 3), (-12, 59, 0), (12, 59, 3)): g.set(*c, 'torch')
    oak_tree(g, 10, 12, 4); oak_tree(g, -12, 13, 4)
    sprinkle(g, rnd, 'grass_block', [('short_grass', 0.2), ('poppy', 0.03)])
    st.spawn = (-8, 12)
    st.init = [sset('armor', 2), sset('eyes', 12), sset('need', 10)]
    st.gear = [hold('ender_eye')]
    def throw(label, at, first=False):
        st.beat(label, ts=1, at=None if first else at, st_='엔더의 눈 던지는 중', wst='눈이 날아간 쪽으로 가는 중', flags='eyes busy', wflags='eyes', alen=36, hold_='ender_eye',
                facing=(0.5, 70, 8.5),
                ticks={3: [swing(), snd('entity.ender_eye.launch', 1, 0.7),
                           at_s('summon item_display ~ ~1.6 ~ {Tags:["ek.tmp","ek.eyefx","ek.new"],billboard:"center",teleport_duration:2,item:{id:"minecraft:ender_eye",count:1},' + (DISPLAY_T % (1.5, 1.5, 1.5)) + '}'),
                           'scoreboard players set @e[tag=ek.new] ek.life 28', 'tag @e[tag=ek.new] remove ek.new'],
                       31: [snd('entity.item.pickup'), popup('눈 회수', 'dark_aqua', '2')]},
                raw=['execute if score #at ek matches 4..30 as @e[tag=ek.eyefx] at @s facing 0.5 68 8.5 run tp @s ^ ^ ^0.3'])
    st.beat('top', st_='요새 찾는 중', flags='eyes', alen=20, ticks={4: say1('엔더의 눈 던진다. 요새 나와라')})
    throw('eye1', (-8, 12), True); throw('eye2', (-4, 11)); throw('eye3', (-1, 10))
    st.beat('stairs', at=(0, 9), st_='입구 발견', wst='눈이 떨어진 곳으로 가는 중', alen=14, ticks={3: say1('바로 밑이다')})
    st.beat('down', at=(0, 2), st_='요새 진입', wst='요새로 내려가는 중', wflags='dark maze', flags='dark maze', alen=8, ticks={2: say1('요새 찾았다. 포탈 방 어디야')})
    st.beat('lib', at=(-10, 1), st_='도서관 뒤지는 중', wst='왼쪽 길로 가보는 중', wflags='dark maze', flags='busy dark maze', alen=40, facing=(-11.5, 59.5, 3.5),
            ticks={5: snd('block.chest.open')}, on_end=[say1('책밖에 없네. 반대쪽')])
    st.beat('dead', at=(10, 2), st_='막다른 길', wst='오른쪽 길로 가보는 중', wflags='dark maze', flags='dark maze', alen=24, ticks={4: say1('막다른 길이네')}, every=[looker()])
    st.via('v1', (0, 2), '남은 길로 가는 중', 'dark maze')
    st.beat('north', at=(0, -2), st_='북쪽 통로', wst='남은 길로 가는 중', wflags='dark maze', flags='dark maze', alen=3)
    mine(st, 'room', (3, -5), [(4, 59, -5)], 'spawner', 34, st_='좀벌레 스포너 부수는 중', wst='포탈 방 발견', flags='busy mine spawner dark', wflags='dark',
         hold_='diamond_pickaxe', ticks={1: [say1('포탈 방이다! 스포너부터 부수고')] + heal_once('room', 6)})
    todo = [(x, z, f) for (x, z, f) in FRAMES if (x, z) not in PREFILLED]
    st.beat('frames', at=(0, -6), st_='엔더의 눈 끼우는 중', wst='포탈 앞으로 가는 중', flags='busy frame', wflags='frame', alen=len(todo) * 10 + 6,
            facing=(0.5, 60.5, -8.5), hold_='ender_eye',
            on_act=['execute if score #eyes ek < #need ek run function ek:ev/eyeshort/start'],
            ticks={(k + 1) * 10: [f'setblock {x} 60 {z} minecraft:end_portal_frame[facing={f},eye=true]', snd('block.end_portal_frame.fill', 1, 0.8), swing()]
                   for k, (x, z, f) in enumerate(todo)})
    st.beat('open', st_='엔드 포탈이 열림', alen=40,
            ticks={2: ['fill -1 60 -10 1 60 -8 minecraft:end_portal', snd('block.end_portal.spawn', 1, 0.8)],
                   12: [say1('열렸다. 드래곤 딱 대')] + heal_once('open', 6)})
    st.beat('jump', ts=1, at=(0, -7), st_='포탈로 뛰어드는 중', wst='포탈로 가는 중', alen=16,
            ticks={4: [say1('간다')], 8: [snd('block.portal.travel', 1.2, 0.4)],
                   12: [at_s('particle minecraft:portal ~ ~1 ~ 0.3 0.6 0.3 0.5 60 force')]})
    st.extra.add('jump')
    return st

# ================================================================ 7: the End
CRYSTALS = {1: (-6, 69, -4), 2: (7, 71, -5), 3: (-5, 73, 4), 4: (6, 70, 3)}
ENDERS = [(-3, -9), (9, 0), (2, 5)]
def stage7():
    st = Stage(7, '7단계: 엔드'); g = st.g; g.base_y = 65
    g.fill(-14, 58, -14, 14, 58, 14, 'black_concrete')
    for y, r in ((64, 10.2), (63, 8.6), (62, 6.4), (61, 3.6)):
        for (x, z) in ellipse(0, -2, r, r): g.set(x, y, z, 'end_stone')
    g.fill(-1, 64, 12, 1, 64, 14, 'obsidian')
    for (bx, bz, h) in ((-7, -5, 4), (6, -6, 6), (-6, 3, 8), (5, 2, 5)):
        g.fill(bx, 65, bz, bx + 1, 64 + h, bz + 1, 'obsidian')
    for x in range(-7, -3):
        for z in range(2, 6):
            if x in (-7, -4) or z in (2, 5): g.col(x, z, 73, 74, 'iron_bars')
    g.fill(-6, 75, 3, -5, 75, 4, 'iron_bars')
    g.fill(-1, 65, -3, 1, 65, -1, 'bedrock'); g.col(0, -2, 65, 68, 'bedrock')
    for k, (x, y, z) in CRYSTALS.items():
        st.ents.append('summon minecraft:end_crystal %s %s %s {Tags:["ek.stg","ek.cr","ek.cr%d"],ShowBottom:0b,Invulnerable:1b}' % (x, y, z, k))
    for i, (x, z) in enumerate(ENDERS):
        st.ent('enderman', x + 0.5, 65, z + 0.5, ['ek.end', 'ek.end%d' % i], ',Rotation:[%df,0f]' % (120 * i))
    # The dragon the game logic moves is a marker (ek.dragon). The visible ender dragon (ek.dvis) is copied onto it every tick.
    # It is deliberately not NoAI: a NoAI dragon keeps one heading, frozen wings, and does not follow teleports on the client.
    # Its hover AI is re-anchored to its own position every tick (phase 6 -> 10), so the AI never pulls or turns it.
    # Heights keep its wing boxes (dragon y-2 .. y+4) above Steve at all times: circle 82, perch 71, dive 9 above Steve.
    st.ents.append('summon minecraft:marker 0.5 82 -1.5 {Tags:["ek.stg","ek.dpivot"]}')
    st.ents.append('summon minecraft:marker 0.5 82 9.5 {Tags:["ek.stg","ek.dragon"],Rotation:[-90f,0f]}')
    st.ents.append('summon minecraft:marker 0.5 82 9.5 {Tags:["ek.stg","ek.dtgt"]}')
    st.ents.append('summon minecraft:ender_dragon 0.5 82 9.5 {Tags:["ek.stg","ek.dvis"],Silent:1b,Invulnerable:1b,PersistenceRequired:1b,DragonPhase:10,Rotation:[-90f,0f]}')
    st.spawn = (0, 13)
    st.init = [sset('armor', 3), sset('dhp', 100), sset('dmode', 0), sset('crleft', 4)]
    st.gear = [hold('bow')]
    st.tick = [
        'execute if score #dmode ek matches 0 as @e[tag=ek.dpivot,limit=1] at @s run tp @s ~ ~ ~ ~2 ~',
        # -90 would be the exact tangent (a dragon's head points opposite its yaw); the renderer uses the yaw from 7 ticks ago, so lead by 14 degrees
        'execute if score #dmode ek matches 0 at @e[tag=ek.dpivot,limit=1] run tp @e[tag=ek.dragon,limit=1] ^ ^ ^11 ~-76 0',
        'execute if score #dmode ek matches 1 as @e[tag=ek.dragon,limit=1] at @s facing 0.5 71 -1.5 run tp @s ^ ^ ^0.35 ~180 0',
        'execute if score #dmode ek matches 1 positioned 0.5 71 -1.5 if entity @e[tag=ek.dragon,distance=..1.2] run function ek:s7/perched',
        'execute unless score #dmode ek matches 4 at @e[tag=ek.dragon,limit=1] run tp @e[tag=ek.dvis,limit=1] ~ ~ ~ ~ ~',
        'execute unless score #dmode ek matches 4 run data merge entity @e[tag=ek.dvis,limit=1] {DragonPhase:6}',
        'execute unless score #dmode ek matches 4 run data merge entity @e[tag=ek.dvis,limit=1] {DragonPhase:10}']
    P.fn('s7/perched', sset('dmode', 2), 'tp @e[tag=ek.dragon,limit=1] 0.5 71 -1.5 180 0')
    st.evclean = [iff('dmode', 3, sset('dmode', 0)),
                  'execute as @e[tag=ek.end] run tag @s remove ek.angry'] + \
                 ['tp @e[tag=ek.end%d,limit=1] %s 65 %s' % (i, x + 0.5, z + 0.5) for i, (x, z) in enumerate(ENDERS)]
    st.beat('arrive', st_='엔드 도착', alen=25, ticks={5: say1('엔드 도착. 수정부터 깬다')}, every=[looker()])
    for k in range(3):
        z = 12 - k
        st.beat('vb%d' % k, at=(0, z), st_='공허 위에 다리 놓는 중', wst='공허 위에 다리 놓는 중', flags='bridge busy', wflags='bridge', alen=8,
                facing=(0.5, 64.5, z - 0.5), hold_='cobblestone', on_act=[pose('crouching')],
                ticks={4: [f'setblock 0 64 {z - 1} minecraft:cobblestone', snd('block.stone.place', 0.9), swing()]})
        st.extra.add('vb%d' % k)
    st.beat('island', at=(0, 8), st_='섬에 도착', wst='공허 위에 다리 놓는 중', wflags='bridge', alen=6, on_act=[pose('standing')])
    st.extra.add('island')
    def shoot(label, k, at, pop, say_=None):
        cx, cy, cz = CRYSTALS[k]
        st.beat(label, at=at, st_='수정 쏘는 중', wst='수정이 보이는 곳으로 가는 중', flags='aim busy', alen=40, hold_='bow', facing=(cx, cy + 1, cz),
                ticks={24: [swing(), snd('entity.arrow.shoot', 1, 0.8)],
                       32: [f'execute at @e[tag=ek.cr{k}] run function ek:fx/boom', f'kill @e[tag=ek.cr{k}]', ssub('crleft', 1), popup_at(cx, cy + 2, cz, pop, 'light_purple')] + ([say1(say_)] if say_ else [])})
    shoot('cr1', 1, (0, 4), '수정 1/4'); shoot('cr2', 2, None, '수정 2/4')
    st.beat('p3', ts=1, at=(-3, 4), st_='기둥 타고 올라가는 중', wst='철창 수정 기둥으로 가는 중', flags='busy', alen=70, hold_='cobblestone',
            on_act=[say1('철창 있는 건 올라가서 깬다')],
            # only pillar while below the top (y 73): this beat is replayed after interruptions and must not build the pillar higher each time
            every=[(8, ['execute store result score #sy ek run data get entity @e[tag=ek.steve,limit=1] Pos[1] 10',
                        'execute if score #sy ek matches ..729 as @e[tag=ek.steve,limit=1] at @s run setblock ~ ~ ~ minecraft:cobblestone',
                        'execute if score #sy ek matches ..729 run ' + snd('block.stone.place', 0.9, 0.7)], (1, 64))],
            ticks={32: sset('f_high', 1)})
    st.beat('cage', back='p3', st_='철창 부수는 중', flags='high busy', alen=46, hold_='diamond_pickaxe', facing=(-5, 73.5, 4),
            every=[(6, [swing(), snd('block.stone.hit', 1.2, 0.6)])],
            ticks={20: ['fill -7 73 2 -4 75 5 minecraft:air replace minecraft:iron_bars', snd('block.glass.break', 0.8)],
                   40: ['execute at @e[tag=ek.cr3] run function ek:fx/boom', 'kill @e[tag=ek.cr3]', ssub('crleft', 1), popup_at(-5, 75, 4, '수정 3/4', 'light_purple')]})
    st.beat('mlg', ts=1, st_='물양동이 낙법', alen=30, hold_='water_bucket',
            ticks={2: say1('엠엘지 간다'), 8: 'fill -3 65 4 -3 80 4 minecraft:air replace minecraft:cobblestone',
                   18: [snd('item.bucket.empty'), at_s('particle minecraft:splash ~ ~0.2 ~ 0.4 0.1 0.4 0.1 40 force'), popup('MLG!', 'aqua')]})
    shoot('cr4', 4, (2, 6), '수정 4/4', '수정 끝. 내려와라 드래곤')
    st.beat('perch', at=(2, 1), st_='드래곤이 내려오길 기다리는 중', wst='분수대 앞으로 가는 중', flags='perch', alen=90, hold_='red_bed', facing=(0.5, 70, -1.5),
            on_act=[unl('dmode', 2, sset('dmode', 1))])
    P.fn('s7/bedboom',
         'setblock 2 65 0 minecraft:air', 'setblock 1 65 0 minecraft:air', 'execute positioned 1.5 66 0.5 run function ek:fx/boom',
         snd('entity.ender_dragon.hurt', 1, 0.8), ssub('dhp', 25), iff('dhp', '..-1', sset('dhp', 0)),
         'execute store result storage ek:s tmp.n int 1 run scoreboard players get #dhp ek', 'function ek:s7/hp_popup with storage ek:s tmp')
    P.fn('s7/hp_popup', '$execute positioned 0.5 73 -1.5 run function ek:fx/popup {t:"드래곤 체력 $(n)%",c:"light_purple",s:"3"}')
    st.beat('beds', st_='침대 폭발로 딜 넣는 중', flags='bed busy', alen=40, hold_='red_bed', facing=(0.5, 70, -1.5),
            on_act=[unl('dmode', 2, sset('dmode', 1))],
            ticks={10: ['setblock 2 65 0 minecraft:red_bed[part=foot,facing=west]', 'setblock 1 65 0 minecraft:red_bed[part=head,facing=west]', snd('block.wood.place'), swing()],
                   24: 'function ek:s7/bedboom', 38: iff('dhp', '1..', sset('at', 0))})
    st.beat('kill', ts=1, st_='드래곤 처치!', alen=205,
            on_act=[sset('dmode', 4), 'data merge entity @e[tag=ek.dvis,limit=1] {Health:0f}', snd('entity.ender_dragon.death', 1, 0.8), say1('잡았다!!!')],
            every=[(10, ['execute at @e[tag=ek.dragon,limit=1] run particle minecraft:explosion_emitter ~ ~2 ~ 2 2 2 0 2 force'], (1, 60))],
            on_end=['execute as @e[tag=ek.dragon] run function ek:fx/vanish', 'function ek:game/lose'])
    return st

def all_stages():
    return [stage1(), stage2(), stage3(), stage4(), stage5(), stage6(), stage7()]
