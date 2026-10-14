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
import argparse, datetime, json, math, pathlib, random, urllib.parse

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

# wide screens show more of the map than the 380px the scene was drawn on: carry the ground detail out to the river's full length
# (X0..X1). A separate generator keeps the original centre exactly as it was.
_xr = random.Random(11)
for _lo, _hi in ((X0, -1), (W, X1)):
    _f = (_hi - _lo + 1) / W
    for _ in range(round(226 * _f)):
        x, y = _xr.randint(_lo, _hi - 2), _xr.randint(0, H - 3)
        ground.px(x, y, '.tuft'); ground.px(x + 1, y + 1, '.tuft'); ground.px(x - 1, y + 1, '.tuft')
    for _ in range(round(68 * _f)):
        flowers.px(_xr.randint(_lo, _hi - 1), _xr.randint(1, H - 2), _xr.choice(['#ffffff', '#ffd1e0', '#fff3a0']))
    for _ in range(round(34 * _f)):
        cx, cy, col = _xr.randint(_lo, _hi - 2), _xr.randint(2, H - 3), _xr.choice(['#ff8fb8', '#ffffff', '#fff070', '#c9a6ff'])
        for _k in range(3): spring_extra.px(cx + _xr.randint(-2, 2), cy + _xr.randint(-1, 1), col)
    for _ in range(round(40 * _f)):
        cx, cy = _xr.randint(_lo, _hi - 4), _xr.randint(2, H - 3)
        for _k in range(4):
            x, y = cx + _xr.randint(-3, 3), cy + _xr.randint(-1, 1)
            col = _xr.choice(['#e8782a', '#d9452f', '#e9b52e', '#c2561c'])
            litter.px(x, y, col); litter.px(x + 1, y, col)

# phones show a taller crop (down to about y = 330), so carry the ground detail below the original map too
_xd = random.Random(13); _DY = 112
for _ in range(round(226 * _DY / H * 0.8)):
    x, y = _xd.randint(0, W - 3), _xd.randint(H, H + _DY)
    ground.px(x, y, '.tuft'); ground.px(x + 1, y + 1, '.tuft'); ground.px(x - 1, y + 1, '.tuft')
for _ in range(round(68 * _DY / H)):
    flowers.px(_xd.randint(1, W - 2), _xd.randint(H, H + _DY), _xd.choice(['#ffffff', '#ffd1e0', '#fff3a0']))
for _ in range(round(34 * _DY / H)):
    cx, cy, col = _xd.randint(2, W - 3), _xd.randint(H, H + _DY), _xd.choice(['#ff8fb8', '#ffffff', '#fff070', '#c9a6ff'])
    for _k in range(3): spring_extra.px(cx + _xd.randint(-2, 2), cy + _xd.randint(-1, 1), col)
for _ in range(round(40 * _DY / H)):
    cx, cy = _xd.randint(2, W - 3), _xd.randint(H, H + _DY)
    for _k in range(4):
        x, y = cx + _xd.randint(-3, 3), cy + _xd.randint(-1, 1)
        col = _xd.choice(['#e8782a', '#d9452f', '#e9b52e', '#c2561c'])
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
# the same trees, scattered along both banks beyond the original map (wide screens only; phones crop them out)
_tr = random.Random(5)
for _lo, _hi in ((X0 + 8, -30), (W + 30, X1 - 8)):
    _x = _lo + _tr.randint(0, 20)
    while _x < _hi:
        _y = _tr.choice([_tr.randint(34, 74), _tr.randint(172, 216)])
        TREE_SPOTS.append((_x, _y, _tr.choice([0, 1, 1])))
        _x += _tr.randint(22, 46)
def tree_svg(i, x, y, big, cls=None):
    t = tree(bool(big))
    snow = snow_layer(t, pred=lambda c: c.startswith('.lf'))
    out = (f'<g class="tv{i % 3}" transform="translate({x} {y})">{svg_paths(t)}'
            f'<g class="snow">{svg_paths(snow)}</g></g>')
    # phones: "tt" trees lift with the river, "bot" trees drop with BU, "te" trees are hidden (they would be cut off)
    if cls is None: cls = ("tt" if y < 100 else "bot") + (" te" if x < 56 or x > 326 or (x, y) == (238, 60) else "")
    return f'<g class="{cls}">{out}</g>'          # "tt": top-half trees move up with the river on phones
trees_svg = "\n\t\t\t".join(tree_svg(i, x, y, b) for i, (x, y, b) in enumerate(TREE_SPOTS))

# Phones (see menu.js) show only x 46..334 and re-arrange the map, which leaves the few trees that fit looking lonely. Add
# phone-only trees, spread evenly with "best candidate" sampling around everything that is already there. Positions are
# in phone-view coordinates (the "tt" group is lifted 40 and the "bot" group dropped ~14 by style.css, so convert back).
def phone_trees():
    rnd = random.Random(17)
    BOX = [(62, -26, 140, 66), (244, -26, 318, 66),            # Harvard and MIT with their name tags
           (148, 136, 234, 232), (212, 106, 330, 180),         # BU with its tag, and its speech bubble
           (148, 194, 280, 218), (40, 68, 340, 110),           # the people walking to BU, and the river
           (62, -90, 190, -20), (190, -90, 318, -20),          # a bubble above Harvard or MIT
           (120, 28, 204, 60), (172, 28, 252, 60)]             # ...and the people walking to either
    pts = []                                                    # centres of the trees already shown on phones
    for (x, y, b) in TREE_SPOTS:
        if 56 <= x <= 326 and (x, y) != (238, 60) and x <= W: pts.append((x, (y - 40 if y < 100 else y + 14) - 8))
    boxes = BOX + [(x - 10, y - 12, x + 10, y + 12) for (x, y) in pts]
    out = []
    def ok(x, y):
        return not any(bx0 - 9 < x < bx1 + 9 and by0 - 11 < y < by1 + 11 for bx0, by0, bx1, by1 in boxes)
    for zone, n, (ylo, yhi) in (("tt", 5, (-6, 62)), ("bot", 15, (122, 312))):
        for _ in range(n):
            best = None
            for _k in range(80):
                x, y = rnd.randint(58, 322), rnd.randint(ylo, yhi) - 8
                if not ok(x, y): continue
                d = min([math.hypot(x - px, (y - py) * 1.15) for px, py in pts] + [60])
                if best is None or d > best[0]: best = (d, x, y)
            if best is None: continue
            _, x, y = best; pts.append((x, y)); boxes.append((x - 10, y - 12, x + 10, y + 12))
            out.append((x, y + 8 + (40 if zone == "tt" else -14), rnd.choice([0, 1, 1]), zone))
    return out
