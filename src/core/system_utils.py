import winreg
import sys
import os

def resource_path(relative_path):
    """
    PyInstaller 빌드 시 임시 폴더(_MEIPASS)를 고려하여 절대 경로를 반환합니다.
    """
    try:
        # PyInstaller에 의해 생성된 임시 폴더 경로(_MEIPASS) 확인
        base_path = sys._MEIPASS
    except Exception:
        # 일반 실행 시 (개발 환경) 현재 파일 기준의 루트 경로
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)

def get_data_dir():
    """
    사용자 데이터(설정, 로그 등)를 저장할 경로를 반환합니다.
    윈도우의 경우 %APPDATA%\Lullit 폴더를 사용합니다.
    """
    app_name = "Lullit"
    if sys.platform == "win32":
        base_dir = os.getenv("APPDATA")
    else:
        # 리눅스/맥OS의 경우 홈 디렉토리의 숨김 폴더 사용
        base_dir = os.path.expanduser("~")
    
    data_dir = os.path.join(base_dir, app_name)
    
    # 해당 폴더가 없으면 생성
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
        except Exception as e:
            print(f"데이터 디렉토리 생성 실패: {e}")
            # 실패 시 현재 폴더 반환 (최후의 수단)
            return os.path.abspath(".")
            
    return data_dir

def set_run_on_startup(enable: bool):
    """
    윈도우 시작 시 프로그램이 자동으로 실행되도록 레지스트리에 등록하거나 제거합니다.
    경로: HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
    """
    try:
        # 윈도우 시작프로그램 레지스트리 키 열기
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        app_name = "Lullit"  # 레지스트리에 등록될 이름
        
        if enable:
            # 빌드된 .exe 환경인지 확인 (PyInstaller 환경)
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                # 개발 환경에서는 현재 스크립트 경로 사용
                exe_path = os.path.abspath(sys.argv[0])
            
            # 경로에 공백이 있을 수 있으므로 큰따옴표로 감싸서 레지스트리에 저장합니다.
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            # 자동 실행 해제 시 레지스트리 값 삭제
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                # 이미 값이 없는 경우 무시
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print("시작프로그램 레지스트리 설정 오류:", e)
