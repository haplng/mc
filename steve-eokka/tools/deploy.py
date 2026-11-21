"""Zip the generated pack into the test server's world, reload it there and print whatever the server complains about."""
import os, sys, time, zipfile
import os as _os; ROOT = _os.environ.get('EK_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live import Live

SRC = ROOT + '/out/eokka'
DST = ROOT + '/server/run/world/datapacks/eokka.zip'

def pack():
    tmp = DST + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(SRC):
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, SRC))
    os.replace(tmp, DST)

def main():
    pack()
    L = Live(); L.log()
    L.cmd('reload')
    time.sleep(2.5)
    L.step(5)
    bad = L.problems()
    print('reloaded;', len(bad), 'complaints')
    for l in bad[:40]: print('  ', l[:400])
    return L

if __name__ == '__main__':
    main()
