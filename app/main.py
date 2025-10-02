import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
import mss
from PIL import Image

from ui_app import MainWindow
from ocr_win import windows_ocr
from hotkey_manager import WinHotkeyManager
from settings import SettingsManager
from overlay import OverlayWindow
from llm_api import LLMClient, LLMError

def capture_rect_global(rect) -> Image.Image:
    with mss.mss() as sct:
        raw = sct.grab({"left": rect.x(), "top": rect.y(),
                        "width": rect.width(), "height": rect.height()})
        return Image.frombytes("RGB", (raw.width, raw.height), raw.rgb)

def _prefix_function(s: str) -> list[int]:
    pi = [0] * len(s)
    j = 0
    for i in range(1, len(s)):
        while j and s[i] != s[j]:
            j = pi[j - 1]
        if s[i] == s[j]:
            j += 1
            pi[i] = j
    return pi

class App(QtWidgets.QApplication):
    pass

def main():
    app = App(sys.argv)

    # 1) 설정 로드
    mgr = SettingsManager()
    w = MainWindow(mgr)
    w.setWindowIcon(QtGui.QIcon("icon.ico"))
    w.show()

    # LLM 클라이언트
    llm = LLMClient(mgr)

    # overlay
    w.current_overlay = None

    # 2) OCR 연결
    before_ocr_text = None
    def run_pipeline(rect_global):
        nonlocal before_ocr_text
        if getattr(w, "current_overlay", None):
            try: w.current_overlay.close()
            except Exception: pass
            w.current_overlay = None

        # 오버레이 생성
        overlay = None
        if mgr.use_overlay_layout:
            overlay = OverlayWindow(rect_global, "", font_family=mgr.font_family, font_size=mgr.font_size)
            w.current_overlay = overlay

        # 캡처/OCR/번역
        try:
            img = capture_rect_global(rect_global)
            ocr_text = windows_ocr(img, w.get_lang_tag())
            if not ocr_text:
                return
        except Exception as e:
            w.show_text(f"OCR 실패: {e}")
            return
        
        if mgr.use_scroll_detect and before_ocr_text != None:
            index = 0
            maxlen = len(ocr_text) - 7
            while index <= maxlen:
                temp = ocr_text[index:] + "궯" + before_ocr_text
                temp_len = _prefix_function(temp)[-1]
                if temp_len >= 7: break
                index += 1
                
            if temp_len >= 7:
                ocr_text = before_ocr_text + ocr_text[index+temp_len:]
        before_ocr_text = ocr_text

        try:
            translated = LLMClient(mgr).translate(ocr_text)
            if mgr.use_overlay_layout: overlay.set_text(translated)
            w.show_text(translated + f"\n\n\n### 캡처한 원문:\n{ocr_text}")
        except LLMError as e:
            w.show_text(f"번역 실패: {e}")


    def on_rect_selected(rect_global):
        w.last_selection_rect = QtCore.QRect(rect_global)
        run_pipeline(rect_global)

    w.rectSelected.connect(on_rect_selected)

    # 3) 전역 핫키 등록
    before_hk_key = None
    before_hk_rem_key = None
    hk = None
    hk_rem = None
    def register_hotkey():
        nonlocal hk, hk_rem, before_hk_key, before_hk_rem_key
        ok1 = True
        ok2 = True
        # hotkey 1
        if before_hk_key != mgr.hotkey_combo and mgr.hotkey_combo: 
            ok1 = None
            if hk is not None:
                hk.stop(); hk = None

            def on_hotkey():
                QtCore.QMetaObject.invokeMethod(w, "start_capture", Qt.QueuedConnection)

            hk = WinHotkeyManager(on_hotkey, combo=mgr.hotkey_combo, norepeat=True, hotkey_id=1)
            ok1 = hk.start()
            before_hk_key = mgr.hotkey_combo

        # hotkey 2
        if before_hk_rem_key != mgr.hotkey_rem_combo and mgr.hotkey_rem_combo: 
            ok2 = None
            if hk_rem is not None:
                hk_rem.stop(); hk_rem = None

            def on_hotkey_rem():
                QtCore.QMetaObject.invokeMethod(w, "run_last_rect", Qt.QueuedConnection)

            hk_rem = WinHotkeyManager(on_hotkey_rem, combo=mgr.hotkey_rem_combo, norepeat=True, hotkey_id=2)    
            ok2 = hk_rem.start()
            before_hk_rem_key = mgr.hotkey_rem_combo

        # post processing
        if ok1 and ok2:
            w.statusBar().showMessage(f"전역 핫키 등록: {mgr.hotkey_combo}, {mgr.hotkey_rem_combo}", 4000)
        else:
            reason = hk.last_error
            if not reason: reason = hk_rem.last_error
            w.statusBar().showMessage(f"전역 핫키 등록 실패: {reason}", 6000)
            QtWidgets.QMessageBox.warning(w, "핫키 등록 실패", f"핫키 등록 실패:{reason}")
    register_hotkey()

    # 4) 설정 저장
    def on_settings_updated():
        nonlocal llm
        mgr.load()
        register_hotkey()   # 새 조합으로 재등록
        llm = LLMClient(mgr)# llm 클라이언트 재구성
        
    w.settingsUpdated.connect(on_settings_updated)

    app.aboutToQuit.connect(lambda: (hk and hk.stop(), hk_rem and hk_rem.stop()))
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
