# the end game without a player in it: beds gone at 30:00, dragons at 40:00, and how the bots fare under them
import sys, time, re, math, json; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]); mid = sys.argv[2]
c('function bw:game/close'); time.sleep(1)
b = join(); c(f'scoreboard players set tester bw.stage {stage}')
print(mid, 'stage', stage, 'start', start(mid, b)); time.sleep(0.5); c('gamemode spectator tester')
for i in (1, 2, 4): c(f'scoreboard players set #dbuff{i} bw 1')
time.sleep(40); c('scoreboard players set #sec bw 1797'); time.sleep(5)
print('30:00 -> beds', ''.join(str(sc(f'#bed{i}')) for i in range(8)), [m[:40] for m in b.chat[-2:]])
c('scoreboard players set #sec bw 2397'); time.sleep(5)
D = '@e[type=ender_dragon,tag=bw.dragon]'
print('40:00 -> sudden', sc('#sudden'), 'dragons', c(f'execute if entity {D}')[-10:], 'griefing', c('gamerule mob_griefing')[-5:])
t0 = time.time(); seen = len(b.chat); mspt = []
while time.time() - t0 < 150 and sc('#state') == 3:
    time.sleep(10)
    m = re.search(r'Average time per tick: ([\d.]+)', c('tick query')); mspt.append(float(m.group(1)) if m else 0)
    out = ''.join(str(sc(f'#out{i}')) for i in range(8))
    print(f'  +{time.time() - t0:3.0f}s out {out} bots {len(bots())} dragons {c(f"execute if entity {D}")[-9:].strip()} mspt {mspt[-1]}', [m_[:44] for m_ in b.chat[seen:] if '처치' in m_ or '탈락' in m_ or '죽' in m_][-3:])
    seen = len(b.chat)
print('END state', sc('#state'), 'sec', sc('#sec'), 'mspt max', max(mspt or [0]), 'dragons left', c(f'execute if entity @e[type=ender_dragon]')[-12:], [m[:50] for m in b.chat[-4:]])
time.sleep(10); print('10 s later: state', sc('#state'), 'dragons', c('execute if entity @e[type=ender_dragon]')[-12:], 'griefing', c('gamerule mob_griefing')[-5:])
print(errors()[-300:]); c('function bw:game/close'); b.close()
