{ Hide every component designator and comment on the PCB silkscreen (clean board look;
  designators stay available for the assembly drawing). }
procedure Run;
var
    Board : IPCB_Board;
    It    : IPCB_BoardIterator;
    C     : IPCB_Component;
    L     : TInterfaceList;
    I     : Integer;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    if Board = nil then begin HatResult('{"error":"no board"}'); Exit; end;
    L := TInterfaceList.Create;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eComponentObject));
    It.AddFilter_LayerSet(AllLayers);
    It.AddFilter_Method(eProcessAll);
    C := It.FirstPCBObject;
    while C <> nil do begin L.Add(C); C := It.NextPCBObject; end;
    Board.BoardIterator_Destroy(It);
    PCBServer.PreProcess;
    for I := 0 to L.Count - 1 do
    begin
        C := L.Items[I];
        PCBServer.SendMessageToRobots(C.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
        C.NameOn := False;
        C.CommentOn := False;
        PCBServer.SendMessageToRobots(C.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
    end;
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    HatLog('hidden text on ' + IntToStr(L.Count));
    HatResult('{"components": ' + IntToStr(L.Count) + '}');
end;
