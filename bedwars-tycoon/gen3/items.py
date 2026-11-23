"""Everything a player can hold in a round: what the shop sells, what it costs, what it takes to unlock, and the exact item that is handed over.
Players are in adventure mode, so every item carries what it may break (only what Bed Wars lets you break) and, for blocks, that it may be placed."""
from util import TEAMS, TEAM_KO, TEAM_DYE_RGB, snbt, q

HIDDEN = '["minecraft:can_break","minecraft:can_place_on","minecraft:unbreakable","minecraft:dyed_color","minecraft:attribute_modifiers","minecraft:attack_range"]'
BREAK = 'can_break=[{blocks:"#bw:breakable"}]'
TOOL = f'unbreakable={{}},{BREAK},tooltip_display={{hidden_components:{HIDDEN}}}'
BLOCK = f'can_place_on=[{{}}],{BREAK},tooltip_display={{hidden_components:{HIDDEN}}}'
PLAIN = f'{BREAK},tooltip_display={{hidden_components:{HIDDEN}}}'

def it(item, comps, extra=''):
    return f'minecraft:{item}[{comps}{"," + extra if extra else ""}]'
def name(s): return 'item_name=' + snbt({'text': s})

CUR = {'fe': ('철', 'minecraft:iron_ingot', 'white'), 'au': ('금', 'minecraft:gold_ingot', 'gold'), 'em': ('에메랄드', 'minecraft:emerald', 'dark_green'),
       'di': ('다이아몬드', 'minecraft:diamond', 'aqua')}

def potion(color, effect, amp, secs, title):
    return it('potion', PLAIN, f'potion_contents={{custom_color:{color},custom_effects:[{{id:"minecraft:{effect}",amplifier:{amp}b,duration:{secs * 20}}}]}},custom_name={{text:{q(title)},italic:false}}')

