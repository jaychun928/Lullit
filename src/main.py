# -*- coding: utf-8 -*-
import sys
import os
import gc
import datetime
import traceback

# [경로 설정] src 폴더를 sys.path의 최상단에 추가 (모듈 임포트가 가능하도록)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 프로젝트 루트 폴더도 추가 (필요시)
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# GUI 실행 환경에서 sys.stdout/stderr가 None인 경우를 대비한 안전 장치
class SafeStream:
    def __init__(self, original_stream=None, log_file=None):
        self.original_stream = original_stream
        self.log_file = log_file
    def write(self, data):
        if self.original_stream:
            try: self.original_stream.write(data)
            except: pass
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(data)
            except: pass
    def flush(self):
        if self.original_stream:
            try: self.original_stream.flush()
            except: pass

# 실행 파일(frozen) 환경 여부에 따른 로그 디렉토리 결정
# [수정] 권한 문제 방지를 위해 사용자 데이터 폴더(APPDATA)를 기본 로그 경로로 사용
try:
    from core.system_utils import get_data_dir
    LOG_DIR = get_data_dir()
except Exception:
    # 폴백 로직
    if getattr(sys, 'frozen', False):
        LOG_DIR = os.path.dirname(sys.executable)
    else:
        LOG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STDOUT_LOG = os.path.join(LOG_DIR, "stdout_log.txt")
STDERR_LOG = os.path.join(LOG_DIR, "error_log.txt")

sys.stdout = SafeStream(sys.stdout, STDOUT_LOG)
sys.stderr = SafeStream(sys.stderr, STDERR_LOG)

print(f"\n--- [{datetime.datetime.now()}] Lullit v0.4.0 시작 시도 ---")

try:
    # PySide6 핵심 모듈 임포트
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
    from PySide6.QtGui import QIcon, QAction, QColor, QFont
    from PySide6.QtCore import Qt, QCoreApplication, QTimer
    from PySide6.QtNetwork import QLocalServer, QLocalSocket

    # 그래픽 드라이버 호환성 설정 및 폰트 렌더링 최적화
    try:
        # 고해상도 대응 설정 강화
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        # 소프트웨어 렌더링 (호환성용 유지)
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
        
        # [추가] 전역 폰트 렌더링 옵션 (가독성 및 깨짐 방지)
        font = QFont("Pretendard")
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        QApplication.setFont(font)
    except:
        pass
    
    from core.system_utils import resource_path, set_run_on_startup
    print("기본 모듈 로드 완료.")

except Exception as e:
    with open(STDERR_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.datetime.now()}] 임포트 단계 오류: {e}\n{traceback.format_exc()}")
    sys.exit(1)

