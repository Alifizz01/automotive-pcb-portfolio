# -*- coding: utf-8 -*-
"""Generate library_spec.txt, the text source every symbol in
CAN_Sniffer_HAT.SchLib is built from."""
from paths import SCHLIB as LIB, LIBRARY_SPEC as OUT

L, R = "eRotate180", "eRotate0"     # left-side pin extends left, right-side extends right
def ob(t):
    """Altium overbar: a backslash after every character."""
    return "".join(c + chr(92) for c in t)

lines = ["LIBRARY|" + LIB]

def sym(name, desc, parts=1):
    lines.append("SYMBOL|%s|%s|%d" % (name, desc, parts))

def pin(num, pname, ptype, orient, x, y, length=300, show_name=1, show_des=1):
    lines.append("PIN|%s|%s|%s|%s|%d|%d|1|%d|%d|%d"
                 % (num, pname, ptype, orient, x, y, length, show_name, show_des))

def gr(entry):
    lines.append("GRAPHIC|" + entry)

PWR, IN, OUT_, IO, PAS = ("eElectricPower", "eElectricInput", "eElectricOutput",
                          "eElectricIO", "eElectricPassive")

# ---- U1 MCP2518FD, SOIC-14 (datasheet DS20006027A Table 1-1) ----
sym("MCP2518FD", "CAN FD controller, SPI, 8 Mbit/s, SOIC-14")
W = 900
for num, nm, ty, y in [("13", ob("CS"), IN, 0), ("10", "SCK", IN, -100),
                       ("11", "SDI", IN, -200), ("12", "SDO", OUT_, -300),
                       ("4", ob("INT"), OUT_, -500),
                       ("14", "VDD", PWR, -700), ("7", "VSS", PWR, -800)]:
    pin(num, nm, ty, L, 0, y)
for num, nm, ty, y in [("1", "TXCAN", OUT_, 0), ("2", "RXCAN", IN, -100),
                       ("6", "OSC1", IN, -300), ("5", "OSC2", OUT_, -400),
                       ("3", "CLKO/SOF", OUT_, -500),
                       ("8", "INT1/GPIO1", IO, -700), ("9", "INT0/GPIO0/XSTBY", IO, -800)]:
    pin(num, nm, ty, R, W, y)

# ---- U2 MCP2562FD, SOIC-8 (datasheet DS20005284A Table 1-2) ----
sym("MCP2562FD", "CAN FD transceiver with VIO level shift, SOIC-8")
W = 700
for num, nm, ty, y in [("1", "TXD", IN, 0), ("4", "RXD", OUT_, -100),
                       ("8", "STBY", IN, -300),
                       ("3", "VDD", PWR, -500), ("5", "VIO", PWR, -600), ("2", "VSS", PWR, -700)]:
    pin(num, nm, ty, L, 0, y)
for num, nm, ty, y in [("7", "CANH", IO, 0), ("6", "CANL", IO, -100)]:
    pin(num, nm, ty, R, W, y)

# ---- U3 CAT24C32, SOIC-8 (datasheet CAT24C32/D pin configurations) ----
sym("CAT24C32", "32 kbit I2C EEPROM, 16-bit addressing, HAT ID EEPROM, SOIC-8")
W = 600
for num, nm, ty, y in [("5", "SDA", IO, 0), ("6", "SCL", IN, -100), ("7", "WP", IN, -300),
                       ("1", "A0", IN, -500), ("2", "A1", IN, -600), ("3", "A2", IN, -700)]:
    pin(num, nm, ty, L, 0, y)
for num, nm, ty, y in [("8", "VCC", PWR, 0), ("4", "VSS", PWR, -100)]:
    pin(num, nm, ty, R, W, y)

# ---- passives ----
sym("RES", "Resistor, 0805")
pin("1", "1", PAS, L, 0, 0, 100, 0, 0)
pin("2", "2", PAS, R, 300, 0, 100, 0, 0)
gr("rectangle|1|1|0|0|-50|300|50")

