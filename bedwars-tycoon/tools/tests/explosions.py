# explosions: what was built goes, the map's own blocks of the same kinds come back
import sys, time, re, math; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
ZOFF = int(re.search(r'~(\d+) ~7', open('/tmp/bwout/bedwars_maps/data/bw/function/game/axefix.mcfunction').read()).group(1)) + 7
c('function bw:game/close'); time.sleep(1)
b = join(); c('scoreboard players set tester bw.stage 0')
print('start', start('tea', b), 'state', sc('#state')); time.sleep(1)
c('effect give tester minecraft:resistance infinite 4 true')
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} {blk}')
X, Y, Z = 600, 92, 30
for kind, fn in (('fireball', 'fb/boom'), ('tnt', 'fb/tntboom')):
    c(f'fill {X - 3} {Y - 1} {Z - 3} {X + 3} {Y + 3} {Z + 3} minecraft:air'); c(f'fill {X - 3} {Y - 1} {Z - 3 + ZOFF} {X + 3} {Y + 3} {Z + 3 + ZOFF} minecraft:air')
    # "map": a wool block, planks, end stone and a glass block, the same in the copy
    mapb = {(X + 1, Y, Z): 'white_wool', (X - 1, Y, Z): 'oak_planks', (X, Y, Z + 1): 'end_stone', (X, Y - 1, Z): 'glass', (X, Y, Z - 1): 'stone'}
    for (x, y, z), n in mapb.items(): c(f'setblock {x} {y} {z} minecraft:{n}'); c(f'setblock {x} {y} {z + ZOFF} minecraft:{n}')
    built = {(X + 1, Y + 1, Z): 'red_wool', (X - 1, Y + 1, Z): 'oak_planks', (X, Y + 1, Z + 1): 'end_stone', (X, Y + 1, Z - 1): 'glass', (X + 1, Y, Z + 1): 'obsidian'}
    for (x, y, z), n in built.items(): c(f'setblock {x} {y} {z} minecraft:{n}')
    tag = 'bw.fbm' if kind == 'fireball' else 'bw.tntm'
    c(f'summon minecraft:marker {X + 0.5} {Y + 0.6} {Z + 0.5} {{Tags:["bw","bw.round","{tag}"]}}'); time.sleep(0.8)
    print(kind)
    print('   map blocks  :', {n: ('kept' if is_(x, y, z, 'minecraft:' + n) else 'GONE') for (x, y, z), n in mapb.items()})
    print('   built blocks:', {n: ('still there' if is_(x, y, z, 'minecraft:' + n) else 'gone') for (x, y, z), n in built.items()})
    print('   items lying about:', re.findall(r'id: "minecraft:(\w+)"', c(f'execute as @e[type=item,x={X - 8},y={Y - 8},z={Z - 8},dx=16,dy=16,dz=16] run data get entity @s Item.id')) or c(f'execute if entity @e[type=item,x={X - 8},y={Y - 8},z={Z - 8},dx=16,dy=16,dz=16]')[:12])
    c(f'fill {X - 3} {Y - 1} {Z - 3} {X + 3} {Y + 3} {Z + 3} minecraft:air'); c(f'fill {X - 3} {Y - 1} {Z - 3 + ZOFF} {X + 3} {Y + 3} {Z + 3 + ZOFF} minecraft:air'); c('kill @e[type=item]')
print(errors()[-300:]); c('function bw:game/close'); time.sleep(1); b.close()
