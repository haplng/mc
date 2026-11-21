"""Version 2 systems: aiming and throwing, the mount, Steve's distractions, lucky boxes and the action-bar HUD.

Everything here exists to make a run less scripted:
  * aimed cards land where the player looks, after a short flight, and only work when they land close to Steve
  * Steve walks at a different pace every time and now and then stops to fiddle with something (any card is a sweet spot then)
  * lucky boxes drop at random places and are opened by looking at them and right-clicking
  * the giant rides an invisible mount, so walking round the table is several times faster
"""
from core import *

V2_SCORES = ('drop', 'dropt', 'dcard', 'dcost', 'idle', 'idlek', 'wild', 'lucky', 'box', 'boxlife', 'npt', 'cur', 'lock',
             'near', 'moving', 'tier', 'nthrow', 'nhit', 'pace', 'aimed', 'am', 'amprev', 'idlecd', 'boxt', 'boxhint',
             'mod', 'ex', 'halt', 'dash', 'ddodge', 'noticed')
AIM = '@e[tag=ek.aim,limit=1]'
CUR = '@e[tag=ek.cur,limit=1]'
CURV = '@e[tag=ek.curv,limit=1]'
BOX = '@e[tag=ek.box,limit=1]'

# 26.3 form of "the player is holding the sneak key" (raw key state, so it stays true while the key is held even after a dismount)
SNEAK = ('predicate {type:"minecraft:entity_properties",entity:"this",'
         'predicate:{"minecraft:type_specific/player":{input:{sneak:true}}}}')
SADDLE = 'minecraft:stone_button[minecraft:equippable={slot:"saddle"}]'
# An invisible horse scaled so that its rider sits exactly as high as the giant stands (1.44375 * 6.65 = the giant's 9.6 ride offset).
# The stone button counts as a saddle (needed to steer) but has no saddle model, so nothing of the mount is ever drawn.
MOUNT = ('summon minecraft:horse ~ ~ ~ {Tags:["ek.mount","ek.mnew"],Tame:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,NoAI:1b,Health:1f,'
         'attributes:[{id:"minecraft:scale",base:6.65d},{id:"minecraft:movement_speed",base:0.35d},{id:"minecraft:jump_strength",base:0d},'
         '{id:"minecraft:max_health",base:1d},{id:"minecraft:step_height",base:0.6d}],'
         'equipment:{saddle:{id:"minecraft:stone_button",count:1,components:{"minecraft:equippable":{slot:"saddle"}}}},'
         'active_effects:[{id:"minecraft:invisibility",duration:-1,show_particles:0b,show_icon:0b}]}')

def tdx(tags, text, color, scale, extra=''):
    """A camera-facing label that shows through blocks (cursor, landing mark, box mark)."""
    tg = ','.join('"%s"' % a for a in tags)
    return ('summon minecraft:text_display ~ ~ ~ {Tags:[%s],billboard:"center",see_through:1b,background:0,line_width:400,view_range:4f,'
            'brightness:{sky:15,block:15},%s,text:{text:"%s",color:"%s",bold:true}%s}') % (tg, DISPLAY_T % (scale, scale, scale), text, color, extra)


