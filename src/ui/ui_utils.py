# -*- coding: utf-8 -*-
import re
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication

def get_scale_factor():
    """
    현재 주 모니터의 해상도와 DPI를 기반으로 스케일 인자를 계산합니다.
    기준 해상도: 2560x1440 (QHD) - 고해상도 기준
    """
    # [캐싱] 매번 계산하지 않도록 캐시 변수 활용 가능
    if not hasattr(get_scale_factor, "_cache"):
        app = QApplication.instance()
        if not app:
            return 1.0
            
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return 1.0
            
        size = screen.size()
        # 기준 해상도(2560x1440) 대비 현재 논리적 해상도의 비율 계산
        width_ratio = size.width() / 2560.0
        height_ratio = size.height() / 1440.0
        
        final_scale = min(width_ratio, height_ratio)
        
        # 최소 범위를 0.6으로 설정하여 저해상도에서도 가독성 확보, 최대는 1.2
        get_scale_factor._cache = max(0.6, min(final_scale, 1.2))
        
    return get_scale_factor._cache

def dp(px):
    """
    픽셀(px) 값을 현재 화면 스케일에 맞춰 변환합니다.
    """
    return int(px * get_scale_factor())

def scale_qss(qss_content):
    """
    QSS 문자열 내의 모든 '숫자px' 패턴을 찾아 스케일링된 값으로 치환합니다.
    예: font-size: 20px; -> font-size: 16px; (스케일 0.8인 경우)
    """
    scale = get_scale_factor()
    if scale == 1.0:
        return qss_content
        
    def replace_px(match):
        value = float(match.group(1))
        scaled_value = int(value * scale)
        return f"{scaled_value}px"
        
    # '20px' 또는 '20.5px' 형태의 패턴을 찾음 (숫자와 px 사이 공백 없음 가정)
    return re.sub(r'(\d+(?:\.\d+)?)px', replace_px, qss_content)
