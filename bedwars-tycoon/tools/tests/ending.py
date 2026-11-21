import sys, time, re, math, struct; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
sys.path.insert(0, '/home/claude/bw/gen3'); import items
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0'); c('scoreboard players set tester bw.coins 0')
print('start', start('tea', b)); time.sleep(1.0)
def bpos(x, y, z): return struct.pack('>Q', ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF))
seq = [300]
def dig(x, y, z, secs):
    seq[0] += 1; b._send('play', 'player_action', varint(0) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(secs)
    seq[0] += 1; b._send('play', 'player_action', varint(3) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(0.5)
bed = re.findall(r'(-?[\d.]+)d', c('data get storage bw:nav tea.bed1')); bx, by, bz = math.floor(float(bed[0])), math.floor(float(bed[1])), math.floor(float(bed[2]))
c('effect give tester minecraft:resistance infinite 4 true'); c(f'tp tester {bx + 0.5} {by} {bz + 2.5} 180 30'); time.sleep(1.5); b.slot(0); time.sleep(0.3)
cells = [(x, by, z) for x in (bx - 1, bx, bx + 1) for z in (bz - 1, bz, bz + 1) if 'passed' in c(f'execute if block {x} {by} {z} #minecraft:beds')]
print('holding', c('data get entity tester SelectedItem.id')[-26:], 'bed cells', cells)
n0 = len(b.chat); dig(*cells[0], 1.2); print('break enemy bed with the kit sword:', sc('#bed1'), 'gb', sc('tester', 'bw.gb'), 'coins', sc('tester', 'bw.coins'), [m.strip()[:40] for m in b.chat[n0:]])
print('   bed item entities left:', c(f'execute positioned {bx} {by} {bz} if entity @e[type=item,distance=..6]')[:22])
# own bed
ob = re.findall(r'(-?[\d.]+)d', c('data get storage bw:nav tea.bed0')); ox, oy, oz = math.floor(float(ob[0])), math.floor(float(ob[1])), math.floor(float(ob[2]))
c(f'tp tester {ox + 0.5} {oy} {oz + 2.5} 180 30'); time.sleep(1.5)
cells = [(x, oy, z) for x in (ox - 1, ox, ox + 1) for z in (oz - 1, oz, oz + 1) if 'passed' in c(f'execute if block {x} {oy} {z} #minecraft:beds')]
n0 = len(b.chat); dig(*cells[0], 1.2); time.sleep(0.5); print('own bed:', sc('#bed0'), 'still there', all('passed' in c(f'execute if block {x} {y} {z} #minecraft:beds') for x, y, z in cells), [m.strip()[:40] for m in b.chat[n0:]])
# ending + giving up
c('function bw:game/close'); time.sleep(1.5); c('scoreboard players set #goal bw 500'); c('scoreboard players set tester bw.coins 600'); n0 = len(b.chat); time.sleep(1.6)
print('ending:', 'bw.ended' in c('tag tester list'), [m.strip()[:60] for m in b.chat[n0:]]); c('scoreboard players set #goal bw 10000'); c('tag tester remove bw.ended')
print('start again', start('tea', b)); time.sleep(1.0); b.command('trigger lobby'); time.sleep(1.5); print('give up via /trigger lobby: state', sc('#state'), 'pos', pos('tester'), [m.strip()[:40] for m in b.chat[-2:]])
print(errors()); b.close()
