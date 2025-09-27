# main.py
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
import mss
from PIL import Image

from ui_app import MainWindow
from ocr_win import windows_ocr_sync
from hotkey_manager import WinHotkeyManager
from settings import SettingsManager

def capture_rect_global(rect) -> Image.Image:
    with mss.mss() as sct:
        raw = sct.grab({"left": rect.x(), "top": rect.y(),
                        "width": rect.width(), "height": rect.height()})
        return Image.frombytes("RGB", (raw.width, raw.height), raw.rgb)

class App(QtWidgets.QApplication):
    pass

def main():
    app = App(sys.argv)

    # 1) 설정 로드
    mgr = SettingsManager()
    w = MainWindow(mgr)
    w.show()

    # 2) OCR 연결
    def on_rect_selected(rect_global):
        img = capture_rect_global(rect_global)
        try:
            result = windows_ocr_sync(img, w.get_lang_tag())
        except Exception as e:
            w.show_text(f"OCR 실패: {e}")
            return
        lines = [ln.text for ln in result.lines]
        w.show_text("\n".join(lines).strip() or "(인식된 텍스트 없음)")
    w.rectSelected.connect(on_rect_selected)

    # 3) 전역 핫키 등록 (설정 값 사용)
    hk = None
    def register_hotkey():
        nonlocal hk
        # 기존 것 정리
        if hk is not None:
            hk.stop()
            hk = None
        def on_hotkey():
            QtCore.QMetaObject.invokeMethod(w, "start_capture", Qt.QueuedConnection)
        hk = WinHotkeyManager(on_hotkey, combo=mgr.hotkey_combo, norepeat=True, hotkey_id=1)
        ok = hk.start()
        w.statusBar().showMessage(
            f"전역 핫키 {'등록' if ok else '실패'}: {mgr.hotkey_combo}", 4000
        )
    register_hotkey()

    # 4) 설정 저장/적용 시 핫키 재등록
    def on_settings_updated():
        mgr.load()          # 파일에서 재반영(다른 프로세스와 공유 고려)
        register_hotkey()   # 새 조합으로 재등록
    w.settingsUpdated.connect(on_settings_updated)

    app.aboutToQuit.connect(lambda: hk and hk.stop())
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
