import sys, time, re; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0'); c('scoreboard players set tester bw.coins 1000')
print('start', start('tea', b)); time.sleep(1)
def chest(kind, team='red'):
    t = f',tag=bw.t.{team}' if team else ''
    a = pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.a{t},limit=1,sort=nearest]'); bb = pos(f'@e[type=marker,tag=bw.gui.{kind},tag=bw.gui.b{t},limit=1,sort=nearest]')
    return a, bb
def slots(p):
    a = c(f'data get block {int(p[0] - 0.5)} {int(p[1])} {int(p[2] - 0.5) if p[2] > 0 else int(p[2] - 0.5)} Items')
    return a
def blk(p): import math; return f'{math.floor(p[0])} {math.floor(p[1])} {math.floor(p[2])}'
def items_of(p):
    a = c(f'data get block {blk(p)} Items'); out = {}
    for m in re.finditer(r'bwgui: \{id: (\d+)\}.*?Slot: (\d+)b, id: "minecraft:([a-z_]+)"', a): out[int(m.group(2))] = (int(m.group(1)), m.group(3))
    if not out:
        for m in re.finditer(r'Slot: (\d+)b', a): out[int(m.group(1))] = ('?', '?')
    return out, a
def click(p, slot):
    c('clear tester minecraft:stone'); r_ = c(f'item replace entity tester container.20 from block {blk(p)} container.{slot}'); time.sleep(0.35); return r_
A, Bm = chest('shop'); print('shop chest a', A, 'b', Bm)
c(f'tp tester {A[0] + 2} {A[1]} {A[2]}'); c('give tester minecraft:iron_ingot 64'); c('give tester minecraft:gold_ingot 20'); c('give tester minecraft:emerald 8'); c('give tester minecraft:diamond 20'); time.sleep(1.2)
ia, raw = items_of(A); ib, rawb = items_of(Bm)
print('top half', len(ia), 'slots:', dict(sorted(ia.items()))); print('bottom half', len(ib), dict(sorted(ib.items())))
print('raw sample', raw[:420])
# buy wool (slot 19 of the window = top half container 19)
n0 = len(b.chat); click(A, 19); print('wool:', count('red_wool'), 'iron left', count('iron_ingot'), b.chat[n0:])
# stone sword (slot 20), chain armour (slot 21 -> locked), pick (22)
n0 = len(b.chat); click(A, 20); print('stone sword:', inv(), b.chat[n0:])
n0 = len(b.chat); click(A, 21); print('chain (locked):', b.chat[n0:])
n0 = len(b.chat); click(A, 22); click(A, 22); print('pick x2:', sc('tester', 'bw.pick'), [i for i in inv() if 'pick' in i[1]], b.chat[n0:])
# tab 5 (tools): slot 4
click(A, 4); time.sleep(0.8); ia, _ = items_of(A); print('page', sc('@e[type=marker,tag=bw.gui.shop,tag=bw.gui.a,tag=bw.t.red,limit=1]', 'bw.page'), 'row1 panes', [ia.get(k, ('', ''))[1][:4] for k in range(9, 18)], 'items', {k: v for k, v in ia.items() if k >= 18})
n0 = len(b.chat); click(A, 19); print('shears:', sc('tester', 'bw.shears'), b.chat[n0:])
# a foreign item put into the chest comes back
c(f'item replace block {blk(A)} container.26 with minecraft:dirt 3'); time.sleep(0.6); print('foreign: in chest?', 'dirt' in c(f'data get block {blk(A)} Items'), 'tester has dirt', count('dirt'), 'item entity near', c('execute if entity @e[type=item,distance=..9,nbt={Item:{id:"minecraft:dirt"}}]')[:14])
# team upgrades
T, Tb = chest('team'); c(f'tp tester {T[0] - 2} {T[1]} {T[2]}'); time.sleep(1.2); it, raw = items_of(T); print('team top', dict(sorted(it.items())))
n0 = len(b.chat); click(T, 10); print('sharp locked:', b.chat[n0:])
c('tag tester add bw.u.up_sharp'); c('tag tester add bw.u.up_prot'); c('tag tester add bw.u.up_forge'); time.sleep(0.7)
n0 = len(b.chat); click(T, 10); print('sharp:', sc('#sharp0'), 'diamonds', count('diamond'), c('data get entity tester Inventory[{Slot:0b}].components')[:160], b.chat[n0:])
n0 = len(b.chat); click(T, 11); click(T, 11); print('prot x2:', sc('#prot0'), 'diamonds', count('diamond'), c('data get entity tester equipment.chest.components."minecraft:enchantments"')[-60:], b.chat[n0:])
n0 = len(b.chat); click(T, 19); print('forge:', sc('#fl0'), sc('#fs0'), b.chat[n0:])
print(errors()); b.close()
