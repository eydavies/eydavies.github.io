#!/usr/bin/env python3
"""Builds the University of Cambridge page: cambridge/index.html.

A zoomable pixel-art map of 28 Cambridge colleges in the style of The Local Group's home page (local-group/), with a small toolbar floating over the map instead of a banner. The layout
follows an illustrated map of the town: the River Cam comes in from the lower left, runs up the Backs, hooks round St John's
and Magdalene, and leaves down the right-hand side. It borrows the Local Group's drawing helpers by running
local-group/build.py into a temporary folder, and links to that site's style.css and season.js, so the look (seasons, night
mode, header, fonts) stays in step. Nothing in local-group/ links back here.

    cd <repo root> && python3 cambridge/build.py

Writes cambridge/index.html only. Positions come from REF (coordinates on the reference map), scaled by F, then nudged apart
until no building or name tag overlaps. The map is a schematic, not a survey.
"""
import contextlib, hashlib, html as _html, io, json, math, pathlib, random, runpy, shutil, sys, tempfile

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
TOD_BUTTON, BUILD_SEASON = G["TOD_BUTTON"], G["BUILD_SEASON"]
text_width = G["text_width"]
def boat_svg():                                  # the Local Group's boats, but a punter in summer, and in spring a single duck, no ducklings
    sk = f'<g class="fa">{svg_paths(G["skater"](0))}</g><g class="fb">{svg_paths(G["skater"](1))}</g>'
    sl = f'<g class="fa">{svg_paths(sprites.punt(Grid, OL, 0))}</g><g class="fb">{svg_paths(sprites.punt(Grid, OL, 1))}</g>'
    rw = f'<g class="fa row">{svg_paths(G["rower"](0))}</g><g class="fb row">{svg_paths(G["rower"](1))}</g>'
    duck = f'<g class="dbob">{svg_paths(G["duck"](True))}</g>'
    return (f'<g class="bt bt-fall">{rw}</g><g class="bt bt-winter">{sk}</g><g class="bt bt-spring">{duck}</g><g class="bt bt-summer">{sl}</g>')

import sprites
GL = sprites.GL
SPR = sprites.build_all(Grid, OL)

# ------------------------------------------------------------------ the walkers: students in black gowns (no caps), 12 px tall, drawn facing left (the script mirrors them)
GOWN, GOWN_D, GOWN_L = '#3d3f66', '#2c2e4d', '#555985'
def gowned(hair, skin, trousers, book, frame):
    g = Grid(); px = g.px
    for x in (-1, 0, 1): px(x, -12, hair)
    for y in (-11, -10): px(-1, y, skin); px(0, y, skin); px(1, y, hair)       # the face looks left; hair at the back of the head
    px(-1, -9, '#ffffff'); px(0, -9, '#ffffff'); px(1, -9, GOWN)               # a white collar
    for y in range(-8, -5):
        px(-1, y, GOWN_L); px(0, y, GOWN); px(1, y, GOWN)                      # the shoulders and chest
        px(-2, y, GOWN_D); px(2, y, GOWN_D)                                    # the arms, hung in loose sleeves
    px(-2, -5, skin)                                                           # a hand
    for y in (-5, -4):
        px(-1, y, GOWN_L)
        for x in range(0, 3): px(x, y, GOWN)
    px(2, -5, GOWN_D); px(2, -4, GOWN_D)
    for x in range(-3, 4): px(x, -3, GOWN_D if x in (-3, 3) else GOWN)      # the gown flares to the hem and swings as they step
    for x in (range(-3, 4) if frame == 0 else range(-2, 4)): px(x, -2, GOWN_D)
    if frame == 0: px(-1, -1, '#1d1b2a'); px(1, -1, '#1d1b2a')
    else: px(0, -1, '#1d1b2a'); px(-1, -1, '#1d1b2a')
    if book:
        for (x, y) in ((-4, -6), (-3, -6), (-4, -5), (-3, -5)): px(x, y, book)
    g.outline(OL)
    return g
