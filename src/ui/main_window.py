import os
import sys

# 현재 파일(main_window.py)의 상위 폴더인 src 폴더를 탐색 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QStackedWidget, QPushButton, QProgressBar, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QComboBox, QCheckBox, QSpacerItem, QSizePolicy, QDialog, QTextEdit, QSpinBox, QSlider
)
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QMouseEvent, QDesktopServices, QPixmap

from core.system_utils import set_run_on_startup, resource_path
from ui.ui_utils import dp, scale_qss

class ClickableCard(QFrame):
    """클릭 신호를 방출하는 커스텀 프레임 카드 (시각 효과 제거)"""
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_pressed = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_pressed:
            self._is_pressed = False
            # 마우스가 카드 영역 안에서 떼어졌을 때만 클릭 신호 방출
            if self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
        super().mouseReleaseEvent(event)

class StretchingDetailDialog(QDialog):
    """특정 부위의 모든 스트레칭 동작을 리스트로 보여주는 상세 창"""
    def __init__(self, category, items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 현재 해상도에 따른 크기 설정
        self.resize(dp(540), dp(700))

        is_dark = True
        if parent and hasattr(parent, 'config_manager') and parent.config_manager:
            is_dark = parent.config_manager.get("dark_mode", True)

        theme_str = "dark" if is_dark else "light"
        if parent:
            self.move(parent.geometry().center() - self.rect().center())

        main_layout = QVBoxLayout(self)
        container = QFrame()
        container.setObjectName("DocViewer")
        container.setProperty("theme", theme_str)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(dp(30), dp(30), dp(30), dp(30))
        layout.setSpacing(dp(20))

        # 제목 영역
        header_layout = QHBoxLayout()
        title_label = QLabel(category)
        title_label.setObjectName("DocTitle")
        title_label.setStyleSheet(f"font-size: {dp(24)}px; font-weight: bold; color: #33BA25;")
        header_layout.addWidget(title_label)

        close_icon_btn = QPushButton("✕")
        close_icon_btn.setFixedSize(dp(30), dp(30))
        close_icon_btn.setStyleSheet(scale_qss("""
            QPushButton { 
                background: transparent; color: #8E8E93; font-size: 20px; border: none; 
            }
            QPushButton:hover { color: #FF3B30; }
        """))
        close_icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_icon_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_icon_btn)
        layout.addLayout(header_layout)

        # 스크롤 가능한 상세 내용
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        item_layout = QVBoxLayout(scroll_content)
        item_layout.setSpacing(dp(25))
        item_layout.setContentsMargins(0, 0, dp(10), 0)

        for item in items:
            item_box = QFrame()
            item_box.setStyleSheet(f"""
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: {dp(12)}px;
                padding: {dp(15)}px;
            """)
            box_vbox = QVBoxLayout(item_box)

            # 동작 제목 + 난이도/시간
            top_hbx = QHBoxLayout()
            name_lbl = QLabel(item['title'])
            name_lbl.setStyleSheet(f"font-size: {dp(18)}px; font-weight: bold; color: {('#FFFFFF' if is_dark else '#1C1C1E')};")

            info_lbl = QLabel(f"{item['duration']} | 난이도 {item['diff']}")
            info_lbl.setStyleSheet(f"font-size: {dp(13)}px; color: #33BA25; font-weight: 500;")

            top_hbx.addWidget(name_lbl)
            top_hbx.addStretch()
            top_hbx.addWidget(info_lbl)
            box_vbox.addLayout(top_hbx)
            box_vbox.addSpacing(dp(8))

            # 설명
            desc_lbl = QLabel(item['desc'])
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"font-size: {dp(15)}px; color: #A1A1A6; line-height: 1.5;")
            box_vbox.addWidget(desc_lbl)

            item_layout.addWidget(item_box)

        item_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        main_layout.addWidget(container)

        # 그림자
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(dp(30))
        shadow.setColor(QColor(0, 0, 0, 150) if is_dark else QColor(0, 0, 0, 40))
        container.setGraphicsEffect(shadow)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if hasattr(self, "old_pos") and self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

class ToastWidget(QFrame):

    """설정 저장 시 하단에 나타나는 토스트 알림 (다크/라이트 모드 대응)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # UI 구성요소 한 번만 생성
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(dp(24), dp(14), dp(24), dp(14))
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_toast)
        
        self.update_style()
        self.hide()

    def update_style(self):
        # 부모의 설정을 확인하거나 기본값 사용
        is_dark = True
        if self.parent() and hasattr(self.parent(), 'dark_cb'):
            is_dark = self.parent().dark_cb.isChecked()
            
        bg_color = "rgba(44, 44, 46, 0.95)" if is_dark else "rgba(255, 255, 255, 0.98)"
        text_color = "#FFFFFF" if is_dark else "#1C1C1E"
        border_color = "rgba(255, 255, 255, 0.15)" if is_dark else "rgba(0, 0, 0, 0.08)"
        shadow_color = "rgba(0, 0, 0, 0.5)" if is_dark else "rgba(0, 0, 0, 0.1)"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 14px;
                border: 1px solid {border_color};
            }}
            QLabel {{
                color: {text_color}; 
                font-size: 16px; 
                font-weight: 500;
                font-family: "Pretendard", sans-serif;
                background: transparent;
                border: none;
            }}
        """)

    def show_message(self, text):
        self.update_style()  # 메시지 표시 전 스타일(테마) 갱신
        self.label.setText(text)
        
        # 텍스트에 맞게 크기 조절 (최소 너비 보장)
        self.label.adjustSize()
        self.adjustSize()
        self.setMinimumWidth(min(400, self.label.width() + 60))
        
        if self.parent():
            # 부모 하단 중앙에 배치
            x = (self.parent().width() - self.width()) // 2
            y = self.parent().height() - self.height() - 50
            self.move(x, y)
            
        self.raise_()
        self.show()
        
        self.anim.stop()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1)
        self.anim.start()
        
        self.timer.start(2500)

    def hide_toast(self):
        self.anim.stop()
        try:
            self.anim.finished.disconnect()
        except:
            pass
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.hide)
        self.anim.start()

