"""The item shop. Right-clicking a shopkeeper opens a dialog with the Bed Wars categories; clicking an item pays for it with
iron / gold / emeralds from the inventory. The dialogs are written out by functions with macros, so every time one is shown it
knows what the player can afford (green / red), which tool tier comes next, and what the last purchase was."""
import json, os

# ------------------------------------------------------------------ SNBT
class Raw(str):
    """text that goes into the SNBT unquoted (a macro variable holding a whole compound)"""

def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def snbt(o):
    if isinstance(o, Raw): return str(o)
    if isinstance(o, bool): return 'true' if o else 'false'
    if isinstance(o, int): return str(o)
    if isinstance(o, str): return q(o)
    if isinstance(o, (list, tuple)): return '[' + ','.join(snbt(v) for v in o) + ']'
    if isinstance(o, dict):
        key = lambda k: k if all(c.isalnum() or c in '._+-' for c in k) else q(k)
        return '{' + ','.join(f'{key(k)}:{snbt(v)}' for k, v in o.items()) + '}'
    raise TypeError(repr(o))

def t(text, color=None, **kw):
    d = {'text': text}
    if color: d['color'] = color
    d.update(kw); return d

def spr(path):
    """an item or block texture as an 8x8 icon inside text ('item/iron_ingot', 'block/white_wool')"""
    return {'type': 'object', 'atlas': 'minecraft:items' if path.startswith('item/') else 'minecraft:blocks', 'sprite': 'minecraft:' + path,
            'color': 'white', 'shadow_color': 0}

def line(*parts):
    """parts side by side; the empty first part keeps them from inheriting each other's colour"""
    return [{'text': ''}] + list(parts)

def grp(*parts):
    """the same as one compound, for values kept in storage and dropped into a dialog by a macro"""
    return {'text': '', 'extra': list(parts)}

# ------------------------------------------------------------------ what is sold
CUR = {'iron': dict(name='철', subj='철이', item='minecraft:iron_ingot', color='white', icon='item/iron_ingot', score='#iron'),
       'gold': dict(name='금', subj='금이', item='minecraft:gold_ingot', color='gold', icon='item/gold_ingot', score='#gold'),
       'em': dict(name='에메랄드', subj='에메랄드가', item='minecraft:emerald', color='green', icon='item/emerald', score='#em')}
TEAMS = ['red', 'blue', 'lime', 'yellow', 'cyan', 'white', 'pink', 'gray']
LATER = '※ 특수 효과는 나중에 추가돼.'
UNB = '[unbreakable={}]'

def I(id, key, name, short, n, cost, cur, icon, desc, give, later=False):
    return dict(id=id, key=key, name=name, short=short, n=n, cost=cost, cur=cur, icon=icon, desc=desc, give=give, later=later)

