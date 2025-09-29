from typing import Optional
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from settings import SettingsManager, ASSET_FONTS_DIR
import os
import html

# ---- 캡처 오버레이 ----
class SelectionOverlay(QtWidgets.QWidget):
    selected = QtCore.pyqtSignal(QtCore.QRect)   # 글로벌 좌표
    cancelled = QtCore.pyqtSignal()

    def __init__(self, monitor_geo: QtCore.QRect):
        super().__init__(parent=None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)
        self.monitor_geo = monitor_geo
        self.setGeometry(monitor_geo)
        self._start: Optional[QtCore.QPoint] = None
        self._end: Optional[QtCore.QPoint] = None

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 120))
        if self._start and self._end:
            rect = self._rect_local()
            p.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0, 220), 2))
            p.setBrush(QtGui.QBrush(QtGui.QColor(0, 255, 0, 60)))
            p.drawRect(rect)

    def mousePressEvent(self, e): self._start = self._end = e.pos(); self.update()
    def mouseMoveEvent(self, e):  self._end = e.pos(); self.update()
    def mouseReleaseEvent(self, e):
        self._end = e.pos()
        rect_local = self._rect_local()
        if rect_local.width() >= 2 and rect_local.height() >= 2:
            rect_global = QtCore.QRect(
                rect_local.x() + self.monitor_geo.x(),
                rect_local.y() + self.monitor_geo.y(),
                rect_local.width(), rect_local.height()
            )
            self.selected.emit(rect_global)
        else:
            self.cancelled.emit()
        self.close()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.cancelled.emit(); self.close()

    def _rect_local(self) -> QtCore.QRect:
        x1, y1 = self._start.x(), self._start.y()
        x2, y2 = self._end.x(), self._end.y()
        return QtCore.QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))


