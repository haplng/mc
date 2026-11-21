"""Drive the item shop on the running test server with a fake player and report what happened."""
import sys, time, re, json
sys.path.insert(0, '/home/claude/bw/tools'); sys.path.insert(0, '/home/claude/mc/tools')
import rcon, bwbot
r = rcon.Rcon()
PACK = '/home/claude/bw/out3/bedwars_maps/data/bw/function'
def npcs(mid):
    out = []
    for l in open(f'{PACK}/step/{mid}/try.mcfunction', encoding='utf-8'):
        m = re.match(r'summon minecraft:villager (\S+) (\S+) (\S+) .*Rotation:\[(\S+?)f,.*Tags:\[(.*?)\]', l)
        if m: out.append((float(m[1]), float(m[2]), float(m[3]), float(m[4]), [g.strip('"') for g in m[5].split(',')]))
    return out
def inv(name='tester'):
    """item id -> count, read from the player's inventory data (top-level stacks only)"""
    t = r.cmd(f'data get entity {name} Inventory')
    t = t[t.find('['):]; items = {}; depth = 0; start = None
    for k, ch in enumerate(t):
        if ch == '{':
            if depth == 0: start = k
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                s = t[start:k + 1]; i = re.search(r'id: "minecraft:([a-z_]+)"', s); c = re.search(r'count: (\d+)', s)
                if i: items[i.group(1)] = items.get(i.group(1), 0) + int(c.group(1) if c else 1)
    return items
def wait(cond, t=3.0):
    t0 = time.time()
    while time.time() - t0 < t:
        if cond(): return True
        time.sleep(0.05)
    return False
def strings(o, out=None):
    out = [] if out is None else out
    if isinstance(o, str): out.append(o)
    elif isinstance(o, dict):
        for v in o.values(): strings(v, out)
    elif isinstance(o, list):
        for v in o: strings(v, out)
    return out
fails = []
def check(ok, what):
    print(('  ok   ' if ok else '  FAIL ') + what)
    if not ok: fails.append(what)

b = bwbot.BwBot(); assert b.wait_joined(), b.kicked
time.sleep(1.0)
print('joined at', b.pos)
r.cmd('gamemode survival tester'); r.cmd('op tester')     # ops are exempt from the command spam kick, like the owner of a single-player world
tea = npcs('tea')
red = [n for n in tea if 'bw.t.red' in n[4]]
print('red tea npcs', [(n[0], n[1], n[2], n[3], n[4][2]) for n in red])
shop = next(n for n in red if 'bw.npc.shop' in n[4]); upg = next(n for n in red if 'bw.npc.upgrade' in n[4])
# stand in front of the red shopkeeper (two blocks towards the middle of the cup)
import math
def front(n, d=2.0):
    yaw = math.radians(n[3]); return n[0] - math.sin(yaw) * d, n[1], n[2] + math.cos(yaw) * d
