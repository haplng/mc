"""The black market: a dealer hidden in the lobby sells 'hacks' for coins. None of them is a real cheat - each one is the datapack doing,
for the player who bought it, what the cheat of that name would make visible: longer reach, less knockback, blocks appearing under the feet…
Three shelves; the lower the shelf, the later it opens and the more it costs."""
from util import TEAMS, snbt, t, line, tell, q
import gui
from gui import ln, icon, cost_line, short

# key, name, shelf (1 beginner, 2 advanced, 3 endgame), icon, levels [(label, coins)], what it does here
HACKS = [
    dict(key='velocity', name='Velocity', tier=1, icon='feather', levels=[('jump', 150), ('reduce', 300)], desc=['맞아도 덜 밀려나.', 'jump: 넉백 20% 감소', 'reduce: 넉백 45% 감소']),
    dict(key='reach', name='Reach', tier=1, icon='fishing_rod', levels=[('3.1', 120), ('3.5', 300), ('4.0', 600)], desc=['더 멀리 있는 적을 때려.', '기본 사거리는 3.0칸.']),
    dict(key='eagle', name='Eagle', tier=1, icon='rabbit_foot', levels=[('0.2 80ms', 100), ('0.3 50ms', 250)], desc=['블록을 들고 가장자리에 서면', '알아서 멈춰서 안 떨어져.', '2단계는 더 빨리, 더 확실히 잡아 줘.']),
    dict(key='aim', name='Aim Assist', tier=1, icon='ender_eye', levels=[('normal', 200), ('silent', 500)], desc=['normal: 조준이 가까운 적 쪽으로', '부드럽게 끌려가.', 'silent: 화면은 그대로인데', '살짝 빗나가도 맞아.']),
    dict(key='clicker', name='AutoClicker', tier=1, icon='clock', levels=[('', 350)], desc=['검을 들고 적을 조준하고 있으면', '알아서 계속 때려.']),
    dict(key='block', name='AutoBlock', tier=1, icon='shield', levels=[('Legit Autoblock', 200), ('Lag block', 450)], desc=['맞을 때 알아서 막아.', 'Legit Autoblock: 피해 25% 감소', 'Lag block: 피해 50% 감소']),
    dict(key='kbd', name='Knockback Displace', tier=1, icon='piston', levels=[('90degree', 250), ('void', 600)], desc=['내가 때린 적이 엉뚱한 쪽으로 날아가.', '90degree: 옆으로 밀려나', 'void: 가까운 낭떠러지 쪽으로 밀려나']),
    dict(key='antifb', name='Anti Fireball', tier=1, icon='fire_charge', levels=[('', 200)], desc=['날아오는 화염구를', '알아서 되받아쳐.']),
    dict(key='velocity2', name='Velocity', tier=2, icon='phantom_membrane', levels=[('0 100', 900)], desc=['넉백이 아예 사라져.', '(초급 Velocity를 reduce까지 사야 해)'], need=('velocity', 2)),
    dict(key='scaffold', name='Scaffold', tier=2, icon='scaffolding', levels=[('Tower(vanilla)', 1000), ('Tower(vanilla), Keep Y', 1500)],
         desc=['가방의 블록이 발밑에 알아서 놓여.', '제자리에서 점프를 누르면 탑이 올라가.', 'Keep Y: 뛰면서 가도 같은 높이로 깔려.']),
    dict(key='lag', name='Lag range', tier=2, icon='repeater', levels=[('100ms', 700), ('200ms', 1200)], desc=['Reach에 더해 사거리가 늘어나.', '100ms: +0.56칸  /  200ms: +1.12칸']),
    dict(key='stasis', name='Stasis', tier=2, icon='ender_pearl', levels=[('', 800)], desc=['공허로 떨어지면 3초 동안', '공중에 붕 떠 있어. (30초에 한 번)']),
    dict(key='tower', name='Tower', tier=3, icon='firework_rocket', levels=[('fly x1.5 motion', 1500), ('fly x3 motion', 2500)], desc=['제자리에서 점프를 누르고 있으면', '블록을 깔면서 날듯이 올라가.', 'x1.5 / x3: 그냥 쌓는 것보다 그만큼 빨라.']),
    dict(key='nofall', name='NoFall', tier=3, icon='hay_block', levels=[('', 1200)], desc=['낙하 피해를 안 받아.']),
    dict(key='fbjump', name='FB Longjump', tier=3, icon='blaze_powder', levels=[('', 2000)], desc=['화염구를 발밑을 보고 쓰면', '피해 없이 아주 멀리 날아가.']),
    dict(key='tpaura', name='TP Aura', tier=3, icon='chorus_fruit', levels=[('', 3500)], desc=['검을 들고 있으면 14칸 안의 적에게', '순간이동해서 때려.']),
]
for n, h in enumerate(HACKS): h['id'] = n + 1
TIER = {1: dict(name='초급', stage=3, need=0, color='green'), 2: dict(name='고급', stage=6, need=4, color='gold'), 3: dict(name='최종장', stage=9, need=3, color='red')}
SLOT = {}                                              # where each hack lies in the window; its on/off switch is one row below
for tier, row0 in ((1, 9), (2, 27), (3, 32)):
    for k, h in enumerate([h for h in HACKS if h['tier'] == tier]): SLOT[h['key']] = row0 + k
