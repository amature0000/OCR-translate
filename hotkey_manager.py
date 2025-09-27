# hotkey_manager.py
import ctypes, threading, time
from ctypes import wintypes

user32   = ctypes.WinDLL('user32', use_last_error=True)

# --- Win32 consts ---
WM_HOTKEY     = 0x0312
PM_REMOVE     = 0x0001
QS_ALLINPUT   = 0x04FF
WAIT_OBJECT_0 = 0x00000000

# Modifiers
MOD_ALT      = 0x0001
MOD_CONTROL  = 0x0002
MOD_SHIFT    = 0x0004
MOD_WIN      = 0x0008
MOD_NOREPEAT = 0x4000

# VK map
VK = {
    **{f"F{i}": 0x6F + i for i in range(1, 25)},  # F1=0x70 ... F24=0x87
    **{c: ord(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    **{str(i): 0x30 + i for i in range(10)},
}

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",    wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam",  wintypes.WPARAM),
        ("lParam",  wintypes.LPARAM),
        ("time",    wintypes.DWORD),
        ("pt",      POINT),
        ("lPrivate", wintypes.DWORD),
    ]

def _parse_combo(combo: str):
    mods = 0
    parts = [p.strip().upper() for p in combo.split("+")]
    key = None
    for p in parts:
        if p in ("CTRL", "CONTROL"): mods |= MOD_CONTROL
        elif p == "SHIFT":           mods |= MOD_SHIFT
        elif p in ("ALT", "MENU"):   mods |= MOD_ALT
        elif p in ("WIN", "META"):   mods |= MOD_WIN
        else:
            key = p
    if key is None:
        raise ValueError("키가 없습니다. 예: 'ctrl+shift+f1'")

    if key.startswith("F") and key[1:].isdigit():
        vk = VK.get(key)
        if vk is None:
            raise ValueError(f"지원하지 않는 함수키: {key}")
    elif len(key) == 1 and key.isalnum():
        vk = VK.get(key.upper())
    else:
        raise ValueError(f"지원하지 않는 키: {key}")
    return mods, vk

class WinHotkeyManager:
    """
    Win32 RegisterHotKey 기반 전역 핫키.
    """
    def __init__(self, on_hotkey, combo: str = "ctrl+shift+f1", norepeat=True, hotkey_id: int = 1):
        self.on_hotkey = on_hotkey
        self.combo = combo
        self.norepeat = norepeat
        self.hotkey_id = hotkey_id
        self._stop_evt = threading.Event()
        self._thread = None
        self._registered = False

    def start(self) -> bool:
        if self._thread:
            return True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        time.sleep(0.05)
        return self._registered

    def stop(self):
        self._stop_evt.set()

    def _worker(self):
        mods, vk = _parse_combo(self.combo)
        if self.norepeat:
            mods |= MOD_NOREPEAT

        if not user32.RegisterHotKey(None, self.hotkey_id, mods, vk):
            self._registered = False
            return
        self._registered = True

        msg = MSG()
        try:
            while not self._stop_evt.is_set():
                ret = user32.MsgWaitForMultipleObjects(0, None, False, 100, QS_ALLINPUT)
                if ret == WAIT_OBJECT_0:
                    while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                        if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
                            try:
                                self.on_hotkey()
                            except Exception:
                                pass
                        user32.TranslateMessage(ctypes.byref(msg))
                        user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    pass
        finally:
            user32.UnregisterHotKey(None, self.hotkey_id)
