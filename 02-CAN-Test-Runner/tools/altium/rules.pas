{ Design rules for the CAN-FD Test Runner (D-03). Existing rules are collected first and
  edited afterwards: editing a rule inside the board iterator re-queues it forever. }
const
    POWER_SCOPE = 'InNet(''GND'') or InNet(''3V3'') or InNet(''5V_AUX'') or InNet(''VSYS'') or InNet(''VBAT'') or InNet(''VCHG'') or InNet(''5V_BUCK'') or InNet(''VIN_P'') or InNet(''V1_IN'') or InNet(''V2_IN'') or InNet(''CELL_P'') or InNet(''CELL_N'') or InNet(''FET_MID'') or InNet(''BUCK_SW'') or InNet(''BB_L1'') or InNet(''BB_L2'') or InNet(''BOOST_SW'') or InNet(''VBUS'')';

procedure SetW(R : IPCB_Rule; MinW, PrefW, MaxW : Double);
begin
    R.MinWidth[eTopLayer] := MMsToCoord(MinW); R.FavoredWidth[eTopLayer] := MMsToCoord(PrefW); R.MaxWidth[eTopLayer] := MMsToCoord(MaxW);
    R.MinWidth[eMidLayer1] := MMsToCoord(MinW); R.FavoredWidth[eMidLayer1] := MMsToCoord(PrefW); R.MaxWidth[eMidLayer1] := MMsToCoord(MaxW);
    R.MinWidth[eMidLayer2] := MMsToCoord(MinW); R.FavoredWidth[eMidLayer2] := MMsToCoord(PrefW); R.MaxWidth[eMidLayer2] := MMsToCoord(MaxW);
    R.MinWidth[eBottomLayer] := MMsToCoord(MinW); R.FavoredWidth[eBottomLayer] := MMsToCoord(PrefW); R.MaxWidth[eBottomLayer] := MMsToCoord(MaxW);
end;

procedure AddWidth(Board : IPCB_Board; Name, Scope : String; MinW, PrefW, MaxW : Double; Rep : TStringList);
var R : IPCB_Rule;
begin
    R := PCBServer.PCBRuleFactory(eRule_MaxMinWidth);
    R.Name := Name;
    R.Scope1Expression := Scope;
    SetW(R, MinW, PrefW, MaxW);
    Board.AddPCBObject(R);
    Rep.Add('added ' + R.Descriptor);
end;

procedure Run;
var
    Board : IPCB_Board;
    Iter  : IPCB_BoardIterator;
    Rule  : IPCB_Rule;
    Rules : TInterfaceList;
    Rep   : TStringList;
    I     : Integer;
    R     : IPCB_Rule;
begin
    LogLines := TStringList.Create;
    Rep := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    if Board = nil then begin HatResult('{"error":"no board"}'); Exit; end;
    PCBServer.PreProcess;
    Rules := TInterfaceList.Create;
    Iter := Board.BoardIterator_Create;
    Iter.AddFilter_ObjectSet(MkSet(eRuleObject));
    Iter.AddFilter_LayerSet(AllLayers);
    Iter.AddFilter_Method(eProcessAll);
    Rule := Iter.FirstPCBObject;
    while Rule <> nil do begin Rules.Add(Rule); Rule := Iter.NextPCBObject; end;
    Board.BoardIterator_Destroy(Iter);
    HatLog('rules: ' + IntToStr(Rules.Count) + ' existing');
    for I := 0 to Rules.Count - 1 do
    begin
        Rule := Rules.Items[I];
        PCBServer.SendMessageToRobots(Rule.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
        if Rule.RuleKind = eRule_Clearance then Rule.Gap := MMsToCoord(0.127);
        if Rule.RuleKind = eRule_MaxMinWidth then
        begin
            Rule.Scope1Expression := 'not (' + POWER_SCOPE + ')';
            SetW(Rule, 0.102, 0.15, 1.0);
        end;
        if Rule.RuleKind = eRule_RoutingViaStyle then
        begin
            Rule.MinHoleWidth := MMsToCoord(0.3); Rule.MaxHoleWidth := MMsToCoord(0.4); Rule.PreferedHoleWidth := MMsToCoord(0.3);
            Rule.MinWidth := MMsToCoord(0.6); Rule.MaxWidth := MMsToCoord(0.8); Rule.PreferedWidth := MMsToCoord(0.6);
        end;
        if (Rule.RuleKind = eRule_AssyTestPointUsage) or (Rule.RuleKind = eRule_TestPointUsage) then Rule.Enabled := False;
        PCBServer.SendMessageToRobots(Rule.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
        Rep.Add(Rule.Name + ' : ' + Rule.Descriptor);
    end;
    HatLog('rules: edited');
    AddWidth(Board, 'Width_Power', POWER_SCOPE, 0.3, 0.5, 2.0, Rep);
    AddWidth(Board, 'Width_CAN', 'InNet(''CAN1_H_C'') or InNet(''CAN1_L_C'') or InNet(''CAN2_H_C'') or InNet(''CAN2_L_C'')', 0.15, 0.2, 0.5, Rep);
    R := PCBServer.PCBRuleFactory(eRule_Clearance);
    R.Name := 'Clearance_Pour';
    R.Scope1Expression := 'InPolygon';
    R.Scope2Expression := 'All';
    R.Gap := MMsToCoord(0.25);
    Board.AddPCBObject(R);
    Rep.Add('added ' + R.Descriptor);
    R := PCBServer.PCBRuleFactory(eRule_PasteMaskExpansion);
    R.Name := 'NoPaste_TagConnect';
    R.Scope1Expression := 'InComponent(''J7'')';
    R.Expansion := MMsToCoord(-0.4);
    Board.AddPCBObject(R);
    Rep.Add('added ' + R.Descriptor);
    PCBServer.PostProcess;
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
