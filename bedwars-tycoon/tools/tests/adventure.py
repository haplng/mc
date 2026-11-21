import sys, time, re, math, struct; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
sys.path.insert(0, '/home/claude/bw/gen3'); import items
b = join()
if sc('#state') != 3: print('start', start('tea', b)); time.sleep(0.5)
c('effect give tester minecraft:resistance infinite 4 true')
c('fill 596 90 -4 612 90 4 minecraft:stone'); c('fill 596 91 -4 612 99 4 minecraft:air'); c('tp tester 603.5 91 0.5 -90 45'); time.sleep(0.8)
def bpos(x, y, z): return struct.pack('>Q', ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF))
seq = [200]
def place(x, y, z, face=1):
    seq[0] += 1; b._send('play', 'use_item_on', varint(0) + bpos(x, y, z) + varint(face) + struct.pack('>fff', 0.5, 1.0, 0.5) + b'\x00\x00' + varint(seq[0]))
def dig(x, y, z, secs):
    seq[0] += 1; b._send('play', 'player_action', varint(0) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(secs)
    seq[0] += 1; b._send('play', 'player_action', varint(3) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(0.4)
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} minecraft:{blk}')
c('gamemode adventure tester'); time.sleep(0.3)
x = 604
for label, item in (('shop item', items.it("red_wool", items.BLOCK)), ('can_place_on=[{}] only', 'minecraft:red_wool[can_place_on=[{}]]'),
                    ('can_place_on=[{blocks:"minecraft:stone"}]', 'minecraft:red_wool[can_place_on=[{blocks:"minecraft:stone"}]]'),
                    ('can_place_on={blocks:"minecraft:stone"}', 'minecraft:red_wool[can_place_on={blocks:"minecraft:stone"}]'),
                    ('can_place_on=[{blocks:"#bw:any"}] ', 'minecraft:red_wool[can_place_on=[{blocks:"#minecraft:mineable/pickaxe"}]]')):
    c('clear tester'); r_ = c(f'give tester {item} 8'); b.slot(0); time.sleep(0.4); place(x, 90, 0); time.sleep(0.5)
    print(f'{label:45s} give: {r_[:28]:28s} placed: {is_(x, 91, 0, "red_wool")}  comp: {c("data get entity tester SelectedItem.components")[-110:]}'); x += 1
# breaking in adventure
c('setblock 610 91 0 minecraft:red_wool'); c('tp tester 608.5 91 0.5 -90 45'); time.sleep(0.8)
c('clear tester'); c(f'give tester {items.WOOD_SWORD}'); b.slot(0); time.sleep(0.4); dig(610, 91, 0, 1.8); print('break wool with the kit sword:', not is_(610, 91, 0, 'red_wool'))
c('setblock 610 91 0 minecraft:red_wool'); c('clear tester'); c('give tester minecraft:wooden_sword'); time.sleep(0.4); dig(610, 91, 0, 1.8); print('break wool with a plain sword (must fail):', not is_(610, 91, 0, 'red_wool'))
dig(609, 90, 0, 1.0); c('clear tester'); c(f'give tester {items.WOOD_SWORD}'); time.sleep(0.3); dig(609, 90, 0, 4.0); print('break map stone with the kit sword (must fail):', not is_(609, 90, 0, 'stone'))
b.close()
