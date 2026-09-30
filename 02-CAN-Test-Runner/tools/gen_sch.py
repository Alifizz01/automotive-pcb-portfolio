# -*- coding: utf-8 -*-
"""Emit altium/build_sch.pas: draws CAN_Test_Runner.SchDoc from design.py.

Components are built directly on the sheet (Replicate() out of a SchLib proved unreliable
in project 01). Every pin gets a short wire stub ending in a net label or power port, so the
netlist is exactly design.NETS. Parts are laid out in functional blocks on an A1 sheet.
"""
import os
import design
from design import SYM, PARTS, NETS, NOERC
from footprints import FP

HERE = os.path.dirname(os.path.abspath(__file__))
design.check()
SQ = chr(39)
q = lambda s: SQ + s.replace(SQ, SQ + SQ) + SQ
ELEC = {"Passive": "eElectricPassive", "Input": "eElectricInput", "Output": "eElectricOutput",
        "IO": "eElectricIO", "Power": "eElectricPower"}
POWER = {"GND": (4, "eRotate270"), "3V3": (2, "eRotate90"), "5V_AUX": (2, "eRotate90")}
TWO_PIN = {"RES", "CAP", "IND", "LED", "DIODE_SCHOTTKY", "TVS_UNI", "BATT_18650", "BATT_COIN"}

# pin -> net
PIN_NET = {}
for n, members in NETS.items():
    for m in members:
        PIN_NET[m] = n

# ---------------------------------------------------------------- blocks
BLOCK = dict(design.BLOCK)
BLOCK.update({r: "CAN" for r in ("J1", "J2", "U2", "U3", "U11", "U12")})
BLOCK.update({r: "USB_SD" for r in ("J3", "J4", "U13", "Q5")})
BLOCK.update({r: "UI" for r in ("J5", "BT2", "SW1", "SW2", "U10", "D7")})
BLOCK.update({r: "MCU" for r in ("U1", "Y1", "J7")})
BLOCK.update({r: "POWER_IN" for r in ("U4", "L1", "D1", "D2", "D3")})
BLOCK.update({r: "CHARGER" for r in ("U5", "D4", "D5", "D6", "Q1", "Q4", "J6")})
BLOCK.update({r: "CELL" for r in ("BT1", "U6", "Q2", "Q3", "U7")})
BLOCK.update({r: "RAILS" for r in ("U8", "U9", "L2", "L3")})
REGION = {   # x0, y0, x1, y1 in mils, inside the A1 border and clear of the title block
    "POWER_IN": (400, 15600, 10000, 21300, "Vehicle input, protection, 6-32 V to 5 V buck"),
    "CHARGER": (10200, 15600, 16700, 21300, "Charge input OR-ing, LiFePO4 charger, power path"),
    "CELL": (16900, 15600, 23700, 21300, "Cell, protection, charge counter"),
    "RAILS": (23900, 15600, 30800, 21300, "3V3 buck-boost, 5 V boost"),
    "MCU": (400, 1400, 10000, 15400, "STM32H563 microcontroller"),
    "CAN": (10200, 8000, 18400, 15400, "CAN FD channels 1 and 2"),
    "USB_SD": (18600, 8000, 30800, 15400, "USB-C device and microSD"),
    "UI": (10200, 2400, 30800, 7800, "Display, RTC, buttons, status"),
}


def text_w(s):
    return len(s) * 60 + 60


