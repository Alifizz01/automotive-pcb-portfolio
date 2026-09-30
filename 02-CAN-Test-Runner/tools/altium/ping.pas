procedure Run;
begin
    LogLines := TStringList.Create;
    HatLog('ping');
    HatResult('{"ping":1}');
end;
