# -*- coding: utf-8 -*-
"""Emit the DelphiScript that wires the CAN Sniffer pHAT sheet.

Every pin gets a short stub wire. Power pins terminate in a power port,
signal pins carry a net label on the stub. Connectivity therefore comes from
named nets rather than routed polylines - unambiguous, and ERC-clean.
"""
import os, sys

from paths import LIBRARY_SPEC as SPEC, SCHDOC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_place import PARTS

STUB = 200          # mils of stub wire past the pin's electrical end

# ---------------------------------------------------------------- netlist --
NETS = {
    "+5V":  ["J1.2", "J1.4", "U2.3", "C2.1", "C5.1"],
    "+3V3": ["J1.1", "J1.17", "U1.14", "U2.5", "U3.8", "C1.1", "C3.1", "C4.1",
             "C6.1", "R1.2", "R2.2", "R3.2", "R5.1", "R6.1", "J3.22"],
    "GND":  ["J1.6", "J1.9", "J1.14", "J1.20", "J1.25", "J1.30", "J1.34", "J1.39",
             "U1.7", "U2.2", "U3.4", "U3.1", "U3.2", "U3.3",
             "C1.2", "C2.2", "C3.2", "C4.2", "C5.2", "C6.2", "C7.2", "C8.2",
             "R4.2", "D1.2", "J2.3", "J3.23", "J3.24", "Y1.2", "Y1.4"],
    # SPI0 to the controller
    "SPI_MOSI": ["J1.19", "U1.11"],
    "SPI_MISO": ["J1.21", "U1.12"],
    "SPI_SCLK": ["J1.23", "U1.10"],
    "SPI_CE0":  ["J1.24", "U1.13"],
    "CAN_INT":  ["J1.22", "U1.4"],
    # controller to transceiver
    "TXCAN": ["U1.1", "U2.1"],
    "RXCAN": ["U1.2", "U2.4", "D2.2"],
    # 40 MHz reference
    "XTAL1": ["U1.6", "Y1.1", "C7.1"],
    "XTAL2": ["U1.5", "Y1.3", "C8.1"],
    # HAT ID EEPROM
    "ID_SD": ["J1.27", "U3.5", "R1.1"],
    "ID_SC": ["J1.28", "U3.6", "R2.1"],
    "EE_WP": ["U3.7", "R3.1", "TP1.1"],
    # CAN bus and selectable termination
    "CANH": ["U2.7", "J2.1", "R7.1"],
    "CANL": ["U2.6", "J2.2", "JP1.2"],
    "TERM": ["R7.2", "JP1.1"],
    "STBY": ["U2.8", "R4.1"],
    # indicators
    "LED_PWR": ["R5.2", "D1.1"],
    "LED_ACT": ["R6.2", "D2.1"],
}

# unused Pi GPIO passed straight through to the breakout header
BRK = [("GPIO2", 3, 1), ("GPIO3", 5, 2), ("GPIO4", 7, 3), ("GPIO5", 29, 4),
       ("GPIO6", 31, 5), ("GPIO7", 26, 6), ("GPIO12", 32, 7), ("GPIO13", 33, 8),
       ("GPIO14", 8, 9), ("GPIO15", 10, 10), ("GPIO16", 36, 11), ("GPIO17", 11, 12),
       ("GPIO18", 12, 13), ("GPIO19", 35, 14), ("GPIO20", 38, 15), ("GPIO21", 40, 16),
       ("GPIO22", 15, 17), ("GPIO23", 16, 18), ("GPIO24", 18, 19), ("GPIO26", 37, 20),
       ("GPIO27", 13, 21)]
for net, jpin, bpin in BRK:
    NETS[net] = ["J1.%d" % jpin, "J3.%d" % bpin]

POWER = {"+5V": 2, "+3V3": 2, "GND": 4}      # net -> Altium power port style
# MCP2518FD pins left deliberately unconnected (clock out, spare GPIO/interrupts)
NOERC = ["U1.3", "U1.8", "U1.9"]

# --------------------------------------------------- pin coordinate table --
symbols, cur = {}, None
for raw in open(SPEC, encoding="utf-8"):
    f = raw.rstrip("\n").split("|")
    if f[0] == "SYMBOL":
        cur = f[1]
        symbols[cur] = []
    elif f[0] == "PIN":
        symbols[cur].append(f[1:])

pins = {}
for des, ref, _c, cx, cy in PARTS:
    for p in symbols[ref]:
        num, orient, px, py = p[0], p[3], int(p[4]), int(p[5])
        plen = int(p[7]) if len(p) > 7 and p[7] else 300
        d = 1 if orient == "eRotate0" else -1
        pins["%s.%s" % (des, num)] = (cx + px + d * plen, cy + py, d)

