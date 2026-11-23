"""The opponents. Each of the seven other teams has one computer player: a mannequin (a player model without a mind of its own)
that this file moves the way a person would play Bed Wars - it collects from its forge, buys gear, builds a bed defence,
bridges to a neighbour with its head down and its knees bent, fights with a sword, breaks beds, and comes back five seconds after dying.
How well it does all that depends on the stage the player has reached; from stage 15 on the bots cheat too.

Walking is done by the game itself: the bot's helmet carries an enchantment whose only effect is a small push forward every tick while
a score says 'walk'. That is exactly how a player's own movement works, so knockback, friction, jumping and falling all behave as they do for people."""
import math
from util import TEAMS, TEAM_KO, TEAM_COLOR, TEAM_DYE_RGB, Raw, snbt, t, line, tell, q
import items

N = 8
BOTS = range(1, N)
SKINS = ['wide/steve', 'slim/alex', 'slim/ari', 'wide/efe', 'wide/kai', 'slim/makena', 'slim/noor', 'wide/sunny', 'slim/zuri']
NAMES = ['ItzMango', 'sn0wfall', 'Kaito_', 'NotLuca', 'Zephyrr', 'qwertyPvP', 'Mochi_22', 'BedBreaker12', 'xRushy', 'Tofu_Lord', 'p1nkbean', 'Deokbokki',
         'KimchiKing', 'vortexx_', 'Hanul', 'Jisoo_BW', 'lil_creeper', 'Dalgona', 'woolwalker', 'N0tAfk', 'Seojun07', 'MinGyu_', 'sweatyTaco', 'obbyrusher',
         'Yuna_Luv', 'BridgeGod99', 'Haneul_', 'egg_bridge', 'doyun2010', 'clutchmaster', 'Ramyun', 'gapple_gobbler', 'SoraSky', 'TNTjunho', 'ttv_wooly',
         'Bada_', 'fireball_fred', 'JiHo_zz', 'voidwalkr', 'Nabi_', 'sunbae', 'RiceCake', 'oppaPvP', 'Byeol', 'laggyboi', 'Gureum', 'noobslayer_kr', 'Hodu']
C76 = math.cos(math.radians(76))
# what "walk" means, as a push per tick: on the ground a steady pace v needs v * 0.454, in the air v * 0.09 (friction 0.546 and 0.91)
FWD = {1: 0.0647, 2: 0.2158, 3: 0.2806, 4: 0.108}            # sneak, walk, sprint, trapped
BACK = {-1: 0.0647, -2: 0.13, -3: 0.2158}                     # bridging backwards, eyes on the block below (pitch 76)

# stage ->  reach*100, hit %, ticks between swings, walk mode, bridge mode, forge %, defence tier, % to go for a human, strafes, knockback taken %
LEVELS = [
    (270, 35, 16, 2, -1, 45, 0, 10, 0, 100), (280, 40, 15, 2, -1, 50, 1, 12, 0, 100), (290, 45, 14, 2, -1, 55, 1, 14, 0, 100), (300, 50, 14, 2, -1, 60, 1, 16, 1, 100),
    (300, 55, 13, 3, -2, 65, 2, 18, 1, 100), (300, 60, 13, 3, -2, 70, 2, 20, 1, 100), (300, 65, 12, 3, -2, 75, 2, 22, 1, 100), (300, 70, 12, 3, -2, 80, 2, 25, 1, 100),
    (310, 75, 11, 3, -2, 85, 3, 28, 1, 100), (310, 78, 11, 3, -3, 90, 3, 30, 1, 100), (320, 81, 11, 3, -3, 95, 3, 33, 1, 100), (320, 84, 10, 3, -3, 100, 3, 36, 1, 100),
    (330, 87, 10, 3, -3, 100, 4, 40, 1, 100), (340, 90, 10, 3, -3, 100, 4, 45, 1, 90), (350, 93, 10, 3, -3, 100, 4, 50, 1, 80),
    # from here on they cheat: reach, velocity, scaffold (they bridge at a run, facing forward)
    (370, 95, 10, 3, 3, 100, 4, 55, 1, 60), (380, 96, 10, 3, 3, 100, 4, 58, 1, 50), (400, 97, 10, 3, 3, 100, 4, 60, 1, 35), (420, 98, 10, 3, 3, 100, 4, 62, 1, 20),
    (450, 99, 10, 3, 3, 100, 4, 65, 1, 0), (450, 99, 10, 3, 3, 100, 4, 70, 1, 0)]
REACHES = sorted({l[0] for l in LEVELS})
# how long a bot needs for a block, in ticks, by its tool (none, wooden, iron, diamond)
MINE = [('#minecraft:wool', [22, 10, 7, 5]), ('minecraft:oak_planks', [45, 24, 14, 9]), ('minecraft:ladder', [12, 8, 6, 5]), ('minecraft:terracotta', [50, 20, 12, 8]),
        ('#bw:glass', [9, 9, 9, 9]), ('minecraft:end_stone', [150, 60, 30, 18]), ('minecraft:obsidian', [9999, 9999, 9999, 55]), ('minecraft:tnt', [4, 4, 4, 4]),
        ('minecraft:sponge', [14, 14, 14, 14]), ('minecraft:wet_sponge', [14, 14, 14, 14])]
SWORDS = ['wooden_sword', 'stone_sword', 'iron_sword', 'diamond_sword']
SWORD_DMG = [400, 500, 600, 700]
ARMOR = ['leather', 'chainmail', 'iron', 'diamond']
TOOLS = [None, 'wooden_pickaxe', 'iron_pickaxe', 'diamond_pickaxe']

def per_bot(fmt): return [fmt.format(i=i, dye=TEAMS[i], ko=TEAM_KO[i], col=TEAM_COLOR[i]) for i in BOTS]
def by_team(name, rng=BOTS): return [f'execute if score @s bw.team matches {i} run function bw:ai/{name}{i}' for i in rng]
def by_map(maps, name): return [f"execute if score #map bw matches {n + 1} run function bw:m/{m['id']}/{name}" for n, m in enumerate(maps)]
GOAL = lambda i: f'@e[type=minecraft:marker,tag=bw.g{i},limit=1]'
VEC = '@e[type=minecraft:marker,tag=bw.vec,limit=1]'
FOE = '@e[tag=bw.foe,limit=1]'

def enchantments(P):
    score = lambda obj, v: {'type': 'minecraft:entity_scores', 'entity': 'this', 'scores': {obj: v}}
    ground = lambda g: {'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:flags': {'is_on_ground': g}}}
    def imp(direction, mag, obj, v, g):
        return {'effect': {'type': 'minecraft:apply_impulse', 'direction': direction, 'coordinate_scale': [1, 0, 1], 'magnitude': round(mag, 4)},
                'requirements': {'type': 'minecraft:all_of', 'terms': [score(obj, v), ground(g)]}}
    tick = []
    for v, sp in FWD.items(): tick += [imp([0, 0, 1], sp * 0.454, 'bw.mf', v, True), imp([0, 0, 1], sp * 0.09, 'bw.mf', v, False)]
    for v, sp in BACK.items(): tick += [imp([0, 0, -1], sp * 0.454 / C76, 'bw.mf', v, True), imp([0, 0, -1], sp * 0.09 / C76, 'bw.mf', v, False)]
    for v, d in ((1, [1, 0, 0]), (-1, [-1, 0, 0])): tick += [imp(d, 0.05, 'bw.ms', v, True), imp(d, 0.01, 'bw.ms', v, False)]
    base = lambda effects: {'description': {'text': ''}, 'supported_items': '#minecraft:enchantable/durability', 'weight': 1, 'max_level': 1,
                            'min_cost': {'base': 1, 'per_level_above_first': 0}, 'max_cost': {'base': 1, 'per_level_above_first': 0}, 'anvil_cost': 1,
                            'slots': ['head'], 'effects': effects}
    import extras
    P.json('bw/enchantment/bot.json', base({'minecraft:tick': tick, 'minecraft:post_attack': [
        {'enchanted': 'victim', 'affected': 'victim', 'effect': {'type': 'minecraft:run_function', 'function': 'bw:ai/hurt'}}], **extras.dragon_immunity()}))
    # explosions that only take what players built: every other solid block of the game is immune
    blast = lambda radius, kb, immune: base({'minecraft:tick': [{'effect': {
        'type': 'minecraft:explode', 'block_interaction': 'tnt', 'immune_blocks': immune, 'knockback_multiplier': kb, 'radius': radius,
        'small_particle': {'type': 'minecraft:explosion'}, 'large_particle': {'type': 'minecraft:explosion_emitter'}, 'sound': 'minecraft:entity.generic.explode'}}]})
    P.json('bw/enchantment/blast_fb.json', blast(2.4, 1.6, '#bw:immune_fb'))
    P.json('bw/enchantment/blast_tnt.json', blast(3.6, 1.0, '#bw:immune_tnt'))
    P.json('bw/predicate/ground.json', ground(True))
    P.json('bw/predicate/riding.json', {'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:vehicle': {}}})
    P.json('bw/predicate/invisible.json', {'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:effects': {'minecraft:invisibility': {}}}})

SOFT = {'oak_planks', 'terracotta', 'ladder', 'tnt', 'sponge', 'wet_sponge'} | {d + '_wool' for d in TEAMS}

def block_tags(P, blocks_json, is_open):
    names = [k.replace('minecraft:', '') for k in blocks_json]
    opn = sorted(n for n in names if is_open(n) or n in ('air', 'cave_air', 'void_air'))
    P.json('bw/tags/block/open.json', {'values': ['minecraft:' + n for n in opn]})
    P.json('bw/tags/block/glass.json', {'values': [f'minecraft:{d}_stained_glass' for d in TEAMS]})
    soft = SOFT
    P.json('bw/tags/block/immune_fb.json', {'values': sorted('minecraft:' + n for n in names if n not in soft and n not in opn)})
    P.json('bw/tags/block/immune_tnt.json', {'values': sorted('minecraft:' + n for n in names if n not in soft | {'end_stone'} and n not in opn)})

def nav_storage(P, maps, navs):
    """the planned ways, defence blocks and bed positions go into storage once, when the pack loads"""
    out = []
    for m in maps:
        mid = m['id']; nv = navs[mid]; cx, cy, cz = m['center']
        W = lambda c: f'[{c[0] + cx + 0.5}d,{float(c[1] + cy)}d,{c[2] + cz + 0.5}d]'
        lines = [f'data modify storage bw:nav {mid} set value {{}}']
        for name, pts in nv['routes'].items():
            lines.append(f'data modify storage bw:nav {mid}.{name} set value [{",".join(W(c) for c in pts)}]')
        for name, c in nv['nodes'].items(): lines.append(f'data modify storage bw:nav {mid}.n_{name} set value {W(c)}')
        for i in range(N):
            d = nv['defs'][str(i)]; wool = f'minecraft:{TEAMS[i]}_wool'
            tiers = {0: [], 1: [(c, wool) for c in d['l1']], 2: [(c, 'minecraft:end_stone') for c in d['l1']] + [(c, wool) for c in d['l2']],
                     3: [(c, 'minecraft:end_stone') for c in d['l1']] + [(c, 'minecraft:oak_planks') for c in d['l2']],
                     4: [(c, 'minecraft:obsidian') for c in d['l1']] + [(c, 'minecraft:end_stone') for c in d['l2']]}
            for T, cells in tiers.items():
                lines.append(f'data modify storage bw:nav {mid}.def{i}_{T} set value [' + ','.join(f'{{x:{c[0] + cx},y:{c[1] + cy},z:{c[2] + cz},b:"{b}"}}' for c, b in cells) + ']')
            b0, b1 = d['bed']
            lines.append(f'data modify storage bw:nav {mid}.bed{i} set value [{(b0[0] + b1[0]) / 2 + cx + 0.5}d,{b0[1] + cy + 0.3}d,{(b0[2] + b1[2]) / 2 + cz + 0.5}d]')
        P.fn(f'nav/{mid}', lines); out.append(f'function bw:nav/{mid}')
        # the way home from every cell of ground (see nav.flow): its own storage file, written once
        fl = []
        for F, cells in (('f', nv['flow']), ('g', nv['flowg'])):          # f: to the nearest point; g: to the nearest forge
            fl.append(f'data modify storage bwflow:{F} {mid} set value {{}}')
            for k in range(0, len(cells), 3000):
                fl.append(f'data modify storage bwflow:{F} {mid} merge value {{' + ','.join(f'"{x + cx} {y + cy} {z + cz}":{v}b' for x, y, z, v in cells[k:k + 3000]) + '}')
        hubs = {}
        for key, name in nv['hubs'].items():
            x, y, z = (int(v) for v in key.split()); hubs[(x + cx, y + cy, z + cz)] = name
        fl.append(f'data modify storage bwflow:h {mid} set value {{' + ','.join(f'"{c[0]} {c[1]} {c[2]}":"{v}"' for c, v in sorted(hubs.items())) + '}')
        # ways out of the patches of ground that no walk leads home from: {foot of the pillar: the points to go by, and the known ground they end on}
        fl.append(f'data modify storage bwflow:x {mid} set value {{' + ','.join(
            f'"{c[0] + cx} {c[1] + cy} {c[2] + cz}":{{p:[{",".join(W(p) for p in pts)}],f:[{f[0] + cx},{f[1] + cy},{f[2] + cz}]}}' for c, pts, f in nv['esc']) + '}')
        P.fn(f'flow/{mid}', fl); out.append(f'function bw:flow/{mid}')
        # the hubs as markers too: a bot that stands on nothing the map knows asks which is nearest
        P.add(f'm/{mid}/begin', [f'summon minecraft:marker {c[0] + 0.5} {float(c[1])} {c[2] + 0.5} {{Tags:["bw","bw.round","bw.hub"],data:{{n:"{v}"}}}}' for c, v in sorted(hubs.items()) if v[0] != 'g'])
    return out

