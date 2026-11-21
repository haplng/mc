"""Fake player for the bed wars tests: the plain bot plus entity tracking, right-clicking an entity, and reading the dialogs,
chat lines and sounds the server sends."""
import sys, json, struct, time, threading
sys.path.insert(0, '/home/claude/mc/tools')
import bot as _bot
from bot import Bot, Buf, varint, string

REG = json.load(open('/home/claude/mcsrv/reports/out/reports/registries.json'))
ENT = {v['protocol_id']: k.replace('minecraft:', '') for k, v in REG['minecraft:entity_type']['entries'].items()}
SND = {v['protocol_id']: k.replace('minecraft:', '') for k, v in REG['minecraft:sound_event']['entries'].items()}
ITEM = {v['protocol_id']: k.replace('minecraft:', '') for k, v in REG['minecraft:item']['entries'].items()}

def nbt_payload(b, t):
    if t == 0: return None
    if t == 1: return b.fmt('>b')[0]
    if t == 2: return b.fmt('>h')[0]
    if t == 3: return b.fmt('>i')[0]
    if t == 4: return b.fmt('>q')[0]
    if t == 5: return b.fmt('>f')[0]
    if t == 6: return b.fmt('>d')[0]
    if t == 7: n = b.fmt('>i')[0]; return list(b.take(n))
    if t == 8: n = b.fmt('>H')[0]; return b.take(n).decode('utf-8', 'replace')
    if t == 9:
        et = b.fmt('>b')[0]; n = b.fmt('>i')[0]; return [nbt_payload(b, et) for _ in range(n)]
    if t == 10:
        out = {}
        while True:
            tt = b.fmt('>b')[0]
            if tt == 0: return out
            n = b.fmt('>H')[0]; k = b.take(n).decode('utf-8', 'replace'); out[k] = nbt_payload(b, tt)
    if t == 11: n = b.fmt('>i')[0]; return [b.fmt('>i')[0] for _ in range(n)]
    if t == 12: n = b.fmt('>i')[0]; return [b.fmt('>q')[0] for _ in range(n)]
    raise ValueError(f'nbt tag {t}')

def nbt(b):
    """network NBT: a tag id and its payload, no name"""
    return nbt_payload(b, b.fmt('>b')[0])

def flat(c):
    """plain text of a text component (sprites become [sprite name])"""
    if c is None: return ''
    if isinstance(c, str): return c
    if isinstance(c, list): return ''.join(flat(x) for x in c)
    if isinstance(c, dict):
        if set(c) == {''}: return flat(c[''])                 # a bare string inside a list of compounds travels wrapped like this
        s = c.get('text', '')
        if 'sprite' in c: s += '[' + c['sprite'].split('/')[-1] + ']'
        if 'translate' in c: s += '{' + c['translate'] + '}'
        return s + flat(c.get('extra'))
    return str(c)

class BwBot(Bot):
    def __init__(self, name='tester', **kw):
        self.entities = {}; self.dialogs = []; self.cleared = 0; self.chat = []; self.sounds = []; self.raw = {}
        self._wrap()
        super().__init__(name, **kw)

    def _wrap(self):
        self.CB = None
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
                elif name == 'set_health':
                    (hp,) = b.fmt('>f'); self.health = hp
                    if hp <= 0: self._send('play', 'client_command', varint(0)); self.deaths = getattr(self, 'deaths', 0) + 1
                elif name == 'system_chat':
                    c = nbt(b); overlay = b.take(1) != b'\x00'
                    self.chat.append(('bar ' if overlay else '') + flat(c))
                elif name == 'sound':
                    sid = b.varint()
                    self.sounds.append(SND.get(sid - 1, sid) if sid else 'direct')
                b.i = i0
        except Exception as e:
            self.raw.setdefault('errors', []).append(repr(e)); b.i = 0; b.varint() if False else None
        return pid, b

    def find(self, kind, x, y, z, r=1.5):
        best = None
        for eid, (t, ex, ey, ez) in self.entities.items():
            if t != kind: continue
            d = ((ex - x) ** 2 + (ey - y) ** 2 + (ez - z) ** 2) ** 0.5
            if d <= r and (best is None or d < best[1]): best = (eid, d)
        return best[0] if best else None

    def interact(self, eid, hand=0, sneak=False):
        """right-click an entity (26.3: id, hand, where on it as a compact vector, sneaking)"""
        self._send('play', 'interact', varint(eid) + varint(hand) + b'\x00' + (b'\x01' if sneak else b'\x00'))

    def command(self, text):
        self._send('play', 'chat_command', string(text))

if __name__ == '__main__':
    b = BwBot(); print('joined', b.wait_joined(), b.kicked); time.sleep(2)
    print(len(b.entities), list(b.entities.items())[:5], b.chat[:5]); b.close()
