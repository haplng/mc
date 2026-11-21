"""Shop windows the Hypixel way: a six-row chest full of items, and clicking an item buys it.
The window is a real double chest that stands as the counter in front of each keeper. Its items are only pictures: each carries an id,
and the moment one leaves the chest (picked up, shift-clicked, thrown, moved with a number key) it is taken away again, the purchase
that belongs to the id is made, and the chest is painted anew. Whatever a player puts into the chest is handed straight back."""
import os, json
from util import TEAMS, TEAM_KO, TEAM_COLOR, snbt, t, line, tell, q
import items

HID = ('tooltip_display={hidden_components:["minecraft:attribute_modifiers","minecraft:enchantments","minecraft:potion_contents","minecraft:unbreakable",'
       '"minecraft:dyed_color","minecraft:can_break","minecraft:can_place_on"]}')
TITLE = {'shop': '아이템 상점', 'team': '팀 업그레이드', 'unlock': '해금 (코인)', 'black': '암시장'}
SUBJ = {'fe': '철이', 'au': '금이', 'em': '에메랄드가', 'di': '다이아몬드가', 'coins': '코인이'}
CURN = {'fe': ('철', 'white'), 'au': ('금', 'gold'), 'em': ('에메랄드', 'dark_green'), 'di': ('다이아몬드', 'aqua'), 'coins': ('코인', 'gold')}
CURI = {'fe': 'minecraft:iron_ingot', 'au': 'minecraft:gold_ingot', 'em': 'minecraft:emerald', 'di': 'minecraft:diamond'}

def ln(*parts, color='gray'):
    """one line of an item's description"""
    return [{'text': '', 'italic': False, 'color': color}] + [p if isinstance(p, dict) else {'text': p} for p in parts]

def icon(item, gid, name, color, lines, n=1, extra='', glint=False):
    comps = [f'custom_data={{bwgui:{{id:{gid}}}}}', 'item_name=' + snbt({'text': name, 'color': color}), 'lore=' + snbt(lines), HID]
    if glint: comps.append('enchantment_glint_override=true')
    if extra: comps.append(extra)
    return f'minecraft:{item}[{",".join(comps)}] {n}'

def cost_line(c, cur): return ln('가격: ', {'text': f'{c} {CURN[cur][0]}', 'color': CURN[cur][1]})
BUY = ln({'text': '클릭해서 구매!', 'color': 'yellow'})
def short(cur): return ln({'text': f'{SUBJ[cur]} 부족해!', 'color': 'red'})

