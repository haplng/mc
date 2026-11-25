# -*- coding: utf-8 -*-
"""🏆 도전과제 100개 (+ 뿌리). 어려울수록 코인을 많이 준다.

kind:
  stat  (점수 이름, 값)      그 점수가 값 이상
  cond  [조건 …]            execute 조건 전부
  hand  족보 key            그 족보를 찾음
  col   모음 이름            그 모음(tag)의 족보를 전부 찾음
  tier  등급                그 등급 족보를 전부 찾음
  manual                    다른 곳에서 직접 줌
"""
from common import NHANDS, UNLOCKS, unl_stage
from jokers import JOKERS

A = []


def D(key, parent, frame, icon, title, desc, reward, kind, arg=None, hidden=False):
    A.append(dict(key=key, parent=parent, frame=frame, hidden=hidden, icon=icon, title=title, desc=desc, reward=reward, kind=kind, arg=arg))


D('root', None, 'task', 'gold_block', '⚀ 숫자 굴리기', '숫자 속 족보를 찾아보세요', 1000, 'manual')
# ---- 굴리기 (10) ----
D('r1', 'root', 'task', 'paper', '첫 굴림', '숫자를 처음으로 굴려요', 1000, 'stat', ('rolls', 1))
D('r100', 'r1', 'task', 'iron_nugget', '굴리기 입문', '숫자를 100번 굴려요', 5000, 'stat', ('rolls', 100))
D('r1k', 'r100', 'task', 'gold_nugget', '멈출 수 없어', '숫자를 1,000번 굴려요', 30000, 'stat', ('rolls', 1000))
D('r10k', 'r1k', 'goal', 'gold_ingot', '손목이 아파요', '숫자를 1만 번 굴려요', 300000, 'stat', ('rolls', 10000))
D('r100k', 'r10k', 'goal', 'netherite_ingot', '기계와 하나 되기', '숫자를 10만 번 굴려요', 3000000, 'stat', ('rolls', 100000))
D('r1m', 'r100k', 'challenge', 'diamond_block', '백만 번의 굴림', '숫자를 100만 번 굴려요', 30000000, 'stat', ('rolls', 1000000))
D('r10m', 'r1m', 'challenge', 'netherite_block', '무한 굴레', '숫자를 1,000만 번 굴려요', 200000000, 'stat', ('rolls', 10000000))
D('auto_on', 'r100', 'task', 'repeater', '손 떼고 보기', '자동 굴리기를 사요', 5000, 'stat', ('u2', 1))
D('a10k', 'auto_on', 'goal', 'comparator', '잠수의 달인', '자동 굴리기로 숫자를 1만 번 굴려요', 300000, 'stat', ('arl', 10000))
D('a1m', 'a10k', 'challenge', 'observer', '쉬지 않는 기계', '자동 굴리기로 숫자를 100만 번 굴려요', 30000000, 'stat', ('arl', 1000000))
# ---- 도감 (9) ----
D('d10', 'root', 'task', 'book', '수집가', '족보를 10개 모아요', 3000, 'stat', ('found', 10))
D('d50', 'd10', 'task', 'writable_book', '열정적인 수집가', '족보를 50개 모아요', 30000, 'stat', ('found', 50))
D('d100', 'd50', 'goal', 'enchanted_book', '족보 박사', '족보를 100개 모아요', 300000, 'stat', ('found', 100))
D('d150', 'd100', 'goal', 'bookshelf', '걸어다니는 도감', '족보를 150개 모아요', 1000000, 'stat', ('found', 150))
D('d200', 'd150', 'goal', 'lectern', '족보 백과사전', '족보를 200개 모아요', 3000000, 'stat', ('found', 200))
D('d250', 'd200', 'goal', 'chiseled_bookshelf', '절반은 넘었다', '족보를 250개 모아요', 10000000, 'stat', ('found', 250))
D('d300', 'd250', 'challenge', 'enchanting_table', '전설의 수집가', '족보를 300개 모아요', 50000000, 'stat', ('found', 300))
D('d350', 'd300', 'challenge', 'end_portal_frame', '거의 다 왔어', '족보를 350개 모아요', 150000000, 'stat', ('found', 350))
D('d400', 'd350', 'challenge', 'beacon', '완벽주의자', '족보 %d개를 전부 모아요' % NHANDS, 500000000, 'stat', ('found', NHANDS))
# ---- 등급 (11) ----
D('t1', 'r1', 'task', 'lime_dye', '조금 특별한', '보통 이상 족보를 뽑아요', 1000, 'stat', ('mxt', 1))
D('t2', 't1', 'task', 'diamond', '레어!', '희귀 이상 족보를 뽑아요', 5000, 'stat', ('mxt', 2))
D('t3', 't2', 'goal', 'amethyst_shard', '에픽!!', '영웅 이상 족보를 뽑아요', 50000, 'stat', ('mxt', 3))
D('t4', 't3', 'goal', 'golden_apple', '전설의 시작', '전설 이상 족보를 뽑아요', 2000000, 'stat', ('mxt', 4))
D('t5', 't4', 'challenge', 'enchanted_golden_apple', '신화가 되다', '신화 족보를 뽑아요', 30000000, 'stat', ('mxt', 5))
D('tc0', 'd10', 'task', 'white_dye', '흔함 정복', '흔함 족보를 전부 모아요', 20000, 'tier', 0)
D('tc1', 'tc0', 'goal', 'lime_dye', '보통 정복', '보통 족보를 전부 모아요', 300000, 'tier', 1)
D('tc2', 'tc1', 'goal', 'light_blue_dye', '희귀 정복', '희귀 족보를 전부 모아요', 3000000, 'tier', 2)
D('tc3', 'tc2', 'challenge', 'amethyst_block', '영웅 정복', '영웅 족보를 전부 모아요', 20000000, 'tier', 3)
D('tc4', 'tc3', 'challenge', 'gold_block', '전설 정복', '전설 족보를 전부 모아요', 80000000, 'tier', 4)
D('tc5', 'tc4', 'challenge', 'dragon_egg', '신화 정복', '신화 족보를 전부 모아요', 500000000, 'tier', 5)
# ---- 코인 (7) ----
D('c10k', 'root', 'task', 'gold_nugget', '저금통', '코인을 1만⛃ 모아요', 2000, 'stat', ('cq', 10000))
D('c1m', 'c10k', 'task', 'gold_ingot', '백만장자', '코인을 100만⛃ 모아요', 100000, 'stat', ('cq', 1000000))
D('c100m', 'c1m', 'goal', 'gold_block', '억만장자', '코인을 1억⛃ 모아요', 10000000, 'stat', ('cq', 100000000))
D('c10b', 'c100m', 'goal', 'emerald_block', '큰손', '코인을 100억⛃ 모아요', 1000000000, 'stat', ('cb', 10))
D('c1t', 'c10b', 'challenge', 'diamond_block', '조만장자', '코인을 1조⛃ 모아요', 100000000000, 'stat', ('cb', 1000))
D('c100t', 'c1t', 'challenge', 'netherite_block', '숫자가 안 읽혀요', '코인을 100조⛃ 모아요', 10000000000000, 'stat', ('cb', 100000))
D('broke', 'c10k', 'task', 'bowl', '빈털터리', '무언가를 사고 코인이 10⛃도 안 남아요', 10000, 'cond',
  ['if score @s jb.coins matches ..9', 'if score @s jb.cb matches 0', 'if score @s jb.ubuy matches 1..'], hidden=True)
