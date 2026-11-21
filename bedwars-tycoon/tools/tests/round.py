import sys, time, re; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0'); c('scoreboard players set tester bw.coins 0')
print('start', start('tea', b)); time.sleep(1)
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
hp = lambda: float(c('data get entity tester Health').split()[-1].rstrip('f'))
# --- A: stand next to bot 1 at its forge
p = pos(B(1)); print('bot1 at', p, 'st', sc(B(1), 'bw.st'))
c(f'tp tester {p[0] + 1.5} {p[1]} {p[2]}'); time.sleep(4)
print('A after 4s: tester hp', hp(), 'bot st', sc(B(1), 'bw.st'), 'lh', sc('tester', 'bw.lh'), 'lht', sc('tester', 'bw.lht'), 'bot pos', pos(B(1)), 'tester', pos('tester'))
# --- B: hit the bot
eid = None
for e, v in b.entities.items():
    if v[0] == 'mannequin' and abs(v[1] - p[0]) < 3 and abs(v[3] - p[2]) < 3: eid = e
print('eid', eid, 'mannequins known', sum(1 for v in b.entities.values() if v[0] == 'mannequin'))
h0 = sc(B(1), 'bw.hp')
for k in range(3):
    pp = pos(B(1)); c(f'tp tester {pp[0] + 1.2} {pp[1]} {pp[2]}'); time.sleep(0.3); b._send('play', 'attack', varint(eid)); time.sleep(0.6)
print('B: bot hp', h0, '->', sc(B(1), 'bw.hp'), 'bot lh', sc(B(1), 'bw.lh'), 'lht', sc(B(1), 'bw.lht'), 'st', sc(B(1), 'bw.st'))
# give the bot something to carry, then kill it with real hits
c('effect give tester minecraft:resistance 8 4 true'); c('scoreboard players set #wfe1 bw 7'); c('scoreboard players set #wau1 bw 2')
c(f'damage {B(1)} 17 minecraft:player_attack by tester'); time.sleep(0.2)
pp = pos(B(1)); 
if pp: c(f'tp tester {pp[0] + 1.2} {pp[1]} {pp[2]}'); time.sleep(0.6); b._send('play', 'attack', varint(eid)); time.sleep(0.7); b._send('play', 'attack', varint(eid)); time.sleep(1.0)
print('   bot1 alive?', pos(B(1)), 'bres1', sc('#bres1'), 'gk', sc('tester', 'bw.gk'), 'coins', sc('tester', 'bw.coins'), 'iron', count('iron_ingot'), 'gold', count('gold_ingot'))
print('   chat', [m.strip()[:70] for m in b.chat[-4:]])
c('tp tester 656.5 65 -23.5'); time.sleep(5.5); print('   respawned?', pos(B(1)), 'bres1', sc('#bres1'), 'sword tier', sc('#bsw1'))
# --- player death and respawn
c('tp tester 656.5 65 -23.5'); time.sleep(0.3); c('scoreboard players set tester bw.pick 2'); c('give tester minecraft:iron_ingot 5')
c('kill tester'); time.sleep(1.0)
print('C: dead: mode', c('data get entity tester playerGameType')[-3:], 'resp', sc('tester', 'bw.resp'), 'pos', pos('tester'), 'iron', count('iron_ingot'), 'pick', sc('tester', 'bw.pick'))
time.sleep(5.2); print('   respawn: mode', c('data get entity tester playerGameType')[-3:], 'pos', pos('tester'), 'inv', inv(), 'hp', hp())
# --- break an enemy bed as the player (team 1's bed), standing next to it
bed = c('data get storage bw:nav tea.bed1'); m = re.findall(r'(-?[\d.]+)d', bed); bx, by, bz = float(m[0]), float(m[1]), float(m[2])
c(f'tp tester {bx + 1.5} {by} {bz}'); time.sleep(0.5); print('   fill', c(f'fill {int(bx) - 2} {int(by)} {int(bz) - 2} {int(bx) + 2} {int(by)} {int(bz) + 2} minecraft:air replace #minecraft:beds')[:40]); time.sleep(0.8)
print('D: bed1', sc('#bed1'), 'gb', sc('tester', 'bw.gb'), 'coins', sc('tester', 'bw.coins'), [m.strip()[:60] for m in b.chat[-3:]])
# --- own bed: breaking it puts it back
c('tp tester 648.5 65 -23.5'); time.sleep(0.4); print('   fill', c('fill 644 65 -25 648 65 -21 minecraft:air replace #minecraft:beds')[:40]); time.sleep(0.8)
print('E: own bed', sc('#bed0'), c('execute if block 646 65 -23 #minecraft:beds')[:11], [m.strip()[:60] for m in b.chat[-2:]])
# --- void
c('tp tester 600 40 100'); time.sleep(1.5); print('F: void death resp', sc('tester', 'bw.resp'), c('data get entity tester playerGameType')[-3:])
# --- win: every other team out
time.sleep(5.5)
for i in range(1, 8): c(f'scoreboard players set #bed{i} bw 0'); c(f'kill {B(i)}')
c('tp @e[type=mannequin,tag=bw.bot] 0 -400 0'); time.sleep(0.5)
for i in range(1, 8): c(f'scoreboard players set #bres{i} bw 0')
time.sleep(2.5)
print('G: state', sc('#state'), 'alive', sc('#alive'), 'coins', sc('tester', 'bw.coins'), 'stage', sc('tester', 'bw.stage'), 'wins', sc('tester', 'bw.wins'), [m.strip()[:50] for m in b.chat[-5:]])
time.sleep(9); print('   after close: state', sc('#state'), 'pos', pos('tester'), 'mode', c('data get entity tester playerGameType')[-3:], 'border', c('worldborder get')[-25:], 'forceload', c('forceload query')[:60])
print(errors()); b.close()
