"""mcfunction validator against the real 26.3 command tree + registries (misode/mcmeta)."""
import json, re, os, sys
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

REF = ROOT + '/ref'
TREE = json.load(open(f'{REF}/263_commands_data.json'))
REG = json.load(open(f'{REF}/263_registries_data.json'))
BLOCKS = json.load(open(f'{REF}/263_blocks_data.json'))

def reg(name):
    name = name.replace('minecraft:', '')
    return set(REG.get(name, []))

ITEMS = reg('item'); SOUNDS = reg('sound_event'); PARTICLES = reg('particle_type')
COMPONENTS = reg('data_component_type')
NUM = re.compile(r'^-?(\d+\.?\d*|\.\d+)$')
COORD = re.compile(r'^([~^])?(-?(\d+\.?\d*|\.\d+))?$')
RLOC = re.compile(r'^#?([a-z0-9_.-]+:)?[a-z0-9_./-]+$')
SEL_KEYS = {'tag','type','limit','sort','distance','scores','nbt','name','x','y','z','dx','dy','dz',
            'x_rotation','y_rotation','level','gamemode','team','predicate','advancements'}
TEXT_KEYS = {'text','translate','score','selector','nbt','storage','entity','block','interpret','extra','color',
             'bold','italic','underlined','strikethrough','obfuscated','font','shadow_color','click_event',
             'hover_event','insertion','type','with','fallback','separator','keybind','object','sprite','atlas',
             'player','source'}
OPS = {'=','+=','-=','*=','/=','%=','<','>','><'}

def strip_ns(s): return s[10:] if s.startswith('minecraft:') else s

def read_tok(s, i):
    depth = 0; q = None; j = i; n = len(s)
    while j < n:
        c = s[j]
        if q:
            if c == '\\': j += 2; continue
            if c == q: q = None
        else:
            if c in '"\'': q = c
            elif c in '[{(': depth += 1
            elif c in ']})': depth -= 1
            elif c == ' ' and depth == 0: break
        j += 1
    if q or depth != 0: return None
    return j

def split_top(s, sep=','):
    out = []; depth = 0; q = None; cur = ''
    i = 0
    while i < len(s):
        c = s[i]
        if q:
            cur += c
            if c == '\\' and i + 1 < len(s): cur += s[i+1]; i += 2; continue
            if c == q: q = None
        else:
            if c in '"\'': q = c; cur += c
            elif c in '[{(': depth += 1; cur += c
            elif c in ']})': depth -= 1; cur += c
            elif c == sep and depth == 0: out.append(cur); cur = ''
            else: cur += c
        i += 1
    if cur.strip() != '' or out: out.append(cur)
    return out

# ---------- tiny SNBT/JSON-ish parser (syntax check + structure) ----------
class SnbtErr(Exception): pass
def parse_snbt(s):
    pos = [0]
    def ws():
        while pos[0] < len(s) and s[pos[0]] in ' \t': pos[0] += 1
    def val():
        ws()
        if pos[0] >= len(s): raise SnbtErr('eof')
        c = s[pos[0]]
        if c == '{':
            pos[0] += 1; d = {}
            ws()
            if s[pos[0]:pos[0]+1] == '}': pos[0] += 1; return d
            while True:
                ws(); k = key(); ws()
                if s[pos[0]:pos[0]+1] != ':': raise SnbtErr(f'expected : at {pos[0]} near {s[max(0,pos[0]-15):pos[0]+15]!r}')
                pos[0] += 1
                d[k] = val(); ws()
                ch = s[pos[0]:pos[0]+1]
                if ch == ',': pos[0] += 1; continue
                if ch == '}': pos[0] += 1; return d
                raise SnbtErr(f'expected , or }} at {pos[0]} near {s[max(0,pos[0]-15):pos[0]+15]!r}')
        if c == '[':
            pos[0] += 1; ws()
            m = re.match(r'[BILbil];', s[pos[0]:])
            if m: pos[0] += 2
            arr = []
            ws()
            if s[pos[0]:pos[0]+1] == ']': pos[0] += 1; return arr
            while True:
                arr.append(val()); ws()
                ch = s[pos[0]:pos[0]+1]
                if ch == ',': pos[0] += 1; continue
                if ch == ']': pos[0] += 1; return arr
                raise SnbtErr(f'expected , or ] at {pos[0]} near {s[max(0,pos[0]-15):pos[0]+15]!r}')
        if c in '"\'':
            return qstr()
        m = re.match(r'[A-Za-z0-9_.+\-#]+', s[pos[0]:])
        if not m: raise SnbtErr(f'bad value at {pos[0]} near {s[max(0,pos[0]-15):pos[0]+15]!r}')
        pos[0] += m.end(); return ('lit', m.group(0))
    def qstr():
        q = s[pos[0]]; pos[0] += 1; out = ''
        while True:
            if pos[0] >= len(s): raise SnbtErr('unterminated string')
            c = s[pos[0]]
            if c == '\\':
                out += s[pos[0]+1:pos[0]+2]; pos[0] += 2; continue
            if c == q: pos[0] += 1; return out
            out += c; pos[0] += 1
    def key():
        if s[pos[0]:pos[0]+1] in ('"', "'"): return qstr()
        m = re.match(r'[A-Za-z0-9_.+\-]+', s[pos[0]:])
        if not m: raise SnbtErr(f'bad key at {pos[0]} near {s[max(0,pos[0]-15):pos[0]+15]!r}')
        pos[0] += m.end(); return m.group(0)
    v = val(); ws()
    if pos[0] != len(s): raise SnbtErr(f'trailing data at {pos[0]}: {s[pos[0]:pos[0]+20]!r}')
    return v

