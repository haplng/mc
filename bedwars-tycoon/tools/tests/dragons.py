# sudden death: dragons
import sys, time, re, math, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
c('scoreboard players set #dbuff0 bw 1'); c('scoreboard players set #sec bw 2398'); time.sleep(2.5)
D = '@e[type=ender_dragon,tag=bw.dragon]'
n = c(f'execute if entity {D}'); print('sudden', sc('#sudden'), 'dragons:', n[-12:], 'mob_griefing', c('gamerule mob_griefing')[-6:], b.chat[-1:])
teams = re.findall(r'has (\d+) \[bw\]', c(f'execute as {D} run scoreboard players get @s bw.team')) ; print('  teams of the dragons', sorted(teams))
print('  helmet:', c('data get entity tester equipment.head.components')[:160])
print('  names:', re.findall(r'text: "([^"]*)"', c(f'execute as {D} run data get entity @s CustomName'))[:9])
red = '@e[type=ender_dragon,tag=bw.dragon,scores={bw.team=0},limit=1]'; blue = '@e[type=ender_dragon,tag=bw.dragon,scores={bw.team=1},limit=1]'
blocks0 = c('execute store result score #n bw run clone 532 51 -68 668 81 68 532 51 -68 filtered minecraft:air force') if False else None
for k in range(10):
    time.sleep(2.0)
    print(f'  {2 * (k + 1):2d}s red dragon', pos(red), 'phase', sc(red, 'bw.dph'), '| blue', pos(blue), '| tester', pos('tester'), 'hp', c('data get entity tester Health').split()[-1], 'mode', c('data get entity tester playerGameType')[-2:], '| bots', len(bots()), '| mspt', c('tick query')[:0] or re.search(r'Average time per tick: ([\d.]+)', c('tick query')).group(1))
print('  chat', [m[:60] for m in b.chat[-6:]])
# what the dragons have eaten: map blocks that are gone (compare with the copy)
print(errors()[-400:])
c('function bw:game/close'); time.sleep(1.5); print('after close: dragons', c('execute if entity @e[type=ender_dragon]')[:12], 'mob_griefing', c('gamerule mob_griefing')[-6:], 'state', sc('#state'))
b.close()
