"""The Bed Wars round itself. Walking through a lobby gate restores that map and starts a round on it: forges, diamond and emerald
generators run on Hypixel's clock; beds, deaths, respawns, eliminations, the sidebar and the end of the round; coins for what you did.
Opponents are added by ai.py and the shop windows by gui.py - this file only knows 'fighters' (players and bots) of teams 0..7."""
from util import TEAMS, TEAM_KO, TEAM_COLOR, Raw, snbt, t, line, tell, q
import items

N = 8
# ---- Hypixel's clock (solo / doubles). The wiki confirms: diamond tier I every 30 s (4 lie there at most), emerald tier I every 65 s (2 at most).
FORGE_IRON = 20            # ticks per iron ingot at a forge without upgrades
FORGE_GOLD = 120           # ticks per gold ingot
FORGE_EMERALD = 1200       # ticks per emerald once the forge is an Emerald Forge
FORGE_SPEED = [100, 150, 200, 200, 300]      # % by forge level: none, Iron, Golden, Emerald (also makes emeralds), Molten
CAP = dict(fe=48, au=8, di=4, em=2)
DIAMOND = [600, 460, 240]  # ticks per diamond at tier I, II, III
EMERALD = [1300, 1000, 600]
EVENTS = [(360, 'd2', '다이아몬드 II'), (720, 'e2', '에메랄드 II'), (1080, 'd3', '다이아몬드 III'), (1440, 'e3', '에메랄드 III'),
          (1800, 'beds', '침대 파괴'), (2400, 'sudden', '서든 데스'), (3000, 'over', '게임 종료')]
RESPAWN = 100              # ticks
COIN = dict(kill=5, final=15, bed=30, win=100, play=10)
GOAL = 10000               # coins to hold for the ending
# maps: coins to unlock (the smallest is open from the start) and how much more a round on it pays, in percent
MAP_PRICE = {'tea': 0, 'chess': 250, 'circus': 600, 'library': 1200, 'solar': 2500}
MAP_BONUS = {'tea': 100, 'chess': 115, 'circus': 130, 'library': 150, 'solar': 175}
ROMAN = ['I', 'II', 'III', 'IV']
BREAKABLE = [f'minecraft:{d}_wool' for d in TEAMS] + [f'minecraft:{d}_stained_glass' for d in TEAMS] + [
    'minecraft:terracotta', 'minecraft:end_stone', 'minecraft:oak_planks', 'minecraft:obsidian', 'minecraft:ladder', 'minecraft:sponge', 'minecraft:wet_sponge', 'minecraft:tnt']

def per_team(fmt):
    """one line per team; fmt may use {i} {dye} {ko} {col}"""
    return [fmt.format(i=i, dye=TEAMS[i], ko=TEAM_KO[i], col=TEAM_COLOR[i]) for i in range(N)]

def by_map(maps, name):
    return [f"execute if score #map bw matches {n + 1} run function bw:m/{m['id']}/{name}" for n, m in enumerate(maps)]

