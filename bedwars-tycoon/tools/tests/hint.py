import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state'))
time.sleep(1); h = pos('@e[type=villager,tag=bw.npc.hint,limit=1]'); print('hint npc at', h)
c('effect give tester minecraft:resistance 60 4 true')
c(f'tp tester {h[0] + 1.5} {h[1]} {h[2]}')
t0 = time.time(); eid = None
while time.time() - t0 < 10 and not eid:
    time.sleep(0.5); b._send('play', 'move_player_status_only', bytes([1]))   # a real client reports its position all the time; that is what makes the server send the entities around
    eid = b.find('villager', h[0], h[1], h[2], 1.5)
print('seen after', round(time.time() - t0, 1), eid)
for k in range(2):
    n0 = len(b.chat); b.interact(eid); time.sleep(1.2); print('   click', k, b.chat[n0:], b.sounds[-2:])
print(errors()); c('function bw:game/close'); time.sleep(1); b.close()