ITEMS = [
    # blocks
    I(1, 'wool', '양털', '양털', 16, 4, 'iron', 'block/white_wool', '섬 사이에 다리를 놓기 좋아. 팀 색으로 나와.', ('dyed', '_wool', None)),
    I(2, 'clay', '테라코타', '테라코타', 16, 12, 'iron', 'block/terracotta', '침대를 지키는 기본 블록. 팀 색으로 나와.', ('dyed', '_terracotta', None)),
    I(3, 'glass', '폭발 방지 유리', '방폭 유리', 4, 12, 'iron', 'block/glass', '폭발을 막아 주는 유리.', ('dyed', '_stained_glass', '폭발 방지 유리')),
    I(4, 'endstone', '엔드 스톤', '엔드 스톤', 12, 24, 'iron', 'block/end_stone', '침대를 지키는 단단한 블록.', ('give', 'minecraft:end_stone')),
    I(5, 'ladder', '사다리', '사다리', 8, 4, 'iron', 'block/ladder', '높은 곳에 오를 때 써.', ('give', 'minecraft:ladder')),
    I(6, 'wood', '참나무 판자', '나무 판자', 16, 4, 'gold', 'block/oak_planks', '침대를 지키는 좋은 블록.', ('give', 'minecraft:oak_planks')),
    I(7, 'obsidian', '흑요석', '흑요석', 4, 4, 'em', 'block/obsidian', '침대를 가장 단단하게 지켜 줘.', ('give', 'minecraft:obsidian')),
    # melee
    I(8, 'stone_sword', '돌 검', '돌 검', 1, 10, 'iron', 'item/stone_sword', '기본 검보다 조금 더 세.', ('give', 'minecraft:stone_sword' + UNB)),
    I(9, 'iron_sword', '철 검', '철 검', 1, 7, 'gold', 'item/iron_sword', '든든한 철 검.', ('give', 'minecraft:iron_sword' + UNB)),
    I(10, 'diamond_sword', '다이아몬드 검', '다이아 검', 1, 4, 'em', 'item/diamond_sword', '가장 센 검.', ('give', 'minecraft:diamond_sword' + UNB)),
    I(11, 'stick', '막대기 (밀치기 I)', '넉백 막대', 1, 5, 'gold', 'item/stick', '적을 다리 밖으로 밀어내.',
      ('give', 'minecraft:stick[enchantments={"minecraft:knockback":1},item_name={text:"막대기 (밀치기 I)"}]')),
    # armor (leggings and boots, like Hypixel)
    I(12, 'chain', '사슬 갑옷', '사슬 갑옷', 1, 40, 'iron', 'item/chainmail_boots', '사슬 레깅스와 부츠를 바로 입혀 줘.', ('armor', 1, 'chainmail')),
    I(13, 'iron_armor', '철 갑옷', '철 갑옷', 1, 12, 'gold', 'item/iron_boots', '철 레깅스와 부츠를 바로 입혀 줘.', ('armor', 2, 'iron')),
    I(14, 'diamond_armor', '다이아몬드 갑옷', '다이아 갑옷', 1, 6, 'em', 'item/diamond_boots', '다이아몬드 레깅스와 부츠를 바로 입혀 줘.', ('armor', 3, 'diamond')),
    # tools
    I(15, 'shears', '가위', '가위', 1, 20, 'iron', 'item/shears', '양털을 순식간에 잘라.', ('once', 'minecraft:shears' + UNB, 'minecraft:shears')),
    I(16, 'pick', '곡괭이', '곡괭이', 1, 0, 'iron', 'item/wooden_pickaxe', '살 때마다 한 단계씩 좋아져.', ('tool', 'pk')),
    I(17, 'axe', '도끼', '도끼', 1, 0, 'iron', 'item/wooden_axe', '살 때마다 한 단계씩 좋아져.', ('tool', 'ax')),
    # ranged
    I(18, 'arrow', '화살', '화살', 6, 2, 'gold', 'item/arrow', '활에 넣어 쏴.', ('give', 'minecraft:arrow')),
    I(19, 'bow', '활', '활', 1, 12, 'gold', 'item/bow', '멀리 있는 적을 맞혀.', ('give', 'minecraft:bow')),
    I(20, 'bow_p', '활 (힘 I)', '힘 활', 1, 24, 'gold', 'item/bow', '더 아픈 활.', ('give', 'minecraft:bow[enchantments={"minecraft:power":1}]')),
    I(21, 'bow_pp', '활 (힘 I, 밀치기 I)', '힘+밀치기 활', 1, 6, 'em', 'item/bow', '아프고, 맞으면 밀려나.',
      ('give', 'minecraft:bow[enchantments={"minecraft:power":1,"minecraft:punch":1}]')),
    # potions
    I(22, 'speed', '신속 II 물약 (45초)', '신속 물약', 1, 1, 'em', 'item/potion', '45초 동안 빨리 달려.',
      ('give', 'minecraft:potion[potion_contents={custom_color:8171462,custom_effects:[{id:"minecraft:speed",amplifier:1b,duration:900}]},custom_name={text:"신속 II 물약 (45초)",italic:false}]')),
    I(23, 'jump', '점프 강화 V 물약 (45초)', '점프 물약', 1, 1, 'em', 'item/potion', '45초 동안 아주 높이 뛰어.',
      ('give', 'minecraft:potion[potion_contents={custom_color:2293580,custom_effects:[{id:"minecraft:jump_boost",amplifier:4b,duration:900}]},custom_name={text:"점프 강화 V 물약 (45초)",italic:false}]')),
    I(24, 'invis', '투명 물약 (30초)', '투명 물약', 1, 2, 'em', 'item/potion', '30초 동안 몸이 안 보여.',
      ('give', 'minecraft:potion[potion_contents={custom_color:8356754,custom_effects:[{id:"minecraft:invisibility",amplifier:0b,duration:600}]},custom_name={text:"투명 물약 (30초)",italic:false}]')),
    # utility
    I(25, 'gapple', '황금 사과', '황금 사과', 1, 3, 'gold', 'item/golden_apple', '든든한 회복.', ('give', 'minecraft:golden_apple')),
    I(26, 'bedbug', '빈대', '빈대', 1, 30, 'iron', 'item/snowball', '던진 곳에 좀벌레가 나와 적을 괴롭혀.', ('give', 'minecraft:snowball[item_name={text:"빈대"}]'), True),
    I(27, 'golem', '드림 디펜더', '드림 디펜더', 1, 120, 'iron', 'item/iron_golem_spawn_egg', '기지를 지켜 주는 철 골렘.',
      ('give', 'minecraft:iron_golem_spawn_egg[item_name={text:"드림 디펜더"}]'), True),
    I(28, 'fireball', '화염구', '화염구', 1, 40, 'iron', 'item/fire_charge', '우클릭으로 쏴서 다리 위의 적을 날려 버려.', ('give', 'minecraft:fire_charge[item_name={text:"화염구"}]'), True),
    I(29, 'tnt', 'TNT', 'TNT', 1, 4, 'gold', 'block/tnt_side', '놓자마자 불이 붙어.', ('give', 'minecraft:tnt'), True),
    I(30, 'pearl', '엔더 진주', '엔더 진주', 1, 4, 'em', 'item/ender_pearl', '적 기지로 가는 가장 빠른 길.', ('give', 'minecraft:ender_pearl')),
    I(31, 'water', '물 양동이', '물 양동이', 1, 3, 'gold', 'item/water_bucket', '쫓아오는 적을 늦추고 폭발도 막아.', ('give', 'minecraft:water_bucket')),
    I(32, 'egg', '다리 알', '다리 알', 1, 1, 'em', 'item/egg', '던진 방향으로 다리가 생겨.', ('give', 'minecraft:egg[item_name={text:"다리 알"}]'), True),
    I(33, 'milk', '마법 우유', '마법 우유', 1, 4, 'gold', 'item/milk_bucket', '마시면 30초 동안 함정에 안 걸려.', ('give', 'minecraft:milk_bucket[item_name={text:"마법 우유"}]'), True),
    I(34, 'sponge', '스펀지', '스펀지', 4, 3, 'gold', 'block/sponge', '물을 빨아들여.', ('give', 'minecraft:sponge')),
    I(35, 'tower', '소형 팝업 타워', '팝업 타워', 1, 24, 'iron', 'block/barrel_side', '놓으면 탑이 솟아올라.', ('give', 'minecraft:chest[item_name={text:"소형 팝업 타워"}]'), True),
]
BY = {i['key']: i for i in ITEMS}
# tool tiers: (name, short name, enchantment text, item, sprite, cost, currency)
TIERS = {'pk': [('나무 곡괭이', '나무 곡괭이', '효율 I', 'minecraft:wooden_pickaxe[enchantments={"minecraft:efficiency":1},unbreakable={}]', 'wooden_pickaxe', 10, 'iron'),
                ('철 곡괭이', '철 곡괭이', '효율 II', 'minecraft:iron_pickaxe[enchantments={"minecraft:efficiency":2},unbreakable={}]', 'iron_pickaxe', 10, 'iron'),
                ('금 곡괭이', '금 곡괭이', '효율 III, 날카로움 II', 'minecraft:golden_pickaxe[enchantments={"minecraft:efficiency":3,"minecraft:sharpness":2},unbreakable={}]', 'golden_pickaxe', 3, 'gold'),
                ('다이아몬드 곡괭이', '다이아 곡괭이', '효율 III', 'minecraft:diamond_pickaxe[enchantments={"minecraft:efficiency":3},unbreakable={}]', 'diamond_pickaxe', 6, 'gold')],
         'ax': [('나무 도끼', '나무 도끼', '효율 I', 'minecraft:wooden_axe[enchantments={"minecraft:efficiency":1},unbreakable={}]', 'wooden_axe', 10, 'iron'),
                ('돌 도끼', '돌 도끼', '효율 I', 'minecraft:stone_axe[enchantments={"minecraft:efficiency":1},unbreakable={}]', 'stone_axe', 10, 'iron'),
                ('철 도끼', '철 도끼', '효율 II', 'minecraft:iron_axe[enchantments={"minecraft:efficiency":2},unbreakable={}]', 'iron_axe', 3, 'gold'),
                ('다이아몬드 도끼', '다이아 도끼', '효율 III', 'minecraft:diamond_axe[enchantments={"minecraft:efficiency":3},unbreakable={}]', 'diamond_axe', 6, 'gold')]}
