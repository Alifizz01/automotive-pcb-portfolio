# -*- coding: utf-8 -*-
"""Every land pattern on the CAN-FD Test Runner, in millimetres, top view, +y up.

Each footprint traces to the manufacturer's recommended land pattern. Where a KiCad
library footprint exists for the same part it was used as an independent cross-check
of the reading (noted as 'x-check KiCad').

Pad tuple: (name, x, y, w, h, shape, kind, drill, slot)
  shape : 'R' rect, 'O' round/oval, 'RR' rounded rect
  kind  : 'SMD' top copper | 'TH' plated through | 'NPTH' unplated hole
  drill : hole diameter (TH/NPTH), slot: (w, h) for a slotted hole or None
Silk: list of (x1, y1, x2, y2) lines on the top overlay.
"""

FP = {}


def fp(name, desc, pads, silk=(), height=1.0, body=None):
    FP[name] = {"desc": desc, "pads": list(pads), "silk": list(silk), "height": height,
                "body": body}


def box(x1, y1, x2, y2):
    return [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]


def smd(n, x, y, w, h, shape="R"):
    return (str(n), x, y, w, h, shape, "SMD", 0, None)


def th(n, x, y, dia, drill, shape="O", slot=None):
    return (str(n), x, y, dia[0] if isinstance(dia, tuple) else dia,
            dia[1] if isinstance(dia, tuple) else dia, shape, "TH", drill, slot)


def npth(x, y, d):
    return ("", x, y, d, d, "O", "NPTH", d, None)


# ------------------------------------------------------------------ chip passives
# IPC-7351 nominal density; 0603 is the smallest passive allowed by MFR-05.
def chip(name, desc, pitch, pw, ph, bw, bh, h=0.8, polar=False):
    s = [(-bw / 2 + 0.1, bh / 2 + 0.15, bw / 2 - 0.1, bh / 2 + 0.15),
         (-bw / 2 + 0.1, -bh / 2 - 0.15, bw / 2 - 0.1, -bh / 2 - 0.15)]
    if polar:   # cathode bar next to pad 2
        s.append((pitch / 2 + pw / 2 + 0.2, -ph / 2, pitch / 2 + pw / 2 + 0.2, ph / 2))
    fp(name, desc, [smd(1, -pitch / 2, 0, pw, ph), smd(2, pitch / 2, 0, pw, ph)], s, h,
       (bw, bh))


chip("R0603", "0603 resistor, IPC-7351 nominal", 1.6, 0.9, 0.95, 1.6, 0.8, 0.5)
chip("C0603", "0603 capacitor, IPC-7351 nominal", 1.6, 0.9, 0.95, 1.6, 0.8, 0.9)
chip("R0805", "0805 resistor, IPC-7351 nominal", 1.9, 1.0, 1.4, 2.0, 1.25, 0.6)
chip("C0805", "0805 capacitor, IPC-7351 nominal", 1.9, 1.0, 1.4, 2.0, 1.25, 1.25)
chip("C1210", "1210 capacitor, IPC-7351 nominal", 2.95, 1.2, 2.7, 3.2, 2.5, 2.5)
chip("LED0603", "0603 LED, pad 2 = cathode", 1.6, 0.9, 0.95, 1.6, 0.8, 0.8, polar=True)

# ------------------------------------------------------------------ inductors (Wurth drawings)
chip("L_WE-LQS-6045", "Wurth WE-LQS 6045, 74404064330 land pattern", 4.6, 1.8, 5.7, 6.0, 6.0, 4.5)
chip("L_WE-LQS-2520", "Wurth WE-LQS 2520, 74404024022 land pattern", 1.9, 1.1, 2.0, 2.5, 2.0, 1.2)
chip("L_WE-MAPI-2016", "Wurth WE-MAPI 2016, 744383430047 land pattern", 1.45, 0.85, 1.9, 2.0, 1.6, 1.0)

