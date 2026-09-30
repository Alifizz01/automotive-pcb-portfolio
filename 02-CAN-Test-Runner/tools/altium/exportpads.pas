procedure Run;
var
    Board : IPCB_Board;
    Iter  : IPCB_BoardIterator;
    Comp  : IPCB_Component;
    Grp   : IPCB_GroupIterator;
    Pad   : IPCB_Pad;
    Rep   : TStringList;
    NetN  : String;
    S     : String;
begin
    LogLines := TStringList.Create;
    Client.OpenDocument('PCB', PCB_DOC);
    Rep := TStringList.Create;
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    Iter := Board.BoardIterator_Create;
    Iter.AddFilter_ObjectSet(MkSet(ePadObject));
    Iter.AddFilter_LayerSet(AllLayers);
    Iter.AddFilter_Method(eProcessAll);
    Pad := Iter.FirstPCBObject;
    while Pad <> nil do
    begin
        NetN := '';
        if Pad.InNet then NetN := Pad.Net.Name;
        S := 'FREE';
        if Pad.InComponent then S := Pad.Component.Name.Text;
        Rep.Add(S + '|' + Pad.Name + '|' + NetN + '|' + FloatToStr(CoordToMMs(Pad.X)) + '|' + FloatToStr(CoordToMMs(Pad.Y)) + '|' +
                FloatToStr(CoordToMMs(Pad.TopXSize)) + '|' + FloatToStr(CoordToMMs(Pad.TopYSize)) + '|' + FloatToStr(Pad.Rotation) + '|' +
                Layer2String(Pad.Layer) + '|' + FloatToStr(CoordToMMs(Pad.HoleSize)) + '|' + IntToStr(Pad.TopShape));
        Pad := Iter.NextPCBObject;
    end;
    Board.BoardIterator_Destroy(Iter);
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
end;