# key, name, count, cost, currency, icon item (+components), description, what happens on purchase, coins to unlock (0 = from the start)
#   give kinds: ('dyed', suffix)  team-coloured block      ('give', item)  plain hand-over      ('sword', item)  replaces the wooden sword
#               ('armor', level, material)                  ('tool', 'pick'|'axe')               ('shears',)
ITEMS = [
    dict(key='wool', name='양털', n=16, cost=4, cur='fe', icon='white_wool', desc=['섬 사이에 다리를 놓기 좋아.', '팀 색으로 나와.'], give=('dyed', '_wool'), unlock=0),
    dict(key='clay', name='단단한 점토', n=16, cost=12, cur='fe', icon='terracotta', desc=['침대를 지키는 기본 블록.'], give=('give', it('terracotta', BLOCK)), unlock=40),
    dict(key='glass', name='폭발 방지 유리', n=4, cost=12, cur='fe', icon='glass', desc=['폭발에 끄떡없는 유리.', '팀 색으로 나와.'], give=('dyed', '_stained_glass'), unlock=80),
    dict(key='endstone', name='엔드 스톤', n=12, cost=24, cur='fe', icon='end_stone', desc=['침대를 지키는 단단한 블록.', '화염구로는 안 부서져.'], give=('give', it('end_stone', BLOCK)), unlock=120),
    dict(key='ladder', name='사다리', n=8, cost=4, cur='fe', icon='ladder', desc=['높은 곳에 오를 때 써.'], give=('give', it('ladder', BLOCK)), unlock=30),
    dict(key='wood', name='참나무 판자', n=16, cost=4, cur='au', icon='oak_planks', desc=['침대를 지키는 좋은 블록.'], give=('give', it('oak_planks', BLOCK)), unlock=60),
    dict(key='obsidian', name='흑요석', n=4, cost=4, cur='em', icon='obsidian', desc=['침대를 가장 단단하게 지켜 줘.', '다이아몬드 곡괭이로만 캘 수 있어.'], give=('give', it('obsidian', BLOCK)), unlock=300),
    dict(key='stone_sword', name='돌 검', n=1, cost=10, cur='fe', icon='stone_sword', desc=['기본 검보다 조금 더 세.'], give=('sword', 'stone_sword'), unlock=0),
    dict(key='iron_sword', name='철 검', n=1, cost=7, cur='au', icon='iron_sword', desc=['든든한 철 검.'], give=('sword', 'iron_sword'), unlock=100),
    dict(key='diamond_sword', name='다이아몬드 검', n=1, cost=4, cur='em', icon='diamond_sword', desc=['가장 센 검.'], give=('sword', 'diamond_sword'), unlock=300),
    dict(key='stick', name='막대기 (밀치기 I)', n=1, cost=5, cur='au', icon='stick', desc=['적을 다리 밖으로 밀어내.'],
         give=('give', it('stick', PLAIN, 'enchantments={"minecraft:knockback":1},' + name('막대기 (밀치기 I)'))), unlock=150),
    dict(key='chain', name='사슬 갑옷', n=1, cost=24, cur='fe', icon='chainmail_boots', desc=['사슬 레깅스와 부츠.', '죽어도 사라지지 않아.'], give=('armor', 1, 'chainmail'), unlock=60),
    dict(key='iron_armor', name='철 갑옷', n=1, cost=12, cur='au', icon='iron_boots', desc=['철 레깅스와 부츠.', '죽어도 사라지지 않아.'], give=('armor', 2, 'iron'), unlock=200),
    dict(key='diamond_armor', name='다이아몬드 갑옷', n=1, cost=6, cur='em', icon='diamond_boots', desc=['다이아몬드 레깅스와 부츠.', '죽어도 사라지지 않아.'], give=('armor', 3, 'diamond'), unlock=450),
    dict(key='shears', name='가위', n=1, cost=20, cur='fe', icon='shears', desc=['양털을 순식간에 잘라.', '죽어도 사라지지 않아.'], give=('shears',), unlock=0),
    dict(key='pick', name='곡괭이', n=1, cost=0, cur='fe', icon='wooden_pickaxe', desc=['살 때마다 한 단계씩 좋아져.', '죽으면 한 단계 내려가.'], give=('tool', 'pick'), unlock=0),
    dict(key='axe', name='도끼', n=1, cost=0, cur='fe', icon='wooden_axe', desc=['살 때마다 한 단계씩 좋아져.', '죽으면 한 단계 내려가.'], give=('tool', 'axe'), unlock=50),
    dict(key='arrow', name='화살', n=6, cost=2, cur='au', icon='arrow', desc=['활에 넣어 쏴.'], give=('give', it('arrow', PLAIN)), unlock=120),
    dict(key='bow', name='활', n=1, cost=12, cur='au', icon='bow', desc=['멀리 있는 적을 맞혀.'], give=('give', it('bow', TOOL)), unlock=120),
    dict(key='bow_p', name='활 (힘 I)', n=1, cost=20, cur='au', icon='bow', glint=True, desc=['더 아픈 활.'], give=('give', it('bow', TOOL, 'enchantments={"minecraft:power":1}')), unlock=250),
    dict(key='bow_pp', name='활 (힘 I, 밀치기 I)', n=1, cost=6, cur='em', icon='bow', glint=True, desc=['아프고, 맞으면 밀려나.'],
         give=('give', it('bow', TOOL, 'enchantments={"minecraft:power":1,"minecraft:punch":1}')), unlock=400),
    dict(key='speed', name='신속 II 물약 (45초)', n=1, cost=1, cur='em', icon='potion', icon_extra='potion_contents={custom_color:8171462}', desc=['45초 동안 빨리 달려.'],
         give=('give', potion(8171462, 'speed', 1, 45, '신속 II 물약 (45초)')), unlock=80),
    dict(key='jump', name='점프 강화 V 물약 (45초)', n=1, cost=1, cur='em', icon='potion', icon_extra='potion_contents={custom_color:2293580}', desc=['45초 동안 아주 높이 뛰어.'],
         give=('give', potion(2293580, 'jump_boost', 4, 45, '점프 강화 V 물약 (45초)')), unlock=80),
    dict(key='invis', name='투명 물약 (30초)', n=1, cost=2, cur='em', icon='potion', icon_extra='potion_contents={custom_color:8356754}', desc=['30초 동안 몸이 안 보여.'],
         give=('give', potion(8356754, 'invisibility', 0, 30, '투명 물약 (30초)')), unlock=200),
    dict(key='gapple', name='황금 사과', n=1, cost=3, cur='au', icon='golden_apple', desc=['든든한 회복.'], give=('give', it('golden_apple', PLAIN)), unlock=50),
    dict(key='fireball', name='화염구', n=1, cost=40, cur='fe', icon='fire_charge', desc=['우클릭으로 쏴.', '다리 위의 적을 날려 버려.'],
         give=('give', it('carrot_on_a_stick', PLAIN, '!minecraft:max_damage,!minecraft:damage,item_model="minecraft:fire_charge",max_stack_size=64,custom_data={bw:"fireball"},' + name('화염구'))), unlock=150),
    dict(key='tnt', name='TNT', n=1, cost=4, cur='au', icon='tnt', desc=['놓자마자 불이 붙어.', '침대를 둘러싼 블록을 날려.'], give=('give', it('tnt', BLOCK)), unlock=180),
    dict(key='pearl', name='엔더 진주', n=1, cost=4, cur='em', icon='ender_pearl', desc=['적 기지로 가는 가장 빠른 길.'], give=('give', it('ender_pearl', PLAIN)), unlock=350),
    dict(key='water', name='물 양동이', n=1, cost=2, cur='au', icon='water_bucket', desc=['쫓아오는 적을 늦춰.'], give=('give', it('water_bucket', BLOCK)), unlock=60),
    dict(key='egg', name='다리 알', n=1, cost=1, cur='em', icon='egg', desc=['던진 방향으로 다리가 생겨.'],
         give=('give', it('snowball', PLAIN, 'item_model="minecraft:egg",custom_data={bw:"egg"},' + name('다리 알'))), unlock=250),
    dict(key='sponge', name='스펀지', n=4, cost=2, cur='au', icon='sponge', desc=['물을 빨아들여.'], give=('give', it('sponge', BLOCK)), unlock=30),
    # (new items go at the end so that the ids of the older ones stay what they were)
    dict(key='bedbug', name='빈대', n=1, cost=24, cur='fe', icon='snowball', desc=['던진 곳에 좀벌레가 나와서', '15초 동안 적을 물어뜯어.'],
         give=('give', it('snowball', PLAIN, 'custom_data={bw:"bedbug"},' + name('빈대'))), unlock=100),
    dict(key='golem', name='드림 디펜더', n=1, cost=120, cur='fe', icon='iron_golem_spawn_egg', desc=['철 골렘이 4분 동안', '기지를 지켜 줘.'],
         give=('give', it('iron_golem_spawn_egg', BLOCK, 'entity_data={id:"minecraft:iron_golem",Tags:["bw","bw.round","bw.mob","bw.golem","bw.mobnew"],PersistenceRequired:1b},' + name('드림 디펜더'))), unlock=220),
    dict(key='milk', name='마법 우유', n=1, cost=4, cur='au', icon='milk_bucket', desc=['마시면 30초 동안', '적의 함정에 걸리지 않아.'],
         give=('give', it('milk_bucket', PLAIN, name('마법 우유'))), unlock=120),
    dict(key='tower', name='팝업 타워', n=1, cost=24, cur='fe', icon='chest', desc=['놓으면 그 자리에', '사다리 달린 탑이 솟아.'],
         give=('give', it('chest', BLOCK, 'custom_data={bw:"tower"},' + name('팝업 타워'))), unlock=150),
]
for n, d in enumerate(ITEMS): d['id'] = n + 1
BY = {d['key']: d for d in ITEMS}