# ---- 한 방 (10) ----
D('o10', 'r1', 'task', 'wheat', '풍년', '숫자 하나로 족보를 10개 이상 받아요', 5000, 'stat', ('mxn', 10))
D('o15', 'o10', 'goal', 'hay_block', '대풍년', '숫자 하나로 족보를 15개 이상 받아요', 300000, 'stat', ('mxn', 15))
D('o20', 'o15', 'challenge', 'tnt', '천재지변', '숫자 하나로 족보를 20개 이상 받아요', 10000000, 'stat', ('mxn', 20))
D('oc10k', 'r1', 'task', 'emerald', '짭짤하다', '숫자 하나로 1만⛃ 이상 받아요', 5000, 'stat', ('mxr', 10000))
D('oc100k', 'oc10k', 'task', 'emerald_block', '대박', '숫자 하나로 10만⛃ 이상 받아요', 50000, 'stat', ('mxr', 100000))
D('oc1m', 'oc100k', 'goal', 'diamond', '초대박', '숫자 하나로 100만⛃ 이상 받아요', 500000, 'stat', ('mxr', 1000000))
D('oc10m', 'oc1m', 'goal', 'totem_of_undying', '인생 역전', '숫자 하나로 1,000만⛃ 이상 받아요', 5000000, 'stat', ('mxr', 10000000))
D('oc100m', 'oc10m', 'challenge', 'nether_star', '로또 1등', '숫자 하나로 1억⛃ 이상 받아요', 50000000, 'stat', ('mxr', 100000000))
D('nolucky', 'r1', 'task', 'dead_bush', '꽝!', '족보가 하나도 없는 숫자를 뽑아요', 1000, 'stat', ('zn', 1), hidden=True)
D('unlucky2', 'nolucky', 'goal', 'wither_rose', '불운의 아이콘', '꽝을 10번 뽑아요 (🍀 행운이 막아 줘도 쳐요)', 500000, 'stat', ('zn', 10), hidden=True)
# ---- 별 (11) ----
D('s2', 'd10', 'task', 'glowstone_dust', '첫 별', '족보 하나를 ★2로 만들어요', 2000, 'stat', ('smax', 2))
D('s3', 's2', 'task', 'glowstone', '별 셋', '족보 하나를 ★3으로 만들어요', 10000, 'stat', ('smax', 3))
D('s4', 's3', 'goal', 'sea_lantern', '별 넷', '족보 하나를 ★4로 만들어요', 100000, 'stat', ('smax', 4))
D('s5', 's4', 'goal', 'nether_star', '첫 ★5', '족보 하나를 ★5로 만들어요', 500000, 'stat', ('smax', 5))
D('s5x10', 's5', 'goal', 'end_rod', '별 부자', '★5 족보를 10개 만들어요', 3000000, 'stat', ('s5n', 10))
D('s5x50', 's5x10', 'challenge', 'end_crystal', '은하수', '★5 족보를 50개 만들어요', 30000000, 'stat', ('s5n', 50))
D('s5x100', 's5x50', 'challenge', 'dragon_head', '우주의 주인', '★5 족보를 100개 만들어요', 100000000, 'stat', ('s5n', 100))
D('st100', 's2', 'task', 'firework_star', '별 100개', '모든 족보의 별을 합쳐 100개', 100000, 'stat', ('stot', 100))
D('st500', 'st100', 'goal', 'firework_rocket', '별 500개', '모든 족보의 별을 합쳐 500개', 5000000, 'stat', ('stot', 500))
D('st1000', 'st500', 'challenge', 'conduit', '별 1,000개', '모든 족보의 별을 합쳐 1,000개', 50000000, 'stat', ('stot', 1000))
D('st1500', 'st1000', 'challenge', 'heart_of_the_sea', '별 1,500개', '모든 족보의 별을 합쳐 1,500개', 300000000, 'stat', ('stot', 1500))
# ---- 미션 (5) ----
D('m1', 'un_ms1', 'task', 'filled_map', '첫 미션', '미션을 처음 성공해요', 5000, 'stat', ('mdone', 1))
D('m10', 'm1', 'task', 'compass', '미션 10번', '미션을 10번 성공해요', 50000, 'stat', ('mdone', 10))
D('m50', 'm10', 'goal', 'recovery_compass', '미션 50번', '미션을 50번 성공해요', 500000, 'stat', ('mdone', 50))
D('m100', 'm50', 'goal', 'spyglass', '미션 100번', '미션을 100번 성공해요', 2000000, 'stat', ('mdone', 100))
D('m500', 'm100', 'challenge', 'lodestone', '미션 중독', '미션을 500번 성공해요', 20000000, 'stat', ('mdone', 500))
# ---- 코인 상점 (6) ----
D('u_first', 'root', 'task', 'emerald', '첫 투자', '코인 상점에서 처음으로 무언가를 사요', 1000, 'stat', ('ubuy', 1))
D('u1max', 'u_first', 'goal', 'lightning_rod', '번개 손', '⚡ 속도를 최대로', 3000000, 'stat', ('u1', 10))
D('u2max', 'u_first', 'goal', 'redstone_block', '24시간 영업', '⟳ 자동 굴리기를 최대로', 20000000, 'stat', ('u2', 10))
D('u3max', 'u_first', 'goal', 'chest', '한 번에 여덟 개', '✚ 여러 개를 최대로', 10000000, 'stat', ('u3', 7))
D('u4max', 'u_first', 'challenge', 'raw_gold_block', '황금 손', '⛃ 부스트를 최대로', 40000000, 'stat', ('u4', 10))
D('uall', 'u4max', 'challenge', 'nether_star', '풀업', '코인 상점 업그레이드 4개를 전부 최대로', 100000000, 'cond',
  ['if score @s jb.u1 matches 10..', 'if score @s jb.u2 matches 10..', 'if score @s jb.u3 matches 7..', 'if score @s jb.u4 matches 10..'])
