import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0'); c('scoreboard players set tester bw.coins 0')
print('start', start('tea', b)); time.sleep(1)
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
def setk(**kw):
    for k, v in kw.items(): c(f'scoreboard players set tester bw.h_{k} {v}')
    c('execute as tester run function bw:hack/apply')
rot = lambda: c('data get entity tester Rotation')[-24:]
c('effect give tester minecraft:resistance infinite 4 true')
# a quiet arena: a platform far from the bots (inside the border), with one captive bot
c('fill 596 90 -4 612 90 4 minecraft:stone'); c('fill 596 91 -4 612 96 4 minecraft:air')
c(f'tp {B(1)} 606.5 91 0.5'); c('tp tester 603.5 91 0.5 -90 0'); time.sleep(0.5)
c('item replace entity tester weapon.mainhand with minecraft:stone_sword'); c(f'scoreboard players set {B(1)} bw.st 9'); c(f'scoreboard players set {B(1)} bw.pst 9')
freeze = lambda: (c(f'tp {B(1)} 606.5 91 0.5'), c(f'scoreboard players set {B(1)} bw.st 9'), c(f'scoreboard players set {B(1)} bw.pst 9'), c(f'data modify entity {B(1)} Health set value 40f'))
# ---- reach / velocity / nofall numbers
setk(reach=2, lag=1, velocity=2, nofall=1)
print('attr: range', c('attribute tester minecraft:entity_interaction_range get')[-5:], 'kb', c('attribute tester minecraft:knockback_resistance get')[-5:], 'fall', c('attribute tester minecraft:fall_damage_multiplier get')[-5:], 'hreach', sc('tester', 'bw.hreach'))
setk(velocity2=1); print('  velocity2: kb', c('attribute tester minecraft:knockback_resistance get')[-5:])
# ---- AutoClicker: looking straight at the bot 3 blocks away
freeze(); b.look(-90, 0); setk(clicker=1); time.sleep(1.2)
print('autoclicker: bot hp', sc(B(1), 'bw.hp'), 'lh', sc(B(1), 'bw.lh'), 'bot st', sc(B(1), 'bw.st'))
freeze(); b.look(-40, 0); time.sleep(0.2); h0 = sc(B(1), 'bw.hp'); time.sleep(1.0); print('   looking away: hp', h0, '->', sc(B(1), 'bw.hp'))
setk(clicker=0)
# ---- Aim assist normal: crosshair 20 degrees off drifts on to the bot
freeze(); b.look(-70, 0); time.sleep(0.1); r0 = rot(); setk(aim=1); time.sleep(1.0); print('aim normal: rot', r0, '->', rot())
# ---- silent: the sword gets a wide attack range
setk(aim=2); time.sleep(0.4); print('aim silent: sword', c('data get entity tester SelectedItem.components')[-90:])
setk(aim=0); time.sleep(0.4); print('   off: sword', c('data get entity tester SelectedItem')[-70:])
# ---- AutoBlock: the bot's blows land softer
def bot_hits(n=4):
    c('data modify entity tester Health set value 20f'); c('effect clear tester minecraft:resistance'); time.sleep(0.1)
    for _ in range(n):
        c(f'execute as {B(1)} at @s run tag tester add bw.foe'); c(f'scoreboard players set #a_acc bw 100'); c(f'execute as {B(1)} at @s run function bw:ai/swing'); time.sleep(0.6)
    hp = float(c('data get entity tester Health').split()[-1].rstrip('f')); c('effect give tester minecraft:resistance infinite 4 true'); return hp
freeze(); print('bot hits x4, no autoblock: hp', bot_hits()); setk(block=2); freeze(); print('   with Lag block: hp', bot_hits()); setk(block=0)
# ---- Knockback Displace: the bot flies sideways (90degree) when struck
from bot import varint
def strike():
    freeze(); time.sleep(0.3); eid = [e for e, v in b.entities.items() if v[0] == 'mannequin']; 
    p0 = pos(B(1)); 
    for e in eid: b._send('play', 'attack', varint(e))
    time.sleep(0.12); m = c(f'data get entity {B(1)} Motion')[-70:]; time.sleep(0.7); return p0, pos(B(1)), m
