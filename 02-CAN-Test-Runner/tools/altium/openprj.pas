procedure Run;
begin
    LogLines := TStringList.Create;
    ResetParameters;
    AddStringParameter('ObjectKind', 'Project');
    AddStringParameter('FileName', PRJ_PATH);
    RunProcess('WorkspaceManager:OpenObject');
    HatLog('project opened');
    Client.ShowDocument(Client.OpenDocument('SCH', SCH_DOC));
    HatResult('{"ok":true}');
end;