class DocumentViewer(QDialog):
    """이용약관 및 개인정보 처리방침을 보여주는 팝업 창 (테마 대응)"""
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(dp(500), dp(600))
        
        # 현재 테마 파악
        is_dark = True
        if parent and hasattr(parent, 'config_manager') and parent.config_manager:
            # config_manager가 있다면 저장된 설정값 사용
            is_dark = parent.config_manager.get("dark_mode", True)
        
        theme_str = "dark" if is_dark else "light"
        
        # 부모 중앙에 배치
        if parent:
            self.move(parent.geometry().center() - self.rect().center())
        
        main_layout = QVBoxLayout(self)
        container = QFrame()
        container.setObjectName("DocViewer")
        container.setProperty("theme", theme_str) # 테마 속성 부여
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(dp(30), dp(30), dp(30), dp(30))
        
        # 제목 및 닫기 버튼 영역 (헤더)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, dp(10))
        
        title_label = QLabel(title)
        title_label.setObjectName("DocTitle")
        title_label.setProperty("theme", theme_str)
        title_label.setStyleSheet(f"font-size: {dp(24)}px; font-weight: bold; color: #33BA25;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_icon_btn = QPushButton("✕")
        close_icon_btn.setFixedSize(dp(32), dp(32))
        close_icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_icon_btn.setStyleSheet(scale_qss("""
            QPushButton { 
                background: transparent; color: #8E8E93; font-size: 22px; border: none; font-weight: bold;
            }
            QPushButton:hover { color: #FF3B30; }
        """))
        close_icon_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_icon_btn)
        
        layout.addLayout(header_layout)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(content)
        self.text_edit.setObjectName("DocContent")
        self.text_edit.setProperty("theme", theme_str)
        layout.addWidget(self.text_edit)
        
        main_layout.addWidget(container)
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        if is_dark:
            shadow.setColor(QColor(0, 0, 0, 180))
        else:
            shadow.setColor(QColor(0, 0, 0, 40)) # 라이트 모드는 연한 그림자
        container.setGraphicsEffect(shadow)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if hasattr(self, "old_pos") and self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

