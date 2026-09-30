"""Extract the STM32H563 LQFP100 (non-SMPS) pin map from ST DS14258 Table 14.

Writes stm32h563_lqfp100.txt: 'pin|name|type|alternate functions|additional functions'.
Table 14 pin-number columns (DS14258 Rev 1 p78): WLCSP80-SMPS, LQFP100-SMPS, LQFP144-SMPS,
UFBGA169-SMPS, LQFP176-SMPS, UFBGA176-SMPS, LQFP64, LQFP100, ... -> plain LQFP100 = col 7.
"""
import os, fitz
HERE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(HERE, "..", "docs", "datasheets", "STM32H563.pdf")
rows = {}
d = fitz.open(DS)
for pg in range(77, 107):
    for tb in d[pg].find_tables().tables:
        for r in tb.extract():
            if len(r) < 18:
                continue
            c = [(x or "").replace("\n", " ").strip() for x in r]
            if c[7].isdigit() and c[13] and c[14] in ("I/O", "S", "I", "O"):
                rows.setdefault(int(c[7]), (c[13].replace(" ", ""), c[14], c[17] if len(c) > 17 else "", c[18] if len(c) > 18 else ""))
with open(os.path.join(HERE, "stm32h563_lqfp100.txt"), "w", encoding="utf-8") as f:
    for p in sorted(rows):
        f.write("%d|%s|%s|%s|%s\n" % ((p,) + rows[p]))
print("pins found:", len(rows), "missing:", [p for p in range(1, 101) if p not in rows])
