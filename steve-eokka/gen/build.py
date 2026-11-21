"""Generate the datapack, validate every command against the 26.3 tree, check paths, write previews."""
import sys, os, shutil, json
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/tools')
from core import *
import terrain, stages as ST, cards as CD, engine
import validate

OUT = ROOT + '/out/eokka'
os.makedirs(ROOT + '/out', exist_ok=True)

def main():
    stages = ST.all_stages()
    cards, pools = CD.build(stages)
    engine.build(stages, cards, pools)
    problems = []
    for s in stages:
        s.emit()
        problems += s.g.check(f's{s.n}')
        iss, routes, pts = s.check_paths()
        problems += iss
        terrain.preview(s.g, f'{ROOT}/out/preview_s{s.n}.png', pts, routes)
    CD.finish_events()
    blocks = set(validate.BLOCKS)
    for b in terrain.PASS: assert b in blocks, b
    P.files['data/ek/tags/block/pass.json'] = js({'values': ['minecraft:' + b for b in terrain.PASS]})
    # what the player's line of sight goes through: the same, except that liquids and portal surfaces stop it
    RAY = [b for b in terrain.PASS if b not in ('water', 'lava', 'nether_portal', 'end_portal')]
    P.files['data/ek/tags/block/ray.json'] = js({'values': ['minecraft:' + b for b in RAY]})
    P.files['pack.mcmeta'] = js({'pack': {'description': '스티브 억까 시뮬레이터', 'min_format': [121, 0], 'max_format': [121, 0]}})
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    P.write(OUT)
    n, errs, fns = validate.validate_pack(OUT, 'ek', P.objectives, P.bossbars)
    print(f'{len(fns)} functions, {n} commands, {len(errs)} syntax errors, {len(problems)} terrain/path problems')
    for fn, ln, e, line in errs[:40]:
        print(f'  {fn}:{ln}: {e}\n      {line[:230]}')
    for p in problems[:40]: print('  ' + p)
    # unresolved function references + unused score names sanity
    for s in stages:
        print(f'  stage {s.n}: {len(s.beats)} beats, ~{s.duration():.0f}s uninterrupted, {len(s.g.cmds())} build commands, {len(s.ents)} entities')
    return len(errs) + len(problems)

if __name__ == '__main__':
    sys.exit(1 if main() else 0)