# (hair, skin, trousers, book): one in three has dark skin
PEOPLE = [('#3b2a20', '#ffd9a8', '#4a4a5a', None), ('#1d1d1d', '#7a4a2a', '#3a3a4a', '#a5342f'), ('#e9c46a', '#f1c27d', '#555566', None),
          ('#1d1d1d', '#c68642', '#3a3a4a', '#2a7f62'), ('#8a4b24', '#ffd9a8', '#4a4a5a', '#2a5ea5'), ('#1d1d1d', '#5c3a21', '#3a3a4a', None),
          ('#c9c9c9', '#f1c27d', '#555566', '#a5342f'), ('#d96a3c', '#ffe0bd', '#4a4a5a', None)]
WALKER_DEFS = "".join(f'<g id="pw{i}a">{svg_paths(gowned(*p, 0))}</g><g id="pw{i}b">{svg_paths(gowned(*p, 1))}</g>' for i, p in enumerate(PEOPLE))

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
REF_RIVER = [(-2600, 1410), (-1500, 1330), (-700, 1230), (0, 1170), (130, 1140), (215, 1100), (285, 1050), (350, 1000), (415, 955), (480, 915),
             (545, 885), (620, 845), (700, 795), (790, 768), (870, 762), (940, 768), (995, 785), (1050, 835), (1095, 900),
             (1135, 955), (1215, 1010), (1295, 1085), (1355, 1165), (1395, 1255), (1410, 1400), (1405, 1520), (1370, 1620),
             (1295, 1700), (1210, 1770), (1160, 1860), (1130, 1960), (1120, 2700), (1120, 4400)]
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
RIVER_NEAR = set()                              # every pixel within HALF + 9 of the water, so trees can be tested in one lookup
for (cx, cy) in CENTRE[::2]:
    r_ = HALF + 9
    for dy in range(-r_ - 1, r_ + 2):
        for dx in range(-r_ - 1, r_ + 2):
            if dx * dx + dy * dy <= (r_ + .5) ** 2: RIVER_NEAR.add((round(cx) + dx, round(cy) + dy))

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
# the world: the most of the page you can ever see. Tile-aligned, so the tree tiles below meet it cleanly. The river runs off both of its edges.
TS = 320
WM, IM = 460, 70                                # the margin of the world, and of the zone of individually placed trees, around the map
WX0, WY0 = MINX - WM, MINY - WM
WX1, WY1 = MAXX + WM, MAXY + WM
IX0, IY0 = MINX - IM, MINY - IM                 # the tree zone is a whole number of tiles, with the tiles of woods starting on its corner
IX1, IY1 = IX0 + -(-(W + 2 * IM) // TS) * TS, IY0 + -(-(H + 2 * IM) // TS) * TS
assert CENTRE[0][0] < WX0 - 40 and CENTRE[-1][1] > WY1 + 40, "the river must run off the edge of the world"

# ------------------------------------------------------------------ the streets: the main roads of the reference map, a spur from each college, bridges where they cross the river
# (name, width 1-3, key points on the reference map). Drawn smoothed; any stretch inside the river becomes a bridge deck.
ROADS_REF = [
    ("Regent St to Castle St", 3, [(130, 1875), (200, 1812), (300, 1740), (380, 1670), (450, 1600), (515, 1535), (535, 1440), (580, 1360), (625, 1275), (660, 1225),
                                   (740, 1170), (820, 1120), (900, 1065), (970, 1030), (1060, 985), (1130, 940), (1190, 905), (1250, 865), (1292, 832),
                                   (1335, 765), (1370, 690), (1400, 600), (1412, 450), (1410, 300)]),
    ("Trumpington St to St John's St", 3, [(60, 1640), (130, 1480), (230, 1360), (320, 1275), (400, 1215), (470, 1185), (560, 1150), (630, 1095), (690, 1050),
                                           (760, 1025), (850, 1015), (930, 1010), (975, 1030)]),
    ("Queens' Road", 3, [(40, 1090), (170, 985), (300, 890), (420, 800), (520, 730), (620, 660), (720, 600), (820, 575), (900, 572), (1000, 585)]),
    ("Madingley Road", 3, [(390, 545), (500, 470), (620, 395), (740, 320), (840, 262), (930, 205), (962, 195)]),
    ("Madingley Rd to Northampton St", 3, [(962, 195), (975, 300), (995, 420), (1005, 530), (1010, 585), (1090, 625), (1180, 730), (1260, 830), (1292, 832)]),
    ("Jesus Lane and Maid's Causeway", 3, [(965, 1035), (1000, 1120), (1012, 1200), (1005, 1280), (990, 1380), (975, 1470), (958, 1560), (955, 1650), (950, 1750),
                                           (950, 1900), (948, 1990)]),
    ("Victoria Avenue", 3, [(955, 1665), (1060, 1640), (1180, 1600), (1290, 1555), (1400, 1510), (1450, 1495)]),
    ("Storey's Way", 2, [(900, 152), (1000, 142), (1130, 128), (1200, 108), (1290, 50), (1350, 15)]),
    ("Margaret Road", 2, [(1215, 190), (1170, 260), (1130, 340), (1100, 420), (1085, 490)]),
    ("Mount Pleasant", 2, [(1090, 495), (1160, 550), (1230, 620), (1290, 700), (1335, 765)]),
    ("Emmanuel Road", 2, [(600, 1640), (700, 1650), (830, 1660), (955, 1665)]),
    ("Clarendon Street", 2, [(545, 1812), (700, 1808), (850, 1803), (950, 1800)]),
    ("Drummer St and Park Terrace", 2, [(690, 1440), (700, 1560), (650, 1650), (590, 1720), (545, 1810), (548, 1860), (570, 1960)]),
    ("West Road", 2, [(110, 620), (200, 720), (290, 830), (340, 900)]),
    ("Silver Street", 2, [(300, 1262), (250, 1160), (215, 1090), (180, 1030), (165, 985)]),
]
ROAD_DENSE = []                                 # (name, width, [(x, y) every art pixel, smoothed])
for (rname, rw, rpts) in ROADS_REF:
    key = [art(p) for p in rpts]; dn = []
    for (ax, ay), (bx, by) in zip(key, key[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay)))
        for i in range(n): dn.append((ax + (bx - ax) * i / n, ay + (by - ay) * i / n))
    dn.append(key[-1])
    sm = []
    for i in range(len(dn)):                    # a light smoothing, so the corners are rounded but the ends stay put
        k = min(5, i, len(dn) - 1 - i); lo, hi = i - k, i + k
        sm.append((sum(p[0] for p in dn[lo:hi + 1]) / (hi - lo + 1), sum(p[1] for p in dn[lo:hi + 1]) / (hi - lo + 1)))
    ROAD_DENSE.append((rname, rw, sm))

