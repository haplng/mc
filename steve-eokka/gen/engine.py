"""Core game engine functions (everything that is not stage- or card-specific)."""
from core import *
import v2
from v2 import V2_SCORES

FLAGS = ['busy', 'mine', 'high', 'bridge', 'dark', 'maze', 'lavaspot', 'obs', 'barter', 'fight', 'eyes', 'frame',
         'gravel', 'aim', 'bed', 'perch', 'portal', 'nobed', 'spawner']
GRADES = ['성자', '천사', '평범한 불운', '장난꾸러기 운명', '억까꾼', '악질', '악마']
UNLOCK = {None: '', 'runs1': 'if score #runs ek matches 1.. ', 'runs2': 'if score #runs ek matches 2.. ',
          'win1': 'if score #wins ek matches 1.. '}
UNLOCK_NOT = {'runs1': 'unless score #runs ek matches 1.. ', 'runs2': 'unless score #runs ek matches 2.. ',
              'win1': 'unless score #wins ek matches 1.. '}
UNLOCK_TXT = {'runs1': '한 판을 끝까지 하면 열림', 'runs2': '두 판을 끝까지 하면 열림', 'win1': '한 번 이기면 열림'}

def item(slot, name, color, model, lore=(), who='@s'):
    lr = ''
    if lore:
        lr = ',minecraft:lore=[%s]' % ','.join(js(t(l, c, italic=False)) for l, c in lore)
    return 'item replace entity %s hotbar.%d with minecraft:carrot_on_a_stick[minecraft:item_name=%s,minecraft:item_model="minecraft:%s",minecraft:max_damage=1000%s]' % (
        who, slot, js(t(name, color, italic=False)), model, lr)

