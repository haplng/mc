"""Checks for a canvas: block states against the 26.3 block report, markers, and a physics pass
(things that would fall, pop off or flow after the structure is placed in the world)."""
import json, math, re, os
from collections import Counter
from canvas import parse

ROOT = os.environ.get('BW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = json.load(open(ROOT + '/ref/263_blocks_data.json'))

def states(cv, label=''):
    bad = {}
    for s in set(cv.b.values()):
        name, props = parse(s); n = name.replace('minecraft:', '')
        if n not in B: bad[s] = 'unknown block'; continue
        allowed = B[n][0]
        for k, v in props.items():
            if k not in allowed: bad[s] = f'no property {k}'
            elif v not in allowed[k]: bad[s] = f'{k}={v} not in {allowed[k]}'
    for s, why in sorted(bad.items()): print(f'  BAD {label}: {s}  ({why})')
    return bad

# ------------------------------------------------------------------ shapes
SOIL = {'grass_block', 'dirt', 'coarse_dirt', 'podzol', 'rooted_dirt', 'moss_block', 'pale_moss_block', 'mud', 'muddy_mangrove_roots', 'farmland', 'mycelium'}
DRY = SOIL | {'sand', 'red_sand'}
PLANTS = {'short_grass', 'fern', 'dandelion', 'poppy', 'blue_orchid', 'allium', 'azure_bluet', 'red_tulip', 'orange_tulip', 'white_tulip', 'pink_tulip',
          'oxeye_daisy', 'cornflower', 'lily_of_the_valley', 'torchflower', 'pink_petals', 'wildflowers', 'bush', 'firefly_bush', 'sweet_berry_bush',
          'oak_sapling', 'spruce_sapling', 'birch_sapling', 'jungle_sapling', 'acacia_sapling', 'cherry_sapling', 'dark_oak_sapling', 'azalea',
          'flowering_azalea', 'closed_eyeblossom', 'open_eyeblossom'}
TALL = {'tall_grass', 'large_fern', 'sunflower', 'lilac', 'rose_bush', 'peony', 'pitcher_plant'}
DRYPLANTS = {'dead_bush', 'short_dry_grass', 'tall_dry_grass'}
CROPS = {'wheat', 'carrots', 'potatoes', 'beetroots'}
NONE = PLANTS | TALL | DRYPLANTS | CROPS | {'water', 'lava', 'cobweb', 'snow', 'leaf_litter', 'vine', 'glow_lichen', 'ladder', 'lever', 'rail', 'powered_rail',
       'detector_rail', 'activator_rail', 'redstone_wire', 'redstone_torch', 'torch', 'soul_torch', 'wall_torch', 'soul_wall_torch', 'copper_torch',
       'copper_wall_torch', 'tripwire', 'string', 'hanging_roots', 'spore_blossom', 'seagrass', 'tall_seagrass', 'kelp', 'kelp_plant', 'sea_pickle',
       'lily_pad', 'moss_carpet', 'pale_moss_carpet', 'pale_hanging_moss', 'red_mushroom', 'brown_mushroom', 'crimson_roots', 'warped_roots',
       'nether_sprouts', 'weeping_vines', 'weeping_vines_plant', 'twisting_vines', 'twisting_vines_plant', 'cave_vines', 'cave_vines_plant',
       'sugar_cane', 'fire', 'soul_fire', 'structure_void', 'light', 'cocoa', 'small_dripleaf', 'big_dripleaf', 'big_dripleaf_stem', 'bamboo', 'bamboo_sapling',
       'cactus_flower', 'end_rod', 'lightning_rod', 'flower_pot'}
PARTIAL_PAT = re.compile(r'(_slab|_stairs|_fence|_fence_gate|_wall|_pane|iron_bars|copper_bars|_door|_trapdoor|_carpet|_bed|_banner|_sign|lantern|chain|_button|'
                         r'_pressure_plate|candle|chest|campfire|anvil|cauldron|hopper|lectern|grindstone|bell|brewing_stand|_pot$|potted_|_head|_skull|'
                         r'_egg|leaves|scaffolding|composter|stonecutter|enchanting_table|daylight_detector|farmland|dirt_path|cake|_shelf$|coral_fan|'
                         r'amethyst_cluster|_bud$|pointed_dripstone|conduit|heavy_core|decorated_pot|dragon_egg|chorus_plant|chorus_flower|cactus|'
                         r'azalea|sniffer_egg|dried_ghast|_golem_statue|bars$)')

def nm(s): return s.split('[')[0].replace('minecraft:', '') if s else None
def props(s):
    return dict(kv.split('=') for kv in s[s.index('[') + 1:-1].split(',')) if s and '[' in s else {}

def full(s):
    """a full cube that supports anything on any face"""
    if not s: return False
    n = nm(s)
    if n in ('sea_lantern', 'jack_o_lantern'): return True
    if n in NONE: return False
    if n.endswith('_slab'): return props(s).get('type') == 'double'
    if PARTIAL_PAT.search(n): return False
    return True

def top_full(s):
    if full(s): return True
    if not s: return False
    n = nm(s); p = props(s)
    if n.endswith('_slab'): return p.get('type') in ('top', 'double')
    if n.endswith('_stairs'): return p.get('half') == 'top'
    return False

def top_center(s):
    if top_full(s): return True
    if not s: return False
    n = nm(s)
    return n.endswith('_fence') or n.endswith('_wall') or (n.endswith('chain') and props(s).get('axis') == 'y') or n in ('hopper', 'scaffolding', 'cauldron', 'composter', 'anvil', 'lectern', 'grindstone')

def bottom_full(s):
    if full(s): return True
    if not s: return False
    n = nm(s); p = props(s)
    if n.endswith('_slab'): return p.get('type') in ('bottom', 'double')
    if n.endswith('_stairs'): return p.get('half') == 'bottom'
    return False

def bottom_center(s):
    if bottom_full(s): return True
    if not s: return False
    n = nm(s)
    return n.endswith('_fence') or n.endswith('_wall') or (n.endswith('chain') and props(s).get('axis') == 'y') or n in ('iron_bars', 'end_rod')

GRAVITY = re.compile(r'^(sand|red_sand|gravel|suspicious_sand|suspicious_gravel|.*_concrete_powder|anvil|chipped_anvil|damaged_anvil|dragon_egg|scaffolding)$')
DV = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}