# ------------------------------------------------------------- validation --
used, dupes = set(), []
for net, members in NETS.items():
    for m in members:
        if m not in pins:
            raise SystemExit("net %s references unknown pin %s" % (net, m))
        if m in used:
            dupes.append(m)
        used.add(m)
for m in NOERC:
    if m in used:
        dupes.append(m)
    used.add(m)
if dupes:
    raise SystemExit("pins in more than one net: %s" % dupes)
missing = sorted(set(pins) - used)
if missing:
    raise SystemExit("pins in no net and not marked NoERC: %s" % missing)
print("netlist covers all %d pins (%d nets, %d NoERC)"
      % (len(pins), len(NETS), len(NOERC)))
for net, members in NETS.items():
    if len(members) < 2:
        raise SystemExit("net %s has fewer than 2 pins" % net)

# ------------------------------------------------------------- emit script --
out = []
A = out.append
SQ = chr(39)
q = lambda s: SQ + s.replace(SQ, SQ + SQ) + SQ

A("SandboxLog('wire: start');")
A("S2 := %s;" % q(SCHDOC))
A("Obj3 := SchServer.GetSchDocumentByPath(S2);")
A("if Obj3 = nil then")
A("begin")
A("    ResultText := " + q('{"error":"sheet not open"}') + ";")
A("    SandboxLog('wire: DOC NIL');")
A("    Exit;")
A("end;")
A("I1 := 0; I2 := 0; I3 := 0;")
A("SchServer.ProcessControl.PreProcess(Obj3, '');")

for net in sorted(NETS):
    style = POWER.get(net)
    A("SandboxLog('wire: net %s');" % net)
    for member in NETS[net]:
        hx, hy, d = pins[member]
        # A net label's text always extends to the RIGHT of its anchor, so a
        # left-facing stub must be long enough for the text to sit over the
        # stub instead of running back across the pin.
        if style or d > 0:
            stub = STUB
        else:
            stub = max(STUB, ((len(net) * 60 + 120) // 100 + 1) * 100)
        ex = hx + d * stub
        A("Obj4 := SchServer.SchObjectFactory(eWire, eCreate_GlobalCopy);")
        A("Obj4.InsertVertex := 1;")
        A("Obj4.SetState_Vertex(1, Point(MilsToCoord(%d), MilsToCoord(%d)));" % (hx, hy))
        A("Obj4.InsertVertex := 2;")
        A("Obj4.SetState_Vertex(2, Point(MilsToCoord(%d), MilsToCoord(%d)));" % (ex, hy))
        A("Obj3.RegisterSchObjectInContainer(Obj4);")
        A("I1 := I1 + 1;")
        if style:
            A("Obj4 := SchServer.SchObjectFactory(ePowerObject, eCreate_GlobalCopy);")
            A("Obj4.Location := Point(MilsToCoord(%d), MilsToCoord(%d));" % (ex, hy))
            A("Obj4.Style := %d;" % style)
            A("Obj4.Orientation := %s;" % ("eRotate270" if net == "GND" else "eRotate90"))
            A("Obj4.Text := %s;" % q(net))
            A("Obj4.ShowNetName := True;")
            A("Obj3.RegisterSchObjectInContainer(Obj4);")
            A("I3 := I3 + 1;")
        else:
            A("Obj4 := SchServer.SchObjectFactory(eNetlabel, eCreate_GlobalCopy);")
            A("Obj4.Location := Point(MilsToCoord(%d), MilsToCoord(%d));" % (ex, hy))
            A("Obj4.Text := %s;" % q(net))
            A("Obj4.Orientation := eRotate0;")
            A("Obj3.RegisterSchObjectInContainer(Obj4);")
            A("I2 := I2 + 1;")

A("SandboxLog('wire: placing NoERC markers');")
for member in NOERC:
    hx, hy, d = pins[member]
    A("Obj4 := SchServer.SchObjectFactory(eNoERC, eCreate_GlobalCopy);")
    A("Obj4.Location := Point(MilsToCoord(%d), MilsToCoord(%d));" % (hx, hy))
    A("Obj3.RegisterSchObjectInContainer(Obj4);")

A("SchServer.ProcessControl.PostProcess(Obj3, '');")
A("Obj3.GraphicallyInvalidate;")
A("Obj2 := Client.GetDocumentByPath(S2);")
A("Obj2.DoFileSave('SCH');")
A("SandboxLog('wire: ' + IntToStr(I1) + ' wires, ' + IntToStr(I2) + ' labels, ' + IntToStr(I3) + ' power ports');")
A("ResultText := " + q('{"wires": ') + " + IntToStr(I1) + " + q(', "labels": ')
  + " + IntToStr(I2) + " + q(', "power_ports": ') + " + IntToStr(I3) + " + q("}") + ";")
A("SandboxLog('wire: done');")

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wire.pas")
open(path, "w", encoding="utf-8").write(chr(10).join(out) + chr(10))
print("wrote %s: %d lines" % (path, len(out)))