sym("CAP", "Capacitor, non-polarised, 0805")
pin("1", "1", PAS, L, 130, 0, 130, 0, 0)
pin("2", "2", PAS, R, 170, 0, 130, 0, 0)
gr("line|1|2|130|-80|130|80")
gr("line|1|2|170|-80|170|80")

sym("LED", "LED, 0805")
pin("1", "A", PAS, L, 0, 0, 100, 0, 0)
pin("2", "K", PAS, R, 300, 0, 100, 0, 0)
gr("polygon|1|1|1|100|-80|100|80|220|0")
gr("line|1|2|220|-80|220|80")
gr("polyline|1|1|130|100|180|150")
gr("polyline|1|1|150|90|200|140")

sym("CRYSTAL", "40 MHz crystal, 3.2 x 2.5 mm 4-pad, case pads grounded")
pin("1", "XI", PAS, L, 0, 0)
pin("2", "GND", PAS, L, 0, -100)
pin("3", "XO", PAS, R, 400, 0)
pin("4", "GND", PAS, R, 400, -100)

sym("JUMPER2", "2-pin header with shunt, 2.54 mm")
pin("1", "1", PAS, L, 0, 0, 100, 0, 1)
pin("2", "2", PAS, R, 300, 0, 100, 0, 1)
gr("rectangle|1|1|0|0|-60|300|60")

sym("TESTPOINT", "Test point / probe pad")
pin("1", "TP", PAS, L, 0, 0, 100, 0, 0)
gr("ellipse|1|1|1|50|0|50|50")

# ---- connectors ----
PI40 = ["3V3","5V","GPIO2","5V","GPIO3","GND","GPIO4","GPIO14","GND","GPIO15",
        "GPIO17","GPIO18","GPIO27","GND","GPIO22","GPIO23","3V3","GPIO24","GPIO10","GND",
        "GPIO9","GPIO25","GPIO11","GPIO8","GND","GPIO7","ID_SD","ID_SC","GPIO5","GND",
        "GPIO6","GPIO12","GPIO13","GND","GPIO19","GPIO16","GPIO26","GPIO20","GND","GPIO21"]
sym("HDR_2X20_PI", "Raspberry Pi 40-pin GPIO header, 2x20, 2.54 mm")
for i, nm in enumerate(PI40):
    num = i + 1
    row = -(i // 2) * 100
    pin(str(num), nm, PAS, L if num % 2 else R, 0 if num % 2 else 900, row)

BRK = ["GPIO2","GPIO3","GPIO4","GPIO5","GPIO6","GPIO7","GPIO12","GPIO13",
       "GPIO14","GPIO15","GPIO16","GPIO17","GPIO18","GPIO19","GPIO20","GPIO21",
       "GPIO22","GPIO23","GPIO24","GPIO26","GPIO27","3V3","GND","GND"]
sym("HDR_2X12_BRK", "GPIO breakout header, 2x12, 2.54 mm - all 21 unused Pi GPIO")
for i, nm in enumerate(BRK):
    num = i + 1
    row = -(i // 2) * 100
    pin(str(num), nm, PAS, L if num % 2 else R, 0 if num % 2 else 900, row)

sym("SCREWTERM_3", "Pluggable screw terminal, 3 position, 3.5 mm pitch")
for i, nm in enumerate(["CAN_H", "CAN_L", "GND"]):
    pin(str(i + 1), nm, PAS, L, 0, -i * 100)
# Explicit body: all three pins sit on one side, so the auto-sized body would be
# a zero-width rectangle - which silently aborts pin creation for the symbol.
gr("rectangle|1|1|0|0|-300|400|100")
for i in range(3):
    gr("ellipse|1|1|0|200|%d|60|60" % (-i * 100))

open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("wrote", OUT)
print("symbols:", sum(1 for x in lines if x.startswith("SYMBOL|")))
print("pins:", sum(1 for x in lines if x.startswith("PIN|")))
