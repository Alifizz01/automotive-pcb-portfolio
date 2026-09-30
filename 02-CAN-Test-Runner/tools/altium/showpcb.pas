procedure Run;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    ResetParameters; AddStringParameter('Action', 'Board'); RunProcess('PCB:Zoom');
    HatResult('{"ok":true}');
end;