PHONE_TREES = phone_trees()
trees_svg += "\n\t\t\t" + "\n\t\t\t".join(tree_svg(100 + i, x, y, b, "mob " + z) for i, (x, y, b, z) in enumerate(PHONE_TREES))

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
    """The Great Dome in sandstone: wide wings with tall windows, a flat-roofed portico of 8 columns with three red doors,
    and the dome in its three tiers (an inscribed drum, a narrower drum, then the shallow patinated dome with a pale cap)."""
    g = Grid()
    WING, WING_L, WING_D, WING_HL = '#d8c49a', '#e8d8b2', '#bba67c', '#f4e8c8'          # warm sandstone
    DR, DR_L, DR_D, DR_HL = '#dccdaa', '#ebdfc4', '#c3b38d', '#f6eedb'                  # slightly paler stone for the drums
    WINC, GLASS, GLASS_LO, DOOR, DOORD = '#7d8aa3', '#56627f', '#58647f', '#9a3b30', '#7a2c25'
    PATINA, CAPC = ('#a9b8aa', '#93a596'), ('#f0ead8', '#e2dac4', '#c9c1ac')
    # wings: a blank band under the cornice, short windows above tall ones that reach down near the ground;
    # the windows are 2px wide with 2px between them, like the gaps between the columns
    g.rect(-29, -23, 29, -1, WING)
    g.hline(-23, -29, 29, WING_L); g.hline(-22, -29, 29, WING_D)
    for x in (19, 23, 27):
        g.sym(x, -17, x + 1, -14, WINC)
        g.sym(x, -10, x + 1, -3, WINC)
    g.hline(-1, -29, 29, WING_D)
    # dome, tier 1: the wide drum with the date, cornice above it
    g.rect(-12, -29, 12, -26, DR)
    for x in range(-4, 5, 2): g.px(x, -27, DR_D)
    g.hline(-30, -13, 13, DR_HL); g.hline(-29, -12, 12, DR_D); g.hline(-26, -12, 12, DR_D)
    # tier 2: a narrower drum with its own cornice
    g.rect(-10, -33, 10, -31, DR)
    g.hline(-34, -11, 11, DR_HL); g.hline(-33, -10, 10, DR_D); g.hline(-31, -10, 10, DR_D)
    # tier 3: the shallow dome, striped copper patina below a pale cap
    cy = -35
    g.disc(0, cy, 10, 7, PATINA[0], cond=lambda x, y: y <= cy)
    for (x, y), c in list(g.p.items()):
        if c == PATINA[0] and y <= cy:
            if (cy - y) % 2 == 1: g.px(x, y, PATINA[1])
            if y <= cy - 4: g.px(x, y, CAPC[0] if x <= -4 else (CAPC[2] if x >= 5 else CAPC[1]))
    # portico: glazed wall behind the columns, flat entablature with the lettering band, 8 columns, three doors, steps
    g.rect(-16, -25, 16, -2, WING)
    g.rect(-15, -22, 15, -13, GLASS)
    g.rect(-15, -12, 15, -2, GLASS_LO)                              # the lower glazing: same colour by day, but it glows at night (see WINDOW_COLOURS)
    g.hline(-25, -17, 17, WING_HL); g.hline(-24, -17, 17, WING_L); g.hline(-23, -17, 17, WING)
    for x in range(-14, 15, 2): g.px(x, -23, WING_D)
    g.hline(-22, -16, 16, WING_D)
    for x in (-15, -11, -7, -3, 2, 6, 10, 14):                     # 2px columns, 2px gaps, a 3px gap in the middle
        g.vline(x, -21, -3, WING_HL); g.vline(x + 1, -21, -3, WING_L); g.px(x + 1, -21, WING)
    g.rect(-1, -10, 1, -2, DOOR); g.rect(-5, -9, -4, -2, DOORD); g.rect(4, -9, 5, -2, DOORD)
    g.rect(-17, -1, 17, -1, WING_D); g.rect(-16, -2, 16, -2, WING_L)
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

# ------------------------------------------------------------------ night mode: lit windows + the moon/sun button
# Windows are found by their colour in each sprite; at night the sprite is dimmed (an SVG colour filter, see style.css)
# and these pixels are drawn again on top in warm light, each window with its own slightly different warmth.
WINDOW_COLOURS = {"harvard": {'#3f4f73'}, "mit": {'#7d8aa3', '#58647f'}, "bu": {'#44587a', '#8aa3c4', '#e8b84a'}}
LIGHTS = ['#ffe27a', '#ffd058', '#ffeaa0', '#ffd866']
def night_lights(spr, colours):
    lit = {k for k, c in spr.p.items() if c in colours}
    seen, comps = set(), []
    for k in sorted(lit, key=lambda k: (k[1], k[0])):
        if k in seen: continue
        stack, comp = [k], []
        seen.add(k)
        while stack:
            x, y = stack.pop(); comp.append((x, y))
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in lit and q not in seen: seen.add(q); stack.append(q)
        comps.append(comp)
    g, halo = Grid(), Grid()
    for i, comp in enumerate(comps):
        col = LIGHTS[(comp[0][0] * 7 + comp[0][1] * 3 + i) % len(LIGHTS)]
        for (x, y) in comp:
            g.px(x, y, col)
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in spr.p and q not in lit: halo.px(q[0], q[1], '#ffd866')     # a soft glow on the frame around it
    return f'<g opacity=".28">{svg_paths(halo)}</g>{svg_paths(g)}'

