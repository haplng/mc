# survival rules: what was built can be broken (with the bare hand too), the map cannot
import sys, time, re, math, struct, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
sys.path.insert(0, '/home/claude/bw/gen3'); import items
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
c('effect give tester minecraft:resistance infinite 4 true')
def bpos(x, y, z): return struct.pack('>Q', ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF))
seq = [300]
def place(x, y, z, face=1):
    seq[0] += 1; b._send('play', 'use_item_on', varint(0) + bpos(x, y, z) + varint(face) + struct.pack('>fff', 0.5, 1.0, 0.5) + b'\x00\x00' + varint(seq[0]))
def dig(x, y, z, secs):
    seq[0] += 1; b._send('play', 'player_action', varint(0) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(secs)
    seq[0] += 1; b._send('play', 'player_action', varint(3) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(0.4)
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} {blk}')
spd = lambda: c('attribute tester minecraft:block_break_speed base get').split()[-1]
p = pos('tester'); px, py, pz = math.floor(p[0]), math.floor(p[1]), math.floor(p[2])
print('mode', c('data get entity tester playerGameType')[-3:], 'pos', p, 'copy placed', sc('#cp_tea'), 'zoff predicate placed at floor:', c(f'execute positioned {px} {py - 1} {pz} if predicate bw:placed')[:11])
# a floor block two steps away with air above it
cand = [(dx, dz) for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)) if not is_(px + dx, py - 1, pz + dz, '#bw:open') and is_(px + dx, py, pz + dz, 'minecraft:air') and is_(px + dx // 2, py, pz + dz // 2, '#bw:open')]
dx, dz = cand[0]; tx, ty, tz = px + dx, py - 1, pz + dz
yaw = {(2, 0): -90, (-2, 0): 90, (0, 2): 0, (0, -2): 180}[(dx, dz)]
c(f'tp tester {px + 0.5} {py} {pz + 0.5} {yaw} 39'); time.sleep(1.0); b.look(yaw, 39); time.sleep(0.4)
print('floor block', (tx, ty, tz), c(f'data get block {tx} {ty} {tz}')[:50] if False else '', 'looking at map: speed', spd(), 'deny', sc('tester', 'bw.deny'))
c('clear tester'); b.slot(3); time.sleep(0.3)
dig(tx, ty, tz, 3.0); print('  dig the map floor with the bare hand 3 s -> still there:', not is_(tx, ty, tz, 'minecraft:air'))
# put a wool block on it and break that with the bare hand
c(f'give tester {items.it("red_wool", items.BLOCK)} 4'); time.sleep(0.3); b.slot(0); time.sleep(0.3); place(tx, ty, tz); time.sleep(0.5)
print('placed wool:', is_(tx, ty + 1, tz, 'minecraft:red_wool'))
b.look(yaw, 25); time.sleep(0.5); print('  looking at the wool: speed', spd(), 'deny', sc('tester', 'bw.deny'))
b.slot(3); time.sleep(0.3); dig(tx, ty + 1, tz, 1.6); print('  dig the wool with the bare hand 1.6 s -> gone:', is_(tx, ty + 1, tz, 'minecraft:air'), '| wool items lying:', c('execute if entity @e[type=item,nbt={Item:{id:"minecraft:red_wool"}}]')[:12])
b.look(yaw, 39); time.sleep(0.4); print('  back on the map floor: speed', spd())
b.look(yaw, -60); time.sleep(0.4); print('  looking at the sky: speed', spd())
# an enemy bed
bed = None
maps = {m['id']: m for m in json.load(open('/tmp/bwout/maps.json'))}
bm = pos('@e[type=marker,tag=bw.bed,tag=bw.t.blue,limit=1]'); bx, by, bz = math.floor(bm[0]), math.floor(bm[1]), math.floor(bm[2])
for ddx, ddz, yw in ((-2, 0, -90), (2, 0, 90), (0, -2, 0), (0, 2, 180)):
    if is_(bx + ddx, by, bz + ddz, '#bw:open') and is_(bx + ddx // 2, by, bz + ddz // 2, '#bw:open') and not is_(bx + ddx, by - 1, bz + ddz, '#bw:open'):
        c(f'tp tester {bx + ddx + 0.5} {by} {bz + ddz + 0.5} {yw} 40'); time.sleep(1.0); b.look(yw, 40); time.sleep(0.5)
        print('at the blue bed', (bx, by, bz), 'from', (ddx, ddz), ': speed', spd()); break
dig(bx, by, bz, 1.0); time.sleep(0.5); print('  bed broken by hand:', sc('#bed1') == 0, b.chat[-2:])
print(errors()[-300:]); b.close()
