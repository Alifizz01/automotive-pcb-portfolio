# -*- coding: utf-8 -*-
"""Build the schematic sheet by constructing each component directly from
library_spec.txt - the same source of truth the .SchLib is built from.

Replicate() on an open SchLib proved unreliable (it silently returns clones
with no pins, or nothing at all, depending on the library editor's current
component), so nothing here depends on it.
"""
import os, sys

from paths import SCHLIB as LIB, SCHDOC as DOC, LIBRARY_SPEC as SPEC


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_place import PARTS          # reuse the placement table

# ---- parse library_spec.txt into symbol definitions -----------------------
symbols, cur = {}, None
for raw in open(SPEC, encoding="utf-8"):
    f = raw.rstrip("\n").split("|")
    if f[0] == "SYMBOL":
        cur = f[1]
        symbols[cur] = {"desc": f[2], "pins": [], "graphics": []}
    elif f[0] == "PIN":
        symbols[cur]["pins"].append(f[1:])
    elif f[0] == "GRAPHIC":
        symbols[cur]["graphics"].append(f[1:])

# Footprint model attached to each placed component. AddSchImplementation takes
# NO arguments and returns the new implementation - passing one hangs Altium.
FOOTPRINTS = {
    "MCP2518FD":    "SOIC-14_150MIL",
    "MCP2562FD":    "SOIC-8_150MIL",
    "CAT24C32":     "SOIC-8_150MIL",
    "RES":          "0805",
    "CAP":          "0805",
    "LED":          "LED_0805",
    "CRYSTAL":      "XTAL_3225_4P",
    "HDR_2X20_PI":  "HDR_2X20_254",
    "HDR_2X12_BRK": "HDR_2X12_254",
    "SCREWTERM_3":  "TERM_3P_350",
    "JUMPER2":      "HDR_1X2_254",
    "TESTPOINT":    "TESTPOINT_60",
}

out = []
A = out.append
SQ = chr(39)


def q(s):
    return SQ + s.replace(SQ, SQ + SQ) + SQ


A("SandboxLog('sheet: start');")
A("if SchServer = nil then Client.StartServer('SCH');")
A("S1 := %s;" % q(LIB))
A("S2 := %s;" % q(DOC))
A("Obj2 := CreateNewDocumentFromDocumentKind('SCH');")
A("Obj2.DoSafeChangeFileNameAndSave(S2, 'SCH');")
A("Obj3 := SchServer.GetSchDocumentByPath(S2);")
A("if Obj3 = nil then")
A("begin")
A('    ResultText := ' + q('{"error":"sheet did not open"}') + ';')
A("    SandboxLog('sheet: DOC NIL');")
A("    Exit;")
A("end;")
A("Obj3.SheetStyle := 1;")   # eSheetA3
A("SandboxLog('sheet: blank A3 sheet ready');")
A("I1 := 0; I2 := 0;")
A("SchServer.ProcessControl.PreProcess(Obj3, '');")

