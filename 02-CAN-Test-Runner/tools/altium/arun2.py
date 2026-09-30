r"""Run a FULL DelphiScript file (with its own var declarations) in Altium.

The bridge's sandbox forbids variable declarations, which makes record types
such as TPolySegment - the only way to write a board outline - impossible.
This deploys a real script project instead and launches it the same way.

Usage: arun2.py <script.pas> [timeout_seconds]
The script must define `procedure Run;` and is expected to write its result to
C:\Users\Public\altium_mcp\hat_result.json (helpers HatLog/HatResult provided
by the caller's own code).
"""
import os, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dialog_guard import DialogGuard

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "proj")
EXCHANGE = r"C:\Users\Public\altium_mcp"
RESULT = os.path.join(EXCHANGE, "hat_result.json")
LOG = os.path.join(EXCHANGE, "hat_log.txt")
ALTIUM = r"C:\Program Files\Altium\AD26\X2.EXE"

src = sys.argv[1]
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
shutil.copyfile(src, os.path.join(PROJ, "HatScript.pas"))
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
