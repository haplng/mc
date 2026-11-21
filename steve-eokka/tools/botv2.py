"""Fake-player checks for the version 2 systems on the real server: mount, zoom, the look-at cursor, throws and lucky boxes."""
import math, os, re, struct, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live import Live
from bot import Bot

EYE = 1.62 * 16
def aim_at(eye, tgt):
    dx, dy, dz = tgt[0] - eye[0], tgt[1] - eye[1], tgt[2] - eye[2]
    return math.degrees(math.atan2(-dx, dz)), -math.degrees(math.atan2(dy, math.hypot(dx, dz)))

class T:
    def __init__(self):
        self.L = Live(); self.L.log(); self.fail = []
        self.L.cmd('function ek:lobby/enter'); self.L.step(3)
        self.b = Bot('tester'); assert self.b.wait_joined(), self.b.kicked
        time.sleep(0.5); self.L.step(10); time.sleep(0.3)
        self.L.cmd('tp tester 0.5 57 26.5 180 25'); time.sleep(0.3); self.L.step(5); time.sleep(0.3)
    def ok(self, name, cond, info=''):
        print(('  ok   ' if cond else '  FAIL ') + name + ('   ' + str(info) if info != '' else ''))
        if not cond: self.fail.append(name)
    def step(self, n=2):
        time.sleep(0.12); self.L.step(n); time.sleep(0.05)
    def ppos(self): return self.L.pos_of('@a[name=tester,limit=1]')
    def psc(self, obj):
        t = self.L.cmd(f'scoreboard players get tester {obj}'); m = re.search(r'has (-?\d+)', t); return int(m.group(1)) if m else None
    def eye(self, crouch=False):
        p = self.ppos(); return (p[0], p[1] + (1.27 * 16 if crouch else EYE), p[2])
    def look_at(self, tgt, crouch=False):
        y, p = aim_at(self.eye(crouch), tgt); self.b.look(y, p); self.step(2)

