"""The rest of Bed Wars, the things the first full version had left out:
bedbugs, dream defenders, magic milk and the pop-up tower; the four traps with their queue, cushioned boots and the dragon buff;
the dragons of sudden death; and Hypixel's rule for breaking blocks - anything a player or a bot has put down can be broken, with any
item or with the bare hand, and the map itself cannot (a pristine copy of every map, far away, tells the two apart)."""
import zlib, json
from util import TEAMS, TEAM_KO, TEAM_COLOR, snbt, t, line, tell, q
import items

N = 8
def by_map(maps, name): return [f"execute if score #map bw matches {n + 1} run function bw:m/{m['id']}/{name}" for n, m in enumerate(maps)]
def per_team(fmt): return [fmt.format(i=i, dye=TEAMS[i], ko=TEAM_KO[i], col=TEAM_COLOR[i]) for i in range(N)]

BUG_LIFE = 15 * 20          # a bedbug lives 15 seconds
GOLEM_LIFE = 240 * 20       # a dream defender 4 minutes
MILK = 30 * 20              # magic milk: 30 seconds without traps
TRAP_RANGE = 10             # blocks from the bed
TRAP_PAUSE = 10             # seconds before the next trap in line can go off
MOB = '@e[tag=bw.mt,limit=1]'
FIGHT = 'tag=bw.fighter'


def dragon_immunity():
    """the part of an enchantment that makes its wearer immune to the dragon of its own team"""
    return {'minecraft:damage_immunity': [{'effect': {}, 'requirements': {'type': 'minecraft:any_of', 'terms': [
        {'type': 'minecraft:all_of', 'terms': [
            {'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:team': f'bw.{d}'}},
            {'type': 'minecraft:entity_properties', 'entity': 'attacker', 'predicate': {'minecraft:entity_type': 'minecraft:ender_dragon', 'minecraft:team': f'bw.{d}'}}]}
        for d in TEAMS]}}]}


def copy_offset(struct_dir, ids):
    """where the untouched copies of the maps stand: far to the south, at a place that changes whenever a map is rebuilt
    (so a copy made by an older pack is never mistaken for the map as it is now)"""
    import gzip
    h = 0
    for i in ids: h = zlib.crc32(gzip.decompress(open(f'{struct_dir}/{i}.nbt', 'rb').read()), h)
    return 100000 + 512 * (h % 1024), h % 2000000000 + 1


def block_tags(P, blocks_json, is_open, soft):
    names = [k.replace('minecraft:', '') for k in blocks_json]
    P.json('bw/tags/block/blastable.json', {'values': sorted('minecraft:' + n for n in soft | {'end_stone'})})
    thin = [n for n in names if not is_open(n) and (n.endswith(('_slab', '_stairs', '_fence', '_fence_gate', '_wall', '_pane', '_trapdoor', '_carpet', '_pressure_plate', '_button',
                                                                 '_sign', '_banner', '_candle', '_rod', '_chain', '_lantern', '_bars', '_head', '_skull', '_door'))
                                             or n in ('ladder', 'iron_bars', 'chain', 'lantern', 'soul_lantern', 'flower_pot', 'snow', 'scaffolding', 'cobweb', 'lightning_rod', 'end_rod',
                                                      'bell', 'grindstone', 'lectern', 'cake', 'candle', 'turtle_egg', 'sea_pickle', 'conduit', 'brewing_stand', 'cauldron', 'hopper',
                                                      'anvil', 'chipped_anvil', 'damaged_anvil', 'enchanting_table', 'daylight_detector', 'stonecutter', 'campfire', 'soul_campfire',
                                                      'lily_pad', 'big_dripleaf', 'small_dripleaf', 'pointed_dripstone', 'amethyst_cluster', 'bamboo', 'cactus', 'dragon_egg'))]
    P.json('bw/tags/block/thin.json', {'values': sorted('minecraft:' + n for n in thin)})
    # what a right click with an axe or shears would change for good: bark, wax, rust, pumpkins
    fix = [n for n in names if not n.startswith('stripped_') and (n.endswith(('_log', '_wood', '_stem', '_hyphae')) or n == 'bamboo_block' or n.startswith('waxed_')
                                                                 or n.startswith(('exposed_', 'weathered_', 'oxidized_')) or n == 'pumpkin')
           and not n.endswith(('_chest', '_door', '_trapdoor', '_bulb', 'melon_stem', 'pumpkin_stem', 'dripleaf_stem'))]
    P.json('bw/tags/block/axefix.json', {'values': sorted('minecraft:' + n for n in fix)})
    # the shop counters are the one thing a dragon must not eat
    P.json('minecraft/tags/block/dragon_immune.json', {'values': ['minecraft:' + w + o + 'copper_chest' for w in ('', 'waxed_') for o in ('', 'exposed_', 'weathered_', 'oxidized_')]})