def get_optimized_tray_icon(logo_path, tray_icon_path, style):
    try:
        from PySide6.QtGui import QPixmap, QImage, QIcon
        from PySide6.QtCore import Qt, QRect
        target_path = tray_icon_path if os.path.exists(tray_icon_path) else logo_path
        if not os.path.exists(target_path): return style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        
        image = QImage(target_path)
        if image.isNull(): return style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        
        if target_path == logo_path:
            width, height = image.width(), image.height()
            # 이미지 크기가 너무 크면 리샘플링하여 메모리 절약
            if width > 128 or height > 128:
                image = image.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
                width, height = image.width(), image.height()

            left, top, right, bottom = width, height, 0, 0
            for y in range(height):
                for x in range(width):
                    if image.pixelColor(x, y).alpha() > 10:
                        if x < left: left = x
                        if x > right: right = x
                        if y < top: top = y
                        if y > bottom: bottom = y
            if left <= right and top <= bottom:
                image = image.copy(QRect(left, top, right - left + 1, bottom - top + 1))
        
        from ui.ui_utils import dp
        final_pixmap = QPixmap.fromImage(image).scaled(dp(32), dp(32), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon = QIcon(final_pixmap)
        
        # 임시 객체 명시적 제거 유도
        del image
        del final_pixmap
        return icon
    except:
        return style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

def main():
    try:
        # [추가] High-DPI 스케일링 설정 (QApplication 생성 전)
        from PySide6.QtCore import Qt, QCoreApplication
        # 소수점 배율(125%, 150%)에서도 텍스트가 흐릿해지지 않게 설정
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        
        # 가비지 컬렉션 임계값 조정 (세대별 수집 빈도 최적화)
        gc.set_threshold(1000, 15, 15)
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # 폰트 설정
        from PySide6.QtGui import QFontDatabase, QFont
        from ui.ui_utils import dp # UI 유틸리티 임포트
        font_dir = resource_path(os.path.join("ui", "assets", "fonts"))
        if os.path.exists(font_dir):
            font_path = os.path.join(font_dir, "Pretendard-Regular.otf")
            if os.path.exists(font_path):
                QFontDatabase.addApplicationFont(font_path)
        
        # 폰트 크기도 화면 배율에 맞춰 동적 조절 (기본 11 -> dp(11))
        app.setFont(QFont("Pretendard", dp(11)))

        # [중복 실행 방지] 하나만 실행되도록 보장
        from PySide6.QtNetwork import QLocalServer, QLocalSocket
        server_name = "Lullit_Single_Instance_Socket"
        
        # 1. 기존 서버에 연결 시도
        check_socket = QLocalSocket()
        check_socket.connectToServer(server_name)
        if check_socket.waitForConnected(500):
            check_socket.write(b"SHOW_WINDOW")
            check_socket.waitForBytesWritten(500)
            check_socket.disconnectFromServer()
            print("이미 실행 중인 앱이 있어 종료합니다.")
            sys.exit(0)
            
        # 2. 서버가 없으면 내가 서버가 됨
        QLocalServer.removeServer(server_name)
        local_server = QLocalServer()
        if not local_server.listen(server_name):
            print(f"로컬 서버 시작 실패: {local_server.errorString()}")

        print("엔진 및 UI 초기화 중...")
        from core.config_manager import ConfigManager
        from core.fatigue_engine import FatigueEngine
        config_manager = ConfigManager()
        set_run_on_startup(config_manager.get("run_on_startup"))
        engine = FatigueEngine(config_manager)
        
        from ui.main_window import MainWindow
        from ui.overlay import StretchOverlay
        main_window = MainWindow(engine, config_manager)
        overlay = StretchOverlay(config_manager)

        # 3. 새로운 연결(중복 실행 시도)이 들어오면 내 창을 보여줌
        def handle_new_connection():
            new_client = local_server.nextPendingConnection()
            if new_client and new_client.waitForReadyRead(500):
                if new_client.readAll().data().decode() == "SHOW_WINDOW":
                    main_window.show()
                    main_window.raise_()
                    main_window.activateWindow()
                new_client.disconnectFromServer()
        
        local_server.newConnection.connect(handle_new_connection)

        engine.threshold_reached.connect(lambda: (main_window.increment_alarm_count(), overlay.show_overlay()))

        # 트레이 아이콘
        logo_path = resource_path(os.path.join("ui", "assets", "logo.png"))
        tray_icon_path = resource_path(os.path.join("ui", "assets", "tray_icon.png"))
        icon = get_optimized_tray_icon(logo_path, tray_icon_path, app.style())
        tray = QSystemTrayIcon(icon, app)
        menu = QMenu()
        menu.addAction("열기").triggered.connect(main_window.show)
        exit_action = menu.addAction("종료")
        exit_action.triggered.connect(lambda: (engine.stop(), app.quit()))
        tray.setContextMenu(menu)
        tray.show()

        print("UI 표시 완료. 엔진을 곧 시작합니다.")
        main_window.show()
        
        # [핵심 보강] UI가 뜬 직후에 엔진 시작 (지연 시간 1초)
        QTimer.singleShot(1000, engine.start)
        
        ret = app.exec()
        sys.exit(ret)
        
    except Exception as e:
        with open(STDERR_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now()}] 치명적 런타임 오류: {e}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
