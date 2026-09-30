# -*- coding: utf-8 -*-
"""Watchdog that dismisses Altium modal dialogs while a script runs.

Altium pops modal dialogs ("No PCB document found in the project.", save
prompts, licence notices). Any one of them blocks the scripting engine
indefinitely, so an automated run appears to hang.

The bridge's own handler misses most of them: it matches only windows titled
exactly Error/Warning/Information/Confirm - Altium commonly titles them "X2" -
and it fires once, six seconds in, sending WM_CLOSE which some dialogs ignore.

This guard instead:
  * matches ANY visible top-level window owned by the Altium process that is
    not the main window, regardless of title;
  * clicks a real button, preferring safe affirmative ones;
  * polls continuously for the whole script run, not once.
"""
import ctypes
import threading
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

BM_CLICK = 0x00F5
WM_CLOSE = 0x0010

# Preference order. "Yes"/"OK" first so a save prompt saves rather than discards;
# destructive-sounding buttons are never clicked (see SKIP).
# Workflow dialogs (the ECO) must be driven, not just dismissed: execute the
# changes first, and only then close. Ordinary prompts fall through to ok/yes.
BUTTON_PREFERENCE = ["route all", "execute changes", "validate changes", "ok", "yes",
                     "continue", "ignore", "close", "no", "cancel"]
# Each button label is clicked at most once per dialog, so "execute changes"
# cannot fire twice and duplicate the import.
_clicked = {}
SKIP = {"don't save", "dont save", "discard", "delete", "abort", "reset"}

DIALOG_CLASSES = {"#32770", "TMessageForm", "TXDialogForm", "TfrmMessage"}


def _text(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _classname(hwnd):
    buf = ctypes.create_unicode_buffer(128)
    user32.GetClassNameW(hwnd, buf, 128)
    return buf.value


def _pid_of(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _altium_pids():
    """PIDs of running Altium (X2.exe) processes."""
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq X2.EXE", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return set()
    pids = set()
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            pids.add(int(parts[1]))
    return pids


def _children(hwnd):
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(child, _):
        found.append(child)
        return True

    user32.EnumChildWindows(hwnd, cb, 0)
    return found


def find_dialogs(pids):
    """Visible top-level windows owned by Altium that are not the main window."""
    hits = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        if _pid_of(hwnd) not in pids:
            return True
        title = _text(hwnd)
        cls = _classname(hwnd)
        # never touch the main application window
        if "Altium Designer" in title:
            return True
        if cls in DIALOG_CLASSES or (user32.GetWindow(hwnd, 4) and title):
            hits.append((hwnd, title, cls))
        return True

    user32.EnumWindows(cb, 0)
    return hits


_sightings = {}
_shot = set()


def dismiss_one(hwnd):
    """Click the best available button.

    A dialog is often enumerable a moment before its buttons exist, so a
    button-less window is left alone for a few sweeps rather than being sent
    WM_CLOSE immediately - WM_CLOSE on a confirm means "No", which is the wrong
    answer for a save prompt.
    """
    buttons = []
    for child in _children(hwnd):
        if not user32.IsWindowVisible(child):
            continue
        cls = _classname(child).lower()
        if "button" in cls:
            if not user32.IsWindowEnabled(child):
                continue          # e.g. Execute Changes before validation passes
            label = _text(child).replace("&", "").strip().lower()
            if label and label not in SKIP:
                buttons.append((child, label))
    done = _clicked.setdefault(hwnd, set())
    for want in BUTTON_PREFERENCE:
        for child, label in buttons:
            if label == want and label not in done:
                done.add(label)
                user32.SendMessageW(child, BM_CLICK, 0, 0)
                return "clicked '%s'" % label
    if buttons:
        child, label = buttons[0]
        user32.SendMessageW(child, BM_CLICK, 0, 0)
        _sightings.pop(hwnd, None)
        return "clicked '%s'" % label
    seen = _sightings.get(hwnd, 0) + 1
    _sightings[hwnd] = seen
    if seen < 5:
        return None                      # give the buttons time to appear
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    _sightings.pop(hwnd, None)
    return "no buttons after %d sweeps, sent WM_CLOSE" % seen


def sweep(pids=None):
    """One pass. Returns a list of human-readable descriptions."""
    pids = pids or _altium_pids()
    if not pids:
        return []
    done = []
    for hwnd, title, cls in find_dialogs(pids):
        body = ""
        for child in _children(hwnd):
            if "static" in _classname(child).lower():
                t = _text(child).strip()
                if t and len(t) > len(body):
                    body = t
        if not body and hwnd not in _shot:
            _shot.add(hwnd)
            try:  # Delphi TMessageForm draws text with a windowless label - screenshot it
                from PIL import ImageGrab
                r = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                ImageGrab.grab((r.left, r.top, r.right, r.bottom), all_screens=True).save(
                    r"C:\Users\Public\altium_mcp\last_dialog.png")
                body = "(see dialog_%d.png)" % int(time.time())
            except Exception as e:
                body = "(capture failed: %s)" % e
        action = dismiss_one(hwnd)
        if action:
            done.append("[%s] %s | %s -> %s" % (cls, title or "(untitled)", body[:90], action))
    return done


class DialogGuard(threading.Thread):
    """Polls for Altium dialogs and dismisses them for the life of a call."""

    def __init__(self, interval=0.5):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop = threading.Event()
        self.dismissed = []

    def run(self):
        pids = _altium_pids()
        last_refresh = time.time()
        while not self._stop.is_set():
            try:
                if time.time() - last_refresh > 10:
                    pids = _altium_pids()
                    last_refresh = time.time()
                for msg in sweep(pids):
                    self.dismissed.append(msg)
                    print("[dialog-guard] " + msg, flush=True)
            except Exception as e:            # never let the guard kill the run
                print("[dialog-guard] error: %s" % e, flush=True)
            self._stop.wait(self.interval)

    def stop(self):
        self._stop.set()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        g = DialogGuard()
        g.start()
        print("watching for Altium dialogs, Ctrl-C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            g.stop()
    else:
        found = find_dialogs(_altium_pids())
        print("altium pids:", _altium_pids())
        print("open dialogs:", len(found))
        for hwnd, title, cls in found:
            print("  [%s] %r" % (cls, title))
        for msg in sweep():
            print("dismissed:", msg)
