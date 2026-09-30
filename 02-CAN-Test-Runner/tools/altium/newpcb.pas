{ Create CAN_Test_Runner.PcbDoc: 100 x 66 mm outline with 3 mm corner radius, four M3
  mounting holes 4 mm in from each edge, and a four-layer stack (MFR-01). }
const
    BW = 100.0;
    BH = 66.0;
    RC = 3.0;

procedure AddHole(Board : IPCB_Board; X, Y : Double; N : Integer);
var Pad : IPCB_Pad;
begin
    Pad := PCBServer.PCBObjectFactory(ePadObject, eNoDimension, eCreate_Default);
    Pad.X := MMsToCoord(X);
    Pad.Y := MMsToCoord(Y);
    Pad.Layer := eMultiLayer;
    Pad.TopXSize := MMsToCoord(3.2); Pad.TopYSize := MMsToCoord(3.2);
    Pad.MidXSize := MMsToCoord(3.2); Pad.MidYSize := MMsToCoord(3.2);
    Pad.BotXSize := MMsToCoord(3.2); Pad.BotYSize := MMsToCoord(3.2);
    Pad.TopShape := eRounded;
    Pad.HoleSize := MMsToCoord(3.2);
    Pad.Plated := False;
    Pad.Name := 'MH' + IntToStr(N);
    Pad.Moveable := False;
    Board.AddPCBObject(Pad);
end;

procedure SetLine(O : IPCB_BoardOutline; I : Integer; X, Y : Double);
var S : TPolySegment;
begin
    S := O.Segments[I];
    S.Kind := ePolySegmentLine;
    S.vx := MMsToCoord(X);
    S.vy := MMsToCoord(Y);
    O.Segments[I] := S;
end;

procedure SetArc(O : IPCB_BoardOutline; I : Integer; X, Y, CX, CY, A1, A2 : Double);
var S : TPolySegment;
begin
    S := O.Segments[I];
    S.Kind := ePolySegmentArc;
    S.vx := MMsToCoord(X);
    S.vy := MMsToCoord(Y);
    S.cx := MMsToCoord(CX);
    S.cy := MMsToCoord(CY);
    S.Radius := MMsToCoord(RC);
    S.Angle1 := A1;
    S.Angle2 := A2;
    O.Segments[I] := S;
end;

procedure Run;
var
    Doc     : IServerDocument;
    Board   : IPCB_Board;
    Outline : IPCB_BoardOutline;
    LS      : IPCB_LayerStack_V7;
begin
    LogLines := TStringList.Create;
    HatLog('pcb: start');
    Doc := Client.GetDocumentByPath(PCB_DOC);
    if Doc <> nil then Client.CloseDocument(Doc);
    if FileExists(PCB_DOC) then DeleteFile(PCB_DOC);
    Doc := CreateNewDocumentFromDocumentKind('PCB');
    Doc.DoSafeChangeFileNameAndSave(PCB_DOC, 'PCB');
    Client.ShowDocument(Doc);
    Board := PCBServer.GetCurrentPCBBoard;
    if Board = nil then begin HatResult('{"error":"no board"}'); Exit; end;
    HatLog('pcb: board open');

    PCBServer.PreProcess;
    Outline := Board.BoardOutline;
    Outline.Invalidate;
    Outline.PointCount := 8;
    { counter-clockwise from the bottom edge; each arc segment ends a straight edge }
    SetLine(Outline, 0, RC, 0);
    SetArc(Outline, 1, BW - RC, 0, BW - RC, RC, 270, 360);
    SetLine(Outline, 2, BW, RC);
    SetArc(Outline, 3, BW, BH - RC, BW - RC, BH - RC, 0, 90);
    SetLine(Outline, 4, BW - RC, BH);
    SetArc(Outline, 5, RC, BH, RC, BH - RC, 90, 180);
    SetLine(Outline, 6, 0, BH - RC);
    SetArc(Outline, 7, 0, RC, RC, RC, 180, 270);
    Outline.Rebuild;
    Outline.Validate;
    HatLog('pcb: outline');

    AddHole(Board, 4, 4, 1);
    AddHole(Board, BW - 4, 4, 2);
    AddHole(Board, 4, BH - 4, 3);
    AddHole(Board, BW - 4, BH - 4, 4);
    HatLog('pcb: holes');

    LS := Board.LayerStack_V7;
    LS.InsertLayer(eMidLayer1);
    LS.InsertLayer(eMidLayer2);
    HatLog('pcb: signal layers now ' + IntToStr(LS.SignalLayerCount));
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    Doc.Modified := True;
    Doc.DoFileSave('');
    HatLog('pcb: saved');
    HatResult('{"layers": ' + IntToStr(LS.SignalLayerCount) + '}');
end;