# tool tiers: name, enchantment text, item, components, cost, currency
PICKS = [('나무 곡괭이', '효율 I', 'wooden_pickaxe', '"minecraft:efficiency":1', 10, 'fe'), ('철 곡괭이', '효율 II', 'iron_pickaxe', '"minecraft:efficiency":2', 10, 'fe'),
         ('금 곡괭이', '효율 III, 날카로움 II', 'golden_pickaxe', '"minecraft:efficiency":3,"minecraft:sharpness":2', 3, 'au'),
         ('다이아몬드 곡괭이', '효율 III', 'diamond_pickaxe', '"minecraft:efficiency":3', 6, 'au')]
AXES = [('나무 도끼', '효율 I', 'wooden_axe', '"minecraft:efficiency":1', 10, 'fe'), ('돌 도끼', '효율 I', 'stone_axe', '"minecraft:efficiency":1', 10, 'fe'),
        ('철 도끼', '효율 II', 'iron_axe', '"minecraft:efficiency":2', 3, 'au'), ('다이아몬드 도끼', '효율 III', 'diamond_axe', '"minecraft:efficiency":3', 6, 'au')]
TIERS = {'pick': PICKS, 'axe': AXES}
def tool_item(t): return it(t[2], TOOL, 'enchantments={' + t[3] + '}')
SHEARS = it('shears', TOOL)
def sword(mat): return it(mat, TOOL)
WOOD_SWORD = sword('wooden_sword')

