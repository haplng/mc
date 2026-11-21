"""Preview of what changed in v7: each team base cut open at head height with the two shopkeepers drawn in, and the lobby's upgrade shop."""
import sys, pickle, importlib
sys.path.insert(0, '/home/claude/bw/gen3')
from PIL import Image, ImageDraw, ImageFont
import preview
from canvas import Canvas
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(sz): return ImageFont.truetype(FONT, sz, index=1)
BASES = [('m01_tea', 'cup_base', '티타임 — 찻잔 벽 안쪽 틈', 2), ('m02_chess', 'rook_base', '체스 — 탑 벽 아래 홈', 2), ('m03_circus', 'tent_base', '서커스 — 천막 안 매표소', 2),
         ('m06_library', 'book_base', '도서관 — 책장 벽감', 2), ('m09_solar', 'planet_base', '태양계 — 돔 안 기둥 사이', 2)]
def base_cut(mod, fn, top, rot, s):
    cv = getattr(importlib.import_module(mod), fn)('red')
    out = Canvas(1)
    for (x, y, z), b in cv.b.items():
        if -2 <= y <= top and abs(x) <= 14 and -15 <= z <= 12: out.b[(x, y, z)] = b
    for (x, y, z), t in cv.ents:
        tags = [str(v) for v in t['Tags']]
        if 'bw.shop' in tags or 'bw.upgrade' in tags:
            px, py, pz = int(x // 1), int(y // 1), int(z // 1)
            col = 'light_blue' if 'bw.shop' in tags else 'magenta'
            for dy in range(4): out.b[(px, py + dy, pz)] = col + '_concrete'
            out.b[(px, py + 4, pz)] = 'white_concrete'
    return preview.iso2(out, s, rot, 2.2)
def hall(cut, rot, s):
    b = pickle.load(open('/home/claude/bw/out3/canvas/lobby.pkl', 'rb'))['b']; out = Canvas(1)
    for (x, y, z), v in b.items():
        if -31 <= x <= -8 and 15 <= z <= 29 and 0 <= y <= 14 and not (cut and y >= 4 and -30 <= x <= -16):
            if 'leaves' in v or ('log' in v and not (-29 <= x <= -17 and 17 <= z <= 27)): continue      # hide the trees around it
            out.b[(x, y, z)] = v
    if cut:
        for dy in range(4): out.b[(-25, 1 + dy, 22)] = 'yellow_concrete'
        out.b[(-25, 5, 22)] = 'white_concrete'
    return preview.iso2(out, s, rot, 2.2)
def main(outp, rot=0):
    S = 9; pad = 14; lab = 34
    ims = [(t, base_cut(m, f, top, rot, S)) for m, f, t, top in BASES]
    h1 = [('로비 업그레이드 가게 (스폰 광장 서쪽)', hall(False, 1, 11)), ('안쪽 — 계산대 뒤에 업그레이드 NPC', hall(True, 1, 11))]
    W = max(sum(i.width for _, i in ims) + pad * (len(ims) + 1), sum(i.width for _, i in h1) + pad * 3)
    H1 = max(i.height for _, i in ims) + lab; H2 = max(i.height for _, i in h1) + lab
    img = Image.new('RGB', (W, H1 + H2 + pad * 3 + 30), (18, 20, 28)); d = ImageDraw.Draw(img)
    x = pad
    for t, im in ims:
        d.text((x, pad), t, fill=(255, 214, 90), font=font(19)); img.paste(im, (x, pad + lab)); x += im.width + pad
    d.text((pad, pad + H1 + 4), '기지를 2칸 높이에서 잘라 본 모습 (빨강팀).  하늘색 기둥 = 아이템 상점 NPC 자리,  분홍 기둥 = 팀 업그레이드 NPC 자리,  노란 기둥 = 로비 업그레이드 NPC 자리', fill=(200, 205, 215), font=font(17))
    x = pad; y = H1 + pad * 2 + 30
    for t, im in h1:
        d.text((x, y), t, fill=(255, 214, 90), font=font(19)); img.paste(im, (x, y + lab)); x += im.width + pad * 3
    img.save(outp); print(outp, img.size)
if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
