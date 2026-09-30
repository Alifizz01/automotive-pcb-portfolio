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
    while R <> nil do begin L.Add(R); R := It.NextPCBObject; end;
    Board.BoardIterator_Destroy(It);
    PCBServer.PreProcess;
    for I := 0 to L.Count - 1 do
    begin
        R := L.Items[I];
        if R.RuleKind = eRule_MaxMinHoleSize then begin HatLog('hole'); R.MaxLimit := MMsToCoord(3.5); Rep.Add(R.Descriptor); end;
        if R.RuleKind = eRule_MinimumSolderMaskSliver then begin HatLog('sliver'); R.MinSolderMaskSliver := MMsToCoord(0.075); Rep.Add(R.Descriptor); end;
        if R.RuleKind = eRule_SilkToSolderMaskClearance then begin HatLog('silk'); R.DRCEnabled := False; Rep.Add(R.Descriptor); end;
    end;
    PCBServer.PostProcess;
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
