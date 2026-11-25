# -*- coding: utf-8 -*-
"""도감, 족보 이름 저장, 월드(방과 벽), 도전과제, 관리자 명령."""
import json
from common import *
from jokers import JOKERS
import hands as HM
import adv as ADV

PAGE = 12


def inv_text(inv):
    if inv < 10:
        return '1/%s' % ('%.1f' % inv).rstrip('0').rstrip('.')
    if inv < 10000:
        return '1/{:,}'.format(int(round(inv)))
    v = inv / 10000.0
    if v < 100:
        return '1/%s만' % ('%.1f' % v).rstrip('0').rstrip('.')
    return '1/{:,}만'.format(int(round(v)))


def short_rule(rule):
    return rule.split(' · 예)')[0]


def build_names(P, HI):
    f = P.fn('hand/names')
    for h in HI:
        tc = TIER_COLOR[h['tier']]
        d = {'n': T(h['name'], tc, True), 't': h['tier'], 'r': short_rule(h['rule'])}
        for k in range(5):
            ex = [T(h['name'], tc)]
            if k:
                ex.append(T(' ★%d' % (k + 1), 'gold'))
            ex.append(T('  +{:,}⛃'.format(h['pays'][k]), 'yellow'))
            d['s%d' % (k + 1)] = T('\n· ', 'dark_gray', extra=ex)
        d['nh'] = T(h['name'], tc, False, hover_event={'action': 'show_text', 'value': [
            T(h['name'] + '\n', tc, True), T(short_rule(h['rule']), 'white'), T('\n+{:,}⛃'.format(h['pays'][0]), 'yellow')]})
        f.append('data modify storage jb:hn h%d set value %s' % (h['id'], J(d)))


