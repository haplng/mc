"""Voxel grid for the tabletop dioramas -> fill commands, path simulation, preview images."""
import math, random

X0, X1, Z0, Z1, Y0, Y1 = -14, 14, -14, 14, 58, 86

PASS = ['air', 'cave_air', 'void_air', 'short_grass', 'fern', 'dandelion', 'poppy', 'azure_bluet', 'oxeye_daisy',
        'cornflower', 'torch', 'wall_torch', 'soul_torch', 'redstone_torch', 'fire', 'soul_fire', 'water', 'lava',
        'nether_portal', 'end_portal', 'red_mushroom', 'brown_mushroom', 'dead_bush', 'crimson_roots',
        'warped_roots', 'nether_sprouts', 'crimson_fungus', 'warped_fungus', 'wheat', 'cobweb', 'light', 'snow',
        'vine', 'tall_grass', 'lever', 'stone_button']
FRAGILE = set(PASS) | {'red_bed', 'oak_door', 'pointed_dripstone', 'nether_brick_fence', 'oak_fence', 'iron_bars',
                       'end_portal_frame', 'lightning_rod', 'chest', 'furnace', 'spawner'}
GRAVITY = {'sand', 'gravel', 'red_sand'}
FLUID = {'water', 'lava'}

def base(b): return b.split('[')[0]

class Grid:
    def __init__(s): s.b = {}; s.base_y = 59
    def inb(s, x, y, z): return X0 <= x <= X1 and Z0 <= z <= Z1 and Y0 <= y <= Y1
    def set(s, x, y, z, blk):
        if not s.inb(x, y, z): return
        if blk is None or blk == 'air': s.b.pop((x, y, z), None)
        else: s.b[(x, y, z)] = blk
    def get(s, x, y, z): return s.b.get((x, y, z), 'air')
    def fill(s, x1, y1, z1, x2, y2, z2, blk):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1): s.set(x, y, z, blk)
    def solid(s, x, y, z):
        if not (X0 <= x <= X1 and Z0 <= z <= Z1): return False
        if y < Y0: return True
        return base(s.get(x, y, z)) not in PASS
    def top(s, x, z):
        for y in range(Y1, Y0 - 1, -1):
            if s.solid(x, y, z): return y
        return Y0 - 1
    def stand(s, x, z):
        for y in range(s.base_y, Y1):
            if s.solid(x, y - 1, z) and not s.solid(x, y, z) and not s.solid(x, y + 1, z): return y
        return s.top(x, z) + 1
    def col(s, x, z, y1, y2, blk):
        for y in range(y1, y2 + 1): s.set(x, y, z, blk)

    # ----- commands -----
    def cmds(s):
        groups = {}
        for (x, y, z), b in s.b.items(): groups.setdefault(b, set()).add((x, y, z))
        boxes = []
        for b, cells in groups.items():
            rem = set(cells)
            for (x, y, z) in sorted(cells, key=lambda c: (c[1], c[2], c[0])):
                if (x, y, z) not in rem: continue
                x2 = x
                while (x2 + 1, y, z) in rem: x2 += 1
                z2 = z
                while all((xx, y, z2 + 1) in rem for xx in range(x, x2 + 1)): z2 += 1
                y2 = y
                while all((xx, y2 + 1, zz) in rem for xx in range(x, x2 + 1) for zz in range(z, z2 + 1)): y2 += 1
                for xx in range(x, x2 + 1):
                    for yy in range(y, y2 + 1):
                        for zz in range(z, z2 + 1): rem.discard((xx, yy, zz))
                boxes.append((b, x, y, z, x2, y2, z2))
        def phase(bx):
            bb = base(bx[0])
            if bb in FLUID: return 3
            if bb in FRAGILE: return 2
            if bb in GRAVITY: return 1
            return 0
        boxes.sort(key=lambda bx: (phase(bx), bx[2], bx[0]))
        out = []
        for b, x, y, z, x2, y2, z2 in boxes:
            if (x, y, z) == (x2, y2, z2): out.append(f'setblock {x} {y} {z} minecraft:{b}')
            else: out.append(f'fill {x} {y} {z} {x2} {y2} {z2} minecraft:{b}')
        return out

    def check(s, name):
        """Fluids must be contained, gravity blocks supported."""
        errs = []
        for (x, y, z), b in s.b.items():
            bb = base(b)
            if bb in FLUID:
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, nz = x + dx, z + dz
                    if not (X0 <= nx <= X1 and Z0 <= nz <= Z1): errs.append(f'{name}: fluid {bb} at border {(x,y,z)}'); continue
                    n = base(s.get(nx, y, nz))
                    if n != bb and not s.solid(nx, y, nz): errs.append(f'{name}: fluid {bb} at {(x,y,z)} leaks to {(nx,y,nz)}')
                if y > Y0 and base(s.get(x, y - 1, z)) != bb and not s.solid(x, y - 1, z):
                    errs.append(f'{name}: fluid {bb} at {(x,y,z)} leaks down')
            if bb in GRAVITY and y > Y0 and not s.solid(x, y - 1, z):
                errs.append(f'{name}: {bb} unsupported at {(x,y,z)}')
        return errs

    # ----- walking simulation (mirrors steve/step + steve/snap) -----
    def walk(s, a, b, label=''):
        """Simulate walking from cell a to cell b. Returns (issues, ticks)."""
        x, z = a[0] + 0.5, a[1] + 0.5
        tx, tz = b[0] + 0.5, b[1] + 0.5
        y = s.stand(a[0], a[1])
        issues = []; ticks = 0
        while abs(x - tx) > 0.3 or abs(z - tz) > 0.3:
            d = math.hypot(tx - x, tz - z)
            x += (tx - x) / d * 0.2; z += (tz - z) / d * 0.2
            cx, cz = math.floor(x), math.floor(z)
            if not (X0 <= cx <= X1 and Z0 <= cz <= Z1): issues.append(f'{label}: leaves board at {(cx,cz)}'); break
            if s.solid(cx, y, cz):
                y += 1
                if s.solid(cx, y, cz): issues.append(f'{label}: wall >1 high at {(cx,y,cz)}')
            elif not s.solid(cx, y - 1, cz):
                y -= 1
                if not s.solid(cx, y - 1, cz): issues.append(f'{label}: drop >1 at {(cx,y,cz)}')
            f = base(s.get(cx, y, cz))
            if f in FLUID: issues.append(f'{label}: walks through {f} at {(cx,y,cz)}')
            ticks += 1
            if ticks > 600: issues.append(f'{label}: never arrives'); break
        return sorted(set(issues)), ticks