def icon_svg(spr, scale, cls, snow=False):
    x0, y0, x1, y1 = spr.bbox(); w, h = x1 - x0 + 1, y1 - y0 + 1
    inner = svg_paths(spr) + (f'<g class="snow">{svg_paths(snow_layer(spr))}</g>' if snow else '')
    return (f'<svg class="{cls}" viewBox="{x0} {y0} {w} {h}" width="{w * scale}" height="{h * scale}" '
            f'shape-rendering="crispEdges" aria-hidden="true" focusable="false">{inner}</svg>')

def moon_icon():
    """A crescent moon with a few stars (13 x 13)."""
    g = Grid(); M, MS = '#fff0b8', '#e9c96e'
    g.disc(6, 6, 6, 6, M); 
    for (x, y), c in list(g.p.items()):
        if ((x - 9) / 5.3) ** 2 + ((y - 4) / 5.3) ** 2 <= 1: del g.p[(x, y)]
    for (x, y) in ((1, 7), (2, 9), (3, 10)): g.px(x, y, MS)
    g.outline(OL)
    g.px(10, 9, '#ffe9a8'); g.px(11, 7, '#ffe9a8'); g.px(9, 11, '#ffe9a8')
    return g

def sun_icon():
    """A sun with short rays (13 x 13)."""
    g = Grid(); S, SH = '#ffd23f', '#f0a830'
    g.disc(6, 6, 3.6, 3.6, S)
    for (x, y), c in list(g.p.items()):
        if x + y >= 14: g.px(x, y, SH)
    for (x, y) in ((6, 0), (6, 1), (6, 11), (6, 12), (0, 6), (1, 6), (11, 6), (12, 6),
                   (2, 2), (3, 3), (10, 2), (9, 3), (2, 10), (3, 9), (10, 10), (9, 9)): g.px(x, y, S)
    g.outline(OL)
    return g

