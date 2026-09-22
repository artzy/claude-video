# /watch

**어떤 영상이든 Claude가 시청할 수 있게 해 줍니다.**

Claude Code (권장 — 마켓플레이스로 자동 업데이트):
```
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video
```

Codex, Cursor, Copilot, Gemini CLI, 또는 50개 이상의 [Agent Skills](https://agentskills.io) 호스트:
```bash
npx skills add bradautomates/claude-video -g
```
(`-g`는 사용자 전역 설치로, 모든 프로젝트에서 사용할 수 있습니다. 빼면 현재 프로젝트에만 설치됩니다.)

추가 설치 옵션(claude.ai 웹, 수동)은 아래 [Install](#install) 섹션을 참고하세요.

시작 시 별도 설정은 필요 없습니다 — macOS에서는 첫 실행 시 `brew`로 `yt-dlp`와 `ffmpeg`를 설치하고, Linux/Windows에서는 정확한 설치 명령을 출력합니다. 공개 영상 대부분은 무료 자막으로 충분합니다. Whisper API 키는 영상에 자막이 없을 때만 필요합니다.

---

Claude는 웹페이지를 읽고, 스크립트를 실행하고, 저장소를 탐색할 수 있습니다. 하지만 기본 상태로는 *영상을 볼* 수 없습니다. YouTube 링크를 붙여 넣으면 제목으로 추측하거나, 화면의 90%가 빠진 자막만 가져오게 됩니다.

Claude Video `/watch`로는 URL이나 로컬 경로를 붙여 넣고 질문을 하면, Claude가 먼저 자막을 확인하고, 필요한 것만 다운로드하고, 프레임을 추출하며(장면 인식, 또는 `efficient`에서 빠른 키프레임), 타임스탬프가 있는 대본을 가져온 뒤(가능하면 무료 자막, 없으면 Whisper API), 각 프레임을 이미지로 `Read`합니다. 답할 때쯤이면 영상을 *보았고* 오디오를 *들은* 상태입니다.

```
/watch https://youtu.be/dQw4w9WgXcQ what happens at the 30 second mark?
```

## 실제로 쓰는 용도

**남의 콘텐츠 분석.** `/watch https://youtu.be/<viral-video> what hook did they open with?` Claude가 첫 프레임을 보고, 오프닝 대본을 읽고, 구조를 분해합니다. 광고 크리에이티브, 경쟁사 런칭, 팟캐스트 인트로 등 *무엇*만큼 *어떻게*가 중요한 경우에 적합합니다.

**영상으로 버그 진단.** 뭔가 깨진 화면 녹화를 받았을 때. `/watch bug-repro.mov what's going wrong?` Claude가 녹화를 보고, 문제가 나타나는 프레임을 찾아 화면을 설명하며, 파일을 직접 열지 않고도 원인을 잡는 경우가 많습니다.

**영상 요약.** `/watch https://youtu.be/<long-thing> summarize this` — 구조, 핵심 장면, 실제로 말하고 보여 준 내용을 뽑아 줍니다. 2배속으로 보는 것보다 빠릅니다.

**업데이트 영상의 과장 제거.** `/watch https://youtu.be/<launch-video> what's actually new — skip the hype` "게임 체인저" 발표에서 진짜 중요한 몇 가지만 추려, 십 분짜리 인트로와 과대 광고 없이 알맹이만 얻습니다.

**플레이리스트를 노트로.** `/watch https://youtu.be/<video> summarize this to a note` 시리즈에 반복 적용해 영상별 요약을 쌓으면, 채널이나 강의를 앉아 보는 시간이 아니라 검색 가능한 노트 세트가 됩니다.

## 동작 방식

1. **영상과 질문을 붙여 넣습니다.** URL(yt-dlp가 지원하는 것 — YouTube, Loom, TikTok, X, Instagram 외 수백 개) 또는 로컬 경로(`.mp4`, `.mov`, `.mkv`, `.webm`).
2. **`yt-dlp`가 먼저 자막을 확인합니다.** `transcript` 디테일에서는 자막이 있는 URL은 영상 다운로드 없이 반환합니다. 그 외, 또는 Whisper에 오디오가 필요할 때는 해당 실행에 필요한 것만 다운로드합니다.
3. **`ffmpeg`가 선택한 디테일로 프레임을 추출합니다.** `efficient`는 키프레임만 디코드(거의 즉시); `balanced`/`token-burner`는 장면 전환 프레임을 우선하고, 부족하면 길이에 맞춘 균일 샘플링으로 넘어갑니다. JPEG는 기본 너비 512px이며, Claude Read 호환을 위해 높이 최대 1998px로 제한됩니다.
4. **대본은 두 경로 중 하나에서 옵니다.** 1순위: `yt-dlp`가 소스의 네이티브 자막(수동/자동)을 가져옵니다. 무료, 즉시, 대략 정확. 폴백: 모노 16 kHz 64 kbps mp3(~480 kB/분)를 뽑아 Whisper로 보냅니다 — Groq의 `whisper-large-v3`(권장 — 더 저렴하고 빠름) 또는 OpenAI의 `whisper-1`.
5. **프레임 + 대본을 Claude에 넘깁니다.** 스크립트가 `t=MM:SS` 마커가 있는 프레임 경로와 타임스탬프 대본을 출력합니다. Claude는 각 프레임을 병렬로 `Read`합니다 — JPEG가 컨텍스트에 이미지로 바로 렌더됩니다.
6. **화면과 오디오에 근거해 답합니다.** "설명 기준"이나 "제목 기준"이 아닙니다. 프레임을 봤고, 대본을 들었으며, 영상을 본 사람처럼 답합니다.
7. **정리.** 스크립트가 끝에 작업 디렉터리를 출력합니다. 후속 질문이 없으면 Claude가 삭제합니다.

## 프레임 예산 — 왜 중요한가

토큰 비용은 프레임이 지배합니다. 프레임마다 이미지이고, 이미지 토큰은 빠르게 쌓입니다. 스크립트의 auto-fps 로직은, 사실 30초 구간이면 충분한데 30분 영상을 성기게 훑느라 컨텍스트를 날리지 않도록 하기 위한 것입니다.

| 길이 | 기본 프레임 예산 | 결과 |
|----------|---------------------|--------------|
| ≤30초 | ~30프레임 | 촘촘함 — 핵심 순간 거의 전부 |
| 30초 - 1분 | ~40프레임 | 여전히 촘촘함 |
| 1 - 3분 | ~60프레임 | 여유 있음 |
| 3 - 10분 | ~80프레임 | 성기지만 쓸 만함 |
| > 10분 | 100프레임 (캡 모드) | "성긴 스캔" 경고 — 구간 재실행, 또는 `--detail token-burner`로 무제한 커버리지 |

사용자가 특정 순간을 말할 때("2:30 근처", "마지막 30초", "0:45부터 1:00까지")는 `--start` / `--end`를 넘기세요. 포커스 모드는 초당 예산을 더 촘촘하게 잡고, 최대 2 fps로 제한합니다. 전체를 성기게 도는 것보다 훨씬 유용합니다.

## 프레임 중복 제거

프레임 선택 — 키프레임(`efficient`), 장면 전환(`balanced`/`token-burner`), 또는 폴백 균일 샘플러 — 도 거의 같은 프레임을 올릴 수 있습니다. 한 슬라이드를 90초 붙잡는 화면 녹화는 열 개쯤 나오며, 각각이 별도 이미지로 과금됩니다. 중복 제거 패스가 Claude에 프레임이 가기 전에 이를 버립니다. 모든 프레임 모드에서 기본 켜짐(`--no-dedup`으로 끔):

1. `ffmpeg` 한 번으로 각 추출 JPEG를 16×16 그레이스케일 썸네일로 축소합니다. 이후는 순수 stdlib Python — 이미지 라이브러리 없음.
2. 각 프레임에 대해 *마지막으로 유지한 프레임*과의 **평균 절대 차이**(픽셀당 밝기 변화 평균, 0–255)를 계산합니다.
3. 차이가 임계값(`2.0`) 이하면 거의 중복으로 보고 버립니다. 아니면 유지하고 새 기준이 됩니다.
4. 프레임 예산 캡은 중복 제거 *이후*에 적용되므로, 예산은 서로 다른 프레임에 쓰입니다.

마지막 *유지* 프레임과 비교하면(직전 프레임이 아님) 프레임 간 임계값을 넘기지 않는 느린 페이드도 잡습니다. 임계값은 의도적으로 낮고 구조가 아닌 절대 밝기를 보므로, 한 줄 코드 diff, 한 줄 스크롤되는 터미널, 색만 다른 단색 슬라이드는 살아남습니다.

**Frames** 줄에 축소 결과가 나옵니다. 예: `6 selected from 14 candidates (… 8 near-duplicates dropped …)`. 항상 움직이는 영상에서는 아무것도 버리지 않으며, 원래 내던 비용 그대로입니다.

## 디테일 모드 — 측정값

`--detail` 다이얼은 속도와 토큰 비용 대 시각 충실도를 맞바꿉니다. 아래 숫자는 **49:08** YouTube 영상(1280×720, 영어 자동 자막) — 길고 거의 정적 화면 녹화, 캡을 가장 세게 밀어붙이는 케이스 — 실제 실행 결과입니다. 추출 시간은 미리 받아 둔 복사본에 대한 로컬 CPU 기준이며, 1회 다운로드는 **~37초** / 76 MB로 세 프레임 모드가 공유합니다.

| 모드 | 엔진 | 프레임 | 캡 | 추출 시간 | 시간 커버리지 | 예상 이미지 토큰 |
|------|--------|--------|-----|-----------------|-------------------|-------------------|
| `transcript` | 없음 (자막) | 0 | — | **~4.5초** (yt-dlp 1회, 다운로드 없음) | 전체 (텍스트) | 0 (≈26.6k 텍스트 토큰) |
| `efficient` | 키프레임 (`-skip_frame nokey`) | 50 | 50 | **~0.5초** | 0:00 → 49:04 (전체) | **~9.8k** |
| `balanced` | 장면 전환 | 100 | 100 | **~20.9초** | 0:00 → 48:38 (전체) | **~19.7k** |
| `token-burner` | 장면 전환 | 116 | 무제한 | **~21.0초** | 0:00 → 48:38 (전체) | **~22.8k** |

- **이미지 토큰**은 Anthropic의 `(width × height) / 750` — 기본 512px 너비에서 이 720p 프레임은 512×288, **≈197 토큰/프레임**; `--resolution 1024`는 대략 4배. 자막이 있는 모든 모드에서 대본이 포함되며, 긴 영상에서는 대본이 더 큰 비용인 경우가 많습니다.
- **프레임 모드 공통 샘플링 규칙.** 전체 구간에서 후보를 모두 찾은 뒤, 캡까지 균등 샘플링(첫·마지막은 항상 유지). 모드 차이는 후보 *출처*(키프레임 vs 장면 컷)와 캡뿐이며, 커버리지 펼치는 방식은 같아서 마지막 프레임은 항상 끝에 옵니다.
- **`efficient`는 속도 티어**(~0.5초) — 키프레임만 재구성하므로 매 프레임을 디코드해 컷을 찾는 장면 모드보다 ~40배 빠릅니다. 저모션 영상에서는 `balanced`보다 *더 많은* 프레임을 줄 수도 있습니다(키프레임이 장면 컷보다 많을 때); "efficient"는 빠른 추출이지, 더 적은 프레임이 아닙니다.
- **`token-burner`는 캡을 넘길 때만 `balanced`와 갈라집니다.** 이 클립은 컷 116개라 `balanced`는 100개 샘플, `token-burner`는 116개 전부. 컷이 수백 개인 고모션에서는 `token-burner`가 전부 유지(>250프레임 토큰 경고)하고 `balanced`는 100으로 줄입니다.

콜드 URL 기준 end-to-end로 `transcript`가 압도적으로 가장 저렴하고, 프레임 모드는 위 추출 시간에 공유 ~37초 다운로드가 더해집니다.

## Install

| 표면 | 설치 |
|---------|---------|
| **Claude Code** | `/plugin marketplace add bradautomates/claude-video` 후 `/plugin install watch@claude-video` |
| **Codex, Cursor, Copilot, Gemini CLI, +50** | `npx skills add bradautomates/claude-video -g` |
| **claude.ai** (웹) | [Download `watch.skill`](https://github.com/bradautomates/claude-video/releases/latest) → Settings → Capabilities → Skills → `+` |
| **수동 / 개발** | `git clone` 후 `skills/watch`를 호스트 skills 디렉터리에 심링크 (아래 참고) |

### Claude Code

```
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video
```

이후 업데이트: `/plugin update watch@claude-video`.

### Codex, Cursor, Copilot, Gemini CLI 및 50개 이상 호스트

[Agent Skills](https://agentskills.io) CLI가 감지한 에이전트에 스킬을 설치합니다:

```bash
npx skills add bradautomates/claude-video -g
```

`-g`는 사용자 전역 설치(`~/.codex/skills`, `~/.cursor/skills` 등); 빼면 현재 프로젝트에 설치. 유용한 플래그:

- `-a, --agent <names…>` — 특정 호스트만, 예: `-a codex -a cursor`
- `-l, --list` — 설치하지 않고 이 저장소의 스킬 목록만
- `--copy` — 심링크 대신 파일 복사 (심링크 미지원 파일시스템용)

CLI는 `skills/watch/SKILL.md`에서 스킬을 찾아 폴더 전체 — `SKILL.md`와 `scripts/` 런타임 — 를 한 단위로 복사합니다. `SKILL.md`는 설치된 위치를 기준으로 스크립트를 해석하므로 모든 호스트에서 동일하게 동작합니다.

이후 업데이트: `npx skills update watch -g`.

#### Cursor (권장 플래그)

Cursor에만 전역 설치:

```bash
npx skills add bradautomates/claude-video -g -a cursor -y
```

로컬 클론에서 (개발 중 스킬을 소스로 동기화):

```bash
# macOS / Linux
npx skills add . -g -a cursor -y

# Windows PowerShell — 프로젝트 범위(이 저장소) + 사용자 전역
New-Item -ItemType Directory -Force "$PWD\.cursor\skills" | Out-Null
cmd /c mklink /J "$PWD\.cursor\skills\watch" "$PWD\skills\watch"
New-Item -ItemType Directory -Force "$env:USERPROFILE\.cursor\skills" | Out-Null
cmd /c mklink /J "$env:USERPROFILE\.cursor\skills\watch" "$PWD\skills\watch"
```

Cursor는 개인 스킬을 `~/.cursor/skills/`, 프로젝트 스킬을 `.cursor/skills/`에서 로드합니다. 링크 후 **새 Agent 채팅**을 열고 `/watch`를 쓰거나 영상 URL을 붙여 넣으세요.

### claude.ai (웹)

1. 최신 릴리스에서 [`watch.skill`](https://github.com/bradautomates/claude-video/releases/latest)을 다운로드합니다.
2. Settings → Capabilities → Skills로 이동합니다.
3. `+`를 누르고 파일을 넣습니다.

Capabilities에서 먼저 "Code execution and file creation"을 켜 두세요 — 스킬이 `ffmpeg`와 `yt-dlp`를 셸로 호출하므로 없으면 실행되지 않습니다.

### 수동 (개발자)

저장소를 클론하고, 호스트의 skills 디렉터리에 자급식 스킬 폴더를 심링크합니다 — 심링크면 작업 트리를 편집할 때 설치본이 따라갑니다:

```bash
git clone https://github.com/bradautomates/claude-video.git
ln -s "$(pwd)/claude-video/skills/watch" ~/.claude/skills/watch   # 또는 ~/.codex/skills/watch 또는 ~/.cursor/skills/watch
```

Windows (심링크는 개발자 모드 또는 관리자 셸; junction은 둘 다 없이 가능):

```powershell
git clone https://github.com/bradautomates/claude-video.git
cd claude-video
New-Item -ItemType Directory -Force "$env:USERPROFILE\.cursor\skills" | Out-Null
cmd /c mklink /J "$env:USERPROFILE\.cursor\skills\watch" "$PWD\skills\watch"
```

claude.ai용으로는 소스에서 `.skill` 번들을 빌드합니다: `bash skills/watch/scripts/build-skill.sh` → `dist/watch.skill`.

## 첫 실행

첫 `/watch` 호출 시 스킬이 `scripts/setup.py --check`를 실행합니다. PATH에 `ffmpeg` / `yt-dlp`가 없거나 Whisper API 키가 없으면 해결을 안내합니다:

- **macOS** — `brew install ffmpeg yt-dlp`를 자동 실행.
- **Linux** — 정확한 `apt` / `dnf` / `pipx` 명령을 출력.
- **Windows** — `winget` / `pip` 명령을 출력.
- **API 키** — `~/.config/watch/.env`(모드 `0600`)에 `GROQ_API_KEY`(권장)와 `OPENAI_API_KEY` 주석 플레이스홀더를 생성.

설정 후 프리플라이트는 조용히 지나가고 `/watch`가 바로 동작합니다. 검사는 100ms 미만이라 이후 실행을 느리게 하지 않습니다.

## 키는 직접 준비

공개 영상 대부분은 무료 자막으로 충분합니다. Whisper 폴백은 자막 트랙이 진짜 없을 때만 — 보통 로컬 파일, TikTok, 일부 Vimeo, 가끔 자막 없는 YouTube — 켜집니다.

| 기능 | 필요 조건 | 비용 |
|------------|---------------|------|
| 다운로드 + 네이티브 자막 | `yt-dlp` + `ffmpeg` | 무료 |
| Whisper 폴백 (권장) | [Groq API key](https://console.groq.com/keys) — `whisper-large-v3` | 저렴, 빠름 |
| Whisper 폴백 (대안) | [OpenAI API key](https://platform.openai.com/api-keys) — `whisper-1` | 표준 요금 |
| Whisper 완전 비활성 | `--no-whisper` | 무료, 자막 없으면 프레임만 |

## 사용법

```
/watch https://youtu.be/dQw4w9WgXcQ what happens at the 30 second mark?
/watch https://www.tiktok.com/@user/video/123 summarize this
/watch ~/Movies/screen-recording.mp4 when does the UI break?
/watch https://vimeo.com/123 what tools does she mention?
```

특정 구간 포커스 — 더 촘촘한 프레임 예산, 더 낮은 토큰 비용:
```
/watch https://youtu.be/abc --start 2:15 --end 2:45
/watch video.mp4 --start 50 --end 60
/watch "$URL" --start 1:12:00            # 1시간 12분부터 끝까지
```

기타 옵션 (`scripts/watch.py`로 전달):

- `--detail transcript|efficient|balanced|token-burner` — 충실도/속도 다이얼. `transcript`는 프레임 생략(대본만); `efficient`는 빠른 키프레임(캡 50); `balanced`는 장면 인식 프레임(캡 100); `token-burner`는 장면 인식·무제한.
- `--timestamps T1,T2,…` — 각 절대 타임스탬프(`SS`/`MM:SS`/`HH:MM:SS`)에서 프레임 1장. Claude가 대본을 먼저 읽고 발표자가 가리키는 순간("여기 보세요", "보시다시피")을 노립니다. 디테일 프레임 위에 추가(캡에 대해 예약); 포커스 모드에서 창 밖 큐는 버림; `--detail transcript`면 이 프레임만.
- `--max-frames N` — 토큰 예산을 줄이려면 프레임 캡을 낮춤.
- `--resolution W` — 화면 글(슬라이드, 터미널, 코드)을 읽어야 할 때 프레임 너비를 1024px로.
- `--fps F` — auto-fps 계산 덮어쓰기(여전히 최대 2 fps).
- `--whisper groq|openai` — Whisper 백엔드 강제.
- `--no-whisper` — 전사 완전 비활성; 프레임만.
- `--no-dedup` — 거의 중복 프레임 유지. 기본은 프레임 델타로 직전 유지 프레임과 거의 같은 것(고정 슬라이드, 정적 화면 녹화, 일시정지)을 버려 예산을 서로 다른 내용에 씀; 이 플래그는 끔.
- `--out-dir DIR` — 작업 파일을 특정 위치에 유지(기본: 자동 임시 디렉터리).

## 한계

- **긴 영상 정확도는 디테일 모드에 달립니다.** 캡 모드(`efficient`, 기본 `balanced`)에서는 ~10분 이후 커버리지가 성겨집니다 — 프레임 캡이 전체 클립에 퍼지므로 "성긴 스캔" 경고가 나오고, `--start`/`--end`로 포커스 재실행하는 편이 낫습니다. `token-burner`는 캡을 풀어 전체 영상의 *모든* 장면 전환 프레임을 유지하므로 긴 클립에서도 완전하지만 이미지 토큰이 더 듭니다. 10분 기준은 캡 모드 가이드이지 하드 상한이 아닙니다.
- **디테일은 다이얼 하나.** 기본은 균형: 장면 인식 프레임, 최대 2 fps, 100프레임 캡. 빠른 50프레임 키프레임은 `--detail efficient`, 무제한 장면 후보는 `--detail token-burner`. 기본값을 바꾸려면 `~/.config/watch/.env`에 `WATCH_DETAIL`을 설정하세요.

## 구조

```
.
├── skills/watch/                 # 자급식 스킬 — 모든 설치기가 단위로 복사
│   ├── SKILL.md                  # 스킬 계약 — 모든 표면의 진실 소스
│   └── scripts/
│       ├── watch.py              # 진입점 — 다운로드 → 프레임 → 대본 오케스트레이션
│       ├── download.py           # yt-dlp 래퍼
│       ├── frames.py             # ffmpeg 프레임 추출 + auto-fps
│       ├── transcribe.py         # VTT 파싱 + 중복 제거 + Whisper 오케스트레이션
│       ├── whisper.py            # Groq / OpenAI 클라이언트 (순수 stdlib)
│       ├── config.py             # 공유 설정 (~/.config/watch/.env)
│       ├── setup.py              # 프리플라이트 + 설치기
│       └── build-skill.sh        # claude.ai 업로드용 dist/watch.skill 빌드 (개발 전용)
├── hooks/                        # SessionStart 상태 훅 (Claude Code 전용)
├── .claude-plugin/               # plugin.json + marketplace.json (Claude Code)
├── .codex-plugin/                # plugin.json — Codex/agents 매니페스트 ("skills": "./skills/")
├── .agents/plugins/              # marketplace.json — Agent Skills 마켓플레이스 목록
├── AGENTS.md → CLAUDE.md         # 범용 에이전트 진입점
├── tests/                        # pytest 스위트 (ffmpeg 합성 클립, 네트워크 없음)
└── .github/workflows/            # release.yml — 태그 푸시 시 watch.skill 자동 빌드
```

## 개발

```bash
# 테스트 스위트 실행 (stdlib + pytest; 프레임 테스트에 ffmpeg 필요):
python3 -m pytest -q

# claude.ai 업로드 번들 빌드:
bash skills/watch/scripts/build-skill.sh      # → dist/watch.skill
```

릴리스: `vX.Y.Z` 태그를 만들고 푸시합니다. 워크플로가 `dist/watch.skill`을 빌드해 GitHub 릴리스에 첨부합니다. 버전은 `skills/watch/SKILL.md`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`에 맞춰 두세요.

버전 이력은 [CHANGELOG.md](CHANGELOG.md)를 참고하세요.

## 오픈 소스

MIT 라이선스.

`yt-dlp`, `ffmpeg`, Claude의 멀티모달 `Read` 도구 위에 구축되었습니다. Whisper 전사는 [Groq](https://groq.com) 또는 [OpenAI](https://openai.com)를 사용합니다.

제작: Brad Bonanno — [YouTube (@bradbonanno)](https://www.youtube.com/@bradbonanno)에서 AI로 만드는 콘텐츠를 다루고, [Solaris Automation](https://www.solarisautomation.io/)에서 비즈니스를 위한 AI 운영 체제를 만듭니다. `/watch`로 영상을 스크럽하는 시간을 아꼈다면 채널에 들러 인사해 주세요.

## Star History

<a href="https://www.star-history.com/?repos=bradautomates%2Fclaude-video&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=bradautomates/claude-video&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=bradautomates/claude-video&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=bradautomates/claude-video&type=date&legend=top-left" />
 </picture>
</a>

---

[github.com/bradautomates/claude-video](https://github.com/bradautomates/claude-video) · [@bradbonanno](https://www.youtube.com/@bradbonanno) · [Solaris Automation](https://www.solarisautomation.io/) · [LICENSE](LICENSE)