def write(P, maps, resets, zoff):
    """P: the pack; maps: mapdata dicts (with name); resets: what pack.py knows about restoring each map; zoff: where the copies stand (z offset)"""
    load = [f'scoreboard objectives add {o} dummy' for o in ('bw.life', 'bw.mcd', 'bw.milk', 'bw.deny', 'bw.mfat', 'bw.dph', 'bw.bgc', 'bw.did', 'bw.dcl')] + [
        'scoreboard objectives add bw.usedmilk minecraft.used:minecraft.milk_bucket', 'scoreboard objectives add bw.usedchest minecraft.used:minecraft.chest',
        'scoreboard objectives add bw.usedgolem minecraft.used:minecraft.iron_golem_spawn_egg', 'scoreboard players set #3 bw 3']
    tick = []        # appended to game/tick

    # =================================================================== what was built and what is map
    here_open = {'type': 'minecraft:location_check', 'predicate': {'block': {'blocks': '#bw:open'}}}
    copy_open = {'type': 'minecraft:location_check', 'offsetZ': zoff, 'predicate': {'block': {'blocks': '#bw:open'}}}
    # a block a bot may dig through: one of the kinds players build with, standing where the map has nothing
    P.json('bw/predicate/built.json', {'type': 'minecraft:all_of', 'terms': [{'type': 'minecraft:location_check', 'predicate': {'block': {'blocks': '#bw:breakable'}}}, copy_open]})
    # anything at all that stands where the map has nothing
    P.json('bw/predicate/placed.json', {'type': 'minecraft:all_of', 'terms': [{'type': 'minecraft:inverted', 'term': here_open}, copy_open]})

    # ---- players: survival mode, and the speed of their hands says what may be broken.
    # Every tick the game looks along the player's line of sight. Something built (or a bed) within reach: the hands work.
    # Only map in sight: they do not. Thin map things (slabs, fences, carpets ...) do not end the look - the block behind may be the one meant.
    P.fn('game/aim0', ['scoreboard players set #rs bw 0', 'scoreboard players set #deny bw 1',
                       'execute if score #deny bw matches 1 anchored eyes positioned ^ ^ ^ run function bw:game/aim',
                       'execute unless score @s bw.deny = #deny bw run function bw:game/aimset'])
    P.fn('game/aim', ['execute if block ~ ~ ~ #bw:open run return run function bw:game/aimon',
                      'execute if predicate bw:placed run return run scoreboard players set #deny bw 0',
                      # the bed of one's own team (players are always red) is not for breaking
                      'execute if block ~ ~ ~ minecraft:red_bed run return 0',
                      'execute if block ~ ~ ~ #minecraft:beds run return run scoreboard players set #deny bw 0',
                      'execute if block ~ ~ ~ #bw:thin run function bw:game/aimon'])
    P.fn('game/aimon', ['scoreboard players add #rs bw 1', 'execute if score #rs bw matches ..50 positioned ^ ^ ^0.1 run function bw:game/aim'])
    P.fn('game/aimset', ['scoreboard players operation @s bw.deny = #deny bw',
                         'execute if score #deny bw matches 1 run attribute @s minecraft:block_break_speed base set 0',
                         'execute if score #deny bw matches 0 run attribute @s minecraft:block_break_speed base set 1'])
    tick.append(f'execute as @a[{FIGHT},gamemode=survival] at @s run function bw:game/aim0')

    # ---- an explosion takes map blocks of the soft kinds along with what was built: the copy gives them back a tick later, and the litter goes
    # (not once the dragons are out: what they have eaten must not grow back)
    P.fn('fb/after', [f'execute unless score #sudden bw matches 1 run clone ~-6 ~-6 ~{zoff - 6} ~6 ~6 ~{zoff + 6} ~-6 ~-6 ~-6 filtered #bw:blastable force',
                      'execute as @e[type=minecraft:item,distance=..9,tag=!bw.res] store result score @s bw.t run data get entity @s Age',
                      'kill @e[type=minecraft:item,distance=..9,tag=!bw.res,scores={bw.t=..3}]'])

    # ---- survival hands can also peel bark, scrape wax and carve pumpkins: the copy puts those back at once (1.8 has none of it)
    AX = ('wooden_axe', 'stone_axe', 'iron_axe', 'diamond_axe', 'shears')
    load += [f'scoreboard objectives add bw.ax{k} minecraft.used:minecraft.{n}' for k, n in enumerate(AX)]
    P.fn('game/axefix', [*[f'scoreboard players set @s bw.ax{k} 0' for k in range(len(AX))],
                         f'execute unless score #sudden bw matches 1 run clone ~-7 ~-7 ~{zoff - 7} ~7 ~7 ~{zoff + 7} ~-7 ~-7 ~-7 filtered #bw:axefix force'])
    tick += [f'execute as @a[{FIGHT},scores={{bw.ax{k}=1..}}] at @s run function bw:game/axefix' for k in range(len(AX))]
    tick += [f'scoreboard players set @a[scores={{bw.ax{k}=1..}}] bw.ax{k} 0' for k in range(len(AX))]

    # ---- "You can't place blocks here!": not on a generator, a spawn point or a shopkeeper (one block around each, three high).
    # A block item used near one of them: whatever was put down inside goes back into the hand that placed it.
    PB = ('red_wool', 'terracotta', 'red_stained_glass', 'end_stone', 'ladder', 'oak_planks', 'obsidian', 'sponge')
    load += [f'scoreboard objectives add bw.pb{k} minecraft.used:minecraft.{n}' for k, n in enumerate(PB)]
    PROT = '@e[type=minecraft:marker,tag=bw.prot,distance=..9]'
    P.fn('game/placed', ['tag @s add bw.placer', f'execute as {PROT} at @s run function bw:game/protbox', 'tag @s remove bw.placer'])
    P.fn('game/protbox', [f'execute positioned ~{dx} ~{dy} ~{dz} if predicate bw:placed run function bw:game/unplace' for dy in (0, 1, 2) for dx in (-1, 0, 1) for dz in (-1, 0, 1)])
    P.fn('game/unplace', ['loot give @a[tag=bw.placer,limit=1] mine ~ ~ ~ minecraft:netherite_pickaxe[enchantments={"minecraft:silk_touch":1}]', 'setblock ~ ~ ~ minecraft:air',
                          'title @a[tag=bw.placer] actionbar ' + snbt(t('여기에는 블록을 놓을 수 없어!', 'red')),
                          'execute as @a[tag=bw.placer] at @s run playsound minecraft:block.note_block.bass master @s ~ ~ ~ 0.7 0.7'])
    tick += [f'execute unless score #sudden bw matches 1 as @a[{FIGHT},scores={{bw.pb{k}=1..}}] at @s if entity {PROT} run function bw:game/placed' for k in range(len(PB))]
    tick += [f'scoreboard players set @a[scores={{bw.pb{k}=1..}}] bw.pb{k} 0' for k in range(len(PB))]
    for m in maps:
        P.add(f'm/{m["id"]}/begin', [f'tag @e[type=minecraft:marker,tag={tg}] add bw.prot' for tg in ('bw.spawn', 'bw.gen', 'bw.shop', 'bw.upgrade')])

    # ---- the copies: placed once per world (the first round on a map), their chunks loaded together with the map's
    for m in maps:
        mid = m['id']; r = resets[mid]
        P.fn(f'reset/{mid}/copy', [*r['copy'], f'scoreboard players set #cp_{mid} bw {r["copygen"]}'])

    # =================================================================== bedbugs and dream defenders
    TEAMJOIN = per_team('execute if score @s bw.team matches {i} run team join bw.{dye} @s')
    # a snowball named Bedbug: a marker rides on it; where the marker is left alone, the bug hatches
    P.fn('mob/bugball', ['tag @s add bw.bugball', f'scoreboard players operation @s bw.team = @e[{FIGHT},sort=nearest,limit=1] bw.team', 'function bw:mob/rider'])
    P.fn('mob/rider', ['summon minecraft:marker ~ ~ ~ {Tags:["bw","bw.round","bw.bugm","bw.bugnew"]}',
                       'scoreboard players operation @e[type=minecraft:marker,tag=bw.bugnew] bw.team = @s bw.team',
                       'ride @e[type=minecraft:marker,tag=bw.bugnew,limit=1] mount @s', 'tag @e[type=minecraft:marker,tag=bw.bugnew] remove bw.bugnew'])
    P.fn('mob/hatch', ['summon minecraft:silverfish ~ ~0.1 ~ {Tags:["bw","bw.round","bw.mob","bw.bug","bw.mobnew"],PersistenceRequired:1b,DeathLootTable:"minecraft:empty",CustomNameVisible:1b}',
                       'scoreboard players operation @e[type=minecraft:silverfish,tag=bw.mobnew] bw.team = @s bw.team',
                       'execute as @e[type=minecraft:silverfish,tag=bw.mobnew] run function bw:mob/bug_setup',
                       'playsound minecraft:entity.silverfish.ambient hostile @a ~ ~ ~ 1 1', 'kill @s'])
    P.fn('mob/bug_setup', ['tag @s remove bw.mobnew', 'item replace entity @s armor.head with minecraft:stone_button[enchantments={"bw:dragonkin":1}]', 'data modify entity @s drop_chances.head set value 0f', f'scoreboard players set @s bw.life {BUG_LIFE}', 'scoreboard players set @s bw.mcd 10', *TEAMJOIN,
                           *per_team('execute if score @s bw.team matches {i} run data modify entity @s CustomName set value {{text:"{ko} 팀 빈대",color:"{col}"}}')])
    # a golem out of the egg: it belongs to whoever just used an egg
    P.fn('mob/golem0', [f'scoreboard players operation @s bw.team = @e[{FIGHT},sort=nearest,limit=1] bw.team',
                        f'execute if entity @a[{FIGHT},scores={{bw.usedgolem=1..}},distance=..8] run scoreboard players operation @s bw.team = @a[{FIGHT},scores={{bw.usedgolem=1..}},sort=nearest,limit=1] bw.team',
                        'function bw:mob/golem_setup'])
    P.fn('mob/golem_setup', ['tag @s remove bw.mobnew', 'item replace entity @s armor.head with minecraft:stone_button[enchantments={"bw:dragonkin":1}]', 'data modify entity @s drop_chances.head set value 0f', f'scoreboard players set @s bw.life {GOLEM_LIFE}', 'scoreboard players set @s bw.mcd 20', *TEAMJOIN,
                             'data merge entity @s {DeathLootTable:"minecraft:empty",PersistenceRequired:1b,CustomNameVisible:1b}',
                             'attribute @s minecraft:attack_damage base set 10', 'attribute @s minecraft:follow_range base set 24',
                             'function bw:mob/golem_name', 'playsound minecraft:entity.iron_golem.repair neutral @a ~ ~ ~ 1 0.8'])
    P.fn('mob/golem_name', ['scoreboard players operation #s bw = @s bw.life', 'scoreboard players operation #s bw /= #20 bw',
                            'execute store result storage bw:tmp mob.s int 1 run scoreboard players get #s bw',
                            *per_team('execute if score @s bw.team matches {i} run data merge storage bw:tmp {{mob:{{ko:"{ko}",col:"{col}"}}}}'),
                            'function bw:mob/golem_name2 with storage bw:tmp mob'])
    P.fn('mob/golem_name2', ['$data modify entity @s CustomName set value [{text:"$(ko) 팀 드림 디펜더 ",color:"$(col)"},{text:"$(s)초",color:"gray"}]'])
    # every tick, each of them
    P.fn('mob/tick', ['scoreboard players remove @s bw.life 1', 'execute if score @s bw.life matches ..0 run return run function bw:mob/expire',
                      'scoreboard players remove @s[scores={bw.mcd=1..}] bw.mcd 1',
                      'scoreboard players operation #me bw = @s bw.team', 'tag @e[tag=bw.mt] remove bw.mt',
                      f'execute as @e[{FIGHT},distance=..16,sort=nearest] unless score @s bw.team = #me bw unless entity @e[tag=bw.mt,limit=1] run tag @s add bw.mt',
                      'execute unless entity @e[tag=bw.mt,limit=1] run return 0',
                      # a player: its own head does the chasing (a golem has to be told whom to hate); what its jaws do counts for its team
                      'execute if entity @s[tag=bw.golem] if entity @a[tag=bw.mt,limit=1] if score #t4 bw matches 0 run function bw:mob/anger',
                      'execute as @a[tag=bw.mt,distance=..3] run function bw:mob/credit',
                      # a bot: walk at it and bite
                      'execute if entity @e[type=minecraft:mannequin,tag=bw.mt,limit=1] run function bw:mob/chase'])
    P.fn('mob/credit', ['scoreboard players operation @s bw.lh = #me bw', 'scoreboard players set @s bw.lht 100'])
    P.fn('mob/anger', ['execute store result score #gt bw run time query gametime', 'scoreboard players add #gt bw 80',
                       'data modify entity @s angry_at set from entity @a[tag=bw.mt,limit=1] UUID',
                       'execute store result entity @s anger_end_time long 1 run scoreboard players get #gt bw'])
    P.fn('mob/chase', ['execute if entity @s[tag=bw.bug] if entity @e[tag=bw.mt,distance=..1.6] run return run function bw:mob/bite',
                       'execute if entity @s[tag=bw.golem] if entity @e[tag=bw.mt,distance=..2.6] run return run function bw:mob/bite',
                       f'execute facing entity {MOB} feet rotated ~ 0 run function bw:mob/step'])
    P.fn('mob/step', ['execute if entity @s[tag=bw.bug] if block ^ ^ ^0.5 #bw:open run return run tp @s ^ ^ ^0.24 ~ ~',
                      'execute if entity @s[tag=bw.golem] if block ^ ^ ^0.9 #bw:open if block ^ ^1 ^0.9 #bw:open run return run tp @s ^ ^ ^0.19 ~ ~',
                      # one block up
                      'execute if entity @s[tag=bw.bug] if block ^ ^1 ^0.5 #bw:open if block ~ ~1 ~ #bw:open run return run tp @s ^ ^1.05 ^0.3 ~ ~',
                      'execute if entity @s[tag=bw.golem] if block ^ ^1 ^0.9 #bw:open if block ^ ^2 ^0.9 #bw:open if block ^ ^3 ^0.9 #bw:open if block ~ ~3 ~ #bw:open run tp @s ^ ^1.05 ^0.5 ~ ~'])
    P.fn('mob/bite', ['execute unless score @s bw.mcd matches 0 run return 0',
                      'scoreboard players set @s[tag=bw.bug] bw.mcd 20', 'scoreboard players set @s[tag=bw.golem] bw.mcd 25',
                      f'scoreboard players operation {MOB} bw.lh = #me bw', f'scoreboard players set {MOB} bw.lht 200',
                      f'execute if entity @s[tag=bw.bug] run damage {MOB} 2 minecraft:mob_attack by @s',
                      f'execute if entity @s[tag=bw.golem] run damage {MOB} 9 minecraft:mob_attack by @s',
                      # the golem's blow throws its victim into the air
                      f'execute if entity @s[tag=bw.golem] run data modify entity {MOB} Motion[1] set value 0.45d',
                      'execute if entity @s[tag=bw.golem] run playsound minecraft:entity.iron_golem.attack hostile @a ~ ~ ~ 1 1'])
    P.fn('mob/expire', ['particle minecraft:poof ~ ~0.5 ~ 0.3 0.4 0.3 0.02 12', 'tp @s ~ -400 ~', 'kill @s'])
    tick += ['execute as @e[type=minecraft:marker,tag=bw.bugm] unless predicate bw:riding at @s run function bw:mob/hatch',
             'execute as @e[type=minecraft:iron_golem,tag=bw.mobnew] at @s run function bw:mob/golem0',
             'scoreboard players set @a[scores={bw.usedgolem=1..}] bw.usedgolem 0',
             'execute as @e[tag=bw.mob] at @s run function bw:mob/tick']
    P.add('game/second', ['execute as @e[type=minecraft:iron_golem,tag=bw.golem] run function bw:mob/golem_name'])
    # a bot throws a bedbug (run as the bot, at its eyes, looking where it should fly)
    P.fn('mob/throw', ['execute positioned 0.0 0.0 0.0 run tp @e[type=minecraft:marker,tag=bw.vec,limit=1] ^ ^ ^1.1',
                       'summon minecraft:snowball ~ ~ ~ {Tags:["bw","bw.round","bw.seen","bw.bugball","bw.ballnew"],Item:{id:"minecraft:snowball",count:1}}',
                       'data modify entity @e[type=minecraft:snowball,tag=bw.ballnew,limit=1] Motion set from entity @e[type=minecraft:marker,tag=bw.vec,limit=1] Pos',
                       'scoreboard players operation @e[type=minecraft:snowball,tag=bw.ballnew] bw.team = @s bw.team',
                       'execute as @e[type=minecraft:snowball,tag=bw.ballnew] at @s run function bw:mob/rider',
                       'tag @e[type=minecraft:snowball,tag=bw.ballnew] remove bw.ballnew', 'playsound minecraft:entity.snowball.throw player @a ~ ~ ~ 0.6 0.6'])
    P.fn('mob/botgolem', ['summon minecraft:iron_golem ~ ~ ~ {Tags:["bw","bw.round","bw.mob","bw.golem","bw.botgolem"]}',
                          'scoreboard players operation @e[type=minecraft:iron_golem,tag=bw.botgolem] bw.team = @s bw.team',
                          'execute as @e[type=minecraft:iron_golem,tag=bw.botgolem] at @s run function bw:mob/golem_setup',
                          'tag @e[type=minecraft:iron_golem,tag=bw.botgolem] remove bw.botgolem'])

    # =================================================================== magic milk
    P.fn('item/milk', ['scoreboard players set @s bw.usedmilk 0', f'scoreboard players set @s bw.milk {MILK}', 'clear @s minecraft:bucket',
                       # milk washes every effect off: the ones that belong to the round come back
                       'effect give @s minecraft:night_vision infinite 0 true', 'effect give @s minecraft:saturation infinite 0 true',
                       tell('@s', t('마법 우유', 'aqua'), t('를 마셨어. 30초 동안 함정에 걸리지 않아.', 'gray'))])
    tick += [f'execute as @a[{FIGHT},scores={{bw.usedmilk=1..}}] run function bw:item/milk', 'scoreboard players set @a[scores={bw.usedmilk=1..}] bw.usedmilk 0',
             'scoreboard players remove @e[scores={bw.milk=1..}] bw.milk 1']

    # =================================================================== the pop-up tower
    TOWER = 'minecraft:chest{components:{"minecraft:custom_data":{bw:"tower"}}}'
    P.fn('item/tower0', ['scoreboard players set @s bw.usedchest 0', 'scoreboard players set #rs bw 0', 'scoreboard players set #hit bw 0',
                         'execute anchored eyes positioned ^ ^ ^ run function bw:item/towerray',
                         # not on the line of sight (the head turned in that instant): it is somewhere close by
                         f'execute if score #hit bw matches 0 store result score #n bw run fill ~-5 ~-5 ~-5 ~5 ~5 ~5 minecraft:air replace {TOWER}',
                         'execute if score #hit bw matches 0 if score #n bw matches 1.. anchored eyes positioned ^ ^ ^2 run function bw:item/tower1'])
    P.fn('item/towerray', [f'execute if block ~ ~ ~ {TOWER} run return run function bw:item/tower1', 'scoreboard players add #rs bw 1',
                           'execute if score #rs bw matches ..60 positioned ^ ^ ^0.1 run function bw:item/towerray'])
    P.fn('item/tower1', ['scoreboard players set #hit bw 1', f'execute if block ~ ~ ~ {TOWER} run setblock ~ ~ ~ minecraft:air',
                         'execute align xyz positioned ~0.5 ~ ~0.5 run summon minecraft:marker ~ ~ ~ {Tags:["bw","bw.round","bw.tower","bw.tnew"]}',
                         'scoreboard players operation @e[type=minecraft:marker,tag=bw.tnew] bw.team = @s bw.team', 'scoreboard players set @e[type=minecraft:marker,tag=bw.tnew] bw.t 0',
                         # the tower faces the way its builder looks: the door towards the builder
                         'execute if entity @s[y_rotation=-45..45] as @e[type=minecraft:marker,tag=bw.tnew] at @s run tp @s ~ ~ ~ 0 0',
                         'execute if entity @s[y_rotation=45..135] as @e[type=minecraft:marker,tag=bw.tnew] at @s run tp @s ~ ~ ~ 90 0',
                         'execute if entity @s[y_rotation=135..180] as @e[type=minecraft:marker,tag=bw.tnew] at @s run tp @s ~ ~ ~ 180 0',
                         'execute if entity @s[y_rotation=-180..-135] as @e[type=minecraft:marker,tag=bw.tnew] at @s run tp @s ~ ~ ~ 180 0',
                         'execute if entity @s[y_rotation=-135..-45] as @e[type=minecraft:marker,tag=bw.tnew] at @s run tp @s ~ ~ ~ -90 0',
                         'tag @e[type=minecraft:marker,tag=bw.tnew] remove bw.tnew'])
    # the tower, seen from its builder: left/right u, up y, away v; the chest stood where the door is
    ring5 = [(u, v) for u in range(-2, 3) for v in range(-2, 3) if max(abs(u), abs(v)) == 2 and min(abs(u), abs(v)) <= 1]
    disc5 = [(u, v) for u in range(-2, 3) for v in range(-2, 3)]
    ring7 = [(u, v) for u in range(-3, 4) for v in range(-3, 4) if max(abs(u), abs(v)) == 3 and min(abs(u), abs(v)) <= 2]
    teeth = [(u, v) for (u, v) in ring7 if (u if abs(v) == 3 else v) % 2 == 0]
    LAD = (0, 1)                                         # the ladder climbs the inside of the far wall
    cell = lambda u, y, v: f'^{u} ^{y} ^{v + 2}'
    FACE = [('-1..1', 'north'), ('89..91', 'east'), ('179..180', 'south'), ('-180..-179', 'south'), ('-91..-89', 'west')]
    def ladder(y): return [f'execute if entity @s[y_rotation={rot}] run setblock {cell(LAD[0], y, LAD[1])} minecraft:ladder[facing={f}] keep' for rot, f in FACE]
    layers = []
    for y in range(5):
        layers.append([f'$setblock {cell(u, y, v)} minecraft:$(w) keep' for (u, v) in ring5 if not (y <= 1 and (u, v) == (0, -2))] + ladder(y))
    layers.append([f'$setblock {cell(u, 5, v)} minecraft:$(w) keep' for (u, v) in disc5 + ring7 if (u, v) != LAD] + ladder(5))
    layers.append([f'$setblock {cell(u, 6, v)} minecraft:$(w) keep' for (u, v) in teeth])
    for k, ls in enumerate(layers):
        P.fn(f'item/tl{k}', ls + ['playsound minecraft:block.wool.place block @a ~ ~ ~ 1 0.8'])
    P.fn('item/tower_t', [f'$execute if score @s bw.t matches {2 * k + 1} run function bw:item/tl{k} {{w:"$(w)"}}' for k in range(len(layers))] +
         [f'execute if score @s bw.t matches {2 * len(layers) + 1}.. run kill @s'])
    P.fn('item/towertick', ['scoreboard players add @s bw.t 1', *per_team('execute if score @s bw.team matches {i} run function bw:item/tower_t {{w:"{dye}_wool"}}')])
    tick += [f'execute as @a[{FIGHT},scores={{bw.usedchest=1..}}] at @s run function bw:item/tower0', 'scoreboard players set @a[scores={bw.usedchest=1..}] bw.usedchest 0',
             'execute as @e[type=minecraft:marker,tag=bw.tower] at @s run function bw:item/towertick']

    # =================================================================== traps
    P.fn('trap/add', ['$execute if score #tqn$(i) bw matches 2 run scoreboard players set #tq$(i)c bw $(k)',
                      '$execute if score #tqn$(i) bw matches 1 run scoreboard players set #tq$(i)b bw $(k)',
                      '$execute if score #tqn$(i) bw matches 0 run scoreboard players set #tq$(i)a bw $(k)',
                      '$scoreboard players add #tqn$(i) bw 1'])
    ENEMY = lambda i: f'@e[{FIGHT},distance=..{TRAP_RANGE}]'
    NAMES = {d['k']: d['name'] for d in items.TRAPS}
    # run as an enemy who has come near the bed of team i, at that bed
    P.fn('trap/hit', ['$execute if score #tcd$(i) bw matches 1.. run return 0',
                      # a bot that knows what it is doing has drunk its milk on the way
                      'execute if entity @s[tag=bw.bot] if score #lvl bw matches 10.. run function bw:trap/botmilk',
                      'execute if score @s bw.milk matches 1.. run return 0',
                      f'$scoreboard players set #tcd$(i) bw {TRAP_PAUSE}',
                      '$scoreboard players operation #k bw = #tq$(i)a bw',
                      '$scoreboard players operation #tq$(i)a bw = #tq$(i)b bw', '$scoreboard players operation #tq$(i)b bw = #tq$(i)c bw', '$scoreboard players set #tq$(i)c bw 0',
                      '$scoreboard players remove #tqn$(i) bw 1',
                      '$scoreboard players set #ti bw $(i)',
                      *[f'execute if score #k bw matches {k} run function bw:trap/k{k}' for k in (1, 2, 3, 4)],
                      *[f'execute if score #k bw matches {k} run data modify storage bw:tmp trap.n set value {q(NAMES[k])}' for k in (1, 2, 3, 4)],
                      '$title @a[tag=bw.play,scores={bw.team=$(i)}] times 0 50 10',
                      '$title @a[tag=bw.play,scores={bw.team=$(i)}] subtitle [{storage:"bw:tmp",nbt:"trap.n",color:"yellow"},{text:" - 적이 기지에 들어왔어",color:"gray"}]',
                      '$title @a[tag=bw.play,scores={bw.team=$(i)}] title {text:"함정 발동!",color:"red",bold:true}',
                      '$execute as @a[tag=bw.play,scores={bw.team=$(i)}] at @s run playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 1 0.6'])
    foes = f'execute as @e[{FIGHT},distance=..{TRAP_RANGE + 2}] unless score @s bw.team = #ti bw unless score @s bw.milk matches 1.. run '
    P.fn('trap/k1', [foes + 'function bw:trap/blind'])
    P.fn('trap/blind', ['effect give @s[type=minecraft:player] minecraft:blindness 8 0', 'effect give @s[type=minecraft:player] minecraft:slowness 8 1',
                        'scoreboard players set @s[tag=bw.bot] bw.slow 160', 'title @s[type=minecraft:player] actionbar ' + snbt(t('함정에 걸렸어! 눈이 멀고 느려졌어.', 'red'))])
    P.fn('trap/k2', [f'execute as @e[{FIGHT},distance=..24] if score @s bw.team = #ti bw run function bw:trap/counter'])
    P.fn('trap/counter', ['effect give @s[type=minecraft:player] minecraft:speed 15 1', 'effect give @s[type=minecraft:player] minecraft:jump_boost 15 1',
                          # a bot at home drops what it is doing and goes for the intruder
                          'execute if entity @s[tag=bw.bot] run scoreboard players set @s bw.calm 0'])
    P.fn('trap/k3', [foes + 'function bw:trap/alarm',
                     'execute as @a[tag=bw.play] if score @s bw.team = #ti bw at @s run playsound minecraft:block.bell.use master @s ~ ~ ~ 1 2'])
    P.fn('trap/alarm', ['effect clear @s minecraft:invisibility', 'effect give @s minecraft:glowing 10 0 true',
                        'title @s[type=minecraft:player] actionbar ' + snbt(t('경보 함정! 모습이 드러났어.', 'red')),
                        'tellraw @a[tag=bw.play] [{text:"경보! ",color:"red",bold:true},{selector:"@s"},{text:"이(가) 기지에 들어왔어.",color:"gray",bold:false}]'])
    P.fn('trap/k4', [foes + 'function bw:trap/fatigue'])
    P.fn('trap/fatigue', ['effect give @s[type=minecraft:player] minecraft:mining_fatigue 10 0', 'scoreboard players set @s[tag=bw.bot] bw.mfat 200',
                          'title @s[type=minecraft:player] actionbar ' + snbt(t('함정에 걸렸어! 채굴 피로.', 'red'))])
    P.fn('trap/botmilk', [f'execute if score @s bw.team matches {i} if score #wau{i} bw matches 4.. run function bw:trap/botmilk2 {{i:{i}}}' for i in range(1, N)])
    P.fn('trap/botmilk2', ['$scoreboard players remove #wau$(i) bw 4', f'scoreboard players set @s bw.milk {MILK}'])
    for m in maps:
        sec = []
        for i in range(N):
            bx, by, bz = m['teams'][i]['bed']
            sec += [f'execute if score #tcd{i} bw matches 1.. run scoreboard players remove #tcd{i} bw 1',
                    f'execute if score #tq{i}a bw matches 1.. if score #tcd{i} bw matches 0 positioned {bx} {by} {bz} as @e[{FIGHT},distance=..{TRAP_RANGE}] unless score @s bw.team matches {i} run function bw:trap/hit {{i:{i}}}']
        P.add(f'm/{m["id"]}/sec', sec)
    P.add('game/tick', ['scoreboard players remove @e[type=minecraft:mannequin,scores={bw.mfat=1..}] bw.mfat 1'])

    # =================================================================== sudden death: the dragons
    # One dragon for every team that is still in (two with the Dragon Buff). They are the game's own dragons, held in their hovering
    # state and flown by the pack: down at an enemy or at one of the islands, through whatever is in the way, then up and down again.
    # Their own team is immune to them (an enchantment on helmets says so).
    dk = dragon_immunity()
    P.json('bw/enchantment/dragonkin.json', {'description': {'text': '드래곤의 가호'}, 'supported_items': '#minecraft:enchantable/head_armor', 'weight': 1, 'max_level': 1,
                                             'min_cost': {'base': 1, 'per_level_above_first': 0}, 'max_cost': {'base': 1, 'per_level_above_first': 0}, 'anvil_cost': 1,
                                             'slots': ['head'], 'effects': dk})
    P.json('bw/item_modifier/dragonkin.json', {'type': 'minecraft:set_enchantments', 'enchantments': {'bw:dragonkin': 1}, 'add': False})
    # Every dragon has a point of its own to fly at (a marker with the same number): where an enemy stood when it chose, or a place on one of
    # the islands. It flies through that point - through the island, if that is where it is - then climbs for a few seconds and chooses again.
    # A player who keeps moving is missed; one who stands still is not.
    P.fn('dragon/setup', ['tag @s remove bw.dnew', 'scoreboard players set @s bw.dph 0', 'execute store result score @s bw.t run random value 0..80',
                          'scoreboard players set @s bw.dcl 100', 'scoreboard players add #did bw 1', 'scoreboard players operation @s bw.did = #did bw',
                          'summon minecraft:marker ~ ~ ~ {Tags:["bw","bw.round","bw.dtm","bw.dtnew"]}',
                          'scoreboard players operation @e[type=minecraft:marker,tag=bw.dtnew] bw.did = #did bw', 'tag @e[type=minecraft:marker,tag=bw.dtnew] remove bw.dtnew', *TEAMJOIN,
                          *per_team('execute if score @s bw.team matches {i} run data modify entity @s CustomName set value {{text:"{ko} 팀 드래곤",color:"{col}"}}')])
    for m in maps:
        cx, cy, cz = m['center']; top = m['top_y'] + 24
        dr = ['scoreboard players set #did bw 0']
        for i in range(N):
            import math
            ang = math.radians(45 * i); x = cx + round(30 * math.cos(ang)); z = cz + round(30 * math.sin(ang))
            one = (f'summon minecraft:ender_dragon {x} {top} {z} {{Tags:["bw","bw.round","bw.dragon","bw.dnew"],Invulnerable:1b,DragonPhase:10,PersistenceRequired:1b}}')
            dr += [f'execute if score #out{i} bw matches 0 run {one}',
                   f'execute if score #out{i} bw matches 0 if score #dbuff{i} bw matches 1.. run {one}',
                   f'scoreboard players set @e[type=minecraft:ender_dragon,tag=bw.dnew] bw.team {i}',
                   'execute as @e[type=minecraft:ender_dragon,tag=bw.dnew] at @s run function bw:dragon/setup']
        P.fn(f'm/{m["id"]}/dragons', dr)
        # up: towards a point high above the middle of the map
        P.fn(f'm/{m["id"]}/dragon_up', [f'execute facing {cx} {top + 10} {cz} run tp @s ^ ^ ^0.5 ~180 0'])
    DT = '@e[type=minecraft:marker,tag=bw.dtc,limit=1]'
    P.fn('dragon/tick', ['scoreboard players add @s bw.t 1', 'scoreboard players operation #me bw = @s bw.team', 'scoreboard players operation #did bw = @s bw.did',
                         'tag @e[type=minecraft:marker,tag=bw.dtc] remove bw.dtc', 'execute as @e[type=minecraft:marker,tag=bw.dtm] if score @s bw.did = #did bw run tag @s add bw.dtc',
                         # whoever its head reaches is its team's doing
                         f'execute as @e[{FIGHT},distance=..10] unless score @s bw.team = #me bw run function bw:mob/credit',
                         'execute if score @s bw.dph matches 1 run function bw:dragon/dive',
                         'execute if score @s bw.dph matches 0 run function bw:dragon/up'])
    P.fn('dragon/dive', [f'execute facing entity {DT} feet run tp @s ^ ^ ^0.62 ~180 0',
                         f'execute if entity @e[type=minecraft:marker,tag=bw.dtc,distance=..5] run function bw:dragon/turn', 'execute if score @s bw.t matches 300.. run function bw:dragon/turn'])
    P.fn('dragon/turn', ['scoreboard players set @s bw.dph 0', 'scoreboard players set @s bw.t 0', 'execute store result score @s bw.dcl run random value 50..130'])
    P.fn('dragon/up', [*by_map(maps, 'dragon_up'), 'execute if score @s bw.t >= @s bw.dcl run function bw:dragon/pick'])
    P.fn('dragon/pick', ['scoreboard players set @s bw.dph 1', 'scoreboard players set @s bw.t 0', 'tag @e[tag=bw.dt] remove bw.dt',
                         'execute store result score #rn bw run random value 1..100',
                         f'execute if score #rn bw matches ..55 as @e[{FIGHT},distance=..300,sort=random] unless score @s bw.team = #me bw unless entity @e[tag=bw.dt,limit=1] run tag @s add bw.dt',
                         'execute unless entity @e[tag=bw.dt,limit=1] run tag @e[type=minecraft:marker,tag=bw.hub,sort=random,limit=1] add bw.dt',
                         f'execute at @e[tag=bw.dt,limit=1] run tp {DT} ~ ~1 ~', 'tag @e[tag=bw.dt] remove bw.dt'])
    P.fn('dragon/begin', ['gamerule mob_griefing true', *by_map(maps, 'dragons'),
                          # helmets keep their wearers safe from their own dragon
                          f'execute as @a[{FIGHT}] run item modify entity @s armor.head bw:dragonkin',
                          'execute as @a at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 0.8'])
    P.fn('dragon/end', ['execute as @e[type=minecraft:ender_dragon,tag=bw.dragon] run data merge entity @s {Silent:1b}',
                        'tp @e[type=minecraft:ender_dragon,tag=bw.dragon] 0 -400 0', 'kill @e[type=minecraft:ender_dragon,tag=bw.dragon]', 'gamerule mob_griefing false'])
    tick.append('execute if score #sudden bw matches 1 as @e[type=minecraft:ender_dragon,tag=bw.dragon] at @s run function bw:dragon/tick')
    P.add('game/tick', tick)
    return dict(load=load)
