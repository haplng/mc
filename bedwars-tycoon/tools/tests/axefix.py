# survival hands: bark peeled with an axe comes back; a dragon does not eat the shop counter
import sys, time, re, math, struct, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
sys.path.insert(0, '/home/claude/bw/gen3'); import items
ZOFF = int(re.search(r'~(\d+) ~7', open('/tmp/bwout/bedwars_maps/data/bw/function/game/axefix.mcfunction').read()).group(1)) + 7
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state'), 'zoff', ZOFF); time.sleep(1)
def bpos(x, y, z): return struct.pack('>Q', ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF))
seq = [500]
def use_on(x, y, z, face=1):
    seq[0] += 1; b._send('play', 'use_item_on', varint(0) + bpos(x, y, z) + varint(face) + struct.pack('>fff', 0.5, 1.0, 0.5) + b'\x00\x00' + varint(seq[0]))
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} {blk}')
what = lambda x, y, z: next((n for n in ('oak_log', 'stripped_oak_log', 'waxed_copper_block', 'copper_block', 'air') if is_(x, y, z, 'minecraft:' + n)), '?')
p = pos('tester'); px, py, pz = math.floor(p[0]), math.floor(p[1]), math.floor(p[2])
cand = [(dx, dz) for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)) if is_(px + dx, py, pz + dz, 'minecraft:air') and is_(px + dx // 2, py, pz + dz // 2, '#bw:open')]
dx, dz = cand[0]; tx, ty, tz = px + dx, py, pz + dz
yaw = {(2, 0): -90, (-2, 0): 90, (0, 2): 0, (0, -2): 180}[(dx, dz)]
c(f'tp tester {px + 0.5} {py} {pz + 0.5} {yaw} 20'); time.sleep(0.8); b.look(yaw, 20); time.sleep(0.3)
c('clear tester'); c('give tester minecraft:wooden_axe'); time.sleep(0.3); b.slot(0); time.sleep(0.3)
for blk in ('oak_log', 'waxed_copper_block'):
    # a "map" block: the same in the map and in its copy
    c(f'setblock {tx} {ty} {tz} minecraft:{blk}'); c(f'setblock {tx} {ty} {tz + ZOFF} minecraft:{blk}'); time.sleep(0.3)
    c('scoreboard players set #sudden bw 1'); use_on(tx, ty, tz); time.sleep(0.4); mid = what(tx, ty, tz)       # with the fix switched off, to see the axe at work
    c('scoreboard players set #sudden bw 0'); c(f'setblock {tx} {ty} {tz} minecraft:{blk}'); time.sleep(0.2)
    use_on(tx, ty, tz); time.sleep(0.4)
    print(f'  {blk}: an axe makes it {mid}; with the fix it is {what(tx, ty, tz)}')
    c(f'setblock {tx} {ty} {tz} minecraft:air'); c(f'setblock {tx} {ty} {tz + ZOFF} minecraft:air')
# ---- a dragon through the shop counter
S = pos('@e[type=marker,tag=bw.gui.shop,tag=bw.gui.a,tag=bw.t.red,limit=1]'); sx, sy, sz = math.floor(S[0]), math.floor(S[1]), math.floor(S[2])
c('scoreboard players set #sec bw 2398'); time.sleep(2.5); c('tag @e[type=ender_dragon] remove bw.dragon')
c('tp tester 600.5 90 0.5'); 
d = '@e[type=ender_dragon,scores={bw.team=3},limit=1]'
air0 = c(f'execute store result score #n bw run clone {sx - 6} {sy - 3} {sz - 6} {sx + 6} {sy + 6} {sz + 6} {sx - 6} {sy - 3} {sz - 6} filtered minecraft:air force')
for k in range(8): c(f'tp {d} {sx + 0.5} {sy - 1 + (k % 3)} {sz + 0.5 + (k % 2) * 3} 0 0'); time.sleep(0.25)
c(f'tp {d} 600 140 0'); time.sleep(0.3)
air1 = c(f'execute store result score #n bw run clone {sx - 6} {sy - 3} {sz - 6} {sx + 6} {sy + 6} {sz + 6} {sx - 6} {sy - 3} {sz - 6} filtered minecraft:air force')
print('dragon through the red shop: air cells', re.findall(r'\d+', air0)[:1], '->', re.findall(r'\d+', air1)[:1], '| counter still there:', is_(sx, sy, sz, 'minecraft:waxed_copper_chest'),
      '| keeper alive:', 'passed' in c('execute if entity @e[type=villager,tag=bw.npc.shop,tag=bw.t.red]'))
print(errors()[-300:])
c('function bw:game/close'); time.sleep(1.5); b.close()