roads, bridges = Grid(), Grid()
RPTS = []                                       # road centre points, so trees keep off them
ROAD_JOBS = []                                  # (points, width): drawn together at the end, so junctions are clean
ROUTES = []                                     # polylines the walkers follow: (count, [(x, y), ...])
WIDTH = {1: (1.9, 1.0), 2: (2.5, 1.5), 3: (3.3, 2.3)}
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
def draw_path(pts, w=2): ROAD_JOBS.append((pts, w))
def flush_roads():
    jobs = [(path_pts(p), w) for p, w in ROAD_JOBS]
    for pp, w in jobs:                          # first every edge, then every surface: a side road never leaves an edge line across a main road
        e = WIDTH[w][0]
        for (x, y) in pp:
            if (round(x), round(y)) in RIVER: stamp(bridges, x, y, 3.7 + (w == 3) * .6, '#a39d8e')
            else: stamp(roads, x, y, e, '.pthd')
    for pp, w in jobs:
        i_ = WIDTH[w][1]
        for (x, y) in pp:
            if (round(x), round(y)) in RIVER: stamp(bridges, x, y, 2.7 + (w == 3) * .6, '#d9d2c0')
            else: stamp(roads, x, y, i_, '.pth'); RPTS.append((x, y))
for (rname, rw, sm) in ROAD_DENSE:
    draw_path(sm, rw)
    run = best = 0                              # no road may run along the water for long: that would not be a bridge
    for (x, y) in sm:
        run = run + 1 if (round(x), round(y)) in RIVER else 0; best = max(best, run)
    assert best < 48, f"{rname} runs {best} px inside the river"

