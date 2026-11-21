"""Map 4 - 기차: steam locomotives on broken viaducts round a square loop of railway with four stations and a turntable."""
import math
from canvas import Canvas
from kit import *

ID = 'train'; NAME = '기차'
GATE = dict(frame='stone_bricks', roof_full='spruce_planks', plaza='polished_andesite', glass='light_gray_stained_glass')
STONE = [('stone_bricks', 7), ('cracked_stone_bricks', 1), ('andesite', 1), ('mossy_stone_bricks', 1)]
ARCH = {2: 3, 3: 2, 4: 1, 5: 1, 6: 1, 7: 1, 8: 2, 9: 3}

def column(cv, x, z, t, deep=9):
    """the stonework under one deck cell of a viaduct (t = position along the track)"""
    cv.set(x, -1, z, 'stone_bricks')
    d = deep if t % 10 in (0, 1) else ARCH[t % 10]
    for i in range(d): cv.set(x, -2 - i, z, cv.pick(STONE))
    if t % 10 in (0, 1): cv.set(x, -2 - d, z, 'stone_brick_wall') if False else None

def track(cv, x, z, along, t, k=0):
    """one cell of the ballasted track bed (rails are laid by the caller)"""
    cv.set(x, 0, z, 'spruce_planks' if t % 2 == 0 else 'gravel')

def loco(dye):
    cv = Canvas(sum(map(ord, dye)) + 4)
    BK = 'polished_deepslate'; PB = 'polished_blackstone'; T = dye + '_concrete'
    if dye == 'gray': BK = 'smooth_basalt'
    box(cv, -2, 1, -12, 2, 4, 4, 'blackstone'); box(cv, -2, 5, -12, 2, 5, 4, PB)
    for sx in (-3, 3):
        for wz in (-9, -4, 1):
            vdisc(cv, sx, 3, wz, 2, PB, axis='x'); cv.set(sx, 3, wz, T)
        for z in range(-9, 2): cv.set(sx + (1 if sx > 0 else -1), 3, z, 'iron_bars') if False else None
    for z in range(-6, 4):                                             # boiler
        vdisc(cv, 0, 8, z, 2.6, T if z in (-4, 0) else BK, axis='z')
    vdisc(cv, 0, 8, 4, 2.6, 'gray_concrete', axis='z'); vdisc(cv, 0, 8, 4, 1, 'light_gray_concrete', axis='z'); cv.set(0, 8, 5, 'iron_block')
    cv.set(0, 11, 3, 'sea_lantern')
    for x in range(-3, 4):                                             # buffer beam and cowcatcher
        cv.set(x, 2, 5, T); cv.set(x, 1, 5, T)
        if abs(x) <= 2: cv.set(x, 1, 6, T)
    cv.set(0, 11, 1, PB); cv.set(0, 12, 1, PB); cv.set(0, 13, 1, 'campfire[lit=true]')
    cv.set(0, 11, -2, 'gold_block'); cv.set(0, 11, -5, 'end_rod[facing=up]')
    # cab
    box(cv, -3, 6, -12, 3, 11, -7, T, hollow=True); box(cv, -2, 6, -11, 2, 11, -8, None)
    box(cv, -3, 12, -13, 3, 12, -6, PB)
    for x in (-1, 0, 1):
        for y in (6, 7, 8, 9): cv.set(x, y, -12, None)
    for sx in (-3, 3):
        for z in (-10, -9):
            for y in (8, 9): cv.set(sx, y, z, 'glass')
    for x in (-2, 2): cv.set(x, 9, -7, 'glass'); cv.set(x, 10, -7, 'glass')
    cv.set(0, 6, -8, 'blast_furnace[facing=north,lit=true]'); cv.set(-2, 6, -8, 'coal_block'); cv.set(2, 6, -8, 'barrel[facing=up]')
    cv.set(0, 11, -9, 'lantern[hanging=true]')
    for y in range(1, 6): cv.set(0, y, -13, 'ladder[facing=north]')
    return cv

