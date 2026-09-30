# -*- coding: utf-8 -*-
"""Placement for the 100 x 66 mm Test Runner board.

Major parts are placed by hand (mechanics and signal flow); every passive is then placed by
a greedy search next to the pins it serves, on a 0.25 mm occupancy grid with a courtyard
margin, so nothing overlaps. Writes altium/placement.txt (REF X Y ROT SIDE) and
pads_new.txt (every pad at its placed position, the router's input).
"""
import math, os
import numpy as np
import design
from footprints import FP

HERE = os.path.dirname(os.path.abspath(__file__))
BW, BH = 100.0, 66.0
HOLES = [(4, 4), (96, 4), (4, 62), (96, 62)]

# ref: (x, y, rotation, side)   side T = top, B = bottom (mirrored)
FIXED = {
    # connectors on the edges
    "J1": (24, 9.42, 0, "T"), "J2": (62, 9.42, 0, "T"),
    "J3": (96.525, 22, 90, "T"), "J4": (91.5, 42, 90, "T"),
    "J5": (34, 61.5, 0, "T"), "J6": (6.5, 44, 270, "T"), "J7": (45, 55, 0, "T"),
    "BT1": (45, 40, 180, "B"), "BT2": (19, 58, 0, "T"),
    "SW1": (77, 60, 0, "T"), "SW2": (88, 60, 0, "T"),
    # controller
    "U1": (58, 38, 0, "T"), "Y1": (46.5, 39.5, 0, "T"),
    # CAN front ends, right behind their connectors
    "U2": (18, 19, 0, "T"), "U11": (27.5, 16.5, 90, "T"),
    "U3": (56, 19, 0, "T"), "U12": (65.5, 16.5, 90, "T"),
    # vehicle input and 5 V buck, between J2 and the USB/SD edge
    "D1": (33, 16.5, 0, "T"), "D2": (71, 16.5, 0, "T"), "D3": (74.5, 22, 90, "T"),
    "U4": (80.5, 20, 0, "T"), "L1": (81.5, 28.5, 0, "T"),
    # charger and power path next to it
    "U5": (68.5, 22.5, 0, "T"), "D4": (70.5, 36.5, 0, "T"), "D5": (88, 30, 90, "T"), "D6": (65.5, 27, 90, "T"),
    "Q1": (69.5, 27.5, 0, "T"), "Q4": (78.5, 35.5, 0, "T"),
    # rails, left of the controller
    "U8": (37, 37, 0, "T"), "L2": (37, 42, 0, "T"), "U9": (37, 30, 0, "T"), "L3": (41.5, 30, 90, "T"),
    # cell protection near the cell's negative pad (x 10.3), counter near the positive (x 89.7)
    "U6": (15, 36, 0, "T"), "Q2": (19.5, 33, 0, "T"), "Q3": (19.5, 37.5, 0, "T"), "U7": (80, 53, 0, "T"),
    # user interface
    "U10": (30, 48, 0, "T"), "D7": (67, 63, 0, "T"), "Q5": (78, 44, 90, "T"), "U13": (88.5, 22, 90, "T"),
}


