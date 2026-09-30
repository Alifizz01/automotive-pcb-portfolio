"""Bring Altium to the foreground and send keys. usage: altkeys.py esc|ctrlf3 [n]"""
import ctypes, sys, time
from ctypes import wintypes
u = ctypes.windll.user32
hits = []
@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def cb(h, _):
    n = u.GetWindowTextLengthW(h); b = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, b, n + 1)
    if 'Altium Designer' in b.value and u.IsWindowVisible(h): hits.append(h)
    return True
u.EnumWindows(cb, 0)
h = hits[0]
u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0)   # Alt tap unlocks SetForegroundWindow
u.ShowWindow(h, 9); u.SetForegroundWindow(h); time.sleep(0.6)
ok = u.GetForegroundWindow() == h
what = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
for _ in range(n):
    if what == 'esc':
        u.keybd_event(0x1B, 0, 0, 0); u.keybd_event(0x1B, 0, 2, 0)
    else:
        u.keybd_event(0x11, 0, 0, 0); u.keybd_event(0x72, 0, 0, 0); u.keybd_event(0x72, 0, 2, 0); u.keybd_event(0x11, 0, 2, 0)
    time.sleep(0.3)
print('foreground ok' if ok else 'FOREGROUND FAILED', what, n)
