import random
# 외부 텍스트 파일 대신 소스 코드 내의 데이터를 가져옴
from core.stretches_data import STRETCHING_CLASSES, REST_MESSAGES

class StretchingLoader:
    """스트레칭 문구 데이터(src/core/stretches_data.py)를 로드하고 관리하는 클래스"""
    
    def __init__(self):
        # 모든 카테고리의 상세 설명(desc)을 리스트 하나로 합칩니다 (랜덤 알림용)
        self.stretches = []
        for category_data in STRETCHING_CLASSES.values():
            if 'items' in category_data:
                for item in category_data['items']:
                    self.stretches.append(f"[{item['title']}]\n{item['desc']}")
        
        self.rest_messages = REST_MESSAGES

    def get_random_stretch(self):
        """스트레칭 목록 중 하나를 랜덤하게 선택하여 반환"""
        # 리스트가 비어 있을 경우를 대비한 안전 장치
        if not self.stretches:
            return "잠시 기지개를 켜고 휴식을 취해 보세요."
        return random.choice(self.stretches)

    def get_random_rest_message(self):
        """휴식 권장 멘트 중 하나를 랜덤하게 선택하여 반환"""
        if not self.rest_messages:
            return "잠시 숨을 고를 시간이에요."
        return random.choice(self.rest_messages)

    def load_stretches(self):
        """기존 코드와의 호환성을 위해 남겨둔 빈 메서드"""
        # 이제 파일 로드 로직이 필요 없으므로 아무 일도 하지 않습니다.
        pass
