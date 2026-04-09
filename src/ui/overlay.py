import ctypes
import os
import sys

# 현재 파일(overlay.py)의 상위 폴더인 src 폴더를 탐색 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer, QEasingCurve
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPixmap, QMovie, QPainter, QIcon

# 스트레칭 문구를 파일에서 로드하기 위한 유틸리티 임포트
from core.stretching_loader import StretchingLoader
from core.system_utils import resource_path
from ui.ui_utils import dp, scale_qss

class CroppedLabel(QLabel):
    """이미지나 GIF를 1:1 비율로 중앙 크롭하여 표시하는 커스텀 라벨 (둥근 모서리 적용)"""
    def __init__(self, size=200, radius=28):
        super().__init__()
        self.radius = radius
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._movie = None
        self._pixmap = None

    def setMovie(self, movie):
        self._movie = movie
        self._pixmap = None
        # 프레임이 바뀔 때마다 다시 그리도록 연결
        self._movie.frameChanged.connect(self.update)
        self._movie.start()

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self._movie = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 둥근 모서리 클리핑 적용
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.radius, self.radius)
        painter.setClipPath(path)

        pix = None
        if self._movie:
            pix = self._movie.currentPixmap()
        elif self._pixmap:
            pix = self._pixmap

        if pix and not pix.isNull():
            w, h = pix.width(), pix.height()
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            
            from PySide6.QtCore import QRect
            source_rect = QRect(left, top, side, side)
            painter.drawPixmap(self.rect(), pix, source_rect)
        else:
            # 기본 배경이나 🧘 이모지 표시 시에도 둥근 배경 적용
            painter.setBrush(QColor(0, 0, 0, 20))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), self.radius, self.radius)
            super().paintEvent(event)

