procedure Run;
var Board : IPCB_Board; It : IPCB_BoardIterator; R : IPCB_Rule; L : TInterfaceList; I : Integer; Rep : TStringList;
begin
    LogLines := TStringList.Create; Rep := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    L := TInterfaceList.Create;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eRuleObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    R := It.FirstPCBObject;
    while R <> nil do begin if R.Name = 'Width_Power' then L.Add(R); R := It.NextPCBObject; end;
    Board.BoardIterator_Destroy(It);
    PCBServer.PreProcess;
    for I := 0 to L.Count - 1 do
    begin
        R := L.Items[I];
        PCBServer.SendMessageToRobots(R.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
        R.MinWidth[eTopLayer] := MMsToCoord(0.2); R.MinWidth[eBottomLayer] := MMsToCoord(0.2);
        R.MinWidth[eMidLayer1] := MMsToCoord(0.2); R.MinWidth[eMidLayer2] := MMsToCoord(0.2);
        PCBServer.SendMessageToRobots(R.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
        Rep.Add(R.Descriptor);
    end;
    PCBServer.PostProcess;
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
