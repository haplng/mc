"""Validate every block state of a canvas against the 26.3 block report."""
import json
from canvas import parse
import os
B = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ref', '263_blocks_data.json')))
def check(cv, label=''):
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

PASSABLE = ('air', 'short_grass', 'fern', 'pink_petals', 'leaf_litter', 'snow', 'dead_bush', 'short_dry_grass', 'carpet', 'red_mushroom', 'brown_mushroom',
            'crimson_roots', 'warped_roots', 'nether_sprouts', 'lily_of_the_valley', 'azure_bluet', 'dandelion', 'oxeye_daisy', 'cornflower', 'allium', 'bush')
def markers(cv, label=''):
    """every marker must stand in open air (with head room); generators need the block below to be solid"""
    import math
    bad = []
    for (x, y, z), t in cv.ents:
        tags = [str(v) for v in t.get('Tags', [])]
        if 'bw.bed' in tags:
            if 'bed' not in (cv.get(math.floor(x), math.floor(y), math.floor(z)) or ''): bad.append((tags[-1], (x, y, z), 'not on the bed'))
            continue
        bx, by, bz = math.floor(x), math.floor(y), math.floor(z)
        for dy in (0, 1):
            s = cv.get(bx, by + dy, bz)
            if s and not any(p in s for p in PASSABLE): bad.append((tags[-1], (bx, by + dy, bz), s))
        if not cv.get(bx, by - 1, bz): bad.append((tags[-1], (bx, by - 1, bz), 'nothing below'))
    for b in bad: print(f'  MARKER {label}: {b}')
    return bad
