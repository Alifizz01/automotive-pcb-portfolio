procedure Run;
var Board : IPCB_Board; It : IPCB_BoardIterator; P : IPCB_Primitive; L : TInterfaceList; I : Integer;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    L := TInterfaceList.Create;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eTrackObject, eViaObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    P := It.FirstPCBObject;
    while P <> nil do begin if not P.InComponent then L.Add(P); P := It.NextPCBObject; end;
    Board.BoardIterator_Destroy(It);
    PCBServer.PreProcess;
    for I := 0 to L.Count - 1 do begin P := L.Items[I]; P.Moveable := True; end;
    PCBServer.PostProcess;
    HatResult('{"unlocked": ' + IntToStr(L.Count) + '}');
end;
