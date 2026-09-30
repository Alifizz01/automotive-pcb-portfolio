procedure Run;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    HatLog('drc: start');
    ResetParameters;
    RunProcess('PCB:DesignRuleCheck');
    HatLog('drc: done');
    HatResult('{"ok":true}');
end;
