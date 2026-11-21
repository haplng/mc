import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 2'); c('scoreboard players set tester bw.coins 400'); c('gamemode adventure tester')
for m_ in ('chess', 'circus', 'library', 'solar'): c(f'tag tester remove bw.m.{m_}')
print('tags', [t_ for t_ in c('tag tester list').split(', ') if 'bw.m.' in t_])
n0 = len(b.chat); print('locked gate: start took', start('chess', b, wait=4, unlock=False), 'state', sc('#state'), b.chat[n0:])
time.sleep(3.2); print('   message again after 3s:', len(b.chat) - n0, 'lines')
def blk(p): return f'{math.floor(p[0])} {math.floor(p[1])} {math.floor(p[2])}'
def items_of(p):
    a = c(f'data get block {blk(p)} Items'); out = {}
    for m in re.finditer(r'bwgui: \{id: (\d+)\}.*?Slot: (\d+)b, id: "minecraft:([a-z_]+)"', a): out[int(m.group(2))] = (int(m.group(1)), m.group(3))
    return out
def click(p, slot): c(f'item replace entity tester container.20 from block {blk(p)} container.{slot}'); time.sleep(0.4)
U = pos('@e[type=marker,tag=bw.gui.unlock,tag=bw.gui.a,limit=1]'); Ub = pos('@e[type=marker,tag=bw.gui.unlock,tag=bw.gui.b,limit=1]')
c(f'tp tester {U[0] + 2} {U[1]} {U[2]}'); time.sleep(1.5); ib = items_of(Ub); print('bottom row', {k: v for k, v in ib.items() if k >= 18})
print('   chess lore', re.findall(r'text: "([^"]+)"', c(f'data get block {blk(Ub)} Items[{{Slot:21b}}]'))[:12])
n0 = len(b.chat); click(Ub, 22); print('circus (600, too dear):', b.chat[n0:])
n0 = len(b.chat); click(Ub, 21); print('chess (250): coins', sc('tester', 'bw.coins'), 'tag', 'bw.m.chess' in c('tag tester list'), b.chat[n0:])
print('enter chess: took', start('chess', b, unlock=False), 'state', sc('#state'), 'map', sc('#map'), 'mapmult', sc('#mapmult'), 'mult', sc('#mult'), 'lvl', sc('#lvl'), [m[:40] for m in b.chat[-3:]])
# the stranger with the hint
time.sleep(1); h = pos('@e[type=villager,tag=bw.npc.hint,limit=1]'); print('hint npc at', h)
if h:
    c(f'tp tester {h[0] + 1.5} {h[1]} {h[2]}'); time.sleep(1.2); eid = b.find('villager', h[0], h[1], h[2], 1.0); n0 = len(b.chat); b.interact(eid) if eid else None; time.sleep(0.6); print('   click', eid, b.chat[n0:])
print(errors()); b.close()