def player(P):
    P.fn('player/init2', 'tag @s add ek.v2', 'team join ek @s',
         'tellraw @s ' + comp(t('  [새로워진 점]\n', 'yellow', True),
                              t('  · 이름에 ◎가 붙은 카드는 네가 바라보는 곳에 떨어져. 스티브를 잘 겨냥해서 던져.\n', 'white'),
                              t('  · 판 주위를 훨씬 빠르게 돌아다닐 수 있어. Shift를 누르고 있으면 가까이 당겨 보여.\n', 'white'),
                              t('  · 스티브가 가끔 딴짓을 하고, 판 위에 행운 상자가 떨어져. 자세한 건 로비 5번 칸 설명서.\n', 'white')))
    # Only adventure-mode players are put on the mount; someone who switched to creative or spectator to look around is left alone.
    P.fn('player/free',
         'execute on vehicle if entity @s[tag=ek.mount] on passengers run ride @s dismount',
         'execute at @s as @e[tag=ek.mount,distance=..16] run function ek:fx/vanish',
         'attribute @s minecraft:movement_speed base set 0.1')
    P.fn('player/tick',
         'execute if entity @s[gamemode=!adventure] run return run function ek:player/free',
         'scoreboard players set @s ek.rd 0',
         'execute on vehicle if entity @s[tag=ek.mount] on passengers run scoreboard players set @s ek.rd 1',
         'scoreboard players set @s ek.zm 0',
         'execute if %s run scoreboard players set @s ek.zm 1' % SNEAK,
         # Holding sneak: step off the mount on the spot (before the game does it and puts the rider down beside the mount)
         # and stand still with speed 0, which halves the field of view. Letting go puts the player back on the mount.
         'execute if score @s ek.zm matches 1 if score @s ek.rd matches 1 at @s run function ek:player/off',
         'execute if score @s ek.zm matches 1 run attribute @s minecraft:movement_speed base set 0',
         'execute unless score @s ek.zm matches 1 run attribute @s minecraft:movement_speed base set 0.1',
         'execute if score @s ek.zm matches 1 if score @s ek.rd matches 0 at @s at @e[tag=ek.mount,limit=1,sort=nearest,distance=0.6..16] run tp @s ~ ~ ~',
         'execute unless score @s ek.zm matches 1 if score @s ek.rd matches 0 at @s run function ek:player/mount',
         'execute if score @s ek.mh matches 1.. run function ek:player/mhint')
    # Getting on makes the game print "press sneak to dismount" over the hotbar; wipe it (in a run the HUD line simply returns).
    P.fn('player/mhint', 'scoreboard players remove @s ek.mh 1',
         unl('state', 1, 'title @s actionbar ""'), iff('state', 1, sset('abt', 0)))
    P.fn('player/off', 'ride @s dismount', 'tp @s ~ ~ ~')
    P.fn('player/mount',
         'execute unless entity @e[tag=ek.mount,distance=..16] run function ek:player/mount_new',
         # the mount comes to the player, never the other way round (a player moved by a command must not snap back)
         'tp @e[tag=ek.mount,limit=1,sort=nearest,distance=..16] ~ ~ ~',
         'ride @s mount @e[tag=ek.mount,limit=1,sort=nearest,distance=..16]', 'scoreboard players set @s ek.mh 3')
    P.fn('player/mount_new', MOUNT, 'team join ek @e[tag=ek.mnew]', 'tag @e[tag=ek.mnew] remove ek.mnew')
    # once a second: mounts nobody is near are removed, the "saddle" is put back if the player took it out, stray items go
    P.fn('player/fix',
         'execute as @e[tag=ek.mount] at @s unless entity @a[distance=..16] run function ek:fx/vanish',
         'item replace entity @e[tag=ek.mount] saddle with ' + SADDLE,
         'clear @a minecraft:stone_button', 'item replace entity @a weapon.offhand with minecraft:air')