# ------------------------------------------------------------------ diodes (Nexperia / Bourns reflow)
chip("SOD123W", "Nexperia CFP3/SOD123W reflow footprint, pad 1 = cathode", 2.9, 1.2, 1.2, 2.6, 1.7, 1.1, polar=False)
chip("SOD128", "Nexperia CFP5/SOD128 reflow footprint, pad 1 = cathode", 4.4, 1.4, 2.1, 3.8, 2.5, 1.1)
chip("SMB", "DO-214AA (SMB), Bourns recommended footprint, pad 1 = cathode", 4.3, 2.3, 2.7, 4.3, 3.6, 2.4)
for n in ("SOD123W", "SOD128", "SMB"):      # cathode bar on the pad-1 side
    p = FP[n]["pads"][0]
    FP[n]["silk"].append((p[1] - p[3] / 2 - 0.25, -p[4] / 2, p[1] - p[3] / 2 - 0.25, p[4] / 2))

# ------------------------------------------------------------------ SOT-23 / SC-70 (TI DBZ0003A, DCK0003A)
fp("SOT-23-3", "SOT-23-3, TI DBZ0003A land pattern (also Nexperia TO-236AB parts)",
   [smd(1, -1.05, 0.95, 1.3, 0.6), smd(2, -1.05, -0.95, 1.3, 0.6), smd(3, 1.05, 0, 1.3, 0.6)],
   [(-0.3, 1.5, 0.3, 1.5), (-0.3, -1.5, 0.3, -1.5), (0.7, 1.5, 0.7, 0.6), (0.7, -1.5, 0.7, -0.6)],
   1.1, (1.3, 2.9))
fp("SC-70-3", "SC-70-3, TI DCK0003A land pattern",
   [smd(1, -1.1, 0.65, 0.95, 0.4), smd(2, -1.1, -0.65, 0.95, 0.4), smd(3, 1.1, 0, 0.95, 0.4)],
   [(-0.3, 1.15, 0.3, 1.15), (-0.3, -1.15, 0.3, -1.15)], 1.1, (1.25, 2.0))


# ------------------------------------------------------------------ SOIC-8 150 mil (Microchip C04-2065)
def soic8(name, desc, ep=None, colx=2.7, pw=1.55, ph=0.6):
    pads = [smd(i + 1, -colx, 1.905 - i * 1.27, pw, ph) for i in range(4)]
    pads += [smd(5 + i, colx, -1.905 + i * 1.27, pw, ph) for i in range(4)]
    if ep:
        pads.append(smd(9, 0, 0, ep[0], ep[1]))
    s = box(-1.8, -2.55, 1.8, 2.55) + [(-3.6, 2.55, -1.9, 2.55)]   # pin-1 extension line
    fp(name, desc, pads, s, 1.75, (3.9, 4.9))


soic8("SOIC-8_150MIL", "8-lead SOIC 150 mil, Microchip C04-2065 land pattern")
soic8("SOIC-8_DDA_PowerPAD", "TI DDA0008B PowerPAD SOIC-8, TI example board layout", ep=(2.71, 3.4))


# ------------------------------------------------------------------ TI leadless parts
def son(name, desc, left, right, ep=None, body=(2, 2), pitch=0.5, h=0.8, colx=None, pw=0.5, ph=0.25,
        right_pw=None, right_x=None):
    n = len(left)
    top = (n - 1) / 2 * pitch
    pads = [smd(num, -colx, top - i * pitch, pw, ph) for i, num in enumerate(left)]
    rx = right_x if right_x is not None else colx
    rpw = right_pw if right_pw is not None else pw
    pads += [smd(num, rx, -top + i * pitch, rpw, ph) for i, num in enumerate(right)]
    if ep:
        pads.append(smd(ep[0], ep[1], ep[2], ep[3], ep[4]))
    bw, bh = body
    s = [(-bw / 2, bh / 2 + 0.15, bw / 2, bh / 2 + 0.15), (-bw / 2, -bh / 2 - 0.15, bw / 2, -bh / 2 - 0.15),
         (-bw / 2 - 0.35, top + 0.35, -bw / 2 - 0.15, top + 0.35)]
    fp(name, desc, pads, s, h, body)


son("WSON-8_DSG", "TI DSG0008A WSON-8 2x2, TI example board layout", [1, 2, 3, 4], [5, 6, 7, 8],
    ep=("9", 0, 0, 0.9, 1.6), colx=0.95, pw=0.5, ph=0.25)
son("WSON-6_DRV", "TI DRV0006A WSON-6 2x2, TI example board layout", [1, 2, 3], [4, 5, 6],
    ep=("7", 0, 0, 1.0, 1.6), pitch=0.65, colx=0.975, pw=0.45, ph=0.3)
