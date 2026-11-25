# -*- coding: utf-8 -*-
"""공통 상수·도구 (글자 조립, 대화상자, 가격표)."""
import json

NS = 'jb'
DVER = 3          # 플레이어 데이터 판 — 바뀌면 진행도를 처음부터
BVER = 14         # 월드(벽) 판 — 바뀌면 벽을 다시 짓는다
NHANDS = 400

TIER_NAME = ['흔함', '보통', '희귀', '영웅', '전설', '신화']
TIER_COLOR = ['white', 'green', 'aqua', 'light_purple', 'gold', 'red']
# 숫자가 빛나는 색 (0 = 안 걸린 자리)
LIT = ['#7C7C7C', '#F2F2F2', '#55FF55', '#55FFFF', '#FF77FF', '#FFC400', '#FF4545']
# 벽 '최근 숫자'의 색 (꽝, 흔함…신화)
WALL = ['#4F4F4F', '#9A9A9A', '#55FF55', '#55FFFF', '#FF77FF', '#FFC400', '#FF4545']

# 별: 등급별로 ★2..★5가 되는 누적 횟수, 별 하나당 코인 +25%
STAR_T = [[50, 250, 1000, 5000], [20, 100, 400, 1500], [10, 40, 150, 500], [5, 15, 50, 150], [3, 8, 20, 50], [2, 4, 8, 15]]

# 코인 상점
SPEED_T = [100, 85, 63, 50, 40, 30, 20, 13, 8, 4, 1]           # 숫자 하나가 다 나오는 틱
AUTO_END = [0, 100, 75, 50, 33, 20, 13, 8, 5, 3, 1]            # 자동: 결과 뒤 쉬는 틱
COST_U1 = [2000, 7000, 23000, 70000, 200000, 600000, 1500000, 3700000, 9500000, 21000000]
COST_U2 = [3500, 22000, 90000, 300000, 1000000, 3000000, 8500000, 22000000, 55000000, 140000000]
COST_U3 = [6000, 50000, 280000, 1300000, 5500000, 21000000, 75000000]
COST_U4 = [5000, 26000, 100000, 420000, 1500000, 4800000, 13000000, 37000000, 95000000, 270000000]

# 해금 (순서대로 하나씩)
UNLOCKS = [
    ('ms1', '📋 쉬운 미션', 10000, '세 자리 미션이 열려요'),
    ('dice', '⚀ 주사위', 30000, '어디서든 굴릴 수 있는 주사위를 받아요'),
    ('jk1', '🃏 조커 1칸', 100000, '조커를 1장 낄 수 있어요'),
    ('jk2', '🃏 조커 2칸', 1500000, '조커를 2장 낄 수 있어요'),
    ('ms2', '📋 보통 미션', 10000000, '네 자리 미션이 열려요'),
    ('t4', '전설 족보', 100000000, '전설 족보가 나오기 시작해요'),
    ('jk3', '🃏 조커 3칸', 3000000000, '조커를 3장 낄 수 있어요'),
    ('ms3', '📋 어려운 미션', 10000000000, '다섯 자리 미션이 열려요'),
    ('jk4', '🃏 조커 4칸', 60000000000, '조커를 4장 낄 수 있어요'),
    ('t5', '신화 족보', 300000000000, '신화 족보가 나오기 시작해요'),
]


def unl_stage(key):
    """이 해금이 끝난 상태의 jb.unl 값"""
    return [u[0] for u in UNLOCKS].index(key) + 1


# 미션: 자리 수, 기본 보상, 해금, '숫자 하나 평균 수입'의 몇 배 (둘 중 큰 쪽을 준다)
MISSIONS = [(1, '쉬움', 'green', 3, 30000, 'ms1', 30), (2, '보통', 'yellow', 4, 330000, 'ms2', 300), (3, '어려움', 'red', 5, 4000000, 'ms3', 3000)]