# ---- 환경설정 ----
class SettingsDialog(QtWidgets.QDialog):
    settingsSaved = QtCore.pyqtSignal()

    def __init__(self, manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.mgr = manager
        self.setWindowTitle("환경설정")
        self.resize(640, 520)

        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        lay = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget(); lay.addWidget(self.tabs)

        # Tab 1: 핫키
        self.tab_hotkey = QtWidgets.QWidget(); self.tabs.addTab(self.tab_hotkey, "핫키")
        self._build_tab_hotkey()

        # Tab 2: 프롬프트
        self.tab_prompt = QtWidgets.QWidget(); self.tabs.addTab(self.tab_prompt, "프롬프트")
        self._build_tab_prompt()

        # Tab 3: API
        self.tab_api = QtWidgets.QWidget(); self.tabs.addTab(self.tab_api, "API")
        self._build_tab_api()

        # Tab 4: 폰트
        self.tab_display = QtWidgets.QWidget(); self.tabs.addTab(self.tab_display, "폰트")
        self._build_tab_display()

        # Tab 5: 정보
        self.tab_info = QtWidgets.QWidget(); self.tabs.addTab(self.tab_info, "정보")
        self._build_tab_info()

        # 버튼
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel, parent=self
        )

        self.btn_reset = QtWidgets.QPushButton("초기화")
        btns.addButton(self.btn_reset, QtWidgets.QDialogButtonBox.ResetRole)
        self.btn_reset.clicked.connect(self._reset_to_defaults)

        btns.accepted.connect(self._save_and_close)  # Save
        btns.rejected.connect(self.reject)  # Cancel
        lay.addWidget(btns)

        self._load_values()

    # --- 핫키 ---
    def _build_tab_hotkey(self):
        form = QtWidgets.QFormLayout(self.tab_hotkey)

        self.edt_hotkey = QtWidgets.QLineEdit()
        self.edt_hotkey.setPlaceholderText("예: ctrl+shift+f1 / alt+f12 / ctrl+s")
        self.lbl_hotkey_hint = QtWidgets.QLabel("형식: (커맨드 키) + (키). 예) ctrl+shift+f1, ctrl+g")
        self.lbl_hotkey_hint.setStyleSheet("color: gray;")

        form.addRow("핫키 설정", self.edt_hotkey)
        form.addRow(self.lbl_hotkey_hint)

    def _get_hotkey_combo_from_ui(self) -> str:
        return self.edt_hotkey.text().strip()

    # --- 프롬프트 ---
    def _build_tab_prompt(self):
        lay = QtWidgets.QVBoxLayout(self.tab_prompt)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)
        lbl_head = QtWidgets.QLabel("LLM에 다음과 같이 전달됩니다.")

        # 1) Commands
        lbl_cmd = QtWidgets.QLabel("Commands:")
        lbl_cmd.setStyleSheet("font-weight: 600;")
        self.txt_commands = QtWidgets.QPlainTextEdit()
        self.txt_commands.setPlaceholderText("")
        self.txt_commands.setMinimumHeight(160)

        
        lbl_ttt = QtWidgets.QLabel("Text to Translate:")
        lbl_ttt.setStyleSheet("font-weight: 600;")
        
        self.lbl_sample_text = QtWidgets.QLabel("OCR로 추출한 문장")
        
        self.lbl_sample_text.setStyleSheet(
            "border: 1px solid #d0d0d0; padding: 6px 8px; background: #fafafa; font-family: Consolas, 'Courier New', monospace;"
        )

        # 배치
        lay.addWidget(lbl_head)
        lay.addWidget(lbl_cmd)
        lay.addWidget(self.txt_commands)
        lay.addSpacing(6)
        lay.addWidget(lbl_ttt)
        lay.addWidget(self.lbl_sample_text)
        lay.addStretch(1)

    # --- API ---
    def _build_tab_api(self):
        form = QtWidgets.QFormLayout(self.tab_api)

        self.edt_model = QtWidgets.QLineEdit()
        self.edt_model.setPlaceholderText("예: gemini-1.5-pro")

        self.edt_key = QtWidgets.QLineEdit()
        self.edt_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.edt_key.setPlaceholderText("Your Gemini API Key")

        form.addRow("모델", self.edt_model)
        form.addRow("API 키", self.edt_key)

    # --- 폰트 ---
    def _build_tab_display(self):
        form = QtWidgets.QFormLayout(self.tab_display)

        self.cmb_font = QtWidgets.QComboBox()
        fams = self.mgr.asset_font_families
        self.cmb_font.addItems(fams)

        self.spn_font_size = QtWidgets.QSpinBox()
        self.spn_font_size.setRange(6, 96)
        self.spn_font_size.setSingleStep(1)

        form.addRow("폰트", self.cmb_font)
        form.addRow("크기(pt)", self.spn_font_size)
        self.chk_overlay = QtWidgets.QCheckBox("오버레이 레이아웃 사용")
        self.chk_overlay.setToolTip("해제하면 캡처 후 메인창에만 번역 결과를 표시합니다.")
        form.addRow("", self.chk_overlay)
        
        fonts_dir = os.path.abspath(ASSET_FONTS_DIR)
        file_url = QtCore.QUrl.fromLocalFile(fonts_dir).toString()
        native_path = QtCore.QDir.toNativeSeparators(fonts_dir)
        
        self.lbl_font_hint = QtWidgets.QLabel(self.tab_display)
        self.lbl_font_hint.setWordWrap(True)
        self.lbl_font_hint.setTextFormat(Qt.RichText)
        self.lbl_font_hint.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.lbl_font_hint.setOpenExternalLinks(True)

        # 클릭 시 탐색기에서 폴더 열림
        self.lbl_font_hint.setText(
            f'원하는 폰트를 추가하려면 '
            f'<a href="{file_url}">프로그램 설치 경로</a>에 원하는 폰트를 다운로드하세요.'
        )

        # 실제 경로를 옅게 표시(선택)
        self.lbl_font_path = QtWidgets.QLabel(self.tab_display)
        self.lbl_font_path.setTextFormat(Qt.RichText)
        self.lbl_font_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_font_path.setStyleSheet("color:#888;")
        self.lbl_font_path.setText(f'경로: <code>{html.escape(native_path)}</code>')

        # 라벨들은 설명성이라 라벨명 없이 한 줄씩 추가
        form.addRow(self.lbl_font_hint)
        form.addRow(self.lbl_font_path)

    # --- 정보 ---
    def _build_tab_info(self):
        lay = QtWidgets.QVBoxLayout(self.tab_info)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        title = QtWidgets.QLabel("정보")
        f = title.font(); f.setPointSize(12); f.setBold(True)
        title.setFont(f)

        self.lbl_github = QtWidgets.QLabel()
        self.lbl_github.setTextFormat(Qt.RichText)
        self.lbl_github.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.lbl_github.setOpenExternalLinks(True)

        repo_url = "https://github.com/amature0000/OCR-translate"
        self.lbl_github.setText(
            f'프로젝트 깃허브: <a href="{repo_url}">{repo_url}</a>'
        )

        # 정보
        self.lbl_desc = QtWidgets.QLabel("이 프로젝트는 개인이 사용하기 위한 프로젝트입니다.")
        self.lbl_desc.setStyleSheet("color: #6b7785;")

        lay.addWidget(title)
        lay.addWidget(self.lbl_github)
        lay.addWidget(self.lbl_desc)
        lay.addStretch(1)

    def _load_values(self):
        # 핫키
        self.edt_hotkey.setText(self.mgr.hotkey_combo)
        # Commands
        self.txt_commands.setPlainText(self.mgr.system_prompt)
        # API
        self.edt_model.setText(self.mgr.gemini_model)
        self.edt_key.setText(self.mgr.gemini_api_key)
        # 폰트
        idx = self.cmb_font.findText(self.mgr.font_family, Qt.MatchFixedString)
        if idx >= 0:
            self.cmb_font.setCurrentIndex(idx)
        else:
            self.cmb_font.setCurrentIndex(0)
        self.spn_font_size.setValue(self.mgr.font_size)

    def _save_and_close(self):
        try:
            self._apply_to_manager()
            self.settingsSaved.emit()
            self.accept()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "오류", str(e))

    def _reset_to_defaults(self):
        reply = QtWidgets.QMessageBox.question(
            self, "초기화 확인", "모든 설정을 기본값으로 되돌릴까요?\n(저장은 누를 때 적용됩니다.)",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return

        defaults = SettingsManager.default_settings()
        # UI에 기본값 주입
        self.edt_hotkey.setText(defaults.hotkey_combo)
        self.txt_commands.setPlainText(defaults.system_prompt)
        self.edt_model.setText(defaults.gemini_model)
        self.edt_key.setText(defaults.gemini_api_key)

    def _apply_to_manager(self):
        self.mgr.set_hotkey_combo(self.edt_hotkey.text().strip())
        self.mgr.set_system_prompt(self.txt_commands.toPlainText())
        self.mgr.set_gemini(self.edt_model.text().strip(), self.edt_key.text())
        self.mgr.set_font(self.cmb_font.currentText(), self.spn_font_size.value())
        self.mgr.save()


# ---- 메인 윈도우 ----
class MainWindow(QtWidgets.QMainWindow):
    rectSelected = QtCore.pyqtSignal(QtCore.QRect)
    settingsUpdated = QtCore.pyqtSignal()

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.mgr = settings
        self.setWindowTitle("OCR-translator")
        self.resize(820, 540)

        self.selected_screen_idx: int = 0
        self.sel_overlay: Optional[SelectionOverlay] = None
        self.current_overlay = None

        # 중앙 UI
        central = QtWidgets.QWidget(); v = QtWidgets.QVBoxLayout(central)

        row = QtWidgets.QHBoxLayout()
        self.btn_capture = QtWidgets.QPushButton("번역하기")
        self.btn_capture.clicked.connect(self.start_capture)

        self.lang = QtWidgets.QComboBox()
        self.lang.addItems(["en-US", "ja-JP", "zh-CN"])
        self.lang.setCurrentIndex(0)

        row.addWidget(self.btn_capture)
        row.addSpacing(12)
        row.addWidget(QtWidgets.QLabel("OCR 언어:"))
        row.addWidget(self.lang)
        row.addStretch(1)

        self.out = QtWidgets.QPlainTextEdit(); self.out.setReadOnly(True)

        v.addLayout(row)
        v.addWidget(self.out)
        self.setCentralWidget(central)
        self.statusBar().showMessage("준비")

        # 메뉴바
        self._build_menubar()

    # --- 메뉴바 ---
    def _build_menubar(self):
        menubar = self.menuBar(); menubar.clear()
        
        act_settings = menubar.addAction("환경설정")
        act_settings.triggered.connect(self._open_settings)

        self.menu_monitor = menubar.addMenu("모니터")
        self._refresh_monitor_menu()


    def _refresh_monitor_menu(self):
        self.menu_monitor.clear()
        screens = QtWidgets.QApplication.screens()
        for idx, sc in enumerate(screens):
            geo = sc.geometry()
            text = f"모니터 {idx+1} — {geo.width()}x{geo.height()}"
            act = QtWidgets.QAction(text, self, checkable=True)
            act.setChecked(idx == self.selected_screen_idx)
            act.triggered.connect(lambda checked, i=idx: self._select_monitor(i))
            self.menu_monitor.addAction(act)

        # 수동 새로고침 액션
        self.menu_monitor.addSeparator()
        act_refresh = QtWidgets.QAction("새로고침", self)
        act_refresh.triggered.connect(self._refresh_monitor_menu)
        self.menu_monitor.addAction(act_refresh)

    def _select_monitor(self, idx: int):
        self.selected_screen_idx = idx
        self._refresh_monitor_menu()
        geo = self.current_screen_geo()
        self.statusBar().showMessage(
            f"모니터 {idx+1} 선택: {geo.width()}x{geo.height()} @ ({geo.x()},{geo.y()})", 2500
        )

    def _open_settings(self):
        dlg = SettingsDialog(self.mgr, self)
        dlg.settingsSaved.connect(lambda: self.settingsUpdated.emit())
        dlg.exec_()

    # --- 공개 메서드 (main.py에서 사용) ---
    def current_screen_geo(self) -> QtCore.QRect:
        screens = QtWidgets.QApplication.screens()
        if not screens:
            return QtWidgets.QApplication.primaryScreen().geometry()
        idx = max(0, min(self.selected_screen_idx, len(screens)-1))
        return screens[idx].geometry()

    @QtCore.pyqtSlot()
    def start_capture(self):
        if self.sel_overlay:
            try: self.sel_overlay.close()
            except Exception: pass
            self.sel_overlay = None

        monitor_geo = self.current_screen_geo()
        self.sel_overlay = SelectionOverlay(monitor_geo)
        self.sel_overlay.selected.connect(self._relay_rect_selected)
        self.sel_overlay.cancelled.connect(lambda: self.statusBar().showMessage("취소됨", 2000))

        self.sel_overlay.showFullScreen()
        self.sel_overlay.raise_()
        self.sel_overlay.activateWindow()
        self.statusBar().showMessage(
            f"모니터 {self.selected_screen_idx+1}: 드래그하여 영역 선택 (ESC 취소)"
        )

    def _relay_rect_selected(self, rect_global: QtCore.QRect):
        self.rectSelected.emit(rect_global)

    def get_lang_tag(self) -> str:
        return self.lang.currentText()

    def show_text(self, text: str):
        self.out.setPlainText(text)
        self.statusBar().showMessage("완료", 2000)