class StretchOverlay(QWidget):
    """스트레칭 알림 오버레이: 캐릭터와 텍스트 카드를 분리하여 표시"""
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.movie = None
        self.stretching_loader = StretchingLoader()
        
        # --- 창 속성 설정 ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self._set_win32_clickthrough()
        
        # 창 크기 (이미지와 텍스트 카드의 조화를 위해 대폭 축소)
        self.setFixedSize(dp(540), dp(220)) 
        
        # 전체 컨테이너 (투명, 그림자 효과의 대상)
        self.inner_frame = QFrame(self)
        self.inner_frame.setStyleSheet("background: transparent; border: none;")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(dp(15))
        shadow.setXOffset(0)
        shadow.setYOffset(dp(3))
        shadow.setColor(QColor(0, 0, 0, 50))
        self.inner_frame.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.inner_frame)
        
        inner_layout = QHBoxLayout(self.inner_frame)
        inner_layout.setContentsMargins(dp(10), dp(10), dp(10), dp(10))
        inner_layout.setSpacing(dp(15)) # 간격을 더 타이트하게
        
        # 1. 좌측: 캐릭터 영역 (200x200 유지)
        self.icon_label = CroppedLabel(dp(200), dp(28))
        self._load_overlay_image()
        inner_layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 2. 우측: 텍스트 카드 영역 (캐릭터 높이에 맞춰 대폭 축소)
        self.text_card = QFrame()
        self.text_card.setObjectName("TextCard")
        # 고정 너비를 설정하여 이미지만큼 컴팩트하게 (300px 정도)
        self.text_card.setFixedWidth(dp(300))
        self.text_card.setFixedHeight(dp(200)) # 캐릭터 높이와 동일하게
        
        text_layout = QVBoxLayout(self.text_card)
        # 여백을 20px 정도로 줄여 더 꽉 차 보이게 조정
        text_layout.setContentsMargins(dp(20), dp(20), dp(20), dp(20))
        text_layout.setSpacing(0)
        
        text_layout.addStretch()
        self.title_label = QLabel("스트레칭 시간입니다.")
        self.title_label.setObjectName("TitleText")
        self.title_label.setFixedHeight(dp(40))
        # [수정] 제목 가로 중앙 정렬 적용
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_layout.addWidget(self.title_label)
        
        text_layout.addSpacing(dp(5))
        
        self.desc_label = QLabel("")
        self.desc_label.setObjectName("BodyText")
        self.desc_label.setWordWrap(True)
        # [수정] 가로/세로 모두 중앙 정렬 적용
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 최소 높이를 80px 정도로 줄여 균형 유지
        self.desc_label.setMinimumHeight(dp(80))
        text_layout.addWidget(self.desc_label)
        text_layout.addStretch()
        
        inner_layout.addWidget(self.text_card)
        
        # [수정] 카드 영역 전체를 클릭하면 닫히도록 커서 설정
        self.inner_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide_overlay)

    def mousePressEvent(self, event):
        """이미지나 텍스트 카드 영역을 클릭하면 즉시 숨김"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 아이콘 라벨이나 텍스트 카드 영역을 클릭했는지 확인
            if self.icon_label.geometry().contains(event.pos()) or \
               self.text_card.geometry().contains(event.pos()):
                self.hide_overlay()

    def _set_win32_clickthrough(self):
        hwnd = self.winId()
        WS_EX_LAYERED = 0x00080000
        WS_EX_NOACTIVATE = 0x08000000
        GWL_EXSTYLE = -20
        user32 = ctypes.windll.user32
        user32.SetWindowLongW(int(hwnd), GWL_EXSTYLE, WS_EX_LAYERED | WS_EX_NOACTIVATE)

    def _load_overlay_image(self):
        if hasattr(self, 'icon_label') and (self.movie or self.icon_label.pixmap()):
            return
            
        gif_path = resource_path(os.path.join("ui", "assets", "character", "stretching.gif"))
        img_path = resource_path(os.path.join("ui", "assets", "character", "stretching.png"))
        
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.icon_label.setMovie(self.movie)
        elif os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("🧘")
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def show_overlay(self):
        self._load_overlay_image()
        if self.movie:
            self.movie.start()

        is_dark = self.config_manager.get("dark_mode", True) if self.config_manager else True
        bg_color = "rgba(25, 25, 25, 220)" if is_dark else "rgba(255, 255, 255, 230)"
        title_color = "#FFFFFF" if is_dark else "#1C1C1E"
        body_color = "#BBBBBB" if is_dark else "#3C3C43"
        border_color = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.05)"
        
        # 텍스트 카드(#TextCard)에만 스타일 적용
        self.text_card.setStyleSheet(scale_qss(f"""
            QFrame#TextCard {{
                background-color: {bg_color};
                border-radius: 28px;
                border: 1px solid {border_color};
            }}
            QLabel {{ background: transparent; border: none; }}
            QLabel#TitleText {{ 
                font-family: "Pretendard", sans-serif;
                color: {title_color}; font-size: 28px; font-weight: 700; 
            }}
            QLabel#BodyText {{ 
                font-family: "Pretendard", sans-serif;
                color: {body_color}; font-size: 19px; font-weight: 400;
                line-height: 1.6;
            }}
        """))


        rest_message = self.stretching_loader.get_random_rest_message()
        self.desc_label.setText(rest_message)
        
        target_opacity = self.config_manager.get("overlay_opacity") or 1.0 if self.config_manager else 1.0
        
        screen = QGuiApplication.primaryScreen().geometry()
        x = screen.x() + screen.width() - self.width() - dp(30)
        y = screen.y() + dp(40)
        self.move(x, y)
        
        self.show()
        try: self.anim.finished.disconnect()
        except: pass
        self.anim.stop()
        self.anim.setStartValue(self.windowOpacity())
        self.anim.setEndValue(target_opacity)
        self.anim.start()
        
        self.hide_timer.start(15000)

    def hide_overlay(self):
        """오버레이를 숨길 때 애니메이션을 정지하여 메모리 절약"""
        self.hide_timer.stop()
        if self.movie:
            self.movie.stop() # GIF 애니메이션 정지 (CPU/메모리 절약)
            
        try: self.anim.finished.disconnect()
        except: pass
        self.anim.stop()
        self.anim.setStartValue(self.windowOpacity())
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.hide)
        self.anim.start()
