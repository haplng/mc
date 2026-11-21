"""Small helpers shared by the pack writers: SNBT text, team table, function writer."""
import os, json

TEAMS = ['red', 'blue', 'lime', 'yellow', 'cyan', 'white', 'pink', 'gray']
TEAM_KO = ['빨강', '파랑', '초록', '노랑', '청록', '하양', '분홍', '회색']
TEAM_COLOR = ['red', 'blue', 'green', 'yellow', 'dark_aqua', 'white', 'light_purple', 'gray']     # chat / team colours
TEAM_DYE_RGB = [11546150, 3949738, 8439583, 16701501, 1481884, 16383998, 15961002, 4673362]       # leather armour

class Raw(str):
    """text that goes into SNBT unquoted (a macro variable holding a whole compound, a number with a suffix)"""

def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def snbt(o):
    if isinstance(o, Raw): return str(o)
    if isinstance(o, bool): return 'true' if o else 'false'
    if isinstance(o, int): return str(o)
    if isinstance(o, float): return repr(o) + 'd'
    if isinstance(o, str): return q(o)
    if isinstance(o, (list, tuple)): return '[' + ','.join(snbt(v) for v in o) + ']'
    if isinstance(o, dict):
        key = lambda k: k if all(c.isalnum() or c in '._+-' for c in k) else q(k)
        return '{' + ','.join(f'{key(k)}:{snbt(v)}' for k, v in o.items()) + '}'
    raise TypeError(repr(o))

def t(text, color=None, **kw):
    d = {'text': text}
    if color: d['color'] = color
    d.update(kw); return d

def line(*parts):
    """parts side by side; the empty first part keeps them from inheriting each other's style"""
    return [{'text': ''}] + list(parts)

def tell(sel, *parts):
    return f'tellraw {sel} ' + snbt(line(*parts))

class Pack:
    """collects functions and data files of the 'bw' namespace and writes them under a pack folder"""
    def __init__(self, root):
        self.root = root; self.fns = {}
    def fn(self, path, lines):
        assert path not in self.fns, 'function written twice: ' + path
        self.fns[path] = [l for l in lines if l]
        p = f'{self.root}/data/bw/function/{path}.mcfunction'
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write('\n'.join(self.fns[path]) + '\n')
    def add(self, path, lines):
        """append to a function that was (or will be) written with fn"""
        cur = self.fns.pop(path, [])
        self.fn(path, cur + list(lines))
    def json(self, rel, obj):
        p = f'{self.root}/data/{rel}'; os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(obj, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