for des, ref, comment, cx, cy in PARTS:
    sym = symbols[ref]
    A("SandboxLog('sheet: building %s (%s)');" % (des, ref))
    A("Obj5 := SchServer.SchObjectFactory(eSchComponent, eCreate_Default);")
    A("Obj5.CurrentPartID := 1;")
    A("Obj5.DisplayMode := 0;")
    A("Obj5.PartCount := 1;")
    A("Obj5.LibReference := %s;" % q(ref))
    A("Obj5.DesignItemId := %s;" % q(ref))
    A("Obj5.LibraryPath := S1;")
    A("Obj5.ComponentDescription := %s;" % q(sym["desc"]))

    # body: explicit graphics, else an auto-sized rectangle around the pins
    if sym["graphics"]:
        for g in sym["graphics"]:
            kind = g[0]
            if kind == "rectangle":
                _, part, w, solid, x1, y1, x2, y2 = g
                A("Obj4 := SchServer.SchObjectFactory(eRectangle, eCreate_Default);")
                A("Obj4.LineWidth := eSmall;")
                A("Obj4.Location := Point(MilsToCoord(%s), MilsToCoord(%s));" % (x1, y1))
                A("Obj4.Corner := Point(MilsToCoord(%s), MilsToCoord(%s));" % (x2, y2))
                A("Obj4.IsSolid := %s;" % ("True" if solid == "1" else "False"))
                A("Obj4.AreaColor := $00B0FFFF;")
                A("Obj4.Color := $00FF0000;")
                A("Obj4.OwnerPartId := 1;")
                A("Obj4.OwnerPartDisplayMode := 0;")
                A("Obj5.AddSchObject(Obj4);")
            elif kind == "line":
                _, part, w, x1, y1, x2, y2 = g
                A("Obj4 := SchServer.SchObjectFactory(eLine, eCreate_Default);")
                A("Obj4.LineWidth := eSmall;")
                A("Obj4.Location := Point(MilsToCoord(%s), MilsToCoord(%s));" % (x1, y1))
                A("Obj4.Corner := Point(MilsToCoord(%s), MilsToCoord(%s));" % (x2, y2))
                A("Obj4.OwnerPartId := 1;")
                A("Obj4.OwnerPartDisplayMode := 0;")
                A("Obj5.AddSchObject(Obj4);")
            elif kind in ("polygon", "polyline"):
                if kind == "polygon":
                    coords = g[4:]
                    A("Obj4 := SchServer.SchObjectFactory(ePolygon, eCreate_Default);")
                    A("Obj4.IsSolid := True;")
                    A("Obj4.AreaColor := $000000FF;")
                else:
                    coords = g[3:]
                    A("Obj4 := SchServer.SchObjectFactory(ePolyline, eCreate_Default);")
                pts = [(coords[i], coords[i + 1]) for i in range(0, len(coords) - 1, 2)]
                A("Obj4.LineWidth := eSmall;")
                A("Obj4.VerticesCount := %d;" % len(pts))
                for i, (px, py) in enumerate(pts, start=1):
                    A("Obj4.Vertex[%d] := Point(MilsToCoord(%s), MilsToCoord(%s));"
                      % (i, px, py))
                A("Obj4.OwnerPartId := 1;")
                A("Obj4.OwnerPartDisplayMode := 0;")
                A("Obj5.AddSchObject(Obj4);")
            elif kind == "ellipse":
                _, part, w, solid, ecx, ecy, r1, r2 = g
                A("Obj4 := SchServer.SchObjectFactory(eEllipse, eCreate_Default);")
                A("Obj4.Location := Point(MilsToCoord(%s), MilsToCoord(%s));" % (ecx, ecy))
                A("Obj4.Radius := MilsToCoord(%s);" % r1)
                A("Obj4.SecondaryRadius := MilsToCoord(%s);" % r2)
                A("Obj4.IsSolid := %s;" % ("True" if solid == "1" else "False"))
                A("Obj4.AreaColor := $00B0FFFF;")
                A("Obj4.Color := $00FF0000;")
                A("Obj4.OwnerPartId := 1;")
                A("Obj4.OwnerPartDisplayMode := 0;")
                A("Obj5.AddSchObject(Obj4);")
    else:
        xs = [int(p[4]) for p in sym["pins"]]
        ys = [int(p[5]) for p in sym["pins"]]
        A("Obj4 := SchServer.SchObjectFactory(eRectangle, eCreate_Default);")
        A("Obj4.LineWidth := eSmall;")
        A("Obj4.Location := Point(MilsToCoord(%d), MilsToCoord(%d));"
          % (min(xs), min(ys) - 100))
        A("Obj4.Corner := Point(MilsToCoord(%d), MilsToCoord(%d));"
          % (max(xs), max(ys) + 100))
        A("Obj4.IsSolid := True;")
        A("Obj4.AreaColor := $00B0FFFF;")
        A("Obj4.Color := $00FF0000;")
        A("Obj4.OwnerPartId := 1;")
        A("Obj4.OwnerPartDisplayMode := 0;")
        A("Obj5.AddSchObject(Obj4);")

    # pins
    for p in sym["pins"]:
        num, pname, ptype, orient, px, py = p[0], p[1], p[2], p[3], p[4], p[5]
        plen = p[7] if len(p) > 7 and p[7] else "300"
        shown = p[8] if len(p) > 8 and p[8] else "1"
        showd = p[9] if len(p) > 9 and p[9] else "1"
        A("Obj4 := SchServer.SchObjectFactory(ePin, eCreate_Default);")
        A("Obj4.Designator := %s;" % q(num))
        A("Obj4.Name := %s;" % q(pname))
        A("Obj4.Electrical := %s;" % ptype)
        A("Obj4.Orientation := %s;" % orient)
        A("Obj4.Location := Point(MilsToCoord(%s), MilsToCoord(%s));" % (px, py))
        A("Obj4.PinLength := MilsToCoord(%s);" % plen)
        A("Obj4.ShowName := %s;" % ("True" if shown == "1" else "False"))
        A("Obj4.ShowDesignator := %s;" % ("True" if showd == "1" else "False"))
        A("Obj4.OwnerPartId := 1;")
        A("Obj4.OwnerPartDisplayMode := 0;")
        A("Obj5.AddSchObject(Obj4);")
        A("I2 := I2 + 1;")

    xs = [int(p[4]) for p in sym["pins"]]
    ys = [int(p[5]) for p in sym["pins"]]
    A("Obj5.Designator.Text := %s;" % q(des))
    A("Obj5.Designator.IsHidden := False;")
    A("Obj5.Designator.Location := Point(MilsToCoord(%d), MilsToCoord(%d));"
      % (min(xs), max(ys) + 130))
    A("Obj5.Comment.Text := %s;" % q(comment))
    A("Obj5.Comment.IsHidden := False;")
    A("Obj5.Comment.Location := Point(MilsToCoord(%d), MilsToCoord(%d));"
      % (min(xs), max(ys) + 260))
    A("Obj3.RegisterSchObjectInContainer(Obj5);")
    A("Obj5.MoveToXY(MilsToCoord(%d), MilsToCoord(%d));" % (cx, cy))
    A("Obj4 := Obj5.AddSchImplementation;")
    A("Obj4.ModelName := %s;" % q(FOOTPRINTS[ref]))
    A("Obj4.ModelType := 'PCBLIB';")
    A("Obj4.IsCurrent := True;")
    A("Obj4.UseComponentLibrary := True;")
    A("I1 := I1 + 1;")

A("SchServer.ProcessControl.PostProcess(Obj3, '');")
A("Obj3.GraphicallyInvalidate;")
A("Obj2.DoFileSave('SCH');")
A("SandboxLog('sheet: ' + IntToStr(I1) + ' components, ' + IntToStr(I2) + ' pins');")
A('ResultText := ' + q('{"components": ') + " + IntToStr(I1) + " + q(', "pins": ')
  + " + IntToStr(I2) + " + q("}") + ";")
A("SandboxLog('sheet: done');")

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_sheet2.pas")
open(path, "w", encoding="utf-8").write(chr(10).join(out) + chr(10))
print("wrote %s: %d lines, %d components" % (path, len(out), len(PARTS)))
print("expected pins:", sum(len(symbols[r]["pins"]) for _, r, _, _, _ in PARTS))
