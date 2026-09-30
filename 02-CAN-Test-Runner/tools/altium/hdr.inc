const
    LOG_PATH = 'C:\Users\Public\altium_mcp\hat_log.txt';
    RESULT_PATH = 'C:\Users\Public\altium_mcp\hat_result.json';
    OUT_PATH = 'C:\Users\Public\altium_mcp\out.txt';
    PRJ_PATH = 'C:\Users\Nitrox\OneDrive\Desktop\Altium_learn\pcb-portfolio\02-CAN-Test-Runner\hardware\CAN_Test_Runner.PrjPcb';
    SCH_DOC = 'C:\Users\Nitrox\OneDrive\Desktop\Altium_learn\pcb-portfolio\02-CAN-Test-Runner\hardware\CAN_Test_Runner.SchDoc';
    PCB_DOC = 'C:\Users\Nitrox\OneDrive\Desktop\Altium_learn\pcb-portfolio\02-CAN-Test-Runner\hardware\CAN_Test_Runner.PcbDoc';
    LIB_DOC = 'C:\Users\Nitrox\OneDrive\Desktop\Altium_learn\pcb-portfolio\02-CAN-Test-Runner\hardware\CAN_Test_Runner.PcbLib';
var
    LogLines : TStringList;

procedure HatLog(Msg : String);
begin
    LogLines.Add(Msg);
    LogLines.SaveToFile(LOG_PATH);
end;

procedure HatResult(Json : String);
var L : TStringList;
begin
    L := TStringList.Create;
    L.Text := Json;
    L.SaveToFile(RESULT_PATH);
    L.Free;
end;

