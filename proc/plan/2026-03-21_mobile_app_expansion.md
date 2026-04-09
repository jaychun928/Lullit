# Lullit 모바일 앱 확장 계획 (Mobile Expansion - React Native)

## 목표
데스크탑 프로젝트(`Lullit-PC`)의 자산과 로직을 활용하여, **React Native** 기반의 독립된 모바일 프로젝트를 생성하고 스마트 피로도 알림 앱을 구축함.

## 작업 항목
### 1. React Native 프로젝트 환경 구축 및 리소스 추출
- [ ] **신규 프로젝트 초기화**: 상위 디렉토리에 `Lullit-Mobile` 폴더 생성 및 `npx react-native init` (TypeScript 템플릿)
- [ ] **디자인 시스템 및 라이브러리 설정**:
  - [ ] `styled-components` 또는 `Tailwind CSS (NativeWind)` 설정
  - [ ] `react-navigation`을 통한 기본 네비게이션 구조 설계
- [ ] **디자인 자산(Assets) 마이그레이션**:
  - [ ] `Lullit-PC/src/ui/assets/fonts/`의 **Pretendard** 폰트 이식 및 `react-native.config.js` 설정
  - [ ] 로고 및 아이콘 파일을 `src/assets/images`로 복사
  - [ ] QSS 테마를 **Theme 객체 (Lullit Green, Dark Mode)**로 변환 정의

### 2. 핵심 로직(Fatigue Engine) TypeScript 이식
- [ ] **피로도 엔진 포팅**: `fatigue_engine.py`의 가중치 로직을 TypeScript 클래스로 변환
- [ ] **상태 관리**: `Zustand` 또는 `Context API`를 이용한 실시간 피로도 점수 관리
- [ ] **모바일 전용 입력 트래킹 구현**:
  - [ ] `react-native-device-info` 등을 활용한 상태 감지
  - [ ] `AppState` API를 사용하여 앱 활성화 시간(Focus Time) 트래킹

### 3. 모바일 UI/UX 구현 (MVP)
- [ ] **메인 대시보드**: React Native용 커스텀 '진행률 바' 위젯 구현
- [ ] **스트레칭 가이드**: 가로/세로 유연한 레이아웃을 위한 Flexbox 기반 UI 설계
- [ ] **알림 시스템**:
  - [ ] `react-native-notifee` 또는 `react-native-push-notification` 연동
  - [ ] 백그라운드 작업 처리를 위한 `react-native-background-fetch` 검토

### 4. 데이터 저장 및 동기화
- [ ] **로컬 저장소**: `MMKV` 또는 `AsyncStorage`를 이용한 설정값 유지
- [ ] **공통 데이터 구조**: 데스크탑의 `stretching.json` 데이터를 모바일용 JSON 포맷으로 최적화

## 비고
- React Native를 사용하여 Android와 iOS 양쪽에서 일관된 미니멀리즘 UX를 제공함.
- `Lullit-PC`의 디자인 원칙을 계승하되, 모바일 터치 인터페이스에 최적화된 인터랙션 추가.