fx, fy, fz = front(shop)
print('tp', r.cmd(f'tp tester {fx} {fy} {fz}'))
time.sleep(1.5)
print('bot pos', b.pos, 'entities', len(b.entities))
print('  block under npc / window:', r.cmd(f'execute positioned {shop[0]} {shop[1]} {shop[2]} run data get entity @e[type=villager,distance=..0.6,limit=1] Tags')[:160])
eid = b.find('villager', shop[0], shop[1], shop[2], 0.8)
check(eid is not None, f'shopkeeper entity visible to the client at {shop[:3]}')
print(r.cmd('data get entity @e[type=villager,tag=bw.npc.shop,tag=bw.t.red,limit=1] Rotation'))
# ---- 1. right-click opens the quick-buy page
n0 = len(b.dialogs); b.interact(eid)
check(wait(lambda: len(b.dialogs) > n0), 'right-click on the shopkeeper opens a dialog')
d = b.dialogs[-1]
print('   title:', bwbot.flat(d.get('title')), '| type', d.get('type'), '| columns', d.get('columns'), '| actions', len(d.get('actions', [])), '| pause', d.get('pause'), '| after', d.get('after_action'))
check(len(d.get('actions', [])) == 28, 'quick buy page has 8 tabs + 20 items')
check(not any('$(' in s for s in strings(d)), 'no unresolved macro variable in the dialog')
print('   body:', repr(bwbot.flat(d['body']['contents'] if isinstance(d['body'], dict) else d['body'][0]['contents'])))
for a in d['actions'][:10]: print('   btn:', bwbot.flat(a['label']), '|', a['action'].get('command'), '| tip:', repr(bwbot.flat(a.get('tooltip')))[:110])
check(r.score('tester', 'bw.page') == 1 and r.score('tester', 'bw.team') == 0, f"page/team scores {r.score('tester', 'bw.page')}/{r.score('tester', 'bw.team')}")
# ---- 2. buying without resources
r.cmd('clear tester')
n0 = len(b.dialogs); c0 = len(b.chat); b.command('trigger bw.buy set 1')
check(wait(lambda: len(b.dialogs) > n0), 'a failed purchase refreshes the dialog')
print('   chat:', b.chat[c0:], '| body:', repr(bwbot.flat(b.dialogs[-1]['body']['contents'])))
check('red_wool' not in inv(), 'nothing given without iron')
# ---- 3. buying every item with plenty of resources
r.cmd('give tester minecraft:iron_ingot 600'); r.cmd('give tester minecraft:gold_ingot 300'); r.cmd('give tester minecraft:emerald 100')
time.sleep(0.3)
sys.path.insert(0, '/home/claude/bw/gen3'); import shop as S
for it in S.ITEMS:
    if it['id'] % 6 == 0:                                        # keep the inventory from filling up (armour stays on)
        r.cmd('clear tester'); r.cmd('give tester minecraft:iron_ingot 300'); r.cmd('give tester minecraft:gold_ingot 150'); r.cmd('give tester minecraft:emerald 60'); time.sleep(0.3)
    before = inv(); n0 = len(b.dialogs); c0 = len(b.chat); s0 = len(b.sounds)
    b.command(f"trigger bw.buy set {it['id']}")
    ok = wait(lambda: len(b.dialogs) > n0, 2.5); time.sleep(0.15)
    after = inv(); cur = S.CUR[it['cur']]['item'].split(':')[1]
    kind = it['give'][0]
    if kind == 'tool': cost = S.TIERS[it['give'][1]][0][5]; cur = S.CUR[S.TIERS[it['give'][1]][0][6]]['item'].split(':')[1]
    else: cost = it['cost']
    paid = before.get(cur, 0) - after.get(cur, 0)
    gained = {k: v - before.get(k, 0) for k, v in after.items() if v - before.get(k, 0) > 0}
    msg = b.chat[c0:]
    good = ok and paid == cost and (gained or kind == 'armor') and any('구매 완료' in m for m in msg)
    print(('  ok   ' if good else '  FAIL ') + f"{it['id']:2d} {it['name']:14s} paid {paid} {cur} (want {cost}) got {gained} | {msg} | sounds {b.sounds[s0:]}")
    if not good: fails.append(f"buy {it['id']}")
print('   armor:', r.cmd('data get entity tester equipment')[:300])
# ---- 4. tool tiers, things owned once, armour that is no better
r.cmd('clear tester'); r.cmd('give tester minecraft:iron_ingot 300'); r.cmd('give tester minecraft:gold_ingot 150'); r.cmd('give tester minecraft:emerald 60')
r.cmd('give tester minecraft:wooden_pickaxe'); r.cmd('give tester minecraft:shears'); time.sleep(0.3)
for want_gain in ('iron_pickaxe', 'golden_pickaxe', 'diamond_pickaxe', None):
    before = inv(); c0 = len(b.chat); n0 = len(b.dialogs); b.command('trigger bw.buy set 16'); wait(lambda: len(b.dialogs) > n0); time.sleep(0.15); after = inv()
    picks = {k: v for k, v in after.items() if 'pickaxe' in k}
    check((want_gain in picks and len(picks) == 1) if want_gain else picks == {'diamond_pickaxe': 1}, f'pickaxe step -> {picks} {b.chat[c0:]}')
n0 = len(b.dialogs); b.command('trigger bw.buy set 14'); wait(lambda: len(b.dialogs) > n0); time.sleep(0.15)      # put the diamond armour back on
check('diamond_leggings' in r.cmd('data get entity tester equipment'), 'diamond armour is worn again')
for iid, why in ((15, 'shears twice'), (12, 'chain armour while wearing diamond'), (14, 'diamond armour twice')):
    before = inv(); c0 = len(b.chat); n0 = len(b.dialogs); b.command(f'trigger bw.buy set {iid}'); wait(lambda: len(b.dialogs) > n0); time.sleep(0.15)
    check(inv() == before and any('이미' in m for m in b.chat[c0:]), f'{why} is refused: {b.chat[c0:]}')
