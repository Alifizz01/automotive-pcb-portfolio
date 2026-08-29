# -*- coding: utf-8 -*-
"""Emit the DelphiScript that builds the CAN Sniffer pHAT schematic sheet."""
from paths import SCHLIB as LIB, SCHDOC as DOC

# designator, libref, comment(value), x, y
PARTS = [
    # --- host interface ---
    ("J1",  "HDR_2X20_PI",  "Pi 40-pin GPIO",     1400, 10400),
    # --- CAN FD controller ---
    ("U1",  "MCP2518FD",    "MCP2518FDT-H/SL",    4600, 10400),
    ("C1",  "CAP",          "100nF",              4400,  8800),
    ("Y1",  "CRYSTAL",      "40MHz",              6200,  9900),
    ("C7",  "CAP",          "18pF",               6200,  9300),
    ("C8",  "CAP",          "18pF",               6200,  8900),
    # --- CAN FD transceiver ---
    ("U2",  "MCP2562FD",    "MCP2562FD-E/SN",     8000, 10400),
    ("C2",  "CAP",          "100nF",              7800,  8400),
    ("C3",  "CAP",          "100nF",              7800,  8000),
    ("R4",  "RES",          "10k",                7600,  8900),
    # --- bus connector and termination ---
    ("R7",  "RES",          "120R 1%",           10600, 10400),
    ("JP1", "JUMPER2",      "TERM",              10600,  9900),
    ("J2",  "SCREWTERM_3",  "CAN 3.5mm",         13200, 10400),
    # --- HAT ID EEPROM ---
    ("U3",  "CAT24C32",     "CAT24C32WI-GT3",     4600,  6400),
    ("R1",  "RES",          "3k9",                2400,  6900),
    ("R2",  "RES",          "3k9",                2400,  6400),
    ("R3",  "RES",          "1k",                 2400,  5900),
    ("TP1", "TESTPOINT",    "WP",                 2400,  5400),
    ("C4",  "CAP",          "100nF",              6600,  6400),
    # --- indicators ---
    ("R5",  "RES",          "1k",                 9000,  6400),
    ("D1",  "LED",          "Green PWR",         10900,  6400),
    ("R6",  "RES",          "1k",                 9000,  5800),
    ("D2",  "LED",          "Yellow ACT",        10900,  5800),
    # --- bulk decoupling ---
    ("C5",  "CAP",          "10uF",               1400,  4000),
    ("C6",  "CAP",          "10uF",               2600,  4000),
    # --- GPIO breakout ---
    ("J3",  "HDR_2X12_BRK", "2x12 breakout",     13200,  8200),
]

out = []
A = out.append
A("SandboxLog('build: start');")
A("if SchServer = nil then Client.StartServer('SCH');")
A("S1 := '%s';" % LIB)
A("S2 := '%s';" % DOC)
A("SandboxLog('build: opening library');")
# GetSchDocumentByPath only returns ALREADY-OPEN documents - open it first.
A("if not Client.IsDocumentOpen(S1) then")
A("    Client.OpenDocument('SchLib', S1);")
A("Obj1 := SchServer.GetSchDocumentByPath(S1);")
A("if Obj1 = nil then")
A("begin")
A("    ResultText := '{\"error\":\"library failed to open\"}';")
A("    SandboxLog('build: LIBRARY NIL - aborting');")
A("    Exit;")
A("end;")
A("SandboxLog('build: library open');")
A("SandboxLog('build: creating sheet');")
A("Obj2 := CreateNewDocumentFromDocumentKind('SCH');")
A("Obj2.DoSafeChangeFileNameAndSave(S2, 'SCH');")
A("Obj3 := SchServer.GetSchDocumentByPath(S2);")
A("SandboxLog('build: sheet ready');")
A("I1 := 0;")
A("SchServer.ProcessControl.PreProcess(Obj3, '');")
# Obj1 = library, Obj2 = sheet IServerDocument, Obj3 = sheet ISch_Document,
# Obj4 = symbol found / iterator cursor, Obj5 = iterator then the placed clone.
for des, ref, comment, x, y in PARTS:
    A("SandboxLog('build: placing %s (%s)');" % (des, ref))
    A("Obj5 := Obj1.SchLibIterator_Create;")
    A("Obj5.AddFilter_ObjectSet(MkSet(eSchComponent));")
    A("B1 := 0;")
    A("Obj4 := Obj5.FirstSchObject;")
    A("while (Obj4 <> nil) and (B1 = 0) do")
    A("begin")
    A("    if Obj4.LibReference = '%s' then" % ref)
    A("        B1 := 1")
    A("    else")
    A("        Obj4 := Obj5.NextSchObject;")
    A("end;")
    A("Obj1.SchIterator_Destroy(Obj5);")
    A("if B1 = 1 then")
    A("begin")
    A("    Obj5 := Obj4.Replicate;")
    A("    Obj5.Location := Point(MilsToCoord(%d), MilsToCoord(%d));" % (x, y))
    A("    Obj5.Designator.Text := '%s';" % des)
    A("    Obj5.Designator.IsHidden := False;")
    A("    Obj5.Comment.Text := '%s';" % comment)
    A("    Obj5.Comment.IsHidden := False;")
    A("    Obj5.LibraryPath := S1;")
    A("    Obj5.DesignItemId := '%s';" % ref)
    A("    Obj3.RegisterSchObjectInContainer(Obj5);")
    A("    I1 := I1 + 1;")
    A("end")
    A("else")
    A("    SandboxLog('build: MISSING SYMBOL %s for %s');" % (ref, des))
A("SchServer.ProcessControl.PostProcess(Obj3, '');")
A("Obj3.GraphicallyInvalidate;")
A("Obj2.DoFileSave('SCH');")
A("SandboxLog('build: placed ' + IntToStr(I1) + ' components');")
A("ResultText := '{\"placed\": ' + IntToStr(I1) + ', \"expected\": %d}';" % len(PARTS))
A("SandboxLog('build: done');")

import os
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_sheet.pas"),
     "w", encoding="utf-8").write(chr(10).join(out) + chr(10))
print("emitted %d components, %d script lines" % (len(PARTS), len(out)))
