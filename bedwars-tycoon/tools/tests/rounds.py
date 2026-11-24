# several rounds in a row as one player (the name is taken from argv, 'tester' otherwise): what a round needs must still be there from the
# second round on. Every round: buy wool, put two down, break one with the empty hand, break two enemy beds (empty hand, ingots in the hand),
# fail to break the own bed and the map floor, final-kill a bot. Round 1 ends with the player out, round 2 lets the bots play six minutes
# and is won, the others are given up. To play as a real player of a copied world, copy players/data/<their uuid>.dat to the offline uuid
# of the name first (md5 of "OfflinePlayer:<name>", version 3) and pass the name:   python3 rounds.py haplng 1,2,3
import sys, time, re, math, struct; sys.path.insert(0, '/home/claude/bw/tools')
from gt import *
from bot import varint
from bwbot import BwBot
N = sys.argv[1] if len(sys.argv) > 1 else 'tester'
ROUNDS = [int(v) for v in sys.argv[2].split(',')] if len(sys.argv) > 2 else [1, 2, 3]
BEDS = {0: [(646, 65, -23), (645, 65, -23)], 1: [(646, 65, 23), (645, 65, 23)], 2: [(623, 65, 46), (623, 65, 45)], 3: [(577, 65, 46), (577, 65, 45)],
        4: [(554, 65, 23), (555, 65, 23)], 5: [(554, 65, -23), (555, 65, -23)], 6: [(577, 65, -46), (577, 65, -45)], 7: [(623, 65, -46), (623, 65, -45)]}   # tea
