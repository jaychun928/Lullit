import time
import math
import ctypes
import threading
from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal

# Win32 API를 사용하기 위한 좌표 구조체 정의
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_virtual_cursor_pos():
    """Windows API를 호출하여 현재 마우스 커서의 좌표를 가져옵니다."""
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

class FatigueEngine(QObject):
    """사용자의 입력 활동과 시간을 분석하여 스트레칭 시점을 결정하는 핵심 엔진"""
    
    # UI에 현재 피로도와 목표치를 전달하는 신호
    fatigue_updated = Signal(float, float) # (현재 점수, 목표 점수)
    # [추가] 실시간 분석 데이터를 전달하는 신호 (키보드, 클릭, 이동거리)
    stats_updated = Signal(int, int, float) 
    # 목표 점수에 도달했을 때 알림 팝업을 요청하는 신호
    threshold_reached = Signal()

    @property
    def FATIGUE_THRESHOLD(self):
        """스트레칭 알림이 울리는 목표 점수 (설정된 분 * 60초)"""
        if hasattr(self, 'config_manager') and self.config_manager:
            val = self.config_manager.get("alarm_interval_minutes")
            if val: return float(val * 60)
        return 3600.0  # 기본값: 3600점 (60분 해당)

    # 가중치 상수 정의 (점수 계산 기준)
    TIME_UNIT_SCORE = 1     # 1초당 기본 1점 추가
    MOUSE_CLICK_SCORE = 0.05   # 마우스 클릭 1회당 0.5점 추가
    MOUSE_MOVE_UNIT = 1000.0  # 마우스 이동 거리 1000픽셀당
    MOUSE_MOVE_SCORE = 0.3    # 1.0점 추가
    KEY_INPUT_SCORE = 0.07     # 키보드 입력 1회당 0.2점 추가

    IDLE_DETECTION_TIME = 300.0  # 300초(5분) 동안 입력이 없으면 휴식 상태로 간주
    IDLE_RECOVERY_RATE = 0.1     # 휴식 상태 시 1분마다 현재 점수의 10%를 감소(회복)

    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.current_score = 0.0          # 현재 누적된 피로도 점수
        self.last_input_time = time.time() # 마지막으로 입력이 감지된 시각
        self.accumulated_distance = 0.0   # 1점 단위로 계산하기 위해 누적된 마우스 이동 거리
        self.running = False              # 엔진 작동 상태
        
        # [추가] AI 분석용 실시간 통계 변수
        self.total_kbd_hits = 0
        self.total_mouse_clicks = 0
        self.total_travel_distance = 0.0 # 전체 이동 거리 (픽셀)

        # 마우스 및 키보드 전역 리스너 초기화 (시스템 전체 입력 감지)
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)

    def start(self):
        """피로도 추적 엔진 및 입력 리스너 시작"""
        self.running = True
        self.last_input_time = time.time()
        self.mouse_listener.start()
        self.keyboard_listener.start()
        # 별도의 스레드에서 점수 계산 루프를 실행하여 메인 UI가 멈추지 않게 함
        threading.Thread(target=self._calculation_loop, daemon=True).start()

    def stop(self):
        """모든 리스너와 엔진 정지"""
        self.running = False
        self.mouse_listener.stop()
        self.keyboard_listener.stop()

    def reset_score(self):
        """스트레칭이 완료되었거나 필요할 때 점수를 0으로 초기화"""
        self.current_score = 0.0
        self.fatigue_updated.emit(self.current_score, self.FATIGUE_THRESHOLD)

    def update_threshold(self):
        """설정 변경 시 호출되어 즉시 UI에 반영되도록 신호를 보냄"""
        self.fatigue_updated.emit(self.current_score, self.FATIGUE_THRESHOLD)

    def _register_input(self):
        """어떤 입력이든 감지되면 마지막 입력 시간을 현재로 갱신"""
        self.last_input_time = time.time()

    def on_mouse_click(self, x, y, button, pressed):
        """마우스 클릭 발생 시 점수 가산"""
        if pressed:
            self._register_input()
            self.current_score += self.MOUSE_CLICK_SCORE
            # [추가] 통계 업데이트
            self.total_mouse_clicks += 1
            self._emit_stats()

    def on_key_press(self, key):
        """키보드 입력 발생 시 점수 가산"""
        self._register_input()
        self.current_score += self.KEY_INPUT_SCORE
        # [추가] 통계 업데이트
        self.total_kbd_hits += 1
        self._emit_stats()

    def _emit_stats(self):
        """현재 통계를 UI로 전송"""
        self.stats_updated.emit(self.total_kbd_hits, self.total_mouse_clicks, self.total_travel_distance)

    def _calculation_loop(self):
        """1초마다 실행되는 핵심 계산 루프: 마우스 이동 거리 측정 및 시간 점수 합산"""
        last_tick = time.time()
        last_idle_minute_tick = last_tick
        
        # 루프 시작 시점의 마우스 위치 저장
        last_mx, last_my = get_virtual_cursor_pos()
        
        while self.running:
            try:
                now = time.time()
                dt = now - last_tick  # 지난 루프부터 흐른 시간 계산
                last_tick = now
                idle_time = now - self.last_input_time  # 마지막 입력 이후 경과 시간
                
                # 1. 커서 이동 거리 체크 (CPU 부하를 줄이기 위해 1초 단위 샘플링)
                mx, my = get_virtual_cursor_pos()
                if mx != last_mx or my != last_my:
                    self._register_input()
                    # 두 점 사이의 거리를 계산하여 누적
                    dist = math.hypot(mx - last_mx, my - last_my)
                    self.accumulated_distance += dist
                    # [추가] 전체 누적 거리 업데이트
                    self.total_travel_distance += dist

                    # 누적 거리가 1000픽셀을 넘을 때마다 점수 추가
                    if self.accumulated_distance >= self.MOUSE_MOVE_UNIT:
                        units = int(self.accumulated_distance // self.MOUSE_MOVE_UNIT)
                        self.current_score += units * self.MOUSE_MOVE_SCORE
                        self.accumulated_distance -= (units * self.MOUSE_MOVE_UNIT)
                    last_mx, last_my = mx, my
                    # [추가] 통계 전송
                    self._emit_stats()
                
                # 2. 시간 기반 점수 추가 및 자동 회복(Rest) 로직
                if idle_time < self.IDLE_DETECTION_TIME:
                    # 사용자가 활동 중이라면 흐른 시간만큼 점수 가산
                    self.current_score += self.TIME_UNIT_SCORE * dt
                    last_idle_minute_tick = now 
                else:
                    # 5분 이상 미활동(휴식) 중이라면 1분마다 점수를 10%씩 깎아줌
                    if now - last_idle_minute_tick >= 60.0:
                        last_idle_minute_tick = now
                        self.current_score -= self.current_score * self.IDLE_RECOVERY_RATE
                        if self.current_score < 0:
                            self.current_score = 0
                
                # 3. 목표 점수 도달 여부 확인
                if self.current_score >= self.FATIGUE_THRESHOLD:
                    # 알림 신호 발생 및 점수 리셋
                    self.threshold_reached.emit()
                    self.reset_score()
                else:
                    # 실시간으로 변경된 점수를 UI(프로그레스 바 등)에 전달
                    self.fatigue_updated.emit(self.current_score, self.FATIGUE_THRESHOLD)
                    
            except Exception as e:
                print(f"피로도 엔진 루프 오류: {e}")
                
            # CPU 점유율을 0%에 가깝게 유지하기 위해 1초 동안 대기
            time.sleep(1.0)
