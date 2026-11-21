"""A minimal fake player for the local 26.3 test server (offline mode, no compression, protocol 777).

It logs in, answers keep-alives and teleports, and can look around, pick a hotbar slot, right-click and sneak.
Everything else the server sends is skipped unread. Packet ids come from the game's own reports/packets.json.
"""
import json, os, socket, struct, threading, time, uuid
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

REPORT = ROOT + '/server/reports/out/reports/packets.json'
PROTOCOL = 777


def _ids():
    p = json.load(open(REPORT)); out = {}
    for st in p:
        for d in p[st]:
            for k, v in p[st][d].items(): out[(st, d[0], k.replace('minecraft:', ''))] = v['protocol_id']
    return out


def varint(n):
    n &= 0xFFFFFFFF; b = b''
    while True:
        c = n & 0x7F; n >>= 7
        if n: b += bytes([c | 0x80])
        else: return b + bytes([c])


def string(s):
    e = s.encode('utf-8'); return varint(len(e)) + e


class Buf:
    def __init__(self, data): self.d = data; self.i = 0
    def varint(self):
        n = 0; shift = 0
        while True:
            c = self.d[self.i]; self.i += 1
            n |= (c & 0x7F) << shift; shift += 7
            if not c & 0x80: break
        return n - (1 << 32) if n & (1 << 31) else n
    def take(self, n):
        b = self.d[self.i:self.i + n]; self.i += n; return b
    def fmt(self, f):
        return struct.unpack(f, self.take(struct.calcsize(f)))
    def string(self): return self.take(self.varint()).decode('utf-8', 'replace')


class Bot:
    def __init__(self, name='tester', host='127.0.0.1', port=25565):
        self.ID = _ids(); self.name = name
        self.s = socket.create_connection((host, port), timeout=30)
        self.state = 'handshake'; self.alive = True; self.joined = False
        self.pos = None; self.rot = (0.0, 0.0); self.seq = 0; self.kicked = None; self.seen = {}
        self.lock = threading.Lock()
        self._send('handshake', 'intention', varint(PROTOCOL) + string(host) + struct.pack('>H', port) + varint(2))
        self.state = 'login'
        self._send('login', 'hello', string(name) + uuid.uuid4().bytes)
        self.t = threading.Thread(target=self._loop, daemon=True); self.t.start()

    # ---- wire
    def _send(self, st, name, payload=b''):
        body = varint(self.ID[(st, 's', name)]) + payload
        with self.lock: self.s.sendall(varint(len(body)) + body)

    def _read(self, n):
        b = b''
        while len(b) < n:
            c = self.s.recv(n - len(b))
            if not c: raise ConnectionError('closed')
            b += c
        return b

    def _packet(self):
        n = 0; shift = 0
        while True:
            c = self._read(1)[0]; n |= (c & 0x7F) << shift; shift += 7
            if not c & 0x80: break
        b = Buf(self._read(n)); return b.varint(), b

    def _loop(self):
        I = self.ID
        try:
            while self.alive:
                pid, b = self._packet()
                st = self.state
                self.seen[(st, pid)] = self.seen.get((st, pid), 0) + 1
                if st == 'login':
                    if pid == I[('login', 'c', 'login_finished')]:
                        self._send('login', 'login_acknowledged'); self.state = 'configuration'
                    elif pid == I[('login', 'c', 'login_disconnect')]:
                        self.kicked = b.d[b.i:].decode('utf-8', 'replace'); break
                    elif pid == I[('login', 'c', 'login_compression')]:
                        raise RuntimeError('server wants compression; set network-compression-threshold=-1')
                elif st == 'configuration':
                    if pid == I[('configuration', 'c', 'select_known_packs')]:
                        self._send('configuration', 'select_known_packs', varint(0))
                    elif pid == I[('configuration', 'c', 'keep_alive')]:
                        self._send('configuration', 'keep_alive', b.take(8))
                    elif pid == I[('configuration', 'c', 'ping')]:
                        self._send('configuration', 'pong', b.take(4))
                    elif pid == I[('configuration', 'c', 'finish_configuration')]:
                        self._send('configuration', 'finish_configuration'); self.state = 'play'
                    elif pid == I[('configuration', 'c', 'disconnect')]:
                        self.kicked = repr(b.d[b.i:][:200]); break
                else:
                    if pid == I[('play', 'c', 'keep_alive')]:
                        self._send('play', 'keep_alive', b.take(8))
                    elif pid == I[('play', 'c', 'ping')]:
                        self._send('play', 'pong', b.take(4))
                    elif pid == I[('play', 'c', 'player_position')]:
                        tid = b.varint(); x, y, z, vx, vy, vz, yr, xr = b.fmt('>ddddddff'); (flags,) = b.fmt('>i')
                        px, py, pz = self.pos or (0.0, 0.0, 0.0); ry, rx = self.rot
                        x = px + x if flags & 1 else x; y = py + y if flags & 2 else y; z = pz + z if flags & 4 else z
                        yr = ry + yr if flags & 8 else yr; xr = rx + xr if flags & 16 else xr
                        self.pos = (x, y, z); self.rot = (yr, xr)
                        # 26.3: the confirmation carries the position and rotation the client ended up with
                        self._send('play', 'accept_teleportation', varint(tid) + struct.pack('>dddff', x, y, z, yr, xr))
                        # no separate position packet: 26.3 kicks a client that sends two positions in one tick
                        if not self.joined:
                            self.joined = True; self._send('play', 'player_loaded')
                    elif pid == I[('play', 'c', 'chunk_batch_finished')]:
                        self._send('play', 'chunk_batch_received', struct.pack('>f', 20.0))
                    elif pid == I[('play', 'c', 'disconnect')]:
                        self.kicked = repr(b.d[b.i:][:300]); break
        except Exception as e:
            if self.alive: self.kicked = self.kicked or f'{type(e).__name__}: {e}'
        self.alive = False

    # ---- actions
    def wait_joined(self, timeout=20):
        t = time.time()
        while time.time() - t < timeout:
            if self.joined or not self.alive: break
            time.sleep(0.05)
        return self.joined

    def look(self, yaw, pitch):
        self.rot = (yaw, pitch); self._send('play', 'move_player_rot', struct.pack('>ffb', yaw, pitch, 1))

    def slot(self, n): self._send('play', 'set_carried_item', struct.pack('>h', n))

    def use(self):
        self.seq += 1
        self._send('play', 'use_item', varint(0) + varint(self.seq) + struct.pack('>ff', *self.rot))

    def sneak(self, on): self._send('play', 'player_input', bytes([0x20 if on else 0]))

    def close(self):
        self.alive = False
        try: self.s.close()
        except Exception: pass


if __name__ == '__main__':
    b = Bot(); ok = b.wait_joined(); print('joined', ok, 'kicked', b.kicked, 'pos', b.pos)
    time.sleep(1); print('pos', b.pos, 'alive', b.alive, 'kicked', b.kicked); b.close()
