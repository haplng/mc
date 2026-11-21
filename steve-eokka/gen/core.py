"""Shared helpers for the datapack generator."""
import json, os

NS = 'ek'
STEVE = '@e[tag=ek.steve,limit=1]'

def flat(x):
    out = []
    def rec(v):
        if v is None: return
        if isinstance(v, str):
            if v: out.append(v)
        else:
            for i in v: rec(i)
    rec(x)
    return out

class Pack:
    def __init__(s):
        s.fns = {}; s.n = 0; s.files = {}
        s.objectives = ['ek', 'ek.use', 'ek.life', 'ek.cd', 'ek.sn', 'ek.zm', 'ek.rd', 'ek.mh']
        s.bossbars = ['ek:prog', 'ek:mental', 'ek:energy']
    def fn(s, name, *lines):
        assert name not in s.fns, 'duplicate function ' + name
        s.fns[name] = flat(lines)
        return 'function ek:' + name
    def add(s, name, *lines):
        s.fns.setdefault(name, []).extend(flat(lines))
    def uid(s, prefix):
        s.n += 1
        return f'{prefix}{s.n}'
    def write(s, root):
        for name, lines in s.fns.items():
            path = os.path.join(root, 'data', NS, 'function', name + '.mcfunction')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(lines) + '\n')
        for rel, content in s.files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)

P = Pack()

# ---------- text ----------
def js(o): return json.dumps(o, ensure_ascii=False, separators=(',', ':'))
def t(text, color=None, bold=False, italic=None):
    d = {'text': text}
    if color: d['color'] = color
    if bold: d['bold'] = True
    if italic is not None: d['italic'] = italic
    return d
def sc(name, color=None):
    d = {'score': {'name': '#' + name, 'objective': 'ek'}}
    if color: d['color'] = color
    return d
def st(path, color=None):
    d = {'nbt': path, 'storage': 'ek:s'}
    if color: d['color'] = color
    return d
def comp(*parts):
    parts = [p if isinstance(p, dict) else {'text': p} for p in parts]
    return js(parts[0]) if len(parts) == 1 else js({'text': '', 'extra': parts})
def clean(text):
    assert '"' not in text and '\\' not in text and '$(' not in text, text
    return text

# ---------- commands ----------
def S(cmd): return f'execute as {STEVE} at @s run {cmd}'
def at_s(cmd): return f'execute at {STEVE} run {cmd}'
def snd(i, pitch=1, vol=1): return f'execute as @a at @s run playsound minecraft:{i} master @s ~ ~ ~ {vol} {pitch}'
def sset(n, v): return f'scoreboard players set #{n} ek {v}'
def sadd(n, v): return f'scoreboard players add #{n} ek {v}'
def ssub(n, v): return f'scoreboard players remove #{n} ek {v}'
def sop(a, op, b): return f'scoreboard players operation #{a} ek {op} #{b} ek'
def iff(n, r, cmd): return f'execute if score #{n} ek matches {r} run {cmd}'
def unl(n, r, cmd): return f'execute unless score #{n} ek matches {r} run {cmd}'
def pre(prefix, cmds): return [f'{prefix} run {c}' for c in flat(cmds)]
def tell(*parts): return 'tellraw @a ' + comp(*parts)
def abar(*parts, hold=50): return ['title @a actionbar ' + comp(*parts), sset('abt', hold)]
def status(text): return 'data modify storage ek:s status set value "%s"' % clean(text)
def bstatus(text): return ['data modify storage ek:s bstatus set value "%s"' % clean(text), status(text)]
def popup(text, color='yellow', s='3', dy=2.6):
    return 'execute at %s positioned ~ ~%s ~ run function ek:fx/popup {t:"%s",c:"%s",s:"%s"}' % (STEVE, dy, clean(text), color, s)
def popup_at(x, y, z, text, color='yellow', s='3'):
    return 'execute positioned %s %s %s run function ek:fx/popup {t:"%s",c:"%s",s:"%s"}' % (x, y, z, clean(text), color, s)
def hold(item): return f'item replace entity {STEVE} weapon.mainhand with minecraft:{item}'
def face(x, y, z): return S(f'tp @s ~ ~ ~ facing {x} {y} {z}')
def swing(): return f'swing {STEVE} mainhand'
def pose(p): return 'data modify entity %s pose set value "%s"' % (STEVE, p)
def part(name, dy=1, spread=0.3, speed=0.05, n=8): return at_s(f'particle minecraft:{name} ~ ~{dy} ~ {spread} {spread} {spread} {speed} {n} force')
def bpart(block, x, y, z, n=6): return 'particle minecraft:block{block_state:"minecraft:%s"} %s %s %s 0.3 0.3 0.3 0 %d force' % (block, x + 0.5, y + 0.5, z + 0.5, n)
def hurt(): return 'function ek:steve/hurt'
def dmg(n): return [sset('dmg', n), 'function ek:game/dmg']
def heal(n): return [sset('heal', n), 'function ek:game/heal']
HEAL_KEYS = []
def heal_once(key, n):
    """Milestone morale boost that only counts the first time (not again after a setback)."""
    HEAL_KEYS.append(key)
    P.fn('game/ho_' + key, sset('ho_' + key, 1), heal(n))
    return ['execute unless score #ho_%s ek matches 1 run function ek:game/ho_%s' % (key, key)]

def say1(line): return 'function ek:steve/say {t:"%s"}' % clean(line)

def say(lines, low=None):
    """Reaction line: random pick; when Steve's mental is low, half the time a 'tilted' line instead."""
    if isinstance(lines, str): lines = [lines]
    name = P.uid('say/r')
    body = []
    lowfn = 'ek:say/low'
    if low:
        lowfn = 'ek:' + name + '_low'
        P.fn(name + '_low', 'execute store result score #r ek run random value 1..%d' % len(low),
             [iff('r', i + 1, say1(l)) for i, l in enumerate(low)])
    body.append('execute if score #pct ek matches ..35 store result score #r2 ek run random value 1..2')
    body.append('execute if score #pct ek matches ..35 if score #r2 ek matches 1 run return run function ' + lowfn)
    if len(lines) == 1:
        body.append(say1(lines[0]))
    else:
        body.append('execute store result score #r ek run random value 1..%d' % len(lines))
        body += [iff('r', i + 1, say1(l)) for i, l in enumerate(lines)]
    return P.fn(name, body)

CAUSES = {
    'creeper': '크리퍼 폭사', 'fall': '낙사', 'lightning': '벼락', 'suffocate': '자갈 질식', 'zombie': '좀비',
    'lava': '용암', 'piglin': '피글린', 'silverfish': '좀벌레', 'enderman': '엔더맨', 'void': '공허 낙사',
    'bed': '침대 폭발', 'anvil': '모루', 'unknown': '원인 불명',
}
def die(cause, msg):
    assert cause in CAUSES
    return [tell(t('Steve이(가) ' + msg, 'white')), sadd('deaths', 1), sadd('dc_' + cause, 1),
            'kill @e[tag=ek.steve]', 'kill @e[tag=ek.bub]', sset('steve', 0), sset('bubt', 0),
            snd('entity.player.death', 1, 0.8)]

DISPLAY_T = 'transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[%sf,%sf,%sf]}'
def tdisp(x, y, z, tags, text_json, scale, extra=''):
    tg = ','.join('"%s"' % a for a in tags)
    return 'summon text_display %s %s %s {Tags:[%s],billboard:"center",line_width:400,background:0,shadow:1b,view_range:4f,brightness:{sky:15,block:15},%s,text:%s%s}' % (
        x, y, z, tg, DISPLAY_T % (scale, scale, scale), text_json, extra)