def ui(P, pools):
    base = [t('스티브: ', 'gray'), st('status', 'white')]
    star = {'nbt': 'ab.star', 'storage': 'ek:s', 'color': 'aqua', 'bold': True}
    combo = {'nbt': 'ab.combo', 'storage': 'ek:s', 'color': 'gold'}
    P.fn('ui/tick', iff('abt', '1..', ssub('abt', 1)), 'execute as @a run function ek:ui/ab')
    P.fn('ui/ab',
         'execute store result score #sl ek run data get entity @s SelectedItemSlot', sset('hint', 0),
         [iff('stage', n, f'function ek:ui/hint_s{n}') for n in pools],
         'execute if score #sl ek matches ..5 if score #wild ek matches 1 run scoreboard players set #hint ek 2',
         'execute if score #sl ek matches ..5 if score #lucky ek matches 1 run scoreboard players set #hint ek 3',
         iff('intr', '1..', sset('hint', 0)),
         'data modify storage ek:s ab.star set value ""',
         iff('hint', 1, 'data modify storage ek:s ab.star set value "   ★ 지금이 노림수!"'),
         iff('hint', 2, 'data modify storage ek:s ab.star set value "   ★ 딴짓 중! 아무 카드나 노림수"'),
         iff('hint', 3, 'data modify storage ek:s ab.star set value "   ★ 행운! 다음 억까는 노림수"'),
         # am: what the cursor means for the card in hand (0 not an aimed card, 1 off the table, 2 far, 3 graze, 4 hit, 5 direct,
         # 6 a throw is in the air, 7 pointing at a lucky box)
         sset('aimed', 0), [iff('stage', n, f'function ek:ui/aim_s{n}') for n in pools],
         sset('am', 0), iff('aimed', 1, 'function ek:ui/aimstate'),
         'execute if entity @e[tag=ek.box,tag=ek.pick] run scoreboard players set #am ek 7',
         'execute unless score #am ek = #amprev ek run function ek:ui/curcolor',
         iff('abt', 0, 'function ek:ui/show'))
    P.fn('ui/aim_on', '$function $(f)', sset('aimed', 1))
    P.fn('ui/aimstate', sset('am', 1), iff('cur', 1, 'function ek:ui/aimtier'), iff('drop', 1, sset('am', 6)))
    P.fn('ui/aimtier', sset('am', 2), 'execute unless entity @e[tag=ek.steve] run return 0',
         f'execute as {CUR} run function ek:aim/dist', 'function ek:drop/tier',
         iff('tier', 1, sset('am', 3)), iff('tier', 2, sset('am', 4)), iff('tier', 3, sset('am', 5)))
    col = {3: 'gold', 4: 'yellow', 5: 'green', 7: 'light_purple'}
    P.fn('ui/curcolor', sop('amprev', '=', 'am'),
         'data modify entity %s text set value {text:"◎",color:"white",bold:true}' % CURV,
         [iff('am', k, 'data modify entity %s text set value {text:"◎",color:"%s",bold:true}' % (CURV, c)) for k, c in col.items()])
    lab = {1: ('   ◎ 판 안쪽을 바라봐', 'gray'), 2: ('   ◎ 스티브한테서 멀다', 'gray'), 3: ('   ◎ 스칠 거리', 'gold'),
           4: ('   ◎ 맞는 거리', 'yellow'), 5: ('   ◎ 정통', 'green'), 6: ('   ▼ 떨어지는 중', 'white')}
    show = [iff('am', 0, 'title @s actionbar ' + comp(*base, star, combo))]
    for k, (txt, c) in lab.items():
        show.append(iff('am', k, 'title @s actionbar ' + comp(*base, t(txt, c), star, combo)))
    show.append(iff('am', 7, 'title @s actionbar ' + comp(t('행운 상자! 우클릭으로 열기', 'yellow', True))))
    P.fn('ui/show', show)


