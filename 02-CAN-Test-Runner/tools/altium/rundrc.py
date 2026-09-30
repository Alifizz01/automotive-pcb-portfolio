"""Run Altium's DRC WITHOUT the dialog guard (it closes the DRC dialog before it runs),
wait for a fresh report, print violations."""
import os, shutil, subprocess, time
DRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware",
                   "Project Outputs for CAN_Test_Runner", "Design Rule Check - CAN_Test_Runner.drc")
before = os.path.getmtime(DRC) if os.path.exists(DRC) else 0
shutil.copyfile("hdr.inc", "_full.pas")
open("_full.pas", "a").write(open("drc.pas").read())
shutil.copyfile("_full.pas", os.path.join("proj", "HatScript.pas"))
prj = os.path.abspath(os.path.join("proj", "HatScript.PrjScr"))
subprocess.Popen(r'"C:\Program Files\Altium\AD26\X2.EXE" -RScriptingSystem:RunScript(ProjectName="%s"^|ProcName="HatScript>Run")' % prj, shell=True)
t = time.time()
while time.time() - t < 120 and (not os.path.exists(DRC) or os.path.getmtime(DRC) <= before):
    time.sleep(1)
time.sleep(1)
print("fresh report" if os.path.getmtime(DRC) > before else "NO NEW REPORT")
for l in open(DRC, encoding="utf-8", errors="replace"):
    if "Violation" in l or l.startswith("Time "):
        print(l.rstrip())
