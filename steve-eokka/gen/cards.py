"""The 24 cards: each has a normal hit, a sweet-spot crit and a 'Steve learned it' blocked variant."""
from core import *
import stages as ST

EVENTS = []
class Ev:
    def __init__(s, name, st_=None):
        s.id = len(EVENTS) + 1; s.name = name; s.steps = {}; s.raw = []; s.st = st_; EVENTS.append(s)
    def at(s, tt, *cmds):
        s.steps.setdefault(tt, []).extend(flat(cmds)); return s
    def rng(s, a, b, *cmds):
        for c in flat(cmds): s.raw.append('execute if score #it ek matches %d..%d run %s' % (a, b, c))
        return s
    def every(s, a, b, p, *cmds):
        for tt in range(a, b + 1, p): s.at(tt, *cmds)
        return s
    def end(s, tt, mode):
        start = [sset('intr', s.id), sset('it', 0)]
        if s.st: start.append(status(s.st))
        start += s.steps.get(0, [])
        P.fn(f'ev/{s.name}/start', start)
        tick = []
        for k in sorted(s.steps):
            if k == 0: continue
            cmds = s.steps[k]
            if len(cmds) == 1: tick.append(iff('it', k, cmds[0]))
            else:
                P.fn(f'ev/{s.name}/t{k}', cmds); tick.append(iff('it', k, f'function ek:ev/{s.name}/t{k}'))
        tick += s.raw
        tick.append(iff('it', tt, 'function ek:ev/end_' + mode))
        P.fn(f'ev/{s.name}/tick', tick)
        return s

def finish_events():
    P.fn('ev/tick', sadd('it', 1), [iff('intr', e.id, f'return run function ek:ev/{e.name}/tick') for e in EVENTS])

class Card:
    def __init__(s, id, name, icon, color, cost, desc, sweet_desc, sweet, learn, unlock=None, usable=None):
        s.id = id; s.name = name; s.icon = icon; s.color = color; s.cost = cost; s.desc = desc; s.sweet_desc = sweet_desc
        s.sweet = sweet; s.learn = learn; s.unlock = unlock; s.usable = usable or {}; s.aim = None

MOB = 'NoAI:1b,PersistenceRequired:1b,Invulnerable:1b,Silent:1b'
HAT = ',equipment:{head:{id:"minecraft:stone_button",count:1}}'
def mob(kind, tag, rel, extra='', chase=True):
    tags = '"ek.mob","%s"' % tag + (',"ek.chase"' if chase else '')
    return 'execute as %s at @s rotated ~ 0 positioned %s run summon minecraft:%s ~ ~ ~ {Tags:[%s],%s%s}' % (STEVE, rel, kind, tags, MOB, extra)
AIM = '@e[tag=ek.aim,limit=1]'
def mob_aim(kind, tag, dx=0, dz=0, extra='', chase=True):
    # the mob appears where the player's throw landed; aimed mobs run (ek.fast) so they reach Steve inside the scripted chase time
    tags = '"ek.mob","%s"' % tag + (',"ek.chase","ek.fast"' if chase else '')
    return 'execute at %s positioned ~%s ~ ~%s run summon minecraft:%s ~ ~ ~ {Tags:[%s],%s%s}' % (AIM, dx, dz, kind, tags, MOB, extra)
def mob_at(kind, tag, x, y, z, extra=''):
    return 'summon minecraft:%s %s %s %s {Tags:["ek.mob","%s"],%s%s}' % (kind, x, y, z, tag, MOB, extra)
def fx_item(tag, item, x, y, z, scale):
    return 'summon item_display %s %s %s {Tags:["ek.mob","%s"],billboard:"center",teleport_duration:1,item:{id:"minecraft:%s",count:1},%s}' % (x, y, z, tag, item, DISPLAY_T % (scale, scale, scale))
