from typing import Optional
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

# Windows z-order 강제
import ctypes
from ctypes import wintypes
SetWindowPos = ctypes.windll.user32.SetWindowPos
HWND_TOPMOST   = -1
SWP_NOMOVE     = 0x0002
SWP_NOSIZE     = 0x0001
SWP_SHOWWINDOW = 0x0040

class OverlayWindow(QtWidgets.QWidget):
    """선택 영역에 맞춰 폭을 고정, 텍스트 높이에 맞춰 동적으로 높이를 조절하는 오버레이."""
    PADDING = QtCore.QMargins(14, 12, 14, 12)  # 좌/상/우/하 내부 여백

    def __init__(self, rect_global: QtCore.QRect, text: str = "",
                 parent: Optional[QtWidgets.QWidget] = None,
                 font_family: Optional[str] = None,
                 font_size: int = 14):
        super().__init__(parent=None)  # 항상 최상위

        self.setWindowFlags(
            Qt.Popup
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.StrongFocus)

        # 기준 사각형
        self.base_rect = QtCore.QRect(rect_global)

        self._font = QtGui.QFont(font_family)
        self._font.setPointSize(max(int(font_size), 10))
        self._font.setWeight(QtGui.QFont.Black)
        self._font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self._font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, 0.4)

        content = QtWidgets.QWidget()
        content.setAutoFillBackground(False)
        content.setAttribute(Qt.WA_TranslucentBackground, True)

        self._lay = QtWidgets.QVBoxLayout(content)
        self._lay.setContentsMargins(self.PADDING.left(), self.PADDING.top(),
                                     self.PADDING.right(), self.PADDING.bottom())
        self._lay.setSpacing(0)

        # 내용 라벨
        self.label = QtWidgets.QLabel(text, self)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.label.setFont(self._font)
        self.label.setStyleSheet("QLabel { background: transparent; color: #FFFFFF; }")

        # 그림자
        shadow = QtWidgets.QGraphicsDropShadowEffect(self.label)
        shadow.setBlurRadius(2.5)
        shadow.setOffset(0, 0)
        shadow.setColor(QtGui.QColor(0, 0, 0, 230))
        self.label.setGraphicsEffect(shadow)

        self._lay.addWidget(self.label)

        # 루트 레이아웃
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(content)

        # 초기 배치
        self._relayout()
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.ActiveWindowFocusReason)

        try:
            hwnd = int(self.winId())
            SetWindowPos(wintypes.HWND(hwnd), HWND_TOPMOST, 0, 0, 0, 0,
                         SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        except Exception:
            pass

    # ---------------- 동적 레이아웃 ----------------
    def _screen_for_rect(self, rect: QtCore.QRect) -> QtGui.QScreen:
        scr = QtWidgets.QApplication.screenAt(rect.center())
        return scr or QtWidgets.QApplication.primaryScreen()

    def _calc_text_height(self, content_width: int) -> int:
        """패딩 제외한 콘텐츠 폭에 맞춰 문단 높이(px)를 계산."""
        doc = QtGui.QTextDocument()
        doc.setDefaultFont(self._font)
        doc.setPlainText(self.label.text())
        doc.setTextWidth(max(1, content_width))
        size = doc.size()  # QSizeF
        return int(size.height() + 0.999)

    def _relayout(self):
        total_w = max(50, self.base_rect.width())
        content_w = total_w - self.PADDING.left() - self.PADDING.right()

        self.label.setFixedWidth(max(1, content_w))

        text_h = self._calc_text_height(content_w)
        total_h_needed = text_h + self.PADDING.top() + self.PADDING.bottom()

        scr = self._screen_for_rect(self.base_rect)
        sgeo = scr.geometry()

        x = self.base_rect.x()
        y = self.base_rect.y()
        h = total_h_needed

        max_h = sgeo.height()
        if h > max_h:
            h = max_h

        overflow_bottom = (y + h) - (sgeo.y() + sgeo.height())
        if overflow_bottom > 0:
            y = max(sgeo.y(), y - overflow_bottom)

        if x < sgeo.x():
            x = sgeo.x()
        if x + total_w > sgeo.x() + sgeo.width():
            x = (sgeo.x() + sgeo.width()) - total_w

        self.setGeometry(QtCore.QRect(x, y, total_w, h))

    # --------------- API ---------------
    def set_text(self, text: str):
        self.label.setText(text or "")
        self._relayout()

    # ------------------------------
    def paintEvent(self, e: QtGui.QPaintEvent):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, False)
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 190))

    def focusOutEvent(self, e: QtGui.QFocusEvent):
        self.close()
        super().focusOutEvent(e)
