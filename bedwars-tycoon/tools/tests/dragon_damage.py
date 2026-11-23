# sudden death: who the dragons hurt
import sys, time, re; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
c('scoreboard players set #sec bw 2398'); time.sleep(2.5)
D = 'type=ender_dragon'
print('dragons per team:', re.findall(r'has (\d+) \[bw\.team\]', c(f'execute as @e[{D},tag=bw.dragon] run scoreboard players get @s bw.team')))
c(f'tag @e[{D}] remove bw.dragon')          # nobody drives them any more: they hover where they are
c('effect clear tester'); c('effect give tester minecraft:instant_health 1 5 true')
def hp(sel): 
    m = re.search(r'(-?[\d.]+)f', c(f'data get entity {sel} Health')); return float(m.group(1)) if m else None
def head_on(team, sel):
    """put the head of this team's dragon on the entity for a second and a half; what it costs"""
    d = f'@e[{D},scores={{bw.team={team}}},limit=1]'
    c(f'tp {d} 600 140 0'); time.sleep(0.3); h0 = hp(sel)
    for k in range(6):
        c(f'execute at {sel} run tp {d} ~ ~-0.5 ~6.5 0 0'); time.sleep(0.25)
    h1 = hp(sel); c(f'tp {d} 600 140 0'); return h0, h1
# the tester stands on a block high above the middle, alone
c('setblock 600 89 30 minecraft:obsidian'); c('tp tester 600.5 90 30.5'); time.sleep(0.6); b.status() if hasattr(b, 'status') else None
print('tester (red) under the red dragon :', head_on(0, 'tester'))
print('tester (red) under the blue dragon:', head_on(1, 'tester'), b.chat[-1:])
c('effect give tester minecraft:instant_health 1 5 true')
B1 = '@e[type=mannequin,tag=bw.bot,scores={bw.team=1},limit=1]'; B2 = '@e[type=mannequin,tag=bw.bot,scores={bw.team=2},limit=1]'
print('blue bot under the blue dragon:', head_on(1, B1))
print('lime bot under the blue dragon:', head_on(1, B2))
print('lime bot under the red dragon :', head_on(0, B2), [m[:50] for m in b.chat[-3:]])
print(errors()[-300:])
c('function bw:game/close'); time.sleep(1.5); c('setblock 600 89 30 minecraft:air'); b.close()