# ----- primitives -----
def oak_tree(g, x, z, h=4):
    y0 = g.stand(x, z)
    for dy in (h - 2, h - 1):
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) == 2 and abs(dz) == 2: continue
                g.set(x + dx, y0 + dy, z + dz, 'oak_leaves[persistent=true]')
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            g.set(x + dx, y0 + h, z + dz, 'oak_leaves[persistent=true]')
    for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        g.set(x + dx, y0 + h + 1, z + dz, 'oak_leaves[persistent=true]')
    g.col(x, z, y0, y0 + h - 1, 'oak_log')
    return [(x, y0 + i, z) for i in range(h)]

def ellipse(cx, cz, rx, rz):
    out = []
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            if ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 <= 1.0: out.append((x, z))
    return out

COLORS = {
    'grass_block': (106, 170, 74), 'dirt': (134, 96, 67), 'stone': (125, 125, 125), 'cobblestone': (110, 110, 110),
    'oak_leaves': (60, 120, 40), 'oak_log': (102, 81, 50), 'water': (60, 100, 220), 'lava': (230, 110, 20),
    'sand': (219, 207, 163), 'gravel': (136, 126, 126), 'deepslate': (80, 80, 84), 'netherrack': (110, 50, 50),
    'nether_bricks': (50, 25, 30), 'obsidian': (25, 20, 40), 'end_stone': (220, 222, 160), 'black_concrete': (10, 10, 14),
    'stone_bricks': (120, 120, 120), 'crimson_nylium': (130, 30, 30), 'bedrock': (60, 60, 60), 'oak_planks': (160, 130, 80),
    'coal_ore': (60, 60, 60), 'iron_ore': (200, 160, 130), 'deepslate_diamond_ore': (90, 220, 220), 'soul_sand': (80, 62, 50),
    'glowstone': (250, 210, 110), 'bookshelf': (150, 110, 70), 'farmland': (90, 60, 40), 'wheat': (200, 180, 60),
    'end_portal_frame': (60, 110, 90), 'cobbled_deepslate': (70, 70, 74), 'tuff': (100, 105, 95), 'magma_block': (150, 60, 20),
    'nether_wart_block': (120, 10, 10), 'crimson_stem': (100, 40, 60), 'red_bed': (180, 40, 40), 'crafting_table': (130, 90, 50),
}
def preview(g, path, points=(), routes=()):
    from PIL import Image, ImageDraw
    S = 16
    img = Image.new('RGB', (29 * S, 29 * S), (0, 0, 0)); d = ImageDraw.Draw(img)
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            ty = None
            for y in range(Y1, Y0 - 1, -1):
                if g.get(x, y, z) != 'air': ty = y; break
            if ty is None: col = (0, 0, 0)
            else:
                b = base(g.get(x, ty, z)); c = COLORS.get(b, (180, 60, 200) if b not in PASS else (150, 200, 120))
                sh = 0.55 + 0.45 * min(1.0, (ty - Y0) / 12.0)
                col = tuple(int(v * sh) for v in c)
            px, pz = (x - X0) * S, (z - Z0) * S
            d.rectangle([px, pz, px + S - 1, pz + S - 1], fill=col)
            if ty is not None: d.text((px + 2, pz + 2), str(ty - 57), fill=(255, 255, 255))
    for (a, b) in routes:
        d.line([(a[0] - X0) * S + 8, (a[1] - Z0) * S + 8, (b[0] - X0) * S + 8, (b[1] - Z0) * S + 8], fill=(255, 255, 0), width=2)
    for i, (x, z) in enumerate(points):
        px, pz = (x - X0) * S, (z - Z0) * S
        d.ellipse([px + 3, pz + 3, px + 13, pz + 13], outline=(255, 0, 0), width=2)
    img.save(path)
