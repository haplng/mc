"""Build the ten maps: check them, write structure files and preview pictures, and return what the pack writer needs."""
import sys, os, time, json, math, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check, preview

MODULES = ['m01_tea', 'm02_chess', 'm03_circus', 'm04_train', 'm05_stadium', 'm06_library', 'm07_turtle', 'm08_windmill', 'm09_solar', 'm10_pirate']
ROOT = os.environ.get('BW_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('BW_OUT', ROOT + '/out3')

def build_maps(struct_dir, previews=True, only=None):
    os.makedirs(struct_dir, exist_ok=True); os.makedirs(OUT + '/preview', exist_ok=True); os.makedirs(OUT + '/canvas', exist_ok=True)
    out = []; problems = 0
    for name in MODULES:
        mod = importlib.import_module(name)
        if only and mod.ID not in only: continue
        t0 = time.time()
        mb = mod.build(); cv = mb.cv
        bad = check.states(cv, mod.ID); ph = check.physics(cv, mod.ID); mk = check.markers(cv, mod.ID); rb, area = check.reach(cv, mod.ID)
        cen = check.census(cv); gaps = mb.gaps()
        want = {'bw.spawn': 8, 'bw.bed': 8, 'bw.gen.iron': 8, 'bw.shop': 8, 'bw.upgrade': 8, 'bw.gen.diamond': 4, 'bw.gen.emerald': 4}
        if cen != want: print('  CENSUS', mod.ID, cen); problems += 1
        problems += len(bad) + len(mk) + len(rb)
        (x0, y0, z0), (x1, y1, z1) = cv.bounds()
        org, size, n, npal = cv.save_structure(f'{struct_dir}/{mod.ID}.nbt')
        red = [p for p, t in cv.ents if {'bw.t.red', 'bw.spawn'} <= {str(v) for v in t['Tags']}][0]
        rec = dict(id=mod.ID, name=mod.NAME, origin=[int(v) for v in org], size=[int(v) for v in size], blocks=n, palette=npal, gate=mod.GATE,
                   size_text=f'{size[0]}x{size[2]}', red_spawn=list(red), gaps=gaps, physics_fixed=sum(ph.values()), markers=len(cv.ents))
        out.append(rec)
        import pickle
        pickle.dump(dict(b=cv.b, ents=[(p, [str(v) for v in t['Tags']]) for p, t in cv.ents]), open(f'{OUT}/canvas/{mod.ID}.pkl', 'wb'))
        if previews:
            preview.iso2(cv, 3, 0, 2.2).save(f'{OUT}/preview/{mod.ID}_iso.png'); preview.top(cv, 3).save(f'{OUT}/preview/{mod.ID}_top.png')
        g = {k: v for k, v in gaps.items() if k.startswith('base-')}
        print(f"{mod.ID:9s} {mod.NAME:5s} {size[0]}x{size[2]} h{size[1]} blocks {n:6d} pal {npal:3d} bad {len(bad)} fixed {sum(ph.values())} markers {len(mk)} reach {len(rb)} gaps {g} {time.time()-t0:.1f}s", flush=True)
    return out, problems

if __name__ == '__main__':
    recs, problems = build_maps(OUT + '/structures', previews='nopreview' not in sys.argv, only=[a for a in sys.argv[1:] if a != 'nopreview'] or None)
    print('problems', problems)