def problem(cv, p, s):
    """why this block cannot stay where it is (None if it can)"""
    x, y, z = p; n = nm(s); pr = props(s)
    below = cv.b.get((x, y - 1, z)); above = cv.b.get((x, y + 1, z)); bn = nm(below)
    wet = lambda q: (cv.b.get(q) is not None) and (nm(cv.b[q]) == 'water' or props(cv.b[q]).get('waterlogged') == 'true')
    if n == 'water' or pr.get('waterlogged') == 'true':
        if below is None: return 'water leaks down'
        if n == 'water' and (nm(below) in NONE and not wet((x, y - 1, z))): return 'water leaks down'
        for dx, dz in DV.values():
            q = cv.b.get((x + dx, y, z + dz))
            if q is None: return 'water leaks sideways'
            if nm(q) in NONE and not wet((x + dx, y, z + dz)) and nm(q) not in ('seagrass', 'kelp', 'kelp_plant', 'tall_seagrass', 'sea_pickle'): return 'water leaks sideways'
        if n == 'water': return None
    if GRAVITY.match(n):
        return None if below is not None and nm(below) not in NONE else 'falls'
    if 'leaves' in n and pr.get('persistent') != 'true': return 'leaves decay'
    if n.endswith('_carpet') or n in ('moss_carpet', 'pale_moss_carpet'): return None if below is not None else 'no floor'
    if n in PLANTS: return None if bn in SOIL else 'plant needs soil'
    if n in DRYPLANTS: return None if (bn in DRY or (bn and 'terracotta' in bn)) else 'plant needs sand'
    if n in CROPS: return None if bn == 'farmland' else 'crop needs farmland'
    if n in TALL:
        if pr.get('half') == 'upper': return None if nm(below) == n else 'half plant'
        return None if (bn in SOIL and nm(above) == n) else 'half plant'
    if n in ('red_mushroom', 'brown_mushroom'): return None if bn in ('mycelium', 'podzol', 'crimson_nylium', 'warped_nylium') else 'mushroom in daylight'
    if n in ('crimson_roots', 'warped_roots', 'nether_sprouts'): return None if bn and ('nylium' in bn or bn in SOIL or bn == 'soul_soil') else 'needs nylium'
    if n == 'cactus':
        if bn not in ('sand', 'red_sand', 'cactus'): return 'cactus needs sand'
        return 'cactus touches a block' if any(cv.b.get((x + dx, y, z + dz)) for dx, dz in DV.values()) else None
    if n in ('bamboo', 'sugar_cane'): return None if bn in DRY or bn in ('gravel', n) else 'needs ground'
    if n == 'leaf_litter': return None if top_full(below) else 'needs floor'
    if n == 'snow': return None if (top_full(below) and bn not in ('ice', 'packed_ice', 'barrier')) else 'snow needs a full block'
    if n == 'lily_pad': return None if wet((x, y - 1, z)) else 'needs water'
    if n in ('seagrass', 'kelp', 'kelp_plant', 'tall_seagrass'): return 'water plant: avoid' 
    if 'coral' in n and not n.startswith('dead_'):
        if n.endswith('_block'):
            return None if any(wet(q) for q in ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1), (x, y + 1, z), (x, y - 1, z))) else 'coral dies'
        return None if pr.get('waterlogged') == 'true' else 'coral dies'
    if n.endswith('lantern') and n not in ('sea_lantern', 'jack_o_lantern'):
        if pr.get('hanging') == 'true': return None if bottom_center(above) else 'lantern hangs on nothing'
        return None if top_center(below) else 'lantern stands on nothing'
    if n in ('hanging_roots', 'spore_blossom', 'pale_hanging_moss'): return None if bottom_full(above) else 'hangs on nothing'
    if n in ('weeping_vines', 'weeping_vines_plant', 'cave_vines', 'cave_vines_plant'):
        return None if (bottom_full(above) or nm(above) in ('weeping_vines_plant', 'cave_vines_plant')) else 'hangs on nothing'
    if n in ('torch', 'soul_torch', 'redstone_torch', 'copper_torch') or 'candle' in n and 'cake' not in n:
        return None if top_center(below) else 'needs a block below'
    if n.endswith('_pressure_plate'): return None if top_center(below) else 'needs a block below'
    if n in ('rail', 'powered_rail', 'detector_rail', 'activator_rail', 'redstone_wire', 'cake', 'repeater', 'comparator') or n.endswith('_door'):
        if n.endswith('_door') and pr.get('half') == 'upper': return None if nm(below) == n else 'half door'
        return None if top_full(below) else 'needs a full block below'
    if n.endswith('_banner') and not n.endswith('_wall_banner'): return None if below is not None and nm(below) not in NONE else 'needs a block below'
    if n.endswith('_sign') and 'wall' not in n and 'hanging' not in n: return None if below is not None and nm(below) not in NONE else 'needs a block below'
    if n in ('ladder', 'wall_torch', 'soul_wall_torch', 'copper_wall_torch', 'tripwire_hook') or n.endswith('_wall_banner') or n.endswith('_wall_sign') or n.endswith('_wall_fan'):
        dx, dz = DV[pr.get('facing', 'north')]
        q = cv.b.get((x - dx, y, z - dz))
        return None if full(q) else 'nothing behind it'
    if n.endswith('_button') or n == 'lever':
        face = pr.get('face', 'wall')
        if face == 'floor': return None if top_full(below) else 'needs a block'
        if face == 'ceiling': return None if bottom_full(above) else 'needs a block'
        dx, dz = DV[pr.get('facing', 'north')]
        return None if full(cv.b.get((x - dx, y, z - dz))) else 'nothing behind it'
    if n in ('vine', 'glow_lichen', 'sculk_vein'):
        ok = False
        for d, (dx, dz) in DV.items():
            if pr.get(d) == 'true':
                if full(cv.b.get((x + dx, y, z + dz))): ok = True
                else: return 'vine side has no wall'
        if pr.get('up') == 'true' and bottom_full(above): ok = True
        return None if ok or (n == 'vine' and nm(above) == 'vine') else 'vine holds on nothing'
    if n.endswith('_bed'):
        dx, dz = DV[pr['facing']]
        q = (x + dx, y, z + dz) if pr['part'] == 'foot' else (x - dx, y, z - dz)
        o = cv.b.get(q)
        return None if o and nm(o) == n and props(o).get('part') != pr['part'] else 'half bed'
    if n == 'sea_pickle': return None if below is not None and nm(below) not in NONE else 'needs floor'
    if n == 'cocoa':
        dx, dz = DV[pr['facing']]
        return None if nm(cv.b.get((x + dx, y, z + dz))) in ('jungle_log', 'jungle_wood', 'stripped_jungle_log') else 'cocoa needs jungle log'
    if n in ('fire', 'soul_fire'): return 'fire goes out or spreads'
    return None

