"""Grid router for the CAN-FD Sniffer pHAT (2 layers, 65 x 30 mm).

Reads ../pads_export.txt (dumped from the board by scripts/exportpads.pas) and
writes routes.txt, which scripts/placeroutes.pas turns into Altium tracks/vias.

Strategy (what a designer would do by hand on a 2-layer board):
  * bottom layer is kept as a near-solid GND pour -> routing there costs 4x,
  * every SMD GND pad gets a short stub + via straight into that pour,
  * signals and power are routed as octilinear (0/45/90 deg) tracks,
  * copper stays out of the 6.2 mm bare land round each mounting hole
    (Raspberry Pi HAT mechanical spec).

Usage: python route.py [--plot]
"""
import heapq, math, os, sys, itertools, random
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PADS = os.path.join(HERE, "..", "pads_new.txt")      # written by place.py
OUT = os.path.join(HERE, "routes.txt")

G = 0.05                     # grid pitch, mm
BW, BH = 65.0, 30.0
NX, NY = int(BW / G) + 1, int(BH / G) + 1
CLR = 0.25                   # routing clearance (rule is 0.152; keep margin)
EDGE = 0.5                   # copper to board edge
MH_KEEP = 3.2                # radius of bare land round mounting holes
VIA_D, VIA_H = 0.6, 0.3
BOTTOM_COST = 4.0
VIA_COST = 6.0 / G           # a via "costs" 6 mm of track

WIDTH = {"+3V3": 0.5, "+5V": 0.5, "GND": 0.4, "CANH": 0.3, "CANL": 0.3}
DEFAULT_W = 0.254


# ---------------------------------------------------------------- data
class Pad:
    def __init__(self, f):
        self.ref, self.num, self.net = f[0], f[1], f[2]
        self.x, self.y = float(f[3]), float(f[4])
        sx, sy, rot = float(f[5]), float(f[6]), float(f[7])
        if round(rot) % 180 == 90:
            sx, sy = sy, sx
        self.sx, self.sy = sx, sy
        self.th = f[8] == "Multi Layer"
        self.round = f[10].strip() == "1" and abs(sx - sy) < 1e-3
        self.layers = (0, 1) if self.th else (0,)

    @property
    def name(self):
        return "%s.%s" % (self.ref, self.num)


def load_pads():
    pads = []
    for line in open(PADS, encoding="utf-8"):
        f = line.rstrip("\n").split("|")
        if len(f) >= 11:
            pads.append(Pad(f))
    return pads


def cell(x, y):
    return int(round(x / G)), int(round(y / G))


def mm(i, j):
    return i * G, j * G


# ---------------------------------------------------------------- rasters
XX, YY = np.meshgrid(np.arange(NX) * G, np.arange(NY) * G, indexing="ij")


def pad_mask(p, grow=0.0):
    if p.round:
        return (XX - p.x) ** 2 + (YY - p.y) ** 2 <= (p.sx / 2 + grow) ** 2
    return (np.abs(XX - p.x) <= p.sx / 2 + grow) & (np.abs(YY - p.y) <= p.sy / 2 + grow)


def seg_mask(x1, y1, x2, y2, r):
    """cells within r of the segment (capsule)"""
    x0, x1b = min(x1, x2) - r, max(x1, x2) + r
    y0, y1b = min(y1, y2) - r, max(y1, y2) + r
    i0, i1 = max(0, int(x0 / G) - 1), min(NX, int(x1b / G) + 2)
    j0, j1 = max(0, int(y0 / G) - 1), min(NY, int(y1b / G) + 2)
    sub_x, sub_y = XX[i0:i1, j0:j1], YY[i0:i1, j0:j1]
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        t = 0
    else:
        t = np.clip(((sub_x - x1) * dx + (sub_y - y1) * dy) / L2, 0, 1)
    d2 = (sub_x - (x1 + t * dx)) ** 2 + (sub_y - (y1 + t * dy)) ** 2
    m = np.zeros((NX, NY), bool)
    m[i0:i1, j0:j1] = d2 <= r * r
    return m


