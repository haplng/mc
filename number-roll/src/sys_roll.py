# -*- coding: utf-8 -*-
"""굴리기: 숫자 하나의 처리(족보 → 코인 → 기록), 직접 굴리기 연출, 자동 굴리기."""
from common import *


def build_commit(P, HI, fams_joker):
    """족보별 정산 함수 hand/c, cs, su, new, ct, tp.

    HI: 족보 정보 목록 [{id,key,name,tier,pay,fam,...}]
    """
    for h in HI:
        i, t = h['id'], h['tier']
        T2, T3, T4, T5 = STAR_T[t]
        pays = h['pays']
        tg = min(t, 3)
        c = P.fn('hand/c/%d' % i)
        c.append('execute if score #cm jv matches 1 run scoreboard players add @s jb.h%d 1' % i)
        c.append('scoreboard players set #hp jv %d' % pays[0])
        c.append('execute if score @s jb.h%d matches %d.. run function jb:hand/cs/%d' % (i, T2, i))
        c.append('scoreboard players operation #p%d jv += #hp jv' % tg)
        if h['fam'] in fams_joker:
            c.append('scoreboard players operation #pf_%s jv += #hp jv' % fams_joker[h['fam']])
        c.append('execute if score #bid jv matches 0 run scoreboard players set #bid jv %d' % i)
        c.append('execute if score #cm jv matches 1 if score @s jb.h%d matches 1 run function jb:hand/new/%d' % (i, i))
        if t >= 2:
            c.append('execute if score #cm jv matches 1 if score @s jb.topr matches ..%d run function jb:hand/tp/%d' % (h['rank'] - 1, i))
            tp = P.fn('hand/tp/%d' % i)
            tp.append('scoreboard players set @s jb.topr %d' % h['rank'])
            tp.append('scoreboard players set @s jb.topid %d' % i)
            tp.append('scoreboard players operation @s jb.topn = #n jv')
        c.append('execute if score #txt jv matches 1.. run function jb:hand/ct/%d' % i)
        cs = P.fn('hand/cs/%d' % i)
        cs.append('execute if score @s jb.h%d matches %d..%d run scoreboard players set #hp jv %d' % (i, T2, T3 - 1, pays[1]))
        cs.append('execute if score @s jb.h%d matches %d..%d run scoreboard players set #hp jv %d' % (i, T3, T4 - 1, pays[2]))
        cs.append('execute if score @s jb.h%d matches %d..%d run scoreboard players set #hp jv %d' % (i, T4, T5 - 1, pays[3]))
        cs.append('execute if score @s jb.h%d matches %d.. run scoreboard players set #hp jv %d' % (i, T5, pays[4]))
        cs.append('execute if score #cm jv matches 1 if score @s jb.h%d matches %d..%d run function jb:hand/su/%d' % (i, T2, T5, i))
        su = P.fn('hand/su/%d' % i)
        for k, Tk in enumerate((T2, T3, T4, T5), 2):
            su.append('execute if score @s jb.h%d matches %d run function jb:hand/starup {i:%d,s:%d}' % (i, Tk, i, k))
        nw = P.fn('hand/new/%d' % i)
        nw.append('scoreboard players add @s jb.found 1')
        nw.append('scoreboard players add @s jb.ft%d 1' % t)
        nw.append('scoreboard players add @s jb.stot 1')
        nw.append('scoreboard players add #newc jv 1')
        nw.append('data modify storage jb:wk nw append value %d' % i)
        ct = P.fn('hand/ct/%d' % i)
        ct.append('execute if score @s jb.h%d matches ..%d run data modify storage jb:wk bl append from storage jb:hn h%d.s1' % (i, T2 - 1, i))
        ct.append('execute if score @s jb.h%d matches %d..%d run data modify storage jb:wk bl append from storage jb:hn h%d.s2' % (i, T2, T3 - 1, i))
        ct.append('execute if score @s jb.h%d matches %d..%d run data modify storage jb:wk bl append from storage jb:hn h%d.s3' % (i, T3, T4 - 1, i))
        ct.append('execute if score @s jb.h%d matches %d..%d run data modify storage jb:wk bl append from storage jb:hn h%d.s4' % (i, T4, T5 - 1, i))
        ct.append('execute if score @s jb.h%d matches %d.. run data modify storage jb:wk bl append from storage jb:hn h%d.s5' % (i, T5, i))
        ct.append('execute if score #txt jv matches 2 run return 0')
        ct.append('scoreboard players set #ml jv %d' % (t + 1))
        ct.append('function jb:hand/mk/clr')
        ct.append('function jb:hand/m/%d' % i)
        ct.append('function jb:hand/mk/merge')
        ct.append('data modify storage jb:wk rvl prepend value %d' % i)
    # 별이 오름
    P.add('hand/starup', '''
        scoreboard players add @s jb.ept 1
        scoreboard players add @s jb.stot 1
        $scoreboard players operation @s jb.smax > #c$(s) jv
        $execute if score #c$(s) jv matches 5 run scoreboard players add @s jb.s5n 1
        scoreboard players add #supc jv 1
        $data modify storage jb:wk su append value {i:$(i),s:$(s)}
    ''')