class Gui:
    def __init__(self, P):
        self.P = P; self.kinds = {}; self.acts = {}; self.load = []; self.before = {}
    def page(self, kind, p, slots):
        """slots: {0..53: [(condition, item), ...]}; a condition is an 'execute' fragment tested for the player (@s) who is looking"""
        self.kinds.setdefault(kind, {})[p] = slots
    def act(self, gid, lines):
        assert gid not in self.acts, gid
        self.acts[gid] = lines
    def prepare(self, kind, lines):
        """commands run (as the player) before a window of this kind is painted"""
        self.before[kind] = lines

    def finish(self):
        P = self.P
        for kind, pages in self.kinds.items():
            for p, slots in pages.items():
                for half, base in (('a', 0), ('b', 27)):
                    out = []
                    for c in range(27):
                        vs = slots.get(base + c)
                        if not vs: out.append(f'item replace block ~ ~ ~ container.{c} with minecraft:air'); continue
                        for cond, item in vs:
                            out.append((f'execute {cond} run ' if cond else '') + f'item replace block ~ ~ ~ container.{c} with {item}')
                    P.fn(f'gui/{kind}/p{p}{half}', out)
            P.fn(f'gui/{kind}/a', [f'execute if score #page bw matches {p} run function bw:gui/{kind}/p{p}a' for p in pages])
            P.fn(f'gui/{kind}/b', [f'execute if score #page bw matches {p} run function bw:gui/{kind}/p{p}b' for p in pages])
            # as the player, standing at the half of the chest that holds the top three rows
            P.fn(f'gui/{kind}/paint', [
                'scoreboard players operation #page bw = @e[type=minecraft:marker,tag=bw.gui.a,distance=..0.6,limit=1] bw.page',
                f'execute unless score #page bw matches 1..{max(pages)} run scoreboard players set #page bw 1',
                *self.before.get(kind, []),
                f'function bw:gui/{kind}/a',
                f'execute positioned as @e[type=minecraft:marker,tag=bw.gui.b,tag=bw.gui.{kind},distance=..1.6,sort=nearest,limit=1] run function bw:gui/{kind}/b'])
        slots36 = [f'container.{k}' for k in range(36)]
        tmp = '@e[type=minecraft:armor_stand,tag=bw.tmp,limit=1]'
        any_gui = '*[minecraft:custom_data~{bwgui:{}}]'
        P.fn('gui/near', [
            # a click: one of the pictures is on the cursor or in the pack
            f'execute if items entity @s player.cursor {any_gui} run return run function bw:gui/click',
            f'execute if items entity @s container.* {any_gui} run return run function bw:gui/click',
            f'execute if items entity @s weapon.offhand {any_gui} run return run function bw:gui/click',
            # whatever was put into the chest comes back out
            'execute as @e[type=minecraft:marker,tag=bw.gui,distance=..8] at @s if items block ~ ~ ~ container.* *[!minecraft:custom_data~{bwgui:{}}] run function bw:gui/eject',
            f'execute as @e[type=minecraft:item,distance=..10] if items entity @s contents {any_gui} run kill @s',
            # painted twice a second, so prices turn green as the money comes in
            'scoreboard players add @s bw.gt 1', 'execute if score @s bw.gt matches 10.. run function bw:gui/refresh'])
        P.fn('gui/click', [
            f'item replace entity {tmp} weapon.mainhand with minecraft:air',
            f'execute if items entity @s player.cursor {any_gui} run item replace entity {tmp} weapon.mainhand from entity @s player.cursor',
            f'execute if items entity @s weapon.offhand {any_gui} run item replace entity {tmp} weapon.mainhand from entity @s weapon.offhand',
            *[f'execute if items entity @s {s} {any_gui} run item replace entity {tmp} weapon.mainhand from entity @s {s}' for s in slots36],
            'scoreboard players set @s bw.click 0',
            f'execute store result score @s bw.click run data get entity {tmp} equipment.mainhand.components."minecraft:custom_data".bwgui.id',
            f'clear @s {any_gui}',
            'function bw:gui/money',
            'function bw:gui/do',
            'function bw:gui/refresh'])
        P.fn('gui/do', [f'execute if score @s bw.click matches {gid} run return run function bw:gui/act/{gid}' for gid in sorted(self.acts)])
        for gid, lines in self.acts.items(): P.fn(f'gui/act/{gid}', lines)
        P.fn('gui/money', [*[f'execute store result score @s bw.{k} run clear @s {v} 0' for k, v in CURI.items()]])
        P.fn('gui/refresh', ['scoreboard players set @s bw.gt 0', 'function bw:gui/money',
                             *[f'execute at @e[type=minecraft:marker,tag=bw.gui.a,tag=bw.gui.{kind},distance=..8] run function bw:gui/{kind}/paint' for kind in self.kinds]])
        P.fn('gui/eject', [f'execute if items block ~ ~ ~ container.{c} *[!minecraft:custom_data~{{bwgui:{{}}}}] run function bw:gui/eject1 {{n:{c}}}' for c in range(27)])
        P.fn('gui/eject1', ['summon minecraft:item ~ ~1 ~ {Item:{id:"minecraft:stone",count:1},PickupDelay:0s,Tags:["bw","bw.ej"]}',
                            '$item replace entity @e[type=minecraft:item,tag=bw.ej,distance=..2,limit=1] contents from block ~ ~ ~ container.$(n)',
                            '$item replace block ~ ~ ~ container.$(n) with minecraft:air', 'tag @e[type=minecraft:item,tag=bw.ej] remove bw.ej'])
        # a new chest: which half is it, what is it called
        P.fn('gui/init', ['execute if block ~ ~ ~ minecraft:waxed_copper_chest[type=right] run tag @s add bw.gui.a',
                          'execute unless entity @s[tag=bw.gui.a] run tag @s add bw.gui.b', 'scoreboard players set @s bw.page 1',
                          *[f'execute if entity @s[tag=bw.gui.{k}] run data modify block ~ ~ ~ CustomName set value {snbt({"text": v})}' for k, v in TITLE.items()]])
        P.fn('gui/no', ['$tellraw @s {text:"$(msg)",color:"red"}', 'playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 0.5 0.6'])
        for cur in SUBJ:
            P.fn(f'gui/short/{cur}', ['$scoreboard players set #need bw $(need)', f'scoreboard players operation #need bw -= @s bw.{cur}',
                                      tell('@s', t(f'{SUBJ[cur]} 부족해! ', 'red'), {'score': {'name': '#need', 'objective': 'bw'}, 'color': 'red'}, t('개 더 필요해!', 'red')),
                                      'playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 0.5 0.6'])
        P.fn('gui/ok', ['$tellraw @s [{text:"구매: ",color:"green"},{text:"$(name)",color:"gold"}]', 'playsound minecraft:block.note_block.pling master @s ~ ~ ~ 0.8 2'])
        P.fn('gui/tab', ['$scoreboard players set @e[type=minecraft:marker,tag=bw.gui.a,tag=bw.gui.$(kind),distance=..8,sort=nearest,limit=1] bw.page $(p)',
                         'playsound minecraft:ui.button.click master @s ~ ~ ~ 0.4 1'])
        P.fn('gui/nop', [])
        load = [*[f'scoreboard objectives add {o} dummy' for o in ('bw.page', 'bw.click', 'bw.gt', 'bw.fe', 'bw.au', 'bw.em', 'bw.di')], *self.load]
        tick = ['execute as @a[gamemode=!spectator] at @s if entity @e[type=minecraft:marker,tag=bw.gui,distance=..8,limit=1] run function bw:gui/near',
                'execute if score #lt bw matches 5 as @e[type=minecraft:marker,tag=bw.gui,tag=!bw.gui.a,tag=!bw.gui.b] at @s run function bw:gui/init']
        return dict(load=load, tick=tick)

