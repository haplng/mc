# a bot's dream defender and bedbug against the player
import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
c('fill 596 90 -4 612 90 4 minecraft:stone'); c('fill 596 91 -4 612 96 4 minecraft:air')
c('tp tester 603.5 91 0.5 -90 0'); time.sleep(0.6); b._send('play', 'move_player_status_only', bytes([1])); b._send('play', 'client_tick_end')
hp = lambda: float(re.search(r'(-?[\d.]+)f', c('data get entity tester Health')).group(1))
# the golem of team 2, three blocks from the player
c(f'execute as {B(2)} positioned 607.5 91 0.5 run function bw:mob/botgolem'); time.sleep(0.5)
G = '@e[type=iron_golem,tag=bw.golem,limit=1]'
print('golem:', pos(G), 'team', sc(G, 'bw.team'), 'name', re.findall(r'text: "([^"]*)"', c(f'data get entity {G} CustomName'))[:2], 'dmg', c(f'attribute {G} minecraft:attack_damage get')[-5:],
      'head', c(f'data get entity {G} equipment.head.components')[-40:])
h0 = hp(); t0 = time.time()
while time.time() - t0 < 8 and hp() >= h0: time.sleep(0.25); b._send('play', 'move_player_status_only', bytes([1])); b._send('play', 'client_tick_end')
print(f'  player hp {h0} -> {hp()} after {time.time() - t0:.1f} s; golem now at', pos(G), 'angry at', c(f'data get entity {G} angry_at')[-50:], '| lh', sc('tester', 'bw.lh'), 'lht', sc('tester', 'bw.lht'))
c(f'kill {G}'); c('effect give tester minecraft:instant_health 1 5 true'); time.sleep(0.5)
# a bedbug of team 2
c(f'summon minecraft:marker 606.5 91.2 0.5 {{Tags:["bw","bw.round","tbug"]}}'); c('scoreboard players set @e[type=marker,tag=tbug] bw.team 2'); c('tag @e[type=marker,tag=tbug] add bw.bugm'); time.sleep(0.6)
S = '@e[type=silverfish,tag=bw.bug,limit=1]'
print('bedbug:', pos(S), 'team', sc(S, 'bw.team'), 'name', re.findall(r'text: "([^"]*)"', c(f'data get entity {S} CustomName'))[:1])
h0 = hp(); t0 = time.time()
while time.time() - t0 < 8 and hp() >= h0: time.sleep(0.25); b._send('play', 'move_player_status_only', bytes([1])); b._send('play', 'client_tick_end')
print(f'  player hp {h0} -> {hp()} after {time.time() - t0:.1f} s; bug at', pos(S)); time.sleep(12)
print('  after 15 s: bug alive?', c(f'execute if entity {S}')[:11])
print(errors()[-200:]); c('function bw:game/close'); time.sleep(1); b.close()
