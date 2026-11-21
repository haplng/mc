"""Package the datapack into a ready-to-play 26.3 world folder (formats copied from a known-good 26.3 save)."""
import os, shutil, time, zipfile, nbtlib
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
from nbtlib import String, Long, Int, Float, IntArray, List, Byte
from PIL import Image, ImageDraw, ImageFont

REF = ROOT + '/template'
PACK = ROOT + '/out/eokka'
OUT = _os.environ.get('EK_OUT') or ROOT + '/world'
NAME = '스티브 억까 시뮬레이터'
README = """Generator for the map datapack (Minecraft Java 26.3).

gen/build.py    writes the datapack and checks every command against the 26.3 command tree
                (needs the command tree, registries and blocks json of 26.3 in ref/)
gen/world.py    packs it into a world folder
gen/v2.py       aiming and throwing, the mount, Steve's distractions, lucky boxes, stage twists, the HUD line

The tests run against a real 26.3 dedicated server (tools/rcon.py, tools/live.py):
tools/deploy.py     zip the pack into the test world and /reload it, print what the server complains about
tools/livecards.py  use every card in every beat of every stage (needs the small helper pack "ekt" in the test world)
tools/livev2.py     distractions, noticing falling objects, stage twists, the sniping bonus
tools/botv2.py      a fake protocol player: mount, zoom, the look-at cursor, throws, lucky boxes, relog
tools/liveplay.py   a scripted 'decent player' that plays whole runs, to see how far a run goes with the current balance
tools/sim.py, playtest.py, batch.py, cardtest.py are the older offline interpreter tests; they do not know the aiming rules.

26.3 notes that cost time:
* loot conditions (also inline in "execute if predicate {...}") use the key "type", not "condition";
  the player sub-predicate is written {"minecraft:type_specific/player":{input:{sneak:true}}}
* block states in entity NBT are {id:..,properties:..} or a plain string, not {Name:..}
* a predicate FILE that fails to parse stops the whole world from loading, so the pack ships none
* the visible ender dragon must not be NoAI (it would not follow teleports on the client); logic moves the ek.dragon marker
* a mount is only steerable when it is tamed and wears something in the saddle slot
"""

def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT + '/data/minecraft'); os.makedirs(OUT + '/datapacks')
    f = nbtlib.load(REF + '/level.dat')
    d = f['Data']
    d['LevelName'] = String(NAME); d['Time'] = Long(0); d['LastPlayed'] = Long(int(time.time() * 1000))
    d['spawn']['pos'] = IntArray([0, 57, 26]); d['spawn']['yaw'] = Float(180.0); d['spawn']['pitch'] = Float(25.0)
    d['DataPacks']['Enabled'] = List[String]([String('vanilla'), String('file/eokka.zip')])
    d['difficulty_settings']['difficulty'] = String('normal'); d['GameType'] = Int(2); d['allowCommands'] = Byte(1)
    f.save(OUT + '/level.dat', gzipped=True)
    for name in ('world_gen_settings.dat', 'world_clocks.dat', 'weather.dat'):
        shutil.copy(f'{REF}/data/minecraft/{name}', f'{OUT}/data/minecraft/{name}')
    g = nbtlib.load(REF + '/data/minecraft/game_rules.dat')
    rules = g['data']
    for k, v in {'spawn_mobs': 0, 'spawn_monsters': 0, 'mob_griefing': 0, 'block_drops': 0, 'mob_drops': 0, 'entity_drops': 0, 'fall_damage': 0,
                 'fire_damage': 0, 'drowning_damage': 0, 'advance_time': 0, 'advance_weather': 0, 'keep_inventory': 1, 'spawner_blocks_work': 0,
                 'send_command_feedback': 0, 'show_death_messages': 0, 'show_advancement_messages': 0, 'locator_bar': 0, 'immediate_respawn': 1}.items():
        assert 'minecraft:' + k in rules, k
        rules['minecraft:' + k] = Byte(v)
    for k, v in {'random_tick_speed': 0, 'max_command_sequence_length': 1000000, 'max_block_modifications': 100000, 'fire_spread_radius_around_player': 0}.items():
        assert 'minecraft:' + k in rules, k
        rules['minecraft:' + k] = Int(v)
    g.save(OUT + '/data/minecraft/game_rules.dat', gzipped=True)
    with zipfile.ZipFile(OUT + '/datapacks/eokka.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(PACK):
            for fn in sorted(fs):
                full = os.path.join(dp, fn); z.write(full, os.path.relpath(full, PACK).replace(os.sep, '/'))
    os.makedirs(OUT + '/_source')
    with zipfile.ZipFile(OUT + '/_source/eokka_generator.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for sub in ('gen', 'tools'):
            for fn in sorted(os.listdir(ROOT + '/' + sub)):
                if fn.endswith('.py'): z.write(f'{ROOT}/{sub}/{fn}', f'{sub}/{fn}')
        z.writestr('README.txt', README)
    # icon: storm cloud + lightning over a little grass block, with the title word
    S = 256
    im = Image.new('RGB', (S, S), (24, 28, 54)); dr = ImageDraw.Draw(im)
    for i in range(S): dr.line([(0, i), (S, i)], fill=(24 + i // 10, 28 + i // 8, 54 + i // 5))
    dr.rectangle([48, 176, 208, 256], fill=(121, 85, 58)); dr.rectangle([48, 160, 208, 184], fill=(96, 168, 72))
    for cx, cy, r in ((90, 70, 40), (140, 56, 48), (188, 76, 36), (120, 88, 40), (160, 90, 38)):
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 74, 96))
    dr.polygon([(142, 96), (104, 150), (128, 150), (112, 196), (170, 132), (142, 132), (160, 96)], fill=(255, 221, 64))
    try:
        font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc', 64, index=1)
        dr.text((S // 2, 222), '억까', font=font, fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=(180, 30, 30))
    except Exception as ex:
        print('font skipped:', ex)
    im.resize((64, 64), Image.LANCZOS).save(OUT + '/icon.png')
    # verify what we wrote
    chk = nbtlib.load(OUT + '/level.dat')['Data']
    print('level:', chk['LevelName'], dict(chk['spawn']), list(chk['DataPacks']['Enabled']), chk['Version']['Name'], 'DataVersion', chk['DataVersion'])
    with zipfile.ZipFile(OUT + '/datapacks/eokka.zip') as z:
        names = z.namelist()
        print('zip:', len(names), 'files,', os.path.getsize(OUT + '/datapacks/eokka.zip'), 'bytes; has pack.mcmeta:', 'pack.mcmeta' in names,
              '; load tag:', z.read('data/minecraft/tags/function/load.json').decode(), '; mcmeta:', z.read('pack.mcmeta').decode())
    for dp, _, fs in os.walk(OUT):
        for fn in fs: print('  ', os.path.relpath(os.path.join(dp, fn), OUT), os.path.getsize(os.path.join(dp, fn)))

if __name__ == '__main__':
    main()