def write(P, maps, navs):
    load = [*[f'scoreboard objectives add {o} dummy' for o in ('bw.st', 'bw.pst', 'bw.dest', 'bw.t1', 'bw.t2', 'bw.atk', 'bw.jc', 'bw.br', 'bw.slow', 'bw.hp', 'bw.tgt', 'bw.mf', 'bw.ms',
                                                              'bw.mine', 'bw.stuck', 'bw.px', 'bw.py', 'bw.pz', 'bw.strafe', 'bw.sw', 'bw.tool', 'bw.pose', 'bw.fbc', 'bw.idle', 'bw.wpt', 'bw.av', 'bw.avn', 'bw.avs', 'bw.ft', 'bw.calm', 'bw.trc', 'bw.tx', 'bw.tz', 'bw.off', 'bw.offa', 'bw.avf', 'bw.av0', 'bw.avc', 'bw.twr', 'bw.rrc', 'bw.nearc')],
            'data modify storage bw:ai names set value ' + snbt(NAMES), *nav_storage(P, maps, navs)]
    enchantments(P)
    # ------------------------------------------------------------------ how good they are
    lv = []
    names = ('reach', 'acc', 'cd', 'walk', 'bridge', 'eff', 'def', 'aggro', 'strafe', 'kb')
    for n, row in enumerate(LEVELS):
        rng = f'{n}' if n < len(LEVELS) - 1 else f'{n}..'
        lv.append(f'execute if score #lvl bw matches {rng} run function bw:ai/lv/{n}')
        P.fn(f'ai/lv/{n}', [f'scoreboard players set #a_{k} bw {v}' for k, v in zip(names, row)] + [
            f'scoreboard players set #a_wait bw {max(8, 40 - 4 * n)}', f'scoreboard players set #a_think bw {max(10, 60 - 5 * n)}',
            f'scoreboard players set #a_place bw {max(3, 9 - n // 2)}', f'scoreboard players set #a_hack bw {1 if n >= 15 else 0}',
            # a beginner fumbles at a bed for two seconds; a good player has it in under one
            f'scoreboard players set #a_bedt bw {max(14, 44 - 4 * n)}'])
    P.fn('ai/level', lv)

    # ------------------------------------------------------------------ a bot is born
    for n, m in enumerate(maps):
        mid = m['id']; T = m['teams']
        P.add(f'm/{mid}/begin', [f'data modify storage bw:ai ctx.m set value "{mid}"'])
        for i in BOTS:
            x, y, z = T[i]['spawn']; skin = SKINS[(i + n) % len(SKINS)]
            P.fn(f'm/{mid}/bot{i}', [
                f'summon minecraft:mannequin {x}.5 {y} {z}.5 {{Tags:["bw","bw.round","bw.bot","bw.new"],Rotation:[{T[i]["yaw"]}f,0f],'
                f'profile:{{texture:"minecraft:entity/player/{skin}",model:"{skin.split("/")[0]}"}},hide_description:1b,CustomNameVisible:1b,'
                'attributes:[{id:"minecraft:max_health",base:40d}],Health:40f,drop_chances:{head:0f,chest:0f,legs:0f,feet:0f,mainhand:0f,offhand:0f}}',
                f'execute as @e[type=minecraft:mannequin,tag=bw.new] run function bw:ai/init{i}'])
        P.add(f'm/{mid}/tick', [f"execute as @e[type=minecraft:mannequin,tag=bw.bot] at @s if entity @s[y=-200,dy={m['void_y'] + 200}] run function bw:ai/die"])
        # heal pool and traps are things of a place
        sec = []
        for i in range(N):
            gx, gy, gz = T[i]['gen']; bx, by, bz = T[i]['bed']
            sec += [f'execute if score #heal{i} bw matches 1.. positioned {gx} {gy} {gz} run effect give @e[tag=bw.fighter,scores={{bw.team={i}}},distance=..16] minecraft:regeneration 2 1 true']
            if i:
                sec += [f'execute if score #lvl bw matches 7.. if score #wfe{i} bw matches 120.. if score #bed{i} bw matches 1 unless entity @e[type=minecraft:iron_golem,tag=bw.golem,scores={{bw.team={i}}}] '
                        f'positioned {bx} {by} {bz} run function bw:ai/golemchk {{i:{i}}}']
        P.fn(f'm/{mid}/sec', sec)
    P.add('game/second', by_map(maps, 'sec'))
    begin = ['function bw:ai/level', 'kill @e[type=minecraft:marker,tag=bw.goal]', 'function bw:ai/purge',
             'execute if score #a_hack bw matches 1 run ' + tell('@a[tag=bw.play]', t('⚠ ', 'red'), t('이번 판 상대는 뭔가 수상해… 핵을 쓰는 것 같아.', 'yellow'))]
    for i in BOTS:
        begin += [*[f'scoreboard players set #{v}{i} bw 0' for v in ('bsw', 'bar', 'btl', 'bfb', 'bga', 'wfe', 'wau', 'wdi', 'wem', 'bdone')],
                  f'scoreboard players operation #fs{i} bw = #a_eff bw',
                  'execute store result storage bw:tmp k int 1 run random value 0..%d' % (len(NAMES) - 1), f'function bw:ai/name{i} with storage bw:tmp',
                  f'execute store result storage bw:ai ctx.T int 1 run scoreboard players get #a_def bw', f'function bw:ai/defcopy{i} with storage bw:ai ctx',
                  f'summon minecraft:marker 0 0 0 {{Tags:["bw","bw.round","bw.goal","bw.g{i}"]}}',
                  f'function bw:ai/spawn{i}']
        P.fn(f'ai/name{i}', [f'$data modify storage bw:ai n{i} set from storage bw:ai names[$(k)]'])
        P.fn(f'ai/defcopy{i}', [f'$data modify storage bw:bot def{i} set from storage bw:nav $(m).def{i}_$(T)'])
        P.fn(f'ai/spawn{i}', by_map(maps, f'bot{i}'))
        P.fn(f'ai/init{i}', [
            'tag @s remove bw.new', 'tag @s add bw.fighter', f'scoreboard players set @s bw.team {i}', f'team join bw.{TEAMS[i]} @s',
            f'data modify entity @s CustomName set from storage bw:ai n{i}',
            *[f'scoreboard players set @s {o} 0' for o in ('bw.st', 'bw.pst', 'bw.dest', 'bw.t1', 'bw.t2', 'bw.atk', 'bw.jc', 'bw.br', 'bw.slow', 'bw.mf', 'bw.ms', 'bw.mine',
                                                           'bw.stuck', 'bw.lht', 'bw.pose', 'bw.fbc', 'bw.idle', 'bw.wpt', 'bw.av', 'bw.avs', 'bw.ft', 'bw.calm', 'bw.trc', 'bw.tx', 'bw.tz', 'bw.off', 'bw.offa', 'bw.avf', 'bw.av0', 'bw.avc', 'bw.bgc', 'bw.mfat', 'bw.milk', 'bw.twr', 'bw.rrc', 'bw.nearc')],
            'scoreboard players set @s bw.avn 25', f'data modify storage bw:bot tr{i} set value []',
            'scoreboard players set @s bw.tgt -1', 'scoreboard players set @s bw.strafe 1',
            f'scoreboard players operation @s bw.sw = #bsw{i} bw', f'scoreboard players operation @s bw.armor = #bar{i} bw', f'scoreboard players operation @s bw.tool = #btl{i} bw',
            # how much of a hit's knockback they take (the cheaters at the top take little or none)
            *[f'execute if score #a_kb bw matches {a}..{b} run attribute @s minecraft:knockback_resistance base set {v}' for a, b, v in ((81, 99, 0.15), (51, 80, 0.4), (21, 50, 0.65), (1, 20, 0.85), (0, 0, 1.0))],
            'execute if score #a_hack bw matches 1 run attribute @s minecraft:fall_damage_multiplier base set 0',
            'function bw:ai/equip',
            f'data modify storage bw:bot at{i} set value "s{i}"', f'data modify storage bw:tmp rt.to set value "g{i}"', f'function bw:ai/route{i}', 'scoreboard players set @s bw.dest 1'])
        # walking somewhere: copy the planned way and aim the goal marker at its first point
        P.fn(f'ai/route{i}', [f'data modify storage bw:tmp rt.at set from storage bw:bot at{i}', 'data modify storage bw:tmp rt.m set from storage bw:ai ctx.m',
                              f'data modify storage bw:bot r{i} set value []', f'function bw:ai/route{i}b with storage bw:tmp rt',
                              f'execute unless data storage bw:bot r{i}[0] run return fail',
                              f'data modify entity {GOAL(i)} Pos set from storage bw:bot r{i}[0]',
                              'scoreboard players set @s bw.st 2', 'scoreboard players set @s bw.stuck 0', 'scoreboard players set @s bw.wpt 0', 'scoreboard players set @s bw.av 0',
                              'scoreboard players set @s bw.avn 25', 'scoreboard players set @s bw.avc 0', 'return 1'])
        P.fn(f'ai/route{i}b', [f'$data modify storage bw:bot r{i} set from storage bw:nav $(m).$(at)_$(to)', f'$data modify storage bw:bot to{i} set value "$(to)"',
                               # a fight or a siege may have led it away from the place the way starts at: go back there first
                               f'$execute if data storage bw:bot r{i}[0] run data modify storage bw:bot r{i} prepend from storage bw:nav $(m).n_$(at)'])
        P.fn(f'ai/next{i}', ['scoreboard players set @s bw.nearc 0', f'data remove storage bw:bot r{i}[0]', f'data modify storage bw:bot tr{i} set value []',
                             f'execute unless data storage bw:bot r{i}[0] run return run function bw:ai/arrive{i}',
                             f'data modify entity {GOAL(i)} Pos set from storage bw:bot r{i}[0]', 'scoreboard players set @s bw.stuck 0', 'scoreboard players set @s bw.wpt 0',
                             'scoreboard players set @s bw.av 0', 'scoreboard players set @s bw.avn 25', 'scoreboard players set @s bw.avc 0'])
        P.fn(f'ai/arrive{i}', [f'data modify storage bw:bot at{i} set from storage bw:bot to{i}', 'function bw:ai/arrive'])
        P.fn(f'ai/nearly{i}', ['scoreboard players add @s bw.nearc 1', f'execute if score @s bw.nearc matches 15.. run function bw:ai/next{i}'])
        # the way back: the steps of the detour, the latest first, and then on along the planned way
        P.fn(f'ai/retrace{i}', [f'data modify storage bw:bot r{i} prepend from storage bw:bot tr{i}[]', f'data modify storage bw:bot tr{i} set value []',
                                f'data modify entity {GOAL(i)} Pos set from storage bw:bot r{i}[0]', 'scoreboard players set @s bw.stuck 0', 'scoreboard players set @s bw.wpt 0',
                                'scoreboard players set @s bw.av 0', 'scoreboard players set @s bw.avn 25', 'scoreboard players set @s bw.avc 0', 'scoreboard players set @s bw.off 0', 'return 1'])
    P.add('game/begin', begin)
    # bots of a round that is over: out of sight, and no longer anybody
    P.fn('ai/purge', ['tag @e[type=minecraft:mannequin,tag=bw.round] remove bw.bot', 'tag @e[type=minecraft:mannequin,tag=bw.round] remove bw.fighter',
                      'tp @e[type=minecraft:mannequin,tag=bw.round] 0 -400 0', 'kill @e[type=minecraft:mannequin,tag=bw.round]'])
    # what a bot wears and holds
    eq = []
    for i in BOTS:
        helm = (f'minecraft:leather_helmet[dyed_color={TEAM_DYE_RGB[i]},enchantments={{"bw:bot":1}},enchantment_glint_override=false]')
        eq += [f'execute if score @s bw.team matches {i} run item replace entity @s armor.head with {helm}',
               f'execute if score @s bw.team matches {i} run item replace entity @s armor.chest with minecraft:leather_chestplate[dyed_color={TEAM_DYE_RGB[i]}]',
               f'execute if score @s bw.team matches {i} if score @s bw.armor matches 0 run item replace entity @s armor.legs with minecraft:leather_leggings[dyed_color={TEAM_DYE_RGB[i]}]',
               f'execute if score @s bw.team matches {i} if score @s bw.armor matches 0 run item replace entity @s armor.feet with minecraft:leather_boots[dyed_color={TEAM_DYE_RGB[i]}]']
        for p in (1, 2, 3, 4):
            eq.append(f'execute if score @s bw.team matches {i} if score #prot{i} bw matches {p} run function bw:game/prot{p}b')
        eq.append(f'execute if score @s bw.team matches {i} if score #sharp{i} bw matches 1.. run item modify entity @s weapon.mainhand bw:sharp')
    for a in (1, 2, 3):
        eq[0:0] = [f'execute if score @s bw.armor matches {a} run item replace entity @s armor.legs with minecraft:{ARMOR[a]}_leggings',
                   f'execute if score @s bw.armor matches {a} run item replace entity @s armor.feet with minecraft:{ARMOR[a]}_boots']
    eq[0:0] = [f'execute if score @s bw.sw matches {s} run item replace entity @s weapon.mainhand with minecraft:{SWORDS[s]}' for s in range(4)]
    P.fn('ai/equip', eq)
    for p in (1, 2, 3, 4):
        P.json(f'bw/item_modifier/prot{p}b.json', {'type': 'minecraft:set_enchantments', 'enchantments': {'minecraft:protection': p}, 'add': False})
        P.fn(f'game/prot{p}b', [f'item modify entity @s armor.{s} bw:prot{p}b' for s in ('head', 'chest', 'legs', 'feet')])

    # ------------------------------------------------------------------ every tick
    P.add('game/tick', ['execute as @e[type=minecraft:armor_stand,tag=bw.boom] at @s run function bw:fb/after', 'kill @e[type=minecraft:armor_stand,tag=bw.boom]',
                        'execute as @e[type=minecraft:mannequin,tag=bw.bot] at @s run function bw:ai/bot',
                        *[f'execute if score #bres{i} bw matches 1.. run function bw:ai/resp{i}' for i in BOTS],
                        'function bw:fb/tick'])
    for i in BOTS:
        P.fn(f'ai/resp{i}', [f'scoreboard players remove #bres{i} bw 1', f'execute if score #bres{i} bw matches 0 if score #state bw matches 3 run function bw:ai/spawn{i}'])
    P.fn('ai/bot', [
        'execute store result score @s bw.hp run data get entity @s Health 10',
        'execute if score @s bw.hp matches ..200 run return run function bw:ai/die',
        *[f'scoreboard players remove @s[scores={{{o}=1..}}] {o} 1' for o in ('bw.atk', 'bw.t1', 'bw.t2', 'bw.jc', 'bw.br', 'bw.slow', 'bw.fbc', 'bw.calm', 'bw.bgc')],
        'scoreboard players set @s bw.mf 0', 'scoreboard players set @s bw.ms 0', 'scoreboard players set #drop bw 0', 'scoreboard players set #high bw 0',
        # who is near: the closest fighter of another team that can be seen
        'scoreboard players operation #me bw = @s bw.team', 'tag @e[tag=bw.foe] remove bw.foe',
        'execute as @e[tag=bw.mob,distance=..5,sort=nearest] unless score @s bw.team = #me bw unless entity @e[tag=bw.foe,limit=1] run tag @s add bw.foe',
        'execute as @e[tag=bw.fighter,distance=0.01..16,sort=nearest] unless score @s bw.team = #me bw unless predicate bw:invisible unless entity @e[tag=bw.foe,limit=1] run tag @s add bw.foe',
        # back on its feet after a bridge
        'execute if score @s bw.br matches 0 if score @s bw.pose matches 1 run function bw:ai/stand',
        'execute unless score @s bw.st matches 3 if score @s bw.calm matches 0 if entity @e[tag=bw.foe,distance=..7] run function bw:ai/engage',
        # off the planned way (a fight, a siege, building): it remembers its steps, to find the way back
        'execute if score @s bw.st matches 3..6 run function bw:ai/crumbs',
        'execute if score @s bw.st matches 3 run return run function bw:ai/fight',
        'execute if score @s bw.st matches 0 run return run function bw:ai/think',
        'execute if score @s bw.st matches 1 run return run function bw:ai/home',
        'execute if score @s bw.st matches 2 run return run function bw:ai/go',
        'execute if score @s bw.st matches 4 run return run function bw:ai/siege',
        'execute if score @s bw.st matches 5 run return run function bw:ai/build',
        'execute if score @s bw.st matches 6 run return run function bw:ai/gem'])
    P.fn('ai/stand', ['data modify entity @s pose set value "standing"', 'scoreboard players set @s bw.pose 0'])
    P.fn('ai/crouch', ['data modify entity @s pose set value "crouching"', 'scoreboard players set @s bw.pose 1'])
    P.fn('ai/crumbs', ['scoreboard players add @s bw.trc 1', 'execute if score @s bw.trc matches 8.. run function bw:ai/crumb0'])
    P.fn('ai/crumb0', ['scoreboard players set @s bw.trc 0', 'execute unless predicate bw:ground run return 0',
                       'execute store result score #x bw run data get entity @s Pos[0] 2', 'execute store result score #z bw run data get entity @s Pos[2] 2',
                       'execute if score #x bw = @s bw.tx if score #z bw = @s bw.tz run return 0',
                       'scoreboard players operation @s bw.tx = #x bw', 'scoreboard players operation @s bw.tz = #z bw',
                       *[f'execute if score @s bw.team matches {i} run return run function bw:ai/crumb {{i:{i}}}' for i in BOTS]])
    P.fn('ai/crumb', ['$data modify storage bw:bot tr$(i) prepend from entity @s Pos', '$execute if data storage bw:bot tr$(i)[60] run data remove storage bw:bot tr$(i)[-1]'])
    P.fn('ai/retrace', [*[f'execute if score @s bw.team matches {i} if data storage bw:bot tr{i}[0] run return run function bw:ai/retrace{i}' for i in BOTS], 'return fail'])
    P.fn('ai/engage', ['scoreboard players operation @s bw.pst = @s bw.st', 'scoreboard players set @s bw.st 3', 'scoreboard players set @s bw.trc 8', 'scoreboard players set @s bw.tx -99999', 'scoreboard players set @s bw.mine 0', 'scoreboard players set @s bw.ft 0',
                       'execute store result score @s bw.strafe run random value 0..1', 'execute if score @s bw.strafe matches 0 run scoreboard players set @s bw.strafe -1',
                       'execute store result score @s bw.t2 run random value 12..30'])
    P.fn('ai/giveup', ['scoreboard players set @s bw.calm 160', 'function bw:ai/disengage'])
    P.fn('ai/disengage', ['scoreboard players operation @s bw.st = @s bw.pst', 'execute if score @s bw.st matches 3 run scoreboard players set @s bw.st 0', 'scoreboard players set @s bw.stuck 0'])

    # ------------------------------------------------------------------ fighting
    fight = [
        'execute unless entity @e[tag=bw.foe,distance=..16] run return run function bw:ai/disengage',
        # they cannot get at each other (one is up on something): after six seconds without a blow it goes back to what it was doing
        'scoreboard players add @s bw.ft 1', 'execute if score @s bw.ft matches 120.. run return run function bw:ai/giveup',
        f'rotate @s facing entity {FOE} eyes',
        # close in at a run; stop when toe to toe; circle if they know how
        'execute if entity @e[tag=bw.foe,distance=2.0..] run scoreboard players set @s bw.mf 3',
        'execute if score @s bw.slow matches 1.. if score @s bw.mf matches 3 run scoreboard players set @s bw.mf 4',
        'execute if score #a_strafe bw matches 1 if entity @e[tag=bw.foe,distance=..4.5] run scoreboard players operation @s bw.ms = @s bw.strafe',
        'execute if score @s bw.t2 matches 0 run function bw:ai/flip',
        'scoreboard players set #drop bw 0',
        'execute positioned ~-64 ~-50 ~-64 if entity @e[tag=bw.foe,dx=128,dy=48.4,dz=128] run scoreboard players set #drop bw 1',
        'execute positioned ~-64 ~-50 ~-64 if entity @e[tag=bw.foe,dx=128,dy=47.4,dz=128] run scoreboard players set #high bw 1',
        'execute rotated as @s rotated ~ 0 run function bw:ai/feet',
        'execute if score @s bw.br matches 1.. run scoreboard players set @s bw.ms 0',
        # a golden apple when it is going badly (they have learned that by stage 6)
        *[f'execute if score @s bw.team matches {i} if score #bga{i} bw matches 1.. if score @s bw.hp matches ..290 run function bw:ai/gapple{i}' for i in BOTS],
        # a fireball at someone out on a bridge
        *[f'execute if score @s bw.team matches {i} if score #bfb{i} bw matches 1.. if score @s bw.fbc matches 0 if entity @e[tag=bw.foe,distance=6..14] run function bw:ai/throw{i}' for i in BOTS],
        'execute if score #lvl bw matches 5.. if score @s bw.bgc matches 0 if entity @e[tag=bw.foe,distance=4..11] run function bw:ai/bug']
    for r in REACHES:
        fight.append(f'execute if score @s bw.atk matches 0 if score #a_reach bw matches {r} if entity @e[tag=bw.foe,distance=..{r / 100 + 0.25:.2f}] run function bw:ai/swing')
    P.fn('ai/fight', fight)
    P.fn('ai/flip', ['scoreboard players operation @s bw.strafe *= #-1 bw', 'execute store result score @s bw.t2 run random value 12..32'])
    for i in BOTS:
        P.fn(f'ai/gapple{i}', [f'scoreboard players remove #bga{i} bw 1', 'effect give @s minecraft:regeneration 5 1', 'effect give @s minecraft:absorption 120 0',
                               'playsound minecraft:entity.player.burp player @a ~ ~ ~ 0.8 1', 'particle minecraft:item{item:"minecraft:golden_apple"} ~ ~1.5 ~ 0.2 0.2 0.2 0.05 12'])
        P.fn(f'ai/throw{i}', [f'scoreboard players remove #bfb{i} bw 1', 'scoreboard players set @s bw.fbc 120', 'swing @s mainhand',
                              f'execute anchored eyes facing entity {FOE} feet positioned ^ ^ ^1.2 run function bw:fb/launch'])
    P.fn('ai/bug', [*[f'execute if score @s bw.team matches {i} if score #wfe{i} bw matches 24.. run return run function bw:ai/bug{i}' for i in BOTS]])
    for i in BOTS:
        P.fn(f'ai/bug{i}', [f'scoreboard players remove #wfe{i} bw 24', 'scoreboard players set @s bw.bgc 400', 'swing @s mainhand',
                            f'execute anchored eyes facing entity {FOE} eyes positioned ^ ^ ^0.7 rotated ~ ~-7 run function bw:mob/throw'])
        # a dream defender, when somebody is at its bed and it can pay (stage 7 and up; one at a time)
        P.fn(f'ai/golem{i}', [f'scoreboard players remove #wfe{i} bw 120', 'function bw:mob/botgolem'])
    P.fn('ai/golemchk', ['scoreboard players set #n bw 0', '$execute as @e[tag=bw.fighter,distance=..16] unless score @s bw.team matches $(i) run scoreboard players set #n bw 1',
                         '$execute if score #n bw matches 1 as @e[type=minecraft:mannequin,tag=bw.bot,scores={bw.team=$(i)},distance=..20,limit=1] at @s run function bw:ai/golem$(i)'])
    P.fn('ai/swing', [
        'swing @s mainhand',
        'execute store result score #rn bw run random value 0..3', 'scoreboard players operation @s bw.atk = #a_cd bw', 'scoreboard players operation @s bw.atk += #rn bw',
        'execute store result score #rn bw run random value 1..100',
        'execute if score #rn bw > #a_acc bw run return 0',
        'execute if score @s bw.slow matches 1.. if score #rn bw matches 40.. run return 0',
        # how hard: the sword, the team's sharpness, and whatever softens it on the other side (hacks.py: autoblock)
        *[f'execute if score @s bw.sw matches {s} run scoreboard players set #dmg bw {SWORD_DMG[s]}' for s in range(4)],
        *[f'execute if score @s bw.team matches {i} if score #sharp{i} bw matches 1.. run scoreboard players add #dmg bw 125' for i in BOTS],
        f'execute as {FOE} run function bw:ai/soften',
        'execute store result storage bw:tmp hit.d float 0.01 run scoreboard players get #dmg bw',
        'function bw:ai/hit with storage bw:tmp hit'])
    P.fn('ai/soften', [])                                            # hacks.py adds to this
    P.fn('ai/hit', [f'$damage {FOE} $(d) minecraft:mob_attack by @s', 'scoreboard players set @s bw.ft 0',
                    f'scoreboard players operation {FOE} bw.lh = @s bw.team', f'scoreboard players set {FOE} bw.lht 200'])
    # the helmet's enchantment calls this when the bot is struck by a hand, a sword or an arrow
    P.fn('ai/hurt', ['execute unless entity @s[tag=bw.bot] run return 0',
                     'scoreboard players set #att bw -1', 'execute on attacker run scoreboard players operation #att bw = @s bw.team',
                     'execute if score #att bw matches 0.. run scoreboard players operation @s bw.lh = #att bw', 'execute if score #att bw matches 0.. run scoreboard players set @s bw.lht 200',
                     'scoreboard players set @s bw.ft 0', 'scoreboard players set @s bw.calm 0',
                     'execute unless score @s bw.st matches 3 run function bw:ai/engage'])

    # ------------------------------------------------------------------ feet: steps, gaps, walls (run with the direction of travel as rotation)
    P.fn('ai/feet', [
        # a step up: jump (the body is wider than the line it walks, so the shoulders are looked at as well)
        'execute if score @s bw.jc matches 0 if predicate bw:ground run function bw:ai/step',
        # a wall: break it if a player built it, walk round it if not
        'function bw:ai/probe',
        'execute if block ^ ^1 ^0.7 #bw:open unless block ^ ^ ^0.7 #bw:open unless block ^ ^2 ^0.7 #bw:open positioned ^ ^ ^0.7 if predicate bw:built run function bw:ai/wall',
        # nothing to walk on: lay a block, unless the way goes down here
        # (going down on purpose - a planned drop, or after someone who is lower - it only bridges a gap that has no bottom)
        'execute if score #drop bw matches 0 if predicate bw:ground if block ^ ^-1 ^0.6 #bw:open positioned ^ ^-1 ^0.6 run function bw:ai/lay',
        'execute if score #drop bw matches 1 if predicate bw:ground if block ^ ^-1 ^0.6 #bw:open if block ^ ^-2 ^0.6 #bw:open if block ^ ^-3 ^0.6 #bw:open if block ^ ^-4 ^0.6 #bw:open positioned ^ ^-1 ^0.6 run function bw:ai/lay',
        # (coming down from a roof it got onto: only where there is nothing at all below)
        'execute if score #drop bw matches 2 if predicate bw:ground ' + ' '.join(f'if block ^ ^-{d} ^0.6 #bw:open' for d in range(1, 13)) + ' positioned ^ ^-1 ^0.6 run function bw:ai/lay',
        'execute if score @s bw.br matches 1.. run function bw:ai/stance'])
    P.fn('ai/jump', ['data modify entity @s Motion[1] set value 0.42d', 'scoreboard players set @s bw.jc 9'])
    CF, CH = '^ ^ ^0.7', '^ ^1 ^0.7'                                  # straight ahead: at the feet, at the head
    LF, LH = '^0.32 ^ ^0.55', '^0.32 ^1 ^0.55'                        # the left shoulder
    RF, RH = '^-0.32 ^ ^0.55', '^-0.32 ^1 ^0.55'                      # the right shoulder
    P.fn('ai/step', [f'execute unless block {CF} #bw:open if block {CH} #bw:open run return run function bw:ai/stepup',
                     # only a shoulder would catch: slide past it, the way people do at a door post
                     f'execute unless block {LF} #bw:open if block {LH} #bw:open if block {RF} #bw:open run return run scoreboard players set @s bw.ms -1',
                     f'execute unless block {RF} #bw:open if block {RH} #bw:open if block {LF} #bw:open run return run scoreboard players set @s bw.ms 1',
                     f'execute unless block {LF} #bw:open if block {LH} #bw:open run return run function bw:ai/stepup'])
    # up it goes - unless there is no room over its head, or it already stands higher than where it is going: then this thing is not on the way, it is in the way
    P.fn('ai/stepup', ['execute if score #high bw matches 0 if block ~ ~2 ~ #bw:open run return run function bw:ai/jump',
                       f'execute unless block {CF} #bw:open positioned {CF} run return run function bw:ai/wall',
                       f'execute positioned {LF} run function bw:ai/wall'])
    P.fn('ai/probe', [f'execute unless block {CH} #bw:open positioned {CH} run return run function bw:ai/wall',
                      *[f'execute positioned {p} if predicate bw:built run return run function bw:ai/wall' for p in (LH, RH)],
                      f'execute unless block {LH} #bw:open if block {RH} #bw:open run return run scoreboard players set @s bw.ms -1',
                      f'execute unless block {RH} #bw:open if block {LH} #bw:open run return run scoreboard players set @s bw.ms 1',
                      f'execute unless block {LH} #bw:open positioned {LH} run return run function bw:ai/wall'])
    P.fn('ai/wall', ['execute if predicate bw:built run return run function bw:ai/mine',
                     'scoreboard players add @s bw.stuck 2', 'execute if score @s bw.av matches 0 run function bw:ai/avoid'])
    # something of the map is in the way: step along it for a while, longer every time it happens before the next point is reached
    P.fn('ai/avoid', ['execute if score @s bw.avn matches 100.. if function bw:ai/retrace run return 0',
                      # seven tries to get round it and still not there: it is not getting there on foot
                      'scoreboard players add @s bw.avc 1', 'execute if score @s bw.avc matches 4.. run return run function bw:ai/reroute',
                      'scoreboard players operation @s bw.av = @s bw.avn', 'scoreboard players operation @s bw.av0 = @s bw.avn', 'scoreboard players set @s bw.avf 0', 'execute if score @s bw.avn matches ..90 run scoreboard players operation @s bw.avn += @s bw.avn',
                      'execute unless score @s bw.avs matches -1..1 run scoreboard players set @s bw.avs 1', 'execute if score @s bw.avs matches 0 run scoreboard players set @s bw.avs 1',
                      'execute store result score #rn bw run random value 0..1', 'execute if score @s bw.avn matches 50 if score #rn bw matches 0 run scoreboard players operation @s bw.avs *= #-1 bw'])
    FLIP = 'run return run function bw:ai/flipside'
    AHEAD = ' '.join(f'if block ^ ^{h} ^{d} #bw:open' for d in (0.7, 1.4, 2.1) for h in ('', '1')) + f' if block {LF} #bw:open if block {LH} #bw:open if block {RF} #bw:open if block {RH} #bw:open'
    P.fn('ai/around', ['scoreboard players remove @s bw.av 1', 'scoreboard players operation @s bw.mf = #a_walk bw',
                       # a few steps along it, and the way to where it was going lies open again (the door was a little to the side): go
                       'scoreboard players operation #el bw = @s bw.av0', 'scoreboard players operation #el bw -= @s bw.av',
                       f'execute if score #el bw matches 6.. {AHEAD} run return run scoreboard players set @s bw.av 0',
                       # shut in on both sides (a corner, a niche): back out of it, away from where it wanted to go
                       'execute if score @s bw.avf matches 4.. rotated ~180 0 run function bw:ai/around3',
                       'execute unless score @s bw.avf matches 4.. if score @s bw.avs matches 1 rotated ~90 0 run function bw:ai/around2',
                       'execute unless score @s bw.avf matches 4.. if score @s bw.avs matches -1 rotated ~-90 0 run function bw:ai/around2',
                       'function bw:ai/unstick'])
    P.fn('ai/around2', ['rotate @s ~ 0',
                        # no way on this side (at head height; or at the feet, where it cannot or may not jump): the other side
                        f'execute unless block {CH} #bw:open positioned {CH} unless predicate bw:built {FLIP}',
                        f'execute unless block {CF} #bw:open unless block ~ ~2 ~ #bw:open positioned {CF} unless predicate bw:built {FLIP}',
                        f'execute unless block {CF} #bw:open if score #high bw matches 1 positioned {CF} unless predicate bw:built {FLIP}',
                        'function bw:ai/feet'])
    P.fn('ai/flipside', ['scoreboard players operation @s bw.avs *= #-1 bw', 'scoreboard players add @s bw.avf 1'])
    P.fn('ai/around3', ['rotate @s ~ 0', 'function bw:ai/feet'])
    wool = [f'execute if score @s bw.team matches {i} run setblock ~ ~ ~ minecraft:{TEAMS[i]}_wool' for i in BOTS]
    P.fn('ai/lay', ['execute align xyz unless entity @e[tag=bw.fighter,dx=0,dy=0,dz=0] run function bw:ai/wool', 'swing @s mainhand',
                    'playsound minecraft:block.wool.place block @a ~ ~ ~ 0.8 1', 'scoreboard players set @s bw.br 14'])
    P.fn('ai/wool', wool)
    # bridging the way people do: backwards, crouched, eyes on the edge - until they learn to do it at a walk, and the cheaters at a run
    P.fn('ai/stance', ['execute if score #a_bridge bw matches 3 run return 0',
                       'rotate @s ~180 76', 'scoreboard players operation @s bw.mf = #a_bridge bw', 'scoreboard players set @s bw.ms 0',
                       'execute if score @s bw.pose matches 0 if score #a_bridge bw matches -2..-1 run function bw:ai/crouch'])
    # breaking a block, standing at it: it takes as long as the bot's tool makes it take
    mine = ['scoreboard players set #need bw 9999']
    for blk, times in MINE:
        for tier, n in enumerate(times):
            mine.append(f'execute if block ~ ~ ~ {blk} if score @s bw.tool matches {tier} run scoreboard players set #need bw {n}')
    mine += ['execute if score @s bw.mfat matches 1.. if score #need bw matches ..3000 run scoreboard players operation #need bw *= #3 bw',
             # a block this bot cannot break (obsidian without a diamond pickaxe): it gives the siege up soon
             'execute if score #need bw matches 9999 if score @s bw.st matches 4 if score @s bw.t1 matches 61.. run scoreboard players set @s bw.t1 60',
             'execute if score #need bw matches 9999 run return run scoreboard players add @s bw.stuck 2',
             'scoreboard players add @s bw.mine 1', 'scoreboard players set @s bw.mf 0',
             'scoreboard players operation #q bw = @s bw.mine', 'scoreboard players operation #q bw %= #4 bw',
             'execute if score #q bw matches 0 run swing @s mainhand', 'execute if score #q bw matches 0 run playsound minecraft:block.stone.hit block @a ~ ~ ~ 0.6 1',
             'execute if score #q bw matches 0 run particle minecraft:crit ~ ~0.5 ~ 0.3 0.3 0.3 0.1 3',
             'execute if score @s bw.mine >= #need bw run function bw:ai/mined']
    P.fn('ai/mine', mine)
    P.fn('ai/mined', ['setblock ~ ~ ~ minecraft:air destroy', 'scoreboard players set @s bw.mine 0', 'scoreboard players set @s bw.stuck 0'])

    # ------------------------------------------------------------------ walking a planned way
    # A point is reached within 0.4 of its middle (two overlapping boxes make the narrow one): turning for the next point any earlier cuts the
    # corner, and the corner may be a wall. Something standing on the point (another bot): 0.7 will do after three quarters of a second.
    P.fn('ai/reached', [*[f'execute if score @s bw.team matches {i} positioned ~-0.4 ~-0.6 ~-0.4 if entity @e[type=minecraft:marker,tag=bw.g{i},dx=0,dy=1.2,dz=0] positioned ~-0.2 ~ ~-0.2 if entity @e[type=minecraft:marker,tag=bw.g{i},dx=0,dy=1.2,dz=0] run return run function bw:ai/next{i}' for i in BOTS],
                        *[f'execute if score @s bw.team matches {i} positioned ~-0.7 ~-0.6 ~-0.7 if entity @e[type=minecraft:marker,tag=bw.g{i},dx=0.4,dy=1.2,dz=0.4] run function bw:ai/nearly{i}' for i in BOTS]])
    P.fn('ai/go', [# in the middle of a jump up its own pillar it has not arrived yet: the block under its feet comes first
                   'scoreboard players set #pj bw 0', 'execute if score @s bw.twr matches 1.. unless predicate bw:ground run scoreboard players set #pj bw 1',
                   'execute if score #pj bw matches 0 run function bw:ai/reached',
                   # standing right over the point (on something built into it) counts too
                   *[f'execute if score @s bw.team matches {i} if score @s bw.st matches 2 if predicate bw:ground positioned ~ ~-{d} ~ if entity @e[type=minecraft:marker,tag=bw.g{i},distance=..0.55] run function bw:ai/next{i}' for i in BOTS for d in (1, 2, 3)],
                   # ... and so does standing on the roof over it (after a fight that ended up there): on to the next point, down the side
                   *[f'execute if score @s bw.team matches {i} if score @s bw.st matches 2 if predicate bw:ground if data storage bw:bot r{i}[1] positioned ~-0.6 ~-30 ~-0.6 if entity @e[type=minecraft:marker,tag=bw.g{i},dx=0.2,dy=25.5,dz=0.2] run function bw:ai/next{i}' for i in BOTS],
                   'execute unless score @s bw.st matches 2 run return 0',
                   # ... the last point of the way: the way it came if it remembers one, else straight on until the roof ends
                   *[f'execute if score @s bw.team matches {i} if score @s bw.off matches 0 if predicate bw:ground positioned ~-0.6 ~-30 ~-0.6 if entity @e[type=minecraft:marker,tag=bw.g{i},dx=0.2,dy=25.5,dz=0.2] run function bw:ai/roof' for i in BOTS],
                   'execute if score @s bw.off matches 1.. run return run function bw:ai/walkoff',
                   *[f'execute if score @s bw.team matches {i} facing entity {GOAL(i)} feet rotated ~ 0 run function bw:ai/walk {{i:{i}}}' for i in BOTS]])
    P.fn('ai/roof', ['execute if function bw:ai/retrace run return 0', 'scoreboard players set @s bw.off 60', 'scoreboard players set @s bw.offa 0'])
    P.fn('ai/walkoff', ['scoreboard players remove @s bw.off 1', 'scoreboard players set #drop bw 2', 'scoreboard players set #high bw 1',
                        # down: that was the edge
                        'execute if predicate bw:ground if score @s bw.offa matches 7.. run return run scoreboard players set @s bw.off 0',
                        'execute if predicate bw:ground run scoreboard players set @s bw.offa 0', 'execute unless predicate bw:ground run scoreboard players add @s bw.offa 1',
                        'execute rotated as @s rotated ~ 0 run function bw:ai/walkoff2'])
    P.fn('ai/walkoff2', ['rotate @s ~ 0', 'scoreboard players operation @s bw.mf = #a_walk bw', 'function bw:ai/feet'])
    P.fn('ai/walk', [
        'scoreboard players set #drop bw 0',
        # the next point is a step down right here: walk off the edge instead of bridging
        '$execute if entity @e[type=minecraft:marker,tag=bw.g$(i),distance=..4.3] positioned ~-64 ~-50 ~-64 if entity @e[type=minecraft:marker,tag=bw.g$(i),dx=128,dy=48.4,dz=128] run scoreboard players set #drop bw 1',
        # it stands well above the point it is going to (more than a block and a half): nothing on the way there needs climbing
        '$execute positioned ~-128 ~-50 ~-128 if entity @e[type=minecraft:marker,tag=bw.g$(i),dx=256,dy=47.4,dz=256] run scoreboard players set #high bw 1',
        # ... and nobody bridges two blocks above solid ground: with ground close below, step off the edge
        'execute if score #high bw matches 1 if score #drop bw matches 0 run scoreboard players set #drop bw 1',
        # in the middle of a jump of its pillar: the block still has to go under its feet (the point may be only two blocks up, and then it is no
        # longer "well above" once the jump has begun)
        'execute if score @s bw.twr matches 1.. unless predicate bw:ground run return run function bw:ai/tower0',
        'scoreboard players set @s bw.twr 0',
        # the next point is straight above: go up on a pillar
        '$execute if entity @e[type=minecraft:marker,tag=bw.g$(i),distance=..16] positioned ~-0.6 ~0.8 ~-0.6 if entity @e[type=minecraft:marker,tag=bw.g$(i),dx=0.2,dy=15,dz=0.2] run return run execute at @s run function bw:ai/tower',
        # ... or up a wall right next to it that is too high to jump
        '$execute if entity @e[type=minecraft:marker,tag=bw.g$(i),distance=..16] positioned ~-1.7 ~1.4 ~-1.7 if entity @e[type=minecraft:marker,tag=bw.g$(i),dx=2.4,dy=15,dz=2.4] run return run execute at @s run function bw:ai/tower',
        'execute if score @s bw.av matches 1.. run return run function bw:ai/around',
        'rotate @s ~ 0', 'scoreboard players operation @s bw.mf = #a_walk bw',
        'execute if score @s bw.slow matches 1.. run scoreboard players set @s bw.mf 4',
        'function bw:ai/feet',
        # people hop along when they are in a hurry
        '$execute if score #a_walk bw matches 3 if score #high bw matches 0 if score @s bw.br matches 0 if score @s bw.jc matches 0 if predicate bw:ground unless entity @e[type=minecraft:marker,tag=bw.g$(i),distance=..4] unless block ^ ^-1 ^1.5 #bw:open unless block ^ ^-1 ^3 #bw:open if block ^ ^2 ^1 #bw:open run function bw:ai/hop',
        'function bw:ai/unstick'])
    P.fn('ai/hop', ['execute store result score #rn bw run random value 1..10', 'execute if score #rn bw matches ..3 run function bw:ai/jump', 'execute if score #rn bw matches 4.. run scoreboard players set @s bw.jc 6'])
    P.fn('ai/tower0', ['scoreboard players remove @s bw.twr 1', 'function bw:ai/tower'])
    P.fn('ai/tower', ['scoreboard players set @s bw.mf 0', 'execute if predicate bw:ground run scoreboard players set @s bw.twr 14',
                      # something built over its head: through it
                      'execute unless block ~ ~2 ~ #bw:open positioned ~ ~2 ~ run return run function bw:ai/wall',
                      # half under the edge of something (the bridge it fell from): to the middle of its own block first, or its head hits that edge
                      'execute if predicate bw:ground align xz positioned ~0.5 ~ ~0.5 unless entity @s[distance=..0.2] run tp @s ~ ~ ~',
                      'execute if score @s bw.jc matches 0 if predicate bw:ground run function bw:ai/jump',
                      'execute positioned ~ ~-1.05 ~ if block ~ ~ ~ #bw:open unless predicate bw:ground run function bw:ai/lay', 'scoreboard players set @s bw.br 0',
                      'function bw:ai/unstick'])
    # not getting anywhere: first a jump, then a step to the side, and at last straight to the point (it happens after a fight far off the way)
    P.fn('ai/unstick', ['scoreboard players add @s bw.idle 1', 'execute if score @s bw.idle matches 20.. run function bw:ai/moved',
                        'execute if score @s bw.stuck matches 40..44 if score #high bw matches 0 if predicate bw:ground run function bw:ai/jump',
                        # after a detour (a fight took it round a corner): back the way it came
                        'execute if score @s bw.stuck matches 60.. if function bw:ai/retrace run return 0',
                        'scoreboard players add @s bw.wpt 1', 'execute if score @s bw.wpt matches 400.. if score @s bw.stuck matches 200.. run return run function bw:ai/reroute',
                        'execute if score @s bw.wpt matches 1000.. run function bw:ai/reroute'])
    P.fn('ai/moved', ['scoreboard players set @s bw.idle 0',
                      'execute store result score #x bw run data get entity @s Pos[0] 2', 'execute store result score #z bw run data get entity @s Pos[2] 2', 'scoreboard players set #y bw 0',
                      'scoreboard players set #same bw 0',
                      'execute if score #x bw = @s bw.px if score #z bw = @s bw.pz run scoreboard players set #same bw 1',
                      'execute if score #same bw matches 1 run scoreboard players add @s bw.stuck 20', 'execute if score #same bw matches 0 run scoreboard players set @s bw.stuck 0',
                      'scoreboard players operation @s bw.px = #x bw', 'scoreboard players operation @s bw.py = #y bw', 'scoreboard players operation @s bw.pz = #z bw'])
    # ------------------------------------------------------------------ lost: the way home
    # A bot that cannot get on (seven tries round a wall, or far too long on one stretch) used to be put on its next point. Now it does what a
    # person does: it looks where it is and walks back to a place it knows. Every cell of ground on the map carries the next step of the
    # shortest walk to the nearest bed-side, diamond or emerald point (nav.flow); the bot's way becomes that walk, cell by cell, and from the
    # point it goes on to wherever it was going.
    DBG = lambda what: [f'execute if score #dbg bw matches 1 if score @s bw.team matches {i} run tellraw @a ["{what} bot{i} rrc ",{{score:{{name:"@s",objective:"bw.rrc"}}}}," st ",{{score:{{name:"@s",objective:"bw.st"}}}}," dest ",{{score:{{name:"@s",objective:"bw.dest"}}}}," pos ",{{nbt:"Pos",entity:"@s"}}," goal ",{{nbt:"Pos",entity:"{GOAL(i)}"}}," to ",{{nbt:"to{i}",storage:"bw:bot"}}]' for i in BOTS]
    P.fn('ai/reroute', ['execute at @s run function bw:ai/reroute1'])
    P.fn('ai/reroute1', ['scoreboard players add #reroutes bw 1',
                         'scoreboard players set @s bw.stuck 0', 'scoreboard players set @s bw.wpt 0', 'scoreboard players set @s bw.avc 0', 'scoreboard players set @s bw.av 0',
                         'scoreboard players set @s bw.avn 25', 'scoreboard players add @s bw.rrc 1',
                         # three ways home tried and still not there: think of something else to do
                         'execute if score @s bw.rrc matches 4.. run return run function bw:ai/rr_giveup',
                         'execute store result score #fx bw run data get entity @s Pos[0]', 'execute store result score #fy bw run data get entity @s Pos[1]',
                         'execute store result score #fz bw run data get entity @s Pos[2]',
                         'scoreboard players operation #sx bw = #fx bw', 'scoreboard players operation #sy bw = #fy bw', 'scoreboard players operation #sz bw = #fz bw',
                         # on its way home, and on its own island: the walk to its own forge
                         'scoreboard players operation #hd bw = @s bw.dest', 'execute if score @s bw.dest matches 9 run function bw:ai/rr_hd',
                         'scoreboard players set #own bw 0', 'execute if score #hd bw matches 1 run function bw:ai/rr_home',
                         'execute if score #own bw matches 1 run return 1',
                         # anything else: the walk to the nearest point of the map
                         'scoreboard players operation #fx bw = #sx bw', 'scoreboard players operation #fy bw = #sy bw', 'scoreboard players operation #fz bw = #sz bw',
                         'data modify storage bw:tmp fl set value {path:[],f:"f"}', 'data modify storage bw:tmp fl.m set from storage bw:ai ctx.m',
                         'scoreboard players set #fc bw 0', 'function bw:ai/flow_find',
                         'execute if score #fc bw matches 0 run return run function bw:ai/reroute_off',
                         'scoreboard players set #fn bw 0', 'function bw:ai/flow_put', 'function bw:ai/flow_walk with storage bw:tmp fl',
                         'execute unless data storage bw:tmp fl.hub run return run function bw:ai/reroute_off',
                         *DBG('REROUTE'), 'function bw:ai/rr_set'])
    P.fn('ai/rr_hd', [f'execute if score @s bw.team matches {i} store result score #hd bw run data get storage bw:bot ho{i}.dest' for i in BOTS])
    P.fn('ai/rr_home', ['data modify storage bw:tmp fl set value {path:[],f:"g"}', 'data modify storage bw:tmp fl.m set from storage bw:ai ctx.m',
                        'scoreboard players set #fc bw 0', 'function bw:ai/flow_find', 'execute if score #fc bw matches 0 run return 0',
                        'scoreboard players set #fn bw 0', 'function bw:ai/flow_put', 'function bw:ai/flow_walk with storage bw:tmp fl',
                        *[f'execute if score @s bw.team matches {i} if data storage bw:tmp fl{{hub:"g{i}"}} run scoreboard players set #own bw 1' for i in BOTS],
                        'execute if score #own bw matches 0 run return 0', *DBG('REROUTE-HOME'), 'function bw:ai/rr_set'])
    # the cell it stands in; the one above (it stands on a slab) or below (it is in the air); else one step to a side, level, up, or down as far as six
    CARDS = ((1, 0), (-1, 0), (0, 1), (0, -1))
    find = ['function bw:ai/flow_at {dx:0,dy:0,dz:0}', 'execute if score #fc bw matches 0 run function bw:ai/flow_at {dx:0,dy:1,dz:0}',
            'execute if score #fc bw matches 0 run function bw:ai/flow_at {dx:0,dy:-1,dz:0}']
    for dx, dz in CARDS:
        col = f'if block ~{dx} ~ ~{dz} #bw:open if block ~{dx} ~1 ~{dz} #bw:open'
        find.append(f'execute if score #fc bw matches 0 if block ~{dx} ~1 ~{dz} #bw:open if block ~{dx} ~2 ~{dz} #bw:open if block ~ ~2 ~ #bw:open run function bw:ai/flow_at {{dx:{dx},dy:1,dz:{dz}}}')
        for d in range(0, 7):
            find.append(' '.join(['execute if score #fc bw matches 0', col, *[f'if block ~{dx} ~-{j} ~{dz} #bw:open' for j in range(1, d + 1)], f'run function bw:ai/flow_at {{dx:{dx},dy:{-d},dz:{dz}}}']))
    P.fn('ai/flow_find', find + ['execute if score #fc bw matches 0 run function bw:ai/flow_rays'])
    # ... or further off in a straight line (eight directions, ten steps): from a bridge of its own to the island beside it. Every cell on the
    # line has to let a bot through - open, or something built that it can dig; the ground may be missing (it lays blocks) or lower (it drops)
    DIRS8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    P.fn('ai/flow_rays', [c_ for k, (dx, dz) in enumerate(DIRS8) for c_ in (
        'execute if score #fc bw matches 0 run scoreboard players operation #rx bw = #fx bw', 'execute if score #fc bw matches 0 run scoreboard players operation #rz bw = #fz bw',
        'execute if score #fc bw matches 0 run scoreboard players set #rn bw 0', 'execute if score #fc bw matches 0 run scoreboard players set #ryo bw 0',
        'execute if score #fc bw matches 0 run scoreboard players set #up bw 0', f'execute if score #fc bw matches 0 positioned ~{dx} ~ ~{dz} run function bw:ai/ray{k}')])
    for k, (dx, dz) in enumerate(DIRS8):
        P.fn(f'ai/ray{k}', ['scoreboard players add #rn bw 1', 'execute if score #rn bw matches 11.. run return 0',
                            *([f'scoreboard players {"add" if dx > 0 else "remove"} #rx bw 1'] if dx else []), *([f'scoreboard players {"add" if dz > 0 else "remove"} #rz bw 1'] if dz else []),
                            f'function bw:ai/ray{k}b'])
        P.fn(f'ai/ray{k}b', [# something in the way at this height: one block up is a step, two are a wall
                             f'execute unless block ~ ~ ~ #bw:open unless predicate bw:built run return run function bw:ai/ray{k}up',
                             'execute unless block ~ ~1 ~ #bw:open positioned ~ ~1 ~ unless predicate bw:built run return 0',
                             'scoreboard players set #up bw 0', 'function bw:ai/ray_at {dy:0}',
                             *[' '.join(['execute if score #fc bw matches 0', *[f'if block ~ ~-{j} ~ #bw:open' for j in range(1, d + 1)], f'run function bw:ai/ray_at {{dy:{-d}}}']) for d in (1, 2, 3)],
                             f'execute if score #fc bw matches 0 positioned ~{dx} ~ ~{dz} run function bw:ai/ray{k}'])
        P.fn(f'ai/ray{k}up', ['scoreboard players add #up bw 1', 'execute if score #up bw matches 2.. run return 0', 'scoreboard players add #ryo bw 1',
                              f'execute positioned ~ ~1 ~ run function bw:ai/ray{k}b'])
    P.fn('ai/ray_at', ['scoreboard players operation #ax bw = #rx bw', 'scoreboard players operation #az bw = #rz bw', '$scoreboard players set #ay bw $(dy)', 'scoreboard players operation #ay bw += #fy bw', 'scoreboard players operation #ay bw += #ryo bw',
                       'execute store result storage bw:tmp fl.x int 1 run scoreboard players get #ax bw', 'execute store result storage bw:tmp fl.y int 1 run scoreboard players get #ay bw',
                       'execute store result storage bw:tmp fl.z int 1 run scoreboard players get #az bw', 'function bw:ai/flow_get with storage bw:tmp fl',
                       'execute if score #fc bw matches 1.. run scoreboard players operation #fx bw = #ax bw', 'execute if score #fc bw matches 1.. run scoreboard players operation #fy bw = #ay bw',
                       'execute if score #fc bw matches 1.. run scoreboard players operation #fz bw = #az bw'])
    P.fn('ai/flow_at', ['$scoreboard players set #ax bw $(dx)', '$scoreboard players set #ay bw $(dy)', '$scoreboard players set #az bw $(dz)',
                        'scoreboard players operation #ax bw += #fx bw', 'scoreboard players operation #ay bw += #fy bw', 'scoreboard players operation #az bw += #fz bw',
                        'execute store result storage bw:tmp fl.x int 1 run scoreboard players get #ax bw', 'execute store result storage bw:tmp fl.y int 1 run scoreboard players get #ay bw',
                        'execute store result storage bw:tmp fl.z int 1 run scoreboard players get #az bw', 'function bw:ai/flow_get with storage bw:tmp fl',
                        'execute if score #fc bw matches 1.. run scoreboard players operation #fx bw = #ax bw', 'execute if score #fc bw matches 1.. run scoreboard players operation #fy bw = #ay bw',
                        'execute if score #fc bw matches 1.. run scoreboard players operation #fz bw = #az bw'])
    P.fn('ai/flow_get', ['$execute store result score #fc bw run data get storage bwflow:$(f) $(m)."$(x) $(y) $(z)"'])
    # the cell #fx #fy #fz becomes the next point of the way (its middle)
    P.fn('ai/flow_put', ['scoreboard players operation #x2 bw = #fx bw', 'scoreboard players operation #x2 bw += #fx bw', 'scoreboard players add #x2 bw 1',
                         'scoreboard players operation #z2 bw = #fz bw', 'scoreboard players operation #z2 bw += #fz bw', 'scoreboard players add #z2 bw 1',
                         'data modify storage bw:tmp fl.path append value [0d,0d,0d]',
                         'execute store result storage bw:tmp fl.path[-1][0] double 0.5 run scoreboard players get #x2 bw',
                         'execute store result storage bw:tmp fl.path[-1][1] double 1 run scoreboard players get #fy bw',
                         'execute store result storage bw:tmp fl.path[-1][2] double 0.5 run scoreboard players get #z2 bw',
                         'execute store result storage bw:tmp fl.x int 1 run scoreboard players get #fx bw', 'execute store result storage bw:tmp fl.y int 1 run scoreboard players get #fy bw',
                         'execute store result storage bw:tmp fl.z int 1 run scoreboard players get #fz bw'])
    P.fn('ai/flow_walk', ['$execute store result score #fc bw run data get storage bwflow:$(f) $(m)."$(x) $(y) $(z)"',
                          'execute if score #fc bw matches 40 run return run function bw:ai/flow_hub with storage bw:tmp fl',
                          # the foot of a planned way out of a patch (a pillar, a bridge): its points, and on from the ground it reaches
                          'execute if score #fc bw matches 50 run return run function bw:ai/flow_esc with storage bw:tmp fl',
                          'execute unless score #fc bw matches 1..32 run return 0',
                          'scoreboard players remove #fc bw 1', 'scoreboard players operation #fk bw = #fc bw', 'scoreboard players operation #fk bw /= #8 bw',
                          'scoreboard players operation #fc bw %= #8 bw', 'scoreboard players remove #fc bw 6',
                          'execute if score #fk bw matches 0 run scoreboard players add #fx bw 1', 'execute if score #fk bw matches 1 run scoreboard players remove #fx bw 1',
                          'execute if score #fk bw matches 2 run scoreboard players add #fz bw 1', 'execute if score #fk bw matches 3 run scoreboard players remove #fz bw 1',
                          'scoreboard players operation #fy bw += #fc bw', 'function bw:ai/flow_put',
                          'scoreboard players add #fn bw 1', 'execute if score #fn bw matches 600.. run return 0',
                          'function bw:ai/flow_walk with storage bw:tmp fl'])
    P.fn('ai/flow_esc', ['$data modify storage bw:tmp fl.path append from storage bwflow:x $(m)."$(x) $(y) $(z)".p[]',
                         *[f'$execute store result score #f{v} bw run data get storage bwflow:x $(m)."$(x) $(y) $(z)".f[{k}]' for k, v in enumerate('xyz')],
                         'scoreboard players add #fn bw 20', 'execute if score #fn bw matches 600.. run return 0',
                         *[f'execute store result storage bw:tmp fl.{v} int 1 run scoreboard players get #f{v} bw' for v in 'xyz'],
                         'function bw:ai/flow_walk with storage bw:tmp fl'])
    P.fn('ai/flow_hub', ['$data modify storage bw:tmp fl.hub set from storage bwflow:h $(m)."$(x) $(y) $(z)"'])
    # the way is known (bw:tmp fl.path, ending at the point fl.hub): what it was doing is kept for later
    P.fn('ai/rr_set', by_team('rr_set'))
    for i in BOTS:
        P.fn(f'ai/rr_set{i}', [f'execute unless score @s bw.dest matches 9 run data modify storage bw:bot ho{i} set value {{}}',
                               f'execute unless score @s bw.dest matches 9 run data modify storage bw:bot ho{i}.to set from storage bw:bot to{i}',
                               f'execute unless score @s bw.dest matches 9 store result storage bw:bot ho{i}.dest int 1 run scoreboard players get @s bw.dest',
                               f'data modify storage bw:bot r{i} set from storage bw:tmp fl.path', f'data modify storage bw:bot to{i} set from storage bw:tmp fl.hub',
                               f'data modify storage bw:bot tr{i} set value []', 'scoreboard players set @s bw.dest 9', 'scoreboard players set @s bw.st 2',
                               f'data modify entity {GOAL(i)} Pos set from storage bw:bot r{i}[0]'])
        # at the point: on to where it was going (if there is a planned way from here), else home
        P.fn(f'ai/homed{i}', ['scoreboard players set @s bw.rrc 0', f'execute if score #dbg bw matches 1 run tellraw @a ["HOMED bot{i} at ",{{nbt:"at{i}",storage:"bw:bot"}}," wanted ",{{nbt:"ho{i}.to",storage:"bw:bot"}}]', f'execute store result score @s bw.dest run data get storage bw:bot ho{i}.dest',
                              f'data modify storage bw:tmp rt.to set from storage bw:bot ho{i}.to', f'data modify storage bw:tmp cmp set from storage bw:bot ho{i}.to',
                              f'execute store success score #diff bw run data modify storage bw:tmp cmp set from storage bw:bot at{i}',
                              'execute if score #diff bw matches 0 unless score @s bw.dest matches 9 run return run function bw:ai/arrive',
                              f'execute store success score #ok bw run function bw:ai/route{i}',
                              f'execute if score #ok bw matches 0 run function bw:ai/to{i} {{to:"g{i}",dest:1}}'])
    P.fn('ai/homed', by_team('homed'))
    # not on ground the map knows (something built, a ledge below the islands): straight for the nearest point - up a pillar first if that is higher
    HUB = '@e[type=minecraft:marker,tag=bw.hub,sort=nearest,limit=1]'
    P.fn('ai/reroute_off', [f'execute unless entity {HUB} run return run function bw:ai/rr_giveup',
                            f'execute store result score #hy bw run data get entity {HUB} Pos[1]', 'execute store result score #by bw run data get entity @s Pos[1]',
                            'scoreboard players operation #hy bw -= #by bw', 'data modify storage bw:tmp fl.path set value []', 'data remove storage bw:tmp fl.cp',
                            # lower than the point: a pillar (fourteen blocks at a time: from its top it walks on and goes up again under the point).
                            # Where it stands there may be map overhead (the underside of an island): then the pillar starts a few steps to the side.
                            'execute if score #hy bw matches 15.. run scoreboard players set #hy bw 14',
                            'execute if score #hy bw matches 2.. run function bw:ai/rr_up',
                            'execute if score #hy bw matches 2.. if score #colok bw matches 0 run return run function bw:ai/rr_giveup',
                            f'data modify storage bw:tmp fl.path append from entity {HUB} Pos', f'data modify storage bw:tmp fl.hub set from entity {HUB} data.n',
                            *DBG('REROUTE-OFF'), 'function bw:ai/rr_set'])
    P.fn('ai/rr_up', ['function bw:ai/colchk',
                      'execute if score #colok bw matches 0 run function bw:ai/crays',
                      'execute if score #colok bw matches 0 run return 0',
                      # the foot of the pillar (if it is not where the bot stands), then its top
                      'execute if data storage bw:tmp fl.cp run data modify storage bw:tmp fl.path append from storage bw:tmp fl.cp',
                      'execute unless data storage bw:tmp fl.cp run data modify storage bw:tmp fl.cp set from entity @s Pos',
                      'data modify storage bw:tmp fl.path append from storage bw:tmp fl.cp',
                      'scoreboard players operation #by bw += #hy bw', 'execute store result storage bw:tmp fl.path[-1][1] double 1 run scoreboard players get #by bw'])
    # is there room for a pillar here, #hy blocks up (cells open, or built - those it digs)?
    P.fn('ai/colchk', ['scoreboard players set #colok bw 1', 'scoreboard players operation #cn bw = #hy bw', 'execute positioned ~ ~2 ~ run function bw:ai/colup'])
    P.fn('ai/colup', ['execute unless block ~ ~ ~ #bw:open unless predicate bw:built run return run scoreboard players set #colok bw 0',
                      'scoreboard players remove #cn bw 1', 'execute if score #cn bw matches 1.. positioned ~ ~1 ~ run function bw:ai/colup'])
    P.fn('ai/crays', [c_ for k, (dx, dz) in enumerate(DIRS8) for c_ in ('execute if score #colok bw matches 0 run scoreboard players set #rn bw 0', 'execute if score #colok bw matches 0 run scoreboard players set #up bw 0',
                                                                          f'execute if score #colok bw matches 0 positioned ~{dx} ~ ~{dz} run function bw:ai/cray{k}')])
    for k, (dx, dz) in enumerate(DIRS8):
        P.fn(f'ai/cray{k}', ['scoreboard players add #rn bw 1', 'execute if score #rn bw matches 41.. run return 0',
                             f'execute unless block ~ ~ ~ #bw:open unless predicate bw:built run return run function bw:ai/cray{k}up',
                             'execute unless block ~ ~1 ~ #bw:open positioned ~ ~1 ~ unless predicate bw:built run return 0',
                             'scoreboard players set #up bw 0', 'function bw:ai/colchk',
                             'execute if score #colok bw matches 1 align xyz positioned ~0.5 ~ ~0.5 summon minecraft:marker run return run function bw:ai/colmark',
                             f'execute positioned ~{dx} ~ ~{dz} run function bw:ai/cray{k}'])
        P.fn(f'ai/cray{k}up', ['scoreboard players add #up bw 1', 'execute if score #up bw matches 2.. run return 0', f'execute positioned ~ ~1 ~ run function bw:ai/cray{k}'])
    P.fn('ai/colmark', ['data modify storage bw:tmp fl.cp set from entity @s Pos', 'kill @s'])
    P.fn('ai/rr_giveup', ['scoreboard players add #giveups bw 1', *DBG('GIVEUP'), 'scoreboard players set @s bw.rrc 0', 'scoreboard players set @s bw.st 1', 'scoreboard players set @s bw.t1 60',
                       'scoreboard players set @s bw.dest 1'])

    # ------------------------------------------------------------------ arriving somewhere
    P.fn('ai/arrive', ['scoreboard players set @s bw.mine 0',
                       'execute if score @s bw.dest matches 9 run return run function bw:ai/homed',
                       'execute if score @s bw.dest matches 1 run scoreboard players set @s bw.st 1',
                       'execute if score @s bw.dest matches 1 run scoreboard players operation @s bw.t1 = #a_think bw',
                       'execute if score @s bw.dest matches 2 run scoreboard players set @s bw.st 1',
                       'execute if score @s bw.dest matches 2 run scoreboard players set @s bw.t1 30',
                       'execute if score @s bw.dest matches 3 run scoreboard players set @s bw.st 5',
                       'execute if score @s bw.dest matches 4 run function bw:ai/siege0',
                       'execute if score @s bw.dest matches 5 run scoreboard players set @s bw.st 6',
                       'execute if score @s bw.dest matches 5 run scoreboard players set @s bw.t1 320'])
    # ---- at home: take what the forge made, buy, then decide
    P.fn('ai/home', [*by_team('collect'), 'execute if score @s bw.t1 matches 1.. run return run function bw:ai/idle',
                     'execute if score @s bw.dest matches 2 run function bw:ai/shopping', 'function bw:ai/think'])
    P.fn('ai/idle', ['execute if score @s bw.t1 matches 15 run rotate @s ~40 0'])
    P.fn('ai/shopping', [*by_team('buy'), 'function bw:ai/equip', 'playsound minecraft:block.note_block.pling player @a ~ ~ ~ 0.3 2'])
    P.fn('ai/think', by_team('think'))
    for i in BOTS:
        nv0 = navs[maps[0]['id']]
        # (only at the forge itself: a bot that stands thinking somewhere else has nothing to pick up)
        P.fn(f'ai/collect{i}', [f'execute unless entity @e[type=minecraft:marker,tag=bw.gen.iron,tag=bw.t.{TEAMS[i]},distance=..6] run return 0',
                                f'scoreboard players operation #wfe{i} bw += #pfe{i} bw', f'scoreboard players set #pfe{i} bw 0',
                                f'scoreboard players operation #wau{i} bw += #pau{i} bw', f'scoreboard players set #pau{i} bw 0',
                                f'scoreboard players operation #wem{i} bw += #pem{i} bw', f'scoreboard players set #pem{i} bw 0'])
        # buying, in the order a person would: sword, armour, tools, then the nice things; diamonds go into team upgrades
        def buy(cond, cost, effect):
            c = ' '.join(f'if score #w{cur}{i} bw matches {n}..' for cur, n in cost)
            return [f'execute {cond} {c} run function bw:ai/b/{i}_{len(buys)}'], [*[f'scoreboard players remove #w{cur}{i} bw {n}' for cur, n in cost], *effect]
        buys = []
        def add(cond, cost, effect):
            ln, body = buy(cond, cost, effect); P.fn(f'ai/b/{i}_{len(buys)}', body); buys.append(ln[0])
        add(f'if score #bsw{i} bw matches 0', [('fe', 10)], [f'scoreboard players set #bsw{i} bw 1', 'scoreboard players set @s bw.sw 1'])
        add(f'if score #lvl bw matches 1.. if score #bar{i} bw matches 0', [('fe', 40)], [f'scoreboard players set #bar{i} bw 1', 'scoreboard players set @s bw.armor 1'])
        add(f'if score #lvl bw matches 2.. if score #btl{i} bw matches 0', [('fe', 20)], [f'scoreboard players set #btl{i} bw 1', 'scoreboard players set @s bw.tool 1'])
        add(f'if score #lvl bw matches 3.. if score #bsw{i} bw matches ..1', [('au', 7)], [f'scoreboard players set #bsw{i} bw 2', 'scoreboard players set @s bw.sw 2'])
        add(f'if score #lvl bw matches 4.. if score #bar{i} bw matches ..1', [('au', 12)], [f'scoreboard players set #bar{i} bw 2', 'scoreboard players set @s bw.armor 2'])
        add(f'if score #lvl bw matches 5.. if score #btl{i} bw matches 1', [('fe', 10), ('au', 3)], [f'scoreboard players set #btl{i} bw 2', 'scoreboard players set @s bw.tool 2'])
        add(f'if score #lvl bw matches 6.. if score #bsw{i} bw matches ..2', [('em', 4)], [f'scoreboard players set #bsw{i} bw 3', 'scoreboard players set @s bw.sw 3'])
        add(f'if score #lvl bw matches 8.. if score #bar{i} bw matches ..2', [('em', 6)], [f'scoreboard players set #bar{i} bw 3', 'scoreboard players set @s bw.armor 3'])
        add(f'if score #lvl bw matches 9.. if score #btl{i} bw matches 2', [('au', 6)], [f'scoreboard players set #btl{i} bw 3', 'scoreboard players set @s bw.tool 3'])
        add(f'if score #lvl bw matches 6.. if score #bga{i} bw matches ..1', [('au', 3)], [f'scoreboard players add #bga{i} bw 1'])
        add(f'if score #lvl bw matches 7.. if score #bfb{i} bw matches ..1', [('fe', 40)], [f'scoreboard players add #bfb{i} bw 1'])
        say = lambda what: tell('@a[tag=bw.play]', {'selector': '@s'}, t(f' 팀이 {what}을(를) 샀어.', 'dark_gray'))
        add(f'if score #lvl bw matches 5.. if score #sharp{i} bw matches 0', [('di', 4)], [f'scoreboard players set #sharp{i} bw 1'])
        for p, c in enumerate((2, 4, 8, 16)):
            add(f'if score #lvl bw matches {6 + 2 * p}.. if score #prot{i} bw matches {p}', [('di', c)], [f'scoreboard players set #prot{i} bw {p + 1}'])
        for f_, c in enumerate((2, 4)):
            add(f'if score #lvl bw matches {7 + 3 * f_}.. if score #fl{i} bw matches {f_}', [('di', c)],
                [f'scoreboard players set #fl{i} bw {f_ + 1}', f'scoreboard players operation #fs{i} bw = #a_eff bw', f'scoreboard players operation #fs{i} bw *= #{[150, 200][f_]} bw',
                 f'scoreboard players operation #fs{i} bw /= #100 bw'])
        # traps: a blinding one from stage 8, a miner's fatigue behind it from stage 11 (the second in the queue costs 2)
        add(f'if score #lvl bw matches 8.. if score #tqn{i} bw matches 0', [('di', 1)], [f'function bw:trap/add {{i:{i},k:1}}'])
        add(f'if score #lvl bw matches 11.. if score #tqn{i} bw matches 1', [('di', 2)], [f'function bw:trap/add {{i:{i},k:4}}'])
        add(f'if score #lvl bw matches 13.. if score #dbuff{i} bw matches 0', [('di', 5)], [f'scoreboard players set #dbuff{i} bw 1'])
        P.fn(f'ai/buy{i}', buys)
        # ---- what next? (asked at home, and wherever a job is finished)
        order = {m['id']: navs[m['id']]['near'][str(i)] for m in maps}
        think = [
            'scoreboard players set @s bw.st 1', 'scoreboard players operation @s bw.t1 = #a_think bw',
            # away from home with nothing to do there: the next bed, or home
            f'execute unless data storage bw:bot {{at{i}:"g{i}"}} unless data storage bw:bot {{at{i}:"k{i}"}} run return run function bw:ai/away{i}',
            f'execute if data storage bw:bot {{at{i}:"k{i}"}} run return run function bw:ai/to{i} {{to:"g{i}",dest:1}}',
            # the first trip needs wool, and wool costs iron
            f'execute if score #bsw{i} bw matches 0 if score #wfe{i} bw < #a_wait bw run return 0',
            # something worth buying: walk over to the shop
            f'scoreboard players set #can bw 0', *[ln.replace(f'run function bw:ai/b/{i}_{k}', 'run scoreboard players set #can bw 1') for k, ln in enumerate(buys)],
            f'execute if score #can bw matches 1 run return run function bw:ai/to{i} {{to:"k{i}",dest:2}}',
            # the bed first, if they know how
            f'execute if score #bed{i} bw matches 1 if score #bdone{i} bw matches 0 if data storage bw:bot def{i}[0] run return run function bw:ai/to{i} {{to:"b{i}",dest:3}}',
            # diamonds now and then, once there is something to spend them on
            'execute store result score #rn bw run random value 1..100',
            f'execute if score #lvl bw matches 5.. if score #sec bw matches 60.. if score #rn bw matches ..30 run return run function bw:ai/dia{i}',
            f'function bw:ai/pick{i}',
            f'execute if score @s bw.tgt matches 0.. run return run function bw:ai/attack{i}']
        P.fn(f'ai/think{i}', think)
        P.fn(f'ai/to{i}', [f'$data modify storage bw:tmp rt.to set value "$(to)"', '$scoreboard players set @s bw.dest $(dest)',
                           f'execute store success score #ok bw run function bw:ai/route{i}',
                           'execute if score #ok bw matches 0 run scoreboard players set @s bw.st 1', 'execute if score #ok bw matches 0 run scoreboard players set @s bw.t1 40'])
        # the nearest diamond generator, by map
        P.fn(f'ai/dia{i}', [f"execute if score #map bw matches {n + 1} run function bw:ai/to{i} {{to:\"d{navs[m['id']]['neard'][str(i)][0]}\",dest:5}}" for n, m in enumerate(maps)])
        P.fn(f'ai/attack{i}', ['execute store result storage bw:tmp at.j int 1 run scoreboard players get @s bw.tgt', f'function bw:ai/attack{i}b with storage bw:tmp at'])
        P.fn(f'ai/attack{i}b', [f'$function bw:ai/to{i} {{to:"a$(j)",dest:4}}'])
        # whom to go for: usually a neighbour, sometimes the player (more often the better they are)
        pick = ['scoreboard players set @s bw.tgt -1', 'execute store result score #rn bw run random value 1..100',
                'execute if score #rn bw <= #a_aggro bw if score #out0 bw matches 0 run scoreboard players set @s bw.tgt 0',
                'execute store result score #rn bw run random value 0..2']
        for n, m in enumerate(maps):
            od = order[m['id']]
            for s in range(3):
                for j in od[s:] + od[:s]:
                    pick.append(f'execute if score #map bw matches {n + 1} if score #rn bw matches {s} if score @s bw.tgt matches -1 if score #out{j} bw matches 0 run scoreboard players set @s bw.tgt {j}')
        P.fn(f'ai/pick{i}', pick)
        # somewhere out in the world: another bed if there is one, else home
        P.fn(f'ai/away{i}', [f'function bw:ai/pick{i}', 'execute store result score #rn bw run random value 1..100',
                             f'execute if data storage bw:bot {{at{i}:"b{i}"}} run return run function bw:ai/to{i} {{to:"g{i}",dest:1}}',
                             # with diamonds or emeralds in the pocket they go home to spend them; so they do when the fight took a lot out of them
                             f'execute if score #wdi{i} bw matches 2.. run return run function bw:ai/to{i} {{to:"g{i}",dest:1}}',
                             f'execute if score @s bw.hp matches ..300 run return run function bw:ai/to{i} {{to:"g{i}",dest:1}}',
                             f'execute if score @s bw.tgt matches 0.. if score #rn bw matches ..75 run return run function bw:ai/attack{i}',
                             f'function bw:ai/to{i} {{to:"g{i}",dest:1}}'])

    # ------------------------------------------------------------------ at an enemy bed
    P.fn('ai/siege0', ['scoreboard players set @s bw.st 4', 'scoreboard players set @s bw.t1 500', 'scoreboard players set @s bw.mine 0',
                       'execute store result storage bw:tmp sg.j int 1 run scoreboard players get @s bw.tgt', 'data modify storage bw:tmp sg.m set from storage bw:ai ctx.m',
                       'execute store result storage bw:tmp sg.i int 1 run scoreboard players get @s bw.team', 'function bw:ai/siege1 with storage bw:tmp sg'])
    P.fn('ai/siege1', ['$data modify entity @e[type=minecraft:marker,tag=bw.g$(i),limit=1] Pos set from storage bw:nav $(m).bed$(j)'])
    P.fn('ai/siege', [
        # the bed is gone, or this is taking too long: something else
        'scoreboard players set #gone bw 0',
        *[f'execute if score @s bw.tgt matches {j} if score #bed{j} bw matches 0 run scoreboard players set #gone bw 1' for j in range(N)],
        'execute if score #gone bw matches 1 run return run scoreboard players set @s bw.st 0',
        'execute if score @s bw.t1 matches 0 run return run scoreboard players set @s bw.st 0',
        *[f'execute if score @s bw.team matches {i} anchored eyes facing entity {GOAL(i)} feet run function bw:ai/siege2 {{i:{i}}}' for i in BOTS]])
    P.fn('ai/siege2', [
        'rotate @s ~ ~',
        # further than an arm: walk up to it
        '$execute unless entity @e[type=minecraft:marker,tag=bw.g$(i),distance=..3.6] run scoreboard players set @s bw.mf 2',
        '$execute unless entity @e[type=minecraft:marker,tag=bw.g$(i),distance=..3.6] anchored feet rotated ~ 0 run function bw:ai/feet',
        '$execute unless entity @e[type=minecraft:marker,tag=bw.g$(i),distance=..3.6] run return 0',
        # what is between the eyes and the bed?
        'scoreboard players set #rs bw 0', 'scoreboard players set #hit bw 0',
        'execute anchored eyes positioned ^ ^ ^0.3 run function bw:ai/ray',
        'execute if score #hit bw matches 0 run scoreboard players set @s bw.mf 1'])
    P.fn('ai/ray', ['execute unless block ~ ~ ~ #bw:open run return run function bw:ai/rayhit', 'scoreboard players add #rs bw 1',
                    'execute if score #rs bw matches ..12 positioned ^ ^ ^0.4 run function bw:ai/ray'])
    P.fn('ai/rayhit', ['scoreboard players set #hit bw 1',
                       'execute if block ~ ~ ~ #minecraft:beds run return run function bw:ai/bedhit',
                       'execute if predicate bw:built align xyz positioned ~0.5 ~ ~0.5 run return run function bw:ai/mine',
                       # the map itself is in the way: try from a little to the side
                       'scoreboard players operation @s bw.ms = @s bw.strafe', 'scoreboard players add @s bw.stuck 1',
                       'execute if score @s bw.stuck matches 60.. run function bw:ai/flip', 'execute if score @s bw.stuck matches 60.. run scoreboard players set @s bw.stuck 0'])
    P.fn('ai/bedhit', ['scoreboard players add @s bw.mine 1', 'scoreboard players operation #q bw = @s bw.mine', 'scoreboard players operation #q bw %= #4 bw',
                       'execute if score #q bw matches 0 run swing @s mainhand', 'execute if score #q bw matches 0 run playsound minecraft:block.wood.hit block @a ~ ~ ~ 0.8 1',
                       'execute if score @s bw.mine >= #a_bedt bw run function bw:ai/bedbreak'])
    P.fn('ai/bedbreak', ['scoreboard players set @s bw.mine 0', 'tag @e remove bw.breaker', 'tag @s add bw.breaker',
                         *[f'execute if score @s bw.tgt matches {j} run function bw:ai/bedkill{j}' for j in range(N)], 'scoreboard players set @s bw.st 0'])
    for j in range(N): P.fn(f'ai/bedkill{j}', by_map(maps, f'bedkill{j}'))

    # ------------------------------------------------------------------ building the bed defence, one block at a time
    P.fn('ai/build', ['execute if score @s bw.t1 matches 1.. run return 0', 'scoreboard players operation @s bw.t1 = #a_place bw', *by_team('build')])
    for i in BOTS:
        P.fn(f'ai/build{i}', [f'execute unless data storage bw:bot def{i}[0] run return run function bw:ai/built{i}',
                              f'data modify storage bw:tmp pl set from storage bw:bot def{i}[0]', f'data remove storage bw:bot def{i}[0]',
                              'function bw:ai/placeblock with storage bw:tmp pl'])
        P.fn(f'ai/built{i}', [f'scoreboard players set #bdone{i} bw 1', 'scoreboard players set @s bw.st 0'])
    P.fn('ai/placeblock', ['$rotate @s facing $(x).5 $(y).5 $(z).5', 'swing @s mainhand',
                           '$execute positioned $(x) $(y) $(z) if block ~ ~ ~ #bw:open unless entity @e[tag=bw.fighter,dx=0,dy=0,dz=0] run setblock ~ ~ ~ $(b)',
                           '$execute positioned $(x) $(y) $(z) run playsound minecraft:block.stone.place block @a ~ ~ ~ 0.8 1'])
    # ------------------------------------------------------------------ waiting at a diamond generator
    P.fn('ai/gem', ['execute as @e[type=minecraft:item,tag=bw.res,distance=..2.5] run function bw:ai/pickup',
                    'execute if score @s bw.t1 matches 100 run rotate @s ~90 0',
                    *[f'execute if score @s bw.team matches {i} if score #wdi{i} bw matches 4.. run scoreboard players set @s bw.t1 0' for i in BOTS],
                    'execute if score @s bw.t1 matches 0 run scoreboard players set @s bw.st 0'])
    P.fn('ai/pickup', ['execute store result score #n bw if items entity @s contents minecraft:diamond',
                       *[f'execute if score #me bw matches {i} run scoreboard players operation #wdi{i} bw += #n bw' for i in BOTS],
                       'execute store result score #n bw if items entity @s contents minecraft:emerald',
                       *[f'execute if score #me bw matches {i} run scoreboard players operation #wem{i} bw += #n bw' for i in BOTS],
                       'playsound minecraft:entity.item.pickup player @a ~ ~ ~ 0.3 1.6', 'kill @s'])

    # ------------------------------------------------------------------ dying
    P.fn('ai/die', [
        'scoreboard players set #kt bw -1', 'execute if score @s bw.lht matches 1.. run scoreboard players operation #kt bw = @s bw.lh',
        'scoreboard players set #final bw 1',
        *[f'execute if score @s bw.team matches {i} if score #bed{i} bw matches 1 run scoreboard players set #final bw 0' for i in BOTS],
        'function bw:game/kill',
        *by_team('dead'),
        'tag @s remove bw.bot', 'tag @s remove bw.fighter', 'particle minecraft:poof ~ ~1 ~ 0.3 0.5 0.3 0.02 12', 'kill @s',
        'execute if score #final bw matches 1 run function bw:game/check'])
    for i in BOTS:
        P.fn(f'ai/dead{i}', [
            # what it carried goes to whoever got it
            *[f'execute store result storage bw:tmp loot.{k} int 1 run scoreboard players get #w{k}{i} bw' for k in ('fe', 'au', 'di', 'em')],
            *[f'execute if score #w{k}{i} bw matches 1.. as @a[tag=bw.killer] run function bw:ai/loot_{k} with storage bw:tmp loot' for k in ('fe', 'au', 'di', 'em')],
            # ... a bot as well: into its purse
            *[f'execute if score #kt bw matches {j} run scoreboard players operation #w{k}{j} bw += #w{k}{i} bw' for j in BOTS if j != i for k in ('fe', 'au', 'di', 'em')],
            *[f'scoreboard players set #w{k}{i} bw 0' for k in ('fe', 'au', 'di', 'em')],
            # the sword is lost, armour stays, the tool drops a tier - the same as for people
            f'scoreboard players set #bsw{i} bw 0', f'execute if score #btl{i} bw matches 2.. run scoreboard players remove #btl{i} bw 1',
            f'execute if score #final bw matches 0 run scoreboard players set #bres{i} bw 100',
            f'execute if score #final bw matches 1 run ' + tell('@a', t('<', 'gray'), {'selector': '@s'}, t('> gg', 'gray'))])
    for k, item, ko, col in (('fe', 'iron_ingot', '철', 'white'), ('au', 'gold_ingot', '금', 'gold'), ('di', 'diamond', '다이아몬드', 'aqua'), ('em', 'emerald', '에메랄드', 'dark_green')):
        P.fn(f'ai/loot_{k}', [f'$give @s minecraft:{item} $({k})', f'$tellraw @s {{text:"+$({k}) {ko}",color:"{col}"}}'])
    # a player's own purse goes the same way when a bot gets them (run as the player, #kt = the team that did it)
    P.fn('ai/ploot', [*[f'execute store result score #l{k} bw run clear @s minecraft:{item} 0' for k, item in (('fe', 'iron_ingot'), ('au', 'gold_ingot'), ('di', 'diamond'), ('em', 'emerald'))],
                      *[f'execute if score #kt bw matches {j} run scoreboard players operation #w{k}{j} bw += #l{k} bw' for j in BOTS for k in ('fe', 'au', 'di', 'em')]])

    # ------------------------------------------------------------------ fireballs and TNT (for everyone)
    blast = lambda ench: ('summon minecraft:armor_stand ~ ~ ~ {Marker:1b,Invisible:1b,NoGravity:1b,Tags:["bw","bw.round","bw.boom"],'
                          'equipment:{head:{id:"minecraft:leather_helmet",count:1,components:{"minecraft:enchantments":{"bw:%s":1}}}}}' % ench)
    credit = ['scoreboard players operation #att bw = @s bw.team',
              'execute as @e[tag=bw.fighter,distance=..5] unless score @s bw.team = #att bw run scoreboard players operation @s bw.lh = #att bw',
              'execute as @e[tag=bw.fighter,distance=..5] unless score @s bw.team = #att bw run scoreboard players set @s bw.lht 200']
    # run as the thrower, at the point in front of its eyes, looking where the ball should go
    P.fn('fb/launch', [
        f'execute positioned 0.0 0.0 0.0 run tp {VEC} ^ ^ ^1',
        'summon minecraft:fireball ~ ~ ~ {Tags:["bw","bw.round","bw.fb","bw.fbnew"],ExplosionPower:0b,acceleration_power:0.0526d,Passengers:[{id:"minecraft:marker",Tags:["bw","bw.round","bw.fbm","bw.fbnew"]}]}',
        f'data modify entity @e[type=minecraft:fireball,tag=bw.fbnew,limit=1] Motion set from entity {VEC} Pos',
        'data modify entity @e[type=minecraft:fireball,tag=bw.fbnew,limit=1] Owner set from entity @s UUID',
        'scoreboard players operation @e[tag=bw.fbnew] bw.team = @s bw.team', 'tag @e[tag=bw.fbnew] remove bw.fbnew',
        'playsound minecraft:entity.blaze.shoot player @a ~ ~ ~ 1 1'])
    P.fn('fb/tick', [
        'execute as @e[type=minecraft:marker,tag=bw.fbm] unless predicate bw:riding at @s run function bw:fb/boom',
        'execute as @e[type=minecraft:marker,tag=bw.tntm] unless predicate bw:riding at @s run function bw:fb/tntboom',
        'scoreboard players add @e[type=minecraft:fireball,tag=bw.fb] bw.t 1', 'kill @e[type=minecraft:fireball,tag=bw.fb,scores={bw.t=160..}]',
        'execute as @a[tag=bw.fighter,scores={bw.use=1..}] at @s run function bw:fb/use',
        'execute as @a[tag=bw.fighter,scores={bw.tnt=1..}] at @s run function bw:fb/tnt',
        # bridge eggs: a trail of wool under the flying egg
        'execute as @e[type=minecraft:snowball,tag=!bw.seen] run function bw:fb/egg0',
        'execute as @e[type=minecraft:snowball,tag=bw.egg] at @s run function bw:fb/egg',
        'scoreboard players set @a[scores={bw.use=1..}] bw.use 0', 'scoreboard players set @a[scores={bw.tnt=1..}] bw.tnt 0'])
    P.fn('fb/boom', [blast('blast_fb'), *credit,
                     'execute as @e[tag=bw.fighter,distance=..2.6] run damage @s 4 minecraft:explosion', 'execute as @e[tag=bw.fighter,distance=2.6..4.2] run damage @s 2 minecraft:explosion', 'kill @s'])
    P.fn('fb/tntboom', [blast('blast_tnt'), *credit,
                        'execute as @e[tag=bw.fighter,distance=..2.5] run damage @s 9 minecraft:explosion', 'execute as @e[tag=bw.fighter,distance=2.5..4.5] run damage @s 5 minecraft:explosion',
                        'execute as @e[tag=bw.fighter,distance=4.5..6.5] run damage @s 2 minecraft:explosion', 'kill @s'])
    P.fn('fb/use', ['scoreboard players set @s bw.use 0',
                    'execute unless items entity @s weapon.mainhand *[minecraft:custom_data~{bw:"fireball"}] unless items entity @s weapon.offhand *[minecraft:custom_data~{bw:"fireball"}] run return 0',
                    # hacks.py: a fireball used on oneself (FB Longjump)
                    'execute store result score #pre bw run function bw:fb/pre', 'execute if score #pre bw matches 1 run return 0',
                    'function bw:fb/throw'])
    P.fn('fb/throw', ['clear @s *[minecraft:custom_data~{bw:"fireball"}] 1', 'execute anchored eyes positioned ^ ^ ^1.3 run function bw:fb/launch'])
    P.fn('fb/tnt', ['scoreboard players set @s bw.tnt 0', 'scoreboard players set #rs bw 0', 'scoreboard players set #hit bw 0',
                    'execute anchored eyes positioned ^ ^ ^0.2 run function bw:fb/tntray',
                    # not where the eyes point (it was put down on the side of a block further off): look all around
                    'execute if score #hit bw matches 0 store result score #n bw run fill ~-5 ~-5 ~-5 ~5 ~5 ~5 minecraft:air replace minecraft:tnt',
                    'execute if score #hit bw matches 0 if score #n bw matches 1.. anchored eyes positioned ^ ^ ^3 run function bw:fb/prime'])
    P.fn('fb/tntray', ['execute if block ~ ~ ~ minecraft:tnt run return run function bw:fb/ignite', 'scoreboard players add #rs bw 1',
                       'execute if score #rs bw matches ..28 positioned ^ ^ ^0.2 run function bw:fb/tntray'])
    P.fn('fb/ignite', ['scoreboard players set #hit bw 1', 'setblock ~ ~ ~ minecraft:air', 'execute align xyz positioned ~0.5 ~ ~0.5 run function bw:fb/prime'])
    P.fn('fb/prime', ['summon minecraft:tnt ~ ~ ~ {fuse:52s,explosion_power:0f,Tags:["bw","bw.round","bw.tntnew"],Passengers:[{id:"minecraft:marker",Tags:["bw","bw.round","bw.tntm","bw.tntnew"]}]}',
                      'scoreboard players operation @e[tag=bw.tntnew] bw.team = @s bw.team', 'tag @e[tag=bw.tntnew] remove bw.tntnew',
                      'playsound minecraft:entity.tnt.primed block @a ~ ~ ~ 1 1'])
    P.fn('fb/egg0', ['tag @s add bw.seen', 'execute if data entity @s Item.components."minecraft:custom_data"{bw:"egg"} run tag @s add bw.egg',
                     'execute if data entity @s Item.components."minecraft:custom_data"{bw:"bedbug"} at @s run function bw:mob/bugball',
                     'execute if entity @s[tag=bw.egg] at @s run scoreboard players operation @s bw.team = @a[tag=bw.fighter,sort=nearest,limit=1] bw.team'])
    P.fn('fb/egg', ['scoreboard players add @s bw.t 1', 'execute if score @s bw.t matches ..2 run return 0', 'execute if score @s bw.t matches 45.. run return run kill @s',
                    *[f'execute if score @s bw.team matches {i} run fill ~-1 ~-2 ~-1 ~ ~-2 ~ minecraft:{TEAMS[i]}_wool keep' for i in range(N)],
                    'playsound minecraft:block.wool.place block @a ~ ~ ~ 0.5 1.4'])
    load += ['scoreboard objectives add bw.use minecraft.used:minecraft.carrot_on_a_stick', 'scoreboard objectives add bw.tnt minecraft.used:minecraft.tnt',
             *[f'scoreboard players set #{v} bw {v}' for v in (8, 150, 200)], 'scoreboard players set #-1 bw -1']
    return dict(load=load, tick=[])