def build(P, cards, pools):
    C = {c.id: c for c in cards}
    P.add('game/win', 'function ek:drop/cancel', 'function ek:box/clear')
    P.add('game/lose', 'function ek:drop/cancel', 'function ek:box/clear')

    # ------------------------------------------------------------------ cursor: where on the table the player is looking
    P.fn('aim/tick',
         'execute unless entity @e[tag=ek.cur] run summon minecraft:marker 0.5 60 0.5 {Tags:["ek.cur"]}',
         'execute unless entity @e[tag=ek.curv] positioned 0.5 300 0.5 run ' + tdx(['ek.curv'], '◎', 'white', 5, ',teleport_duration:1'),
         sset('cur', 0), sset('lock', 0), sset('near', 0), 'tag @e[tag=ek.pick] remove ek.pick', sset('ray', 260),
         'execute anchored eyes positioned ^ ^ ^ run function ek:aim/ray',
         # Looking straight at Steve while the ground behind him is far away (he is on a bridge, a pillar, a ledge): take his spot.
         # Otherwise the cursor stays on the ground, so the player keeps full control for leading a walking Steve.
         'execute if score #near ek matches 1 if score #cur ek matches 0 run function ek:aim/lock',
         f'execute if score #near ek matches 1 if score #lock ek matches 0 at {CUR} unless entity @e[tag=ek.steve,distance=..2.5] run function ek:aim/lock',
         f'execute if score #cur ek matches 1 at {CUR} run tp {CURV} ~ ~0.7 ~',
         iff('cur', 0, f'tp {CURV} 0.5 300 0.5'))
    P.fn('aim/ray',
         'execute positioned ~ ~-0.9 ~ if entity @e[tag=ek.steve,distance=..0.9] run scoreboard players set #near ek 1',
         'execute if score #npt ek matches 1.. as @e[tag=ek.pt,distance=..2.2] run tag @s add ek.pick',
         'execute unless block ~ ~ ~ #ek:ray run return run function ek:aim/hit',
         ssub('ray', 1),
         'execute if score #ray ek matches 1.. positioned ^ ^ ^0.5 run function ek:aim/ray')
    # the ray stopped inside a block: step back into the open cell in front of it and let the cursor settle on the floor below
    P.fn('aim/hit', iff('npt', '1..', 'function ek:aim/ghost'),
         sset('fall', 40), 'execute positioned ^ ^ ^-0.5 align xyz positioned ~0.5 ~ ~0.5 run function ek:aim/fall')
    # A lucky box glows through walls, so it can also be opened through them: for boxes only, the line of sight carries on past blocks.
    P.fn('aim/ghost',
         'execute as @e[tag=ek.pt,distance=..2.2] run tag @s add ek.pick',
         ssub('ray', 1),
         'execute if score #ray ek matches 1.. positioned ^ ^ ^0.5 run function ek:aim/ghost')
    P.fn('aim/fall',
         'execute unless block ~ ~-1 ~ #ek:ray run return run function ek:aim/set',
         ssub('fall', 1),
         'execute if score #fall ek matches 1.. positioned ~ ~-1 ~ run function ek:aim/fall')
    P.fn('aim/set', f'tp {CUR} ~ ~ ~',
         f'execute as {CUR} if entity @s[x=-14,y=58,z=-14,dx=28,dy=30,dz=28] run scoreboard players set #cur ek 1')
    P.fn('aim/lock', f'execute at {STEVE} run tp {CUR} ~ ~ ~', sset('cur', 1), sset('lock', 1))
    # squared distance (in 0.01 block^2) between the executing marker and Steve; height differences count half
    P.fn('aim/dist', sset('d2', 99999999), 'execute unless entity @e[tag=ek.steve] run return 0',
         [f'execute store result score #a{k} ek run data get entity @s Pos[{i}] 10' for i, k in enumerate('xyz')],
         [f'execute store result score #b{k} ek run data get entity {STEVE} Pos[{i}] 10' for i, k in enumerate('xyz')],
         [sop('a' + k, '-=', 'b' + k) for k in 'xyz'], sop('ay', '/=', 'c2'),
         [sop('a' + k, '*=', 'a' + k) for k in 'xyz'],
         sop('d2', '=', 'ax'), sop('d2', '+=', 'ay'), sop('d2', '+=', 'az'))

    # ------------------------------------------------------------------ throws
    # cards/…/aim pays and calls drop/start at the cursor; drop/land works out how close to Steve it came down (#tier):
    # 3 direct, 2 hit, 1 graze, 0 miss.  Only 2 and 3 play the card's event.
    P.fn('drop/start',
         'kill @e[tag=ek.aim]', 'kill @e[tag=ek.dropv]', 'kill @e[tag=ek.ring]',
         'summon minecraft:marker ~ ~ ~ {Tags:["ek.aim"]}',
         '$summon minecraft:item_display ~ ~$(t) ~ {Tags:["ek.dropv"],billboard:"center",teleport_duration:1,brightness:{sky:15,block:15},item:{id:"$(item)",count:1},' + (DISPLAY_T % (3, 3, 3)) + '}',
         'execute positioned ~ ~0.6 ~ run ' + tdx(['ek.ring'], '✖', 'red', 5),
         sset('drop', 1), snd('entity.egg.throw', 0.7, 0.8))
    P.fn('drop/tick', ssub('dropt', 1), 'execute as @e[tag=ek.dropv] at @s run tp @s ~ ~-1 ~',
         'execute if score #dropt ek matches 6 if score #ddodge ek matches 1 run function ek:drop/dodge',
         iff('dropt', '..0', 'function ek:drop/land'))
    # Things that fall slowly enough to cast a shadow (anvil, gravel) can be noticed by a walking Steve: he either stops dead
    # (when it is coming down just ahead of him) or bolts forward (when it is coming down on him). Busy or distracted, he never notices.
    P.fn('drop/dodge',
         unl('phase', 0, 'return 0'), iff('idle', '1..', 'return 0'), iff('intr', '1..', 'return 0'), unl('steve', 1, 'return 0'),
         f'execute at {AIM} unless entity @e[tag=ek.steve,distance=..3.4] run return 0',
         'execute store result score #r ek run random value 1..100',
         'execute if score #diff ek matches 0 unless score #r ek matches ..20 run return 0',
         'execute if score #diff ek matches 1 unless score #r ek matches ..35 run return 0',
         'execute if score #diff ek matches 2 unless score #r ek matches ..55 run return 0',
         popup('!', 'yellow', '4'), snd('entity.experience_orb.pickup', 0.6, 0.6),
         sset('noticed', 1), sset('dash', 8), abar(t('스티브가 눈치챘다!', 'yellow'), hold=25),
         f'execute as {STEVE} at @s facing entity @e[tag=ek.tgt,limit=1] feet rotated ~ 0 positioned ^ ^ ^1.6 if entity @e[tag=ek.aim,distance=..1.5] run function ek:drop/dodge_halt',
         'execute store result score #r ek run random value 1..2',
         iff('r', 1, say(['어? 위에 뭐야', '방금 그림자 뭐야', '느낌이 쎄한데'])))
    P.fn('drop/dodge_halt', sset('dash', 0), sset('halt', 14))
    P.fn('steve/dash', ssub('dash', 1), S('function ek:steve/step'), S('function ek:steve/step'))
    P.fn('drop/land',
         sset('drop', 0), 'kill @e[tag=ek.dropv]', 'kill @e[tag=ek.ring]',
         unl('state', 1, 'return run kill @e[tag=ek.aim]'),
         # something else got to Steve first (or he is not there at all): the throw is void and its energy comes back
         iff('intr', '1..', 'return run function ek:drop/fizzle'),
         unl('steve', 1, 'return run function ek:drop/fizzle'),
         'execute unless entity @e[tag=ek.steve] run return run function ek:drop/fizzle',
         sset('moving', 0), 'execute if score #phase ek matches 0 if score #idle ek matches 0 if score #noticed ek matches 0 run scoreboard players set #moving ek 1',
         f'execute as {AIM} run function ek:aim/dist',
         'function ek:drop/dispatch')
    P.fn('drop/tier', sset('tier', 0),
         'execute if score #d2 ek <= #rg ek run scoreboard players set #tier ek 1',
         'execute if score #d2 ek <= #rh ek run scoreboard players set #tier ek 2',
         'execute if score #d2 ek <= #rd ek run scoreboard players set #tier ek 3')
    P.fn('drop/refund', sop('energy', '+=', 'dcost'), iff('energy', '101..', sset('energy', 100)), 'function ek:game/energy_bar')
    P.fn('drop/fizzle', 'function ek:drop/refund', 'kill @e[tag=ek.aim]', 'weather clear',
         abar(t('던진 게 불발됐다. 기력은 돌려받았어.', 'gray'), hold=40))
    P.fn('drop/cancel', iff('drop', 1, 'function ek:drop/refund'), sset('drop', 0),
         'kill @e[tag=ek.aim]', 'kill @e[tag=ek.dropv]', 'kill @e[tag=ek.ring]')
    P.fn('drop/miss',
         f'execute at {AIM} positioned ~ ~1.5 ~ run function ek:fx/popup {{t:"빗나감",c:"gray",s:"3.5"}}',
         f'execute at {AIM} run particle minecraft:poof ~ ~0.5 ~ 0.3 0.3 0.3 0.02 12 force',
         snd('block.note_block.bass', 0.6, 0.5), 'kill @e[tag=ek.aim]', 'weather clear',
         # a clean miss gives half the energy back
         sop('dcost', '/=', 'c2'), 'function ek:drop/refund',
         abar(t('빗나갔다. 기력은 절반만 돌려받았어.', 'gray'), hold=30),
         'execute store result score #r ek run random value 1..3',
         iff('r', 1, say(['방금 뭐 떨어졌나?', '뒤에서 무슨 소리 났는데', '뭐야 아무것도 없네', '오늘 하늘에서 뭐가 자꾸 떨어져'])))
    P.fn('drop/sunk',
         f'execute at {AIM} positioned ~ ~1.5 ~ run function ek:fx/popup {{t:"용암에 빠졌다",c:"gold",s:"3.5"}}',
         f'execute at {AIM} run particle minecraft:lava ~ ~0.3 ~ 0.3 0.2 0.3 0 15 force',
         snd('block.lava.extinguish', 0.8, 0.6), 'kill @e[tag=ek.aim]',
         abar(t('용암에 떨어져서 타 버렸다.', 'gold'), hold=30))
    P.fn('drop/graze',
         popup('스쳤다', 'yellow', '3'), hurt(), dmg(2), 'kill @e[tag=ek.aim]', 'weather clear', 'schedule function ek:fx/nofire 12t',
         abar(t('스쳤다. 조금만 더 가까이.', 'yellow'), hold=30),
         'execute if score #mental ek matches 1.. run ' + say(['아 깜짝이야', '방금 뭐였어?', '뭐가 스쳤는데', '아슬아슬했네']))
    P.fn('drop/snipe', sset('aimx', 130),
         f'execute at {AIM} positioned ~ ~3 ~ run function ek:fx/popup {{t:"저격! 피해 +30%",c:"gold",s:"3.5"}}',
         snd('entity.arrow.hit_player', 1.2, 0.8))
    P.fn('fx/nofire', 'fill -14 58 -14 14 86 14 minecraft:air replace minecraft:fire',
         'execute as @e[tag=ek.steve] run data merge entity @s {Fire:0s}')

    # ------------------------------------------------------------------ Steve gets distracted
    chat = ['이 서버 오늘 렉 좀 있네', '님들 드래곤 몇 분 컷임?', '엄마가 밥 먹으래 잠만', '아 손 시려', '오늘 운 좋은 듯', 'ㅋㅋㅋㅋ', '물 좀 마시고 옴']
    kinds = ['채팅 치는 중', '인벤토리 정리 중', '경치 구경 중', '스트레칭 중', '잠수 중 (AFK)']
    P.fn('steve/idle_roll',
         'execute store result score #r ek run random value 1..60',
         unl('r', 1, 'return 0'),
         'execute store result score #idle ek run random value 60..100',
         'execute store result score #idlek ek run random value 1..%d' % len(kinds),
         sset('wild', 1), popup('딴짓 중!', 'aqua', '3'), snd('block.note_block.chime', 1.4, 0.7),
         [iff('idlek', i + 1, status(k)) for i, k in enumerate(kinds)])
    P.fn('steve/idle_tick', ssub('idle', 1),
         sop('m8', '=', 'idle'), sop('m8', '%=', 'c8'), sop('m20', '=', 'idle'), sop('m20', '%=', 'c20'),
         'execute if score #idlek ek matches 2 if score #m8 ek matches 0 run ' + swing(),
         'execute if score #idlek ek matches 2 if score #m8 ek matches 0 run ' + snd('item.bundle.insert', 1, 0.5),
         'execute if score #idlek ek matches 3 run ' + S('tp @s ~ ~ ~ ~7 ~'),
         'execute if score #idlek ek matches 4 if score #m20 ek matches 10 run ' + pose('crouching'),
         'execute if score #idlek ek matches 4 if score #m20 ek matches 0 run ' + pose('standing'),
         iff('idle', '..0', 'function ek:steve/idle_end'))
    P.fn('steve/idle_stop', sset('idle', 0), sset('wild', 0), 'execute store result score #idlecd ek run random value 240..420',
         iff('mod', 5, 'execute store result score #idlecd ek run random value 90..180'))
    P.fn('steve/idle_end', 'function ek:steve/idle_stop', pose('standing'),
         'data modify storage ek:s status set from storage ek:s bstatus',
         'execute if score #idlek ek matches 1 run ' + say(chat))

    # ------------------------------------------------------------------ lucky boxes
    P.fn('box/tick', iff('box', 1, 'function ek:box/live'), iff('box', 0, 'function ek:box/wait'))
    P.fn('box/wait', ssub('boxt', 1),
         'execute if score #boxt ek matches ..0 if score #intr ek matches 0 if score #steve ek matches 1 run function ek:box/spawn')
    P.fn('box/spawn',
         'execute store result score #boxt ek run random value 500..900',
         iff('mod', 4, 'execute store result score #boxt ek run random value 220..400'),
         'execute store result storage ek:s box.x int 1 run random value -12..12',
         'execute store result storage ek:s box.z int 1 run random value -12..12',
         'function ek:box/spawn_m with storage ek:s box')
    P.fn('box/spawn_m', sset('fall', 30), '$execute positioned $(x) 87 $(z) run function ek:box/fall')
    P.fn('box/fall',
         'execute unless block ~ ~-1 ~ #ek:ray run return run function ek:box/place',
         ssub('fall', 1),
         'execute if score #fall ek matches 1.. positioned ~ ~-1 ~ run function ek:box/fall')
    P.fn('box/place',
         'summon minecraft:item_display ~ ~1 ~ {Tags:["ek.box","ek.pt"],teleport_duration:1,Glowing:1b,glow_color_override:16766720,brightness:{sky:15,block:15},item:{id:"minecraft:chest",count:1},' + (DISPLAY_T % (2, 2, 2)) + '}',
         'execute positioned ~ ~3 ~ run ' + tdx(['ek.boxv'], '?', 'gold', 6),
         sset('box', 1), sset('boxlife', 300), sset('npt', 1),
         'particle minecraft:end_rod ~ ~1 ~ 0.4 0.6 0.4 0.05 30 force', snd('block.note_block.bell', 1.2, 0.8),
         abar(t('행운 상자가 떨어졌다! 바라보고 우클릭', 'yellow'), hold=50),
         iff('boxhint', 0, tell(t('  행운 상자가 떨어졌다. 사라지기 전에 상자를 바라보고 우클릭하면 열려.', 'yellow'))), sset('boxhint', 1))
    P.fn('box/live', ssub('boxlife', 1), f'execute as {BOX} at @s run tp @s ~ ~ ~ ~9 ~',
         iff('boxlife', '..0', 'function ek:box/expire'))
    P.fn('box/expire', f'execute at {BOX} run particle minecraft:poof ~ ~ ~ 0.4 0.4 0.4 0.02 20 force', 'function ek:box/clear')
    P.fn('box/clear', 'kill @e[tag=ek.box]', 'kill @e[tag=ek.boxv]', sset('box', 0), sset('npt', 0))
    P.fn('box/open',
         f'execute at {BOX} run particle minecraft:totem_of_undying ~ ~0.5 ~ 0.4 0.6 0.4 0.3 40 force',
         f'execute at {BOX} run summon minecraft:marker ~ ~ ~ {{Tags:["ek.boxp","ek.tmp","ek.new"]}}',
         'scoreboard players set @e[tag=ek.new] ek.life 5', 'tag @e[tag=ek.new] remove ek.new',
         snd('entity.player.levelup', 1.3, 0.8), 'function ek:box/clear',
         'execute store result score #r ek run random value 1..100',
         iff('r', '..45', 'return run function ek:box/r_energy'),
         iff('r', '46..75', 'return run function ek:box/r_lucky'),
         'function ek:box/r_forget')
    BP = 'execute at @e[tag=ek.boxp,limit=1] positioned ~ ~2 ~ run function ek:fx/popup {t:"%s",c:"%s",s:"3.5"}'
    P.fn('box/r_energy', sadd('energy', 40), iff('energy', '101..', sset('energy', 100)), 'function ek:game/energy_bar',
         BP % ('기력 +40', 'yellow'), abar(t('행운 상자: 기력 +40', 'yellow'), hold=50))
    P.fn('box/r_lucky', sset('lucky', 1), BP % ('다음 억까는 노림수 확정', 'aqua'),
         abar(t('행운 상자: 다음 억까는 무조건 노림수 적중!', 'aqua'), hold=60))
    P.fn('box/r_forget',
         sset('fgot', 0), [iff('stage', n, f'function ek:box/forget_s{n}') for n in pools],
         # nothing learned in this stage yet: energy instead
         iff('fgot', 0, 'function ek:box/r_energy'))
    for n, ids in pools.items():
        P.fn(f'box/forget_s{n}',
             ['execute if score #l_%s ek matches 1 run return run function ek:box/forget1 {id:"%s"}' % (cid, cid) for cid in ids])
    P.fn('box/forget1', sset('fgot', 1), '$function ek:c/$(id)/forget',
         'execute at @e[tag=ek.boxp,limit=1] positioned ~ ~2 ~ run function ek:fx/popup {t:"간파 하나 초기화",c:"light_purple",s:"3.5"}')

    # ------------------------------------------------------------------ "today's twist": every stage after the first rolls one
    mods = [('평범한 하루', '', 'gray'), ('기력이 넘치는 날', '기력이 1.5배 빨리 찬다', 'yellow'), ('스티브 컨디션 최상', '스티브가 서둘러 걷는다', 'red'),
            ('재수 없는 날', '모든 억까 피해 +20%', 'gold'), ('행운 상자 풍년', '행운 상자가 훨씬 자주 떨어진다', 'yellow'),
            ('스티브가 산만한 날', '스티브가 딴짓을 훨씬 자주 한다', 'aqua')]
    P.fn('game/mod_roll', sset('mod', 0), sset('ex', 0),
         'execute if score #stage ek matches 2.. store result score #mod ek run random value 0..%d' % (len(mods) - 1),
         [iff('mod', i, tell(t('  오늘의 변수: ', 'gray'), t(nm, col, True), t('  ' + ds, 'gray'))) for i, (nm, ds, col) in enumerate(mods) if i],
         [iff('mod', i, 'title @a subtitle ' + comp(sc('day', 'white'), t('일차 · ', 'white'), t(nm, col))) for i, (nm, ds, col) in enumerate(mods) if i])
