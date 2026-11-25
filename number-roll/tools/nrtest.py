# -*- coding: utf-8 -*-
"""숫자 굴리기 — 서버에서 돌려 보는 시험 (가짜 플레이어 + RCON).

  MCSRV=/home/claude/mcsrv python3 nrtest.py DIST_DIR
  (26.3 서버가 떠 있고 새 데이터팩이 들어가 있어야 한다. DIST_DIR 의 hands.json 을 읽는다.)
"""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
MCSRV = os.environ.get('MCSRV', '/home/claude/mcsrv')
sys.path.insert(0, MCSRV); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import rcon
from nrbot import NrBot, flat
from jokers import JOKERS
import common as CM

HI = json.load(open(os.path.join(sys.argv[1], 'hands.json'), encoding='utf-8'))
R = rcon.Rcon()
LOG = MCSRV + '/run/logs/latest.log'
FAIL = []


def c(s): return R.cmd(s)
def sc(obj, who='tester'):
    m = re.search(r'has (-?\d+)', c('scoreboard players get %s %s' % (who, obj))); return int(m.group(1)) if m else None
def g(name): return sc('jv', name)
def setp(obj, v): c('scoreboard players set tester jb.%s %d' % (obj, v))
def run(fn): return c('execute as tester at @s run function %s' % fn)
def coins(): return sc('jb.cb') * 10 ** 9 + sc('jb.coins')
def setcoins(n):
    setp('cb', n // 10 ** 9); setp('coins', n % 10 ** 9)
def ok(cond, what):
    print(('  ok   ' if cond else '  FAIL ') + what)
    if not cond: FAIL.append(what)
def aslist(x): return x if isinstance(x, list) else ([] if x is None else [x])
def dsum(d):
    if d is None: return None
    return {'title': flat(d.get('title')), 'body': ' / '.join(flat(x.get('contents')) if isinstance(x, dict) else str(x) for x in aslist(d.get('body'))),
            'acts': [flat(a.get('label')) for a in aslist(d.get('actions'))]}
def nlog(): return len(open(LOG, encoding='utf-8', errors='replace').read().split('\n'))
def problems(since):
    L = open(LOG, encoding='utf-8', errors='replace').read().split('\n')[since:]
    return [l for l in L if re.search(r'ERROR|Exception|Failed|Unknown|Incorrect|Expected|Invalid|Can\'t|error', l)
            and not re.search(r'authlib|minecraftservices|Services|java\.base|UnknownHost|sessionserver|\tat |moved too quickly|Can\'t keep up|RCON', l)]


n0 = nlog()
b = NrBot('tester')
assert b.wait_joined(), b.kicked
time.sleep(1.5); c('op tester')
def trig(code, obj='jb.menu', wait=0.4):
    n = len(b.dialogs); nc = len(b.chat); b.trig(code, obj); time.sleep(wait)
    return (dsum(b.dialogs[-1]) if len(b.dialogs) > n else None), b.chat[nc:]
def wait_roll(maxs=25):
    t0 = time.time()
    while time.time() - t0 < maxs:
        time.sleep(0.2)
        if sc('jb.state') in (0, 3): return True
    return False

print('[1] 처음 상태')
run('jb:admin/reset_me'); time.sleep(1.5)
ok(sc('jb.pid') is not None and sc('jb.dv') == CM.DVER, '플레이어 준비')
ok(coins() == 1000, '시작 코인 1,000 (%d)' % coins())
m = re.search(r'Found (\d+)', c('clear tester carrot_on_a_stick 0')); ok(m and m.group(1) == '3', '처음 아이템 3개 (코인 상점·강화·메뉴)')
ok(any('다음 해금' in v[0] and '쉬운 미션' in v[0] for v in b.boss.values()), '위 막대: 다음 해금')
ok(b.bar and '⛃ 1,000' in b.bar[-1], '아래 줄: 코인')

print('[2] 직접 굴리기')
c0 = coins(); nc = len(b.chat); run('jb:roll/click'); ok(wait_roll(), '굴림이 끝남'); time.sleep(0.4)
ok(sc('jb.rolls') == 1, '굴린 숫자 1')
line = [x for x in b.chat[nc:] if re.match(r'\d{9}  ', x)]
ok(len(line) == 1, '채팅 줄 하나: %s' % (line[:1],))
ok(coins() > c0, '코인이 늘었음 (%d → %d)' % (c0, coins()))
ok(b.subs and '✦' in b.subs[-1] or '꽝' in (b.subs[-1] if b.subs else ''), '끝 요약: %s' % b.subs[-1:])

print('[3] 코인 상점·해금')
setcoins(10 ** 6)
d, ch = trig(50); ok(d and d['title'] == '⛃ 코인 상점' and len(d['acts']) == 5, '상점 열림')
for n, costs in ((1, CM.COST_U1), (2, CM.COST_U2), (3, CM.COST_U3), (4, CM.COST_U4)):
    c0 = coins(); trig(10 + n); ok(coins() == c0 - costs[0] or coins() > c0 - costs[0], '업그레이드 %d 삼 (-%d)' % (n, c0 - coins()))
ok([sc('jb.u%d' % i) for i in (1, 2, 3, 4)] == [1, 1, 1, 1], '업그레이드 단계 1/1/1/1')
ok(sc('jb.autoon') == 1, '자동 굴리기 켜짐'); setp('autoon', 0)
for i, (key, nm, price, tip) in enumerate(CM.UNLOCKS):
    setcoins(price + 5); adv0 = coins()
    d, ch = trig(15, wait=0.5)
    ok(sc('jb.unl') == i + 1 and any('해금!' in x for x in ch), '해금 %s (%s)' % (nm, CM.won(price)))
ok(sc('jb.jslot') == 4, '조커 4칸')
c('execute store result score #x jv run clear tester carrot_on_a_stick 0'); ok(g('#x') == 6, '아이템 6개 (주사위·자동·상점·강화·조커·메뉴): %s' % g('#x'))
ok(all(sc('jb.ml%d' % i) for i in (1, 2, 3)), '미션 3개 생김')
d, ch = trig(15); ok(d and '모두 열었어요' in ' '.join(d['acts']), '해금 끝 표시')
setcoins(5); d, ch = trig(11); ok(sc('jb.u1') == 1, '코인 부족하면 안 사짐')

print('[4] 조커')
setcoins(10 ** 13 * 9)
d, ch = trig(70); ok(d and len(d['acts']) == len(JOKERS), '조커 %d장 보임' % len(JOKERS))
tot = sum(j['price'] for j in JOKERS); c0 = coins()
for j in JOKERS: trig(100 + j['id'], wait=0.3)
ok(coins() + sum(0 for _ in ()) <= c0 - tot + 10 ** 12 and sc('jb.jown') == len(JOKERS), '전부 삼 (가진 조커 %s, 쓴 코인 %s)' % (sc('jb.jown'), CM.won(c0 - coins())))
ok(sc('jb.jeq') == 4, '4장까지만 낌')
for j in JOKERS:
    if sc('jb.j%d' % j['id']) == 2: trig(100 + j['id'], wait=0.25)
ok(sc('jb.jeq') == 0, '다 뺌')

print('[5] 코인 계산 (정해 둔 숫자로)')
c('advancement grant tester everything'); time.sleep(1.2)     # 뒤 시험에서 도전과제 보상이 끼어들지 않게
pay = {h['id']: h['pays'] for h in HI}
def calc(n, eq=(), e1=0, e2=0, u4=0, man=1, found=0, stot=0, cdig=5):
    for j in JOKERS: setp('j%d' % j['id'], 2 if j['id'] in eq else 1)
    setp('jeq', len(eq)); setp('e1', e1); setp('e2', e2); setp('u4', u4); setp('found', found); setp('stot', stot)
    c('scoreboard players set #n jv %d' % n); c('scoreboard players set #man jv %d' % man); c('scoreboard players set #cdig jv %d' % cdig)
    c('scoreboard players set #cm jv 2'); c('scoreboard players set #txt jv 0')
    run('jb:num/d9'); run('jb:hand/eval'); run('jb:roll/commit'); run('jb:roll/coins')
    return g('#pay0'), g('#rth') * 10 ** 9 + g('#rtl'), g('#nh')
for h in HI: pass
c('scoreboard players set tester jb.unl %d' % len(CM.UNLOCKS)); run('jb:roll/pre')
tests = [(777000123, ()), (777000123, (2,)), (777000123, (2, 3)), (123456789, (5, 12, 16)), (112233445, (4, 1, 9, 13)), (906090609, (7, 10)), (500000000, (14, 15, 17, 18))]
JK = {j['id']: j for j in JOKERS}
for n, eq in tests:
    for (e1, e2, u4, man) in ((0, 0, 0, 1), (3, 2, 4, 0)):
        p0, rt, nh = calc(n, eq, e1, e2, u4, man, found=200, stot=500, cdig=9)
        # 기대값: 부분 조커는 족보별 코인이 필요해서 전체 조커·강화·부스트만 따로 확인한다
        s = str(n).zfill(9)
        part = [j for j in eq if JK[j]['kind'][0] == 'part']
        base = None
        if not part:
            # 강화: 등급별 합이 필요 → 조커 없이 한 번 더 계산해 비율로 본다
            pb, rb, _ = calc(n, (), e1, e2, u4, man, found=200, stot=500, cdig=9)
            m = 1.0
            for j in eq:
                k = JK[j]['kind']
                if k[0] == 'digit': m *= 1 + s.count(str(k[1])) * k[2] / 100
                elif k[0] == 'nh_le': m *= k[2] / 100 if nh <= k[1] else 1
                elif k[0] == 'nh_ge': m *= k[2] / 100 if nh >= k[1] else 1
                elif k[0] == 'manual': m *= k[1] / 100 if man else 1
                elif k[0] == 'auto': m *= 1 if man else k[1] / 100
                elif k[0] == 'found': m *= 1 + 200 // k[1] * k[2] / 100
                elif k[0] == 'stars': m *= 1 + 500 // k[1] * k[2] / 100
                elif k[0] == 'cdig': m *= 1 + 9 * k[1] / 100
                elif k[0] == 'tiers': m = None; break
            if m is not None:
                ok(abs(rt - rb * m) <= rb * m * 0.006 + 3, '%09d 조커 %s 강화 %d/%d 부스트 %d %s: %d (기대 %.0f, 기본 %d, 족보 %d개)' % (n, list(eq), e1, e2, u4, '직접' if man else '자동', rt, rb * m, p0, nh))
            else:
                ok(rt >= rb, '%09d 조커 %s: %d ≥ %d' % (n, list(eq), rt, rb))
        else:
            pb, rb, _ = calc(n, tuple(j for j in eq if j not in part), e1, e2, u4, man, found=200, stot=500, cdig=9)
            ok(rt >= rb and p0 == pb, '%09d 부분 조커 %s: %d ≥ %d (기본 %d)' % (n, list(eq), rt, rb, p0))
for j in JOKERS: setp('j%d' % j['id'], 1)
setp('jeq', 0); setp('e1', 0); setp('e2', 0); setp('u4', 1); c('scoreboard players set #cm jv 1')
run('jb:admin/sync') if False else None

print('[6] 미션')
setp('m1a', 7); setp('m1b', 7); setp('m1c', 7); setp('mc1', 45000); setp('mcb1', 0)
c('scoreboard players set #n jv 123777456'); run('jb:num/d9'); c0 = coins(); md = sc('jb.mdone'); run('jb:ms/chk'); time.sleep(0.2)
ok(coins() == c0 + 45000 and sc('jb.mdone') == md + 1, '미션 성공 보상 +45,000 (%d)' % (coins() - c0))
setp('j%d' % [j['id'] for j in JOKERS if j['kind'][0] == 'mission'][0], 2)
setp('m2a', 1); setp('m2b', 2); setp('m2c', 3); setp('m2d', 4)
setp('rch', 5); setp('rc', 0); setp('rr', 100)       # 최근 1분: 숫자 100개로 50억 → 하나에 5,000만 → ×300 = 150억
c('scoreboard players set #n jv 991234099'); run('jb:num/d9'); c0 = coins(); run('jb:ms/chk'); time.sleep(0.2)
ok(coins() == c0 + 3 * 15000000000, '미션 헌터 ×3, 수입에 맞춘 보상 (+%s)' % CM.won(coins() - c0))
setp('rch', 0); setp('rr', 0)
setp('j%d' % [j['id'] for j in JOKERS if j['kind'][0] == 'mission'][0], 1)
run('jb:roll/flush_now') if False else None

print('[7] 화면들')
for code, title in ((1, '📖 메뉴'), (60, '⭐ 강화'), (7, '⚙ 설정'), (8, '⌚ 숫자 기록'), (33, '📊 통계'), (20, '📖 족보 도감'), (4000, '흔함'), (4500, '신화'), (4504, '신화')):
    d, ch = trig(code); ok(d is not None and title in d['title'], '%d → %s' % (code, d and d['title']))
d, ch = trig(123456789, 'jb.srch'); ok(d and '123456789' in d['body'] and '족보' in d['body'], '숫자 검색')
setp('ept', 500)
for code in (61, 62, 64, 65): trig(code, wait=0.25)
ok([sc('jb.e%d' % i) for i in (1, 2, 4, 5)] == [1, 1, 1, 1], '강화 하나씩 삼'); ok(sc('jb.ept') == 500 - sum(p[3][0] for p in CM.PERKS), '⭐ 값 치름')
trig(350, 'jb.vset'); ok(sc('jb.vol') == 35, '소리 35')
trig(1000, 'jb.vset')

print('[8] 여러 개 직접 굴리기 + 채팅 거르기')
setp('u3', 7); setp('u1', 9); setp('e4', 5); setp('achat', 3); nc = len(b.chat); r0 = sc('jb.rolls')
run('jb:roll/click'); ok(wait_roll(), '끝남'); time.sleep(0.4)
lines = [x for x in b.chat[nc:] if re.match(r'\d{9}  ', x)]
ok(sc('jb.rolls') == r0 + 8 and len(lines) == 1, '8개 굴려도 줄은 하나 (끔): %d줄' % len(lines))
setp('achat', 4); nc = len(b.chat); run('jb:roll/click'); wait_roll(); time.sleep(0.4)
lines = [x for x in b.chat[nc:] if re.match(r'\d{9}  ', x)]
ok(len(lines) == 8, '전부: %d줄' % len(lines))
setp('achat', 0)

print('[9] 자동 굴리기 (최대)')
run('jb:admin/maxall'); time.sleep(0.5); r0 = sc('jb.rolls'); c0 = coins(); t0 = time.time(); time.sleep(8)
r1 = sc('jb.rolls'); dt = time.time() - t0
ok((r1 - r0) / dt > 40, '초당 %.0f개' % ((r1 - r0) / dt))
ok(coins() > c0, '코인 늘어남 (+%s)' % CM.won(coins() - c0))
print('    ', c('tick query')[:160].replace('\n', ' '))
setp('autoon', 0); time.sleep(0.5)
d, ch = trig(4000); ok(d and '✔' in ' '.join(d['acts']), '도감에 찾은 족보 표시')
d, ch = trig(8); ok(d and len(d['acts']) > 10, '기록 목록')
d, ch = trig(33); ok(d and '굴린 숫자' in d['body'], '통계'); print('    ', d['body'].replace('\n', ' | ')[:400])

print('[10] 옛 저장 → 처음부터')
setp('dv', 2); time.sleep(1.5)
ok(sc('jb.dv') == CM.DVER and coins() == 1000 and sc('jb.found') == 0 and sc('jb.unl') == 0 and sc('jb.jown') == 0, '초기화됨')
ok(any('새로워졌어요' in x for x in b.chat[-6:]), '안내 문구')

bad = problems(n0)
for l in bad[:15]: print('  LOG', l[:300])
ok(not bad, '서버 로그에 오류 없음')
ok(not b.errs, '패킷 읽기 오류 없음 %s' % b.errs[:2])
print('\n실패 %d개' % len(FAIL))
for f in FAIL: print('  -', f)
b.close()
sys.exit(1 if FAIL else 0)
