{ Close the PCB, reopen it from disk, and report what the saved file really
  contains: board outline vertices and mounting holes. }

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

procedure Run;
var
    Doc     : IServerDocument;
    Board   : IPCB_Board;
    Outline : IPCB_BoardOutline;
    PolySeg : TPolySegment;
    Iter    : IPCB_BoardIterator;
    Pad     : IPCB_Pad;
    I       : Integer;
    Verts   : String;
    Holes   : String;
    NHoles  : Integer;
    MinX, MaxX, MinY, MaxY : Float;
    V       : Float;
begin
    LogLines := TStringList.Create;
    HatLog('vpcb: start');

    Doc := Client.GetDocumentByPath(PCB_DOC);
    if Doc <> nil then
    begin
        Doc.Modified := False;
        Client.CloseDocument(Doc);
        HatLog('vpcb: closed in-memory copy');
    end;
    Doc := Client.OpenDocument('PCB', PCB_DOC);
    Client.ShowDocument(Doc);
    HatLog('vpcb: reopened from disk');

    Board := PCBServer.GetCurrentPCBBoard;
    if Board = nil then
    begin
        HatResult('{"error":"no board after reopen"}');
        Exit;
    end;

    Outline := Board.BoardOutline;
    Verts := '';
    MinX := 1e9; MaxX := -1e9; MinY := 1e9; MaxY := -1e9;
    for I := 0 to Outline.PointCount - 1 do
    begin
        PolySeg := Outline.Segments[I];
        V := CoordToMMs(PolySeg.vx);
        if V < MinX then MinX := V;
        if V > MaxX then MaxX := V;
        V := CoordToMMs(PolySeg.vy);
        if V < MinY then MinY := V;
        if V > MaxY then MaxY := V;
        Verts := Verts + '(' + FloatToStr(CoordToMMs(PolySeg.vx)) + ',' +
                 FloatToStr(CoordToMMs(PolySeg.vy)) + ') ';
    end;
    HatLog('vpcb: outline ' + Verts);

    NHoles := 0;
    Holes := '';
    Iter := Board.BoardIterator_Create;
    Iter.AddFilter_ObjectSet(MkSet(ePadObject));
    Iter.AddFilter_LayerSet(AllLayers);
    Iter.AddFilter_Method(eProcessAll);
    Pad := Iter.FirstPCBObject;
    while Pad <> nil do
    begin
        if Copy(Pad.Name, 1, 2) = 'MH' then
        begin
            NHoles := NHoles + 1;
            Holes := Holes + Pad.Name + '(' + FloatToStr(CoordToMMs(Pad.X)) + ',' +
                     FloatToStr(CoordToMMs(Pad.Y)) + ',d' +
                     FloatToStr(CoordToMMs(Pad.HoleSize)) + ') ';
        end;
        Pad := Iter.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(Iter);
    HatLog('vpcb: ' + IntToStr(NHoles) + ' mounting holes: ' + Holes);

    HatResult('{"outline_size_mm": "' + FloatToStr(MaxX - MinX) + ' x ' +
              FloatToStr(MaxY - MinY) + '", "vertices": "' + Verts +
              '", "mounting_holes": ' + IntToStr(NHoles) + ', "holes": "' + Holes + '"}');
    HatLog('vpcb: done');
end;
