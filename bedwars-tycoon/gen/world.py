"""Make a fresh void world folder that installs the bed wars lobby and maps on first start."""
import os, sys, shutil, time, json
import nbtlib
from nbtlib import String, Int, Byte, Long, List, Compound, IntArray, Float
from PIL import Image, ImageDraw, ImageFont

ROOT = os.environ.get('BW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.environ.get('BW_TEMPLATE') or os.path.join(ROOT, 'template')     # a 26.3 world's level.dat + data/minecraft/*.dat
NAME = '배드워즈 타이쿤'

def build(out_dir, pack_zip, spawn=(0, 65, 9)):
    w = os.path.join(out_dir, NAME)
    if os.path.isdir(w): shutil.rmtree(w)
    os.makedirs(w + '/data/minecraft'); os.makedirs(w + '/datapacks')
    # level.dat
    lv = nbtlib.load(TEMPLATE + '/level.dat'); d = lv['Data']
    d['LevelName'] = String(NAME); d['LastPlayed'] = Long(int(time.time() * 1000)); d['Time'] = Long(0)
    d['spawn'] = Compound({'pos': IntArray([Int(spawn[0]), Int(spawn[1]), Int(spawn[2])]), 'yaw': Float(180.0), 'pitch': Float(0.0),
                           'dimension': String('minecraft:overworld')})
    d['GameType'] = Int(1); d['allowCommands'] = Byte(1)
    d['DataPacks']['Enabled'] = List[String]([String('vanilla'), String('file/bedwars_maps.zip')])
    lv.save(w + '/level.dat', gzipped=True)
    # void overworld (nether and end as they were)
    g = nbtlib.load(TEMPLATE + '/data/minecraft/world_gen_settings.dat')
    g['data']['dimensions']['minecraft:overworld']['generator'] = Compound({
        'type': String('minecraft:flat'),
        'settings': Compound({'layers': List[Compound]([Compound({'block': String('minecraft:air'), 'height': Int(1)})]),
                              'biome': String('minecraft:the_void'), 'features': Byte(0), 'lakes': Byte(0),
                              'structure_overrides': List[String]([])})})
    g['data']['generate_structures'] = Byte(0)
    g.save(w + '/data/minecraft/world_gen_settings.dat', gzipped=True)
    # game rules: no mobs, no fire spread, no random ticks (the builds stay as built), spawn exactly on the lobby
    r = nbtlib.load(TEMPLATE + '/data/minecraft/game_rules.dat')
    rules = r['data']
    for k, v in {'respawn_radius': 0, 'random_tick_speed': 0, 'fire_spread_radius_around_player': 0}.items():
        assert 'minecraft:' + k in rules, k; rules['minecraft:' + k] = Int(v)
    for k, v in {'spawn_monsters': 0, 'spawn_mobs': 0, 'spawn_phantoms': 0, 'spawn_patrols': 0, 'spawn_wandering_traders': 0,
                 'spawn_wardens': 0, 'advance_time': 0, 'advance_weather': 0, 'mob_griefing': 0, 'keep_inventory': 1}.items():
        assert 'minecraft:' + k in rules, k; rules['minecraft:' + k] = Byte(v)
    r.save(w + '/data/minecraft/game_rules.dat', gzipped=True)
    for f in ('weather.dat', 'world_clocks.dat'):
        if os.path.exists(f'{TEMPLATE}/data/minecraft/{f}'): shutil.copy(f'{TEMPLATE}/data/minecraft/{f}', f'{w}/data/minecraft/{f}')
    if os.path.exists(TEMPLATE + '/lunar_hosted_world_data.json'): shutil.copy(TEMPLATE + '/lunar_hosted_world_data.json', w)
    shutil.copy(pack_zip, w + '/datapacks/bedwars_maps.zip')
    # icon: a red bed on a floating island
    S = 256
    im = Image.new('RGB', (S, S)); dr = ImageDraw.Draw(im)
    for i in range(S): dr.line([(0, i), (S, i)], fill=(40 + i // 6, 60 + i // 5, 120 + i // 4))
    dr.polygon([(40, 150), (216, 150), (180, 210), (128, 245), (76, 210)], fill=(110, 80, 55))
    dr.rectangle([40, 138, 216, 156], fill=(90, 160, 60))
    dr.rectangle([70, 96, 186, 132], fill=(200, 40, 40)); dr.rectangle([70, 96, 104, 132], fill=(240, 240, 240))
    dr.rectangle([70, 132, 80, 140], fill=(120, 85, 50)); dr.rectangle([176, 132, 186, 140], fill=(120, 85, 50))
    try:
        font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc', 46, index=1)
        dr.text((S // 2, 50), 'BED WARS', font=font, fill=(255, 215, 80), anchor='mm', stroke_width=4, stroke_fill=(60, 30, 10))
    except Exception as ex: print('font skipped', ex)
    im.resize((64, 64), Image.LANCZOS).save(w + '/icon.png')
    return w

if __name__ == '__main__':
    print(build(sys.argv[1], sys.argv[2]))
