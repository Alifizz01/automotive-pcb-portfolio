{ Enumerate every command the PCB server publishes, so board-shape handling can
  be driven by a process whose real name is known rather than guessed. }

const
    LOG_PATH = 'C:\Users\Public\altium_hat\hat_log.txt';
    RESULT_PATH = 'C:\Users\Public\altium_hat\hat_result.json';
    DUMP_PATH = 'C:\Users\Public\altium_hat\pcb_processes.txt';

var
    LogLines : TStringList;

procedure HatLog(Msg : String);
begin
    LogLines.Add(Msg);
    LogLines.SaveToFile(LOG_PATH);
end;

procedure HatResult(Json : String);
var
    L : TStringList;
begin
    L := TStringList.Create;
    try
        L.Text := Json;
        L.SaveToFile(RESULT_PATH);
    finally
        L.Free;
    end;
end;

procedure Run;
var
    Rec    : IServerRecord;
    Proc   : IServerProcess;
    Dump   : TStringList;
    Hits   : TStringList;
    I, J   : Integer;
    Id     : String;
    Params : String;
begin
    LogLines := TStringList.Create;
    HatLog('procs: start');

    Rec := Client.GetServerRecordByName('PCB');
    if Rec = nil then
    begin
        HatResult('{"error":"no PCB server record"}');
        HatLog('procs: PCB SERVER RECORD NIL');
        Exit;
    end;
    HatLog('procs: PCB server record found, commands = ' + IntToStr(Rec.GetCommandCount));

    Dump := TStringList.Create;
    Hits := TStringList.Create;
    for I := 0 to Rec.GetCommandCount - 1 do
    begin
        Proc := Rec.GetCommand(I);
        if Proc = nil then Continue;
        Id := Proc.GetOriginalId;
        Params := '';
        for J := 0 to Proc.GetParameterCount - 1 do
            Params := Params + Proc.GetParameter(J) + ' ';
        Dump.Add(Id + ' | ' + Params);
        if (Pos('Board', Id) > 0) or (Pos('Shape', Id) > 0) or (Pos('Outline', Id) > 0) then
            Hits.Add(Id + ' | ' + Params);
    end;
    Dump.SaveToFile(DUMP_PATH);
    HatLog('procs: dumped ' + IntToStr(Dump.Count) + ' commands, ' +
           IntToStr(Hits.Count) + ' board/shape related');

    HatResult('{"commands": ' + IntToStr(Dump.Count) +
              ', "board_related": ' + IntToStr(Hits.Count) + '}');
    HatLog('procs: done');
end;
