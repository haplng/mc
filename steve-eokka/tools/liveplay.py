"""A scripted 'decent player' on the real server, to see how far a run goes with the current balance.

It looks at the same hints a player sees (the star), throws at Steve with some aiming error, and opens most lucky boxes.
Usage: python3 tools/liveplay.py [n|e|h] [runs] [aim error in blocks]
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live import Live
import livecards as LC

def play(L, P, diff, err, seed, patient=True):
    rnd = random.Random(seed)
    L.cmd('function ek:lobby/enter'); L.step(5); L.cmd('function ek:game/start_' + diff)
    L.cmd('execute unless entity @e[tag=ek.cur] run summon minecraft:marker 0.5 60 0.5 {Tags:["ek.cur"]}')
    t = 0; boxseen = False
    while t < 60000:
        L.step(10); t += 10
        s = L.scores('state', 'stage', 'intr', 'steve', 'drop', 'energy', 'box', 'wild', 'lucky', 'phase')
        if s['state'] != 1: break
        if s['box'] == 1 and not boxseen:
            boxseen = True
            if rnd.random() < 0.7: L.cmd('tag @e[tag=ek.box] add ek.pick'); L.cmd('function ek:box/open'); boxseen = False
        if s['box'] != 1: boxseen = False
        if s['intr'] != 0 or s['steve'] != 1 or s['drop'] == 1: continue
        cards = P[s['stage']]; best = None
        for slot, cid, fn in cards:
            L.cmd(f'scoreboard players set #sl ek {slot}'); L.cmd('scoreboard players set #hint ek 0'); L.cmd(f"function ek:ui/hint_s{s['stage']}")
            hint = L.score('#hint') == 1 or s['wild'] == 1 or s['lucky'] == 1
            if fn == 'aim' and cid == 'anvil' and s['phase'] == 0: hint = hint or rnd.random() < 0.5      # anvil: go for the walking kill
            if hint and (best is None or rnd.random() < 0.5): best = (slot, cid, fn)
        if best is None:
            if not patient or s['energy'] >= 95: best = rnd.choice(cards)
            else: continue
        slot, cid, fn = best
        if fn == 'aim':
            # lead a walking Steve by roughly where he will be, plus aiming error
            lead = 2.2 if s['phase'] == 0 else 0.0
            L.cmd(f'execute as @e[tag=ek.steve,limit=1] at @s facing entity @e[tag=ek.tgt,limit=1] feet rotated ~ 0 positioned ^ ^ ^{lead} run tp @e[tag=ek.cur,limit=1] ~{rnd.gauss(0, err):.2f} ~ ~{rnd.gauss(0, err):.2f}')
            L.cmd('scoreboard players set #cur ek 1')
        L.cmd(f'function ek:c/{cid}/{fn}')
    r = L.scores('state', 'res', 'stage', 'day', 'mental', 'mmax', 'total', 'ncards', 'nthrow', 'nhit', 'deaths', 'maxcombo')
    r['ticks'] = t
    return r

if __name__ == '__main__':
    diff = sys.argv[1] if len(sys.argv) > 1 else 'n'
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    err = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    L = Live(); L.log(); P = LC.pools()
    for k in range(runs):
        r = play(L, P, diff, err, 100 + k)
        print(('WIN ' if r['res'] == 1 else 'LOSS'), f"stage {r['stage']} day {r['day']} mental {r['mental']}/{r['mmax']} dmg {r['total']} cards {r['ncards']} throws {r['nhit']}/{r['nthrow']} deaths {r['deaths']} combo {r['maxcombo']} ticks {r['ticks']}", flush=True)
    bad = [l for l in L.problems() if not any(b in l for b in LC.BENIGN)]
    print(len(bad), 'complaints'); [print('  ', l[:300]) for l in bad[:10]]