def build_dex(P, HI):
    by_t = {t: [h for h in HI if h['tier'] == t] for t in range(6)}
    for t in by_t:
        by_t[t].sort(key=lambda h: (h['pay'], h['id']))
    locks = {4: unl_stage('t4'), 5: unl_stage('t5')}
    # ---------- 첫 화면 ----------
    f = P.fn('dex/open')
    f.append('data modify storage jb:wk dx set value {}')
    f.append('execute store result storage jb:wk dx.f int 1 run scoreboard players get @s jb.found')
    f.append('execute store result storage jb:wk dx.st int 1 run scoreboard players get @s jb.stot')
    acts = []
    for t in range(6):
        tot = len(by_t[t])
        f.append('execute store result storage jb:wk dx.c%d int 1 run scoreboard players get @s jb.ft%d' % (t, t))
        f.append('scoreboard players operation #bk jv = @s jb.ft%d' % t)
        f.append('scoreboard players operation #bk jv *= #c10 jv')
        f.append('scoreboard players set #bt2 jv %d' % tot)
        f.append('scoreboard players operation #bk jv /= #bt2 jv')
        for k in range(11):
            f.append('execute if score #bk jv matches %d run data modify storage jb:wk dx merge value {f%d:"%s",e%d:"%s"}' % (k, t, '■' * k, t, '□' * (10 - k)))
        f.append('data modify storage jb:wk dx.a%d set value %d' % (t, 4000 + 100 * t))
        if t in locks:
            f.append('execute unless score @s jb.unl matches %d.. run data modify storage jb:wk dx merge value {a%d:21,c%d:"🔒",f%d:"",e%d:"코인 상점에서 해금"}' % (locks[t], t, t, t, t))
        acts.append({'label': C([T(TIER_NAME[t], TIER_COLOR[t], True), T('   $(c%d) / %d   ' % (t, tot), 'white'), T('$(f%d)' % t, TIER_COLOR[t]), T('$(e%d)' % t, 'dark_gray')]),
                     'tooltip': T('눌러서 %s 족보 보기' % TIER_NAME[t], 'gray'), 'width': 380,
                     'action': {'type': 'minecraft:run_command', 'command': '/trigger jb.menu set $(a%d)' % t}})
    acts.append(button(T('← 메뉴', 'gray'), 1, width=380))
    f.append('function jb:dex/show with storage jb:wk dx')
    body = [T('모은 족보  ', 'gray'), T('$(f) / %d' % NHANDS, 'yellow', True), T('     ★ $(st)', 'gold', True),
            T('\n같은 족보를 많이 뽑으면 별(★)이 오르고, 별마다 코인 +25%', 'gray')]
    P.add('dex/show', '$dialog show @s ' + J(dialog(T('📖 족보 도감', 'gold', True), body, acts, width=380)))
    P.add('dex/open_snd', snd('item.book.page_turn', 60, 1) + '\nfunction jb:dex/open')
    P.add('dex/locked', snd('block.note_block.bass', 70, 0.7) + '\ntellraw @s %s' % J(
        [T('🔒 ', 'gold'), T('⛃ 코인 상점의 🔓 해금에서 열 수 있어요.', 'white')]))
    P.add('dex/loadfd', '$data modify storage jb:wk fd set from storage jb:fd f.p$(pid)')
    # ---------- 등급별 쪽 ----------
    go = P.fn('dex/go')
    for t in locks:
        go.append('execute if score #m jv matches %d..%d unless score @s jb.unl matches %d.. run return run function jb:dex/locked' % (4000 + 100 * t, 4099 + 100 * t, locks[t]))
    pg = {'type': 'minecraft:multi_action', 'title': '$(tt)', 'actions': '$(a)', 'columns': 1, 'after_action': 'none', 'pause': False,
          'can_close_with_escape': True, 'exit_action': {'label': {'text': '닫기'}, 'width': 200, 'action': cmd_action(99)}}
    P.add('dex/pg', '$dialog show @s ' + J(pg).replace('"$(tt)"', '$(tt)').replace('"$(a)"', '$(a)'))
    for t in range(6):
        hs = by_t[t]
        npg = (len(hs) + PAGE - 1) // PAGE
        tc = TIER_COLOR[t]
        T2, T3, T4, T5 = STAR_T[t]
        for p in range(npg):
            code = 4000 + 100 * t + p
            go.append('execute if score #m jv matches %d run return run function jb:dex/t%dp%d' % (code, t, p))
            f = P.fn('dex/t%dp%d' % (t, p))
            f.append('data modify storage jb:wk dg set value {a:[]}')
            f.append('data modify storage jb:wk fd set value {}')
            f.append('execute store result storage jb:wk fdp.pid int 1 run scoreboard players get @s jb.pid')
            f.append('function jb:dex/loadfd with storage jb:wk fdp')
            for h in hs[p * PAGE:(p + 1) * PAGE]:
                i = h['id']
                pays = ['{:,}'.format(x) for x in h['pays']]
                rng = [(1, T2 - 1), (T2, T3 - 1), (T3, T4 - 1), (T4, T5 - 1), (T5, None)]
                for k, (lo, hi) in enumerate(rng):
                    r = '%d..%d' % (lo, hi) if hi is not None else '%d..' % lo
                    nx = '다음 별 ★%d: %s번 뽑기' % (k + 2, '{:,}'.format(rng[k + 1][0])) if k < 4 else '별을 전부 모았어요!'
                    val = {'s': (' ★%d' % (k + 1)) if k else '', 'st': '★' * (k + 1) + '☆' * (4 - k), 'pp': pays[k], 'nx': nx}
                    f.append('execute if score @s jb.h%d matches %s run data modify storage jb:wk dg merge value %s' % (i, r, J(val)))
                f.append('execute store result storage jb:wk dg.n int 1 run scoreboard players get @s jb.h%d' % i)
                f.append('data modify storage jb:wk dg.b set value "?"')
                f.append('data modify storage jb:wk dg.b set from storage jb:wk fd.b%d' % i)
                f.append('execute if score @s jb.h%d matches 1.. run function jb:dex/r%d with storage jb:wk dg' % (i, i))
                head = [T(h['name'] + '\n', tc, True), T('%s · %s\n\n' % (TIER_NAME[t], HM.FAMS[h['fam']]), tc), T(h['rule'] + '\n', 'white')]
                if h['fl']:
                    head.append(T('“%s”\n' % h['fl'], 'gray', italic=True))
                head.append(T('\n확률 %s\n' % inv_text(h['inv']), 'gray'))
                head.append(T('기본 코인 +%s⛃\n' % pays[0], 'yellow'))
                un = {'label': C([T('✘ ', 'dark_gray'), T(h['name'], 'gray'), T('   ' + short_rule(h['rule']), 'dark_gray'), T('   +%s⛃' % pays[0], 'dark_gray')]),
                      'tooltip': C(head + [T('아직 못 찾음', 'red', True)]), 'width': 560}
                f.append('execute unless score @s jb.h%d matches 1.. run data modify storage jb:wk dg.a append value %s' % (i, J(un)))
                fo = {'label': C([T('✔ ', 'green'), T(h['name'], tc, True), T('$(s)', 'gold', True), T('   ' + short_rule(h['rule']), 'gray'),
                                  T('   +$(pp)⛃', 'yellow'), T('   ×$(n)', 'aqua')]),
                      'tooltip': C(head + [T('$(st)', 'gold', True), T('  지금 +$(pp)⛃\n', 'yellow'), T('$(nx)\n\n', 'gray'),
                                           T('찾음 · $(n)번\n', 'green', True), T('처음 뽑은 숫자: $(b)', 'gold')]), 'width': 560}
                P.add('dex/r%d' % i, '$data modify storage jb:wk dg.a append value ' + J(fo))
            nav = []
            if p > 0:
                nav.append(button(T('◀ 앞 쪽', 'green'), code - 1, width=560))
            if p < npg - 1:
                nav.append(button(T('다음 쪽 ▶', 'green'), code + 1, width=560))
            nav.append(button(T('← 도감', 'aqua'), 20, width=560))
            for b in nav:
                f.append('data modify storage jb:wk dg.a append value %s' % J(b))
            f.append('data modify storage jb:wk dg.tt set value %s' % J(C([T(TIER_NAME[t], tc, True), T('  족보  (%d/%d)' % (p + 1, npg), 'white')])))
            f.append(snd('item.book.page_turn', 60, 1.1))
            f.append('function jb:dex/pg with storage jb:wk dg')
    return by_t


