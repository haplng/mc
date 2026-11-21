"""Preview pictures of a canvas (isometric and top-down)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import render

OVER = {'smooth_quartz': (236, 231, 224), 'quartz_bricks': (232, 226, 218), 'quartz_pillar': (230, 224, 215), 'chiseled_quartz_block': (228, 222, 213),
        'bone_block': (226, 221, 200), 'white_concrete': (207, 213, 214), 'calcite': (223, 224, 220), 'honeycomb_block': (229, 148, 29),
        'shroomlight': (241, 150, 72), 'glowstone': (250, 210, 120), 'sea_lantern': (190, 215, 208), 'ochre_froglight': (250, 240, 190),
        'pearlescent_froglight': (245, 230, 240), 'verdant_froglight': (225, 245, 220), 'dark_prismarine': (51, 91, 75), 'prismarine_bricks': (99, 171, 158),
        'smooth_stone': (158, 158, 158), 'bricks': (150, 97, 83), 'mud_bricks': (137, 104, 79), 'hay_block': (166, 136, 38), 'bookshelf': (130, 100, 60),
        'chiseled_bookshelf': (140, 105, 65), 'target': (226, 170, 158), 'tnt': (200, 60, 50), 'sponge': (195, 192, 74), 'slime_block': (112, 192, 91),
        'melon': (111, 145, 30), 'dried_kelp_block': (50, 58, 38), 'amethyst_block': (133, 97, 191), 'budding_amethyst': (132, 96, 186),
        'purpur_block': (170, 126, 170), 'obsidian': (15, 10, 24), 'crying_obsidian': (32, 10, 60), 'netherite_block': (66, 61, 63),
        'raw_gold_block': (221, 169, 46), 'raw_copper_block': (154, 105, 79), 'raw_iron_block': (166, 135, 107), 'copper_block': (192, 107, 79),
        'cut_copper': (191, 106, 80), 'oxidized_copper': (82, 162, 132), 'weathered_copper': (108, 153, 110), 'exposed_copper': (161, 125, 103),
        'packed_ice': (141, 180, 250), 'blue_ice': (116, 167, 253), 'ice': (145, 183, 253), 'snow_block': (249, 254, 254), 'powder_snow': (248, 253, 253),
        'smooth_sandstone': (223, 214, 170), 'cut_sandstone': (217, 206, 159), 'smooth_red_sandstone': (181, 97, 31), 'cut_red_sandstone': (189, 101, 31),
        'tuff': (108, 109, 102), 'tuff_bricks': (98, 102, 95), 'polished_tuff': (97, 104, 99), 'dripstone_block': (134, 107, 92),
        'rooted_dirt': (144, 103, 76), 'mud': (60, 57, 60), 'packed_mud': (142, 106, 79), 'moss_block': (89, 109, 45), 'water': (56, 100, 220),
        'cobbled_deepslate': (77, 77, 80), 'deepslate': (80, 80, 82), 'polished_deepslate': (72, 72, 73), 'deepslate_bricks': (70, 70, 71),
        'deepslate_tiles': (54, 54, 55), 'polished_blackstone': (53, 48, 56), 'polished_blackstone_bricks': (48, 42, 49), 'blackstone': (42, 35, 40),
        'gilded_blackstone': (85, 62, 38), 'basalt': (73, 72, 77), 'smooth_basalt': (72, 72, 78), 'polished_basalt': (88, 88, 91),
        'iron_block': (220, 220, 220), 'gold_block': (246, 208, 61), 'diamond_block': (98, 237, 228), 'emerald_block': (42, 203, 87),
        'lapis_block': (30, 67, 140), 'redstone_block': (175, 24, 5), 'coal_block': (16, 15, 15), 'bamboo_block': (127, 144, 57),
        'stripped_bamboo_block': (193, 173, 80), 'bamboo_planks': (193, 173, 80), 'bamboo_mosaic': (190, 170, 78), 'jungle_planks': (160, 115, 80),
        'stripped_oak_log': (177, 144, 86), 'stripped_oak_wood': (177, 144, 86), 'stripped_birch_log': (196, 176, 118), 'stripped_birch_wood': (196, 176, 118),
        'stripped_spruce_log': (115, 89, 52), 'stripped_spruce_wood': (115, 89, 52), 'stripped_dark_oak_log': (72, 56, 36), 'stripped_dark_oak_wood': (72, 56, 36),
        'stripped_jungle_log': (171, 132, 84), 'stripped_jungle_wood': (171, 132, 84), 'stripped_cherry_log': (215, 145, 148), 'stripped_cherry_wood': (215, 145, 148),
        'stripped_acacia_log': (174, 92, 59), 'stripped_mangrove_log': (119, 54, 47), 'mangrove_planks': (117, 54, 48), 'cherry_planks': (226, 178, 172),
        'dark_oak_planks': (66, 43, 20), 'spruce_planks': (114, 84, 48), 'birch_planks': (192, 175, 121), 'oak_planks': (162, 130, 78),
        'acacia_planks': (168, 90, 50), 'crimson_planks': (101, 48, 70), 'warped_planks': (43, 104, 99), 'pale_oak_planks': (227, 217, 216),
        'barrel': (130, 95, 55), 'crafting_table': (130, 100, 60), 'smithing_table': (60, 62, 72), 'loom': (150, 120, 90), 'lectern': (160, 125, 75),
        'chest': (160, 110, 40), 'ender_chest': (20, 60, 70), 'end_rod': (240, 240, 230), 'campfire': (220, 140, 50), 'cauldron': (70, 70, 72),
        'beacon': (120, 220, 215), 'jukebox': (110, 70, 50), 'note_block': (100, 65, 45), 'daylight_detector': (130, 115, 95), 'observer': (100, 100, 100),
        'red_nether_bricks': (70, 7, 9), 'nether_bricks': (44, 21, 26), 'end_stone': (219, 222, 158), 'end_stone_bricks': (218, 224, 162),
        'white_tulip': (220, 225, 215), 'red_tulip': (200, 40, 30), 'orange_tulip': (230, 130, 35), 'pink_tulip': (235, 170, 205), 'allium': (180, 110, 220),
        'cornflower': (70, 110, 220), 'blue_orchid': (40, 170, 240), 'dandelion': (245, 220, 50), 'poppy': (210, 40, 35), 'oxeye_daisy': (230, 230, 220),
        'azure_bluet': (225, 230, 235), 'lily_of_the_valley': (235, 240, 235), 'short_grass': (95, 150, 55), 'fern': (85, 140, 55), 'tall_grass': (95, 150, 55),
        'sunflower': (245, 200, 40), 'rose_bush': (190, 40, 50), 'peony': (235, 180, 215), 'lilac': (190, 150, 210), 'pink_petals': (240, 170, 205),
        'wildflowers': (240, 220, 120), 'tube_coral_block': (48, 87, 206), 'brain_coral_block': (207, 91, 159), 'bubble_coral_block': (165, 26, 162),
        'fire_coral_block': (163, 35, 46), 'horn_coral_block': (216, 199, 66), 'sea_pickle': (140, 160, 60), 'wet_sponge': (170, 180, 70),
        'iron_bars': (150, 150, 150), 'iron_chain': (70, 75, 90), 'rail': (140, 120, 95), 'powered_rail': (170, 130, 60), 'ladder': (140, 110, 60),
        'glass': (200, 230, 235), 'tinted_glass': (50, 40, 55), 'bell': (250, 210, 70), 'lodestone': (150, 150, 155), 'resin_block': (220, 100, 30),
        'resin_bricks': (205, 88, 24), 'farmland': (110, 75, 45), 'dirt_path': (148, 122, 65), 'cobweb': (225, 230, 235), 'cake': (240, 230, 220),
        'white_candle': (225, 225, 215), 'candle': (230, 200, 150), 'red_candle': (190, 50, 40), 'torch': (255, 220, 100), 'lantern': (250, 200, 110),
        'soul_lantern': (110, 220, 230), 'copper_lantern': (240, 170, 110), 'smooth_stone_slab': (158, 158, 158), 'stone': (125, 125, 125),
        'andesite': (136, 136, 137), 'polished_andesite': (132, 135, 134), 'diorite': (189, 188, 189), 'polished_diorite': (193, 193, 195),
        'granite': (149, 103, 86), 'polished_granite': (154, 107, 89), 'grass_block': (95, 159, 53), 'mycelium': (111, 99, 105), 'podzol': (92, 63, 24),
        'sand': (219, 207, 163), 'red_sand': (190, 102, 33), 'gravel': (131, 127, 126), 'clay': (160, 166, 179), 'sandstone': (216, 203, 155),
        'chiseled_sandstone': (216, 203, 155), 'stone_bricks': (122, 121, 122), 'mossy_stone_bricks': (115, 121, 105), 'cracked_stone_bricks': (118, 117, 118),
        'chiseled_stone_bricks': (120, 119, 120), 'cobblestone': (127, 127, 127), 'mossy_cobblestone': (110, 118, 95), 'terracotta': (152, 94, 68),
        'magma_block': (142, 63, 32), 'jack_o_lantern': (215, 152, 53), 'pumpkin': (198, 118, 24), 'redstone_lamp': (95, 55, 30), 'copper_bulb': (156, 87, 57),
        'nether_wart_block': (115, 3, 2), 'warped_wart_block': (22, 119, 121), 'purpur_pillar': (171, 129, 171), 'prismarine': (99, 156, 151)}
TERRA = {'white': (210, 178, 161), 'orange': (162, 84, 38), 'magenta': (150, 88, 109), 'light_blue': (113, 109, 138), 'yellow': (186, 133, 35),
         'lime': (104, 118, 53), 'pink': (162, 78, 79), 'gray': (58, 42, 36), 'light_gray': (135, 107, 98), 'cyan': (87, 91, 91), 'purple': (118, 70, 86),
         'blue': (74, 60, 91), 'brown': (77, 51, 36), 'green': (76, 83, 42), 'red': (143, 61, 47), 'black': (37, 23, 16)}
CONC = {'white': (207, 213, 214), 'orange': (224, 97, 1), 'magenta': (169, 48, 159), 'light_blue': (36, 137, 199), 'yellow': (241, 175, 21),
        'lime': (94, 169, 24), 'pink': (214, 101, 143), 'gray': (55, 58, 62), 'light_gray': (125, 125, 115), 'cyan': (21, 119, 136), 'purple': (100, 32, 156),
        'blue': (45, 47, 143), 'brown': (96, 60, 32), 'green': (73, 91, 36), 'red': (142, 33, 33), 'black': (8, 10, 15)}
_c = {}
def colour(n):
    if n in _c: return _c[n]
    c = None
    if n in OVER: c = OVER[n]
    else:
        for suf, tab in (('_terracotta', TERRA), ('_concrete', CONC)):
            if n.endswith(suf) and n[:-len(suf)] in tab: c = tab[n[:-len(suf)]]
        if c is None:
            for suf in ('_stairs', '_slab', '_wall', '_fence', '_fence_gate', '_trapdoor', '_door', '_pressure_plate', '_button'):
                if n.endswith(suf):
                    b = n[:-len(suf)]
                    for cand in (b, b + 's', b + '_planks', b + '_block'):
                        if cand in OVER: c = OVER[cand]; break
                    if c is None:
                        for s2, tab in (('_terracotta', TERRA), ('_concrete', CONC)):
                            if b.endswith(s2) and b[:-len(s2)] in tab: c = tab[b[:-len(s2)]]
                    break
        if c is None: c = render.color(n, 0)
    _c[n] = c
    return c

def arrays(cv, skip=('barrier', 'light', 'structure_void')):
    P = []; C = []
    for (x, y, z), s in cv.b.items():
        n = s.split('[')[0].replace('minecraft:', '')
        if n in skip: continue
        c = colour(n)
        if c is None: continue
        P.append((x, y, z)); C.append(c)
    return np.array(P, np.int64), np.array(C, np.float32)

def top(cv, s=2, bg=(18, 20, 28)):
    P, C = arrays(cv)
    x0, y0, z0 = P.min(0); x1, y1, z1 = P.max(0); W, H = x1 - x0 + 1, z1 - z0 + 1
    order = np.argsort(P[:, 1], kind='stable')
    px = P[order, 0] - x0; pz = P[order, 2] - z0
    img = np.zeros((H, W, 3), np.float32); img[:] = bg; hy = np.full((H, W), -1e9, np.float32)
    img[pz, px] = C[order]; hy[pz, px] = P[order, 1]
    sh = np.clip((hy - y0) / max(1, (y1 - y0)), 0, 1)[..., None] * 0.5 + 0.5
    img = np.where(hy[..., None] > -1e8, img * sh, img)
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    return im.resize((W * s, H * s), Image.NEAREST) if s != 1 else im

def side_by_side(ims, pad=8, bg=(18, 20, 28)):
    H = max(i.height for i in ims); W = sum(i.width for i in ims) + pad * (len(ims) - 1)
    S = Image.new('RGB', (W, H), bg); x = 0
    for i in ims: S.paste(i, (x, (H - i.height) // 2)); x += i.width + pad
    return S

def fit(im, maxw=1500, maxh=1100):
    sc = min(maxw / im.width, maxh / im.height, 1.0)
    return im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS) if sc < 1 else im

def iso2(cv, s=4, rot=0, yk=2.5, bg=(18, 20, 28)):
    """isometric picture with a depth buffer; yk = screen units per block of height (3 = low camera, 2 = high camera)"""
    P, C = arrays(cv)
    x = P[:, 0].copy(); y = P[:, 1].copy(); z = P[:, 2].copy()
    for _ in range(rot % 4): x, z = -z, x
    order = np.lexsort((y, x + z))
    x, y, z = x[order], y[order], z[order]; C = C[order]
    u = x - z; v = x + z - yk * y
    u = u - u.min(); v = v - v.min()
    sh_ = int(round(yk * s)); v = (x + z) * s - y * sh_; v = v - v.min()
    W = int((u.max() + 2) * s); H = int(v.max() + sh_ + s + 1)
    base = v * W + u * s; rank = np.arange(len(x), dtype=np.int64)
    rb = np.full(W * H, -1, np.int64)
    groups = [([(dx, dy) for dy in range(s) for dx in range(2 * s)], 1.0),
              ([(dx, dy) for dy in range(s, s + sh_) for dx in range(s)], 0.74),
              ([(dx, dy) for dy in range(s, s + sh_) for dx in range(s, 2 * s)], 0.55)]
    for offs, _ in groups:
        for dx, dy in offs:
            idx = base + dy * W + dx; rb[idx] = np.maximum(rb[idx], rank)
    img = np.zeros((W * H, 3), np.uint8); img[:] = bg
    for offs, sh in groups:
        col = (C * sh).clip(0, 255).astype(np.uint8)
        for dx, dy in offs:
            idx = base + dy * W + dx; m = rb[idx] == rank; img[idx[m]] = col[m]
    return Image.fromarray(img.reshape(H, W, 3))

def iso(cv, s=2, rot=0): return iso2(cv, s, rot, yk=2)