class Board:
    def __init__(self, pads):
        self.pads = pads
        self.nets = sorted({p.net for p in pads if p.net})
        self.nid = {n: k + 1 for k, n in enumerate(self.nets)}
        # owner[layer] : 0 free, -1 foreign/no-net copper, k net id
        self.owner = [np.zeros((NX, NY), np.int16) for _ in range(2)]
        self.hard = np.zeros((NX, NY), bool)      # edge + mounting holes, both layers
        self.hard[: int(EDGE / G), :] = self.hard[-int(EDGE / G):, :] = True
        self.hard[:, : int(EDGE / G)] = self.hard[:, -int(EDGE / G):] = True
        for p in pads:
            if p.ref == "FREE":
                self.hard |= (XX - p.x) ** 2 + (YY - p.y) ** 2 <= MH_KEEP ** 2
                continue
            k = self.nid.get(p.net, -1)
            m = pad_mask(p)
            for L in p.layers:
                self.owner[L][m] = k
        self.tracks, self.vias = [], []

    def add_track(self, net, L, a, b, w):
        self.tracks.append((net, L, a, b, w))
        self.owner[L][seg_mask(a[0], a[1], b[0], b[1], w / 2)] = self.nid[net]

    def add_via(self, net, pt):
        self.vias.append((net, pt))
        m = (XX - pt[0]) ** 2 + (YY - pt[1]) ** 2 <= (VIA_D / 2) ** 2
        for L in (0, 1):
            self.owner[L][m] = self.nid[net]

    def blocked(self, net, w):
        """per layer: True where the CENTRE of a track of width w may not go"""
        k = self.nid[net]
        out = []
        for L in (0, 1):
            foreign = (self.owner[L] != 0) & (self.owner[L] != k)
            d = ndimage.distance_transform_edt(~foreign) * G
            out.append((d < w / 2 + CLR) | self.hard)
        return out

    def via_ok(self, net):
        return self.blocked(net, VIA_D)


# ---------------------------------------------------------------- search
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def astar(block, via_block, sources, targets, bottom_cost=BOTTOM_COST):
    """sources/targets: sets of (L,i,j). Returns list of (L,i,j) or None."""
    tlist = list(targets)
    tx = np.array([t[1] for t in tlist]); ty = np.array([t[2] for t in tlist])

    def h(i, j):
        dx = np.abs(tx - i); dy = np.abs(ty - j)
        return float(np.min(np.maximum(dx, dy) + (math.sqrt(2) - 1) * np.minimum(dx, dy)))

    gbest = {}
    prev = {}
    pq = []
    for s in sources:
        gbest[s] = 0.0
        heapq.heappush(pq, (h(s[1], s[2]), 0.0, s))
    tset = set(targets)
    n = 0
    while pq:
        f, g, s = heapq.heappop(pq)
        if g > gbest.get(s, 1e18):
            continue
        if s in tset:
            path = [s]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1]
        n += 1
        if n > 1_500_000:
            return None
        L, i, j = s
        lc = 1.0 if L == 0 else bottom_cost
        for di, dj in DIRS:
            a, b = i + di, j + dj
            if not (0 <= a < NX and 0 <= b < NY):
                continue
            t = (L, a, b)
            if block[L][a, b] and t not in tset:
                continue
            ng = g + lc * (1.4142 if di and dj else 1.0)
            if ng < gbest.get(t, 1e18):
                gbest[t] = ng; prev[t] = s
                heapq.heappush(pq, (ng + h(a, b), ng, t))
        # via
        if not via_block[i, j]:
            t = (1 - L, i, j)
            ng = g + VIA_COST
            if ng < gbest.get(t, 1e18):
                gbest[t] = ng; prev[t] = s
                heapq.heappush(pq, (ng + h(i, j), ng, t))
    return None


