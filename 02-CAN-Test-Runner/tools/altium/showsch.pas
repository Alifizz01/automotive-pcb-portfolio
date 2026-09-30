procedure Run;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('SCH', SCH_DOC));
    ResetParameters;
    AddStringParameter('Action', 'Document');
    RunProcess('Sch:Zoom');
    HatResult('{"ok":true}');
end;
