# -*- coding: utf-8 -*-
"""숫자 굴리기 데이터팩을 만든다.

  python3 build.py [출력 폴더]        (기본: ../dist)

필요한 것: tiers.json (tools/count.c + tools/mktiers.py 로 만든 족보별 확률표)
"""
import json
import os
import re
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hands as HM
import engine as EM
from common import *
import sys_roll
import sys_ui
import sys_misc
import sys_dex
from jokers import JOKERS

VERSION = '3.0'


def hand_info():
    tiers = json.load(open(os.path.join(HERE, 'tiers.json'), encoding='utf-8'))['hands']
    real = [h for h in HM.HANDS if not (h['eng'] and h['eng'][0] == 'alias')]
    assert len(real) == NHANDS, len(real)
    order = sorted(range(len(real)), key=lambda i: (tiers[real[i]['key']]['tier'], tiers[real[i]['key']]['inv'], i))
    HI = []
    for n, i in enumerate(order, 1):
        h = real[i]
        t = tiers[h['key']]
        p1 = t['pay']
        pays = [int(p1 * (4 + k) / 4.0 + 0.5) for k in range(5)]
        HI.append(dict(id=n, key=h['key'], name=h['name'], rule=h['rule'], fl=h['fl'], fam=h['fam'], tag=h['tag'], tier=t['tier'],
                       inv=t['inv'], pay=p1, pays=pays, count=t['count'], ex=t['ex']))
    rk = sorted(HI, key=lambda h: (h['pay'], h['id']))
    for r, h in enumerate(rk, 1):
        h['rank'] = r
    names = [h['name'] for h in HI]
    dup = set(n for n in names if names.count(n) > 1)
    assert not dup, dup
    return HI


def build(outdir):
    HI = hand_info()
    ids = {h['key']: h['id'] for h in HI}
    tier = {h['key']: h['tier'] for h in HI}
    pay = {h['key']: h['pay'] for h in HI}
    eng = EM.Engine(HM.HANDS, tier, ids)
    eng.build_eval()
    eng.build_hits(pay)
    eng.build_marks()
    P = Pack()
    P.F.update(eng.F)
    fams_joker = {'same': 'same', 'stair': 'stair', 'mirror': 'mirror', 'word': 'word', 'combo': 'word'}
    sys_roll.build_commit(P, HI, fams_joker)
    sys_roll.build_roll(P)
    sys_ui.build_menu(P)
    sys_misc.build_tools(P)
    sys_misc.build_missions(P)
    sys_misc.build_hist(P)
    sys_misc.build_wall(P)
    sys_misc.build_player(P, HI)
    sys_misc.build_load_tick(P, HI, [])
    sys_dex.build_names(P, HI)
    by_t = sys_dex.build_dex(P, HI)
    sys_dex.build_world(P, HI, by_t, ('4 77 1 555 09', ['삼겹살', '쌍쌍파티', '회식']))
    sys_dex.build_adv(P, HI)
    sys_dex.build_admin(P, HI)
    # 상수, 엔진 점수 초기화
    consts = set(eng.consts)
    names = set()
    for path, lines in P.F.items():
        for ln in lines:
            for m in re.finditer(r'#c(\d+) jv', ln):
                consts.add(int(m.group(1)))
            if path.startswith('hand/'):
                for m in re.finditer(r'(#[A-Za-z0-9_]+) jv', ln):
                    names.add(m.group(1))
    cf = P.fn('consts')
    for c in sorted(consts):
        cf.append('scoreboard players set #c%d jv %d' % (c, c))
    names = sorted(n for n in names if not re.fullmatch(r'#c\d+', n) and n != '#gen')
    init = P.fn('hand/init')
    wrap = P.fn('hand/genwrap')
    for n in names:
        init.append('scoreboard players add %s jv 0' % n)
        wrap.append('scoreboard players set %s jv 0' % n)
    wrap.append('scoreboard players set #gen jv 1')
    # 없는 함수를 부르는 곳이 없는지 확인
    called = set()
    for path, lines in P.F.items():
        for ln in lines:
            for m in re.finditer(r'function jb:([a-z0-9_/]+)', ln):
                if '$(' not in ln[m.start():m.end() + 2]:
                    called.add(m.group(1))
    missing = sorted(c for c in called if c not in P.F)
    assert not missing, missing[:20]
    # ---------- 파일 쓰기 ----------
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    root = os.path.join(outdir, 'dice_roll')
    for path, lines in P.F.items():
        full = os.path.join(root, 'data', 'jb', 'function', path + '.mcfunction')
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    for path, text in P.extra.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(text)
    tagdir = os.path.join(root, 'data', 'minecraft', 'tags', 'function')
    os.makedirs(tagdir, exist_ok=True)
    open(os.path.join(tagdir, 'load.json'), 'w').write('{"values": ["jb:load"]}')
    open(os.path.join(tagdir, 'tick.json'), 'w').write('{"values": ["jb:tick"]}')
    meta = {'pack': {'description': [T('⚀ 숫자 굴리기 ', 'gold'), T('족보 %d · v%s' % (NHANDS, VERSION), 'yellow')], 'min_format': 94, 'max_format': 999},
            'filter': {'block': [{'namespace': 'minecraft', 'path': 'advancement/.*'}]}}
    open(os.path.join(root, 'pack.mcmeta'), 'w', encoding='utf-8').write(json.dumps(meta, ensure_ascii=False, indent=2))
    zpath = os.path.join(outdir, 'dice_roll.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, dn, fns in os.walk(root):
            for fn in sorted(fns):
                full = os.path.join(dp, fn)
                z.write(full, os.path.relpath(full, root))
    json.dump(HI, open(os.path.join(outdir, 'hands.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    nfiles = sum(len(f) for _, _, f in os.walk(root))
    print('functions %d, files %d, zip %d bytes' % (len(P.F), nfiles, os.path.getsize(zpath)))
    return P, HI, eng


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'dist')
    build(out)
