# 시스템 명세서 (System Specification) - "Lullit" (v0.4.0)

## 1. 프로젝트 개요
사용자의 PC 활동량(키보드, 마우스 입력)을 분석하여 '피로도'를 계산하고, 최적의 타이밍에 미니멀한 스트레칭 알림을 제공하는 윈도우 전용 데스크탑 애플리케이션. v0.4.0에서는 **스트레칭 클래스 콘텐츠 개편**, **네비게이션 사용성 개선**, **메모리 최적화** 및 **베타 배포 준비**를 완료함.

## 2. 디자인 원칙 (Visual Identity)
- **컨셉**: Toss & Apple 스타일의 극한의 미니멀리즘과 부드러운 사용자 경험.
- **창 크기 (Dynamic Scaling)**: 
  - **기준 해상도**: `2560x1440 (QHD)`에서 100% 크기 유지.
  - **스케일링**: 1080p 해상도에서 최소 0.6배율 적용 (FHD 환경 가독성 유지).
- **Typography**: 
  - **Pretendard** 폰트 전역 임베딩.
  - **가독성 상향**: 전역 폰트 크기 +1px 상향 조정 및 QSS 기반 폰트 관리.
  - **잘림 방지**: 버튼 및 캡션 영역의 `min-height`를 상향 조정하여 폰트 크기 변화에도 레이아웃 무결성 유지.

## 3. 기술 스택
- **언어**: Python 3.13+
- **UI Framework**: PySide6 (Qt for Python).
- **해상도 대응**: `ui_utils.py`를 통한 `dp()` 및 `scale_qss()` 동적 픽셀 보정.
- **렌더링 최적화**: 
  - `QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)` 활성화.
  - `QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)` 활성화.
  - **폰트 힌팅**: `QFont.PreferFullHinting` 및 안티앨리어싱 전략 적용으로 저해상도 텍스트 깨짐 방지.

## 4. 기능 명세 (IA & Features)
### 4.1. 메인 윈도우 (Main Window)
- **Home**: 알림 횟수 요약, 진행률 바(`dp(16)`), 이용 팁 팝업 기능.
- **스트레칭 클래스 (개편)**: 
  - **목록**: 부위별(목, 어깨, 허리, 손목, 눈) 2열 그리드 카드 배치.
  - **상세**: 클릭 시 내부 스택 전환(Nested Stack)을 통한 단계별 스트레칭 정보 제공.
- **알림 상세 설정**: 알림 주기 및 투명도 설정. 메뉴 이탈 시 저장 안 된 변경사항 자동 폐기.
- **고급 설정**: 시작 프로그램 등록, 테마 모드 선택. 중앙 정렬된 저장 버튼.

### 4.2. 알림 오버레이 (Ghost Overlay)
- **속성**: Always on Top, Translucent, Click-through (닫기 버튼 제외).
- **틀 고정 (Template)**: 캐릭터 영역(`dp(200)`) 및 텍스트 영역의 위치를 엄격히 고정하여 메시지 길이에 상관없이 시각적 안정성 유지.
- **텍스트 배치**: 제목("스트레칭 시간입니다.")과 랜덤 메시지를 상하 중앙 정렬하여 시인성 극대화.

## 5. 핵심 로직 (Fatigue Engine)
### 5.1. 점수 가산 방식 (Weights)
- **Time**: 1.0점 / 초
- **Mouse Click**: 0.5점 / 회
- **Mouse Move**: 1.0점 / 1000px
- **Key Press**: 0.2점 / 타

## 6. 데이터 구조
- **환경 설정**: `app_config.json`.
- **스트레칭 데이터**: `stretches_data.py` (부위별 딕셔너리 구조로 개편).