print('plain hit: ', strike()); setk(kbd=1); print('kbd 90degree:', strike()); setk(kbd=0)
# ---- TP Aura: the bot is 9 blocks away
c('tp tester 597.5 91 0.5 -90 0'); freeze(); setk(tpaura=1); time.sleep(1.0); print('tpaura: tester', pos('tester'), 'bot hp', sc(B(1), 'bw.hp')); setk(tpaura=0)
# ---- Scaffold: standing past an edge with wool in the pack
c('clear tester'); c('give tester minecraft:red_wool 8'); c('tp tester 612.9 91 0.5 -90 0'); time.sleep(0.2); b.look(-90, 0); time.sleep(0.2)
c('tp tester 613.6 91 0.5 -90 0'); b.look(-90, 0); time.sleep(0.2); print('no scaffold: block under', c('execute if block 613 90 0 minecraft:red_wool')[:11])
setk(scaffold=1); b.look(-90, 0); time.sleep(0.4); print('scaffold: block under', c('execute if block 613 90 0 minecraft:red_wool')[:11], 'wool left', count('red_wool'))
# ---- Tower: jump held, standing still
setk(tower=2); b._send('play', 'player_input', bytes([0x10])); time.sleep(0.5); print('tower: levitation', 'levitation' in c('data get entity tester active_effects'), 'tag', 'bw.lev' in c('tag tester list'))
b._send('play', 'player_input', bytes([0])); time.sleep(0.3); print('   released: levitation', 'levitation' in c('data get entity tester active_effects')); setk(tower=0, scaffold=0)
# ---- Eagle: with a block in the hand, stepping past the edge puts you back
c('item replace entity tester weapon.mainhand with minecraft:red_wool 4'); c('fill 613 90 0 613 90 0 minecraft:air'); setk(eagle=2)
c('tp tester 612.5 91 2.5 -90 0'); b.look(-90, 0); time.sleep(0.3); c('tp tester 613.2 91 2.5'); b.look(-90, 0); time.sleep(0.4); print('eagle: stepped to 613.2 ->', pos('tester'), 'speed mod', c('attribute tester minecraft:movement_speed get')[-6:])
c('tp tester 612.8 91 2.5'); b.look(-90, 0); time.sleep(0.3); print('   near the edge: speed', c('attribute tester minecraft:movement_speed get')[-7:]); setk(eagle=0)
# ---- Stasis: falling near the void
vy = 64 - 13 - 6 + 4; setk(stasis=1); c(f'tp tester 600.5 {vy} 40.5'); b._send('play', 'move_player_status_only', bytes([0])); time.sleep(0.4)
print('stasis: levitation', 'levitation' in c('data get entity tester active_effects'), 'cooldown', sc('tester', 'bw.stc'), 'alive mode', c('data get entity tester playerGameType')[-2:])
c('tp tester 603.5 91 0.5 -90 0'); setk(stasis=0)
# ---- fireball: thrown at a wool wall with end stone behind; FB longjump when looking down
c('fill 608 91 -3 608 94 3 minecraft:red_wool'); c('fill 609 91 -3 609 94 3 minecraft:end_stone'); c('fill 610 91 -3 610 92 3 minecraft:white_concrete')
c(f'tp {B(1)} 600.5 91 3.5'); c('clear tester'); print(c('give tester minecraft:carrot_on_a_stick[!minecraft:max_damage,!minecraft:damage,item_model="minecraft:fire_charge",max_stack_size=64,custom_data={bw:"fireball"}] 3')[:30])
b.slot(0); b.look(-90, 0); time.sleep(0.3); b.use(); time.sleep(0.25); print('fireball: entity', c('execute if entity @e[type=fireball,tag=bw.fb]')[:14], 'marker', c('execute if entity @e[type=marker,tag=bw.fbm]')[:14]); time.sleep(1.5)
cnt = lambda blk, x: int((re.search(r'filled (\d+)', c(f'fill {x} 91 -3 {x} 94 3 minecraft:barrier replace minecraft:{blk}')) or [0, 0])[1])
w = cnt('red_wool', 608); c('fill 608 91 -3 608 94 3 minecraft:red_wool replace minecraft:barrier'); e = cnt('end_stone', 609); c('fill 609 91 -3 609 94 3 minecraft:end_stone replace minecraft:barrier')
print('   after boom: wool left', w, 'of 28, end stone left', e, 'of 28, fireballs left', count('carrot_on_a_stick'), 'fb entities', c('execute if entity @e[type=fireball]')[:14])
setk(fbjump=1); b.look(-90, 70); time.sleep(0.2); b.use(); time.sleep(0.3); print('fb longjump: fireballs left', count('carrot_on_a_stick'), 'no projectile', c('execute if entity @e[type=fireball]')[:14], b.chat[-1:]); setk(fbjump=0)
# ---- TNT
c('fill 606 91 0 606 91 0 minecraft:tnt'); b.look(-90, 20); c('tp tester 603.5 91 0.5 -90 20'); time.sleep(0.2); c('scoreboard players set tester bw.tnt 1'); time.sleep(0.3)
print('tnt: primed', c('execute if entity @e[type=tnt]')[:14], 'block gone', c('execute if block 606 91 0 minecraft:air')[:11]); time.sleep(3.0)
w = cnt('red_wool', 608); c('fill 608 91 -3 608 94 3 minecraft:red_wool replace minecraft:barrier'); e = cnt('end_stone', 609); c('fill 609 91 -3 609 94 3 minecraft:end_stone replace minecraft:barrier'); q_ = cnt('white_concrete', 610)
print('   after tnt: wool left', w, 'end stone left', e, 'concrete left', q_, 'of 14; stone floor intact', c('execute if block 606 90 0 minecraft:stone')[:11])
# ---- bridge egg
c('summon minecraft:snowball 603.5 93 -6.5 {Motion:[0.9d,0.25d,0d],Item:{id:"minecraft:snowball",count:1,components:{"minecraft:custom_data":{bw:"egg"}}}}'); time.sleep(2.0)
print('egg: wool trail', c('fill 600 85 -9 630 95 -4 minecraft:barrier replace minecraft:red_wool')[:40])
print(errors()); b.close()
