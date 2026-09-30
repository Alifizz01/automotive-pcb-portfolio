{ Clear DRC error markers and fit the whole board in the current (3D) view. }
procedure Run;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    ResetParameters;
    RunProcess('PCB:ResetAllErrorMarkers');
    ResetParameters;
    AddStringParameter('Action', 'Board');
    RunProcess('PCB:Zoom');
    HatResult('{"ok":true}');
end;
