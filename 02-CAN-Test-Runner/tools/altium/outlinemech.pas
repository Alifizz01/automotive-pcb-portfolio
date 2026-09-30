{ Draw the board outline (100 x 66 mm, 3 mm corner radius, as set by newpcb.pas) on
  Mechanical 1 so the Gerber set carries a board profile. Only adds 8 primitives. }
procedure L(Board : IPCB_Board; X1, Y1, X2, Y2 : Double);
var T : IPCB_Track;
begin
    T := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
    T.X1 := MMsToCoord(X1); T.Y1 := MMsToCoord(Y1); T.X2 := MMsToCoord(X2); T.Y2 := MMsToCoord(Y2);
    T.Layer := eMechanical1; T.Width := MMsToCoord(0.1);
    Board.AddPCBObject(T);
    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, T.I_ObjectAddress);
end;

procedure A(Board : IPCB_Board; Cx, Cy, S, E : Double);
var R : IPCB_Arc;
begin
    R := PCBServer.PCBObjectFactory(eArcObject, eNoDimension, eCreate_Default);
    R.XCenter := MMsToCoord(Cx); R.YCenter := MMsToCoord(Cy); R.Radius := MMsToCoord(3);
    R.StartAngle := S; R.EndAngle := E;
    R.Layer := eMechanical1; R.LineWidth := MMsToCoord(0.1);
    Board.AddPCBObject(R);
    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, R.I_ObjectAddress);
end;

procedure Run;
var Board : IPCB_Board; Doc : IServerDocument;
begin
    LogLines := TStringList.Create;
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    if Board = nil then begin HatResult('{"error":"no board"}'); Exit; end;
    PCBServer.PreProcess;
    L(Board, 3, 0, 97, 0);    A(Board, 97, 3, 270, 360);
    L(Board, 100, 3, 100, 63); A(Board, 97, 63, 0, 90);
    L(Board, 97, 66, 3, 66);  A(Board, 3, 63, 90, 180);
    L(Board, 0, 63, 0, 3);    A(Board, 3, 3, 180, 270);
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    Doc := Client.GetDocumentByPath(PCB_DOC);
    Doc.Modified := True;
    HatResult('{"saved":' + BoolToStr(Doc.DoFileSave(''), True) + '}');
end;
