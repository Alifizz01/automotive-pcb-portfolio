procedure Dump(Srv : String; Rep : TStringList);
var Rec : IServerRecord; Proc : IServerProcess; I, J : Integer; P : String;
begin
    Rec := Client.GetServerRecordByName(Srv);
    if Rec = nil then begin Rep.Add(Srv + ' NIL'); Exit; end;
    for I := 0 to Rec.GetCommandCount - 1 do
    begin
        Proc := Rec.GetCommand(I);
        if Proc = nil then Continue;
        P := '';
        for J := 0 to Proc.GetParameterCount - 1 do P := P + Proc.GetParameter(J) + ' ';
        Rep.Add(Srv + ':' + Proc.GetOriginalId + ' | ' + P);
    end;
end;

procedure Run;
var Rep : TStringList;
begin
    LogLines := TStringList.Create;
    Rep := TStringList.Create;
    Dump('WorkspaceManager', Rep); Dump('SCH', Rep); Dump('PCB', Rep);
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
