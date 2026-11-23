# team upgrades: traps and their queue, cushioned boots, dragon buff; magic milk against a trap
import sys, time, re, math, struct, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
sys.path.insert(0, '/home/claude/bw/gen3'); import items
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
for d in items.UPGRADES + items.TRAPS: c(f'tag tester add bw.u.up_{d["key"]}')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
c('effect give tester minecraft:resistance infinite 4 true')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
def blk(p): return f'{math.floor(p[0])} {math.floor(p[1])} {math.floor(p[2])}'
def chest(kind, team='red'):
    return (pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.a,tag=bw.t.{team},limit=1]'), pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.b,tag=bw.t.{team},limit=1]'))
def items_of(p):
    a = c(f'data get block {blk(p)} Items'); out = {}
    for m in re.finditer(r'bwgui: \{id: (\d+)\}.*?"minecraft:item_name": \{([^}]*)\}.*?Slot: (\d+)b, id: "minecraft:([a-z_]+)"', a):
        nm = re.search(r'text: "([^"]*)"', m.group(2)); col = re.search(r'color: "([^"]*)"', m.group(2))
        out[int(m.group(3))] = (int(m.group(1)), m.group(4), nm.group(1) if nm else '', col.group(1) if col else '')
    return out
def click(p, slot):
    r_ = c(f'item replace entity tester container.20 from block {blk(p)} container.{slot}'); time.sleep(0.4); return r_
T, Tb = chest('team'); c(f'tp tester {T[0] - 2} {T[1]} {T[2]}'); c('give tester minecraft:diamond 40'); time.sleep(1.5)
top = items_of(T); bot_ = items_of(Tb)
print('top:', {k: v[1:] for k, v in sorted(top.items()) if k not in range(27, 36)}); print('bottom:', {k + 27: v[1:] for k, v in sorted(bot_.items()) if v[1] != 'gray_stained_glass_pane'})
q = lambda: (sc('#tqn0'), sc('#tq0a'), sc('#tq0b'), sc('#tq0c'), count('diamond'))
n0 = len(b.chat); click(T, 14); print('buy trap 1:', q(), b.chat[n0:])
n0 = len(b.chat); click(T, 23); print('buy trap 4:', q(), b.chat[n0:])
n0 = len(b.chat); click(T, 15); print('buy trap 2:', q(), b.chat[n0:])
n0 = len(b.chat); click(T, 16); print('a fourth:', q(), b.chat[n0:])
time.sleep(0.6); print('queue shown:', {k + 27: v[2] for k, v in sorted(items_of(Tb).items()) if k + 27 in (39, 40, 41)}, '| trap icon now:', items_of(T).get(14))
n0 = len(b.chat); click(T, 21); click(T, 21); print('cushion x2:', sc('#cush0'), count('diamond'), 'boots:', c('data get entity tester equipment.feet.components')[-110:], b.chat[n0:])
n0 = len(b.chat); click(T, 22); print('dragon buff:', sc('#dbuff0'), count('diamond'), b.chat[n0:])
# ---- an enemy at the red bed: the traps go off one by one, ten seconds apart
bed = pos('@e[type=marker,tag=bw.bed,tag=bw.t.red,limit=1]')
c(f'scoreboard players set {B(1)} bw.st 9'); c(f'scoreboard players set {B(1)} bw.pst 9'); c(f'tp {B(1)} {bed[0] + 3} {bed[1] + 3} {bed[2]}'); c(f'data merge entity {B(1)} {{NoGravity:1b}}')
n0 = len(b.chat); time.sleep(1.6); print('trap 1 (blind):', q()[:4], 'cooldown', sc('#tcd0'), 'bot slow', sc(B(1), 'bw.slow'), 'titles', [x for x in b.titles[-3:]] if hasattr(b, 'titles') else '')
time.sleep(10.5); print('trap 4 (fatigue):', q()[:4], 'bot mfat', sc(B(1), 'bw.mfat'))
time.sleep(10.5); print('trap 2 (counter):', q()[:4], 'tester effects', re.findall(r'id: "minecraft:(\w+)"', c('data get entity tester active_effects')))
c(f'data merge entity {B(1)} {{NoGravity:0b}}'); c(f'tp {B(1)} 606.5 120 0.5')
# ---- the tester at the blue bed: blinded; with milk in it: not
bb = pos('@e[type=marker,tag=bw.bed,tag=bw.t.blue,limit=1]')
c('function bw:trap/add {i:1,k:1}'); c('function bw:trap/add {i:1,k:3}'); c('effect clear tester minecraft:speed'); c('scoreboard players set tester bw.milk 100')
c(f'tp tester {bb[0] + 3} {bb[1] + 1} {bb[2]}'); time.sleep(1.6); print('with milk at the blue bed: queue', sc('#tqn1'), 'blind', 'blindness' in c('data get entity tester active_effects'))
c('scoreboard players set tester bw.milk 0'); time.sleep(1.6); print('without: queue', sc('#tqn1'), 'blind', 'blindness' in c('data get entity tester active_effects'), b.chat[-1:])
c('effect give tester minecraft:invisibility 60 0'); c('scoreboard players set #tcd1 bw 0'); time.sleep(1.6); print('alarm: queue', sc('#tqn1'), 'invisible', 'invisibility' in c('data get entity tester active_effects'), b.chat[-1:])
print(errors()[-300:]); b.close()