def build_roll(P):
    # ------------------------------------------------------------------
    # 숫자 하나
    # ------------------------------------------------------------------
    P.add('roll/pre', '''
        scoreboard players set #ul4 jv 0
        execute if score @s jb.unl matches %d.. run scoreboard players set #ul4 jv 1
        scoreboard players set #ul5 jv 0
        execute if score @s jb.unl matches %d.. run scoreboard players set #ul5 jv 1
        scoreboard players set #cdig jv 1
        execute if score @s jb.coins matches 10.. run scoreboard players set #cdig jv 2
        execute if score @s jb.coins matches 100.. run scoreboard players set #cdig jv 3
        execute if score @s jb.coins matches 1000.. run scoreboard players set #cdig jv 4
        execute if score @s jb.coins matches 10000.. run scoreboard players set #cdig jv 5
        execute if score @s jb.coins matches 100000.. run scoreboard players set #cdig jv 6
        execute if score @s jb.coins matches 1000000.. run scoreboard players set #cdig jv 7
        execute if score @s jb.coins matches 10000000.. run scoreboard players set #cdig jv 8
        execute if score @s jb.coins matches 100000000.. run scoreboard players set #cdig jv 9
        execute if score @s jb.cb matches 1.. run scoreboard players set #cdig jv 10
        execute if score @s jb.cb matches 10.. run scoreboard players set #cdig jv 11
        execute if score @s jb.cb matches 100.. run scoreboard players set #cdig jv 12
        execute if score @s jb.cb matches 1000.. run scoreboard players set #cdig jv 13
        execute if score @s jb.cb matches 10000.. run scoreboard players set #cdig jv 14
        execute if score @s jb.cb matches 100000.. run scoreboard players set #cdig jv 15
        execute if score @s jb.cb matches 1000000.. run scoreboard players set #cdig jv 16
    ''' % (unl_stage('t4'), unl_stage('t5')))

    P.add('roll/one', '''
        execute store result score #n jv run random value 0..999999999
        function jb:num/d9
        function jb:hand/eval
        execute if score @s jb.e5 matches 1.. run function jb:roll/luck
        scoreboard players set #txt jv 0
        execute if score #man jv matches 1 run scoreboard players set #txt jv 1
        execute if score #man jv matches 0 if score #bt jv >= #fmin jv run scoreboard players set #txt jv 1
        execute if score #txt jv matches 1 run function jb:roll/txt_pre
        scoreboard players set #cm jv 1
        function jb:roll/commit
        function jb:ms/chk
        function jb:roll/coins
        function jb:roll/record
    ''')
    P.add('roll/txt_pre', '''
        function jb:hand/mprep
        data modify storage jb:wk bl set value []
        data modify storage jb:wk rvl set value []
        scoreboard players set #lc1 jv 0
        scoreboard players set #lc2 jv 0
        scoreboard players set #lc3 jv 0
        scoreboard players set #lc4 jv 0
        scoreboard players set #lc5 jv 0
        scoreboard players set #lc6 jv 0
        scoreboard players set #lc7 jv 0
        scoreboard players set #lc8 jv 0
        scoreboard players set #lc9 jv 0
    ''')
    P.add('roll/commit', '''
        scoreboard players set #p0 jv 0
        scoreboard players set #p1 jv 0
        scoreboard players set #p2 jv 0
        scoreboard players set #p3 jv 0
        scoreboard players set #pf_same jv 0
        scoreboard players set #pf_stair jv 0
        scoreboard players set #pf_mirror jv 0
        scoreboard players set #pf_word jv 0
        scoreboard players set #bid jv 0
        function jb:hand/scan
        scoreboard players operation #pay jv = #p0 jv
        scoreboard players operation #pay jv += #p1 jv
        scoreboard players operation #pay jv += #p2 jv
        scoreboard players operation #pay jv += #p3 jv
    ''')
    # 🍀 행운
    P.add('roll/luck', '''
        scoreboard players set #lt jv 0
        function jb:roll/luck1
        execute if score @s jb.e5 matches 3.. if score #bt jv matches 1 run function jb:roll/luck3
    ''')
    P.add('roll/luck1', '''
        execute if score @s jb.e5 matches 1 if score #bt jv matches 0.. run return 0
        execute if score @s jb.e5 matches 2.. if score #bt jv matches 1.. run return 0
        execute if score #bt jv matches ..-1 run scoreboard players add @s jb.zn 1
        scoreboard players add #lt jv 1
        execute if score #lt jv matches 60.. run return 0
        execute store result score #n jv run random value 0..999999999
        function jb:num/d9
        function jb:hand/eval
        function jb:roll/luck1
    ''')
    P.add('roll/luck3', '''
        scoreboard players operation #lkn jv = #n jv
        scoreboard players operation #lkb jv = #bt jv
        scoreboard players operation #lkh jv = #nh jv
        execute store result score #n jv run random value 0..999999999
        function jb:num/d9
        function jb:hand/eval
        scoreboard players set #lt jv 0
        function jb:roll/luck1
        scoreboard players set #lkw jv 0
        execute if score #bt jv < #lkb jv run scoreboard players set #lkw jv 1
        execute if score #bt jv = #lkb jv if score #nh jv < #lkh jv run scoreboard players set #lkw jv 1
        execute if score #lkw jv matches 1 run function jb:roll/luck3b
    ''')
    P.add('roll/luck3b', '''
        scoreboard players operation #n jv = #lkn jv
        function jb:num/d9
        function jb:hand/eval
    ''')

    # ------------------------------------------------------------------
    # 코인 계산
    #   기본(#p0..#p3) → 🃏 부분 조커 → ⭐ 강화(💎 🎰) → 🃏 전체 조커(곱) → ⛃ 부스트
    #   값이 커지면 천 단위(#ku=1)로 바꿔 계산한다.
    #   결과: #rth(10억 단위) #rtl(나머지), 비교·기록용 #rt(20억에서 멈춤), #pay0(보너스 전)
    # ------------------------------------------------------------------
    P.add('roll/coins', '''
        scoreboard players operation #pay0 jv = #pay jv
        execute if score @s jb.jeq matches 1.. run function jb:joker/parts
        scoreboard players set #ku jv 0
        execute if score #pay jv matches 2000000.. run function jb:roll/tok_p
        execute if score #ku jv matches 0 if score #pay jv matches ..19999 run function jb:roll/toc_p
        scoreboard players operation #v jv = #pay jv
        execute if score @s jb.e1 matches 1.. run function jb:roll/b1
        execute if score @s jb.e2 matches 1.. if score #nh jv matches 2.. run function jb:roll/b2
        execute if score @s jb.jeq matches 1.. run function jb:joker/wholes
        execute if score @s jb.u4 matches 1.. run function jb:roll/boost
        execute if score #ku jv matches -1 run function jb:roll/tok_c
        execute if score #ku jv matches 0 run return run function jb:roll/out0
        function jb:roll/out1
    ''')
    # 큰 값은 천 단위로 (#ku = 1), 작은 값은 0.01 단위로 (#ku = -1) 계산해 버림을 줄인다
    P.add('roll/tok_p', '''
        scoreboard players operation #p2 jv /= #c1000 jv
        scoreboard players operation #p3 jv /= #c1000 jv
        scoreboard players operation #pay jv /= #c1000 jv
        scoreboard players set #ku jv 1
    ''')
    P.add('roll/toc_p', '''
        scoreboard players operation #p2 jv *= #c100 jv
        scoreboard players operation #p3 jv *= #c100 jv
        scoreboard players operation #pay jv *= #c100 jv
        scoreboard players set #ku jv -1
    ''')
    # 💎 희귀 이상 족보 +50%씩
    P.add('roll/b1', '''
        scoreboard players operation #t jv = #p2 jv
        scoreboard players operation #t jv += #p3 jv
        scoreboard players operation #t jv *= @s jb.e1
        scoreboard players operation #t jv /= #c2 jv
        scoreboard players operation #v jv += #t jv
    ''')
    # 🎰 족보가 하나 더 걸릴 때마다 +10%씩
    P.add('roll/b2', '''
        scoreboard players operation #u jv = #nh jv
        scoreboard players remove #u jv 1
        scoreboard players operation #u jv *= @s jb.e2
        scoreboard players operation #t jv = #pay jv
        scoreboard players operation #t jv *= #u jv
        scoreboard players operation #t jv /= #c10 jv
        scoreboard players operation #v jv += #t jv
    ''')
    P.add('roll/boost', '''
        scoreboard players operation #m jv = @s jb.u4
        scoreboard players operation #m jv *= #c50 jv
        scoreboard players add #m jv 100
        function jb:roll/vmul
    ''')
    # #v = #v × #m / 100   (#m: 100..1000)
    P.add('roll/vmul', '''
        execute if score #ku jv matches -1 if score #v jv matches 2000000.. run function jb:roll/tok_c
        execute if score #ku jv matches 0 if score #v jv matches 2000000.. run function jb:roll/tok
        execute if score #v jv matches ..2000000 run return run function jb:roll/vmul_d
        function jb:roll/vmul_s
    ''')
    P.add('roll/tok_c', '''
        scoreboard players operation #v jv /= #c100 jv
        scoreboard players set #ku jv 0
    ''')
    P.add('roll/tok', '''
        scoreboard players operation #v jv /= #c1000 jv
        scoreboard players set #ku jv 1
    ''')
    P.add('roll/vmul_d', '''
        scoreboard players operation #v jv *= #m jv
        scoreboard players operation #v jv /= #c100 jv
    ''')
    # 큰 값: 1만 단위로 쪼개 곱한다. 20억(천 단위로는 2조⛃)에서 멈춘다.
    P.add('roll/vmul_s', '''
        scoreboard players operation #vh jv = #v jv
        scoreboard players operation #vh jv /= #c10000 jv
        scoreboard players operation #vl jv = #v jv
        scoreboard players operation #vl jv %= #c10000 jv
        scoreboard players operation #vh jv *= #m jv
        scoreboard players operation #vl jv *= #m jv
        scoreboard players operation #vl jv /= #c100 jv
        execute if score #vh jv matches 20000000.. run return run scoreboard players set #v jv 2000000000
        scoreboard players operation #vh jv *= #c100 jv
        scoreboard players operation #v jv = #vh jv
        scoreboard players operation #v jv += #vl jv
        execute if score #v jv matches 2000000001.. run scoreboard players set #v jv 2000000000
    ''')
    P.add('roll/out0', '''
        scoreboard players set #rth jv 0
        scoreboard players operation #rtl jv = #v jv
        scoreboard players operation #rt jv = #v jv
    ''')
    P.add('roll/out1', '''
        scoreboard players operation #rth jv = #v jv
        scoreboard players operation #rth jv /= #c1000000 jv
        scoreboard players operation #rtl jv = #v jv
        scoreboard players operation #rtl jv %= #c1000000 jv
        scoreboard players operation #rtl jv *= #c1000 jv
        scoreboard players set #rt jv 2000000000
        execute if score #rth jv matches ..1 run function jb:roll/out1b
    ''')
    P.add('roll/out1b', '''
        scoreboard players operation #rt jv = #rth jv
        scoreboard players operation #rt jv *= #c1000000000 jv
        scoreboard players operation #rt jv += #rtl jv
    ''')

    # ------------------------------------------------------------------
    # 기록: 통계, 숫자 기록, 벽, 채팅 줄
    # ------------------------------------------------------------------
    P.add('roll/record', '''
        scoreboard players operation @s jb.mxr > #rt jv
        scoreboard players operation @s jb.mxn > #nh jv
        scoreboard players operation @s jb.mxt > #bt jv
        execute if score #nh jv matches 0 run scoreboard players add @s jb.zn 1
        execute store result storage jb:wk he.n int 1 run scoreboard players get #n jv
        execute store result storage jb:wk he.b int 1 run scoreboard players get #bid jv
        function jb:hist/add with storage jb:wk id
        scoreboard players add @s jb.hn 1
        execute if score @s jb.hn matches 1200.. run function jb:hist/trim with storage jb:wk id
        function jb:rb/add
        execute if score #txt jv matches 1 run function jb:roll/line
        execute if score #newc jv matches 1.. run function jb:roll/news
        execute if score #supc jv matches 1.. run function jb:roll/sups
        execute if data storage jb:wk wq[0] run function jb:roll/pushq with storage jb:wk id
        execute if data storage jb:wk wa[0] run function jb:roll/pusha with storage jb:wk id
    ''')
    P.add('roll/pushq', '''
        $data modify storage jb:pl $(key).w append from storage jb:wk wq[]
        data modify storage jb:wk wq set value []
    ''')
    P.add('roll/pusha', '''
        $data modify storage jb:pl $(key).a append from storage jb:wk wa[]
        data modify storage jb:wk wa set value []
    ''')
    # 채팅 한 줄 (걸린 숫자)
    P.add('roll/line', '''
        data modify storage jb:wk r set value {x:"",bn:{text:""}}
        function jb:num/ns
        execute store result storage jb:wk r.n int 1 run scoreboard players get #n jv
        scoreboard players operation #fh jv = #rth jv
        scoreboard players operation #fl jv = #rtl jv
        function jb:sys/big
        data modify storage jb:wk r.cs set from storage jb:wk cm.o
        execute store result storage jb:wk r.nh int 1 run scoreboard players get #nh jv
        execute store result storage jb:wk r.kind int 1 run scoreboard players get #bt jv
        data modify storage jb:wk r.w set value 0
        execute if score #nh jv matches 1.. run data modify storage jb:wk r.w set value 1
        execute if score #nh jv matches 2.. run function jb:roll/extra
        execute if score #nh jv matches 1.. run function jb:roll/bname
        function jb:vis/build
        data modify storage jb:wk r.vis set from storage jb:wk vis
        execute unless score #rt jv = #pay0 jv run function jb:roll/tipb
        function jb:roll/tip with storage jb:wk r
        data modify storage jb:wk r.bl set from storage jb:wk bl
        execute if score #bt jv matches 4.. run function jb:roll/bcast with storage jb:wk r
        scoreboard players set #lp jv 0
        execute if score #man jv matches 0 run scoreboard players set #lp jv 1
        execute if score #man jv matches 1 if score #bt jv >= #fmin jv run scoreboard players set #lp jv 1
        execute if score #lp jv matches 1 run function jb:roll/push with storage jb:wk id
        execute if score #man jv matches 1 if score #rt jv > @s jb.sbp run function jb:roll/setshown
    ''')
    P.add('roll/extra', '''
        scoreboard players operation #t jv = #nh jv
        scoreboard players remove #t jv 1
        execute store result storage jb:wk rx.x int 1 run scoreboard players get #t jv
        function jb:roll/extra2 with storage jb:wk rx
    ''')
    P.add('roll/extra2', '$data modify storage jb:wk r.x set value " 외 $(x)개"')
    P.add('roll/bname', '''
        execute store result storage jb:wk bi.i int 1 run scoreboard players get #bid jv
        function jb:hand/bn with storage jb:wk bi
    ''')
    P.add('hand/bn', '$data modify storage jb:wk r.bn set from storage jb:hn h$(i).n')
    P.add('roll/tipb', '''
        scoreboard players operation #fn jv = #pay0 jv
        function jb:sys/comma
        function jb:roll/tipb2 with storage jb:wk cm
    ''')
    P.add('roll/tipb2', '$data modify storage jb:wk bl append value %s' % J(T('\n⭐🃏⛃ 보너스 전  +$(o)⛃', 'dark_gray')))
    P.add('roll/tip', '$data modify storage jb:wk bl prepend value %s' % J(
        T('$(ns)', 'white', True, extra=[T('\n족보 $(nh)개  ', 'gray', False), T('+$(cs)⛃', 'yellow', False)])))
    P.add('roll/bcast', '$data modify storage jb:wk wa append value {c:%s}' % J(
        C([T('✦ ', 'gold', True), {'selector': '@s', 'color': 'yellow'}, T('님이 ', 'gray'), '$(bn)', T('! ($(ns))', 'gray')])).replace('"$(bn)"', '$(bn)'))
    P.add('roll/push', '''
        $data modify storage jb:pl $(key).r append from storage jb:wk r
    ''')
    P.add('roll/setshown', '''
        scoreboard players operation @s jb.sbp = #rt jv
        scoreboard players operation @s jb.sbt = #bt jv
        scoreboard players operation @s jb.sn = #n jv
        function jb:roll/svvis with storage jb:wk id
    ''')
    P.add('roll/svvis', '''
        $data modify storage jb:rvv $(key) set value {}
        $data modify storage jb:rvv $(key).v set from storage jb:wk vis
        $data modify storage jb:rvv $(key).b set from storage jb:wk r.bn
        $data modify storage jb:rvv $(key).x set from storage jb:wk r.x
        $data modify storage jb:rvv $(key).rv set from storage jb:wk rvl
        $data modify storage jb:rvv $(key).ln set from storage jb:wk r
        $execute store result storage jb:rvv $(key).lp int 1 run scoreboard players get #lp jv
    ''')
    # 화면에 보여 준 숫자의 줄은 걸러졌더라도 채팅 맨 위에 넣는다
    P.add('roll/bestline', '$execute if data storage jb:rvv $(key){lp:0} run data modify storage jb:pl $(key).r prepend from storage jb:rvv $(key).ln')
    # 채팅 줄 찍기
    line = [{'text': '', 'extra': ['$(vis)'], 'hover_event': {'action': 'show_text', 'value': {'text': '', 'extra': '$(bl)'}},
             'click_event': {'action': 'run_command', 'command': '/trigger jb.srch set $(n)'}},
            T('  '), '$(bn)', T('$(x)', 'gray'), T('  │  ', 'dark_gray'), T('+$(cs)⛃', 'gold', True)]
    s = J(line).replace('"$(vis)"', '$(vis)').replace('"$(bl)"', '$(bl)').replace('"$(bn)"', '$(bn)')
    P.add('roll/m1', '$tellraw @s ' + s)
    line0 = [{'text': '', 'extra': ['$(vis)'], 'hover_event': {'action': 'show_text', 'value': {'text': '', 'extra': '$(bl)'}},
              'click_event': {'action': 'run_command', 'command': '/trigger jb.srch set $(n)'}}, T('  꽝', 'dark_gray')]
    s0 = J(line0).replace('"$(vis)"', '$(vis)').replace('"$(bl)"', '$(bl)')
    P.add('roll/m0', '$tellraw @s ' + s0)
    # 새 족보 / 별 알림 (드문 일)
    P.add('roll/news', '''
        function jb:num/ns
        data modify storage jb:wk nwa.ns set from storage jb:wk r.ns
        execute store result storage jb:wk nwa.pid int 1 run scoreboard players get @s jb.pid
        execute store result storage jb:wk nwa.k int 1 run scoreboard players get #newc jv
        scoreboard players set #nwi jv 0
        data modify storage jb:wk nwl set value []
        function jb:roll/news1
        execute if score #newc jv matches 1 run function jb:roll/news3 with storage jb:wk nwa
        execute if score #newc jv matches 2.. run function jb:roll/news4 with storage jb:wk nwa
        scoreboard players set #newc jv 0
        scoreboard players set @s jb.nwf 1
        scoreboard players set #bdt jv 99
    ''')
    P.add('roll/news1', '''
        execute unless data storage jb:wk nw[0] run return 0
        data modify storage jb:wk nwa.i set from storage jb:wk nw[0]
        data remove storage jb:wk nw[0]
        function jb:roll/news2 with storage jb:wk nwa
        function jb:roll/news1
    ''')
    P.add('roll/news2', '''
        $data modify storage jb:fd f.p$(pid).b$(i) set value "$(ns)"
        $data modify storage jb:wk nwa.nm set from storage jb:hn h$(i).n
        $data modify storage jb:wk nwa.rl set from storage jb:hn h$(i).r
        execute if score #nwi jv matches 1.. run data modify storage jb:wk nwl append value {text:" · ",color:"dark_gray",bold:false}
        $data modify storage jb:wk nwl append from storage jb:hn h$(i).nh
        scoreboard players add #nwi jv 1
    ''')
    P.add('roll/news3', '$data modify storage jb:wk wq append value {c:%s}' % J(
        C([T('🆕 새 족보  ', 'yellow', True), '$(nm)', T('  $(rl)', 'gray')])).replace('"$(nm)"', '$(nm)'))
    P.add('roll/news4', '''
        $data modify storage jb:wk nwe set value {c:{text:"🆕 새 족보 $(k)개  ",color:"yellow",bold:true,extra:[]}}
        data modify storage jb:wk nwe.c.extra set from storage jb:wk nwl
        data modify storage jb:wk wq append from storage jb:wk nwe
    ''')
    P.add('roll/sups', '''
        scoreboard players set #supc jv 0
        function jb:roll/sups1
    ''')
    P.add('roll/sups1', '''
        execute unless data storage jb:wk su[0] run return 0
        function jb:roll/sups2 with storage jb:wk su[0]
        data remove storage jb:wk su[0]
        function jb:roll/sups1
    ''')
    P.add('roll/sups2', '''
        $data modify storage jb:wk sua set value {s:$(s)}
        $data modify storage jb:wk sua.nm set from storage jb:hn h$(i).n
        function jb:roll/sups3 with storage jb:wk sua
    ''')
    P.add('roll/sups3', '$data modify storage jb:wk wq append value {c:%s}' % J(
        [T('★ 별이 올랐어요! ', 'gold', True), '$(nm)', T(' ★$(s)', 'gold', True), T('   ⭐ +1', 'aqua', True)]).replace('"$(nm)"', '$(nm)'))

    # ------------------------------------------------------------------
    # 모아 둔 출력 내보내기
    # ------------------------------------------------------------------
    P.add('roll/flush', '''
        data remove storage jb:wk fl
        data remove storage jb:wk fw
        data remove storage jb:wk fa
        $data modify storage jb:wk fl set from storage jb:pl $(key).r
        $data modify storage jb:wk fw set from storage jb:pl $(key).w
        $data modify storage jb:wk fa set from storage jb:pl $(key).a
        $data modify storage jb:pl $(key) set value {r:[],w:[],a:[]}
        execute if data storage jb:wk fl[0] run function jb:roll/fl_loop
        execute if data storage jb:wk fw[0] run function jb:roll/fw_loop
        execute if data storage jb:wk fa[0] run function jb:roll/fa_loop
        execute if score @s jb.nwf matches 1 run function jb:fx/new
    ''')
    P.add('roll/fl_loop', '''
        function jb:roll/fl_one with storage jb:wk fl[0]
        data remove storage jb:wk fl[0]
        execute if data storage jb:wk fl[0] run function jb:roll/fl_loop
    ''')
    P.add('roll/fl_one', '$function jb:roll/m$(w) with storage jb:wk fl[0]')
    P.add('roll/fw_loop', '''
        function jb:roll/fw_one with storage jb:wk fw[0]
        data remove storage jb:wk fw[0]
        execute if data storage jb:wk fw[0] run function jb:roll/fw_loop
    ''')
    P.add('roll/fw_one', '$tellraw @s $(c)')
    P.add('roll/fa_loop', '''
        function jb:roll/fa_one with storage jb:wk fa[0]
        data remove storage jb:wk fa[0]
        execute if data storage jb:wk fa[0] run function jb:roll/fa_loop
    ''')
    P.add('roll/fa_one', '$tellraw @a $(c)')
    P.add('roll/key_m', '''
        execute store result storage jb:wk id.pid int 1 run scoreboard players get @s jb.pid
        function jb:roll/key_m2 with storage jb:wk id
    ''')
    P.add('roll/key_m2', '$data modify storage jb:wk id.key set value "p$(pid)"')
    P.add('roll/key_a', '''
        execute store result storage jb:wk id.pid int 1 run scoreboard players get @s jb.pid
        function jb:roll/key_a2 with storage jb:wk id
    ''')
    P.add('roll/key_a2', '$data modify storage jb:wk id.key set value "a$(pid)"')
    P.add('roll/clear', '$data modify storage jb:pl $(key) set value {r:[],w:[],a:[]}')

    # ------------------------------------------------------------------
    # 직접 굴리기 (상태: 6 계산 → 2 숫자 공개 → 5 족보 하나씩 → 3 마무리 → 0)
    # ------------------------------------------------------------------
    P.add('roll/click', '''
        scoreboard players set @s jb.hold 6
        function jb:roll/request
    ''')
    P.add('roll/request', '''
        execute if score @s jb.state matches 2 run return 0
        execute if score @s jb.state matches 5..6 run return 0
        function jb:roll/start
    ''')
    P.add('roll/start', '''
        scoreboard players set @s jb.state 6
        scoreboard players set @s jb.q 0
        scoreboard players operation @s jb.qn = @s jb.u3
        scoreboard players add @s jb.qn 1
        scoreboard players set @s jb.pc 0
        scoreboard players set @s jb.pcb 0
        scoreboard players set @s jb.sbp -1
        scoreboard players set @s jb.sbt -1
        scoreboard players set @s jb.fwm 0
        scoreboard players set @s jb.t 0
        scoreboard players set @s jb.k 0
        function jb:roll/key_m
        function jb:roll/clear with storage jb:wk id
        %s
        function jb:roll/evstep
    ''' % snd('block.note_block.chime', 60, 1.6))
    P.add('roll/tick', '''
        execute if score @s jb.state matches 2 run return run function jb:roll/anim
        execute if score @s jb.state matches 3 run return run function jb:roll/after
        execute if score @s jb.state matches 5 run return run function jb:roll/hrv
        execute if score @s jb.state matches 6 run return run function jb:roll/evstep
    ''')
    P.add('roll/evstep', '''
        scoreboard players set #man jv 1
        function jb:roll/fmin
        function jb:roll/pre
        function jb:roll/key_m
        function jb:roll/ev1
        function jb:roll/ev1
        function jb:roll/ev1
        function jb:roll/ev1
        execute if score @s jb.q >= @s jb.qn run function jb:roll/anim_start
    ''')
    P.add('roll/ev1', '''
        execute if score @s jb.q >= @s jb.qn run return 0
        function jb:roll/one
        function jb:roll/credit_m
        scoreboard players add @s jb.q 1
    ''')
    P.add('roll/credit_m', '''
        execute if score #bt jv matches 4.. run scoreboard players set @s jb.fwm 1
        scoreboard players operation @s jb.pc += #rtl jv
        execute if score @s jb.pc matches 1000000000.. run scoreboard players add @s jb.pcb 1
        execute if score @s jb.pc matches 1000000000.. run scoreboard players remove @s jb.pc 1000000000
        scoreboard players operation @s jb.pcb += #rth jv
    ''')
    lines = ['scoreboard players set @s jb.state 2', 'scoreboard players set @s jb.k 0', 'scoreboard players set @s jb.t 0']
    for lv, t in enumerate(SPEED_T):
        lines.append('execute if score @s jb.u1 matches %d run scoreboard players set @s jb.tt %d' % (lv, t))
    lines += ['function jb:show/calc', 'function jb:roll/key_m', 'function jb:show/save with storage jb:wk id',
              'title @s times 0 20 6', 'function jb:roll/show']
    P.fn('roll/anim_start').extend(lines)
    P.add('roll/anim', '''
        scoreboard players add @s jb.t 1
        scoreboard players operation #kt jv = @s jb.t
        scoreboard players operation #kt jv *= #c10 jv
        scoreboard players operation #kt jv /= @s jb.tt
        scoreboard players operation #kt jv < #c9 jv
        execute if score @s jb.t >= @s jb.tt run scoreboard players set #kt jv 9
        execute if score #kt jv > @s jb.k run function jb:roll/lock
        function jb:roll/show
        execute if score @s jb.t >= @s jb.tt if score @s jb.k matches 9.. run function jb:roll/hrstart
    ''')
    P.add('roll/lock', '''
        scoreboard players add @s jb.k 1
        execute if score @s jb.k >= #kt jv run %s
        execute if score @s jb.k < #kt jv run function jb:roll/lock
    ''' % snd('block.note_block.hat', 55, 1.0))
    P.add('roll/show', '''
        function jb:roll/key_m
        execute store result storage jb:wk id.k int 1 run scoreboard players get @s jb.k
        function jb:roll/show1 with storage jb:wk id
    ''')
    P.add('roll/show1', '''
        $data modify storage jb:wk hfw.f set from storage jb:an $(key).f[$(k)]
        function jb:roll/show2 with storage jb:wk hfw
    ''')
    P.add('roll/show2', '''
        title @s subtitle {"text":""}
        $title @s title $(f)
    ''')
    # 족보 하나씩 보여 주기
    P.add('roll/hrstart', '''
        execute if score @s jb.e4 matches 5.. run return run function jb:roll/finish
        scoreboard players set @s jb.state 5
        scoreboard players set @s jb.rvt 99
    ''')
    P.add('roll/hrv', '''
        scoreboard players add @s jb.rvt 1
        scoreboard players set #hR jv 10
        scoreboard players operation #t jv = @s jb.e4
        scoreboard players operation #t jv *= #c2 jv
        scoreboard players operation #hR jv -= #t jv
        execute if score @s jb.rvt < #hR jv run return 0
        scoreboard players set @s jb.rvt 0
        function jb:roll/key_m
        function jb:roll/hr1 with storage jb:wk id
    ''')
    P.add('roll/hr1', '''
        $execute unless data storage jb:rvv $(key).rv[0] run return run function jb:roll/finish
        $execute store result storage jb:wk hx.i int 1 run data get storage jb:rvv $(key).rv[0]
        $data remove storage jb:rvv $(key).rv[0]
        scoreboard players operation #n jv = @s jb.sn
        function jb:num/d9
        function jb:hand/mprep
        function jb:roll/lcclr
        function jb:hand/mk/clr
        title @s times 0 40 6
        function jb:roll/hr2 with storage jb:wk hx
    ''')
    P.add('roll/lcclr', '\n'.join('scoreboard players set #lc%d jv 0' % i for i in range(1, 10)))
    P.add('roll/hr2', '''
        $execute store result score #ml jv run data get storage jb:hn h$(i).t
        scoreboard players add #ml jv 1
        $function jb:hand/m/$(i)
        function jb:hand/mk/merge
        function jb:vis/build
        data modify storage jb:wk hx.v set from storage jb:wk vis
        $data modify storage jb:wk hx.s set from storage jb:hn h$(i).n
        function jb:roll/hr3 with storage jb:wk hx
        scoreboard players operation #lv jv = #ml jv
        function jb:roll/ding
    ''')
    P.add('roll/hr3', '''
        $title @s subtitle $(s)
        $title @s title $(v)
    ''')
    ding = []
    ding.append('execute if score #lv jv matches 1 run ' + snd('block.note_block.pling', 50, 1.0))
    ding.append('execute if score #lv jv matches 2 run ' + snd('block.note_block.pling', 65, 1.26))
    ding.append('execute if score #lv jv matches 3 run ' + snd('block.note_block.chime', 75, 1.41))
    ding.append('execute if score #lv jv matches 3 run ' + snd('block.note_block.pling', 45, 1.41))
    ding.append('execute if score #lv jv matches 4 run ' + snd('block.note_block.chime', 85, 1.68))
    ding.append('execute if score #lv jv matches 4 run ' + snd('block.amethyst_block.chime', 85, 1.2))
    ding.append('execute if score #lv jv matches 5.. run ' + snd('block.note_block.bell', 90, 2.0))
    ding.append('execute if score #lv jv matches 5.. run ' + snd('block.note_block.chime', 85, 1.5))
    ding.append('execute if score #lv jv matches 5.. run ' + snd('block.amethyst_block.chime', 90, 1.0))
    ding.append('execute if score #lv jv matches 6 run ' + snd('ui.toast.challenge_complete', 80, 1.2))
    ding.append('execute if score #lv jv matches 4.. unless score @s jb.mfw matches 1 at @s run particle minecraft:end_rod ~ ~1.2 ~ 0.5 0.6 0.5 0.03 14 force @s')
    P.fn('roll/ding').extend(ding)
    P.add('roll/finish', '''
        scoreboard players set @s jb.state 3
        scoreboard players set @s jb.t 0
        scoreboard players operation @s jb.rolls += @s jb.qn
        scoreboard players operation #cgh jv = @s jb.pcb
        scoreboard players operation #cgl jv = @s jb.pc
        function jb:sys/addc2
        scoreboard players operation #sen jv = @s jb.qn
        function jb:stats/earn
        scoreboard players set @s jb.end 40
        title @s times 0 40 10
        function jb:roll/fsum
        function jb:roll/fsnd
        function jb:roll/key_m
        function jb:roll/bestline with storage jb:wk id
        function jb:roll/flush with storage jb:wk id
        execute if score @s jb.fwm matches 1 run function jb:fx/big
        scoreboard players set @s jb.fwm 0
        function jb:adv/chk
    ''')
    P.add('roll/after', '''
        scoreboard players add @s jb.t 1
        execute if score @s jb.t >= @s jb.end run scoreboard players set @s jb.state 0
    ''')
    P.add('roll/fsum', '''
        function jb:roll/key_m
        scoreboard players operation #fh jv = @s jb.pcb
        scoreboard players operation #fl jv = @s jb.pc
        function jb:sys/big
        function jb:roll/fsumv with storage jb:wk id
        data modify storage jb:wk fz.c set from storage jb:wk cm.o
        execute if score @s jb.sbt matches ..-1 run return run function jb:roll/fsum0 with storage jb:wk fz
        function jb:roll/fsum1 with storage jb:wk fz
    ''')
    P.add('roll/fsumv', '$data modify storage jb:wk fz set from storage jb:rvv $(key)')
    P.add('roll/fsum0', '''
        title @s subtitle {"text": "꽝", "color": "gray", "bold": true}
        $title @s title $(v)
    ''')
    sub = [T('✦ ', 'gold'), '$(b)', T('$(x)', 'gray'), T('   +$(c)⛃', 'gold', True)]
    P.add('roll/fsum1', '$title @s subtitle ' + J(sub).replace('"$(b)"', '$(b)') + '\n$title @s title $(v)')
    fs = ['execute if score @s jb.sbt matches ..-1 run return run ' + snd('block.note_block.bass', 50, 0.8),
          'execute if score @s jb.sbt matches 0 run ' + snd('block.note_block.pling', 80, 1),
          'execute if score @s jb.sbt matches 1 run ' + snd('entity.experience_orb.pickup', 80, 1),
          'execute if score @s jb.sbt matches 2 run ' + snd('entity.player.levelup', 80, 1),
          'execute if score @s jb.sbt matches 3.. unless score @s jb.mhero matches 1 run ' + snd('ui.toast.challenge_complete', 80, 1)]
    P.fn('roll/fsnd').extend(fs)

    # ------------------------------------------------------------------
    # 자동 굴리기
    # ------------------------------------------------------------------
    at = ['scoreboard players add @s jb.at 1',
          'execute if score @s jb.asx matches 1 run return run function jb:roll/auto_step',
          'scoreboard players set #per jv -1']
    for lv, t in enumerate(SPEED_T):
        at.append('execute if score @s jb.u1 matches %d run scoreboard players add #per jv %d' % (lv, t))
    for lv, t in enumerate(AUTO_END):
        if lv:
            at.append('execute if score @s jb.u2 matches %d run scoreboard players add #per jv %d' % (lv, t))
    at.append('execute if score @s jb.at >= #per jv run function jb:roll/auto_session')
    P.fn('roll/autotick').extend(at)
    P.add('roll/auto_session', '''
        scoreboard players set @s jb.at 0
        scoreboard players set @s jb.afw 0
        scoreboard players set @s jb.afh -1
        scoreboard players set @s jb.aq 0
        scoreboard players operation @s jb.aqn = @s jb.u3
        scoreboard players add @s jb.aqn 1
        function jb:roll/key_a
        function jb:roll/clear with storage jb:wk id
        scoreboard players set @s jb.asx 1
        function jb:roll/auto_step
    ''')
    P.add('roll/auto_step', '''
        scoreboard players set #man jv 0
        function jb:roll/fmin
        function jb:roll/pre
        function jb:roll/key_a
        function jb:roll/auto_one
        function jb:roll/auto_one
        function jb:roll/auto_one
        function jb:roll/auto_one
        execute if score @s jb.aq >= @s jb.aqn run function jb:roll/auto_end
    ''')
    # 채팅에 보여 줄 숫자 (설정): 그 등급 이상만
    P.add('roll/fmin', '''
        scoreboard players set #fmin jv 2
        execute if score @s jb.achat matches 1 run scoreboard players set #fmin jv 3
        execute if score @s jb.achat matches 2 run scoreboard players set #fmin jv 4
        execute if score @s jb.achat matches 3 run scoreboard players set #fmin jv 99
        execute if score @s jb.achat matches 4 run scoreboard players set #fmin jv -1
    ''')
    P.add('roll/auto_one', '''
        execute if score @s jb.aq >= @s jb.aqn run return 0
        function jb:roll/one
        function jb:roll/credit_a
        scoreboard players add @s jb.aq 1
    ''')
    P.add('roll/credit_a', '''
        execute if score #bt jv matches 4.. run scoreboard players set @s jb.afw 1
        scoreboard players operation @s jb.afh > #bt jv
        scoreboard players operation #cgh jv = #rth jv
        scoreboard players operation #cgl jv = #rtl jv
        function jb:sys/addc2
        scoreboard players set #sen jv 1
        function jb:stats/earn
        scoreboard players operation @s jb.asum += #rtl jv
        execute if score @s jb.asum matches 1000000000.. run scoreboard players add @s jb.asumb 1
        execute if score @s jb.asum matches 1000000000.. run scoreboard players remove @s jb.asum 1000000000
        scoreboard players operation @s jb.asumb += #rth jv
        scoreboard players add @s jb.rolls 1
        scoreboard players add @s jb.arl 1
        execute if score #bt jv matches 3.. unless score @s jb.state matches 1.. unless score @s jb.alert matches 1.. run function jb:roll/auto_alert
    ''')
    P.add('roll/auto_alert', '''
        scoreboard players operation #kind jv = #bt jv
        scoreboard players add #kind jv 1
        function jb:fx/hit
        scoreboard players set @s jb.alert 40
    ''')
    P.add('roll/auto_end', '''
        scoreboard players set @s jb.asx 0
        function jb:roll/key_a
        function jb:roll/flush with storage jb:wk id
        execute if score @s jb.afw matches 1 unless score @s jb.fwt matches 1.. run function jb:fx/big
        execute if score @s jb.afh matches 3.. unless score @s jb.asc matches 1.. unless score @s jb.mhero matches 1 run %s
        execute if score @s jb.afh matches 3.. unless score @s jb.asc matches 1.. run scoreboard players set @s jb.asc 30
    ''' % snd('ui.toast.challenge_complete', 80, 1))
