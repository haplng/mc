"""Tiny RCON client for the local 26.3 test server (see tools/server.sh)."""
import socket, struct, sys, time


class Rcon:
    def __init__(self, host='127.0.0.1', port=25575, password='ekqatest', timeout=20):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.rid = 0
        self._send(3, password)
        rid, typ, body = self._recv()
        if rid == -1: raise RuntimeError('rcon login refused')

    def _send(self, typ, body):
        self.rid += 1
        data = struct.pack('<ii', self.rid, typ) + body.encode('utf-8') + b'\x00\x00'
        self.s.sendall(struct.pack('<i', len(data)) + data)
        return self.rid

    def _read(self, n):
        buf = b''
        while len(buf) < n:
            chunk = self.s.recv(n - len(buf))
            if not chunk: raise RuntimeError('rcon closed')
            buf += chunk
        return buf

    def _recv(self):
        (ln,) = struct.unpack('<i', self._read(4))
        data = self._read(ln)
        rid, typ = struct.unpack('<ii', data[:8])
        return rid, typ, data[8:-2].decode('utf-8', 'replace')

    def cmd(self, command):
        """Run one command and return the text the server answered with.

        The server reads exactly one packet per socket read and drops the connection if two arrive together,
        so never send a second packet before the first one is answered. Long answers come in 4096-byte pieces.
        """
        self._send(2, command)
        out = ''
        while True:
            r, typ, body = self._recv()
            out += body
            if len(body.encode('utf-8')) < 4000: break
            self.s.settimeout(0.3)
            try:
                peek = self.s.recv(1, socket.MSG_PEEK)
            except (socket.timeout, BlockingIOError):
                peek = b''
            finally:
                self.s.settimeout(20)
            if not peek: break
        return out

    def score(self, name, obj='ek'):
        t = self.cmd(f'scoreboard players get {name} {obj}')
        # "... has 12 [ek]" / "Can't get value ..."
        import re
        m = re.search(r' has (-?\d+) ', t)
        return int(m.group(1)) if m else None

    def close(self):
        try: self.s.close()
        except Exception: pass


def connect(retries=60):
    last = None
    for _ in range(retries):
        try: return Rcon()
        except Exception as e:
            last = e; time.sleep(1)
    raise last


if __name__ == '__main__':
    r = connect()
    for c in sys.argv[1:]:
        print('>', c); print(r.cmd(c))