son("WSON-6_DSE", "TI DSE0006A WSON-6 1.5x1.5, TI example board layout", [1, 2, 3], [4, 5, 6],
    body=(1.5, 1.5), colx=0.55, pw=0.8, ph=0.25, right_pw=0.7, right_x=0.6)
# TPS63802 DLA0010A: pins 1-5 left (0.6 x 0.25 at x -0.9), 6-10 right (0.9 x 0.25 at x +0.75),
# pin 8 is the long 1.3 mm GND pad centred at x +0.55.
FP_DLA = [smd(i + 1, -0.9, 1.0 - i * 0.5, 0.6, 0.25) for i in range(5)]
FP_DLA += [smd(6, 0.75, -1.0, 0.9, 0.25), smd(7, 0.75, -0.5, 0.9, 0.25), smd(8, 0.55, 0, 1.3, 0.25),
           smd(9, 0.75, 0.5, 0.9, 0.25), smd(10, 0.75, 1.0, 0.9, 0.25)]
fp("VSON-10_DLA", "TI DLA0010A VSON-HR 2x3, TI example board layout", FP_DLA,
   [(-1.0, 1.65, 1.0, 1.65), (-1.0, -1.65, 1.0, -1.65), (-1.45, 1.3, -1.45, 1.0)], 1.0, (2.0, 3.0))

# ------------------------------------------------------------------ Microchip VQFN-16 3x3 (C04-2508)
q = []
for i in range(4):
    q.append(smd(1 + i, -1.45, 0.75 - i * 0.5, 0.8, 0.3))      # left, top to bottom
    q.append(smd(5 + i, -0.75 + i * 0.5, -1.45, 0.3, 0.8))     # bottom, left to right
    q.append(smd(9 + i, 1.45, -0.75 + i * 0.5, 0.8, 0.3))      # right, bottom to top
    q.append(smd(13 + i, 0.75 - i * 0.5, 1.45, 0.3, 0.8))      # top, right to left
q.append(smd(17, 0, 0, 1.1, 1.1))
fp("VQFN-16_3x3_4MX", "Microchip VQFN-16 3x3 (4MX), drawing C04-2508", q,
   [(-1.5, 1.95, -1.95, 1.95), (1.5, 1.95, 1.95, 1.95), (1.95, 1.95, 1.95, 1.5),
    (-1.5, -1.95, -1.95, -1.95), (-1.95, -1.95, -1.95, -1.5), (1.5, -1.95, 1.95, -1.95),
    (1.95, -1.95, 1.95, -1.5), (-2.2, 1.2, -2.2, 0.8)], 0.9, (3, 3))

# ------------------------------------------------------------------ LQFP-100 14x14 (ST DS14258 Fig. 84)
lq = []
for i in range(25):
    lq.append(smd(1 + i, -7.75, 6.0 - i * 0.5, 1.2, 0.3))      # left, pin 1 top
    lq.append(smd(26 + i, -6.0 + i * 0.5, -7.75, 0.3, 1.2))    # bottom
    lq.append(smd(51 + i, 7.75, -6.0 + i * 0.5, 1.2, 0.3))     # right
    lq.append(smd(76 + i, 6.0 - i * 0.5, 7.75, 0.3, 1.2))      # top
fp("LQFP-100_14x14", "LQFP-100 14 x 14 mm, 0.5 mm pitch, ST DS14258 footprint example", lq,
   box(-7.1, -7.1, 7.1, 7.1) + [(-7.1, 6.6, -6.6, 7.1), (-8.6, 6.7, -8.6, 5.3)], 1.6, (14, 14))

# ------------------------------------------------------------------ crystals / RTC
fp("XTAL_3225_4P", "3.2 x 2.5 mm 4-pad crystal (Abracon ABM8), x-check KiCad Crystal_SMD_3225-4Pin",
   [smd(1, -1.1, -0.85, 1.4, 1.2), smd(2, 1.1, -0.85, 1.4, 1.2), smd(3, 1.1, 0.85, 1.4, 1.2),
    smd(4, -1.1, 0.85, 1.4, 1.2)],
   [(-2.0, -1.6, -2.0, 1.6), (-0.2, 1.6, 0.2, 1.6), (-0.2, -1.6, 0.2, -1.6)], 0.8, (3.2, 2.5))
