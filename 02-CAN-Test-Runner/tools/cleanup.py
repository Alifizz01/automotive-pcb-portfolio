"""Find duplicate vias and dead-end tracks (net antennae) in copper.txt exported from the board.
Writes altium/cleanup.txt: 'V net x y' and 'T net layer x1 y1 x2 y2' lines to delete."""
import math
U = 10000 / 0.0254 / 1000          # internal units per mm
TOP, BOT, L2, L3, MULTI = 1, 32, 2, 3, 74
POUR = {("GND", TOP), ("GND", BOT), ("GND", L2), ("3V3", L3)}
T, V, P = [], [], []
for line in open("copper.txt"):
    f = line.rstrip("\n").split("|")
    if f[0] == "T": T.append([f[1], int(f[2])] + [int(v) for v in f[3:8]])
    elif f[0] == "V": V.append([f[1]] + [int(v) for v in f[2:5]])
    elif f[0] == "P":
        w, h, rot = int(f[5]), int(f[6]), float(f[7].replace(",", "."))
        if round(rot) % 180 == 90: w, h = h, w
        P.append([f[1], int(f[2]), int(f[3]), int(f[4]), w, h])
tol = 0.03 * U
# 1) duplicate vias: same net, overlapping -> keep the first
dupv, keepv = [], []
for v in V:
    if any(k[0] == v[0] and math.hypot(k[1] - v[1], k[2] - v[2]) < v[3] for k in keepv):
        dupv.append(v)
    else:
        keepv.append(v)
cross = [(a, b) for i, a in enumerate(keepv) for b in keepv[i + 1:]
         if a[0] != b[0] and math.hypot(a[1] - b[1], a[2] - b[2]) < (a[3] + b[3]) / 2]


def on_seg(px, py, t):
    x1, y1, x2, y2, w = t[2:7]
    dx, dy = x2 - x1, y2 - y1
    L2_ = dx * dx + dy * dy
    s = 0 if L2_ == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2_))
    return math.hypot(px - (x1 + s * dx), py - (y1 + s * dy)) <= w / 2 + tol


def connected(net, layer, x, y, me, tracks):
    if (net, layer) in POUR:
        return True
    for v in keepv:
        if v[0] == net and math.hypot(v[1] - x, v[2] - y) <= v[3] / 2 + tol:
            return True
    for p in P:
        if p[0] == net and p[1] in (layer, MULTI) and abs(p[2] - x) <= p[4] / 2 + tol and abs(p[3] - y) <= p[5] / 2 + tol:
            return True
    for t in tracks:
        if t is not me and t[0] == net and t[1] == layer and on_seg(x, y, t):
            return True
    return False


tracks = [t for t in T]
dead = []
while True:
    kill = [t for t in tracks if not connected(t[0], t[1], t[2], t[3], t, tracks)
            or not connected(t[0], t[1], t[4], t[5], t, tracks)]
    if not kill:
        break
    dead += kill
    tracks = [t for t in tracks if t not in kill]
with open("altium/cleanup.txt", "w") as fo:
    for v in dupv:
        fo.write("V %s %d %d\n" % (v[0], v[1], v[2]))
    for t in dead:
        fo.write("T %s %d %d %d %d %d\n" % (t[0], t[1], t[2], t[3], t[4], t[5]))
print("duplicate vias", len(dupv), "| dead-end tracks", len(dead), "| different-net vias overlapping", len(cross))
for a, b in cross[:10]:
    print("  %s / %s at (%.2f, %.2f) mm" % (a[0], b[0], a[1] / U, a[2] / U))
