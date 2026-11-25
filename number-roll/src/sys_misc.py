# -*- coding: utf-8 -*-
"""그 밖의 것들: 숫자·글자 도구, 소리, 미션, 기록, 벽, 월드, 플레이어, 불러오기/매 틱."""
from common import *
from jokers import JOKERS, MISSION_JOKER


def build_tools(P):
    # ---------- 숫자 → 자리 ----------
    d9 = P.fn('num/d9')
    d9.append('scoreboard players operation #t jv = #n jv')
    for i in range(9, 0, -1):
        d9.append('scoreboard players operation #d%d jv = #t jv' % i)
        d9.append('scoreboard players operation #d%d jv %%= #c10 jv' % i)
        d9.append('scoreboard players operation #t jv /= #c10 jv')
    ns = P.fn('num/ns')
    for i in range(1, 10):
        ns.append('execute store result storage jb:wk nd.d%d int 1 run scoreboard players get #d%d jv' % (i, i))
    ns.append('function jb:num/ns2 with storage jb:wk nd')
    P.add('num/ns2', '$data modify storage jb:wk r.ns set value "$(d1)$(d2)$(d3)$(d4)$(d5)$(d6)$(d7)$(d8)$(d9)"')
    # ---------- 빛나는 숫자 글자 (#d, #lc → jb:wk vis) ----------
    vb = P.fn('vis/build')
    vb.append('data modify storage jb:wk vis set value {text:"",bold:true,extra:[]}')
    for i in range(1, 10):
        vb.append('execute store result storage jb:wk vd.d int 1 run scoreboard players get #d%d jv' % i)
        vb.append('execute store result storage jb:wk vd.l int 1 run scoreboard players get #lc%d jv' % i)
        vb.append('function jb:vis/dig with storage jb:wk vd')
    P.add('vis/dig', '''
        $data modify storage jb:wk vis.extra append from storage jb:lit d$(l)
        $data modify storage jb:wk vis.extra[-1].text set value "$(d)"
    ''')
    lit = {}
    for i, col in enumerate(LIT):
        lit['d%d' % i] = {'text': '', 'color': col, 'bold': True}
    lit['d5']['shadow_color'] = -5223936
    lit['d6']['shadow_color'] = -7733248
    lit['t'] = {'text': '', 'color': '#4A4A4A', 'bold': True, 'obfuscated': True}
    lit['p'] = {'text': '', 'color': 'white', 'bold': True}
    for i, col in enumerate(WALL):
        lit['rb%d' % i] = {'text': '\n', 'color': col, 'extra': [{'text': ''}]}
        if i >= 4:
            lit['rb%d' % i]['bold'] = True
    P.add('lit/init', 'data merge storage jb:lit %s\ndata modify storage jb:lit pad set value "888888888"' % J(lit))
    # ---------- 숫자 공개 연출용 그림(프레임) ----------
    P.add('show/digp', '''
        data modify storage jb:wk hc append from storage jb:lit p
        $data modify storage jb:wk hc[-1].text set value "$(d)"
    ''')
    P.add('show/tail', '''
        execute store result storage jb:wk ht.r int 1 run scoreboard players get #tr jv
        execute if score #tr jv matches 1.. run function jb:show/tail2 with storage jb:wk ht
    ''')
    P.add('show/tail2', '''
        data modify storage jb:wk hc append from storage jb:lit t
        $data modify storage jb:wk hc[-1].text set string storage jb:lit pad 0 $(r)
    ''')
    P.add('show/save', '$data modify storage jb:an $(key) set from storage jb:wk hb')
    calc = P.fn('show/calc')
    calc.append('scoreboard players operation #n jv = @s jb.sn')
    calc.append('function jb:num/d9')
    calc.append('data modify storage jb:wk hb set value {f:[]}')
    for k in range(0, 10):
        calc.append('data modify storage jb:wk hc set value [{text:""}]')
        for i in range(1, k + 1):
            calc.append('execute store result storage jb:wk hdg.d int 1 run scoreboard players get #d%d jv' % i)
            calc.append('function jb:show/digp with storage jb:wk hdg')
        calc.append('scoreboard players set #tr jv %d' % (9 - k))
        calc.append('function jb:show/tail')
        calc.append('data modify storage jb:wk hb.f append from storage jb:wk hc')
    # ---------- 쉼표 숫자 (#fn → jb:wk cm.o) ----------
    cm = P.fn('sys/comma')
    cm.append('execute store result storage jb:wk cm.n int 1 run scoreboard players get #fn jv')
    cm.append('scoreboard players set #fdl jv 1')
    for k in range(1, 10):
        cm.append('execute if score #fn jv matches %d.. run scoreboard players set #fdl jv %d' % (10 ** k, k + 1))
    cm.append('execute if score #fdl jv matches ..3 run return run function jb:sys/cm0 with storage jb:wk cm')
    cm.append('function jb:sys/cms with storage jb:wk cm')
    P.add('sys/cm0', '$data modify storage jb:wk cm.o set value "$(n)"')
    P.add('sys/cms', '$data modify storage jb:wk cm.s set value "$(n)"')
    for L in range(4, 11):
        cm.append('execute if score #fdl jv matches %d run function jb:sys/cm%d' % (L, L))
        f = P.fn('sys/cm%d' % L)
        head = L - 3 * ((L - 1) // 3)
        cuts = [(0, head)]
        p = head
        while p < L:
            cuts.append((p, p + 3))
            p += 3
        for nm, (a, b) in zip('abcd', cuts):
            f.append('data modify storage jb:wk cm.%s set string storage jb:wk cm.s %d %d' % (nm, a, b))
        f.append('function jb:sys/cmj%d with storage jb:wk cm' % len(cuts))
    P.add('sys/cmj2', '$data modify storage jb:wk cm.o set value "$(a),$(b)"')
    P.add('sys/cmj3', '$data modify storage jb:wk cm.o set value "$(a),$(b),$(c)"')
    P.add('sys/cmj4', '$data modify storage jb:wk cm.o set value "$(a),$(b),$(c),$(d)"')
    # ---------- 코인: jb.coins(0..999,999,999) + jb.cb(10억 단위) ----------
    # #cg (0..21억) 만큼 주기
    P.add('sys/addc', '''
        scoreboard players operation #cgh jv = #cg jv
        scoreboard players operation #cgh jv /= #c1000000000 jv
        scoreboard players operation #cgl jv = #cg jv
        scoreboard players operation #cgl jv %= #c1000000000 jv
        function jb:sys/addc2
    ''')
    # #cgh(10억 단위) #cgl(10억 미만) 만큼 주기
    P.add('sys/addc2', '''
        scoreboard players operation @s jb.coins += #cgl jv
        execute if score @s jb.coins matches 1000000000.. run scoreboard players add @s jb.cb 1
        execute if score @s jb.coins matches 1000000000.. run scoreboard players remove @s jb.coins 1000000000
        scoreboard players operation @s jb.cb += #cgh jv
        execute if score @s jb.cb matches 10000000.. run function jb:sys/cap
    ''')
    P.add('sys/cap', '''
        scoreboard players set @s jb.cb 9999999
        scoreboard players set @s jb.coins 999999999
    ''')
    # 값 #costb(10억 단위) #cost 를 낼 수 있나 → #ok
    P.add('sys/afford', '''
        scoreboard players set #ok jv 0
        execute if score @s jb.cb > #costb jv run return run scoreboard players set #ok jv 1
        execute if score @s jb.cb = #costb jv if score @s jb.coins >= #cost jv run scoreboard players set #ok jv 1
    ''')
    P.add('sys/spend', '''
        scoreboard players operation @s jb.coins -= #cost jv
        execute if score @s jb.coins matches ..-1 run scoreboard players remove @s jb.cb 1
        execute if score @s jb.coins matches ..-1 run scoreboard players add @s jb.coins 1000000000
        scoreboard players operation @s jb.cb -= #costb jv
    ''')
    # 큰 수를 읽기 좋게 (#fh ×10억 + #fl → jb:wk cm.o):  1,234,567 / 12억 3,456만 / 3조 2,100억
    P.add('sys/big', '''
        execute if score #fh jv matches 0 if score #fl jv matches ..99999999 run return run function jb:sys/big0
        execute if score #fh jv matches ..999 run return run function jb:sys/big_e
        function jb:sys/big_j
    ''')
    P.add('sys/big0', '''
        scoreboard players operation #fn jv = #fl jv
        function jb:sys/comma
    ''')
    P.add('sys/big_e', '''
        scoreboard players operation #bga jv = #fh jv
        scoreboard players operation #bga jv *= #c10 jv
        scoreboard players operation #t jv = #fl jv
        scoreboard players operation #t jv /= #c100000000 jv
        scoreboard players operation #bga jv += #t jv
        scoreboard players operation #bgb jv = #fl jv
        scoreboard players operation #bgb jv %= #c100000000 jv
        scoreboard players operation #bgb jv /= #c10000 jv
        data modify storage jb:wk bg set value {u:"억",w:"만"}
        function jb:sys/big2
    ''')
    P.add('sys/big_j', '''
        scoreboard players operation #bga jv = #fh jv
        scoreboard players operation #bga jv /= #c1000 jv
        scoreboard players operation #bgb jv = #fh jv
        scoreboard players operation #bgb jv %= #c1000 jv
        scoreboard players operation #bgb jv *= #c10 jv
        scoreboard players operation #t jv = #fl jv
        scoreboard players operation #t jv /= #c100000000 jv
        scoreboard players operation #bgb jv += #t jv
        data modify storage jb:wk bg set value {u:"조",w:"억"}
        function jb:sys/big2
    ''')
    P.add('sys/big2', '''
        scoreboard players operation #fn jv = #bga jv
        function jb:sys/comma
        data modify storage jb:wk bg.a set from storage jb:wk cm.o
        execute if score #bgb jv matches 0 run return run function jb:sys/big3 with storage jb:wk bg
        scoreboard players operation #fn jv = #bgb jv
        function jb:sys/comma
        data modify storage jb:wk bg.b set from storage jb:wk cm.o
        function jb:sys/big4 with storage jb:wk bg
    ''')
    P.add('sys/big3', '$data modify storage jb:wk cm.o set value "$(a)$(u)"')
    P.add('sys/big4', '$data modify storage jb:wk cm.o set value "$(a)$(u) $(b)$(w)"')
    gr = P.fn('sys/gamerules')
    for r, v in (('max_command_sequence_length', '10000000'), ('send_command_feedback', 'false'), ('command_block_output', 'false'),
                 ('advance_time', 'false'), ('advance_weather', 'false'), ('spawn_mobs', 'false'), ('spawn_monsters', 'false'),
                 ('keep_inventory', 'true'), ('fall_damage', 'false'), ('spawn_phantoms', 'false'), ('mob_griefing', 'false'),
                 ('respawn_radius', '0'), ('immediate_respawn', 'true'), ('show_advancement_messages', 'false'),
                 ('spawn_patrols', 'false'), ('spawn_wandering_traders', 'false'), ('fire_damage', 'false'), ('drowning_damage', 'false')):
        gr.append('function jb:sys/gr {r:"%s",v:"%s"}' % (r, v))
    P.add('sys/gr', '$gamerule $(r) $(v)')
    # ---------- 소리 ----------
    P.add('snd/play', '''
        execute unless score @s jb.vol matches 0..100 run scoreboard players set @s jb.vol 100
        $scoreboard players set #sv jv $(b)
        scoreboard players operation #sv jv *= @s jb.vol
        execute store result storage jb:wk sv.v float 0.0001 run scoreboard players get #sv jv
        $data modify storage jb:wk sv.s set value "$(s)"
        $data modify storage jb:wk sv.p set value $(p)f
        execute if score @s jb.vol matches 1.. run function jb:snd/play2 with storage jb:wk sv
    ''')
    P.add('snd/play2', '$execute at @s run playsound $(s) master @s ~ ~ ~ $(v) $(p)')
    P.add('fx/big', 'scoreboard players set @s jb.fwt 44')
    hit = ['execute if score #kind jv matches 1 run ' + snd('block.note_block.pling', 45, 1.3),
           'execute if score #kind jv matches 2 run ' + snd('block.note_block.chime', 55, 1.5),
           'execute if score #kind jv matches 3 run ' + snd('block.amethyst_block.chime', 65, 1.7),
           'execute if score #kind jv matches 4.. run ' + snd('block.note_block.bell', 75, 1.5),
           'execute if score #kind jv matches 4.. run ' + snd('block.note_block.chime', 65, 2.0),
           'execute if score #kind jv matches 5.. run ' + snd('ui.toast.challenge_complete', 80, 1.0),
           'execute if score #kind jv matches 4.. unless score @s jb.mfw matches 1 at @s run particle minecraft:firework ~ ~1 ~ 0.5 0.5 0.5 0.03 18 force @s',
           'execute if score #kind jv matches 4.. unless score @s jb.mfw matches 1 at @s run particle minecraft:end_rod ~ ~1 ~ 0.4 0.7 0.4 0.01 12 force @s']
    P.fn('fx/hit').extend(hit)
    P.add('fx/new', 'scoreboard players set @s jb.nwf 0\n' + snd('entity.player.levelup', 60, 1.8) + '\n' + snd('block.note_block.chime', 70, 1.2))
    ft = ['scoreboard players remove @s jb.fwt 1']
    for tk, s, b, p in ((43, 'launch', 80, 1.0), (40, 'launch', 70, 1.2), (30, 'large_blast', 90, 1.0), (27, 'blast', 80, 1.1),
                        (24, 'large_blast_far', 80, 0.9), (20, 'twinkle', 70, 1.0), (16, 'blast_far', 70, 1.2), (12, 'twinkle_far', 70, 1.1), (6, 'twinkle', 50, 1.3)):
        ft.append('execute if score @s jb.fwt matches %d unless score @s jb.mfw matches 1 run %s' % (tk, snd('entity.firework_rocket.' + s, b, p)))
    ft.append('execute if score @s jb.fwt matches 30 unless score @s jb.mfw matches 1 at @s run particle minecraft:firework ~ ~2 ~ 1 1 1 0.1 60 force @s')
    ft.append('execute if score @s jb.fwt matches 24 unless score @s jb.mfw matches 1 at @s run particle minecraft:firework ~ ~2.5 ~ 1.5 1 1.5 0.1 50 force @s')
    P.fn('fx/tick').extend(ft)


def build_missions(P):
    """미션: 숫자 속에 정해진 숫자열이 들어 있으면 성공. 보상은 (기본 × 부스트) 와 (숫자 하나 평균 수입 × K) 중 큰 쪽."""
    letters = 'abcde'
    init = P.fn('ms/init')
    chk = P.fn('ms/chk')
    mjk = [j for j in JOKERS if j['kind'][0] == 'mission'][0]
    for (i, nm, col, L, base, ukey, K) in MISSIONS:
        st = unl_stage(ukey)
        init.append('function jb:ms/new%d' % i)
        f = P.fn('ms/new%d' % i)
        f.append('scoreboard players set @s jb.ml%d 0' % i)
        f.append('execute unless score @s jb.unl matches %d.. run return 0' % st)
        f.append('scoreboard players set @s jb.ml%d %d' % (i, L))
        f.append('execute store result score #mv jv run random value 0..%d' % (10 ** L - 1))
        f.append('scoreboard players operation #t jv = #mv jv')
        for j in range(L - 1, -1, -1):
            f.append('scoreboard players operation @s jb.m%d%s = #t jv' % (i, letters[j]))
            f.append('scoreboard players operation @s jb.m%d%s %%= #c10 jv' % (i, letters[j]))
            f.append('scoreboard players operation #t jv /= #c10 jv')
        f.append('function jb:ms/rw%d' % i)
        f.append('scoreboard players add #mv jv %d' % (10 ** L))
        f.append('execute store result storage jb:wk mss.v int 1 run scoreboard players get #mv jv')
        f.append('execute store result storage jb:wk mss.pid int 1 run scoreboard players get @s jb.pid')
        f.append('data modify storage jb:wk mss.i set value %d' % i)
        f.append('function jb:ms/str with storage jb:wk mss')
        # 보상 (지금 기준으로 다시 셈): 기본 × 부스트, 또는 숫자 하나 평균 수입의 K배
        rw = P.fn('ms/rw%d' % i)
        rw.append('scoreboard players set #mrh jv 0')
        rw.append('scoreboard players set #mrl jv %d' % base)
        rw.append('scoreboard players operation #t jv = #mrl jv')
        rw.append('scoreboard players operation #t jv *= @s jb.u4')
        rw.append('scoreboard players operation #t jv /= #c2 jv')
        rw.append('scoreboard players operation #mrl jv += #t jv')
        rw.append('scoreboard players set #mk jv %d' % K)
        rw.append('function jb:ms/rel')
        rw.append('scoreboard players operation @s jb.mc%d = #mrl jv' % i)
        rw.append('scoreboard players operation @s jb.mcb%d = #mrh jv' % i)
        chk.append('execute if score @s jb.ml%d matches 1.. run function jb:ms/c%d' % (i, i))
        c = P.fn('ms/c%d' % i)
        for p in range(1, 10 - L + 1):
            c.append('execute ' + ' '.join('if score #d%d jv = @s jb.m%d%s' % (p + j, i, letters[j]) for j in range(L)) +
                     ' run return run function jb:ms/done%d' % i)
        d = P.fn('ms/done%d' % i)
        d.append('function jb:ms/rw%d' % i)
        d.append('scoreboard players operation #cgh jv = @s jb.mcb%d' % i)
        d.append('scoreboard players operation #cgl jv = @s jb.mc%d' % i)
        d.append('scoreboard players set #fh jv 0')
        d.append('scoreboard players set #fl jv 0')
        d.append('function jb:ms/pay')
        for _ in range(mjk['kind'][1] - 1):
            d.append('execute if score @s jb.j%d matches 2 run function jb:ms/pay' % mjk['id'])
        d.append('scoreboard players add @s jb.mdone 1')
        d.append('function jb:sys/big')
        d.append('data modify storage jb:wk mdn.c set from storage jb:wk cm.o')
        d.append('execute store result storage jb:wk mdn.pid int 1 run scoreboard players get @s jb.pid')
        d.append('data modify storage jb:wk mdn.i set value %d' % i)
        d.append('function jb:ms/msg with storage jb:wk mdn')
        d.append(snd('entity.player.levelup', 80, 1.0))
        d.append('function jb:ms/new%d' % i)
        d.append('function jb:ms/side')
    # 1분마다: 걸려 있는 미션의 보상을 지금 수입에 맞춰 다시 적는다
    rf = P.fn('ms/refresh')
    for (i, nm, col, L, base, ukey, K) in MISSIONS:
        rf.append('execute if score @s jb.ml%d matches 1.. run function jb:ms/rw%d' % (i, i))
    rf.append('execute if score @s jb.ml1 matches 1.. run function jb:ms/side')
    # 보상 한 번 주고, 준 양을 #fh #fl 에 더한다
    P.add('ms/pay', '''
        function jb:sys/addc2
        scoreboard players operation #fl jv += #cgl jv
        execute if score #fl jv matches 1000000000.. run scoreboard players add #fh jv 1
        execute if score #fl jv matches 1000000000.. run scoreboard players remove #fl jv 1000000000
        scoreboard players operation #fh jv += #cgh jv
    ''')
    # 숫자 하나 평균 수입(최근 1분) × #mk 가 더 크면 그쪽으로 (#mrh #mrl)
    P.add('ms/rel', '''
        execute unless score @s jb.rr matches 1.. run return 0
        execute if score @s jb.rch matches 1.. run return run function jb:ms/rel_k
        scoreboard players operation #q jv = @s jb.rc
        scoreboard players operation #q jv /= @s jb.rr
        execute if score #q jv matches 700001.. run return run function jb:ms/rel_k
        scoreboard players operation #q jv *= #mk jv
        scoreboard players operation #qh jv = #q jv
        scoreboard players operation #qh jv /= #c1000000000 jv
        scoreboard players operation #ql jv = #q jv
        scoreboard players operation #ql jv %= #c1000000000 jv
        function jb:ms/rel_max
    ''')
    P.add('ms/rel_k', '''
        scoreboard players operation #q jv = @s jb.rch
        scoreboard players operation #q jv < #c2000 jv
        scoreboard players operation #q jv *= #c1000000 jv
        scoreboard players operation #t jv = @s jb.rc
        scoreboard players operation #t jv /= #c1000 jv
        scoreboard players operation #q jv += #t jv
        scoreboard players operation #q jv /= @s jb.rr
        scoreboard players operation #q jv < #c700000 jv
        scoreboard players operation #q jv *= #mk jv
        scoreboard players operation #qh jv = #q jv
        scoreboard players operation #qh jv /= #c1000000 jv
        scoreboard players operation #ql jv = #q jv
        scoreboard players operation #ql jv %= #c1000000 jv
        scoreboard players operation #ql jv *= #c1000 jv
        function jb:ms/rel_max
    ''')
    P.add('ms/rel_max', '''
        execute if score #qh jv > #mrh jv run return run function jb:ms/rel_set
        execute if score #qh jv = #mrh jv if score #ql jv > #mrl jv run function jb:ms/rel_set
    ''')
    P.add('ms/rel_set', '''
        scoreboard players operation #mrh jv = #qh jv
        scoreboard players operation #mrl jv = #ql jv
    ''')
    P.add('ms/str', '''
        $data modify storage jb:wk mss.t set value "$(v)"
        data modify storage jb:wk mss.s set string storage jb:wk mss.t 1
        $data modify storage jb:ms m.p$(pid).s$(i) set from storage jb:wk mss.s
    ''')
    P.add('ms/msg', '''
        $data modify storage jb:wk mdn.s set from storage jb:ms m.p$(pid).s$(i)
        function jb:ms/msg2 with storage jb:wk mdn
    ''')
    P.add('ms/msg2', '$data modify storage jb:wk wq append value {c:%s}' % J(
        [T('📋 미션 성공! ', 'gold', True), T('$(s)', 'white', True), T('   +$(c)⛃', 'gold', True)]))
    # 옆 점수판(사이드바)과 메뉴에 보일 줄
    side = P.fn('ms/side')
    side.append('execute store result storage jb:wk sd.pid int 1 run scoreboard players get @s jb.pid')
    lines = P.fn('ms/lines')
    lines.append('execute store result storage jb:wk sd.pid int 1 run scoreboard players get @s jb.pid')
    for (i, nm, col, L, base, ukey, K) in MISSIONS:
        side.append('execute unless score @s jb.ml%d matches 1.. run scoreboard players reset jb_m%d jb.side' % (i, i))
        side.append('execute if score @s jb.ml%d matches 1.. run function jb:ms/side%d' % (i, i))
        s1 = P.fn('ms/side%d' % i)
        s1.append('scoreboard players operation #fh jv = @s jb.mcb%d' % i)
        s1.append('scoreboard players operation #fl jv = @s jb.mc%d' % i)
        s1.append('function jb:sys/short')
        s1.append('data modify storage jb:wk sd.r set from storage jb:wk sh.o')
        s1.append('data modify storage jb:wk sd.i set value %d' % i)
        s1.append('function jb:ms/side_s with storage jb:wk sd')
        s1.append('scoreboard players set jb_m%d jb.side %d' % (i, 4 - i))
        s1.append('function jb:ms/side%db with storage jb:wk sd' % i)
        P.add('ms/side%db' % i, '$scoreboard players display name jb_m%d jb.side %s' % (i, J(
            [T(nm + '  ', col), T('$(s)', 'white', True), T('   +$(r)⛃', 'gold')])))
        lines.append('execute if score @s jb.ml%d matches 1.. run function jb:ms/line%d' % (i, i))
        l1 = P.fn('ms/line%d' % i)
        l1.append('scoreboard players operation #fh jv = @s jb.mcb%d' % i)
        l1.append('scoreboard players operation #fl jv = @s jb.mc%d' % i)
        l1.append('function jb:sys/short')
        l1.append('data modify storage jb:wk sd.r set from storage jb:wk sh.o')
        l1.append('data modify storage jb:wk sd.i set value %d' % i)
        l1.append('function jb:ms/side_s with storage jb:wk sd')
        l1.append('function jb:ms/line%db with storage jb:wk sd' % i)
        row = [T('\n' + nm + '  ', col, False), T('$(s)', 'white', True), T('   +$(r)⛃', 'gold', False)]
        if i == 1:
            comp = T('\n\n📋 미션', 'gold', True, extra=[T('  이 숫자가 들어간 숫자를 뽑으면 성공', 'gray', False)] + row)
        else:
            comp = {'text': '', 'extra': row}
        P.add('ms/line%db' % i, '$data modify storage jb:wk mh.m%d set value %s' % (i, J(comp)))
    P.add('ms/side_s', '$data modify storage jb:wk sd.s set from storage jb:ms m.p$(pid).s$(i)')


def build_hist(P):
    P.add('hist/add', '$data modify storage jb:hist h.p$(pid) append from storage jb:wk he')
    trim = P.fn('hist/trim')
    for _ in range(200):
        trim.append('$data remove storage jb:hist h.p$(pid)[0]')
    trim.append('scoreboard players remove @s jb.hn 200')
    P.add('hist/clear_me', '''
        execute store result storage jb:wk hq.pid int 1 run scoreboard players get @s jb.pid
        function jb:hist/clear2 with storage jb:wk hq
    ''')
    P.add('hist/clear2', '''
        $data remove storage jb:hist h.p$(pid)
        $data remove storage jb:fd f.p$(pid)
        $data remove storage jb:ms m.p$(pid)
    ''')
    # 숫자 하나 풀이 (#n → 족보 목록 bl, 코인 #pay, 가장 좋은 족보 #bid). #txt: 2=글만, 1=빛나는 자리까지
    P.add('hist/calc', '''
        function jb:num/d9
        function jb:roll/pre
        function jb:hand/eval
        scoreboard players set #cm jv 2
        data modify storage jb:wk bl set value []
        data modify storage jb:wk rvl set value []
        execute if score #txt jv matches 1 run function jb:roll/txt_pre
        function jb:roll/commit
        function jb:num/ns
    ''')
    P.add('hist/open', '''
        scoreboard players set #hpg jv 0
        function jb:hist/page
        %s
    ''' % snd('item.book.page_turn', 60, 1))
    P.add('hist/page_t', '''
        scoreboard players operation #hpg jv = #m jv
        scoreboard players remove #hpg jv 3000
        function jb:hist/page
        %s
    ''' % snd('item.book.page_turn', 60, 1))
    P.add('hist/page', '''
        execute store result storage jb:wk hq.pid int 1 run scoreboard players get @s jb.pid
        data modify storage jb:wk hl set value []
        function jb:hist/load with storage jb:wk hq
        execute store result score #hn jv run data get storage jb:wk hl
        scoreboard players operation #hpt jv = #hn jv
        scoreboard players add #hpt jv 19
        scoreboard players operation #hpt jv /= #c20 jv
        execute if score #hpt jv matches ..0 run scoreboard players set #hpt jv 1
        scoreboard players operation #hmx jv = #hpt jv
        scoreboard players remove #hmx jv 1
        scoreboard players operation #hpg jv < #hmx jv
        execute if score #hpg jv matches ..-1 run scoreboard players set #hpg jv 0
        scoreboard players operation #hs jv = #hpg jv
        scoreboard players operation #hs jv *= #c20 jv
        function jb:hist/skip
        data modify storage jb:wk hd set value {acts:[]}
        scoreboard players set #hi jv 0
        function jb:hist/take
        scoreboard players operation #t jv = #hpg jv
        scoreboard players add #t jv 2999
        execute store result storage jb:wk hd.pv int 1 run scoreboard players get #t jv
        scoreboard players add #t jv 2
        execute store result storage jb:wk hd.nv int 1 run scoreboard players get #t jv
        execute if score #hpg jv matches 1.. run function jb:hist/nav_p with storage jb:wk hd
        execute if score #hpg jv matches 0 run function jb:hist/nav_px
        execute if data storage jb:wk hl[-1] run function jb:hist/nav_n with storage jb:wk hd
        execute unless data storage jb:wk hl[-1] run function jb:hist/nav_nx
        data modify storage jb:wk hd.acts append value %s
        data modify storage jb:wk hd.acts append value %s
        execute store result storage jb:wk hd.hn int 1 run scoreboard players get #hn jv
        scoreboard players operation #t jv = #hpg jv
        scoreboard players add #t jv 1
        execute store result storage jb:wk hd.pg int 1 run scoreboard players get #t jv
        execute store result storage jb:wk hd.pt int 1 run scoreboard players get #hpt jv
        data modify storage jb:wk hd.q set value "$(q)"
        function jb:hist/show with storage jb:wk hd
    ''' % (J({'label': T('🔍 검색', 'yellow', True), 'width': 200, 'action': {'type': 'minecraft:dynamic/run_command', 'template': 'trigger jb.srch set $(q)'}}),
           J(button(T('← 메뉴', 'gray'), 1, width=200))))
    P.add('hist/load', '$execute if data storage jb:hist h.p$(pid) run data modify storage jb:wk hl set from storage jb:hist h.p$(pid)')
    P.add('hist/skip', 'execute if score #hs jv matches 1.. if data storage jb:wk hl[-1] run function jb:hist/skip2')
    P.add('hist/skip2', '''
        data remove storage jb:wk hl[-1]
        scoreboard players remove #hs jv 1
        function jb:hist/skip
    ''')
    P.add('hist/take', 'execute if score #hi jv matches ..19 if data storage jb:wk hl[-1] run function jb:hist/take2')
    P.add('hist/take2', '''
        execute store result score #n jv run data get storage jb:wk hl[-1].n
        data remove storage jb:wk hl[-1]
        scoreboard players set #txt jv 2
        function jb:hist/calc
        data modify storage jb:wk hx set value {bn:{text:"꽝",color:"dark_gray"}}
        data modify storage jb:wk hx.ns set from storage jb:wk r.ns
        execute store result storage jb:wk hx.n int 1 run scoreboard players get #n jv
        execute store result storage jb:wk hx.i int 1 run scoreboard players get #bid jv
        execute if score #bid jv matches 1.. run function jb:hist/bn with storage jb:wk hx
        function jb:hist/tiphead
        data modify storage jb:wk hx.bl set from storage jb:wk bl
        function jb:hist/ent with storage jb:wk hx
        scoreboard players add #hi jv 1
        function jb:hist/take
    ''')
    P.add('hist/bn', '$data modify storage jb:wk hx.bn set from storage jb:hn h$(i).n')
    P.add('hist/tiphead', '''
        execute store result storage jb:wk th.k int 1 run scoreboard players get #nh jv
        scoreboard players operation #fn jv = #pay jv
        function jb:sys/comma
        data modify storage jb:wk th.c set from storage jb:wk cm.o
        data modify storage jb:wk th.ns set from storage jb:wk r.ns
        function jb:hist/tiphead2 with storage jb:wk th
    ''')
    P.add('hist/tiphead2', '$data modify storage jb:wk bl prepend value %s' % J(
        T('$(ns)', 'white', True, extra=[T('\n족보 $(k)개  ', 'gray', False), T('+$(c)⛃', 'yellow', False)])))
    ent = {'label': [T('$(ns)  ', 'white', True), '$(bn)'], 'tooltip': {'text': '', 'extra': '$(bl)'}, 'width': 200,
           'action': {'type': 'minecraft:run_command', 'command': '/trigger jb.srch set $(n)'}}
    P.add('hist/ent', '$data modify storage jb:wk hd.acts append value ' + J(ent).replace('"$(bn)"', '$(bn)').replace('"$(bl)"', '$(bl)'))
    P.add('hist/nav_p', '$data modify storage jb:wk hd.acts append value ' + J({'label': T('◀ 최근', 'green'), 'width': 200, 'action': {'type': 'minecraft:run_command', 'command': '/trigger jb.menu set $(pv)'}}))
    P.add('hist/nav_px', 'data modify storage jb:wk hd.acts append value ' + J({'label': T('◀ 최근', 'dark_gray'), 'width': 200, 'action': cmd_action(3000)}))
    P.add('hist/nav_n', '$data modify storage jb:wk hd.acts append value ' + J({'label': T('예전 ▶', 'green'), 'width': 200, 'action': {'type': 'minecraft:run_command', 'command': '/trigger jb.menu set $(nv)'}}))
    P.add('hist/nav_nx', 'data modify storage jb:wk hd.acts append value ' + J({'label': T('예전 ▶', 'dark_gray'), 'width': 200, 'action': cmd_action(3000)}))
    inp = [{'type': 'minecraft:text', 'key': 'q', 'label': T('🔍 아무 숫자나 검색', 'yellow'), 'width': 300, 'max_length': 9}]
    d = dialog(T('⌚ 숫자 기록', 'gold', True), T('최근 $(hn)개  ·  $(pg)/$(pt)쪽  ·  숫자를 누르면 자세히', 'white'), '$(acts)', columns=2, inputs=inp, width=420)
    P.add('hist/show', '$dialog show @s ' + J(d).replace('"$(acts)"', '$(acts)'))
    # 검색 / 자세히
    P.add('hist/search', '''
        scoreboard players operation #sq jv = @s jb.srch
        scoreboard players set @s jb.srch -1
        execute if score #sq jv matches 1000000000.. run return run %s
        scoreboard players operation #n jv = #sq jv
        scoreboard players set #txt jv 1
        function jb:hist/calc
        function jb:vis/build
        data modify storage jb:wk sd set value {q:"$(q)"}
        data modify storage jb:wk sd.v set from storage jb:wk vis
        data modify storage jb:wk sd.ns set from storage jb:wk r.ns
        execute store result storage jb:wk sd.n int 1 run scoreboard players get #sq jv
        execute store result storage jb:wk sd.k int 1 run scoreboard players get #nh jv
        scoreboard players operation #fn jv = #pay jv
        function jb:sys/comma
        data modify storage jb:wk sd.c set from storage jb:wk cm.o
        execute store result storage jb:wk sd.pid int 1 run scoreboard players get @s jb.pid
        execute if score #nh jv matches 0 run data modify storage jb:wk bl append value {"text": "\\n(없음)", "color": "dark_gray"}
        execute unless score @s jb.unl matches %d.. run data modify storage jb:wk bl append value %s
        data modify storage jb:wk bl prepend value {"text": "걸린 족보", "color": "gray"}
        data modify storage jb:wk sd.dl set from storage jb:wk bl
        data modify storage jb:wk sd.rec set value {"text": "", "color": "gray"}
        function jb:hist/find with storage jb:wk sd
        function jb:hist/detail with storage jb:wk sd
        %s
    ''' % (snd('block.note_block.bass', 70, 0.7), unl_stage('t5'),
           J(T('\n\n🔒 전설·신화 족보는 코인 상점에서 해금하면 보여요', 'dark_gray')), snd('ui.button.click', 60, 1.2)))
    P.add('hist/find', '''
        data remove storage jb:wk hm
        $data modify storage jb:wk hm set from storage jb:hist h.p$(pid)[{n:$(n)}]
        execute if data storage jb:wk hm.n run data modify storage jb:wk sd.rec set value {"text": "   ✔ 굴려 본 숫자", "color": "green"}
    ''')
    body = [{'type': 'minecraft:plain_message', 'width': 420, 'contents': {'text': '', 'extra': ['$(v)', T('\n'), T('족보 $(k)개  +$(c)⛃', 'yellow'), '$(rec)']}},
            {'type': 'minecraft:plain_message', 'width': 420, 'contents': {'text': '', 'extra': '$(dl)'}}]
    acts = [{'label': T('🔍 검색', 'yellow', True), 'width': 200, 'action': {'type': 'minecraft:dynamic/run_command', 'template': 'trigger jb.srch set $(q)'}},
            button(T('← 기록', 'gold'), 3000, width=200)]
    d = dialog(T('🔍 $(ns)', 'white', True), body, acts, columns=2, inputs=inp)
    P.add('hist/detail', '$dialog show @s ' + J(d).replace('"$(v)"', '$(v)').replace('"$(rec)"', '$(rec)').replace('"$(dl)"', '$(dl)'))


def build_wall(P):
    """동쪽 벽 '최근 숫자': 16줄(세로 칸), 칸마다 25개. 오른쪽 칸이 차면 전체가 왼쪽으로 한 칸 민다."""
    init = P.fn('rb/init')
    init.append('data merge storage jb:rb {v:3,%s}' % ','.join('c%d:[{text:""}]' % i for i in range(16)))
    init.append('scoreboard players set #rbn jv 0')
    init.append('scoreboard players set #rbd jv 2')
    add = P.fn('rb/add')
    add.append('scoreboard players operation #np jv = #n jv')
    add.append('scoreboard players add #np jv 1000000000')
    add.append('execute store result storage jb:wk nx int 1 run scoreboard players get #np jv')
    add.append('function jb:rb/tpl')
    add.append('data modify storage jb:wk rbe.extra[0].text set string storage jb:wk nx 1')
    add.append('execute if score #rbn jv matches 25.. run function jb:rb/shift')
    add.append('data modify storage jb:rb c15 append from storage jb:wk rbe')
    add.append('scoreboard players add #rbn jv 1')
    add.append('scoreboard players operation #rbd jv > #c1 jv')
    tpl = P.fn('rb/tpl')
    for t in range(-1, 6):
        if t < 5:
            tpl.append('execute if score #bt jv matches %d run return run data modify storage jb:wk rbe set from storage jb:lit rb%d' % (t, t + 1))
        else:
            tpl.append('data modify storage jb:wk rbe set from storage jb:lit rb6')
    sh = P.fn('rb/shift')
    for i in range(15):
        sh.append('data modify storage jb:rb c%d set from storage jb:rb c%d' % (i, i + 1))
    sh.append('data modify storage jb:rb c15 set value [{text:""}]')
    sh.append('scoreboard players set #rbn jv 0')
    sh.append('scoreboard players set #rbd jv 2')
    dr = P.fn('rb/draw')
    dr.append('scoreboard players set #rbt jv 0')
    dr.append('execute if score #rbd jv matches 2 run function jb:rb/draw_all')
    dr.append('function jb:rb/draw1 {i:15}')
    dr.append('scoreboard players set #rbd jv 0')
    da = P.fn('rb/draw_all')
    for i in range(15):
        da.append('function jb:rb/draw1 {i:%d}' % i)
    P.add('rb/draw1', '''
        data modify storage jb:wk rbt set value {text:"",extra:[]}
        $data modify storage jb:wk rbt.extra set from storage jb:rb c$(i)
        $data modify entity @e[type=text_display,tag=jb.rb$(i),limit=1] text set from storage jb:wk rbt
    ''')


def build_player(P, HI):
    def item(key, name, color, model, lore):
        return 'carrot_on_a_stick[custom_data={jb:"%s"},item_name={text:"%s",color:"%s",bold:true},item_model="minecraft:%s",lore=[{text:"%s",color:"gray",italic:false}]]' % (key, name, color, model, lore)
    ITEMS = {
        'roll': item('roll', '⚀ 주사위', 'gold', 'quartz_block', '우클릭 · 꾹 누르면 계속'),
        'coin': item('coin', '⛃ 코인 상점', 'green', 'emerald', '우클릭'),
        'star': item('star', '⭐ 강화', 'aqua', 'nether_star', '우클릭'),
        'joker': item('joker', '🃏 조커', 'light_purple', 'paper', '우클릭'),
        'menu': item('menu', '📖 메뉴', 'yellow', 'book', '우클릭'),
        'auto_on': item('auto', '⟳ 자동: 켜짐', 'green', 'lime_dye', '우클릭: 끄기'),
        'auto_off': item('auto', '⟳ 자동: 꺼짐', 'red', 'gray_dye', '우클릭: 켜기'),
    }
    # 손에 든 물건 쓰기
    use = P.fn('player/use')
    use.append('scoreboard players set @s jb.use 0')
    acts = {'roll': 'roll/click', 'coin': 'menu/coin_snd', 'star': 'menu/perk_snd', 'joker': 'menu/joker_snd', 'menu': 'menu/main'}
    for k, fn in acts.items():
        use.append('execute if items entity @s weapon.mainhand carrot_on_a_stick[custom_data~{jb:"%s"}] run return run function jb:%s' % (k, fn))
    use.append('execute if items entity @s weapon.mainhand carrot_on_a_stick[custom_data~{jb:"auto"}] run return run function jb:auto/use {h:"mainhand"}')
    for k, fn in acts.items():
        use.append('execute unless items entity @s weapon.mainhand carrot_on_a_stick if items entity @s weapon.offhand carrot_on_a_stick[custom_data~{jb:"%s"}] run return run function jb:%s' % (k, fn))
    use.append('execute unless items entity @s weapon.mainhand carrot_on_a_stick if items entity @s weapon.offhand carrot_on_a_stick[custom_data~{jb:"auto"}] run return run function jb:auto/use {h:"offhand"}')
    P.add('auto/toggle', '''
        execute if score @s jb.u2 matches 0 run return run %s
        scoreboard players add @s jb.autoon 1
        execute if score @s jb.autoon matches 2.. run scoreboard players set @s jb.autoon 0
        execute if score @s jb.autoon matches 1 run %s
        execute if score @s jb.autoon matches 0 run %s
    ''' % (snd('block.note_block.bass', 70, 0.7), snd('block.note_block.pling', 60, 1.6), snd('block.note_block.pling', 60, 0.8)))
    P.add('auto/use', '''
        function jb:auto/toggle
        $execute if score @s jb.autoon matches 1 run item replace entity @s weapon.$(h) with %s
        $execute unless score @s jb.autoon matches 1 run item replace entity @s weapon.$(h) with %s
    ''' % (ITEMS['auto_on'], ITEMS['auto_off']))
    # 물건 다시 주기 (순서: 주사위, 자동, 코인 상점, 강화, 조커, 메뉴)
    it = P.fn('player/items')
    it.append('clear @s carrot_on_a_stick')
    it.append('execute if score @s jb.unl matches %d.. run give @s %s' % (unl_stage('dice'), ITEMS['roll']))
    it.append('execute if score @s jb.u2 matches 1.. if score @s jb.autoon matches 1 run give @s %s' % ITEMS['auto_on'])
    it.append('execute if score @s jb.u2 matches 1.. unless score @s jb.autoon matches 1 run give @s %s' % ITEMS['auto_off'])
    it.append('give @s %s' % ITEMS['coin'])
    it.append('give @s %s' % ITEMS['star'])
    it.append('execute if score @s jb.jslot matches 1.. run give @s %s' % ITEMS['joker'])
    it.append('give @s %s' % ITEMS['menu'])
    dr = P.fn('player/dropped')
    for k in ('roll', 'coin', 'star', 'joker', 'menu', 'auto'):
        dr.append('execute if items entity @s contents carrot_on_a_stick[custom_data~{jb:"%s"}] run return run function jb:player/undrop' % k)
    P.add('player/undrop', '''
        kill @s
        execute as @p run function jb:player/items
    ''')
    P.add('player/fell', 'tp @s 0.5 151 4.5 180 0')
    P.add('player/welcome', '''
        title @s times 10 70 20
        title @s subtitle {"text": "빨간 블록 우클릭!", "color": "yellow"}
        title @s title {"text": "⚀ 숫자 굴리기", "color": "gold", "bold": true}
        tellraw @s %s
        %s
    ''' % (J(C([T('⚀ 숫자 굴리기  ', 'gold', True), T('숫자 속 족보를 찾으면 코인!', 'white'), T('  (📖 메뉴 → 족보 도감)', 'gray')])),
           snd('ui.toast.challenge_complete', 60, 1.2)))
    P.add('player/welcome_all', 'execute as @a[scores={jb.rolls=0}] run function jb:player/welcome')
    # 처음 들어온 사람 / 판이 바뀐 사람
    init = P.fn('player/init')
    init.append('scoreboard players operation @s jb.pid = #nextpid jv')
    init.append('scoreboard players add #nextpid jv 1')
    zero = ['coins', 'rolls', 'state', 't', 'k', 'q', 'qn', 'sn', 'pc', 'autoon', 'u1', 'u2', 'u3', 'u4', 'end', 'tt', 'at', 'aq', 'aqn', 'asx',
            'hold', 'fwm', 'asc', 'rvt', 'fwt', 'mhero', 'mfw', 'hudw', 'asum', 'ashow', 'alert', 'achat', 'found', 'ept',
            'e1', 'e2', 'e4', 'e5', 'ml1', 'ml2', 'ml3', 'mc1', 'mc2', 'mc3', 'mdone', 'ptk', 'wc', 'wch', 'rc', 'rch', 'wr', 'rr',
            'tcl', 'tch', 'topr', 'topid', 'topn', 'stot', 'smax', 's5n', 'ft0', 'ft1', 'ft2', 'ft3', 'ft4', 'ft5', 'zn', 'arl', 'afw', 'afh',
            'unl', 'jslot', 'jeq', 'jown', 'hn', 'mxr', 'mxn', 'nwf', 'ubuy', 'pbuy', 'muted', 'cb', 'pcb', 'asumb', 'ashowb', 'mcb1', 'mcb2', 'mcb3', 'cq']
    for z in zero:
        init.append('scoreboard players set @s jb.%s 0' % z)
    init.append('scoreboard players set @s jb.mxt -1')
    init.append('scoreboard players set @s jb.sbp -1')
    init.append('scoreboard players set @s jb.sbt -1')
    init.append('scoreboard players set @s jb.vol 100')
    for jk in JOKERS:
        init.append('scoreboard players set @s jb.j%d 0' % jk['id'])
    for h in HI:
        init.append('scoreboard players set @s jb.h%d 0' % h['id'])
    init.append('scoreboard players set @s jb.dv %d' % DVER)
    init.append('function jb:ms/init')
    init.append('clear @s carrot_on_a_stick')
    init.append('gamemode adventure @s')
    init.append('xp set @s 0 levels')
    init.append('xp set @s 0 points')
    init.append('execute unless score #built jv matches 1 run function jb:world/prepare')
    init.append('execute if score #built jv matches 1 run tp @s 0.5 151 11.5 0 -10')
    init.append('execute if score #built jv matches 1 run function jb:player/items')
    init.append('function jb:ms/side')
    init.append('schedule function jb:player/welcome_all 60t')
    P.add('player/wipe', '''
        function jb:hist/clear_me
        function jb:player/bb_rm_me
        advancement revoke @s from jb:root
        scoreboard players reset @s jb.pid
        tellraw @s %s
    ''' % J(C([T('⚀ 숫자 굴리기', 'gold', True), T('가 새로워졌어요! 족보 %d개 · 🃏 조커 · 🔓 해금 — 처음부터 다시 시작해요.' % NHANDS, 'white')])))


def build_load_tick(P, HI, objectives_extra):
    load = P.fn('load')
    load.append('scoreboard objectives add jv dummy')
    objs = ['pid', 'dv', 'coins', 'rolls', 'state', 't', 'k', 'q', 'qn', 'sn', 'sbp', 'sbt', 'pc', 'autoon', 'u1', 'u2', 'u3', 'u4', 'end', 'tt', 'at', 'aq', 'aqn', 'asx',
            'hold', 'vol', 'fwm', 'asc', 'rvt', 'fwt', 'mhero', 'mfw', 'hudw', 'asum', 'ashow', 'alert', 'achat', 'found', 'ept',
            'e1', 'e2', 'e4', 'e5', 'ml1', 'ml2', 'ml3', 'mc1', 'mc2', 'mc3', 'mdone', 'ptk', 'wc', 'wch', 'rc', 'rch', 'wr', 'rr',
            'tcl', 'tch', 'topr', 'topid', 'topn', 'stot', 'smax', 's5n', 'ft0', 'ft1', 'ft2', 'ft3', 'ft4', 'ft5', 'zn', 'arl', 'afw', 'afh',
            'unl', 'jslot', 'jeq', 'jown', 'hn', 'mxr', 'mxn', 'mxt', 'nwf', 'ubuy', 'pbuy', 'muted', 'cb', 'pcb', 'asumb', 'ashowb', 'mcb1', 'mcb2', 'mcb3', 'cq']
    objs += ['m1a', 'm1b', 'm1c', 'm2a', 'm2b', 'm2c', 'm2d', 'm3a', 'm3b', 'm3c', 'm3d', 'm3e']
    objs += ['j%d' % jk['id'] for jk in JOKERS]
    objs += objectives_extra
    for o in objs:
        load.append('scoreboard objectives add jb.%s dummy' % o)
    for h in HI:
        load.append('scoreboard objectives add jb.h%d dummy' % h['id'])
    # 예전 판에서 쓰던 점수판 정리
    for o in ['lv', 'xp', 'need', 'gxp', 'px', 'e3', 'mx1', 'mx2', 'mx3', 'm1', 'm2', 'm3', 'pb', 'topp', 'ept2', 'newt', 'zs', 'zl', 'zc', 'broke'] + ['h%d' % i for i in range(len(HI) + 1, 420)]:
        load.append('scoreboard objectives remove jb.%s' % o)
    load.append('scoreboard objectives add jb.use minecraft.used:minecraft.carrot_on_a_stick')
    load.append('scoreboard objectives add jb.menu trigger')
    load.append('scoreboard objectives add jb.srch trigger')
    load.append('scoreboard objectives add jb.vset trigger')
    load.append('scoreboard objectives add jb.side dummy %s' % J(T('📋 미션', 'gold', True)))
    load.append('scoreboard objectives modify jb.side numberformat blank')
    load.append('scoreboard objectives setdisplay sidebar jb.side')
    load.append('function jb:consts')
    load.append('function jb:hand/init')
    load.append('function jb:lit/init')
    load.append('data remove storage jb:hn h')
    load.append('function jb:hand/names')
    load.append('function jb:sys/gamerules')
    load.append('execute unless score #nextpid jv matches 1.. run scoreboard players set #nextpid jv 1')
    load.append('execute unless score #gen jv matches 1.. run scoreboard players set #gen jv 1')
    load.append('execute unless data storage jb:rb {v:3} run function jb:rb/init')
    load.append('data modify storage jb:wk wq set value []')
    load.append('data modify storage jb:wk wa set value []')
    load.append('data modify storage jb:wk nw set value []')
    load.append('data modify storage jb:wk su set value []')
    load.append('scoreboard players set #newc jv 0')
    load.append('scoreboard players set #supc jv 0')
    P.add('tick', '''
        execute as @a[scores={jb.pid=1..}] unless score @s jb.dv matches %d run function jb:player/wipe
        execute as @a unless score @s jb.pid matches 1.. run function jb:player/init
        execute as @a[scores={jb.use=1..}] run function jb:player/use
        execute as @e[type=interaction,tag=jb.btn] run function jb:world/click
        execute as @a[scores={jb.menu=1..}] run function jb:menu/trigger
        scoreboard players enable @a jb.menu
        execute as @a unless score @s jb.srch = @s jb.srch run scoreboard players set @s jb.srch -1
        execute as @a[scores={jb.srch=0..}] run function jb:hist/search
        scoreboard players enable @a jb.srch
        execute as @a unless score @s jb.vset = @s jb.vset run scoreboard players set @s jb.vset -1
        execute as @a[scores={jb.vset=0..}] run function jb:snd/vset
        scoreboard players enable @a jb.vset
        execute as @e[type=item,nbt=!{PickupDelay:32767s}] at @s run function jb:player/dropped
        scoreboard players remove @a[scores={jb.alert=1..}] jb.alert 1
        scoreboard players remove @a[scores={jb.hold=1..}] jb.hold 1
        execute as @a[scores={jb.hold=1..,jb.state=3}] run function jb:roll/start
        execute as @a[scores={jb.hold=1..,jb.state=0}] run function jb:roll/start
        execute as @a[scores={jb.state=1..}] run function jb:roll/tick
        execute as @a[scores={jb.autoon=1,jb.u2=1..}] run function jb:roll/autotick
        scoreboard players add #hud jv 1
        execute if score #hud jv matches 4.. as @a[scores={jb.pid=1..}] run function jb:player/hud
        execute if score #hud jv matches 4.. run scoreboard players set #hud jv 0
        scoreboard players add #pulse jv 1
        execute if score #pulse jv matches 40.. as @a run function jb:player/pulse
        execute if score #pulse jv matches 40.. run scoreboard players set #pulse jv 0
        execute as @a[y=-100,dy=240] if score #built jv matches 1 run function jb:player/fell
        execute if score #built jv matches 1 unless score #bver jv matches %d run function jb:world/build
        scoreboard players add #prt jv 1
        execute if score #prt jv matches 10.. run function jb:world/slow
        scoreboard players add #rbt jv 1
        execute if score #rbd jv matches 1.. if score #rbt jv matches 10.. run function jb:rb/draw
        execute as @a[scores={jb.fwt=1..}] run function jb:fx/tick
        scoreboard players remove @a[scores={jb.asc=1..}] jb.asc 1
        scoreboard players add #advt jv 1
        execute if score #advt jv matches 20.. run function jb:adv/tick
        scoreboard players add @a[scores={jb.rolls=1..}] jb.ptk 1
        scoreboard players add #stt jv 1
        execute if score #stt jv matches 1200.. run function jb:stats/minute
    ''' % (DVER, BVER))
