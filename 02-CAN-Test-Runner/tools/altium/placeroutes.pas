const
    ROUTES = 'C:\Users\Public\altium_mcp\routes.txt';

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

function UM(S : String) : Integer;
begin
    Result := MMsToCoord(StrToInt(S) / 1000);
end;

procedure Run;
var
    Board : IPCB_Board;
    Lines, F : TStringList;
    I, NT, NV : Integer;
    Trk   : IPCB_Track;
    Via   : IPCB_Via;
    Net   : IPCB_Net;
    Rep   : TStringList;
begin
    LogLines := TStringList.Create;
    Rep := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    Lines := TStringList.Create;
    Lines.LoadFromFile(ROUTES);
    F := TStringList.Create;
    F.Delimiter := ' ';
    NT := 0; NV := 0;
    PCBServer.PreProcess;
    for I := 0 to Lines.Count - 1 do
    begin
        F.DelimitedText := Lines[I];
        if F.Count < 5 then Continue;
        Net := FindNet(Board, F[1]);
        if Net = nil then begin Rep.Add('NO NET ' + F[1]); Continue; end;
        if F[0] = 'T' then
        begin
            Trk := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
            Trk.X1 := UM(F[3]); Trk.Y1 := UM(F[4]);
            Trk.X2 := UM(F[5]); Trk.Y2 := UM(F[6]);
            Trk.Width := UM(F[7]);
            if F[2] = '0' then Trk.Layer := eTopLayer else if F[2] = '2' then Trk.Layer := eMidLayer2 else if F[2] = '3' then Trk.Layer := eMidLayer1 else Trk.Layer := eBottomLayer;
            Trk.Net := Net;
            Board.AddPCBObject(Trk);
            PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Trk.I_ObjectAddress);
            NT := NT + 1;
        end
        else
        begin
            Via := PCBServer.PCBObjectFactory(eViaObject, eNoDimension, eCreate_Default);
            Via.X := UM(F[2]); Via.Y := UM(F[3]);
            Via.Size := UM(F[4]);
            Via.HoleSize := UM(F[5]);
            Via.LowLayer := eTopLayer;
            Via.HighLayer := eBottomLayer;
            Via.Net := Net;
            Board.AddPCBObject(Via);
            PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Via.I_ObjectAddress);
            NV := NV + 1;
        end;
    end;
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    Rep.Add('tracks=' + IntToStr(NT) + ' vias=' + IntToStr(NV));
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