def nearest_road(pt):
    best = None
    for (_, _, sm) in ROAD_DENSE:
        for (x, y) in sm[::2]:
            if (round(x), round(y)) in RIVER: continue
            d = math.hypot(x - pt[0], y - pt[1])
            if best is None or d < best[0]: best = (d, (round(x), round(y)))
    return best
def _near_boxes(pts, skip=None):                # how many samples of a path pass through another college's building or name tag
    n = 0
    for (x, y) in path_pts(pts)[::2]:
        for c in COLLEGES:
            if c is skip: continue
            if abs(x - c["x"]) < RX + 3 and -30 < y - c["y"] < 4: n += 1
            elif abs(x - c["x"]) < c["hw"] + 1 and 4 < y - c["y"] < 24: n += 1
    return n
def spur_for(pt, skip=None):                    # the best of: straight, or one bend either way (like a street grid), from pt to the nearest road
    d, rp = nearest_road(pt)
    if d < 3: return None
    opts = [[pt, rp], [pt, (rp[0], pt[1]), rp], [pt, (pt[0], rp[1]), rp]]
    return min(opts, key=lambda o: (_near_boxes(o, skip) * 40 + sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(o, o[1:]))))
for c in COLLEGES:                              # a short spur from every college's gate to the nearest street
    sp = spur_for((c["x"], c["y"] + 1), skip=c)
    if sp:
        draw_path(sp, 1)
        if sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(sp, sp[1:])) >= 22: ROUTES.append((1, sp[::-1]))
for c in COLLEGES:                              # the Backs: a footbridge from each college over the river to the meadow
    if not c.get("backs"): continue
    cx, cy = min(RIVER_PTS, key=lambda p: math.hypot(p[0] - c["x"], p[1] - c["y"] - 8))
    dx, dy = cx - c["x"], cy - (c["y"] + 1)
    n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
    draw_path([(c["x"], c["y"] + 1), (cx + dx * (HALF + 12), cy + dy * (HALF + 12))], 1)

# ------------------------------------------------------------------ the parks: square-cornered greens with their own footpaths (and, in the two Pieces, a lamp in the middle)
# name, centre on the reference map, half-width and half-height in art pixels, paths: x = corner to corner, long = along the length, none
PARKS = [
    dict(name="Parker's Piece", ref=(385, 1850), hw=35, hh=35, kind="x", lamp=1),
    dict(name="Christ's Pieces", ref=(790, 1510), hw=17, hh=22, kind="x", lamp=1),
    dict(name="Jesus Green", ref=(1285, 1440), hw=15, hh=34, kind="long"),
    dict(name="Midsummer Common", ref=(1120, 1735), hw=36, hh=20, kind="long"),
    dict(name="St John's College Playing Fields", ref=(810, 390), hw=40, hh=44, kind="none"),
    dict(name="University Rugby Ground", ref=(110, 640), hw=14, hh=11, kind="pitch"),
]
def _park_conflict(box):                        # does the park touch a college's building, plaza or the river?
    x0, y0, x1, y1 = box
    for c in COLLEGES:
        if c["x"] - RX - 3 < x1 and x0 < c["x"] + RX + 3 and c["y"] - 29 < y1 and y0 < c["y"] + 6: return True
    return any((x, y) in RIVER for x in range(x0, x1 + 1, 2) for y in range(y0, y1 + 1, 2))
for p in PARKS:                                  # start from the reference position, move the least that clears the colleges
    cx0, cy0 = (round(v) for v in art(p["ref"]))
    best = None
    for dy in range(-26, 27, 2):
        for dx in range(-26, 27, 2):
            box = (cx0 + dx - p["hw"], cy0 + dy - p["hh"], cx0 + dx + p["hw"], cy0 + dy + p["hh"])
            if not _park_conflict(box) and (best is None or dx * dx + dy * dy < best[0]): best = (dx * dx + dy * dy, dx, dy)
    if best is None: raise SystemExit(f"nowhere to put {p['name']}")
    p["cx"], p["cy"] = cx0 + best[1], cy0 + best[2]
    p["box"] = (p["cx"] - p["hw"], p["cy"] - p["hh"], p["cx"] + p["hw"], p["cy"] + p["hh"])