# ---- 해금 (5) ----
D('un_ms1', 'u_first', 'task', 'map', '미션 시작', '🔓 쉬운 미션을 열어요', 5000, 'stat', ('unl', unl_stage('ms1')))
D('un_dice', 'un_ms1', 'task', 'white_concrete', '주사위를 손에', '🔓 주사위를 받아요', 10000, 'stat', ('unl', unl_stage('dice')))
D('un_t4', 'un_dice', 'goal', 'golden_helmet', '전설을 향해', '🔓 전설 족보를 열어요', 1000000, 'stat', ('unl', unl_stage('t4')))
D('un_t5', 'un_t4', 'challenge', 'netherite_helmet', '신화를 향해', '🔓 신화 족보를 열어요', 50000000, 'stat', ('unl', unl_stage('t5')))
D('un_all', 'un_t5', 'challenge', 'ender_chest', '다 열었다', '해금을 전부 마쳐요', 50000000, 'stat', ('unl', len(UNLOCKS)))
# ---- 강화 (3) ----
D('perk_first', 's2', 'task', 'amethyst_shard', '첫 강화', '⭐ 강화를 처음 해요', 2000, 'stat', ('pbuy', 1))
D('luck3', 'perk_first', 'goal', 'rabbit_foot', '행운의 여신', '🍀 행운을 3단계로', 10000000, 'stat', ('e5', 3))
D('perk_all', 'luck3', 'challenge', 'end_crystal', '완전체', '⭐ 강화 4개를 전부 최대로', 100000000, 'cond',
  ['if score @s jb.e1 matches 5..', 'if score @s jb.e2 matches 5..', 'if score @s jb.e4 matches 5..', 'if score @s jb.e5 matches 3..'])
