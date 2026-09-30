const
    POLYF = 'C:\Users\Public\altium_mcp\poly.txt';

function FindNet(Board : IPCB_Board; Name : String) : IPCB_Net;
var It : IPCB_BoardIterator; N : IPCB_Net;
begin
    Result := nil;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eNetObject));
    It.AddFilter_LayerSet(AllLayers);
    It.AddFilter_Method(eProcessAll);
    N := It.FirstPCBObject;
    while N <> nil do
    begin
        if N.Name = Name then begin Result := N; Break; end;
        N := It.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(It);
end;

procedure MakePour(Board : IPCB_Board; Net : IPCB_Net; Layer : Integer; Pts : TStringList; Name : String);
var
    Poly : IPCB_Polygon;
    Seg  : TPolySegment;
    F    : TStringList;
    I    : Integer;
begin
    F := TStringList.Create;
    F.Delimiter := ' ';
    Poly := PCBServer.PCBObjectFactory(ePolyObject, eNoDimension, eCreate_Default);
    Poly.Layer := Layer;
    Poly.Net := Net;
    Poly.Name := Name;
    Poly.PolyHatchStyle := ePolySolid;
    Poly.PourOver := ePolygonPourOver_SameNet;
    Poly.RemoveDead := True;
    Poly.PointCount := Pts.Count;
    for I := 0 to Pts.Count do
    begin
        F.DelimitedText := Pts[I mod Pts.Count];
        Seg := Poly.Segments[I];
        Seg.Kind := ePolySegmentLine;
        Seg.vx := MMsToCoord(StrToInt(F[0]) / 1000);
        Seg.vy := MMsToCoord(StrToInt(F[1]) / 1000);
        Poly.Segments[I] := Seg;
    end;
    Board.AddPCBObject(Poly);
    Poly.Rebuild;
    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Poly.I_ObjectAddress);
    HatLog('pour: ' + Name + ' area=' + FloatToStr(Poly.AreaSize));
end;

procedure Run;
var
    Board : IPCB_Board;
    Pts   : TStringList;
    Net   : IPCB_Net;
    R     : IPCB_Rule;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    Pts := TStringList.Create;
    Pts.LoadFromFile(POLYF);
    Net := FindNet(Board, 'GND');
    PCBServer.PreProcess;
    MakePour(Board, Net, eMidLayer1, Pts, 'GND_Plane_L2');
    MakePour(Board, FindNet(Board, '3V3'), eMidLayer2, Pts, '3V3_Plane_L3');
    MakePour(Board, Net, eTopLayer, Pts, 'GND_Top');
    MakePour(Board, Net, eBottomLayer, Pts, 'GND_Bottom');
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    HatResult('{"ok":true}');
end;
