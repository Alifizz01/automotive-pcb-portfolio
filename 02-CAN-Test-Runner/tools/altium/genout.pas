{ Run the project's output jobs: Fabrication (Gerber, NC drill, IPC-2581) and Assembly
  (pick and place, BOM, STEP to files; assembly drawings and schematic prints to PDF). }
procedure RunJob(Job, Medium, Action : String);
begin
    Client.ShowDocument(Client.OpenDocument('OUTPUTJOB', ExtractFilePath(PRJ_PATH) + Job));
    HatLog(Job + ' / ' + Medium);
    ResetParameters;
    AddStringParameter('Action', Action);
    AddStringParameter('ObjectKind', 'OutputBatch');
    AddStringParameter('OutputMedium', Medium);
    AddStringParameter('DisableDialog', 'True');
    AddStringParameter('OpenOutput', 'False');
    if Action = 'PublishToPDF' then RunProcess('WorkspaceManager:Print')
    else RunProcess('WorkspaceManager:GenerateReport');
end;

procedure Run;
begin
    LogLines := TStringList.Create;
    RunJob('Fabrication.OutJob', 'Fabrication', 'Run');
    RunJob('Assembly.OutJob', 'Assembly', 'Run');
    RunJob('Assembly.OutJob', 'PDF', 'PublishToPDF');
    HatResult('{"ok":true}');
end;