def main():
    t = T(); L = t.L; b = t.b
    print('== join / mount')
    t.ok('tag ek.in + ek.v2', L.count('@a[name=tester,tag=ek.in,tag=ek.v2]') == 1)
    t.ok('in team ek', L.count('@a[name=tester,team=ek]') == 1)
    t.ok('one mount', L.count('@e[tag=ek.mount]') == 1, L.count('@e[tag=ek.mount]'))
    t.ok('mount in team', L.count('@e[tag=ek.mount,team=ek]') == 1)
    t.ok('riding (ek.rd)', t.psc('ek.rd') == 1, t.psc('ek.rd'))
    p = t.ppos(); m = L.pos_of('@e[tag=ek.mount,limit=1]')
    t.ok('rider height', abs(p[1] - 57.0) < 0.05, (p, m))
    print('   vehicle:', L.cmd('execute as @a[name=tester] on vehicle run data get entity @s attributes')[:300])
    print('   saddle:', L.cmd('data get entity @e[tag=ek.mount,limit=1] equipment')[:200])
    print('   speed attr:', L.cmd('attribute tester minecraft:movement_speed base get')[:80])

    print('== start a game (slot 0, right-click)')
    b.slot(0); t.step(1); b.use(); t.step(3)
    s = L.scores('state', 'stage', 'steve'); t.ok('game started', s['state'] == 1, s)
    L.step(60)
    sp = L.pos_of('@e[tag=ek.steve,limit=1]'); print('   steve at', sp, 'player at', t.ppos())

    print('== cursor')
    L.cmd('scoreboard players set #idlecd ek 99999')       # no distractions while measuring
    for _ in range(40):                                     # wait for a standing-still moment (act phase)
        if L.score('#phase') == 1 and L.score('#intr') == 0: break
        L.step(10)
    sp = L.pos_of('@e[tag=ek.steve,limit=1]')
    t.look_at((sp[0], sp[1] + 0.1, sp[2]))
    c = L.pos_of('@e[tag=ek.cur,limit=1]'); d = math.dist(c, sp)
    t.ok('cursor at Steve when looking at his feet', L.score('#cur') == 1 and d < 1.6, (c, sp, round(d, 2)))
    t.look_at((sp[0] + 4, sp[1] + 0.05, sp[2]))
    c = L.pos_of('@e[tag=ek.cur,limit=1]'); d = math.dist(c, (sp[0] + 4, sp[1], sp[2]))
    t.ok('cursor follows the look (4 east of Steve)', L.score('#cur') == 1 and d < 1.6, (c, round(d, 2), 'lock', L.score('#lock')))
    cv = L.pos_of('@e[tag=ek.curv,limit=1]'); t.ok('cursor label follows', cv and math.dist(cv, (c[0], c[1] + 0.7, c[2])) < 0.2, cv)
    b.look(180, -60); t.step(2)
    t.ok('no cursor when looking at the ceiling', L.score('#cur') == 0, L.pos_of('@e[tag=ek.curv,limit=1]'))
    b.look(0, 30); t.step(2)
    t.ok('no cursor when looking away from the table', L.score('#cur') == 0)

    print('== throw (creeper, slot 0)')
    for _ in range(40):
        if L.score('#phase') == 1 and L.score('#intr') == 0: break
        L.step(10)
    L.cmd('scoreboard players set #energy ek 100')
    sp = L.pos_of('@e[tag=ek.steve,limit=1]')
    b.slot(0); t.look_at((sp[0], sp[1] + 0.1, sp[2]))
    print('   actionbar state am =', L.score('#am'), 'aimed', L.score('#aimed'), 'tier', L.score('#tier'))
    b.use(); t.step(2)
    s = L.scores('drop', 'dropt', 'energy', 'dcard'); t.ok('throw in the air', s['drop'] == 1 and s['energy'] < 100, s)
    t.ok('aim marker + falling item + landing mark', (L.count('@e[tag=ek.aim]'), L.count('@e[tag=ek.dropv]'), L.count('@e[tag=ek.ring]')) == (1, 1, 1))
    b.use(); t.step(1)
    L.step(20)
    s = L.scores('drop', 'intr', 'tier', 'sweet', 'aimx'); t.ok('landed and started the event', s['drop'] == 0 and s['intr'] >= 1 and s['tier'] >= 2, s)
    t.ok('creeper spawned', L.count('@e[tag=ek.creep]') == 1)
    L.step(140)
    t.ok('event over, nothing left behind', L.score('#intr') == 0 and L.count('@e[tag=ek.aim]') + L.count('@e[tag=ek.mob]') == 0, L.scores('intr', 'mental'))

    print('== miss')
    for _ in range(40):
        if L.score('#phase') == 1 and L.score('#intr') == 0 and L.score('#steve') == 1: break
        L.step(10)
    L.cmd('scoreboard players set #energy ek 100')
    sp = L.pos_of('@e[tag=ek.steve,limit=1]')
    far = (sp[0] + (12 if sp[0] < 0 else -12), sp[1], sp[2])
    b.slot(5); t.look_at(far); c = L.pos_of('@e[tag=ek.cur,limit=1]')
    print('   cursor', c, 'cur', L.score('#cur'), 'am', L.score('#am'))
    m0 = L.score('#mental'); b.use(); t.step(2); L.step(20)
    s = L.scores('drop', 'intr', 'tier', 'energy', 'mental'); t.ok('anvil far away misses and half its energy comes back', s['tier'] == 0 and s['intr'] == 0 and s['mental'] == m0 and 84 <= s['energy'] <= 90, s)

    print('== zoom (hold sneak)')
    before = t.ppos()
    b.sneak(True); t.step(2)
    after = t.ppos()
    t.ok('off the mount, zoom on', t.psc('ek.rd') == 0 and t.psc('ek.zm') == 1, (t.psc('ek.rd'), t.psc('ek.zm')))
    t.ok('stayed on the spot', math.dist(before, after) < 0.3, (before, after))
    t.ok('speed 0', '0.0' in L.cmd('attribute tester minecraft:movement_speed base get'), L.cmd('attribute tester minecraft:movement_speed base get')[:60])
    pose = L.data('@a[name=tester,limit=1]', 'Pose') if False else ''
    sp = L.pos_of('@e[tag=ek.steve,limit=1]')
    t.look_at((sp[0], sp[1] + 0.1, sp[2]), crouch=True)
    c = L.pos_of('@e[tag=ek.cur,limit=1]'); d = math.dist(c, sp)
    t.ok('cursor still right while crouched', L.score('#cur') == 1 and d < 1.6, (c, sp, round(d, 2)))
    L.step(40)
    t.ok('still off the mount after 2 s', t.psc('ek.rd') == 0 and math.dist(before, t.ppos()) < 0.3, t.ppos())
    b.sneak(False); t.step(3)
    t.ok('back on the mount', t.psc('ek.rd') == 1 and L.count('@e[tag=ek.mount]') == 1, (t.psc('ek.rd'), L.count('@e[tag=ek.mount]')))
    t.ok('speed 0.1', '0.1' in L.cmd('attribute tester minecraft:movement_speed base get'))
    t.ok('same place', math.dist(before, t.ppos()) < 0.3, t.ppos())

    print('== lucky box')
    # a box in the open, where nothing stands between it and the player (a random one may well be hidden behind a tree or a hill)
    L.cmd('function ek:box/clear'); L.cmd('execute positioned 6.5 62 11.5 run function ek:box/place'); L.step(2)
    bp = L.pos_of('@e[tag=ek.box,limit=1]'); t.ok('box spawned', bp is not None, bp)
    if bp:
        t.look_at(bp)
        t.ok('box picked by the look', L.count('@e[tag=ek.box,tag=ek.pick]') == 1, ('am', L.score('#am')))
        e0 = L.scores('energy', 'lucky'); b.slot(1); t.step(1); b.use(); t.step(3)
        e1 = L.scores('energy', 'lucky', 'box', 'fgot'); t.ok('box opened', e1['box'] == 0 and L.count('@e[tag=ek.box]') == 0 and (e1['energy'] > e0['energy'] or e1['lucky'] == 1), (e0, e1))
    # a box under a tree, hidden from above: it glows through the leaves, so looking at it still opens it
    L.cmd('execute positioned 0.5 62 8.5 run function ek:box/place'); L.step(2)
    bp = L.pos_of('@e[tag=ek.box,limit=1]'); t.look_at(bp)
    t.ok('hidden box picked through the leaves', L.count('@e[tag=ek.box,tag=ek.pick]') == 1, ('am', L.score('#am'), 'cursor', L.pos_of('@e[tag=ek.cur,limit=1]')))
    b.use(); t.step(3); t.ok('hidden box opened', L.score('#box') == 0)
    sp = L.pos_of('@e[tag=ek.steve,limit=1]'); b.look(180, -60); t.step(2)
    t.ok('nothing picked when not looking at a box', L.count('@e[tag=ek.pick]') == 0)

    print('== ride around (vehicle move packets)')
    p0 = t.ppos(); m0 = L.pos_of('@e[tag=ek.mount,limit=1]')
    for k in range(1, 11):
        b._send('play', 'move_vehicle', struct.pack('>dddffb', m0[0] + 0.6 * k, m0[1], m0[2], b.rot[0], 0.0, 1)); time.sleep(0.06); L.step(1)
    p1 = t.ppos(); t.ok('moved 6 blocks with the mount', abs((p1[0] - p0[0]) - 6.0) < 0.5 and t.psc('ek.rd') == 1, (p0, p1))

    print('== relog')
    b.close(); time.sleep(0.6); L.step(5)
    print('   mounts while offline:', L.count('@e[tag=ek.mount]'))
    b2 = Bot('tester'); t.b = b2; assert b2.wait_joined(), b2.kicked
    time.sleep(0.5); L.step(10)
    t.ok('riding again after relog, one mount', t.psc('ek.rd') == 1 and L.count('@e[tag=ek.mount]') == 1, (t.psc('ek.rd'), L.count('@e[tag=ek.mount]')))
    b2.close(); time.sleep(0.5); L.step(3)
    bad = [l for l in L.problems() if 'DYING' not in l and 'authlib' not in l and 'java.base' not in l and 'minecraftservices' not in l and 'Services Discovery' not in l]
    print('server complaints:', len(bad))
    for l in bad[:20]: print('   ', l[:300])
    print('FAILED:' if t.fail else 'ALL OK', t.fail)

if __name__ == '__main__':
    main()