# ---- 조커 (4) ----
D('j_first', 'un_dice', 'task', 'paper', '첫 조커', '🃏 조커를 처음 사요', 30000, 'stat', ('jown', 1))
D('j_5', 'j_first', 'goal', 'map', '조커 수집', '🃏 조커를 5장 모아요', 1000000, 'stat', ('jown', 5))
D('j_4eq', 'j_5', 'goal', 'item_frame', '풀 덱', '🃏 조커를 4장 끼고 있어요', 20000000, 'stat', ('jeq', 4))
D('j_all', 'j_4eq', 'challenge', 'glow_item_frame', '조커 마스터', '🃏 조커 %d장을 전부 모아요' % len(JOKERS), 300000000, 'stat', ('jown', len(JOKERS)))
# ---- 모음집 (13) ----
D('col_region', 't1', 'goal', 'minecart', '전국 팔도 유람', '지역번호 족보(서울 사람 포함)를 전부 모아요', 500000, 'col', 'region')
D('col_phone', 't1', 'task', 'bell', '전화번호부', '전화번호 족보를 전부 모아요', 300000, 'col', 'phone')
D('col_calc', 't2', 'challenge', 'redstone_lamp', '계산기 박사', '계산기 뒤집기 족보를 전부 모아요', 30000000, 'col', 'calc')
D('col_mc', 't2', 'challenge', 'grass_block', '마크 덕후 인증', '마인크래프트 족보를 전부 모아요', 100000000, 'col', 'mc')
D('col_day', 't2', 'goal', 'clock', '달력 완성', '날짜 족보를 전부 모아요', 3000000, 'col', 'day')
D('col_time', 't2', 'goal', 'daylight_detector', '하루 일과', '시간 족보를 전부 모아요', 5000000, 'col', 'time')
D('col_gugu', 't2', 'challenge', 'bookshelf', '구구단 마스터', '구구단 2단부터 9단까지 전부 모아요', 200000000, 'col', 'gugu')
D('col_idiom', 't2', 'challenge', 'writable_book', '사자성어 박사', '사자성어·속담 족보를 전부 모아요', 10000000, 'col', 'idiom')
D('col_beeper', 't2', 'challenge', 'note_block', '삐삐 세대', '삐삐 암호 족보를 전부 모아요', 100000000, 'col', 'beeper')
D('col_money', 't1', 'challenge', 'gold_ingot', '돼지 저금통 가득', '동전·지폐 족보를 전부 모아요', 50000000, 'col', 'money')
D('col_rank', 't1', 'challenge', 'golden_helmet', '1등 정복', '99…로 시작하는 1등 족보 5개를 전부 모아요', 30000000, 'col', 'rank')
D('col_sale', 't1', 'challenge', 'iron_nugget', '세일 중독', '00…으로 시작하는 세일 족보 5개를 전부 모아요', 30000000, 'col', 'sale')
D('col_wheel', 't1', 'challenge', 'minecart', '바퀴 수집가', '00…으로 끝나는 바퀴 족보 6개를 전부 모아요', 200000000, 'col', 'wheel')
# ---- 명물 족보 (5) + 그 밖 (1) ----
D('f_octo', 't3', 'challenge', 'ink_sac', '문어 다리', None, 30000000000, 'hand', 'run8')
D('f_oct', 't3', 'challenge', 'jukebox', '한 옥타브', None, 30000000000, 'hand', 'octu')
D('f_pal', 't3', 'goal', 'glass_pane', '다 큰 도라지라도 큰다', None, 1000000, 'hand', 'pal9')
D('f_robot', 't3', 'challenge', 'redstone_torch', '삐빅, 로봇입니다', None, 30000000000, 'hand', 'lo1')
D('f_mc', 't3', 'challenge', 'crafting_table', '마인크래프트 탄생', None, 30000000000, 'hand', 'y2009517')
D('mute', 'root', 'task', 'note_block', '쉿!', '소리를 0으로 꺼요', 1000, 'stat', ('muted', 1), hidden=True)
assert len(A) == 101, len(A)
assert len({a['key'] for a in A}) == len(A)