def geom(sname):
    """symbol geometry: list of pins (num, name, type, side, x, y, len) and body width/height."""
    desc, left, right = SYM[sname]
    pins = []
    if sname in TWO_PIN:
        a, b = left[0], right[0]
        pins = [(a[0], a[1], a[2], "L", 0, 0, 100), (b[0], b[1], b[2], "R", 300, 0, 100)]
        return pins, 300, 0
    wl = max([len(p[1]) for p in left] + [0]) * 55
    wr = max([len(p[1]) for p in right] + [0]) * 55
    w = max(500, ((wl + wr + 250) // 100 + 1) * 100)
    for i, p in enumerate(left):
        pins.append((p[0], p[1], p[2], "L", 0, -i * 100, 200))
    for i, p in enumerate(right):
        pins.append((p[0], p[1], p[2], "R", w, -i * 100, 200))
    h = (max(len(left), len(right)) - 1) * 100
    return pins, w, h


def margins(ref, pins):
    """space needed left / right of the symbol for stubs and labels"""
    lm, rm = 300, 300
    for num, name, typ, side, x, y, plen in pins:
        n = PIN_NET.get(ref + "." + num)
        lab = 0 if (n is None or n in POWER) else text_w(n)
        need = plen + 200 + max(lab, 200)
        if side == "L":
            lm = max(lm, need)
        else:
            rm = max(rm, need)
    return lm, rm


out = []
A = out.append
A("""var
    Sch     : ISch_Document;
    CurComp : ISch_Component;

procedure NewComp(Des, LibRef, Desc, Comment, FPName, MPN : String);
begin
    CurComp := SchServer.SchObjectFactory(eSchComponent, eCreate_Default);
    CurComp.CurrentPartID := 1;
    CurComp.DisplayMode := 0;
    CurComp.PartCount := 1;
    CurComp.LibReference := LibRef;
    CurComp.DesignItemId := LibRef;
    CurComp.ComponentDescription := Desc;
    CurComp.Designator.Text := Des;
    CurComp.Comment.Text := Comment;
end;

procedure CPin(Num, PName : String; Elec, Orient, X, Y, Len : Integer; ShowName : Boolean);
var Pin : ISch_Pin;
begin
    Pin := SchServer.SchObjectFactory(ePin, eCreate_Default);
    Pin.Designator := Num;
    Pin.Name := PName;
    Pin.Electrical := Elec;
    Pin.Orientation := Orient;
    Pin.Location := Point(MilsToCoord(X), MilsToCoord(Y));
    Pin.PinLength := MilsToCoord(Len);
    Pin.ShowName := ShowName;
    Pin.ShowDesignator := True;
    Pin.OwnerPartId := 1;
    Pin.OwnerPartDisplayMode := 0;
    CurComp.AddSchObject(Pin);
end;

procedure CRect(X1, Y1, X2, Y2 : Integer; Solid : Boolean);
var R : ISch_Rectangle;
begin
    R := SchServer.SchObjectFactory(eRectangle, eCreate_Default);
    R.LineWidth := eSmall;
    R.Location := Point(MilsToCoord(X1), MilsToCoord(Y1));
    R.Corner := Point(MilsToCoord(X2), MilsToCoord(Y2));
    R.IsSolid := Solid;
    R.AreaColor := $00B0FFFF;
    R.Color := $00800000;
    R.OwnerPartId := 1;
    R.OwnerPartDisplayMode := 0;
    CurComp.AddSchObject(R);
end;

procedure CLine(X1, Y1, X2, Y2 : Integer);
var L : ISch_Line;
begin
    L := SchServer.SchObjectFactory(eLine, eCreate_Default);
    L.LineWidth := eSmall;
    L.Color := $00800000;
    L.Location := Point(MilsToCoord(X1), MilsToCoord(Y1));
    L.Corner := Point(MilsToCoord(X2), MilsToCoord(Y2));
    L.OwnerPartId := 1;
    L.OwnerPartDisplayMode := 0;
    CurComp.AddSchObject(L);
end;

procedure PlaceComp(X, Y, DX, DY, CX, CY : Integer; FPName, MPN : String);
var Impl : ISch_Implementation; Prm : ISch_Parameter;
begin
    CurComp.Designator.IsHidden := False;
    CurComp.Designator.Location := Point(MilsToCoord(DX), MilsToCoord(DY));
    CurComp.Comment.IsHidden := False;
    CurComp.Comment.Location := Point(MilsToCoord(CX), MilsToCoord(CY));
    Sch.RegisterSchObjectInContainer(CurComp);
    CurComp.MoveToXY(MilsToCoord(X), MilsToCoord(Y));
    Impl := CurComp.AddSchImplementation;
    Impl.ModelName := FPName;
    Impl.ModelType := 'PCBLIB';
    Impl.IsCurrent := True;
    Impl.UseComponentLibrary := False;
    Prm := SchServer.SchObjectFactory(eParameter, eCreate_Default);
    Prm.Name := 'MPN';
    Prm.Text := MPN;
    Prm.IsHidden := True;
    Prm.Location := Point(MilsToCoord(X), MilsToCoord(Y));
    CurComp.AddSchObject(Prm);
end;

procedure Wire(X1, Y1, X2, Y2 : Integer);
var W : ISch_Wire;
begin
    W := SchServer.SchObjectFactory(eWire, eCreate_GlobalCopy);
    W.InsertVertex := 1;
    W.SetState_Vertex(1, Point(MilsToCoord(X1), MilsToCoord(Y1)));
    W.InsertVertex := 2;
    W.SetState_Vertex(2, Point(MilsToCoord(X2), MilsToCoord(Y2)));
    Sch.RegisterSchObjectInContainer(W);
end;

procedure NetLbl(X, Y : Integer; T : String);
var N : ISch_NetLabel;
begin
    N := SchServer.SchObjectFactory(eNetlabel, eCreate_GlobalCopy);
    N.Location := Point(MilsToCoord(X), MilsToCoord(Y));
    N.Text := T;
    N.Orientation := eRotate0;
    Sch.RegisterSchObjectInContainer(N);
end;

procedure PPort(X, Y : Integer; T : String; Style, Orient : Integer);
var P : ISch_PowerObject;
begin
    P := SchServer.SchObjectFactory(ePowerObject, eCreate_GlobalCopy);
    P.Location := Point(MilsToCoord(X), MilsToCoord(Y));
    P.Style := Style;
    P.Orientation := Orient;
    P.Text := T;
    P.ShowNetName := True;
    Sch.RegisterSchObjectInContainer(P);
end;

procedure NoErc(X, Y : Integer);
var E : ISch_NoERC;
begin
    E := SchServer.SchObjectFactory(eNoERC, eCreate_GlobalCopy);
    E.Location := Point(MilsToCoord(X), MilsToCoord(Y));
    Sch.RegisterSchObjectInContainer(E);
end;

procedure Title(X, Y : Integer; T : String);
var L : ISch_Label;
begin
    L := SchServer.SchObjectFactory(eLabel, eCreate_GlobalCopy);
    L.Location := Point(MilsToCoord(X), MilsToCoord(Y));
    L.Text := T;
    L.Color := $00000080;
    Sch.RegisterSchObjectInContainer(L);
end;

procedure Frame(X1, Y1, X2, Y2 : Integer);
var R : ISch_Rectangle;
begin
    R := SchServer.SchObjectFactory(eRectangle, eCreate_GlobalCopy);
    R.LineWidth := eSmall;
    R.Location := Point(MilsToCoord(X1), MilsToCoord(Y1));
    R.Corner := Point(MilsToCoord(X2), MilsToCoord(Y2));
    R.IsSolid := False;
    R.Color := $00808080;
    Sch.RegisterSchObjectInContainer(R);
end;

procedure Run;
var Doc : IServerDocument;
begin
    LogLines := TStringList.Create;
    HatLog('sch: start');
    if SchServer = nil then Client.StartServer('SCH');
    Doc := Client.GetDocumentByPath(SCH_DOC);
    if Doc <> nil then Client.CloseDocument(Doc);
    if FileExists(SCH_DOC) then DeleteFile(SCH_DOC);
    Doc := CreateNewDocumentFromDocumentKind('SCH');
    Doc.DoSafeChangeFileNameAndSave(SCH_DOC, 'SCH');
    Sch := SchServer.GetSchDocumentByPath(SCH_DOC);
    if Sch = nil then begin HatResult('{"error":"sheet did not open"}'); Exit; end;
    Sch.SheetStyle := eSheetA1;
    HatLog('sch: A1 sheet ready');
    SchServer.ProcessControl.PreProcess(Sch, '');""")

# ---------------------------------------------------------------- layout + emit
order = {b: [] for b in REGION}
for ref, s, f, c, mpn in PARTS:
    order[BLOCK[ref]].append((ref, s, f, c, mpn))
placed = 0
for b, items in order.items():
    x0, y0, x1, y1, title = REGION[b]
    A("    Frame(%d, %d, %d, %d);" % (x0, y0, x1, y1))
    A("    Title(%d, %d, %s);" % (x0 + 100, y1 - 180, q(title)))
    # big parts first in each block so rows pack well
    items.sort(key=lambda it: (0 if it[1] not in TWO_PIN else 1, it[0]))
    cx, row_top, row_h = x0 + 100, y1 - 450, 0
    for ref, s, f, c, mpn in items:
        pins, w, h = geom(s)
        lm, rm = margins(ref, pins)
        cell_w = lm + w + rm
        cell_h = h + 600
        if cx + cell_w > x1 - 100 and cx > x0 + 100:
            cx = x0 + 100
            row_top -= row_h
            row_h = 0
        ox = ((cx + lm) // 100) * 100
        oy = ((row_top - 350) // 100) * 100       # first pin row
        if oy - h < y0 + 100:
            raise SystemExit("block %s overflows at %s" % (b, ref))
        A("    HatLog(%s);" % q("sch: " + ref))
        A("    NewComp(%s, %s, %s, %s, %s, %s);" % (q(ref), q(s), q(SYM[s][0][:200]), q(c), q(f), q(mpn)))
        # graphics
        if s in TWO_PIN:
            if s in ("RES", "IND"):
                A("    CRect(100, 50, 200, -50, True);")
            elif s == "CAP":
                A("    CLine(100, 0, 135, 0); CLine(165, 0, 200, 0); CLine(135, 70, 135, -70); CLine(165, 70, 165, -70);")
            elif s in ("DIODE_SCHOTTKY", "LED"):
                A("    CLine(100, 0, 110, 0); CLine(110, 60, 110, -60); CLine(110, 60, 190, 0); CLine(110, -60, 190, 0); CLine(190, 60, 190, -60); CLine(190, 0, 200, 0);")
            elif s == "TVS_UNI":   # pin 1 (cathode) on the left
                A("    CLine(100, 0, 110, 0); CLine(110, 60, 110, -60); CLine(190, 60, 190, -60); CLine(190, 60, 110, 0); CLine(190, -60, 110, 0); CLine(190, 0, 200, 0);")
            else:   # batteries
                A("    CLine(100, 0, 135, 0); CLine(135, 90, 135, -90); CLine(165, 50, 165, -50); CLine(165, 0, 200, 0);")
        else:
            A("    CRect(0, 100, %d, %d, True);" % (w, -h - 100))
        for num, name, typ, side, x, y, plen in pins:
            show = "False" if s in TWO_PIN else "True"
            A("    CPin(%s, %s, %s, %s, %d, %d, %d, %s);" % (
                q(num), q(name), ELEC[typ], "eRotate180" if side == "L" else "eRotate0", x, y, plen, show))
        A("    PlaceComp(%d, %d, %d, %d, %d, %d, %s, %s);" % (
            ox, oy, 0, 180 if s not in TWO_PIN else 100, 0 if s not in TWO_PIN else 0,
            -h - 250 if s not in TWO_PIN else -200, q(f), q(mpn)))
        # stubs, labels, ports, no-ERC
        for num, name, typ, side, x, y, plen in pins:
            d = -1 if side == "L" else 1
            hx, hy = ox + x + d * plen, oy + y
            key = ref + "." + num
            n = PIN_NET.get(key)
            if n is None:
                A("    NoErc(%d, %d);" % (hx, hy))
                continue
            if n in POWER:
                ex = hx + d * 200
                A("    Wire(%d, %d, %d, %d);" % (hx, hy, ex, hy))
                st, orient = POWER[n]
                A("    PPort(%d, %d, %s, %d, %s);" % (ex, hy, q(n), st, orient))
            else:
                stub = 200 if d > 0 else max(200, ((text_w(n) + 99) // 100) * 100)
                ex = hx + d * stub
                A("    Wire(%d, %d, %d, %d);" % (hx, hy, ex, hy))
                A("    NetLbl(%d, %d, %s);" % (ex if d > 0 else ex, hy, q(n)))
        placed += 1
        cx += cell_w
        row_h = max(row_h, cell_h)

A("""    SchServer.ProcessControl.PostProcess(Sch, '');
    Sch.GraphicallyInvalidate;
    Doc.Modified := True;
    Doc.DoFileSave('');
    HatLog('sch: saved');
    HatResult('{"components": %d}');
end;""" % placed)

path = os.path.join(HERE, "altium", "build_sch.pas")
open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("wrote %s (%d lines, %d components)" % (path, len(out), placed))