ON = lambda k: f'scores={{bw.h_{k}=1..}},tag=!bw.off_{k}'
BOT = '@e[type=minecraft:mannequin,tag=bw.bot'
SCAF = ['end_stone', 'terracotta', 'oak_planks']

def write(P, G, maps, navs):
    load = [*[f'scoreboard objectives add bw.h_{h["key"]} dummy' for h in HACKS],
            *[f'scoreboard objectives add {o} dummy' for o in ('bw.hc1', 'bw.hc2', 'bw.stc', 'bw.sy', 'bw.acd', 'bw.tpc', 'bw.ecd')]]
    # =================================================================== the dealer's window
    slots = {}
    slots[4] = [('', icon('ender_chest', 150, '암시장', 'dark_purple', [ln('여기서 산 건 계속 네 거야.'), ln('아래의 염료를 누르면 켜고 끌 수 있어.'), ln(''),
                                                                    ln({'text': '초급', 'color': 'green'}, ': 3단계부터'), ln({'text': '고급', 'color': 'gold'}, ': 6단계 + 초급 4개'),
                                                                    ln({'text': '최종장', 'color': 'red'}, ': 9단계 + 고급 3개')]))]
    for s, (tier, name) in ((0, (1, '초급 핵')), (45, (2, '고급 핵')), (53, (3, '최종장 핵'))):
        slots[s] = [('', icon({1: 'lime_dye', 2: 'orange_dye', 3: 'red_dye'}[tier], 150, name, TIER[tier]['color'],
                              [ln(f'{TIER[tier]["stage"]}단계부터 열려.')] + ([ln(f'{TIER[tier - 1]["name"]} 핵 {TIER[tier]["need"]}개가 있어야 해.')] if tier > 1 else [])))]
    for h in HACKS:
        k = h['key']; T = TIER[h['tier']]; n = len(h['levels']); obj = f'bw.h_{k}'; gid = 400 + h['id']
        closed = f'unless score @s bw.stage matches {T["stage"]}..'
        opened = f'if score @s bw.stage matches {T["stage"]}..'
        vs = [(closed, icon('barrier', gid, '???', 'dark_gray', [ln(f'{T["name"]} 핵'), ln(''), ln({'text': f'{T["stage"]}단계가 되면 보여 줄게.', 'color': 'red'})]))]
        if T['need']:
            cnt = f'bw.hc{h["tier"] - 1}'
            vs.append((f'{opened} unless score @s {cnt} matches {T["need"]}..',
                       icon('barrier', gid, h['name'], 'dark_gray', [ln(f'{T["name"]} 핵'), ln(''), ln({'text': f'{TIER[h["tier"] - 1]["name"]} 핵을 {T["need"]}개 이상 가져와.', 'color': 'red'})])))
            opened += f' if score @s {cnt} matches {T["need"]}..'
        if h.get('need'):
            vs.append((f'{opened} unless score @s bw.h_{h["need"][0]} matches {h["need"][1]}..',
                       icon('barrier', gid, h['name'] + ' (0 100)', 'dark_gray', [ln({'text': '초급 Velocity를 끝까지 올려야 해.', 'color': 'red'})])))
            opened += f' if score @s bw.h_{h["need"][0]} matches {h["need"][1]}..'
        def lvlines(have):
            if n == 1 and not h['levels'][0][0]: return []
            out = []
            for j, (label, price) in enumerate(h['levels']):
                mark = '✔ ' if j < have else ('▶ ' if j == have else '   ')
                out.append(ln({'text': mark + label, 'color': 'green' if j < have else ('yellow' if j == have else 'dark_gray')}, {'text': f'  {price} 코인', 'color': 'gold' if j >= have else 'dark_gray'}))
            return out + [ln('')]
        for have in range(n + 1):
            cond = f'{opened} if score @s {obj} matches {have}'
            title = h['name'] + (f' ({h["levels"][min(have, n - 1)][0]})' if h['levels'][min(have, n - 1)][0] else '')
            body = [ln({'text': T['name'] + ' 핵', 'color': T['color']}), ln(''), *[ln(x) for x in h['desc']], ln(''), *lvlines(have)]
            if have == n:
                vs.append((cond, icon(h['icon'], gid, title, 'green', body + [ln({'text': '✔ 전부 가지고 있어.', 'color': 'green'})], glint=True)))
            else:
                price = h['levels'][have][1]
                vs += [(f'{cond} if score @s bw.coins matches {price}..', icon(h['icon'], gid, title, 'yellow', [cost_line(price, 'coins'), ln('')] + body + [ln({'text': '클릭해서 구매!' if have == 0 else '클릭해서 강화!', 'color': 'yellow'})], glint=have > 0)),
                       (f'{cond} unless score @s bw.coins matches {price}..', icon(h['icon'], gid, title, 'red', [cost_line(price, 'coins'), ln('')] + body + [short('coins')], glint=have > 0))]
        slots[SLOT[k]] = vs
        tg = 430 + h['id']
        slots[SLOT[k] + 9] = [(f'if entity @s[{ON(k)}]', icon('lime_dye', tg, h['name'] + ': 켜짐', 'green', [ln('클릭하면 꺼져.')])),
                              (f'if entity @s[scores={{{obj}=1..}},tag=bw.off_{k}]', icon('gray_dye', tg, h['name'] + ': 꺼짐', 'gray', [ln('클릭하면 켜져.')]))]
        # buying the next level
        act = [f'execute unless score @s bw.stage matches {T["stage"]}.. run return run function bw:gui/no {{msg:"{T["stage"]}단계가 되면 와."}}']
        if T['need']: act.append(f'execute unless score @s bw.hc{h["tier"] - 1} matches {T["need"]}.. run return run function bw:gui/no {{msg:"{TIER[h["tier"] - 1]["name"]} 핵을 {T["need"]}개 이상 가져와."}}')
        if h.get('need'): act.append(f'execute unless score @s bw.h_{h["need"][0]} matches {h["need"][1]}.. run return run function bw:gui/no {{msg:"초급 Velocity를 끝까지 올려야 해."}}')
        act.append(f'execute if score @s {obj} matches {n}.. run return run function bw:gui/no {{msg:"이미 전부 가지고 있어."}}')
        for have, (label, price) in enumerate(h['levels']):
            act.append(f'execute if score @s {obj} matches {have} run return run function bw:hack/buy/{k}{have}')
            P.fn(f'hack/buy/{k}{have}', [*gui.pay('coins', price), f'scoreboard players set @s {obj} {have + 1}', f'tag @s remove bw.off_{k}',
                                         tell('@s', t('[암시장] ', 'dark_purple'), t(h['name'] + (f' ({label})' if label else ''), 'gold'), t(' — 거래 끝. 들키지 마.', 'gray')),
                                         'playsound minecraft:entity.wandering_trader.yes master @s ~ ~ ~ 0.8 0.8', 'function bw:hack/apply'])
        G.act(gid, act)
        G.act(tg, [f'execute unless score @s {obj} matches 1.. run return 0',
                   f'execute store success score #ok bw run tag @s remove bw.off_{k}', f'execute if score #ok bw matches 0 run tag @s add bw.off_{k}',
                   'playsound minecraft:ui.button.click master @s ~ ~ ~ 0.5 1', 'function bw:hack/apply'])
    G.page('black', 1, slots)
    count = lambda tier: [f'scoreboard players set @s bw.hc{tier} 0'] + [f'execute if score @s bw.h_{h["key"]} matches 1.. run scoreboard players add @s bw.hc{tier} 1' for h in HACKS if h['tier'] == tier]
    init = [f'scoreboard players add @s bw.h_{h["key"]} 0' for h in HACKS]
    G.prepare('black', init + count(1) + count(2))

    # =================================================================== what the hacks do
    # ---- the ones that are only a number: reach, knockback, fall damage
    mod = lambda attr, mid, val, op='add_value': f'attribute @s minecraft:{attr} modifier add bw:{mid} {val} {op}'
    rm = lambda attr, mid: f'attribute @s minecraft:{attr} modifier remove bw:{mid}'
    apply = [rm('entity_interaction_range', 'reach'), rm('entity_interaction_range', 'lag'), rm('knockback_resistance', 'vel'), rm('fall_damage_multiplier', 'nofall'),
             *[f'execute if entity @s[scores={{bw.h_reach={lv}}},tag=!bw.off_reach] run ' + mod('entity_interaction_range', 'reach', v) for lv, v in ((1, 0.1), (2, 0.5), (3, 1.0))],
             *[f'execute if entity @s[scores={{bw.h_lag={lv}}},tag=!bw.off_lag] run ' + mod('entity_interaction_range', 'lag', v) for lv, v in ((1, 0.56), (2, 1.12))],
             *[f'execute if entity @s[scores={{bw.h_velocity={lv}}},tag=!bw.off_velocity] run ' + mod('knockback_resistance', 'vel', v) for lv, v in ((1, 0.2), (2, 0.45))],
             f'execute if entity @s[{ON("velocity2")}] run ' + rm('knockback_resistance', 'vel'), f'execute if entity @s[{ON("velocity2")}] run ' + mod('knockback_resistance', 'vel', 1.0),
             f'execute if entity @s[{ON("nofall")}] run ' + mod('fall_damage_multiplier', 'nofall', -1, 'add_multiplied_total'),
             # silent aim widens what the sword in the hand can hit; its reach has to carry the reach hacks itself
             'scoreboard players set #r bw 300',
             *[f'execute if entity @s[scores={{bw.h_reach={lv}}},tag=!bw.off_reach] run scoreboard players add #r bw {v}' for lv, v in ((1, 10), (2, 50), (3, 100))],
             *[f'execute if entity @s[scores={{bw.h_lag={lv}}},tag=!bw.off_lag] run scoreboard players add #r bw {v}' for lv, v in ((1, 56), (2, 112))],
             'execute store result storage bw:tmp aim.r float 0.01 run scoreboard players get #r bw',
             'execute store result score @s bw.hreach run scoreboard players get #r bw',
             *[f'scoreboard players add @s {o} 0' for o in ('bw.stc', 'bw.acd', 'bw.tpc', 'bw.ecd')]]
    P.fn('hack/apply', init + apply)
    load.append('scoreboard objectives add bw.hreach dummy')
    P.fn('hack/silent', ['$item modify entity @s weapon.mainhand {type:"minecraft:set_components",components:{"minecraft:attack_range":{max_reach:$(r),hitbox_margin:0.9}}}'])
    P.fn('hack/unsilent', ['item modify entity @s weapon.mainhand {type:"minecraft:set_components",components:{"!minecraft:attack_range":{}}}'])
    P.json('bw/tags/item/scaf.json', {'values': [f'minecraft:{d}_wool' for d in TEAMS] + [f'minecraft:{b}' for b in SCAF]})
    P.json('bw/predicate/jump.json', {'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:type_specific/player': {'input': {'jump': True}}}})
    P.json('bw/predicate/moving.json', {'type': 'minecraft:any_of', 'terms': [
        {'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:type_specific/player': {'input': {k: True}}}} for k in ('forward', 'backward', 'left', 'right')]})
    P.json('bw/predicate/sneak.json', {'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:type_specific/player': {'input': {'sneak': True}}}})

    tick = [f'execute as @a[tag=bw.fighter] at @s run function bw:hack/tick']
    ht = [*[f'scoreboard players remove @s[scores={{{o}=1..}}] {o} 1' for o in ('bw.stc', 'bw.acd', 'bw.tpc', 'bw.ecd')],
          # the sword in the hand: wide for silent aim, plain otherwise
          f'execute if entity @s[{ON("aim").replace("=1..", "=2")}] if items entity @s weapon.mainhand #bw:sharp[!minecraft:attack_range] run function bw:hack/silent with storage bw:tmp aim',
          f'execute unless entity @s[{ON("aim").replace("=1..", "=2")}] if items entity @s weapon.mainhand *[minecraft:attack_range] run function bw:hack/unsilent',
          f'execute if entity @s[{ON("aim").replace("=1..", "=1")}] if items entity @s weapon.mainhand #bw:sharp run function bw:hack/aim',
          f'execute if entity @s[{ON("clicker")}] if score @s bw.acd matches 0 if items entity @s weapon.mainhand #bw:sharp if entity {BOT},distance=..6] run function bw:hack/click',
          f'execute if entity @s[{ON("tpaura")}] if score @s bw.tpc matches 0 if items entity @s weapon.mainhand #minecraft:swords if entity {BOT},distance=..14] run function bw:hack/tpaura',
          f'execute if entity @s[{ON("antifb")}] as @e[type=minecraft:fireball,tag=bw.fb,tag=!bw.refl,distance=..4.5] unless score @s bw.team = @p bw.team run function bw:hack/reflect',
          f'execute if entity @s[{ON("eagle")}] if items entity @s weapon.mainhand #bw:placeable run function bw:hack/eagle',
          f'execute unless entity @s[{ON("eagle")}] run attribute @s minecraft:movement_speed modifier remove bw:eagle',
          f'execute if entity @s[{ON("scaffold")}] if items entity @s container.* #bw:scaf run function bw:hack/scaffold',
          f'execute if entity @s[{ON("tower")}] run function bw:hack/tower',
          'execute if entity @s[tag=bw.lev] unless predicate bw:jump run function bw:hack/towerend']
    P.fn('hack/tick', ht)
    # ---- Aim Assist (normal): the crosshair drifts towards an enemy that is nearly in it
    aim = ['tag @e[tag=bw.aimt] remove bw.aimt']
    for d in (2, 3, 4):
        aim.append(f'execute unless entity @e[tag=bw.aimt] anchored eyes positioned ^ ^ ^{d} positioned ~ ~-1.4 ~ as {BOT},distance=..1.9,sort=nearest,limit=1] run tag @s add bw.aimt')
        aim.append(f'execute anchored eyes positioned ^ ^ ^{d} positioned ~ ~-1.4 ~ if entity @e[tag=bw.aimt,distance=0.4..1.9] positioned ~ ~1.4 ~ anchored feet '
                   f'facing entity @e[tag=bw.aimt,limit=1] eyes positioned ^ ^ ^0.3 anchored eyes run function bw:hack/aimturn')
    P.fn('hack/aim', aim)
    P.fn('hack/aimturn', ['execute if entity @e[tag=bw.aimd] run return 0', 'rotate @s facing ~ ~ ~', 'tag @s add bw.aimd'])
    tick.append('tag @a[tag=bw.aimd] remove bw.aimd')
    # ---- a hit that the datapack makes for the player (AutoClicker, TP Aura): damage like a real swing, credit, and the bot fights back
    P.fn('hack/strike', [                                   # as the player; the victim carries bw.rayt
        'execute store result score #dmg bw run attribute @s minecraft:attack_damage get 100',
        *[f'execute if score @s bw.team matches {i} if score #sharp{i} bw matches 1.. run scoreboard players add #dmg bw 100' for i in range(8)],
        'execute store result storage bw:tmp hit.d float 0.01 run scoreboard players get #dmg bw', 'function bw:hack/strike2 with storage bw:tmp hit'])
    P.fn('hack/strike2', ['$damage @e[tag=bw.rayt,limit=1] $(d) minecraft:player_attack by @s', 'swing @s mainhand',
                          'scoreboard players operation #att bw = @s bw.team', 'tag @a remove bw.hitter', 'tag @s add bw.hitter', 'execute as @e[tag=bw.rayt,limit=1] at @s run function bw:hack/struck', 'tag @e[tag=bw.rayt] remove bw.rayt'])
    P.fn('hack/struck', ['scoreboard players operation @s bw.lh = #att bw', 'scoreboard players set @s bw.lht 200', 'scoreboard players set @s bw.ft 0', 'scoreboard players set @s bw.calm 0',
                         'execute unless score @s bw.st matches 3 run function bw:ai/engage', 'function bw:hack/displace'])
    # ---- AutoClicker: whoever is under the crosshair and in reach gets hit, as fast as hits count
    P.fn('hack/click', ['scoreboard players set @s bw.acd 2', 'scoreboard players set #rs bw 0', 'tag @e[tag=bw.rayt] remove bw.rayt',
                        'execute anchored eyes positioned ^ ^ ^0.4 run function bw:hack/ray', 'execute if entity @e[tag=bw.rayt] run function bw:hack/strike'])
    P.fn('hack/ray', ['execute unless block ~ ~ ~ #bw:open run return 0',
                      f'execute positioned ~-0.95 ~-0.95 ~-0.95 as {BOT},dx=0,dy=0,dz=0] positioned ~0.9 ~0.9 ~0.9 if entity @s[dx=0,dy=0,dz=0] run tag @s add bw.rayt',
                      'execute if entity @e[tag=bw.rayt] run return 1', 'scoreboard players add #rs bw 30',
                      'execute if score #rs bw < @s bw.hreach positioned ^ ^ ^0.3 run function bw:hack/ray'])
    # ---- TP Aura: appear behind the nearest enemy and hit
    P.fn('hack/tpaura', ['scoreboard players set @s bw.tpc 12', 'tag @e[tag=bw.rayt] remove bw.rayt', f'tag {BOT},distance=..14,sort=nearest,limit=1] add bw.rayt',
                         'particle minecraft:portal ~ ~1 ~ 0.3 0.6 0.3 0.4 30',
                         # behind it if there is room to stand there, else where it stands
                         'scoreboard players set #ok bw 0',
                         'execute at @e[tag=bw.rayt,limit=1] rotated as @e[tag=bw.rayt,limit=1] rotated ~ 0 positioned ^ ^ ^-1.6 if block ~ ~ ~ #bw:open if block ~ ~1 ~ #bw:open unless block ~ ~-1 ~ #bw:open '
                         'store success score #ok bw run tp @s ~ ~ ~ facing entity @e[tag=bw.rayt,limit=1] eyes',
                         'execute if score #ok bw matches 0 at @e[tag=bw.rayt,limit=1] run tp @s ~ ~ ~',
                         'execute at @s run playsound minecraft:entity.enderman.teleport player @a ~ ~ ~ 0.7 1.3', 'execute at @s run particle minecraft:portal ~ ~1 ~ 0.3 0.6 0.3 0.4 30',
                         'function bw:hack/strike'])
    # ---- Knockback Displace: where the enemy flies after my hit. Run as the bot that was just hit, with the hitter marked bw.hitter
    P.add('ai/hurt', ['tag @a remove bw.hitter', 'execute on attacker run tag @s[type=minecraft:player] add bw.hitter', 'execute if entity @a[tag=bw.hitter] run function bw:hack/displace'])
    P.fn('hack/displace', [
        f'execute unless entity @a[tag=bw.hitter,{ON("kbd")}] run return 0',
        'scoreboard players set #dir bw 0',
        # void: is there an edge within three blocks, in any of eight directions?
        *[f'execute if entity @a[tag=bw.hitter,scores={{bw.h_kbd=2}}] if score #dir bw matches 0 rotated {a} 0 if block ^ ^-1 ^{d} #bw:open if block ^ ^-2 ^{d} #bw:open if block ^ ^-4 ^{d} #bw:open '
          f'run function bw:hack/fling' for d in (1.5, 2.5, 3.5) for a in (0, 45, 90, 135, 180, 225, 270, 315)],
        # 90degree (and void with no edge near): sideways from the hitter
        'execute if score #dir bw matches 0 store result score #rn bw run random value 0..1',
        'execute if score #dir bw matches 0 if score #rn bw matches 0 facing entity @a[tag=bw.hitter,limit=1] feet rotated ~90 0 run function bw:hack/fling',
        'execute if score #dir bw matches 0 facing entity @a[tag=bw.hitter,limit=1] feet rotated ~-90 0 run function bw:hack/fling'])
    P.fn('hack/fling', ['scoreboard players set #dir bw 1', 'execute positioned 0.0 0.0 0.0 run tp @e[type=minecraft:marker,tag=bw.vec,limit=1] ^ ^0.72 ^1',
                        'data modify storage bw:tmp fl set from entity @e[type=minecraft:marker,tag=bw.vec,limit=1] Pos',
                        'execute store result storage bw:tmp fl[0] double 0.00055 run data get storage bw:tmp fl[0] 1000', 'execute store result storage bw:tmp fl[1] double 0.00055 run data get storage bw:tmp fl[1] 1000',
                        'execute store result storage bw:tmp fl[2] double 0.00055 run data get storage bw:tmp fl[2] 1000', 'data modify entity @s Motion set from storage bw:tmp fl',
                        'particle minecraft:sweep_attack ~ ~1 ~ 0 0 0 0 1'])
    # ---- AutoBlock: a bot's blow lands softer
    P.add('ai/soften', [f'execute if entity @s[type=minecraft:player,scores={{bw.h_block=1}},tag=!bw.off_block] run scoreboard players operation #dmg bw *= #75 bw',
                        f'execute if entity @s[type=minecraft:player,scores={{bw.h_block=2}},tag=!bw.off_block] run scoreboard players operation #dmg bw *= #50 bw',
                        f'execute if entity @s[type=minecraft:player,{ON("block")}] run scoreboard players operation #dmg bw /= #100 bw',
                        f'execute if entity @s[type=minecraft:player,{ON("block")}] at @s run playsound minecraft:item.shield.block player @a ~ ~ ~ 0.5 1.2'])
    # ---- Anti Fireball: sent back where the player is looking (as the fireball)
    P.fn('hack/reflect', ['tag @s add bw.refl', 'execute as @p at @s anchored eyes positioned 0.0 0.0 0.0 run tp @e[type=minecraft:marker,tag=bw.vec,limit=1] ^ ^ ^1.2',
                          'data modify entity @s Motion set from entity @e[type=minecraft:marker,tag=bw.vec,limit=1] Pos', 'data modify entity @s Owner set from entity @p UUID',
                          'scoreboard players operation @s bw.team = @p bw.team', 'execute on passengers run scoreboard players operation @s bw.team = @p bw.team',
                          'execute as @p run swing @s mainhand', 'playsound minecraft:entity.blaze.hurt player @a ~ ~ ~ 1 1.4', 'particle minecraft:crit ~ ~ ~ 0.3 0.3 0.3 0.3 12'])
    # ---- Eagle: with a block in the hand the player slows at an edge like someone sneaking, and is put back if they step past it
    P.fn('hack/eagle', ['attribute @s minecraft:movement_speed modifier remove bw:eagle',
                        'execute unless predicate bw:ground run return 0',
                        # a firm place: remember it
                        'execute unless block ~ ~-0.5 ~ #bw:open run tp @e[type=minecraft:marker,tag=bw.safe,limit=1] ~ ~ ~',
                        # past the edge (the block under the middle of the feet is gone): back to the last firm place
                        f'execute if block ~ ~-0.5 ~ #bw:open if entity @s[scores={{bw.h_eagle=2}}] run function bw:hack/eagleback',
                        f'execute if block ~ ~-0.5 ~ #bw:open if entity @s[scores={{bw.h_eagle=1}}] if score @s bw.ecd matches 0 run function bw:hack/eagleback',
                        # near an edge: slow, like sneaking
                        *[f'execute if entity @s[scores={{bw.h_eagle={lv}}}] unless block ~ ~-0.5 ~ #bw:open run function bw:hack/edge{lv}' for lv in (1, 2)]])
    for lv, dd in ((1, 0.5), (2, 0.6)):
        P.fn(f'hack/edge{lv}', [f'execute if block ~{dx} ~-0.5 ~{dz} #bw:open run return run attribute @s minecraft:movement_speed modifier add bw:eagle -0.7 add_multiplied_total'
                                for dx, dz in ((dd, 0), (-dd, 0), (0, dd), (0, -dd))])
    P.fn('hack/eagleback', ['scoreboard players set @s bw.ecd 2', 'execute if entity @e[type=minecraft:marker,tag=bw.safe,distance=..1.2] positioned as @e[type=minecraft:marker,tag=bw.safe,limit=1] run tp @s ~ ~ ~'])
    # ---- Scaffold: blocks from the pack appear under the feet
    P.fn('hack/scaffold', [
        'execute if predicate bw:ground run tp @e[type=minecraft:marker,tag=bw.safe2,limit=1] ~ ~ ~',
        'execute if predicate bw:ground positioned ~ ~-0.5 ~ if block ~ ~ ~ #bw:open align xyz run return run function bw:hack/putblock',
        # standing still and jumping: a tower, at the pace of a jump
        'execute unless predicate bw:ground if predicate bw:jump unless predicate bw:moving positioned ~ ~-1.01 ~ if block ~ ~ ~ #bw:open align xyz run return run function bw:hack/putblock',
        # Keep Y: jumping along, the blocks stay at the height the jump started from
        'execute unless predicate bw:ground if entity @s[scores={bw.h_scaffold=2}] if predicate bw:moving run function bw:hack/keepy'])
    P.fn('hack/keepy', ['execute store result storage bw:tmp ky.y double 0.01 run data get entity @e[type=minecraft:marker,tag=bw.safe2,limit=1] Pos[1] 100', 'function bw:hack/keepy2 with storage bw:tmp ky'])
    P.fn('hack/keepy2', ['$execute positioned ~ $(y) ~ positioned ~ ~-0.5 ~ if block ~ ~ ~ #bw:open align xyz run function bw:hack/putblock'])
    put = ['scoreboard players set #ok bw 0']
    put += [f'execute if score #ok bw matches 0 if score @s bw.team matches {i} store success score #ok bw run clear @s minecraft:{TEAMS[i]}_wool 1' for i in range(8)]
    put += [f'execute if score #ok bw matches 1 if score @s bw.team matches {i} run return run setblock ~ ~ ~ minecraft:{TEAMS[i]}_wool' for i in range(8)]
    for b in SCAF:
        put += [f'execute store success score #ok bw run clear @s minecraft:{b} 1', f'execute if score #ok bw matches 1 run return run setblock ~ ~ ~ minecraft:{b}']
    P.fn('hack/putblock', put)
    # ---- Tower: hold jump on the spot and rise on a column, faster than jumping
    P.fn('hack/tower', ['execute unless predicate bw:jump run return 0', 'execute if predicate bw:moving run return 0', 'execute unless items entity @s container.* #bw:scaf run return 0',
                        'execute if entity @s[scores={bw.h_tower=1}] run effect give @s minecraft:levitation 1 2 true',
                        'execute if entity @s[scores={bw.h_tower=2}] run effect give @s minecraft:levitation 1 5 true', 'tag @s add bw.lev',
                        'execute positioned ~ ~-1.01 ~ if block ~ ~ ~ #bw:open align xyz run function bw:hack/putblock'])
    P.fn('hack/towerend', ['tag @s remove bw.lev', 'effect clear @s minecraft:levitation'])
    # ---- Stasis: falling into the void, the player hangs in the air for three seconds (per map: it needs the height of the void)
    for m in maps:
        P.add(f'm/{m["id"]}/tick', [f'execute as @a[tag=bw.fighter,scores={{bw.h_stasis=1..,bw.stc=0}},tag=!bw.off_stasis] at @s if entity @s[y={m["void_y"] + 1},dy=7] unless predicate bw:ground run function bw:hack/stasis'])
    P.fn('hack/stasis', ['scoreboard players set @s bw.stc 600', 'effect give @s minecraft:levitation 3 0 true', 'effect give @s minecraft:slow_falling 6 0 true',
                         'title @s actionbar ' + snbt(t('Stasis!', 'light_purple', bold=True)), 'playsound minecraft:block.beacon.activate player @s ~ ~ ~ 1 1.6',
                         'particle minecraft:end_rod ~ ~0.5 ~ 0.4 0.6 0.4 0.02 25'])
    # ---- FB Longjump: a fireball used looking at one's feet throws the player far, and does not hurt
    base = lambda effects: {'description': {'text': ''}, 'supported_items': '#minecraft:enchantable/durability', 'weight': 1, 'max_level': 1,
                            'min_cost': {'base': 1, 'per_level_above_first': 0}, 'max_cost': {'base': 1, 'per_level_above_first': 0}, 'anvil_cost': 1, 'slots': ['head'], 'effects': effects}
    P.json('bw/enchantment/push.json', base({'minecraft:tick': [{'effect': {'type': 'minecraft:explode', 'block_interaction': 'none', 'knockback_multiplier': 2.3, 'radius': 3.0,
           'small_particle': {'type': 'minecraft:explosion'}, 'large_particle': {'type': 'minecraft:explosion_emitter'}, 'sound': 'minecraft:entity.generic.explode'}}]}))
    P.fn('hack/fbjump', ['clear @s *[minecraft:custom_data~{bw:"fireball"}] 1',
                         'execute rotated ~ 0 positioned ^ ^1.3 ^-1.0 run summon minecraft:armor_stand ~ ~ ~ {Marker:1b,Invisible:1b,NoGravity:1b,Tags:["bw","bw.round","bw.boom"],'
                         'equipment:{head:{id:"minecraft:leather_helmet",count:1,components:{"minecraft:enchantments":{"bw:push":1}}}}}',
                         'title @s actionbar ' + snbt(t('FB Longjump', 'gold', bold=True)), 'return 1'])
    P.fn('fb/pre', [f'execute if entity @s[{ON("fbjump")},x_rotation=45..90] run return run function bw:hack/fbjump', 'return 0'])
    P.add('game/kit', ['function bw:hack/apply'])
    P.add('lobby/init', ['function bw:hack/apply'])
    P.add('game/begin', ['summon minecraft:marker 0 0 0 {Tags:["bw","bw.round","bw.safe"]}', 'summon minecraft:marker 0 0 0 {Tags:["bw","bw.round","bw.safe2"]}'])
    load += ['scoreboard players set #75 bw 75', 'scoreboard players set #50 bw 50']
    return dict(load=load, tick=tick)

