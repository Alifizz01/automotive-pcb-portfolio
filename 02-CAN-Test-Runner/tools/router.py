"""Grid router for the CAN-FD Test Runner (4 layers, 100 x 66 mm).

Inner layer 1 is a solid GND plane and inner layer 2 a solid 3V3 plane, so every SMD pad on
those nets gets a short stub and a via instead of a track. Signals and the other power nets
are routed on top and bottom. Derived from the project 01 router.
Original description follows.


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
PADS = os.path.join(HERE, "pads_board.txt")      # exported from the placed board
OUT = os.path.join(HERE, "routes.txt")

G = 0.1                      # grid pitch, mm
BW, BH = 100.0, 66.0
NX, NY = int(BW / G) + 1, int(BH / G) + 1
CLR = 0.19                   # routing clearance (rule 0.127 + grid rounding margin)
EDGE = 0.5                   # copper to board edge
MH_KEEP = 2.3                # 3.2 mm hole + 0.7 mm keep-out
VIA_D, VIA_H = 0.6, 0.3
BOTTOM_COST = 1.6
NL = 4                       # 0 top, 1 bottom, 2 inner L3 (3V3 pour), 3 inner L2 (GND plane, last resort)
LCOST = [1.0, 1.6, 2.4, 5.0]
VIA_COST = 6.0 / G           # a via "costs" 6 mm of track

PLANE = {"GND", "3V3"}
WIDTH = {n: 0.5 for n in ("VIN_P", "V1_IN", "V2_IN", "5V_BUCK", "VCHG", "VSYS", "VBAT", "CELL_P", "CELL_N",
                          "FET_MID", "5V_AUX", "BUCK_SW", "BB_L1", "BB_L2", "BOOST_SW", "VBUS")}
WIDTH.update({"GND": 0.4, "3V3": 0.4, "CAN1_H_C": 0.2, "CAN1_L_C": 0.2, "CAN2_H_C": 0.2, "CAN2_L_C": 0.2})
DEFAULT_W = 0.15


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
        self.layers = tuple(range(NL)) if self.th else ((1,) if f[8] == "Bottom Layer" else (0,))
        self.hole = (not self.net) and self.th

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
        self.owner = [np.zeros((NX, NY), np.int16) for _ in range(NL)]
        self.hard = np.zeros((NX, NY), bool)      # edge + mounting holes, both layers
        self.hard[: int(EDGE / G), :] = self.hard[-int(EDGE / G):, :] = True
        self.hard[:, : int(EDGE / G)] = self.hard[:, -int(EDGE / G):] = True
        for p in pads:
            if p.ref == "FREE":
                self.hard |= (XX - p.x) ** 2 + (YY - p.y) ** 2 <= MH_KEEP ** 2
                continue
            if p.hole:     # holder pegs: unplated holes through every layer
                self.hard |= (XX - p.x) ** 2 + (YY - p.y) ** 2 <= (p.sx / 2 + 0.3) ** 2
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
        for L in range(NL):
            self.owner[L][m] = self.nid[net]

    def blocked(self, net, w):
        """per layer: True where the CENTRE of a track of width w may not go"""
        k = self.nid[net]
        out = []
        for L in range(NL):
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
        lc = LCOST[L]
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
        # via: to any other layer
        if not via_block[i, j]:
            for L2 in range(NL):
                if L2 == L:
                    continue
                t = (L2, i, j)
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
    _vb = bd.via_ok(net)
    vblock = np.logical_or.reduce(_vb)
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
    """stub + via from every SMD pad of a plane net (GND, 3V3) into its inner plane"""
    for net in sorted(PLANE):
        for p in [q for q in bd.pads if q.net == net and not q.th]:
            L = p.layers[0]
            fw = WIDTH[net] if min(p.sx, p.sy) >= 0.5 else 0.2      # neck-down at fine-pitch pads
            ox, oy = STUB_END.get(id(p), (p.x, p.y))                # fine pitch: via at its own stub end
            block = bd.blocked(net, fw)
            vb = bd.via_ok(net)
            vblock = np.logical_or.reduce(vb)
            block[L][pad_mask(p)] = False
            best = None
            r0 = 0.0 if id(p) in STUB_END else 0.6
            for r in np.arange(r0, 3.01, 0.1):
                for ang in range(0, 360, 15):
                    x = ox + r * math.cos(math.radians(ang)); y = oy + r * math.sin(math.radians(ang))
                    if not (1 < x < BW - 1 and 1 < y < BH - 1):
                        continue
                    i, j = cell(x, y)
                    if vblock[i, j]:
                        continue
                    for opt in octi_options((ox, oy), (round(x / G) * G, round(y / G) * G)):
                        if all(clear_line(block, L, opt[k], opt[k + 1]) for k in range(len(opt) - 1)):
                            best = opt; break
                    if best:
                        break
                if best:
                    break
            if not best:
                report.append("%s fanout FAIL %s" % (net, p.name))
                continue
            for a1, b1 in zip(best, best[1:]):
                bd.add_track(net, L, a1, b1, fw)
            bd.add_via(net, best[-1])


STUB_END = {}


def escape_stubs(bd, report, routed_nets):
    """Staggered escape stubs from every fine-pitch signal pin, laid down before any routing,
    so each pin keeps its own exit (the usual fan-out pattern for LQFP/QFN parts)."""
    byref = {}
    for p in bd.pads:
        byref.setdefault(p.ref, []).append(p)
    n = 0
    for ref, ps in byref.items():
        if ref == "FREE":
            continue
        smd = [p for p in ps if not p.th and not p.hole]
        pitch = min((math.dist((a.x, a.y), (b.x, b.y)) for a in smd for b in smd if a is not b), default=9)
        if pitch > 0.66:
            continue
        cx = sum(p.x for p in ps) / len(ps); cy = sum(p.y for p in ps) / len(ps)
        rows = {}
        for p in smd:
            if not p.net or p.net in PLANE or p.net not in routed_nets:
                continue
            if p.sx >= p.sy:
                d = (1 if p.x > cx else -1, 0); key = ("x", round(p.x, 1))
            else:
                d = (0, 1 if p.y > cy else -1); key = ("y", round(p.y, 1))
            rows.setdefault(key, []).append((p, d))
        for key, items in rows.items():
            items.sort(key=lambda it: (it[0].y if key[0] == "x" else it[0].x))
            for k, (p, d) in enumerate(items):
                half = (p.sx if d[0] else p.sy) / 2
                ln = half + (0.5 if k % 2 == 0 else 1.4)
                end = (round((p.x + d[0] * ln) / G) * G, round((p.y + d[1] * ln) / G) * G)
                L = p.layers[0]
                block = bd.blocked(p.net, DEFAULT_W)
                block[L][pad_mask(p)] = False
                if clear_line(block, L, (p.x, p.y), end):
                    bd.add_track(p.net, L, (p.x, p.y), end, DEFAULT_W)
                    STUB_END[id(p)] = end
                    n += 1
    report.append("escape stubs: %d" % n)


def run(order, seed_report=True):
    bd = Board(load_pads())
    report = []
    gnd_fanout(bd, report)
    escape_stubs(bd, report, set(order))
    ok = True
    for net in order:
        w = WIDTH.get(net, DEFAULT_W)
        tries = [w] + [x for x in (0.3, 0.2) if x < w]
        done = False
        for wi in tries:
            if route_net(bd, net, wi, report):
                if wi != w:
                    report.append("  %s necked to %.1f mm" % (net, wi))
                done = True
                break
        ok = ok and done
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
        ax.plot([a[0], b[0]], [a[1], b[1]], color=["#e03030", "#3070ff", "#30c060", "#a060c0"][L],
                lw=w * 72 / 25.4 * fig.dpi / 100 * (fig.get_size_inches()[0] * 25.4 / (BW + 2)) / 1.0,
                solid_capstyle="round", alpha=0.85)
    for net, pt in bd.vias:
        ax.add_patch(Circle(pt, VIA_D / 2, fc="#ddd", ec="k", lw=0.3))
        ax.add_patch(Circle(pt, VIA_H / 2, fc="k"))
    ax.set_xlim(-1, BW + 1); ax.set_ylim(-1, BH + 1); ax.set_aspect("equal")
    fig.tight_layout(); fig.savefig(fn); plt.close(fig)


def failed_nets(report):
    out = []
    for r in report:
        if r.startswith("FAIL "):
            n = r.split()[1]
            if n not in out:
                out.append(n)
    return out


if __name__ == "__main__":
    import pickle
    pads = load_pads()
    nets = {}
    for p in pads:
        if p.net and p.net not in PLANE:
            nets.setdefault(p.net, []).append(p)
    def span(n):
        xs = [p.x for p in nets[n]]; ys = [p.y for p in nets[n]]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))
    routed = [n for n in nets if len(nets[n]) >= 2]
    power = sorted([n for n in routed if WIDTH.get(n, 0) >= 0.5], key=span)
    signal = sorted([n for n in routed if n not in power], key=span)
    base = power + signal
    first = []
    best = None
    for it in range(int(os.environ.get("RIPUP_PASSES", "4"))):
        order = first + [n for n in base if n not in first]
        bd, rep, ok = run(order)
        # a net that finally routed after necking is not a failure
        fails = [n for n in failed_nets(rep) if not any(r.strip().startswith(n + " necked") for r in rep)]
        fanfail = [r for r in rep if "fanout FAIL" in r]
        print("pass %d: %d nets failed, %d fanouts failed" % (it + 1, len(fails), len(fanfail)), flush=True)
        if best is None or len(fails) + len(fanfail) < best[0]:
            best = (len(fails) + len(fanfail), bd, rep, fails)
            write(bd)
            pickle.dump((bd.tracks, bd.vias), open(os.path.join(HERE, "routes_best.pkl"), "wb"))
        if not fails:
            break
        first = fails + [n for n in first if n not in fails]
    n, bd, rep, fails = best
    for r in rep:
        print(r)
    print("routed ok:", not fails, " failed nets:", fails, " tracks:", len(bd.tracks), " vias:", len(bd.vias))
    if "--plot" in sys.argv:
        plot(bd, os.path.join(HERE, "routes.png"))
