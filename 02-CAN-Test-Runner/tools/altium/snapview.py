"""Focus Altium, fit document (Ctrl+PgDn), grab the document view. usage: snapview.py out.png [nofit]"""
import ctypes, sys, time
from ctypes import wintypes
from PIL import ImageGrab
u = ctypes.windll.user32; hits = []
@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def cb(h, _):
    n = u.GetWindowTextLengthW(h); b = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, b, n + 1)
    if 'Altium Designer' in b.value and u.IsWindowVisible(h): hits.append(h)
    return True
u.EnumWindows(cb, 0); h = hits[0]
u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0)
u.ShowWindow(h, 3); u.SetForegroundWindow(h); time.sleep(0.8)
r = wintypes.RECT(); u.GetWindowRect(h, ctypes.byref(r))
u.SetCursorPos((r.left + 310 + r.right) // 2, (r.top + r.bottom) // 2); time.sleep(0.3)
if 'nofit' not in sys.argv:
    u.keybd_event(0x11, 0, 0, 0); u.keybd_event(0x22, 0, 0, 0); u.keybd_event(0x22, 0, 2, 0); u.keybd_event(0x11, 0, 2, 0)
    time.sleep(1.5)
u.SetCursorPos(r.left + 100, r.bottom - 30); time.sleep(0.8)
ImageGrab.grab((r.left + 312, r.top + 140, r.right - 40, r.bottom - 60), all_screens=True).save(sys.argv[1])
