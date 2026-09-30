procedure Run;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('SCH', SCH_DOC));
    HatLog('eco: sch shown');
    ResetParameters;
    RunProcess('WorkspaceManager:Synchronize');
    HatLog('eco: returned');
    HatResult('{"ok":true}');
end;
