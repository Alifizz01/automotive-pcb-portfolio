{ Set the CAN Sniffer pHAT board outline to 65.0 x 30.0 mm and place the four
  M2.5 mounting holes.

  Board outline vertices can only be written through TPolySegment records, and
  a script has to declare a variable to hold one, which is why this is a proper
  script project rather than a snippet.
  Writing Segments[i].vx directly does nothing: the property returns the record
  by value, so it must be copied out, modified, and assigned back. }

const
    PCB_DOC = '{{PCB_DOC}}';   { filled in by arun2.py on deploy }
    LOG_PATH = 'C:\Users\Public\altium_hat\hat_log.txt';
    RESULT_PATH = 'C:\Users\Public\altium_hat\hat_result.json';

var
    LogLines : TStringList;

procedure HatLog(Msg : String);
begin
    LogLines.Add(Msg);
    LogLines.SaveToFile(LOG_PATH);
end;

procedure HatResult(Json : String);
var
    L : TStringList;
begin
    L := TStringList.Create;
    try
        L.Text := Json;
        L.SaveToFile(RESULT_PATH);
    finally
        L.Free;
    end;
end;

procedure AddMountingHole(Board : IPCB_Board, XmmVal : Float, YmmVal : Float, Idx : Integer);
var
    Pad : IPCB_Pad;
begin
    Pad := PCBServer.PCBObjectFactory(ePadObject, eNoDimension, eCreate_Default);
    Pad.X := MMsToCoord(XmmVal);
    Pad.Y := MMsToCoord(YmmVal);
    Pad.Layer := eMultiLayer;
    Pad.HoleSize := MMsToCoord(2.75);
    Pad.Plated := False;
    { No copper land: the Raspberry Pi HAT drawing asks for the mounting hole land
      to be bare board or isolated copper, never connected to GND. }
    Pad.TopXSize := MMsToCoord(2.75);
    Pad.TopYSize := MMsToCoord(2.75);
    Pad.TopShape := eRounded;
    Pad.Name := 'MH' + IntToStr(Idx);
    Board.AddPCBObject(Pad);
    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast,
                                  PCBM_BoardRegisteration, Pad.I_ObjectAddress);
end;

procedure Run;
var
    Doc      : IServerDocument;
    Board    : IPCB_Board;
    Outline  : IPCB_BoardOutline;
    PolySeg  : TPolySegment;
    Iter     : IPCB_BoardIterator;
    Prim     : IPCB_Primitive;
    Doomed   : TInterfaceList;
    XS, YS   : array[0..3] of Float;
    I        : Integer;
    W, H     : Float;
begin
    LogLines := TStringList.Create;
    HatLog('outline: start');

    if not Client.IsDocumentOpen(PCB_DOC) then
        Client.OpenDocument('PCB', PCB_DOC);
    Doc := Client.GetDocumentByPath(PCB_DOC);
    if Doc = nil then
    begin
        HatResult('{"error":"pcb document did not open"}');
        Exit;
    end;
    Client.ShowDocument(Doc);
    HatLog('outline: document shown');

    Board := PCBServer.GetCurrentPCBBoard;
    if Board = nil then
    begin
        HatResult('{"error":"no current PCB board"}');
        HatLog('outline: BOARD NIL');
        Exit;
    end;
    HatLog('outline: board acquired');

    XS[0] := 0;  YS[0] := 0;
    XS[1] := 65; YS[1] := 0;
    XS[2] := 65; YS[2] := 30;
    XS[3] := 0;  YS[3] := 30;

    PCBServer.PreProcess;

    { Remove mounting holes left by an earlier run so this script is repeatable }
    Doomed := TInterfaceList.Create;
    Iter := Board.BoardIterator_Create;
    Iter.AddFilter_ObjectSet(MkSet(ePadObject));
    Iter.AddFilter_LayerSet(AllLayers);
    Iter.AddFilter_Method(eProcessAll);
    Prim := Iter.FirstPCBObject;
    while Prim <> nil do
    begin
        if Copy(Prim.Name, 1, 2) = 'MH' then
            Doomed.Add(Prim);
        Prim := Iter.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(Iter);
    for I := 0 to Doomed.Count - 1 do
        Board.RemovePCBObject(Doomed.Items[I]);
    HatLog('outline: cleared ' + IntToStr(Doomed.Count) + ' old mounting holes');

    { Board.BoardOutline returns a fresh temporary on every call, so writes to
      Board.BoardOutline.X are silently discarded. Hold one reference instead. }
    Outline := Board.BoardOutline;
    Outline.Invalidate;
    Outline.PointCount := 4;
    for I := 0 to 3 do
    begin
        PolySeg := Outline.Segments[I];
        PolySeg.Kind := ePolySegmentLine;
        PolySeg.vx := MMsToCoord(XS[I]);
        PolySeg.vy := MMsToCoord(YS[I]);
        Outline.Segments[I] := PolySeg;
        HatLog('outline: vertex ' + IntToStr(I) + ' -> ' +
               FloatToStr(XS[I]) + ',' + FloatToStr(YS[I]));
    end;
    Outline.Rebuild;
    Outline.Validate;
    HatLog('outline: rebuilt');

    { Mounting holes: 3.5 mm in from each edge, per the Raspberry Pi HAT board
      mechanical specification and the Zero 2 W drawing (58 x 23 mm pitch). }
    AddMountingHole(Board, 3.5, 3.5, 1);
    AddMountingHole(Board, 61.5, 3.5, 2);
    AddMountingHole(Board, 3.5, 26.5, 3);
    AddMountingHole(Board, 61.5, 26.5, 4);
    HatLog('outline: 4 mounting holes placed');

    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;

    { measure from a freshly fetched outline, not the one we just wrote }
    W := CoordToMMs(Board.BoardOutline.BoundingRectangle.Right -
                    Board.BoardOutline.BoundingRectangle.Left);
    H := CoordToMMs(Board.BoardOutline.BoundingRectangle.Top -
                    Board.BoardOutline.BoundingRectangle.Bottom);
    HatLog('outline: measured ' + FloatToStr(W) + ' x ' + FloatToStr(H) + ' mm');

    Doc.Modified := True;
    Doc.DoFileSave('');
    HatLog('outline: saved');

    HatResult('{"width_mm": ' + FloatToStr(W) + ', "height_mm": ' + FloatToStr(H) +
              ', "points": ' + IntToStr(Board.BoardOutline.PointCount) + '}');
    HatLog('outline: done');
end;
