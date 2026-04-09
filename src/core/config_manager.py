import os
import json
import sys
import shutil
from core.system_utils import get_data_dir

def get_base_path():
    """실행 파일 또는 스크립트가 있는 기본 경로를 반환합니다. (마이그레이션용)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 새 설정 파일 경로 (표준 데이터 폴더)
DATA_DIR = get_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "app_config.json")

def migrate_config():
    """기존 위치(프로그램 폴더)에 설정 파일이 있다면 새 위치(AppData)로 옮깁니다."""
    old_config = os.path.join(get_base_path(), "app_config.json")
    if os.path.exists(old_config) and not os.path.exists(CONFIG_FILE):
        try:
            shutil.copy2(old_config, CONFIG_FILE)
            print(f"설정 파일 마이그레이션 완료: {old_config} -> {CONFIG_FILE}")
        except Exception as e:
            print(f"설정 파일 마이그레이션 실패: {e}")

# 시작 시 마이그레이션 실행
migrate_config()

class ConfigManager:
    """애플리케이션의 설정값을 파일(JSON)로 관리하는 클래스"""
    def __init__(self):
        # 기본 설정값 정의
        self.config = {
            "alarm_interval_minutes": 60,  # 기본 스트레칭 알림 주기 (60분)
            "overlay_opacity": 0.75,        # 오버레이 투명도 (0.2 ~ 1.0)
            "run_on_startup": True,         # 부팅 시 자동 실행 여부
            "dark_mode": True,              # 다크 모드 여부
            "theme_mode": "dark"            # 테마 모드 (light/dark/system)
        }
        self.load_config()  # 프로그램 시작 시 기존 설정 파일 로드

    def load_config(self):
        """파일에서 설정을 읽어와 현재 객체에 반영"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 파일에 저장된 값들로 기본값을 덮어씁니다.
                    self.config.update(data)
            except Exception as e:
                print(f"설정 로드 오류 ({CONFIG_FILE}):", e)

    def save_config(self):
        """현재 설정값을 JSON 파일로 저장"""
        try:
            # 저장 전에 디렉토리가 존재하는지 한 번 더 확인
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
                
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                # 가독성을 위해 들여쓰기(indent=4)를 포함하여 저장
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"설정 저장 오류 ({CONFIG_FILE}):", e)

    def get(self, key, default=None):
        """특정 설정 키의 값을 반환 (키가 없으면 기본값 반환)"""
        return self.config.get(key, default)

    def set(self, key, value):
        """설정 값을 변경하고 즉시 파일에 저장"""
        self.config[key] = value
        self.save_config()
