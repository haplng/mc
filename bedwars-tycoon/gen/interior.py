"""Furniture and fittings for the inside of buildings, plus the generator shrines."""
import json, os, math
from canvas import parse, fmt

_B = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ref', '263_blocks_data.json')))

def face(state, d):
    """give a block a facing if it has one (d: north/south/east/west)"""
    name, p = parse(state if ':' in state.split('[')[0] else 'minecraft:' + state)
    n = name.replace('minecraft:', '')
    if n in _B and 'facing' in _B[n][0] and 'facing' not in p:
        if d in _B[n][0]['facing']: p['facing'] = d
        elif 'up' in _B[n][0]['facing']: p['facing'] = 'up'
    return fmt(name, p)

OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}

STYLES = {
    'home':   ['bookshelf', 'bookshelf', 'barrel', 'crafting_table', 'furnace', 'smoker', 'barrel', 'bookshelf', 'bookshelf'],
    'farm':   ['hay_block', 'hay_block', 'barrel', 'composter', 'crafting_table', 'smoker', 'barrel', 'hay_block', 'barrel'],
    'desert': ['decorated_pot', 'barrel', 'decorated_pot', 'crafting_table', 'furnace', 'barrel', 'decorated_pot', 'barrel', 'decorated_pot'],
    'frost':  ['barrel', 'bookshelf', 'barrel', 'crafting_table', 'furnace', 'smoker', 'barrel', 'bookshelf', 'barrel'],
    'nether': ['chiseled_bookshelf', 'barrel', 'brewing_stand', 'crafting_table', 'blast_furnace', 'smithing_table', 'barrel', 'chiseled_bookshelf', 'lodestone'],
    'end':    ['purpur_pillar', 'magenta_shulker_box', 'brewing_stand', 'enchanting_table', 'purpur_pillar', 'ender_chest', 'magenta_shulker_box', 'purpur_pillar', 'end_stone_bricks'],
    'jungle': ['chiseled_stone_bricks', 'barrel', 'decorated_pot', 'crafting_table', 'furnace', 'barrel', 'decorated_pot', 'barrel', 'chiseled_stone_bricks'],
    'harbour':['barrel', 'barrel', 'cartography_table', 'crafting_table', 'smoker', 'barrel', 'loom', 'barrel', 'barrel'],
    'castle': ['bookshelf', 'bookshelf', 'lectern', 'crafting_table', 'enchanting_table', 'bookshelf', 'bookshelf', 'lectern', 'bookshelf'],
    'mush':   ['barrel', 'crafting_table', 'brown_mushroom_block', 'smoker', 'barrel'],
}
POTS = {
    'home': ['potted_red_tulip', 'potted_azure_bluet', 'potted_fern', 'potted_oxeye_daisy'],
    'sakura': ['potted_cherry_sapling', 'potted_bamboo', 'potted_azure_bluet', 'potted_lily_of_the_valley'],
    'desert': ['potted_cactus', 'potted_dead_bush'], 'frost': ['potted_spruce_sapling', 'potted_fern'],
    'nether': ['potted_crimson_fungus', 'potted_warped_fungus', 'potted_crimson_roots'], 'end': ['potted_cactus'],
    'jungle': ['potted_jungle_sapling', 'potted_fern', 'potted_bamboo'], 'mush': ['potted_red_mushroom', 'potted_brown_mushroom'],
    'castle': ['potted_blue_orchid', 'potted_allium', 'potted_cornflower', 'potted_white_tulip'],
}

def table(cv, x, y, z, wood, chairs=((0, 1), (0, -1))):
    cv.set(x, y, z, f'{wood}_fence'); cv.set(x, y + 1, z, f'{wood}_pressure_plate')
    for dx, dz in chairs:
        d = 'south' if dz > 0 else 'north' if dz < 0 else 'east' if dx > 0 else 'west'
        cv.set(x + dx, y, z + dz, f'{wood}_stairs[facing={d},half=bottom]')

def rug(cv, x0, x1, z0, z1, y, dye, edge='white'):
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            border = x in (x0, x1) or z in (z0, z1)
            if cv.empty(x, y, z): cv.set(x, y, z, f'{edge if border else dye}_carpet')

def room(cv, x0, x1, z0, z1, y, dye, style='home', wood='oak', pots='home', door=None, back='north', h=3):
    """furnish a rectangular room (inclusive interior bounds), its back wall on the given side"""
    items = STYLES.get(style, STYLES['home'])
    pl = POTS.get(pots, POTS['home'])
    xs = list(range(x0, x1 + 1))
    zb = z0 if back == 'north' else z1
    inward = 'south' if back == 'north' else 'north'
    for i, x in enumerate(xs):
        if door and (x, zb) == door: continue
        it = items[i % len(items)] if len(xs) >= 3 else items[i]
        cv.set(x, y, zb, face(it, inward))
        top = None
        if it in ('barrel', 'decorated_pot', 'hay_block', 'chiseled_stone_bricks', 'purpur_pillar', 'end_stone_bricks', 'lodestone'):
            top = cv.rng.choice(pl)
        elif it in ('bookshelf', 'chiseled_bookshelf'):
            top = face(it, inward) if h >= 3 else None
        if top and cv.empty(x, y + 1, zb): cv.set(x, y + 1, zb, top)
    # table with two chairs along the left wall, pots and a workstation along the right wall
    zm = (z0 + z1) // 2
    if x1 - x0 >= 4 and z1 - z0 >= 2:
        table(cv, x0 + 1, y, zm, wood, chairs=((0, 1), (0, -1)) if z1 - z0 >= 3 else ((1, 0),))
        for z in range(z0 + (1 if back == 'north' else 0), z1 + (0 if back == 'north' else -1) + 1):
            if (x1, z) != door and cv.empty(x1, y, z) and (z - z0) % 2 == 0:
                cv.set(x1, y, z, f'{wood}_slab[type=top]' if False else face('barrel', 'west'))
                if cv.empty(x1, y + 1, z): cv.set(x1, y + 1, z, cv.rng.choice(pl))
        rug(cv, x0 + 3, x1 - 2, z0 + 1, z1 - 1, y, dye)

