"""Drive Design > Update PCB Document by mouse on the active schematic, guard the ECO dialog."""
import ctypes, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dialog_guard as g
from PIL import ImageGrab
from ctypes import wintypes
SHOT = r'C:/Users/Nitrox/AppData/Local/Temp/claude/C--Windows-System32/ca6e4a38-0961-4006-aa1b-2ffe971cfbef/scratchpad/'
u = ctypes.windll.user32; hits = []
@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def cb(h, _):
    n = u.GetWindowTextLengthW(h); b = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, b, n + 1)
    if 'Altium Designer' in b.value and u.IsWindowVisible(h): hits.append(h)
    return True
u.EnumWindows(cb, 0); h = hits[0]
u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0); u.SetForegroundWindow(h); time.sleep(0.8)
r = wintypes.RECT(); u.GetWindowRect(h, ctypes.byref(r))
def click(x, y):
    u.SetCursorPos(r.left + x, r.top + y); time.sleep(0.25); u.mouse_event(2, 0, 0, 0, 0); u.mouse_event(4, 0, 0, 0, 0)
click(242, 44); time.sleep(1.2)
ImageGrab.grab((r.left, r.top, r.left + 900, r.top + 300), all_screens=True).save(SHOT + 'm3.png')
click(385, 67); time.sleep(2)
def dlg():
    for _ in range(40):
        d = g.find_dialogs(g._altium_pids())
        if d: return d[0][0]
        time.sleep(0.5)
    return None
hd = dlg()
if not hd:
    print("no ECO dialog"); sys.exit(1)
rr = wintypes.RECT(); u.GetWindowRect(hd, ctypes.byref(rr))
def dclick(x, y):
    u.SetCursorPos(rr.left + x, rr.top + y); time.sleep(0.3); u.mouse_event(2, 0, 0, 0, 0); u.mouse_event(4, 0, 0, 0, 0)
dclick(59, 481); time.sleep(6)                 # Validate Changes
ImageGrab.grab((rr.left, rr.top, rr.right, rr.bottom), all_screens=True).save(SHOT + 'eco_validated.png')
dclick(172, 481); time.sleep(25)               # Execute Changes
ImageGrab.grab((rr.left, rr.top, rr.right, rr.bottom), all_screens=True).save(SHOT + 'eco_executed.png')
dclick(1039, 481); time.sleep(2)               # Close
print("ECO driven")
