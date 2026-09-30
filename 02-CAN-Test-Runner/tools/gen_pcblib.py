# -*- coding: utf-8 -*-
"""Emit altium/build_pcblib.pas: builds CAN_Test_Runner.PcbLib from footprints.py.

Layers are set with constants, never strings: String2Layer silently maps 'Multi-Layer'
to eNoLayer (lesson from project 01). Usage: python gen_pcblib.py [name ...]
"""
import os, sys
from footprints import FP

HERE = os.path.dirname(os.path.abspath(__file__))
only = sys.argv[1:]
SQ = chr(39)
q = lambda s: SQ + s.replace(SQ, SQ + SQ) + SQ
SHAPE = {"R": "eRectangular", "O": "eRounded", "RR": "eRoundedRectangular"}

out = []
A = out.append
A("""procedure AddPad(Comp : IPCB_LibComponent; PName : String; X, Y, W, H : Double; Shape : Integer;
                 Kind : Integer; Drill, SlotLen : Double; SlotRot : Double);
var Pad : IPCB_Pad;
begin
    Pad := PCBServer.PCBObjectFactory(ePadObject, eNoDimension, eCreate_Default);
    Pad.Mode := ePadMode_Simple;
    Pad.X := MMsToCoord(X);
    Pad.Y := MMsToCoord(Y);
    Pad.TopXSize := MMsToCoord(W);
    Pad.TopYSize := MMsToCoord(H);
    Pad.TopShape := Shape;
    Pad.Name := PName;
    if Kind = 0 then
    begin
        Pad.Layer := eTopLayer;
        Pad.HoleSize := 0;
    end
    else
    begin
        Pad.Layer := eMultiLayer;
        Pad.MidXSize := MMsToCoord(W); Pad.MidYSize := MMsToCoord(H); Pad.MidShape := Shape;
        Pad.BotXSize := MMsToCoord(W); Pad.BotYSize := MMsToCoord(H); Pad.BotShape := Shape;
        Pad.HoleSize := MMsToCoord(Drill);
        Pad.Plated := Kind = 1;
        if SlotLen > 0 then
        begin
            Pad.HoleType := eSlotHole;
            Pad.HoleWidth := MMsToCoord(SlotLen);
            Pad.HoleRotation := SlotRot;
        end;
    end;
    Comp.AddPCBObject(Pad);
    PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Pad.I_ObjectAddress);
end;

procedure AddSilk(Comp : IPCB_LibComponent; X1, Y1, X2, Y2 : Double);
var T : IPCB_Track;
begin
    T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
    T.X1 := MMsToCoord(X1); T.Y1 := MMsToCoord(Y1);
    T.X2 := MMsToCoord(X2); T.Y2 := MMsToCoord(Y2);
    T.Width := MMsToCoord(0.15);
    T.Layer := eTopOverlay;
    Comp.AddPCBObject(T);
    PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);
end;

procedure Run;
var
    Doc  : IServerDocument;
    Lib  : IPCB_Library;
    Comp : IPCB_LibComponent;
    N    : Integer;
begin
    LogLines := TStringList.Create;
    HatLog('lib: start');
    { always rebuild from scratch: close and delete any previous library }
    Doc := Client.GetDocumentByPath(LIB_DOC);
    if Doc <> nil then Client.CloseDocument(Doc);
    if FileExists(LIB_DOC) then DeleteFile(LIB_DOC);
    HatLog('lib: old library removed');
    Doc := CreateNewDocumentFromDocumentKind('PCBLIB');
    Doc.DoSafeChangeFileNameAndSave(LIB_DOC, 'PCBLIB');
    Client.ShowDocument(Doc);
    Lib := PCBServer.GetCurrentPCBLibrary;
    if Lib = nil then begin HatResult('{"error":"no library"}'); Exit; end;
    HatLog('lib: open');
    N := 0;""")

for name, f in FP.items():
    if only and name not in only:
        continue
    A("    HatLog(%s);" % q("lib: " + name))
    A("    Comp := PCBServer.CreatePCBLibComp;")
    A("    Comp.Name := %s;" % q(name))
    A("    Comp.Description := %s;" % q(f["desc"][:250]))
    A("    Comp.Height := MMsToCoord(%.3f);" % f["height"])
    A("    Lib.RegisterComponent(Comp);")
    A("    PCBServer.PreProcess;")
    for (pn, x, y, w, h, shape, kind, drill, slot) in f["pads"]:
        k = {"SMD": 0, "TH": 1, "NPTH": 2}[kind]
        sl, rot = 0.0, 0.0
        if slot:   # slot drawn along the long axis of the pad
            sl = max(slot)
            rot = 90.0 if h > w else 0.0
        A("    AddPad(Comp, %s, %.4f, %.4f, %.4f, %.4f, %s, %d, %.4f, %.4f, %.1f);"
          % (q(pn), x, y, w, h, SHAPE[shape], k, drill, sl, rot))
    for (x1, y1, x2, y2) in f["silk"]:
        A("    AddSilk(Comp, %.4f, %.4f, %.4f, %.4f);" % (x1, y1, x2, y2))
    A("    PCBServer.PostProcess;")
    A("    N := N + 1;")

A("""    Lib.Board.ViewManager_FullUpdate;
    Doc.Modified := True;
    Doc.DoFileSave('');
    HatLog('lib: saved ' + IntToStr(N));
    HatResult('{"footprints": ' + IntToStr(N) + '}');
end;""")

path = os.path.join(HERE, "altium", "build_pcblib.pas")
open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("wrote %s (%d lines)" % (path, len(out)))
