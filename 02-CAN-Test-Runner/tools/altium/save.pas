procedure Run;
var Doc : IServerDocument;
begin
    LogLines := TStringList.Create;
    Client.OpenDocument('PCB', PCB_DOC);
    Doc := Client.GetDocumentByPath(PCB_DOC);
    Doc.Modified := True;
    Doc.DoFileSave('');
    HatLog('save: done');
    HatResult('{"ok":true}');
end;