def build_world(P, HI, by_t, example):
    V = 'jb.v%d' % BVER

    def td(x, y, z, text, rot, scale, tags=(), lw=400):
        return ('summon text_display %s %s %s {text:%s,billboard:"fixed",Rotation:[%sf,0f],alignment:"center",background:0,shadow:1b,line_width:%d,'
                'transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[%sf,%sf,%sf]},Tags:[%s]}' % (
                    x, y, z, J(text), rot, lw, scale, scale, scale, ','.join('"%s"' % t for t in ('jb.ent', V) + tuple(tags))))
    b = P.fn('world/build')
    b.extend(['kill @e[tag=dice.ent]', 'kill @e[tag=jb.ent]', 'kill @e[tag=nr.entity]',
              'fill -20 148 -20 20 164 20 air', 'fill -16 150 -16 16 150 16 smooth_quartz', 'fill -16 149 -16 16 149 16 polished_blackstone_bricks',
              'fill -16 150 -16 16 150 -16 polished_blackstone_bricks', 'fill -16 150 16 16 150 16 polished_blackstone_bricks',
              'fill -16 150 -16 -16 150 16 polished_blackstone_bricks', 'fill 16 150 -16 16 150 16 polished_blackstone_bricks',
              'fill -16 151 -16 16 151 -16 polished_blackstone_wall', 'fill -16 151 16 16 151 16 polished_blackstone_wall',
              'fill -16 151 -16 -16 151 16 polished_blackstone_wall', 'fill 16 151 -16 16 151 16 polished_blackstone_wall',
              'fill -16 152 -16 16 158 -16 barrier', 'fill -16 152 16 16 158 16 barrier', 'fill -16 152 -16 -16 158 16 barrier', 'fill 16 152 -16 16 158 16 barrier'])
    for x in range(-12, 13, 6):
        for z in range(-12, 13, 6):
            b.append('setblock %d 150 %d sea_lantern' % (x, z))
    b.extend(['fill 0 150 -10 0 150 10 yellow_glazed_terracotta', 'setblock 0 150 0 sea_lantern',
              'fill -8 151 -15 8 159 -15 gold_block', 'fill -7 152 -15 7 158 -15 black_concrete', 'fill -8 151 -14 8 151 -13 polished_blackstone_bricks',
              'fill -7 152 -14 7 152 -14 gold_block', 'setblock 0 151 -11 polished_blackstone_bricks', 'setblock 0 152 -11 red_concrete'])
    b.append(td(0.5, 156.6, -13.95, [T('⚀ 숫자 굴리기 ⚀', 'gold', True)], 0, 3.2))
    b.append(td(0.5, 155.3, -13.95, [T('숫자 속 ', 'white'), T('족보', 'yellow', True), T('를 찾아라!', 'white')], 0, 1.6))
    b.append('summon interaction 0.5 151.85 -10.5 {width:1.2f,height:1.3f,response:1b,Tags:["jb.ent","%s","jb.btn","jb.b_roll"]}' % V)
    b.append(td(0.5, 153.4, -10.5, [T('▶ 우클릭 ◀', 'red', True)], 0, 1.3))
    # 서쪽 벽: 도감
    b.extend(['fill -15 151 -14 -15 159 14 gold_block', 'fill -15 151 -13 -15 158 13 black_concrete'])
    b.append(td(-13.95, 157.25, 0.5, [T('📖 족보 도감 📖', 'gold', True)], -90, 1.6))
    b.append(td(-13.95, 156.7, 0.5, [T('...', 'white')], -90, 0.8, ('jb.dex_h',)))

    def px(s):
        return sum(4 if ch == ' ' else (6 if ord(ch) < 128 else 9) for ch in s)
    tot_px = {}
    for t in range(6):
        tot_px[t] = sum(px(h['name']) + 13 for h in by_t[t])
    SCALE = 0.7
    TOTAL_LW = 1345.0
    raw = {t: max(150.0, tot_px[t] / 20.0) for t in range(6)}
    k = TOTAL_LW / sum(raw.values())
    z = 13.3
    for t in range(6):
        lw = int(raw[t] * k)
        w = lw * SCALE / 40.0
        zc = round(z - w / 2, 2)
        b.append(td(-13.95, 155.9, zc, [T(TIER_NAME[t], TIER_COLOR[t], True)], -90, 0.9, ('jb.bdh%d' % t,)))
        b.append(td(-13.95, 151.15, zc, [T(' ')], -90, SCALE, ('jb.bdn%d' % t,), lw=lw))
        z -= w + 0.41
    # 동쪽 벽: 최근 숫자
    b.extend(['fill 14 151 -14 14 159 14 gold_block', 'fill 14 151 -13 14 158 13 black_concrete'])
    b.append(td(13.95, 157.25, 0.5, [T('⚀ 최근 숫자 ⚀', 'gold', True)], 90, 1.6))
    for i in range(16):
        b.append(td(13.95, 151.15, round(-11.65 + 1.62 * i, 2), [T(' ')], 90, 0.88, ('jb.rb%d' % i,), lw=200))
    b.append('scoreboard players set #rbd jv 2')
    # 남쪽 벽: 하는 법
    ex_n, ex_names = example
    how = [T('⚀ 하는 법 ⚀\n', 'gold', True), T('빨간 블록 우클릭 → 숫자 9자리\n', 'white'), T('족보가 있으면 ', 'white'), T('딩!', 'yellow', True), T(' 전부 코인\n', 'white'),
           T('예) %s → ' % ex_n, 'gray')]
    for j, nm in enumerate(ex_names):
        if j:
            how.append(T(' + ', 'gray'))
        how.append(T(nm, 'white', True))
    how += [T('\n\n⛃ 코인 상점', 'green', True), T(' 더 빠르게, 알아서, 여러 개씩\n', 'white'),
            T('🔓 해금', 'gold', True), T(' 미션 · 주사위 · 🃏 조커 · 전설 · 신화\n', 'white'),
            T('★ 별', 'gold', True), T(' 같은 족보를 많이 뽑으면 코인이 늘고 ', 'white'), T('⭐ 강화', 'aqua', True),
            T('\n\n📖 목표: 족보 %d개 모으기' % NHANDS, 'yellow')]
    b.append(td(0.5, 152.6, 15.9, [C(how)], 180, 1.0))
    b.extend(['setworldspawn 0 151 11', 'time set noon', 'weather clear', 'scoreboard players set #built jv 1',
              'scoreboard players set #bver jv %d' % BVER, 'forceload remove -32 -32 32 32', 'forceload add -16 -16 16 16',
              'tp @a[scores={jb.rolls=1..}] 0.5 151 4.5 180 0', 'tp @a[scores={jb.rolls=..0}] 0.5 151 11.5 0 -10',
              'effect clear @a minecraft:slow_falling', 'execute as @a[scores={jb.pid=1..}] run function jb:player/items',
              'execute as @a[scores={jb.pid=1..}] run function jb:ms/side', 'scoreboard players set #bdt jv 99'])
    P.add('world/prepare', '''
        forceload add -32 -32 32 32
        tp @s 0.5 160 4.5 180 0
        effect give @s minecraft:slow_falling 10 0 true
        schedule function jb:world/build 40t
    ''')
    P.add('world/click', '''
        execute if data entity @s interaction if entity @s[tag=jb.b_roll] on target run function jb:roll/click
        data remove entity @s interaction
        data remove entity @s attack
    ''')
    P.add('world/slow', '''
        scoreboard players set #prt jv 0
        kill @e[tag=jb.ent,tag=!%s]
        kill @e[tag=dice.ent]
        scoreboard players add #bdt jv 1
        execute if score #bdt jv matches 4.. positioned -13 152 0 as @p run function jb:world/board_chk
        execute if score #gen jv matches 2000000000.. run function jb:hand/genwrap
    ''' % V)
    P.add('world/board_chk', '''
        execute if score @s jb.state matches 2 run return 0
        execute if score @s jb.state matches 5..6 run return 0
        scoreboard players operation #bdk jv = @s jb.found
        scoreboard players operation #bdk jv *= #c100 jv
        scoreboard players operation #bdk jv += @s jb.unl
        scoreboard players operation #bdk jv *= #c1000 jv
        scoreboard players operation #bdk jv += @s jb.pid
        execute if score #bdk jv = #bdlast jv if score #bdt jv matches ..98 run return run scoreboard players set #bdt jv 0
        scoreboard players operation #bdlast jv = #bdk jv
        function jb:world/board
    ''')
    bd = P.fn('world/board')
    bd.append('scoreboard players set #bdt jv 0')
    bd.append('execute store result storage jb:wk bh.f int 1 run scoreboard players get @s jb.found')
    bd.append('function jb:world/board_h with storage jb:wk bh')
    P.add('world/board_h', '$data modify entity @e[type=text_display,tag=jb.dex_h,limit=1] text set value %s' % J([T('모은 족보 $(f) / %d' % NHANDS, 'yellow', True)]))
    locks = {4: unl_stage('t4'), 5: unl_stage('t5')}
    for t in range(6):
        bd.append('function jb:world/bt%d' % t)
        f = P.fn('world/bt%d' % t)
        f.append('data modify storage jb:wk bn set value [""]')
        f.append('execute store result storage jb:wk bc.c int 1 run scoreboard players get @s jb.ft%d' % t)
        f.append('function jb:world/bdh%d with storage jb:wk bc' % t)
        P.add('world/bdh%d' % t, '$data modify entity @e[type=text_display,tag=jb.bdh%d,limit=1] text set value %s' % (t, J(
            [T(TIER_NAME[t] + '  ', TIER_COLOR[t], True), T('$(c)/%d' % len(by_t[t]), 'white', False)])))
        f.append('scoreboard players set #ft jv 0')
        for h in by_t[t]:
            f.append('execute if score @s jb.h%d matches 1.. run function jb:world/bd/%d' % (h['id'], h['id']))
            P.add('world/bd/%d' % h['id'], '''
                execute if score #ft jv matches 1.. run data modify storage jb:wk bn append value {"text": " · ", "color": "dark_gray"}
                data modify storage jb:wk bn append value %s
                scoreboard players add #ft jv 1
            ''' % J(T(h['name'], TIER_COLOR[t])))
        f.append('execute if score #ft jv matches 0 run data modify storage jb:wk bn set value [{text:"아직 없음",color:"dark_gray"}]')
        if t in locks:
            f.append('execute unless score @s jb.unl matches %d.. run data modify storage jb:wk bn set value [{text:"🔒 코인 상점에서 해금",color:"dark_gray"}]' % locks[t])
        f.append('data modify storage jb:wk bnc set value {text:""}')
        f.append('data modify storage jb:wk bnc.extra set from storage jb:wk bn')
        f.append('data modify entity @e[type=text_display,tag=jb.bdn%d,limit=1] text set from storage jb:wk bnc' % t)