TOOLTAG = {'pk': '#minecraft:pickaxes', 'ax': '#minecraft:axes'}
PAGES = [(1, '빠른 구매', 'item/nether_star', ['wool', 'stone_sword', 'chain', 'pick', 'bow', 'speed', 'tnt', 'wood', 'iron_sword', 'iron_armor', 'shears', 'arrow',
                                              'jump', 'water', 'endstone', 'diamond_sword', 'diamond_armor', 'gapple', 'fireball', 'pearl']),
         (2, '블록', 'block/terracotta', ['wool', 'clay', 'glass', 'endstone', 'ladder', 'wood', 'obsidian']),
         (3, '근접 무기', 'item/golden_sword', ['stone_sword', 'iron_sword', 'diamond_sword', 'stick']),
         (4, '방어구', 'item/chainmail_boots', ['chain', 'iron_armor', 'diamond_armor']),
         (5, '도구', 'item/stone_pickaxe', ['shears', 'pick', 'axe']),
         (6, '원거리', 'item/bow', ['arrow', 'bow', 'bow_p', 'bow_pp']),
         (7, '물약', 'item/brewing_stand', ['speed', 'jump', 'invis']),
         (8, '유틸리티', 'block/tnt_side', ['gapple', 'bedbug', 'golem', 'fireball', 'tnt', 'pearl', 'water', 'egg', 'milk', 'sponge', 'tower'])]
