"""Build one map module, check it and write preview pictures:  python3 run.py m01_tea [part]"""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check, preview
OUT = os.path.join(os.environ.get('BW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out3', 'preview'); os.makedirs(OUT, exist_ok=True)
SC = int(os.environ.get('SC', 4))

def report(mod, mb, t0):
    cv = mb.cv
    bad = check.states(cv, mod.ID); ph = check.physics(cv, mod.ID); mk = check.markers(cv, mod.ID)
    (x0, y0, z0), (x1, y1, z1) = cv.bounds()
    print(f'{mod.ID} {mod.NAME}: size {x1-x0+1}x{z1-z0+1} h{y1-y0+1} (y {y0}..{y1}) blocks {len(cv.b)} overlap {mb.overlap} bad {len(bad)} physics {sum(ph.values())} markers {len(mk)} {check.census(cv)}')
    print('   gaps', mb.gaps(), f'{time.time()-t0:.1f}s')

if __name__ == '__main__':
    name = sys.argv[1]; mod = importlib.import_module(name); t0 = time.time()
    if len(sys.argv) > 2:                       # close-ups of single parts: run.py m01_tea cup_base:red cake
        ims = []
        for part in sys.argv[2:]:
            f, _, arg = part.partition(':')
            cv = getattr(mod, f)(*([int(arg) if arg.isdigit() else arg] if arg else []))
            check.states(cv, part); check.physics(cv, part); check.markers(cv, part)
            (x0, y0, z0), (x1, y1, z1) = cv.bounds(); print(part, 'size', x1 - x0 + 1, z1 - z0 + 1, 'y', y0, y1, 'blocks', len(cv.b))
            ims += [preview.iso2(cv, SC, 0), preview.iso2(cv, SC, 1), preview.iso2(cv, SC, 2)]
        preview.fit(preview.side_by_side(ims), 2000, 1400).save(f'{OUT}/{mod.ID}_parts.png')
    else:
        mb = mod.build(); report(mod, mb, t0)
        preview.fit(preview.side_by_side([preview.top(mb.cv, 3), preview.iso(mb.cv, 3, 0)]), 1900, 1000).save(f'{OUT}/{mod.ID}.png')