def check_text(v, where):
    if isinstance(v, str) or (isinstance(v, tuple)): return None
    if isinstance(v, list):
        for x in v:
            e = check_text(x, where)
            if e: return e
        return None
    if isinstance(v, dict):
        for k, x in v.items():
            if k not in TEXT_KEYS: return f'unknown text component key {k!r}'
            if k == 'extra':
                e = check_text(x, where)
                if e: return e
        return None
    return None

class V:
    def __init__(self, functions, objectives, bossbars, own_block_tags, ns):
        self.functions = functions; self.objectives = objectives; self.bossbars = bossbars
        self.block_tags = own_block_tags; self.ns = ns
        self.reason = None; self.best = 0; self.lenient = False

    def fail(self, i, why):
        if i >= self.best:
            self.best = i; self.reason = why
        return None

    # ---- argument consumers ----
    def entity(self, tok, props, i):
        if tok.startswith('@'):
            m = re.match(r'^@([aeprsn])(\[(.*)\])?$', tok, re.S)
            if not m: return self.fail(i, f'bad selector {tok!r}')
            kind = m.group(1); args = {}
            if m.group(3) is not None:
                for part in split_top(m.group(3)):
                    if '=' not in part: return self.fail(i, f'bad selector arg {part!r}')
                    k, val = part.split('=', 1); k = k.strip()
                    if k not in SEL_KEYS: return self.fail(i, f'unknown selector key {k!r}')
                    args.setdefault(k, []).append(val.strip())
            single = kind in 'sprn' and args.get('limit', ['1'])[0] == '1'
            if kind in 'ae' and args.get('limit', [''])[0] == '1': single = True
            if kind == 's': single = True
            if props.get('amount') == 'single' and not single:
                return self.fail(i, f'selector {tok!r} may match multiple entities but a single one is required (add limit=1)')
            if props.get('type') == 'players':
                types = [strip_ns(t) for t in args.get('type', [])]
                if kind in 'en' and 'player' not in types:
                    return self.fail(i, f'selector {tok!r} must be players-only here')
            for t in args.get('type', []):
                t2 = strip_ns(t.lstrip('!'))
                if not t2.startswith('#') and t2 not in reg('entity_type'):
                    return self.fail(i, f'unknown entity type {t!r} in selector')
            for n in args.get('nbt', []):
                try: parse_snbt(n.lstrip('!'))
                except SnbtErr as e: return self.fail(i, f'bad nbt in selector: {e}')
            return True
        if re.match(r'^[A-Za-z0-9_\-#.%$]+$', tok): return True
        return self.fail(i, f'bad entity/name {tok!r}')

    def block(self, tok, i, predicate=False):
        m = re.match(r'^(#?[a-z0-9_:./-]+)(\[[^\]]*\])?(\{.*\})?$', tok, re.S)
        if not m: return self.fail(i, f'bad block {tok!r}')
        bid = m.group(1)
        if bid.startswith('#'):
            if not predicate: return self.fail(i, 'block tag not allowed here')
            if bid.startswith(f'#{self.ns}:') and bid[len(self.ns)+2:] not in self.block_tags:
                return self.fail(i, f'unknown own block tag {bid}')
            return True
        b = strip_ns(bid)
        if b not in BLOCKS:
            if self.lenient: return True
            return self.fail(i, f'unknown block {bid!r}')
        if m.group(2):
            props = BLOCKS[b][0]
            for kv in m.group(2)[1:-1].split(','):
                if '=' not in kv: return self.fail(i, f'bad block state {kv!r}')
                k, val = kv.split('=')
                if k not in props: return self.fail(i, f'block {b} has no property {k!r} (has {list(props)})')
                if val not in props[k]: return self.fail(i, f'block {b} property {k} cannot be {val!r} (allowed {props[k]})')
        if m.group(3):
            try: parse_snbt(m.group(3))
            except SnbtErr as e: return self.fail(i, f'bad block nbt: {e}')
        return True

    def item(self, tok, i, predicate=False):
        m = re.match(r'^(\*|#?[a-z0-9_:./-]+)(\[.*\])?$', tok, re.S)
        if not m: return self.fail(i, f'bad item {tok!r}')
        iid = m.group(1)
        if iid == '*' or iid.startswith('#'):
            if not predicate: return self.fail(i, 'item wildcard/tag not allowed here')
        elif strip_ns(iid) not in ITEMS and not self.lenient:
            return self.fail(i, f'unknown item {iid!r}')
        if m.group(2):
            for part in split_top(m.group(2)[1:-1]):
                part = part.strip()
                mm = re.match(r'^(!?[a-z0-9_:./-]+)(=|~)?(.*)$', part, re.S)
                if not mm: return self.fail(i, f'bad item component {part[:40]!r}')
                cid = strip_ns(mm.group(1).lstrip('!'))
                if cid not in COMPONENTS and cid not in ('count',):
                    return self.fail(i, f'unknown item component {cid!r}')
                if mm.group(2):
                    val = mm.group(3)
                    try: pv = parse_snbt(val)
                    except SnbtErr as e: return self.fail(i, f'bad component value for {cid}: {e}')
                    if cid in ('item_name', 'custom_name'):
                        e = check_text(pv, cid)
                        if e: return self.fail(i, e)
                    if cid == 'lore':
                        e = check_text(pv, cid)
                        if e: return self.fail(i, e)
                    if cid == 'item_model':
                        mid = strip_ns(pv if isinstance(pv, str) else pv[1])
                        if mid not in ITEMS: return self.fail(i, f'item_model {mid!r} is not a vanilla item id')
        return True

    def consume(self, name, node, s, i, path):
        p = node['parser']; props = node.get('properties', {})
        def tok():
            j = read_tok(s, i)
            if j is None or j == i: return None, None
            return s[i:j], j
        def ntoks(n):
            j = i; toks = []
            for k in range(n):
                e = read_tok(s, j)
                if e is None or e == j: return None, None
                toks.append(s[j:e]); j = e
                if k < n - 1:
                    if j >= len(s) or s[j] != ' ': return None, None
                    j += 1
            return toks, j
        if p in ('minecraft:message',) or (p == 'brigadier:string' and props.get('type') == 'greedy'):
            return len(s) if i < len(s) else None
        if p in ('minecraft:vec3', 'minecraft:block_pos'):
            toks, j = ntoks(3)
            if toks is None: return self.fail(i, 'expected 3 coordinates')
            carets = [t.startswith('^') for t in toks]
            if any(carets) and not all(carets): return self.fail(i, f'cannot mix ^ with other coordinates: {toks}')
            for t in toks:
                if not COORD.match(t): return self.fail(i, f'bad coordinate {t!r}')
                if p == 'minecraft:block_pos' and not t.startswith(('~', '^')) and '.' in t:
                    return self.fail(i, f'block position must be integer: {t!r}')
            return j
        if p in ('minecraft:vec2', 'minecraft:column_pos', 'minecraft:rotation'):
            toks, j = ntoks(2)
            if toks is None: return self.fail(i, 'expected 2 values')
            for t in toks:
                if not COORD.match(t) or t.startswith('^'): return self.fail(i, f'bad value {t!r}')
                if p == 'minecraft:column_pos' and not t.startswith('~') and '.' in t:
                    return self.fail(i, f'column position must be integer: {t!r}')
            return j
        t, j = tok()
        if t is None: return self.fail(i, f'expected <{name}:{p}>')
        ok = True
        if p == 'brigadier:bool': ok = t in ('true', 'false')
        elif p in ('brigadier:integer', 'brigadier:long'):
            ok = bool(re.match(r'^-?\d+$', t))
            if ok:
                v = int(t)
                if 'min' in props and v < props['min']: return self.fail(i, f'{v} below min {props["min"]}')
                if 'max' in props and v > props['max']: return self.fail(i, f'{v} above max {props["max"]}')
        elif p in ('brigadier:float', 'brigadier:double'):
            ok = bool(NUM.match(t))
            if ok:
                v = float(t)
                if 'min' in props and v < props['min']: return self.fail(i, f'{v} below min {props["min"]}')
                if 'max' in props and v > props['max']: return self.fail(i, f'{v} above max {props["max"]}')
        elif p == 'brigadier:string':
            if props.get('type') == 'word': ok = bool(re.match(r'^[A-Za-z0-9_\-.+]+$', t))
            else: ok = bool(re.match(r'^("([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'|[A-Za-z0-9_\-.+]+)$', t))
        elif p in ('minecraft:entity', 'minecraft:game_profile'):
            if not self.entity(t, props, i): return None
        elif p == 'minecraft:score_holder':
            if t != '*' and not self.entity(t, {'amount': props.get('amount')} if t.startswith('@') else {}, i): return None
        elif p == 'minecraft:block_state':
            if not self.block(t, i): return None
        elif p == 'minecraft:block_predicate':
            if not self.block(t, i, True): return None
        elif p == 'minecraft:item_stack':
            if not self.item(t, i): return None
        elif p == 'minecraft:item_predicate':
            if not self.item(t, i, True): return None
        elif p in ('minecraft:nbt_compound_tag', 'minecraft:nbt_tag'):
            try:
                v = parse_snbt(t)
                if p == 'minecraft:nbt_compound_tag' and not isinstance(v, dict): return self.fail(i, 'expected compound')
                if isinstance(v, dict) and 'summon' in path:
                    for key in ('text', 'CustomName'):
                        if key in v:
                            e = check_text(v[key], key)
                            if e: return self.fail(i, e)
            except SnbtErr as e: return self.fail(i, f'bad nbt: {e}')
        elif p in ('minecraft:component', 'minecraft:style'):
            try:
                v = parse_snbt(t)
                e = check_text(v, 'component')
                if e: return self.fail(i, e)
            except SnbtErr as e: return self.fail(i, f'bad text component: {e}')
        elif p == 'minecraft:nbt_path': ok = True
        elif p == 'minecraft:function':
            if not RLOC.match(t): return self.fail(i, f'bad function id {t!r}')
            if t.startswith(f'{self.ns}:') and t[len(self.ns)+1:] not in self.functions and not self.lenient:
                return self.fail(i, f'function {t} does not exist')
        elif p == 'minecraft:resource_location':
            if not RLOC.match(t): return self.fail(i, f'bad id {t!r}')
            if path and path[0] == 'playsound' and strip_ns(t) not in SOUNDS and not self.lenient:
                return self.fail(i, f'unknown sound {t!r}')
            if path and path[0] == 'bossbar' and 'add' not in path and t not in self.bossbars:
                return self.fail(i, f'unknown bossbar {t!r}')
        elif p in ('minecraft:resource', 'minecraft:resource_key', 'minecraft:resource_or_tag', 'minecraft:resource_or_tag_key'):
            if not RLOC.match(t): return self.fail(i, f'bad id {t!r}')
            r = reg(props.get('registry', ''))
            if r and not t.startswith('#') and strip_ns(t) not in r and not self.lenient:
                return self.fail(i, f'{t!r} not in registry {props.get("registry")}')
        elif p == 'minecraft:particle':
            m = re.match(r'^([a-z0-9_:]+)(\{.*\})?$', t, re.S)
            if not m or strip_ns(m.group(1)) not in PARTICLES: return self.fail(i, f'unknown particle {t!r}')
            if m.group(2):
                try: parse_snbt(m.group(2))
                except SnbtErr as e: return self.fail(i, f'bad particle options: {e}')
        elif p == 'minecraft:objective':
            if t not in self.objectives: return self.fail(i, f'unknown objective {t!r}')
        elif p == 'minecraft:operation': ok = t in OPS
        elif p in ('minecraft:int_range', 'minecraft:float_range'):
            ok = bool(re.match(r'^(-?\d+(\.\d+)?)?(\.\.)?(-?\d+(\.\d+)?)?$', t)) and t not in ('', '..')
        elif p == 'minecraft:time': ok = bool(re.match(r'^-?\d+(\.\d+)?[dst]?$', t))
        elif p == 'minecraft:gamemode': ok = t in ('survival', 'creative', 'adventure', 'spectator')
        elif p == 'minecraft:entity_anchor': ok = t in ('eyes', 'feet')
        elif p == 'minecraft:swizzle': ok = bool(re.match(r'^[xyz]{1,3}$', t))
        elif p == 'minecraft:heightmap': ok = t in ('world_surface', 'motion_blocking', 'motion_blocking_no_leaves', 'ocean_floor')
        elif p == 'minecraft:item_slot' or p == 'minecraft:slot_source':
            ok = bool(re.match(r'^(weapon(\.(mainhand|offhand))?|armor\.(head|chest|legs|feet|body)|saddle|hotbar\.[0-8]|inventory\.\d+|container\.\d+|contents|player\.cursor)$', t))
        elif p == 'minecraft:team_color' or p == 'minecraft:color':
            ok = t in ('black','dark_blue','dark_green','dark_aqua','dark_red','dark_purple','gold','gray','dark_gray','blue','green','aqua','red','light_purple','yellow','white','reset')
        elif p == 'minecraft:dimension': ok = bool(RLOC.match(t))
        elif p == 'minecraft:objective_criteria': ok = bool(re.match(r'^[a-zA-Z0-9_.:]+$', t))
        elif p == 'minecraft:scoreboard_slot': ok = True
        elif p == 'minecraft:team': ok = bool(re.match(r'^[A-Za-z0-9_\-.+]+$', t))
        elif p == 'minecraft:angle': ok = bool(COORD.match(t)) and not t.startswith('^')
        else:
            ok = True
        if not ok: return self.fail(i, f'bad <{name}:{p}> value {t!r}')
        return j

    def children(self, name, node):
        if 'redirect' in node:
            n = TREE
            for k in node['redirect']: n = n['children'][k]
            return n.get('children', {})
        if 'children' in node: return node['children']
        if name == 'run': return TREE['children']
        return {}

    def match(self, name, node, s, i, path):
        for cname, ch in self.children(name, node).items():
            if ch['type'] == 'literal':
                if not (s.startswith(cname, i) and (i + len(cname) == len(s) or s[i + len(cname)] == ' ')): continue
                j = i + len(cname)
            else:
                j = self.consume(cname, ch, s, i, path)
                if j is None: continue
            if j == len(s):
                if ch.get('executable'): return True
                self.fail(j, f'incomplete command after {cname!r}')
                continue
            if s[j] != ' ':
                self.fail(j, f'unexpected text after <{cname}>: {s[j:j+20]!r}'); continue
            if self.match(cname, ch, s, j + 1, path + [cname]): return True
        if i >= self.best and self.reason is None:
            self.fail(i, f'no matching syntax at: {s[i:i+30]!r}')
        return False

    def check(self, line):
        self.reason = None; self.best = 0; self.lenient = False
        s = line
        if s.startswith('$'):
            self.lenient = True
            s = re.sub(r'\$\(\w+\)', '0', s[1:])
        if '  ' in re.sub(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'', '', s):
            return 'double space outside strings'
        if self.match('', TREE, s, 0, []): return None
        return f'{self.reason} (near col {self.best}: {s[max(0,self.best-25):self.best+35]!r})'

def validate_pack(root, ns, objectives, bossbars):
    fdir = os.path.join(root, 'data', ns, 'function')
    functions = set()
    for d, _, fs in os.walk(fdir):
        for f in fs:
            if f.endswith('.mcfunction'):
                functions.add(os.path.relpath(os.path.join(d, f), fdir)[:-11].replace(os.sep, '/'))
    tags = set()
    tdir = os.path.join(root, 'data', ns, 'tags', 'block')
    if os.path.isdir(tdir):
        for d, _, fs in os.walk(tdir):
            for f in fs: tags.add(os.path.relpath(os.path.join(d, f), tdir)[:-5].replace(os.sep, '/'))
    v = V(functions, set(objectives), set(bossbars), tags, ns)
    errors = []; n = 0
    for fn in sorted(functions):
        for ln, line in enumerate(open(os.path.join(fdir, fn + '.mcfunction'), encoding='utf-8'), 1):
            line = line.rstrip('\n')
            if line != line.strip(): errors.append((fn, ln, 'leading/trailing whitespace', line)); continue
            if not line or line.startswith('#'): continue
            n += 1
            e = v.check(line)
            if e: errors.append((fn, ln, e, line))
    return n, errors, functions

if __name__ == '__main__':
    root, ns = sys.argv[1], sys.argv[2]
    objs = sys.argv[3].split(',') if len(sys.argv) > 3 else []
    bars = sys.argv[4].split(',') if len(sys.argv) > 4 else []
    n, errs, fns = validate_pack(root, ns, objs, bars)
    print(f'{len(fns)} functions, {n} commands, {len(errs)} errors')
    for fn, ln, e, line in errs[:60]:
        print(f'  {fn}:{ln}: {e}\n      {line[:200]}')