def physics(cv, label='', fix=True, quiet=False):
    """find blocks that will not survive; with fix, remove them (repeating until stable) and report the totals"""
    total = Counter(); rounds = 0
    todo = set(cv.b.keys())
    while todo and rounds < 60:
        rounds += 1; gone = []
        for p in todo:
            s = cv.b.get(p)
            if s is None: continue
            why = problem(cv, p, s)
            if why: gone.append((p, s, why))
        if not gone: break
        nxt = set()
        for p, s, why in gone:
            total[(nm(s), why)] += 1
            if fix:
                cv.b.pop(p, None); cv.nbt.pop(p, None)
                x, y, z = p
                for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    q = (x + d[0], y + d[1], z + d[2])
                    if q in cv.b: nxt.add(q)
        if not fix: break
        todo = nxt
    if total and not quiet:
        print(f'  PHYSICS {label}: ' + ', '.join(f'{n} x{c} ({w})' for (n, w), c in total.most_common(12)))
    return total

PASSABLE = NONE | {'air'}
def markers(cv, label=''):
    """every marker must stand in open air with head room and a floor; the bed marker must be on a bed"""
    bad = []
    for (x, y, z), t in cv.ents:
        tags = [str(v) for v in t.get('Tags', [])]
        bx, by, bz = math.floor(x), math.floor(y), math.floor(z)
        if 'bw.bed' in tags:
            if 'bed' not in (cv.get(bx, by, bz) or ''): bad.append((tags[-1], (bx, by, bz), 'not on the bed'))
            continue
        for dy in (0, 1):
            s = cv.get(bx, by + dy, bz)
            if s and nm(s) not in PASSABLE and not nm(s).endswith('_carpet'): bad.append((tags, (bx, by + dy, bz), s))
        if not cv.get(bx, by - 1, bz): bad.append((tags, (bx, by - 1, bz), 'nothing below'))
    for b in bad: print(f'  MARKER {label}: {b}')
    return bad

