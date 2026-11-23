# no building on generators / spawn / shopkeepers; one's own bed; who gets a dead player's purse
import sys, time, re, math, struct, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
sys.path.insert(0, '/home/claude/bw/gen3'); import items
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
def bpos(x, y, z): return struct.pack('>Q', ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF))
seq = [700]
def place(x, y, z, face=1):
    seq[0] += 1; b._send('play', 'use_item_on', varint(0) + bpos(x, y, z) + varint(face) + struct.pack('>fff', 0.5, 1.0, 0.5) + b'\x00\x00' + varint(seq[0]))
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} {blk}')
spd = lambda: c('attribute tester minecraft:block_break_speed base get').split()[-1]
F = lambda p: (math.floor(p[0]), math.floor(p[1]), math.floor(p[2]))
c('effect give tester minecraft:resistance infinite 4 true')
print('protected markers:', c('execute if entity @e[type=marker,tag=bw.prot]')[-10:])
# ---- wool put down next to things
c('clear tester'); c(f'give tester {items.it("red_wool", items.BLOCK)} 8'); time.sleep(0.3); b.slot(0); time.sleep(0.3)
for what, sel in (('own forge', '@e[type=marker,tag=bw.gen.iron,tag=bw.t.red,limit=1]'), ('own spawn', '@e[type=marker,tag=bw.spawn,tag=bw.t.red,limit=1]'),
                  ('a diamond generator', '@e[type=marker,tag=bw.gen.diamond,sort=nearest,limit=1]')):
    m = F(pos(sel)); tx, ty, tz = m[0] + 1, m[1], m[2]          # the cell beside the marker, on the floor
    if not is_(tx, ty, tz, 'minecraft:air') or is_(tx, ty - 1, tz, '#bw:open'): tx, tz = m[0], m[2] + 1
    c(f'tp tester {m[0] + 0.5} {m[1] + 0.2} {m[2] - 1.5} 0 40' if (tx, tz) == (m[0] + 1, m[2]) else f'tp tester {m[0] - 1.5} {m[1] + 0.2} {m[2] + 0.5} -90 40'); time.sleep(0.8)
    n0 = count('red_wool'); place(tx, ty - 1, tz); time.sleep(0.5)
    print(f'{what}: wool on the cell beside it -> there now: {is_(tx, ty, tz, "minecraft:red_wool")}, wool left {n0} -> {count("red_wool")}')
    # and three cells away: stays
    fx, fz = (m[0] + 3, m[2]) if not is_(m[0] + 3, m[1] - 1, m[2], '#bw:open') and is_(m[0] + 3, m[1], m[2], 'minecraft:air') else (m[0], m[2] + 3)
    if not is_(fx, m[1] - 1, fz, '#bw:open') and is_(fx, m[1], fz, 'minecraft:air'):
        place(fx, m[1] - 1, fz); time.sleep(0.5); print(f'   three cells away -> there: {is_(fx, m[1], fz, "minecraft:red_wool")}'); c(f'setblock {fx} {m[1]} {fz} minecraft:air')
# ---- one's own bed
bm = F(pos('@e[type=marker,tag=bw.bed,tag=bw.t.red,limit=1]'))
for ddx, ddz, yw in ((-2, 0, -90), (2, 0, 90), (0, -2, 0), (0, 2, 180)):
    if is_(bm[0] + ddx, bm[1], bm[2] + ddz, '#bw:open') and is_(bm[0] + ddx // 2, bm[1], bm[2] + ddz // 2, '#bw:open') and not is_(bm[0] + ddx, bm[1] - 1, bm[2] + ddz, '#bw:open'):
        c(f'tp tester {bm[0] + ddx + 0.5} {bm[1]} {bm[2] + ddz + 0.5} {yw} 40'); time.sleep(0.9); b.look(yw, 40); time.sleep(0.5)
        print('looking at the red bed: speed', spd(), 'deny', sc('tester', 'bw.deny')); break
# ---- the purse of the dead
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
c('clear tester'); c('give tester minecraft:iron_ingot 37'); c('give tester minecraft:gold_ingot 5'); c('give tester minecraft:emerald 2'); c('give tester minecraft:diamond 3'); c('effect clear tester minecraft:resistance')
w0 = [sc(f'#w{k}2') for k in ('fe', 'au', 'di', 'em')]
c('scoreboard players set tester bw.lh 2'); c('scoreboard players set tester bw.lht 100'); c('damage tester 100 minecraft:generic'); time.sleep(1.0)
print('killed by team 2: its purse', w0, '->', [sc(f'#w{k}2') for k in ('fe', 'au', 'di', 'em')], [m[:40] for m in b.chat[-2:]])
time.sleep(6.5)
c('scoreboard players set #wfe3 bw 21'); c('scoreboard players set #wau3 bw 4'); c('scoreboard players set #wem3 bw 1'); c('scoreboard players set #wdi3 bw 0')
c(f'scoreboard players set {B(3)} bw.lh 0'); c(f'scoreboard players set {B(3)} bw.lht 100'); n0 = len(b.chat); c(f'damage {B(3)} 25 minecraft:generic'); time.sleep(1.0)
print('tester kills bot 3 (21 iron, 4 gold, 1 emerald):', [m[:30] for m in b.chat[n0:]], 'has', count('iron_ingot'), count('gold_ingot'), count('emerald'))
c('scoreboard players set #wfe4 bw 9'); w5 = sc('#wfe5'); c(f'scoreboard players set {B(4)} bw.lh 5'); c(f'scoreboard players set {B(4)} bw.lht 100'); c(f'damage {B(4)} 25 minecraft:generic'); time.sleep(0.6)
print('bot 5 kills bot 4 (9 iron): purse of 5', w5, '->', sc('#wfe5'))
print(errors()[-300:]); c('function bw:game/close'); time.sleep(1); b.close()
