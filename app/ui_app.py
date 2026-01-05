from typing import Optional
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
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
        self.tab_prompts = QtWidgets.QWidget(); self.tabs.addTab(self.tab_prompts, "프롬프트")
        self._build_tab_prompts()

        # Tab 3: API
        self.tab_api = QtWidgets.QWidget(); self.tabs.addTab(self.tab_api, "API")
        self._build_tab_api()

        # Tab 4: 폰트
        self.tab_display = QtWidgets.QWidget(); self.tabs.addTab(self.tab_display, "폰트")
        self._build_tab_display()

        # Tab 5: 정보
        self.tab_info = QtWidgets.QWidget(); self.tabs.addTab(self.tab_info, "기타")
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
        self.edt_hotkey.setPlaceholderText("캡처 보드를 여는 핫키")
        self.edt_hotkey_rem = QtWidgets.QLineEdit()
        self.edt_hotkey_rem.setPlaceholderText("직전 캡처 영역을 그대로 다시 캡처하여 번역하는 핫키")
        self.chk_overlay_0 = QtWidgets.QCheckBox("스크롤 인식: 이전에 캡처한 문장과 겹치는 경우, 두 문장을 합쳐서 번역합니다.")
        self.chk_overlay_0.setToolTip("직전 번역 기록과 겹치는 문장을 캡처하면, 이전 문장과 합쳐서 번역합니다.")
        self.lbl_hotkey_hint = QtWidgets.QLabel("형식: (커맨드 키) + (키). 예) ctrl+shift+f1, ctrl+g")
        self.lbl_hotkey_hint.setStyleSheet("color: gray;")

        form.addRow("캡처 핫키", self.edt_hotkey)
        form.addRow("재번역 핫키", self.edt_hotkey_rem)
        form.addRow("", self.chk_overlay_0)
        form.addRow(self.lbl_hotkey_hint)

    # --- 프롬프트 ---
    def _build_tab_prompts(self):
        root = QtWidgets.QVBoxLayout(self.tab_prompts)

        split = QtWidgets.QHBoxLayout()
        root.addLayout(split, 1)

        # 프리셋 리스트
        left = QtWidgets.QVBoxLayout()
        self.lst_presets = QtWidgets.QListWidget()
        self.lst_presets.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        left.addWidget(self.lst_presets, 1)
        split.addLayout(left, 1)

        # 프리셋 에디터
        right_form = QtWidgets.QFormLayout()
        self.edt_preset_name = QtWidgets.QLineEdit()
        self.txt_system_prompt = QtWidgets.QPlainTextEdit()
        self.txt_system_prompt.setTabChangesFocus(False)
        right_form.addRow("이름", self.edt_preset_name)
        right_form.addRow("시스템 프롬프트", self.txt_system_prompt)
        right_wrap = QtWidgets.QWidget()
        right_wrap.setLayout(right_form)
        split.addWidget(right_wrap, 2)

        # 버튼
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_preset_add = QtWidgets.QPushButton("추가")
        self.btn_preset_del = QtWidgets.QPushButton("삭제")
        self.btn_preset_apply = QtWidgets.QPushButton("적용")
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_preset_add)
        btn_row.addWidget(self.btn_preset_del)
        btn_row.addWidget(self.btn_preset_apply)
        root.addLayout(btn_row)

        # =======
        def _current_preset_id():
            it = self.lst_presets.currentItem()
            return it.data(QtCore.Qt.UserRole) if it else None

        def _load_preset_to_editor(pid: str):
            p = next((x for x in self.mgr.list_presets() if x.id == pid), None)
            if not p:
                self.edt_preset_name.clear()
                self.txt_system_prompt.clear()
                return
            self.edt_preset_name.setText(p.name)
            self.txt_system_prompt.setPlainText(p.system_prompt)

        def _refresh_list(select_pid: str | None = None):
            self.lst_presets.clear()
            active_id = self.mgr._settings.active_preset_id
            for p in self.mgr.list_presets():
                text = p.name + ("  •활성" if p.id == active_id else "")
                it = QtWidgets.QListWidgetItem(text)
                it.setData(QtCore.Qt.UserRole, p.id)
                self.lst_presets.addItem(it)
            
            if select_pid:
                for i in range(self.lst_presets.count()):
                    it = self.lst_presets.item(i)
                    if it.data(QtCore.Qt.UserRole) == select_pid:
                        self.lst_presets.setCurrentItem(it)
                        break
            elif self.lst_presets.count():
                self.lst_presets.setCurrentRow(0)

            cur = _current_preset_id()
            if cur: _load_preset_to_editor(cur)
            else:
                self.edt_preset_name.clear()
                self.txt_system_prompt.clear()

        _refresh_list()

        # 리스트 변경 시
        self.lst_presets.currentItemChanged.connect(
            lambda it, prev: _load_preset_to_editor(it.data(QtCore.Qt.UserRole)) if it else None
        )

        # ==========
        def on_add():
            name = (self.edt_preset_name.text() or "").strip() or "새 프리셋"
            body = self.txt_system_prompt.toPlainText()
            p = self.mgr.add_preset(name, body)
            _refresh_list(select_pid=p.id)
            self.settingsSaved.emit()

        def on_del():
            pid = _current_preset_id()
            if not pid:
                QtWidgets.QMessageBox.information(self, "오류", "삭제할 프리셋을 선택하세요.")
                return
            self.mgr.delete_preset(pid)
            _refresh_list()
            self.settingsSaved.emit()

        def on_apply():
            pid = _current_preset_id()
            if not pid:
                QtWidgets.QMessageBox.information(self, "오류", "적용할 프리셋을 선택하세요.")
                return
            name = (self.edt_preset_name.text() or "").strip() or "이름 없음"
            body = self.txt_system_prompt.toPlainText()
            self.mgr.update_preset(pid, name=name, system_prompt=body)
            self.mgr.set_preset(pid)
            _refresh_list(select_pid=pid)
            self.settingsSaved.emit()

        self.btn_preset_add.clicked.connect(on_add)
        self.btn_preset_del.clicked.connect(on_del)
        self.btn_preset_apply.clicked.connect(on_apply)
    # --- API ---
    def _build_tab_api(self):
        form = QtWidgets.QFormLayout(self.tab_api)

        self.edt_model = QtWidgets.QLineEdit()
        self.edt_model.setPlaceholderText("예: gemini-1.5-pro")

        self.edt_key = QtWidgets.QLineEdit()
        self.edt_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.edt_key.setPlaceholderText("Your Gemini API Key")

        self.api_chk_0 = QtWidgets.QCheckBox("구글 번역 사용: AI 번역 대신 기본 구글 번역을 사용합니다.")
        self.api_chk_0.setToolTip("해당 기능을 활성화하면 프롬프트는 비활성화됩니다.")

        form.addRow("모델", self.edt_model)
        form.addRow("API 키", self.edt_key)
        form.addItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Fixed))
        form.addRow(self.api_chk_0)

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

        self.lbl_font_hint.setText(
            f'원하는 폰트를 추가하려면 '
            f'<a href="{file_url}">프로그램 설치 경로</a>에 원하는 폰트를 다운로드하세요.'
        )

        self.lbl_font_path = QtWidgets.QLabel(self.tab_display)
        self.lbl_font_path.setTextFormat(Qt.RichText)
        self.lbl_font_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_font_path.setStyleSheet("color:#888;")
        self.lbl_font_path.setText(f'경로: <code>{html.escape(native_path)}</code>')

        form.addRow(self.lbl_font_hint)
        form.addRow(self.lbl_font_path)

    # --- 기타 ---
    def _build_tab_info(self):
        lay = QtWidgets.QVBoxLayout(self.tab_info)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        title0 = QtWidgets.QLabel("기타 설정")
        f = title0.font(); f.setPointSize(12); f.setBold(True)
        title0.setFont(f)

        grp = QtWidgets.QGroupBox("클립보드에 다음 결과를 복사합니다.")
        v = QtWidgets.QVBoxLayout(grp)

        self.rb_clip_source = QtWidgets.QRadioButton("원문 텍스트를 복사")
        self.rb_clip_translated = QtWidgets.QRadioButton("번역된 텍스트를 복사")
        self.rb_clip_image = QtWidgets.QRadioButton("캡처한 이미지를 복사")

        v.addWidget(self.rb_clip_source)
        v.addWidget(self.rb_clip_translated)
        v.addWidget(self.rb_clip_image)

        self.clip_btn_group = QtWidgets.QButtonGroup(self)
        self.clip_btn_group.addButton(self.rb_clip_source, 0)
        self.clip_btn_group.addButton(self.rb_clip_translated, 1)
        self.clip_btn_group.addButton(self.rb_clip_image, 2)

        self.info_chk_0 = QtWidgets.QCheckBox("OCR 툴: 번역 과정을 거치지 않고 OCR(텍스트 캡처)만 수행합니다.")

        title = QtWidgets.QLabel("정보")
        f = title.font(); f.setPointSize(12); f.setBold(True)
        title.setFont(f)

        self.lbl_github = QtWidgets.QLabel()
        self.lbl_github.setTextFormat(Qt.RichText)
        self.lbl_github.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.lbl_github.setOpenExternalLinks(True)
        repo_url = "https://github.com/amature0000/SOTE"
        self.lbl_github.setText(
            f'프로젝트 깃허브: <a href="{repo_url}">{repo_url}</a>'
        )

        lay.addWidget(title0)
        lay.addWidget(grp)
        lay.addWidget(self.info_chk_0)
        lay.addItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Fixed))
        lay.addWidget(title)
        lay.addWidget(self.lbl_github)
        lay.addStretch(1)

    def _load_values(self):
        # 핫키
        self.edt_hotkey.setText(self.mgr.hotkey_combo)
        self.edt_hotkey_rem.setText(self.mgr.hotkey_rem_combo)
        self.chk_overlay_0.setChecked(self.mgr.use_scroll_detect)
        # API
        self.edt_model.setText(self.mgr.gemini_model)
        self.edt_key.setText(self.mgr.gemini_api_key)
        self.api_chk_0.setChecked(self.mgr.use_google_api)
        # 폰트
        idx = self.cmb_font.findText(self.mgr.font_family, Qt.MatchFixedString)
        self.chk_overlay.setChecked(self.mgr.use_overlay_layout)
        if idx >= 0:
            self.cmb_font.setCurrentIndex(idx)
        else:
            self.cmb_font.setCurrentIndex(0)
        self.spn_font_size.setValue(self.mgr.font_size)
        # 기타
        self.info_chk_0.setChecked(self.mgr.no_llm)
        mode = self.mgr.copy_rule
        if mode == 0:
            self.rb_clip_source.setChecked(True)
        elif mode == 1:
            self.rb_clip_translated.setChecked(True)
        else:
            self.rb_clip_image.setChecked(True)

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
        self.edt_hotkey_rem.setText(defaults.hotkey_rem_combo)
        self.chk_overlay_0.setChecked(defaults.use_scroll_detect)
        self.edt_model.setText(defaults.gemini_model)
        self.edt_key.setText(defaults.gemini_api_key)
        self.api_chk_0.setChecked(defaults.use_google_api)
        self.chk_overlay.setChecked(defaults.use_overlay_layout)
        self.info_chk_0.setChecked(defaults.no_llm)
        mode = defaults.copy_rule
        if mode == 1:
            self.rb_clip_source.setChecked(True)
        elif mode == 2:
            self.rb_clip_translated.setChecked(True)
        else:
            self.rb_clip_image.setChecked(True)

    def _apply_to_manager(self):
        self.mgr.set_hotkey_combo(self.edt_hotkey.text().strip())
        self.mgr.set_hotkey_rem_combo(self.edt_hotkey_rem.text().strip())
        self.mgr.set_use_scroll_detect(self.chk_overlay_0.isChecked())
        self.mgr.set_gemini(self.edt_model.text().strip(), self.edt_key.text())
        self.mgr.set_use_google_api(self.api_chk_0.isChecked())
        self.mgr.set_font(self.cmb_font.currentText(), self.spn_font_size.value())
        self.mgr.set_use_overlay_layout(self.chk_overlay.isChecked())
        self.mgr.set_no_llm(self.info_chk_0.isChecked())
        mode = 2
        if self.rb_clip_source.isChecked(): mode = 0
        elif self.rb_clip_translated.isChecked(): mode = 1
        self.mgr.set_copy_rule(mode)

        self.mgr.save()

