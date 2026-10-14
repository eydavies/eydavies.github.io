#!/usr/bin/env python3
"""Build The Local Group mini-site (pixel art). Run from anywhere:

    python3 local-group/build.py

Which university hosts the NEXT meeting, and when, lives in next-meeting.json:

    {"campus": "harvard", "date": "November 18"}        campus: harvard | mit | bu

Edit that file, re-run this script, then commit the regenerated index.html (and the
other pages). To preview another campus without touching the file:

    python3 local-group/build.py --campus mit --date "December 9" --out /tmp/preview

The season (fall foliage, snow, spring blossom, summer green) is chosen in the visitor's
browser from today's date in Boston, so nobody has to rebuild the site when the months
change: Dec-Feb winter, Mar-May spring, Jun-Aug summer, Sep-Nov fall. To preview a season,
open the page with ?season=winter (or spring, summer, fall) on the end of the address.

Everything on the map is drawn on a pixel grid by this script (1 SVG unit = 1 art
pixel) so that the buildings, people and speech bubble stay crisp at any size.
"""
import argparse, datetime, json, math, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description="Build The Local Group pages.")
ap.add_argument("--campus", help="override next-meeting.json: harvard, mit or bu")
ap.add_argument("--date", help='override next-meeting.json, e.g. "November 18"')
ap.add_argument("--out", help="write the pages here instead of next to this script")
ARGS = ap.parse_args()
OUT = pathlib.Path(ARGS.out) if ARGS.out else HERE
OUT.mkdir(parents=True, exist_ok=True)
NEXT = json.loads((HERE / "next-meeting.json").read_text(encoding="utf-8"))
if ARGS.campus: NEXT["campus"] = ARGS.campus
if ARGS.date: NEXT["date"] = ARGS.date

W, H = 380, 226            # scene size in art pixels
VIEW = f"0 0 {W} {H}"
COMPACT_VIEW = "46 0 288 226"   # tall, narrow screens (phones) crop the empty sides
OL = '#2b2438'             # outline colour
SEASON_BY_MONTH = {12: 'winter', 1: 'winter', 2: 'winter', 3: 'spring', 4: 'spring', 5: 'spring',
                   6: 'summer', 7: 'summer', 8: 'summer', 9: 'fall', 10: 'fall', 11: 'fall'}
BUILD_SEASON = SEASON_BY_MONTH[datetime.date.today().month]   # only a fallback: season.js decides in the browser