TOD_BUTTON = ('<button class="tod" type="button" id="tod" aria-pressed="false" aria-label="Night mode" title="Night mode">'
              f'<span class="tod-moon">{icon_svg(moon_icon(), 2, "tod-svg")}</span><span class="tod-sun">{icon_svg(sun_icon(), 2, "tod-svg")}</span></button>')

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
        extra_after = (f'<g class="dim" aria-hidden="true">{walkers(c["walk"])}</g>\n\t\t\t\t\t'
                       f'<g transform="translate({tx} {ty})"><g class="bscale"><g class="bob">{svg_paths(bubble(NEXT_DATE, c["color"], side))}</g></g></g>')
    return f'''<g class="cg cg-{key}{' bot' if key == 'bu' else ''}"><g transform="translate({c["x"]} {c["y"]})">
				<a class="campus{' next' if nxt else ''}" href="{c["href"]}" style="--c:{c["color"]}" aria-label="{label}">
					<rect x="-{rx + 3}" y="-60" width="{2 * rx + 6}" height="78" fill="none" pointer-events="all"/>
					<g class="dim">{extra_before}{shadow}<g class="plaza">{plz}</g></g>
					<g class="bldg"><g transform="translate({dx} 0)">
					<g class="dim">{svg_paths(spr)}<g class="snow">{svg_paths(snow_layer(spr))}</g></g>
					<g class="lit" aria-hidden="true">{night_lights(spr, WINDOW_COLOURS[key])}</g>
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
    return (f'<g class="obs dim"><g transform="translate(340 30)" aria-hidden="true" pointer-events="none">'
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
    """Side-on: a cream racing shell (bow to the right) and a rower facing the stern, one oar swinging (2 frames).
    Catch: leaning forward with arms stretched, the blade dips in ahead. Finish: leaning back, hands at the chest, blade out behind."""
    g = Grid(); JERSEY, HAIR, OAR, BLADE, SHORTS, SHOE = '#3f78d6', '#6b4226', '#8a5a3b', '#cc0000', '#2f3e46', '#2b2438'
    def line(x0, y0, x1, y1, col):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1): g.px(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), col)
    g.rect(-9, -1, 8, 0, '#fffaf0'); g.px(9, -1, '#fffaf0'); g.hline(-1, 3, 6, '#cc0000')
    if frame == 0:                                   # catch
        hip, sh, hx = 1, -1, -2
        line(-2, -5, -4, -4, ROWER_SKIN)                                        # arms stretched out to the handle
        line(-5, -4, 5, 1, OAR); g.px(5, 1, BLADE); g.px(4, 1, BLADE)
    else:                                            # finish
        hip, sh, hx = 2, 2, 1
        line(3, -5, 2, -4, ROWER_SKIN)                                          # hands drawn in to the chest
        line(2, -4, -8, 1, OAR); g.px(-8, 1, BLADE); g.px(-7, 1, BLADE)
    g.rect(hip - 3, -2, hip, -2, SHORTS); g.px(hip - 4, -2, SHOE)                                                # legs out to the stretcher
    g.rect(sh, -5, sh + 1, -3, JERSEY)                                                                           # shoulders and back
    g.rect(hx, -7, hx + 1, -6, HAIR); g.px(hx, -6, ROWER_SKIN)                                                   # head: hair, face towards the stern
    g.outline(OL)
    for x in (-12, -14, -17): g.px(x, -1 if x == -12 else 0, '#ffffff')
    g.px(-15, -1, '#ffffff'); g.px(-18, -1, '#ffffff')
    if frame == 1:                                   # splashes where the blade leaves the water
        for (x, y) in ((-10, 0), (-9, 2), (-11, 2)): g.px(x, y, '#ffffff')
    else:
        for (x, y) in ((7, 0), (7, 2)): g.px(x, y, '#ffffff')
    return g

# winter: an ice-skater in a red hat and a yellow scarf, leaning into a long forward glide: push off, then glide
# with the free leg lifted behind (the scarf streams back the whole time, so it always looks like forward motion)
def skater(frame):
    g = Grid(); HAT, FACE, SCARF, COAT, GLOVE, PANTS, BOOT, BLADE = '#e63946', SKATER_SKIN, '#ffd23f', '#3a6ea5', '#f4f4f0', '#2f3e46', '#4a3a30', '#e8f0f8'
    g.rect(0, -8, 2, -8, HAT); g.px(1, -9, '#ffffff')                                 # bobble hat, head pushed forward
    g.rect(0, -7, 2, -6, FACE); g.px(2, -7, '#2b2438')                                # face with an eye
    g.hline(-5, 0, 2, SCARF)                                                          # scarf, with a tail streaming behind
    for (x, y) in ((-1, -5), (-2, -5 + frame), (-3, -4 + frame)): g.px(x, y, SCARF)
    g.rect(0, -4, 2, -4, COAT); g.rect(-1, -3, 1, -2, COAT)                           # coat, leaning forward
    g.px(-2, -3, COAT); g.px(-3, -3, GLOVE)                                           # hands held behind the back
    if frame == 0:                                                                    # push-off: one leg stretched out behind
        g.px(1, -1, PANTS); g.px(1, 0, PANTS); g.px(1, 1, BOOT); g.hline(2, 0, 3, BLADE)
        for (x, y) in ((0, -1), (-1, 0), (-2, 1)): g.px(x, y, PANTS)
        g.px(-3, 1, BOOT); g.hline(2, -5, -2, BLADE)
    else:                                                                             # glide: free leg lifted behind
        g.px(1, -1, PANTS); g.px(1, 0, PANTS); g.px(1, 1, BOOT); g.hline(2, -1, 3, BLADE)
        for (x, y) in ((0, -1), (-1, -1), (-2, 0)): g.px(x, y, PANTS)
        g.px(-3, 0, BOOT); g.px(-4, 0, BLADE)
    g.outline(OL)
    for (x, y) in ((-8, 3), (-11, 4), (-14, 3), (-17, 4), (-10, 2), (-20, 3)): g.px(x, y, '#ffffff')      # ice shavings
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

# ------------------------------------------------------------------ easter egg: two little figures who appear where you click
# (desktop only, see menu.js). Facing right; menu.js mirrors them. 'w' = walking (2 frames), 's' = swimming (head and
# shoulders above the water, 2 frames of ripples). A has short blonde hair and a burgundy top, B longer brown hair and a checked cardigan.
def egg_figure(kind, frame, swim=False):
    g = Grid()
    SKIN = '#f1c27d'
    if kind == 'A':       # short blonde hair, burgundy top, stone-coloured trousers
        HAIR, TOP, TOPD, PANTS = '#f0cf6a', '#8c1c3a', '#6e1530', '#b9ae98'
        g.rect(-1, -11, 1, -11, HAIR); g.px(-1, -10, HAIR); g.px(0, -10, HAIR); g.px(1, -10, HAIR)
        g.rect(-1, -9, 1, -8, SKIN)
        g.rect(-1, -7, 1, -4, TOP); g.px(0, -5, TOPD); g.px(-2, -6, TOP); g.px(2, -6, TOP)
    else:                 # slightly longer brown hair, brown-and-green checked cardigan, dark trousers
        HAIR, BRN, GRN, PANTS = '#6b4226', '#8b5a2b', '#4f8f4a', '#464a5c'
        g.rect(-1, -11, 1, -10, HAIR); g.px(-2, -10, HAIR); g.px(-2, -9, HAIR)
        g.rect(-1, -9, 1, -8, SKIN)
        for y in range(-7, -3):
            for x in (-1, 0, 1): g.px(x, y, BRN if (x + y) % 2 == 0 else GRN)
        g.px(-2, -6, BRN); g.px(2, -6, GRN)
        g.px(0, -7, '#ffffff'); g.px(1, -7, '#ffffff'); g.px(1, -6, '#ffffff')       # white undershirt showing at the open collar
    if swim:
        g.outline(OL)
        for x in ((-3, -2, 2, 3) if frame == 0 else (-2, -1, 1, 2)): g.px(x, -6, '.shm')
        return g
    if frame == 0:
        for y in (-3, -2): g.px(-1, y, PANTS); g.px(1, y, PANTS)
        g.px(-1, -1, '#2b2438'); g.px(1, -1, '#2b2438')
    else:
        for y in (-3, -2): g.px(0, y, PANTS)
        g.px(0, -1, '#2b2438'); g.px(-1, -1, '#2b2438')
    g.outline(OL)
    return g
def egg_sit():
    """Both figures side by side on a park bench, seen from the front (the third click)."""
    g = Grid()
    WOOD, WOODD, WOODL, LEG, SHOE, SKIN = '#b87a46', '#8a5a2c', '#d39a5e', '#4a3a2a', '#2b2438', '#f1c27d'
    g.rect(-6, -8, 6, -8, WOODL); g.rect(-6, -7, 6, -6, WOOD)                    # backrest
    g.rect(-6, -5, -6, -1, LEG); g.rect(6, -5, 6, -1, LEG)                       # posts
    cx = -3                                                                      # blonde, burgundy top, stone trousers
    for x in (cx - 1, cx, cx + 1): g.px(x, -11, '#f0cf6a'); g.px(x, -10, '#f0cf6a')
    g.rect(cx - 1, -9, cx + 1, -8, SKIN)
    g.rect(cx - 1, -7, cx + 1, -5, '#8c1c3a'); g.px(cx, -6, '#6e1530')
    for x in (cx - 2, cx + 2): g.rect(x, -7, x, -6, '#8c1c3a'); g.px(x, -5, SKIN)
    g.rect(cx - 1, -3, cx + 1, -2, '#b9ae98'); g.px(cx - 1, -1, SHOE); g.px(cx + 1, -1, SHOE)
    cx = 3                                                                       # longer brown hair, checked cardigan
    HAIR, BRN, GRN = '#6b4226', '#8b5a2b', '#4f8f4a'
    g.rect(cx - 1, -11, cx + 1, -10, HAIR)
    for x in (cx - 2, cx + 2): g.rect(x, -10, x, -9, HAIR)
    g.rect(cx - 1, -9, cx + 1, -8, SKIN)
    for y in range(-7, -4):
        for x in range(cx - 2, cx + 3):
            if abs(x - cx) <= 1 or y >= -7 and y <= -6: g.px(x, y, BRN if (x + y) % 2 == 0 else GRN)
    g.px(cx, -7, '#ffffff'); g.px(cx, -6, '#ffffff')                              # white undershirt at the open collar
    for x in (cx - 2, cx + 2): g.px(x, -5, SKIN)
    g.rect(cx - 1, -3, cx + 1, -2, '#464a5c'); g.px(cx - 1, -1, SHOE); g.px(cx + 1, -1, SHOE)
    g.rect(-6, -4, 6, -4, WOODL)                                                 # seat (the legs hang below it)
    g.outline(OL)
    return g
EGG_BENCH = f'<g id="egg-bench">{svg_paths(egg_sit())}</g>'
EGG_DEFS = EGG_BENCH + "".join(f'<g id="egg-{k}-{t}{f}">{svg_paths(egg_figure(k, f, t == "s"))}</g>' for k in "AB" for t in "ws" for f in (0, 1))
EGG_OBST = ";".join(f'{c["x"]},{c["y"] - (62 if c["y"] < 100 else 46)},{c["y"] + 17},32' for c in CAMPUSES.values())     # x, top, bottom, half-width of each building

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
	<a class="skip-link" href="#main">Skip to content</a>
	<div class="hero">
		<div class="sky" aria-hidden="true"></div>
		<svg class="galaxy" viewBox="0 0 @@GALW@@ @@GALH@@" shape-rendering="crispEdges" aria-hidden="true" focusable="false">@@GALAXY@@</svg>

		@@TOD@@

		<div class="intro">
			<h1>The Local Group</h1>
			<p class="tagline">A discussion and seminar group for galactic dynamics and near-field cosmology.</p>
			<nav class="buttons" aria-label="The Local Group">
				<a class="btn" href="schedule.html">Schedule</a>
				<a class="btn" href="https://forms.gle/UewtgsnsCusrJGoR7" target="_blank" rel="noopener">Mailing List<span class="sr"> (opens in a new tab)</span></a>
				<a class="btn" href="about.html">About</a>
			</nav>
		</div>
	</div>

	<main class="scene-wrap" id="main">
		<h2 class="sr">Meeting locations</h2>
		<svg class="scene" role="group" aria-label="Pixel-art map of the three host institutions: Harvard and MIT on the north bank of the river, Boston University on the south bank, joined by a bridge. Select a building to see its meetings." viewBox="@@VIEW@@" data-view="@@VIEW@@" data-compact="@@COMPACT@@" data-ctop="@@CTOP@@" data-cbot="@@CBOT@@" data-river="@@RIVERCFG@@" data-bridge="@@BRIDGEX@@" data-obst="@@OBST@@" data-w="@@W@@" preserveAspectRatio="xMidYMid meet" shape-rendering="crispEdges" role="group" aria-label="Pixel map of the Charles River with Harvard and MIT on the north bank and Boston University on the south bank">
			<defs>
				@@EGGDEFS@@
				<!-- night: every colour moves 45% of the way towards a deep blue (same blend as the page background in style.css) -->
				<filter id="dim" color-interpolation-filters="sRGB" x="-5%" y="-5%" width="110%" height="110%">
					<feColorMatrix type="matrix" values="0.55 0 0 0 0.025  0 0.55 0 0 0.039  0 0 0.55 0 0.1125  0 0 0 1 0"/>
				</filter>
			</defs>
			<g aria-hidden="true" class="dim">
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
					<g id="egg-swim" aria-hidden="true" pointer-events="none"></g>
					<g transform="translate(@@BRIDGEX@@ 0)">@@BRIDGE@@</g>
				</g>
				@@TREES@@
			</g>

			@@OBSERVERS@@
			@@CAMPUSES@@
			<g id="egg-walk" class="dim" aria-hidden="true" pointer-events="none"></g>
			@@PARTICLES@@
		</svg>
	</main>
</body>
</html>
'''

