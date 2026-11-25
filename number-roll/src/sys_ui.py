# -*- coding: utf-8 -*-
"""화면: 메뉴, 코인 상점, 강화, 조커, 통계, 설정, HUD."""
from common import *
from jokers import JOKERS


def secs(t):
    f = t / 20.0
    if f >= 1:
        s = ('%.1f' % f).rstrip('0').rstrip('.')
    else:
        s = ('%.2f' % f).rstrip('0').rstrip('.')
    return s + '초'


def set_cost(price):
    """#costb(10억 단위) #cost 를 정하는 명령 두 줄"""
    h, l = hl(price)
    return ['scoreboard players set #costb jv %d' % h, 'scoreboard players set #cost jv %d' % l]


def price_color(f, cost_fn, key):
    """값(#costb, #cost)과 가진 코인을 비교해 색을 정한다 (초록=살 수 있음, 빨강=부족, 금=끝)"""
    f.append('function jb:%s' % cost_fn)
    f.append('data modify storage jb:wk up.%s set value "green"' % key)
    f.append('function jb:sys/afford')
    f.append('execute if score #ok jv matches 0 run data modify storage jb:wk up.%s set value "red"' % key)
    f.append('execute if score #cost jv matches -1 run data modify storage jb:wk up.%s set value "gold"' % key)


def coins_to(f, path):
    """가진 코인을 읽기 좋은 글로 → storage jb:wk <path>"""
    f.append('scoreboard players operation #fh jv = @s jb.cb')
    f.append('scoreboard players operation #fl jv = @s jb.coins')
    f.append('function jb:sys/big')
    f.append('data modify storage jb:wk %s set from storage jb:wk cm.o' % path)


