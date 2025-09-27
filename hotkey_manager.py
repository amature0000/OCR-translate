# hotkey_manager.py
import ctypes, threading, time
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)

WM_HOTKEY     = 0x0312
PM_REMOVE     = 0x0001
QS_ALLINPUT   = 0x04FF
WAIT_OBJECT_0 = 0x00000000

MOD_ALT      = 0x0001
MOD_CONTROL  = 0x0002
MOD_SHIFT    = 0x0004
MOD_WIN      = 0x0008
MOD_NOREPEAT = 0x4000

# --- 기본 VK ---
VK = {
    **{f"F{i}": 0x6F + i for i in range(1, 25)},  # F1=0x70 ... F24=0x87
    **{c: ord(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},  # A..Z
    **{str(i): 0x30 + i for i in range(10)},             # 0..9
}

# --- 확장 VK (일반적으로 많이 쓰는 키들) ---
EXTRA_VK = {
    # 제어키
    "SPACE": 0x20, "TAB": 0x09, "ENTER": 0x0D, "RETURN": 0x0D,
    "ESC": 0x1B, "ESCAPE": 0x1B, "BACKSPACE": 0x08,
    # 네비게이션/편집
    "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    "INSERT": 0x2D, "DELETE": 0x2E, "HOME": 0x24, "END": 0x23,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22,
    "PRINTSCREEN": 0x2C, "PRTSC": 0x2C,
    # OEM/기호키 (미국 키보드 기준)
    "OEM_MINUS": 0xBD, "OEM_PLUS": 0xBB, "OEM_1": 0xBA,  # ;:
    "OEM_2": 0xBF,   # /?
    "OEM_3": 0xC0,   # `~
    "OEM_4": 0xDB,   # [{
    "OEM_5": 0xDC,   # \|
    "OEM_6": 0xDD,   # ]}
    "OEM_7": 0xDE,   # '"
    # 별칭(사람이 입력하는 문자 → OEM 키로 매핑)
    "-": 0xBD, "=": 0xBB, ";": 0xBA, "/": 0xBF, "`": 0xC0,
    "[": 0xDB, "\\": 0xDC, "]": 0xDD, "'": 0xDE,
}

# 오류 코드 → 메시지
ERROR_HOTKEY_ALREADY_REGISTERED = 1409

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

def validate_combo(combo: str):
    """
    콤보 문자열을 검증하고 (mods, vk) 반환.
    실패 시 (None, None, reason) 반환.
    """
    try:
        mods, vk = _parse_combo(combo)
        return mods, vk, None
    except ValueError as e:
        return None, None, str(e)

def _parse_combo(combo: str):
    if not combo:
        raise ValueError("빈 문자열입니다.")
    parts_raw = [p for p in combo.replace(" ", "").split("+") if p]
    parts = [p.upper() for p in parts_raw]
    mods = 0
    key = None
    for p in parts:
        if p in ("CTRL", "CONTROL"): mods |= MOD_CONTROL
        elif p == "SHIFT":           mods |= MOD_SHIFT
        elif p in ("ALT", "MENU"):   mods |= MOD_ALT
        elif p in ("WIN", "META"):   mods |= MOD_WIN
        else:
            key = p
    if key is None:
        raise ValueError("키가 없습니다. 예: ctrl+shift+f1")

    # 사전에 있는지 검색 순서: VK → EXTRA_VK → F-패턴 → 한 글자 영숫자
    if key in VK:
        vk = VK[key]
    elif key in EXTRA_VK:
        vk = EXTRA_VK[key]
    elif key.startswith("F") and key[1:].isdigit():
        vk = VK.get(key)
        if vk is None:
            raise ValueError(f"지원하지 않는 함수키: {key}")
    elif len(key) == 1 and key.isalnum():
        vk = VK.get(key)
        if vk is None:
            raise ValueError(f"지원하지 않는 키: {key}")
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
        self.last_error: str | None = None

    def start(self) -> bool:
        # 스레드 띄우기 전에 combo 형식 사전 검증
        try:
            _ = _parse_combo(self.combo)
        except ValueError as e:
            self.last_error = f"형식 오류: {e}"
            return False

        if self._thread:
            return True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        time.sleep(0.05)
        return self._registered

    def stop(self):
        self._stop_evt.set()

    def _worker(self):
        try:
            mods, vk = _parse_combo(self.combo)
            if self.norepeat:
                mods |= MOD_NOREPEAT

            if not user32.RegisterHotKey(None, self.hotkey_id, mods, vk):
                err = ctypes.get_last_error()
                if err == ERROR_HOTKEY_ALREADY_REGISTERED:
                    self.last_error = "이미 다른 프로그램에서 사용 중인 핫키 조합입니다."
                else:
                    self.last_error = f"RegisterHotKey 실패 (WinError {err})"
                self._registered = False
                return

            self._registered = True
            msg = MSG()
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
        finally:
            user32.UnregisterHotKey(None, self.hotkey_id)
