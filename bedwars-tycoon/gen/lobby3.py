"""Build the lobby for a given list of maps (json in, structure + json out). Runs with the v2 generator modules.
usage: python3 lobby3.py maps.json out.nbt out.json"""
import sys, os, json, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lobby
spec = importlib.util.spec_from_file_location('check3', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gen3', 'check.py')); check3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(check3)

maps = json.load(open(sys.argv[1], encoding='utf-8'))
themes = [dict(id=m['id'], name=m['name'], size_text=m['size_text'], house=dict(frame=m['gate']['frame'], roof_full=m['gate']['roof_full']),
               plaza=m['gate']['plaza'], gate_glass=m['gate']['glass']) for m in maps]
cv, pads = lobby.build_lobby(themes)
bad = check3.states(cv, 'lobby'); ph = check3.physics(cv, 'lobby')
org, size, n, npal = cv.save_structure(sys.argv[2])
sp = [p for p, t in cv.ents if 'bw.lobby.spawn' in [str(v) for v in t['Tags']]][0]
json.dump(dict(origin=[int(v) for v in org], size=[int(v) for v in size], blocks=n, pads=pads, spawn=list(sp), bad=len(bad), physics=sum(ph.values())),
          open(sys.argv[3], 'w'))
print('lobby', size, 'blocks', n, 'bad', len(bad), 'physics fixed', sum(ph.values()))
if len(sys.argv) > 4:
    import pickle; pickle.dump(dict(b=cv.b), open(sys.argv[4], 'wb'))