def rot(x, y, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return x * c - y * s, x * s + y * c


def pad_world(fpname, px, py, x, y, a, side):
    if side == "B":          # Altium flips a part to the bottom by mirroring in y (checked on BT1's pegs)
        py = -py
    rx, ry = rot(px, py, a)
    return x + rx, y + ry


def extent(fpname, x, y, a, side, margin=0.25):
    """courtyard: union of pads and body, in board coordinates"""
    f = FP[fpname]
    pts = []
    for p in f["pads"]:
        hw, hh = p[3] / 2, p[4] / 2
        for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
            pts.append((p[1] + dx, p[2] + dy))
    if f["body"]:
        bw, bh = f["body"]
        pts += [(-bw / 2, -bh / 2), (bw / 2, bh / 2), (-bw / 2, bh / 2), (bw / 2, -bh / 2)]
    else:                      # no centred body: the silkscreen outline is the courtyard
        for x1, y1, x2, y2 in f["silk"]:
            pts += [(x1, y1), (x2, y2)]
    w = [pad_world(fpname, px, py, x, y, a, side) for px, py in pts]
    xs, ys = [p[0] for p in w], [p[1] for p in w]
    return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin


G = 0.25
NX, NY = int(BW / G), int(BH / G)
occ = {"T": np.zeros((NX, NY), bool), "B": np.zeros((NX, NY), bool)}


def mark(side, e):
    i0, j0 = max(0, int(e[0] / G)), max(0, int(e[1] / G))
    i1, j1 = min(NX, int(math.ceil(e[2] / G))), min(NY, int(math.ceil(e[3] / G)))
    occ[side][i0:i1, j0:j1] = True


def free(side, e):
    if e[0] < 0.6 or e[1] < 0.6 or e[2] > BW - 0.6 or e[3] > BH - 0.6:
        return False
    for hx, hy in HOLES:     # 3.2 mm hole + 1 mm keep-out
        cx, cy = min(max(hx, e[0]), e[2]), min(max(hy, e[1]), e[3])
        if math.hypot(cx - hx, cy - hy) < 2.6:
            return False
    i0, j0 = int(e[0] / G), int(e[1] / G)
    i1, j1 = int(math.ceil(e[2] / G)), int(math.ceil(e[3] / G))
    return not occ[side][i0:i1, j0:j1].any()


PARTS = {r: (s, f) for r, s, f, c, m in design.PARTS}


def check_fixed():
    """every hand-placed part must clear every other one on its side, and every hole"""
    bad = []
    items = list(FIXED.items())
    holes = []
    for ref, (x, y, a, side) in items:
        f = PARTS[ref][1]
        for p in FP[f]["pads"]:
            if p[6] in ("TH", "NPTH"):
                cx, cy = pad_world(f, p[1], p[2], x, y, a, side)
                holes.append((ref, cx, cy, max(p[3], p[4]) / 2 + 0.3))
    for i, (r1, (x1, y1, a1, s1)) in enumerate(items):
        e1 = extent(PARTS[r1][1], x1, y1, a1, s1, 0.15)
        for r2, (x2, y2, a2, s2) in items[i + 1:]:
            if s1 != s2:
                continue
            e2 = extent(PARTS[r2][1], x2, y2, a2, s2, 0.15)
            if e1[0] < e2[2] and e2[0] < e1[2] and e1[1] < e2[3] and e2[1] < e1[3]:
                bad.append("overlap %s / %s" % (r1, r2))
        for (hr, hx, hy, rr) in holes:
            if hr == r1:
                continue
            cx, cy = min(max(hx, e1[0]), e1[2]), min(max(hy, e1[1]), e1[3])
            if math.hypot(cx - hx, cy - hy) < rr:
                bad.append("hole of %s at (%.1f, %.1f) under %s" % (hr, hx, hy, r1))
    return bad


PIN_NET = {m: n for n, ms in design.NETS.items() for m in ms}
PLACE = {}
DECOUPLE = {}
_bad = check_fixed()
if _bad:
    raise SystemExit("fixed placement conflicts:\n  " + "\n  ".join(_bad))
for ref, (x, y, a, side) in FIXED.items():
    f = PARTS[ref][1]
    e = extent(f, x, y, a, side)
    PLACE[ref] = (x, y, a, side)
    mark(side, e)
    if side == "B":            # a bottom part still blocks through-hole space? only its own side
        pass
# a through-hole part blocks the other side only at its holes, not its whole outline
for ref, (x, y, a, side) in FIXED.items():
    f = PARTS[ref][1]
    other = "B" if side == "T" else "T"
    for p in FP[f]["pads"]:
        if p[6] in ("TH", "NPTH"):
            cx, cy = pad_world(f, p[1], p[2], x, y, a, side)
            r = max(p[3], p[4]) / 2 + 0.25
            mark(other, (cx - r, cy - r, cx + r, cy + r))

POWERNETS = {"GND", "3V3", "5V_AUX", "VSYS"}


def pin_pos(ref, num):
    s, f = PARTS[ref]
    x, y, a, side = PLACE[ref]
    for p in FP[f]["pads"]:
        if p[0] == num:
            return pad_world(f, p[1], p[2], x, y, a, side)
    return None


passives = [r for r, s, f, c, m in design.PARTS if r not in FIXED]

# Decouplers: every cap between a supply rail and GND is tied to one IC supply pin on that
# rail (ER-06: within 5 mm). Pins are served round-robin so each gets its own cap, and these
# caps are placed first, before other passives take the space next to the ICs.
SUPPLY_OWNER = {}
SUPPLY_PIN_NAMES = {"VDD", "VDDA", "VDDUSB", "VREF+", "VBAT", "VIO", "VIN", "IN", "OUT", "VOUT", "VCC"}


def SUPPLY_NAME(ref, num):
    d, left, right = design.SYM[PARTS[ref][0]]
    return any(p[0] == num and p[1] in SUPPLY_PIN_NAMES for p in left + right)

_pins_by_rail = {}
for n, ms in design.NETS.items():
    if n == "GND":
        continue
    for m in ms:
        r2 = m.split(".", 1)[0]
        if (r2.startswith("U") or r2 == "J5") and SUPPLY_NAME(r2, m.split(".", 1)[1]):
            _pins_by_rail.setdefault(n, []).append(m)
_turn = {}
for r in passives:
    if PARTS[r][0] != "CAP":
        continue
    nets = {PIN_NET.get(r + ".1"), PIN_NET.get(r + ".2")}
    if "GND" in nets and len(nets) == 2:
        rail = (nets - {"GND"}).pop()
        pins = _pins_by_rail.get(rail)
        if pins:
            k = _turn.get(rail, 0); _turn[rail] = k + 1
            SUPPLY_OWNER[r] = pins[k % len(pins)]
passives.sort(key=lambda r: 0 if r in SUPPLY_OWNER else 1)
NEAR_MCU = {"R25": True}      # passives that belong at the MCU end (e.g. BOOT0 pull-down)
for r in passives:            # BOOT0 / NRST / crystal parts stay by the MCU
    nets = {PIN_NET.get(r + ".1"), PIN_NET.get(r + ".2")}
    if nets & {"BOOT0", "NRST", "OSC_IN", "OSC_OUT", "VCAP1", "VCAP2"}:
        NEAR_MCU[r] = True
_ux, _uy = FIXED["U1"][:2]
ESCAPE_BAND = (_ux - 10.4, _uy - 10.4, _ux + 10.4, _uy + 10.4)
# place passives whose nets reach a placed part first; repeat until all placed
pending = list(passives)
for rounds in range(6):
    nxt = []
    for ref in pending:
        s, f = PARTS[ref]
        targets = []
        if ref in SUPPLY_OWNER:
            r2, p2 = SUPPLY_OWNER[ref].split(".", 1)
            targets = [pin_pos(r2, p2)]
        for num in (("1", "2") if not targets else ()):
            n = PIN_NET.get(ref + "." + num)
            if n is None or n in POWERNETS:
                continue
            for m in design.NETS[n]:
                r2, p2 = m.split(".", 1)
                if r2 != ref and r2 in PLACE:
                    pp = pin_pos(r2, p2)
                    if pp:
                        targets.append(pp)
        if not targets:
            # decoupling cap between supply rails: next to a supply pin of the IC in its own
            # schematic block, one cap per pin in turn (ER-06: within 5 mm of the pin)
            rails = [PIN_NET.get(ref + ".1"), PIN_NET.get(ref + ".2")]
            rail = next((r for r in rails if r and r != "GND"), None)
            blk = design.BLOCK.get(ref)
            cands = []
            for m in design.NETS.get(rail, []):
                r2, p2 = m.split(".", 1)
                if r2 in PLACE and PARTS[r2][0] not in ("RES", "CAP") and (design.BLOCK.get(r2) == blk or blk == "MCU" and r2 == "U1"):
                    cands.append(pin_pos(r2, p2))
            if not cands:
                for m in design.NETS.get(rail, []):
                    r2, p2 = m.split(".", 1)
                    if r2 in PLACE and PARTS[r2][0] not in ("RES", "CAP"):
                        cands.append(pin_pos(r2, p2))
            used = DECOUPLE.setdefault(rail, 0)
            DECOUPLE[rail] = used + 1
            targets = [cands[used % len(cands)]] if cands else [(50, 33)]
        if ref not in SUPPLY_OWNER and not NEAR_MCU.get(ref):
            far = []
            for num in ("1", "2"):
                n = PIN_NET.get(ref + "." + num)
                if n is None or n in POWERNETS:
                    continue
                for m in design.NETS[n]:
                    r2, p2 = m.split(".", 1)
                    if r2 not in (ref, "U1") and r2 in PLACE:
                        far.append(pin_pos(r2, p2))
            if far:
                targets = far
        tx = sum(t[0] for t in targets) / len(targets)
        ty = sum(t[1] for t in targets) / len(targets)
        best = None
        for rad in np.arange(0, 25, 0.25):
            nk = max(8, int(rad * 16))
            for k in range(nk):
                ang = 2 * math.pi * k / nk
                x = round((tx + rad * math.cos(ang)) / 0.25) * 0.25
                y = round((ty + rad * math.sin(ang)) / 0.25) * 0.25
                for a in (0, 90):
                    e = extent(f, x, y, a, "T", 0.4)
                    in_band = (e[0] < ESCAPE_BAND[2] and ESCAPE_BAND[0] < e[2] and e[1] < ESCAPE_BAND[3] and ESCAPE_BAND[1] < e[3])
                    if in_band and ref not in SUPPLY_OWNER and not NEAR_MCU.get(ref):
                        continue
                    if free("T", e):
                        best = (x, y, a); break
                if best: break
            if best: break
        if not best:
            raise SystemExit("no room for " + ref)
        PLACE[ref] = (best[0], best[1], best[2], "T")
        mark("T", extent(f, best[0], best[1], best[2], "T", 0.4))
    pending = nxt
    if not pending:
        break

with open(os.path.join(HERE, "altium", "placement.txt"), "w") as fo:
    for ref, (x, y, a, side) in PLACE.items():
        fo.write("%s %d %d %d %s\n" % (ref, round(x * 1000), round(y * 1000), a, side))

# pads at placed positions, in the pads_export format the router reads
with open(os.path.join(HERE, "pads_new.txt"), "w") as fo:
    for ref, (x, y, a, side) in PLACE.items():
        s, f = PARTS[ref]
        for p in FP[f]["pads"]:
            if not p[0]:
                continue
            wx, wy = pad_world(f, p[1], p[2], x, y, a, side)
            w, h = p[3], p[4]
            if a % 180 == 90:
                w, h = h, w
            layer = "Multi Layer" if p[6] == "TH" else ("Top Layer" if side == "T" else "Bottom Layer")
            shape = "1" if p[5] == "O" else "2"
            fo.write("%s|%s|%s|%.4f|%.4f|%.4f|%.4f|0|%s|%.3f|%s\n" % (
                ref, p[0], PIN_NET.get(ref + "." + p[0], ""), wx, wy, w, h, layer, p[7], shape))
    for i, (hx, hy) in enumerate(HOLES):
        fo.write("FREE|MH%d||%.4f|%.4f|3.2|3.2|0|Multi Layer|3.2|1\n" % (i + 1, hx, hy))
print("placed", len(PLACE), "parts")
