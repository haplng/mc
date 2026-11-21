"""ASCII slices of a base canvas: python3 slice.py m01_tea cup_base y1 y2 [x0 x1 z0 z1]"""
import sys, importlib
sys.path.insert(0, '/home/claude/bw/gen3')
mod, fn = sys.argv[1], sys.argv[2]
ys = range(int(sys.argv[3]), int(sys.argv[4]) + 1)
m = importlib.import_module(mod)
cv = getattr(m, fn)('red')
(x0, y0, z0), (x1, y1, z1) = cv.bounds()
if len(sys.argv) > 5: x0, x1, z0, z1 = map(int, sys.argv[5:9])
def ch(n):
    if n is None: return '.'
    n = n.split('[')[0]
    table = {'chest': 'C', 'ender_chest': 'E', 'red_bed': 'B', 'ladder': 'H', 'barrel': 'b', 'red_carpet': ',', 'flower_pot': 'p',
             'red_concrete': '#', 'white_concrete': 'W', 'smooth_quartz': 'Q', 'quartz_block': 'q', 'orange_stained_glass': 'g'}
    if n in table: return table[n]
    if 'stairs' in n: return 's'
    if 'slab' in n: return '_'
    if 'fence' in n: return 'f'
    if 'lantern' in n: return 'L'
    if 'carpet' in n: return ','
    if 'glass' in n: return 'g'
    if 'wool' in n: return 'w'
    if 'iron_block' in n or 'gold_block' in n or 'emerald' in n or 'diamond' in n: return 'G'
    return 'x'
mk = {}
for e in cv.ents:
    pos = e['pos'] if isinstance(e, dict) else e[0]
    tags = e.get('nbt', {}).get('Tags', []) if isinstance(e, dict) else []
    mk[(int(pos[0] // 1), int(pos[1] // 1), int(pos[2] // 1))] = tags
print('markers', {k: [t for t in v if t.startswith('bw.')] for k, v in mk.items()})
for y in ys:
    print(f'--- y={y}   x {x0}..{x1} (left→right), z {z0}..{z1} (top→bottom)')
    print('     ' + ''.join(str(abs(x) % 10) for x in range(x0, x1 + 1)))
    for z in range(z0, z1 + 1):
        print(f'{z:4d} ' + ''.join(ch(cv.name(x, y, z)) if cv.get(x, y, z) else '.' for x in range(x0, x1 + 1)))
