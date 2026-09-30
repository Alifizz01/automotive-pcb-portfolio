"""click.py x y [shot.png]: click at window-relative x,y (full-res), optional screenshot after."""
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
u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0); u.ShowWindow(h, 3); u.SetForegroundWindow(h); time.sleep(0.6)
r = wintypes.RECT(); u.GetWindowRect(h, ctypes.byref(r))
x, y = int(sys.argv[1]), int(sys.argv[2])
u.SetCursorPos(r.left + x, r.top + y); time.sleep(0.2)
u.mouse_event(2, 0, 0, 0, 0); u.mouse_event(4, 0, 0, 0, 0); time.sleep(1.0)
if len(sys.argv) > 3:
    ImageGrab.grab((r.left, r.top, r.right, r.bottom), all_screens=True).save(sys.argv[3])
print('window', r.left, r.top, r.right, r.bottom)
