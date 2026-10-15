"""The 14 small college icons for the Cambridge page (pixel art, drawn on the Grid from local-group/build.py).

Every sprite has its origin at the bottom centre (y = -1 is the lowest row of the walls), is at most ~26 px wide and ~24 px
tall, and uses the colour GL for window panes so the night-time lights (see build.py) find them. Each is a simplified
nod to something recognisable about the college, not a survey drawing.
"""

GL = '#3f4f73'                       # window panes: lit up at night


def build_all(Grid, OL):
    CREAM, CREAMD, WHITE = '#e9dfc0', '#cdbf94', '#f6efdc'
    BR, BRD = '#b85a43', '#9c4634'                       # red brick
    DK, DKD = '#8d4a45', '#74393a'                       # darker, greyer brick
    SL, SLL = '#4a4e69', '#5f6488'                       # slate roof
    WOOD, GOLD, GREY, GREYD = '#6b3a2e', '#f2c14e', '#a9afbd', '#8b92a3'
    CU, CUH = '#4fa58a', '#86d4b6'                       # copper
    TIMB = '#5a3b2a'

    def brick(g, x0, y0, x1, y1, a=BR, b=BRD):
        g.rect(x0, y0, x1, y1, a)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x + (y % 2) * 2) % 4 == 0: g.px(x, y, b)

    def stone(g, x0, y0, x1, y1, a=CREAM, b=CREAMD):
        g.rect(x0, y0, x1, y1, a)
        for y in range(y0 + 1, y1 + 1, 3):
            for x in range(x0 + (y // 3) % 2, x1 + 1, 4): g.px(x, y, b)

    def win(g, x, y, w=1, h=2):                          # w x h pane
        g.rect(x, y, x + w - 1, y + h - 1, GL)

    def merlons(g, y, x0, x1, c=CREAM):                  # crenellations along y (solid every other pixel)
        for x in range(x0, x1 + 1, 2): g.px(x, y, c)

    def pediment(g, cx, y, half, c=CREAM, d=CREAMD):     # triangle rising from baseline y
        for i in range(half + 1):
            g.rect(cx - half + i, y - i, cx + half - i, y - i, c)
        g.hline(y, cx - half, cx + half, d)

    def cupola(g, cx, y, c=WHITE, roof=CU, roofh=CUH):   # little lantern with a domed top, base at y
        g.rect(cx - 1, y - 2, cx + 1, y, c); g.px(cx, y - 1, GL)
        g.hline(y - 3, cx - 2, cx + 2, c)
        g.rect(cx - 1, y - 5, cx + 1, y - 4, roof); g.px(cx, y - 6, GOLD); g.px(cx - 1, y - 5, roofh)

    # ---------------------------------------------------------------- King's: the chapel with its four pinnacled turrets
    def kings():
        g = Grid()
        stone(g, -10, -12, 10, -1)
        g.hline(-13, -10, 10, CREAMD); merlons(g, -14, -10, 10, CREAMD)
        for x in (-8, -4, 0, 4, 8): g.vline(x - 1, -11, -2, CREAMD)           # buttresses between the tall windows
        for x in (-7, -3, 1, 5):
            g.rect(x, -11, x + 1, -3, GL)
        for sx in (-1, 1):                                                   # the turrets
            x0 = 10 if sx > 0 else -13
            stone(g, x0, -19, x0 + 2, -1)
            g.hline(-20, x0, x0 + 2, CREAMD)
            g.px(x0, -21, CREAM); g.px(x0 + 2, -21, CREAM); g.px(x0 + 1, -22, CREAM); g.px(x0 + 1, -23, GOLD)
            g.px(x0 + 1, -14, GL); g.px(x0 + 1, -8, GL)
        g.rect(-1, -4, 1, -1, WOOD)                                          # west door
        g.outline(OL); return g

    # ---------------------------------------------------------------- Queens': red-brick court with a timber-framed gallery
    def queens():
        g = Grid()
        brick(g, -12, -8, 12, -1)
        g.rect(-12, -12, 12, -9, CREAM)                                      # the half-timbered President's Gallery
        for x in range(-12, 13, 4): g.vline(x, -12, -9, TIMB)
        g.hline(-12, -12, 12, TIMB); g.hline(-9, -12, 12, TIMB)
        for x in (-10, -6, -2, 2, 6, 10): g.px(x + 1, -11, GL); g.px(x + 1, -10, GL)
        for i, half in enumerate((13, 12, 11)): g.hline(-13 - i, -half, half, SLL if i % 2 else SL)
        brick(g, 4, -19, 5, -14); g.hline(-20, 3, 6, CREAMD)               # chimney
        brick(g, -12, -17, -6, -13); merlons(g, -18, -12, -6, BR)           # the gatehouse tower
        win(g, -9, -16, 1, 2)
        for x in (-8, -4, 0, 4, 8): win(g, x, -7, 2, 3)
        g.rect(-9, -5, -7, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Trinity: the Great Gate with its clock and battlements
    def trinity():
        g = Grid()
        stone(g, -13, -11, 13, -1)
        merlons(g, -12, -13, 13, CREAMD)
        for x in (-10, -7, 7, 10): win(g, x, -9, 1, 2)
        for x in (-10, -7, 7, 10): win(g, x, -5, 1, 2)
        stone(g, -5, -20, 5, -1)
        g.hline(-21, -5, 5, CREAMD); merlons(g, -22, -5, 5, CREAM)
        g.disc(0, -16, 2.6, 2.6, WHITE); g.px(0, -16, GL); g.px(0, -17, GL); g.px(1, -16, GL)   # the clock
        g.rect(-2, -9, 2, -8, GOLD)                                                           # the statue niche
        g.rect(-2, -7, 2, -1, WOOD); g.rect(-1, -7, 1, -5, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- St John's: red-brick gatehouse with four turrets
    def johns():
        g = Grid()
        brick(g, -13, -10, 13, -1)
        merlons(g, -11, -13, 13, BR)
        for x in (-11, -8, 7, 10): win(g, x, -8, 1, 2)
        brick(g, -5, -19, 5, -1)
        for sx in (-1, 1):                                                    # the four turrets (two seen from the front)
            x0 = 5 if sx > 0 else -8
            stone(g, x0, -21, x0 + 2, -12)
            g.hline(-22, x0, x0 + 2, CREAMD); g.px(x0 + 1, -23, CREAM); g.px(x0 + 1, -24, GOLD)
        g.rect(-5, -20, 5, -20, CREAMD)
        g.rect(-2, -16, 2, -12, CREAM); g.px(0, -14, '#c43a3a'); g.px(0, -15, GOLD)       # coat of arms
        g.rect(-2, -9, 2, -1, WOOD); g.rect(-1, -9, 1, -8, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Trinity Hall: a modest brick court with gables
    def trinhall():
        g = Grid()
        brick(g, -10, -8, 10, -1, DK, DKD)
        for cx in (-6, 0, 6):                                                 # three little gables
            for i in range(4): g.hline(-9 - i, cx - 3 + i, cx + 3 - i, DK)
            g.px(cx, -11, CREAM)
        for x in (-8, -4, 4, 8): win(g, x, -7, 1, 3)
        for x in (-6, 6): win(g, x, -7, 1, 3)
        g.hline(-8, -10, 10, CREAM)
        g.rect(-1, -6, 1, -1, WOOD)
        brick(g, 8, -15, 9, -11, DK, DKD); g.hline(-16, 7, 10, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Clare: pale classical front with a pediment and cupola
    def clare():
        g = Grid()
        stone(g, -11, -9, 11, -1, WHITE, CREAMD)
        g.hline(-10, -11, 11, CREAMD)
        for x in (-9, -6, -3, 3, 6, 9): win(g, x, -8, 1, 3)
        pediment(g, 0, -10, 5, WHITE, CREAMD)
        g.disc(0, -13, 1.2, 1.2, GL)
        cupola(g, 0, -15)
        for x in range(-11, 12, 2): g.px(x, -11, CREAM)                      # balustrade
        g.rect(-2, -6, 2, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Gonville & Caius: a gate topped with a little cap
    def caius():
        g = Grid()
        stone(g, -11, -10, 11, -1)
        merlons(g, -11, -11, 11, CREAMD)
        for x in (-9, -6, 5, 8): win(g, x, -8, 1, 3)
        stone(g, -4, -14, 4, -1)
        g.hline(-15, -4, 4, CREAMD)
        for x in (-4, 0, 4): g.px(x, -16, CREAM)
        g.rect(-2, -20, 2, -17, CREAM); g.px(0, -19, GL); g.hline(-21, -3, 3, CREAMD)
        g.rect(-1, -23, 1, -22, CU); g.px(0, -24, GOLD); g.px(-1, -23, CUH)
        g.rect(-2, -8, 2, -1, WOOD); g.rect(-1, -8, 1, -7, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Corpus Christi: stone court and the golden Chronophage clock
    def corpus():
        g = Grid()
        stone(g, -10, -9, 10, -1, CREAM, CREAMD)
        for sx in (-6, 0, 6):                                                 # dormers in a slate roof
            pass
        for i, half in enumerate((11, 10, 9)): g.hline(-10 - i, -half, half, SLL if i % 2 else SL)
        for cx in (-6, 6):
            g.rect(cx - 1, -14, cx + 1, -11, CREAM); g.px(cx, -13, GL); g.hline(-15, cx - 2, cx + 2, SL); g.px(cx, -16, SL)
        for x in (-8, -4, 4, 8): win(g, x, -8, 1, 3)
        g.rect(-1, -6, 1, -1, WOOD)
        g.disc(0, -13, 2.4, 2.4, GOLD); g.px(0, -13, '#a87a1c'); g.px(0, -14, '#a87a1c'); g.px(1, -13, '#a87a1c')   # the clock
        g.outline(OL); return g

    # ---------------------------------------------------------------- Peterhouse: pale Gothic hall with a spirelet
    def peter():
        g = Grid()
        stone(g, -12, -9, 12, -1, '#efe1b2', '#d6c58a')
        stone(g, -5, -15, 5, -1, '#efe1b2', '#d6c58a')
        for i in range(6): g.hline(-16 - i, -5 + i, 5 - i, SL if i % 2 == 0 else SLL)       # steep gabled hall
        g.px(0, -22, GOLD)
        for x in (-3, 0, 3): g.rect(x, -12, x, -8, GL); g.px(x, -13, GL)                   # tall pointed windows
        for x in (-10, -8, 8, 10): win(g, x, -7, 1, 3)
        g.rect(-1, -4, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Pembroke: Wren's chapel, red brick with a cupola
    def pembroke():
        g = Grid()
        brick(g, -9, -10, 9, -1)
        for x in (-9, 9, -3, 3): g.vline(x, -10, -1, CREAM) if x in (-9, 9) else None
        for x in (-6, 0, 6): win(g, x, -8, 1, 4)
        pediment(g, 0, -11, 5, CREAM, CREAMD)
        g.disc(0, -13, 1.1, 1.1, GL)
        cupola(g, 0, -16)
        g.rect(-1, -4, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- St Catharine's: baroque wings round an open court
    def stcath():
        g = Grid()
        for sx in (-1, 1):
            x0 = 4 if sx > 0 else -12
            brick(g, x0, -11, x0 + 8, -1)
            g.hline(-11, x0, x0 + 8, CREAM)
            for x in (x0 + 2, x0 + 6): win(g, x, -9, 1, 2); win(g, x, -5, 1, 2)
            pediment(g, x0 + 4, -12, 3, CREAM, CREAMD)
        for sx in (-3, 3):                                                    # gate piers with balls
            stone(g, sx - 1, -6, sx, -1); g.px(sx - 1, -7, CREAM); g.px(sx, -7, CREAM)
        g.hline(-3, -2, 2, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Christ's: gatehouse with the Beaufort arms
    def christs():
        g = Grid()
        stone(g, -11, -9, 11, -1)
        merlons(g, -10, -11, 11, CREAMD)
        for x in (-9, -6, 5, 8): win(g, x, -7, 1, 3)
        stone(g, -5, -16, 5, -1)
        merlons(g, -17, -5, 5, CREAM)
        g.rect(-2, -14, 2, -10, WHITE); g.px(-1, -13, '#c43a3a'); g.px(0, -13, GOLD); g.px(1, -13, '#c43a3a')
        g.px(-1, -12, GOLD); g.px(0, -12, '#c43a3a'); g.px(1, -12, GOLD); g.px(0, -11, '#c43a3a')
        g.rect(-2, -8, 2, -1, WOOD); g.rect(-1, -9, 1, -8, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Emmanuel: pedimented chapel front and cupola
    def emma():
        g = Grid()
        brick(g, -12, -9, 12, -1)
        g.hline(-9, -12, 12, CREAM)
        for x in (-10, -7, 7, 10): win(g, x, -7, 1, 3)
        stone(g, -5, -12, 5, -1)
        pediment(g, 0, -13, 5, CREAM, CREAMD)
        for x in (-3, 0, 3): g.rect(x, -10, x, -5, GL)
        cupola(g, 0, -18)
        g.rect(-1, -4, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Sidney Sussex: dark brick with crow-stepped gables
    def sidney():
        g = Grid()
        brick(g, -11, -8, 11, -1, DK, DKD)
        for cx in (-6, 0, 6):                                                 # crow-stepped gables
            for i, half in enumerate((3, 2, 1)):
                g.hline(-9 - i * 2, cx - half, cx + half, DK); g.hline(-10 - i * 2, cx - half, cx + half, DK)
            g.px(cx, -15, CREAM)
        for x in (-8, -4, 4, 8): win(g, x, -7, 1, 3)
        for x in (-6, 0, 6): win(g, x, -12, 1, 2)
        g.hline(-8, -11, 11, CREAM)
        g.rect(-1, -5, 1, -1, WOOD)
        g.outline(OL); return g


    # ================================================================ the colleges beyond the river bend
    CONC, CONCD = '#c9c4b8', '#a8a294'                   # concrete
    MBR, MBRD = '#86594a', '#6e4638'                     # dark modern brick

    def roof(g, cx, y, half, c=SL, c2=SLL):              # a pitched roof (triangle), eaves at row y, rising one row per pixel
        for i in range(half + 1):
            g.hline(y - i, cx - half + i, cx + half - i, c if i % 2 == 0 else c2)

    def strip(g, x0, x1, y):                             # a long ribbon window
        g.hline(y, x0, x1, GL)

    # ---------------------------------------------------------------- Churchill: stepped 1960s blocks, flat roofs, ribbon windows
    def churchill():
        g = Grid()
        brick(g, -13, -9, -5, -1, MBR, MBRD); brick(g, -4, -17, 3, -1, MBR, MBRD); brick(g, 4, -12, 13, -1, MBR, MBRD)
        for x0, x1, top in ((-13, -5, -9), (-4, 3, -17), (4, 13, -12)): g.hline(top, x0, x1, CONC)
        for y in (-7, -4): strip(g, -12, -6, y)
        for y in (-15, -12, -9, -6): strip(g, -3, 2, y)
        for y in (-9, -6, -3): strip(g, 5, 12, y)
        g.rect(-2, -4, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Girton: Waterhouse red brick with its tall tower
    def girton():
        g = Grid()
        brick(g, -13, -9, 13, -1)
        for cx in (-9, 9): roof(g, cx, -10, 4, SL, SLL); g.px(cx, -13, CREAM)       # two gables
        for x in (-11, -7, 7, 11): win(g, x, -7, 1, 3)
        brick(g, -3, -18, 3, -1); g.hline(-18, -4, 4, CREAMD)
        roof(g, 0, -19, 4, SL, SLL)
        g.px(0, -24, GOLD)
        g.rect(-1, -15, 1, -12, CREAM); g.px(0, -14, GL)
        g.rect(-1, -5, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Fitzwilliam: dark brick with a curved concrete chapel roof
    def fitz():
        g = Grid()
        brick(g, -13, -9, 13, -1, MBR, MBRD)
        g.hline(-9, -13, 13, CONC)
        for y in (-7, -4): strip(g, -12, -7, y); strip(g, 7, 12, y)
        g.rect(-5, -12, 5, -1, CONC)
        g.disc(0, -12, 6, 6, CONC, cond=lambda x, y: y <= -12)                      # the curved roof
        for (x, y), c in list(g.p.items()):
            if c == CONC and y <= -14 and x > 1: g.px(x, y, CONCD)
        g.rect(-1, -9, 1, -5, GL)
        g.rect(-1, -4, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Lucy Cavendish: two steep-gabled Victorian houses
    def lucy():
        g = Grid()
        for x0 in (-12, 1):
            brick(g, x0, -9, x0 + 10, -1)
            roof(g, x0 + 5, -10, 6, SL, SLL)
            win(g, x0 + 2, -7, 1, 2); win(g, x0 + 7, -7, 1, 2)
            g.rect(x0 + 4, -4, x0 + 6, -1, WOOD)
        brick(g, -2, -17, -1, -12); g.hline(-18, -3, 0, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Murray Edwards: white concrete with a green dome
    def murray():
        g = Grid()
        g.rect(-13, -9, 13, -1, WHITE); g.hline(-9, -13, 13, CONC)
        for y in (-7, -4): strip(g, -12, -6, y); strip(g, 6, 12, y)
        g.rect(-5, -13, 5, -1, WHITE)
        for x in (-3, 0, 3): g.rect(x, -11, x, -4, GL)
        g.hline(-14, -6, 6, CONC)
        g.disc(0, -14, 6, 6, CU, cond=lambda x, y: y <= -15)
        for (x, y), c in list(g.p.items()):
            if c == CU and x <= -2: g.px(x, y, CUH)
        g.px(0, -21, GOLD); g.px(0, -22, GOLD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- St Edmund's: Gothic brick with a tall chapel gable and fleche
    def stedmunds():
        g = Grid()
        brick(g, -12, -8, 12, -1)
        for x in (-10, -7, 7, 10): win(g, x, -6, 1, 3)
        brick(g, -5, -13, 5, -1)
        roof(g, 0, -14, 6, SL, SLL)
        g.disc(0, -12, 1.4, 1.4, GL)
        brick(g, -12, -13, -9, -9); roof(g, -10, -14, 2, SL, SLL); g.vline(-10, -20, -17, SL); g.px(-10, -21, GOLD)
        g.rect(-1, -6, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Magdalene: red brick court with a bell cupola and white arcade
    def magdalene():
        g = Grid()
        brick(g, -12, -11, 12, -1)
        g.hline(-8, -12, 12, CREAM); g.hline(-12, -12, 12, CREAM)
        for x in (-9, -5, 5, 9): win(g, x, -10, 1, 2)
        for x in (-9, -5, 5, 9): win(g, x, -6, 1, 3)
        for cx in (-3, 0, 3):                                                       # the arcade
            g.rect(cx - 1, -6, cx + 1, -1, CREAM); g.rect(cx, -5, cx, -2, GL)
        cupola(g, 0, -13, WHITE, SL, SLL)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Robinson: a big brick block around a round hall
    def robinson():
        g = Grid()
        brick(g, -13, -10, 13, -1, DK, DKD)
        merlons(g, -11, -13, 13, DK)
        for x in (-11, -8, 8, 11): win(g, x, -8, 1, 2)
        g.rect(-6, -18, 6, -9, DK); 
        brick(g, -6, -18, 6, -10, DK, DKD)
        g.hline(-19, -7, 7, CONC)
        for x in (-4, -1, 2, 5): g.rect(x, -16, x, -12, GL)
        g.hline(-9, -6, 6, CONC)
        g.rect(-2, -5, 2, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Selwyn: red brick Gothic with a stone-trimmed chapel and turret
    def selwyn():
        g = Grid()
        brick(g, -12, -9, 12, -1)
        for x in (-8, -5, 5, 8): win(g, x, -7, 1, 3)
        brick(g, -3, -14, 4, -1)
        roof(g, 0, -15, 5, SL, SLL)
        g.disc(0, -11, 1.3, 1.3, CREAM); g.px(0, -11, GL)
        brick(g, 8, -17, 11, -9); roof(g, 9, -18, 2, SL, SLL); g.px(9, -23, GOLD)
        g.hline(-9, -12, 12, CREAM)
        g.rect(-1, -5, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Darwin: a cream Georgian house by the river
    def darwin():
        g = Grid()
        g.rect(-10, -12, 10, -1, '#efe6cc')
        g.hline(-12, -10, 10, CREAMD); g.hline(-6, -10, 10, CREAMD)
        for x in (-8, -4, 4, 8): win(g, x, -10, 1, 3); win(g, x, -5, 1, 3)
        for i, half in enumerate((11, 10, 9, 8)): g.hline(-13 - i, -half, half, SLL if i % 2 else SL)
        brick(g, 5, -20, 6, -16); g.hline(-21, 4, 7, CREAMD)
        g.rect(-2, -6, 2, -1, WHITE); g.rect(-1, -5, 1, -1, WOOD)
        g.hline(-7, -3, 3, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Downing: Greek-revival portico between low wings
    def downing():
        g = Grid()
        stone(g, -13, -8, 13, -1, WHITE, CREAMD)
        for x in (-11, -8, 8, 11): win(g, x, -6, 1, 3)
        stone(g, -6, -11, 6, -9, WHITE, CREAMD)
        pediment(g, 0, -12, 7, WHITE, CREAMD)
        for x in (-5, -2, 1, 4): g.rect(x, -9, x + 1, -2, WHITE); g.vline(x + 1, -9, -2, CREAMD)       # four columns
        g.hline(-1, -6, 6, CREAMD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Homerton: Victorian Gothic with a tall pointed tower
    def homerton():
        g = Grid()
        brick(g, -13, -9, 13, -1)
        for cx in (-9, 9): roof(g, cx, -10, 4, SL, SLL)
        for x in (-11, -7, 7, 11): win(g, x, -7, 1, 3)
        brick(g, -3, -16, 3, -1)
        stone(g, -4, -20, 4, -17, CREAM, CREAMD); g.px(0, -19, GL); g.px(-2, -19, GL); g.px(2, -19, GL)
        merlons(g, -21, -4, 4, CREAM)
        for x in (-4, 4): g.px(x, -22, CREAM); g.px(x, -23, GOLD)
        g.rect(-1, -14, 1, -11, CREAM); g.px(0, -13, GL)
        g.rect(-1, -5, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Hughes Hall: a Victorian villa with a bay window
    def hughes():
        g = Grid()
        brick(g, -9, -9, 9, -1, BR, BRD)
        g.hline(-9, -9, 9, CREAM)
        roof(g, 0, -10, 10, SL, SLL)
        brick(g, 5, -17, 6, -12); g.hline(-18, 4, 7, CREAMD)
        g.rect(-8, -8, -4, -2, CREAM); win(g, -7, -7, 1, 3); win(g, -5, -7, 1, 3)       # bay window
        win(g, 4, -7, 1, 3); win(g, 7, -7, 1, 3)
        g.rect(-1, -5, 1, -1, WOOD)
        g.outline(OL); return g

    # ---------------------------------------------------------------- Jesus: brick gate tower with turrets, chapel spirelet beside it
    def jesus():
        g = Grid()
        brick(g, -13, -9, 13, -1, DK, DKD)
        merlons(g, -10, -13, 13, DK)
        for x in (-11, -8, 7, 10): win(g, x, -7, 1, 3)
        brick(g, -4, -17, 4, -1, DK, DKD)
        merlons(g, -18, -4, 4, DK)
        for sx in (-5, 4): brick(g, sx, -21, sx + 1, -12, DK, DKD); g.px(sx, -22, CREAM); g.px(sx + 1, -22, CREAM)
        g.rect(-2, -9, 2, -1, WOOD); g.rect(-1, -10, 1, -9, CREAMD)
        g.rect(-1, -14, 1, -12, CREAM); g.px(0, -13, '#c43a3a')
        g.outline(OL); return g

    return dict(kings=kings, queens=queens, trinity=trinity, johns=johns, trinhall=trinhall, clare=clare, caius=caius,
                corpus=corpus, peter=peter, pembroke=pembroke, stcath=stcath, christs=christs, emma=emma, sidney=sidney,
                churchill=churchill, girton=girton, fitz=fitz, lucy=lucy, murray=murray, stedmunds=stedmunds, magdalene=magdalene,
                robinson=robinson, selwyn=selwyn, darwin=darwin, downing=downing, homerton=homerton, hughes=hughes, jesus=jesus)
