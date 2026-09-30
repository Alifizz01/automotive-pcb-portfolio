const CF = 'C:\Users\Public\altium_mcp\cleanup.txt';
procedure Run;
var Board : IPCB_Board; It : IPCB_BoardIterator; P : IPCB_Primitive; Lines, F : TStringList; Kill : TInterfaceList;
    I, J, TOL : Integer; Hit : Boolean; NT, NV : Integer;
begin
    LogLines := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    Lines := TStringList.Create; Lines.LoadFromFile(CF);
    F := TStringList.Create; F.Delimiter := ' ';
    Kill := TInterfaceList.Create; TOL := 50; NT := 0; NV := 0;
    It := Board.BoardIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eTrackObject, eViaObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);
    P := It.FirstPCBObject;
    while P <> nil do
    begin
        if P.InNet and (not P.InComponent) and (not P.InPolygon) then
        begin
            Hit := False;
            for I := 0 to Lines.Count - 1 do
            begin
                F.DelimitedText := Lines[I];
                if F[1] <> P.Net.Name then Continue;
                if (F[0] = 'V') and (P.ObjectId = eViaObject) then
                    if (Abs(P.X - StrToInt(F[2])) <= TOL) and (Abs(P.Y - StrToInt(F[3])) <= TOL) then begin Hit := True; Lines.Delete(I); NV := NV + 1; Break; end;
                if (F[0] = 'T') and (P.ObjectId = eTrackObject) then
                    if (P.Layer = StrToInt(F[2])) and (Abs(P.X1 - StrToInt(F[3])) <= TOL) and (Abs(P.Y1 - StrToInt(F[4])) <= TOL)
                       and (Abs(P.X2 - StrToInt(F[5])) <= TOL) and (Abs(P.Y2 - StrToInt(F[6])) <= TOL) then begin Hit := True; Lines.Delete(I); NT := NT + 1; Break; end;
            end;
            if Hit then Kill.Add(P);
        end;
        P := It.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(It);
    PCBServer.PreProcess;
    for J := 0 to Kill.Count - 1 do Board.RemovePCBObject(Kill.Items[J]);
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    HatResult('{"tracks_removed": ' + IntToStr(NT) + ', "vias_removed": ' + IntToStr(NV) + ', "unmatched": ' + IntToStr(Lines.Count) + '}');
end;