# ⭐ 강화: (점수 이름, 그림, 이름, 단계별 가격, 설명, 단계별 효과 글)
PERKS = [
    ('e1', '💎', '고급 족보', [5, 15, 40, 100, 220], '희귀 이상 족보 코인 +50%씩',
     ['+0%', '+50%', '+100%', '+150%', '+200%', '+250%']),
    ('e2', '🎰', '콤보', [5, 15, 40, 100, 220], '족보가 하나 더 걸릴 때마다 코인 +10%씩',
     ['+0%', '+10%', '+20%', '+30%', '+40%', '+50%']),
    ('e4', '⏩', '빨리 보기', [3, 6, 12, 25, 50], '족보를 하나씩 보여 주는 시간이 줄어요',
     ['0.5초', '0.4초', '0.3초', '0.2초', '0.1초', '바로']),
    ('e5', '🍀', '행운', [30, 110, 250], '안 좋은 숫자를 다시 굴려 줘요',
     ['없음', '꽝 안 나옴', '흔함만 있는 숫자도 안 나옴', '보통이면 한 번 더 굴림']),
]


def won(n):
    """1234 → 1,234 / 23000 → 2.3만 / 500000000 → 5억 / 1500000000000 → 1.5조"""
    if n < 10000:
        return '{:,}'.format(n)
    for unit, name in ((10 ** 12, '조'), (10 ** 8, '억'), (10 ** 4, '만')):
        if n >= unit:
            v = n / unit
            if v == int(v):
                return '{:,}'.format(int(v)) + name
            return ('%g' % (round(v, 1) if v < 100 else round(v))) + name


def hl(n):
    """코인 값 → (10억 단위, 나머지)"""
    return divmod(n, 10 ** 9)


def J(x):
    return json.dumps(x, ensure_ascii=False, separators=(', ', ': '))


def T(text, color=None, bold=None, **kw):
    d = {'text': text}
    if color:
        d['color'] = color
    if bold is not None:
        d['bold'] = bold
    d.update(kw)
    return d


def C(parts):
    """여러 조각을 한 줄로 — 앞 조각의 꾸밈(굵게·색)이 뒤 조각으로 번지지 않게 빈 글로 감싼다"""
    return {'text': '', 'extra': list(parts)}


def cmd_action(n):
    return {'type': 'minecraft:run_command', 'command': '/trigger jb.menu set %d' % n}


def button(label, n, tooltip=None, width=300):
    b = {'label': C(label) if isinstance(label, list) else label, 'width': width, 'action': cmd_action(n)}
    if tooltip is not None:
        b['tooltip'] = C(tooltip) if isinstance(tooltip, list) else (tooltip if isinstance(tooltip, dict) else T(tooltip, 'gray'))
    return b


def dialog(title, body=None, actions=None, columns=1, inputs=None, exit_n=99, exit_label='닫기', width=360):
    d = {'type': 'minecraft:multi_action', 'title': title}
    if body is not None:
        if not isinstance(body, list) or (body and 'type' not in body[0]):
            body = [{'type': 'minecraft:plain_message', 'width': width, 'contents': body}]
        d['body'] = body
    if inputs:
        d['inputs'] = inputs
    d['actions'] = actions
    d['columns'] = columns
    d['after_action'] = 'none'
    d['pause'] = False
    d['can_close_with_escape'] = True
    d['exit_action'] = {'label': {'text': exit_label}, 'width': 200, 'action': cmd_action(exit_n)}
    return d


class Pack:
    """함수 모음. F['roll/one'] = [명령 …]"""

    def __init__(self):
        self.F = {}
        self.extra = {}      # 그 밖의 파일 (경로 → 내용)

    def fn(self, name):
        return self.F.setdefault(name, [])

    def add(self, name, text):
        f = self.fn(name)
        for ln in text.strip('\n').split('\n'):
            ln = ln.strip()
            if ln:
                f.append(ln)
        return f


def snd(s, b, p):
    return 'function jb:snd/play {s:"minecraft:%s",b:%d,p:%s}' % (s, b, p)
