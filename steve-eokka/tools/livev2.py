"""Server-side checks (no player needed) for distractions, noticing, stage twists and the result panel numbers."""
import collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live import Live

def start(L, stage=1):
    L.cmd('function ekt:goto {prev:%d}' % (stage - 1)); L.cmd('scoreboard players set #arm ekt 0')
    L.cmd('execute unless entity @e[tag=ek.cur] run summon minecraft:marker 0.5 60 0.5 {Tags:["ek.cur"]}')

def wait(L, cond, limit=3000, chunk=1):
    for _ in range(limit // chunk):
        if cond(): return True
        L.step(chunk)
    return False

def main():
    L = Live(); L.log(); fails = []
    def ok(name, cond, info=''):
        print(('  ok   ' if cond else '  FAIL ') + name + ('   ' + str(info) if info != '' else ''))
        if not cond: fails.append(name)

    print('== distraction')
    start(L); L.cmd('scoreboard players set #idlecd ek 0')
    got = wait(L, lambda: (L.score('#idle') or 0) > 0, 4000, 2)
    s = L.scores('idle', 'wild', 'idlek', 'phase', 'beat'); ok('Steve got distracted', got and s['wild'] == 1, s)
    print('   status:', L.cmd('data get storage ek:s status')[:80])
    p0 = L.pos_of('@e[tag=ek.steve,limit=1]'); L.step(20); p1 = L.pos_of('@e[tag=ek.steve,limit=1]')
    ok('he stands still meanwhile', abs(p0[0] - p1[0]) + abs(p0[2] - p1[2]) < 0.01, (p0, p1))
    L.cmd('scoreboard players set #energy ek 100'); L.cmd('function ek:c/pick/try')
    s = L.scores('sweet', 'intr'); ok('any card is a sweet spot while he is distracted', s['sweet'] == 1 and s['intr'] >= 1, s)
    wait(L, lambda: L.score('#intr') == 0, 400, 5)
    s = L.scores('idle', 'wild', 'idlecd'); ok('distraction over after the event', s['idle'] == 0 and s['wild'] == 0 and s['idlecd'] >= 90, s)
    # a distraction that simply runs out
    start(L); L.cmd('scoreboard players set #idlecd ek 0')
    wait(L, lambda: (L.score('#idle') or 0) > 0, 4000, 2); b0 = L.score('#beat')
    wait(L, lambda: L.score('#idle') == 0, 200, 2)
    s = L.scores('idle', 'wild', 'beat', 'phase'); ok('distraction ends by itself and the walk goes on', s['wild'] == 0 and s['beat'] == b0, s)
    print('   status after:', L.cmd('data get storage ek:s status')[:80])

    print('== noticing a falling anvil (walking Steve, thrown 2.4 blocks ahead)')
    res = collections.Counter(); tiers = collections.Counter()
    for trial in range(30):
        start(L, 1 if trial % 2 else 4); L.cmd('scoreboard players set #idlecd ek 99999')
        if not wait(L, lambda: L.score('#phase') == 0 and (L.score('#wt') or 0) >= 4 and L.score('#intr') == 0, 600): continue
        L.cmd('execute as @e[tag=ek.steve,limit=1] at @s facing entity @e[tag=ek.tgt,limit=1] feet rotated ~ 0 run tp @e[tag=ek.cur,limit=1] ^ ^ ^2.4')
        L.cmd('scoreboard players set #cur ek 1'); L.cmd('scoreboard players set #energy ek 100'); L.cmd('function ek:c/anvil/aim')
        L.step(9); s = L.scores('halt', 'dash', 'dropt', 'phase')
        kind = 'halt' if s['halt'] else ('dash' if s['dash'] else 'none'); res[kind] += 1
        L.step(8); tiers[(kind, L.score('#tier'), L.score('#sweet'))] += 1
    print('   reactions:', dict(res)); print('   (reaction, tier, crit):', dict(tiers))
    ok('he sometimes notices (and stops)', res['halt'] > 0 and res['none'] > 0, dict(res))
    ok('an unnoticed led anvil is a direct crit', any(k[0] == 'none' and k[1] == 3 and k[2] == 1 for k in tiers), '')
    ok('a noticed anvil is never a crit', not any(k[0] != 'none' and k[1] >= 2 and k[2] == 1 for k in tiers), '')

    print('== thrown on top of a walking Steve (he should bolt, not stop)')
    res = collections.Counter()
    for trial in range(16):
        start(L, 1); L.cmd('scoreboard players set #idlecd ek 99999'); L.cmd('scoreboard players set #diff ek 2')
        if not wait(L, lambda: L.score('#phase') == 0 and (L.score('#wt') or 0) >= 4 and L.score('#intr') == 0, 600): continue
        L.cmd('execute at @e[tag=ek.steve,limit=1] run tp @e[tag=ek.cur,limit=1] ~ ~ ~')
        L.cmd('scoreboard players set #cur ek 1'); L.cmd('scoreboard players set #energy ek 100'); L.cmd('function ek:c/anvil/aim')
        L.step(9); s = L.scores('halt', 'dash')
        res['halt' if s['halt'] else ('dash' if s['dash'] else 'none')] += 1
    print('   reactions:', dict(res)); ok('no pointless stops', res['halt'] == 0, dict(res))

    print('== twists')
    start(L); L.cmd('scoreboard players set #mod ek 0'); L.cmd('scoreboard players set #energy ek 0'); L.cmd('scoreboard players set #et ek 0'); L.step(240); e0 = L.score('#energy')
    start(L); L.cmd('scoreboard players set #mod ek 1'); L.cmd('scoreboard players set #energy ek 0'); L.cmd('scoreboard players set #et ek 0'); L.step(240); e1 = L.score('#energy')
    ok('energy twist is about 1.5x', 1.35 < e1 / max(1, e0) < 1.65, (e0, e1))
    out = {}
    for mod in (0, 3):
        start(L); L.cmd(f'scoreboard players set #mod ek {mod}'); L.cmd('scoreboard players set #combo_t ek 0'); m0 = L.score('#mental')
        L.cmd('scoreboard players set #dmg ek 10'); L.cmd('function ek:game/dmg'); out[mod] = m0 - L.score('#mental')
    ok('damage twist is +20%', out[0] == 10 and out[3] == 12, out)
    start(L, 3); print('   rolled twist for stage 3:', L.score('#mod'))

    print('== sniping bonus')
    start(L); L.cmd('scoreboard players set #mod ek 0'); L.cmd('scoreboard players set #combo_t ek 0'); L.cmd('scoreboard players set #aimx ek 130'); m0 = L.score('#mental')
    L.cmd('scoreboard players set #dmg ek 10'); L.cmd('function ek:game/dmg'); d1 = m0 - L.score('#mental')
    L.cmd('scoreboard players set #combo_t ek 0'); L.cmd('scoreboard players set #dmg ek 10'); m0 = L.score('#mental'); L.cmd('function ek:game/dmg'); d2 = m0 - L.score('#mental')
    ok('+30% once, then back to normal', d1 == 13 and d2 == 10, (d1, d2))

    bad = [l for l in L.problems() if not any(b in l for b in ('DYING', 'authlib', 'java.base/', 'minecraftservices', 'Services Discovery', 'EntityStorage] Serialization errors', 'chunk@['))]
    print('server complaints:', len(bad))
    for l in bad[:20]: print('   ', l[:300])
    print('FAILED:' if fails else 'ALL OK', fails)

if __name__ == '__main__':
    main()
