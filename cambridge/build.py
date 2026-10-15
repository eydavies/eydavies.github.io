#!/usr/bin/env python3
"""Builds the University of Cambridge page: cambridge/index.html.

A zoomable pixel-art map of 28 Cambridge colleges in the style of The Local Group's home page (local-group/). The layout
follows an illustrated map of the town: the River Cam comes in from the lower left, runs up the Backs, hooks round St John's
and Magdalene, and leaves down the right-hand side. It borrows the Local Group's drawing helpers by running
local-group/build.py into a temporary folder, and links to that site's style.css and season.js, so the look (seasons, night
mode, header, fonts) stays in step. Nothing in local-group/ links back here.

    cd <repo root> && python3 cambridge/build.py

Writes cambridge/index.html only. Positions come from REF (coordinates on the reference map), scaled by F, then nudged apart
until no building or name tag overlaps. The map is a schematic, not a survey.
"""
import contextlib, hashlib, io, math, pathlib, random, runpy, shutil, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
LG = HERE.parent / "local-group"
sys.path.insert(0, str(HERE))

# ------------------------------------------------------------------ borrow the Local Group's helpers
_tmp = pathlib.Path(tempfile.mkdtemp())
for _f in LG.iterdir():
    if _f.is_file() and _f.suffix != ".html" and _f.name != "build.py": shutil.copy(_f, _tmp / _f.name)
_argv = sys.argv
sys.argv = ["build.py", "--out", str(_tmp)]
try:
    with contextlib.redirect_stdout(io.StringIO()):
        G = runpy.run_path(str(LG / "build.py"), run_name="lg_build")
finally:
    sys.argv = _argv
    shutil.rmtree(_tmp, ignore_errors=True)
Grid, svg_paths, plaza, tag = G["Grid"], G["svg_paths"], G["plaza"], G["tag"]
night_lights, snow_layer, OL, tree = G["night_lights"], G["snow_layer"], G["OL"], G["tree"]
TOD_BUTTON, GALAXY, GAL_W, GAL_H, BUILD_SEASON = G["TOD_BUTTON"], G["GALAXY"], G["GAL_W"], G["GAL_H"], G["BUILD_SEASON"]
text_width, boat_svg = G["text_width"], G["boat_svg"]

import sprites
GL = sprites.GL
SPR = sprites.build_all(Grid, OL)