B = lambda i: f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]'
def bpos(x, y, z): return struct.pack('>Q', ((x & 0x3FFFFFF) << 38) | ((z & 0x3FFFFFF) << 12) | (y & 0xFFF))
seq = [500]
def dig(x, y, z, secs):      # hold the attack button on a block, then let go (26.3: 0 start, 3 stop)
    seq[0] += 1; b._send('play', 'player_action', varint(0) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(secs)
    seq[0] += 1; b._send('play', 'player_action', varint(3) + bpos(x, y, z) + bytes([1]) + varint(seq[0])); time.sleep(0.4)
def place(x, y, z):
    seq[0] += 1; b._send('play', 'use_item_on', varint(0) + bpos(x, y, z) + varint(1) + struct.pack('>fff', 0.5, 1.0, 0.5) + b'\x00\x00' + varint(seq[0]))
is_ = lambda x, y, z, blk: 'passed' in c(f'execute if block {x} {y} {z} {blk}')
mode = lambda: c(f'data get entity {N} playerGameType').split()[-1]
said = lambda n0: [m.strip().replace('\n', ' ')[:90] for m in b.chat[n0:]]
def gate(wait=60):           # walk into the tea gate the way a player does (no game mode change first)
    c(f'tp {N} -29.5 65 -24.5'); t0 = time.time()
    while time.time() - t0 < wait and sc('#state') != 3: time.sleep(0.5)
    return round(time.time() - t0, 1)
def beds_ok(): return ''.join('1' if all(is_(*p, '#minecraft:beds') for p in BEDS[i]) else '0' for i in range(8))
def scores(k): return ''.join(str(sc(f'#{k}{i}')) for i in range(8))
def stand(x, z, yaw, pitch=40): c(f'tp {N} {x} 65 {z} {yaw} {pitch}'); time.sleep(0.9); b.look(yaw, pitch); time.sleep(0.4)
def hand(slot): b.slot(slot); time.sleep(0.3)
def report(tag):
    print(f'   [{tag}] state {sc("#state")} sec {sc("#sec")} mode {mode()} fighter {"bw.fighter" in c(f"tag {N} list")} | bed blocks {beds_ok()} scores {scores("bed")} out {scores("out")} | bots {len(bots())}')
b = BwBot(N); assert b.wait_joined(), b.kicked; c(f'op {N}'); c(f'tag {N} add bw.m.tea'); c(f'tag {N} add bw.u.wool'); time.sleep(3)
print('logged in:', pos(N), 'mode', mode(), 'state', sc('#state'), 'coins', sc(N, 'bw.coins'))
wool_at = {}
for rnd in ROUNDS:
    n0 = len(b.chat); t = gate(); time.sleep(1.5)
    nm = [c(f'data get entity {B(i)} CustomName').split(': ')[-1].strip('"') for i in range(1, 8)]
    print(f'=== ROUND {rnd}: playing {t} s after the gate; bot names {nm}{"" if len(set(nm)) == 7 else "  <-- A NAME TWICE"}')
    report('start'); c(f'effect give {N} minecraft:resistance infinite 4 true')
    print('   kit', inv(N), '| wool of earlier rounds still in the map:', {k: is_(*v, '#minecraft:wool') for k, v in wool_at.items()})
    c(f'give {N} minecraft:iron_ingot 8'); time.sleep(0.6); c(f'execute as {N} run function bw:gui/act/1'); time.sleep(0.4)      # the wool purchase of the shop chest
    p = pos(N); px, pz = math.floor(p[0]), math.floor(p[2])
    spot = next(((px + dx, pz + dz) for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)) if not is_(px + dx, 64, pz + dz, '#bw:open') and is_(px + dx, 65, pz + dz, 'minecraft:air')), None)
    wslot = next((i for i in range(9) if 'red_wool' in c(f'data get entity {N} Inventory[{{Slot:{i}b}}].id')), None)
    print('   bought wool:', count('red_wool', N), 'in slot', wslot, said(n0)[-1:])
    if spot is not None and wslot is not None:
        hand(wslot); place(spot[0], 64, spot[1]); time.sleep(0.4); place(spot[0], 65, spot[1]); time.sleep(0.5)
        print('   two wool put down at', spot, ':', is_(spot[0], 65, spot[1], 'minecraft:red_wool'), is_(spot[0], 66, spot[1], 'minecraft:red_wool'))
        wool_at[rnd] = (spot[0], 65, spot[1]); c(f'clear {N} minecraft:red_wool'); time.sleep(0.3)
        yaw = {(1, 0): -90, (-1, 0): 90, (0, 1): 0, (0, -1): 180}[((spot[0] > px) - (spot[0] < px), (spot[1] > pz) - (spot[1] < pz))]
        c(f'tp {N} {px + 0.5} 65 {pz + 0.5} {yaw} 5'); time.sleep(0.8); b.look(yaw, 5); time.sleep(0.4)
        hand(8); dig(spot[0], 66, spot[1], 1.4); print('   placed wool, empty hand            -> gone:', is_(spot[0], 66, spot[1], 'minecraft:air'))
    stand(648.5, 23.5, 90); hand(8); n1 = len(b.chat); dig(646, 65, 23, 1.0); time.sleep(0.6)
    print('   blue bed, empty hand               -> broken:', sc('#bed1') == 0, said(n1)[:1])
    stand(623.5, 48.5, 180); c(f'item replace entity {N} container.7 with minecraft:iron_ingot 6'); hand(7); n1 = len(b.chat); dig(623, 65, 46, 1.0); time.sleep(0.6)
    print('   lime bed, iron ingots in the hand  -> broken:', sc('#bed2') == 0, said(n1)[:1])
    stand(648.5, -23.5, 90); hand(8); dig(646, 65, -23, 1.2); time.sleep(0.6); print('   own bed, empty hand                -> still there:', sc('#bed0') == 1 and beds_ok()[0] == '1')
    stand(650.5, -23.5, 90, 80); dig(650, 64, -24, 2.5); print('   map floor, 2.5 s                   -> still there:', not is_(650, 64, -24, 'minecraft:air'))
    pb = pos(B(1))
    if pb:
        c(f'tp {N} {pb[0] + 1.2} {pb[1]} {pb[2]}'); time.sleep(0.5); n1 = len(b.chat); c(f'damage {B(1)} 100 minecraft:player_attack by {N}'); time.sleep(1.2)
        print('   blue bot killed after its bed      ->', said(n1)[:3], 'out1', sc('#out1'))
    report('mid'); n1 = len(b.chat)
    if rnd == 2:             # nobody touches anything for six minutes of game time: do the bots carry the round on?
        c(f'tp {N} 656.5 65 -23.5'); c('tick sprint 7200'); t0 = time.time()
        while time.time() - t0 < 150 and sc('#state') == 3 and (sc('#sec') or 0) < 370: time.sleep(3)
        ev = [m for m in said(n1) if '침대 파괴' in m or '탈락' in m or '처치' in m]
        print(f'   six minutes on ({time.time() - t0:.0f} s real): sec {sc("#sec")}, {len(ev)} bed/kill lines, first:', ev[:4]); report('after 6 min'); n1 = len(b.chat)
    if rnd == 1:             # the own bed goes, then the player dies for good
        c('tag @e remove bw.breaker'); c('function bw:m/tea/bedkill0'); time.sleep(0.5); c(f'effect clear {N} minecraft:resistance'); c(f'kill {N}'); time.sleep(1.5)
        print('   player out: state', sc('#state'), 'mode', mode(), said(n1)[-3:])
    elif rnd == 2 and sc('#state') == 3:
        for i in range(1, 8): c(f'scoreboard players set #bed{i} bw 0'); c(f'kill {B(i)}')
        c('tp @e[type=mannequin,tag=bw.bot] 0 -400 0'); time.sleep(0.5)
        for i in range(1, 8): c(f'scoreboard players set #bres{i} bw 0')
        time.sleep(2.5); print('   everyone else out: state', sc('#state'), 'coins', sc(N, 'bw.coins'), 'stage', sc(N, 'bw.stage'), said(n1)[-3:])
    elif sc('#state') == 3:
        b.command('trigger lobby'); time.sleep(1.5); print('   /trigger lobby: state', sc('#state'), said(n1)[-2:])
    t0 = time.time()
    while time.time() - t0 < 20 and sc('#state') != 0: time.sleep(0.5)
    time.sleep(1.5); print(f'   lobby again after {time.time() - t0:.1f} s: state', sc('#state'), 'pos', pos(N), 'mode', mode(), 'inv', inv(N)[:3], 'coins', sc(N, 'bw.coins'), 'stage', sc(N, 'bw.stage'))
print('server log:', errors()[-500:] or 'nothing wrong'); b.close()