html = (HTML.replace("@@TOD@@", TOD_BUTTON).replace("@@VIEW@@", VIEW).replace("@@COMPACT@@", COMPACT_VIEW).replace("@@CTOP@@", str(compact_top())).replace("@@CBOT@@", "226").replace("@@BRIDGE@@", svg_paths(bridge())).replace("@@BRIDGEX@@", str(BRIDGE_X)).replace("@@OBSERVERS@@", observers()).replace("@@W@@", str(W)).replace("@@GALAXY@@", GALAXY).replace("@@GALW@@", str(GAL_W)).replace("@@GALH@@", str(GAL_H))
        .replace("@@RIVERCFG@@", f"{RIVER_Y},{AMP},{PERIOD},{HALF}").replace("@@EGGDEFS@@", EGG_DEFS).replace("@@OBST@@", EGG_OBST)
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

def food_icon():
    """A mug of coffee beside a chocolate chip cookie."""
    g = Grid(); MUG, COF, STEAM = '#e8704f', '#5a3a22', '#c8d0e0'
    g.rect(0, 5, 5, 10, MUG); g.rect(1, 5, 4, 6, COF); g.px(1, 7, '#f08c6c'); g.px(1, 8, '#f08c6c')
    for x, y in ((6, 6), (7, 7), (7, 8), (6, 9)): g.px(x, y, MUG)                    # handle
    for x, y in ((2, 3), (3, 2), (2, 1), (3, 0)): g.px(x, y, STEAM)                  # steam
    COOK, COOKD, CHIP = '#e3ac60', '#c58a3e', '#4a2c1a'                              # a chocolate chip cookie
    cx, cy, r = 16, 6, 4.8
    for y in range(0, 12):
        for x in range(10, 23):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r * r: g.px(x, y, COOKD if d2 > (r - 1.3) ** 2 and (x + y) > cx + cy - 1 else COOK)
    for x, y in ((14, 4), (17, 3), (18, 6), (15, 7), (17, 9), (13, 8)): g.px(x, y, CHIP)   # chocolate chips
    for x, y in ((14, 5), (18, 7)): g.px(x, y, CHIP)
    g.outline(OL)
    return g
FOOD_ICON = icon_svg(food_icon(), 2, "f-svg")

def pie_icon(frac):
    """A little pie chart, filled clockwise from 12 o'clock by `frac` of the circle (13 x 13)."""
    g = Grid(); N, R = 13, 6.2
    for y in range(N):
        for x in range(N):
            dx, dy = x - 6, y - 6
            if dx * dx + dy * dy > R * R: continue
            ang = (math.atan2(dx, -dy) % (2 * math.pi)) / (2 * math.pi)
            g.px(x, y, '#e8704f' if (dx == 0 and dy == 0) or ang < frac else '#ffffff')
    g.outline(OL)
    return g

# How often a meeting happens: the pie shows how much of a year it fills (one month of twelve, or one semester of three).
FREQUENCIES = {"monthly": ("Monthly", "once a month", 1 / 12), "semesterly": ("Semesterly", "once a semester", 1 / 3)}
FREQ_ICON = {k: icon_svg(pie_icon(v[2]), 2, "q-svg") for k, v in FREQUENCIES.items()}

TALK_TYPES = {"chalk": ("Chalk talk", "at the board, no slides", chalk_icon),
              "colloquium": ("Colloquium", "a talk with slides", projector_icon),
              "workshop": ("Workshop", "open group discussion", table_icon)}
TALK_ICON = {k: icon_svg(v[2](), 2, "t-svg") for k, v in TALK_TYPES.items()}
_WIDTHS = {k: (lambda b: b[2] - b[0] + 1)(c['sprite']().bbox()) for k, c in CAMPUSES.items()}
assert len(set(_WIDTHS.values())) == 1, f'campus icons must all be the same width: {_WIDTHS}'
CAMPUS_ICON = {k: icon_svg(c["sprite"](), 2, "m-svg", snow=True) for k, c in CAMPUSES.items()}

# Where each meeting place is, for the directions links (a campus without an entry here, e.g. Harvard for now,
# gets no map icon and its room is not a link). Directions open Google Maps with the place as the destination.
DIRECTIONS = {
    "harvard": dict(building="Center for Astrophysics | Harvard & Smithsonian", place="Center for Astrophysics, 60 Garden St, Cambridge, MA 02138", address="60 Garden Street, Cambridge, MA 02138"),
    "mit": dict(building="MIT Kavli Institute", place="MIT Building 37, 70 Vassar St, Cambridge, MA 02139", address="70 Vassar Street, Cambridge, MA 02139"),
    "bu":  dict(building="College of Arts & Sciences", place="College of Arts & Sciences, 725 Commonwealth Ave, Boston, MA 02215", address="725 Commonwealth Avenue, Boston, MA 02215"),
}
def maps_url(key):
    return "https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote(DIRECTIONS[key]["place"])

def map_icon():
    """A little folded paper map with a red pin (16 x 14)."""
    g = Grid(); P1, P2, P3, RD = '#a8d98a', '#f6efc0', '#9fd0f2', '#e63946'
    g.rect(0, 5, 4, 13, P1); g.rect(5, 4, 10, 12, P2); g.rect(11, 5, 15, 13, P3)       # three folded panels
    g.rect(5, 12, 10, 13, P2); g.rect(0, 13, 15, 13, P1); g.rect(11, 13, 15, 13, P3)
    for x, y in ((6, 10), (7, 9), (9, 11), (10, 10)): g.px(x, y, '#d9c98a')            # a dashed road
    for x, y in ((12, 7), (13, 8), (13, 9), (14, 10), (14, 11)): g.px(x, y, '#5bb8f0')  # a river
    for x, y in ((1, 7), (2, 8), (1, 10), (3, 11)): g.px(x, y, '#7cc060')              # a few trees
    g.disc(8, 2, 2.4, 2.4, RD); g.rect(7, 4, 9, 4, RD); g.px(8, 5, RD); g.px(8, 6, RD)  # the pin
    g.px(8, 2, '#ffffff')
    g.outline(OL)
    return g
MAP_ICON = icon_svg(map_icon(), 2, "dir-svg")

def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def tba(value, label):
    v = (value or "").strip()
    return f"{label} TBA" if v.upper() in ("", "TBA") else v

def load_schedule(): return json.loads((HERE / "schedule.json").read_text(encoding="utf-8"))

def meeting_card(m, venues, on_campus_page=False):
    """One meeting. On the main schedule the campus icon and name link to that campus's page."""
    d = datetime.date.fromisoformat(m["date"]); c = CAMPUSES[m["campus"]]
    talks = "".join(
        f'<li data-type="{t["type"]}"><span class="t-ico" title="{TALK_TYPES[t["type"]][0]}">{TALK_ICON[t["type"]]}<span class="sr">{TALK_TYPES[t["type"]][0]}: </span></span>'
        f'<span class="t-text"><span class="t-title">{esc(t.get("title") or "Untitled talk")}</span>'
        f'<span class="t-speaker">{esc(t.get("speaker") or "Speaker TBA")}</span></span></li>' for t in m["talks"])
    room = tba(m.get("room") or venues.get(m["campus"], {}).get("room"), "Room")
    freq = (m.get("frequency") or "monthly").strip().lower()
    if freq not in FREQUENCIES: raise SystemExit(f'schedule.json: frequency must be one of {", ".join(FREQUENCIES)} (meeting {m["date"]})')
    room_html = esc(room)
    food_html = esc(m.get("food") or "TBA")
    if (m.get("food_url") or "").strip():                                           # the caterer's name links to their website
        food_html = f'<a class="room-link" href="{esc(m["food_url"].strip())}" target="_blank" rel="noopener">{food_html}<span class="sr"> (opens in a new tab)</span></a>'
    if m["campus"] in DIRECTIONS and room.upper() != "ROOM TBA":                    # a known room links to its directions
        room_html = (f'<a class="room-link" href="{esc(maps_url(m["campus"]))}" target="_blank" rel="noopener" '
                     f'title="Directions on Google Maps">{esc(room)}<span class="sr">, directions on Google Maps (opens in a new tab)</span></a>')
    if on_campus_page:
        ico, where = "", f"{d:%A}"
    else:
        ico = f'<a class="m-ico" href="{c["href"]}" tabindex="-1" aria-hidden="true">{CAMPUS_ICON[m["campus"]]}</a>'     # the name link beside it does the job for keyboards and screen readers
        where = f'{d:%A} at <a href="{c["href"]}">{c["label"]}<span class="sr">: room and all of its meetings</span></a>'
    return (f'<li id="{m["date"]}" data-date="{m["date"]}" data-freq="{freq}"><article class="card meeting" style="--c:{c["color"]}">'
            f'<header>{ico}<div><h2><time datetime="{m["date"]}">{d:%B} {d.day}, {d.year}</time></h2><p class="m-where">{where}</p>'
            f'<p class="m-when"><span>{esc(tba(m.get("time"), "Time"))}</span><span>{room_html}</span></p>'
            f'</div><span class="m-freq" role="img" title="{esc(FREQUENCIES[freq][0])}: {esc(FREQUENCIES[freq][1])}" '
            f'aria-label="{esc(FREQUENCIES[freq][0])} meeting: {esc(FREQUENCIES[freq][1])}">{FREQ_ICON[freq]}</span></header>'
            f'<ul class="talks">{talks}</ul>'
            f'<p class="m-food"><span class="f-ico">{FOOD_ICON}</span><span>Catering provided by {food_html}</span></p></article></li>')

def boston_today():
    """Today's date in Boston (the page's JavaScript re-sorts with the visitor's clock, so a meeting moves to 'Past events' the day after it)."""
    try:
        import zoneinfo
        return datetime.datetime.now(zoneinfo.ZoneInfo("America/New_York")).date()
    except Exception:
        return datetime.date.today()

def meeting_lists(ms, venues, on_campus_page=False):
    """Upcoming meetings (soonest first), then a 'Past events' toggle holding the older ones (most recent first)."""
    today = boston_today().isoformat()
    up = sorted([m for m in ms if m["date"] >= today], key=lambda m: m["date"])
    past = sorted([m for m in ms if m["date"] < today], key=lambda m: m["date"], reverse=True)
    here = " here" if on_campus_page else ""
    none, noup = f"No meetings are scheduled{here} yet.", f"No upcoming meetings are scheduled{here} yet."
    msg = "" if up else (noup if past else none)
    card = lambda m: meeting_card(m, venues, on_campus_page=on_campus_page)
    return (f'<ol class="meetings" id="upcoming">' + "".join(card(m) for m in up) + '</ol>\n\t\t'
            f'<p class="card empty" id="no-upcoming" data-none="{esc(none)}" data-noup="{esc(noup)}" '
            f'data-nomatch="No upcoming meetings match this selection."{"" if msg else " hidden"}>{esc(msg)}</p>\n\t\t'
            f'<section class="past" id="past" aria-label="Past events"{"" if past else " hidden"}>'
            f'<h2 class="past-h">Past events</h2>'
            f'<button type="button" class="past-toggle" aria-expanded="false" aria-controls="past-list">'
            f'<span class="pt-sign" aria-hidden="true">+</span><span>Past events</span> <span class="pt-count">({len(past)})</span></button>'
            f'<ol class="meetings past-list" id="past-list">' + "".join(card(m) for m in past) + '</ol></section>')

def schedule_page():
    data = load_schedule(); venues = data.get("venues", {})
    def key_item(kind, k, icon, name, desc):
        return (f'<li><button type="button" class="key-btn" data-kind="{kind}" data-val="{k}" aria-pressed="false">'
                f'<span class="l-ico">{icon}</span><span><b>{name}</b><br>{esc(desc)}</span></button></li>')
    legend = "".join(key_item("type", k, TALK_ICON[k], name, desc) for k, (name, desc, _) in TALK_TYPES.items())
    freqs = "".join(key_item("freq", k, FREQ_ICON[k], name, desc) for k, (name, desc, _) in FREQUENCIES.items())
    meetings = meeting_lists(data["meetings"], venues)
    main = (f'<section class="card legend" id="key" aria-label="Key">'
            f'<div class="legend-head"><h2>Key<span class="key-note" hidden> (filtered)</span></h2>'
            f'<button type="button" class="key-toggle" aria-expanded="true" aria-controls="key-body" title="Hide the key">'
            f'<span aria-hidden="true">-</span><span class="sr">Hide the key</span></button></div>'
            f'<div class="legend-body" id="key-body"><div><h3>Talk types</h3><ul>{legend}</ul></div>'
            f'<div><h3>Meeting frequency</h3><ul>{freqs}</ul></div></div></section>\n\t\t'
            + meetings + '\n\t\t'
            f'<p class="sr" id="filter-status" role="status" aria-live="polite"></p>\n\t\t'
            f'<p class="card empty" id="no-match" hidden>No meetings match this selection. Click the highlighted icon in the key to clear it.</p>')
    page = subpage("Schedule", "Upcoming meetings and talks.", "Upcoming meetings and talks of The Local Group, a discussion and seminar group for galactic dynamics and near-field cosmology.", main)
    return page.replace("</body>", '<script defer src="schedule.js"></script>\n</body>')

def campus_page(key):
    """Harvard / MIT / BU page: the room at the top, then only the meetings held there."""
    c = CAMPUSES[key]; data = load_schedule(); venues = data.get("venues", {})
    room = tba(venues.get(key, {}).get("room"), "Room")
    mine = [m for m in sorted(data["meetings"], key=lambda m: m["date"]) if m["campus"] == key]
    body = meeting_lists(mine, venues, on_campus_page=True)
    dr = DIRECTIONS.get(key)
    bldg = (f'<p class="v-bldg">{esc(dr["building"])}</p><p class="v-bldg v-addr">{esc(dr["address"])}</p>') if dr else ""
    link = (f'<a class="dir" href="{esc(maps_url(key))}" target="_blank" rel="noopener" title="Directions on Google Maps" '
            f'aria-label="Directions to {esc(dr["building"])} on Google Maps (opens in a new tab)">{MAP_ICON}<span>Directions</span></a>') if dr else ""
    main = (f'<section class="card venue" style="--c:{c["color"]}"><span class="m-ico">{CAMPUS_ICON[key]}</span>'
            f'<div><h2>Where</h2><p class="v-room">{esc(room)}</p>{bldg}</div>{link}</section>\n\t\t' + body)
    return subpage(c["label"], f"Meetings hosted at {c['label']}.", f"Meetings of The Local Group hosted at {c['label']}, with the room and the schedule of talks.", main).replace("</body>", '<script defer src="schedule.js"></script>\n</body>')

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
	<a class="skip-link" href="#main">Skip to content</a>
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
        site = (f'<a class="p-site" href="{esc(url)}" target="_blank" rel="noopener">{esc(url.split("//")[-1].strip("/"))}<span class="sr"> (opens in a new tab)</span></a>' if url
                else '<span class="p-site tba">Website TBA</span>')
        rows.append(f'<li><span class="p-ico">{star}</span><div><h3>{esc(o["name"])}</h3>'
                    f'<p class="p-pos{"" if pos else " tba"}">{esc(pos) if pos else "Position TBA"}</p>{site}</div></li>')
    panels = []
    for mt in data.get("meetings", []):                                   # one panel per kind of meeting: the pie, a heading, and a description
        kind = mt["kind"]
        if kind not in FREQUENCIES: raise SystemExit(f'about.json: meetings kind must be one of {", ".join(FREQUENCIES)}')
        name, desc, _ = FREQUENCIES[kind]
        paras = "".join(f"<p>{esc(t.strip())}</p>" for t in (mt.get("text") or "").split("\n\n") if t.strip())
        panels.append(f'<section class="card about-meet"><span class="am-ico">{icon_svg(pie_icon(FREQUENCIES[kind][2]), 3, "q-svg")}</span>'
                      f'<div><h2>{esc(mt.get("title") or name + " meetings")}</h2><p class="am-freq">{esc(desc[0].upper() + desc[1:])}</p>{paras}</div></section>')
    main = "\n\t\t".join(panels) + ('\n\t\t' if panels else '') + '<section class="card organisers"><h2>Organisers</h2><ul class="people">' + "".join(rows) + '</ul></section>'
    return subpage("About", "What is The Local Group?", "About The Local Group, a discussion and seminar group for galactic dynamics and near-field cosmology, and the people who organise it.", main)

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
	<meta name="theme-color" content="#0f1535">
	<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' shape-rendering='crispEdges'%3E%3Crect width='16' height='16' fill='%238fd16c'/%3E%3Cpath fill='%233f95d8' d='M0 6h16v6H0z'/%3E%3Cpath fill='%235bb8f0' d='M0 6h16v4H0z'/%3E%3C/svg%3E">
	<link rel="preload" href="PressStart2P.woff2" as="font" type="font/woff2" crossorigin>
	<script src="season.js"></script>
	<link rel="stylesheet" href="style.css">
</head>
<body class="sub" style="--c:@@COLOR@@">
	<a class="skip-link" href="#main">Skip to content</a>
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
_V = {n: _ver(n) for n in ("style.css", "menu.js", "season.js", "schedule.js")}
for _page in OUT.glob("*.html"):
    _t = _page.read_text(encoding="utf-8")
    for _n, _h in _V.items():
        _t = re.sub(r'(?:src|href)="%s(?:\?v=\w+)?"' % re.escape(_n),
                    lambda m, _n=_n, _h=_h: m.group(0).split('"')[0] + '"%s?v=%s"' % (_n, _h), _t)
    _page.write_text(_t, encoding="utf-8")
print("built The Local Group:", NEXT["campus"], "-", NEXT_DATE)
