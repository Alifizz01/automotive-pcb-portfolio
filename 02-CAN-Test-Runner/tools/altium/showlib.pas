procedure Run;
var Doc : IServerDocument; Lib : IPCB_Library; It : IPCB_LibraryIterator; C : IPCB_LibComponent;
begin
    LogLines := TStringList.Create;
    Doc := Client.OpenDocument('PCBLIB', LIB_DOC); Client.ShowDocument(Doc);
    Lib := PCBServer.GetCurrentPCBLibrary;
    It := Lib.LibraryIterator_Create; It.SetState_FilterAll;
    C := It.FirstPCBObject;
    while C <> nil do
    begin
        if C.Name = 'USB-C_GCT_USB4105' then Lib.SetBoardToComponentByName(C.Name);
        C := It.NextPCBObject;
    end;
    Lib.LibraryIterator_Destroy(It);
    Lib.Board.ViewManager_FullUpdate;
    ResetParameters; AddStringParameter('Action', 'All'); RunProcess('PCB:Zoom');
    HatResult('{"ok":true}');
end;