def wagon(kind):
    cv = Canvas(80 + kind)
    box(cv, -1, 1, -4, 1, 1, 3, 'blackstone'); box(cv, -2, 2, -4, 2, 2, 3, 'spruce_planks')
    for sx in (-2, 2):
        for wz in (-3, 2): cv.set(sx, 1, wz, 'polished_blackstone')
    if kind % 4 == 0:                                                  # coal
        box(cv, -2, 3, -4, 2, 4, 3, 'dark_oak_planks', hollow=True); box(cv, -1, 3, -3, 1, 4, 2, 'coal_block'); cv.set(0, 5, 0, 'coal_block'); cv.set(0, 5, -1, 'coal_block')
    elif kind % 4 == 1:                                                # box car
        box(cv, -2, 3, -4, 2, 5, 3, 'mangrove_planks'); box(cv, -2, 6, -4, 2, 6, 3, 'spruce_slab[type=bottom]')
        for y in (3, 4): cv.set(-2, y, 0, 'dark_oak_planks'); cv.set(2, y, 0, 'dark_oak_planks'); cv.set(-2, y, -1, 'dark_oak_planks'); cv.set(2, y, -1, 'dark_oak_planks')
    elif kind % 4 == 2:                                                # logs
        for z in (-4, 3):
            for sx in (-2, 2): cv.set(sx, 3, z, 'spruce_fence'); cv.set(sx, 4, z, 'spruce_fence')
        for x in (-1, 0, 1):
            for z in range(-4, 4): cv.set(x, 3, z, 'oak_log[axis=z]')
        for x in (-1, 0):
            for z in range(-4, 4): cv.set(x, 4, z, 'spruce_log[axis=z]')
    else:                                                              # tank
        for z in range(-3, 3): vdisc(cv, 0, 4, z, 1.6, 'light_gray_concrete' if z not in (-3, 2) else 'gray_concrete', axis='z')
        cv.set(0, 6, 0, 'iron_block')
    return cv

def loco_base(dye):
    cv = Canvas(sum(map(ord, dye)) + 14)
    T = dye + '_concrete'
    for x in range(-10, 11):
        for z in range(-15, 15):
            t = z + 15
            if z >= 13: t = 0
            column(cv, x, z, t)
            cv.set(x, 0, z, 'polished_andesite' if (abs(x) == 10 or z in (-15, 14)) else cv.pick(STONE))
    for z in range(-15, 15):                                           # track on the right half
        for x in range(3, 8): cv.set(x, 0, z, 'spruce_planks' if z % 2 == 0 else 'gravel')
        if z > 6 or z < -13:
            cv.set(4, 1, z, 'rail[shape=north_south]'); cv.set(6, 1, z, 'rail[shape=north_south]')
        cv.set(1, 0, z, 'yellow_concrete')
    cv.paste(loco(dye), 5, 0, 0)
    for z in (-13, -5, 3, 10):                                         # lamps under the arches
        pass
    # station canopy on the left half
    for z in (-14, -8, -2):
        for x in (-9, -1):
            for y in range(1, 5): cv.set(x, y, z, 'spruce_fence')
    box(cv, -10, 5, -15, 0, 5, -1, 'spruce_planks')
    for x in range(-10, 1):
        cv.set(x, 5, -15, 'spruce_stairs[facing=south,half=bottom]'); cv.set(x, 5, -1, 'spruce_stairs[facing=north,half=bottom]')
    for z in range(-14, -1):
        cv.set(-10, 5, z, dye + '_wool'); cv.set(0, 5, z, dye + '_wool')
    box(cv, -8, 6, -13, -2, 6, -3, 'spruce_slab[type=bottom]')
    for z in (-11, -5): hang_lamp(cv, -5, 4, z)
    gen_pad(cv, -5, 0, -10, 'iron', frame='polished_andesite')
    cv.set(-9, 1, -11, 'chest[facing=east]'); cv.set(-9, 1, -9, 'ender_chest[facing=east]')
    for z in (-6, -5, -4): cv.set(-9, 1, z, 'spruce_stairs[facing=west,half=bottom]')
    cv.set(-9, 1, -13, 'barrel[facing=up]'); cv.set(-8, 1, -13, 'barrel[facing=up]'); cv.set(-9, 2, -13, 'lantern[hanging=false]')
    # signal post, luggage, stalls
    for y in range(1, 6): cv.set(9, y, 9, 'polished_blackstone_wall')
    cv.set(9, 6, 9, 'redstone_block'); cv.set(9, 7, 9, 'emerald_block') if False else cv.set(9, 7, 9, 'lime_concrete')
    crates(cv, -9, 1, 11, 4)
    stall(cv, -6, 1, 4, 3, 'white', dye); stall(cv, 0, 1, 4, 2, 'white', dye) if False else None
    stall(cv, -6, 1, 9, 3, 'light_gray', dye)
    bed(cv, dye, 0, 1, 10)
    team_markers(cv, dye, spawn=(-5, 1, -5), bedpos=(0, 1, 10), gen=(-5, 0, -10), shop=(-6, 1, 4), upg=(-6, 1, 9))
    return cv