COLS = 4; BW = 116                       # four buttons of 116 px side by side fit a 480 px wide screen
BUY = {'text': '클릭해서 구매!', 'color': 'yellow'}
HINT = {'text': '물건을 누르면 바로 구매돼.', 'color': 'gray'}

def textures():
    """every icon the dialogs use (the pack writer checks them against the game's own files)"""
    out = {c['icon'] for c in CUR.values()} | {i['icon'] for i in ITEMS} | {p[2] for p in PAGES}
    for tiers in TIERS.values(): out |= {'item/' + tr[4] for tr in tiers}
    return sorted(out)

def width(s):
    """rough pixel width of a label in the default font (Hangul 9, digits and latin 6, space 4)"""
    w = 0
    for ch in s:
        if ch == ' ': w += 4
        elif '가' <= ch <= '힣': w += 9
        elif ch in 'iIl!.,:': w += 2 + 1
        elif ch in '()': w += 5
        else: w += 6
    return w

# ------------------------------------------------------------------ dialogs
def cmd(c): return {'type': 'minecraft:run_command', 'command': c}

def item_button(it):
    i = it['id']; cur = CUR[it['cur']]; cnt = f" ×{it['n']}" if it['n'] > 1 else ''
    if it['give'][0] == 'tool':
        label = line(spr(f'item/$(s{i})'), t(f' $(n{i})  ', 'white'), Raw(f'$(x{i})'))
        tip = line(t(f'$(m{i}) ($(g{i}))', f'$(c{i})'), t('\n'), Raw(f'$(y{i})'), t('\n\n' + it['desc'], 'gray'), t('\n\n'), Raw(f'$(l{i})'))
    else:
        label = line(spr(it['icon']), t(f" {it['short']}{cnt}  ", 'white'), spr(cur['icon']), t(str(it['cost']), f'$(c{i})'))
        tip = line(t(it['name'] + cnt, f'$(c{i})'), t('\n가격: ', 'gray'), t(f"{it['cost']} {cur['name']}", cur['color']), t('\n\n' + it['desc'], 'gray'),
                   *([t('\n' + LATER, 'dark_gray')] if it['later'] else []), t('\n\n'), Raw(f'$(l{i})'))
    return {'label': label, 'tooltip': tip, 'width': BW, 'action': cmd(f'trigger bw.buy set {i}')}

