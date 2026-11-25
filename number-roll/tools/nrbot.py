"""숫자 굴리기 시험용 가짜 플레이어 (로컬 26.3 서버, 오프라인 모드).

steve-eokka/tools/bot.py 의 기본 봇에 채팅·액션바·대화상자·소리·제목·보스바 읽기와 명령 보내기를 더했다.
"""
import json, os, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'steve-eokka', 'tools'))
MCSRV = os.environ.get('MCSRV', '/home/claude/mcsrv')
import bot as _bot
_bot.REPORT = MCSRV + '/reports/out/reports/packets.json'
from bot import Bot, varint, string

REG = json.load(open(MCSRV + '/reports/out/reports/registries.json'))
ENT = {v['protocol_id']: k.replace('minecraft:', '') for k, v in REG['minecraft:entity_type']['entries'].items()}
SND = {v['protocol_id']: k.replace('minecraft:', '') for k, v in REG['minecraft:sound_event']['entries'].items()}


def mutf(raw):
    """자바식 UTF-8 (이모지가 대리 쌍으로 들어 있음) → 글"""
    try:
        return raw.decode('utf-8', 'surrogatepass').encode('utf-16', 'surrogatepass').decode('utf-16', 'replace')
    except Exception:
        return raw.decode('utf-8', 'replace')


def nbt_payload(b, t):
    if t == 0: return None
    if t == 1: return b.fmt('>b')[0]
    if t == 2: return b.fmt('>h')[0]
    if t == 3: return b.fmt('>i')[0]
    if t == 4: return b.fmt('>q')[0]
    if t == 5: return b.fmt('>f')[0]
    if t == 6: return b.fmt('>d')[0]
    if t == 7: n = b.fmt('>i')[0]; return list(b.take(n))
    if t == 8: n = b.fmt('>H')[0]; return mutf(b.take(n))
    if t == 9:
        et = b.fmt('>b')[0]; n = b.fmt('>i')[0]; return [nbt_payload(b, et) for _ in range(n)]
    if t == 10:
        out = {}
        while True:
            tt = b.fmt('>b')[0]
            if tt == 0: return out
            n = b.fmt('>H')[0]; k = mutf(b.take(n)); out[k] = nbt_payload(b, tt)
    if t == 11: n = b.fmt('>i')[0]; return [b.fmt('>i')[0] for _ in range(n)]
    if t == 12: n = b.fmt('>i')[0]; return [b.fmt('>q')[0] for _ in range(n)]
    raise ValueError('nbt tag %d' % t)


def nbt(b):
    return nbt_payload(b, b.fmt('>b')[0])


def flat(c):
    """글자 조각 → 그냥 글"""
    if c is None: return ''
    if isinstance(c, str): return c
    if isinstance(c, list): return ''.join(flat(x) for x in c)
    if isinstance(c, dict):
        if set(c) == {''}: return flat(c[''])
        s = c.get('text', '')
        if 'translate' in c: s += '{' + c['translate'] + '}'
        return s + flat(c.get('extra'))
    return str(c)


class NrBot(Bot):
    def __init__(self, name='tester', **kw):
        self.dialogs = []; self.cleared = 0; self.chat = []; self.bar = []; self.sounds = []; self.titles = []; self.subs = []
        self.boss = {}; self.errs = []; self.CB = None; self.rawchat = []; self.entities = {}
        super().__init__(name, **kw)

    def _packet(self):
        pid, b = super()._packet()
        try:
            if self.state == 'play':
                if self.CB is None:
                    self.CB = {v: k[2] for k, v in self.ID.items() if k[0] == 'play' and k[1] == 'c'}
                name = self.CB.get(pid); i0 = b.i
                if name == 'add_entity':
                    eid = b.varint(); b.take(16); et = b.varint(); x, y, z = b.fmt('>ddd')
                    self.entities[eid] = (ENT.get(et, et), x, y, z)
                elif name == 'remove_entities':
                    for _ in range(b.varint()): self.entities.pop(b.varint(), None)
                elif name == 'show_dialog':
                    hid = b.varint()
                    self.dialogs.append(nbt(b) if hid == 0 else {'registry_id': hid - 1})
                elif name == 'clear_dialog': self.cleared += 1
                elif name == 'system_chat':
                    c = nbt(b); overlay = b.take(1) != b'\x00'
                    (self.bar if overlay else self.chat).append(flat(c))
                    if not overlay: self.rawchat.append(c)
                elif name == 'set_action_bar_text': self.bar.append(flat(nbt(b)))
                elif name == 'set_title_text': self.titles.append(flat(nbt(b)))
                elif name == 'set_subtitle_text': self.subs.append(flat(nbt(b)))
                elif name == 'sound':
                    sid = b.varint()
                    self.sounds.append(SND.get(sid - 1, sid) if sid else b.string().replace('minecraft:', ''))
                elif name == 'boss_event':
                    uid = b.take(16).hex(); act = b.varint()
                    if act == 0:
                        t = flat(nbt(b)); (hp,) = b.fmt('>f'); self.boss[uid] = [t, hp]
                    elif act == 1: self.boss.pop(uid, None)
                    elif act == 2 and uid in self.boss: self.boss[uid][1] = b.fmt('>f')[0]
                    elif act == 3 and uid in self.boss: self.boss[uid][0] = flat(nbt(b))
                b.i = i0
        except Exception as e:
            self.errs.append(repr(e)); b.i = 0; b.varint()
        return pid, b

    def find(self, kind, x, y, z, r=1.5):
        best = None
        for eid, (t, ex, ey, ez) in self.entities.items():
            if t != kind: continue
            d = ((ex - x) ** 2 + (ey - y) ** 2 + (ez - z) ** 2) ** 0.5
            if d <= r and (best is None or d < best[1]): best = (eid, d)
        return best[0] if best else None

    def interact(self, eid, hand=0, sneak=False):
        """엔티티 우클릭 (26.3: 번호, 손, 맞은 자리(압축 벡터), 웅크림)"""
        self._send('play', 'interact', varint(eid) + varint(hand) + b'\x00' + (b'\x01' if sneak else b'\x00'))

    def command(self, text):
        self._send('play', 'chat_command', string(text))

    def trig(self, n, obj='jb.menu'):
        self.command('trigger %s set %d' % (obj, n))


if __name__ == '__main__':
    b = NrBot(); print('joined', b.wait_joined(), b.kicked); time.sleep(2)
    print(b.chat[:5], b.bar[-1:], b.titles[-2:], b.boss, b.errs[:3]); b.close()