GRID = [19, 20, 21, 22, 23, 24, 25, 28, 29, 30, 31, 32, 33, 34, 37, 38, 39, 40, 41, 42, 43]       # where the goods lie, like Hypixel's shop
PANE = lambda col: f'minecraft:{col}_stained_glass_pane[custom_data={{bwgui:{{id:150}}}},item_name={snbt({"text": "⬆ 종류   ⬇ 물건", "color": "dark_gray"})},{HID}] 1'

def tabs(slots, kind, base, names, cur):
    """the top row (categories) and the row of panes under it; the pane under the open category is green"""
    for j, (name, ic) in enumerate(names):
        slots[j] = [('', icon(ic, base + j + 1, name, 'green', [ln({'text': '클릭해서 보기!', 'color': 'yellow'})]))]
    for j in range(9): slots[9 + j] = [('', PANE('lime' if j == cur else 'gray'))]

def shop_variants(d, lock=True):
    """the pictures of one shop item: locked, affordable, too expensive (and 'already have' for armour and shears)"""
    key = d['key']; kind = d['give'][0]; U = f'if entity @s[tag=bw.u.{key}]'; NU = f'unless entity @s[tag=bw.u.{key}]'
    out = [(NU, icon('gray_dye', d['id'], d['name'], 'red', [ln({'text': '✘ 잠김', 'color': 'red'}), ln(''), ln('로비의 업그레이드 가게에서'), ln({'text': f'{d["unlock"]} 코인', 'color': 'gold'}, '으로 해금할 수 있어.')]))]
    def pic(item, name, color, cost, cur, desc, foot, n=1):
        return icon(item, d['id'], name, color, [cost_line(cost, cur), ln(''), *[ln(x) for x in desc], ln(''), foot], n=n, extra=d.get('icon_extra', ''), glint=d.get('glint', False))
    if kind == 'tool':
        obj = 'bw.' + d['give'][1]; tiers = items.TIERS[d['give'][1]]
        for k, tr in enumerate(tiers):
            have = f'{U} if score @s {obj} matches {k}'
            desc = [tr[1], '죽으면 한 단계 내려가.'] + ([f'지금: {tiers[k - 1][0]}'] if k else [])
            out += [(f'{have} if score @s bw.{tr[5]} matches {tr[4]}..', pic(tr[2], tr[0], 'green', tr[4], tr[5], desc, BUY)),
                    (f'{have} unless score @s bw.{tr[5]} matches {tr[4]}..', pic(tr[2], tr[0], 'red', tr[4], tr[5], desc, short(tr[5])))]
        last = tiers[-1]
        out.append((f'{U} if score @s {obj} matches {len(tiers)}..', icon(last[2], d['id'], last[0], 'green', [ln(last[1]), ln(''), ln({'text': '최고 단계야!', 'color': 'green'})])))
        return out
    own = None
    if kind == 'armor': own = f'score @s bw.armor matches {d["give"][1]}..'
    if kind == 'shears': own = 'score @s bw.shears matches 1..'
    can = f'{U} unless {own} ' if own else U + ' '
    if own: out.append((f'{U} if {own}', pic(d['icon'], d['name'], 'green', d['cost'], d['cur'], d['desc'], ln({'text': '이미 가지고 있어.', 'color': 'green'}))))
    out += [(f'{can}if score @s bw.{d["cur"]} matches {d["cost"]}..', pic(d['icon'], d['name'], 'green', d['cost'], d['cur'], d['desc'], BUY, d['n'])),
            (f'{can}unless score @s bw.{d["cur"]} matches {d["cost"]}..', pic(d['icon'], d['name'], 'red', d['cost'], d['cur'], d['desc'], short(d['cur']), d['n']))]
    return out

