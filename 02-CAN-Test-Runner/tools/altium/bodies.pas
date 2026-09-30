{ Real 3D models (KiCad packages3D STEP, hardware/3D_Models) on every component.
  Idempotent: existing bodies are removed first.
  Mode 'O' : model origin = footprint origin + (Dx,Dy) local  (KiCad and our origin agree)
  Mode 'B' : model XY bounding-box centre on the local point (Dx,Dy)
  BT1 sits on the bottom: flipped to top, body added, flipped back, position restored. }
const
    M3D = 'C:\Users\Nitrox\OneDrive\Desktop\Altium_learn\pcb-portfolio\02-CAN-Test-Runner\hardware\3D_Models\';

function BR(Body : IPCB_ComponentBody) : String;
begin
    Result := FloatToStr(CoordToMMs(Body.BoundingRectangle.Left)) + ',' + FloatToStr(CoordToMMs(Body.BoundingRectangle.Bottom))
        + ' .. ' + FloatToStr(CoordToMMs(Body.BoundingRectangle.Right)) + ',' + FloatToStr(CoordToMMs(Body.BoundingRectangle.Top));
end;

procedure AddBody(Board : IPCB_Board; Comp : IPCB_Component; FileName : String; ExtraRot : Double;
                  Mode : String; Dx, Dy : Double; Rep : TStringList);
var
    Body : IPCB_ComponentBody;
    Model: IPCB_Model;
    A : Double;
    Tx, Ty : Integer;
    Bx, By : Integer;
begin
    Body := PCBServer.PCBObjectFactory(eComponentBodyObject, eNoDimension, eCreate_Default);
    Model := Body.ModelFactory_FromFilename(M3D + FileName, False);
    Body.SetState_FromModel;
    Body.Model := Model;
    Body.Layer := eMechanical13;
    Rep.Add(Comp.Name.Text + ' raw BR ' + BR(Body));
    Body.RotateAroundXY(0, 0, Comp.Rotation + ExtraRot);
    A := Comp.Rotation * PI / 180;
    Tx := Comp.X + Round(MMsToCoord(Dx * Cos(A) - Dy * Sin(A)));
    Ty := Comp.Y + Round(MMsToCoord(Dx * Sin(A) + Dy * Cos(A)));
    if Mode = 'B' then
    begin
        Bx := (Body.BoundingRectangle.Left + Body.BoundingRectangle.Right) div 2;
        By := (Body.BoundingRectangle.Bottom + Body.BoundingRectangle.Top) div 2;
        Body.MoveByXY(Tx - Bx, Ty - By);
    end
    else
        Body.MoveByXY(Tx, Ty);
    Board.AddPCBObject(Body);
    Comp.AddPCBObject(Body);
    PCBServer.SendMessageToRobots(Board.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Body.I_ObjectAddress);
    Rep.Add(Comp.Name.Text + ' ' + Comp.Pattern + ' <- ' + FileName + ' h=' + FloatToStr(CoordToMMs(Body.OverallHeight))
        + ' at ' + FloatToStr(CoordToMMs(Comp.X)) + ',' + FloatToStr(CoordToMMs(Comp.Y)) + ' BR ' + BR(Body));
end;

procedure Place(Board : IPCB_Board; Comp : IPCB_Component; Rep : TStringList);
var P : String;
begin
    P := Comp.Pattern;
    if (P = 'R0603') or (P = 'C0603') or (P = 'R0805') or (P = 'C0805') or (P = 'C1210')
        or (P = 'SOD123W') or (P = 'SOD128') or (P = 'SMB') then AddBody(Board, Comp, P + '.step', 0, 'O', 0, 0, Rep)
    else if P = 'LED0603' then AddBody(Board, Comp, 'LED0603.step', 180, 'O', 0, 0, Rep)
    else if P = 'L_WE-LQS-6045' then AddBody(Board, Comp, 'L6045.step', 0, 'B', 0, 0, Rep)
    else if P = 'L_WE-LQS-2520' then AddBody(Board, Comp, 'L2520.step', 0, 'O', 0, 0, Rep)
    else if P = 'L_WE-MAPI-2016' then AddBody(Board, Comp, 'L2016.step', 0, 'B', 0, 0, Rep)
    else if (P = 'SOT-23-3') or (P = 'SC-70-3') or (P = 'WSON-8_DSG') or (P = 'WSON-6_DRV') or (P = 'WSON-6_DSE') then
        AddBody(Board, Comp, P + '.step', 0, 'O', 0, 0, Rep)
    else if P = 'SOIC-8_150MIL' then AddBody(Board, Comp, 'SOIC-8.step', 0, 'O', 0, 0, Rep)
    else if P = 'SOIC-8_DDA_PowerPAD' then AddBody(Board, Comp, 'SOIC-8-EP.step', 0, 'O', 0, 0, Rep)
    else if P = 'VSON-10_DLA' then AddBody(Board, Comp, 'VSON10.step', 0, 'O', 0, 0, Rep)
    else if P = 'VQFN-16_3x3_4MX' then AddBody(Board, Comp, 'VQFN-16.step', 0, 'O', 0, 0, Rep)
    else if P = 'LQFP-100_14x14' then AddBody(Board, Comp, 'LQFP-100.step', 0, 'O', 0, 0, Rep)
    else if P = 'XTAL_3225_4P' then AddBody(Board, Comp, 'XTAL3225.step', 0, 'O', 0, 0, Rep)
    else if P = 'RV-3028-C7' then AddBody(Board, Comp, 'RV3028.step', 90, 'B', 0, 0, Rep)
    else if P = 'USB-C_GCT_USB4105' then AddBody(Board, Comp, 'USB4105.step', 0, 'O', 0, 0, Rep)
    else if P = 'MICROSD_HIROSE_DM3AT' then AddBody(Board, Comp, 'DM3AT.step', 0, 'O', 0, 0, Rep)
    else if P = 'DSUB-9_M_WR-DSUB_618009231221' then AddBody(Board, Comp, 'DSUB9.step', 0, 'O', -5.54, 1.42, Rep)
    else if P = 'FPC_10P_0.5_WR-FPC_687110149022' then AddBody(Board, Comp, 'FPC10.step', 0, 'B', 0, -1.65, Rep)
    else if P = 'JST_PH_S3B-PH-SM4-TB' then AddBody(Board, Comp, 'JST_PH3.step', 0, 'B', 0, -1.9, Rep)
    else if P = 'BATT_KEYSTONE_3000_12MM' then AddBody(Board, Comp, 'KS3000.step', 0, 'B', 0, 0, Rep)
    else if P = 'SW_WS-TASV_6x6' then AddBody(Board, Comp, 'SW6x6.step', 0, 'O', 0, 0, Rep)
    else Rep.Add(Comp.Name.Text + ' ' + P + ' : no model');
