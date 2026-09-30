function CountComps(Path : String) : String;
var B : IPCB_Board; It : IPCB_BoardIterator; C : IPCB_Component; N : Integer;
begin
    B := PCBServer.GetPCBBoardByPath(Path);
    if B = nil then begin Result := 'not open'; Exit; end;
    N := 0;
    It := B.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eComponentObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    C := It.FirstPCBObject;
    while C <> nil do begin N := N + 1; C := It.NextPCBObject; end;
    B.BoardIterator_Destroy(It);
    Result := IntToStr(N);
end;

procedure Run;
var Rep : TStringList; D : IServerDocument;
begin
    LogLines := TStringList.Create;
    Client.OpenDocument('PCB', PCB_DOC);
    Rep := TStringList.Create;
    Rep.Add('runner board comps: ' + CountComps(PCB_DOC));
    Rep.Add('sniffer board comps: ' + CountComps('C:\Users\Nitrox\OneDrive\Desktop\Altium_learn\CAN-Sniffer-HAT\PCB_Project\CAN_Sniffer_HAT.PcbDoc'));
    D := Client.GetDocumentByPath('C:\Users\Nitrox\OneDrive\Desktop\Altium_learn\CAN-Sniffer-HAT\PCB_Project\CAN_Sniffer_HAT.PcbDoc');
    if D <> nil then Rep.Add('sniffer pcb modified: ' + BoolToStr(D.Modified, True));
    D := Client.GetDocumentByPath(PCB_DOC);
    if D <> nil then Rep.Add('runner pcb modified: ' + BoolToStr(D.Modified, True));
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
