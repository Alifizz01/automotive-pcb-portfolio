procedure Run;
var WS : IWorkSpace; P : IProject; I : Integer; Rep : TStringList;
begin
    LogLines := TStringList.Create;
    Rep := TStringList.Create;
    WS := GetWorkSpace;
    for I := 0 to WS.DM_ProjectCount - 1 do
    begin
        P := WS.DM_Projects(I);
        Rep.Add('project ' + P.DM_ProjectFullPath);
        if Pos('CAN_Sniffer_HAT', P.DM_ProjectFullPath) > 0 then
        begin
            P.DM_RemoveSourceDocument(SCH_DOC);
            Rep.Add('  removed stray SchDoc from sniffer project (not saved)');
        end;
    end;
    for I := 0 to WS.DM_ProjectCount - 1 do
    begin
        P := WS.DM_Projects(I);
        if Pos('CAN_Test_Runner', P.DM_ProjectFullPath) > 0 then
        begin
            P.DM_SetAsCurrentProject;
            Rep.Add('  runner set current; docs=' + IntToStr(P.DM_LogicalDocumentCount));
        end;
    end;
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