def write(P, maps, lobby, resets, n_installed):
    """P: util.Pack. maps: mapdata dicts (with name) in gate order. lobby: dict(tp='x y z yaw pitch', spawn=(x, y, z)).
    resets: per map id dict(forceload, unload, corners, kill, wipe (list of fills), place)."""
    load = ['scoreboard objectives add bw.death deathCount', 'scoreboard objectives add bw.side dummy ' + snbt(t('BED WARS', 'yellow', bold=True)),
            'scoreboard objectives add bw.lob dummy ' + snbt(t('배드워즈 타이쿤', 'yellow', bold=True)),
            *[f'scoreboard objectives add {o} dummy' for o in ('bw.team', 'bw.resp', 'bw.rs', 'bw.coins', 'bw.stage', 'bw.wins', 'bw.gk', 'bw.gf', 'bw.gb',
                                                             'bw.armor', 'bw.pick', 'bw.axe', 'bw.shears', 'bw.lh', 'bw.lht', 'bw.t', 'bw.gcd')],
            *per_team('team add bw.{dye}'), *per_team('team modify bw.{dye} color {col}'), *per_team('team modify bw.{dye} friendlyFire false'),
            *per_team('team modify bw.{dye} collisionRule pushOtherTeams'),
            *[f'scoreboard players set #{v} bw {v}' for v in (2, 4, 10, 20, 25, 60, 100, 1000)],
            'execute unless score #state bw matches 0.. run scoreboard players set #state bw 0',
            f'execute unless score #goal bw matches 1.. run scoreboard players set #goal bw {GOAL}',
            # a world that was closed in the middle of a round comes back to the lobby
            'execute if score #state bw matches 1.. run schedule function bw:game/close 20t']
    P.json('bw/tags/block/breakable.json', {'values': BREAKABLE + ['#minecraft:beds', 'minecraft:fire']})
    P.json('bw/tags/block/reset.json', {'values': BREAKABLE + ['minecraft:water', 'minecraft:fire']})
    P.json('bw/tags/item/placeable.json', {'values': [b for b in BREAKABLE if 'wet' not in b]})
    hidden = ['minecraft:can_break', 'minecraft:can_place_on', 'minecraft:unbreakable', 'minecraft:dyed_color', 'minecraft:attribute_modifiers', 'minecraft:attack_range']
    P.json('bw/item_modifier/placeable.json', {'type': 'minecraft:set_components', 'components': {
        'minecraft:can_place_on': [{}], 'minecraft:can_break': [{'blocks': '#bw:breakable'}], 'minecraft:tooltip_display': {'hidden_components': hidden}}})

    # ------------------------------------------------------------------ starting a round
    for n, m in enumerate(maps):
        mid = m['id']; r = resets[mid]
        P.fn(f'game/pick/{mid}', [
            'execute unless score #state bw matches 0 run return fail',
            f'execute unless entity @s[tag=bw.m.{mid}] run return run function bw:lobby/locked {{name:"{m["name"]}",price:{MAP_PRICE[mid]}}}',
            f'execute unless score #installed bw matches {n_installed}.. run return fail',
            'execute if score #wipe bw matches 1 run return fail',
            'scoreboard players set #state bw 1', f'scoreboard players set #map bw {n + 1}', 'scoreboard players set #tries bw 0',
            'tag @a remove bw.play', 'tag @a remove bw.out', 'tag @a remove bw.was_c',
            'tag @a[gamemode=creative] add bw.was_c', 'tag @a[gamemode=!spectator] add bw.play',
            'title @a times 5 100 10', 'title @a subtitle ' + snbt(t('맵을 준비하는 중…', 'gray')), 'title @a title ' + snbt(t(m['name'], 'gold', bold=True)),
            'scoreboard objectives setdisplay sidebar',
            f'function bw:reset/{mid}/load'])
        P.fn(f'reset/{mid}/load', [*r['forceload'], f'schedule function bw:reset/{mid}/try 10t'])
        P.fn(f'reset/{mid}/try', [
            *r['forceload'], 'scoreboard players add #tries bw 1',
            'execute if score #tries bw matches 120.. run return run function bw:game/close',
            *[f'execute unless loaded {x} {y} {z} run return run schedule function bw:reset/{mid}/try 10t' for x, y, z in r['corners']],
            *r['kill'], f'schedule function bw:reset/{mid}/w0 1t'])
        G = 14; groups = [r['wipe'][k:k + G] for k in range(0, len(r['wipe']), G)]
        for k, grp in enumerate(groups):
            P.fn(f'reset/{mid}/w{k}', grp + [f'schedule function bw:reset/{mid}/w{k + 1} 1t' if k + 1 < len(groups) else f'schedule function bw:reset/{mid}/place 1t'])
        P.fn(f'reset/{mid}/place', [*r['kill'], *r['place'], 'schedule function bw:game/begin 10t'])
    P.fn('game/begin', [
        'scoreboard players set #state bw 3',
        *[f'scoreboard players set #{v} bw 0' for v in ('time', 'sec', 't20', 't4', 'dg', 'eg', 'sudden', 'allbeds', 'lvl')],
        'scoreboard players set #dt bw 1', 'scoreboard players set #et bw 1',
        *per_team('scoreboard players set #bed{i} bw 1'),
        *[f'scoreboard players set #{v}{i} bw 0' for v in ('out', 'hum', 'fl', 'fe', 'au', 'fm', 'pfe', 'pau', 'pem', 'bres', 'sharp', 'prot', 'haste', 'heal', 'trap', 'trapt') for i in range(N)],
        *per_team('scoreboard players set #fs{i} bw 100'),
        # the opponents are as good as the best player's stage; coins grow with it too
        'execute as @a[tag=bw.play] run scoreboard players operation #lvl bw > @s bw.stage',
        'scoreboard players operation #mult bw = #lvl bw', 'scoreboard players operation #mult bw *= #25 bw', 'scoreboard players add #mult bw 100',
        'scoreboard players set #mapmult bw 100',
        'gamerule keep_inventory true', 'gamerule immediate_respawn true', 'gamerule natural_health_regeneration false', 'gamerule spawn_mobs false',
        'gamerule advance_time false', 'gamerule advance_weather false', 'gamerule show_death_messages false', 'gamerule locator_bar false',
        'gamerule mob_griefing false', 'gamerule fall_damage true', 'gamerule show_advancement_messages false', 'time set 6000', 'weather clear',
        *by_map(maps, 'begin'),
        # a bigger map pays more
        'scoreboard players operation #mult bw *= #mapmult bw', 'scoreboard players operation #mult bw /= #100 bw',
        'scoreboard players operation #bonus bw = #mapmult bw', 'scoreboard players remove #bonus bw 100',
        'execute if score #bonus bw matches 1.. run ' + tell('@a[tag=bw.play]', t('큰 맵 보너스: 코인 +', 'yellow'), {'score': {'name': '#bonus', 'objective': 'bw'}, 'color': 'gold'}, t('%', 'gold')),
        'title @a[tag=bw.play] times 5 40 10', 'title @a[tag=bw.play] subtitle ' + snbt(t('침대를 지키고, 남의 침대를 부숴!', 'gray')),
        'title @a[tag=bw.play] title ' + snbt(t('게임 시작!', 'green', bold=True)),
        'execute as @a[tag=bw.play] at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 0.4 1.6',
        # the first rounds: how the shop is opened and how to give up
        tell('@a[tag=bw.play,scores={bw.wins=..1}]', t('[배드워즈 타이쿤] ', 'gold'), t('상인 앞의 구리 상자를 우클릭하면 상점이 열려. 그만두려면 ', 'white'), t('/trigger lobby', 'yellow')),
        'scoreboard objectives setdisplay sidebar bw.side', 'function bw:game/side'])
    # one player joins a team: colours, score, gear back to nothing
    P.fn('game/join', ['$team join bw.$(dye) @s', '$scoreboard players set @s bw.team $(i)', '$scoreboard players set #hum$(i) bw 1',
                       *[f'scoreboard players set @s {o} 0' for o in ('bw.armor', 'bw.pick', 'bw.axe', 'bw.shears', 'bw.resp', 'bw.death', 'bw.gk', 'bw.gf', 'bw.gb', 'bw.lht')],
                       'gamemode adventure @s', 'clear @s', 'effect clear @s', 'attribute @s minecraft:attack_speed base set 1024',
                       'experience set @s 0 levels', 'experience set @s 0 points',
                       *[f'item replace entity @s enderchest.{k} with minecraft:air' for k in range(27)], 'function bw:game/kit'])
    # ------------------------------------------------------------------ what a player wears and carries by right
    kit = ['effect give @s minecraft:night_vision infinite 0 true', 'effect give @s minecraft:saturation infinite 0 true',
           'effect give @s minecraft:instant_health 1 10 true']
    for i in range(N):
        kit += [f'execute if score @s bw.team matches {i} run item replace entity @s armor.head with {items.armour("helmet", "leather", i)}',
                f'execute if score @s bw.team matches {i} run item replace entity @s armor.chest with {items.armour("chestplate", "leather", i)}',
                f'execute if score @s bw.team matches {i} if score @s bw.armor matches 0 run item replace entity @s armor.legs with {items.armour("leggings", "leather", i)}',
                f'execute if score @s bw.team matches {i} if score @s bw.armor matches 0 run item replace entity @s armor.feet with {items.armour("boots", "leather", i)}']
    for lv, mat in ((1, 'chainmail'), (2, 'iron'), (3, 'diamond')):
        kit += [f'execute if score @s bw.armor matches {lv} run item replace entity @s armor.legs with {items.armour("leggings", mat)}',
                f'execute if score @s bw.armor matches {lv} run item replace entity @s armor.feet with {items.armour("boots", mat)}']
    kit += [f'execute unless items entity @s container.* #minecraft:swords run give @s {items.WOOD_SWORD}', 'function bw:game/tools', 'function bw:game/enchant']
    P.fn('game/kit', kit)
    P.fn('game/tools', ['clear @s #minecraft:pickaxes', 'clear @s #minecraft:axes', 'clear @s minecraft:shears',
                        *[f'execute if score @s bw.pick matches {lv + 1} run give @s {items.tool_item(tr)}' for lv, tr in enumerate(items.PICKS)],
                        *[f'execute if score @s bw.axe matches {lv + 1} run give @s {items.tool_item(tr)}' for lv, tr in enumerate(items.AXES)],
                        f'execute if score @s bw.shears matches 1 run give @s {items.SHEARS}', 'function bw:game/enchant'])
    # team upgrades that live on the gear: Sharpened Swords, Reinforced Armor (put on again whenever the gear changes)
    ench = []
    for i in range(N):
        ench.append(f'execute if score @s bw.team matches {i} if score #sharp{i} bw matches 1.. run function bw:game/sharp')
        for lv in (1, 2, 3, 4):
            ench.append(f'execute if score @s bw.team matches {i} if score #prot{i} bw matches {lv} run function bw:game/prot{lv}')
    P.fn('game/enchant', ench)
    slots = [f'container.{k}' for k in range(36)]
    P.fn('game/sharp', [f'execute if items entity @s {s} #bw:sharp run item modify entity @s {s} bw:sharp' for s in slots])
    P.json('bw/tags/item/sharp.json', {'values': ['#minecraft:swords', '#minecraft:axes']})
    P.json('bw/item_modifier/sharp.json', {'type': 'minecraft:set_enchantments', 'enchantments': {'minecraft:sharpness': 1}, 'add': False})
    for lv in (1, 2, 3, 4):
        P.fn(f'game/prot{lv}', [f'item modify entity @s armor.{s} bw:prot{lv}' for s in ('head', 'chest', 'legs', 'feet')])
        P.json(f'bw/item_modifier/prot{lv}.json', {'type': 'minecraft:set_enchantments', 'enchantments': {'minecraft:protection': lv, 'minecraft:binding_curse': 1}, 'add': False})
    # blocks picked up from the ground (your own wool, broken off) may be placed again; empty buckets and bottles go
    P.fn('game/fixblocks', [f'execute if items entity @s {s} #bw:placeable[!minecraft:can_place_on] run item modify entity @s {s} bw:placeable' for s in slots + ['weapon.offhand']])

    # ------------------------------------------------------------------ the round, tick by tick
    P.fn('game/tick', [
        'scoreboard players add #time bw 1', 'scoreboard players add #t20 bw 1',
        *by_map(maps, 'tick'),
        'execute as @a[tag=bw.play,scores={bw.death=1..}] at @s run function bw:game/pdeath',
        'execute as @a[tag=bw.play,scores={bw.resp=1..}] run function bw:game/presp',
        'scoreboard players remove @e[tag=bw.fighter,scores={bw.lht=1..}] bw.lht 1',
        'execute as @a[tag=bw.fighter] if items entity @s container.* #bw:placeable[!minecraft:can_place_on] run function bw:game/fixblocks',
        # someone who joins the server in the middle of a round watches
        'execute as @a[tag=!bw.play,gamemode=!spectator] run function bw:game/watch',
        'execute if score #t20 bw matches 20.. run function bw:game/second'])
    P.fn('game/watch', ['gamemode spectator @s', *by_map(maps, 'limbo')])
    sec = ['scoreboard players set #t20 bw 0', 'scoreboard players add #sec bw 1']
    for at, key, name in EVENTS:
        sec.append(f'execute if score #sec bw matches {at} run function bw:game/ev/{key}')
    sec += [
        # health comes back the old way: about half a heart every four seconds
        'scoreboard players operation #q4 bw = #sec bw', 'scoreboard players operation #q4 bw %= #4 bw',
        'execute if score #q4 bw matches 0 run effect give @e[tag=bw.fighter] minecraft:regeneration 3 0 true',
        'execute if score #sudden bw matches 1 if score #q4 bw matches 0..1 as @e[tag=bw.fighter] run damage @s 1 minecraft:magic',
        'clear @a[tag=bw.play] minecraft:bucket', 'clear @a[tag=bw.play] minecraft:glass_bottle',
        *per_team('execute if score #haste{i} bw matches 1.. run effect give @a[tag=bw.fighter,scores={{bw.team={i}}}] minecraft:haste 3 0 true'),
        *per_team('execute if score #haste{i} bw matches 2 run effect give @a[tag=bw.fighter,scores={{bw.team={i}}}] minecraft:haste 3 1 true'),
        'function bw:game/holo', 'function bw:game/check', 'execute if score #state bw matches 3 run function bw:game/side']
    P.fn('game/second', sec)
    def announce(*parts): return tell('@a', t('▶ ', 'gold'), *parts)
    up = lambda what, col, tier: announce(t(what, col), t(' 생성기가 ', 'yellow'), t(tier + '단계', 'red'), t('로 올랐어!', 'yellow'))
    P.fn('game/ev/d2', ['scoreboard players set #dt bw 2', up('다이아몬드', 'aqua', 'II')])
    P.fn('game/ev/d3', ['scoreboard players set #dt bw 3', up('다이아몬드', 'aqua', 'III')])
    P.fn('game/ev/e2', ['scoreboard players set #et bw 2', up('에메랄드', 'dark_green', 'II')])
    P.fn('game/ev/e3', ['scoreboard players set #et bw 3', up('에메랄드', 'dark_green', 'III')])
    P.fn('game/ev/beds', [announce(t('남은 침대가 전부 파괴됐어!', 'red', bold=True)), 'scoreboard players set #allbeds bw 1',
                          'execute as @a at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 1', *by_map(maps, 'allbeds')])
    P.fn('game/ev/sudden', ['scoreboard players set #sudden bw 1', announce(t('서든 데스! 이제 모두가 서서히 피해를 입어.', 'red', bold=True))])
    P.fn('game/ev/over', [announce(t('시간 종료!', 'yellow')), 'function bw:game/end_lose'])

    # ---- sidebar: lines are fake players with their own display names
    def row(n, comp):
        return [f'scoreboard players set #r{n} bw.side {n}', f'scoreboard players display name #r{n} bw.side {snbt(comp)}', f'scoreboard players display numberformat #r{n} bw.side blank']
    nxt = []; prev = 0
    for at, key, name in EVENTS:
        nxt += [f'execute if score #sec bw matches {prev}..{at - 1} run scoreboard players set #left bw {at}',
                f'execute if score #sec bw matches {prev}..{at - 1} run data modify storage bw:tmp side.ev set value {q(name)}']
        prev = at
    nxt += ['scoreboard players operation #left bw -= #sec bw', 'scoreboard players operation #lm bw = #left bw', 'scoreboard players operation #lm bw /= #60 bw',
            'scoreboard players operation #ls bw = #left bw', 'scoreboard players operation #ls bw %= #60 bw',
            'execute store result storage bw:tmp side.m int 1 run scoreboard players get #lm bw', 'execute store result storage bw:tmp side.s int 1 run scoreboard players get #ls bw',
            'data modify storage bw:tmp side.z set value ""', 'execute if score #ls bw matches ..9 run data modify storage bw:tmp side.z set value "0"']
    for i in range(N):                                          # ✔ bed standing, 1 = someone left without a bed, ✘ out
        nxt += [f'data modify storage bw:tmp side.t{i} set value {snbt(t("✔", "green", bold=True))}',
                f'execute if score #bed{i} bw matches 0 run data modify storage bw:tmp side.t{i} set value {snbt(t("1", "yellow"))}',
                f'execute if score #out{i} bw matches 1 run data modify storage bw:tmp side.t{i} set value {snbt(t("✘", "red"))}',
                f'data modify storage bw:tmp side.y{i} set value ""',
                f'execute if score #hum{i} bw matches 1 run data modify storage bw:tmp side.y{i} set value " 나"']
    P.fn('game/side', nxt + ['function bw:game/side2 with storage bw:tmp side'])
    me = '@a[tag=bw.play,limit=1]'
    lines = [line(t(' ')), line(t('$(ev) ', 'white'), t('$(m):$(z)$(s)', 'green')), line(t('  '))]
    for i in range(N):
        lines.append(line(t(TEAM_KO[i][0], TEAM_COLOR[i], bold=True), t(' ' + TEAM_KO[i] + ': ', 'white'), Raw('$(t%d)' % i), t('$(y%d)' % i, 'gray')))
    lines += [line(t('   ')), line(t('처치 ', 'white'), {'score': {'name': me, 'objective': 'bw.gk'}, 'color': 'green'},
                                   t('  최종 ', 'white'), {'score': {'name': me, 'objective': 'bw.gf'}, 'color': 'green'},
                                   t('  침대 ', 'white'), {'score': {'name': me, 'objective': 'bw.gb'}, 'color': 'green'}),
              line(t('코인 ', 'white'), {'score': {'name': me, 'objective': 'bw.coins'}, 'color': 'gold'})]
    s2 = []
    for k, comp in enumerate(lines): s2 += ['$' + c if '$(' in c else c for c in row(len(lines) - k, comp)]
    P.fn('game/side2', s2)

    # ------------------------------------------------------------------ dying and coming back
    P.fn('game/pdeath', [
        'scoreboard players set @s bw.death 0',
        'scoreboard players set #kt bw -1', 'execute if score @s bw.lht matches 1.. run scoreboard players operation #kt bw = @s bw.lh',
        'scoreboard players set @s bw.lht 0',
        'scoreboard players set #final bw 1',
        *per_team('execute if score @s bw.team matches {i} if score #bed{i} bw matches 1 run scoreboard players set #final bw 0'),
        'function bw:game/kill',
        'clear @s', 'execute if score @s bw.pick matches 2.. run scoreboard players remove @s bw.pick 1',
        'execute if score @s bw.axe matches 2.. run scoreboard players remove @s bw.axe 1',
        'gamemode spectator @s', 'tag @s remove bw.fighter',
        f'execute if score #final bw matches 0 run scoreboard players set @s bw.resp {RESPAWN}',
        'execute if score #final bw matches 0 run title @s times 0 30 5',
        'execute if score #final bw matches 0 run title @s title ' + snbt(t('죽었어!', 'red', bold=True)),
        'execute if score #final bw matches 1 run function bw:game/pout'])
    # as the one who died: #kt = the team that did it (or -1), #final = 1 when there is no bed to come back to
    V = {'selector': '@s'}; K = {'selector': '@e[tag=bw.killer,limit=1]'}; FK = t(' 최종 처치!', 'aqua', bold=True)
    P.fn('game/kill', [
        'tag @e remove bw.killer',
        'execute if score #kt bw matches 0.. as @e[tag=bw.fighter] if score @s bw.team = #kt bw run tag @s add bw.killer',
        'tag @s remove bw.killer',
        'execute if entity @e[tag=bw.killer] if score #final bw matches 0 run ' + tell('@a', V, t('을(를) ', 'gray'), K, t('이(가) 처치했어.', 'gray')),
        'execute if entity @e[tag=bw.killer] if score #final bw matches 1 run ' + tell('@a', V, t('을(를) ', 'gray'), K, t('이(가) 처치했어.', 'gray'), FK),
        'execute unless entity @e[tag=bw.killer] if score #final bw matches 0 run ' + tell('@a', V, t('이(가) 죽었어.', 'gray')),
        'execute unless entity @e[tag=bw.killer] if score #final bw matches 1 run ' + tell('@a', V, t('이(가) 죽어서 탈락했어.', 'gray')),
        'execute as @a[tag=bw.killer] at @s run function bw:game/reward_kill'])
    P.fn('game/reward_kill', [
        'playsound minecraft:entity.experience_orb.pickup master @s ~ ~ ~ 1 1',
        'execute if score #final bw matches 0 run scoreboard players add @s bw.gk 1', 'execute if score #final bw matches 1 run scoreboard players add @s bw.gf 1',
        f'execute if score #final bw matches 0 run function bw:game/coins {{n:{COIN["kill"]},why:"처치"}}',
        f'execute if score #final bw matches 1 run function bw:game/coins {{n:{COIN["final"]},why:"최종 처치"}}'])
    # coins grow with the stage: +25% each
    P.fn('game/coins', ['$scoreboard players set #r bw $(n)', 'scoreboard players operation #r bw *= #mult bw', 'scoreboard players operation #r bw /= #100 bw',
                        'scoreboard players operation @s bw.coins += #r bw',
                        '$tellraw @s [{text:"+",color:"gold"},{score:{name:"#r",objective:"bw"},color:"gold"},{text:" 코인",color:"gold"},{text:" ($(why))",color:"gray"}]'])
    P.fn('game/pout', ['tag @s add bw.out', 'title @s times 5 60 20', 'title @s subtitle ' + snbt(t('침대가 없어서 부활할 수 없어', 'gray')),
                       'title @s title ' + snbt(t('탈락!', 'red', bold=True))])
    P.fn('game/presp', [
        'scoreboard players remove @s bw.resp 1',
        'scoreboard players operation @s bw.rs = @s bw.resp', 'scoreboard players add @s bw.rs 19', 'scoreboard players operation @s bw.rs /= #20 bw',
        'execute if score @s bw.resp matches 1.. run title @s times 0 10 5',
        'execute if score @s bw.resp matches 1.. run title @s subtitle ' + snbt(line({'score': {'name': '@s', 'objective': 'bw.rs'}, 'color': 'red'}, t('초 뒤에 부활', 'yellow'))),
        'execute if score @s bw.resp matches 1.. run title @s title ' + snbt(t('죽었어!', 'red', bold=True)),
        'execute if score @s bw.resp matches 0 run function bw:game/prespawn'])
    P.fn('game/prespawn', [
        *by_map(maps, 'spawn'),
        'gamemode adventure @s', 'function bw:game/kit', 'title @s times 0 20 5', 'title @s subtitle ""', 'title @s title ' + snbt(t('부활!', 'green', bold=True)),
        'effect give @s minecraft:resistance 2 4 true'])

    # ------------------------------------------------------------------ beds
    P.fn('game/bedgone', [        # macro: i ko col; the breaker (if anyone) carries the tag bw.breaker
        '$scoreboard players set #bed$(i) bw 0',
        '$execute if entity @e[tag=bw.breaker] run tellraw @a [{text:""},{text:"\\n침대 파괴 > ",bold:true,color:"white"},{text:"$(ko) 침대",color:"$(col)"},{text:"를 ",color:"gray"},{selector:"@e[tag=bw.breaker,limit=1]"},{text:"이(가) 부쉈어!\\n",color:"gray"}]',
        '$execute unless entity @e[tag=bw.breaker] run tellraw @a [{text:""},{text:"\\n침대 파괴 > ",bold:true,color:"white"},{text:"$(ko) 침대",color:"$(col)"},{text:"가 부서졌어!\\n",color:"gray"}]',
        'execute as @a at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 0.7 1',
        '$title @a[tag=bw.play,scores={bw.team=$(i)}] times 5 50 15',
        '$title @a[tag=bw.play,scores={bw.team=$(i)}] subtitle {text:"이제 죽으면 부활할 수 없어!",color:"gray"}',
        '$title @a[tag=bw.play,scores={bw.team=$(i)}] title {text:"침대 파괴됨!",color:"red",bold:true}',
        'execute as @a[tag=bw.breaker] run scoreboard players add @s bw.gb 1',
        f'execute as @a[tag=bw.breaker] run function bw:game/coins {{n:{COIN["bed"]},why:"침대 파괴"}}',
        'tag @e remove bw.breaker', 'function bw:game/check', 'function bw:game/side'])

    # ------------------------------------------------------------------ who is still in, and the end
    chk = []
    for i in range(N):
        chk += [f'scoreboard players set #mem{i} bw 0',
                f'execute if entity @a[tag=bw.play,tag=!bw.out,scores={{bw.team={i}}}] run scoreboard players set #mem{i} bw 1',
                f'execute if entity @e[tag=bw.bot,scores={{bw.team={i}}}] run scoreboard players set #mem{i} bw 1',
                f'execute if score #bres{i} bw matches 1.. run scoreboard players set #mem{i} bw 1',
                f'execute if score #out{i} bw matches 0 if score #bed{i} bw matches 0 if score #mem{i} bw matches 0 run function bw:game/teamout {{i:{i},ko:"{TEAM_KO[i]}",col:"{TEAM_COLOR[i]}"}}']
    chk += ['scoreboard players set #alive bw 0', *per_team('execute if score #out{i} bw matches 0 run scoreboard players add #alive bw 1'),
            'scoreboard players set #humans bw 0', *per_team('execute if score #hum{i} bw matches 1 if score #out{i} bw matches 0 run scoreboard players add #humans bw 1'),
            'execute if score #state bw matches 3 if score #humans bw matches 0 run return run function bw:game/end_lose',
            'execute if score #state bw matches 3 if score #alive bw matches ..1 run function bw:game/end_win']
    P.fn('game/check', chk)
    P.fn('game/teamout', ['$scoreboard players set #out$(i) bw 1',
                          '$tellraw @a [{text:""},{text:"\\n팀 탈락 > ",bold:true,color:"white"},{text:"$(ko) 팀",color:"$(col)"},{text:"이 탈락했어!\\n",color:"red"}]'])
    P.fn('game/end_win', ['scoreboard players set #state bw 4', 'title @a times 10 100 20', 'title @a subtitle ' + snbt(t('마지막까지 살아남았어', 'gray')),
                          'title @a title ' + snbt(t('승리!', 'gold', bold=True)),
                          'execute as @a at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1',
                          f'execute as @a[tag=bw.play] run function bw:game/coins {{n:{COIN["win"]},why:"승리"}}',
                          f'execute as @a[tag=bw.play] run function bw:game/coins {{n:{COIN["play"]},why:"참가"}}',
                          'scoreboard players add @a[tag=bw.play] bw.wins 1', 'scoreboard players add @a[tag=bw.play] bw.stage 1',
                          tell('@a[tag=bw.play]', t('단계가 올랐어. 다음 판부터 상대가 더 강해져.', 'yellow')),
                          'schedule function bw:game/close 160t'])
    P.fn('game/end_lose', ['scoreboard players set #state bw 4', 'title @a times 10 100 20', 'title @a subtitle ' + snbt(t('다시 도전해 봐', 'gray')),
                           'title @a title ' + snbt(t('패배', 'red', bold=True)),
                           f'execute as @a[tag=bw.play] run function bw:game/coins {{n:{COIN["play"]},why:"참가"}}', 'schedule function bw:game/close 160t'])
    P.fn('game/close', [
        'schedule clear bw:game/begin', 'schedule clear bw:game/close',
        *[f"schedule clear bw:reset/{m['id']}/{w}" for m in maps for w in ['try', 'place'] + [f'w{k}' for k in range(0, 1 + (len(resets[m['id']]['wipe']) - 1) // 14)]],
        'worldborder center 0 0', 'worldborder set 59999968',
        # the bots leave without the dying act (a dying mannequin cannot be saved, and the server says so in its log)
        'function bw:ai/purge', 'kill @e[tag=bw.round,type=!minecraft:mannequin]', 'kill @e[type=minecraft:item,tag=bw.res]',
        *by_map(maps, 'end'),
        'scoreboard objectives setdisplay sidebar',
        'execute as @a[tag=bw.play] run function bw:game/leave',
        'gamemode adventure @a[gamemode=spectator,tag=!bw.play]', f'tp @a[tag=!bw.play] {lobby["tp"]}',
        'gamerule natural_health_regeneration true', 'gamerule show_death_messages true', 'gamerule immediate_respawn false', 'gamerule keep_inventory false',
        'gamerule locator_bar true', 'gamerule show_advancement_messages true', 'scoreboard players set #state bw 0', 'scoreboard players set #map bw 0'])
    sx, sy, sz = lobby['spawn']
    P.fn('game/leave', ['tag @s remove bw.play', 'tag @s remove bw.out', 'tag @s remove bw.fighter', 'scoreboard players set @s bw.resp 0', 'scoreboard players set @s bw.death 0',
                        'team leave @s', 'clear @s', 'effect clear @s', 'attribute @s minecraft:attack_speed base reset',
                        'gamemode adventure @s', 'gamemode creative @s[tag=bw.was_c]', 'tag @s remove bw.was_c',
                        f'tp @s {lobby["tp"]}', f'spawnpoint @s {sx} {sy} {sz}',
                        'effect give @s minecraft:night_vision infinite 0 true', 'effect give @s minecraft:saturation infinite 0 true',
                        tell('@s', t('코인 ', 'gray'), {'score': {'name': '@s', 'objective': 'bw.coins'}, 'color': 'gold'},
                             t('  ·  단계 ', 'gray'), {'score': {'name': '@s', 'objective': 'bw.stage'}, 'color': 'aqua'})])

    # ------------------------------------------------------------------ per map: positions baked in
    for n, m in enumerate(maps):
        mid = m['id']; T = m['teams']; cx, cy, cz = m['center']; r = resets[mid]
        limbo = f"{cx}.5 {m['top_y'] + 14} {cz}.5"
        P.fn(f'm/{mid}/limbo', [f'tp @s {limbo} 0 60'])
        begin = [f'scoreboard players set #mapmult bw {MAP_BONUS[mid]}', f'worldborder center {cx}.5 {cz}.5', f"worldborder set {r['border']}", 'worldborder warning distance 0',
                 f'execute as @a[tag=bw.play] run function bw:game/join {{i:0,dye:"{TEAMS[0]}"}}',
                 f'execute as @a[tag=bw.play] run function bw:m/{mid}/spawn', f"spawnpoint @a[tag=bw.play] {cx} {m['top_y'] + 14} {cz}"]
        stand = '{Marker:1b,Invisible:1b,NoGravity:1b,CustomNameVisible:1b,Tags:["bw","bw.round","bw.holo"%s],CustomName:%s}'
        for k, (x, y, z) in enumerate(m['diamond'] + m['emerald']):
            kind = 'd' if k < len(m['diamond']) else 'e'
            name, col, block = (('다이아몬드', 'aqua', 'diamond_block') if kind == 'd' else ('에메랄드', 'dark_green', 'emerald_block'))
            begin += [f'summon minecraft:armor_stand {x}.5 {y + 2.9} {z}.5 ' + stand % (f',"bw.holo.{kind}t"', snbt(line(t('단계 ', 'yellow'), t('I', 'red')))),
                      f'summon minecraft:armor_stand {x}.5 {y + 2.6} {z}.5 ' + stand % ('', snbt(t(name, col, bold=True))),
                      f'summon minecraft:armor_stand {x}.5 {y + 2.3} {z}.5 ' + stand % (f',"bw.holo.{kind}s"', snbt(t('곧 생성', 'yellow'))),
                      f'summon minecraft:armor_stand {x}.5 {y + 0.4} {z}.5 {{Invisible:1b,NoGravity:1b,Marker:1b,Tags:["bw","bw.round","bw.spin"],equipment:{{head:{{id:"minecraft:{block}",count:1}}}}}}']
        P.fn(f'm/{mid}/begin', begin)
        P.fn(f'm/{mid}/spawn', [f"execute if score @s bw.team matches {i} run tp @s {T[i]['spawn'][0]}.5 {T[i]['spawn'][1]} {T[i]['spawn'][2]}.5 {T[i]['yaw']} 0" for i in range(N)])
        tick = ['scoreboard players add #t4 bw 1', 'execute if score #t4 bw matches 4.. run scoreboard players set #t4 bw 0']
        res = lambda item, x, y, z: f'summon minecraft:item {x}.5 {y + 0.3} {z}.5 {{Item:{{id:"minecraft:{item}",count:1}},PickupDelay:0s,Age:-32768s,Motion:[0d,0d,0d],Tags:["bw","bw.res"]}}'
        for i in range(N):
            gx, gy, gz = T[i]['gen']
            tick += [f'execute if score #out{i} bw matches 0 run scoreboard players operation #fe{i} bw += #fs{i} bw',
                     f'execute if score #fe{i} bw matches {FORGE_IRON * 100}.. run function bw:m/{mid}/fe{i}',
                     f'execute if score #out{i} bw matches 0 run scoreboard players operation #au{i} bw += #fs{i} bw',
                     f'execute if score #au{i} bw matches {FORGE_GOLD * 100}.. run function bw:m/{mid}/au{i}',
                     f'execute if score #fl{i} bw matches 3.. run scoreboard players operation #fm{i} bw += #fs{i} bw',
                     f'execute if score #fm{i} bw matches {FORGE_EMERALD * 100}.. run function bw:m/{mid}/fm{i}']
            for rs, item, per, cap, pile in (('fe', 'iron_ingot', FORGE_IRON, CAP['fe'], 'pfe'), ('au', 'gold_ingot', FORGE_GOLD, CAP['au'], 'pau'), ('fm', 'emerald', FORGE_EMERALD, 4, 'pem')):
                P.fn(f'm/{mid}/{rs}{i}', [
                    f'scoreboard players remove #{rs}{i} bw {per * 100}',
                    # a team of bots keeps a pile its bot collects when it is home; a team with people gets real ingots on the pad
                    f'execute if score #hum{i} bw matches 0 if score #{pile}{i} bw matches ..{cap - 1} run scoreboard players add #{pile}{i} bw 1',
                    f'execute if score #hum{i} bw matches 0 run return 1',
                    f'execute store result score #n bw if items entity @e[type=minecraft:item,x={gx},y={gy},z={gz},distance=..3] contents minecraft:{item}',
                    f'execute if score #n bw matches ..{cap - 1} run ' + res(item, gx, gy, gz)])
        tick += ['scoreboard players add #dg bw 1', 'scoreboard players add #eg bw 1']
        for tier in (1, 2, 3):
            tick += [f'execute if score #dt bw matches {tier} if score #dg bw matches {DIAMOND[tier - 1]}.. run function bw:m/{mid}/gem_d',
                     f'execute if score #et bw matches {tier} if score #eg bw matches {EMERALD[tier - 1]}.. run function bw:m/{mid}/gem_e']
        for kind, pts, item, cap in (('d', m['diamond'], 'diamond', CAP['di']), ('e', m['emerald'], 'emerald', CAP['em'])):
            g = [f'scoreboard players set #{kind}g bw 0']
            for (x, y, z) in pts:
                g += [f'execute store result score #n bw if items entity @e[type=minecraft:item,x={x},y={y},z={z},distance=..3] contents minecraft:{item}',
                      f'execute if score #n bw matches ..{cap - 1} run ' + res(item, x, y, z)]
            P.fn(f'm/{mid}/gem_{kind}', g)
        tick += ['execute as @e[type=minecraft:armor_stand,tag=bw.spin] at @s run tp @s ~ ~ ~ ~7 ~',
                 # the void, and the sky: nobody builds above the map
                 f"execute as @a[tag=bw.fighter] at @s if entity @s[y=-200,dy={m['void_y'] + 200}] run damage @s 1000 minecraft:out_of_world",
                 f"execute as @a[tag=bw.fighter] at @s if entity @s[y={r['ymax']},dy=400] run function bw:game/toohigh",
                 f'execute if score #t4 bw matches 0 run function bw:m/{mid}/beds']
        # beds are looked at five times a second
        beds = []
        for i in range(N):
            bx, by, bz = T[i]['bed']; hx, hy, hz = T[i]['bed_head']; f = T[i]['bed_facing']; blk = T[i]['bed_block']
            beds += [f'execute if score #bed{i} bw matches 1 unless block {bx} {by} {bz} #minecraft:beds run function bw:m/{mid}/bed{i}',
                     f'execute if score #bed{i} bw matches 1 unless block {hx} {hy} {hz} #minecraft:beds run function bw:m/{mid}/bed{i}']
            clean = f'kill @e[type=minecraft:item,x={bx},y={by},z={bz},distance=..5,nbt={{Item:{{id:"minecraft:{blk}"}}}}]'
            P.fn(f'm/{mid}/bed{i}', [
                'tag @e remove bw.breaker',
                f'execute positioned {bx} {by} {bz} as @a[tag=bw.fighter,distance=..9,sort=nearest] unless score @s bw.team matches {i} unless entity @a[tag=bw.breaker] run tag @s add bw.breaker',
                # nobody of another team is there: its own team did it, and the bed is put back
                f'execute unless entity @a[tag=bw.breaker] run return run function bw:m/{mid}/bedfix{i}',
                f'function bw:m/{mid}/bedkill{i}'])
            P.fn(f'm/{mid}/bedfix{i}', [f'setblock {bx} {by} {bz} minecraft:air', f'setblock {hx} {hy} {hz} minecraft:air',
                                        f'setblock {bx} {by} {bz} minecraft:{blk}[facing={f},part=foot]', f'setblock {hx} {hy} {hz} minecraft:{blk}[facing={f},part=head]', clean,
                                        f'execute positioned {bx} {by} {bz} run ' + tell('@a[distance=..9]', t('자기 팀 침대는 부술 수 없어!', 'red'))])
            # the bed of team i is gone for good (the breaker, if any, already carries bw.breaker)
            P.fn(f'm/{mid}/bedkill{i}', [f'scoreboard players set #bed{i} bw 0', f'setblock {bx} {by} {bz} minecraft:air', f'setblock {hx} {hy} {hz} minecraft:air', clean,
                                         f'particle minecraft:explosion {bx} {by + 1} {bz} 0.5 0.5 0.5 0 6',
                                         f'function bw:game/bedgone {{i:{i},ko:"{TEAM_KO[i]}",col:"{TEAM_COLOR[i]}"}}'])
        P.fn(f'm/{mid}/beds', beds)
        P.fn(f'm/{mid}/allbeds', ['tag @e remove bw.breaker', *[f'execute if score #bed{i} bw matches 1 run function bw:m/{mid}/bedkill{i}' for i in range(N)]])
        P.fn(f'm/{mid}/tick', tick)
        P.fn(f'm/{mid}/end', r['unload'])
    P.fn('game/toohigh', ['damage @s 2 minecraft:out_of_world', 'title @s actionbar ' + snbt(t('여긴 너무 높아! 내려가.', 'red'))])
    # hologram texts once a second
    h = []
    for tier in (1, 2, 3):
        h += [f'execute if score #dt bw matches {tier} run scoreboard players set #di bw {DIAMOND[tier - 1]}', f'execute if score #et bw matches {tier} run scoreboard players set #ei bw {EMERALD[tier - 1]}',
              f'execute if score #dt bw matches {tier} run data modify storage bw:tmp holo.dt set value "{ROMAN[tier - 1]}"', f'execute if score #et bw matches {tier} run data modify storage bw:tmp holo.et set value "{ROMAN[tier - 1]}"']
    h += ['scoreboard players operation #di bw -= #dg bw', 'scoreboard players operation #ei bw -= #eg bw', 'scoreboard players add #di bw 19', 'scoreboard players add #ei bw 19',
          'scoreboard players operation #di bw /= #20 bw', 'scoreboard players operation #ei bw /= #20 bw',
          'execute store result storage bw:tmp holo.d int 1 run scoreboard players get #di bw', 'execute store result storage bw:tmp holo.e int 1 run scoreboard players get #ei bw',
          'function bw:game/holo2 with storage bw:tmp holo']
    P.fn('game/holo', h)
    hn = lambda tag, comp: f'$execute as @e[type=minecraft:armor_stand,tag={tag}] run data modify entity @s CustomName set value {comp}'
    P.fn('game/holo2', [hn('bw.holo.dt', '[{text:""},{text:"단계 ",color:"yellow"},{text:"$(dt)",color:"red"}]'), hn('bw.holo.et', '[{text:""},{text:"단계 ",color:"yellow"},{text:"$(et)",color:"red"}]'),
                        hn('bw.holo.ds', '[{text:""},{text:"$(d)",color:"red"},{text:"초 뒤에 생성",color:"yellow"}]'), hn('bw.holo.es', '[{text:""},{text:"$(e)",color:"red"},{text:"초 뒤에 생성",color:"yellow"}]')])

    # ------------------------------------------------------------------ the lobby between rounds
    lrow = lambda n, comp: [f'scoreboard players set #l{n} bw.lob {n}', f'scoreboard players display name #l{n} bw.lob {snbt(comp)}', f'scoreboard players display numberformat #l{n} bw.lob blank']
    one = '@a[limit=1,sort=arbitrary]'
    sc = lambda obj, col: {'score': {'name': one, 'objective': obj}, 'color': col}
    P.fn('lobby/second', [
        'scoreboard players set #lt bw 0',
        'effect give @a minecraft:night_vision infinite 0 true', 'effect give @a[gamemode=!creative,gamemode=!spectator] minecraft:saturation infinite 0 true',
        'scoreboard players add @a bw.coins 0', 'scoreboard players add @a bw.stage 0', 'scoreboard players add @a bw.wins 0',
        'execute as @a[tag=!bw.init] run function bw:lobby/init',
        # a player who was in a round when the world closed
        'execute as @a[tag=bw.play] run function bw:game/leave',
        *lrow(7, line(t(' '))), *lrow(6, line(t('코인: ', 'white'), sc('bw.coins', 'gold'))), *lrow(5, line(t('목표: ', 'white'), {'score': {'name': '#goal', 'objective': 'bw'}, 'color': 'yellow'})),
        *lrow(4, line(t('  '))), *lrow(3, line(t('단계: ', 'white'), sc('bw.stage', 'aqua'))), *lrow(2, line(t('승리: ', 'white'), sc('bw.wins', 'green'))), *lrow(1, line(t('   '))),
        'scoreboard objectives setdisplay sidebar bw.lob',
        'execute as @a[tag=!bw.ended] if score @s bw.coins >= #goal bw at @s run function bw:lobby/ending'])
    P.fn('lobby/locked', ['execute if score @s bw.gcd matches 1.. run return 0', 'scoreboard players set @s bw.gcd 60',
                          '$title @s actionbar [{text:"$(name) 맵은 잠겨 있어 · ",color:"red"},{text:"$(price) 코인",color:"gold"}]',
                          '$tellraw @s [{text:"[배드워즈 타이쿤] ",color:"gold"},{text:"$(name)",color:"aqua"},{text:" 맵은 아직 잠겨 있어. 업그레이드 가게 상자 맨 아랫줄에서 ",color:"white"},{text:"$(price) 코인",color:"gold"},{text:"으로 해금할 수 있어.",color:"white"}]',
                          'playsound minecraft:block.chest.locked master @s ~ ~ ~ 0.8 1'])
    P.fn('lobby/init', ['tag @s add bw.init', *[f'tag @s add bw.m.{k}' for k, v in MAP_PRICE.items() if v == 0], *[f'tag @s add bw.u.{k}' for k in items.STARTERS],
                        tell('@s', t('[배드워즈 타이쿤] ', 'gold'), t('성문으로 들어가면 게임이 시작돼. 이기면 코인을 받고, 스폰 서쪽 업그레이드 가게의 상자에서 코인으로 상점 물건과 맵을 해금해. ', 'white'),
                             {'score': {'name': '#goal', 'objective': 'bw'}, 'color': 'yellow'}, t(' 코인을 모으면 엔딩!', 'yellow'))])
    fw = '{LifeTime:%d,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":{flight_duration:1,explosions:[{shape:"%s",colors:[I;%s],fade_colors:[I;16777215],has_twinkle:true}]}}}}'
    P.fn('lobby/ending', ['tag @s add bw.ended', 'title @s times 10 140 30',
                          'title @s subtitle ' + snbt(line(t('코인 ', 'gray'), {'score': {'name': '@s', 'objective': 'bw.coins'}, 'color': 'gold'}, t('개를 모았어!', 'gray'))),
                          'title @s title ' + snbt(t('엔딩!', 'gold', bold=True)),
                          'playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1',
                          'summon minecraft:firework_rocket ~2 ~1 ~ ' + fw % (22, 'large_ball', '16766720,16711680'),
                          'summon minecraft:firework_rocket ~-2 ~1 ~1 ' + fw % (28, 'star', '65535,65280'),
                          'summon minecraft:firework_rocket ~ ~1 ~-2 ' + fw % (34, 'burst', '16711935,255'),
                          tell('@a', t('\n★ ', 'gold'), {'selector': '@s'}, t('이(가) 목표 코인을 다 모았어. 배드워즈 타이쿤 클리어!\n', 'yellow'),
                               t('   승리 ', 'gray'), {'score': {'name': '@s', 'objective': 'bw.wins'}, 'color': 'green'}, t('번 · ', 'gray'),
                               {'score': {'name': '@s', 'objective': 'bw.stage'}, 'color': 'aqua'}, t('단계. 계속 플레이해도 돼.\n', 'gray'))])
    tick = ['execute if score #state bw matches 3 run function bw:game/tick',
            # everyone alive in a round is a fighter; so is every bot
            'tag @a[tag=bw.fighter,tag=!bw.play] remove bw.fighter', 'execute if score #state bw matches 3 run tag @a[tag=bw.play,gamemode=adventure] add bw.fighter',
            'tag @a[tag=bw.fighter,gamemode=!adventure] remove bw.fighter',
            'scoreboard players remove @a[scores={bw.gcd=1..}] bw.gcd 1',
            'scoreboard players add #lt bw 1', 'execute if score #state bw matches 0 if score #lt bw matches 20.. run function bw:lobby/second']
    return dict(load=load, tick=tick)