def build_adv(P, HI):
    by_key = {h['key']: h for h in HI}
    tick = P.fn('adv/tick')
    tick.append('scoreboard players set #advt jv 0')
    tick.append('execute as @a[scores={jb.pid=1..}] unless score @s jb.state matches 2 unless score @s jb.state matches 5..6 run function jb:adv/chk')
    chk = P.fn('adv/chk')
    chk.append('execute unless entity @s[advancements={jb:root=true}] run advancement grant @s only jb:root')
    # 코인 조건용: 10억에서 멈춘 값 (그 위는 jb.cb 로 본다)
    chk.append('scoreboard players operation @s jb.cq = @s jb.coins')
    chk.append('execute if score @s jb.cb matches 1.. run scoreboard players set @s jb.cq 1000000000')
    for a in ADV.A:
        key = a['key']
        title, desc, reward = a['title'], a['desc'], a['reward']
        if a['kind'] == 'hand':
            h = by_key[a['arg']]
            desc = '족보 “%s”를 뽑아요 — %s' % (h['name'], short_rule(h['rule']))
        g = lambda cond: chk.append('execute %s unless entity @s[advancements={jb:%s=true}] run advancement grant @s only jb:%s' % (cond, key, key))
        if a['kind'] == 'stat':
            sc, n = a['arg']
            g('if score @s jb.%s matches %d..' % (sc, n))
        elif a['kind'] == 'cond':
            g(' '.join(a['arg']))
        elif a['kind'] == 'hand':
            g('if score @s jb.h%d matches 1..' % by_key[a['arg']]['id'])
        elif a['kind'] == 'tier':
            n = sum(1 for h in HI if h['tier'] == a['arg'])
            g('if score @s jb.ft%d matches %d..' % (a['arg'], n))
        elif a['kind'] == 'col':
            hs = [h for h in HI if h['tag'] == a['arg']]
            assert hs, a['arg']
            cf = P.fn('adv/col_%s' % a['arg'])
            for h in hs:
                cf.append('execute unless score @s jb.h%d matches 1.. run return 0' % h['id'])
            cf.append('advancement grant @s only jb:%s' % key)
            chk.append('execute unless entity @s[advancements={jb:%s=true}] run function jb:adv/col_%s' % (key, a['arg']))
        js = {'criteria': {'done': {'trigger': 'minecraft:impossible'}},
              'display': {'icon': {'id': 'minecraft:' + a['icon']}, 'title': {'text': title},
                          'description': [T(desc, 'white'), T('\n보상: %s⛃' % won(reward), 'gold')],
                          'frame': a['frame'], 'show_toast': key != 'root', 'announce_to_chat': False, 'hidden': bool(a['hidden'])},
              'rewards': {'function': 'jb:adv/rw/%s' % key}}
        if a['parent']:
            js['parent'] = 'jb:' + a['parent']
        else:
            js['display']['background'] = 'minecraft:gui/advancements/backgrounds/stone'
        P.extra['data/jb/advancement/%s.json' % key] = json.dumps(js, ensure_ascii=False, indent=1)
        rw = P.fn('adv/rw/%s' % key)
        rh, rl = hl(reward)
        rw.append('scoreboard players set #cgh jv %d' % rh)
        rw.append('scoreboard players set #cgl jv %d' % rl)
        rw.append('function jb:sys/addc2')
        if key != 'root':
            col = {'task': 'green', 'goal': 'aqua', 'challenge': 'light_purple'}[a['frame']]
            rw.append('tellraw @s %s' % J([T('🏆 도전과제! ', 'gold', True), T(title, col, True), T('   +%s⛃' % won(reward), 'gold', True)]))