def station(i):
    """a platform with a small station house; local -x is the track side"""
    cv = Canvas(90 + i)
    BR = [('bricks', 6), ('granite', 1), ('polished_granite', 1)]
    for x in range(0, 10):
        for z in range(-10, 11):
            column(cv, x, z, z + 10 if abs(z) < 9 else 0)
            cv.set(x, 0, z, 'polished_andesite' if (x == 9 or abs(z) == 10) else 'smooth_stone')
    for z in range(-10, 11): cv.set(0, 0, z, 'yellow_concrete')
    box(cv, 4, 1, -7, 9, 4, 7, BR, hollow=True); box(cv, 5, 1, -6, 8, 4, 6, None)
    for z in range(-8, 9):                                             # gabled roof, ridge along z
        for j, x in enumerate((3, 4, 5)):
            cv.set(x, 5 + j, z, 'dark_oak_stairs[facing=east,half=bottom]'); cv.set(13 - x, 5 + j, z, 'dark_oak_stairs[facing=west,half=bottom]')
        cv.set(6, 7, z, 'dark_oak_slab[type=top]') if False else cv.set(6, 8, z, 'dark_oak_slab[type=bottom]'); cv.set(7, 8, z, 'dark_oak_slab[type=bottom]')
    for z in (-7, 7):
        for x, top in ((4, 5), (5, 6), (6, 7), (7, 7), (8, 6), (9, 5)):
            for y in range(5, top + 1): cv.set(x, y, z, cv.pick(BR))
    for z in (-1, 0, 1):
        for y in (1, 2, 3): cv.set(4, y, z, None)
    for z in (-5, -4, 4, 5):
        for y in (2, 3): cv.set(4, y, z, 'glass'); cv.set(9, y, z, 'glass')
    for z in (-6, -5, -4): cv.set(8, 1, z, 'spruce_stairs[facing=east,half=bottom]')
    cv.set(8, 1, 5, 'barrel[facing=up]'); cv.set(8, 1, 6, 'barrel[facing=up]'); cv.set(8, 2, 6, 'lantern[hanging=false]'); cv.set(7, 1, 6, 'crafting_table')
    cv.set(8, 1, 0, 'spruce_fence'); cv.set(8, 2, 0, 'spruce_pressure_plate')
    for z in (-3, 3): hang_lamp(cv, 6, 4, z) if False else None
    for z in range(-5, 6):
        for x in (5, 6, 7): cv.set(x, 0, z, 'spruce_planks')
    cv.set(6, 1, 0, 'red_carpet'); cv.set(6, 1, -1, 'red_carpet'); cv.set(6, 1, 1, 'red_carpet')
    for z in (-9, 9): post_lamp(cv, 2, 1, z, 'polished_blackstone_wall', 'lantern', 3)
    gen_pad(cv, 2, 0, 0, 'diamond', frame='smooth_stone'); gem_marker(cv, 2, 0, 0, 'diamond')
    return cv

def water_tower(i):
    cv = Canvas(95 + i)
    for x in range(0, 7):
        for z in range(0, 7):
            column(cv, x, z, 0, deep=7); cv.set(x, 0, z, 'polished_andesite' if (x == 6 or z == 6) else 'smooth_stone')
    for x in (1, 5):
        for z in (1, 5):
            for y in range(1, 6): cv.set(x, y, z, 'spruce_fence')
    cyl(cv, 3, 6, 9, 3, 3, lambda x, y, z: 'dark_oak_planks' if y in (6, 9) else 'spruce_planks')
    cone(cv, 3, 10, 3, 3.6, 3, 'dark_oak_planks'); cv.set(3, 13, 3, 'lightning_rod[facing=up]')
    for y in range(3, 6): cv.set(3, y, 3, 'iron_chain[axis=y]')
    return cv