end;

procedure Run;
var
    Board : IPCB_Board;
    Iter  : IPCB_BoardIterator;
    Comp  : IPCB_Component;
    Prim  : IPCB_Primitive;
    Grp   : IPCB_GroupIterator;
    Comps, Kill : TInterfaceList;
    Rep   : TStringList;
    I, X0, Y0 : Integer;
    R0    : Double;
begin
    LogLines := TStringList.Create;
    Rep := TStringList.Create;
    Client.ShowDocument(Client.OpenDocument('PCB', PCB_DOC));
    Board := PCBServer.GetPCBBoardByPath(PCB_DOC);
    if Board = nil then begin HatResult('{"error":"no board"}'); Exit; end;
    Comps := TInterfaceList.Create;
    Kill := TInterfaceList.Create;
    Iter := Board.BoardIterator_Create;
    Iter.AddFilter_ObjectSet(MkSet(eComponentObject));
    Iter.AddFilter_LayerSet(AllLayers);
    Iter.AddFilter_Method(eProcessAll);
    Comp := Iter.FirstPCBObject;
    while Comp <> nil do begin Comps.Add(Comp); Comp := Iter.NextPCBObject; end;
    Board.BoardIterator_Destroy(Iter);
    PCBServer.PreProcess;
    for I := 0 to Comps.Count - 1 do
    begin
        Comp := Comps.Items[I];
        Grp := Comp.GroupIterator_Create;
        Grp.AddFilter_ObjectSet(MkSet(eComponentBodyObject));
        Prim := Grp.FirstPCBObject;
        while Prim <> nil do begin Kill.Add(Prim); Prim := Grp.NextPCBObject; end;
        Comp.GroupIterator_Destroy(Grp);
    end;
    for I := 0 to Kill.Count - 1 do
    begin
        Prim := Kill.Items[I];
        Prim.Component.RemovePCBObject(Prim);
        Board.RemovePCBObject(Prim);
    end;
    Rep.Add('removed ' + IntToStr(Kill.Count) + ' old bodies');
    for I := 0 to Comps.Count - 1 do
    begin
        Comp := Comps.Items[I];
        HatLog('bodies: ' + Comp.Name.Text);
        if Comp.Pattern = 'BATT_KEYSTONE_1042_18650' then
        begin
            X0 := Comp.X; Y0 := Comp.Y; R0 := Comp.Rotation;
            Rep.Add('BT1 before: ' + Layer2String(Comp.Layer) + ' rot ' + FloatToStr(R0));
            PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
            Comp.FlipComponent;
            PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
            AddBody(Board, Comp, 'KS1042.step', 0, 'B', 0, 0, Rep);
            PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_BeginModify, c_NoEventData);
            Comp.FlipComponent;
            if Comp.Rotation <> R0 then Comp.Rotation := R0;
            Comp.MoveToXY(X0, Y0);
            PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast, PCBM_EndModify, c_NoEventData);
            Rep.Add('BT1 after: ' + Layer2String(Comp.Layer) + ' rot ' + FloatToStr(Comp.Rotation)
                + ' dXY ' + FloatToStr(CoordToMMs(Comp.X - X0)) + ',' + FloatToStr(CoordToMMs(Comp.Y - Y0)));
        end
        else
            Place(Board, Comp, Rep);
    end;
    PCBServer.PostProcess;
    Board.ViewManager_FullUpdate;
    Rep.SaveToFile(OUT_PATH);
    HatResult('{"ok":true}');
    HatLog('bodies: done');
end;
