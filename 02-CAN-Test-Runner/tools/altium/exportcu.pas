procedure Run;
var Board : IPCB_Board; It : IPCB_BoardIterator; P : IPCB_Primitive; Rep : TStringList; N : String;
begin
    LogLines := TStringList.Create; Rep := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eTrackObject, eViaObject, ePadObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    P := It.FirstPCBObject;
    while P <> nil do
    begin
        N := '';
        if P.InNet then N := P.Net.Name;
        if (P.ObjectId = eTrackObject) and (not P.InComponent) and (not P.InPolygon) then
            Rep.Add('T|' + N + '|' + IntToStr(P.Layer) + '|' + IntToStr(P.X1) + '|' + IntToStr(P.Y1) + '|' + IntToStr(P.X2) + '|' + IntToStr(P.Y2) + '|' + IntToStr(P.Width));
        if P.ObjectId = eViaObject then
            Rep.Add('V|' + N + '|' + IntToStr(P.X) + '|' + IntToStr(P.Y) + '|' + IntToStr(P.Size));
        if P.ObjectId = ePadObject then
            Rep.Add('P|' + N + '|' + IntToStr(P.Layer) + '|' + IntToStr(P.X) + '|' + IntToStr(P.Y) + '|' + IntToStr(P.TopXSize) + '|' + IntToStr(P.TopYSize) + '|' + FloatToStr(P.Rotation));
        P := It.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(It);
    Rep.Add('L|' + IntToStr(eTopLayer) + '|' + IntToStr(eBottomLayer) + '|' + IntToStr(eMidLayer1) + '|' + IntToStr(eMidLayer2) + '|' + IntToStr(eMultiLayer));
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