# ------------------------------------------------------------------ helpers
class Grid:
    def __init__(s): s.p = {}
    def px(s, x, y, c): s.p[(x, y)] = c
    def rect(s, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): s.p[(x, y)] = c
    def vline(s, x, y0, y1, c): s.rect(x, y0, x, y1, c)
    def hline(s, y, x0, x1, c): s.rect(x0, y, x1, y, c)
    def sym(s, x0, y0, x1, y1, c):          # rect mirrored about x = 0 (x0..x1 given on the right side)
        s.rect(x0, y0, x1, y1, c); s.rect(-x1, y0, -x0, y1, c)
    def disc(s, cx, cy, rx, ry, c, cond=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 and (cond is None or cond(x, y)):
                    s.p[(x, y)] = c
    def outline(s, c):
        s.pre = dict(s.p)                    # the shape before its outline, used to lay snow on top surfaces
        new = {}
        for (x, y) in s.p:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in s.p: new[q] = c
        s.p.update(new)
    def bbox(s):
        xs = [k[0] for k in s.p]; ys = [k[1] for k in s.p]
        return min(xs), min(ys), max(xs), max(ys)

def svg_paths(grid):
    """One <path> per colour, merged into horizontal runs. A colour starting with '.' is a CSS class."""
    rows = {}
    for (x, y), c in grid.p.items(): rows.setdefault(c, {}).setdefault(y, []).append(x)
    out = []
    for c, ys in rows.items():
        d = []
        for y in sorted(ys):
            xs = sorted(ys[y]); start = prev = xs[0]
            for x in xs[1:] + [None]:
                if x is not None and x == prev + 1: prev = x; continue
                d.append(f"M{start} {y}h{prev - start + 1}v1h-{prev - start + 1}z")
                if x is not None: start = prev = x
        attr = f'class="{c[1:]}"' if c.startswith('.') else f'fill="{c}"'
        out.append(f'<path {attr} d="{"".join(d)}"/>')
    return "\n\t\t\t\t\t".join(out)

# ------------------------------------------------------------------ river
RIVER_Y, AMP, PERIOD, HALF = 113, 4, 64, 10
def yc(x): return RIVER_Y + math.floor(AMP * math.sin(2 * math.pi * x / PERIOD) + 0.5)

X0, X1 = -500, 900
river = Grid()
for x in range(X0, X1 + 1):
    c = yc(x)
    for y in range(c - HALF, c + HALF + 1):
        river.px(x, y, '.rv1' if y < c + HALF - 2 else '.rv2')
river.outline('.rvo')

def shimmer(shift):
    g = Grid()
    for k in range(X0 // 26 - 1, X1 // 26 + 2):
        x = k * 26 + shift
        for off, dx in ((-5, 0), (3, 13)):
            xx = x + dx
            y = yc(xx) + off
            g.rect(xx, y, xx + 2, y, '.shm')
    return g
SHIM = [shimmer(0), shimmer(9), shimmer(18)]

# ------------------------------------------------------------------ ground decoration
random.seed(7)
ground = Grid()          # grass tufts (snow shadows in winter)
for _ in range(226):
    x, y = random.randint(0, W - 3), random.randint(0, H - 3)
    ground.px(x, y, '.tuft'); ground.px(x + 1, y + 1, '.tuft'); ground.px(x - 1, y + 1, '.tuft')
flowers = Grid()         # summer + spring
for _ in range(68):
    x, y = random.randint(1, W - 2), random.randint(1, H - 2)
    flowers.px(x, y, random.choice(['#ffffff', '#ffd1e0', '#fff3a0']))
spring_extra = Grid()    # spring only: lots of little clusters of flowers
for _ in range(34):
    cx, cy, col = random.randint(2, W - 3), random.randint(2, H - 3), random.choice(['#ff8fb8', '#ffffff', '#fff070', '#c9a6ff'])
    for _k in range(3): spring_extra.px(cx + random.randint(-2, 2), cy + random.randint(-1, 1), col)
litter = Grid()          # fall only: fallen leaves
for _ in range(40):
    cx, cy = random.randint(2, W - 3), random.randint(2, H - 3)
    for _k in range(4):
        x, y = cx + random.randint(-3, 3), cy + random.randint(-1, 1)
        col = random.choice(['#e8782a', '#d9452f', '#e9b52e', '#c2561c'])
        litter.px(x, y, col); litter.px(x + 1, y, col)

def snow_layer(spr, pred=None):
    """White caps on every upward-facing edge of a sprite, a bit thicker on flat tops."""
    pre = spr.pre; top = {k for k, c in pre.items() if (k[0], k[1] - 1) not in pre and (pred is None or pred(c))}
    g = Grid()
    for (x, y) in top:
        g.px(x, y, '#f6faff')
        if (x - 1, y) in top and (x + 1, y) in top and pre.get((x, y + 1)) is not None and (pred is None or pred(pre[(x, y + 1)])):
            g.px(x, y + 1, '#d5e4f5')
    return g

# ------------------------------------------------------------------ trees
def tree(big=True):
    g = Grid()
    if big:
        g.rect(-1, -6, 0, -1, '#8a5a3b')
        parts = [(0, -11, 5.5, 5.5), (-4, -7, 3.6, 3.6), (4, -7, 3.6, 3.6)]
    else:
        g.rect(-1, -4, 0, -1, '#8a5a3b')
        parts = [(0, -8, 4, 4), (-3, -5, 2.6, 2.6), (3, -5, 2.6, 2.6)]
    cells = {}
    for cx, cy, rx, ry in parts:
        t = Grid(); t.disc(cx, cy, rx, ry, 1); cells.update(t.p)
    top = min(y for _, y in cells)
    for (x, y) in cells:
        c = '.lf'
        if (x + 3) + (y - top) < 5: c = '.lfh'
        elif x >= 2 and y >= top + 5: c = '.lfd'
        g.px(x, y, c)
    g.outline(OL)
    return g

TREE_SPOTS = [(22, 66, 1), (44, 36, 0), (200, 70, 1), (238, 60, 0), (352, 68, 1), 
              (18, 172, 1), (24, 214, 0), (128, 214, 0), (300, 214, 0), (342, 186, 1), (360, 216, 0), (300, 172, 1)]
def tree_svg(i, x, y, big):
    t = tree(bool(big))
    snow = snow_layer(t, pred=lambda c: c.startswith('.lf'))
    out = (f'<g class="tv{i % 3}" transform="translate({x} {y})">{svg_paths(t)}'
            f'<g class="snow">{svg_paths(snow)}</g></g>')
    # phones: "tt" trees lift with the river, "bot" trees drop with BU, "te" trees are hidden (they would be cut off)
    cls = ("tt" if y < 100 else "bot") + (" te" if x < 56 or x > 326 or (x, y) == (238, 60) else "")
    return f'<g class="{cls}">{out}</g>'          # "tt": top-half trees move up with the river on phones
trees_svg = "\n\t\t\t".join(tree_svg(i, x, y, b) for i, (x, y, b) in enumerate(TREE_SPOTS))

def xmas_tree():
    """A small decorated Christmas tree with a gold star: only shown on 25 December (see season.js)."""
    g = Grid()
    G1, G2, G3, TRUNK = '#2f8f4e', '#3fae62', '#237a41', '#8a5a3b'
    g.rect(-1, -3, 1, -1, TRUNK)
    tiers = [(-4, 8, 7), (-8, 6, 6), (-12, 4, 5), (-15, 2, 4)]   # (bottom row, rows, half-width at the bottom)
    for bot, n, hw in tiers:
        for k in range(n):
            half = max(1, hw - k)
            y = bot - k
            for x in range(-half, half + 1):
                g.px(x, y, G2 if x < -half // 3 else (G3 if x > half // 2 else G1))
    g.rect(-1, -20, 1, -18, '#3fae62')
    g.px(0, -21, G2)
    g.px(0, -22, '#ffd23f'); g.rect(-1, -23, 1, -23, '#ffd23f'); g.px(0, -24, '#ffd23f'); g.px(-2, -23, '#fff3a0'); g.px(2, -23, '#fff3a0')
    for x, y, c in ((-4, -5, '#e63946'), (3, -6, '#ffd23f'), (-2, -9, '#4aa3ff'), (3, -10, '#e63946'), (-1, -13, '#ffd23f'), (1, -16, '#4aa3ff'), (-5, -4, '#4aa3ff'), (5, -4, '#e63946')):
        g.px(x, y, c)
    g.outline(OL)
    return g
def xmas_lights():
    """Two sets of blinking lights, alternating, laid over the tree."""
    a, b = Grid(), Grid()
    for (x, y) in ((-3, -7), (2, -7), (-6, -4), (6, -5), (0, -11), (-3, -11), (2, -14)): a.px(x, y, '#fff3a0')
    for (x, y) in ((0, -6), (4, -8), (-4, -9), (3, -12), (-2, -15), (1, -9)): b.px(x, y, '#ffffff')
    return svg_paths(a), svg_paths(b)
_xa, _xb = xmas_lights()
XMAS_SVG = (f'<g class="xmas tt" aria-hidden="true"><g transform="translate(160 66)">{svg_paths(xmas_tree())}'
            f'<g class="xla">{_xa}</g><g class="xlb">{_xb}</g></g></g>')

# ------------------------------------------------------------------ buildings
def harvard():
    """Elliot House: red-brick Georgian Revival with a white belfry under a green copper dome."""
    g = Grid()
    BR, BRD, ST, SL, SLL, GL, DOOR = '#b23a48', '#9a2f3d', '#f3ead8', '#4a4e69', '#5f6488', '#3f4f73', '#6b3a2e'
    CU, CUH, CUD, GOLD = '#4fa58a', '#86d4b6', '#37806b', '#f2c14e'
    def brick(x0, y0, x1, y1):
        g.rect(x0, y0, x1, y1, BR)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x + (y % 2) * 2) % 4 == 0: g.px(x, y, BRD)
    def window(x, y):                       # 3x5 pane in a white frame with a sill
        g.rect(x - 1, y - 1, x + 3, y + 5, ST); g.rect(x, y, x + 2, y + 4, GL); g.px(x + 1, y + 2, ST)
    brick(-27, -20, 27, -1)
    g.hline(-1, -27, 27, ST)
    # slate roof with chimneys and dormers
    for i, half in enumerate((29, 28, 26, 25, 23)):
        g.rect(-half, -21 - i, half, -21 - i, SLL if i % 2 else SL)
    for sx in (-1, 1):
        for xc in (12, 21):
            x0 = sx * xc - 1
            g.rect(x0, -24, x0 + 2, -21, ST); g.px(x0 + 1, -23, GL)
    brick(15, -29, 17, -24); g.hline(-30, 14, 18, ST)
    brick(-17, -29, -15, -24); g.hline(-30, -18, -14, ST)
    # windows on both floors, either side of the tower
    for sx in (-1, 1):
        for xs in (10, 16, 22):
            x = xs if sx > 0 else -xs - 2
            window(x, -17); window(x, -9)
    # entrance
    g.rect(-4, -11, 4, -10, ST); g.rect(-2, -9, 2, -1, DOOR); g.px(0, -9, ST)
    # tower: brick shaft, white belfry, green dome
    brick(-6, -33, 6, -21)
    g.rect(-1, -31, 1, -26, GL)
    g.rect(-7, -34, 7, -33, ST)
    g.rect(-5, -42, 5, -35, ST)
    for x0, x1 in ((-4, -3), (-1, 1), (3, 4)): g.rect(x0, -40, x1, -36, GL)
    g.rect(-6, -43, 6, -43, ST)
    g.disc(0, -43, 6, 6.5, CU, cond=lambda x, y: y <= -44)
    for (x, y), c in list(g.p.items()):
        if c == CU and y <= -44:
            if x <= -3: g.px(x, y, CUH)
            elif x >= 3: g.px(x, y, CUD)
    g.vline(0, -53, -50, OL); g.px(0, -54, GOLD)
    g.outline(OL)
    return g

def mit():
    """The Great Dome: wide limestone building, 8-column portico, low dome set back on a drum."""
    g = Grid()
    L, L2, L3, SH, WINC, DOME, DOMEH, DOMED, DOMEX = '#d6d9df', '#eceef2', '#fbfbfd', '#c1c5ce', '#7d8aa3', '#b9c6d9', '#d9e3f1', '#98a8c0', '#a9b8cf'
    # wings: three storeys of windows
    g.rect(-29, -22, 29, -1, L)
    g.hline(-22, -29, 29, SH)
    for top in (-19, -14, -9):
        for xs in (19, 23, 27):
            g.sym(xs, top, xs + 1, top + 2, WINC)
    # drum and dome sit behind the portico
    g.rect(-13, -37, 13, -25, L)
    g.hline(-37, -14, 14, L2)
    for x in range(-12, 13, 3): g.vline(x, -36, -26, SH)
    g.disc(0, -38, 13, 11, DOME, cond=lambda x, y: y <= -38)
    for (x, y), c in list(g.p.items()):
        if c == DOME and y <= -38:
            if x <= -7: g.px(x, y, DOMEH)
            elif x >= 7: g.px(x, y, DOMED)
            elif x in (-3, 3): g.px(x, y, DOMEX)
    g.rect(-2, -51, 2, -49, L2); g.hline(-52, -1, 1, DOME); g.px(0, -53, DOME)
    # portico: steps, shadowed recess, 8 columns, entablature, pediment
    g.rect(-16, -1, 16, -1, '#e5e7eb'); g.rect(-15, -2, 15, -2, L2)
    g.rect(-17, -24, 17, -3, SH)
    for xs in (2, 6, 10, 14):                      # eight columns, lit on the left edge
        for cx in (xs, -xs - 1):
            g.vline(cx, -22, -4, L3); g.vline(cx + 1, -22, -4, L2)
    g.rect(-1, -12, 1, -4, '#4a4e69')
    g.rect(-18, -24, 18, -23, L2)
    for i, half in enumerate((18, 15, 12, 9, 6, 3)):
        g.rect(-half, -25 - i, half, -25 - i, L2 if i else L3)
    g.outline(OL)
    return g

# 3x5 pixel letters (a few are wider) for the name tags and the speech bubble
FONT = {
 'A': (".X.", "X.X", "XXX", "X.X", "X.X"), 'B': ("XX.", "X.X", "XX.", "X.X", "XX."),
 'C': (".XX", "X..", "X..", "X..", ".XX"), 'D': ("XX.", "X.X", "X.X", "X.X", "XX."),
 'E': ("XXX", "X..", "XX.", "X..", "XXX"), 'F': ("XXX", "X..", "XX.", "X..", "X.."),
 'G': (".XX", "X..", "X.X", "X.X", ".XX"), 'H': ("X.X", "X.X", "XXX", "X.X", "X.X"),
 'I': ("XXX", ".X.", ".X.", ".X.", "XXX"), 'J': ("..X", "..X", "..X", "X.X", ".X."),
 'K': ("X.X", "X.X", "XX.", "X.X", "X.X"), 'L': ("X..", "X..", "X..", "X..", "XXX"),
 'M': ("X...X", "XX.XX", "X.X.X", "X...X", "X...X"), 'N': ("X..X", "XX.X", "X.XX", "X..X", "X..X"),
 'O': ("XXX", "X.X", "X.X", "X.X", "XXX"), 'P': ("XX.", "X.X", "XX.", "X..", "X.."),
 'Q': ("XXX", "X.X", "X.X", "XXX", "..X"), 'R': ("XX.", "X.X", "XX.", "X.X", "X.X"),
 'S': (".XX", "X..", ".X.", "..X", "XX."), 'T': ("XXX", ".X.", ".X.", ".X.", ".X."),
 'U': ("X.X", "X.X", "X.X", "X.X", "XXX"), 'V': ("X.X", "X.X", "X.X", "X.X", ".X."),
 'W': ("X...X", "X...X", "X.X.X", "XX.XX", "X...X"), 'X': ("X.X", "X.X", ".X.", "X.X", "X.X"),
 'Y': ("X.X", "X.X", ".X.", ".X.", ".X."), 'Z': ("XXX", "..X", ".X.", "X..", "XXX"),
 '0': ("XXX", "X.X", "X.X", "X.X", "XXX"), '1': (".X.", "XX.", ".X.", ".X.", "XXX"),
 '2': ("XX.", "..X", ".X.", "X..", "XXX"), '3': ("XX.", "..X", ".X.", "..X", "XX."),
 '4': ("X.X", "X.X", "XXX", "..X", "..X"), '5': ("XXX", "X..", "XX.", "..X", "XX."),
 '6': (".XX", "X..", "XXX", "X.X", "XXX"), '7': ("XXX", "..X", ".X.", ".X.", ".X."),
 '8': ("XXX", "X.X", "XXX", "X.X", "XXX"), '9': ("XXX", "X.X", "XXX", "..X", "XX."),
 '=': ("...", "XXX", "...", "XXX", "..."), '!': ("X", "X", "X", ".", "X"), '.': (".", ".", ".", ".", "X"), ',': (".", ".", ".", "X", "X"),
 ' ': ("..", "..", "..", "..", ".."),
}
def text_grid(word, x0, y0, c):
    g = Grid(); x = x0
    for ch in word:
        for ry, row in enumerate(FONT[ch]):
            for rx, v in enumerate(row):
                if v == 'X': g.px(x + rx, y0 + ry, c)
        x += len(FONT[ch][0]) + 1
    return g
def text_width(word): return sum(len(FONT[ch][0]) for ch in word) + len(word) - 1

def dahod():
    """Dahod Family Alumni Center (BU): cream limestone Gothic Revival mansion: crenellated entrance tower with a
    pointed-arch door and lancet windows, a tall chimney, two gables, green slate roof and a flag."""
    g = Grid()
    ST, STL, STD = '#e6d6a8', '#f4ead0', '#cbb887'
    SLT, SLTD = '#6f9a8c', '#557f73'
    GLS, GLSL, DOOR, DOORD = '#44587a', '#8aa3c4', '#6b3a2e', '#4a2a22'
    CHIM, POT = '#c98c5c', '#b5563a'
    def ashlar(x0, y0, x1, y1):                      # limestone blocks: coursing lines with staggered joints
        g.rect(x0, y0, x1, y1, ST)
        for y in range(y0, y1 + 1):
            if y % 4 == 0:
                for x in range(x0, x1 + 1): g.px(x, y, STD)
            elif (x0 + y) % 2 == 0:
                pass
        for y in range(y0, y1 + 1):
            if y % 4 != 0:
                for x in range(x0, x1 + 1):
                    if (x + (y // 4) * 3) % 8 == 0: g.px(x, y, STD)
    def lancet(x, top, h, w=2):                      # slim pointed window in a pale surround
        g.rect(x - 1, top - 1, x + w, top + h, STL)
        g.rect(x, top, x + w - 1, top + h - 1, GLS)
        g.px(x, top, GLSL)
        if w == 2: g.px(x + 1, top, STL)
        g.vline(x, top + 1, top + h - 1, GLSL if h > 4 else GLS)
    def gable(cx, wall_top, half):                   # stone gable with a pale coping and a finial
        for i in range(half + 1):
            y = wall_top - i; h = half - i
            g.rect(cx - h, y, cx + h, y, ST)
            for x in (cx - h, cx + h): g.px(x, y, SLT if i < half else STL)
            if i < half:
                for x in (cx - h - 1, cx + h + 1): g.px(x, y - 1, SLTD)
        g.px(cx, wall_top - half, STL); g.vline(cx, wall_top - half - 3, wall_top - half - 1, STL)
    # slate roof showing behind the tower
    for i, half in enumerate((13, 11, 9, 7, 5)):
        g.rect(-half, -39 - i, half, -39 - i, SLTD if i % 2 else SLT)
    # tall chimney with pots, left of the tower top
    g.rect(-9, -51, -5, -36, CHIM); g.rect(-10, -52, -4, -51, STD)
    for y in range(-50, -37, 3):
        for x in range(-9, -4): g.px(x, y, '#b57a4c')
    g.rect(-8, -55, -7, -53, POT); g.rect(-6, -54, -5, -53, POT)
    # wings
    ashlar(-28, -28, -11, -5); gable(-19, -28, 8)
    ashlar(11, -30, 28, -5); gable(19, -30, 8)
    # central tower
    ashlar(-10, -35, 10, -5)
    g.rect(-11, -36, 11, -36, STL); g.hline(-35, -10, 10, STD)
    for x in range(-10, 11):
        if (x + 10) % 4 < 2: g.rect(x, -38, x, -37, ST)
    g.hline(-37, -11, 11, STL)
    # gable windows
    for cx, top in ((-19, -26), (19, -28)):
        for dx in (-3, 0, 3): g.px(cx + dx, top, GLS); g.px(cx + dx, top + 1, GLS)
    # lancet windows, two floors on each wing, three above the door on the tower
    for x in (-25, -20, -15):
        lancet(x, -24, 6); lancet(x, -15, 6)
    for x in (14, 19, 24):
        lancet(x, -26, 6); lancet(x, -17, 6)
    lancet(-7, -32, 8); lancet(-1, -32, 8, 3); lancet(6, -32, 8)
    # name plate and a small light by the door
    for x in range(-5, 6, 2): g.px(x, -20, STD)
    
    # pointed arch doorway with a dark wooden door
    for i, half in enumerate((5, 5, 5, 5, 5, 5, 5, 5, 4, 3, 2, 1)):
        g.rect(-half, -5 - i, half, -5 - i, STL)
    for i, half in enumerate((4, 4, 4, 4, 4, 4, 4, 4, 3, 2, 1, 0)):
        if i > 10: continue
        g.rect(-half, -5 - i, half, -5 - i, DOOR)
    g.vline(0, -14, -5, DOORD)
    g.rect(-2, -13, -1, -12, '#e8b84a'); g.rect(1, -13, 2, -12, '#e8b84a')
    # terrace wall with balusters, steps up to the door
    g.rect(-29, -4, 29, -1, STL)
    for x in range(-29, 30):
        if x % 3 == 0:
            g.rect(x, -3, x, -2, STD)
    g.rect(-29, -4, 29, -4, STD)
    g.rect(-5, -4, 5, -1, STL); g.hline(-3, -5, 5, STD); g.hline(-2, -6, 6, STL)
    # flagpole and a white flag with a small red crest
    g.vline(3, -60, -39, '#6b6f7a')
    g.rect(4, -60, 10, -55, '#ffffff'); g.hline(-58, 5, 9, '#cc0000'); g.vline(7, -59, -56, '#cc0000')
    g.outline(OL)
    return g

def plaza(rx=27):
    sh = Grid(); sh.disc(0, 2, rx + 2, 5.5, '.pzs')
    pl = Grid(); pl.disc(0, 1, rx, 4.5, '.pz'); pl.outline('.pzo')
    return svg_paths(sh), svg_paths(pl)

def tag(word):
    tw = text_width(word); w = tw + 6; x = -(w // 2); y = 6; h = 11
    g = Grid()
    def notched(x0, y0, x1, y1, c):
        g.rect(x0 + 1, y0, x1 - 1, y1, c); g.rect(x0, y0 + 1, x1, y1 - 1, c)
    notched(x, y, x + w - 1, y + h - 1, '.tagbd')
    notched(x + 1, y + 1, x + w - 2, y + h - 2, '.tagbg')
    g.p.update(text_grid(word, x + 3, y + 3, '.tagtx').p)
    return svg_paths(g)

def person(shirt, hair, pants, skin, dirn, frame, point=False):
    """A tiny walker (9 px tall). dirn -1 = walking left, +1 = walking right; frame 0/1 = legs apart/together."""
    g = Grid(); SK = skin
    f = (lambda x: x) if dirn < 0 else (lambda x: -x)
    def px(x, y, c): g.px(f(x), y, c)
    for x in (-1, 0, 1): px(x, -10, hair); px(x, -9, SK); px(x, -8, SK)
    px(1, -9, hair)
    for x in (-1, 0, 1):
        for y in range(-7, -3): px(x, y, shirt)
    if point:                                # arm raised towards the sky, hand in skin colour
        px(-2, -7, shirt); px(-3, -8, shirt); px(-4, -9, skin)
    else:
        px(-2, -6, shirt)
    px(2, -7, '#8a5a3b'); px(2, -6, '#8a5a3b'); px(2, -5, '#8a5a3b')
    if frame == 0:
        for y in (-3, -2): px(-1, y, pants); px(1, y, pants)
        px(-1, -1, '#2b2438'); px(1, -1, '#2b2438')
    else:
        for y in (-3, -2): px(0, y, pants)
        px(0, -1, '#2b2438'); px(-1, -1, '#2b2438')
    g.outline(OL)
    return g

# (shirt, hair, trousers, skin, start delay). Exactly one walker in three has dark skin.
DARK_SKIN = ('#7a4a2a', '#5c3a21')
PEOPLE = [("#e63946", "#3b2a20", "#3a4a8a", '#ffd9a8', 0),
          ("#2a9d8f", "#1d1d1d", "#264653", '#7a4a2a', -3.2),
          ("#f4a261", "#e9c46a", "#5b5b7a", '#f1c27d', -6.4),
          ("#6a4c93", "#1d1d1d", "#2f3e46", '#c68642', -9.6),
          ("#e9c46a", "#1d1d1d", "#3a4a8a", '#5c3a21', -12.8)]
WALK = 70   # how far (art pixels) the walkers travel; must match walk-l / walk-r in style.css

def walkers(dirn):
    out = []
    for i, (shirt, hair, pants, skin, delay) in enumerate(PEOPLE):
        a, b = svg_paths(person(shirt, hair, pants, skin, dirn, 0)), svg_paths(person(shirt, hair, pants, skin, dirn, 1))
        cls = 'walk-l' if dirn < 0 else 'walk-r'
        off = -dirn * round(WALK * (0.08 + 0.19 * i))      # resting place if animation is switched off
        wrap = '<g>'
        out.append(f'{wrap}<g transform="translate(0 3)"><g class="{cls}" style="animation-delay:{delay}s;--off:{off}px">'
                   f'<g class="fade" style="animation-delay:{delay}s"><g class="fa">{a}</g><g class="fb">{b}</g></g></g></g></g>')
    return "\n\t\t\t\t\t".join(out)

def dirt_path(dirn):
    rnd = random.Random(3 + dirn)
    g = Grid()
    for x in range(24, WALK + 14):
        for y in (1, 2, 3):
            if x > WALK + 8 and (y != 2 or rnd.random() < .5): continue
            g.px(dirn * -x, y, '.pth' if rnd.random() > .12 else '.pthd')
    g.p = {k: v for k, v in g.p.items()}
    return svg_paths(g)

def bubble(date, color, side):
    """Speech bubble; the tip of its tail is at (0, 0). side 'right' = bubble sits to the right of the tip."""
    lines = ["UPCOMING", "MEETING ON", date.upper() + "!"]
    widths = [text_width(l) for l in lines]
    w = max(widths) + 6; h = 3 * 5 + 2 * 2 + 6
    sg = 1 if side == 'right' else -1
    bx0, bx1 = (3, 3 + w - 1) if sg > 0 else (-(3 + w - 1), -3)
    by1 = -4; by0 = by1 - h + 1
    g = Grid()
    g.rect(bx0 + 1, by0, bx1 - 1, by1, '#ffffff'); g.rect(bx0, by0 + 1, bx1, by1 - 1, '#ffffff')
    for y, x0, x1 in ((-3, 6, 10), (-2, 4, 8), (-1, 2, 5), (0, 0, 2)):
        a, b = sorted((sg * x0, sg * x1)); g.rect(a, y, b, y, '#ffffff')
    g.outline(OL)
    for i, line in enumerate(lines):
        g.p.update(text_grid(line, bx0 + 3 + (w - 6 - widths[i]) // 2, by0 + 3 + 7 * i, color if i == 2 else '#1d2b53').p)
    return g

CAMPUSES = {
    #            page          label                color      sprite   tag      x    y   plaza  bubble tip (dx, dy, side)  walkers' direction
    "harvard": dict(href="harvard.html", label="Harvard", color="#a51c30", sprite=harvard, word="HARVARD", x=90, y=77, rx=34, tip=(16, -36, 'right'), walk=-1),
    "mit":     dict(href="mit.html", label="MIT", color="#5f6168", sprite=mit, word="MIT", x=290, y=77, rx=34, tip=(-16, -36, 'left'), walk=1),
    "bu":      dict(href="bu.html", label="Boston University", color="#cc0000", sprite=dahod, word="BOSTON U", x=190, y=190, rx=34, tip=(30, -34, 'right'), walk=-1),
}
if NEXT["campus"] not in CAMPUSES:
    raise SystemExit("next-meeting.json: campus must be one of " + ", ".join(CAMPUSES))
NEXT_DATE = NEXT["date"].strip()

def campus(key):
    c = CAMPUSES[key]
    spr = c["sprite"]()
    x0, _, x1, _ = spr.bbox()
    dx = -((x0 + x1) // 2)
    shadow, plz = plaza(c["rx"])
    rx = c["rx"]
    nxt = key == NEXT["campus"]
    label = c["label"] + (f". Upcoming meeting on {NEXT_DATE}!" if nxt else "")
    extra_before = f'<g>{dirt_path(c["walk"])}</g>' if nxt else ""
    extra_after = ""
    if nxt:
        tx, ty, side = c["tip"]
        extra_after = (f'<g aria-hidden="true">{walkers(c["walk"])}</g>\n\t\t\t\t\t'
                       f'<g transform="translate({tx} {ty})"><g class="bscale"><g class="bob">{svg_paths(bubble(NEXT_DATE, c["color"], side))}</g></g></g>')
    return f'''<g class="cg cg-{key}{' bot' if key == 'bu' else ''}"><g transform="translate({c["x"]} {c["y"]})">
				<a class="campus{' next' if nxt else ''}" href="{c["href"]}" style="--c:{c["color"]}" aria-label="{label}">
					<rect x="-{rx + 3}" y="-60" width="{2 * rx + 6}" height="78" fill="none" pointer-events="all"/>
					{extra_before}
					{shadow}
					<g class="plaza">{plz}</g>
					<g class="bldg"><g transform="translate({dx} 0)">
					{svg_paths(spr)}
					<g class="snow">{svg_paths(snow_layer(spr))}</g>
					</g></g>
					{extra_after}
					<g class="tag">{tag(c["word"])}</g>
				</a>
			</g></g>'''

# ------------------------------------------------------------------ stargazers, top right under the night sky
def telescope():
    """A small refractor on a wooden tripod, aimed up and to the right. Origin = ground under the tripod."""
    g = Grid()
    WOOD, WOODD, BRASS, CREAM, CREAMD, NAVY, GLASS = '#8a5a3b', '#6b4429', '#d4a24a', '#f1ead8', '#cfc6ad', '#3a4a8a', '#9fe0ff'
    for y in range(-15, 0):
        x = round(6 * (y + 16) / 16)
        g.px(-x, y, WOOD); g.px(x, y, WOOD); g.px(0, y, WOODD)
    for k in range(15):                                  # the tube, 45 degrees, k = 0 at the eyepiece end
        cx, cy = -5 + k, -11 - k
        wid = 2 if k >= 12 else 1                        # wider dew shield at the far end
        col = NAVY if k >= 12 else (BRASS if k in (3, 9) else CREAM)
        for x in range(cx - wid, cx + wid + 1): g.px(x, cy, col)
        if col == CREAM: g.px(cx - 1, cy, CREAMD)
    g.px(cx + wid, cy, GLASS)
    g.rect(-1, -17, 1, -15, BRASS)                       # mount
    g.px(-6, -10, '#4a4e69'); g.px(-7, -9, '#4a4e69'); g.px(-8, -8, OL)   # eyepiece
    g.outline(OL)
    return g

# (shirt, hair, trousers, skin): the one at the eyepiece has dark skin
STARGAZERS = [("#d95f9b", "#1d1d1d", "#3a4a8a", '#7a4a2a'),
              ("#4a90d9", "#a8532a", "#4a4e69", '#ffd9a8'),      # points up at the sky
              ("#e9c46a", "#3b2a20", "#5b5b7a", '#f1c27d')]
ROWER_SKIN = '#c68642'

def observers():
    """Telescope and three people at the top right of the map, right under the night-sky header, looking up and to the left."""
    tel = telescope()
    tel.p = {(-x, y): c for (x, y), c in tel.p.items()}          # mirror: the tube now points up-left
    tel.pre = {(-x, y): c for (x, y), c in tel.pre.items()}
    v, ptr, third = STARGAZERS
    return (f'<g class="obs"><g transform="translate(340 30)" aria-hidden="true" pointer-events="none">'
            f'<g>{svg_paths(tel)}<g class="snow">{svg_paths(snow_layer(tel))}</g></g>'
            f'<g transform="translate(10 0)">{svg_paths(person(*v, -1, 1))}</g>'
            f'<g transform="translate(18 0)">{svg_paths(person(*ptr, -1, 1, point=True))}</g>'
            f'<g transform="translate(26 0)">{svg_paths(person(*third, -1, 1))}</g>'
            f'</g></g>')

# ------------------------------------------------------------------ falling leaves, petals, snow
def particles(kind, n, colours, seed, wide=False):
    rnd = random.Random(seed); out = []
    for _ in range(n):
        x = rnd.randint(-150, W + 150); dur = rnd.uniform(16, 30); delay = -rnd.uniform(0, dur)
        drift = rnd.choice([-36, -24, -12, 12, 24, 36])
        w, h = (2, 1) if kind != 'snow' else ((2, 2) if rnd.random() < .22 else (1, 1))
        out.append(f'<g class="pt" style="--x:{x}px;--dx:{drift}px;animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
                   f'<rect class="sw" width="{w}" height="{h}" fill="{rnd.choice(colours)}"/></g>')
    return "".join(out)
PARTICLES = (f'<g class="p p-fall" aria-hidden="true" pointer-events="none">{particles("leaf", 26, ["#e8782a", "#d9452f", "#e9b52e", "#c2561c"], 11)}</g>'
             f'<g class="p p-spring" aria-hidden="true" pointer-events="none">{particles("petal", 20, ["#ffc2d9", "#ffffff", "#ffa8c8"], 12)}</g>'
             f'<g class="p p-winter" aria-hidden="true" pointer-events="none">{particles("snow", 70, ["#ffffff", "#ffffff", "#eaf4ff"], 13)}</g>')

# ------------------------------------------------------------------ what goes along the river, by season
# Origin (0, 0) = the middle of the river; everything faces right and moves right. JS moves the whole #boat group.
SKATER_SKIN, SAILOR_SKIN = '#f1c27d', '#ffd9a8'

# fall: the rower. Two frames: at the catch the oars reach forward, at the finish they sweep back and splash
def rower(frame):
    g = Grid()
    g.rect(-8, 0, 7, 1, '#fffaf0'); g.px(8, 0, '#fffaf0'); g.px(-9, 0, '#fffaf0')
    g.hline(0, 3, 6, '#cc0000')
    g.px(-2, 0, '#2b4a8a')
    if frame == 0:                                   # catch: leaning forward, oars angled ahead
        g.px(-1, -1, ROWER_SKIN)
        for (x, y) in ((-4, -2), (-3, -3), (-2, -4)): g.px(x, y, '#8a5a3b')
        g.px(-1, -4, '#cc0000'); g.px(0, -4, '#cc0000')
        for (x, y) in ((-4, 3), (-3, 4), (-2, 5)): g.px(x, y, '#8a5a3b')
        g.px(-1, 5, '#cc0000'); g.px(0, 5, '#cc0000')
    else:                                            # finish: leaning back, oars swept behind
        g.px(-3, -1, ROWER_SKIN)
        for (x, y) in ((-4, -2), (-5, -3)): g.px(x, y, '#8a5a3b')
        g.px(-6, -4, '#cc0000'); g.px(-7, -4, '#cc0000')
        for (x, y) in ((-4, 3), (-5, 4)): g.px(x, y, '#8a5a3b')
        g.px(-6, 5, '#cc0000'); g.px(-7, 5, '#cc0000')
    g.outline(OL)
    for x in (-12, -14, -17): g.px(x, 0 if x == -12 else 1, '#ffffff')
    g.px(-15, 0, '#ffffff'); g.px(-18, 0, '#ffffff')
    if frame == 1:                                   # splashes where the blades leave the water
        for (x, y) in ((-9, -5), (-10, -3), (-9, 6), (-10, 4)): g.px(x, y, '#ffffff')
    return g

# winter: an ice-skater in a red hat and a yellow scarf, leaning into a long forward glide: push off, then glide
# with the free leg lifted behind (the scarf streams back the whole time, so it always looks like forward motion)
def skater(frame):
    g = Grid(); HAT, FACE, SCARF, COAT, GLOVE, PANTS, BOOT, BLADE = '#e63946', SKATER_SKIN, '#ffd23f', '#3a6ea5', '#f4f4f0', '#2f3e46', '#4a3a30', '#e8f0f8'
    g.rect(0, -11, 2, -10, HAT); g.px(1, -12, HAT); g.px(1, -13, '#ffffff')           # bobble hat, head pushed forward
    g.rect(0, -9, 2, -8, FACE); g.px(2, -9, '#2b2438')                                # face with an eye
    g.hline(-7, 0, 2, SCARF)                                                          # scarf, with a tail streaming behind
    for (x, y) in ((-1, -7), (-2, -7 + frame), (-3, -6 + frame), (-4, -6 + frame)): g.px(x, y, SCARF)
    g.rect(0, -6, 2, -6, COAT); g.rect(-1, -5, 1, -3, COAT)                           # coat, leaning forward
    g.px(-2, -4, COAT); g.px(-3, -4, GLOVE)                                           # hands held behind the back
    if frame == 0:                                                                    # push-off: one leg stretched out behind
        for y in range(-2, 2): g.px(1, y, PANTS)
        g.px(1, 2, BOOT); g.hline(3, 0, 3, BLADE)
        for (x, y) in ((0, -2), (-1, -1), (-2, 0), (-3, 1)): g.px(x, y, PANTS)
        g.px(-4, 2, BOOT); g.hline(3, -6, -3, BLADE)
    else:                                                                             # glide: free leg lifted behind
        for y in range(-2, 2): g.px(1, y, PANTS)
        g.px(1, 2, BOOT); g.hline(3, -1, 3, BLADE)
        for (x, y) in ((0, -2), (-1, -2), (-2, -1), (-3, -1)): g.px(x, y, PANTS)
        g.px(-4, -1, BOOT); g.px(-5, -1, BLADE)
    g.outline(OL)
    for (x, y) in ((-9, 3), (-12, 4), (-15, 3), (-18, 4), (-11, 2), (-21, 3)): g.px(x, y, '#ffffff')      # ice shavings
    return g

# spring: a mother duck and three ducklings in single file
def duck(mother):
    g = Grid()
    if mother:
        BODY, WING, HEAD, BEAK, RING = '#a98462', '#c8a47e', '#2e8b57', '#f5b82e', '#ffffff'
        g.rect(-4, -1, 3, 1, BODY); g.rect(-3, -1, 1, -1, WING); g.px(-5, -2, BODY); g.px(-5, -1, BODY)
        g.px(3, -2, RING); g.rect(3, -4, 5, -3, HEAD); g.px(4, -2, HEAD); g.hline(-3, 6, 7, BEAK); g.px(5, -4, '#1d1d1d')
    else:
        BODY, HEAD, BEAK = '#ffd93d', '#ffe680', '#f08a24'
        g.rect(-2, 0, 1, 1, BODY); g.px(-3, 0, BODY); g.rect(1, -2, 2, -1, HEAD); g.px(3, -1, BEAK); g.px(2, -2, '#1d1d1d')
    g.outline(OL)
    for dx, dy in ((-7, 1), (-8, 2)) if mother else ((-5, 1), (-6, 1)): g.px(dx, dy, '#ffffff')              # ripples
    return g

def ducks_svg():
    mom = f'<g class="dbob" style="animation-delay:0s">{svg_paths(duck(True))}</g>'
    kids = "".join(f'<g transform="translate({-14 - 9 * i} {(1, 0, 1)[i]})"><g class="dbob" style="animation-delay:{0.4 + 0.4 * i:.1f}s">{svg_paths(duck(False))}</g></g>' for i in range(3))
    return mom + kids

# summer: a little one-person sailboat with a red pennant
def sailboat(frame):
    g = Grid(); HULL, STRIPE, KEEL, MAST, SAIL, SAILS, JIB, JACKET, CAP = '#fffaf0', '#cc2f2f', '#2b4a8a', '#8a5a3b', '#fffaf0', '#e4dcc4', '#cfe8ff', '#ff8a3d', '#cc2f2f'
    g.hline(0, -8, 8, HULL); g.px(9, -1, HULL); g.hline(1, -7, 7, STRIPE); g.hline(2, -5, 4, KEEL)
    g.vline(0, -13, -1, MAST)
    for y in range(-13, -4):                                            # mainsail, behind the mast, bulging a pixel in frame 1
        w = int((y + 13) * 0.7) + 1 + (1 if frame and -10 <= y <= -6 else 0)
        g.hline(y, -w, -1, SAIL); g.px(-1, y, SAILS)
    g.hline(-4, -9, -1, MAST)                                           # boom
    for y in range(-11, -4):                                            # jib, in front of the mast
        g.hline(y, 1, 1 + int((y + 11) * 0.6), JIB)
    g.hline(-2, -5, -3, JACKET) if False else None
    g.rect(-5, -1, -2, -1, JACKET); g.rect(-4, -3, -3, -2, SAILOR_SKIN); g.hline(-3, -4, -3, CAP)   # the sailor
    g.px(1, -13, STRIPE); g.px(2, -13, STRIPE); g.px(1, -12, STRIPE)   # pennant
    g.outline(OL)
    for (x, y) in ((-11, 1), (-13, 2), (-16, 1), (-19, 2)): g.px(x, y, '#ffffff')
    return g

def boat_svg():
    sk = f'<g class="fa">{svg_paths(skater(0))}</g><g class="fb">{svg_paths(skater(1))}</g>'
    sl = f'<g class="fa">{svg_paths(sailboat(0))}</g><g class="fb">{svg_paths(sailboat(1))}</g>'
    rw = f'<g class="fa row">{svg_paths(rower(0))}</g><g class="fb row">{svg_paths(rower(1))}</g>'
    return (f'<g class="bt bt-fall">{rw}</g><g class="bt bt-winter">{sk}</g>'
            f'<g class="bt bt-spring">{ducks_svg()}</g><g class="bt bt-summer">{sl}</g>')

# everyone on the map. Fall, winter and summer each have one more person on the river (rower, skater, sailor), so
# there are 9 people and exactly 3 (one in three) have dark skin. In spring the ducks have no person, so there are
# just the 5 walkers + 3 stargazers = 8 people, 3 of them dark-skinned (a third is impossible with 8 people).
DARK = lambda skins: sum(k in DARK_SKIN for k in skins)
_BASE = [p[3] for p in PEOPLE] + [p[3] for p in STARGAZERS]
for _season, _extra in (("fall", [ROWER_SKIN]), ("winter", [SKATER_SKIN]), ("summer", [SAILOR_SKIN])):
    _all = _BASE + _extra
    assert 3 * DARK(_all) == len(_all), f"{_season}: keep exactly one person in three dark-skinned"
assert DARK(_BASE) == 3 and len(_BASE) == 8, "spring: 8 people, 3 of them dark-skinned"

# ------------------------------------------------------------------ bridge: a cute red truss bridge, seen at a slight angle
BRIDGE_X = 148      # the bridge crosses the river just left of BU
def bridge():
    """A wooden deck between red rails, leaning a little so that we also see the red truss on its east side (white
    zig-zag truss), with round lamps and little stone steps at each end. x is relative to
    BRIDGE_X, y is absolute."""
    g = Grid()
    cs = [yc(BRIDGE_X + dx) for dx in range(-12, 13)]
    top, bot, mid = min(cs) - HALF - 4, max(cs) + HALF + 4, yc(BRIDGE_X)
    STONE = '#a39d8e'
    RED, REDL, REDD, WHITE = '#d94a4a', '#f27a6e', '#a82f35', '#fff4e0'
    WOOD, WOODD, TICK, LAMP, LAMPL = '#d9a566', '#b9824a', '#fff4e0', '#ffd75e', '#fffbd0'
    sh = lambda y: -round((y - mid) * 0.18)                     # the slight lean
    put = lambda x, y, c: g.px(x + sh(y), y, c)
    for y in range(top, bot + 1):
        for x in (11, 12, 13):                                  # its shadow on the water
            c = yc(BRIDGE_X + x + sh(y))
            if c - HALF + 1 <= y <= c + HALF - 2: put(x, y, '.rvo')
        for x in range(-7, 8):                                  # deck + rails
            if abs(x) >= 6: col = REDL if (abs(x) == 6) else RED
            else: col = WOODD if y % 3 == 0 else WOOD
            put(x, y, col)
        if y % 8 == 3: put(-5, y, TICK); put(-4, y, TICK)       # smoot marks, painted on the planks
        for x in (8, 9, 10):                                    # the east truss: red with a white zig-zag
            put(x, y, REDD if x != 8 else RED)
        t = y % 6; put(8 + (t if t < 3 else 5 - t), y, WHITE)   # one white zig-zag, like a Warren truss
    for x in range(-8, 9):                                      # little stone abutments at each end
        for yy in (top, top + 1, bot - 1, bot): put(x, yy, STONE)
    for y in (top + 3, mid - 6, mid + 6, bot - 3):              # round lamps on both rails
        for x in (-7, 6):
            put(x, y, LAMPL); put(x + 1, y, LAMP); put(x, y + 1, LAMP); put(x + 1, y + 1, LAMP)
    g.outline(OL)
    return g

# ------------------------------------------------------------------ hero: night sky that fades into the grass
# A face-on Milky Way ringed by a stellar stream sits behind the title. The sky is a tiled starfield
# (hero-stars.svg), faded into the seasonal grass colour with a stepped mask (hero-fade.svg).
STAR_TILE_W, STAR_TILE_H = 256, 128      # art pixels
FADE_H = 24                               # art pixels the fade takes up
GAL_W, GAL_H = 160, 46                    # the galaxy + stream picture, in art pixels

def svg_file(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'shape-rendering="crispEdges">{body}</svg>\n')

def star_tile():
    rnd = random.Random(21); g = Grid()
    for _ in range(STAR_TILE_W * STAR_TILE_H // 260):
        g.px(rnd.randrange(STAR_TILE_W), rnd.randrange(STAR_TILE_H),
             rnd.choice(['#5a6fb8', '#5a6fb8', '#8fa6e8', '#8fa6e8', '#cfe0ff', '#ffffff', '#fff3b0']))
    for _ in range(6):                                     # a few brighter, plus-shaped stars
        x, y = rnd.randrange(3, STAR_TILE_W - 3), rnd.randrange(3, STAR_TILE_H - 3)
        g.px(x, y, '#ffffff')
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): g.px(x + dx, y + dy, '#6f86d6')
    return svg_file(STAR_TILE_W, STAR_TILE_H, svg_paths(g))

def fade_tile():
    """4 px wide mask: opaque at the top, stepping down in 8 soft bands of 3 art pixels to transparent."""
    bands = FADE_H // 3
    rects = "".join(f'<rect y="{i * 3}" width="4" height="3" fill-opacity="{1 - (i + .5) / bands:.3f}"/>' for i in range(bands))
    return svg_file(4, FADE_H, rects)

def spiral(g, cx, cy, R, tilt=.55, rot=-.4, seed=1, arms=2):
    rnd = random.Random(seed)
    c, s_ = math.cos(rot), math.sin(rot)
    def put(xr, yr, col):
        g.px(round(cx + xr * c - yr * tilt * s_), round(cy + xr * s_ + yr * tilt * c), col)
    for _ in range(int(R * R * 2.2)):                      # soft disc of faint stars
        r = R * math.sqrt(rnd.random()); a = rnd.random() * 6.283
        if rnd.random() < .5 * (1 - r / R) + .1: put(r * math.cos(a), r * math.sin(a), '#4a5fb5')
    for arm in range(arms):
        for i in range(520):
            r = 2.5 + i * (R - 2.5) / 520
            th = arm * math.pi + 3.1 * math.log(r / 2.2)
            col = '#ffe9a0' if r < 5 else ('#e9f0ff' if r < R * .6 else '#9ec0ff')
            put(r * math.cos(th), r * math.sin(th), col)
            if rnd.random() < .5: put((r + 1) * math.cos(th), (r + 1) * math.sin(th), '#6f8fe0' if r > 6 else '#ffd978')
    for i in range(-5, 6): put(i, 0, '#ffd978')            # bar
    for y in range(-2, 3):
        for x in range(-2, 3):
            if abs(x) + abs(y) <= 3: put(x, y, '#fff3b0')
    put(0, 0, '#ffffff')

def stream(g, pt, t_prog, t_lo, t_hi, n, seed, width=1.0, lead=.35):
    """Stars scattered along the path pt(t) either side of a progenitor cluster at t_prog, thinning with distance."""
    rnd = random.Random(seed)
    for _ in range(n):
        d = rnd.expovariate(5.5)
        t = t_prog + (d if rnd.random() > lead else -d * .55)
        if not (t_lo <= t <= t_hi): continue
        x, y = pt(t); nx, ny = pt(t + .01); tx, ty = nx - x, ny - y; L = math.hypot(tx, ty) or 1
        off = rnd.gauss(0, .55 * width)
        qx, qy = x - ty / L * off, y + tx / L * off
        col = rnd.choice(['#ffe9a0', '#ffffff', '#ffd978', '#ffffff']) if d < .08 else rnd.choice(['#ffffff', '#cfe0ff', '#9ec0ff', '#ffe9a0', '#bcd2ff'])
        g.px(round(qx), round(qy), col)
        if rnd.random() < .12: g.px(round(qx) + 1, round(qy), col)
    px0, py0 = pt(t_prog)
    g.disc(px0, py0, 2.4, 2.4, '#ffd978'); g.px(round(px0), round(py0), '#ffffff')
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)): g.px(round(px0) + dx, round(py0) + dy, '#ffe9a0')

def galaxy_svg():
    g = Grid(); cx, cy, tilt = GAL_W // 2, 21, -.06
    def ring(t):
        a = 2 * math.pi * t - .5
        x, y = 56 * math.cos(a), 10.5 * math.sin(a)
        return cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)
    stream(g, ring, .72, .05, .98, 700, 5, width=1.4, lead=.5)
    spiral(g, cx, cy, 15, seed=3)
    return svg_paths(g)

(OUT / "hero-stars.svg").write_text(star_tile(), encoding="utf-8")
(OUT / "hero-fade.svg").write_text(fade_tile(), encoding="utf-8")
GALAXY = galaxy_svg()

# On phones the top row is lifted LIFT art pixels toward the header; this finds the highest thing on the map
# (so menu.js can start the view just above it, with no blank band under the header).
LIFT = 40
def compact_top():
    tops = [CAMPUSES[k]["y"] + CAMPUSES[k]["sprite"]().bbox()[1] - LIFT for k in ("harvard", "mit")]
    if NEXT["campus"] in ("harvard", "mit"):                       # speech bubble above the host (drawn at 2x on phones)
        c = CAMPUSES[NEXT["campus"]]; tops.append(c["y"] + c["tip"][1] - 56 - LIFT)
    return min(tops)

# ------------------------------------------------------------------ page
HTML = r'''<!DOCTYPE html>
<html lang="en" data-season="@@SEASON@@">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>The Local Group</title>
	<meta name="description" content="The Local Group: a discussion and seminar group for galactic dynamics and near-field cosmology. Meets monthly at Harvard, MIT and Boston University.">
	<meta name="theme-color" content="#0f1535">
	<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' shape-rendering='crispEdges'%3E%3Crect width='16' height='16' fill='%238fd16c'/%3E%3Cpath fill='%233f95d8' d='M0 6h16v6H0z'/%3E%3Cpath fill='%235bb8f0' d='M0 6h16v4H0z'/%3E%3C/svg%3E">
	<link rel="preload" href="PressStart2P.woff2" as="font" type="font/woff2" crossorigin>
	<script src="season.js"></script>
	<link rel="stylesheet" href="style.css">
	<script defer src="menu.js"></script>
</head>
<body class="home">
	<div class="hero">
		<div class="sky" aria-hidden="true"></div>
		<svg class="galaxy" viewBox="0 0 @@GALW@@ @@GALH@@" shape-rendering="crispEdges" aria-hidden="true" focusable="false">@@GALAXY@@</svg>

		<header class="topbar">
			<a href="../">&lt; Elliot Y. Davies</a>
		</header>

		<div class="intro">
			<h1>The Local Group</h1>
			<p class="tagline">A discussion and seminar group for galactic dynamics and near-field cosmology.</p>
			<nav class="buttons" aria-label="The Local Group">
				<a class="btn" href="schedule.html">Schedule</a>
				<a class="btn" href="https://forms.gle/UewtgsnsCusrJGoR7" target="_blank" rel="noopener">Mailing List</a>
				<a class="btn" href="about.html">About</a>
			</nav>
		</div>
	</div>

	<main class="scene-wrap" id="main">
		<svg class="scene" viewBox="@@VIEW@@" data-view="@@VIEW@@" data-compact="@@COMPACT@@" data-ctop="@@CTOP@@" data-cbot="@@CBOT@@" data-river="@@RIVERCFG@@" data-w="@@W@@" preserveAspectRatio="xMidYMid meet" shape-rendering="crispEdges" role="group" aria-label="Pixel map of the Charles River with Harvard and MIT on the north bank and Boston University on the south bank">
			<g aria-hidden="true">
				<g>@@GROUND@@</g>
				<g class="g-flowers">@@FLOWERS@@</g>
				<g class="g-spring">@@SPRING@@</g>
				<g class="g-litter">@@LITTER@@</g>
				<g class="rv">
					<g>@@RIVER@@</g>
					<g class="sh sh1">@@SH1@@</g>
					<g class="sh sh2">@@SH2@@</g>
					<g class="sh sh3">@@SH3@@</g>
					<g id="boat" transform="translate(40 @@BOATY@@)">@@BOAT@@</g>
					<g transform="translate(@@BRIDGEX@@ 0)">@@BRIDGE@@</g>
				</g>
				@@TREES@@
			</g>

			@@OBSERVERS@@
			@@CAMPUSES@@
			@@PARTICLES@@
		</svg>
	</main>
</body>
</html>
'''

html = (HTML.replace("@@VIEW@@", VIEW).replace("@@COMPACT@@", COMPACT_VIEW).replace("@@CTOP@@", str(compact_top())).replace("@@CBOT@@", "226").replace("@@BRIDGE@@", svg_paths(bridge())).replace("@@BRIDGEX@@", str(BRIDGE_X)).replace("@@OBSERVERS@@", observers()).replace("@@W@@", str(W)).replace("@@GALAXY@@", GALAXY).replace("@@GALW@@", str(GAL_W)).replace("@@GALH@@", str(GAL_H))
        .replace("@@RIVERCFG@@", f"{RIVER_Y},{AMP},{PERIOD}")
        .replace("@@SEASON@@", BUILD_SEASON).replace("@@PARTICLES@@", PARTICLES)
        .replace("@@FLOWERS@@", svg_paths(flowers)).replace("@@SPRING@@", svg_paths(spring_extra)).replace("@@LITTER@@", svg_paths(litter))
        .replace("@@GROUND@@", svg_paths(ground)).replace("@@RIVER@@", svg_paths(river))
        .replace("@@SH1@@", svg_paths(SHIM[0])).replace("@@SH2@@", svg_paths(SHIM[1])).replace("@@SH3@@", svg_paths(SHIM[2]))
        .replace("@@TREES@@", trees_svg + "\n\t\t\t" + XMAS_SVG).replace("@@BOAT@@", boat_svg()).replace("@@BOATY@@", str(yc(40)))
        .replace("@@CAMPUSES@@", "\n\t\t\t".join(campus(k) for k in ("harvard", "mit", "bu"))))
(OUT / "index.html").write_text(html, encoding="utf-8")

# ------------------------------------------------------------------ schedule page (data in schedule.json)
def chalk_icon():
    """A chalkboard on a wooden frame with a chalk tray, equations and a little orbit sketch (25 x 17)."""
    g = Grid(); WOOD, SLATE, CHALK, TRAY, DUST = '#8a5a3b', '#2f4a3f', '#f4f4f0', '#cfb98f', '#a9b8ae'
    g.rect(0, 0, 24, 16, WOOD); g.rect(1, 1, 23, 13, SLATE)
    g.rect(1, 14, 23, 15, TRAY); g.hline(14, 1, 23, '#e3d3ad')
    g.rect(4, 14, 6, 14, CHALK); g.rect(18, 14, 20, 15, DUST)                  # a stick of chalk and an eraser in the tray
    g.hline(3, 3, 12, CHALK); g.hline(5, 3, 8, CHALK); g.hline(5, 10, 13, CHALK)
    g.hline(7, 3, 11, CHALK); g.hline(9, 3, 7, CHALK); g.hline(9, 9, 12, CHALK); g.hline(11, 3, 10, CHALK)
    for x, y in ((17, 4), (18, 4), (19, 4), (16, 5), (20, 5), (16, 6), (20, 6), (17, 7), (18, 7), (19, 7)): g.px(x, y, CHALK)   # circle
    g.px(18, 5, '#ffd23f'); g.px(21, 9, CHALK); g.px(15, 10, CHALK); g.hline(10, 17, 22, CHALK)
    g.outline(OL)
    return g

def projector_icon():
    """An overhead projector: a box with a lit glass stage, a column, and the lens head reaching over the stage (21 x 20)."""
    g = Grid(); BODY, BODYL, DARK, GLASS, HEAD, HEADL = '#4a4e69', '#6b7096', '#2f3248', '#9fe0ff', '#6b7096', '#9ba1c9'
    g.rect(1, 13, 20, 18, BODY); g.hline(13, 1, 20, BODYL)             # base box
    g.rect(3, 12, 15, 12, GLASS)                                        # the lit glass stage
    g.px(15, 16, HEADL); g.px(18, 16, HEADL); g.hline(17, 3, 10, DARK)  # knobs and a vent
    g.rect(3, 19, 5, 19, DARK); g.rect(16, 19, 18, 19, DARK)            # feet
    g.rect(17, 4, 19, 12, DARK)                                         # column
    g.rect(3, 1, 19, 4, HEAD); g.hline(1, 3, 19, HEADL)                 # arm
    g.rect(3, 5, 9, 6, DARK); g.hline(7, 4, 8, GLASS)                   # lens head hanging over the stage
    g.outline(OL)
    return g

def table_icon():
    """A round table on one pedestal with a chair either side, a paper and a mug on top (25 x 13)."""
    g = Grid(); TOP, EDGE, LEG, CHAIR, PAPER, MUG = '#d9a46a', '#a8693a', '#6b4429', '#8a5a3b', '#f4f4f0', '#e63946'
    for sx in (-1, 1):                                                  # chairs, drawn first so the table overlaps them
        f = (lambda x: x) if sx < 0 else (lambda x: 24 - x)
        g.rect(f(0), 3, f(0), 9, CHAIR); g.rect(min(f(0), f(4)), 8, max(f(0), f(4)), 8, CHAIR)
        g.rect(f(0), 9, f(0), 12, LEG); g.rect(f(3), 9, f(3), 12, LEG)
    g.disc(12, 5, 8.4, 2.9, EDGE); g.disc(12, 4, 8.4, 2.9, TOP)
    g.rect(11, 8, 12, 11, LEG); g.rect(8, 12, 15, 12, LEG)
    g.rect(8, 3, 10, 4, PAPER); g.px(15, 3, MUG); g.px(15, 4, MUG)
    g.outline(OL)
    return g

def icon_svg(spr, scale, cls, snow=False):
    x0, y0, x1, y1 = spr.bbox(); w, h = x1 - x0 + 1, y1 - y0 + 1
    inner = svg_paths(spr) + (f'<g class="snow">{svg_paths(snow_layer(spr))}</g>' if snow else '')
    return (f'<svg class="{cls}" viewBox="{x0} {y0} {w} {h}" width="{w * scale}" height="{h * scale}" '
            f'shape-rendering="crispEdges" aria-hidden="true" focusable="false">{inner}</svg>')

TALK_TYPES = {"chalk": ("Chalk talk", "at the board, no slides", chalk_icon),
              "colloquium": ("Colloquium", "a talk with slides", projector_icon),
              "workshop": ("Workshop", "open group discussion", table_icon)}
TALK_ICON = {k: icon_svg(v[2](), 2, "t-svg") for k, v in TALK_TYPES.items()}
_WIDTHS = {k: (lambda b: b[2] - b[0] + 1)(c['sprite']().bbox()) for k, c in CAMPUSES.items()}
assert len(set(_WIDTHS.values())) == 1, f'campus icons must all be the same width: {_WIDTHS}'
CAMPUS_ICON = {k: icon_svg(c["sprite"](), 2, "m-svg", snow=True) for k, c in CAMPUSES.items()}

def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def tba(value, label):
    v = (value or "").strip()
    return f"{label} TBA" if v.upper() in ("", "TBA") else v

def load_schedule(): return json.loads((HERE / "schedule.json").read_text(encoding="utf-8"))

def meeting_card(m, venues, on_campus_page=False):
    """One meeting. On the main schedule the campus icon and name link to that campus's page."""
    d = datetime.date.fromisoformat(m["date"]); c = CAMPUSES[m["campus"]]
    talks = "".join(
        f'<li><span class="t-ico" title="{TALK_TYPES[t["type"]][0]}">{TALK_ICON[t["type"]]}<span class="sr">{TALK_TYPES[t["type"]][0]}: </span></span>'
        f'<span class="t-text"><span class="t-title">{esc(t.get("title") or "Untitled talk")}</span>'
        f'<span class="t-speaker">{esc(t.get("speaker") or "Speaker TBA")}</span></span></li>' for t in m["talks"])
    room = tba(m.get("room") or venues.get(m["campus"], {}).get("room"), "Room")
    if on_campus_page:
        ico, where = "", f"{d:%A}"
    else:
        ico = f'<a class="m-ico" href="{c["href"]}" aria-label="{c["label"]}: room and all of its meetings">{CAMPUS_ICON[m["campus"]]}</a>'
        where = f'{d:%A} at <a href="{c["href"]}">{c["label"]}</a>'
    return (f'<li id="{m["date"]}"><article class="card meeting" style="--c:{c["color"]}">'
            f'<header>{ico}<div><h2>{d:%B} {d.day}, {d.year}</h2><p class="m-where">{where}</p>'
            f'<p class="m-when"><span>{esc(tba(m.get("time"), "Time"))}</span><span>{esc(room)}</span></p>'
            f'<p class="m-food">Food provided by {esc(m.get("food") or "TBA")}</p></div></header>'
            f'<ul class="talks">{talks}</ul></article></li>')

def schedule_page():
    data = load_schedule(); venues = data.get("venues", {})
    legend = "".join(f'<li>{TALK_ICON[k]}<span><b>{name}</b><br>{esc(desc)}</span></li>' for k, (name, desc, _) in TALK_TYPES.items())
    meetings = [meeting_card(m, venues) for m in sorted(data["meetings"], key=lambda m: m["date"])]
    main = (f'<section class="card legend" aria-label="Talk types"><h2>Talk types</h2><ul>{legend}</ul></section>\n\t\t'
            f'<ol class="meetings">\n\t\t\t' + "\n\t\t\t".join(meetings) + '\n\t\t</ol>')
    return subpage("Schedule", "Upcoming meetings and talks.", "Upcoming meetings and talks of The Local Group, a discussion and seminar group for galactic dynamics and near-field cosmology.", main)

def campus_page(key):
    """Harvard / MIT / BU page: the room at the top, then only the meetings held there."""
    c = CAMPUSES[key]; data = load_schedule(); venues = data.get("venues", {})
    room = tba(venues.get(key, {}).get("room"), "Room")
    mine = [m for m in sorted(data["meetings"], key=lambda m: m["date"]) if m["campus"] == key]
    cards = "".join(meeting_card(m, venues, on_campus_page=True) for m in mine)
    body = (f'<ol class="meetings">{cards}</ol>' if mine else '<p class="card empty">No meetings are scheduled here yet.</p>')
    main = (f'<section class="card venue" style="--c:{c["color"]}"><span class="m-ico">{CAMPUS_ICON[key]}</span>'
            f'<div><h2>Where</h2><p class="v-room">{esc(room)}</p></div></section>\n\t\t' + body)
    return subpage(c["label"], f"Meetings hosted at {c['label']}.", f"Meetings of The Local Group hosted at {c['label']}, with the room and the schedule of talks.", main)

SCHED = r'''<!DOCTYPE html>
<html lang="en" data-season="@@SEASON@@">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>@@TITLE@@ | The Local Group</title>
	<meta name="description" content="@@DESC@@">
	<meta name="theme-color" content="#0f1535">
	<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' shape-rendering='crispEdges'%3E%3Crect width='16' height='16' fill='%238fd16c'/%3E%3Cpath fill='%233f95d8' d='M0 6h16v6H0z'/%3E%3Cpath fill='%235bb8f0' d='M0 6h16v4H0z'/%3E%3C/svg%3E">
	<link rel="preload" href="PressStart2P.woff2" as="font" type="font/woff2" crossorigin>
	<script src="season.js"></script>
	<link rel="stylesheet" href="style.css">
</head>
<body class="sched">
	<div class="hero">
		<div class="sky" aria-hidden="true"></div>
		<header class="topbar">
			<a href="./">&lt; The Local Group</a>
		</header>
		<div class="intro">
			<h1>@@TITLE@@</h1>
			<p class="tagline">@@TAGLINE@@</p>
		</div>
	</div>

	<main class="sched-main" id="main">
		@@MAIN@@
	</main>
</body>
</html>
'''

def subpage(title, tagline, desc, main):
    return (SCHED.replace("@@SEASON@@", BUILD_SEASON).replace("@@TITLE@@", title).replace("@@TAGLINE@@", tagline)
            .replace("@@DESC@@", desc).replace("@@MAIN@@", main))

STAR = Grid()
for (x, y) in ((2, 0), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3), (1, 4), (3, 4)): STAR.px(x, y, '#f2c14e')
STAR.px(2, 2, '#fff3a0'); STAR.outline(OL)

def about_page():
    data = json.loads((HERE / "about.json").read_text(encoding="utf-8"))
    star = icon_svg(STAR, 3, "p-star")
    rows = []
    for o in data["organisers"]:
        pos, url = (o.get("position") or "").strip(), (o.get("url") or "").strip()
        site = (f'<a class="p-site" href="{esc(url)}" target="_blank" rel="noopener">{esc(url.split("//")[-1].strip("/"))}</a>' if url
                else '<span class="p-site tba">Website TBA</span>')
        rows.append(f'<li><span class="p-ico">{star}</span><div><h3>{esc(o["name"])}</h3>'
                    f'<p class="p-pos{"" if pos else " tba"}">{esc(pos) if pos else "Position TBA"}</p>{site}</div></li>')
    main = '<section class="card organisers"><h2>Organisers</h2><ul class="people">' + "".join(rows) + '</ul></section>'
    return subpage("About", "Who runs The Local Group.", "About The Local Group, a discussion and seminar group for galactic dynamics and near-field cosmology, and the people who organise it.", main)

(OUT / "schedule.html").write_text(schedule_page(), encoding="utf-8")
(OUT / "harvard.html").write_text(campus_page("harvard"), encoding="utf-8")
(OUT / "mit.html").write_text(campus_page("mit"), encoding="utf-8")
(OUT / "bu.html").write_text(campus_page("bu"), encoding="utf-8")
(OUT / "about.html").write_text(about_page(), encoding="utf-8")

PAGE = r'''<!DOCTYPE html>
<html lang="en" data-season="@@SEASON@@">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>@@NAME@@ | The Local Group</title>
	<meta name="description" content="@@NAME@@ at The Local Group, a discussion and seminar group for galactic dynamics and near-field cosmology.">
	<meta name="theme-color" content="#8fd16c">
	<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' shape-rendering='crispEdges'%3E%3Crect width='16' height='16' fill='%238fd16c'/%3E%3Cpath fill='%233f95d8' d='M0 6h16v6H0z'/%3E%3Cpath fill='%235bb8f0' d='M0 6h16v4H0z'/%3E%3C/svg%3E">
	<link rel="preload" href="PressStart2P.woff2" as="font" type="font/woff2" crossorigin>
	<script src="season.js"></script>
	<link rel="stylesheet" href="style.css">
</head>
<body class="sub" style="--c:@@COLOR@@">
	<header class="topbar">
		<a href="./">&lt; The Local Group</a>
	</header>
	<main class="sub-main" id="main">
		<h1>@@NAME@@</h1>
		<p class="tagline">This page is coming soon.</p>
	</main>
</body>
</html>
'''
for fname, name, color in (("mailing-list.html", "Mailing List", "#1d2b53"),):
    (OUT / fname).write_text(PAGE.replace("@@NAME@@", name).replace("@@COLOR@@", color).replace("@@SEASON@@", BUILD_SEASON), encoding="utf-8")
# Cache-busting: tag the local CSS/JS links with a hash of the file, so a browser that cached an
# older style.css or menu.js always fetches the new one (a stale stylesheet shows every season's art at once).
import hashlib, re
def _ver(name):
    return hashlib.md5((OUT / name).read_bytes()).hexdigest()[:8]
_V = {n: _ver(n) for n in ("style.css", "menu.js", "season.js")}
for _page in OUT.glob("*.html"):
    _t = _page.read_text(encoding="utf-8")
    for _n, _h in _V.items():
        _t = re.sub(r'(?:src|href)="%s(?:\?v=\w+)?"' % re.escape(_n),
                    lambda m, _n=_n, _h=_h: m.group(0).split('"')[0] + '"%s?v=%s"' % (_n, _h), _t)
    _page.write_text(_t, encoding="utf-8")
print("built The Local Group:", NEXT["campus"], "-", NEXT_DATE)