# ---- 메인 윈도우 ----
class MainWindow(QtWidgets.QMainWindow):
    rectSelected = QtCore.pyqtSignal(QtCore.QRect)
    settingsUpdated = QtCore.pyqtSignal()

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.mgr = settings
        self.setWindowTitle("SOTE - Simple OCR Translate for Everything")
        self.resize(820, 540)

        self.selected_screen_idx: int = 0
        self.sel_overlay: Optional[SelectionOverlay] = None
        self.current_overlay = None
        self.last_selection_rect = None

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

    def current_screen_geo(self) -> QtCore.QRect:
        screens = QtWidgets.QApplication.screens()
        if not screens:
            return QtWidgets.QApplication.primaryScreen().geometry()
        idx = max(0, min(self.selected_screen_idx, len(screens)-1))
        return screens[idx].geometry()

    @QtCore.pyqtSlot()
    def start_capture(self):
        self.close_overlays(True)

        monitor_geo = self.current_screen_geo()
        self.sel_overlay = SelectionOverlay(monitor_geo) # 캡처 보드 호출
        self.sel_overlay.selected.connect(self._relay_rect_selected) # 영역 선택시 호출
        self.sel_overlay.cancelled.connect(lambda: self.statusBar().showMessage("취소됨", 2000))

        self.sel_overlay.showFullScreen()
        self.sel_overlay.raise_()
        self.sel_overlay.activateWindow()
        self.statusBar().showMessage(
            f"모니터 {self.selected_screen_idx+1}: 드래그하여 영역 선택 (ESC 취소)"
        )
    
    @QtCore.pyqtSlot()
    def run_last_rect(self):
        r = self.last_selection_rect
        if not r or r.isNull() or r.width() <= 0 or r.height() <= 0:
            self.show_text("이전에 캡처한 영역이 존재하지 않습니다.")
            return
        self.close_overlays()

        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
        QtCore.QTimer.singleShot(20, lambda: self.rectSelected.emit(r))

    def _relay_rect_selected(self, rect_global: QtCore.QRect):
        self.close_overlays()

        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
        QtCore.QTimer.singleShot(30, lambda: self.rectSelected.emit(rect_global))
    
    def close_overlays(self, hard = False):
        if self.sel_overlay:
            try: 
                self.sel_overlay.hide()
                if hard: 
                    self.sel_overlay.close()
                    self.sel_overlay = None
            except Exception: pass
            print("close capture overlay")
        if getattr(self, "current_overlay", None):
            try: self.current_overlay.close()
            except Exception: pass
            print("close overlay")
            self.current_overlay = None

    def get_lang_tag(self) -> str:
        return self.lang.currentText()

    def show_text(self, text: str):
        self.out.setPlainText(text)
        self.statusBar().showMessage("완료", 2000)
