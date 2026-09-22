# Add Eye Tracking to Any VR Headset for $17 — 상세 요약

- **URL:** https://www.youtube.com/watch?v=l95eJe8MV5g
- **제목:** Add Eye Tracking to Any VR Headset for $17
- **업로더:** Jason Orlosky (JEO Research)
- **길이:** 02:10 (약 130초)
- **분석일:** 2026-08-26
- **근거:** captions + scene frames (YouTube 403 → yt-dlp tv client 복구)

## 한줄 요약

**GC0308 IR 카메라(약 $17)** 를 Vive Pro 등 임의 VR 헤드셋에 장착하고, GitHub의 Python 아이트래커와 Unity 캘리브레이션으로 **$20 미만 DIY VR 시선 추적**을 만드는 실습 튜토리얼입니다.

## 핵심정리

- 목적: 시선 분석·게이밍·인터랙션·커뮤니케이션용 앱을 **$20 미만**으로 개발 (00:01–00:15)
- 카메라: **GC0308** — 대부분 HMD에 수납 가능, 사용 중 다소 발열, **밀폐하지 않으면** 동작 양호 (00:15–00:26)
- 데모 HMD: **VIVE Pro**, 단독 약 **$350** (00:26–00:33)
- 장착: 렌즈 초점 **약 3 cm**, 삽입 측 **디스플레이 패딩 일부 제거**, soft wire로 고정 (00:33–00:47)
- 검증: SteamVR 데스크톱 뷰 + 카메라 뷰어로 눈이 잘 보이는지 확인 (00:47–00:53)
- SW: GitHub **Python eye tracking** + **Unity calibration** (00:55–01:17)
- Unity: SteamVR 릭 import → 스크립트를 HMD transform에 부착 → read path = Python 실행 디렉터리 (01:02–01:25)
- 순서: Python 먼저 self-center → Unity Play → 회색 구(미보정) → **C** 키로 빨간 구 캘리브 → 시선 광선 (01:27–01:58)
- 예고: **2카메라**로 정확도·깊이 추적 개선 (02:00–02:08)

## 내용

### 오프닝 — 무엇을 만드는지 (00:01–00:15)

발표자(Jason Orlosky)가 **VIVE Pro**를 쓴 채로 시작합니다. 목표는 “어떤 VR 헤드셋이든” 이 **작은 카메라**로 개조해 **완전한 VR 아이트래커**로 만드는 것. 용도로 gaze analysis, gaming, interaction, communication을 들고, 예산은 **under $20**이라고 명시합니다.

### 하드웨어 — GC0308 (00:15–00:33)

이전 영상에서 다룬 **GC0308**을 다시 꺼냅니다. 화면에는 DIY 안경에 모듈이 달린 모습과 PCB 클로즈업이 겹칩니다.

주장 포인트:

1. **대부분의 VR 헤드셋 안에 물리적으로 들어간다.**
2. 사용 중 **조금 뜨거워지지만**, **완전히 밀폐만 하지 않으면** 실사용에 문제없다.

데모 기기는 **VIVE Pro** — standalone headset으로 약 $350 (시선 추적용 카메라 가격과는 별개).

### 물리적 장착 절차 (00:33–00:53)

1. **카메라 렌즈를 살짝 풀어** 초점을 **대략 3 cm**에 맞춤 — 근안(near-eye) 거리.
2. 카메라를 넣을 **쪽의 디스플레이 패딩 일부를 제거**.
3. 원하는 위치에 **soft wire(연선)** 로 고정 추천.
4. **SteamVR desktop view** + camera viewer로 스트림 확인.

### 소프트웨어 스택 — GitHub + Unity (00:55–01:25)

GitHub에서 **Python eye tracking script**와 **Unity calibration script**가 필요. Unity에서는 해당 HMD용 VR 릭(데모는 SteamVR)을 import하고, 스크립트를 헤드셋 transform 오브젝트에 붙인 뒤, read file path를 Python 실행 디렉터리와 맞춘다.

### 실행·캘리브레이션 워크플로 (01:27–01:58)

1. Unity Play **전에** Python 아이트래커를 먼저 실행하고 눈에 self-center.
2. Unity Play → Scene의 **회색 구** = 미보정 gaze.
3. Game 창 포커스 후 **C** → 빨간 구 등장.
4. 각 구를 응시한 뒤 다시 **C** — 마지막 구가 사라지면 캘리브 완료.
5. 이후 회색 구가 눈을 따라가고, 헤드셋–구 연결선이 **gaze ray**.

### 마무리 (02:00–02:08)

단안 셋업 다음으로 **두 카메라**로 정확도와 depth-based tracking을 개선하겠다는 예고로 끝난다.

### 실무 포인트

- 비용: 카메라 ~$17 + 기존 HMD, SW는 공개 GitHub
- 발열·통기: 밀폐 금지
- 흔한 실패: Python↔Unity 파일 경로 불일치, Game 창 포커스 없이 C 입력