# ---------------------------------------------------------------- geometry clean-up
def clear_line(block, L, a, b):
    x1, y1 = a; x2, y2 = b
    n = max(2, int(math.hypot(x2 - x1, y2 - y1) / (G / 2)) + 1)
    for k in range(n + 1):
        t = k / n
        i, j = cell(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        if block[L][i, j]:
            return False
    return True


def octi_options(a, b):
    """two-segment 45-degree connections a->b (diagonal first / straight first)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = min(abs(dx), abs(dy))
    sx, sy = math.copysign(1, dx), math.copysign(1, dy)
    if abs(dx) < 1e-9 or abs(dy) < 1e-9 or abs(abs(dx) - abs(dy)) < 1e-9:
        return [[a, b]]
    m1 = (a[0] + sx * d, a[1] + sy * d)          # diagonal first
    m2 = (b[0] - sx * d, b[1] - sy * d)          # straight first
    return [[a, m1, b], [a, m2, b]]


def simplify(block, pts, L, keep_ends):
    """greedy octilinear string-pulling on one layer's point list"""
    out = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        best = None
        for j in range(len(pts) - 1, i, -1):
            for opt in octi_options(pts[i], pts[j]):
                if all(clear_line(block, L, opt[k], opt[k + 1]) for k in range(len(opt) - 1)):
                    best = (j, opt); break
            if best:
                break
        if not best:
            best = (i + 1, [pts[i], pts[i + 1]])
        out.extend(best[1][1:])
        i = best[0]
    # merge collinear
    res = [out[0]]
    for p in out[1:]:
        if len(res) >= 2:
            a, b = res[-2], res[-1]
            if abs((b[0] - a[0]) * (p[1] - b[1]) - (b[1] - a[1]) * (p[0] - b[0])) < 1e-6:
                res[-1] = p; continue
        if math.hypot(p[0] - res[-1][0], p[1] - res[-1][1]) > 1e-6:
            res.append(p)
    return res


# ---------------------------------------------------------------- routing a net
def pad_center_cells(p):
    i, j = cell(p.x, p.y)
    return {(L, i, j) for L in p.layers}


def route_net(bd, net, w, report):
    pins = [p for p in bd.pads if p.net == net]
    if len(pins) < 2:
        return True
    block = bd.blocked(net, w)
    vblock = bd.via_ok(net)[0] | bd.via_ok(net)[1]
    # pads of this net are always enterable
    for p in pins:
        for L in p.layers:
            block[L][pad_mask(p)] = False
    tree_cells = set(pad_center_cells(pins[0]))
    tree_pts = {}
    remaining = pins[1:]
    # connect nearest pins first
    while remaining:
        targets = {}
        for p in remaining:
            for c in pad_center_cells(p):
                targets[c] = p
        path = astar(block, vblock, tree_cells, set(targets))
        if path is None:
            report.append("FAIL %s (w=%.3f) to %s" % (net, w, ",".join(p.name for p in remaining)))
            return False
        hit = targets[path[-1]]
        remaining.remove(hit)
        # split into layer runs
        runs, cur = [], [path[0]]
        for s in path[1:]:
            if s[0] != cur[-1][0]:
                runs.append(cur); cur = [s]
            else:
                cur.append(s)
        runs.append(cur)
        for r_i, run in enumerate(runs):
            L = run[0][0]
            pts = [mm(s[1], s[2]) for s in run]
            # snap end at a pad centre exactly
            if r_i == len(runs) - 1:
                pts[-1] = (hit.x, hit.y)
            if r_i == 0:
                for p in pins:
                    if cell(p.x, p.y) == (run[0][1], run[0][2]):
                        pts[0] = (p.x, p.y)
            pts = simplify(block, pts, L, True) if len(pts) > 1 else pts
            for a, b in zip(pts, pts[1:]):
                bd.add_track(net, L, a, b, w)
            if r_i < len(runs) - 1:
                bd.add_via(net, pts[-1])
        for s in path:
            tree_cells.add(s)
        for c in pad_center_cells(hit):
            tree_cells.add(c)
        # new copper must not block own later branches, but DOES change foreign clearance
    return True


def gnd_fanout(bd, report):
    """stub + via from every SMD GND pad into the bottom pour"""
    net = "GND"
    for p in [q for q in bd.pads if q.net == net and not q.th]:
        block = bd.blocked(net, WIDTH[net])
        vb = bd.via_ok(net)
        vblock = vb[0] | vb[1]
        best = None
        for r in np.arange(0.9, 3.01, 0.1):
            for ang in range(0, 360, 15):
                x = p.x + r * math.cos(math.radians(ang)); y = p.y + r * math.sin(math.radians(ang))
                if not (0 < x < BW and 0 < y < BH):
                    continue
                i, j = cell(x, y)
                if vblock[i, j]:
                    continue
                # stub must leave the pad octilinearly and be clear
                for opt in octi_options((p.x, p.y), (round(x / G) * G, round(y / G) * G)):
                    tmp = [b.copy() for b in block]
                    tmp[0][pad_mask(p)] = False
                    if all(clear_line(tmp, 0, opt[k], opt[k + 1]) for k in range(len(opt) - 1)):
                        best = opt; break
                if best:
                    break
            if best:
                break
        if not best:
            report.append("GND fanout FAIL %s" % p.name)
            continue
        for a, b in zip(best, best[1:]):
            bd.add_track(net, 0, a, b, WIDTH[net])
        bd.add_via(net, best[-1])


def run(order, seed_report=True):
    bd = Board(load_pads())
    report = []
    gnd_fanout(bd, report)
    ok = True
    for net in order:
        w = WIDTH.get(net, DEFAULT_W)
        if not route_net(bd, net, w, report):
            if w > 0.3 and route_net(bd, net, 0.3, report):
                report.append("  %s necked to 0.3 mm" % net)
                continue
            ok = False
    return bd, report, ok


def write(bd):
    with open(OUT, "w") as f:
        for net, L, a, b, w in bd.tracks:
            f.write("T %s %d %d %d %d %d %d\n" % (net, L, round(a[0] * 1000), round(a[1] * 1000),
                                                  round(b[0] * 1000), round(b[1] * 1000), round(w * 1000)))
        for net, pt in bd.vias:
            f.write("V %s %d %d %d %d\n" % (net, round(pt[0] * 1000), round(pt[1] * 1000),
                                            round(VIA_D * 1000), round(VIA_H * 1000)))


def plot(bd, fn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    fig, ax = plt.subplots(figsize=(19.5, 9.4), dpi=100)
    ax.add_patch(Rectangle((0, 0), BW, BH, fc="#1d4d2a", ec="k"))
    for p in bd.pads:
        c = "#c8a040" if p.net else "#777"
        if p.ref == "FREE":
            ax.add_patch(Circle((p.x, p.y), MH_KEEP, fc="none", ec="w", ls=":"))
            ax.add_patch(Circle((p.x, p.y), p.sx / 2, fc="w"))
            continue
        if p.round:
            ax.add_patch(Circle((p.x, p.y), p.sx / 2, fc=c))
        else:
            ax.add_patch(Rectangle((p.x - p.sx / 2, p.y - p.sy / 2), p.sx, p.sy, fc=c))
        ax.text(p.x, p.y, p.name, fontsize=5, ha="center", va="center", color="k")
    for net, L, a, b, w in sorted(bd.tracks, key=lambda t: -t[1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#e03030" if L == 0 else "#3070ff",
                lw=w * 72 / 25.4 * fig.dpi / 100 * (fig.get_size_inches()[0] * 25.4 / (BW + 2)) / 1.0,
                solid_capstyle="round", alpha=0.85)
    for net, pt in bd.vias:
        ax.add_patch(Circle(pt, VIA_D / 2, fc="#ddd", ec="k", lw=0.3))
        ax.add_patch(Circle(pt, VIA_H / 2, fc="k"))
    ax.set_xlim(-1, BW + 1); ax.set_ylim(-1, BH + 1); ax.set_aspect("equal")
    fig.tight_layout(); fig.savefig(fn); plt.close(fig)


if __name__ == "__main__":
    # routing order: short/critical first, power trees, then the GPIO fan-in
    base = ["XTAL1", "CANH", "CANL", "TERM", "TXCAN", "RXCAN", "STBY",
            "SPI_SCLK", "SPI_MOSI", "SPI_MISO", "SPI_CE0", "CAN_INT",
            "+5V", "+3V3", "ID_SD", "ID_SC", "EE_WP", "LED_PWR", "LED_ACT"]
    bd, rep, ok = run(base)
    for r in rep:
        print(r)
    print("routed ok:", ok, " tracks:", len(bd.tracks), " vias:", len(bd.vias))
    write(bd)
    if "--plot" in sys.argv:
        plot(bd, os.path.join(HERE, "routes.png"))