def pay(cur, cost):
    """refuse when short, otherwise take the money (run inside an act function; ends the function on refusal)"""
    return [f'execute unless score @s bw.{cur} matches {cost}.. run return run function bw:gui/short/{cur} {{need:{cost}}}',
            f'clear @s {CURI[cur]} {cost}' if cur in CURI else f'scoreboard players remove @s bw.{cur} {cost}']

def write(P, maps=()):
    """maps: dicts with id, name, size (text), price (coins), bonus (percent) - they are unlocked in the lobby too"""
    G = Gui(P)
    # =================================================================== the item shop
    names = [(pg[0], pg[1]) for pg in items.PAGES]
    for p, (pname, picon, keys) in enumerate(items.PAGES, 1):
        slots = {}; tabs(slots, 'shop', 100, names, p - 1)
        for k, key in enumerate(keys): slots[GRID[k]] = shop_variants(items.BY[key])
        G.page('shop', p, slots)
        G.act(100 + p, [f'function bw:gui/tab {{kind:"shop",p:{p}}}'])
    G.act(150, [])
    for d in items.ITEMS:
        kind = d['give'][0]; key = d['key']
        head = [f'execute unless entity @s[tag=bw.u.{key}] run return run function bw:gui/no {{msg:"아직 잠겨 있어. 로비의 업그레이드 가게에서 해금해."}}',
                'execute unless entity @s[tag=bw.fighter] run return run function bw:gui/no {msg:"게임 중에만 살 수 있어."}']
        ok = f'function bw:gui/ok {{name:{q(d["name"])}}}'
        if kind == 'dyed':
            G.act(d['id'], head + pay(d['cur'], d['cost']) + [f'execute if score @s bw.team matches {i} run give @s {items.it(TEAMS[i] + d["give"][1], items.BLOCK)} {d["n"]}' for i in range(8)] + [ok])
        elif kind == 'give':
            G.act(d['id'], head + pay(d['cur'], d['cost']) + [f'give @s {d["give"][1]} {d["n"]}', ok])
        elif kind == 'sword':
            G.act(d['id'], head + pay(d['cur'], d['cost']) + ['clear @s minecraft:wooden_sword', f'give @s {items.sword(d["give"][1])}', 'function bw:game/enchant', ok])
        elif kind == 'armor':
            G.act(d['id'], head + [f'execute if score @s bw.armor matches {d["give"][1]}.. run return run function bw:gui/no {{msg:"이미 같거나 더 좋은 갑옷이 있어."}}'] + pay(d['cur'], d['cost']) +
                  [f'scoreboard players set @s bw.armor {d["give"][1]}', 'function bw:game/kit', ok])
        elif kind == 'shears':
            G.act(d['id'], head + ['execute if score @s bw.shears matches 1.. run return run function bw:gui/no {msg:"가위는 이미 있어."}'] + pay(d['cur'], d['cost']) +
                  ['scoreboard players set @s bw.shears 1', 'function bw:game/tools', ok])
        elif kind == 'tool':
            obj = 'bw.' + d['give'][1]; tiers = items.TIERS[d['give'][1]]
            G.act(d['id'], head + [f'execute if score @s {obj} matches {len(tiers)}.. run return run function bw:gui/no {{msg:"이미 최고 단계야."}}'] +
                  [f'execute if score @s {obj} matches {k} run return run function bw:gui/tool/{d["give"][1]}{k}' for k in range(len(tiers))])
            for k, tr in enumerate(tiers):
                P.fn(f'gui/tool/{d["give"][1]}{k}', pay(tr[5], tr[4]) + [f'scoreboard players set @s {obj} {k + 1}', 'function bw:game/tools', f'function bw:gui/ok {{name:{q(tr[0])}}}'])

    # =================================================================== team upgrades (diamonds)
    UPS = items.UPGRADES
    SLOT = {'sharp': 10, 'prot': 11, 'haste': 12, 'forge': 19, 'heal': 20, 'trap': 14}
    val = {'sharp': 'sharp', 'prot': 'prot', 'haste': 'haste', 'forge': 'fl', 'heal': 'heal', 'trap': 'trap'}
    P.fn('gui/teamvals', [f'$scoreboard players operation @s bw.v{k} = #{v}$(i) bw' for k, v in val.items()])
    G.prepare('team', ['execute store result storage bw:tmp me.i int 1 run scoreboard players get @s bw.team', 'function bw:gui/teamvals with storage bw:tmp me'])
    G.load += [f'scoreboard objectives add bw.v{k} dummy' for k in val]
    slots = {}
    for j in range(9): slots[27 + j] = [('', PANE('gray'))]
    slots[4] = [('', icon('diamond', 150, '팀 업그레이드', 'aqua', [ln('다이아몬드로 사는'), ln('팀 전체의 강화야.')]))]
    for d in UPS:
        key = d['key']; U = f'if entity @s[tag=bw.u.up_{key}]'; NU = f'unless entity @s[tag=bw.u.up_{key}]'; n = len(d['costs'])
        vs = [(NU, icon('gray_dye', d['id'], d['name'], 'red', [ln({'text': '✘ 잠김', 'color': 'red'}), ln(''), ln('로비의 업그레이드 가게에서'), ln({'text': f'{d["unlock"]} 코인', 'color': 'gold'}, '으로 해금할 수 있어.')]))]
        def tier_lines(lv):
            if n == 1: return []
            out = []
            for k, c in enumerate(d['costs']):
                label = d['levels'][k] if d.get('levels') else f'{items_roman(k)}단계'
                out.append(ln({'text': f'{label}, ', 'color': 'green' if k < lv else 'gray'}, {'text': f'{c} 다이아몬드', 'color': 'aqua'}))
            return out + [ln('')]
        for lv in range(n + 1):
            have = f'{U} if score @s bw.v{key} matches {lv}'
            title = d['name'] + (f' {items_roman(lv)}' if n > 1 and lv < n else '')
            body = [*[ln(x) for x in d['desc']], ln(''), *tier_lines(lv)]
            if lv == n:
                vs.append((have, icon(d['icon'], d['id'], d['name'], 'green', body + [ln({'text': '이미 다 샀어!' if key != 'trap' else '함정이 준비됐어.', 'color': 'green'})], glint=True)))
                continue
            c = d['costs'][lv]
            vs += [(f'{have} if score @s bw.di matches {c}..', icon(d['icon'], d['id'], title, 'green', [cost_line(c, 'di'), ln('')] + body + [BUY])),
                   (f'{have} unless score @s bw.di matches {c}..', icon(d['icon'], d['id'], title, 'red', [cost_line(c, 'di'), ln('')] + body + [short('di')]))]
        slots[SLOT[key]] = vs
    G.page('team', 1, slots)
    for d in UPS:
        key = d['key']; v = val[key]; n = len(d['costs'])
        G.act(d['id'], [f'execute unless entity @s[tag=bw.u.up_{key}] run return run function bw:gui/no {{msg:"아직 잠겨 있어. 로비의 업그레이드 가게에서 해금해."}}',
                        'execute unless entity @s[tag=bw.fighter] run return run function bw:gui/no {msg:"게임 중에만 살 수 있어."}',
                        'execute store result storage bw:tmp me.i int 1 run scoreboard players get @s bw.team',
                        f'function bw:gui/up/{key} with storage bw:tmp me'])
        body = [f'$execute if score #{v}$(i) bw matches {n}.. run return run function bw:gui/no {{msg:"이미 다 샀어."}}']
        for lv, c in enumerate(d['costs']):
            body += [f'$execute if score #{v}$(i) bw matches {lv} unless score @s bw.di matches {c}.. run return run function bw:gui/short/di {{need:{c}}}',
                     f'$execute if score #{v}$(i) bw matches {lv} run return run function bw:gui/up/{key}{lv} {{i:$(i)}}']
            label = d['levels'][lv].split(' (')[0] if d.get('levels') else d['name'] + (f' {items_roman(lv)}' if n > 1 else '')
            eff = {'sharp': ['$execute as @a[tag=bw.fighter,scores={bw.team=$(i)}] run function bw:game/enchant'],
                   'prot': ['$execute as @a[tag=bw.fighter,scores={bw.team=$(i)}] run function bw:game/enchant'],
                   'forge': [f'$scoreboard players set #fs$(i) bw {[150, 200, 200, 300][lv]}'], 'haste': [], 'heal': [], 'trap': []}[key]
            P.fn(f'gui/up/{key}{lv}', [f'clear @s minecraft:diamond {c}', f'$scoreboard players set #{v}$(i) bw {lv + 1}', *eff,
                                       '$tellraw @a[tag=bw.play,scores={bw.team=$(i)}] [{selector:"@s"},{text:"이(가) ",color:"green"},{text:' + q(label) + ',color:"gold"},{text:"을(를) 구매했어!",color:"green"}]',
                                       'playsound minecraft:block.note_block.pling master @s ~ ~ ~ 0.8 2'])
        P.fn(f'gui/up/{key}', body)

    # =================================================================== unlocking (coins, in the lobby)
    un = names + [('팀 업그레이드', 'diamond')]
    def unlock_variants(gid, ic, name, tag, price, desc, extra='', n=1):
        got = f'if entity @s[tag={tag}]'; no = f'unless entity @s[tag={tag}]'
        body = [*[ln(x) for x in desc], ln('')]
        return [(got, icon(ic, gid, name, 'green', body + [ln({'text': '✔ 해금 완료', 'color': 'green'})], n=n, extra=extra)),
                (f'{no} if score @s bw.coins matches {price}..', icon(ic, gid, name, 'yellow', [cost_line(price, 'coins'), ln('')] + body + [ln({'text': '클릭해서 해금!', 'color': 'yellow'})], n=n, extra=extra)),
                (f'{no} unless score @s bw.coins matches {price}..', icon(ic, gid, name, 'red', [cost_line(price, 'coins'), ln('')] + body + [short('coins')], n=n, extra=extra))]
    def unlock_act(gid, tag, price, name):
        G.act(gid, [f'execute if entity @s[tag={tag}] run return run function bw:gui/no {{msg:"이미 해금했어."}}',
                    *pay('coins', price), f'tag @s add {tag}',
                    tell('@s', t('해금: ', 'green'), t(name, 'gold'), t('  (남은 코인 ', 'gray'), {'score': {'name': '@s', 'objective': 'bw.coins'}, 'color': 'gold'}, t(')', 'gray')),
                    'playsound minecraft:entity.player.levelup master @s ~ ~ ~ 0.8 1.4'])
    for p in range(1, len(un) + 1):
        slots = {}; tabs(slots, 'unlock', 300, un, p - 1)
        slots[45] = [('', icon('gold_nugget', 150, '코인', 'gold', [ln('가진 코인은 화면 오른쪽에 보여.'), ln(''), ln('게임에서 처치·침대 파괴·승리로 벌어.'), ln('한 번 해금하면 계속 살 수 있어.')]))]
        # the bottom row, on every page: the maps
        for k, m in enumerate(maps):
            desc = [f'크기 {m["size"]}', '8팀'] + ([f'코인 보너스 +{m["bonus"] - 100}%'] if m['bonus'] > 100 else ['처음부터 열려 있는 맵'])
            slots[47 + k] = unlock_variants(1300 + k, m['icon'], '맵: ' + m['name'], f'bw.m.{m["id"]}', m['price'], desc)
        if p <= len(items.PAGES):
            for k, key in enumerate(items.PAGES[p - 1][2]):
                d = items.BY[key]
                slots[GRID[k]] = unlock_variants(1000 + d['id'], d['icon'], d['name'], f'bw.u.{key}', d['unlock'], d['desc'], d.get('icon_extra', ''), d['n'])
        else:
            for k, d in enumerate(UPS):
                slots[GRID[k]] = unlock_variants(1000 + d['id'], d['icon'], d['name'], f'bw.u.up_{d["key"]}', d['unlock'], d['desc'] + ['(게임 중 다이아몬드로 구매)'])
        G.page('unlock', p, slots)
        G.act(300 + p, [f'function bw:gui/tab {{kind:"unlock",p:{p}}}'])
    for d in items.ITEMS: unlock_act(1000 + d['id'], f'bw.u.{d["key"]}', d['unlock'], d['name'])
    for d in UPS: unlock_act(1000 + d['id'], f'bw.u.up_{d["key"]}', d['unlock'], d['name'])
    for k, m in enumerate(maps): unlock_act(1300 + k, f'bw.m.{m["id"]}', m['price'], '맵 ' + m['name'])
    # the coin counter in a lore line is resolved when the chest is painted, for whoever is looking
    return G

def items_roman(k): return ['I', 'II', 'III', 'IV', 'V'][k]

def npc_hints(P, root):
    """a click on a keeper itself: say where to click"""
    msgs = {'shop': ('bw.npc.shop', '내 앞의 상자를 우클릭해. 그게 상점이야.'), 'team': ('bw.npc.upgrade', '내 앞의 상자를 우클릭해. 다이아몬드로 팀을 강화해.'),
            'unlock': ('bw.npc.unlock', '내 앞의 상자를 우클릭해. 코인으로 상점 물건을 해금해.')}
    for kind, (tag, msg) in msgs.items():
        P.json(f'bw/advancement/npc/{kind}.json', {'criteria': {'click': {'trigger': 'minecraft:player_interacted_with_entity',
               'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                         'predicate': {'minecraft:entity_type': 'minecraft:villager', 'minecraft:entity_tags': {'all_of': [tag]}}}}}},
               'rewards': {'function': f'bw:npc/{kind}'}})
        P.fn(f'npc/{kind}', [f'advancement revoke @s only bw:npc/{kind}', tell('@s', t('[상인] ', 'aqua'), t(msg, 'white')), 'playsound minecraft:entity.villager.ambient master @s ~ ~ ~ 0.7 1'])
