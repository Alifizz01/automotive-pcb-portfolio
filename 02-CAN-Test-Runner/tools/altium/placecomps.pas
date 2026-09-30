const
    PLACEF = 'C:\Users\Public\altium_mcp\placement.txt';

procedure Run;
var
    Board : IPCB_Board;
    Lines, F : TStringList;
    Comp  : IPCB_Component;
    I, N  : Integer;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    if Board = nil then begin HatResult('{"error":"no board"}'); Exit; end;
    Lines := TStringList.Create;
    Lines.LoadFromFile(PLACEF);
    F := TStringList.Create;
    F.Delimiter := ' ';
    N := 0;
    PCBServer.PreProcess;
    for I := 0 to Lines.Count - 1 do
    begin
        F.DelimitedText := Lines[I];
        if F.Count < 5 then Continue;
        Comp := Board.GetPcbComponentByRefDes(F[0]);
        if Comp = nil then begin HatLog('MISSING ' + F[0]); Continue; end;
        PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
        if (F[4] = 'B') and (Comp.Layer = eTopLayer) then Comp.FlipComponent;
        Comp.Rotation := StrToInt(F[3]);
        Comp.MoveToXY(MMsToCoord(StrToInt(F[1]) / 1000), MMsToCoord(StrToInt(F[2]) / 1000));
        PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
        N := N + 1;
    end;
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    HatLog('placed ' + IntToStr(N));
    HatResult('{"placed": ' + IntToStr(N) + '}');
end;