def census(cv):
    """count the markers by role; a complete 8-team map has 8 of each team marker, 4 diamond and 4 emerald generators"""
    c = Counter()
    for _, t in cv.ents:
        tags = [str(v) for v in t.get('Tags', [])]
        for k in ('bw.spawn', 'bw.bed', 'bw.gen.iron', 'bw.shop', 'bw.upgrade', 'bw.gen.diamond', 'bw.gen.emerald'):
            if k in tags: c[k] += 1
    return dict(c)

# ------------------------------------------------------------------ can the team walk from its spawn to everything it needs?
def _open(cv, p):
    s = cv.b.get(p)
    if s is None: return True
    n = nm(s)
    return n in NONE or n.endswith('_carpet') or n.endswith('_pressure_plate') or n.endswith('_banner') or 'sign' in n or n in ('candle',) or n.endswith('_candle')
def _floor(cv, p):
    s = cv.b.get(p)
    if s is None: return False
    n = nm(s)
    return not (n in NONE or n.endswith('_carpet') or n.endswith('_banner') or 'sign' in n) or n in ('water',)
def _stand(cv, x, y, z):
    return _floor(cv, (x, y - 1, z)) and _open(cv, (x, y, z)) and _open(cv, (x, y + 1, z))

def _clickable(cv, seen, npc, rng=3.0):
    """can a player standing on one of the walked cells right-click a villager at `npc`? (within reach, nothing solid in between)"""
    nx, ny, nz = npc
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            for dy in (-1, 0, 1):
                c = (nx + dx, ny + dy, nz + dz)
                if c not in seen: continue
                ex, ey, ez = c[0] + 0.5, c[1] + 1.62, c[2] + 0.5
                for ty in (1.7, 1.2):                              # the villager's head, then its chest
                    tx, tyy, tz = nx + 0.5, ny + ty, nz + 0.5
                    d = math.dist((ex, ey, ez), (tx, tyy, tz))
                    if d > rng + 0.3: continue
                    ok = True; n = int(d / 0.05) + 1
                    for i in range(1, n):
                        px, py, pz = ex + (tx - ex) * i / n, ey + (tyy - ey) * i / n, ez + (tz - ez) * i / n
                        q = (math.floor(px), math.floor(py), math.floor(pz))
                        if q[0] == nx and q[2] == nz and q[1] in (ny, ny + 1): break       # arrived at the villager
                        if not _open(cv, q): ok = False; break
                    if ok: return True
    return False

