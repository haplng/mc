"""helpers for testing a round on the local server with the fake player"""
import sys, time, json, re
sys.path.insert(0, '/home/claude/mc/tools'); sys.path.insert(0, '/home/claude/bw/tools')
import rcon
from bwbot import BwBot
OUT = '/tmp/bwout'
r = rcon.Rcon(); c = r.cmd
def sc(n, o='bw'):
    try: return r.score(n, o)
    except Exception: return None
def pos(sel):
    a = c(f'data get entity {sel} Pos')
    m = re.search(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', a)
    return tuple(round(float(v), 2) for v in m.groups()) if m else None
def join(name='tester'):
    b = BwBot(name); assert b.wait_joined(), b.kicked
    c(f'op {name}'); time.sleep(1.0); return b
def start(mid, b=None, wait=40, unlock=True):
    lob = json.load(open(OUT + '/lobby.json')); maps = [m for m in json.load(open(OUT + '/maps.json')) if 'tp' in m]
    k = [m['id'] for m in maps].index(mid); pad = lob['pads'][k]
    xs = [p[0] for p in pad['cells']]; zs = [p[1] for p in pad['cells']]
    if unlock:
        for m_ in ('tea', 'chess', 'circus', 'library', 'solar'): c(f'tag tester add bw.m.{m_}')
    c('gamemode adventure tester'); c(f'tp tester {sum(xs) / len(xs) + 0.5} 65 {sum(zs) / len(zs) + 0.5}')
    t0 = time.time()
    while time.time() - t0 < wait:
        if sc('#state') == 3: break
        time.sleep(0.5)
    return round(time.time() - t0, 1)
def inv(name='tester'):
    a = c(f'data get entity {name} Inventory')
    return re.findall(r'count: (\d+)[^}]*?id: "minecraft:([a-z_]+)"', a) or re.findall(r'id: "minecraft:([a-z_]+)"', a)
def count(item, name='tester'):
    a = c(f'clear {name} minecraft:{item} 0'); m = re.search(r'Found (\d+)', a); return int(m.group(1)) if m else 0
def bots():
    out = {}
    for i in range(1, 8):
        p = pos(f'@e[type=mannequin,tag=bw.bot,scores={{bw.team={i}}},limit=1]')
        if p: out[i] = p
    return out
def errors():
    import subprocess
    return subprocess.run("grep -iE 'error|exception|Failed|Couldn|Unknown' /home/claude/mcsrv/run/logs/latest.log | grep -v 'minecraftservices\\|Services\\|MinecraftClient\\|UnknownHost' | tail -5", shell=True, capture_output=True, text=True).stdout