# ------------------------------------------------------------------ the colleges
# name, tag text, colour (white-on-colour must be readable: checked below), website, sprite, position on the reference map
COLLEGES = [
    # the Backs, north to south
    dict(name="St John's College", word="ST JOHNS", color="#b3202d", url="https://www.joh.cam.ac.uk", sprite="johns", ref=(1025, 835), backs=1),
    dict(name="Trinity College", word="TRINITY", color="#1f3b8a", url="https://www.trin.cam.ac.uk", sprite="trinity", ref=(720, 820), backs=1),
    dict(name="Trinity Hall", word="TRIN HALL", color="#2d2d38", url="https://www.trinhall.cam.ac.uk", sprite="trinhall", ref=(580, 862), backs=1),
    dict(name="Clare College", word="CLARE", color="#86610a", url="https://www.clare.cam.ac.uk", sprite="clare", ref=(505, 892), backs=1),
    dict(name="King's College", word="KINGS", color="#6a1b9a", url="https://www.kings.cam.ac.uk", sprite="kings", ref=(415, 1005), backs=1),
    dict(name="Queens' College", word="QUEENS", color="#2e7d32", url="https://www.queens.cam.ac.uk", sprite="queens", ref=(310, 1048), backs=1),
    # the middle of town
    dict(name="Gonville & Caius College", word="CAIUS", color="#1d6fa5", url="https://www.cai.cam.ac.uk", sprite="caius", ref=(735, 975)),
    dict(name="Corpus Christi College", word="CORPUS", color="#7a1d2b", url="https://www.corpus.cam.ac.uk", sprite="corpus", ref=(470, 1217)),
    dict(name="St Catharine's College", word="ST CATZ", color="#127a78", url="https://www.caths.cam.ac.uk", sprite="stcath", ref=(295, 1115)),
    dict(name="Peterhouse", word="PETERHOUSE", color="#5a5f6b", url="https://www.pet.cam.ac.uk", sprite="peter", ref=(245, 1212)),
    dict(name="Pembroke College", word="PEMBROKE", color="#c0392b", url="https://www.pem.cam.ac.uk", sprite="pembroke", ref=(368, 1465)),
    dict(name="Christ's College", word="CHRISTS", color="#a85320", url="https://www.christs.cam.ac.uk", sprite="christs", ref=(740, 1243)),
    dict(name="Sidney Sussex College", word="SIDNEY", color="#5b3a1e", url="https://www.sid.cam.ac.uk", sprite="sidney", ref=(930, 1212)),
    dict(name="Emmanuel College", word="EMMANUEL", color="#b0447a", url="https://www.emma.cam.ac.uk", sprite="emma", ref=(672, 1678)),
    dict(name="Jesus College", word="JESUS", color="#8e1b3a", url="https://www.jesus.cam.ac.uk", sprite="jesus", ref=(1085, 1435)),
    dict(name="Magdalene College", word="MAGDALENE", color="#6b1f6f", url="https://www.magd.cam.ac.uk", sprite="magdalene", ref=(1330, 930)),
    # west and south
    dict(name="Darwin College", word="DARWIN", color="#37474f", url="https://www.darwin.cam.ac.uk", sprite="darwin", ref=(85, 1080)),
    dict(name="Selwyn College", word="SELWYN", color="#c2185b", url="https://www.selwyn.cam.ac.uk", sprite="selwyn", ref=(175, 830)),
    dict(name="Robinson College", word="ROBINSON", color="#a83232", url="https://www.robinson.cam.ac.uk", sprite="robinson", ref=(405, 515)),
    dict(name="Downing College", word="DOWNING", color="#1e5e8e", url="https://www.dow.cam.ac.uk", sprite="downing", ref=(122, 1607)),
    dict(name="Homerton College", word="HOMERTON", color="#117a65", url="https://www.homerton.cam.ac.uk", sprite="homerton", ref=(140, 1930)),
    dict(name="Hughes Hall", word="HUGHES HALL", color="#6d4c41", url="https://www.hughes.cam.ac.uk", sprite="hughes", ref=(590, 1850)),
    # north
    dict(name="Churchill College", word="CHURCHILL", color="#3c4a5c", url="https://www.chu.cam.ac.uk", sprite="churchill", ref=(990, 105)),
    dict(name="Girton College", word="GIRTON", color="#8f1d3a", url="https://www.girton.cam.ac.uk", sprite="girton", ref=(1375, 40)),
    dict(name="Fitzwilliam College", word="FITZWILLIAM", color="#2b6b4a", url="https://www.fitz.cam.ac.uk", sprite="fitz", ref=(1255, 272)),
    dict(name="Lucy Cavendish College", word="LUCY CAVENDISH", color="#8a2f87", url="https://www.lucy-cav.cam.ac.uk", sprite="lucy", ref=(1040, 305)),
    dict(name="Murray Edwards College", word="MURRAY EDWARDS", color="#b04a00", url="https://www.murrayedwards.cam.ac.uk", sprite="murray", ref=(1335, 445)),
    dict(name="St Edmund's College", word="ST EDMUNDS", color="#2a5f8f", url="https://www.st-edmunds.cam.ac.uk", sprite="stedmunds", ref=(1100, 488)),
]
assert len(COLLEGES) == 28
RX = 16                                        # plaza half-width

def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
for c in COLLEGES:
    ratio = 1.05 / (_lum(c["color"]) + .05)
    assert ratio >= 4.5, f'{c["name"]}: tag colour {c["color"]} has contrast {ratio:.2f} against white'

F, OX, OY = 0.30, -6, 14                       # reference-map pixels -> art pixels (1 SVG unit = 1 art pixel)
def art(p): return (F * p[0] + OX, F * p[1] + OY)

# ------------------------------------------------------------------ the river Cam: in from the lower left, up the Backs, round the hook, out down the right
REF_RIVER = [(-1500, 1330), (-700, 1230), (0, 1170), (130, 1140), (215, 1100), (285, 1050), (350, 1000), (415, 955), (480, 915),
             (545, 885), (620, 845), (700, 795), (790, 768), (870, 762), (940, 768), (995, 785), (1050, 835), (1095, 900),
             (1135, 955), (1215, 1010), (1295, 1085), (1355, 1165), (1395, 1255), (1410, 1400), (1405, 1520), (1370, 1620),
             (1295, 1700), (1210, 1770), (1160, 1860), (1130, 1960), (1120, 2700)]