fp("RV-3028-C7", "Micro Crystal C7 package 3.2 x 1.5, datasheet recommended pad, x-check KiCad",
   [smd(1, -0.65, 1.35, 0.95, 0.65), smd(2, -0.65, 0.45, 0.95, 0.65), smd(3, -0.65, -0.45, 0.95, 0.65),
    smd(4, -0.65, -1.35, 0.95, 0.65), smd(5, 0.65, -1.35, 0.95, 0.65), smd(6, 0.65, -0.45, 0.95, 0.65),
    smd(7, 0.65, 0.45, 0.95, 0.65), smd(8, 0.65, 1.35, 0.95, 0.65)],
   [(-1.4, 1.9, -1.4, 1.2)], 0.8, (1.5, 3.2))

# ------------------------------------------------------------------ connectors
# GCT USB4105 (drawing USB4105 rev B4), x-check KiCad: identical. KiCad y is down -> negate.
usb = [smd("A1", -3.2, 3.68, 0.6, 1.15), smd("A4", -2.4, 3.68, 0.6, 1.15),
       smd("B8", -1.75, 3.68, 0.3, 1.15), smd("A5", -1.25, 3.68, 0.3, 1.15),
       smd("B7", -0.75, 3.68, 0.3, 1.15), smd("A6", -0.25, 3.68, 0.3, 1.15),
       smd("A7", 0.25, 3.68, 0.3, 1.15), smd("B6", 0.75, 3.68, 0.3, 1.15),
       smd("A8", 1.25, 3.68, 0.3, 1.15), smd("B5", 1.75, 3.68, 0.3, 1.15),
       smd("A9", 2.4, 3.68, 0.6, 1.15), smd("A12", 3.2, 3.68, 0.6, 1.15),
       npth(-2.89, 2.605, 0.65), npth(2.89, 2.605, 0.65),
       th("SH", -4.32, 3.105, (1.0, 2.1), 0.6, "O", (0.6, 1.7)),
       th("SH", 4.32, 3.105, (1.0, 2.1), 0.6, "O", (0.6, 1.7)),
       th("SH", -4.32, -1.075, (1.0, 1.8), 0.6, "O", (0.6, 1.4)),
       th("SH", 4.32, -1.075, (1.0, 1.8), 0.6, "O", (0.6, 1.4))]
fp("USB-C_GCT_USB4105", "GCT USB4105 USB-C 2.0 receptacle, top mount; board edge at y = -3.475",
   usb, [(-4.47, -3.475, 4.47, -3.475), (-4.47, -3.475, -4.47, -2.2), (4.47, -3.475, 4.47, -2.2)],
   3.3, (8.94, 7.35))

# Hirose DM3AT-SF-PEJM5 push-push microSD, x-check KiCad (same drawing). y negated.
sd = [smd(str(i + 1), 2.775 - i * 1.1, 7.725, 0.7, 1.2) for i in range(8)]
sd += [smd("9", -5.875, 7.725, 0.7, 1.2), smd("10", -6.825, -2.775, 1.0, 0.8),
       smd("SH", -6.825, 3.425, 1.0, 1.2), smd("SH", -6.825, -6.925, 1.0, 2.8),
       smd("SH", 4.325, 7.725, 1.0, 1.2), smd("SH", 6.675, -7.375, 1.3, 1.9)]
fp("MICROSD_HIROSE_DM3AT", "Hirose DM3AT-SF-PEJM5 microSD push-push with card detect", sd,
   box(-7.3, -8.5, 7.3, 6.9), 1.9, (14.6, 15.1))

# Wurth WR-DSUB 618009231221, male angled, recommended hole pattern (drawing p1).
# Row with pins 1-5 is 2.84 mm further from the board edge than pins 6-9.
ds = [th(str(i + 1), -5.54 + i * 2.77, 1.42, 1.6, 1.04) for i in range(5)]
ds += [th(str(6 + i), -4.155 + i * 2.77, -1.42, 1.6, 1.04) for i in range(4)]
ds += [th("MH", -12.5, 0, 4.4, 3.2), th("MH", 12.5, 0, 4.4, 3.2)]
fp("DSUB-9_M_WR-DSUB_618009231221", "Wurth WR-DSUB male angled 9 pin; board edge 8.0 mm below pin row 6-9",
   ds, [(-15.4, -9.42, 15.4, -9.42), (-15.4, -9.42, -15.4, 3.0), (15.4, -9.42, 15.4, 3.0),
        (-15.4, 3.0, 15.4, 3.0)], 12.55, None)       # courtyard from the silk outline, not centred

