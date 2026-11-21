"""One picture of everything that is installed: the five maps in a row (smallest to largest), the lobby from the spawn and from above.
usage: python3 overview.py <out.png> [scale]   (reads out3/canvas/*.pkl and out3/maps.json)"""
import sys, os, json, pickle
sys.path.insert(0, '/home/claude/bw/gen3')
from PIL import Image, ImageDraw, ImageFont
import preview
from canvas import Canvas
ROOT = '/home/claude/bw'
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(sz): return ImageFont.truetype(FONT, sz, index=1)
def load(i):
    cv = Canvas(1); cv.b = pickle.load(open(f'{ROOT}/out3/canvas/{i}.pkl', 'rb'))['b']; return cv
def main(out, s=2):
    info = [r for r in json.load(open(f'{ROOT}/out3/maps.json', encoding='utf-8')) if not r.get('empty')]
    steps = ['가장 작은 거', '조금 작은 거', '중간', '조금 큰 거', '가장 큰 거']
    maps = []
    for k, r in enumerate(info[1:]):
        im = preview.iso2(load(r['id']), s, 0, 2.2); maps.append((f"{r['name']} {r['size'][0]}x{r['size'][2]} ({steps[k]})", im))
    lob = load('lobby')
    lf = preview.front(lob, 2 * s + 1, zmin=-60, zmax=40); li = preview.iso2(lob, s + 1, 0, 2.2)
    pad = 16; lab = 34
    W = sum(im.width for _, im in maps) + pad * (len(maps) + 1); H1 = max(im.height for _, im in maps) + lab + pad
    lf.thumbnail((W * 0.48, 2000)); li.thumbnail((W * 0.34, 2000))
    H2 = max(lf.height, li.height) + lab + pad
    img = Image.new('RGB', (W, H1 + H2 + pad), (18, 20, 28)); d = ImageDraw.Draw(img); x = pad
    for t, im in maps:
        d.text((x, 8), t, fill=(255, 214, 90), font=font(20)); img.paste(im, (x, lab + (H1 - lab - pad - im.height) // 2)); x += im.width + pad
    d.text((pad, H1 + 6), '로비 (스폰에서 본 모습 / 위에서 본 모습) — 왼쪽 숲 속 오두막이 업그레이드 가게', fill=(255, 214, 90), font=font(20))
    img.paste(lf, (pad, H1 + lab)); img.paste(li, (W - li.width - pad, H1 + lab))
    img.save(out); print(out, img.size)
if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
