procedure Run;
var Board : IPCB_Board; It : IPCB_BoardIterator; P : IPCB_Polygon; L : TInterfaceList; I : Integer;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    L := TInterfaceList.Create;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(ePolyObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    P := It.FirstPCBObject;
    while P <> nil do begin L.Add(P); P := It.NextPCBObject; end;
    Board.BoardIterator_Destroy(It);
    PCBServer.PreProcess;
    for I := 0 to L.Count - 1 do begin P := L.Items[I]; HatLog('repour ' + P.Name); P.Rebuild; end;
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    HatResult('{"repoured": ' + IntToStr(L.Count) + '}');
end;
