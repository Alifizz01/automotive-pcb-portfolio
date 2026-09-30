{ Add Altium's standard Fabrication and Assembly output jobs to the project and open them. }
procedure Run;
var WS : IWorkspace; Prj : IProject; I : Integer; Dir : String;
begin
    LogLines := TStringList.Create;
    Dir := ExtractFilePath(PRJ_PATH);
    WS := GetWorkspace;
    Prj := nil;
    for I := 0 to WS.DM_ProjectCount - 1 do
        if SameText(WS.DM_Projects(I).DM_ProjectFullPath, PRJ_PATH) then Prj := WS.DM_Projects(I);
    if Prj = nil then begin HatResult('{"error":"project not open"}'); Exit; end;
    Prj.DM_AddSourceDocument(Dir + 'Fabrication.OutJob');
    Prj.DM_AddSourceDocument(Dir + 'Assembly.OutJob');
    Client.ShowDocument(Client.OpenDocument('OUTPUTJOB', Dir + 'Fabrication.OutJob'));
    Client.ShowDocument(Client.OpenDocument('OUTPUTJOB', Dir + 'Assembly.OutJob'));
    HatResult('{"ok":true}');
end;
