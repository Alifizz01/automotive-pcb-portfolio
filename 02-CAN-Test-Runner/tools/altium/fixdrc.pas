const
    PWR = '|GND|3V3|5V_AUX|VSYS|VBAT|VCHG|5V_BUCK|VIN_P|V1_IN|V2_IN|CELL_P|CELL_N|FET_MID|BUCK_SW|BB_L1|BB_L2|BOOST_SW|VBUS|';
procedure Run;
var Board : IPCB_Board; It : IPCB_BoardIterator; P : IPCB_Primitive; L, RL : TInterfaceList; I, N : Integer; R : IPCB_Rule;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    L := TInterfaceList.Create; RL := TInterfaceList.Create;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eTrackObject, eRuleObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    P := It.FirstPCBObject;
    while P <> nil do
    begin
        if P.ObjectId = eRuleObject then begin if P.Name = 'Clearance_Pour' then RL.Add(P); end
        else if P.InNet and (not P.InPolygon) and (P.Width < MMsToCoord(0.2)) and (Pos('|' + P.Net.Name + '|', PWR) > 0) then L.Add(P);
        P := It.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(It);
    PCBServer.PreProcess;
    for I := 0 to L.Count - 1 do
    begin
        P := L.Items[I];
        PCBServer.SendMessageToRobots(P.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
        P.Width := MMsToCoord(0.2);
        PCBServer.SendMessageToRobots(P.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
    end;
    for I := 0 to RL.Count - 1 do Board.RemovePCBObject(RL.Items[I]);
    PCBServer.PostProcess;
    HatResult('{"widened": ' + IntToStr(L.Count) + ', "rules_removed": ' + IntToStr(RL.Count) + '}');
end;
