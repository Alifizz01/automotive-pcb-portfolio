"""New placement: signal flow left->right  Pi SPI -> U1 -> U2 -> J2.

Moves footprints in ../pads_export.txt to the NEW table, checks pad-to-pad
clearance between different nets, and writes
  placement.txt      REF x y rot       (read by scripts/placecomps.pas)
  ../pads_new.txt    pads_export format at the new positions (router input)
"""
import math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ref: (x, y, rot) - reference point in mm, rotation in degrees
NEW = {
    # --- controller + clock, under SPI pins 19-24 --------------------
    "U1": (31.0, 17.0, 90),    # top row = SPI pins, faces J1
    "C7": (25.4, 18.4, 270),   # 100 nF at U1.14 VDD
    "C6": (23.0, 18.4, 270),   # 10 uF 3V3 bulk
    "Y1": (33.0, 11.2, 0),     # 40 MHz osc, OUT pad next to U1.6 OSC1
    "C1": (29.0, 10.6, 180),   # 100 nF at Y1 VDD
    # --- HAT ID EEPROM, directly under J1 pins 27/28 -----------------
    "U3": (40.2, 19.8, 90),    # SDA/SCL on the top row -> straight up to J1
    "R1": (45.2, 22.0, 0),     # ID_SD pull-up
    "R2": (45.2, 19.8, 0),     # ID_SC pull-up
    "R3": (45.2, 17.6, 0),     # WP pull-up
    "TP1": (38.8, 14.4, 0),    # WP test point
    "C4": (36.5, 21.6, 270),   # 100 nF at U3 VCC
    # --- CAN transceiver + termination, beside J2 --------------------
    "U2": (49.0, 13.8, 0),     # CANH/CANL side faces J2
    "C2": (44.2, 12.3, 90),    # 100 nF at U2 VDD (5 V)
    "C5": (41.8, 12.3, 90),    # 10 uF 5 V bulk
    "C3": (50.9, 9.3, 0),      # 100 nF at U2 VIO (3V3)
    "R4": (50.2, 18.0, 0),     # STBY pull-down
    "P1": (54.9, 16.87, 270),  # TERM jumper (ref = pin 1)
    "R7": (54.9, 10.6, 90),    # 120 R termination
    # --- status LEDs on the bottom edge ------------------------------
    "D1": (56.0, 4.2, 0), "R5": (51.6, 4.2, 0),
    "D2": (56.0, 6.8, 0), "R6": (51.6, 6.8, 0),
}


def load(fn):
    return [l.rstrip("\n").split("|") for l in open(fn, encoding="utf-8") if l.count("|") >= 10]


def comps(fn):
    out = {}
    for l in open(fn, encoding="utf-8"):
        m = re.match(r"COMP (\S+) fp=\S+ x=(\S+) y=(\S+) rot=(\S+)", l)
        if m:
            out[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    return out


def rot(x, y, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return x * c - y * s, x * s + y * c


def main():
    pads = load(os.path.join(HERE, "..", "pads_export.txt"))
    old = comps(os.path.join(HERE, "..", "comps_before.txt"))
    newpads = []
    for f in pads:
        ref = f[0]
        if ref in NEW:
            ox, oy, orot = old[ref]
            nx, ny, nrot = NEW[ref]
            lx, ly = rot(float(f[3]) - ox, float(f[4]) - oy, -orot)
            px, py = rot(lx, ly, nrot)
            f = f[:]
            f[3], f[4] = "%.5f" % (nx + px), "%.5f" % (ny + py)
            f[7] = "%g" % ((float(f[7]) - orot + nrot) % 360)
        newpads.append(f)
    # clearance check between pads of different nets (rectangle approx)
    def box(f):
        sx, sy = float(f[5]), float(f[6])
        if round(float(f[7])) % 180 == 90:
            sx, sy = sy, sx
        x, y = float(f[3]), float(f[4])
        return x - sx / 2, y - sy / 2, x + sx / 2, y + sy / 2
    bad = 0
    for i in range(len(newpads)):
        for j in range(i + 1, len(newpads)):
            a, b = newpads[i], newpads[j]
            if a[0] == b[0] or (a[2] and a[2] == b[2]):
                continue
            A, B = box(a), box(b)
            gx = max(A[0] - B[2], B[0] - A[2]); gy = max(A[1] - B[3], B[1] - A[3])
            gap = max(gx, gy) if (gx < 0 or gy < 0) else math.hypot(gx, gy)
            if gap < 0.4:
                bad += 1
                print("TIGHT %.2f mm  %s.%s(%s) - %s.%s(%s)" % (gap, a[0], a[1], a[2], b[0], b[1], b[2]))
    # board edge / mounting-hole land
    for f in newpads:
        x0, y0, x1, y1 = box(f)
        if f[0] == "FREE":
            continue
        if x0 < 0.5 or y0 < 0.5 or x1 > 64.5 or y1 > 29.5:
            print("EDGE", f[0], f[1]); bad += 1
        for hx, hy in ((3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)):
            cx, cy = min(max(hx, x0), x1), min(max(hy, y0), y1)
            if math.hypot(cx - hx, cy - hy) < 3.4:
                print("HOLE LAND", f[0], f[1]); bad += 1
    with open(os.path.join(HERE, "..", "pads_new.txt"), "w") as fo:
        fo.writelines("|".join(f) + "\n" for f in newpads)
    with open(os.path.join(HERE, "placement.txt"), "w") as fo:
        for r, (x, y, a) in NEW.items():
            fo.write("%s %d %d %d\n" % (r, round(x * 1000), round(y * 1000), a))
    print("problems:", bad)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
