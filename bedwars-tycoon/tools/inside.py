"""Elevation of a base seen from inside, looking at the wall where a shopkeeper stands.
usage: python3 inside.py <module> <base fn> <out.png> [dye]"""
import sys, importlib
sys.path.insert(0, '/home/claude/bw/gen3')
import numpy as np
from PIL import Image, ImageDraw
import preview

def view(cv, npc, side, S=22, halfw=7, ymax=8):
    """look from the middle of the room towards the wall on `side` (-1: -x, +1: +x); npc = marker cell"""
    nx, ny, nz = npc
    W = 2 * halfw + 1; H = ymax + 2
    img = Image.new('RGB', (W * S, H * S), (150, 190, 235)); d = ImageDraw.Draw(img)
    xs = range(nx + side * 6, nx - side * 5, -side)            # far -> near (towards the room centre)
    def px(z, y):
        col = (z - (nz - halfw)) if side < 0 else ((nz + halfw) - z)      # looking at -x: z grows to the left? keep +z to the right for -x view mirrored below
        return col * S, (H - 1 - (y + 1)) * S
    for x in xs:
        depth = abs(x - nx)
        for z in range(nz - halfw, nz + halfw + 1):
            for y in range(-1, ymax + 1):
                s = cv.get(x, y, z)
                if not s: continue
                n = s.split('[')[0]
                if n in ('light', 'barrier'): continue
                c = np.array(preview.colour(n), float)
                shade = 1.0 - 0.07 * min(depth, 6) if abs(x) <= abs(nx) + 1 or True else 1
                c = tuple(int(v * shade) for v in c)
                X, Y = px(z, y)
                box = [X, Y, X + S - 1, Y + S - 1]
                if n.endswith('_carpet'): box = [X, Y + S - 3, X + S - 1, Y + S - 1]
                elif 'slab' in n and 'type=top' in s: box = [X, Y, X + S - 1, Y + S // 2]
                elif 'slab' in n: box = [X, Y + S // 2, X + S - 1, Y + S - 1]
                elif 'glass' in n:
                    d.rectangle(box, outline=c, width=2); continue
                elif 'lantern' in n or 'chain' in n or 'fence' in n or n.endswith('_pane'): box = [X + S // 3, Y, X + S - 1 - S // 3, Y + S - 1]
                d.rectangle(box, fill=c, outline=tuple(int(v * 0.8) for v in c))
        if x == nx:                                              # the villager, drawn at its depth
            X, Y = px(nz, ny)
            d.rectangle([X + 5, Y - S + 12, X + S - 6, Y + S - 1], fill=(92, 62, 44), outline=(40, 30, 20))          # robe
            d.rectangle([X + 4, Y - S + 1, X + S - 5, Y - S + 12], fill=(190, 140, 110), outline=(60, 40, 30))        # head
            d.rectangle([X + S // 2 - 2, Y - S + 8, X + S // 2 + 1, Y - S + 14], fill=(150, 100, 80))                 # nose
            d.text((X - 14, Y - S - 13), 'NPC name', fill=(255, 255, 255))
    for i in range(W): d.line([i * S, 0, i * S, H * S], fill=(0, 0, 0, 40))
    return img

if __name__ == '__main__':
    mod = importlib.import_module(sys.argv[1]); dye = sys.argv[4] if len(sys.argv) > 4 else 'red'
    cv = getattr(mod, sys.argv[2])(dye)
    mk = {}
    for (x, y, z), t in cv.ents:
        tags = [str(v) for v in t['Tags']]
        for k in ('bw.shop', 'bw.upgrade'):
            if k in tags: mk[k] = (int(x // 1), int(y // 1), int(z // 1))
    a = view(cv, mk['bw.shop'], -1); b = view(cv, mk['bw.upgrade'], 1)
    out = Image.new('RGB', (a.width + b.width + 10, a.height), (20, 20, 28)); out.paste(a, (0, 0)); out.paste(b, (a.width + 10, 0))
    out.save(sys.argv[3]); print(sys.argv[3], out.size, mk)