KEY = [art(p) for p in REF_RIVER]
dense = []
for (ax, ay), (bx, by) in zip(KEY, KEY[1:]):
    n = max(1, int(math.hypot(bx - ax, by - ay)))
    for i in range(n): dense.append((ax + (bx - ax) * i / n, ay + (by - ay) * i / n))
dense.append(KEY[-1])
def smooth(pts, k=16):
    out = []
    for i in range(len(pts)):
        lo, hi = max(0, i - k), min(len(pts) - 1, i + k)
        out.append((sum(p[0] for p in pts[lo:hi + 1]) / (hi - lo + 1), sum(p[1] for p in pts[lo:hi + 1]) / (hi - lo + 1)))
    return out
CENTRE = smooth(dense)
HALF = 7
RIVER = {}
for (cx, cy) in CENTRE:
    for dy in range(-HALF - 1, HALF + 2):
        for dx in range(-HALF - 1, HALF + 2):
            if dx * dx + dy * dy <= (HALF + .3) ** 2: RIVER[(round(cx) + dx, round(cy) + dy)] = 1
river = Grid()
for (x, y) in RIVER:
    river.px(x, y, '.rv1' if (x, y + 1) in RIVER and (x, y + 2) in RIVER else '.rv2')
river.outline('.rvo')
RIVER_PTS = CENTRE[::3]
def river_dist(x, y):
    return min(math.hypot(x - cx, y - cy) for cx, cy in RIVER_PTS)