# ---- 5. every page
for p in range(1, 9):
    n0 = len(b.dialogs); b.command(f'trigger bw.shop set {p}')
    ok = wait(lambda: len(b.dialogs) > n0); d = b.dialogs[-1] if ok else {}
    want = 8 + len(S.PAGES[p - 1][3])
    check(ok and len(d.get('actions', [])) == want and not any('$(' in s for s in strings(d)) and r.score('tester', 'bw.page') == p,
          f"page {p} {bwbot.flat(d.get('title'))!r}: {len(d.get('actions', []))} buttons (want {want})")
    if p in (4, 5):
        for a in d['actions'][8:]: print('      ', bwbot.flat(a['label']), '| tip:', repr(bwbot.flat(a.get('tooltip'))))
json.dump(b.dialogs[-8:], open('/tmp/dialogs.json', 'w'), ensure_ascii=False)
# ---- 6. close, too far away
c0 = b.cleared; b.command('trigger bw.shop set 99'); check(wait(lambda: b.cleared > c0), 'the close button clears the dialog')
r.cmd(f'tp tester {fx + 30} {fy + 20} {fz}'); time.sleep(0.6)
before = inv(); c0 = len(b.chat); cl = b.cleared; b.command('trigger bw.buy set 1'); time.sleep(0.6)
check(inv() == before and any('가까이' in m for m in b.chat[c0:]) and b.cleared > cl, f'buying far from a shopkeeper is refused: {b.chat[c0:]}')
# ---- 7. the other two kinds of keeper
r.cmd(f'tp tester {front(upg)[0]} {fy} {front(upg)[2]}'); time.sleep(1.0)
e2 = b.find('villager', upg[0], upg[1], upg[2], 0.8); n0 = len(b.dialogs); b.interact(e2)
check(wait(lambda: len(b.dialogs) > n0) and b.dialogs[-1].get('type') == 'minecraft:notice', f"team upgrade keeper shows a notice: {bwbot.flat(b.dialogs[-1].get('title'))!r} / {bwbot.flat(b.dialogs[-1]['body']['contents'])!r}")
lob = npcs('lobby')[0]
r.cmd(f'tp tester {lob[0] + 2} {lob[1]} {lob[2]}'); time.sleep(1.5)
e3 = b.find('villager', lob[0], lob[1], lob[2], 0.8); n0 = len(b.dialogs)
check(e3 is not None, 'lobby upgrade keeper is there')
if e3: b.interact(e3)
check(wait(lambda: len(b.dialogs) > n0) and b.dialogs[-1].get('type') == 'minecraft:notice', f"lobby keeper shows a notice: {bwbot.flat(b.dialogs[-1].get('title'))!r} / {bwbot.flat(b.dialogs[-1]['body']['contents'])!r}")
# ---- 8. team colour: the blue base sells blue wool
blue = next(n for n in tea if 'bw.t.blue' in n[4] and 'bw.npc.shop' in n[4])
bx, by, bz = front(blue); r.cmd(f'tp tester {bx} {by} {bz}')
check(wait(lambda: b.find('villager', blue[0], blue[1], blue[2], 0.8) is not None, 8), 'blue shopkeeper reaches the client after the long teleport')
time.sleep(0.3)
e4 = b.find('villager', blue[0], blue[1], blue[2], 0.8); n0 = len(b.dialogs); b.interact(e4)
check(wait(lambda: len(b.dialogs) > n0), f"clicking the blue shopkeeper opens the shop (entity {e4}, team score {r.score('tester', 'bw.team')}, bot at {b.pos})")
before = inv(); n0 = len(b.dialogs); b.command('trigger bw.buy set 1'); wait(lambda: len(b.dialogs) > n0); time.sleep(0.2); after = inv()
check(after.get('blue_wool', 0) - before.get('blue_wool', 0) == 16, f"blue base gives blue wool: {({k: v for k, v in after.items() if 'wool' in k})}")
print('bot errors', b.raw.get('errors'), 'kicked', b.kicked)
print('FAILS', fails)
b.close()