def build_admin(P, HI):
    msg = 'tellraw @s %s' % J([T('[숫자 굴리기] ', 'yellow'), T('코인: ', 'white'), T('$(o)⛃', 'gold', True)])
    P.add('admin/show_coins', '''
        scoreboard players operation #fh jv = @s jb.cb
        scoreboard players operation #fl jv = @s jb.coins
        function jb:sys/big
        function jb:admin/show_coins2 with storage jb:wk cm
    ''')
    P.add('admin/show_coins2', '$' + msg)
    P.add('admin/coins', '''
        scoreboard players set #cg jv 100000
        function jb:sys/addc
        function jb:admin/show_coins
    ''')
    # function jb:admin/set_coins {n:12345}   (20억까지)
    P.add('admin/set_coins', '''
        $scoreboard players set #cg jv $(n)
        execute if score #cg jv matches ..-1 run scoreboard players set #cg jv 0
        scoreboard players set @s jb.coins 0
        scoreboard players set @s jb.cb 0
        function jb:sys/addc
        function jb:admin/show_coins
    ''')
    # function jb:admin/set_eok {n:500}   (억 단위로 정하기)
    P.add('admin/set_eok', '''
        $scoreboard players set #cgh jv $(n)
        execute if score #cgh jv matches ..-1 run scoreboard players set #cgh jv 0
        scoreboard players operation #cgl jv = #cgh jv
        scoreboard players operation #cgl jv %= #c10 jv
        scoreboard players operation #cgl jv *= #c100000000 jv
        scoreboard players operation #cgh jv /= #c10 jv
        scoreboard players set @s jb.coins 0
        scoreboard players set @s jb.cb 0
        function jb:sys/addc2
        function jb:admin/show_coins
    ''')
    mx = P.fn('admin/maxall')
    for sc, v in (('u1', 10), ('u2', 10), ('u3', 7), ('u4', 10), ('e1', 5), ('e2', 5), ('e4', 5), ('e5', 3), ('unl', len(UNLOCKS)), ('jslot', 4), ('autoon', 1)):
        mx.append('scoreboard players set @s jb.%s %d' % (sc, v))
    mx.append('function jb:ms/init')
    mx.append('function jb:ms/side')
    mx.append('function jb:player/items')
    mx.append('scoreboard players set #bdt jv 99')
    mx.append('tellraw @s {text:"[숫자 굴리기] 업그레이드·강화·해금을 최대로 만들었어요.",color:"yellow"}')
    P.add('admin/reset_me', '''
        function jb:hist/clear_me
        function jb:player/bb_rm_me
        advancement revoke @s from jb:root
        scoreboard players reset @s jb.pid
        tellraw @s {text:"[숫자 굴리기] 내 기록을 초기화했어요.",color:"yellow"}
    ''')
    P.add('admin/reset_all', '''
        function jb:world/prepare
        execute as @a[scores={jb.pid=1..}] run function jb:player/bb_rm_me
        advancement revoke @a from jb:root
        scoreboard players reset * jb.pid
        scoreboard players reset * jb.dv
        data remove storage jb:hist h
        data remove storage jb:fd f
        data remove storage jb:ms m
        scoreboard players reset * jb.side
        function jb:rb/init
        title @a clear
        clear @a carrot_on_a_stick
        scoreboard players set #bdt jv 99
        tellraw @a {text:"[숫자 굴리기] 모든 기록을 초기화했어요. 처음부터 시작!",color:"yellow"}
    ''')
    P.add('admin/rebuild', 'function jb:world/prepare')
    for nm in ('coins', 'maxall', 'reset_all', 'reset_me', 'rebuild'):
        P.extra['data/dice/function/admin/%s.mcfunction' % nm] = 'function jb:admin/%s\n' % nm