CHASE = 'function ek:fx/chase'
def vanish(tag): return 'execute as @e[tag=%s] run function ek:fx/vanish' % tag
def sface(tag): return S('tp @s ~ ~ ~ facing entity @e[tag=%s,limit=1] feet' % tag)
def mface(tag): return 'execute as @e[tag=%s] at @s run tp @s ~ ~ ~ facing entity %s eyes' % (tag, STEVE)
def fire(on): return 'data merge entity %s {HasVisualFire:%db}' % (STEVE, 1 if on else 0)
SPIN = S('tp @s ~ ~ ~ ~40 ~')
EVT = '@e[tag=ek.evt,limit=1]'
def evt(): return at_s('summon marker ~ ~ ~ {Tags:["ek.evt"]}')
def bd(hit, crit): return [sset('dmg', max(1, hit // 2)), iff('sweet', 1, sset('dmg', max(1, crit // 2))), 'function ek:game/dmg']
LAVAFX = [part('lava', 1, 0.3, 0, 6), part('large_smoke', 1.5, 0.2, 0.02, 5)]
SWEEP = snd('entity.player.attack.sweep', 1, 0.6)

def lapse(e, t0, days):
    e.at(t0, at_s('particle minecraft:poof ~ ~1 ~ 0.3 0.6 0.3 0.05 30 force'), f'execute as {STEVE} run function ek:fx/vanish', sset('steve', 0),
         'kill @e[tag=ek.bub]', sset('bubt', 0), 'title @a times 5 40 10',
         'title @a subtitle ' + comp(t('%d일 뒤' % days, 'gray')), 'title @a title ' + comp(t(' ')))
    e.rng(t0 + 1, t0 + 50, 'time add 480')
    e.at(t0 + 52, 'time set 6000', sadd('day', days))

def luck(cid, var, H, C, crit_n, hit_n, crit_pop, crit_lines, hit_line, block_pop, block_lines):
    Ev(cid + '_crit').at(0, sadd(var, crit_n), popup(crit_pop, 'red'), snd('block.note_block.bass', 0.5)).at(10, say(crit_lines), dmg(C)).end(30, 'resume')
    Ev(cid + '_hit').at(0, sadd(var, hit_n), popup('불길한 예감...', 'gray'), snd('block.note_block.bass', 0.7, 0.6)).at(10, say1(hit_line), dmg(H)).end(30, 'resume')
    Ev(cid + '_block').at(0, sset(var, 0), popup(block_pop, 'aqua')).at(8, say(block_lines), bd(H, C)).end(30, 'cont')

def build(stages):
    cards = []

    # ---------------------------------------------------------------- creeper
    H, C = 7, 13
    CR = ',ExplosionRadius:0b,Fuse:30s'
    ignite = ['data merge entity @e[tag=ek.creep,limit=1] {ignited:1b}', snd('entity.creeper.primed')]
    boom = ['execute at @e[tag=ek.creep,limit=1] run function ek:fx/boom', vanish('ek.creep')]
    Ev('creeper_crit', '등 뒤에 크리퍼').at(0, mob_aim('creeper', 'ek.creep', 0, 0, CR)).rng(1, 38, CHASE).at(40, ignite) \
        .at(66, boom, die('creeper', '크리퍼에게 폭파당했습니다'), dmg(C)) \
        .at(82, say(['아니 뒤에 크리퍼가 왜 있냐고', '소리도 안 났는데?', '아 깜짝이야 진짜'], low=['하... 또 크리퍼야', '이 게임 나한테 왜 이래'])).end(110, 'death')
    Ev('creeper_hit', '등 뒤에 크리퍼').at(0, mob_aim('creeper', 'ek.creep', 0, 0, CR)).rng(1, 28, CHASE).at(22, sface('ek.creep'), say1('어 크리퍼?')) \
        .at(30, ignite).at(56, boom, hurt(), dmg(H)).at(62, say(['아 반피 됐네', '크리퍼 진짜 싫다', '터지기 전에 봤는데 늦었어'])).end(85, 'resume')
    Ev('creeper_block', '등 뒤에 크리퍼').at(0, mob_aim('creeper', 'ek.creep', 0, 0, CR)).rng(1, 18, CHASE) \
        .at(12, sface('ek.creep'), say(['뒤 한 번 봤지롱', '크리퍼 뒤치기는 이제 안 통함'])).at(24, swing(), SWEEP) \
        .at(34, swing(), SWEEP, 'kill @e[tag=ek.creep]', snd('entity.creeper.death'), bd(H, C)).end(60, 'cont')
    cards.append(Card('creeper', '등 뒤 크리퍼', 'creeper_head', 'green', 30, '바라보는 곳에 크리퍼를 떨어뜨린다', '뭔가에 열중하고 있을 때', [['busy']],
                      '크리퍼한테 두 번은 안 당한다. 이제 뒤 보면서 함'))

    # ---------------------------------------------------------------- night
    H, C = 6, 11
    dusk = lambda e: e.rng(1, 20, 'time add 400')
    dig = [at_s('setblock ~ ~-1 ~ minecraft:air destroy')]
    up = [at_s('setblock ~ ~ ~ minecraft:dirt'), snd('block.gravel.break', 1, 0.5)]
    e = Ev('night_crit', '갑자기 밤이 됐다'); dusk(e)
    e.at(8, say(['어? 벌써 밤이야?', '해가 왜 이렇게 빨리 져'])) \
        .at(24, mob('zombie', 'ek.zom', '^3 ^ ^-5', HAT), mob('zombie', 'ek.zom', '^-4 ^ ^-4', HAT), snd('entity.zombie.ambient')) \
        .rng(25, 158, CHASE).at(44, say1('일단 땅 파고 숨는다')).at(50, dig).at(55, dig).at(60, dig) \
        .at(66, at_s('setblock ~ ~2 ~ minecraft:dirt'), snd('block.gravel.break')) \
        .at(100, say(['...', '첫날부터 땅굴행이네', '위에서 좀비 소리 난다']), dmg(C)).every(90, 150, 30, snd('entity.zombie.ambient', 0.8, 0.6)) \
        .at(160, 'execute at @e[tag=ek.zom] run particle minecraft:flame ~ ~1 ~ 0.2 0.5 0.2 0.02 20 force', vanish('ek.zom'), 'time set 6000', sadd('day', 1)) \
        .at(170, at_s('setblock ~ ~2 ~ minecraft:air')).at(174, up).at(178, up).at(182, up).at(186, say1('아침이다. 하루 날렸네')).end(195, 'resume')
    e = Ev('night_hit', '갑자기 밤이 됐다'); dusk(e)
    e.at(8, say(['밤이네. 그냥 한다', '어두워졌네'])).at(22, mob('zombie', 'ek.zom', '^ ^ ^-6', HAT), snd('entity.zombie.ambient')).rng(23, 60, CHASE) \
        .at(52, sface('ek.zom')).at(58, hurt(), dmg(H)).every(60, 72, 6, swing(), SWEEP) \
        .at(74, 'kill @e[tag=ek.zom]', snd('entity.zombie.death')).at(84, 'time set 6000', say1('금방 아침이네')).end(92, 'resume')
    e = Ev('night_block', '갑자기 밤이 됐다'); dusk(e)
    e.at(8, say(['침대 들고 다닌다니까', '밤? 자면 되지'])).at(24, pose('sleeping'), popup('Zzz', 'gray')) \
        .at(64, 'time set 6000', pose('standing'), bd(H, C)).end(75, 'cont')
    cards.append(Card('night', '밤 일찍 오기', 'clock', 'blue', 25, '해를 떨어뜨려서 밤으로 만든다', '침대를 만들기 직전일 때 / 포탈을 짓고 있을 때',
                      [['nobed'], ['frame']], '이제 침대 들고 다닌다', usable={1: (None, 'bed')}))

    # ---------------------------------------------------------------- arrow
    H, C = 6, 12
    SK = mob_aim('skeleton', 'ek.skel', 0, 0, ',equipment:{mainhand:{id:"minecraft:bow",count:1},head:{id:"minecraft:stone_button",count:1}}', chase=False)
    def shot(e):
        return e.at(0, SK, mface('ek.skel'), snd('entity.skeleton.ambient')).at(14, snd('entity.arrow.shoot'), 'execute at @e[tag=ek.skel,limit=1] run ' + fx_item('ek.arrowfx', 'arrow', '~', '~1.5', '~', 1.5)) \
            .rng(15, 27, 'execute as @e[tag=ek.arrowfx] at @s facing entity %s eyes run tp @s ^ ^ ^2.2' % STEVE)
    shot(Ev('arrow_crit', '어디선가 화살이')).at(28, vanish('ek.arrowfx'), snd('entity.arrow.hit_player'), hurt(), popup('명중', 'red')) \
        .rng(29, 44, S('tp @s ~-0.25 ~ ~0.3')).at(46, die('fall', '스켈레톤에게서 도망치려다 떨어졌습니다'), dmg(C)) \
        .at(60, say(['언덕 위에서 화살 맞고 떨어지네', '스켈레톤 에임 뭐야', '높은 데 올라가면 꼭 이래'])).at(70, vanish('ek.skel')).end(95, 'death')
    shot(Ev('arrow_hit', '어디선가 화살이')).at(28, vanish('ek.arrowfx'), snd('entity.arrow.hit_player'), hurt(), dmg(H)) \
        .at(34, say(['아 스켈레톤 어디서 쏘는 거야', '화살 아파'])).at(46, vanish('ek.skel')).end(60, 'resume')
    shot(Ev('arrow_block', '어디선가 화살이')).at(28, vanish('ek.arrowfx'), snd('item.shield.block'), popup('방패 막기', 'aqua')) \
        .at(32, say(['방패 들었지롱', '화살은 방패로']), bd(H, C)).at(44, vanish('ek.skel')).end(55, 'cont')
    cards.append(Card('arrow', '스켈레톤 저격', 'arrow', 'white', 25, '바라보는 곳에 스켈레톤이 나타나 화살을 쏜다', '높은 곳에 올라가 있을 때', [['high']], '방패 만들어서 들고 다닌다'))

    # ---------------------------------------------------------------- pickaxe
    H, C = 4, 8
    brk = [snd('entity.item.break'), hold('air'), part('poof', 1.2, 0.2, 0.02, 10)]
    Ev('pick_crit', '곡괭이가 부서졌다').at(0, brk, popup('곡괭이가 부서졌다', 'red')) \
        .at(12, say(['아니 지금 부서진다고?', '내구도 확인 안 했네...', '캐던 거 마저 캐야 되는데']), sset('dmg', C), iff('f_obs', 1, sadd('dmg', 4)), 'function ek:game/dmg') \
        .at(14, status('곡괭이 다시 만드는 중')).every(20, 80, 10, swing(), snd('block.wood.hit', 1.4, 0.5)).at(84, popup('곡괭이 다시 제작', 'aqua')).end(90, 'resume')
    Ev('pick_hit', '곡괭이가 부서졌다').at(0, brk, popup('곡괭이가 부서졌다', 'red')).at(12, say1('...안 쓰고 있었는데 왜 부서져'), dmg(H)).end(45, 'resume')
    Ev('pick_block', '곡괭이가 부서졌다').at(0, snd('entity.item.break'), popup('여분 곡괭이로 교체', 'aqua')) \
        .at(8, say(['여분 챙겨 다니지', '곡괭이 두 개 들고 다님']), bd(H, C)).end(35, 'cont')
    cards.append(Card('pick', '곡괭이 부서짐', 'wooden_pickaxe', 'gold', 20, '들고 있는 곡괭이를 부순다', '한창 캐고 있을 때 (흑요석이면 더 아픔)', [['mine']],
                      '곡괭이는 여분까지 챙긴다'))

    # ---------------------------------------------------------------- thunder
    H, C = 6, 12
    nofire = 'fill -14 58 -14 14 86 14 minecraft:air replace minecraft:fire'
    Ev('thunder_crit', '마른하늘에 날벼락').at(0, 'weather thunder').at(20, at_s('summon minecraft:lightning_bolt ~ ~ ~')) \
        .at(22, die('lightning', '벼락에 맞았습니다'), dmg(C)).at(30, nofire) \
        .at(40, say(['맑은 날에 벼락을 맞네', '이게 확률이 몇이야', '날씨가 왜 갑자기'])).at(70, 'weather clear').end(95, 'death')
    Ev('thunder_hit', '마른하늘에 날벼락').at(0, 'weather thunder').at(20, 'execute at %s run summon minecraft:lightning_bolt ~ ~ ~' % AIM) \
        .at(22, hurt(), dmg(H), say(['으악 벼락', '바로 옆에 떨어졌어'])).at(30, nofire).at(60, 'weather clear').end(70, 'resume')
    Ev('thunder_block', '마른하늘에 날벼락').at(0, 'weather thunder', S('setblock ^ ^ ^3 minecraft:lightning_rod keep')) \
        .at(20, S('summon minecraft:lightning_bolt ^ ^ ^3')).at(24, say(['피뢰침 세워놨지', '벼락은 저기로']), bd(H, C)).at(30, nofire).at(55, 'weather clear').end(65, 'cont')
    cards.append(Card('thunder', '마른하늘에 날벼락', 'lightning_rod', 'yellow', 35, '바라보는 곳에 벼락을 떨어뜨린다', '뭔가에 열중하고 있을 때', [['busy']],
                      '피뢰침 들고 다닌다', unlock='runs1'))

    # ---------------------------------------------------------------- gravel
    H, C = 6, 11
    FALL = 'summon minecraft:falling_block ~ ~%d ~ {BlockState:"minecraft:gravel",Time:1,DropItem:0b}'
    bury = [evt(), sset('snap', 0), at_s(FALL % 5), at_s(FALL % 7), snd('block.gravel.break', 1, 0.5)]
    Ev('gravel_crit', '머리 위에서 자갈이').at(0, bury).at(14, popup('자갈에 묻혔다', 'red'), say(['으악 자갈', '숨 막혀'])).every(20, 50, 10, hurt()) \
        .at(58, die('suffocate', '벽 속에서 질식했습니다'), dmg(C)) \
        .at(64, 'execute at %s run fill ~ ~ ~ ~ ~4 ~ minecraft:air replace minecraft:gravel' % EVT) \
        .at(72, say(['머리 위 자갈 확인을 안 했네', '자갈이 제일 싫어', '캐다가 묻히는 게 말이 되냐'])).end(95, 'death')
    Ev('gravel_hit', '머리 위에서 자갈이').at(0, bury).at(14, popup('자갈에 묻혔다', 'red'), say1('아 자갈')).at(22, hurt()).every(26, 38, 6, swing()) \
        .at(40, 'execute at %s run fill ~ ~ ~ ~ ~4 ~ minecraft:air replace minecraft:gravel destroy' % EVT, dmg(H), sset('snap', 1)) \
        .at(46, say1('자갈은 위에서부터 캐야지...')).end(60, 'resume')
    Ev('gravel_block', '머리 위에서 자갈이').at(0, snd('block.gravel.break', 1, 0.5),
                                         at_s('particle minecraft:block{block_state:"minecraft:gravel"} ~ ~2.5 ~ 0.3 0.3 0.3 0 15 force'), popup('자갈을 피했다', 'aqua')) \
        .at(8, say(['소리 듣고 바로 피함', '자갈 밑에선 안 캔다니까']), bd(H, C)).end(35, 'cont')
    cards.append(Card('gravel', '머리 위 자갈', 'gravel', 'gray', 25, '바라보는 곳에 자갈을 쏟아붓는다', '한창 캐고 있을 때', [['mine']], '자갈 밑에선 절대 안 캔다'))

    # ---------------------------------------------------------------- zombies
    H, C = 6, 12
    Ev('zombies_crit', '어둠 속 좀비 떼').at(0, mob_aim('zombie', 'ek.zom', 0, 0, HAT), mob_aim('zombie', 'ek.zom', 1.5, 0.5, HAT), mob_aim('zombie', 'ek.zom', -1.5, -0.5, HAT), snd('entity.zombie.ambient')) \
        .rng(1, 70, CHASE).at(18, say1('좀비 소리?')).every(36, 66, 10, hurt()).at(72, die('zombie', '좀비에게 살해당했습니다'), dmg(C)).at(80, vanish('ek.zom')) \
        .at(84, say(['어두운 데서 좀비 셋은 반칙이지', '횃불 좀 깔 걸', '뒤에서 때리는 건 좀'])).end(105, 'death')
    Ev('zombies_hit', '어둠 속 좀비 떼').at(0, mob_aim('zombie', 'ek.zom', 0, 0, HAT), mob_aim('zombie', 'ek.zom', 1.5, 0.5, HAT), snd('entity.zombie.ambient')) \
        .rng(1, 50, CHASE).at(30, sface('ek.zom')).at(40, hurt(), dmg(H)).every(44, 62, 6, swing(), SWEEP) \
        .at(56, 'kill @e[tag=ek.zom,limit=1]').at(66, 'kill @e[tag=ek.zom]', snd('entity.zombie.death')).at(72, say1('좀비 정도야 뭐')).end(85, 'resume')
    Ev('zombies_block', '어둠 속 좀비 떼').at(0, at_s('setblock ~ ~ ~ minecraft:torch keep'), snd('block.wood.place'), popup('횃불 도배', 'aqua')) \
        .at(8, say(['횃불 깔아서 스폰 안 됨', '밝으면 안 나오지']), bd(H, C)).end(35, 'cont')
    cards.append(Card('zombies', '어둠 속 좀비 떼', 'zombie_head', 'dark_green', 35, '바라보는 곳에 좀비 떼를 풀어놓는다', '어두운 곳에서 뭔가에 열중할 때', [['dark', 'busy']],
                      '가는 데마다 횃불 도배한다'))

    # ---------------------------------------------------------------- lost
    H, C = 5, 8
    wander = S('tp @s ^ ^ ^0.12 ~9 ~')
    Ev('lost_crit', '길을 잃음').at(0, say(['어... 여기 아까 왔던 데 아닌가', '길을 잃었다']), popup('?', 'yellow')).rng(4, 160, wander).every(40, 160, 40, popup('?', 'yellow')) \
        .at(90, say1('나가는 길이 어디야'), dmg(C)).end(165, 'resume')
    Ev('lost_hit', '길을 잃음').at(0, popup('?', 'yellow')).rng(4, 80, wander).at(40, dmg(H), say1('잠깐 헷갈렸네')).end(85, 'resume')
    Ev('lost_block', '길을 잃음').at(0, popup('표시해 둔 길', 'aqua')).at(6, say(['횃불 오른쪽 법칙. 안 헷갈림', '지나온 길에 표시해 뒀지']), bd(H, C)).end(30, 'cont')
    cards.append(Card('lost', '길 잃기', 'compass', 'light_purple', 20, '방향 감각을 뒤섞어서 헤매게 만든다', '복잡한 통로를 지나가고 있을 때', [['maze']],
                      '횃불은 오른쪽에만 꽂는다', usable={6: ('down', 'frames')}))

    # ---------------------------------------------------------------- lava
    H, C = 7, 15
    Ev('lava_crit', '용암이 터져 나왔다').at(0, evt(), snd('block.lava.pop', 0.8), popup('...용암 소리?', 'gold')) \
        .at(14, at_s('setblock ~ ~ ~ minecraft:lava'), fire(1), snd('entity.player.hurt_on_fire'), snd('block.lava.extinguish', 0.8), popup('캔 게 전부 타고 있다', 'red')) \
        .rng(15, 54, SPIN).every(18, 50, 8, LAVAFX).at(30, say1('아아아 다이아')).at(56, die('lava', '용암에 빠졌습니다'), dmg(C)) \
        .at(60, 'execute at %s run setblock ~ ~ ~ minecraft:air' % EVT) \
        .at(72, say(['내 다이아...', '다이아 캐다 용암은 국룰이긴 한데', '키보드 던질 뻔'], low=['아니 진짜 접을까', '다 탔네 하하', '이 동굴 다신 안 온다'])).end(100, 'major')
    Ev('lava_hit', '용암이 터져 나왔다').at(0, evt(), snd('block.lava.pop', 0.8), popup('...용암 소리?', 'gold')) \
        .at(14, at_s('setblock ~ ~ ~ minecraft:lava'), fire(1), snd('entity.player.hurt_on_fire')).rng(15, 34, SPIN) \
        .at(36, 'execute at %s run setblock ~ ~ ~ minecraft:air' % EVT, fire(0), hurt(), dmg(H)).at(42, say(['아 뜨거 뜨거', '용암이 왜 여기서 나와'])).end(60, 'resume')
    Ev('lava_block', '용암이 터져 나왔다').at(0, snd('block.lava.pop', 0.8), popup('...용암 소리?', 'gold')) \
        .at(12, snd('item.bucket.empty'), S('setblock ^ ^ ^1 minecraft:obsidian keep'), popup('물양동이', 'aqua')) \
        .at(18, say(['물양동이 들고 다니지', '용암? 흑요석 만들면 그만']), bd(H, C)).end(40, 'cont')
    cards.append(Card('lava', '다이아 밑 용암', 'lava_bucket', 'red', 40, '바라보는 곳에서 용암이 터져 나온다', '다이아나 흑요석을 캐고 있을 때', [['lavaspot']],
                      '물양동이 없이는 안 캔다'))

    # ---------------------------------------------------------------- floor
    H, C = 6, 15
    Ev('floor_crit', '발밑이 꺼졌다').at(0, snd('block.stone.break'), popup('발밑이 꺼졌다', 'red'),
                                    iff('stage', 6, f'tp {STEVE} 0.5 60 -8.5'), unl('stage', 6, at_s('fill ~ ~-1 ~ ~ ~-2 ~ minecraft:lava'))) \
        .at(6, fire(1), snd('entity.player.hurt_on_fire')).rng(7, 40, SPIN).every(10, 40, 8, LAVAFX).at(42, die('lava', '용암에 빠졌습니다'), dmg(C)) \
        .at(56, say(['발밑이 왜 꺼져???', '방금 그거 뭐였어', '아이템 다 탔다'])).end(85, 'major')
    Ev('floor_hit', '발밑이 꺼졌다').at(0, snd('block.stone.break'), popup('발밑이 꺼졌다', 'red'), at_s('setblock ~ ~-1 ~ minecraft:air destroy')) \
        .at(10, hurt(), dmg(H), say(['으악', '함정 구덩이?'])).at(24, at_s('setblock ~ ~ ~ minecraft:cobblestone'), snd('block.stone.place')).end(40, 'resume')
    Ev('floor_block', '발밑이 꺼졌다').at(0, pose('crouching'), snd('block.stone.place'), popup('블록 클러치', 'aqua')) \
        .at(10, say(['발밑 블록은 항상 깔고 다님', '클러치 연습했지']), bd(H, C)).at(20, pose('standing')).end(35, 'cont')
    cards.append(Card('floor', '발밑 꺼짐', 'iron_trapdoor', 'dark_red', 40, '바라보는 곳의 바닥을 꺼뜨린다', '용암 위 좁은 길에 있을 때 / 포탈에 눈을 끼울 때',
                      [['bridge'], ['frame']], '발밑 블록은 내가 깔고 다닌다', unlock='win1'))

    # ---------------------------------------------------------------- flint / barter / rods (luck cards)
    luck('flint', 'flint', 3, 8, 4, 2, '부싯돌 확률 급락', ['아니 자갈을 몇 개를 캐는데', '부싯돌 확률 10%라며...', '삽이라도 가져올 걸'],
         '왠지 오늘 부싯돌 안 나올 것 같은 느낌', '여분 부싯돌', ['상자에 부싯돌 넣어둔 게 있지', '부싯돌은 미리 챙겨 둠'])
    cards.append(Card('flint', '부싯돌 꽝', 'flint', 'dark_gray', 15, '자갈에서 부싯돌이 안 나오게 한다', '자갈을 캐고 있을 때', [['gravel']],
                      '부싯돌은 여분을 챙겨 둔다', usable={4: (None, 'gravel')}))
    luck('barter', 'bmiss', 3, 8, 3, 2, '교환 꽝 확률 폭등', ['금괴 여덟 개째 자갈만 주네', '이 돼지들이 담합했나', '진주 한 번만 줘라 제발'],
         '왠지 오늘 진주 안 나올 것 같은 느낌', '금 블록 통째로', ['금 블록째로 가져옴. 꽝 나와도 됨', '금은 넉넉하게'])
    cards.append(Card('barter', '교환 꽝', 'gold_ingot', 'gold', 15, '피글린이 쓸모없는 것만 주게 한다', '피글린이랑 교환하고 있을 때', [['barter']],
                      '금을 블록째로 들고 온다', usable={5: (None, 'barter')}))
    luck('rods', 'rmiss', 3, 8, 3, 2, '막대 드롭 급락', ['열 마리째 막대 0개 실화냐', '약탈 검이 없으니까...', '블레이즈가 막대를 안 줘'],
         '왠지 오늘 막대 안 나올 것 같은 느낌', '약탈 검', ['약탈 III 들고 옴', '막대는 금방 모음'])
    cards.append(Card('rods', '막대 안 나옴', 'blaze_rod', 'yellow', 15, '블레이즈가 막대를 안 떨어뜨리게 한다', '블레이즈랑 싸우고 있을 때', [['fight']],
                      '약탈 검을 만들어 온다', usable={5: (None, 'blaze')}))

    # ---------------------------------------------------------------- obsidian short
    H, C = 5, 10
    e = Ev('obsi_crit', '흑요석이 모자람').at(0, popup('흑요석이 9개뿐?!', 'red'), snd('block.note_block.bass', 0.5)) \
        .at(10, say(['어? 하나 모자란데', '분명 10개 캤는데???']), dmg(C)).at(40, say1('...다시 캐러 간다'))
    lapse(e, 60, 2); e.end(118, 'back')
    e = Ev('obsi_hit', '흑요석이 모자람').at(0, popup('흑요석이 9개뿐?!', 'red'), snd('block.note_block.bass', 0.5)).at(10, say1('세어보니 9개네. 하나 더 캐고 온다'), dmg(H))
    lapse(e, 30, 1); e.end(88, 'back')
    Ev('obsi_block', '흑요석이 모자람').at(0, popup('흑요석 여분', 'aqua')).at(8, say(['넉넉하게 11개 캐 왔지', '모자랄까 봐 더 챙김']), bd(H, C)).end(30, 'cont')
    cards.append(Card('obsi', '흑요석 한 개 모자람', 'obsidian', 'dark_purple', 30, '흑요석 하나를 슬쩍 없앤다', '포탈 틀을 쌓고 있을 때', [['frame']],
                      '흑요석은 넉넉하게 캔다', usable={4: (None, 'frame')}))

    # ---------------------------------------------------------------- ghast
    H, C = 7, 15
    def ghast(e):
        return e.at(0, mob_at('ghast', 'ek.ghast', 7.5, 67, 0.5), mface('ek.ghast'), snd('entity.ghast.warn', 1, 0.9)) \
            .at(24, snd('entity.ghast.shoot'), fx_item('ek.fb', 'fire_charge', 5.5, 68, 0.5, 2.5)) \
            .rng(25, 36, 'execute as @e[tag=ek.fb] at @s facing entity %s feet run tp @s ^ ^ ^1.3' % AIM)
    ghast(Ev('ghast_crit', '가스트가 나타났다')).at(38, at_s('function ek:fx/boom'), vanish('ek.fb'), S('tp @s -4.0 ~ ~'),
                                               f'execute as {STEVE} at @s unless block ~ ~-1 ~ minecraft:lava run tp @s -4.0 61 0.5',
                                               fire(1), snd('entity.player.hurt_on_fire'), popup('용암에 빠졌다', 'red')) \
        .rng(39, 72, SPIN).every(42, 70, 8, LAVAFX).at(74, die('lava', '가스트의 화염구를 피하려다 용암에 빠졌습니다'), dmg(C)) \
        .at(84, say(['다리 위에서 가스트는 진짜 아니지', '챙긴 거 다 날아갔네', '방금 화염구 판정 이상한데'], low=['네더 다신 안 온다', '아 진짜 못 해 먹겠네'])) \
        .at(92, vanish('ek.ghast')).end(112, 'major')
    ghast(Ev('ghast_hit', '가스트가 나타났다')).at(38, 'execute at %s run function ek:fx/boom' % AIM, vanish('ek.fb'), hurt(), dmg(H)) \
        .at(44, say(['가스트 소리 진짜 싫어', '어디서 쏘는 거야'])).at(60, vanish('ek.ghast')).end(75, 'resume')
    ghast(Ev('ghast_block', '가스트가 나타났다')).at(37, swing(), snd('entity.player.attack.strong'), popup('쳐냈다', 'aqua')) \
        .rng(38, 50, 'execute as @e[tag=ek.fb] at @s facing entity @e[tag=ek.ghast,limit=1] eyes run tp @s ^ ^ ^1.3') \
        .at(52, 'execute at @e[tag=ek.ghast,limit=1] run function ek:fx/boom', vanish('ek.fb'), 'kill @e[tag=ek.ghast]', snd('entity.ghast.death', 1, 0.8),
            tell(t('Steve이(가) 발전 과제 ', 'white'), t('[발신자에게 반송]', 'green'), t('을 달성했습니다!', 'white'))) \
        .at(58, say(['화염구는 쳐내면 되지', '반사 연습 좀 했다']), bd(H, C)).end(80, 'cont')
    cards.append(Card('ghast', '가스트 화염구', 'ghast_tear', 'white', 35, '가스트가 바라보는 곳에 화염구를 쏜다', '용암 위 다리에 있을 때', [['bridge']], '화염구는 쳐서 돌려보낸다'))

    # ---------------------------------------------------------------- portal off
    H, C = 5, 11
    OFF = ['fill -9 62 10 -8 64 10 minecraft:air', snd('block.glass.break', 0.6), popup_at(-8, 66, 10.5, '포탈 꺼짐', 'red')]
    Ev('portal_crit', '포탈이 꺼졌다').at(0, OFF).at(14, say(['포탈이 왜 꺼져 있어?', '부싯돌 집에 두고 왔는데...']), dmg(C)) \
        .at(30, status('가스트를 유인해서 포탈 다시 켜는 중'), mob_at('ghast', 'ek.ghast', -8.5, 68, 2.5, ',Rotation:[0f,20f]'), snd('entity.ghast.warn', 1, 0.9)) \
        .at(60, snd('entity.ghast.shoot'), fx_item('ek.fb', 'fire_charge', -8.5, 68, 4.5, 2.5)) \
        .rng(61, 72, 'execute as @e[tag=ek.fb] at @s facing -8.0 63 10.5 run tp @s ^ ^ ^0.6') \
        .at(74, 'execute positioned -8.0 62 10.5 run function ek:fx/boom', vanish('ek.fb'), ST.PORTAL5, snd('block.portal.trigger', 1, 0.5)) \
        .at(84, vanish('ek.ghast'), say1('가스트로 포탈 켜기 성공. 하...')).end(95, 'resume')
    Ev('portal_hit', '포탈이 꺼졌다').at(0, OFF).at(14, say1('뒤에서 뭔 소리 났는데? 포탈인가'), dmg(H)).end(40, 'resume')
    Ev('portal_block', '포탈이 꺼졌다').at(0, OFF).at(12, say(['부싯돌은 항상 들고 다님', '바로 다시 켠다']), ST.PORTAL5, snd('item.flintandsteel.use'), bd(H, C)).end(35, 'cont')
    cards.append(Card('portal', '포탈 꺼짐', 'flint_and_steel', 'dark_purple', 30, '네더 포탈을 꺼 버린다', '챙길 걸 다 챙기고 포탈로 돌아갈 때', [['portal']],
                      '부싯돌과 부시는 꼭 챙긴다'))

    # ---------------------------------------------------------------- piglin rage
    H, C = 6, 13
    rage = [popup('금 갑옷이 사라졌다', 'red'), snd('entity.piglin.angry', 1, 0.9), 'tag @e[tag=ek.pig] add ek.chase']
    Ev('piglin_crit', '피글린이 화났다').at(0, rage).rng(1, 44, CHASE).every(24, 40, 8, hurt()).at(46, die('piglin', '피글린에게 살해당했습니다'), dmg(C)) \
        .at(56, say(['금 장화 어디 갔어', '아까까지 신고 있었는데?', '교환 중에 때리는 건 반칙이지'])).end(85, 'death')
    Ev('piglin_hit', '피글린이 화났다').at(0, rage).rng(1, 34, CHASE).at(30, hurt(), dmg(H)).at(36, say1('왜 갑자기 화를 내')).end(55, 'resume')
    Ev('piglin_block', '피글린이 화났다').at(0, popup('금 장화 착용', 'aqua')).at(8, say(['금 장화 신었음', '금만 걸치면 안 때리지']), bd(H, C)).end(30, 'cont')
    cards.append(Card('piglin', '피글린 분노', 'golden_sword', 'gold', 35, '스티브의 금 갑옷을 없애서 피글린을 화나게 한다', '피글린이랑 교환하고 있을 때', [['barter']],
                      '금 장화는 절대 안 벗는다', unlock='runs2'))

    # ---------------------------------------------------------------- ender eye
    H, C = 4, 7
    Ev('eye_crit', '엔더의 눈이 깨졌다').at(0, ssub('eyes', 3), snd('entity.ender_eye.death'), popup('엔더의 눈이 깨졌다 (-3)', 'red'), vanish('ek.eyefx')) \
        .at(10, say(['아 눈 깨졌어', '20% 확률이 지금 터지네', '눈 아까워']), dmg(C)).end(30, 'resume')
    Ev('eye_hit', '엔더의 눈이 깨졌다').at(0, ssub('eyes', 1), snd('entity.ender_eye.death'), popup('주머니 속 눈에 금이 갔다 (-1)', 'red')) \
        .at(10, say1('눈 하나 깨졌네. 아슬아슬한데'), dmg(H)).end(30, 'resume')
    Ev('eye_block', '엔더의 눈이 깨졌다').at(0, popup('눈 여분', 'aqua')).at(8, say(['눈 넉넉하게 만들어 왔지', '여분 4개 더 있음']), bd(H, C)).end(30, 'cont')
    e = Ev('eyeshort', '엔더의 눈이 모자람').at(5, say(['...눈이 모자라네?', '네더를 다시 가야 된다고???']), popup('엔더의 눈 부족', 'red')).at(20, dmg(12))
    lapse(e, 50, 3); e.at(104, sset('eyes', 12)); e.end(108, 'back')
    cards.append(Card('eye', '엔더의 눈 깨짐', 'ender_eye', 'dark_aqua', 20, '엔더의 눈을 깨뜨린다. 모자라면 네더를 다시 가야 함', '눈을 던지고 있을 때', [['eyes']],
                      '눈은 여분까지 만들어 온다', usable={6: (None, 'frames')}))

    # ---------------------------------------------------------------- silverfish
    H, C = 5, 11
    SF = ',attributes:[{id:"minecraft:scale",base:2.2d}]'
    Ev('silverfish_crit', '좀벌레 떼').at(0, [mob_aim('silverfish', 'ek.sf', dx, dz, SF) for dx, dz in ((0, 0), (1.2, 0.6), (-1.2, 0.6), (0.6, -1.2), (-0.6, -1.2))], snd('entity.silverfish.ambient')) \
        .rng(1, 60, CHASE).at(12, say1('좀벌레?!')).every(20, 50, 10, hurt()).at(56, die('silverfish', '좀벌레에게 살해당했습니다'), dmg(C)).at(64, vanish('ek.sf')) \
        .at(70, say(['좀벌레한테 죽는 게 말이 되냐', '요새에서 제일 짜증 나는 놈들', '스포너 부수다가 이게 뭐야'])).end(95, 'death')
    Ev('silverfish_hit', '좀벌레 떼').at(0, [mob_aim('silverfish', 'ek.sf', dx, dz, SF) for dx, dz in ((0, 0), (1.2, 0.6), (-1.2, 0.6))], snd('entity.silverfish.ambient')) \
        .rng(1, 40, CHASE).at(24, hurt(), dmg(H)).every(28, 46, 6, swing(), SWEEP).at(40, 'kill @e[tag=ek.sf,limit=1]').at(48, 'kill @e[tag=ek.sf]') \
        .at(54, say1('벌레 주제에')).end(70, 'resume')
    Ev('silverfish_block', '좀벌레 떼').at(0, popup('좀벌레 차단', 'aqua')).at(8, say(['돌 안 건드리면 안 나옴', '좀벌레 블록은 이제 구분함']), bd(H, C)).end(30, 'cont')
    cards.append(Card('silverfish', '좀벌레 떼', 'silverfish_spawn_egg', 'gray', 30, '바라보는 곳에서 좀벌레 떼가 기어 나온다', '좀벌레 스포너를 부수고 있을 때', [['spawner']],
                      '좀벌레 나오는 돌은 안 건드린다', usable={6: ('down', 'frames')}))

    # ---------------------------------------------------------------- enderman
    H, C = 6, 12
    ANG = '@e[tag=ek.angry,limit=1]'
    def stare(e):
        return e.at(0, 'execute at @e[tag=ek.cur,limit=1] run tag @e[tag=ek.end,limit=1,sort=nearest] add ek.angry',
                    'execute unless entity @e[tag=ek.angry] run tag @e[tag=ek.end,limit=1,sort=random] add ek.angry', snd('entity.enderman.stare', 1, 0.9)).at(10, snd('entity.enderman.scream', 1, 0.8)) \
            .at(16, 'execute at %s rotated ~ 0 positioned ^ ^ ^1.6 run tp %s ~ ~ ~' % (STEVE, ANG), 'execute as %s at @s run tp @s ~ ~ ~ facing entity %s feet' % (ANG, STEVE),
                snd('entity.enderman.teleport'), 'execute at %s run particle minecraft:portal ~ ~1.5 ~ 0.3 0.8 0.3 0.5 40 force' % ANG)
    stare(Ev('enderman_crit', '엔더맨이랑 눈이 마주쳤다')).every(22, 42, 10, hurt()).at(44, die('enderman', '엔더맨에게 살해당했습니다'), dmg(C)) \
        .at(54, say(['눈을 왜 마주쳐서', '활 쏘다가 실수로 봤네', '엔더맨 판정 너무 넓어'])).end(85, 'death')
    stare(Ev('enderman_hit', '엔더맨이랑 눈이 마주쳤다')).at(22, hurt(), dmg(H)).every(26, 38, 6, swing(), SWEEP) \
        .at(40, snd('entity.enderman.teleport'), 'execute at %s run particle minecraft:portal ~ ~1.5 ~ 0.3 0.8 0.3 0.5 40 force' % ANG) \
        .at(44, say1('엔더맨은 왜 건드려 가지고')).end(60, 'resume')
    Ev('enderman_block', '엔더맨이랑 눈이 마주쳤다').at(0, popup('호박 착용', 'aqua')).at(8, say(['호박 썼지롱. 눈 안 마주침', '앞은 잘 안 보이지만 안전함']), bd(H, C)).end(30, 'cont')
    cards.append(Card('enderman', '엔더맨 눈 마주침', 'ender_pearl', 'dark_purple', 30, '스티브가 엔더맨이랑 눈이 마주치게 한다', '활로 수정을 겨누고 있을 때', [['aim']],
                      '호박 쓰고 다닌다'))

    # ---------------------------------------------------------------- dragon wing (void)
    H, C = 7, 18
    DR = '@e[tag=ek.dragon,limit=1]'; DT = '@e[tag=ek.dtgt,limit=1]'
    def swoop(e):
        # the dragon passes 9 blocks over Steve and flies off north, so its wings never reach him (see stage 7)
        return e.at(0, sset('dmode', 3), snd('entity.ender_dragon.growl', 1, 0.9), 'execute at %s run tp %s ~ ~9 ~' % (STEVE, DT)) \
            .rng(1, 28, 'execute as %s at @s facing entity %s feet unless entity @e[tag=ek.dtgt,distance=..1] run tp @s ^ ^ ^0.9 ~180 0' % (DR, DT)) \
            .at(30, snd('entity.ender_dragon.flap', 0.8), popup('날갯짓!', 'light_purple'), sset('snap', 0), pose('standing')) \
            .rng(31, 45, 'execute as %s at @s run tp @s ~ ~0.4 ~-0.9 0 0' % DR)
    e = swoop(Ev('void_crit', '드래곤의 날갯짓')).rng(31, 46, S('tp @s ~ ~0.25 ~0.55')).rng(47, 66, S('tp @s ~ ~-1.1 ~0.25')).at(46, sset('dmode', 0)) \
        .at(67, die('void', '세계 밖으로 떨어졌습니다'), dmg(C)) \
        .at(78, say(['아니 날갯짓 한 방에 공허행이야?', '장비 전부 날아갔네 하...', '넉백 판정이 이게 맞아?'], low=['엔드까지 와서 이러기냐', '진짜 그만하고 싶다'])) \
        .at(90, 'title @a times 5 40 10', 'title @a subtitle ' + comp(t('장비를 처음부터 다시 맞추는 중', 'gray')), 'title @a title ' + comp(t(' '))) \
        .rng(91, 140, 'time add 480').at(142, 'time set 6000', sadd('day', 2)).end(146, 'major')
    swoop(Ev('void_hit', '드래곤의 날갯짓')).rng(31, 46, S('tp @s ~ ~0.25 ~')).at(46, sset('snap', 1), sset('dmode', 0)) \
        .at(60, hurt(), dmg(H), say(['으악 날아간다', '낙뎀 아파'])).end(75, 'resume')
    swoop(Ev('void_block', '드래곤의 날갯짓')).rng(31, 46, S('tp @s ~ ~0.25 ~')).at(46, sset('snap', 1), sset('dmode', 0)) \
        .at(57, snd('item.bucket.empty'), popup('물양동이 착지', 'aqua'), at_s('particle minecraft:splash ~ ~0.2 ~ 0.4 0.1 0.4 0.1 40 force')) \
        .at(60, say(['엠엘지 연습 좀 했지', '드래곤 넉백은 물로 받는다']), bd(H, C)).end(75, 'cont')
    cards.append(Card('void', '드래곤 날갯짓', 'dragon_head', 'light_purple', 45, '드래곤이 날갯짓으로 스티브를 날려 버린다', '공허 위 다리나 기둥 꼭대기에 있을 때',
                      [['bridge'], ['high']], '넉백은 물양동이로 받는다'))

    # ---------------------------------------------------------------- bed
    H, C = 6, 12
    Ev('bed_crit', '침대가 먼저 터졌다').at(0, at_s('function ek:fx/boom'), popup('침대가 먼저 터졌다', 'red'), 'setblock 2 65 0 minecraft:air', 'setblock 1 65 0 minecraft:air') \
        .at(2, die('bed', '[의도적 게임 설계]에 의해 죽었습니다'), dmg(C)).at(14, say(['아 침대 내가 맞았네', '의도적 게임 설계 진짜', '타이밍 한 틱 차이인데'])).end(50, 'death')
    Ev('bed_hit', '침대가 먼저 터졌다').at(0, at_s('function ek:fx/boom'), popup('침대 오폭', 'red')).at(4, hurt(), dmg(H), say(['아 깜짝이야', '침대 왜 지금 터져'])).end(40, 'resume')
    Ev('bed_block', '침대가 먼저 터졌다').at(0, popup('블록 방패', 'aqua')).at(8, say(['침대 앞에 블록 하나 두는 건 기본', '폭발은 블록 뒤에서']), bd(H, C)).end(30, 'cont')
    cards.append(Card('bed', '침대 오폭', 'red_bed', 'red', 30, '침대가 스티브 코앞에서 터지게 한다', '침대로 드래곤을 때리고 있을 때', [['bed']],
                      '침대 앞에 블록을 하나 둔다', usable={7: ('perch', None)}))

    # ---------------------------------------------------------------- dragon heal
    H, C = 5, 9
    def crystal(e, n):
        return e.at(0, 'summon minecraft:end_crystal 9.5 72 -9.5 {Tags:["ek.mob","ek.hc"],ShowBottom:0b,Invulnerable:1b}', snd('block.beacon.activate', 1.2),
                    popup_at(0.5, 76, -1.5, '숨은 수정이 드래곤을 회복시킨다', 'light_purple', '2.5')) \
            .at(4, sadd('dhp', n), iff('dhp', '101..', sset('dhp', 100)))
    crystal(Ev('heal_crit', '숨은 수정'), 50).at(14, say(['피가 왜 차는데???', '수정 다 깼잖아', '어디 숨어 있었어']), dmg(C)) \
        .at(40, hold('bow'), swing(), snd('entity.arrow.shoot')).at(48, 'execute at @e[tag=ek.hc] run function ek:fx/boom', 'kill @e[tag=ek.hc]').end(60, 'resume')
    crystal(Ev('heal_hit', '숨은 수정'), 25).at(14, say1('수정이 하나 더 있었네'), dmg(H)) \
        .at(40, hold('bow'), swing(), snd('entity.arrow.shoot')).at(48, 'execute at @e[tag=ek.hc] run function ek:fx/boom', 'kill @e[tag=ek.hc]').end(60, 'resume')
    Ev('heal_block', '숨은 수정').at(0, popup('수정 개수 확인 완료', 'aqua')).at(8, say(['수정 개수 세고 시작함', '숨은 수정은 없음']), bd(H, C)).end(30, 'cont')
    cards.append(Card('heal', '숨은 수정', 'end_crystal', 'light_purple', 35, '숨겨 둔 수정으로 드래곤 체력을 채운다', '드래곤을 기다리거나 때리고 있을 때',
                      [['bed'], ['perch']], '수정 개수를 세고 시작한다'))

    # ---------------------------------------------------------------- crystal blast
    H, C = 6, 12
    Ev('crystal_crit', '수정이 눈앞에서 터졌다').at(0, at_s('function ek:fx/boom'), popup('수정이 눈앞에서 터졌다', 'red'),
                                          'fill -3 65 4 -3 80 4 minecraft:air replace minecraft:cobblestone') \
        .at(12, die('fall', '높은 곳에서 떨어졌습니다'), dmg(C)).at(24, say(['수정 바로 옆에서 터지네', '기둥 위에서 죽는 게 제일 억울해', '폭발 범위가 이게 맞아?'])).end(60, 'death')
    Ev('crystal_hit', '수정이 혼자 터졌다').at(0, 'execute at @e[tag=ek.cr,limit=1,sort=random] run function ek:fx/boom', popup('수정 유폭', 'red')) \
        .at(4, hurt(), dmg(H), say(['으악 뭐야', '수정이 혼자 터졌어'])).end(40, 'resume')
    Ev('crystal_block', '수정이 혼자 터졌다').at(0, popup('안전거리 확보', 'aqua')).at(8, say(['수정은 멀리서 깬다', '눈덩이 하나면 됨']), bd(H, C)).end(30, 'cont')
    cards.append(Card('crystal', '수정 유폭', 'tnt', 'red', 35, '엔드 수정을 스티브 코앞에서 터뜨린다', '기둥 꼭대기에 올라가 있을 때', [['high']],
                      '수정은 멀리서만 깬다', unlock='win1', usable={7: (None, 'cr4')}))

    # ---------------------------------------------------------------- anvil (every stage; a pure aiming card)
    H, C = 6, 14
    ANV = 'execute at %s run ' % AIM + fx_item('ek.anvfx', 'anvil', '~', '~0.6', '~', 1.8)
    Ev('anvil_crit', '모루에 깔렸다').at(0, at_s(fx_item('ek.anvfx', 'anvil', '~', '~1.3', '~', 1.8)), snd('block.anvil.land', 0.8, 0.9), popup('모루 직격', 'red'), part('poof', 1, 0.4, 0.05, 20)) \
        .at(2, die('anvil', '떨어지는 모루에 깔렸습니다'), dmg(C)) \
        .at(16, say(['하늘에서 모루가 왜 떨어져???', '걸어가다 모루 맞는 게 말이 되냐', '방금 그거 뭐였어 진짜'], low=['모루까지 떨어지네 하하', '이 월드 나 싫어하지'])).end(50, 'death')
    Ev('anvil_hit', '모루가 떨어졌다').at(0, ANV, snd('block.anvil.land', 0.8, 0.9), popup('쿵!', 'red')).at(2, hurt(), dmg(H)) \
        .at(8, say(['으악 모루?!', '하늘에서 모루가 왜 떨어져', '누가 위에서 모루 던지냐'])).end(30, 'resume')
    Ev('anvil_block', '모루가 떨어졌다').at(0, ANV, snd('block.anvil.land', 0.8, 0.9), popup('위를 보고 피했다', 'aqua')) \
        .at(8, say(['모루 떨어지는 소리는 이제 안다', '위 한 번 보고 걸음']), bd(H, C)).end(30, 'cont')
    cards.append(Card('anvil', '하늘에서 모루', 'anvil', 'gray', 30, '바라보는 곳에 모루를 떨어뜨린다', '걸어가는 스티브를 정통으로 맞히면 즉사', [],
                      '이제 머리 위도 보고 다닌다'))

    pools = {1: ['creeper', 'night', 'arrow', 'pick', 'thunder'], 2: ['creeper', 'gravel', 'zombies', 'pick', 'lost'],
             3: ['lava', 'gravel', 'creeper', 'pick', 'floor'], 4: ['flint', 'obsi', 'night', 'creeper', 'thunder'],
             5: ['ghast', 'barter', 'rods', 'portal', 'piglin'], 6: ['eye', 'silverfish', 'lost', 'creeper', 'floor'],
             7: ['void', 'enderman', 'bed', 'heal', 'crystal']}
    for n in pools: pools[n].append('anvil')

    # ---------------------------------------------------------------- aimed cards
    # t: ticks the throw takes to land.  rd / rh / rg: how far from Steve the landing spot may be for a direct hit, a hit and a graze.
    # Mob cards have no graze (the mob walks the rest of the way) and are lost when they land on lava.
    GRAVEL_FX = 'particle minecraft:block{block_state:"minecraft:gravel"} ~ ~0.6 ~ 0.4 0.3 0.4 0 20 force'
    ANVIL_REST = ['summon item_display ~ ~0.6 ~ {Tags:["ek.tmp","ek.new"],billboard:"center",item:{id:"minecraft:anvil",count:1},%s}' % (DISPLAY_T % (1.8, 1.8, 1.8)),
                  'scoreboard players set @e[tag=ek.new] ek.life 30', 'tag @e[tag=ek.new] remove ek.new', 'playsound minecraft:block.anvil.land master @a ~ ~ ~ 3 0.9']
    AIMED = {
        'creeper': dict(t=16, mob=True, rd=2.0, rh=7.0),
        'zombies': dict(t=16, mob=True, rd=2.0, rh=7.0),
        'silverfish': dict(t=14, mob=True, rd=2.0, rh=7.0),
        'arrow': dict(t=12, mob=True, rd=-1, rh=14.0),
        'thunder': dict(t=8, rd=1.0, rh=3.0, rg=5.0, throw=['weather thunder'],
                        miss=['summon minecraft:lightning_bolt ~ ~ ~', 'schedule function ek:fx/nofire 12t']),
        'gravel': dict(t=14, rd=1.0, rh=2.2, rg=3.4, dodge=True, miss=[GRAVEL_FX, 'playsound minecraft:block.gravel.break master @a ~ ~ ~ 3 0.6']),
        'lava': dict(t=12, rd=1.0, rh=2.2, rg=3.4, miss=['particle minecraft:lava ~ ~0.5 ~ 0.3 0.2 0.3 0 12 force', 'playsound minecraft:block.lava.pop master @a ~ ~ ~ 3 0.8']),
        'floor': dict(t=10, rd=1.0, rh=2.0, rg=3.0, miss=['playsound minecraft:block.stone.break master @a ~ ~ ~ 3 0.7']),
        'ghast': dict(t=18, rd=1.5, rh=3.6, rg=5.2, miss=['function ek:fx/boom']),
        'anvil': dict(t=14, rd=1.0, rh=2.2, rg=3.6, direct_crit=True, dodge=True, miss=ANVIL_REST),
    }
    sq = lambda r: -1 if r < 0 else int(round(r * r * 100))
    idx = {c.id: i + 1 for i, c in enumerate(cards)}
    for c in cards: c.aim = AIMED.get(c.id)
    assert set(AIMED) <= set(idx)

    # ---------------------------------------------------------------- try / aim / land / learn functions
    for c in cards:
        pre = []
        for sn, (lo, hi) in c.usable.items():
            stg = stages[sn - 1]
            a = stg.idx[lo] if lo else 0; b = stg.idx[hi] if hi else len(stg.beats) - 1
            pre.append('execute if score #stage ek matches %d unless score #beat ek matches %d..%d run return run function ek:cards/cant' % (sn, a, b))
        pay = ['execute unless score #energy ek matches %d.. run return run function ek:cards/no_energy' % c.cost,
               ssub('energy', c.cost), 'function ek:cards/paid']
        sweet = [sset('sweet', 0)]
        for term in c.sweet:
            sweet.append('execute %srun scoreboard players set #sweet ek 1' % ''.join('if score #f_%s ek matches 1 ' % f for f in term))
        if c.aim and c.aim.get('direct_crit'):
            sweet.append('execute if score #tier ek matches 3 if score #moving ek matches 1 run scoreboard players set #sweet ek 1')
        # a distracted Steve (see steve/idle) or a lucky box makes any card a sweet spot
        sweet += [iff('wild', 1, sset('sweet', 1)), iff('lucky', 1, sset('sweet', 1)), sset('lucky', 0)]
        res = abar(t('【%s】 발동' % c.name, c.color), hold=45)
        res.append(iff('sweet', 1, 'title @a actionbar ' + comp(t('【%s】 발동  ★ 노림수 적중!' % c.name, 'aqua', True))))
        res.append(iff('sweet', 1, snd('entity.player.levelup', 1.6, 0.5)))
        res += [iff('l_' + c.id, 1, f'return run function ek:ev/{c.id}_block/start'), sadd('u_' + c.id, 1),
                iff('sweet', 1, f'return run function ek:ev/{c.id}_crit/start'), f'function ek:ev/{c.id}_hit/start']
        if not c.aim:
            P.fn(f'c/{c.id}/try', pre, pay, sweet, res)
        else:
            a = c.aim
            P.fn(f'c/{c.id}/radii', sset('rd', sq(a['rd'])), sset('rh', sq(a['rh'])), sset('rg', sq(a.get('rg', a['rh']))))
            P.fn(f'c/{c.id}/aim', pre,
                 unl('cur', 1, 'return run function ek:cards/noaim'),
                 iff('drop', 1, 'return run function ek:cards/dropping'),
                 pay, sset('dcard', idx[c.id]), sset('dcost', c.cost), sset('dropt', a['t']), sset('ddodge', 1 if a.get('dodge') else 0), sset('noticed', 0), sadd('nthrow', 1), a.get('throw', []),
                 'execute at @e[tag=ek.cur,limit=1] run function ek:drop/start {t:%d,item:"minecraft:%s"}' % (a['t'], c.icon),
                 abar(t('【%s】 던졌다' % c.name, c.color), hold=a['t'] + 2))
            # a Steve who saw it coming (drop/dodge) takes one step less of it: a direct hit is a hit, a hit only grazes
            land0 = [f'function ek:c/{c.id}/radii', 'function ek:drop/tier',
                     'execute if score #noticed ek matches 1 if score #tier ek matches 1.. run scoreboard players remove #tier ek 1']
            if a.get('mob'):
                land0.append('execute at %s if block ~ ~-1 ~ minecraft:lava run return run function ek:drop/sunk' % AIM)
            for m in a.get('miss', []):
                land0.append('execute if score #tier ek matches ..1 at %s run %s' % (AIM, m))
            land0 += [iff('tier', 0, 'return run function ek:drop/miss'), iff('tier', 1, 'return run function ek:drop/graze'), sadd('nhit', 1)]
            if not a.get('direct_crit'):
                land0.append('execute if score #tier ek matches 3 if score #moving ek matches 1 run function ek:drop/snipe')
            land0.append(f'function ek:c/{c.id}/land')
            P.fn(f'c/{c.id}/land0', land0)
            P.fn(f'c/{c.id}/land', sweet, res)
        P.fn(f'c/{c.id}/learn', sset('l_' + c.id, 1), say1(c.learn),
             popup_at(0.5, 77.5, 0.5, '스티브가 [%s] 대처법을 익혔다' % c.name, 'gray', '2.5'), snd('block.note_block.pling', 0.6, 0.8),
             'function ek:cards/deal', 'function ek:steve/equip')
        # a lucky box can make Steve forget what he learned
        P.fn(f'c/{c.id}/forget', sset('l_' + c.id, 0), sset('u_' + c.id, 0),
             tell(t('  스티브가 ', 'yellow'), t('[%s]' % c.name, c.color), t(' 대처법을 까먹었다!', 'yellow')),
             popup_at(0.5, 77.5, 0.5, '스티브가 [%s] 대처법을 까먹었다' % c.name, 'yellow', '2.5'), 'function ek:cards/deal', 'function ek:steve/equip')
    P.fn('drop/dispatch', [iff('dcard', idx[c.id], f'return run function ek:c/{c.id}/land0') for c in cards if c.aim])
    return cards, pools
