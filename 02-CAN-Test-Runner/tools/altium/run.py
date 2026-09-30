"""Run a DelphiScript body in Altium: prepends hdr.inc, deploys via arun2.py, prints out.txt.
usage: python run.py body.pas [timeout_s]"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
body, timeout = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "300")
out = r"C:\Users\Public\altium_mcp\out.txt"
if os.path.exists(out):
    os.remove(out)
full = os.path.join(HERE, "_full.pas")
with open(full, "w", encoding="utf-8") as f:
    f.write(open(os.path.join(HERE, "hdr.inc"), encoding="utf-8").read())
    f.write(open(body, encoding="utf-8").read())
subprocess.call([sys.executable, os.path.join(HERE, "arun2.py"), full, timeout])
if os.path.exists(out):
    print(open(out, encoding="utf-8", errors="replace").read())
