"""Build all bed wars maps (and the lobby) into structure files + preview renders."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import themes, bwmap, check, render

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out')
def build(ids=None, preview=True):
    os.makedirs(OUT + '/structures', exist_ok=True); os.makedirs(OUT + '/preview', exist_ok=True)
    info = {}
    for i, th in enumerate(themes.THEMES):
        if ids and th['id'] not in ids: continue
        t = time.time()
        cv = bwmap.build_map(th, th['R'], seed=100 + i)
        bad = check.check(cv, th['id']); mb = check.markers(cv, th['id'])
        org, size, n, npal = cv.save_structure(f"{OUT}/structures/{th['id']}.nbt")
        info[th['id']] = dict(name=th['name'], R=th['R'], origin=[int(v) for v in org], size=[int(v) for v in size], blocks=n, palette=npal,
                              markers=len(cv.ents))
        print(f"{i+1:2d} {th['id']:9s} R{th['R']} size {size[0]}x{size[2]} h{size[1]} blocks {n} palette {npal} markers {len(cv.ents)} bad {len(bad)} marker problems {len(mb)} overlap {getattr(cv, 'overlap', 0)} min gap {bwmap.gaps(cv):.0f} {time.time()-t:.1f}s", flush=True)
        if preview:
            bl = {p: (s.split('[')[0], 0) for p, s in cv.b.items()}
            render.render(bl, f"{OUT}/preview/{th['id']}_top.png", f"{OUT}/preview/{th['id']}_iso.png", 2)
    old = {}
    if os.path.exists(OUT + '/info.json'): old = json.load(open(OUT + '/info.json'))
    old.update(info); json.dump(old, open(OUT + '/info.json', 'w'), ensure_ascii=False, indent=1)
    return info

if __name__ == '__main__':
    build(sys.argv[1:] or None)