def page_dialog(page):
    pid, pname, picon, keys = page
    tabs = []
    for (n, name, icon, _) in PAGES:
        sel = n == pid
        tabs.append({'label': line(spr(icon), t(' ' + name, 'green' if sel else 'white', **({'bold': True} if sel else {}))),
                     'tooltip': line(t(name, 'green'), t('\n' + ('지금 보고 있는 칸이야.' if sel else '클릭해서 보기!'), 'gray' if sel else 'yellow')),
                     'width': BW, 'action': cmd(f'trigger bw.shop set {n}')})
    body = [{'type': 'minecraft:plain_message', 'width': 400, 'contents': line(
        t('가진 자원  ', 'gray'), spr('item/iron_ingot'), t(' $(iron)     ', 'white'), spr('item/gold_ingot'), t(' $(gold)     ', 'gold'),
        spr('item/emerald'), t(' $(em)', 'green'), t('\n'), Raw('$(msg)'))}]
    return {'type': 'minecraft:multi_action', 'title': line(t('아이템 상점', 'white', bold=True), t('  ·  ' + pname, 'gray')), 'can_close_with_escape': True,
            'pause': False, 'after_action': 'none', 'body': body, 'columns': COLS, 'actions': tabs + [item_button(BY[k]) for k in keys],
            'exit_action': {'label': t('닫기'), 'width': 150, 'action': cmd('trigger bw.shop set 99')}}

def notice(title, lines):
    """a small window with one button"""
    return snbt({'type': 'minecraft:notice', 'title': t(title, 'white', bold=True), 'pause': False,
                 'body': [{'type': 'minecraft:plain_message', 'width': 300, 'contents': line(*lines)}], 'action': {'label': t('확인'), 'width': 150}})

# ------------------------------------------------------------------ functions
def merge(d): return 'data modify storage bw:shop a merge value ' + snbt(d)

def held(item):
    """conditions that are true when the player carries the item (inventory, hotbar or off hand)"""
    return [f'if items entity @s container.* {item}', f'if items entity @s weapon.offhand {item}']

def prep(it):
    """commands that fill in an item's macro variables for the player the function runs as"""
    i = it['id']; kind = it['give'][0]
    if kind == 'tool':
        tk = it['give'][1]; out = []
        for lv, (name, short, ench, item, sprite, cost, cur) in enumerate(TIERS[tk]):
            c = CUR[cur]
            def var(col, last):
                return {f'c{i}': col, f'l{i}': last, f'x{i}': grp(spr(c['icon']), t(str(cost), col))}
            base = {f'n{i}': short, f'm{i}': name, f'g{i}': ench, f's{i}': sprite,
                    f'y{i}': grp(t('가격: ', 'gray'), t(f"{cost} {c['name']}", c['color']), t(f'   ({lv + 1}/4 단계)', 'dark_gray'))}
            base.update(var('red', {'text': c['subj'] + ' 부족해!', 'color': 'red'}))
            out.append(f'execute if score #{tk} bw matches {lv} run ' + merge(base))
            out.append(f"execute if score #{tk} bw matches {lv} if score {c['score']} bw matches {cost}.. run " + merge(var('green', BUY)))
        name, short, ench, item, sprite, cost, cur = TIERS[tk][-1]
        out.append(f'execute if score #{tk} bw matches 4 run ' + merge({
            f'n{i}': short, f'm{i}': name, f'g{i}': ench, f's{i}': sprite, f'c{i}': 'gray', f'x{i}': grp(t('최고', 'aqua')),
            f'y{i}': grp(t('더 올릴 단계가 없어.', 'gray')), f'l{i}': {'text': '이미 최고 단계야!', 'color': 'aqua'}}))
        return out
    c = CUR[it['cur']]
    out = [merge({f'c{i}': 'red', f'l{i}': {'text': c['subj'] + ' 부족해!', 'color': 'red'}}),
           f"execute if score {c['score']} bw matches {it['cost']}.. run " + merge({f'c{i}': 'green', f'l{i}': BUY})]
    own = {f'c{i}': 'gray', f'l{i}': {'text': '이미 가지고 있어.', 'color': 'aqua'}}
    if kind == 'armor': out.append(f"execute if items entity @s armor.legs #bw:armor{it['give'][1]} run " + merge(own))
    if kind == 'once': out += [f'execute {cond} run ' + merge(own) for cond in held(it['give'][2])]
    return out

