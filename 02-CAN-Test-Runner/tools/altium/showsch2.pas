procedure Run;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('SCH', SCH_DOC));
    HatResult('{"ok":true}');
end;
