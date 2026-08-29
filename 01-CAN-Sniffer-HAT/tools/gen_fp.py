# -*- coding: utf-8 -*-
"""Generate footprint_spec.txt, the text source every land pattern in
CAN_Sniffer_HAT.PcbLib is built from.

Land patterns:
  SOIC-14 / SOIC-8  - Microchip recommended land pattern, drawing C04-2065-SL:
                      pitch 1.27 BSC, contact pad spacing C = 5.40 mm,
                      pad width X = 0.60 mm, pad length Y = 1.55 mm.
                      The MCP2562FD and CAT24C32 datasheets do not print their
                      own land pattern; both are 150 mil SOIC, so the same
                      pattern applies with four pads per side.
  0805              - IPC-7351 hand-solder variant (pads extended outward for
                      hand assembly, per MFR-05).
  2.54 mm headers   - 1.0 mm drill / 1.65 mm pad.
  3.5 mm terminal   - 1.2 mm drill / 2.2 mm pad.
  3225 crystal      - generic 3.2 x 2.5 mm 4-pad land; MUST be re-checked
                      against the crystal actually ordered (see Q-6).
All coordinates in mils. Altium enums: shape 1=round, 2=rect, 9=rounded-rect;
hole type 0 = round.
"""
import os

from paths import FOOTPRINT_SPEC as OUT, PCBLIB as LIB


MM = 39.3701          # mils per mm
lines = ["FPLIB|" + LIB]


def fp(name, desc):
    lines.append("FOOTPRINT|%s|%s" % (name, desc))


def smd(name, x, y, xs, ys, shape=2):
    lines.append("PAD|%s|%.2f|%.2f|0|Top Layer|1|0|0|0|0|%.2f|%.2f|%d"
                 % (name, x, y, xs, ys, shape))


def tht(name, x, y, drill, dia, shape=1):
    lines.append("PAD|%s|%.2f|%.2f|0|Multi-Layer|1|%.2f|0|0|0|%.2f|%.2f|%d"
                 % (name, x, y, drill, dia, dia, shape))


def silk(x1, y1, x2, y2, w=8):
    lines.append("TRACK|%.2f|%.2f|%.2f|%.2f|%d|Top Overlay" % (x1, y1, x2, y2, w))


def box(x1, y1, x2, y2, w=8):
    silk(x1, y1, x2, y1, w); silk(x2, y1, x2, y2, w)
    silk(x2, y2, x1, y2, w); silk(x1, y2, x1, y1, w)


# ---------------------------------------------------------------- SOIC ------
def soic(name, npins, body_len_mm, desc):
    """150 mil SOIC: pins 1..n/2 down the left column, then up the right."""
    fp(name, desc)
    per = npins // 2
    pitch = 1.27 * MM                       # 50 mil
    colx = (5.40 / 2) * MM                  # 106.30 mil
    padx, pady = 1.55 * MM, 0.60 * MM       # 61.02 x 23.62 mil
    top = (per - 1) / 2.0 * pitch
    for i in range(per):                    # left column, pin 1 at top
        smd(str(i + 1), -colx, top - i * pitch, padx, pady)
    for i in range(per):                    # right column, continues from bottom
        smd(str(per + i + 1), colx, -top + i * pitch, padx, pady)
    half_w = (3.90 / 2) * MM - 4            # inside the pad inner edge
    half_l = (body_len_mm / 2) * MM
    box(-half_w, -half_l, half_w, half_l)
    silk(-colx - padx / 2, top + pady, -colx - padx / 2 + 12, top + pady)  # pin-1 tick
    lines.append("ARC|%.2f|%.2f|6|0|360|8|Top Overlay" % (-half_w - 14, top))


soic("SOIC-14_150MIL", 14, 8.65, "14-lead SOIC, 150 mil body, 1.27 mm pitch")
soic("SOIC-8_150MIL", 8, 4.90, "8-lead SOIC, 150 mil body, 1.27 mm pitch")

# ---------------------------------------------------------------- 0805 ------
P0805_X, P0805_Y, P0805_OFF = 1.65 * MM, 1.40 * MM, 1.1875 * MM

fp("0805", "0805 chip resistor/capacitor, hand-solder land")
smd("1", -P0805_OFF, 0, P0805_X, P0805_Y)
smd("2", P0805_OFF, 0, P0805_X, P0805_Y)
silk(-16, 30, 16, 30); silk(-16, -30, 16, -30)

fp("LED_0805", "0805 LED, hand-solder land, pad 2 = cathode")
smd("1", -P0805_OFF, 0, P0805_X, P0805_Y)
smd("2", P0805_OFF, 0, P0805_X, P0805_Y)
silk(-16, 30, 16, 30); silk(-16, -30, 16, -30)
silk(P0805_OFF + P0805_X / 2 + 10, -30, P0805_OFF + P0805_X / 2 + 10, 30)  # cathode bar

# ------------------------------------------------------------- crystal ------
fp("XTAL_3225_4P", "3.2 x 2.5 mm 4-pad crystal - VERIFY against ordered part")
XPX, XPY = 1.20 * MM, 1.10 * MM
XOX, XOY = 1.10 * MM, 0.85 * MM
for name, sx, sy in [("1", -1, -1), ("2", 1, -1), ("3", 1, 1), ("4", -1, 1)]:
    smd(name, sx * XOX, sy * XOY, XPX, XPY)
box(-(3.2 / 2) * MM, -(2.5 / 2) * MM, (3.2 / 2) * MM, (2.5 / 2) * MM)

# -------------------------------------------------------------- headers -----
HDR_DRILL, HDR_PAD = 1.0 * MM, 1.65 * MM


def header(name, cols, desc):
    fp(name, desc)
    span = (cols - 1) * 100.0
    for n in range(1, cols * 2 + 1):
        col = (n - 1) // 2
        x = -span / 2 + col * 100.0
        y = 50.0 if n % 2 else -50.0
        tht(str(n), x, y, HDR_DRILL, HDR_PAD, 2 if n == 1 else 1)
    box(-span / 2 - 50, -100, span / 2 + 50, 100)


header("HDR_2X20_254", 20, "2x20 pin header, 2.54 mm pitch, through-hole")
header("HDR_2X12_254", 12, "2x12 pin header, 2.54 mm pitch, through-hole")

fp("HDR_1X2_254", "2-pin header for shunt, 2.54 mm pitch, through-hole")
tht("1", -50, 0, HDR_DRILL, HDR_PAD, 2)
tht("2", 50, 0, HDR_DRILL, HDR_PAD, 1)
box(-100, -50, 100, 50)

# ------------------------------------------------------- screw terminal -----
fp("TERM_3P_350", "3-position pluggable screw terminal, 3.5 mm pitch")
TP = 3.5 * MM
for i, n in enumerate(("1", "2", "3")):
    tht(n, (i - 1) * TP, 0, 1.2 * MM, 2.2 * MM, 2 if n == "1" else 1)
box(-TP - 70, -140, TP + 70, 140)

# ----------------------------------------------------------- test point -----
fp("TESTPOINT_60", "Test point, 60 mil round pad")
smd("1", 0, 0, 60, 60, 1)

open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("wrote", OUT)
print("footprints:", sum(1 for l in lines if l.startswith("FOOTPRINT|")))
print("pads:", sum(1 for l in lines if l.startswith("PAD|")))