lawn = Grid()
for p in PARKS:
    x0, y0, x1, y1 = p["box"]
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if min(x - x0, x1 - x) + min(y - y0, y1 - y) < 3: continue           # chamfered corners
            lawn.px(x, y, '.lawn')
    if p["kind"] == "pitch":                                                      # pitch markings
        for x in range(x0 + 3, x1 - 2): lawn.px(x, y0 + 3, '#f4f4e8'); lawn.px(x, y1 - 3, '#f4f4e8')
        for y in range(y0 + 3, y1 - 2): lawn.px(x0 + 3, y, '#f4f4e8'); lawn.px(x1 - 3, y, '#f4f4e8'); lawn.px((x0 + x1) // 2, y, '#f4f4e8')
lawn.outline('.lawnd')
LAMPS = []
for p in PARKS:
    x0, y0, x1, y1 = p["box"]; cx, cy = p["cx"], p["cy"]
    if p["kind"] == "x":                        # corner to corner, crossing in the middle
        diag = [[(x0 + 3, y0 + 3), (x1 - 3, y1 - 3)], [(x1 - 3, y0 + 3), (x0 + 3, y1 - 3)]]
    elif p["kind"] == "long":                   # along the length, with a short cross-path
        diag = [[(x0 + 2, cy), (x1 - 2, cy)]] if p["hw"] > p["hh"] else [[(cx, y0 + 2), (cx, y1 - 2)]]
        diag.append([(cx, y0 + 2), (cx, y1 - 2)] if p["hw"] > p["hh"] else [(x0 + 2, cy), (x1 - 2, cy)])
    else: diag = []
    for d in diag:
        draw_path(d, 1 if p["hw"] < 20 else 2)
        if p["kind"] == "x" or d is diag[0]: ROUTES.append((1, d))
    if p.get("lamp"):                           # a round of paving where the paths cross, with a lamp on it
        for yy in range(-4, 5):
            for xx in range(-4, 5):
                r2 = xx * xx + yy * yy
                if r2 <= 20: roads.px(cx + xx, cy + yy, '.pthd' if r2 > 12 else '.pth')
        LAMPS.append((cx, cy + 2))
    if p["kind"] != "pitch":                    # a path out to the nearest street
        pts_ = [(cx, y0 + 1), (cx, y1 - 1), (x0 + 1, cy), (x1 - 1, cy)]
        q = min(pts_, key=lambda q_: nearest_road(q_)[0])
        sp = spur_for(q)
        if sp: draw_path(sp, 1)
for rname, rw, sm in ROAD_DENSE:                # the long streets, as routes for the walkers: only the part of each inside the map
    run = []
    for (x, y) in sm[::6] + [sm[-1]]:
        if MINX + 4 < x < MAXX - 4 and MINY + 4 < y < MAXY - 4: run.append((round(x), round(y)))
        else:
            if len(run) > 8: ROUTES.append((2 if rw == 3 else 1, run))
            run = []
    if len(run) > 8: ROUTES.append((2 if rw == 3 else 1, run))
flush_roads()
bridges.outline(OL)
lamp, lamp_lit, lamp_glow, lamp_glow2 = Grid(), Grid(), Grid(), Grid()
for (LX, LY) in LAMPS:
    for dx in (-1, 0, 1): lamp.px(LX + dx, LY, '#3a3550')
    for y in range(LY - 8, LY): lamp.px(LX, y, '#3a3550')
    lamp.rect(LX - 1, LY - 12, LX + 1, LY - 10, '#f6efc9')
    lamp_lit.rect(LX - 1, LY - 12, LX + 1, LY - 10, '#fff1a0'); lamp_lit.px(LX, LY - 11, '#ffffff')
    lamp_glow.disc(LX, LY - 8, 14, 12, '#ffe27a'); lamp_glow2.disc(LX, LY - 9, 7, 6, '#ffe27a')
lamp.outline(OL)
lawn_boxes = [((x0 - 4, y0 - 4), (x1 + 4, y1 + 12)) for (x0, y0, x1, y1) in (p["box"] for p in PARKS)]

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
GX0, GY0, GX1, GY1 = WX0, WY0, WX1, WY1                                              # the ground fills the world
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
    if (round(x), round(y - 6)) in RIVER_NEAR: return False
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
        if any(a0[0] < x < a1[0] and a0[1] < y < a1[1] for a0, a1 in lawn_boxes): continue
        if tree_ok(x, y) and far_enough(x, y, d):
            TREES.append((x, y, random.choice([0, 1, 1]))); grid_t.setdefault(cell(x, y, d), []).append((x, y)); got += 1
sprinkle(260, MINX, MINY + 16, MAXX, MAXY, 22, 60000)
sprinkle(99999, IX0, IY0, IX1, IY1, 29, 150000)                                  # all round the map, as thick as inside it
# beyond that: one tile of woods, repeated (it never touches the edges of its tile, so there are no seams)
_r = random.Random(77); WOODS = []
for _ in range(6000):
    x, y = _r.randint(10, TS - 10), _r.randint(17, TS - 2)
    if all((x - a) ** 2 + ((y - b) * 1.1) ** 2 >= 29 * 29 for a, b, _c in WOODS): WOODS.append((x, y, _r.choice([0, 1, 1])))
WOODS.sort(key=lambda t: t[1])
woods_tile = "".join(f'<g class="ctree tv{i % 3}" transform="translate({x} {y})"><use href="#tr{b}"/></g>' for i, (x, y, b) in enumerate(WOODS))
woods_defs = f'<pattern id="pt-woods" x="{IX0}" y="{IY0}" width="{TS}" height="{TS}" patternUnits="userSpaceOnUse">{woods_tile}</pattern>'
_cl = " ".join(f"{'M' if i == 0 else 'L'}{round(x)} {round(y)}" for i, (x, y) in enumerate(CENTRE[::12] + [CENTRE[-1]]))        # the river's course, to keep woods off the water
woods_mask = (f'<mask id="wm" maskUnits="userSpaceOnUse" x="{WX0}" y="{WY0}" width="{WX1 - WX0}" height="{WY1 - WY0}">'
              f'<rect x="{WX0}" y="{WY0}" width="{WX1 - WX0}" height="{WY1 - WY0}" fill="#fff"/><rect x="{IX0}" y="{IY0}" width="{IX1 - IX0}" height="{IY1 - IY0}" fill="#000"/>'
              f'<path d="{_cl}" fill="none" stroke="#000" stroke-width="{2 * (HALF + 12)}" stroke-linejoin="round"/></mask>')
woods_rect = f'<rect x="{WX0}" y="{WY0}" width="{WX1 - WX0}" height="{WY1 - WY0}" fill="url(#pt-woods)" mask="url(#wm)"/>'
TREES.sort(key=lambda t: t[1])
def heavy_snow(t):                              # winter: the top three rows of every lobe of foliage are snow, shaded blue-white on the fourth, plus the rim
    pre = t.pre; leaf = {k for k, c in pre.items() if c.startswith('.lf')}
    g = Grid()
    for (x, y) in leaf:
        if (x, y - 1) in leaf: continue                                       # start from each top surface
        d = 0
        while (x, y + d) in leaf and d < 4:
            inner = (x - 1, y + d) in leaf and (x + 1, y + d) in leaf
            if d < 3 or inner: g.px(x, y + d, '#f6faff' if d < 3 else '#d5e4f5')
            d += 1
    for (x, y) in leaf:                                                       # and a dusting along the sunny (upper-left) edge
        if (x - 1, y) not in leaf and (x, y - 1) in leaf and (x + 1, y) in leaf: g.px(x, y, '#f6faff')
    return g
def tree_def(big):
    t = tree(bool(big)); snow = heavy_snow(t)
    return f'<g id="tr{big}">{svg_paths(t)}<g class="snow">{svg_paths(snow)}</g></g>'
trees_svg = "".join(f'<g class="ctree tv{i % 3}" transform="translate({x} {y})"><use href="#tr{b}"/></g>' for i, (x, y, b) in enumerate(TREES))

# ------------------------------------------------------------------ falling leaves, petals and snow: a layer over the screen, so they fall wherever you are looking
def particles(kind, n, colours, seed):
    rnd = random.Random(seed); out = []
    for _ in range(n):
        x = rnd.uniform(-2, 102); dur = rnd.uniform(18, 34); delay = -rnd.uniform(0, dur)
        drift = rnd.choice([-36, -24, -12, 12, 24, 36])
        w, h = (3, 2) if kind != 'snow' else ((3, 3) if rnd.random() < .22 else (2, 2))
        out.append(f'<g class="pt" style="--x:{x:.1f}vw;--dx:{drift}px;animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
                   f'<rect class="sw" width="{w}" height="{h}" fill="{rnd.choice(colours)}"/></g>')
    return "".join(out)
PARTICLES = (f'<g class="p p-fall">{particles("leaf", 100, ["#e8782a", "#d9452f", "#e9b52e", "#c2561c"], 11)}</g>'
             f'<g class="p p-spring">{particles("petal", 80, ["#ffc2d9", "#ffffff", "#ffa8c8"], 12)}</g>'
             f'<g class="p p-winter">{particles("snow", 240, ["#ffffff", "#ffffff", "#eaf4ff"], 13)}</g>')

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
ARM_X0 = WX0 + 40
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
	<meta name="robots" content="noindex, nofollow">
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
	<header class="bar">
		<h1 class="sr">University of Cambridge</h1>
		<nav class="links" aria-label="University of Cambridge">
			<a class="btn" href="../"><span><span aria-hidden="true">&lt; </span><span class="opt">Elliot's </span>homepage</span></a>
			<a class="btn" href="https://www.cam.ac.uk" target="_blank" rel="noopener"><span>cam.ac.uk</span><span class="sr"> (opens in a new tab)</span></a>
		</nav>
		<div class="zoom" role="group" aria-label="Map zoom">
			<button type="button" id="zout" aria-label="Zoom out">-</button>
			<button type="button" id="zin" aria-label="Zoom in">+</button>
			<button type="button" id="zfit" aria-label="Show the whole map">ALL</button>
		</div>
		@@TOD@@
	</header>

	<main class="scene-wrap" id="main">
		<p class="sr">Twenty-eight colleges along the River Cam. Pick one to visit its website.</p>
		<svg class="scene" role="group" aria-label="Pixel-art map of 28 Cambridge colleges along the River Cam, which comes in from the lower left, runs past the Backs and St John's, and leaves down the right-hand side. Each college is a link to its own website." viewBox="@@VIEW@@" data-map="@@MAP@@" data-focus="@@FOCUS@@" data-arm="@@ARM@@" data-arm-x0="@@ARMX0@@" data-world="@@WORLD@@" preserveAspectRatio="xMidYMid meet" shape-rendering="crispEdges" >
			<defs>
				@@TILES@@
				@@TREEDEFS@@
				@@WALKERDEFS@@
				<!-- night: every colour moves 45% of the way towards a deep blue (same blend as the page background in style.css) -->
				<filter id="dim" color-interpolation-filters="sRGB" x="-5%" y="-5%" width="110%" height="110%">
					<feColorMatrix type="matrix" values="0.55 0 0 0 0.025  0 0.55 0 0 0.039  0 0 0.55 0 0.1125  0 0 0 1 0"/>
				</filter>
			</defs>
			<g id="world">
				<g aria-hidden="true">
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
					@@WOODS@@
					<g>@@LAMP@@</g>
					<rect class="veil" x="@@WX0@@" y="@@WY0@@" width="@@WW@@" height="@@WH@@" fill="#0e1640"/>
				</g>
				<g id="walkers" aria-hidden="true" pointer-events="none" data-people="@@NPEOPLE@@" data-routes="@@ROUTES@@"></g>
				<g class="lit lamp" aria-hidden="true" pointer-events="none"><g opacity=".28">@@GLOW@@</g><g opacity=".38">@@GLOW2@@</g>@@LAMPLIT@@</g>

				@@COLLEGES@@
			</g>
		</svg>
		<svg class="fx" aria-hidden="true" focusable="false" shape-rendering="crispEdges">@@PARTICLES@@</svg>
		<p class="map-hint" aria-hidden="true">Drag to move. Pinch, or Ctrl + scroll, to zoom.</p>
	</main>
</body>
</html>
'''

PAD = 10
FOCUS = (round(sum(c['x'] for c in COLLEGES if c.get('backs')) / 6), round(sum(c['y'] for c in COLLEGES if c.get('backs')) / 6))   # phones open here
html = (HTML.replace("@@SEASON@@", BUILD_SEASON).replace("@@TOD@@", TOD_BUTTON)
        .replace("@@VIEW@@", f"{MINX - PAD} {MINY - PAD} {W + 2 * PAD} {H + 2 * PAD}").replace("@@MAP@@", f"{MINX} {MINY} {MAXX} {MAXY}").replace("@@FOCUS@@", f"{FOCUS[0]} {FOCUS[1]}")
        .replace("@@ARM@@", ARM).replace("@@ARMX0@@", str(ARM_X0)).replace("@@WX0@@", str(WX0)).replace("@@WY0@@", str(WY0)).replace("@@WW@@", str(WX1 - WX0)).replace("@@WH@@", str(WY1 - WY0)).replace("@@WORLD@@", f"{WX0} {WY0} {WX1} {WY1}")
        .replace("@@TILES@@", tiles_defs).replace("@@TREEDEFS@@", tree_def(0) + tree_def(1) + woods_defs + woods_mask)
        .replace("@@GROUND@@", ground_rect("tuft")).replace("@@FLOWERS@@", ground_rect("flw")).replace("@@SPRING@@", ground_rect("spr"))
        .replace("@@LITTER@@", ground_rect("lit")).replace("@@LAWN@@", svg_paths(lawn)).replace("@@ROADS@@", svg_paths(roads)).replace("@@RIVER@@", svg_paths(river))
        .replace("@@SH1@@", svg_paths(SHIM[0])).replace("@@SH2@@", svg_paths(SHIM[1])).replace("@@SH3@@", svg_paths(SHIM[2]))
        .replace("@@BOAT@@", boat_svg()).replace("@@BOATY@@", str(round(river_y_at(ARM_X0))))
        .replace("@@WALKERDEFS@@", WALKER_DEFS).replace("@@NPEOPLE@@", str(len(PEOPLE)))
        .replace("@@ROUTES@@", _html.escape(json.dumps([[n] + [round(v) for p_ in pts for v in p_] for n, pts in ROUTES], separators=(",", ":")), quote=True))
        .replace("@@LAMP@@", svg_paths(lamp)).replace("@@LAMPLIT@@", svg_paths(lamp_lit)).replace("@@GLOW@@", svg_paths(lamp_glow)).replace("@@GLOW2@@", svg_paths(lamp_glow2))
        .replace("@@BRIDGES@@", svg_paths(bridges)).replace("@@TREES@@", trees_svg).replace("@@WOODS@@", woods_rect)
        .replace("@@COLLEGES@@", "\n\t\t\t\t".join(college_svg(c) for c in COLLEGES)).replace("@@PARTICLES@@", PARTICLES)
        .replace("@@V_SEASON@@", V["lgseason"]).replace("@@V_LGCSS@@", V["lgcss"]).replace("@@V_CSS@@", V["css"]).replace("@@V_JS@@", V["js"]))
(HERE / "index.html").write_text(html, encoding="utf-8")
print(f"built University of Cambridge: {len(COLLEGES)} colleges, {len(TREES)} trees, map {W}x{H}, {len(html) // 1024} KB")
