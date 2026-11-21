import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
what = sys.argv[1]
if what == 'hint':
    c('function bw:game/close'); time.sleep(1)
    b = join(); c('scoreboard players set tester bw.stage 0')
    print('start', start('tea', b), 'state', sc('#state'))
    time.sleep(1); h = pos('@e[type=villager,tag=bw.npc.hint,limit=1]'); print('hint npc at', h)
    c('effect give tester minecraft:resistance 60 4 true')
    c(f'tp tester {h[0] + 1.5} {h[1]} {h[2]}'); time.sleep(3.0)
    eid = b.find('villager', h[0], h[1], h[2], 1.0); n0 = len(b.chat)
    if eid: b.interact(eid)
    time.sleep(1.0); print('   click', eid, b.chat[n0:])
    print(errors()); b.close()
if what == 'reload':
    c('function bw:game/close'); time.sleep(1)
    b = join(); c('scoreboard players set tester bw.stage 3')
    print('start', start('tea', b), 'state', sc('#state'), 'bots', len(bots()))
    time.sleep(4); print(c('reload')); time.sleep(4)
    print('after /reload: state', sc('#state'), 'bots', len(bots()), 'pos', pos('tester'), 'play tag', 'bw.play' in c('tag tester list'), 'mode', c('data get entity tester playerGameType')[-3:])
    print(errors()); b.close()
if what == 'quit1':   # a round is on, the player leaves, the world is closed
    c('function bw:game/close'); time.sleep(1)
    b = join(); c('scoreboard players set tester bw.stage 3'); c('scoreboard players set tester bw.coins 77')
    print('start', start('tea', b), 'state', sc('#state'), 'bots', len(bots()), 'pos', pos('tester'))
    time.sleep(5); b.close(); time.sleep(1); print('left; state', sc('#state'))
if what == 'quit2':   # the world is open again
    print('state at once', sc('#state')); time.sleep(3); print('state after 3 s', sc('#state'), 'bots', len(bots()))
    b = join(); time.sleep(3)
    print('back: state', sc('#state'), 'pos', pos('tester'), 'play tag', 'bw.play' in c('tag tester list'), 'mode', c('data get entity tester playerGameType')[-3:], 'coins', sc('tester', 'bw.coins'), 'inv', inv()[:6])
    print('new round start', start('tea', b), 'state', sc('#state'), 'bots', len(bots()))
    print(errors()); b.close()