# ----------------------------------------------------------------------
# 보상(코인): 그 도전과제를 깰 즈음의 '몇 분어치 수입' 이 되게 맞췄다 (tools/advcal.py 로 잰 값을 다듬음).
# ----------------------------------------------------------------------
M, E, J_ = 10 ** 4, 10 ** 8, 10 ** 12
REWARDS = {
    'root': 1000, 'r1': 500, 'r100': 10000, 'r1k': 300000, 'r10k': 30000000, 'r100k': 3000000000,
    'r1m': 100000000000, 'r10m': 300000000000, 'auto_on': 1000, 'a10k': 70000000, 'a1m': 150000000000, 'd10': 1000,
    'd50': 2000, 'd100': 20000, 'd150': 50000, 'd200': 700000, 'd250': 10000000, 'd300': 300000000,
    'd350': 50000000000, 'd400': 300000000000, 't1': 500, 't2': 1000, 't3': 20000, 't4': 15000000,
    't5': 7000000000, 'tc0': 10000, 'tc1': 200000, 'tc2': 30000000, 'tc3': 500000000, 'tc4': 70000000000,
    'tc5': 300000000000, 'c10k': 3000, 'c1m': 200000, 'c100m': 15000000, 'c10b': 2000000000, 'c1t': 70000000000,
    'c100t': 3000000000000, 'broke': 3000, 'o10': 1000, 'o15': 70000, 'o20': 70000000, 'oc10k': 20000,
    'oc100k': 150000, 'oc1m': 1500000, 'oc10m': 30000000, 'oc100m': 3000000000, 'nolucky': 15000, 'unlucky2': 7000000,
    's2': 20000, 's3': 70000, 's4': 1500000, 's5': 30000000, 's5x10': 700000000, 's5x50': 3000000000,
    's5x100': 4500000000, 'st100': 20000, 'st500': 30000000, 'st1000': 1500000000, 'st1500': 100000000000, 'm1': 15000,
    'm10': 1000000, 'm50': 15000000, 'm100': 70000000, 'm500': 2000000000, 'u_first': 1000, 'u1max': 7000000,
    'u2max': 15000000, 'u3max': 15000000, 'u4max': 15000000, 'uall': 30000000, 'un_ms1': 3000, 'un_dice': 15000,
    'un_t4': 15000000, 'un_t5': 7000000000, 'un_all': 10000000000, 'perk_first': 20000, 'luck3': 7000000000, 'perk_all': 10000000000,
    'j_first': 50000, 'j_5': 1000000, 'j_4eq': 3000000000, 'j_all': 70000000000, 'col_region': 50000, 'col_phone': 2000000,
    'col_calc': 150000000000, 'col_mc': 150000000000, 'col_day': 7000000, 'col_time': 2000000000, 'col_gugu': 150000000000, 'col_idiom': 7000000000,
    'col_beeper': 150000000000, 'col_money': 100000000000, 'col_rank': 50000000000, 'col_sale': 50000000000, 'col_wheel': 150000000000, 'f_octo': 100000000000,
    'f_oct': 100000000000, 'f_pal': 1000000, 'f_robot': 70000000000, 'f_mc': 100000000000, 'mute': 1000,
}
assert set(REWARDS) == set(a['key'] for a in A), set(REWARDS) ^ set(a['key'] for a in A)
for a in A:
    a['reward'] = REWARDS[a['key']]