def build_menu(P):
    # ------------------------------------------------------------------
    # 트리거 분배
    # ------------------------------------------------------------------
    t = P.fn('menu/trigger')
    t.append('scoreboard players operation #m jv = @s jb.menu')
    t.append('scoreboard players set @s jb.menu 0')
    t.append('execute if score #m jv matches 99 run return run dialog clear @s')
    for n, fn in ((1, 'menu/main'), (7, 'menu/sound'), (8, 'hist/open'), (20, 'dex/open_snd'), (33, 'stats/open'),
                  (50, 'menu/coin_snd'), (60, 'menu/perk_snd'), (70, 'menu/joker_snd'),
                  (11, 'shop/buy1'), (12, 'shop/buy2'), (13, 'shop/buy3'), (14, 'shop/buy4'), (15, 'shop/unlock'),
                  (21, 'dex/locked')):
        t.append('execute if score #m jv matches %d run return run function jb:%s' % (n, fn))
    for (sc, _, _, _, _, _) in PERKS:
        t.append('execute if score #m jv matches %d run return run function jb:perk/buy_%s' % (60 + int(sc[1]), sc))
    t.append('execute if score #m jv matches 101..199 run return run function jb:joker/click')
    t.append('execute if score #m jv matches 3000..3999 run return run function jb:hist/page_t')
    t.append('execute if score #m jv matches 4000..4999 run return run function jb:dex/go')

    # ------------------------------------------------------------------
    # 📖 메뉴
    # ------------------------------------------------------------------
    f = P.fn('menu/main')
    f.append('data modify storage jb:wk mh set value {m1:{text:""},m2:{text:""},m3:{text:""}}')
    coins_to(f, 'mh.c')
    f.append('execute store result storage jb:wk mh.f int 1 run scoreboard players get @s jb.found')
    f.append('execute store result storage jb:wk mh.p int 1 run scoreboard players get @s jb.ept')
    f.append('execute store result storage jb:wk mh.st int 1 run scoreboard players get @s jb.stot')
    f.append('function jb:ms/lines')
    f.append(snd('ui.button.click', 50, 1))
    f.append('function jb:menu/main2 with storage jb:wk mh')
    body = {'text': '', 'extra': [T('⛃ $(c)', 'gold', True), T('     📖 $(f)/%d' % NHANDS, 'yellow', True), T('     ★ $(st)', 'gold', True),
                                  T('     ⭐ $(p)', 'aqua', True), '$(m1)', '$(m2)', '$(m3)']}
    acts = [button(T('📖 족보 도감', 'gold', True), 20), button(T('⌚ 기록 · 검색', 'yellow'), 8),
            button(T('📊 통계', 'aqua'), 33), button(T('⚙ 설정', 'gray'), 7)]
    s = J(dialog(T('📖 메뉴', 'gold', True), body, acts))
    for k in ('m1', 'm2', 'm3'):
        s = s.replace('"$(%s)"' % k, '$(%s)' % k)
    P.add('menu/main2', '$dialog show @s ' + s)

    # ------------------------------------------------------------------
    # ⛃ 코인 상점
    # ------------------------------------------------------------------
    ups = [('u1', COST_U1, '⚡ 속도', '숫자가 다 나올 때까지 걸리는 시간이 줄어요',
            ['%s' % secs(x) for x in SPEED_T]),
           ('u2', COST_U2, '⟳ 자동 굴리기', '알아서 계속 굴려요 · 다음 굴림까지 쉬는 시간이 줄어요',
            ['없음'] + ['쉬는 시간 %s' % secs(x) for x in AUTO_END[1:]]),
           ('u3', COST_U3, '✚ 여러 개', '한 번에 숫자 여러 개를 굴려요',
            ['%d개' % (i + 1) for i in range(8)]),
           ('u4', COST_U4, '⛃ 부스트', '받는 코인이 전부 늘어요',
            ['+%d%%' % (50 * i) for i in range(11)])]
    f = P.fn('menu/coin')
    f.append('data modify storage jb:wk up set value {}')
    coins_to(f, 'up.c')
    acts = []
    for n, (sc, costs, nm, tip, eff) in enumerate(ups, 1):
        mx = len(costs)
        f.append('execute store result storage jb:wk up.l%d int 1 run scoreboard players get @s jb.%s' % (n, sc))
        cf = P.fn('shop/cost%d' % n)
        cf.append('scoreboard players set #costb jv 0')
        cf.append('scoreboard players set #cost jv -1')
        for lv in range(mx + 1):
            if lv < mx:
                assert costs[lv] < 10 ** 9
                cf.append('execute if score @s jb.%s matches %d run scoreboard players set #cost jv %d' % (sc, lv, costs[lv]))
                d = '%s → %s' % (eff[lv], eff[lv + 1])
                k = won(costs[lv]) + '⛃'
            else:
                d = '%s (최대)' % eff[lv]
                k = 'MAX'
            f.append('execute if score @s jb.%s matches %d run data modify storage jb:wk up merge value {d%d:"%s",k%d:"%s"}' % (sc, lv, n, d, n, k))
        price_color(f, 'shop/cost%d' % n, 'kc%d' % n)
        acts.append(button([T(nm + '  ', 'white', True), T('$(l%d)/%d   ' % (n, mx), 'gray'), T('$(d%d)   ' % n, 'aqua'),
                            {'text': '$(k%d)' % n, 'color': '$(kc%d)' % n, 'bold': True}], 10 + n, tip, width=360))
        b = P.fn('shop/buy%d' % n)
        b.append('function jb:shop/cost%d' % n)
        b.append('execute if score #cost jv matches -1 run return run function jb:menu/coin')
        b.append('function jb:sys/afford')
        b.append('execute if score #ok jv matches 0 run return run function jb:shop/poor')
        b.append('function jb:sys/spend')
        b.append('scoreboard players add @s jb.%s 1' % sc)
        b.append('scoreboard players add @s jb.ubuy 1')
        b.append(snd('entity.player.levelup', 70, 1.4))
        if sc == 'u2':
            b.append('execute if score @s jb.u2 matches 1 run scoreboard players set @s jb.autoon 1')
            b.append('function jb:player/items')
        b.append('function jb:menu/coin')
    # 해금
    f.append('data modify storage jb:wk up merge value {un:"모두 열었어요",uk:"",ut:""}')
    uc = P.fn('shop/costu')
    uc.append('scoreboard players set #costb jv 0')
    uc.append('scoreboard players set #cost jv -1')
    road = []
    for i, (key, nm, price, tip) in enumerate(UNLOCKS):
        h, l = hl(price)
        uc.append('execute if score @s jb.unl matches %d run scoreboard players set #cost jv %d' % (i, l))
        if h:
            uc.append('execute if score @s jb.unl matches %d run scoreboard players set #costb jv %d' % (i, h))
        f.append('execute if score @s jb.unl matches %d run data modify storage jb:wk up merge value {un:"%s",uk:"%s⛃",ut:"%s"}' % (i, nm, won(price), tip))
        road.append(T('\n%s  %s⛃' % (nm, won(price)), 'gray'))
    price_color(f, 'shop/costu', 'ukc')
    acts.append(button([T('🔓 다음 해금  ', 'white', True), T('$(un)   ', 'yellow'), {'text': '$(uk)', 'color': '$(ukc)', 'bold': True}], 15,
                       [T('$(ut)', 'white'), T('\n\n해금 순서', 'gold')] + road, width=360))
    f.append('function jb:menu/coin2 with storage jb:wk up')
    P.add('menu/coin2', '$dialog show @s ' + J(dialog(T('⛃ 코인 상점', 'green', True), T('⛃ $(c)', 'gold', True), acts)))
    P.add('menu/coin_snd', snd('ui.button.click', 50, 1) + '\nfunction jb:menu/coin')
    P.add('shop/poor', snd('block.note_block.bass', 70, 0.7) + '\nfunction jb:menu/coin')
    # 해금 사기
    u = P.fn('shop/unlock')
    u.append('function jb:shop/costu')
    u.append('execute if score #cost jv matches -1 run return run function jb:menu/coin')
    u.append('function jb:sys/afford')
    u.append('execute if score #ok jv matches 0 run return run function jb:shop/poor')
    u.append('function jb:sys/spend')
    u.append('scoreboard players add @s jb.unl 1')
    u.append('scoreboard players add @s jb.ubuy 1')
    for i, (key, nm, price, tip) in enumerate(UNLOCKS, 1):
        g = P.fn('shop/un_%s' % key)
        u.append('execute if score @s jb.unl matches %d run function jb:shop/un_%s' % (i, key))
        g.append('tellraw @s %s' % J(C([T('🔓 해금! ', 'gold', True), T(nm, 'yellow', True), T('  ' + tip, 'white')])))
        g.append('title @s times 5 40 10')
        g.append('title @s subtitle %s' % J(T(tip, 'white')))
        g.append('title @s title %s' % J(T('🔓 ' + nm, 'gold', True)))
        if key.startswith('ms'):
            g.append('function jb:ms/new%s' % key[2])
            g.append('function jb:ms/side')
        if key == 'dice':
            g.append('function jb:player/items')
        if key.startswith('jk'):
            g.append('scoreboard players set @s jb.jslot %s' % key[2])
            g.append('function jb:player/items')
        if key in ('t4', 't5'):
            g.append('scoreboard players set #bdt jv 99')
    u.append(snd('ui.toast.challenge_complete', 80, 1.2))
    u.append('dialog clear @s')

    # ------------------------------------------------------------------
    # ⭐ 강화
    # ------------------------------------------------------------------
    f = P.fn('menu/perk')
    f.append('data modify storage jb:wk up set value {}')
    f.append('execute store result storage jb:wk up.p int 1 run scoreboard players get @s jb.ept')
    acts = []
    for n, (sc, icon, nm, costs, tip, eff) in enumerate(PERKS, 1):
        mx = len(costs)
        f.append('execute store result storage jb:wk up.m%d int 1 run scoreboard players get @s jb.%s' % (n, sc))
        cf = P.fn('perk/cost_%s' % sc)
        cf.append('scoreboard players set #pcost jv -1')
        for lv in range(mx + 1):
            if lv < mx:
                cf.append('execute if score @s jb.%s matches %d run scoreboard players set #pcost jv %d' % (sc, lv, costs[lv]))
                d = '%s → %s' % (eff[lv], eff[lv + 1])
                k = '⭐%d' % costs[lv]
            else:
                d = eff[lv]
                k = 'MAX'
            f.append('execute if score @s jb.%s matches %d run data modify storage jb:wk up merge value {e%d:"%s",q%d:"%s"}' % (sc, lv, n, d, n, k))
        f.append('function jb:perk/cost_%s' % sc)
        f.append('data modify storage jb:wk up.qc%d set value "aqua"' % n)
        f.append('execute if score @s jb.ept < #pcost jv run data modify storage jb:wk up.qc%d set value "red"' % n)
        f.append('execute if score #pcost jv matches -1 run data modify storage jb:wk up.qc%d set value "gold"' % n)
        acts.append(button([T('%s %s  ' % (icon, nm), 'white', True), T('$(m%d)/%d   ' % (n, mx), 'gray'), T('$(e%d)   ' % n, 'aqua'),
                            {'text': '$(q%d)' % n, 'color': '$(qc%d)' % n, 'bold': True}], 60 + int(sc[1]), tip, width=380))
        b = P.fn('perk/buy_%s' % sc)
        b.append('function jb:perk/cost_%s' % sc)
        b.append('execute if score #pcost jv matches -1 run return run function jb:menu/perk')
        b.append('execute if score @s jb.ept < #pcost jv run return run function jb:perk/poor')
        b.append('scoreboard players operation @s jb.ept -= #pcost jv')
        b.append('scoreboard players add @s jb.%s 1' % sc)
        b.append('scoreboard players add @s jb.pbuy 1')
        b.append(snd('entity.player.levelup', 70, 1.6))
        b.append(snd('block.amethyst_block.chime', 80, 1.2))
        b.append('function jb:menu/perk')
    f.append('function jb:menu/perk2 with storage jb:wk up')
    body = {'text': '', 'extra': [T('⭐ $(p)', 'aqua', True), T('   족보의 별(★)이 하나 오를 때마다 ⭐ +1', 'gray')]}
    P.add('menu/perk2', '$dialog show @s ' + J(dialog(T('⭐ 강화', 'aqua', True), body, acts, width=380)))
    P.add('menu/perk_snd', snd('ui.button.click', 50, 1) + '\nfunction jb:menu/perk')
    P.add('perk/poor', snd('block.note_block.bass', 70, 0.7) + '\nfunction jb:menu/perk')

    # ------------------------------------------------------------------
    # 🃏 조커
    # ------------------------------------------------------------------
    f = P.fn('menu/joker')
    f.append('data modify storage jb:wk up set value {}')
    coins_to(f, 'up.c')
    f.append('execute store result storage jb:wk up.q int 1 run scoreboard players get @s jb.jeq')
    f.append('execute store result storage jb:wk up.s int 1 run scoreboard players get @s jb.jslot')
    acts = []
    click = P.fn('joker/click')
    for jk in JOKERS:
        n = jk['id']
        f.append('data modify storage jb:wk up merge value {s%d:"%s⛃",c%d:"green"}' % (n, won(jk['price']), n))
        f.append('execute unless score @s jb.j%d matches 1.. run function jb:joker/mp%d' % (n, n))
        mp = P.fn('joker/mp%d' % n)
        mp.extend(set_cost(jk['price']))
        mp.append('function jb:sys/afford')
        mp.append('execute if score #ok jv matches 0 run data modify storage jb:wk up.c%d set value "red"' % n)
        f.append('execute if score @s jb.j%d matches 1 run data modify storage jb:wk up merge value {s%d:"보유 · 눌러서 끼기",c%d:"gray"}' % (n, n, n))
        f.append('execute if score @s jb.j%d matches 2 run data modify storage jb:wk up merge value {s%d:"✔ 끼는 중",c%d:"yellow"}' % (n, n, n))
        tip = [T(jk['desc'], 'white')]
        if jk.get('tip'):
            tip.append(T('\n' + jk['tip'], 'gray'))
        acts.append(button([T('%s %s  ' % (jk['icon'], jk['name']), 'white', True), T(jk['desc'] + '   ', 'aqua'),
                            {'text': '$(s%d)' % n, 'color': '$(c%d)' % n, 'bold': True}], 100 + n, tip, width=460))
        click.append('execute if score #m jv matches %d run return run function jb:joker/c%d' % (100 + n, n))
        c = P.fn('joker/c%d' % n)
        c.append('execute if score @s jb.j%d matches 2 run return run function jb:joker/off%d' % (n, n))
        c.append('execute if score @s jb.j%d matches 1 run return run function jb:joker/on%d' % (n, n))
        c.extend(set_cost(jk['price']))
        c.append('function jb:sys/afford')
        c.append('execute if score #ok jv matches 0 run return run function jb:joker/poor')
        c.append('function jb:sys/spend')
        c.append('scoreboard players set @s jb.j%d 1' % n)
        c.append('scoreboard players add @s jb.jown 1')
        c.append(snd('entity.player.levelup', 70, 1.2))
        c.append('execute if score @s jb.jeq < @s jb.jslot run return run function jb:joker/on%d' % n)
        c.append('function jb:menu/joker')
        on = P.fn('joker/on%d' % n)
        on.append('execute if score @s jb.jeq >= @s jb.jslot run return run function jb:joker/full')
        on.append('scoreboard players set @s jb.j%d 2' % n)
        on.append('scoreboard players add @s jb.jeq 1')
        on.append(snd('item.armor.equip_gold', 80, 1.2))
        on.append('function jb:menu/joker')
        off = P.fn('joker/off%d' % n)
        off.append('scoreboard players set @s jb.j%d 1' % n)
        off.append('scoreboard players remove @s jb.jeq 1')
        off.append(snd('item.armor.equip_leather', 80, 0.9))
        off.append('function jb:menu/joker')
    f.append('function jb:menu/joker2 with storage jb:wk up')
    body = {'text': '', 'extra': [T('🃏 $(q) / $(s)칸', 'light_purple', True), T('     ⛃ $(c)', 'gold', True),
                                  T('\n조건이 맞는 숫자에서 코인을 더 받아요 · 여러 장을 끼면 서로 곱해져요', 'gray')]}
    P.add('menu/joker2', '$dialog show @s ' + J(dialog(T('🃏 조커', 'light_purple', True), body, acts, width=460)))
    P.add('menu/joker_snd', snd('ui.button.click', 50, 1) + '\nfunction jb:menu/joker')
    P.add('joker/poor', snd('block.note_block.bass', 70, 0.7) + '\nfunction jb:menu/joker')
    P.add('joker/full', snd('block.note_block.bass', 70, 0.7) + '\ntellraw @s %s\nfunction jb:menu/joker' % J(
        [T('🃏 ', 'light_purple'), T('칸이 꽉 찼어요. 끼고 있는 조커를 먼저 빼 주세요.', 'white')]))
    # ---- 조커 효과 ----
    # 부분 조커: 그 부분 족보의 코인이 몇 배가 된다 (#p0..#p3, 덤 #px) → #pay 를 다시 더한다
    parts = P.fn('joker/parts')
    parts.append('scoreboard players set #px jv 0')
    wholes = P.fn('joker/wholes')
    for jk in JOKERS:
        n, k = jk['id'], jk['kind']
        code = []
        if k[0] == 'part':
            which, m = k[1], k[2]
            if which == 'p0':
                code.append('scoreboard players operation #p0 jv *= #c%d jv' % m)
            elif which == 'p12':
                code.append('scoreboard players operation #p1 jv *= #c%d jv' % m)
                code.append('scoreboard players operation #p2 jv *= #c%d jv' % m)
            elif which == 'p3':
                code.append('scoreboard players operation #p3 jv *= #c%d jv' % m)
            else:
                code.append('scoreboard players operation #t jv = #pf_%s jv' % which)
                code.append('scoreboard players operation #t jv *= #c%d jv' % (m - 1))
                code.append('scoreboard players operation #px jv += #t jv')
            parts.append('execute if score @s jb.j%d matches 2 run function jb:joker/f%d' % (n, n))
            P.fn('joker/f%d' % n).extend(code)
            continue
        if k[0] == 'mission':
            continue
        if k[0] == 'digit':
            code += ['scoreboard players operation #m jv = #q%d jv' % k[1], 'scoreboard players operation #m jv *= #c%d jv' % k[2],
                     'scoreboard players add #m jv 100']
        elif k[0] == 'nh_le':
            code += ['execute unless score #nh jv matches ..%d run return 0' % k[1], 'scoreboard players set #m jv %d' % k[2]]
        elif k[0] == 'nh_ge':
            code += ['execute unless score #nh jv matches %d.. run return 0' % k[1], 'scoreboard players set #m jv %d' % k[2]]
        elif k[0] == 'tiers':
            code.append('scoreboard players set #jt jv 0')
            for t in range(6):
                code.append('execute if score #t%d jv = #gen jv run scoreboard players add #jt jv 1' % t)
            code += ['execute unless score #jt jv matches %d.. run return 0' % k[1], 'scoreboard players set #m jv %d' % k[2]]
        elif k[0] == 'manual':
            code += ['execute unless score #man jv matches 1 run return 0', 'scoreboard players set #m jv %d' % k[1]]
        elif k[0] == 'auto':
            code += ['execute if score #man jv matches 1 run return 0', 'scoreboard players set #m jv %d' % k[1]]
        elif k[0] in ('found', 'stars'):
            code += ['scoreboard players operation #m jv = @s jb.%s' % ('found' if k[0] == 'found' else 'stot'),
                     'scoreboard players operation #m jv /= #c%d jv' % k[1], 'scoreboard players operation #m jv *= #c%d jv' % k[2],
                     'scoreboard players add #m jv 100']
        elif k[0] == 'cdig':
            code += ['scoreboard players operation #m jv = #cdig jv', 'scoreboard players operation #m jv *= #c%d jv' % k[1],
                     'scoreboard players add #m jv 100']
        else:
            raise ValueError(k)
        code.append('execute if score #m jv matches 101.. run function jb:roll/vmul')
        wholes.append('execute if score @s jb.j%d matches 2 run function jb:joker/f%d' % (n, n))
        P.fn('joker/f%d' % n).extend(code)
    for x in ('p0', 'p1', 'p2', 'p3', 'px'):
        parts.append('scoreboard players operation #pay jv %s #%s jv' % ('=' if x == 'p0' else '+=', x))

    # ------------------------------------------------------------------
    # ⚙ 설정
    # ------------------------------------------------------------------
    P.add('menu/sound', '''
        execute unless score @s jb.vol matches 0..100 run scoreboard players set @s jb.vol 100
        execute store result storage jb:wk sv2.vol int 1 run scoreboard players get @s jb.vol
        data modify storage jb:wk sv2.v set value "$(v)"
        data modify storage jb:wk sv2 merge value {h:"켜짐",hc:"green"}
        execute if score @s jb.mhero matches 1 run data modify storage jb:wk sv2 merge value {h:"꺼짐",hc:"red"}
        data modify storage jb:wk sv2 merge value {f:"켜짐",fc:"green"}
        execute if score @s jb.mfw matches 1 run data modify storage jb:wk sv2 merge value {f:"꺼짐",fc:"red"}
        data modify storage jb:wk sv2 merge value {a:"희귀 이상",ac:"aqua"}
        execute if score @s jb.achat matches 1 run data modify storage jb:wk sv2 merge value {a:"영웅 이상",ac:"light_purple"}
        execute if score @s jb.achat matches 2 run data modify storage jb:wk sv2 merge value {a:"전설 이상",ac:"gold"}
        execute if score @s jb.achat matches 3 run data modify storage jb:wk sv2 merge value {a:"끔",ac:"red"}
        execute if score @s jb.achat matches 4 run data modify storage jb:wk sv2 merge value {a:"전부",ac:"green"}
        function jb:menu/sound2 with storage jb:wk sv2
    ''')

    def dyn(n):
        return {'type': 'minecraft:dynamic/run_command', 'template': 'trigger jb.vset set $(v)%d' % n}
    d = {'type': 'minecraft:multi_action', 'title': T('⚙ 설정', 'yellow', True),
         'inputs': [{'type': 'minecraft:number_range', 'key': 'v', 'label': T('🔊 소리 (0~100)', 'yellow'), 'width': 300,
                     'start': 0, 'end': 100, 'step': 1, 'initial': '$(vol)'}],
         'actions': [
             {'label': T('🔊 소리 적용', 'yellow', True), 'width': 300, 'action': dyn(0)},
             {'label': C([T('큰 족보 소리  ', 'white'), {'text': '$(h)', 'color': '$(hc)', 'bold': True}]), 'width': 300, 'action': dyn(1)},
             {'label': C([T('폭죽  ', 'white'), {'text': '$(f)', 'color': '$(fc)', 'bold': True}]), 'width': 300, 'action': dyn(2)},
             {'label': C([T('채팅에 보여 줄 숫자  ', 'white'), {'text': '$(a)', 'color': '$(ac)', 'bold': True}]), 'width': 300, 'action': dyn(3),
              'tooltip': T('화면에 크게 나온 숫자는 늘 보여 주고, 나머지는 이 등급 이상만 채팅에 적어요', 'gray')},
             {'label': T('← 메뉴', 'gray'), 'width': 300, 'action': dyn(4)}],
         'columns': 1, 'after_action': 'none', 'pause': False, 'can_close_with_escape': True,
         'exit_action': {'label': {'text': '닫기'}, 'width': 200, 'action': dyn(5)}}
    P.add('menu/sound2', '$dialog show @s ' + J(d).replace('"$(vol)"', '$(vol)'))
    P.add('snd/vset', '''
        scoreboard players operation #va jv = @s jb.vset
        scoreboard players operation #va jv %%= #c10 jv
        scoreboard players operation @s jb.vol = @s jb.vset
        scoreboard players operation @s jb.vol /= #c10 jv
        scoreboard players set @s jb.vset -1
        execute if score @s jb.vol matches 101.. run scoreboard players set @s jb.vol 100
        execute if score @s jb.vol matches 0 run scoreboard players set @s jb.muted 1
        execute if score #va jv matches 1 run return run function jb:snd/tog_hero
        execute if score #va jv matches 2 run return run function jb:snd/tog_fw
        execute if score #va jv matches 3 run return run function jb:snd/tog_chat
        execute if score #va jv matches 4 run return run function jb:menu/main
        execute if score #va jv matches 5 run return run dialog clear @s
        %s
        function jb:menu/sound
    ''' % snd('block.note_block.chime', 60, 1.6))
    for nm, sc, mx in (('hero', 'mhero', 2), ('fw', 'mfw', 2), ('chat', 'achat', 5)):
        P.add('snd/tog_%s' % nm, '''
            scoreboard players add @s jb.%s 1
            execute if score @s jb.%s matches %d.. run scoreboard players set @s jb.%s 0
            %s
            function jb:menu/sound
        ''' % (sc, sc, mx, sc, snd('block.note_block.chime', 60, 1.6)))

    # ------------------------------------------------------------------
    # 📊 통계
    # ------------------------------------------------------------------
    P.add('stats/open', '''
        data modify storage jb:wk st set value {}
        scoreboard players operation #s jv = @s jb.ptk
        scoreboard players operation #s jv /= #c20 jv
        scoreboard players operation #h jv = #s jv
        scoreboard players operation #h jv /= #c3600 jv
        scoreboard players operation #s jv %%= #c3600 jv
        scoreboard players operation #s jv /= #c60 jv
        execute store result storage jb:wk st.h int 1 run scoreboard players get #h jv
        execute store result storage jb:wk st.m int 1 run scoreboard players get #s jv
        scoreboard players operation #fn jv = @s jb.rolls
        function jb:sys/comma
        data modify storage jb:wk st.r set from storage jb:wk cm.o
        execute store result storage jb:wk st.f int 1 run scoreboard players get @s jb.found
        execute store result storage jb:wk st.sx int 1 run scoreboard players get @s jb.stot
        execute store result storage jb:wk st.s5 int 1 run scoreboard players get @s jb.s5n
        scoreboard players operation #fn jv = @s jb.rr
        function jb:sys/comma
        data modify storage jb:wk st.rr set from storage jb:wk cm.o
        execute store result storage jb:wk st.md int 1 run scoreboard players get @s jb.mdone
        execute store result storage jb:wk st.jo int 1 run scoreboard players get @s jb.jown
        execute store result storage jb:wk st.mn int 1 run scoreboard players get @s jb.mxn
        scoreboard players set #fh jv 0
        scoreboard players operation #fl jv = @s jb.mxr
        execute if score #fl jv matches 1000000000.. run scoreboard players set #fh jv 1
        execute if score #fl jv matches 1000000000.. run scoreboard players remove #fl jv 1000000000
        execute if score @s jb.mxr matches 2000000000.. run scoreboard players set #fh jv 2
        execute if score @s jb.mxr matches 2000000000.. run scoreboard players set #fl jv 0
        function jb:sys/big
        data modify storage jb:wk st.mr set from storage jb:wk cm.o
        data modify storage jb:wk st.mx set value ""
        execute if score @s jb.mxr matches 2000000000.. run data modify storage jb:wk st.mx set value " 이상"
        scoreboard players operation #fh jv = @s jb.rch
        scoreboard players operation #fl jv = @s jb.rc
        function jb:sys/big
        data modify storage jb:wk st.rc set from storage jb:wk cm.o
        scoreboard players operation #fh jv = @s jb.tch
        scoreboard players operation #fl jv = @s jb.tcl
        function jb:sys/big
        data modify storage jb:wk st.tc set from storage jb:wk cm.o
        data modify storage jb:wk st.b set value {text:"아직 없음",color:"gray"}
        data modify storage jb:wk st.bn set value ""
        execute if score @s jb.topid matches 1.. run function jb:stats/top
        function jb:stats/show with storage jb:wk st
        %s
    ''' % snd('item.book.page_turn', 60, 1))
    P.add('stats/top', '''
        execute store result storage jb:wk bi.i int 1 run scoreboard players get @s jb.topid
        function jb:stats/top2 with storage jb:wk bi
        scoreboard players operation #n jv = @s jb.topn
        function jb:num/d9
        function jb:num/ns
        data modify storage jb:wk st.bn set from storage jb:wk r.ns
    ''')
    P.add('stats/top2', '$data modify storage jb:wk st.b set from storage jb:hn h$(i).n')
    body = {'text': '', 'extra': [
        T('⏱ 플레이 시간  ', 'gray'), T('$(h)시간 $(m)분\n', 'white', True),
        T('⚀ 굴린 숫자  ', 'gray'), T('$(r)개\n', 'white', True),
        T('📖 족보 도감  ', 'gray'), T('$(f) / %d\n' % NHANDS, 'yellow', True),
        T('★ 모은 별  ', 'gray'), T('$(sx)개', 'gold', True), T('   (★5 족보 $(s5)개)\n', 'gray'),
        T('📋 미션 성공  ', 'gray'), T('$(md)번\n', 'green', True),
        T('🃏 가진 조커  ', 'gray'), T('$(jo)장\n', 'light_purple', True),
        T('♛ 최고 족보  ', 'gray'), '$(b)', T('  $(bn)\n', 'white'),
        T('✦ 숫자 하나로  ', 'gray'), T('족보 $(mn)개', 'white', True), T(' · ', 'dark_gray'), T('+$(mr)⛃$(mx)\n', 'gold', True),
        T('\n최근 1분 동안\n', 'yellow', True), T('  ⚀ $(rr)개   ', 'white'), T('⛃ +$(rc)\n', 'gold'),
        T('\n굴려서 번 코인 (전체)\n', 'yellow', True), T('  ⛃ $(tc)', 'gold')]}
    acts = [button(T('⌚ 숫자 기록', 'gold'), 8, width=200), button(T('← 메뉴', 'gray'), 1, width=200)]
    P.add('stats/show', '$dialog show @s ' + J(dialog(T('📊 통계', 'aqua', True), body, acts, columns=2, width=380)).replace('"$(b)"', '$(b)'))
    # 번 코인 적기: #cgh #cgl (방금 준 코인), #sen (굴린 숫자 수)
    P.add('stats/earn', '''
        scoreboard players operation @s jb.wc += #cgl jv
        execute if score @s jb.wc matches 1000000000.. run scoreboard players add @s jb.wch 1
        execute if score @s jb.wc matches 1000000000.. run scoreboard players remove @s jb.wc 1000000000
        scoreboard players operation @s jb.wch += #cgh jv
        scoreboard players operation @s jb.wr += #sen jv
        scoreboard players operation @s jb.tcl += #cgl jv
        execute if score @s jb.tcl matches 1000000000.. run scoreboard players add @s jb.tch 1
        execute if score @s jb.tcl matches 1000000000.. run scoreboard players remove @s jb.tcl 1000000000
        scoreboard players operation @s jb.tch += #cgh jv
    ''')
    P.add('stats/minute', '''
        scoreboard players set #stt jv 0
        execute as @a run function jb:stats/minute1
    ''')
    P.add('stats/minute1', '''
        scoreboard players operation @s jb.rc = @s jb.wc
        scoreboard players operation @s jb.rch = @s jb.wch
        scoreboard players operation @s jb.rr = @s jb.wr
        scoreboard players set @s jb.wc 0
        scoreboard players set @s jb.wch 0
        scoreboard players set @s jb.wr 0
        execute if score @s jb.pid matches 1.. run function jb:ms/refresh
    ''')

    # ------------------------------------------------------------------
    # HUD: 아래 줄(actionbar)과 위 막대(bossbar)
    # ------------------------------------------------------------------
    f = P.fn('player/hud')
    f.append('execute if entity @s[type=player,level=1..] run xp set @s 0 levels')
    f.append('function jb:player/bar')
    f.append('execute if score @s jb.hudw matches 1.. run return run scoreboard players remove @s jb.hudw 4')
    f.append('data modify storage jb:wk h set value {a:"",b:""}')
    coins_to(f, 'h.c')
    f.append('execute store result storage jb:wk h.f int 1 run scoreboard players get @s jb.found')
    f.append('execute if score @s jb.autoon matches 1 if score @s jb.u2 matches 1.. run function jb:player/hud_a')
    f.append('function jb:player/hud_b')
    f.append('function jb:player/hud2 with storage jb:wk h')
    P.add('player/hud2', '$title @s actionbar ' + J(C([T('⛃ $(c)', 'gold', True), T('   📖 $(f)/%d' % NHANDS, 'yellow'), T('$(a)', 'green'), T('$(b)', 'green', True)])))
    P.add('player/hud_a', '''
        scoreboard players operation #fh jv = @s jb.ashowb
        scoreboard players operation #fl jv = @s jb.ashow
        function jb:sys/short
        function jb:player/hud_a2 with storage jb:wk sh
    ''')
    P.add('player/hud_a2', '$data modify storage jb:wk h.a set value "   ⟳ +$(o)⛃"')
    hb = P.fn('player/hud_b')
    for n in (1, 2, 3, 4):
        hb.append('function jb:shop/cost%d' % n)
        hb.append('execute if score #cost jv matches 0.. if score @s jb.coins >= #cost jv run return run data modify storage jb:wk h.b set value "   🛒 살 수 있음"')
        hb.append('execute if score #cost jv matches 0.. if score @s jb.cb matches 1.. run return run data modify storage jb:wk h.b set value "   🛒 살 수 있음"')
    hb.append('function jb:shop/costu')
    hb.append('execute if score #cost jv matches 0.. run function jb:sys/afford')
    hb.append('execute if score #cost jv matches 0.. if score #ok jv matches 1 run return run data modify storage jb:wk h.b set value "   🔓 해금 가능"')
    hb.append('execute if score @s jb.jslot matches 1.. if score @s jb.jown matches ..%d run function jb:player/hud_j' % (len(JOKERS) - 1))
    # 아직 없는 조커 중 제일 싼 것을 살 수 있나
    hj = P.fn('player/hud_j')
    for jk in sorted(JOKERS, key=lambda j: j['price']):
        hj.append('execute if score @s jb.j%d matches 0 run return run function jb:joker/hb%d' % (jk['id'], jk['id']))
        g = P.fn('joker/hb%d' % jk['id'])
        g.extend(set_cost(jk['price']))
        g.append('function jb:sys/afford')
        g.append('execute if score #ok jv matches 1 run data modify storage jb:wk h.b set value "   🃏 조커 살 수 있음"')
    # 자동으로 번 코인: 2초마다 모아서 보여 준다
    P.add('player/pulse', '''
        scoreboard players operation @s jb.ashow = @s jb.asum
        scoreboard players operation @s jb.ashowb = @s jb.asumb
        scoreboard players set @s jb.asum 0
        scoreboard players set @s jb.asumb 0
    ''')
    # 위 막대: 다음 해금까지
    f = P.fn('player/bar')
    f.append('data modify storage jb:wk bb set value {}')
    f.append('execute store result storage jb:wk bb.pid int 1 run scoreboard players get @s jb.pid')
    f.append('function jb:shop/costu')
    f.append('execute if score #cost jv matches -1 run return run function jb:player/bar_dex')
    # 값이 10억을 넘나들면 억 단위로 맞춘다
    f.append('scoreboard players operation #bv jv = @s jb.coins')
    f.append('scoreboard players operation #bm jv = #cost jv')
    f.append('scoreboard players set #bu jv 0')
    f.append('execute if score #costb jv matches 1.. run scoreboard players set #bu jv 1')
    f.append('execute if score @s jb.cb matches 1.. run scoreboard players set #bu jv 1')
    f.append('execute if score #bu jv matches 1 run function jb:player/bar_u')
    f.append('scoreboard players operation #bv jv < #bm jv')
    f.append('execute store result storage jb:wk bb.x int 1 run scoreboard players get #bv jv')
    f.append('execute store result storage jb:wk bb.m int 1 run scoreboard players get #bm jv')
    for i, (key, nm, price, tip) in enumerate(UNLOCKS):
        f.append('execute if score @s jb.unl matches %d run data modify storage jb:wk bb merge value {n:"%s",k:"%s"}' % (i, nm, won(price)))
    f.append('scoreboard players operation #fh jv = @s jb.cb')
    f.append('scoreboard players operation #fl jv = @s jb.coins')
    f.append('function jb:sys/short')
    f.append('data modify storage jb:wk bb.v set from storage jb:wk sh.o')
    f.append('data modify storage jb:wk bb.col set value "yellow"')
    f.append('function jb:sys/afford')
    f.append('execute if score #ok jv matches 1 run data modify storage jb:wk bb.col set value "green"')
    f.append('function jb:player/bar2 with storage jb:wk bb')
    P.add('player/bar_u', '''
        scoreboard players operation #bv jv = @s jb.cb
        scoreboard players operation #bv jv < #c2000000 jv
        scoreboard players operation #bv jv *= #c1000 jv
        scoreboard players operation #t jv = @s jb.coins
        scoreboard players operation #t jv /= #c1000000 jv
        scoreboard players operation #bv jv += #t jv
        scoreboard players operation #bm jv = #costb jv
        scoreboard players operation #bm jv *= #c1000 jv
        scoreboard players operation #t jv = #cost jv
        scoreboard players operation #t jv /= #c1000000 jv
        scoreboard players operation #bm jv += #t jv
        execute if score #bm jv matches ..0 run scoreboard players set #bm jv 1
    ''')
    P.add('player/bar2', '''
        $execute store success score #bbn jv run bossbar add jb:p$(pid) ""
        $bossbar set jb:p$(pid) players @s
        $bossbar set jb:p$(pid) color $(col)
        $bossbar set jb:p$(pid) max $(m)
        $bossbar set jb:p$(pid) value $(x)
        $bossbar set jb:p$(pid) name %s
    ''' % J(C([T('🔓 다음 해금  ', 'gold', True), T('$(n)', 'yellow', True), T('   $(v) / $(k)⛃', 'white')])))
    P.add('player/bar_dex', '''
        execute store result storage jb:wk bb.x int 1 run scoreboard players get @s jb.found
        function jb:player/bar3 with storage jb:wk bb
    ''')
    P.add('player/bar3', '''
        $execute store success score #bbn jv run bossbar add jb:p$(pid) ""
        $bossbar set jb:p$(pid) players @s
        $bossbar set jb:p$(pid) color purple
        $bossbar set jb:p$(pid) max %d
        $bossbar set jb:p$(pid) value $(x)
        $bossbar set jb:p$(pid) name %s
    ''' % (NHANDS, J([T('📖 족보 도감  ', 'gold', True), T('$(x) / %d' % NHANDS, 'yellow', True)])))
    P.add('player/bb_rm', '$bossbar remove jb:p$(pid)\n$bossbar remove jb:lv$(pid)')
    P.add('player/bb_rm_me', '''
        execute store result storage jb:wk bbr.pid int 1 run scoreboard players get @s jb.pid
        function jb:player/bb_rm with storage jb:wk bbr
    ''')
    # 짧은 숫자 (#fh ×10억 + #fl → jb:wk sh.o):  1,234 / 2.3만 / 320만 / 1.5억 / 320억 / 1.5조
    P.add('sys/short', '''
        execute if score #fh jv matches 0 if score #fl jv matches ..9999 run return run function jb:sys/short0
        execute if score #fh jv matches 0 if score #fl jv matches ..99999999 run return run function jb:sys/short_man
        execute if score #fh jv matches ..999 run return run function jb:sys/short_eok
        function jb:sys/short_jo
    ''')
    P.add('sys/short0', '''
        scoreboard players operation #fn jv = #fl jv
        function jb:sys/comma
        data modify storage jb:wk sh.o set from storage jb:wk cm.o
    ''')
    P.add('sys/short_man', '''
        scoreboard players operation #sa1 jv = #fl jv
        scoreboard players operation #sa1 jv /= #c1000 jv
        data modify storage jb:wk sh.u set value "만"
        function jb:sys/short_j
    ''')
    P.add('sys/short_eok', '''
        scoreboard players operation #sa1 jv = #fh jv
        scoreboard players operation #sa1 jv *= #c100 jv
        scoreboard players operation #t jv = #fl jv
        scoreboard players operation #t jv /= #c10000000 jv
        scoreboard players operation #sa1 jv += #t jv
        data modify storage jb:wk sh.u set value "억"
        function jb:sys/short_j
    ''')
    P.add('sys/short_jo', '''
        scoreboard players operation #sa1 jv = #fh jv
        scoreboard players operation #sa1 jv /= #c100 jv
        data modify storage jb:wk sh.u set value "조"
        function jb:sys/short_j
    ''')
    # #sa1 = 단위의 10배 값 (예: 23 → 2.3) → "2.3만" / 100 이상이면 소수 없이 "320만"
    P.add('sys/short_j', '''
        scoreboard players operation #sb1 jv = #sa1 jv
        scoreboard players operation #sb1 jv %= #c10 jv
        scoreboard players operation #sa1 jv /= #c10 jv
        execute if score #sa1 jv matches 100.. run scoreboard players set #sb1 jv 0
        scoreboard players operation #fn jv = #sa1 jv
        function jb:sys/comma
        data modify storage jb:wk sh.a set from storage jb:wk cm.o
        execute store result storage jb:wk sh.b int 1 run scoreboard players get #sb1 jv
        execute if score #sb1 jv matches 0 run return run function jb:sys/short_u1 with storage jb:wk sh
        function jb:sys/short_u2 with storage jb:wk sh
    ''')
    P.add('sys/short_u1', '$data modify storage jb:wk sh.o set value "$(a)$(u)"')
    P.add('sys/short_u2', '$data modify storage jb:wk sh.o set value "$(a).$(b)$(u)"')
