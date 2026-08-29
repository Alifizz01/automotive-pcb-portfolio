r"""Run a full DelphiScript file in Altium, headless.

Altium can execute a loose snippet, but not one that declares its own
variables, and a record type such as TPolySegment has to be declared before it
can be filled in. Since TPolySegment is the only way to write a board outline,
this deploys a real Altium script project and launches it from the command
line, which lifts the restriction.

Usage: arun2.py <script.pas> [timeout_seconds]

The script must define `procedure Run;` and write its result to
C:\Users\Public\altium_hat\hat_result.json. The HatLog and HatResult helpers
in procs.pas do exactly that. Any {{PCB_DOC}} placeholder in the script is
replaced with the real path to the board on the way in.
"""
import io, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dialog_guard import DialogGuard

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "proj")
EXCHANGE = r"C:\Users\Public\altium_hat"
RESULT = os.path.join(EXCHANGE, "hat_result.json")
LOG = os.path.join(EXCHANGE, "hat_log.txt")
ALTIUM = r"C:\Program Files\Altium\AD26\X2.EXE"
PCB_DOC = os.path.join(os.path.dirname(os.path.dirname(HERE)), "hardware",
                       "CAN_Sniffer_HAT.PcbDoc")
os.makedirs(EXCHANGE, exist_ok=True)

src = sys.argv[1]
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
source = io.open(src, encoding="utf-8").read().replace("{{PCB_DOC}}", PCB_DOC)
io.open(os.path.join(PROJ, "HatScript.pas"), "w", encoding="utf-8").write(source)
for f in (RESULT, LOG):
    if os.path.exists(f):
        os.remove(f)

prj = os.path.join(PROJ, "HatScript.PrjScr")
cmd = '"%s" -RScriptingSystem:RunScript(ProjectName="%s"^|ProcName="HatScript>Run")' % (ALTIUM, prj)
guard = DialogGuard()
guard.start()
try:
    subprocess.Popen(cmd, shell=True)
    start = time.time()
    while not os.path.exists(RESULT) and time.time() - start < timeout:
        time.sleep(0.5)
finally:
    guard.stop()

steps = []
if os.path.exists(LOG):
    steps = open(LOG, encoding="utf-8", errors="replace").read().splitlines()
if os.path.exists(RESULT):
    print("RESULT>>>", open(RESULT, encoding="utf-8", errors="replace").read().strip())
else:
    print("RESULT>>> TIMEOUT - no result file")
    print("last step:", steps[-1] if steps else "(no log)")
for s in steps:
    print("  step:", s)
if guard.dismissed:
    print("DIALOGS DISMISSED:", len(guard.dismissed))