def write(fn, pack):
    """write the shop's functions, advancements and tags into the pack (fn(path, lines) writes one function)"""
    # ---- which shopkeeper was clicked: one advancement per kind
    for kind in ('shop', 'team', 'unlock'):
        tag = {'shop': 'bw.npc.shop', 'team': 'bw.npc.upgrade', 'unlock': 'bw.npc.unlock'}[kind]
        p = f'{pack}/data/bw/advancement/npc/{kind}.json'; os.makedirs(os.path.dirname(p), exist_ok=True)
        # 26.3 writes entity predicates as a map of sub-predicates and loot conditions with "type"; a mistake here stops the world from loading
        json.dump({'criteria': {'click': {'trigger': 'minecraft:player_interacted_with_entity',
                                           'conditions': {'entity': {'type': 'minecraft:entity_properties', 'entity': 'this',
                                                                     'predicate': {'minecraft:entity_type': 'minecraft:villager',
                                                                                   'minecraft:entity_tags': {'all_of': [tag]}}}}}},
                   'rewards': {'function': f'bw:npc/{kind}'}}, open(p, 'w'))
    for n, items in ((1, ['chainmail', 'iron', 'diamond', 'netherite']), (2, ['iron', 'diamond', 'netherite']), (3, ['diamond', 'netherite'])):
        p = f'{pack}/data/bw/tags/item/armor{n}.json'; os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({'values': [f'minecraft:{m}_leggings' for m in items]}, open(p, 'w'))
    fn('npc/shop', ['advancement revoke @s only bw:npc/shop',
                    'scoreboard players set #team bw 5',
                    'execute as @e[type=minecraft:villager,tag=bw.npc.shop,distance=..10,sort=nearest,limit=1] run function bw:shop/whose',
                    'scoreboard players operation @s bw.team = #team bw',
                    'scoreboard players set @s bw.page 1',
                    'data modify storage bw:shop a.msg set value ' + snbt(HINT),
                    'function bw:shop/refresh'])
    fn('shop/whose', [f'execute if entity @s[tag=bw.t.{d}] run scoreboard players set #team bw {n}' for n, d in enumerate(TEAMS)])
    fn('npc/team', ['advancement revoke @s only bw:npc/team',
                    'dialog show @s ' + notice('팀 업그레이드', [t('팀 전체가 강해지는 업그레이드를 파는 곳이야.\n\n', 'white'), t('아직 준비 중이야. 곧 열려!', 'yellow')])])
    fn('npc/unlock', ['advancement revoke @s only bw:npc/unlock',
                      'dialog show @s ' + notice('업그레이드', [t('게임에서 모은 코인으로\n상점 물건을 하나씩 해금하는 곳이야.\n\n', 'white'), t('코인 시스템이 들어오면 열려!', 'yellow')])])
    # ---- opening and refreshing a page
    fn('shop/tiers', sum(([f'scoreboard players set #{tk} bw 0'] +
                          [f"execute {cond} run scoreboard players set #{tk} bw {lv + 1}" for lv, tr in enumerate(TIERS[tk]) for cond in held(tr[3].split('[')[0])]
                          for tk in TIERS), []))
    fn('shop/refresh', [f"execute store result score {c['score']} bw run clear @s {c['item']} 0" for c in CUR.values()] +
       [f"execute store result storage bw:shop a.{k} int 1 run scoreboard players get {c['score']} bw" for k, c in CUR.items()] +
       ['function bw:shop/tiers'] + [f'execute if score @s bw.page matches {p[0]} run function bw:shop/page/{p[0]}' for p in PAGES])
    longest = 0
    for page in PAGES:
        pid, pname, picon, keys = page
        fn(f'shop/page/{pid}', sum((prep(BY[k]) for k in keys), []) + [f'function bw:shop/show/{pid} with storage bw:shop a'])
        fn(f'shop/show/{pid}', ['$dialog show @s ' + snbt(page_dialog(page))])
        for k in keys:
            it = BY[k]
            if it['give'][0] != 'tool':
                longest = max(longest, 9 + width(f" {it['short']}" + (f" ×{it['n']}" if it['n'] > 1 else '') + '  ') + 9 + width(str(it['cost'])))
    for tiers in TIERS.values():
        for tr in tiers: longest = max(longest, 9 + width(f' {tr[1]}  ') + 9 + width(str(tr[5])))
    assert longest <= BW - 8, ('a label is too wide for its button', longest)
    fn('shop/nav', ['scoreboard players operation #p bw = @s bw.shop', 'scoreboard players set @s bw.shop 0',
                    'execute if score #p bw matches 99 run return run dialog clear @s',
                    'execute unless score #p bw matches 1..%d run return fail' % len(PAGES),
                    'execute unless entity @e[type=minecraft:villager,tag=bw.npc.shop,distance=..10] run return run function bw:shop/far',
                    'scoreboard players operation @s bw.page = #p bw',
                    'data modify storage bw:shop a.msg set value ' + snbt(HINT),
                    'function bw:shop/refresh'])
    fn('shop/far', ['dialog clear @s', 'tellraw @s ' + snbt(t('상점 주인 가까이에서만 살 수 있어.', 'red'))])
    # ---- paying
    for k, c in CUR.items():
        fn(f'shop/fail/{k}', ['execute store result storage bw:shop t.n int 1 run scoreboard players get #need bw',
                              f"data modify storage bw:shop t.subj set value {q(c['subj'])}",
                              'function bw:shop/failmsg with storage bw:shop t'])
    fn('shop/failmsg', ['$data modify storage bw:shop a.msg set value {text:"✘ $(subj) 부족해! $(n)개 더 필요해.",color:"red"}',
                        '$tellraw @s {text:"$(subj) 부족해! $(n)개 더 필요해!",color:"red"}',
                        'playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 0.6 0.5', 'function bw:shop/refresh'])
    fn('shop/ok', ['$data modify storage bw:shop a.msg set value {text:"✔ $(name) 구매!",color:"green"}',
                   '$tellraw @s [{text:"구매 완료! ",color:"green"},{text:"$(name)",color:"gold"}]',
                   'playsound minecraft:block.note_block.pling master @s ~ ~ ~ 0.8 2', 'function bw:shop/refresh'])
    fn('shop/no', ['$data modify storage bw:shop a.msg set value {text:"✘ $(why)",color:"red"}', '$tellraw @s {text:"$(why)",color:"red"}',
                   'playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 0.6 0.5', 'function bw:shop/refresh'])
    fn('shop/dye', ['data modify storage bw:shop d.dye set value "white"'] +
       [f'execute if score @s bw.team matches {n} run data modify storage bw:shop d.dye set value "{d}"' for n, d in enumerate(TEAMS)])
    def pay(cur, cost):
        c = CUR[cur]
        return [f"execute store result score #have bw run clear @s {c['item']} 0", f'scoreboard players set #need bw {cost}',
                'scoreboard players operation #need bw -= #have bw', f'execute if score #need bw matches 1.. run return run function bw:shop/fail/{cur}',
                f"clear @s {c['item']} {cost}"]
    disp = ['scoreboard players operation #id bw = @s bw.buy', 'scoreboard players set @s bw.buy 0',
            'execute unless entity @e[type=minecraft:villager,tag=bw.npc.shop,distance=..10] run return run function bw:shop/far']
    for it in ITEMS:
        i = it['id']; kind = it['give'][0]; cnt = f" ×{it['n']}" if it['n'] > 1 else ''
        ok = 'function bw:shop/ok ' + snbt({'name': it['name'] + cnt})
        disp.append(f'execute if score #id bw matches {i} run return run function bw:shop/buy/{i}')
        if kind == 'give':
            fn(f'shop/buy/{i}', pay(it['cur'], it['cost']) + [f"give @s {it['give'][1]} {it['n']}", ok])
        elif kind == 'dyed':
            suffix, name = it['give'][1], it['give'][2]
            comp = f'[item_name={{text:{q(name)}}}]' if name else ''
            fn(f'shop/buy/{i}', pay(it['cur'], it['cost']) + ['function bw:shop/dye', f'function bw:shop/give/{i} with storage bw:shop d', ok])
            fn(f'shop/give/{i}', [f"$give @s minecraft:$(dye){suffix}{comp} {it['n']}"])
        elif kind == 'armor':
            lv, mat = it['give'][1], it['give'][2]
            fn(f'shop/buy/{i}', [f'execute if items entity @s armor.legs #bw:armor{lv} run return run function bw:shop/no {snbt({"why": "이미 같거나 더 좋은 방어구를 입고 있어."})}'] +
               pay(it['cur'], it['cost']) + [f'item replace entity @s armor.legs with minecraft:{mat}_leggings{UNB}',
                                             f'item replace entity @s armor.feet with minecraft:{mat}_boots{UNB}',
                                             'playsound minecraft:item.armor.equip_generic master @s ~ ~ ~ 1 1', ok])
        elif kind == 'once':
            fn(f'shop/buy/{i}', [f'execute {cond} run return run function bw:shop/no {snbt({"why": "이미 가지고 있어."})}' for cond in held(it['give'][2])] +
               pay(it['cur'], it['cost']) + [f"give @s {it['give'][1]} 1", ok])
        elif kind == 'tool':
            tk = it['give'][1]
            fn(f'shop/buy/{i}', ['function bw:shop/tiers'] +
               [f'execute if score #{tk} bw matches {lv} run return run function bw:shop/buy/{i}_{lv}' for lv in range(4)] +
               [f'function bw:shop/no {snbt({"why": "이미 최고 단계야."})}'])
            for lv, (name, short, ench, item, sprite, cost, cur) in enumerate(TIERS[tk]):
                fn(f'shop/buy/{i}_{lv}', pay(cur, cost) + [f'clear @s {TOOLTAG[tk]}', f'give @s {item} 1', 'function bw:shop/ok ' + snbt({'name': f'{name} ({ench})'})])
    fn('shop/buy', disp)
    # ---- a handful of each resource for trying the shop out before the generators exist
    fn('shop/money', ['give @s minecraft:iron_ingot 64', 'give @s minecraft:gold_ingot 32', 'give @s minecraft:emerald 16',
                      'tellraw @s ' + snbt(t('시험용 자원을 줬어: 철 64, 금 32, 에메랄드 16', 'yellow'))])
    return dict(load=['scoreboard objectives add bw.buy trigger', 'scoreboard objectives add bw.shop trigger',
                      'scoreboard objectives add bw.page dummy', 'scoreboard objectives add bw.team dummy'],
                tick=['scoreboard players enable @a bw.buy', 'scoreboard players enable @a bw.shop',
                      'scoreboard players set @a[scores={bw.buy=..-1}] bw.buy 0', 'scoreboard players set @a[scores={bw.shop=..-1}] bw.shop 0',
                      'execute as @a[scores={bw.buy=1..}] at @s run function bw:shop/buy',
                      'execute as @a[scores={bw.shop=1..}] at @s run function bw:shop/nav'],
                longest=longest)

if __name__ == '__main__':
    for p in PAGES: print(p[0], p[1], len(p[3]), 'items, dialog', len(snbt(page_dialog(p))), 'chars')
    print(textures())