def round_room(cv, cx, cz, r, y, dye, style='mush', pots='mush', door_dir=(0, 1)):
    items = STYLES.get(style, STYLES['home']); pl = POTS.get(pots, POTS['home'])
    k = 0
    for a in range(0, 360, 40):
        rad = math.radians(a)
        x, z = cx + round((r - 0.6) * math.cos(rad)), cz + round((r - 0.6) * math.sin(rad))
        if (round(math.cos(rad)), round(math.sin(rad))) == door_dir or abs(math.atan2(math.sin(rad), math.cos(rad)) - math.atan2(door_dir[1], door_dir[0])) < 0.6:
            continue
        if not cv.empty(x, y, z): continue
        to_c = 'south' if cz - z > 0 and abs(cz - z) >= abs(cx - x) else 'north' if abs(cz - z) >= abs(cx - x) else 'east' if cx - x > 0 else 'west'
        it = items[k % len(items)]; k += 1
        cv.set(x, y, z, face(it, to_c))
        if it in ('barrel',) and cv.empty(x, y + 1, z): cv.set(x, y + 1, z, cv.rng.choice(pl))
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if cv.empty(cx + dx, y, cz + dz): cv.set(cx + dx, y, cz + dz, f'{dye if (dx, dz) == (0, 0) else "white"}_carpet')

# ------------------------------------------------------------------ generator builds
def forge(cv, th, dye):
    """open forge over a team's iron/gold generator pad (pad x -1..1, z -6..-4, drop point (0, 1, -5))"""
    P = th['house']; fr = P['frame']; rf = P['roof_full']; rs = P['roof_stair']
    for x in (-2, 2):
        for z in (-7, -3):
            for y in (1, 2, 3): cv.set(x, y, z, fr)
    for x in range(-2, 3):
        for z in range(-7, -2):
            edge_x = x in (-2, 2); edge_z = z in (-7, -3)
            if edge_x and edge_z: cv.set(x, 4, z, rf)
            elif edge_z: cv.set(x, 4, z, f'{rs}[facing={"north" if z == -3 else "south"},half=top]')
            elif edge_x: cv.set(x, 4, z, f'{rs}[facing={"west" if x == 2 else "east"},half=top]')
            else: cv.set(x, 4, z, rf)
    cv.set(0, 5, -5, f'{dye}_concrete'); cv.set(-1, 5, -5, rf if 'stairs' not in rf else rf); cv.set(1, 5, -5, rf)
    cv.set(0, 3, -5, 'lantern[hanging=true]' if th.get('lamp', 'lantern') == 'lantern' else (th['lamp'] + '[hanging=true]' if th['lamp'].endswith('lantern') and th['lamp'] != 'sea_lantern' else 'lantern[hanging=true]'))
    cv.set(-3, 1, -6, face('blast_furnace', 'east')); cv.set(3, 1, -6, 'anvil[facing=north]')
    cv.set(-3, 1, -7, 'iron_block' if False else face('smithing_table', 'east'))
    for x in (-2, 2): cv.set(x, 3, -2, f'{dye}_wall_banner[facing=south]')

def shrine(cv, th, ox, oz, core_acc, glass, h=4):
    """a generator shrine: four pillars round a 3x3 pad (centre (ox,0,oz)) and a roof with a hanging lamp"""
    P = th['house']; fr = P['frame']; rf = P['roof_full']; rs = P['roof_stair']
    class O:            # draw relative to the shrine centre
        def __init__(s, c): s.c = c
        def set(s, x, y, z, b): s.c.set(x + ox, y, z + oz, b)
    o = O(cv)
    _shrine(o, fr, rf, rs, core_acc, glass, h)

def _shrine(cv, fr, rf, rs, core_acc, glass, h):
    for x in (-2, 2):
        for z in (-2, 2):
            for y in range(1, h + 1): cv.set(x, y, z, fr)
    y = h + 1
    for x in range(-3, 4):
        for z in range(-3, 4):
            m = max(abs(x), abs(z))
            if m == 3:
                d = 'south' if z == -3 else 'north' if z == 3 else 'east' if x == -3 else 'west'
                cv.set(x, y, z, f'{rs}[facing={d},half=bottom]')
            elif m == 2: cv.set(x, y, z, rf)
            elif m == 1: cv.set(x, y, z, glass)
            else: cv.set(x, y, z, core_acc)
    cv.set(0, y + 1, 0, f'{rs.replace("_stairs", "_slab")}[type=bottom]' if 'stairs' in rs else rf)
    cv.set(0, h, 0, 'iron_chain[axis=y]'); cv.set(0, h - 1, 0, 'lantern[hanging=true]')
