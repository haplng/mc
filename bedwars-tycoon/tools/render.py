"""Render block dicts {(x,y,z): name} to a top-down map and an isometric picture."""
import numpy as np
from PIL import Image
DYE = [(233,236,236),(240,118,19),(189,68,179),(58,175,217),(248,198,39),(112,185,25),(237,141,172),(62,68,71),
       (142,142,134),(21,137,145),(121,42,172),(53,57,157),(114,71,40),(84,109,27),(160,39,34),(20,21,25)]
DYEN = ['white','orange','magenta','light_blue','yellow','lime','pink','gray','light_gray','cyan','purple','blue','brown','green','red','black']
BASE = {
 'stone':(125,125,125),'cobblestone':(110,110,110),'mossy_cobblestone':(100,120,95),'stonebrick':(122,121,122),'stone_bricks':(122,121,122),
 'grass':(95,159,53),'grass_block':(95,159,53),'dirt':(134,96,67),'coarse_dirt':(119,85,59),'podzol':(92,63,24),'sand':(219,207,163),'red_sand':(190,102,33),
 'sandstone':(216,203,155),'red_sandstone':(181,98,31),'gravel':(131,127,126),'clay':(160,166,179),'hardened_clay':(150,92,66),'terracotta':(150,92,66),
 'log':(109,85,50),'log2':(76,60,36),'planks':(162,130,78),'leaves':(60,130,40),'leaves2':(70,110,35),'water':(50,90,220),'flowing_water':(50,90,220),
 'lava':(230,100,20),'snow':(240,250,250),'snow_layer':(240,250,250),'ice':(145,183,253),'packed_ice':(140,170,240),'quartz_block':(235,229,222),
 'prismarine':(99,156,151),'sea_lantern':(172,199,190),'glowstone':(250,210,120),'obsidian':(20,18,30),'end_stone':(220,222,158),'netherrack':(110,54,52),
 'nether_brick':(45,22,26),'soul_sand':(81,62,50),'brick_block':(150,97,83),'bookshelf':(120,90,50),'iron_block':(220,220,220),'gold_block':(245,210,60),
 'diamond_block':(100,220,215),'emerald_block':(42,200,90),'coal_block':(16,16,16),'redstone_block':(170,25,10),'lapis_block':(30,67,140),'hay_block':(166,136,38),
 'melon_block':(110,145,30),'pumpkin':(198,118,24),'mycelium':(111,99,105),'vine':(50,110,30),'tallgrass':(80,140,45),'double_plant':(80,150,45),
 'red_flower':(200,40,40),'yellow_flower':(240,220,40),'cactus':(85,127,43),'reeds':(150,190,90),'web':(220,220,220),'barrier':None,'air':None,
 'stone_slab':(160,160,160),'double_stone_slab':(160,160,160),'wooden_slab':(162,130,78),'double_wooden_slab':(162,130,78),'glass':(200,230,235),'glass_pane':(200,230,235),
 'fence':(162,130,78),'cobblestone_wall':(110,110,110),'end_bricks':(225,230,170),'purpur_block':(170,125,170),'magma':(140,60,20),'chest':(160,110,40),
}
def color(name, data=0):
    n = name.replace('minecraft:', '')
    if n in ('wool', 'carpet', 'stained_hardened_clay', 'stained_glass', 'stained_glass_pane', 'concrete', 'concrete_powder'):
        c = DYE[data & 15]
        if n == 'stained_hardened_clay': c = tuple(int(v * 0.62 + 50) for v in c)
        return c
    for suf in ('_wool', '_terracotta', '_concrete', '_stained_glass', '_carpet', '_glazed_terracotta', '_concrete_powder', '_stained_glass_pane', '_bed', '_banner'):
        if n.endswith(suf):
            col = n[:-len(suf)]
            if col in DYEN:
                c = DYE[DYEN.index(col)]
                return tuple(int(v * 0.62 + 50) for v in c) if suf == '_terracotta' else c
    if n in BASE: return BASE[n]
    EXTRA = {'red_mushroom_block': (200, 45, 40), 'brown_mushroom_block': (150, 110, 80), 'mushroom_stem': (205, 198, 185),
             'nether_wart_block': (130, 10, 10), 'warped_wart_block': (20, 130, 120), 'crimson_nylium': (140, 25, 25), 'warped_nylium': (40, 115, 100),
             'shroomlight': (240, 150, 70), 'soul_soil': (75, 57, 46), 'magma_block': (140, 60, 20), 'purpur_pillar': (171, 128, 171),
             'end_stone_bricks': (218, 224, 162), 'chorus_plant': (95, 60, 95), 'chorus_flower': (150, 110, 150), 'calcite': (223, 224, 220),
             'mud_bricks': (137, 104, 79), 'packed_mud': (142, 106, 79), 'moss_block': (89, 109, 45), 'snow_block': (240, 250, 250),
             'blue_ice': (116, 167, 253), 'mycelium': (111, 99, 105), 'red_concrete': (142, 33, 33), 'white_concrete': (207, 213, 214),
             'farmland': (110, 75, 45), 'wheat': (200, 180, 70), 'carrots': (230, 140, 30), 'pumpkin': (198, 118, 24), 'carved_pumpkin': (198, 118, 24),
             'lava': (230, 100, 20), 'fire': (240, 150, 40), 'cactus': (85, 127, 43), 'bamboo': (110, 150, 40), 'end_rod': (240, 240, 230),
             'pink_petals': (235, 160, 200), 'leaf_litter': (170, 110, 50), 'hanging_roots': (150, 110, 85), 'cave_vines': (90, 120, 40),
             'cave_vines_plant': (90, 120, 40), 'weeping_vines': (130, 20, 20), 'weeping_vines_plant': (130, 20, 20), 'barrel': (130, 95, 55)}
    if n in EXTRA: return EXTRA[n]
    if 'leaves' in n:
        return {'cherry': (232, 170, 200), 'birch': (110, 150, 70), 'spruce': (50, 95, 55), 'jungle': (50, 140, 30), 'azalea': (100, 130, 40)}.get(
            next((w for w in ('cherry', 'birch', 'spruce', 'jungle', 'azalea') if w in n), ''), (60, 130, 40))
    if n.endswith('_log') or n.endswith('_wood') or n.endswith('_stem'):
        if 'birch' in n: return (215, 210, 200)
        if 'cherry' in n: return (55, 33, 44)
        if 'crimson' in n: return (100, 40, 60)
        if 'warped' in n: return (50, 100, 100)
        return (95, 75, 45)
    for k, v in (('stairs', None), ('slab', None), ('fence', None), ('wall', None)):
        if n.endswith(k):
            b = n[:-len(k)].rstrip('_')
            for cand in (b, b + 's', b + '_block', b.replace('_brick', '_bricks'), b + '_planks'):
                if cand in BASE and BASE[cand]: return BASE[cand]
    if 'planks' in n or n.endswith('_wood') or 'oak' in n or 'spruce' in n or 'birch' in n or 'acacia' in n or 'jungle' in n:
        return {'spruce': (115, 85, 50), 'birch': (196, 179, 123), 'dark_oak': (66, 43, 20), 'jungle': (160, 115, 80), 'acacia': (168, 90, 50),
                'cherry': (226, 178, 172), 'mangrove': (117, 54, 48), 'bamboo': (194, 173, 80), 'crimson': (101, 48, 70), 'warped': (43, 104, 99)}.get(
                next((w for w in ('dark_oak', 'spruce', 'birch', 'jungle', 'acacia', 'cherry', 'mangrove', 'bamboo', 'crimson', 'warped') if w in n), ''), (162, 130, 78))
    if 'leaves' in n: return (225, 160, 190) if 'cherry' in n else (60, 130, 40)
    if 'log' in n or 'stem' in n: return (100, 80, 50)
    if 'lantern' in n or 'torch' in n or 'lamp' in n or 'froglight' in n: return (250, 210, 130)
    if 'copper' in n: return (190, 110, 80) if 'oxid' not in n and 'weath' not in n else (80, 160, 130)
    if 'deepslate' in n: return (70, 70, 75)
    if 'blackstone' in n: return (40, 35, 40)
    if 'basalt' in n: return (80, 80, 85)
    if 'quartz' in n: return (235, 229, 222)
    if 'prismarine' in n: return (99, 156, 151)
    if 'brick' in n: return (150, 97, 83)
    if 'andesite' in n: return (135, 135, 136)
    if 'diorite' in n: return (190, 190, 190)
    if 'granite' in n: return (150, 105, 90)
    if 'tuff' in n: return (108, 109, 102)
    if 'calcite' in n: return (223, 224, 220)
    if 'moss' in n: return (90, 110, 45)
    if 'flower' in n or 'tulip' in n or 'orchid' in n or 'poppy' in n or 'dandelion' in n or 'petals' in n: return (220, 120, 160)
    if 'grass' in n or 'fern' in n or 'bush' in n: return (80, 140, 45)
    h = abs(hash(n)) % 60; return (120 + h, 120 + h // 2, 120)

def render(blocks, path_top, path_iso, scale_iso=2):
    """blocks: dict (x,y,z)->(name,data)"""
    P = np.array(list(blocks.keys())); x0, y0, z0 = P.min(0); x1, y1, z1 = P.max(0)
    W, H = x1 - x0 + 1, z1 - z0 + 1
    top = np.zeros((H, W, 3), np.uint8); topy = np.full((H, W), -10**9)
    for (x, y, z), (n, d) in blocks.items():
        c = color(n, d)
        if c is None: continue
        if y > topy[z - z0, x - x0]:
            topy[z - z0, x - x0] = y; top[z - z0, x - x0] = c
    shade = np.clip((topy - y0) / max(1, (y1 - y0)), 0, 1)[..., None] * 0.55 + 0.45
    img = (top * shade).astype(np.uint8); img[topy < -10**8] = (18, 20, 28)
    Image.fromarray(img).resize((W * 3, H * 3), Image.NEAREST).save(path_top)
    # isometric: screen u = x - z, v = (x + z)/2 - y ; draw in order of increasing (x + z + y)
    keys = sorted(blocks.keys(), key=lambda p: (p[0] + p[2], p[1]))
    s = scale_iso
    U = [(x - z) for x, y, z in keys]; V = [((x + z) - 2 * y) for x, y, z in keys]
    umin, umax, vmin, vmax = min(U), max(U), min(V), max(V)
    Wi, Hi = (umax - umin + 4) * s, (vmax - vmin + 8) * s
    im = np.zeros((Hi, Wi, 3), np.uint8); im[:] = (18, 20, 28)
    for (x, y, z), u, v in zip(keys, U, V):
        n, d = blocks[(x, y, z)]; c = color(n, d)
        if c is None: continue
        px, py = (u - umin) * s, (v - vmin) * s
        c = np.array(c, float)
        im[py:py + s, px:px + 2 * s] = (c * 1.0).clip(0, 255)            # top face
        im[py + s:py + 3 * s, px:px + s] = (c * 0.72).clip(0, 255)       # left face
        im[py + s:py + 3 * s, px + s:px + 2 * s] = (c * 0.55).clip(0, 255)  # right face
    Image.fromarray(im).save(path_iso)