def shimmer(shift):
    g = Grid()
    for k in range(-2, len(CENTRE) // 30 + 2):
        i = int(k * 30 + shift * 2.3)
        if not 0 <= i < len(CENTRE): continue
        cx, cy = CENTRE[i]
        x, y = round(cx) + (-4 if k % 2 else 2), round(cy) + (-3 if k % 3 else 3)
        if all((xx, y) in RIVER for xx in range(x - 1, x + 4)) and (x, y - 1) in RIVER and (x, y + 1) in RIVER: g.rect(x, y, x + 2, y, '.shm')
    return g
SHIM = [shimmer(0), shimmer(8), shimmer(16)]

# ------------------------------------------------------------------ placing the colleges: start from the reference map, then nudge apart
for c in COLLEGES:
    c["x"], c["y"] = art(c["ref"])
    c["y"] += 22                               # the reference labels sit above their buildings
    c["hw"] = max(RX + 2, (text_width(c["word"]) + 6) // 2 + 3)
RP = []                                         # river points with their normals, for keeping buildings on their own bank
for i in range(0, len(RIVER_PTS), 2):
    j0, j1 = max(0, i - 3), min(len(RIVER_PTS) - 1, i + 3)
    tx_, ty_ = RIVER_PTS[j1][0] - RIVER_PTS[j0][0], RIVER_PTS[j1][1] - RIVER_PTS[j0][1]
    n_ = math.hypot(tx_, ty_) or 1
    RP.append((RIVER_PTS[i][0], RIVER_PTS[i][1], -ty_ / n_, tx_ / n_))
def bank(x, y):                                 # nearest river point, the distance to it, and which bank (+1 / -1) we are on
    best = min(RP, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
    d = math.hypot(x - best[0], y - best[1])
    return best, d, (1 if (x - best[0]) * best[2] + (y - best[1]) * best[3] >= 0 else -1)
def relax():
    cs = COLLEGES
    for c in cs:
        c["side"] = bank(c["x"], c["y"] - 8)[2]
        c["need"] = HALF + (13 if c["sprite"] in ("queens", "darwin") else 17)
    for it in range(900):
        moved = 0
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                a, b = cs[i], cs[j]
                ox = a["hw"] + b["hw"] + 4 - abs(a["x"] - b["x"])
                oy = 52 - abs(a["y"] - b["y"])
                if ox > 0 and oy > 0:
                    moved += 1
                    if ox < oy * 0.8:
                        s = 1 if a["x"] >= b["x"] else -1
                        a["x"] += s * ox / 2; b["x"] -= s * ox / 2
                    else:
                        s = 1 if a["y"] >= b["y"] else -1
                        a["y"] += s * oy / 2; b["y"] -= s * oy / 2
        for c in cs:
            c["x"] += (art(c["ref"])[0] - c["x"]) * 0.004; c["y"] += (art(c["ref"])[1] + 22 - c["y"]) * 0.004
            (px_, py_, nx_, ny_), d, side = bank(c["x"], c["y"] - 8)
            if d < 70 and (side != c["side"] or d < c["need"]):           # stay on the same bank, clear of the water
                moved += 1
                c["x"] = px_ + nx_ * c["side"] * c["need"]; c["y"] = py_ + ny_ * c["side"] * c["need"] + 8
        if it > 200 and moved == 0: break
relax()
for c in COLLEGES: c["x"], c["y"] = round(c["x"]), round(c["y"])
MINX = min(c["x"] - c["hw"] for c in COLLEGES) - 26; MAXX = max(c["x"] + c["hw"] for c in COLLEGES) + 26
MINY = min(c["y"] - 30 for c in COLLEGES) - 20; MAXY = max(c["y"] + 22 for c in COLLEGES) + 26
MAP = (MINX, MINY, MAXX, MAXY)
W, H = MAXX - MINX, MAXY - MINY

# ------------------------------------------------------------------ roads (a spanning tree joining every college), bridges, lawns
roads, bridges = Grid(), Grid()
RPTS = []                                       # road centre points, so trees keep off them
def stamp(g, cx, cy, r, col):
    for dy in range(-int(r) - 1, int(r) + 2):
        for dx in range(-int(r) - 1, int(r) + 2):
            if dx * dx + dy * dy <= r * r: g.px(round(cx) + dx, round(cy) + dy, col)
def path_pts(pts):
    out = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(1, int(max(abs(bx - ax), abs(by - ay)) * 2))
        for i in range(n + 1): out.append((ax + (bx - ax) * i / n, ay + (by - ay) * i / n))
    return out
def draw_path(pts):
    pp = path_pts(pts)
    wet = [(round(x), round(y)) in RIVER for (x, y) in pp]
    for (x, y), w in zip(pp, wet):
        if w: stamp(bridges, x, y, 3.7, '#a39d8e')
        else: stamp(roads, x, y, 2.5, '.pthd')
    for (x, y), w in zip(pp, wet):
        if w: stamp(bridges, x, y, 2.7, '#d9d2c0')
        else: stamp(roads, x, y, 1.5, '.pth'); RPTS.append((x, y))
nodes = [(c["x"], c["y"] + 1) for c in COLLEGES]
inT, edges = {0}, []
while len(inT) < len(nodes):                    # Prim's minimum spanning tree
    best = None
    for i in inT:
        for j in range(len(nodes)):
            if j in inT: continue
            d = math.hypot(nodes[i][0] - nodes[j][0], nodes[i][1] - nodes[j][1])
            if best is None or d < best[0]: best = (d, i, j)
    _, i, j = best; inT.add(j); edges.append((i, j))
for (i, j) in edges:
    (ax, ay), (bx, by) = nodes[i], nodes[j]
    mid = (bx, ay) if abs(bx - ax) > abs(by - ay) else (ax, by)       # one bend, like a street grid
    draw_path([(ax, ay), mid, (bx, by)])
for c in COLLEGES:                              # the Backs: a footbridge from each college over the river to the meadow
    if not c.get("backs"): continue
    cx, cy = min(RIVER_PTS, key=lambda p: math.hypot(p[0] - c["x"], p[1] - c["y"] - 8))
    dx, dy = cx - c["x"], cy - (c["y"] + 1)
    n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
    draw_path([(c["x"], c["y"] + 1), (cx + dx * (HALF + 12), cy + dy * (HALF + 12))])
bridges.outline(OL)

lawn, lawn_ref = Grid(), [(420, 1810, 95, 110), (810, 1530, 45, 75), (1270, 1640, 100, 70), (790, 430, 110, 110), (430, 395, 90, 40),
                          (1010, 640, 70, 28)]
for (rx_, ry_, ax_, ay_) in lawn_ref:
    cx, cy = art((rx_, ry_)); lawn.disc(cx, cy, ax_ * F, ay_ * F, '.lawn', cond=lambda x, y: (x, y) not in RIVER)
lawn.outline('.lawnd')
lawn_boxes = [(art((a - r, b - s)), art((a + r, b + s))) for a, b, r, s in lawn_ref]

# ------------------------------------------------------------------ the ground: tiles of tufts, flowers and leaves, repeated across the whole map
def tile(seed, n, draw, size=128):
    rnd = random.Random(seed); g = Grid()
    for _ in range(n): draw(g, rnd, size)
    return g
def d_tuft(g, r, s):
    x, y = r.randint(2, s - 3), r.randint(2, s - 3); g.px(x, y, '.tuft'); g.px(x + 1, y + 1, '.tuft'); g.px(x - 1, y + 1, '.tuft')
def d_flower(g, r, s): g.px(r.randint(1, s - 2), r.randint(1, s - 2), r.choice(['#ffffff', '#ffd1e0', '#fff3a0']))
def d_spring(g, r, s):
    cx, cy, col = r.randint(3, s - 4), r.randint(3, s - 4), r.choice(['#ff8fb8', '#ffffff', '#fff070', '#c9a6ff'])
    for _k in range(3): g.px(cx + r.randint(-2, 2), cy + r.randint(-1, 1), col)
def d_litter(g, r, s):
    cx, cy = r.randint(4, s - 5), r.randint(4, s - 5)
    for _k in range(4):
        col = r.choice(['#e8782a', '#d9452f', '#e9b52e', '#c2561c']); x, y = cx + r.randint(-3, 3), cy + r.randint(-1, 1)
        g.px(x, y, col); g.px(x + 1, y, col)
TILES = [("tuft", tile(11, 46, d_tuft)), ("flw", tile(12, 13, d_flower)), ("spr", tile(13, 7, d_spring)), ("lit", tile(14, 8, d_litter))]
tiles_defs = "".join(f'<pattern id="pt-{k}" width="128" height="128" patternUnits="userSpaceOnUse">{svg_paths(g)}</pattern>' for k, g in TILES)
GX0, GY0, GX1, GY1 = MINX - 700, MINY - 700, MAXX + 700, MAXY + 700                # the ground goes on well past the map
def ground_rect(k): return f'<rect x="{GX0}" y="{GY0}" width="{GX1 - GX0}" height="{GY1 - GY0}" fill="url(#pt-{k})"/>'

# ------------------------------------------------------------------ trees: spread evenly, never on a building, road or the river
BOXES = []
for c in COLLEGES:
    BOXES.append((c["x"] - RX - 4, c["y"] - 28, c["x"] + RX + 4, c["y"] + 6))                       # building and plaza
    BOXES.append((c["x"] - c["hw"] - 1, c["y"] + 3, c["x"] + c["hw"] + 1, c["y"] + 24))             # name tag
tree_cells = {}
def cell(x, y, k=20): return (int(x // k), int(y // k))
for (x, y) in RPTS: tree_cells.setdefault(cell(x, y, 10), []).append((x, y))
def tree_ok(x, y):
    for (bx0, by0, bx1, by1) in BOXES:
        if bx0 - 8 < x < bx1 + 8 and by0 - 3 < y < by1 + 17: return False
    cx, cy = cell(x, y - 6, 10)
    for i in range(cx - 1, cx + 2):
        for j in range(cy - 1, cy + 2):
            for (px_, py_) in tree_cells.get((i, j), ()):
                if abs(px_ - x) < 9 and -4 < py_ - y < 12 + 6: return False
    if river_dist(x, y - 6) < HALF + 9: return False
    return True
random.seed(23)
TREES = []                                      # (x, y, big)
grid_t = {}
def far_enough(x, y, d):
    cx, cy = cell(x, y, d)
    for i in range(cx - 1, cx + 2):
        for j in range(cy - 1, cy + 2):
            for (px_, py_) in grid_t.get((i, j), ()):
                if (px_ - x) ** 2 + ((py_ - y) * 1.1) ** 2 < d * d: return False
    return True
def sprinkle(n, x0, y0, x1, y1, d, tries):
    got = 0
    for _ in range(tries):
        if got >= n: break
        x, y = random.randint(x0, x1), random.randint(y0, y1)
        if any(a0[0] < x < a1[0] and a0[1] < y < a1[1] for a0, a1 in lawn_boxes) and random.random() < .8: continue
        if tree_ok(x, y) and far_enough(x, y, d):
            TREES.append((x, y, random.choice([0, 1, 1]))); grid_t.setdefault(cell(x, y, d), []).append((x, y)); got += 1
sprinkle(260, MINX, MINY + 16, MAXX, MAXY, 22, 60000)
sprinkle(220, MINX - 400, MINY - 300, MAXX + 400, MAXY + 300, 38, 40000)      # beyond the map: sparser
TREES.sort(key=lambda t: t[1])
def tree_def(big):
    t = tree(bool(big)); snow = snow_layer(t, pred=lambda c: c.startswith('.lf'))
    return f'<g id="tr{big}">{svg_paths(t)}<g class="snow">{svg_paths(snow)}</g></g>'
trees_svg = "".join(f'<g class="ctree tv{i % 3}" transform="translate({x} {y})"><use href="#tr{b}"/></g>' for i, (x, y, b) in enumerate(TREES))

# ------------------------------------------------------------------ falling leaves, petals and snow over the whole map
def particles(kind, n, colours, seed):
    rnd = random.Random(seed); out = []
    for _ in range(n):
        x = rnd.randint(MINX - 150, MAXX + 150); dur = rnd.uniform(18, 34); delay = -rnd.uniform(0, dur)
        drift = rnd.choice([-36, -24, -12, 12, 24, 36])
        w, h = (2, 1) if kind != 'snow' else ((2, 2) if rnd.random() < .22 else (1, 1))
        out.append(f'<g class="pt" style="--x:{x}px;--dx:{drift}px;animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
                   f'<rect class="sw" width="{w}" height="{h}" fill="{rnd.choice(colours)}"/></g>')
    return "".join(out)
PARTICLES = (f'<g class="p p-fall" aria-hidden="true" pointer-events="none">{particles("leaf", 70, ["#e8782a", "#d9452f", "#e9b52e", "#c2561c"], 11)}</g>'
             f'<g class="p p-spring" aria-hidden="true" pointer-events="none">{particles("petal", 55, ["#ffc2d9", "#ffffff", "#ffa8c8"], 12)}</g>'
             f'<g class="p p-winter" aria-hidden="true" pointer-events="none">{particles("snow", 190, ["#ffffff", "#ffffff", "#eaf4ff"], 13)}</g>')

# ------------------------------------------------------------------ a college: its building, plaza and name tag (a link to its own website)
def college_svg(c):
    spr = SPR[c["sprite"]]()
    x0, _, x1, _ = spr.bbox()
    dx = -((x0 + x1) // 2)
    shadow, plz = plaza(RX)
    hw = c["hw"]
    label = f'{c["name"]} (opens in a new tab)'
    return f'''<g transform="translate({c["x"]} {c["y"]})" class="col">
				<a class="campus" href="{c["url"]}" target="_blank" rel="noopener" style="--c:{c["color"]}" aria-label="{label}">
					<rect x="-{hw}" y="-30" width="{2 * hw}" height="52" fill="none" pointer-events="all"/>
					<g class="dim">{shadow}<g class="plaza">{plz}</g></g>
					<g class="bldg"><g transform="translate({dx} 0)">
					<g class="dim">{svg_paths(spr)}<g class="snow">{svg_paths(snow_layer(spr))}</g></g>
					<g class="lit" aria-hidden="true">{night_lights(spr, {GL})}</g>
					</g></g>
					<g class="tag">{tag(c["word"])}</g>
				</a>
			</g>'''

# ------------------------------------------------------------------ check: no two buildings or name tags overlap
def _icon_box(c):
    x0, y0, x1, y1 = SPR[c["sprite"]]().bbox()
    dx = -((x0 + x1) // 2)
    return (c["x"] + x0 + dx, c["y"] + y0, c["x"] + x1 + dx, c["y"])
def _overlap(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
def _check():
    tags, icons = [], []
    for c in COLLEGES:
        half = (text_width(c["word"]) + 6) / 2
        tags.append((c["name"], (c["x"] - half, c["y"] + 6, c["x"] + half, c["y"] + 17)))
        icons.append((c["name"], _icon_box(c)))
    for i, (n1, t) in enumerate(tags):
        for j, (n2, t2) in enumerate(tags):
            if i < j and _overlap(t, t2): raise SystemExit(f"name tags overlap: {n1} / {n2}")
        for (n2, b) in icons:
            if _overlap(t, b): raise SystemExit(f"tag of {n1} overlaps the building of {n2}")
    for i, (n1, b) in enumerate(icons):
        for j, (n2, b2) in enumerate(icons):
            if i < j and _overlap(b, b2): raise SystemExit(f"buildings overlap: {n1} / {n2}")
    for (n1, t) in tags + icons:
        pass
    for c in COLLEGES:
        if river_dist(c["x"], c["y"] - 8) < HALF + 5: raise SystemExit(f'{c["name"]} sits in the river')
_check()

# ------------------------------------------------------------------ the page
def _ver(path): return hashlib.md5(path.read_bytes()).hexdigest()[:8]
V = {"lgcss": _ver(LG / "style.css"), "lgseason": _ver(LG / "season.js"), "css": _ver(HERE / "cam.css"), "js": _ver(HERE / "cam.js")}

# the stretch of river the boat sails along: centre y every 4 px from x = ARM_X0 (the river runs rightwards there)
ARM_X0 = 0
def river_y_at(x):
    for (cx, cy) in CENTRE:
        if cx >= x: return cy
    return CENTRE[-1][1]
ARM_X1 = int(art((1295, 1085))[0])
ARM = ",".join(str(round(river_y_at(x))) for x in range(ARM_X0, ARM_X1, 4))

HTML = r'''<!DOCTYPE html>
<html lang="en" data-season="@@SEASON@@">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>University of Cambridge</title>
	<meta name="description" content="A zoomable pixel-art map of 28 colleges of the University of Cambridge along the River Cam. Select a college to visit its website.">
	<meta name="theme-color" content="#0f1535">
	<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' shape-rendering='crispEdges'%3E%3Crect width='16' height='16' fill='%238fd16c'/%3E%3Cpath fill='%233f95d8' d='M0 6h16v6H0z'/%3E%3Cpath fill='%235bb8f0' d='M0 6h16v4H0z'/%3E%3C/svg%3E">
	<link rel="preload" href="../local-group/PressStart2P.woff2" as="font" type="font/woff2" crossorigin>
	<script src="../local-group/season.js?v=@@V_SEASON@@"></script>
	<link rel="stylesheet" href="../local-group/style.css?v=@@V_LGCSS@@">
	<link rel="stylesheet" href="cam.css?v=@@V_CSS@@">
	<script defer src="cam.js?v=@@V_JS@@"></script>
</head>
<body class="home cam">
	<a class="skip-link" href="#main">Skip to content</a>
	<div class="hero">
		<div class="sky" aria-hidden="true"></div>
		<svg class="galaxy" viewBox="0 0 @@GALW@@ @@GALH@@" shape-rendering="crispEdges" aria-hidden="true" focusable="false">@@GALAXY@@</svg>

		@@TOD@@

		<div class="intro">
			<h1>University of Cambridge</h1>
			<p class="tagline">Twenty-eight colleges along the River Cam. Pick one to visit its website.</p>
			<nav class="buttons" aria-label="University of Cambridge">
				<a class="btn" href="https://www.cam.ac.uk" target="_blank" rel="noopener">cam.ac.uk<span class="sr"> (opens in a new tab)</span></a>
				<a class="btn" href="../">Elliot's homepage</a>
			</nav>
		</div>
	</div>

	<main class="scene-wrap" id="main">
		<h2 class="sr">The colleges</h2>
		<svg class="scene" role="group" aria-label="Pixel-art map of 28 Cambridge colleges along the River Cam, which comes in from the lower left, runs past the Backs and St John's, and leaves down the right-hand side. Each college is a link to its own website." viewBox="@@VIEW@@" data-map="@@MAP@@" data-focus="@@FOCUS@@" data-arm="@@ARM@@" data-arm-x0="@@ARMX0@@" preserveAspectRatio="xMidYMid meet" shape-rendering="crispEdges" style="--fall:@@FALL@@px">
			<defs>
				@@TILES@@
				@@TREEDEFS@@
				<!-- night: every colour moves 45% of the way towards a deep blue (same blend as the page background in style.css) -->
				<filter id="dim" color-interpolation-filters="sRGB" x="-5%" y="-5%" width="110%" height="110%">
					<feColorMatrix type="matrix" values="0.55 0 0 0 0.025  0 0.55 0 0 0.039  0 0 0.55 0 0.1125  0 0 0 1 0"/>
				</filter>
			</defs>
			<g id="world">
				<g aria-hidden="true" class="dim">
					@@GROUND@@
					<g class="g-flowers">@@FLOWERS@@</g>
					<g class="g-spring">@@SPRING@@</g>
					<g class="g-litter">@@LITTER@@</g>
					<g>@@LAWN@@</g>
					<g class="river">
						<g>@@RIVER@@</g>
						<g class="sh sh1">@@SH1@@</g>
						<g class="sh sh2">@@SH2@@</g>
						<g class="sh sh3">@@SH3@@</g>
						<g id="boat" transform="translate(0 @@BOATY@@)">@@BOAT@@</g>
					</g>
					<g>@@ROADS@@</g>
					<g>@@BRIDGES@@</g>
					@@TREES@@
				</g>

				@@COLLEGES@@
				@@PARTICLES@@
			</g>
		</svg>
		<div class="zoom" role="group" aria-label="Map zoom">
			<button type="button" id="zin" aria-label="Zoom in">+</button>
			<button type="button" id="zout" aria-label="Zoom out">-</button>
			<button type="button" id="zfit" aria-label="Show the whole map">ALL</button>
		</div>
		<p class="map-hint" aria-hidden="true">Drag to move. Pinch, or Ctrl + scroll, to zoom.</p>
	</main>
</body>
</html>
'''

PAD = 10
FOCUS = (round(sum(c['x'] for c in COLLEGES if c.get('backs')) / 6), round(sum(c['y'] for c in COLLEGES if c.get('backs')) / 6))   # phones open here
html = (HTML.replace("@@SEASON@@", BUILD_SEASON).replace("@@TOD@@", TOD_BUTTON).replace("@@GALAXY@@", GALAXY)
        .replace("@@GALW@@", str(GAL_W)).replace("@@GALH@@", str(GAL_H))
        .replace("@@VIEW@@", f"{MINX - PAD} {MINY - PAD} {W + 2 * PAD} {H + 2 * PAD}").replace("@@MAP@@", f"{MINX} {MINY} {MAXX} {MAXY}").replace("@@FOCUS@@", f"{FOCUS[0]} {FOCUS[1]}")
        .replace("@@ARM@@", ARM).replace("@@ARMX0@@", str(ARM_X0)).replace("@@FALL@@", str(H + 60))
        .replace("@@TILES@@", tiles_defs).replace("@@TREEDEFS@@", tree_def(0) + tree_def(1))
        .replace("@@GROUND@@", ground_rect("tuft")).replace("@@FLOWERS@@", ground_rect("flw")).replace("@@SPRING@@", ground_rect("spr"))
        .replace("@@LITTER@@", ground_rect("lit")).replace("@@LAWN@@", svg_paths(lawn)).replace("@@ROADS@@", svg_paths(roads)).replace("@@RIVER@@", svg_paths(river))
        .replace("@@SH1@@", svg_paths(SHIM[0])).replace("@@SH2@@", svg_paths(SHIM[1])).replace("@@SH3@@", svg_paths(SHIM[2]))
        .replace("@@BOAT@@", boat_svg()).replace("@@BOATY@@", str(round(river_y_at(ARM_X0))))
        .replace("@@BRIDGES@@", svg_paths(bridges)).replace("@@TREES@@", trees_svg)
        .replace("@@COLLEGES@@", "\n\t\t\t\t".join(college_svg(c) for c in COLLEGES)).replace("@@PARTICLES@@", PARTICLES)
        .replace("@@V_SEASON@@", V["lgseason"]).replace("@@V_LGCSS@@", V["lgcss"]).replace("@@V_CSS@@", V["css"]).replace("@@V_JS@@", V["js"]))
(HERE / "index.html").write_text(html, encoding="utf-8")
print(f"built University of Cambridge: {len(COLLEGES)} colleges, {len(TREES)} trees, map {W}x{H}, {len(html) // 1024} KB")
