# -*- coding: utf-8 -*-
"""Add the MPN column to Altium's BOM export (the template BOM has no MPN column).

Reads  hardware/Project Outputs for CAN_Test_Runner/BOM/Bill of Materials-CAN_Test_Runner.xlsx
Writes hardware/Project Outputs for CAN_Test_Runner/BOM/BOM_CAN_Test_Runner.csv
Fails if a designator is missing on either side, or one BOM line mixes two MPNs.
"""
import csv
import os
import sys
import contextlib
import io
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import design

OUT = os.path.join(HERE, "..", "hardware", "Project Outputs for CAN_Test_Runner", "BOM")
MPN = {ref: mpn for ref, sym, fp, comment, mpn in design.PARTS}

ws = openpyxl.load_workbook(os.path.join(OUT, "Bill of Materials-CAN_Test_Runner.xlsx"), data_only=True).active
rows = [r for r in ws.iter_rows(values_only=True) if any(r)]
head, body = list(rows[0]), rows[1:]
di = head.index("Designator")
seen, out = set(), []
for r in body:
    refs = [d.strip() for d in str(r[di]).split(",")]
    mpns = {MPN.get(d, "?") for d in refs}
    if len(mpns) != 1 or "?" in mpns:
        raise SystemExit("line %s: MPNs %s" % (r[di], mpns))
    seen.update(refs)
    out.append(list(r) + [mpns.pop()])
if seen != set(MPN):
    raise SystemExit("designators differ: BOM-only %s, design-only %s" % (seen - set(MPN), set(MPN) - seen))

with open(os.path.join(OUT, "BOM_CAN_Test_Runner.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(head + ["MPN"])
    w.writerows(out)
print("BOM: %d lines, %d parts, every designator matched to design.py" % (len(out), len(seen)))