# Wurth WR-FPC 687110149022, 10 pin 0.5 mm, recommended land pattern (zoomed reading).
fpc = [smd(str(i + 1), -2.25 + i * 0.5, 0, 0.3, 1.3) for i in range(10)]
fpc += [smd("MP", -4.05, -2.75, 2.0, 1.8), smd("MP", 4.05, -2.75, 2.0, 1.8)]
fp("FPC_10P_0.5_WR-FPC_687110149022", "Wurth WR-FPC 0.5 mm, 10 pins, horizontal", fpc,
   [(-4.55, -4.2, 4.55, -4.2), (-2.9, 0.9, -2.9, 0.5)], 2.2, (9.1, 5.6))

# JST PH S3B-PH-SM4-TB, x-check KiCad (JST drawing ePH). y negated.
fp("JST_PH_S3B-PH-SM4-TB", "JST PH 2.0 mm, 3 pin, SMD side entry",
   [smd(1, -2, 2.85, 1.0, 3.5, "RR"), smd(2, 0, 2.85, 1.0, 3.5, "RR"), smd(3, 2, 2.85, 1.0, 3.5, "RR"),
    smd("MP", -4.35, -2.9, 1.5, 3.4, "RR"), smd("MP", 4.35, -2.9, 1.5, 3.4, "RR")],
   box(-3.95, -4.8, 3.95, 1.0) + [(-2.9, 4.9, -2.9, 4.2)], 6.0, (7.9, 5.8))

# Tag-Connect TC2050-IDC-NL: copper pads only, no paste, 3 NPTH alignment holes.
tc = [smd(str(1 + i), -2.54 + i * 1.27, -0.635, 0.787, 0.787, "O") for i in range(5)]
tc += [smd(str(6 + i), 2.54 - i * 1.27, 0.635, 0.787, 0.787, "O") for i in range(5)]
tc += [npth(-3.81, 0, 0.99), npth(3.81, 1.016, 0.99), npth(3.81, -1.016, 0.99)]
fp("TAG-CONNECT_TC2050-IDC-NL", "Tag-Connect TC2050-IDC-NL, Cortex 10-pin SWD, no legs", tc,
   [(-3.3, -1.35, -3.0, -1.35)], 0.0, (9.0, 3.0))

# Keystone 1042 18650 SMT holder, x-check KiCad. Pads 1 = +, 2 = -.
fp("BATT_KEYSTONE_1042_18650", "Keystone 1042 SMT 18650 holder", [
    smd(1, -39.69, 0, 7.5, 6.5), smd(2, 39.69, 0, 7.5, 6.5),
    npth(-36.13, 8, 2.39), npth(-27.62, -8, 3.45), npth(27.62, 8, 3.45)],
   box(-38.5, -10.5, 38.5, 10.5) + [(-44.5, 4.0, -44.5, 1.0), (-46.0, 2.5, -43.0, 2.5)], 20.0, (77, 21))

# Keystone 3000 SMT 12 mm coin cell retainer (CR1216/CR1220). Pad 1 = + (two tabs), 2 = - on PCB.
fp("BATT_KEYSTONE_3000_12MM", "Keystone 3000 SMT CR1220 retainer", [
    smd(1, -7.9, 0, 3.5, 3.3), smd(1, 7.9, 0, 3.5, 3.3), smd(2, 0, 0, 10.2, 10.2, "O")],
   [(-6.6, 6.6, 6.6, 6.6), (-6.6, -6.6, 6.6, -6.6)], 3.2, (13.2, 13.2))

# Wurth WS-TASV 430182050816 6 x 6 tact switch, land pattern: pads 1&3 top, 2&4 bottom.
fp("SW_WS-TASV_6x6", "Wurth WS-TASV 6 x 6 mm tact switch, SMD", [
    smd(1, -3.975, 2.25, 1.55, 1.3), smd(3, 3.975, 2.25, 1.55, 1.3),
    smd(2, -3.975, -2.25, 1.55, 1.3), smd(4, 3.975, -2.25, 1.55, 1.3)],
   box(-3.0, -3.0, 3.0, 3.0), 5.0, (6, 6))

if __name__ == "__main__":
    for k, v in FP.items():
        print("%-34s %3d pads  %s" % (k, len(v["pads"]), v["desc"][:60]))