def reach(cv, label='', limit=4000):
    """walk (steps up 1, drops up to 3, ladders) from each team's spawn; report bed / generator / shops that cannot be reached"""
    import collections
    teams = collections.defaultdict(dict)
    for (x, y, z), t in cv.ents:
        tags = [str(v) for v in t.get('Tags', [])]
        team = next((g for g in tags if g.startswith('bw.t.')), None)
        if not team: continue
        for k in ('bw.spawn', 'bw.bed', 'bw.gen', 'bw.shop', 'bw.upgrade'):
            if k in tags: teams[team][k] = (math.floor(x), math.floor(y), math.floor(z))
    bad = []
    for team, m in sorted(teams.items()):
        s = m['bw.spawn']
        if not _stand(cv, *s): bad.append((team, 'spawn not standable', s)); continue
        seen = {s}; dq = collections.deque([s])
        while dq and len(seen) < limit:
            x, y, z = dq.popleft()
            nxt = []
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for dy in (1, 0, -1, -2, -3):
                    q = (x + dx, y + dy, z + dz)
                    if dy == 1 and not _open(cv, (x, y + 2, z)): continue
                    if dy < 0 and not all(_open(cv, (x + dx, y + j, z + dz)) for j in range(dy, 2)): continue
                    if _stand(cv, *q): nxt.append(q); break
            if nm(cv.b.get((x, y, z)) or '') == 'ladder' or nm(cv.b.get((x, y + 1, z)) or '') == 'ladder':
                if _open(cv, (x, y + 2, z)): nxt.append((x, y + 1, z))
            if nm(cv.b.get((x, y - 1, z)) or '') == 'ladder': nxt.append((x, y - 1, z))
            for q in nxt:
                if q not in seen: seen.add(q); dq.append(q)
        if m.get('bw.gen') and m['bw.gen'] not in seen: bad.append((team, 'bw.gen unreachable', m['bw.gen']))
        for k in ('bw.shop', 'bw.upgrade'):                       # a shopkeeper may stand behind a counter: someone must be able to click it
            if m.get(k) and m[k] not in seen and not _clickable(cv, seen, m[k]): bad.append((team, k + ' cannot be clicked', m[k]))
        b = m.get('bw.bed')
        if b and not any((b[0] + dx, b[1], b[2] + dz) in seen for dx in (-1, 0, 1) for dz in (-2, -1, 0, 1, 2)): bad.append((team, 'bed unreachable', b))
        m['area'] = len(seen)
    for b in bad[:6]: print(f'  REACH {label}: {b}')
    return bad, {t: m.get('area', 0) for t, m in teams.items()}