def armour(piece, mat, team=None):
    dyed = f'dyed_color={TEAM_DYE_RGB[team]},' if mat == 'leather' else ''
    return it(f'{mat}_{piece}', TOOL, dyed + 'enchantment_glint_override=false,enchantments={"minecraft:binding_curse":1}')

PAGES = [('빠른 구매', 'nether_star', ['wool', 'stone_sword', 'chain', 'pick', 'bow', 'speed', 'tnt',
                                     'wood', 'iron_sword', 'iron_armor', 'shears', 'arrow', 'jump', 'water',
                                     'endstone', 'diamond_sword', 'diamond_armor', 'axe', 'gapple', 'fireball', 'pearl']),
         ('블록', 'terracotta', ['wool', 'clay', 'glass', 'endstone', 'ladder', 'wood', 'obsidian']),
         ('근접 무기', 'golden_sword', ['stone_sword', 'iron_sword', 'diamond_sword', 'stick']),
         ('방어구', 'chainmail_boots', ['chain', 'iron_armor', 'diamond_armor']),
         ('도구', 'stone_pickaxe', ['shears', 'pick', 'axe']),
         ('원거리', 'bow', ['arrow', 'bow', 'bow_p', 'bow_pp']),
         ('물약', 'brewing_stand', ['speed', 'jump', 'invis']),
         ('유틸리티', 'tnt', ['gapple', 'bedbug', 'golem', 'fireball', 'tnt', 'pearl', 'water', 'egg', 'milk', 'sponge', 'tower'])]

# team upgrades (paid in diamonds): key, name, icon, description, cost of each level, coins to unlock
UPGRADES = [
    dict(key='sharp', name='날카로운 검', icon='iron_sword', desc=['팀의 검과 도끼에', '날카로움 I이 붙어.'], costs=[4], unlock=150),
    dict(key='prot', name='강화 갑옷', icon='iron_chestplate', desc=['팀의 갑옷에', '보호가 붙어.'], costs=[2, 4, 8, 16], unlock=200),
    dict(key='haste', name='광란의 광부', icon='golden_pickaxe', desc=['팀 전원이 계속', '성급함을 받아.'], costs=[2, 4], unlock=100),
    dict(key='forge', name='용광로', icon='furnace', desc=['기지의 자원이', '더 빨리 나와.'], costs=[2, 4, 6, 8], unlock=150,
         levels=['철 용광로 (+50%)', '황금 용광로 (+100%)', '에메랄드 용광로 (에메랄드 생성)', '용암 용광로 (+200%)']),
    dict(key='heal', name='치유의 샘', icon='beacon', desc=['기지 근처에 있으면', '체력이 계속 차.'], costs=[1], unlock=150),
    dict(key='cush', name='쿠션 부츠', icon='diamond_boots', desc=['팀의 부츠에', '가벼운 착지가 붙어.'], costs=[1, 2], unlock=100),
    dict(key='dbuff', name='드래곤 버프', icon='dragon_egg', desc=['서든 데스 때 우리 팀 드래곤이', '1마리가 아니라 2마리가 돼.'], costs=[5], unlock=150),
]
for n, d in enumerate(UPGRADES): d['id'] = 200 + n + 1
UP = {d['key']: d for d in UPGRADES}
# traps (diamonds): up to three wait in a queue, the first one costs 1, the second 2, the third 4; an enemy who comes near the bed sets off the first in line
TRAP_COST = [1, 2, 4]
TRAPS = [
    dict(k=1, key='trap', name='함정이다!', icon='tripwire_hook', desc=['걸린 적은 8초 동안', '눈이 멀고 느려져.'], unlock=120),
    dict(k=2, key='trap2', name='반격 함정', icon='feather', desc=['기지 근처의 우리 팀이 15초 동안', '신속 II와 점프 강화 II를 받아.'], unlock=120),
    dict(k=3, key='trap3', name='경보 함정', icon='redstone_torch', desc=['경보가 울리고,', '투명한 적이 모습을 드러내.'], unlock=100),
    dict(k=4, key='trap4', name='채굴 피로 함정', icon='iron_pickaxe', desc=['걸린 적은 10초 동안', '채굴 피로에 걸려.'], unlock=150),
]
for d in TRAPS: d['id'] = 210 + d['k']

STARTERS = [d['key'] for d in ITEMS if d['unlock'] == 0]
