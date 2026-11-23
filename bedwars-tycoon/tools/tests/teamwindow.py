# team window: every icon, and what the boots carry
import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
sys.path.insert(0, '/home/claude/bw/gen3'); import items
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
for d in items.UPGRADES + items.TRAPS: c(f'tag tester add bw.u.up_{d["key"]}')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
def blk(p): return f'{math.floor(p[0])} {math.floor(p[1])} {math.floor(p[2])}'
def chest(kind, team='red'):
    return (pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.a,tag=bw.t.{team},limit=1]'), pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.b,tag=bw.t.{team},limit=1]'))
def slots(p, off=0):
    out = {}
    for k in range(27):
        a = c(f'data get block {blk(p)} Items[{{Slot:{k}b}}]')
        if 'id:' not in a: continue
        idm = re.search(r'id: "minecraft:([a-z_]+)"', a.split('Slot:')[-1]) or re.search(r', id: "minecraft:([a-z_]+)"', a)
        nm = re.search(r'"minecraft:item_name": \{[^}]*text: "([^"]*)"', a) or re.search(r'"minecraft:item_name": "([^"]*)"', a)
        g = re.search(r'bwgui: \{id: (\d+)', a)
        out[k + off] = (idm.group(1) if idm else '?', nm.group(1) if nm else '', int(g.group(1)) if g else None)
    return out
def click(p, slot):
    r_ = c(f'item replace entity tester container.20 from block {blk(p)} container.{slot}'); time.sleep(0.4); return r_
T, Tb = chest('team'); c(f'tp tester {T[0] - 2} {T[1]} {T[2]}'); c('give tester minecraft:diamond 40'); time.sleep(1.5)
for k, v in sorted({**slots(T), **slots(Tb, 27)}.items()):
    if v[0] not in ('gray_stained_glass_pane', 'black_stained_glass_pane'): print('  slot', k, v)
click(T, 21); click(T, 21); time.sleep(0.5)
print('boots:', c('data get entity tester equipment.feet.components'))
c('function bw:game/close'); time.sleep(1); b.close()