def ring():
    cv = Canvas(44)
    for x in range(-44, 45):
        for z in range(-44, 45):
            m = max(abs(x), abs(z))
            if m < 38: continue
            corner = min(abs(x), abs(z)) >= 36
            t = (z if abs(x) >= 38 else x) + 45
            column(cv, x, z, 0 if corner else t, deep=9)
            cv.set(x, 0, z, 'polished_andesite' if m in (38, 44) else ('spruce_planks' if (t % 2 == 0 and not corner) else 'gravel'))
    for r in (40, 42):                                                 # two rails all the way round
        for i in range(-r + 1, r):
            cv.set(r, 1, i, 'rail[shape=north_south]'); cv.set(-r, 1, i, 'rail[shape=north_south]')
            cv.set(i, 1, r, 'rail[shape=east_west]'); cv.set(i, 1, -r, 'rail[shape=east_west]')
        cv.set(r, 1, r, 'rail[shape=north_west]'); cv.set(-r, 1, r, 'rail[shape=north_east]')
        cv.set(r, 1, -r, 'rail[shape=south_west]'); cv.set(-r, 1, -r, 'rail[shape=south_east]')
    for k in range(4):                                                 # parked wagons
        for j, off in enumerate((-26, 24)):
            w = wagon(k * 2 + j); x, z = rot_xz(41, off, k)
            for (wx, wy, wz) in list(w.b):
                pass
            # rails under the wagon come away so that nothing floats inside it
            for d in range(-4, 4):
                for r in (40, 42):
                    rx, rz = rot_xz(r, off + d, k); cv.set(rx, 1, rz, None)
            cv.paste(w, x, 0, z, k)
    return cv

def turntable():
    cv = Canvas(45)
    disc(cv, 0, 0, 0, 13, STONE); disc(cv, 0, 0, 0, 13, 'polished_andesite', r_in=12)
    disc(cv, 0, -1, 0, 13, 'stone_bricks'); under_dome(cv, 0, -1, 0, 12, 8, [STONE])
    disc(cv, 0, 0, 0, 9, 'smooth_stone', r_in=8)
    for x in range(-12, 13):
        for z in (-2, -1, 0, 1, 2): cv.set(x, 0, z, 'spruce_planks' if x % 2 == 0 else 'dark_oak_planks')
        if abs(x) > 5: cv.set(x, 1, -1, 'rail[shape=east_west]'); cv.set(x, 1, 1, 'rail[shape=east_west]')
    # a little yellow shunter on the bridge
    box(cv, -4, 1, -1, 4, 2, 1, 'blackstone'); box(cv, -4, 3, -1, 1, 4, 1, 'yellow_concrete'); box(cv, 2, 3, -1, 4, 6, 1, 'yellow_concrete')
    cv.set(3, 5, -1, 'glass'); cv.set(3, 5, 1, 'glass'); cv.set(3, 4, 0, None); cv.set(3, 5, 0, None)
    box(cv, 1, 7, -2, 5, 7, 2, 'black_concrete'); cv.set(-3, 5, 0, 'polished_blackstone'); cv.set(-3, 6, 0, 'campfire[lit=true]'); cv.set(-5, 2, 0, 'sea_lantern')
    for k in range(4):
        x, z = rot_xz(7, 7, k); gen_pad(cv, x, 0, z, 'emerald', frame='smooth_stone'); gem_marker(cv, x, 0, z, 'emerald')
        x, z = rot_xz(11, 4, k); post_lamp(cv, x, 1, z, 'polished_blackstone_wall', 'lantern', 3)
    return cv

def build():
    mb = MapBuilder(404)
    mb.put(turntable(), 0, 0, kind='mid')
    mb.put(ring(), 0, 0, kind='mid')
    for k in range(4):
        x, z = rot_xz(45, 0, k); mb.put(station(k), x, z, k=k, kind='mid')
        x, z = rot_xz(45, 45, k); mb.put(water_tower(k), x, z, k=k, kind='mid')
    spots = []
    for q in range(4):
        for sgn in (-1, 1):
            x, z = rot_xz(88, sgn * 27, q); spots.append((x, z, (q + 1) % 4, sgn > 0))
    mb.bases_at(loco_base, spots)
    return mb