def build(stages, cards, pools):
    C = {c.id: c for c in cards}
    NST = len(stages)

    # ------------------------------------------------------------------ load / tick
    P.fn('load',
         [f'scoreboard objectives add {o} dummy' for o in ('ek', 'ek.life', 'ek.cd', 'ek.zm', 'ek.rd', 'ek.mh')],
         'scoreboard objectives add ek.use minecraft.used:minecraft.carrot_on_a_stick',
         'scoreboard objectives remove ek.sn',
         # the giant player and the invisible mount share a team: no pushing each other, and no ghostly outline of the mount
         'team add ek', 'team modify ek collisionRule never', 'team modify ek seeFriendlyInvisibles false',
         [sset(f'c{n}', n) for n in (2, 3, 4, 5, 6, 8, 10, 20, 25, 100, 10000)], sset('pct', 100),
         'execute unless score #aimx ek matches 1.. run scoreboard players set #aimx ek 100',
         ['gamerule %s %s' % kv for kv in [
             ('send_command_feedback', 'false'), ('advance_time', 'false'), ('advance_weather', 'false'),
             ('spawn_mobs', 'false'), ('spawn_monsters', 'false'), ('mob_griefing', 'false'), ('block_drops', 'false'),
             ('mob_drops', 'false'), ('entity_drops', 'false'), ('fall_damage', 'false'), ('fire_damage', 'false'),
             ('drowning_damage', 'false'), ('show_death_messages', 'false'), ('show_advancement_messages', 'false'),
             ('keep_inventory', 'true'), ('immediate_respawn', 'true'), ('random_tick_speed', '0'),
             ('max_command_sequence_length', '1000000'), ('max_block_modifications', '100000'),
             ('locator_bar', 'false'), ('spawn_phantoms', 'false'), ('fire_spread_radius_around_player', '0'),
             ('spawner_blocks_work', 'false'), ('command_block_output', 'false'), ('spawn_wandering_traders', 'false'),
             ('spawn_patrols', 'false'), ('lava_source_conversion', 'false'), ('allow_entering_nether_using_portals', 'false')]],
         'bossbar add ek:prog ""', 'bossbar add ek:mental ""', 'bossbar add ek:energy ""',
         'bossbar set ek:prog color blue', 'bossbar set ek:prog max 100',
         'bossbar set ek:mental color green', 'bossbar set ek:mental max 200',
         'bossbar set ek:energy color yellow', 'bossbar set ek:energy style notched_10', 'bossbar set ek:energy max 100',
         [f'execute unless score #{n} ek matches 0.. run scoreboard players set #{n} ek 0' for n in ('runs', 'wins', 'best', 'state', 'intr', 'abt', 'bubt') + V2_SCORES],
         'execute unless score #built ek matches 1 run function ek:setup/start')

    P.fn('tick',
         'execute unless score #built ek matches 1 run tp @a 0.5 57 26.5',
         'execute unless score #built ek matches 1 run return 0',
         # a world last played with the first version of the pack: once somebody is in, go back to the lobby for a clean start
         'execute unless score #ver ek matches 2 if entity @a run function ek:setup/upgrade',
         'execute as @a[tag=!ek.in] run function ek:player/init',
         'execute as @a[tag=!ek.v2] run function ek:player/init2',
         'scoreboard players remove @a[scores={ek.cd=1..}] ek.cd 1',
         'execute as @a[scores={ek.use=1..}] run function ek:player/use',
         'execute as @a run function ek:player/tick',
         'execute as @e[tag=ek.tmp] run function ek:fx/tmp',
         'kill @e[type=minecraft:item]', sadd('fixt', 1), iff('fixt', '20..', 'function ek:ui/fix'),
         unl('state', 1, 'tp @e[tag=ek.curv] 0.5 300 0.5'),
         iff('state', 0, 'function ek:lobby/tick'),
         iff('state', 1, 'function ek:game/tick'),
         iff('state', 3, 'function ek:result/tick'))

    P.files['data/minecraft/tags/function/load.json'] = js({'values': ['ek:load']})
    P.files['data/minecraft/tags/function/tick.json'] = js({'values': ['ek:tick']})
    # No predicate files: in 26.3 predicates are a registry, and one that fails to parse stops the whole world from loading
    # (the 26.3 loot-condition format differs from older versions). The one predicate the pack needs (is the sneak key held)
    # is written inline in player/tick, where a parse problem could only ever cost that one function.

    # ------------------------------------------------------------------ setup
    P.fn('setup/start', 'forceload add -48 -48 47 47', 'schedule function ek:setup/go 20t')
    P.fn('setup/go',
         ['execute unless loaded %d 60 %d run return run schedule function ek:setup/go 20t' % c
          for c in ((-48, -48), (47, 47), (-48, 47), (47, -48), (0, 0))],
         'function ek:setup/room', sset('built', 1), sset('ver', 2), 'function ek:lobby/enter')
    P.fn('setup/upgrade', sset('ver', 2), 'schedule function ek:setup/upgrade2 40t')
    P.fn('setup/upgrade2', 'function ek:lobby/enter',
         tell(t('  맵이 업데이트돼서 로비에서 새로 시작해. 스티브 멘탈이 늘어서 한 판이 더 길어졌어.', 'yellow')))
    wall = 'minecraft:white_terracotta'; trim = 'minecraft:spruce_planks'
    P.fn('setup/room',
         'fill -45 55 -45 45 55 45 minecraft:smooth_stone',
         'fill -45 56 -45 45 56 45 minecraft:oak_planks',
         'fill -27 56 -27 27 56 27 minecraft:cyan_wool', 'fill -25 56 -25 25 56 25 minecraft:light_blue_wool',
         'fill -45 57 -45 45 96 -45 ' + wall, 'fill -45 57 45 45 96 45 ' + wall,
         'fill -45 57 -45 -45 96 45 ' + wall, 'fill 45 57 -45 45 96 45 ' + wall,
         'fill -45 57 -45 45 60 -45 ' + trim, 'fill -45 57 45 45 60 45 ' + trim,
         'fill -45 57 -45 -45 60 45 ' + trim, 'fill 45 57 -45 45 60 45 ' + trim,
         'fill -16 57 -16 16 57 16 minecraft:dark_oak_planks',
         'fill -15 58 -15 15 59 -15 minecraft:stripped_spruce_wood', 'fill -15 58 15 15 59 15 minecraft:stripped_spruce_wood',
         'fill -15 58 -15 -15 59 15 minecraft:stripped_spruce_wood', 'fill 15 58 -15 15 59 15 minecraft:stripped_spruce_wood',
         # giant toys in the corners
         'fill 32 57 -42 39 64 -35 minecraft:red_concrete', 'fill 33 65 -41 38 70 -36 minecraft:blue_concrete',
         'fill 24 57 -41 30 63 -35 minecraft:yellow_concrete', 'fill -42 57 34 -24 59 36 minecraft:lime_concrete',
         'fill -23 57 34 -21 59 36 minecraft:white_concrete', 'fill -42 57 38 -26 59 40 minecraft:magenta_concrete',
         'fill -25 57 38 -23 59 40 minecraft:white_concrete', 'fill -40 57 -40 -33 60 -33 minecraft:orange_concrete',
         'fill -39 61 -39 -34 62 -34 minecraft:white_concrete')

    # ------------------------------------------------------------------ player
    P.fn('player/init',
         'tag @s add ek.in', 'gamemode adventure @s', 'clear @s',
         'effect give @s minecraft:night_vision infinite 0 true',
         'effect give @s minecraft:saturation infinite 0 true',
         'effect give @s minecraft:resistance infinite 4 true',
         'attribute @s minecraft:scale base set 16',
         'attribute @s minecraft:jump_strength base set 0',
         'tp @s 0.5 57 26.5 180 25',
         'bossbar set ek:prog players @a', 'bossbar set ek:mental players @a', 'bossbar set ek:energy players @a',
         iff('state', 0, 'function ek:lobby/give'), iff('state', 0, 'function ek:lobby/hidebars'),
         iff('state', 1, 'function ek:cards/deal'),
         iff('state', 3, 'function ek:result/give'),
         'tellraw @s ' + comp(t('\n  스티브 억까 시뮬레이터\n', 'gold', True),
                              t('  넌 이 월드 그 자체야. 드래곤 잡으러 가는 스티브를 억까해서 접게 만들어.\n', 'white'),
                              t('  1번 칸을 들고 우클릭하면 시작. 5번 칸은 설명서.\n', 'gray')))
    v2.player(P)
    P.fn('player/use',
         'scoreboard players reset @s ek.use',
         'execute if score @s ek.cd matches 1.. run return 0',
         'scoreboard players set @s ek.cd 6',
         'execute store result score #sl ek run data get entity @s SelectedItemSlot',
         iff('state', 0, 'return run function ek:lobby/use'),
         iff('state', 3, 'return run function ek:result/use'),
         iff('state', 1, 'return run function ek:cards/use'))

    # ------------------------------------------------------------------ lobby
    P.fn('lobby/hidebars', 'bossbar set ek:prog players', 'bossbar set ek:mental players', 'bossbar set ek:energy players')
    # */give clears and deals; */put only writes the slots (identical stacks send nothing to the client), so a card the
    # player threw away or moved comes back within a second
    P.fn('ui/fix', sset('fixt', 0), 'function ek:player/fix', iff('state', 0, 'execute as @a run function ek:lobby/put'), iff('state', 1, 'function ek:cards/put'),
         'execute if score #state ek matches 3 if score #rt ek matches 160.. as @a run function ek:result/put')
    P.fn('lobby/give', 'clear @s', 'function ek:lobby/put')
    P.fn('lobby/put',
         item(0, '▶ 시작: 보통 스티브', 'gold', 'player_head', [('멘탈 320 · 같은 억까 2번이면 간파', 'gray')]),
         item(1, '▶ 시작: 초보 스티브', 'green', 'leather_helmet', [('멘탈 240 · 3번 당해야 간파', 'gray')]),
         'execute if score #wins ek matches 1.. run ' + item(2, '▶ 시작: 고인물 스티브', 'aqua', 'diamond_helmet', [('멘탈 400 · 한 번 당하면 바로 간파', 'gray')]),
         'execute unless score #wins ek matches 1.. run ' + item(2, '잠김: 고인물 스티브', 'dark_gray', 'barrier', [('한 번 이기면 열림', 'gray')]),
         item(4, '설명서', 'white', 'book', [('우클릭하면 채팅창에 설명이 나옴', 'gray')]))
    P.fn('lobby/enter',
         sset('state', 0), sset('intr', 0), 'function ek:game/cleanup', 'kill @e[tag=ek.ui]',
         'fill -14 58 -14 14 86 14 minecraft:air', 'function ek:s1/build',
         'time set 6000', 'weather clear', sset('armor', 0), sset('redo', 0),
         'function ek:s1/spawn',
         tdisp(0.5, 79.5, 0.5, ['ek.ui'], comp(t('스티브 억까 시뮬레이터', 'gold', True)), 8),
         tdisp(0.5, 75.5, 0.5, ['ek.ui'], comp(t('드래곤 잡으러 가는 스티브를 억까해서 접게 만들어라', 'white')), 3),
         tdisp(0.5, 73, 0.5, ['ek.ui', 'ek.rec'], comp(t('1번 칸 들고 우클릭: 시작', 'yellow')), 3),
         'function ek:lobby/record', 'function ek:lobby/hidebars',
         'execute as @a run function ek:lobby/give')
    P.fn('lobby/record',
         'execute store result storage ek:s r.wins int 1 run scoreboard players get #wins ek',
         'execute store result storage ek:s r.runs int 1 run scoreboard players get #runs ek',
         [iff('best', i, 'data modify storage ek:s r.best set value "%s"' % g) for i, g in enumerate(GRADES)],
         'execute if score #runs ek matches 1.. run function ek:lobby/record_m with storage ek:s r')
    P.fn('lobby/record_m',
         '$data modify entity @e[tag=ek.rec,limit=1] text set value {text:"",extra:[{text:"1번 칸 들고 우클릭: 시작\\n",color:"yellow"},{text:"승리 $(wins)회 · 플레이 $(runs)회 · 최고 등급: $(best)",color:"gray"}]}')
    P.fn('lobby/tick', S('tp @s ~ ~ ~ facing entity @p eyes'))
    P.fn('lobby/use',
         iff('sl', 0, 'return run function ek:game/start_n'),
         iff('sl', 1, 'return run function ek:game/start_e'),
         'execute if score #sl ek matches 2 if score #wins ek matches 1.. run return run function ek:game/start_h',
         iff('sl', 2, 'return run tellraw @s ' + comp(t('고인물 스티브는 한 번 이기면 열려.', 'gray'))),
         iff('sl', 4, 'function ek:lobby/howto'))
    P.fn('lobby/howto', 'tellraw @s ' + comp(
        t('\n━━━━━━━━ 설명서 ━━━━━━━━\n', 'gold'),
        t('· 스티브는 7단계(나무·돌 → 철 → 다이아 → 포탈 → 네더 → 요새 → 엔드)를 알아서 진행해.\n', 'white'),
        t('· 카드를 들고 우클릭하면 억까가 들어가. 쓸 때마다 기력이 닳고, 기력은 시간이 지나면 다시 차.\n', 'white'),
        t('· 이름에 ◎가 붙은 카드는 네가 바라보는 곳(판 위의 ◎ 표시)에 떨어져. 떨어지는 데 시간이 걸리니까 걸어가는 스티브는 앞질러서 던져.\n', 'green'),
        t('· 걸어가는 스티브를 정통으로 맞히면 「저격」으로 피해가 30% 늘어. 멀리 떨어지면 빗나가고 기력은 절반만 돌아와.\n', 'green'),
        t('· 모루나 자갈처럼 천천히 떨어지는 건 걸어가던 스티브가 눈치채고 피할 때도 있어. 뭔가에 열중할 때는 못 봐.\n', 'green'),
        t('· 카드마다 노림수가 있어. 스티브가 딱 그 행동을 할 때 쓰면 훨씬 세게 들어가. (화면 아래 ★ 표시)\n', 'aqua'),
        t('· 스티브는 가끔 길 가다 딴짓을 해. 그동안은 아무 카드나 노림수가 돼.\n', 'aqua'),
        t('· 가끔 판 위에 행운 상자가 떨어져. 상자를 바라보고 우클릭하면 열려.\n', 'yellow'),
        t('· 연달아 맞히면 콤보로 피해가 커져. 대신 같은 카드에 계속 당하면 스티브가 간파해서 효과가 반으로 줄어.\n', 'white'),
        t('· 간파는 다음 단계로 넘어가면 풀려서, 그 카드가 한 번은 다시 제대로 통해.\n', 'white'),
        t('· 멘탈은 가만두면 천천히 회복돼. 0으로 만들면 스티브가 월드를 삭제하고 네 승리.\n', 'white'),
        t('· 스티브가 엔더 드래곤을 잡으면 네 패배.\n', 'red'),
        t('· Shift를 누르고 있으면 몸을 숙여서 가까이 볼 수 있어. 판 주위를 돌아다니면서 잘 보이는 자리를 잡아.\n', 'gray'),
        t('━━━━━━━━━━━━━━━━━━━━\n', 'gold')))

    # ------------------------------------------------------------------ game flow
    for nm, d, mm, ri, ln, ei, ds in (('n', 1, 320, 120, 2, 12, 100), ('e', 0, 240, 150, 3, 10, 110), ('h', 2, 400, 100, 1, 12, 90)):
        P.fn('game/start_' + nm, sset('diff', d), sset('mmax', mm), sset('recint', ri), sset('learn', ln), sset('eint', ei),
             sset('dscale', ds), 'function ek:game/begin')
    names = ['creeper'] + [c.id for c in cards if c.id != 'creeper']
    P.fn('game/begin',
         'kill @e[tag=ek.ui]', sset('state', 1), sset('stage', 1), sset('day', 1),
         [sset(n, 0) for n in ('deaths', 'ncards', 'total', 'combo', 'combo_t', 'maxcombo', 'tilt', 'rec', 'et', 'intr', 'abt', 'gu', 'bubt') + V2_SCORES],
         sset('aimx', 100), sset('idlecd', 200), sset('boxt', 400), 'data modify storage ek:s ab set value {star:"",combo:""}',
         [sset('u_' + c.id, 0) for c in cards], [sset('l_' + c.id, 0) for c in cards],
         [sset('dc_' + k, 0) for k in CAUSES], [sset('ho_' + k, 0) for k in HEAL_KEYS],
         sop('mental', '=', 'mmax'), sset('energy', 60), sset('armor', 0),
         'execute store result bossbar ek:mental max run scoreboard players get #mmax ek',
         'bossbar set ek:prog players @a', 'bossbar set ek:mental players @a', 'bossbar set ek:energy players @a',
         'title @a times 5 50 15', 'title @a subtitle ' + comp(t('드래곤이 잡히기 전에 스티브를 접게 만들어라', 'white')),
         'title @a title ' + comp(t('억까 시작', 'gold', True)),
         tell(t('  카드를 들고 우클릭하면 억까가 들어가. ◎ 카드는 바라보는 곳에 떨어지니까 스티브를 잘 겨냥해.', 'gray')),
         tell(t('  화면 아래에 ★가 뜰 때 쓰면 훨씬 세게 들어가.', 'gray')),
         'function ek:game/energy_bar', 'function ek:game/stage_begin')
    P.fn('game/cleanup',
         ['execute as @e[tag=%s] run function ek:fx/vanish' % tg for tg in ('ek.steve', 'ek.mob', 'ek.stg')],
         'kill @e[tag=ek.bub]', 'kill @e[tag=ek.tmp]', 'kill @e[tag=ek.tgt]', 'kill @e[tag=ek.evt]',
         'function ek:drop/cancel', 'function ek:box/clear', sset('idle', 0), sset('wild', 0))
    P.fn('game/stage_setup',
         'function ek:game/cleanup', 'fill -14 58 -14 14 86 14 minecraft:air',
         [iff('stage', s.n, f'function ek:s{s.n}/build') for s in stages],
         [iff('stage', s.n, f'function ek:s{s.n}/init') for s in stages],
         'summon marker 0 60 0 {Tags:["ek.tgt"]}',
         sset('beat', 0), sset('intr', 0), sset('snap', 1), sset('phase', 0), 'time set 6000', 'weather clear',
         [iff('stage', s.n, f'function ek:s{s.n}/spawn') for s in stages])
    P.fn('game/stage_begin',
         sset('maxbeat', 0), sset('redo', 0), 'function ek:game/stage_setup', 'function ek:cards/deal',
         [iff('stage', s.n, 'data modify storage ek:s stage set value "%s"' % s.name) for s in stages],
         'title @a times 5 40 10',
         'title @a subtitle ' + comp(sc('day', 'white'), t('일차', 'white')),
         'title @a title ' + comp(st('stage', 'yellow')),
         snd('block.beacon.activate', 1.4, 0.7),
         'particle minecraft:poof 0.5 64 0.5 9 3 9 0.02 300 force',
         'function ek:game/mod_roll',
         'function ek:beat/start')
    P.fn('game/stage_clear',
         sadd('stage', 1), sadd('day', 1), heal(8), 'function ek:cards/relax', 'function ek:game/stage_begin')
    # A new day: Steve lets his guard down again. Every card he had seen through works properly once more before he
    # remembers (the use counter is left one short of #learn), so no card stays dull for the rest of a run.
    P.fn('cards/relax', sset('relaxed', 0),
         [['execute if score #l_%s ek matches 1 run scoreboard players operation #u_%s ek = #learn ek' % (c.id, c.id),
           'execute if score #l_%s ek matches 1 run scoreboard players remove #u_%s ek 1' % (c.id, c.id),
           'execute if score #l_%s ek matches 1 run scoreboard players set #relaxed ek 1' % c.id,
           sset('l_' + c.id, 0)] for c in cards],
         iff('relaxed', 1, tell(t('  하루가 지나 스티브가 방심했다. 간파당했던 카드도 한 번은 다시 제대로 통한다.', 'yellow'))))
    P.fn('game/tick',
         'execute as @a[limit=1] at @s run function ek:aim/tick',
         'function ek:game/energy',
         iff('drop', 1, 'function ek:drop/tick'), 'function ek:box/tick',
         iff('gu', '1..', ssub('gu', 1)),
         [iff('stage', s.n, f'function ek:s{s.n}/tick') for s in stages if s.tick],
         iff('intr', '1..', 'function ek:ev/tick'),
         'execute if score #intr ek matches 0 if score #steve ek matches 1 run function ek:beat/tick',
         'execute if score #state ek matches 1 if score #intr ek matches 0 if score #steve ek matches 1 unless entity @e[tag=ek.steve] run function ek:steve/lost',
         f'execute if score #snap ek matches 1 as {STEVE} at @s run function ek:steve/snap',
         iff('bubt', '1..', 'function ek:steve/bubble_tick'),
         iff('intr', 0, 'function ek:game/calm'),
         'function ek:ui/tick',
         'execute if score #state ek matches 1 if score #intr ek matches 0 if score #mental ek matches ..0 run function ek:game/win')
    P.fn('game/energy', sadd('et', 1), iff('mod', 1, 'function ek:game/energy_x'), 'execute if score #et ek >= #eint ek run function ek:game/energy1')
    P.fn('game/energy_x', sadd('ex', 1), iff('ex', '2..', sadd('et', 1)), iff('ex', '2..', sset('ex', 0)))
    P.fn('game/energy1', sset('et', 0), iff('energy', '..99', sadd('energy', 1)), 'function ek:game/energy_bar')
    P.fn('game/energy_bar',
         'execute store result bossbar ek:energy value run scoreboard players get #energy ek',
         'bossbar set ek:energy name ' + js(['', t('억까 기력 ', 'yellow'), sc('energy', 'white')]))
    P.fn('game/calm',
         iff('combo_t', 1, 'data modify storage ek:s ab.combo set value ""'), iff('combo_t', '1..', ssub('combo_t', 1)), sadd('rec', 1),
         'execute if score #rec ek >= #recint ek run function ek:game/rec1')
    P.fn('game/rec1', sset('rec', 0),
         'execute if score #mental ek < #mmax ek run scoreboard players add #mental ek 1', 'function ek:game/bars')
    P.fn('game/bars',
         'execute store result bossbar ek:mental value run scoreboard players get #mental ek',
         'bossbar set ek:mental name ' + js(['', t('스티브 멘탈 ', 'white'), sc('mental', 'white'), t('/', 'gray'), sc('mmax', 'gray')]),
         sop('pct', '=', 'mental'), sop('pct', '*=', 'c100'), sop('pct', '/=', 'mmax'),
         iff('pct', '60..', 'bossbar set ek:mental color green'),
         iff('pct', '30..59', 'bossbar set ek:mental color yellow'),
         iff('pct', '..29', 'bossbar set ek:mental color red'),
         'execute store result bossbar ek:prog value run scoreboard players get #prog ek',
         'bossbar set ek:prog name ' + js(['', sc('day', 'white'), t('일차 · ', 'white'), st('stage', 'aqua'), t(' · 진행 ', 'gray'), sc('prog', 'white'), t('%', 'gray')]))
    P.fn('game/dmg',
         iff('combo_t', '1..', sadd('combo', 1)), unl('combo_t', '1..', sset('combo', 1)), sset('combo_t', 140),
         sop('mul', '=', 'combo'), ssub('mul', 1), sop('mul', '*=', 'c20'), sadd('mul', 100),
         iff('mul', '161..', sset('mul', 160)),
         sop('dmg', '*=', 'mul'), sop('dmg', '*=', 'dscale'), sop('dmg', '/=', 'c10000'),
         # a sniped throw (a direct hit on a walking Steve) hits 30% harder; the bonus is spent by the first damage it touches
         sop('dmg', '*=', 'aimx'), sop('dmg', '/=', 'c100'), sset('aimx', 100),
         iff('mod', 3, sop('dmg', '*=', 'c6')), iff('mod', 3, sop('dmg', '/=', 'c5')),
         iff('dmg', '..0', sset('dmg', 1)),
         sop('mental', '-=', 'dmg'), iff('mental', '..-1', sset('mental', 0)), sop('total', '+=', 'dmg'),
         'execute if score #combo ek > #maxcombo ek run scoreboard players operation #maxcombo ek = #combo ek',
         'execute store result storage ek:s tmp.n int 1 run scoreboard players get #dmg ek',
         'execute store result storage ek:s tmp.c int 1 run scoreboard players get #combo ek',
         'function ek:fx/dmg_popup with storage ek:s tmp',
         iff('combo', '2..', 'function ek:fx/combo_popup with storage ek:s tmp'),
         iff('combo', '..1', 'data modify storage ek:s ab.combo set value ""'),
         snd('entity.player.attack.strong', 0.7, 0.8), 'function ek:game/bars')
    P.fn('fx/dmg_popup', '$execute positioned 0.5 71 0.5 run function ek:fx/popup {t:"멘탈 -$(n)",c:"red",s:"4.5"}')
    P.fn('fx/combo_popup', '$execute positioned 0.5 74.5 0.5 run function ek:fx/popup {t:"$(c)콤보!",c:"gold",s:"3.5"}',
         '$data modify storage ek:s ab.combo set value "   $(c)콤보"',
         snd('entity.experience_orb.pickup', 1.5, 0.8))
    P.fn('game/heal',
         sop('mental', '+=', 'heal'), 'execute if score #mental ek > #mmax ek run scoreboard players operation #mental ek = #mmax ek',
         'execute store result storage ek:s tmp.n int 1 run scoreboard players get #heal ek',
         'function ek:fx/heal_popup with storage ek:s tmp', 'function ek:game/bars')
    P.fn('fx/heal_popup', '$execute positioned 0.5 71 0.5 run function ek:fx/popup {t:"멘탈 +$(n)",c:"green",s:"3.5"}')
    P.fn('game/giveup_btn',
         iff('gu', '1..', 'return run function ek:lobby/enter'), sset('gu', 60),
         abar(t('한 번 더 우클릭하면 포기하고 로비로 돌아가.', 'red'), hold=60))

    # ------------------------------------------------------------------ beat engine
    P.fn('beat/flags_clear', [sset('f_' + f, 0) for f in FLAGS])
    P.fn('beat/start',
         'execute if score #beat ek > #maxbeat ek run scoreboard players operation #maxbeat ek = #beat ek',
         'execute if score #beat ek >= #maxbeat ek run scoreboard players set #redo ek 0',
         'function ek:beat/flags_clear', sset('wt', 0), sset('at', 0), sset('phase', 0),
         iff('idle', '1..', 'function ek:steve/idle_stop'), 'execute store result score #pace ek run random value 0..4',
         iff('mod', 2, 'execute store result score #pace ek run random value 3..4'), sset('halt', 0), sset('dash', 0),
         [iff('stage', s.n, f'function ek:s{s.n}/start') for s in stages], 'function ek:game/bars')
    P.fn('beat/tick', iff('phase', 0, 'function ek:beat/walk'), iff('phase', 1, 'function ek:beat/act'))
    P.fn('beat/walk',
         # now and then Steve stops on the way to fiddle with something (see v2.idle); nothing else happens while he does
         iff('idle', '1..', 'return run function ek:steve/idle_tick'),
         # he noticed something falling: freeze for a moment, or (below) bolt forward. Either way he never leaves his path
         iff('halt', '1..', 'return run ' + ssub('halt', 1)),
         sadd('wt', 1),
         iff('idlecd', '1..', ssub('idlecd', 1)),
         'execute if score #idlecd ek matches 0 if score #wt ek matches 12.. if score #redo ek matches 0 if score #f_bridge ek matches 0 run function ek:steve/idle_roll',
         iff('idle', '1..', 'return 0'),
         # every walk has its own pace (0: slow ... 4: hurried), so leading him with a throw is never quite the same twice
         sop('w5', '=', 'wt'), sop('w5', '%=', 'c5'), sop('w3', '=', 'wt'), sop('w3', '%=', 'c3'),
         'execute unless score #pace ek matches 0 run ' + S('function ek:steve/step'),
         'execute if score #pace ek matches 0 unless score #w5 ek matches 0 run ' + S('function ek:steve/step'),
         'execute if score #pace ek matches 3 if score #w5 ek matches 0 run ' + S('function ek:steve/step'),
         'execute if score #pace ek matches 4 if score #w3 ek matches 0 run ' + S('function ek:steve/step'),
         'execute if score #redo ek matches 1 as %s at @s run function ek:steve/step' % STEVE,
         iff('dash', '1..', 'function ek:steve/dash'),
         f'execute store result score #sx ek run data get entity {STEVE} Pos[0] 100',
         f'execute store result score #sz ek run data get entity {STEVE} Pos[2] 100',
         sop('sx', '-=', 'tx'), sop('sz', '-=', 'tz'),
         'execute if score #sx ek matches -32..32 if score #sz ek matches -32..32 run return run function ek:beat/arrive',
         iff('wt', '500..', 'function ek:beat/arrive'))
    P.fn('beat/arrive', sset('phase', 1), sset('at', 0),
         [iff('stage', s.n, f'function ek:s{s.n}/act') for s in stages])
    P.fn('beat/act', 'function ek:beat/act1',
         'execute if score #redo ek matches 1 if score #phase ek matches 1 if score #state ek matches 1 if score #intr ek matches 0 run function ek:beat/act1')
    P.fn('beat/act1', sadd('at', 1),
         [[sop(f'm{n}', '=', 'at'), sop(f'm{n}', '%=', f'c{n}')] for n in (4, 6, 8, 10, 20)],
         [iff('stage', s.n, f'function ek:s{s.n}/tick_beat') for s in stages],
         'execute if score #state ek matches 1 if score #intr ek matches 0 if score #phase ek matches 1 if score #at ek >= #alen ek run function ek:beat/done')
    P.fn('beat/done',
         [iff('stage', s.n, f'function ek:s{s.n}/end') for s in stages],
         'execute unless score #state ek matches 1 run return 0',
         iff('intr', '1..', 'return 0'),
         sadd('beat', 1),
         'execute if score #beat ek >= #blen ek run return run function ek:game/stage_clear',
         'function ek:beat/start')

    # ------------------------------------------------------------------ steve
    P.fn('steve/summon',
         'execute as @e[tag=ek.steve] run function ek:fx/vanish', 'kill @e[tag=ek.bub]',
         'summon mannequin ~ ~ ~ {Tags:["ek.steve"],NoGravity:1b,Invulnerable:1b,immovable:1b,CustomName:"Steve",CustomNameVisible:1b,hide_description:1b,profile:{texture:"minecraft:entity/player/wide/steve",model:"wide"},Rotation:[0f,0f]}',
         'function ek:steve/equip', sset('steve', 1), sset('snap', 1))
    arm = {1: ('air', 'iron_chestplate', 'air', 'air'), 2: ('iron_helmet', 'iron_chestplate', 'iron_leggings', 'iron_boots'),
           3: ('diamond_helmet', 'diamond_chestplate', 'iron_leggings', 'diamond_boots')}
    eq = [iff('armor', 0, f'item replace entity {STEVE} armor.{sl} with minecraft:air') for sl in ('head', 'chest', 'legs', 'feet')]
    for lv, (h, c, l, f) in arm.items():
        for sl, it in (('head', h), ('chest', c), ('legs', l), ('feet', f)):
            eq.append(iff('armor', lv, f'item replace entity {STEVE} armor.{sl} with minecraft:{it}'))
    P.fn('steve/equip', eq,
         iff('l_arrow', 1, f'item replace entity {STEVE} weapon.offhand with minecraft:shield'),
         iff('l_enderman', 1, f'item replace entity {STEVE} armor.head with minecraft:carved_pumpkin'),
         iff('l_piglin', 1, f'item replace entity {STEVE} armor.feet with minecraft:golden_boots'))
    P.fn('steve/step',
         'execute if score #diff ek matches 0 facing entity @e[tag=ek.tgt,limit=1] feet rotated ~ 0 run tp @s ^ ^ ^0.15 ~ ~',
         'execute if score #diff ek matches 1 facing entity @e[tag=ek.tgt,limit=1] feet rotated ~ 0 run tp @s ^ ^ ^0.17 ~ ~',
         'execute if score #diff ek matches 2 facing entity @e[tag=ek.tgt,limit=1] feet rotated ~ 0 run tp @s ^ ^ ^0.2 ~ ~')
    P.fn('steve/snap',
         'execute unless block ~ ~ ~ #ek:pass run return run tp @s ~ ~1 ~',
         'execute if block ~ ~-1 ~ #ek:pass run tp @s ~ ~-1 ~')
    P.fn('steve/say',
         '$tellraw @a {"text":"","extra":[{"text":"<Steve> ","color":"white"},{"text":"$(t)","color":"white"}]}',
         'kill @e[tag=ek.bub]',
         '$execute at @e[tag=ek.steve,limit=1] run summon text_display ~ ~3.1 ~ {Tags:["ek.bub"],billboard:"center",line_width:170,background:-1073741824,teleport_duration:2,view_range:4f,brightness:{sky:15,block:15},' + (DISPLAY_T % (4.2, 4.2, 4.2)) + ',text:{text:"$(t)"}}',
         sset('bubt', 75))
    P.fn('steve/bubble_tick', ssub('bubt', 1),
         f'execute as @e[tag=ek.bub,limit=1] at {STEVE} run tp @s ~ ~3.1 ~',
         iff('bubt', 0, 'kill @e[tag=ek.bub]'))
    P.fn('steve/hurt',
         at_s('particle minecraft:damage_indicator ~ ~1.5 ~ 0.3 0.3 0.3 0.1 8 force'),
         snd('entity.player.hurt'),
         f'data merge entity {STEVE} {{Invulnerable:0b}}', f'damage {STEVE} 1 minecraft:generic',
         f'data merge entity {STEVE} {{Invulnerable:1b,Health:20f}}')
    P.fn('steve/reset_pose', pose('standing'), f'data merge entity {STEVE} {{HasVisualFire:0b}}')
    P.fn('steve/lost',
         sadd('deaths', 1), sadd('dc_unknown', 1), tell(t('Steve이(가) 사망했습니다', 'white')),
         [iff('stage', s.n, f'function ek:s{s.n}/spawn') for s in stages], 'function ek:beat/restart')
    P.fn('say/low', 'execute store result score #r ek run random value 1..6',
         [iff('r', i + 1, say1(l)) for i, l in enumerate(
             ['하... 그만할까', '진짜 접을까', '이 월드 뭔가 이상한데', '왜 나한테만 이래', '오늘 운이 왜 이래', '멘탈 나간다 진짜'])])

    # ------------------------------------------------------------------ fx
    P.fn('fx/popup',
         '$summon text_display ~ ~ ~ {Tags:["ek.tmp","ek.rise","ek.new"],billboard:"center",line_width:400,background:0,shadow:1b,view_range:4f,brightness:{sky:15,block:15},transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[$(s)f,$(s)f,$(s)f]},text:{text:"$(t)",color:"$(c)",bold:true}}',
         'scoreboard players set @e[tag=ek.new] ek.life 45', 'tag @e[tag=ek.new] remove ek.new')
    P.fn('fx/tmp', 'scoreboard players remove @s ek.life 1',
         'execute if entity @s[tag=ek.rise] at @s run tp @s ~ ~0.06 ~',
         'execute if score @s ek.life matches ..0 run function ek:fx/vanish')
    P.fn('fx/vanish', 'tp @s 0 -300 0', 'kill @s')
    P.fn('fx/mob_step',
         f'execute if entity @s[tag=!ek.fast] facing entity {STEVE} feet rotated ~ 0 run tp @s ^ ^ ^0.17 ~ ~',
         f'execute if entity @s[tag=ek.fast] facing entity {STEVE} feet rotated ~ 0 run tp @s ^ ^ ^0.3 ~ ~',
         'execute at @s unless block ~ ~ ~ #ek:pass run return run tp @s ~ ~1 ~',
         'execute at @s if block ~ ~-1 ~ #ek:pass run tp @s ~ ~-1 ~')
    P.fn('fx/chase', 'execute as @e[tag=ek.chase] at @s unless entity @e[tag=ek.steve,distance=..1.5] run function ek:fx/mob_step')
    P.fn('fx/boom', 'particle minecraft:explosion_emitter ~ ~1 ~ 0 0 0 0 1 force', snd('entity.generic.explode', 1, 0.9))

    # ------------------------------------------------------------------ events framework
    P.fn('ev/cleanup',
         'execute as @e[tag=ek.mob] run function ek:fx/vanish', 'kill @e[tag=ek.evt]', 'kill @e[tag=ek.aim]', sset('snap', 1), sset('aimx', 100),
         'weather clear', 'time set 6000', 'function ek:steve/reset_pose',
         [iff('stage', s.n, f'function ek:s{s.n}/evclean') for s in stages if s.evclean])
    P.fn('beat/restart', [iff('stage', s.n, f'function ek:s{s.n}/restart') for s in stages], 'function ek:beat/start')
    P.fn('ev/end_resume', 'function ek:ev/cleanup', sset('intr', 0), 'function ek:cards/learn_check',
         'execute if score #mental ek matches 1.. run function ek:beat/restart')
    P.fn('ev/end_cont', 'function ek:ev/cleanup', sset('intr', 0), 'data modify storage ek:s status set from storage ek:s bstatus',
         'function ek:cards/learn_check')
    P.fn('ev/end_back', 'function ek:ev/cleanup', sset('intr', 0),
         [iff('stage', s.n, f'function ek:s{s.n}/spawn') for s in stages],
         'execute if score #mental ek matches 1.. run ' + say(['다녀왔다. 이번엔 넉넉하게 챙겼음', '왕복만 며칠이야', '다시 이어서 한다']),
         'function ek:cards/learn_check',
         'execute if score #mental ek matches 1.. run function ek:beat/restart')
    P.fn('ev/end_death', 'function ek:ev/cleanup', sset('intr', 0),
         [iff('stage', s.n, f'function ek:s{s.n}/spawn') for s in stages],
         'execute if score #mental ek matches 1.. run ' + say(['리스폰. 다시 간다', '하... 템 주우러 간다', '죽은 자리 어디였지'],
                                                              low=['또 죽었네 하하', '이게 몇 번째야', '...다시 간다']),
         'function ek:cards/learn_check',
         'execute if score #mental ek matches 1.. run function ek:beat/restart')
    P.fn('ev/end_major', 'function ek:ev/cleanup', sset('intr', 0), sadd('day', 1),
         'function ek:game/stage_setup', sset('redo', 1),
         tell(t('(아이템을 전부 잃어서 이번 단계를 처음부터 다시 한다)', 'gray')),
         'execute if score #mental ek matches 1.. run ' + say(['전부 날아갔네... 처음부터 다시', '장비 다시 맞춰 왔다', '이번엔 진짜 조심한다'],
                                                              low=['이걸 또 하라고?', '처음부터라니 말이 되냐', '하... 다시 캔다']),
         'function ek:cards/learn_check',
         'execute if score #mental ek matches 1.. run function ek:beat/start')

    # ------------------------------------------------------------------ cards: use / deal / hints
    P.fn('cards/use',
         iff('sl', 8, 'return run function ek:game/giveup_btn'),
         'execute if entity @e[tag=ek.box,tag=ek.pick] run return run function ek:box/open',
         iff('intr', '1..', 'return run function ek:cards/busy'),
         unl('steve', 1, 'return run function ek:cards/busy'),
         [iff('stage', n, f'return run function ek:cards/use_s{n}') for n in pools])
    P.fn('cards/busy', abar(t('지금은 억까 연출 중이야. 끝나고 써.', 'gray'), hold=30))
    P.fn('cards/no_energy', abar(t('기력이 부족해.', 'red'), hold=30), snd('block.note_block.bass', 0.6, 0.7))
    P.fn('cards/cant', abar(t('지금은 쓸 수 없는 카드야.', 'gray'), hold=30), snd('block.note_block.bass', 0.8, 0.5))
    P.fn('cards/locked', abar(t('아직 잠긴 카드야.', 'gray'), hold=30))
    P.fn('cards/noaim', abar(t('판 안쪽을 바라보고 던져.', 'gray'), hold=30), snd('block.note_block.bass', 0.8, 0.5))
    P.fn('cards/dropping', abar(t('먼저 던진 게 아직 떨어지는 중이야.', 'gray'), hold=20))
    P.fn('cards/deal', 'clear @a', 'function ek:cards/put')
    P.fn('cards/put', [iff('stage', n, f'function ek:cards/put_s{n}') for n in pools])
    for n, ids in pools.items():
        use = []; deal = []; hint = []; aimsel = []
        for slot, cid in enumerate(ids):
            c = C[cid]; un = UNLOCK[c.unlock]
            nm = ('◎ ' + c.name) if c.aim else c.name
            if c.unlock:
                use.append('execute if score #sl ek matches %d %srun return run function ek:cards/locked' % (slot, UNLOCK_NOT[c.unlock]))
                deal.append('execute %srun %s' % (UNLOCK_NOT[c.unlock], item(slot, '잠김: ' + c.name, 'dark_gray', 'barrier', [(UNLOCK_TXT[c.unlock], 'gray')], '@a')))
            use.append(iff('sl', slot, f'return run function ek:c/{cid}/' + ('aim' if c.aim else 'try')))
            lore = [('기력 %d' % c.cost, 'yellow'), (c.desc, 'gray'), ('노림수: ' + c.sweet_desc, 'aqua')]
            if c.aim:
                lore.append(('◎ 스티브 가까이에 떨어져야 통한다', 'green'))
                aimsel.append('execute if score #sl ek matches %d %srun function ek:ui/aim_on {f:"ek:c/%s/radii"}' % (slot, un, cid))
            deal.append('execute %sif score #l_%s ek matches 0 run %s' % (un, cid, item(slot, nm, c.color, c.icon, lore, '@a')))
            deal.append('execute %sif score #l_%s ek matches 1 run %s' % (un, cid, item(slot, nm + ' (간파당함)', 'gray', c.icon, lore + [('스티브가 대처법을 익혀서 효과가 절반', 'red')], '@a')))
            for term in c.sweet:
                hint.append('execute if score #sl ek matches %d %s%srun scoreboard players set #hint ek 1' % (
                    slot, un, ''.join('if score #f_%s ek matches 1 ' % f for f in term)))
        deal.append(item(8, '포기하고 로비로', 'red', 'barrier', [('두 번 우클릭', 'gray')], '@a'))
        P.fn(f'cards/use_s{n}', use)
        P.fn(f'cards/put_s{n}', deal)
        P.fn(f'ui/hint_s{n}', hint)
        P.fn(f'ui/aim_s{n}', aimsel)
    P.fn('cards/learn_check',
         ['execute if score #u_%s ek >= #learn ek if score #l_%s ek matches 0 run function ek:c/%s/learn' % (c.id, c.id, c.id) for c in cards])
    P.fn('cards/paid', sadd('ncards', 1), 'function ek:game/energy_bar', snd('ui.button.click', 1.2, 0.5))

    # ------------------------------------------------------------------ ui
    v2.ui(P, pools)

    # ------------------------------------------------------------------ helper commands for testing by hand
    P.fn('dev/next', 'execute if score #state ek matches 1 if score #stage ek matches ..6 run function ek:game/stage_clear')
    P.fn('dev/rebuild', 'function ek:setup/room', 'function ek:lobby/enter')
    P.fn('dev/unlock', sset('runs', 5), sset('wins', 5), 'function ek:lobby/enter')

    # ------------------------------------------------------------------ results
    P.fn('game/win', sset('state', 3), sset('res', 1), sset('rt', 0), sadd('wins', 1), sadd('runs', 1),
         'function ek:lobby/hidebars', 'clear @a', 'kill @e[tag=ek.bub]')
    P.fn('game/lose', sset('state', 3), sset('res', 0), sset('rt', 0), sadd('runs', 1),
         'function ek:lobby/hidebars', 'clear @a')
    v2.build(P, cards, pools)
    P.fn('result/tick', sadd('rt', 1), iff('res', 1, 'function ek:result/win_tick'), iff('res', 0, 'function ek:result/lose_tick'))
    quit_lines = ['아 안 해. 이 월드 삭제함', '이건 게임이 아니라 억까다', '접는다. 진짜로', '이 시드 뭔가 씌었어. 지운다']
    P.fn('result/quit_line', 'execute store result score #r ek run random value 1..%d' % len(quit_lines),
         [iff('r', i + 1, say1(l)) for i, l in enumerate(quit_lines)])
    P.fn('result/win_tick',
         iff('rt', 5, 'function ek:result/quit_line'),
         iff('rt', 60, tell(t('Steve이(가) 게임을 떠났습니다', 'yellow'))),
         iff('rt', 60, at_s('particle minecraft:poof ~ ~1 ~ 0.3 0.6 0.3 0.05 40 force')),
         iff('rt', 60, 'function ek:game/cleanup'), iff('rt', 60, snd('block.beacon.deactivate', 0.8)),
         iff('rt', 80, 'title @a times 5 70 20'),
         iff('rt', 80, 'title @a subtitle ' + comp(t('억까 성공', 'gold'))),
         iff('rt', 80, 'title @a title ' + comp(t('스티브가 월드를 삭제했습니다', 'red', True))),
         iff('rt', 80, snd('ui.toast.challenge_complete', 1, 0.8)),
         [iff('rt', 90 + 2 * k, 'fill -14 %d -14 14 %d 14 minecraft:air' % (86 - k, 86 - k)) for k in range(29)],
         [iff('rt', 90 + 8 * k, snd('block.stone.break', 0.6 + 0.05 * k, 0.7)) for k in range(8)],
         iff('rt', 155, 'function ek:result/panel'))
    P.fn('result/lose_tick',
         iff('rt', 1, 'title @a times 5 70 20'),
         iff('rt', 1, 'title @a subtitle ' + comp(t('억까 실패...', 'gray'))),
         iff('rt', 1, 'title @a title ' + comp(t('스티브가 엔더 드래곤을 처치했습니다', 'light_purple', True))),
         iff('rt', 1, tell(t('Steve이(가) 발전 과제 ', 'white'), t('[끝을 해방하다]', 'green'), t('를 달성했습니다!', 'white'))),
         iff('rt', 1, snd('ui.toast.challenge_complete', 1, 0.8)),
         iff('rt', 30, say1('드래곤 잡았다!!! 이게 되네')),
         iff('rt', 110, 'function ek:result/panel'))
    # score + grade + top3 causes
    sc_lines = ['execute if score #res ek matches 0 run scoreboard players set #grade ek 3',
                'execute if score #res ek matches 0 if score #total ek matches ..249 run scoreboard players set #grade ek 2',
                'execute if score #res ek matches 0 if score #total ek matches ..149 run scoreboard players set #grade ek 1',
                'execute if score #res ek matches 0 if score #total ek matches ..59 run scoreboard players set #grade ek 0',
                'execute if score #res ek matches 1 run scoreboard players set #grade ek 4',
                'execute if score #res ek matches 1 if score #day ek matches ..8 run scoreboard players set #grade ek 5',
                'execute if score #res ek matches 1 if score #day ek matches ..5 run scoreboard players set #grade ek 6']
    sc_lines.append('execute if score #grade ek > #best ek run scoreboard players operation #best ek = #grade ek')
    sc_lines += [iff('grade', i, 'data modify storage ek:s r.grade set value "%s"' % g) for i, g in enumerate(GRADES)]
    ck = list(CAUSES)
    sc_lines += [sop('tc_' + k, '=', 'dc_' + k) for k in ck]
    for rank in (1, 2, 3):
        sc_lines += [sset('bv', 0), sset('bi', -1)]
        for i, k in enumerate(ck):
            sc_lines.append('execute if score #tc_%s ek > #bv ek run scoreboard players set #bi ek %d' % (k, i))
            sc_lines.append(iff('bi', i, sop('bv', '=', 'tc_' + k)))
        sc_lines.append('data modify storage ek:s r.t%d set value "없음"' % rank)
        for i, k in enumerate(ck):
            sc_lines.append(iff('bi', i, 'data modify storage ek:s r.t%d set value "%s"' % (rank, CAUSES[k])))
            sc_lines.append(iff('bi', i, sset('tc_' + k, 0)))
        sc_lines.append('execute store result storage ek:s r.n%d int 1 run scoreboard players get #bv ek' % rank)
    for k, v in (('day', 'day'), ('deaths', 'deaths'), ('cards', 'ncards'), ('total', 'total'), ('combo', 'maxcombo'), ('thr', 'nthrow'), ('hit', 'nhit')):
        sc_lines.append('execute store result storage ek:s r.%s int 1 run scoreboard players get #%s ek' % (k, v))
    sc_lines.append(iff('res', 1, 'data modify storage ek:s r.res set value "억까 성공: 스티브가 접었다"'))
    sc_lines.append(iff('res', 0, 'data modify storage ek:s r.res set value "억까 실패: 드래곤이 잡혔다"'))
    P.fn('result/score', sc_lines)
    P.fn('result/panel', 'function ek:result/score', 'kill @e[tag=ek.ui]',
         'function ek:result/panel_m with storage ek:s r', 'execute as @a run function ek:result/give',
         iff('runs', 1, tell(t('  새 카드가 열렸다: 마른하늘에 날벼락 (1단계·4단계)', 'yellow'))),
         iff('runs', 2, tell(t('  새 카드가 열렸다: 피글린 분노 (5단계)', 'yellow'))),
         'execute if score #res ek matches 1 if score #wins ek matches 1 run ' + tell(t('  첫 승리 보상: 고인물 스티브, 발밑 꺼짐 (3단계·6단계), 수정 유폭 (7단계)', 'yellow')),
         snd('entity.player.levelup', 1, 0.8))
    P.fn('result/panel_m',
         '$summon text_display 0.5 74 0.5 {Tags:["ek.ui"],billboard:"center",line_width:400,background:-1073741824,view_range:4f,brightness:{sky:15,block:15},' + (DISPLAY_T % (3.2, 3.2, 3.2)) +
         ',text:{text:"",extra:[{text:"$(res)\\n",color:"gold",bold:true},{text:"$(day)일 걸림 · 사망 $(deaths)회 · 카드 $(cards)장\\n",color:"white"},{text:"멘탈 피해 $(total) · 최대 $(combo)콤보\\n",color:"white"},{text:"사망 원인: $(t1) $(n1)회 · $(t2) $(n2)회 · $(t3) $(n3)회\\n",color:"gray"},{text:"억까 등급: $(grade)",color:"aqua",bold:true}]}}',
         '$tellraw @a {"text":"","extra":[{"text":"\\n━━━━━━━━ 결과 ━━━━━━━━\\n","color":"gold"},{"text":"  $(res)\\n","color":"white"},{"text":"  $(day)일 걸림 · 사망 $(deaths)회 · 카드 $(cards)장 · 멘탈 피해 $(total) · 최대 $(combo)콤보\\n","color":"gray"},{"text":"  던진 카드 $(thr)번 중 $(hit)번 명중\\n","color":"gray"},{"text":"  사망 원인: $(t1) $(n1)회 · $(t2) $(n2)회 · $(t3) $(n3)회\\n","color":"gray"},{"text":"  억까 등급: $(grade)\\n","color":"aqua"},{"text":"━━━━━━━━━━━━━━━━━━━━\\n","color":"gold"}]}')
    P.fn('result/give', 'clear @s', 'function ek:result/put')
    P.fn('result/put', item(0, '로비로 돌아가기', 'gold', 'ender_eye', [('우클릭', 'gray')]))
    P.fn('result/use', 'execute if score #sl ek matches 0 if score #rt ek matches 160.. run function ek:lobby/enter')
