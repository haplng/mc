# -*- coding: utf-8 -*-
"""족보 엔진 — 숫자 하나에서 족보 400개를 찾아내는 mcfunction을 만든다.

입력: #d1..#d9 jv (자릿값), #ul4·#ul5 jv (전설·신화 해금 여부)
출력: 걸린 족보는 #g<id> jv 가 #gen jv 과 같아진다 ("도장" 방식 — 초기화가 필요 없다).
      #nh = 걸린 개수, #bt = 가장 높은 등급(-1=꽝)

빠르게 하는 요령
  * 옆자리 차이 #e1..#e8 를 한 번만 구해서 여러 족보가 같이 쓴다.
  * 같은 숫자 구조는 8비트 마스크(#x_S)로 만들어 255개 잎(leaf) 중 하나로 바로 뛴다.
  * 숫자 조각(8282, 119 …)은 자리마다 트라이(trie)를 타고 내려가며 찾는다.
  * 묶음(같은 계열 중 가장 높은 것 하나만)은 "승급" 함수로 그 자리에서 해결한다.
"""
import hands as HM

NS = 'jb:hand/'


def C(n):
    return '#c%d jv' % n


class Engine:
    def __init__(self, hands, tier, ids=None):
        """hands: HM.HANDS 형식 목록(alias 포함). tier: key → 0..5. ids: key → 번호(1부터)"""
        self.F = {}
        self.all = hands
        self.H = {h['key']: h for h in hands}
        self.real = [h for h in hands if not (h['eng'] and h['eng'][0] == 'alias')]
        self.ids = dict(ids) if ids else {h['key']: i + 1 for i, h in enumerate(self.real)}
        for h in hands:
            if h['eng'] and h['eng'][0] == 'alias':
                self.ids[h['key']] = self.ids[h['eng'][1]]
        self.tier = dict(tier)
        for h in hands:
            if h['eng'] and h['eng'][0] == 'alias':
                self.tier[h['key']] = self.tier[h['eng'][1]]
        self.groups = {}
        for h in hands:
            if h['grp']:
                self.groups.setdefault(h['grp'], []).append(h['key'])
        self.consts = set()
        self.scores = set()
        self.upgrade_groups = set()
        self.scan_slot = {}

    # ---------- 기본 도구 ----------
    def fn(self, name):
        return self.F.setdefault('hand/' + name, [])

    def c(self, n):
        self.consts.add(n)
        return C(n)

    def id(self, key):
        return self.ids[key]

    def open(self, key):
        t = self.tier[key]
        if t == 4:
            return 'if score #ul4 jv matches 1 '
        if t == 5:
            return 'if score #ul5 jv matches 1 '
        return ''

    def hit(self, key):
        return 'function %sh/%d' % (NS, self.id(key))

    def hitu(self, key):
        """이미 걸렸으면 다시 걸지 않는다"""
        return 'execute unless score #g%d jv = #gen jv run function %sh/%d' % (self.id(key), NS, self.id(key))

    def rank(self, key):
        g = self.H[key]['grp']
        return self.groups[g].index(key) + 1

    def up(self, key):
        """묶음 승급 호출"""
        g = self.H[key]['grp']
        self.upgrade_groups.add(g)
        return 'function %se/g_%s_%d' % (NS, g, self.rank(key))

    def act(self, key):
        """족보 key를 '그 자리에서' 거는 명령 (묶음이면 승급, 아니면 한 번만 걸기)"""
        if self.H[key]['grp']:
            return self.up(key)
        return self.hitu(key)

    def ladder(self, name, score, rungs):
        """숫자 사다리: rungs = [(조건문자열 'matches 8..', key)] 높은 것부터"""
        f = self.fn('e/' + name)
        for i, (cond, key) in enumerate(rungs):
            f.append('execute if score #%s jv %s %srun return run %s' % (score, cond, self.open(key), self.hit(key)))
        return 'function %se/%s' % (NS, name)

    # ---------- 승급 묶음 ----------
    def build_upgrade(self):
        for g in sorted(self.upgrade_groups):
            keys = self.groups[g]
            un = self.fn('e/gu_%s' % g)
            for r, k in enumerate(keys, 1):
                un.append('execute if score #L_%s jv matches %d run scoreboard players set #g%d jv 0' % (g, r, self.id(k)))
            un.append('scoreboard players remove #nh jv 1')
            for r, k in enumerate(keys, 1):
                f = self.fn('e/g_%s_%d' % (g, r))
                f.append('execute if score #S_%s jv = #gen jv if score #L_%s jv matches %d.. run return 0' % (g, g, r))
                t = self.tier[k]
                if t >= 4:
                    f.append('execute unless score #ul%d jv matches 1 run return 0' % t)
                f.append('execute if score #S_%s jv = #gen jv run function %se/gu_%s' % (g, NS, g))
                f.append('scoreboard players operation #S_%s jv = #gen jv' % g)
                f.append('scoreboard players set #L_%s jv %d' % (g, r))
                f.append(self.hit(k))

    # ---------- 걸림(hit) 함수와 정리(scan) 나무 ----------
    def build_hits(self, pay):
        """pay: key → 기본 코인. 등급 안에서 코인이 큰 순으로 8개씩 묶는다."""
        by_t = {t: [] for t in range(6)}
        for h in self.real:
            by_t[self.tier[h['key']]].append(h['key'])
        self.order = {}
        for t in range(6):
            ks = sorted(by_t[t], key=lambda k: (-pay[k], self.id(k)))
            self.order[t] = ks
            for i, k in enumerate(ks):
                self.scan_slot[k] = (t, i // 8)
        for h in self.real:
            k = h['key']
            t, gidx = self.scan_slot[k]
            f = self.fn('h/%d' % self.id(k))
            if t >= 4:
                f.append('execute unless score #ul%d jv matches 1 run return 0' % t)
            f.append('scoreboard players operation #g%d jv = #gen jv' % self.id(k))
            f.append('scoreboard players operation #t%d_%d jv = #gen jv' % (t, gidx))
            f.append('scoreboard players operation #t%d jv = #gen jv' % t)
            f.append('scoreboard players add #nh jv 1')
            f.append('scoreboard players operation #bt jv > %s' % self.c(t))
        root = self.fn('scan')
        for t in range(5, -1, -1):
            ks = self.order[t]
            if not ks:
                continue
            root.append('execute if score #t%d jv = #gen jv run function %ssc/t%d' % (t, NS, t))
            node = self.fn('sc/t%d' % t)
            for gi in range((len(ks) + 7) // 8):
                node.append('execute if score #t%d_%d jv = #gen jv run function %ssc/t%d_%d' % (t, gi, NS, t, gi))
                leaf = self.fn('sc/t%d_%d' % (t, gi))
                for k in ks[gi * 8:gi * 8 + 8]:
                    leaf.append('execute if score #g%d jv = #gen jv run function %sc/%d' % (self.id(k), NS, self.id(k)))

    # ---------- 범위 나무 (점수 값 → 잎 함수) ----------
    def range_tree(self, name, score, leaves):
        """leaves: {값: 잎 함수 이름}. 4갈래로 나눠 내려간다. 뿌리 함수 이름을 돌려준다."""
        vals = sorted(leaves)
        cnt = [0]

        def build(vs, fname):
            f = self.fn(fname)
            if len(vs) <= 4:
                for v in vs:
                    f.append('execute if score #%s jv matches %d run return run function %s%s' % (score, v, NS, leaves[v]))
                return
            n = len(vs)
            parts = [vs[i * n // 4:(i + 1) * n // 4] for i in range(4)]
            parts = [p for p in parts if p]
            for i, p in enumerate(parts):
                cnt[0] += 1
                child = '%s_%d' % (name, cnt[0])
                if len(p) == 1:
                    f.append('execute if score #%s jv matches %d run return run function %s%s' % (score, p[0], NS, leaves[p[0]]))
                    continue
                if i < len(parts) - 1:
                    f.append('execute if score #%s jv matches ..%d run return run function %s%s' % (score, p[-1], NS, child))
                else:
                    f.append('function %s%s' % (NS, child))
                build(p, child)
        build(vals, name)
        return name

    # =====================================================================
    # 같은 숫자 구조 (마스크 S)
    # =====================================================================
    @staticmethod
    def runs_of(mask):
        runs = []
        start = 1
        for i in range(1, 9):
            if not (mask >> (i - 1)) & 1:
                runs.append((start, i - start + 1))
                start = i + 1
        runs.append((start, 9 - start + 1))
        return runs

    def s_leaf(self, mask):
        runs = self.runs_of(mask)
        L = [r[1] for r in runs]
        nr = len(runs)
        f = []
        mr = max(L)
        np_ = sum(1 for x in L if x >= 2)
        nr3 = sum(1 for x in L if x >= 3)
        nr4 = sum(1 for x in L if x >= 4)
        f.append('scoreboard players set #x_mr jv %d' % mr)
        f.append('scoreboard players set #x_np jv %d' % np_)

        def is_chain(j, k):
            if j + k > nr:
                return False
            if L[j] < 2 or L[j + k - 1] < 2:
                return False
            return all(L[t] == 2 for t in range(j + 1, j + k - 1))
        ch = 0
        for k in (4, 3, 2):
            if any(is_chain(j, k) for j in range(nr)):
                ch = k
                break
        if np_ >= 2:
            adj = any((L[j] >= 3 and L[j + 1] >= 2) or (L[j] >= 2 and L[j + 1] >= 3) for j in range(nr - 1))
            if L == [3, 3, 3]:
                sg = 5
            elif nr4 >= 2:
                sg = 4
            elif nr3 >= 2:
                sg = 3
            elif adj:
                sg = 2
            elif nr3 >= 1:
                sg = 1
            else:
                sg = 0
            f.append('scoreboard players set #x_ch jv %d' % ch)
            f.append('scoreboard players set #x_sg jv %d' % sg)
        if np_ >= 3:
            f.append('scoreboard players set #x_fb jv 0')
            for j in range(nr - 2):
                if L[j] >= 2 and L[j + 1] == 2 and L[j + 2] >= 2:
                    lvl = 2 if (L[j] >= 3 and L[j + 2] >= 3) else 1
                    f.append('execute if score #d%d jv = #d%d jv run scoreboard players operation #x_fb jv > %s' % (runs[j][0], runs[j + 2][0], self.c(lvl)))
        if ch >= 3:
            f.append('scoreboard players set #x_tr jv 0')
            for k in (3, 4):
                for j in range(nr):
                    if is_chain(j, k):
                        ends = [runs[j + t][0] + L[j + t] - 1 for t in range(k - 1)]
                        for sgn in (1, -1):
                            f.append('execute ' + ' '.join('if score #e%d jv matches %d' % (p, sgn) for p in ends) +
                                     ' run scoreboard players operation #x_tr jv > %s' % self.c(k))
        # 반반 / 무지개떡
        if nr == 2 and L[0] in (4, 5):
            f.append(self.hit('half'))
        if nr == 3 and L != [3, 3, 3]:
            f.append(self.hit('tteok'))
        # 양 갈래 / 헤드폰
        if mask & 1 and mask & 128:
            f.append('function %se/pig' % NS)
        front = (mask & 3) == 3
        back = (mask & 192) == 192
        if front and back:
            f.append(self.hit('guns'))
        elif front:
            f.append(self.hit('rush'))
        elif back:
            f.append(self.hit('spurt'))
        # 커플룩
        big = [r for r in runs if r[1] >= 2]
        for a in range(len(big)):
            for b in range(a + 1, len(big)):
                f.append('execute if score #d%d jv = #d%d jv unless score #g%d jv = #gen jv run %s' % (
                    big[a][0], big[b][0], self.id('look'), self.hit('look')))
        # 마카롱
        for j in range(1, nr - 1):
            if L[j] == 3:
                s = runs[j][0]
                f.append('execute if score #d%d jv = #d%d jv unless score #g%d jv = #gen jv run %s' % (
                    s - 1, s + 3, self.id('maca'), self.hit('maca')))
        # 짝수 길이 대칭의 가운데
        for c in range(2, 8):
            if (mask >> (c - 1)) & 1:
                f.append('function %se/pe%d' % (NS, c))
        return f

    def build_s(self):
        leaves = {}
        for m in range(1, 256):
            name = 'e/s/%d' % m
            self.fn(name).extend(self.s_leaf(m))
            leaves[m] = name
        self.range_tree('e/s_root', 'x_S', leaves)
        # 대칭: 짝수 가운데 (c, c+1)
        for c in range(2, 8):
            f = self.fn('e/pe%d' % c)
            f.append('scoreboard players set #x_pd jv 0')
            k = 1
            while c - k >= 1 and c + 1 + k <= 9:
                a, b = c - k, c + 1 + k
                f.append('execute unless score #d%d jv = #d%d jv run return 0' % (a, b))
                f.append('execute unless score #d%d jv = #d%d jv run scoreboard players set #x_pd jv 1' % (a, c))
                f.append('execute if score #x_pd jv matches 1 run scoreboard players operation #x_pal jv > %s' % self.c(2 * k + 2))
                k += 1
        f = self.fn('e/pig')
        f.append('execute if score #d1 jv = #d9 jv %srun return run %s' % (self.open('hp'), self.hit('hp')))
        f.append(self.hit('pig'))
        # 정리
        run_l = self.ladder('l_run', 'x_mr', [('matches %d..' % k, 'run%d' % k) for k in range(8, 1, -1)])
        np_l = self.ladder('l_np', 'x_np', [('matches %d..' % k, 'np%d' % k) for k in (4, 3, 2)])
        ch_l = self.ladder('l_chain', 'x_ch', [('matches %d..' % k, 'ch%d' % k) for k in (4, 3, 2)])
        sg_l = self.ladder('l_sg', 'x_sg', [('matches 5', 'sgr'), ('matches 4..', 'clv2'), ('matches 3..', 'sgx'), ('matches 2..', 'sg2'), ('matches 1..', 'sgm')])
        fb_l = self.ladder('l_bread', 'x_fb', [('matches 2..', 'fat'), ('matches 1..', 'fish')])
        tr_l = self.ladder('l_train', 'x_tr', [('matches 4..', 'tr4'), ('matches 3..', 'tr3')])
        r = self.fn('e/s_res')
        r.append(run_l)
        r.append('execute if score #x_np jv matches 2.. run function %se/s_res2' % NS)
        r2 = self.fn('e/s_res2')
        r2.append(np_l)
        r2.append('execute if score #x_ch jv matches 2.. run ' + ch_l)
        r2.append('execute if score #x_sg jv matches 1.. run ' + sg_l)
        r2.append('execute if score #x_np jv matches 3.. run function %se/s_res3' % NS)
        r3 = self.fn('e/s_res3')
        r3.append('execute if score #x_fb jv matches 1.. run ' + fb_l)
        r3.append('execute if score #x_ch jv matches 3.. if score #x_tr jv matches 3.. run ' + tr_l)

    # =====================================================================
    # 한 칸 건너 같은 숫자 (마스크 Y)
    # =====================================================================
    def y_leaf(self, mask):
        bits = [i for i in range(1, 8) if (mask >> (i - 1)) & 1]
        f = ['scoreboard players set #x_al jv 0', 'scoreboard players set #x_bl jv 0']
        # 번갈아: 이어진 비트 묶음 [a..b]
        i = 0
        while i < len(bits):
            j = i
            while j + 1 < len(bits) and bits[j + 1] == bits[j] + 1:
                j += 1
            m = j - i + 1
            if m >= 2:
                f.append('execute unless score #e%d jv matches 0 run scoreboard players operation #x_al jv > %s' % (bits[i], self.c(m + 2)))
            i = j + 1
        # 깜빡: 두 칸 간격으로 이어진 비트
        for par in (0, 1):
            chain = [b for b in bits if b % 2 == par]
            i = 0
            while i < len(chain):
                j = i
                while j + 1 < len(chain) and chain[j + 1] == chain[j] + 2:
                    j += 1
                seg = chain[i:j + 1]
                k = len(seg)
                for m in range(k, 1, -1):
                    for s in range(0, k - m + 1):
                        sub = seg[s:s + m]
                        f.append('execute ' + ' '.join('unless score #e%d jv matches 0' % b for b in sub) +
                                 ' run scoreboard players operation #x_bl jv > %s' % self.c(m + 1))
                i = j + 1
        # 홀수 길이 대칭의 가운데 (가운데 = i+1)
        for b in bits:
            if 2 <= b <= 6:
                f.append('function %se/po%d' % (NS, b + 1))
        return f

    def build_y(self):
        leaves = {}
        for m in range(1, 128):
            name = 'e/y/%d' % m
            self.fn(name).extend(self.y_leaf(m))
            leaves[m] = name
        self.range_tree('e/y_root', 'x_Y', leaves)
        for c in range(3, 8):
            f = self.fn('e/po%d' % c)
            f.append('scoreboard players set #x_pd jv 0')
            f.append('execute unless score #d%d jv = #d%d jv run scoreboard players set #x_pd jv 1' % (c - 1, c))
            k = 2
            while c - k >= 1 and c + k <= 9:
                a, b = c - k, c + k
                f.append('execute unless score #d%d jv = #d%d jv run return 0' % (a, b))
                f.append('execute unless score #d%d jv = #d%d jv run scoreboard players set #x_pd jv 1' % (a, c))
                f.append('execute if score #x_pd jv matches 1 run scoreboard players operation #x_pal jv > %s' % self.c(2 * k + 1))
                k += 1
        al = self.ladder('l_alt', 'x_al', [('matches %d..' % k, 'alt%d' % k) for k in (8, 7, 6, 5, 4)])
        bl = self.ladder('l_blink', 'x_bl', [('matches %d..' % k, 'bl%d' % k) for k in (5, 4, 3)])
        r = self.fn('e/y_res')
        r.append('execute if score #x_al jv matches 4.. run ' + al)
        r.append('execute if score #x_bl jv matches 3.. run ' + bl)

    # =====================================================================
    # 옆자리 차이로 보는 줄(line) 검사
    # =====================================================================
    def build_lines(self, main):
        # 도레미 / 도시라 (+ 산, 지하)
        for sgn, pre, grp, hgrp in ((1, 'as', 'asc', 'hill'), (-1, 'ds', 'dsc', 'pit')):
            keys = self.groups[grp]       # 길이 3,4,5,6,7,8+
            hk = self.groups[hgrp]        # 2번, 3번
            for i in range(1, 8):
                main.append('execute if score #e%d jv matches %d if score #e%d jv matches %d run function %se/%s%d' % (i, sgn, i + 1, sgn, NS, pre, i))
                f = self.fn('e/%s%d' % (pre, i))
                # 지금까지 확인된 길이 = 3 (e_i, e_{i+1})
                if i + 3 <= 8:
                    f.append('execute if score #e%d jv matches %d if score #e%d jv matches %d run %s' % (i + 2, -sgn, i + 3, -sgn, self.up(hk[0])))
                ln = 3
                while True:
                    nxt = i + ln - 1       # 다음에 볼 차이 번호
                    rk = min(ln, 8) - 2    # 길이 3 → 1번째
                    if nxt > 8 or ln >= 8:
                        f.append(self.up(keys[rk - 1]))
                        break
                    f.append('execute unless score #e%d jv matches %d run return run %s' % (nxt, sgn, self.up(keys[rk - 1])))
                    ln += 1
                    if ln == 4 and i + 5 <= 8:
                        f.append('execute if score #e%d jv matches %d if score #e%d jv matches %d if score #e%d jv matches %d run %s' % (
                            i + 3, -sgn, i + 4, -sgn, i + 5, -sgn, self.up(hk[1])))
        # 계속 커짐 / 작아짐 (5개 이상)
        for rng, pre, grp in (('1..', 'in', 'inc'), ('..-1', 'de', 'dec')):
            keys = self.groups[grp]       # 5,6,7,8+
            for i in range(1, 6):
                main.append('execute ' + ' '.join('if score #e%d jv matches %s' % (i + t, rng) for t in range(4)) + ' run function %se/%s%d' % (NS, pre, i))
                f = self.fn('e/%s%d' % (pre, i))
                ln = 5
                while True:
                    nxt = i + ln - 1
                    rk = min(ln, 8) - 4
                    if nxt > 8 or ln >= 8:
                        f.append(self.up(keys[rk - 1]))
                        break
                    f.append('execute unless score #e%d jv matches %s run return run %s' % (nxt, rng, self.up(keys[rk - 1])))
                    ln += 1
        # 전체 모양
        up = lambda i: 'if score #e%d jv matches 1..' % i
        dn = lambda i: 'if score #e%d jv matches ..-1' % i
        main.append('execute ' + ' '.join(up(i) if i % 2 else dn(i) for i in range(1, 9)) + ' run ' + self.hit('zig'))
        main.append('execute ' + ' '.join(dn(i) if i % 2 else up(i) for i in range(1, 9)) + ' run ' + self.hit('zig'))
        main.append('execute ' + ' '.join(up(i) for i in range(1, 5)) + ' ' + ' '.join(dn(i) for i in range(5, 9)) + ' run ' + self.hit('mtn'))
        main.append('execute ' + ' '.join(dn(i) for i in range(1, 5)) + ' ' + ' '.join(up(i) for i in range(5, 9)) + ' run ' + self.hit('cny'))
        main.append('execute ' + ' '.join('if score #e%d jv matches 0..' % i for i in range(1, 9)) + ' unless score #x_S jv matches 255 run ' + self.hit('sortu'))
        main.append('execute ' + ' '.join('if score #e%d jv matches ..0' % i for i in range(1, 9)) + ' unless score #x_S jv matches 255 run ' + self.hit('sortd'))
        main.append('execute ' + ' '.join('unless score #e%d jv matches -4..4' % i for i in range(1, 9)) + ' run ' + self.hit('jump'))
        main.append('execute ' + ' '.join('if score #e%d jv matches -1..1' % i for i in range(1, 9)) + ' unless score #x_S jv matches 255 run function %se/crawl' % NS)
        f = self.fn('e/crawl')
        f.append('execute if score #x_S jv matches 0 %srun return run %s' % (self.open('worm'), self.hit('worm')))
        f.append(self.hit('tip'))
        oth = [1, 2, 3, 4, 6, 7, 8, 9]
        main.append('execute ' + ' '.join('if score #d5 jv > #d%d jv' % i for i in oth) + ' run ' + self.hit('star'))
        main.append('execute ' + ' '.join('if score #d5 jv < #d%d jv' % i for i in oth) + ' run ' + self.hit('donut'))
        main.append('execute ' + ' '.join('if score #d1 jv > #d%d jv' % i for i in range(2, 10)) + ' ' + ' '.join('if score #d9 jv < #d%d jv' % i for i in range(2, 9)) + ' run ' + self.hit('drag'))
        main.append('execute ' + ' '.join('if score #d1 jv < #d%d jv' % i for i in range(2, 10)) + ' ' + ' '.join('if score #d9 jv > #d%d jv' % i for i in range(2, 9)) + ' run ' + self.hit('late'))
        # 첫·끝
        main.append('execute if score #d1 jv = #d9 jv run function %se/fe' % NS)
        f = self.fn('e/fe')
        f.append('execute if score #d2 jv = #d8 jv if score #d3 jv = #d7 jv unless score #d4 jv = #d6 jv run function %se/frame' % NS)
        f.append('execute if score #d1 jv = #d5 jv %srun return run %s' % (self.open('fme'), self.hit('fme')))
        f.append(self.hit('fe'))
        f = self.fn('e/frame')
        f.append('execute if score #e1 jv matches 0 if score #e2 jv matches 0 run return 0')
        f.append(self.hit('frame'))
        main.append('execute if score #d1 jv = #d7 jv if score #d2 jv = #d8 jv if score #d3 jv = #d9 jv run function %se/carou' % NS)
        f = self.fn('e/carou')
        f.append('execute if score #e1 jv matches 0 if score #e2 jv matches 0 run return 0')
        f.append(self.hit('carou'))
        main.append('execute if score #d1 jv = #d6 jv if score #d2 jv = #d7 jv if score #d3 jv = #d8 jv if score #d4 jv = #d9 jv run function %se/loop' % NS)
        f = self.fn('e/loop')
        f.append('execute if score #e1 jv matches 0 if score #e2 jv matches 0 if score #e3 jv matches 0 run return 0')
        f.append(self.hit('loop'))
        main.append('execute if score #d1 jv = #d6 jv if score #d2 jv = #d5 jv if score #d3 jv = #d4 jv if score #d1 jv = #d7 jv if score #d2 jv = #d8 jv if score #d3 jv = #d9 jv run function %se/zag' % NS)
        f = self.fn('e/zag')
        f.append('execute if score #e1 jv matches 0 if score #e2 jv matches 0 run return 0')
        f.append(self.hit('zag'))
        # 복붙
        for i in range(1, 5):
            main.append('execute if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv run function %se/cp%d' % (i, i + 3, i + 1, i + 4, i + 2, i + 5, NS, i))
            f = self.fn('e/cp%d' % i)
            f.append('execute if score #e%d jv matches 0 if score #e%d jv matches 0 run return 0' % (i, i + 1))
            if i == 1:
                f.append('execute if score #d4 jv = #d7 jv if score #d5 jv = #d8 jv if score #d6 jv = #d9 jv run return run ' + self.up('spam'))
            f.append(self.up('copy'))
        for i in (1, 2):
            main.append('execute ' + ' '.join('if score #d%d jv = #d%d jv' % (i + t, i + 4 + t) for t in range(4)) + ' run function %se/ph%d' % (NS, i))
            f = self.fn('e/ph%d' % i)
            f.append('execute if score #e%d jv matches 0 if score #e%d jv matches 0 if score #e%d jv matches 0 run return 0' % (i, i + 1, i + 2))
            f.append(self.hitu('phone'))
        for i, j in ((1, 5), (1, 6), (1, 7), (2, 6), (2, 7), (3, 7)):
            main.append('execute if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv run function %se/ag%d' % (i, j, i + 1, j + 1, i + 2, j + 2, NS, i))
        for i in (1, 2, 3):
            f = self.fn('e/ag%d' % i)
            f.append('execute if score #e%d jv matches 0 if score #e%d jv matches 0 run return 0' % (i, i + 1))
            f.append(self.hitu('again'))

    # =====================================================================
    # 트라이 (자리별 숫자 조각 찾기)
    # =====================================================================
    def add_str(self, s, action, pos=None):
        """s가 pos(없으면 모든 자리)에서 시작하면 action(p) → 명령 목록"""
        self.trie.append((s, action, pos))

    def collect_strings(self):
        self.trie = []
        H = self.H
        stamp_any = {}    # 합체용 도장이 필요한 조각 → 합체 족보들
        for h in self.real:
            e = h['eng']
            if e and e[0] == 'all':
                for p in e[1]:
                    stamp_any.setdefault(p, []).append(h['key'])
        self.stamp_any = stamp_any
        # 합체 확인 함수
        for h in self.real:
            e = h['eng']
            if e and e[0] == 'all':
                f = self.fn('e/k_%s' % h['key'])
                f.append('execute ' + ' '.join('if score #f_%s jv = #gen jv' % p for p in e[1]) +
                         ' unless score #g%d jv = #gen jv run %s' % (self.id(h['key']), self.hit(h['key'])))
        twice = {}        # 조각 → 두 번 족보 key
        for h in self.real:
            e = h['eng']
            if e and e[0] == 'twice':
                twice[e[1]] = h['key']
        region = set(c for c, _, _ in HM.REG)
        done_strings = set()

        def frag_action(key, s):
            def act(p, key=key, s=s):
                out = [self.act(key)]
                return out
            return act
        for h in self.real:
            e = h['eng']
            if not e:
                continue
            k = h['key']
            if e[0] == 'frag':
                for s in e[1]:
                    self.add_str(s, frag_action(k, s))
            elif e[0] == 'start':
                self.add_str(e[1], frag_action(k, e[1]), pos=1)
            elif e[0] == 'end':
                self.add_str(e[1], frag_action(k, e[1]), pos=10 - len(e[1]))
        # 합체용 도장 + 확인
        for s, combos in stamp_any.items():
            def act(p, s=s, combos=combos):
                out = ['scoreboard players operation #f_%s jv = #gen jv' % s]
                for ck in combos:
                    out.append('function %se/k_%s' % (NS, ck))
                return out
            self.add_str(s, act)
        # 두 번
        for s, k in twice.items():
            def act(p, s=s, k=k):
                L = len(s)
                out = []
                if p - L >= 1:
                    out.append('execute if score #S2_%s jv = #gen jv if score #P2_%s jv matches ..%d run %s' % (s, s, p - L, self.act(k)))
                out.append('execute unless score #S2_%s jv = #gen jv run scoreboard players set #P2_%s jv %d' % (s, s, p))
                out.append('scoreboard players operation #S2_%s jv = #gen jv' % s)
                return out
            self.add_str(s, act)
        # 지역번호 개수
        for s in sorted(region):
            def act(p, s=s):
                return ['function %se/rg' % NS]
            self.add_str(s, act)
        f = self.fn('e/rg')
        f.append('execute unless score #S_rgc jv = #gen jv run scoreboard players set #x_rg jv 0')
        f.append('scoreboard players operation #S_rgc jv = #gen jv')
        f.append('scoreboard players add #x_rg jv 1')
        f.append('execute if score #x_rg jv matches 2 run ' + self.up('rg2'))
        f.append('execute if score #x_rg jv matches 3.. run ' + self.up('rg3'))
        # 자리 고정 족보
        self.add_str('78', lambda p: [self.hit('p78')], pos=7)
        for k in range(2, 7):
            self.add_str('9' * k, (lambda p, k=k: [self.up('l9_%d' % k)]), pos=1)
            self.add_str('0' * k, (lambda p, k=k: [self.up('l0_%d' % k)]), pos=1)
        for k in range(2, 8):
            self.add_str('0' * k, (lambda p, k=k: [self.up('t0_%d' % k)]), pos=10 - k)
        # 한 자리 족보
        self.single = {(1, 6): [self.hit('e6')], (1, 1): [self.hit('f1')], (5, 2): [self.hit('m2')]}
        # 출발·도착 합체
        starts = sorted(set(h['eng'][1] for h in self.real if h['eng'] and h['eng'][0] == 'se'))
        for st in starts:
            self.add_str(st, (lambda p, st=st: ['scoreboard players operation #fs_%s jv = #gen jv' % st]), pos=1)
        for h in self.real:
            if h['eng'] and h['eng'][0] == 'se':
                _, st, en = h['eng']
                self.add_str(en, (lambda p, st=st, k=h['key']: ['execute if score #fs_%s jv = #gen jv run %s' % (st, self.hit(k))]), pos=10 - len(en))
        # 낱말 + 모양 합체
        for h in self.real:
            if h['eng'] and h['eng'][0] == 'wr3':
                key = h['key']
                self.add_str(h['eng'][1], (lambda p, key=key: ['execute if score #x_S jv matches 1.. if score #x_mr jv matches 3.. unless score #g%d jv = #gen jv run %s' % (self.id(key), self.hit(key))]))
        # 2씩·3씩 계단
        for step, grp in ((2, 'st2'), (3, 'st3')):
            keys = self.groups[grp]
            for ln in range(3, 3 + len(keys)):
                for a in range(10):
                    for sg in (1, -1):
                        ds = [a + sg * step * t for t in range(ln)]
                        if all(0 <= x <= 9 for x in ds):
                            self.add_str(''.join(map(str, ds)), (lambda p, key=keys[ln - 3]: [self.up(key)]))
        # 토끼(피보나치)
        keys = self.groups['fib']
        for ln in (4, 5, 6):
            for a in range(10):
                for b in range(10):
                    if a == 0 and b == 0:
                        continue
                    ds = [a, b]
                    while len(ds) < ln and ds[-1] + ds[-2] <= 9:
                        ds.append(ds[-1] + ds[-2])
                    if len(ds) == ln:
                        self.add_str(''.join(map(str, ds)), (lambda p, key=keys[ln - 4]: [self.up(key)]))
        # 키패드 테두리
        cyc = [1, 2, 3, 6, 9, 8, 7, 4]
        keys = self.groups['border']
        for ln in (6, 7, 8):
            for st in range(8):
                for sg in (1, -1):
                    ds = [cyc[(st + sg * t) % 8] for t in range(ln)]
                    self.add_str(''.join(map(str, ds)), (lambda p, key=keys[ln - 6]: [self.up(key)]))
        # 산수
        for a in range(10):
            for b in range(10):
                if a * b >= 10:
                    self.add_str('%d%d%02d' % (a, b, a * b), lambda p: [self.hitu('mul')])
            if a * a >= 10:
                self.add_str('%d%02d' % (a, a * a), lambda p: [self.hitu('sq')])
        # 물구나무 (6↔9가 들어간 180도 대칭 4자리)
        rot = {0: 0, 1: 1, 8: 8, 6: 9, 9: 6}
        for a in rot:
            for b in rot:
                if a in (6, 9) or b in (6, 9):
                    self.add_str('%d%d%d%d' % (a, b, rot[b], rot[a]), lambda p: [self.hitu('flip')])
        # 뚜벅이: 키패드에서 붙어 있는 두 숫자
        R = [3, 0, 0, 0, 1, 1, 1, 2, 2, 2]
        Cc = [1, 0, 1, 2, 0, 1, 2, 0, 1, 2]
        for a in range(10):
            for b in range(10):
                if abs(R[a] - R[b]) + abs(Cc[a] - Cc[b]) == 1:
                    def act(p):
                        if p == 1:
                            return ['scoreboard players operation #S_kw jv = #gen jv', 'scoreboard players set #x_kw jv 1']
                        if p < 8:
                            return ['execute if score #S_kw jv = #gen jv if score #x_kw jv matches %d run scoreboard players set #x_kw jv %d' % (p - 1, p)]
                        return ['execute if score #S_kw jv = #gen jv if score #x_kw jv matches 7 run ' + self.hit('walk')]
                    self.add_str('%d%d' % (a, b), act)

    def build_dispatch(self, main):
        # 자리 p, 숫자 v 잎 + 그 아래 트라이
        for p in range(1, 10):
            main.append('function %se/p%d' % (NS, p))
            d = self.fn('e/p%d' % p)
            # 이 자리에서 시작할 수 있는 조각들
            strs = {}
            for s, action, pos in self.trie:
                if pos is not None and pos != p:
                    continue
                if p + len(s) - 1 > 9:
                    continue
                strs.setdefault(s, []).append(action)
            prefixes = set()
            for s in strs:
                for L in range(1, len(s) + 1):
                    prefixes.add(s[:L])

            def node_lines(pre):
                out = []
                for action in strs.get(pre, []):
                    out.extend(action(p))
                kids = sorted(x for x in prefixes if len(x) == len(pre) + 1 and x.startswith(pre))
                for kd in kids:
                    out.append('execute if score #d%d jv matches %s run return run function %se/t%d_%s' % (p + len(pre), kd[-1], NS, p, kd))
                    self.fn('e/t%d_%s' % (p, kd)).extend(node_lines(kd))
                return out
            for v in range(10):
                d.append('execute if score #d%d jv matches %d run return run function %se/p%d_%d' % (p, v, NS, p, v))
                f = self.fn('e/p%d_%d' % (p, v))
                f.append('scoreboard players add #q%d jv 1' % v)
                f.append('scoreboard players operation #x_mx jv > #q%d jv' % v)
                f.append('execute if score #q%d jv matches 1 run scoreboard players add #x_nd jv 1' % v)
                if v % 2:
                    f.append('scoreboard players add #x_pm jv %d' % (1 << (p - 1)))
                if v == p:
                    f.append('scoreboard players add #x_pl jv 1')
                f.extend(self.single.get((p, v), []))
                if p == 3:
                    f.append('execute if score #d6 jv matches %d if score #d9 jv matches %d run function %se/ticket' % ((v + 1) % 10, (v + 2) % 10, NS))
                    f.append('execute if score #d6 jv matches %d if score #d9 jv matches %d run function %se/ticket' % ((v - 1) % 10, (v - 2) % 10, NS))
                    f.append('execute if score #d6 jv matches %d if score #d9 jv matches %d run function %se/serv' % ((2 * v) % 10, (3 * v) % 10, NS))
                if p == 9:
                    f.append('scoreboard players operation #x_t jv = #d3 jv')
                    f.append('scoreboard players operation #x_t jv += #d6 jv')
                    f.append('execute if score #x_t jv matches %d run function %se/vsum' % (v, NS))
                    f.append('execute if score #x_t jv matches %d run function %se/vsum' % (v + 10, NS))
                f.extend(node_lines(str(v)))
        # 세 자리 묶음 계산
        blk = self.fn('e/blk')
        for nm, a in (('ba', 1), ('bb', 4), ('bc', 7)):
            blk.append('scoreboard players operation #x_%s jv = #d%d jv' % (nm, a))
            blk.append('scoreboard players operation #x_%s jv *= %s' % (nm, self.c(10)))
            blk.append('scoreboard players operation #x_%s jv += #d%d jv' % (nm, a + 1))
            blk.append('scoreboard players operation #x_%s jv *= %s' % (nm, self.c(10)))
            blk.append('scoreboard players operation #x_%s jv += #d%d jv' % (nm, a + 2))
        f = self.fn('e/vsum')
        f.append('function %se/blk' % NS)
        f.append('scoreboard players operation #x_w jv = #x_ba jv')
        f.append('scoreboard players operation #x_w jv += #x_bb jv')
        f.append('execute if score #x_ba jv matches 100.. if score #x_bb jv matches 100.. if score #x_bc jv matches 100.. if score #x_w jv = #x_bc jv run ' + self.hitu('vsum'))
        f = self.fn('e/ticket')
        f.append('function %se/blk' % NS)
        f.append('scoreboard players operation #x_w jv = #x_bb jv')
        f.append('scoreboard players operation #x_w jv -= #x_ba jv')
        f.append('scoreboard players operation #x_u jv = #x_bc jv')
        f.append('scoreboard players operation #x_u jv -= #x_bb jv')
        f.append('execute if score #x_w jv matches 1 if score #x_u jv matches 1 run ' + self.hitu('ticket'))
        f.append('execute if score #x_w jv matches -1 if score #x_u jv matches -1 run ' + self.hitu('ticket'))
        f = self.fn('e/serv')
        f.append('function %se/blk' % NS)
        f.append('scoreboard players operation #x_w jv = #x_ba jv')
        f.append('scoreboard players operation #x_w jv += #x_ba jv')
        f.append('scoreboard players operation #x_u jv = #x_w jv')
        f.append('scoreboard players operation #x_u jv += #x_ba jv')
        f.append('execute if score #x_ba jv matches 1.. if score #x_w jv = #x_bb jv if score #x_u jv = #x_bc jv run ' + self.hitu('serv'))

    # =====================================================================
    # 개수로 보는 족보
    # =====================================================================
    def build_counts(self, main):
        z = lambda *vs: ' '.join('if score #q%d jv matches 0' % v for v in vs)
        main.append('execute if score #q0 jv matches 0 run function %se/z0' % NS)
        f = self.fn('e/z0')
        f.append(self.hit('no0'))
        f.append('execute %s run function %se/high' % (z(1, 2, 3, 4), NS))
        f.append('execute %s run %s' % (z(1, 2, 4, 5, 7, 8), self.hit('s369')))
        f.append('execute %s run %s' % (z(2, 3, 5, 6, 8, 9), self.hit('line')))
        f.append('execute %s run %s' % (z(4, 5, 6, 7, 8, 9), self.hit('row')))
        f.append('execute %s run %s' % (z(1, 2, 3, 7, 8, 9), self.hit('row')))
        f.append('execute %s run %s' % (z(1, 2, 3, 4, 5, 6), self.hit('row')))
        h = self.fn('e/high')
        h.append('execute %s %srun return run %s' % (z(5, 6, 7), self.open('hi8'), self.hit('hi8')))
        h.append('execute %s %srun return run %s' % (z(5, 6), self.open('hi7'), self.hit('hi7')))
        h.append('execute %s %srun return run %s' % (z(5), self.open('hi6'), self.hit('hi6')))
        h.append(self.hit('hi5'))
        main.append('execute %s run function %se/low' % (z(9, 8, 7, 6, 5), NS))
        lo = self.fn('e/low')
        lo.append('execute %s %srun return run %s' % (z(4, 3, 2), self.open('lo1'), self.hit('lo1')))
        lo.append('execute %s %srun return run %s' % (z(4, 3), self.open('lo2'), self.hit('lo2')))
        lo.append('execute %s %srun return run %s' % (z(4), self.open('lo3'), self.hit('lo3')))
        lo.append(self.hit('lo4'))
        main.append('execute %s run %s' % (z(1, 2, 3, 4, 5, 7), self.hit('hole')))
        main.append('execute if score #q1 jv matches 0 run ' + self.hit('no1'))
        main.append('execute if score #q1 jv matches 1.. if score #q2 jv matches 0 run ' + self.hit('only1'))
        main.append('execute if score #q4 jv matches 0 run function %se/z4' % NS)
        f = self.fn('e/z4')
        f.append(self.hit('no4'))
        f.append('execute %s run %s' % (z(3, 7), self.hit('flipok')))
        main.append('execute if score #q0 jv matches 4.. run ' + self.hit('z4'))
        main.append('execute if score #q7 jv matches 3.. run function %se/seven' % NS)
        f = self.fn('e/seven')
        f.append('execute if score #q7 jv matches 7.. %srun return run %s' % (self.open('c7x7'), self.hit('c7x7')))
        f.append(self.hit('s7'))
        main.append('execute if score #q4 jv matches 4.. run ' + self.hit('f4'))
        main.append('execute if score #q3 jv matches 3 run ' + self.hit('t3'))
        main.append('execute if score #q1 jv matches 1 if score #q2 jv matches 2 run ' + self.hit('i1i2'))
        main.append('execute if score #q9 jv matches 4 if score #q1 jv matches 1 run ' + self.hit('g941'))
        # 같은 숫자 개수 사다리
        f = self.fn('e/l_cnt')
        f.append('execute if score #x_mx jv matches 8 %srun return run %s' % (self.open('cnt8'), self.hit('cnt8')))
        for k in (7, 6, 5, 4):
            f.append('execute if score #x_mx jv matches %d.. %srun return run %s' % (k, self.open('cnt%d' % k), self.hit('cnt%d' % k)))
        main.append('execute if score #x_mx jv matches 4.. run function %se/cnt' % NS)
        f = self.fn('e/cnt')
        f.append('execute if score #q6 jv matches 6.. run ' + self.hit('c6x6'))
        f.append('function %se/l_cnt' % NS)
        # 종류 수
        main.append('execute if score #x_nd jv matches ..5 run function %se/nd_lo' % NS)
        main.append('execute if score #x_nd jv matches 8.. run function %se/nd_hi' % NS)
        f = self.fn('e/nd_hi')
        f.append('execute if score #x_nd jv matches 8 run return run ' + self.hit('nd8'))
        f.append('execute if score #q0 jv matches 0 %srun return run %s' % (self.open('pan'), self.hit('pan')))
        f.append(self.hit('nd9'))
        f = self.fn('e/nd_lo')
        f.append('execute if score #x_nd jv matches 5 run function %se/nd5' % NS)
        f.append('execute if score #x_nd jv matches 4 run ' + self.hit('nd4'))
        f.append('execute if score #x_nd jv matches 3 run function %se/nd3' % NS)
        f.append('execute if score #x_nd jv matches 2 run function %se/nd2' % NS)
        f.append('execute if score #x_mx jv matches 3.. run function %se/top' % NS)
        f.append('execute if score #x_nd jv matches 2..4 run function %se/nosolo' % NS)
        # 숫자값 하네: 나온 숫자 v는 딱 v개
        conds = ['if score #q0 jv matches 0']
        for v in range(1, 10):
            conds.append('unless score #q%d jv matches 1..%d' % (v, v - 1) if v > 1 else '')
            conds.append('unless score #q%d jv matches %d..' % (v, v + 1))
        f.append('execute ' + ' '.join(x for x in conds if x) + ' run ' + self.hit('self'))
        g = self.fn('e/nd5')
        g.append(self.hit('nd5'))
        g.append('scoreboard players set #x_t jv 0')
        for v in range(10):
            g.append('execute if score #q%d jv matches 2 run scoreboard players add #x_t jv 1' % v)
        g.append('execute if score #x_t jv matches 4 run ' + self.hit('bus'))
        g = self.fn('e/nd3')
        g.append(self.hit('nd3'))
        g.append('execute if score #x_mx jv matches 3 run ' + self.hit('rps'))
        g = self.fn('e/nd2')
        g.append(self.hit('nd2'))
        g.append('execute if score #q0 jv matches 1.. if score #q9 jv matches 1.. run ' + self.hit('ext'))
        g = self.fn('e/top')
        g.append('scoreboard players set #x_t jv 0')
        for v in range(10):
            g.append('execute if score #q%d jv matches 3.. run scoreboard players add #x_t jv 1' % v)
        g.append('execute if score #x_t jv matches 2.. run function %se/top2' % NS)
        g = self.fn('e/top2')
        # 했던 말 또 하고
        for i in range(1, 5):
            g.append('scoreboard players set #x_t jv 0')
            for j in range(i + 2, 9):
                g.append('execute unless score #e%d jv matches 0 if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv run scoreboard players add #x_t jv 1' % (i, i, j, i + 1, j + 1))
            g.append('execute if score #x_t jv matches 2.. unless score #g%d jv = #gen jv run %s' % (self.id('nag'), self.hit('nag')))
        g.append('scoreboard players set #x_t jv 0')
        for v in range(10):
            g.append('execute if score #q%d jv matches 4.. run scoreboard players add #x_t jv 1' % v)
        g.append('execute if score #x_t jv matches 2.. %srun return run %s' % (self.open('rival'), self.hit('rival')))
        g.append(self.hit('top2'))
        g = self.fn('e/nosolo')
        g.append('scoreboard players set #x_t jv 0')
        for v in range(10):
            g.append('execute if score #q%d jv matches 1 run scoreboard players add #x_t jv 1' % v)
        g.append('execute if score #x_t jv matches 0 run ' + self.hit('nosolo'))
        # 홀짝
        main.append('execute if score #x_pm jv matches ..3 run function %se/par_e' % NS)
        main.append('execute if score #x_pm jv matches 127 run ' + self.up('odd7'))
        main.append('execute if score #x_pm jv matches 128 run ' + self.up('evn7'))
        main.append('execute if score #x_pm jv matches 170 run ' + self.hit('par'))
        main.append('execute if score #x_pm jv matches 254..255 run ' + self.up('odd7'))
        main.append('execute if score #x_pm jv matches 256..257 run ' + self.up('evn7'))
        main.append('execute if score #x_pm jv matches 341 run ' + self.hit('par'))
        main.append('execute if score #x_pm jv matches 383 run ' + self.up('odd7'))
        main.append('execute if score #x_pm jv matches 384 run ' + self.up('evn7'))
        main.append('execute if score #x_pm jv matches 508.. run function %se/par_o' % NS)
        f = self.fn('e/par_e')
        f.append('execute if score #x_pm jv matches 0 run ' + self.up('evn9'))
        f.append(self.up('evn7'))
        f = self.fn('e/par_o')
        f.append('execute if score #x_pm jv matches 511 run ' + self.up('odd9'))
        f.append(self.up('odd7'))
        # 합
        main.append('scoreboard players operation #x_t jv = #q0 jv')
        main.append('scoreboard players operation #x_t jv += #q1 jv')
        main.append('execute if score #x_t jv matches 5.. run function %se/sumlo' % NS)
        main.append('scoreboard players operation #x_t jv = #q8 jv')
        main.append('scoreboard players operation #x_t jv += #q9 jv')
        main.append('execute if score #x_t jv matches 5.. run function %se/sumhi' % NS)
        sm = self.fn('e/sum')
        sm.append('scoreboard players operation #x_sum jv = #d1 jv')
        for i in range(2, 10):
            sm.append('scoreboard players operation #x_sum jv += #d%d jv' % i)
        f = self.fn('e/sumlo')
        f.append('function %se/sum' % NS)
        f.append('execute if score #x_sum jv matches ..4 %srun return run %s' % (self.open('sum4'), self.hit('sum4')))
        f.append('execute if score #x_sum jv matches ..9 run ' + self.hit('sum9'))
        f = self.fn('e/sumhi')
        f.append('function %se/sum' % NS)
        f.append('execute if score #x_sum jv matches 77.. %srun return run %s' % (self.open('sum77'), self.hit('sum77')))
        f.append('execute if score #x_sum jv matches 72.. run ' + self.hit('sum72'))
        # 제자리
        f = self.fn('e/l_place')
        for k in (7, 6, 5, 4):
            f.append('execute if score #x_pl jv matches %d.. %srun return run %s' % (k, self.open('pl%d' % k), self.hit('pl%d' % k)))
        main.append('execute if score #x_pl jv matches 4.. run function %se/l_place' % NS)
        # 박쥐
        main.append('execute if score #d5 jv matches 0..8 %s run function %se/bat' % (z(2, 3, 4, 5, 7), NS))
        f = self.fn('e/bat')
        f.append('execute if score #d5 jv matches 2..7 run return 0')
        f.append('scoreboard players set #x_t jv 0')
        for a, b in ((1, 9), (2, 8), (3, 7), (4, 6)):
            # 짝이 맞는가: (0,0)(1,1)(8,8)(6,9)(9,6)
            f.append('scoreboard players set #x_u jv 0')
            for u, w in ((0, 0), (1, 1), (8, 8)):
                f.append('execute if score #d%d jv matches %d if score #d%d jv matches %d run scoreboard players set #x_u jv 1' % (a, u, b, w))
            for u, w in ((6, 9), (9, 6)):
                f.append('execute if score #d%d jv matches %d if score #d%d jv matches %d run scoreboard players set #x_u jv 2' % (a, u, b, w))
            f.append('execute if score #x_u jv matches 0 run return 0')
            f.append('execute if score #x_u jv matches 2 run scoreboard players set #x_t jv 1')
        f.append('execute if score #x_t jv matches 1 run ' + self.hit('bat'))

    # =====================================================================
    # 대칭 사다리
    # =====================================================================
    def build_pal(self, main):
        f = self.fn('e/l_pal')
        f.append('execute if score #x_pal jv matches 9.. %srun return run function %se/pal9' % (self.open('pal9'), NS))
        for k in (8, 7, 6, 5, 4):
            f.append('execute if score #x_pal jv matches %d.. %srun return run %s' % (k, self.open('pal%d' % k), self.hit('pal%d' % k)))
        g = self.fn('e/pal9')
        g.append(self.hit('pal9'))
        g.append('execute if score #x_nd jv matches 2 run ' + self.hit('panda'))
        main.append('execute if score #x_pal jv matches 4.. run function %se/l_pal' % NS)

    # =====================================================================
    # 전체 조립
    # =====================================================================
    def build_eval(self):
        m = self.fn('eval')
        m.append('scoreboard players add #gen jv 1')
        m.append('scoreboard players set #nh jv 0')
        m.append('scoreboard players set #bt jv -1')
        for i in range(1, 9):
            m.append('scoreboard players operation #e%d jv = #d%d jv' % (i, i + 1))
            m.append('scoreboard players operation #e%d jv -= #d%d jv' % (i, i))
        m.append('scoreboard players set #x_pal jv 0')
        m.append('scoreboard players set #x_S jv 0')
        for i in range(1, 9):
            m.append('execute if score #e%d jv matches 0 run scoreboard players add #x_S jv %d' % (i, 1 << (i - 1)))
        m.append('execute if score #x_S jv matches 1.. run function %se/s_root' % NS)
        m.append('scoreboard players set #x_Y jv 0')
        for i in range(1, 8):
            m.append('execute if score #d%d jv = #d%d jv run scoreboard players add #x_Y jv %d' % (i, i + 2, 1 << (i - 1)))
        m.append('execute if score #x_Y jv matches 1.. run function %se/y_root' % NS)
        self.build_s()
        self.build_y()
        self.build_lines(m)
        for v in range(10):
            m.append('scoreboard players set #q%d jv 0' % v)
        for nm in ('x_mx', 'x_nd', 'x_pm', 'x_pl'):
            m.append('scoreboard players set #%s jv 0' % nm)
        self.collect_strings()
        self.build_dispatch(m)
        self.build_counts(m)
        m.append('execute if score #x_S jv matches 1.. run function %se/s_res' % NS)
        m.append('execute if score #x_Y jv matches 1.. run function %se/y_res' % NS)
        self.build_pal(m)
        self.build_upgrade()
        return m


# =====================================================================
# 빛나는 자리(marks) — 화면에 보여 줄 때만 쓰는 느린 길
#   hand/mprep  : 현재 #d1..#d9 로 #e, #q, #r(홀짝) 준비
#   hand/mk/clr : #mk1..9 = 0      hand/m/<id> : 족보 하나의 자리 표시(#mk)
#   hand/mk/merge : #mk 가 1인 자리의 #lc 를 #ml 이상으로
# =====================================================================
import re as _re


def _split_top(expr):
    parts, depth, cur, q = [], 0, '', False
    for ch in expr:
        if ch == '"':
            q = not q
        if not q:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == '|' and depth == 0:
                parts.append(cur.strip())
                cur = ''
                continue
        cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def _span_fn(self, a, L):
    name = 'mk/s%d_%d' % (a, L)
    if 'hand/' + name not in self.F:
        f = self.fn(name)
        for i in range(a, a + L):
            f.append('scoreboard players set #mk%d jv 1' % i)
    return 'function %s%s' % (NS, name)


def _mask_fn(self, mask):
    name = 'mk/k%d' % mask
    if 'hand/' + name not in self.F:
        f = self.fn(name)
        for i in range(9):
            if mask >> i & 1:
                f.append('scoreboard players set #mk%d jv 1' % (i + 1))
    return 'function %s%s' % (NS, name)


def _dig_conds(p, s):
    return ' '.join('if score #d%d jv matches %s' % (p + i, ch) for i, ch in enumerate(s))


def build_marks(self):
    pre = self.fn('mprep')
    for i in range(1, 9):
        pre.append('scoreboard players operation #e%d jv = #d%d jv' % (i, i + 1))
        pre.append('scoreboard players operation #e%d jv -= #d%d jv' % (i, i))
    for v in range(10):
        pre.append('scoreboard players set #q%d jv 0' % v)
    for p in range(1, 10):
        for v in range(10):
            pre.append('execute if score #d%d jv matches %d run scoreboard players add #q%d jv 1' % (p, v, v))
        pre.append('scoreboard players operation #r%d jv = #d%d jv' % (p, p))
        pre.append('scoreboard players operation #r%d jv %%= %s' % (p, self.c(2)))
    clr = self.fn('mk/clr')
    mg = self.fn('mk/merge')
    for i in range(1, 10):
        clr.append('scoreboard players set #mk%d jv 0' % i)
        mg.append('execute if score #mk%d jv matches 1 run scoreboard players operation #lc%d jv > #ml jv' % (i, i))
    grow = self.fn('mk/grow')
    for i in range(1, 9):
        grow.append('execute if score #mk%d jv matches 1 if score #e%d jv matches 0 run scoreboard players set #mk%d jv 1' % (i, i, i + 1))
    for i in range(8, 0, -1):
        grow.append('execute if score #mk%d jv matches 1 if score #e%d jv matches 0 run scoreboard players set #mk%d jv 1' % (i + 1, i, i))
    cge = self.fn('mk/cge')
    ceq = self.fn('mk/ceq')
    dig = self.fn('mk/dig')
    for p in range(1, 10):
        for v in range(10):
            cge.append('execute if score #d%d jv matches %d if score #q%d jv >= #mt jv run scoreboard players set #mk%d jv 1' % (p, v, v, p))
            ceq.append('execute if score #d%d jv matches %d if score #q%d jv = #mt jv run scoreboard players set #mk%d jv 1' % (p, v, v, p))
        dig.append('execute if score #d%d jv = #mt jv run scoreboard players set #mk%d jv 1' % (p, p))
    sub = [0]

    def newsub(hid):
        sub[0] += 1
        return 'm/x%d_%d' % (hid, sub[0])

    def all_occ(f, strings):
        for s in strings:
            for p in range(1, 10 - len(s) + 1):
                f.append('execute %s run %s' % (_dig_conds(p, s), _span_fn(self, p, len(s))))

    def fib_strings(k):
        out = []
        for a in range(10):
            for b in range(10):
                if a == 0 and b == 0:
                    continue
                ds = [a, b]
                while len(ds) < k and ds[-1] + ds[-2] <= 9:
                    ds.append(ds[-1] + ds[-2])
                if len(ds) == k:
                    out.append(''.join(map(str, ds)))
        return out

    def border_strings(k):
        cyc = [1, 2, 3, 6, 9, 8, 7, 4]
        return [''.join(str(cyc[(st + sg * t) % 8]) for t in range(k)) for st in range(8) for sg in (1, -1)]

    def term(f, hid, t):
        t = t.strip()
        m = _re.fullmatch(r'ALL9', t)
        if m:
            f.append(_mask_fn(self, 511)); return
        if _re.fullmatch(r'\d+', t):
            f.append(_mask_fn(self, int(t))); return
        m = _re.fullmatch(r'span\((\d+),(\d+)\)', t)
        if m:
            f.append(_span_fn(self, int(m.group(1)) + 1, int(m.group(2)))); return
        m = _re.fullmatch(r'MHAS\("([0-9|]+)"\)', t)
        if m:
            strs = m.group(1).split('|')
            name = newsub(hid)
            g = self.fn(name)
            for p in range(1, 10):
                for s in strs:
                    if p + len(s) - 1 <= 9:
                        g.append('execute %s run return run %s' % (_dig_conds(p, s), _span_fn(self, p, len(s))))
            f.append('function %s%s' % (NS, name)); return
        m = _re.fullmatch(r'MALL\("([0-9]+)"\)', t)
        if m:
            all_occ(f, [m.group(1)]); return
        m = _re.fullmatch(r'mrun_e\(x,(-?\d+),(-?\d+),(\d+)\)', t)
        if m:
            lo, hi, k = int(m.group(1)), int(m.group(2)), int(m.group(3))
            rng = '%d' % lo if lo == hi else '%d..%d' % (lo, hi)
            for p in range(1, 10 - k + 1):
                f.append('execute ' + ' '.join('if score #e%d jv matches %s' % (i, rng) for i in range(p, p + k - 1)) + ' run ' + _span_fn(self, p, k))
            return
        m = _re.fullmatch(r'mrunsge\(x,(\d+)\)', t)
        if m:
            k = int(m.group(1))
            for p in range(1, 10 - k + 1):
                f.append('execute ' + ' '.join('if score #e%d jv matches 0' % i for i in range(p, p + k - 1)) + ' run ' + _span_fn(self, p, k))
            return
        m = _re.fullmatch(r'm(chain|train)\(x,(\d+)\)', t)
        if m:
            k = int(m.group(2))
            for p in range(1, 10 - 2 * k + 1):
                eq = ' '.join('if score #e%d jv matches 0' % (p + 2 * j) for j in range(k))
                if m.group(1) == 'chain':
                    ne = ' '.join('unless score #e%d jv matches 0' % (p + 2 * j + 1) for j in range(k - 1))
                    f.append('execute %s %s run %s' % (eq, ne, _span_fn(self, p, 2 * k)))
                else:
                    for sg in (1, -1):
                        st = ' '.join('if score #e%d jv matches %d' % (p + 2 * j + 1, sg) for j in range(k - 1))
                        f.append('execute %s %s run %s' % (eq, st, _span_fn(self, p, 2 * k)))
            return
        if t == 'mlook(x)':
            for i in range(1, 9):
                for j in range(i + 2, 9):
                    for k in range(i + 1, j):
                        f.append('execute if score #e%d jv matches 0 if score #e%d jv matches 0 if score #d%d jv = #d%d jv unless score #e%d jv matches 0 run %s' % (i, j, i, j, k, _mask_fn(self, (3 << (i - 1)) | (3 << (j - 1)))))
            return
        if t == 'msg2(x)':
            for p in range(1, 6):
                f.append('execute if score #e%d jv matches 0 if score #e%d jv matches 0 unless score #e%d jv matches 0 if score #e%d jv matches 0 run %s' % (p, p + 1, p + 2, p + 3, _span_fn(self, p, 5)))
                f.append('execute if score #e%d jv matches 0 unless score #e%d jv matches 0 if score #e%d jv matches 0 if score #e%d jv matches 0 run %s' % (p, p + 1, p + 2, p + 3, _span_fn(self, p, 5)))
            f.append('function %smk/grow' % NS)
            return
        if t == 'mfish(x)':
            for p in range(1, 5):
                f.append('execute if score #e%d jv matches 0 unless score #e%d jv matches 0 if score #e%d jv matches 0 unless score #e%d jv matches 0 if score #e%d jv matches 0 if score #d%d jv = #d%d jv run %s' % (
                    p, p + 1, p + 2, p + 3, p + 4, p, p + 4, _span_fn(self, p, 6)))
            return
        if t == 'mmaca(x)':
            for p in range(1, 6):
                f.append('execute unless score #e%d jv matches 0 if score #e%d jv matches 0 if score #e%d jv matches 0 unless score #e%d jv matches 0 if score #d%d jv = #d%d jv run %s' % (
                    p, p + 1, p + 2, p + 3, p, p + 4, _span_fn(self, p, 5)))
            return
        if t == 'mfat(x)':
            for p in range(1, 3):
                f.append('execute if score #e%d jv matches 0 if score #e%d jv matches 0 unless score #e%d jv matches 0 if score #e%d jv matches 0 unless score #e%d jv matches 0 if score #e%d jv matches 0 if score #e%d jv matches 0 if score #d%d jv = #d%d jv run %s' % (
                    p, p + 1, p + 2, p + 3, p + 4, p + 5, p + 6, p, p + 5, _span_fn(self, p, 8)))
            return
        m = _re.fullmatch(r'mcnt_(ge|eq)\(x,(\d+)\)', t)
        if m:
            f.append('scoreboard players set #mt jv %s' % m.group(2))
            f.append('function %smk/c%s' % (NS, m.group(1)))
            return
        m = _re.fullmatch(r'mdig\(x,(\d+)\)', t)
        if m:
            f.append('scoreboard players set #mt jv %s' % m.group(1))
            f.append('function %smk/dig' % NS)
            return
        m = _re.fullmatch(r'mblink\(x,(\d+)\)', t)
        if m:
            tt = int(m.group(1))
            for p in range(1, 10 - 2 * (tt - 1)):
                conds = []
                for j in range(tt - 1):
                    a = p + 2 * j
                    conds.append('if score #d%d jv = #d%d jv unless score #e%d jv matches 0' % (a, a + 2, a))
                mask = 0
                for j in range(tt):
                    mask |= 1 << (p + 2 * j - 1)
                f.append('execute %s run %s' % (' '.join(conds), _mask_fn(self, mask)))
            return
        m = _re.fullmatch(r'malt\(x,(\d+)\)', t)
        if m:
            k = int(m.group(1))
            for p in range(1, 10 - k + 1):
                conds = ' '.join('if score #d%d jv = #d%d jv' % (i, i + 2) for i in range(p, p + k - 2))
                f.append('execute %s unless score #e%d jv matches 0 run %s' % (conds, p, _span_fn(self, p, k)))
            return
        m = _re.fullmatch(r'moddrun\(x,(\d),(\d+)\)', t)
        if m:
            par, k = int(m.group(1)), int(m.group(2))
            for p in range(1, 10 - k + 1):
                f.append('execute ' + ' '.join('if score #r%d jv matches %d' % (i, par) for i in range(p, p + k)) + ' run ' + _span_fn(self, p, k))
            return
        m = _re.fullmatch(r'mpat_e\(x,P_(\w+),(\d+)\)', t)
        if m:
            pat = {'HILL2': [1, 1, -1, -1], 'HILL3': [1, 1, 1, -1, -1, -1], 'PIT2': [-1, -1, 1, 1], 'PIT3': [-1, -1, -1, 1, 1, 1]}[m.group(1)]
            L = len(pat)
            for p in range(1, 9 - L + 1):
                f.append('execute ' + ' '.join('if score #e%d jv matches %d' % (p + i, pat[i]) for i in range(L)) + ' run ' + _span_fn(self, p, L + 1))
            return
        m = _re.fullmatch(r'mpal\(x,(\d+)\)', t)
        if m:
            L = int(m.group(1))
            for p in range(1, 10 - L + 1):
                conds = ' '.join('if score #d%d jv = #d%d jv' % (p + i, p + L - 1 - i) for i in range(L // 2))
                for k in range(p, p + L - 1):
                    f.append('execute %s unless score #e%d jv matches 0 run %s' % (conds, k, _span_fn(self, p, L)))
            return
        if t == 'mflip4(x)':
            rot = {0: 0, 1: 1, 8: 8, 6: 9, 9: 6}
            strs = ['%d%d%d%d' % (a, b, rot[b], rot[a]) for a in rot for b in rot if a in (6, 9) or b in (6, 9)]
            all_occ(f, strs); return
        if t == 'magain(x)':
            for i in range(1, 4):
                for j in range(i + 4, 8):
                    f.append('execute if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv unless score #e%d jv matches 0 run %s' % (i, j, i + 1, j + 1, i + 2, j + 2, i, _mask_fn(self, (7 << (i - 1)) | (7 << (j - 1)))))
                    f.append('execute if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv unless score #e%d jv matches 0 run %s' % (i, j, i + 1, j + 1, i + 2, j + 2, i + 1, _mask_fn(self, (7 << (i - 1)) | (7 << (j - 1)))))
            return
        if t == 'mcopy(x)':
            for i in range(1, 5):
                for k in (i, i + 1):
                    f.append('execute if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv unless score #e%d jv matches 0 run %s' % (i, i + 3, i + 1, i + 4, i + 2, i + 5, k, _span_fn(self, i, 6)))
            return
        if t == 'mphone(x)':
            for i in (1, 2):
                for k in (i, i + 1, i + 2):
                    f.append('execute ' + ' '.join('if score #d%d jv = #d%d jv' % (i + u, i + 4 + u) for u in range(4)) + ' unless score #e%d jv matches 0 run %s' % (k, _span_fn(self, i, 8)))
            return
        if t == 'nag(x)':
            for i in range(1, 9):
                f.append('scoreboard players set #x_t jv 0')
                for j in range(1, 9):
                    f.append('execute if score #d%d jv = #d%d jv if score #d%d jv = #d%d jv run scoreboard players add #x_t jv 1' % (i, j, i + 1, j + 1))
                f.append('execute unless score #e%d jv matches 0 if score #x_t jv matches 3.. run %s' % (i, _span_fn(self, i, 2)))
            return
        if t == 'mplace(x)':
            for i in range(1, 10):
                f.append('execute if score #d%d jv matches %d run scoreboard players set #mk%d jv 1' % (i, i, i))
            return
        if t in ('mmul(x)', 'msq(x)', 'madd(x)'):
            strs = []
            for a in range(10):
                for b in range(10):
                    if t == 'mmul(x)' and a * b >= 10:
                        strs.append('%d%d%02d' % (a, b, a * b))
                    if t == 'madd(x)' and a + b >= 10:
                        strs.append('%d%d%02d' % (a, b, a + b))
                if t == 'msq(x)' and a * a >= 10:
                    strs.append('%d%02d' % (a, a * a))
            all_occ(f, strs); return
        m = _re.fullmatch(r'mfib\(x,(\d+)\)', t)
        if m:
            all_occ(f, fib_strings(int(m.group(1)))); return
        m = _re.fullmatch(r'mborder\(x,(\d+)\)', t)
        if m:
            all_occ(f, border_strings(int(m.group(1)))); return
        if t == 'mregion(x)':
            all_occ(f, [c for c, _, _ in HM.REG]); return
        raise ValueError('marks: ' + t)

    for h in self.real:
        hid = self.id(h['key'])
        f = self.fn('m/%d' % hid)
        exprs = [h['mk']] + [a['mk'] for a in self.all if a['eng'] and a['eng'][0] == 'alias' and a['eng'][1] == h['key']]
        for ex in exprs:
            for t in _split_top(ex):
                term(f, hid, t)


Engine.build_marks = build_marks
