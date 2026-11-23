# the four items: bedbug, dream defender, magic milk, pop-up tower (used by a player, against a bot)
import sys, time, re, math, struct, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
sys.path.insert(0, '/home/claude/bw/gen3'); import items
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
c('effect give tester minecraft:resistance infinite 4 true')
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
def bpos(x, y, z): return struct.pack('>Q', ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF))
seq = [400]
def place(x, y, z, face=1):
    seq[0] += 1; b._send('play', 'use_item_on', varint(0) + bpos(x, y, z) + varint(face) + struct.pack('>fff', 0.5, 1.0, 0.5) + b'\x00\x00' + varint(seq[0]))
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} {blk}')
hpb = lambda: c(f'data get entity {B(1)} Health').split()[-1]
give = lambda key, n=1: c(f'give tester {items.BY[key]["give"][1]} {n}')
c('fill 590 90 -8 618 90 8 minecraft:stone'); c('fill 590 91 -8 618 100 8 minecraft:air')
freeze = lambda x=606.5, z=0.5: (c(f'tp {B(1)} {x} 91 {z}'), c(f'scoreboard players set {B(1)} bw.st 9'), c(f'scoreboard players set {B(1)} bw.pst 9'), c(f'data modify entity {B(1)} Health set value 40f'))
c('tp tester 600.5 91 0.5 -90 0'); freeze(); time.sleep(1.0); b.look(-90, 0)
# ---- A. bedbug
c('clear tester'); print('give bedbug:', give('bedbug', 2)[:30]); b.slot(0); time.sleep(0.4); b.look(-90, -5); time.sleep(0.2); b.use(); time.sleep(0.3)
print('  ball:', c('execute if entity @e[type=snowball,tag=bw.bugball]')[:12], 'rider:', c('execute if entity @e[type=marker,tag=bw.bugm]')[:12]); time.sleep(1.2)
S = '@e[type=silverfish,tag=bw.bug,limit=1]'
print('  bug:', pos(S), 'team', sc(S, 'bw.team'), 'life', sc(S, 'bw.life'), 'name', c(f'data get entity {S} CustomName')[-40:], '| bot hp', hpb())
time.sleep(3.0); print('  3 s later: bug', pos(S), 'bot', pos(B(1)), 'bot hp', hpb(), 'lh', sc(B(1), 'bw.lh'), 'tester hp', c('data get entity tester Health').split()[-1])
time.sleep(12.5); print('  after 17 s: bug alive?', c('execute if entity @e[type=silverfish,tag=bw.bug]')[:12], '| bot st', sc(B(1), 'bw.st'))
# ---- B. dream defender
freeze(); c('clear tester'); print('give golem:', give('golem')[:34]); b.slot(0); time.sleep(0.4); place(602, 90, 0); time.sleep(0.6)
G = '@e[type=iron_golem,tag=bw.golem,limit=1]'
print('  golem:', pos(G), 'team', sc(G, 'bw.team'), 'life', sc(G, 'bw.life'), 'name', c(f'data get entity {G} CustomName')[-60:], 'dmg', c(f'attribute {G} minecraft:attack_damage base get')[-5:])
h0 = hpb(); time.sleep(4.0); print('  4 s later: golem', pos(G), 'bot', pos(B(1)), 'bot hp', h0, '->', hpb(), 'lh', sc(B(1), 'bw.lh'), 'tester hp', c('data get entity tester Health').split()[-1], 'chat', b.chat[-2:])
time.sleep(1.5); print('  name now', c(f'data get entity {G} CustomName')[-30:]); c(f'scoreboard players set {G} bw.life 2'); time.sleep(0.5); print('  expired:', c('execute if entity @e[type=iron_golem]')[:12], 'drops', c('execute if entity @e[type=item,distance=..40]')[:12])
# ---- C. magic milk
c('clear tester'); print('give milk:', give('milk')[:30]); b.slot(0); time.sleep(0.4); b.use(); time.sleep(2.2)
print('  milk score', sc('tester', 'bw.milk'), 'bucket left', count('bucket'), 'night vision', 'night_vision' in c('data get entity tester active_effects'), b.chat[-1:])
# ---- D. pop-up tower
c('tp tester 600.5 91 -5.5 -90 40'); time.sleep(0.8); b.look(-90, 40); c('clear tester'); print('give tower:', give('tower')[:30]); b.slot(0); time.sleep(0.4)
place(602, 90, -6); time.sleep(0.3); print('  chest placed:', is_(602, 91, -6, 'minecraft:chest'), 'used', sc('tester', 'bw.usedchest')); time.sleep(1.6)
def col(x, z): return ''.join('W' if is_(x, y, z, 'minecraft:red_wool') else 'L' if is_(x, y, z, 'minecraft:ladder') else '.' if is_(x, y, z, 'minecraft:air') else '?' for y in range(91, 99))
print('  chest gone:', is_(602, 91, -6, 'minecraft:air'), '| door column (602,-6):', col(602, -6), '| far wall (606,-6):', col(606, -6), '| ladder (605,-6):', col(605, -6), '| side (604,-8):', col(604, -8), '| rim (601,-6):', col(601, -6), '| centre (604,-6):', col(604, -6))
print('  ladder state:', c('execute if block 605 91 -6 minecraft:ladder[facing=west]')[:12], '| marker left:', c('execute if entity @e[type=marker,tag=bw.tower]')[:12])
for y in (91, 96, 97):
    print('   y', y, ' '.join(''.join('W' if is_(x, y, z, 'minecraft:red_wool') else 'L' if is_(x, y, z, 'minecraft:ladder') else '.' for x in range(600, 609)) for z in range(-10, -2)))
print(errors()[-300:]); b.close()