def npcs(P, maps):
    """the dealer in the cellar, and the stranger on every map who knows where the cellar is"""
    adv = lambda tag, fn: {'criteria': {'click': {'trigger': 'minecraft:player_interacted_with_entity', 'conditions': {'entity': {
        'type': 'minecraft:entity_properties', 'entity': 'this', 'predicate': {'minecraft:entity_type': 'minecraft:villager', 'minecraft:entity_tags': {'all_of': [tag]}}}}}},
        'rewards': {'function': fn}}
    P.json('bw/advancement/npc/black.json', adv('bw.npc.black', 'bw:npc/black'))
    say = lambda who, msg, col='white': tell('@s', t(f'[{who}] ', 'dark_purple'), t(msg, col))
    P.fn('npc/black', ['advancement revoke @s only bw:npc/black', 'playsound minecraft:entity.wandering_trader.ambient master @s ~ ~ ~ 0.8 0.7',
                       'execute unless score @s bw.stage matches 3.. run return run ' + say('???', '…꼬마는 돌아가. 3단계는 돼야 내 물건을 쓸 수 있어.', 'gray'),
                       say('???', '앞의 상자를 열어 봐. 싸진 않아. 그리고 여기서 본 건 비밀이야.')])
    P.json('bw/advancement/npc/hint.json', adv('bw.npc.hint', 'bw:npc/hint'))
    hints = {'tea': ['로비에 있는 거대한 침대 알지?', '어릴 때 침대 밑에 뭐가 산다고들 했잖아…'],
             'chess': ['큰 물건 아래는 늘 어둡지.', '로비에서 제일 큰 물건 아래를 들여다본 적 있어?'],
             'circus': ['사다리는 위로만 가는 게 아니야.', '잔디밭에 구멍이 하나 있더라고. 그늘진 데에.'],
             'library': ['그 사람은 실력 없는 손님은 안 받아.', '3단계는 돼야 물건을 보여 줄걸.'],
             'solar': ['거기 갈 땐 코인을 넉넉히 챙겨.', '정정당당한 물건을 파는 데가 아니거든.']}
    P.fn('npc/hint', ['advancement revoke @s only bw:npc/hint', 'playsound minecraft:entity.wandering_trader.ambient master @s ~ ~ ~ 0.8 1.2',
                      *[f"execute if score #map bw matches {n + 1} run function bw:npc/hint_{m['id']}" for n, m in enumerate(maps)]])
    for m in maps:
        a, b = hints[m['id']]
        P.fn(f"npc/hint_{m['id']}", [tell('@s', t('[수상한 떠돌이] ', 'yellow'), t(a, 'white')), tell('@s', t('[수상한 떠돌이] ', 'yellow'), t(b, 'white'))])
