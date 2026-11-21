import sys, time; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
stage = int(sys.argv[1]) if len(sys.argv) > 1 else 8; mid = sys.argv[2] if len(sys.argv) > 2 else 'tea'; dur = int(sys.argv[3]) if len(sys.argv) > 3 else 150
c('function bw:game/close'); time.sleep(1)
b = join()
c(f'scoreboard players set tester bw.stage {stage}')
print('start took', start(mid, b), 's; lvl', sc('#lvl'), 'reach', sc('#a_reach'), 'acc', sc('#a_acc'), 'wait', sc('#a_wait'), 'def', sc('#a_def'))
c("gamemode spectator tester")
seen = 0; t0 = time.time(); last = {}
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
while time.time() - t0 < dur:
    time.sleep(10)
    line = []
    for i in range(1, 8):
        p = pos(B(i))
        if not p: line.append(f'{i}:dead'); continue
        st = sc(B(i), 'bw.st'); hp = sc(B(i), 'bw.hp'); at = c(f'data get storage bw:bot at{i}').split('"')[1]; to = c(f'data get storage bw:bot to{i}').split('"')[1] if '"' in c(f'data get storage bw:bot to{i}') else '-'
        moved = '' if last.get(i) is None else f'{abs(p[0]-last[i][0]) + abs(p[2]-last[i][2]):.0f}'
        last[i] = p
        line.append(f'{i}:s{st} {at}>{to} hp{hp} ({p[0]:.0f},{p[1]:.0f},{p[2]:.0f}) m{moved} fe{sc(f"#wfe{i}")} sw{sc(f"#bsw{i}")} stk{sc(B(i), "bw.stuck")}')
    print(f'[{time.time() - t0:4.0f}s] sec {sc("#sec")} beds {"".join(str(sc(f"#bed{i}")) for i in range(8))} out {"".join(str(sc(f"#out{i}")) for i in range(8))} state {sc("#state")}')
    for l in line: print('     ', l)
    for m in b.chat[seen:]: print('   CHAT', m[:150])
    seen = len(b.chat)
    if sc('#state') != 3: break
print('tester hp', c('data get entity tester Health'), 'coins', sc('tester', 'bw.coins'), 'wool blocks placed:', c('execute if entity @e[type=item,nbt={Item:{id:"minecraft:blue_wool"}}]'))
print(errors()); b.close()