class MainWindow(QWidget):
    """메인 애플리케이션 창 (Toss/Apple 미니멀리즘 다크 모드)"""
    def __init__(self, engine, config_manager=None):
        super().__init__()
        self.engine = engine
        self.config_manager = config_manager
        
        # [추가] AI 분석용 실시간 통계 변수 초기화
        self.current_kbd = 0
        self.current_click = 0
        self.current_dist = 0.0

        # [최적화] 테마별 아이콘 객체 재사용을 위한 2차원 캐시
        self.icon_cache = {"dark": {}, "light": {}}
        self.tips_btn = None
        self.dark_cb = None
        self._current_theme_folder = None # 현재 적용된 아이콘 테마 폴더명 캐시

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # [최종 수정] 최소 크기는 고정하되, 최대 크기를 시스템 최대값으로 명시적으로 풀어줍니다.
        # 윈도우 OS가 내부적으로 추가하는 여백(그림자 등) 때문에 발생하는 지오메트리 충돌 경고를 방지합니다.
        w, h = dp(980), dp(860)
        self.setMinimumSize(w, h)
        self.setMaximumSize(16777215, 16777215) 
        self.resize(w, h)

        self.old_pos = None

        # 다크 모드에 어울리는 깊고 은은한 그림자
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(40)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(10)
        self.shadow.setColor(QColor(0, 0, 0, 150))

        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setGraphicsEffect(self.shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(dp(25), dp(25), dp(25), dp(25))
        layout.addWidget(self.main_container)

        # 스타일시트 캐싱 (최초 1회 로드 후 변수로 관리하여 파일 I/O 억제)
        from ui.ui_utils import scale_qss
        self.cached_qss = ""
        qss_path = resource_path(os.path.join("ui", "style.qss"))
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.cached_qss = f.read()
            self.setStyleSheet(scale_qss(self.cached_qss))
        except:
            pass

        self.setup_ui()
        self.engine.fatigue_updated.connect(self.update_progress)
        self.engine.stats_updated.connect(self.update_stats)
        self.toast = ToastWidget(self.main_container)

        from PySide6.QtGui import QGuiApplication
        QGuiApplication.styleHints().colorSchemeChanged.connect(self.on_system_theme_changed)

    def on_system_theme_changed(self, scheme):
        # 시스템 테마 변경 감지 로직은 '시스템 설정에 맞추기' 옵션이 제거되었으므로 더 이상 동작하지 않음
        pass

    def get_themed_icon(self, theme_folder, icon_file):
        """테마와 아이콘 파일명에 따른 캐시된 아이콘 반환"""
        theme_key = "dark" if "dark" in theme_folder else "light"
        if icon_file not in self.icon_cache[theme_key]:
            icon_path = resource_path(os.path.join("ui", "assets", "icons", theme_folder, icon_file))
            if os.path.exists(icon_path):
                from PySide6.QtGui import QIcon
                self.icon_cache[theme_key][icon_file] = QIcon(icon_path)
            else:
                return QIcon()
        return self.icon_cache[theme_key][icon_file]

    def setup_ui(self):
        """전체 UI 레이아웃 및 여백 설정"""
        main_layout = QHBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 사이드바
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(dp(260))
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, dp(50), 0, dp(30)) # 상하 여백 확대
        sidebar_layout.setSpacing(dp(4))
        # [수정] 버튼들이 남는 공간을 나눠 갖지 않고 위로 딱 붙도록 정렬 설정
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo_path = resource_path(os.path.join("ui", "assets", "logo.png"))
        logo_label = QLabel()
        if os.path.exists(logo_path):
            from PySide6.QtGui import QPixmap
            # 로고 크기 보정
            pixmap = QPixmap(logo_path).scaled(dp(100), dp(100), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("Lullit")
        
        logo_label.setObjectName("LogoText")
        logo_label.setContentsMargins(dp(30), 0, 0, dp(30))
        sidebar_layout.addWidget(logo_label)

        menus = [
            ("홈", True, "house.svg"), 
            ("스트레칭 클래스", False, "heart-plus.svg"), 
            ("추천 샵", False, "shopping-bag.svg"), 
            ("알림 상세 설정", False, "monitor-cog.svg"), 
            ("고급 설정", False, "settings.svg")
        ]
        self.buttons = []
        icon_dir = resource_path(os.path.join("ui", "assets", "icons"))
        
        for i, (m, is_home, icon_file) in enumerate(menus):
            btn = QPushButton(f"  {m}")
            btn.setObjectName("MenuButton")
            
            # 아이콘 설정
            icon_path = os.path.join(icon_dir, icon_file)
            if os.path.exists(icon_path):
                from PySide6.QtGui import QIcon
                btn.setIcon(QIcon(icon_path))
                from PySide6.QtCore import QSize
                # 아이콘 크기 보정
                btn.setIconSize(QSize(dp(20), dp(20)))
                
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if is_home:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)
            
        # [수정] 상단 메뉴와 마이페이지 사이의 넓은 간격을 제거합니다. (일반 메뉴와 동일 간격 유지)

        self.profile_btn = QPushButton("  마이페이지")
        self.profile_btn.setObjectName("MenuButton")
        
        # 마이페이지 아이콘 설정
        user_icon_path = os.path.join(icon_dir, "user.svg")
        if os.path.exists(user_icon_path):
            from PySide6.QtGui import QIcon
            self.profile_btn.setIcon(QIcon(user_icon_path))
            from PySide6.QtCore import QSize
            self.profile_btn.setIconSize(QSize(dp(20), dp(20)))
            
        self.profile_btn.setCheckable(True)
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_btn.clicked.connect(lambda: self.switch_page(5))
        # profile_btn은 switch_page 인덱스 관리를 위해 리스트에 넣되, 
        # addWidget은 addStretch 이후에 확실히 위치시킴
        self.buttons.append(self.profile_btn)
        sidebar_layout.addWidget(self.profile_btn)

        profile_widget = QFrame()
        profile_widget.setObjectName("ProfileWidget")
        profile_layout = QHBoxLayout(profile_widget)
        profile_layout.setContentsMargins(dp(20), dp(18), dp(20), dp(18))
        
        avatar = QLabel()
        avatar.setFixedSize(dp(36), dp(36))
        avatar.setStyleSheet(f"background-color: #2C2C2E; border-radius: {dp(18)}px;")
        
        profile_text = QLabel("로그인이 필요합니다")
        profile_text.setObjectName("ProfileText")
        
        profile_layout.addWidget(avatar)
        profile_layout.addWidget(profile_text)
        profile_layout.addStretch()
        
        sidebar_layout.addWidget(profile_widget)

        # 피드백 링크 영역
        self.feedback_btn = QPushButton("  앱 개선 의견 보내기")
        self.feedback_btn.setObjectName("FeedbackBtn")
        
        # 피드백 아이콘 설정
        fb_icon_path = os.path.join(icon_dir, "megaphone.svg")
        if os.path.exists(fb_icon_path):
            from PySide6.QtGui import QIcon
            self.feedback_btn.setIcon(QIcon(fb_icon_path))
            from PySide6.QtCore import QSize
            self.feedback_btn.setIconSize(QSize(dp(16), dp(16)))
            
        self.feedback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.feedback_btn.clicked.connect(self.open_feedback_link)
        sidebar_layout.addWidget(self.feedback_btn)

        # [추가] 앱 완전 종료 버튼
        self.exit_btn = QPushButton("  Lullit 완전히 종료하기")
        self.exit_btn.setObjectName("ExitBtn")
        
        # 종료 아이콘 설정
        exit_icon_path = os.path.join(icon_dir, "x.svg")
        if os.path.exists(exit_icon_path):
            from PySide6.QtGui import QIcon
            self.exit_btn.setIcon(QIcon(exit_icon_path))
            from PySide6.QtCore import QSize
            self.exit_btn.setIconSize(QSize(dp(16), dp(16)))
            
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.clicked.connect(self.quit_application)
        sidebar_layout.addWidget(self.exit_btn)

        # 메인 콘텐츠 영역 (지연 로딩 적용)
        self.stack = QStackedWidget()
        
        # 페이지 초기화 함수 등록
        self.page_builders = [
            self.setup_home_page,
            self.setup_stretching_class_page,
            lambda: self.stack.insertWidget(2, self.create_placeholder_page("추천 샵", "당신의 건강을 위한 아이템을 준비 중입니다.")),
            self.setup_alarm_settings_page,
            self.setup_advanced_settings_page,
            lambda: self.stack.insertWidget(5, self.create_placeholder_page("마이페이지", "나의 기록과 성과를 곧 여기서 확인하세요."))
        ]
        
        # 빈 위젯들로 채워넣어 인덱스 유지
        for _ in range(len(self.page_builders)):
            self.stack.addWidget(QWidget())
            
        # [수정] 사이드바와 스택을 먼저 레이아웃에 추가하여 높이를 확보합니다.
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        # [수정] 0번(홈) 페이지 빌드를 레이아웃 추가 이후로 이동
        self.build_page(0)
        self.stack.setCurrentIndex(0)

        # 닫기 버튼 (부모를 self로 변경하여 컨테이너 여백에 잘리지 않도록 함)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setObjectName("WindowCloseBtn")
        self.close_btn.setFixedSize(dp(44), dp(44))
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # 초기 위치 설정 (이후 resizeEvent에서 계속 업데이트됨)
        self.update_close_btn_position()
        self.close_btn.clicked.connect(self.hide)
        self.close_btn.raise_() # 버튼을 다른 위젯보다 위로 올림        
        
        # [추가] 초기 테마 적용
        self.apply_theme()
        
        # [추가] 초기 레이아웃 강제 갱신 (사이드바 메뉴 간격이 좁게 보이는 현상 방지)
        # 사이드바 레이아웃과 메인 컨테이너 레이아웃을 모두 강제 활성화합니다.
        if self.sidebar.layout():
            self.sidebar.layout().activate()
        
        self.main_container.update()
        if self.main_container.layout():
            self.main_container.layout().activate()

    def update_close_btn_position(self):
        """닫기 버튼을 컨테이너 우측 상단 여백에 맞춰 정확히 배치합니다."""
        if hasattr(self, 'close_btn') and self.close_btn:
            # 창 여백(dp(25)) + 컨테이너 내부 안쪽 여백(dp(15)) 고려
            # 컨테이너 우측 경계는 self.width() - dp(25)
            # 버튼 너비는 dp(44)
            x = self.width() - dp(25) - self.close_btn.width() - dp(10)
            y = dp(25) + dp(10)
            self.close_btn.move(x, y)

    def resizeEvent(self, event):
        """창 크기가 바뀔 때 닫기 버튼의 위치를 다시 잡습니다."""
        super().resizeEvent(event)
        self.update_close_btn_position()

    def show_toast(self, text):
        self.toast.show_message(text)
        try:
            self.toast.anim.finished.disconnect()
        except (TypeError, RuntimeError):
            pass
        
    def create_placeholder_page(self, title, description):
        """빈 화면 처리 (여백 40 적용)"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40)) # 명세서 반영: 여백의 미
        
        t_label = QLabel(title)
        t_label.setObjectName("TitleText")
        t_label.setIndent(0)
        t_label.setContentsMargins(0, 0, 0, 0)
        t_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(t_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        d_label = QLabel(description)
        d_label.setObjectName("BodyText")
        d_label.setIndent(0)
        d_label.setContentsMargins(0, 0, 0, 0)
        d_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(d_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout.addSpacing(dp(50))
        
        card = QFrame()
        card.setObjectName("ContentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(dp(60), dp(60), dp(60), dp(60))
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        msg = QLabel("준비 중인 기능입니다")
        msg.setObjectName("SubTitleText")
        msg.setStyleSheet("color: rgba(255, 255, 255, 0.1);")
        card_layout.addWidget(msg)
        
        layout.addWidget(card)
        layout.addStretch()
        return page

    def setup_home_page(self):
        # [추가] 중복 생성 방지 가드
        if hasattr(self, 'home_page') and self.home_page is not None:
            return self.home_page
            
        page = QWidget()
        self.home_page = page
        layout = QVBoxLayout(page)
        layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40)) # 명세서 반영: 여백의 미
        
        title = QLabel("오늘의 요약")
        title.setObjectName("TitleText")
        title.setIndent(0) # 내부 들여쓰기 제거
        title.setContentsMargins(0, 0, 0, 0) # 위젯 여백 제거
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.alarm_count = 0
        self.desc = QLabel(f"지금까지 {self.alarm_count}회의 스트레칭 알림이 울렸어요.\n꾸준한 스트레칭 습관을 만들어 봐요!")
        self.desc.setObjectName("BodyText")
        self.desc.setIndent(0) # 내부 들여쓰기 제거
        self.desc.setContentsMargins(0, 0, 0, 0) # 위젯 여백 제거
        self.desc.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.desc, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout.addSpacing(dp(50))
        
        card = QFrame()
        card.setObjectName("ContentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40))
        card_layout.setSpacing(dp(25))
        
        self.progress_label = QLabel("다음 스트레칭까지 100% 남았어요.")
        self.progress_label.setObjectName("SubTitleText")
        card_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(dp(16))
        self.progress_bar.setTextVisible(False)
        
        card_layout.addWidget(self.progress_bar)
        
        # 카드의 중간 여백 확보
        card_layout.addStretch()
        
        # [수정] 팁 리스트 대신 팝업을 띄우는 링크 버튼 추가
        self.tips_btn = QPushButton("  Lullit 이용 팁 확인하기")
        self.tips_btn.setObjectName("LegalLinkBtn") # 이용약관과 동일한 스타일 적용
        
        # 팁 아이콘 설정 (초기 로드용)
        is_dark = self.config_manager.get("dark_mode", True) if self.config_manager else True
        # 다크 모드(배경 어두움) -> theme_dark (흰색 아이콘)
        # 라이트 모드(배경 밝음) -> theme_light (검정 아이콘)
        theme_folder = "theme_dark" if is_dark else "theme_light"
        tip_icon_path = resource_path(os.path.join("ui", "assets", "icons", theme_folder, "lightbulb.svg"))
        if os.path.exists(tip_icon_path):
            from PySide6.QtGui import QIcon
            from PySide6.QtCore import QSize
            self.tips_btn.setIcon(QIcon(tip_icon_path))
            self.tips_btn.setIconSize(QSize(dp(18), dp(18)))
            
        self.tips_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tips_btn.clicked.connect(self.show_usage_tips)
        
        # 레이아웃 정중앙 하단에 배치
        card_layout.addWidget(self.tips_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(dp(10))
        
        layout.addWidget(card)
        layout.addSpacing(dp(30))

        # [개선] 버튼 영역 가로 배치 (리포트 & 테스트 알림)
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(dp(12)) # 버튼 사이 간격
        btns_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. 활동 분석 리포트 버튼
        self.report_btn = QPushButton("활동 분석 리포트 확인")
        self.report_btn.setObjectName("PrimaryBtn") 
        self.report_btn.setFixedSize(dp(220), dp(56))
        self.report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.report_btn.clicked.connect(self.show_analysis_report)
        btns_layout.addWidget(self.report_btn)

        # 2. 테스트 알림 실행 버튼
        self.quick_btn = QPushButton("테스트 알림 실행")
        self.quick_btn.setObjectName("PrimaryBtn") # 스타일 통일
        self.quick_btn.setFixedSize(dp(220), dp(56))
        self.quick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quick_btn.clicked.connect(self.trigger_quick_action)
        btns_layout.addWidget(self.quick_btn)

        layout.addLayout(btns_layout)
        
        layout.addStretch()
        self.stack.insertWidget(0, page)

    def setup_stretching_class_page(self):
        # [구조 변경] 내부 스택을 두어 목록 <-> 상세 전환 구현
        self.class_stack = QStackedWidget()
        
        # 1. 카테고리 목록 뷰 생성
        self.categories_view = self.create_class_categories_view()
        self.class_stack.addWidget(self.categories_view)
        
        # 2. 상세 보기 뷰 (초기엔 빈 위젯)
        self.detail_view = QWidget()
        self.class_stack.addWidget(self.detail_view)
        
        # 메인 스택에 추가
        self.stack.insertWidget(1, self.class_stack)

    def create_class_categories_view(self):
        """부위별 카테고리 카드 목록을 보여주는 뷰"""
        from core.stretches_data import STRETCHING_CLASSES
        from PySide6.QtWidgets import QGridLayout, QSizePolicy
        
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40))
        
        title = QLabel("스트레칭 클래스")
        title.setObjectName("TitleText")
        title.setIndent(0)
        title.setContentsMargins(0, 0, 0, 0)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        
        desc = QLabel("앉아서 하기 좋은 부위별 맞춤 스트레칭을 확인할 수 있어요.")
        desc.setObjectName("BodyText")
        desc.setIndent(0)
        desc.setContentsMargins(0, 0, 0, 0)
        desc.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(dp(30))
        
        grid = QGridLayout()
        grid.setSpacing(dp(20))
        
        for i, (category, data) in enumerate(STRETCHING_CLASSES.items()):
            # ClickableCard 클래스 사용 (상단에 정의됨)
            card = ClickableCard()
            card.setObjectName("ContentCard")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # 클릭 시 상세 보기로 전환
            card.clicked.connect(lambda cat=category, items=data['items']: self.show_class_detail(cat, items))
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(dp(25), dp(25), dp(25), dp(25))
            card_layout.setSpacing(dp(12))
            
            cat_label = QLabel(category)
            cat_label.setObjectName("SubTitleText")
            cat_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            cat_label.setStyleSheet(f"font-size: {dp(22)}px; font-weight: bold; color: #33BA25;")
            card_layout.addWidget(cat_label)
            
            # [수정] 미니멀한 한 줄 요약 표시
            summary = data.get('summary', "스트레칭 준비 중")
            sum_label = QLabel(summary)
            sum_label.setObjectName("CaptionText")
            sum_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            sum_label.setWordWrap(True)
            sum_label.setStyleSheet(f"color: #A1A1A6; font-size: {dp(16)}px; line-height: 1.4;")
            card_layout.addWidget(sum_label)
            
            card_layout.addStretch()
            
            tag_layout = QHBoxLayout()
            tag_layout.setSpacing(dp(8))
            count_tag = QLabel(f" {len(data['items'])}개 동작 ")
            count_tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            count_tag.setStyleSheet(f"background-color: rgba(51, 186, 37, 0.1); color: #33BA25; border-radius: {dp(6)}px; padding: {dp(4)}px {dp(8)}px; font-size: {dp(12)}px; font-weight: bold;")
            tag_layout.addWidget(count_tag)
            tag_layout.addStretch()
            
            arrow = QLabel("→")
            arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            arrow.setStyleSheet(f"font-size: {dp(20)}px; color: #33BA25; font-weight: bold;")
            tag_layout.addWidget(arrow)
            card_layout.addLayout(tag_layout)
            
            grid.addWidget(card, i // 2, i % 2)
            
        layout.addLayout(grid)
        layout.addStretch()
        return view

    def show_class_detail(self, category, items):
        """특정 부위의 스트레칭 상세 페이지를 빌드하고 전환합니다."""
        if hasattr(self, 'detail_view'):
            self.class_stack.removeWidget(self.detail_view)
            self.detail_view.deleteLater()
            
        self.detail_view = QWidget()
        self.detail_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self.detail_view)
        layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40))
        
        # 상단 헤더
        header_layout = QHBoxLayout()
        back_btn = QPushButton("←")
        back_btn.setFixedSize(dp(40), dp(40))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(scale_qss("""
            QPushButton { 
                background: transparent; color: #33BA25; font-size: 24px; border: none; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(51, 186, 37, 0.1); border-radius: 20px; }
        """))
        back_btn.clicked.connect(lambda: self.class_stack.setCurrentIndex(0))
        
        title = QLabel(f"{category} 클래스")
        title.setObjectName("TitleText")
        title.setIndent(0)
        title.setContentsMargins(0, 0, 0, 0)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addWidget(back_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        layout.addSpacing(dp(10))
        desc = QLabel(f"지친 {category} 부위를 시원하게 풀어주는 스트레칭 모음")
        desc.setObjectName("BodyText")
        desc.setIndent(0)
        desc.setContentsMargins(0, 0, 0, 0)
        desc.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(dp(30))
        
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        item_layout = QVBoxLayout(scroll_content)
        item_layout.setSpacing(dp(20))
        item_layout.setContentsMargins(0, 0, dp(15), 0)
        
        # 현재 테마 파악 (명확한 구분)
        is_dark = True
        if self.config_manager:
            is_dark = self.config_manager.get("theme_mode", "dark") != "light"
        elif hasattr(self, 'dark_cb') and self.dark_cb:
            is_dark = self.dark_cb.isChecked()
            
        theme_str = "dark" if is_dark else "light"
        self.detail_view.setProperty("theme", theme_str)

        # 색상 정의 (다크/라이트 명확히 구분)
        primary_text = "#FFFFFF" if is_dark else "#1C1C1E"
        secondary_text = "#A1A1A6" if is_dark else "#3C3C43"
        card_bg = "rgba(255, 255, 255, 0.03)" if is_dark else "rgba(0, 0, 0, 0.03)"
        
        for item in items:
            item_card = QFrame()
            item_card.setObjectName("ContentCard")
            item_card.setProperty("theme", theme_str) # 카드별 테마 주입
            
            # 테마에 따른 배경색과 둥근 모서리 적용
            item_card.setStyleSheet(f"""
                QFrame#ContentCard {{
                    background-color: {card_bg};
                    border-radius: {dp(18)}px;
                    border: 1px solid {('rgba(255,255,255,0.05)' if is_dark else 'rgba(0,0,0,0.05)')};
                }}
            """)
            
            box_vbox = QVBoxLayout(item_card)
            box_vbox.setContentsMargins(dp(25), dp(25), dp(25), dp(25))
            
            top_hbx = QHBoxLayout()
            name_lbl = QLabel(item['title'])
            name_lbl.setStyleSheet(f"font-size: {dp(20)}px; font-weight: bold; color: {primary_text}; background: transparent;")
            
            top_hbx.addWidget(name_lbl)
            top_hbx.addStretch()
            box_vbox.addLayout(top_hbx)
            
            box_vbox.addSpacing(dp(12))
            
            desc_lbl = QLabel(item['desc'])
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"font-size: {dp(16)}px; color: {secondary_text}; line-height: 1.5; background: transparent;")
            box_vbox.addWidget(desc_lbl)
            
            item_layout.addWidget(item_card)
            
        item_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.class_stack.addWidget(self.detail_view)
        self.class_stack.setCurrentIndex(1)
        
        # 전체 테마 전파 및 강제 갱신 (핵심 보강)
        def force_refresh_theme(parent):
            parent.style().unpolish(parent)
            parent.style().polish(parent)
            for child in parent.findChildren(QWidget):
                child.setProperty("theme", theme_str)
                child.style().unpolish(child)
                child.style().polish(child)
        
        force_refresh_theme(self.detail_view)

    def go_back_to_categories(self):
        """상세 보기에서 목록으로 돌아가며 메모리 정리"""
        self.class_stack.setCurrentIndex(0)
        if hasattr(self, 'detail_view') and self.detail_view:
            # 상세 뷰를 스택에서 제거하고 즉시 삭제 예약
            self.class_stack.removeWidget(self.detail_view)
            self.detail_view.deleteLater()
            self.detail_view = None
            
        # 즉시 메모리 회수 유도
        import gc
        gc.collect()

    def setup_alarm_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40))
        
        title = QLabel("알림 상세 설정")
        title.setObjectName("TitleText")
        title.setIndent(0)
        title.setContentsMargins(0, 0, 0, 0)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        
        desc = QLabel("알림 설정을 확인할 수 있어요.")
        desc.setObjectName("BodyText")
        desc.setIndent(0)
        desc.setContentsMargins(0, 0, 0, 0)
        desc.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignLeft)
        # [수정] 상단 여백을 50 -> 30으로 소폭 줄여 여유를 확보합니다.
        layout.addSpacing(dp(30))
        
        card = QFrame()
        card.setObjectName("ContentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40))
        # [수정] 내부 항목 간격을 30 -> 25로 소폭 줄입니다.
        card_layout.setSpacing(dp(25))
        
        char_label = QLabel("알림 캐릭터 선택(준비 중)")
        char_label.setObjectName("SubTitleText")
        char_label.setIndent(0)
        char_label.setContentsMargins(0, 0, 0, 0)
        char_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(char_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.char_combo = QComboBox()
        self.char_combo.addItems(["기본 캐릭터"])
        self.char_combo.setEnabled(False)
        card_layout.addWidget(self.char_combo)
        
        # 알림 주기 설정 (QSpinBox)
        interval_label = QLabel("기본 알림 주기")
        interval_label.setObjectName("SubTitleText")
        interval_label.setIndent(0)
        interval_label.setContentsMargins(0, 0, 0, 0)
        interval_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(interval_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        interval_info = QLabel("5분에서 120분 사이로 자유롭게 설정할 수 있어요.")
        interval_info.setObjectName("BodyText")
        interval_info.setIndent(0)
        interval_info.setContentsMargins(0, 0, 0, 0)
        interval_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(interval_info, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 120)
        self.interval_spin.setSuffix(" 분")
        current_val = self.config_manager.get("alarm_interval_minutes") if self.config_manager else 60
        self.interval_spin.setValue(current_val)
        self.interval_spin.setFixedSize(dp(140), dp(48)) # 입력창 크기 최적화
        card_layout.addWidget(self.interval_spin, alignment=Qt.AlignmentFlag.AlignLeft)

        card_layout.addSpacing(dp(15)) # 항목 간 간격 확보

        # 오버레이 투명도 설정 (QSlider)
        opacity_label = QLabel("알림 투명도")
        opacity_label.setObjectName("SubTitleText")
        opacity_label.setIndent(0)
        opacity_label.setContentsMargins(0, 0, 0, 0)
        opacity_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(opacity_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        opacity_info = QLabel("알림 투명도를 자유롭게 설정할 수 있어요.")
        opacity_info.setObjectName("BodyText")
        opacity_info.setIndent(0)
        opacity_info.setContentsMargins(0, 0, 0, 0)
        opacity_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(opacity_info, alignment=Qt.AlignmentFlag.AlignLeft)
        
        opacity_layout = QHBoxLayout()
        opacity_layout.setContentsMargins(0, dp(5), 0, dp(5))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        current_opacity = int((self.config_manager.get("overlay_opacity") or 0.75) * 100)
        self.opacity_slider.setValue(current_opacity)
        
        self.opacity_value_label = QLabel(f"{current_opacity}%")
        self.opacity_value_label.setObjectName("BodyText")
        self.opacity_value_label.setStyleSheet("font-weight: bold; color: #33BA25;")
        self.opacity_value_label.setFixedWidth(dp(50))
        
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_value_label.setText(f"{v}%"))
        
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value_label)
        card_layout.addLayout(opacity_layout)
        
        layout.addWidget(card)
        layout.addSpacing(dp(30))
        
        save_btn = QPushButton("알림 설정 저장")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setFixedSize(dp(200), dp(56))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_alarm_settings)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        self.stack.insertWidget(3, page)

    def save_alarm_settings(self):
        if self.config_manager:
            minutes = self.interval_spin.value()
            opacity = self.opacity_slider.value() / 100.0
            
            self.config_manager.set("alarm_interval_minutes", minutes)
            self.config_manager.set("overlay_opacity", opacity)
            
            # 엔진의 피로도 임계값 즉시 업데이트
            if hasattr(self.engine, 'update_threshold'):
                self.engine.update_threshold()
                
            self.show_toast(f"설정이 저장되었습니다.")

    def setup_advanced_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40))
        
        title = QLabel("고급 설정")
        title.setObjectName("TitleText")
        title.setIndent(0)
        title.setContentsMargins(0, 0, 0, 0)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        
        desc = QLabel("시스템 환경 및 애플리케이션 정보를 확인할 수 있어요.")
        desc.setObjectName("BodyText")
        desc.setIndent(0)
        desc.setContentsMargins(0, 0, 0, 0)
        desc.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(dp(50))
        
        card = QFrame()
        card.setObjectName("ContentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(dp(40), dp(40), dp(40), dp(40))
        card_layout.setSpacing(dp(25))
        
        self.startup_cb = QCheckBox("컴퓨터 부팅 시 자동 실행")
        is_startup = self.config_manager.get("run_on_startup") or False if self.config_manager else False
        self.startup_cb.setChecked(is_startup)
        card_layout.addWidget(self.startup_cb)
        
        # [개편] 테마 설정 드롭다운 (라이트 / 다크 / 시스템)
        theme_label = QLabel("테마 설정")
        theme_label.setObjectName("SubTitleText")
        theme_label.setIndent(0)
        theme_label.setContentsMargins(0, 0, 0, 0)
        theme_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(theme_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["밝은 테마", "어두운 테마"])

        # 기존 설정값 불러오기 (기본값: 다크 모드)
        current_theme = self.config_manager.get("theme_mode", "dark")
        theme_map = {"light": 0, "dark": 1}
        self.theme_combo.setCurrentIndex(theme_map.get(current_theme, 1))

        card_layout.addWidget(self.theme_combo)        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(255,255,255,0.05); border: none; height: 1px;")
        card_layout.addWidget(line)
        
        info_title = QLabel("App Info")
        info_title.setObjectName("SubTitleText") # TitleText보다 약간 작은 SubTitleText 스타일 활용
        info_title.setIndent(0)
        info_title.setContentsMargins(0, 0, 0, 0)
        info_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(info_title, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.version_label = QLabel("버전: 0.4.0 (Beta)\n마지막 업데이트: 2026.04.06")
        self.version_label.setObjectName("CaptionText")
        self.version_label.setIndent(0)
        self.version_label.setContentsMargins(0, 0, 0, 0)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(self.version_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # 법적 고지 링크
        legal_layout = QHBoxLayout()
        legal_layout.setSpacing(dp(15))
        
        self.tos_btn = QPushButton("이용약관")
        self.tos_btn.setObjectName("LegalLinkBtn")
        self.tos_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tos_btn.clicked.connect(self.show_tos)
        
        self.pp_btn = QPushButton("개인정보 처리방침")
        self.pp_btn.setObjectName("LegalLinkBtn")
        self.pp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pp_btn.clicked.connect(self.show_pp)
        
        legal_layout.addWidget(self.tos_btn)
        legal_layout.addWidget(self.pp_btn)
        legal_layout.addStretch()
        card_layout.addLayout(legal_layout)
        
        layout.addWidget(card)
        layout.addSpacing(30)

        save_btn = QPushButton("설정 저장")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setFixedSize(dp(200), dp(56))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_advanced_settings)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        self.stack.insertWidget(4, page)
        
    def apply_theme(self):
        """다크/라이트 모드 테마를 모든 하위 위젯에 효율적으로 적용합니다."""
        if hasattr(self, 'theme_combo') and self.theme_combo:
            theme_idx = self.theme_combo.currentIndex()
        else:
            current_theme = self.config_manager.get("theme_mode", "dark")
            theme_idx = {"light": 0, "dark": 1}.get(current_theme, 1)

        is_dark = (theme_idx == 1)
            
        theme_str = "dark" if is_dark else "light"
        theme_folder = "theme_dark" if is_dark else "theme_light"
        
        # 1. 테마 속성 변경이 필요한 경우에만 전파
        if self.property("theme") != theme_str:
            def refresh_widget_recursive(w):
                w.setProperty("theme", theme_str)
                w.style().unpolish(w)
                w.style().polish(w)
                for child in w.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
                    refresh_widget_recursive(child)

            self.setProperty("theme", theme_str)
            for child in self.findChildren(QWidget):
                # 콤보박스 뷰 등 특수 위젯 처리
                if child.property("theme") != theme_str:
                    child.setProperty("theme", theme_str)
                    child.style().unpolish(child)
                    child.style().polish(child)
                    if isinstance(child, QComboBox):
                        view = child.view()
                        if view:
                            view.setProperty("theme", theme_str)
                            view.style().unpolish(view)
                            view.style().polish(view)

            # 그림자 효과 테마 대응
            if self.shadow:
                if is_dark:
                    self.shadow.setColor(QColor(0, 0, 0, 150))
                    self.shadow.setBlurRadius(40)
                else:
                    self.shadow.setColor(QColor(0, 0, 0, 30))
                    self.shadow.setBlurRadius(30)

        # 2. 아이콘 교체 (테마 폴더가 바뀐 경우에만)
        if self._current_theme_folder != theme_folder:
            self._current_theme_folder = theme_folder
            
            menus_icons = ["house.svg", "heart-plus.svg", "shopping-bag.svg", "monitor-cog.svg", "settings.svg"]
            for i, icon_file in enumerate(menus_icons):
                if i < len(self.buttons):
                    self.buttons[i].setIcon(self.get_themed_icon(theme_folder, icon_file))
            
            special_icons = {
                self.profile_btn: "user.svg",
                self.feedback_btn: "megaphone.svg",
                self.exit_btn: "x.svg",
                self.tips_btn: "lightbulb.svg"
            }
            for btn, file_name in special_icons.items():
                if btn:
                    btn.setIcon(self.get_themed_icon(theme_folder, file_name))
        
        if hasattr(self, 'toast') and self.toast:
            self.toast.update_style()

        if self.config_manager:
            self.config_manager.set("dark_mode", is_dark)
            
        # 페이지 전환 및 테마 변경 후에는 선별적으로 GC 호출
        import gc
        gc.collect(1) # 1세대만 수집하여 오버헤드 감소

    def save_advanced_settings(self):
        if self.config_manager:
            # 1. 자동 실행 설정 저장
            startup_checked = self.startup_cb.isChecked()
            self.config_manager.set("run_on_startup", startup_checked)
            set_run_on_startup(startup_checked)
            
            # 2. 테마 모드 설정 저장 (라이트 / 다크)
            theme_idx = self.theme_combo.currentIndex()
            theme_mode = ["light", "dark"][theme_idx]
            self.config_manager.set("theme_mode", theme_mode)
            
            # 3. 테마 즉시 적용
            self.apply_theme()
            
            # 4. 저장 완료 토스트 알림
            self.show_toast("설정이 저장되었습니다.")

    def trigger_quick_action(self):
        self.engine.current_score = self.engine.FATIGUE_THRESHOLD
        self.engine.threshold_reached.emit()
        self.engine.reset_score()

    def update_progress(self, current, threshold):
        percent = int(min(100, (current / threshold) * 100))
        self.progress_bar.setValue(percent)
        rem = 100 - percent
        if rem <= 0:
            self.progress_label.setText("잠시 스트레칭할 시간이에요!")
        else:
            self.progress_label.setText(f"피로도 임계점까지 약 {rem}% 남았습니다.")

    def update_stats(self, kbd, click, dist):
        """실시간 활동 통계 변수만 업데이트 (AI 분석용)"""
        self.current_kbd = kbd
        self.current_click = click
        self.current_dist = dist

    def show_analysis_report(self):
        """기존 팝업(DocumentViewer)과 동일한 디자인의 활동 분석 리포트 (버튼 제거 및 텍스트 최적화)"""
        from PySide6.QtWidgets import QDialog, QFrame, QGridLayout, QGraphicsDropShadowEffect
        from PySide6.QtGui import QGuiApplication, QColor
        
        # 0. 현재 테마 상태 파악 (config_manager 기준)
        is_dark = self.config_manager.get("dark_mode", True) if self.config_manager else True
        theme_str = "dark" if is_dark else "light"
        
        # 1. 물리적 이동 거리 계산 (DPI 기반)
        screen = QGuiApplication.primaryScreen()
        physical_dpi = screen.physicalDotsPerInch()
        meters = (self.current_dist / physical_dpi) * 0.0254
        
        # 2. 다이얼로그 기본 설정
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dialog.setFixedSize(dp(480), dp(460)) # 버튼이 빠지므로 높이를 적절히 조절
        
        # 부모 중앙 배치
        dialog.move(self.geometry().center() - dialog.rect().center())
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(dp(20), dp(20), dp(20), dp(20))
        
        # 컨테이너 (QSS의 #DocViewer 스타일 적용)
        container = QFrame()
        container.setObjectName("DocViewer")
        container.setProperty("theme", theme_str)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(dp(36), dp(40), dp(36), dp(40)) # 상하 여백 확대
        layout.setSpacing(dp(30)) # 요소 간 간격 확대
        
        # 헤더 (제목 + 닫기 버튼)
        header = QHBoxLayout()
        header.setSpacing(0)
        title_label = QLabel("활동 분석 리포트")
        title_label.setObjectName("DocTitle")
        title_label.setProperty("theme", theme_str)
        title_label.setFixedHeight(dp(36)) # 제목 높이 고정 (잘림 방지)
        header.addWidget(title_label)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(dp(32), dp(32))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { 
                background: transparent; color: #8E8E93; font-size: 22px; border: none; 
            }
            QPushButton:hover { color: #FF453A; }
        """)
        close_btn.clicked.connect(dialog.reject)
        header.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)
        
        # 본문 설명
        desc_label = QLabel("현재까지 수집된 행동 데이터입니다. 이 데이터는 AI 분석을 위한 기초 지표로 활용됩니다.")
        desc_label.setObjectName("DocContent")
        desc_label.setProperty("theme", theme_str)
        desc_label.setWordWrap(True)
        desc_label.setMinimumHeight(dp(64)) # 설명 영역 높이 충분히 확보
        layout.addWidget(desc_label)
        
        # 데이터 리스트 영역
        data_container = QFrame()
        data_layout = QVBoxLayout(data_container)
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_layout.setSpacing(dp(24)) # 행 간 간격 확대
        
        # 아이템 추가 함수
        def add_data_item(label_text, value_text):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"font-size: 16px; color: {'white' if is_dark else '#1C1C1E'}; font-weight: 500; background: transparent;")
            lbl.setFixedHeight(dp(24)) # 텍스트 높이 고정
            
            val = QLabel(value_text)
            val.setStyleSheet(f"font-size: 18px; color: {'#4CAF50' if is_dark else '#388E3C'}; font-weight: 700; background: transparent;")
            val.setFixedHeight(dp(24)) # 텍스트 높이 고정
            
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFixedHeight(1)
            line.setStyleSheet(f"background-color: {'rgba(255,255,255,0.08)' if is_dark else 'rgba(0,0,0,0.06)'}; border: none;")
            
            data_layout.addLayout(row)
            data_layout.addWidget(line)

        add_data_item("키보드 입력 횟수", f"{self.current_kbd:,}회")
        add_data_item("마우스 클릭 횟수", f"{self.current_click:,}회")
        add_data_item("마우스 이동 거리", f"{meters:.2f}m")
        
        layout.addWidget(data_container)
        layout.addStretch() # 하단 여백 자연스럽게 확보
        
        # 그림자 효과
        shadow = QGraphicsDropShadowEffect(dialog)
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(12)
        shadow.setColor(QColor(0, 0, 0, 160) if is_dark else QColor(0, 0, 0, 50))
        container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(container)
        dialog.exec()
            
    def increment_alarm_count(self):
        self.alarm_count += 1
        self.desc.setText(f"지금까지 {self.alarm_count}회의 스트레칭 알림이 울렸어요.\n꾸준한 스트레칭 습관을 만들어 봐요!")

    def build_page(self, index):
        """해당 인덱스의 페이지가 아직 생성되지 않았다면 생성합니다."""
        if index < 0 or index >= len(self.page_builders):
            return
            
        # 현재 해당 인덱스의 위젯 확인
        current_widget = self.stack.widget(index)
        
        # 아직 빌드되지 않은 경우 (기본 QWidget이고 is_built 속성이 없는 경우)
        if current_widget and not hasattr(current_widget, "is_built"):
            # 페이지 빌더 실행
            builder = self.page_builders[index]
            if builder:
                # [개선] removeWidget 대신 새로운 위젯을 생성하여 기존 인덱스에 replace
                # 레이아웃 흔들림을 방지하기 위해 stack의 현재 인덱스 위젯을 직접 교체
                
                # builder가 함수인 경우(setup_...) 직접 호출하여 위젯 생성 과정을 거치게 함
                # builder가 lambda인 경우 위젯을 반환하거나 stack에 추가함
                
                # 기존 위젯의 레이아웃 영향을 최소화하기 위해 숨김 처리
                current_widget.hide()
                
                # 페이지 빌드 (builder 내부에서 stack.insertWidget 등을 수행)
                builder()
                
                # 새로 생성된 위젯 가져오기
                new_widget = self.stack.widget(index)
                
                if new_widget and new_widget != current_widget:
                    new_widget.is_built = True
                    
                    # 기존 빈 위젯 제거
                    self.stack.removeWidget(current_widget)
                    current_widget.deleteLater()
                    
                    # 현재 앱의 테마 상태 확인
                    is_dark = True
                    if self.config_manager:
                        is_dark = self.config_manager.get("dark_mode", True)
                    elif hasattr(self, 'dark_cb') and self.dark_cb:
                        is_dark = self.dark_cb.isChecked()
                    
                    theme_str = "dark" if is_dark else "light"
                    new_widget.setProperty("theme", theme_str)
                    
                    # 자식 위젯들에게도 테마 전파
                    def apply_to_children(parent):
                        for child in parent.findChildren(QWidget):
                            child.setProperty("theme", theme_str)
                            child.style().unpolish(child)
                            child.style().polish(child)
                    
                    apply_to_children(new_widget)
                    new_widget.style().unpolish(new_widget)
                    new_widget.style().polish(new_widget)
                
                # 레이아웃 즉시 업데이트 강제
                self.stack.updateGeometry()
                if self.main_container.layout():
                    self.main_container.layout().activate()
                    
                # 메모리 해제 유도
                import gc
                gc.collect()

    def switch_page(self, index):
        # 페이지가 빌드되지 않았다면 빌드
        self.build_page(index)
        
        # [추가] 메뉴 진입 시 상태 초기화 및 설정 동기화
        if index == 1: # 스트레칭 클래스
            if hasattr(self, 'class_stack'):
                self.class_stack.setCurrentIndex(0)
        
        elif index == 3: # 알림 상세 설정
            if self.config_manager:
                # 저장된 최신 값으로 UI 새로고침 (저장 안 한 변경사항 폐기)
                minutes = self.config_manager.get("alarm_interval_minutes") or 60
                opacity = int((self.config_manager.get("overlay_opacity") or 0.75) * 100)
                if hasattr(self, 'interval_spin'): self.interval_spin.setValue(minutes)
                if hasattr(self, 'opacity_slider'): self.opacity_slider.setValue(opacity)
                
        elif index == 4: # 고급 설정
            if self.config_manager:
                is_startup = self.config_manager.get("run_on_startup") or False
                current_theme = self.config_manager.get("theme_mode", "dark")
                theme_map = {"light": 0, "dark": 1}
                if hasattr(self, 'startup_cb'): self.startup_cb.setChecked(is_startup)
                if hasattr(self, 'theme_combo'): self.theme_combo.setCurrentIndex(theme_map.get(current_theme, 1))

        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        
        # [최적화] 페이지 전환 시 적극적인 메모리 회수
        import gc
        gc.collect()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def open_feedback_link(self):
        """구글 폼 링크를 브라우저에서 엽니다."""
        url = "https://docs.google.com/forms/d/e/1FAIpQLSexjn3NoVLStNMewemfT4BDeL_GpUviYn-th984VGjaZ6qhOQ/viewform?usp=publish-editor"
        QDesktopServices.openUrl(QUrl(url))

    def quit_application(self):
        """앱 엔진을 정지하고 프로세스를 완전히 종료합니다."""
        if hasattr(self, 'engine') and self.engine:
            self.engine.stop()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def show_tos(self):
        content = """[이용약관]

제 1 조 (목적)
본 약관은 'Lullit'(이하 '앱')가 제공하는 서비스의 이용 조건 및 절차를 규정함을 목적으로 합니다.

제 2 조 (서비스의 성격)
1. 본 앱은 사용자의 PC 사용 중 정기적인 스트레칭을 유도하는 보조 도구입니다.
2. 본 앱에서 제공하는 정보는 의학적 조언을 대체할 수 없습니다.

제 3 조 (면책 조항)
1. 사용자는 자신의 건강 상태에 맞춰 스트레칭을 수행합니다.
2. 앱 사용 및 스트레칭 수행 중 발생하는 부상, 건강상의 문제 등에 대해 개발자는 어떠한 법적 책임도 지지 않습니다.
3. 시스템 환경이나 오류로 인해 알림이 발생하지 않을 수 있으며, 이로 인한 손해에 대해서도 책임을 지지 않습니다.

제 4 조 (저작권)
본 앱의 소스 코드 및 디자인에 대한 권리는 개발자에게 있습니다.

부칙
본 약관은 2026년 3월 20일부터 시행됩니다."""
        viewer = DocumentViewer("이용약관", content, self)
        viewer.exec()

    def show_pp(self):
        content = """[개인정보 처리방침]

'Lullit'은 사용자의 개인정보를 소중히 다루며, 관련 법령을 준수합니다.

1. 개인정보의 수집 항목
본 앱은 사용자의 성함, 이메일, 연락처, IP 주소 등 어떠한 개인정보도 서버로 전송하거나 수집하지 않습니다.

2. 데이터의 저장
앱의 설정값(알림 주기, 자동 실행 여부 등)은 사용자의 PC 내부(app_config.json)에만 저장되며, 앱 삭제 시 함께 제거될 수 있습니다.

3. 외부 서비스 이용
앱 내의 '의견 보내기' 링크(구글 폼) 이용 시, 사용자가 직접 입력한 정보에 한해 해당 플랫폼의 정책에 따라 수집될 수 있습니다. 이는 사용자의 자발적인 선택에 의합니다.

4. 쿠키 및 자동 수집 장치
본 앱은 쿠키를 사용하지 않으며, 어떠한 행동 로그도 자동으로 수집하지 않습니다.

5. 연락처
개인정보와 관련된 문의사항은 앱 내 피드백 채널을 이용해 주시기 바랍니다.

본 방침은 2026년 3월 20일부터 시행됩니다."""
        viewer = DocumentViewer("개인정보 처리방침", content, self)
        viewer.exec()

    def show_usage_tips(self):
        content = """[Lullit 스마트 이용 팁]

• 설정한 시간보다 알림이 빨리 오는 것 같아요!

사용자의 마우스/키보드 사용이 잦아지면, 앱에서 이를 감지해 기존에 설정한 시간보다 빠르게 알림을 띄워요.

• 앱의 'X' 버튼을 눌러도 알림을 받을 수 있나요?

네.창을 닫아도 앱은 백그라운드에서 계속 실행돼요. 완전한 종료를 위해서는 앱의 'Lullit 완전히 종료하기' 버튼을 누르거나, 트레이 아이콘의 '종료' 버튼을 눌러 주세요.

• 특정 앱에서 알림이 안 보여요.

전체 화면 설정을 한 앱은 알림이 안 보일 수도 있어요. 창 모드나 테두리 없음 설정을 적용하면 알림이 보일 거예요."""
        viewer = DocumentViewer("이용 팁 확인하기", content, self)
        viewer.exec()
