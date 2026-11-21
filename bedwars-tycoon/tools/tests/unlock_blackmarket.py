import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0'); c('scoreboard players set tester bw.coins 3000'); c('gamemode adventure tester')
def blk(p): return f'{math.floor(p[0])} {math.floor(p[1])} {math.floor(p[2])}'
def items_of(p):
    a = c(f'data get block {blk(p)} Items'); out = {}
    for m in re.finditer(r'bwgui: \{id: (\d+)\}.*?Slot: (\d+)b, id: "minecraft:([a-z_]+)"', a): out[int(m.group(2))] = (int(m.group(1)), m.group(3))
    return out
def click(p, slot):
    r_ = c(f'item replace entity tester container.20 from block {blk(p)} container.{slot}'); time.sleep(0.4); return r_
def chest(kind):
    return pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.a,limit=1]'), pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.b,limit=1]')
U, Ub = chest('unlock'); print('unlock chest', U, Ub)
c(f'tp tester {U[0] + 2} {U[1]} {U[2]}'); time.sleep(1.5)
ia = items_of(U); ib = items_of(Ub); print('unlock top', {k: v for k, v in ia.items() if k >= 18 or k < 9}); print('unlock bottom', ib)
click(U, 2); time.sleep(0.8); ia = items_of(U); print('melee page:', {k: v for k, v in ia.items() if k >= 18})
n0 = len(b.chat); click(U, 20); print('unlock iron sword: coins', sc('tester', 'bw.coins'), 'tag', 'bw.u.iron_sword' in c('tag tester list'), b.chat[n0:])
n0 = len(b.chat); click(U, 20); print('again:', b.chat[n0:])
click(U, 8); time.sleep(0.8); ia = items_of(U); print('team-upgrade page:', {k: v for k, v in ia.items() if k >= 18})
n0 = len(b.chat); click(U, 19); print('unlock sharp: coins', sc('tester', 'bw.coins'), 'bw.u.up_sharp' in c('tag tester list'), b.chat[n0:])
# a foreign item
c(f'item replace block {blk(U)} container.26 with minecraft:dirt 3'); time.sleep(0.7)
print('foreign: in chest?', 'dirt' in c(f'data get block {blk(U)} Items'), '| item entity near', c('execute at tester if entity @e[type=item,distance=..9,nbt={Item:{id:"minecraft:dirt"}}]')[:14], '| tester dirt', count('dirt'))
# black market
K, Kb = chest('black'); print('black chest', K, Kb)
c(f'tp tester {K[0]} {K[1]} {K[2] + 2}'); time.sleep(1.5)
ia = items_of(K); ib = items_of(Kb); print('stage 0 top', dict(sorted(ia.items()))); print('stage 0 bottom', dict(sorted(ib.items())))
n0 = len(b.chat); click(K, 10); print('buy at stage 0:', b.chat[n0:])
c('scoreboard players set tester bw.stage 3'); time.sleep(0.8); ia = items_of(K); print('stage 3 top', dict(sorted(ia.items())))
n0 = len(b.chat); click(K, 10); print('reach L1: h', sc('tester', 'bw.h_reach'), 'coins', sc('tester', 'bw.coins'), 'range', c('attribute tester minecraft:entity_interaction_range get')[-5:], b.chat[n0:])
time.sleep(0.7); ia = items_of(K); print('   toggle row', {k: v for k, v in ia.items() if 18 <= k < 27})
click(K, 19); print('toggle off: range', c('attribute tester minecraft:entity_interaction_range get')[-5:], 'tags', [t_ for t_ in c('tag tester list').split(', ') if 'off' in t_])
click(K, 19); print('toggle on: range', c('attribute tester minecraft:entity_interaction_range get')[-5:])
click(K, 10); click(K, 10); print('reach L3: h', sc('tester', 'bw.h_reach'), 'range', c('attribute tester minecraft:entity_interaction_range get')[-5:], 'coins', sc('tester', 'bw.coins'))
for s in (9, 9, 11, 12, 13, 14, 15, 16): click(K, s)
c('scoreboard players set tester bw.coins 20000'); 
for s in (9, 9, 11, 11, 12, 12, 13, 14, 14, 15, 15, 16): click(K, s)
print('tier1 all: ', {h: sc('tester', f'bw.h_{h}') for h in ('velocity', 'reach', 'eagle', 'aim', 'clicker', 'block', 'kbd', 'antifb')}, 'kbres', c('attribute tester minecraft:knockback_resistance get')[-5:])
time.sleep(0.7); ib = items_of(Kb); print('tier2 at stage 3:', {k: v for k, v in ib.items() if k < 9})
c('scoreboard players set tester bw.stage 9'); time.sleep(0.8); ib = items_of(Kb); print('stage 9 bottom:', dict(sorted(ib.items())))
for s in (0, 1, 1, 2, 2, 3): click(Kb, s)
time.sleep(0.5)
for s in (5, 5, 6, 7, 8): click(Kb, s)
print('all:', {h: sc('tester', f'bw.h_{h}') for h in ('velocity2', 'scaffold', 'lag', 'stasis', 'tower', 'nofall', 'fbjump', 'tpaura')}, 'coins', sc('tester', 'bw.coins'))
print('attrs: range', c('attribute tester minecraft:entity_interaction_range get')[-5:], 'kbres', c('attribute tester minecraft:knockback_resistance get')[-5:], 'fall', c('attribute tester minecraft:fall_damage_multiplier get')[-5:], 'hreach', sc('tester', 'bw.hreach'))
print('chat tail', [m[:60] for m in b.chat[-3:]])
# dealer and unlock keeper clicks
eid = b.find('villager', K[0], K[1], K[2] - 2, 2.5); n0 = len(b.chat); b.interact(eid) if eid else None; time.sleep(0.6); print('dealer click', eid, b.chat[n0:])
print(errors()); b.close()
