---
name: watch
version: "0.2.1"
description: >-
  Watch a video (URL or local path). Downloads with yt-dlp, extracts auto-scaled
  frames with ffmpeg, pulls the transcript from captions (or Whisper API
  fallback), and answers questions grounded in what's on screen and in the
  audio. Use when the user pastes a YouTube/TikTok/Loom/Vimeo URL, a local
  .mp4/.mov/.mkv/.webm, types /watch, or asks what happens in a video.
argument-hint: "<video-url-or-path> [question]"
allowed-tools: Bash, Shell, Read, AskUserQuestion
homepage: https://github.com/bradautomates/claude-video
repository: https://github.com/bradautomates/claude-video
author: bradautomates
license: MIT
user-invocable: true
---

# /watch — 포터블 스킬 (다른 프로젝트에서 사용)

이 문서는 [claude-video](https://github.com/bradautomates/claude-video)의 `/watch` 기능을 **다른 Cursor / Agent Skills 호스트 / 프로젝트**에서 재사용하기 위한 포터블 가이드입니다.

**중요:** 이 `.md`만으로는 동작하지 않습니다. 반드시 `scripts/` 런타임과 함께 설치하세요. 에이전트는 아래 [에이전트 계약](#에이전트-계약-skilmd-본문)을 그대로 따릅니다.

원본 소스: `skills/watch/` (이 저장소의 자급식 스킬 폴더).

---

## 다른 곳에서 쓰는 방법

### A. 권장 — Agent Skills CLI로 전역 설치

모든 프로젝트에서 `/watch`를 쓰려면:

```bash
npx skills add bradautomates/claude-video -g
```

Cursor만:

```bash
npx skills add bradautomates/claude-video -g -a cursor -y
```

업데이트:

```bash
npx skills update watch -g
```

### B. 이 저장소를 클론한 뒤 심링크 / 정션

```powershell
# Windows PowerShell (junction — 관리자 권한 불필요)
git clone https://github.com/bradautomates/claude-video.git
cd claude-video
New-Item -ItemType Directory -Force "$env:USERPROFILE\.cursor\skills" | Out-Null
cmd /c mklink /J "$env:USERPROFILE\.cursor\skills\watch" "$PWD\skills\watch"
```

```bash
# macOS / Linux
git clone https://github.com/bradautomates/claude-video.git
ln -s "$(pwd)/claude-video/skills/watch" ~/.cursor/skills/watch
```

특정 **프로젝트에만** 쓰려면 그 프로젝트의 `.cursor/skills/watch`로 링크하세요.

### C. 폴더를 통째로 복사

대상 호스트의 skills 디렉터리에 `watch/` 폴더를 **통째로** 복사합니다:

```
watch/
├── SKILL.md          ← 이 문서의 "에이전트 계약"과 동일 역할
└── scripts/
    ├── watch.py      ← 엔트리포인트
    ├── download.py
    ├── frames.py
    ├── transcribe.py
    ├── whisper.py
    ├── setup.py
    └── config.py
```

| 호스트 | 설치 위치 |
|--------|-----------|
| Cursor (개인) | `~/.cursor/skills/watch/` |
| Cursor (프로젝트) | `<project>/.cursor/skills/watch/` |
| Codex | `~/.codex/skills/watch/` |
| Claude Code | 플러그인 또는 `~/.claude/skills/watch/` |
| 기타 Agent Skills | `~/.agents/skills/watch/` 등 |

이 `watch_skill.md`를 에이전트 스킬로 쓰려면 폴더 이름을 `watch/`로 두고, 파일명을 **`SKILL.md`로 바꿔** 넣으세요 (호스트가 `SKILL.md`를 찾습니다). `scripts/`는 `SKILL.md`와 **형제**여야 합니다.

### D. 사전 요구사항

| 항목 | 설명 |
|------|------|
| Python 3 | Windows에서는 `python` (Store stub인 `python3` 사용 금지) |
| `ffmpeg` / `ffprobe` | 프레임·오디오 추출 |
| `yt-dlp` | URL 다운로드·자막 |
| Whisper 키 (선택) | 자막 없을 때. Groq 권장 → `~/.config/watch/.env`의 `GROQ_API_KEY` |

첫 실행 시 에이전트가 `scripts/setup.py`로 프리플라이트를 돌립니다. macOS는 brew로 바이너리 자동 설치, Linux/Windows는 설치 명령을 출력합니다.

---

## 에이전트 계약 (SKILL.md 본문)

아래부터는 에이전트가 `/watch`를 수행할 때 따라야 할 계약입니다. 다른 프로젝트에 설치한 뒤에도 동일합니다.

### Resolve `SKILL_DIR` (명령 실행 전)

모든 `python3 ...` / `python ...` 는 `SKILL_DIR/scripts/` 아래 번들 스크립트를 실행합니다. `SKILL_DIR` = **방금 Read한 SKILL.md가 있는 디렉터리의 절대 경로**.

```
Read ~/.cursor/skills/watch/SKILL.md         → SKILL_DIR=~/.cursor/skills/watch
Read <project>/.cursor/skills/watch/SKILL.md → SKILL_DIR=<project>/.cursor/skills/watch
Read ~/.codex/skills/watch/SKILL.md          → SKILL_DIR=~/.codex/skills/watch
```

`${SKILL_DIR}`에 그 경로를 그대로 넣으세요. 호스트 전용 환경변수(`CLAUDE_SKILL_DIR` 등)에 의존하지 마세요.

**Shell:** 예시는 bash. **Cursor / Windows PowerShell**에서는 `Test-Path`, `python`(not `python3`), 경로 구분자는 `\` 또는 `/` 모두 가능.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you Read>"
if [ ! -f "$SKILL_DIR/scripts/watch.py" ]; then
  echo "ERROR: scripts/watch.py not found under SKILL_DIR=$SKILL_DIR" >&2
  exit 1
fi
```

```powershell
$SKILL_DIR = "<absolute path of the directory containing the SKILL.md you Read>"
if (-not (Test-Path "$SKILL_DIR\scripts\watch.py")) {
  Write-Error "scripts/watch.py not found under SKILL_DIR=$SKILL_DIR"
  exit 1
}
```

### Step 0 — Setup preflight

**Python:** macOS/Linux → `python3`. **Windows** → `python`.

**사용자에게 묻기:** `AskUserQuestion`이 있으면 사용, 없으면 일반 채팅으로 묻고 답을 기다림.

세션 첫 `/watch`:

```bash
python3 "${SKILL_DIR}/scripts/setup.py" --json
```

| 분기 | 동작 |
|------|------|
| `can_proceed: true`, `first_run: false` | 바로 Step 1 |
| `first_run: true` | 바이너리 설치 → `.env` 스캐폴드 → Whisper 키 권유 → detail 선호 질문 → `SETUP_COMPLETE=true` |
| `can_proceed: false`, `first_run: false` | 설치 복구 후 진행 (선호 재질문 금지) |

후속 호출:

```bash
python3 "${SKILL_DIR}/scripts/setup.py" --check
```

exit 0 → 조용히 Step 1 (성공 메시지를 사용자에게 말하지 않음).

| Exit | 의미 | 조치 |
|------|------|------|
| `2` | `ffmpeg` / `ffprobe` / `yt-dlp` 없음 | 설치 실행 |
| `3` | 첫 실행 + Whisper 키 없음 | `.env` 스캐폴드 후 키 권유 (거절 시 `--no-whisper`) |
| `4` | 둘 다 | 설치 + 키 권유 |

설치 (멱등):

```bash
python3 "${SKILL_DIR}/scripts/setup.py"
```

설정 파일: `~/.config/watch/.env` (mode `0600`).

첫 실행 detail 질문 (순서 고정, `balanced`에 `(recommended)` 유지):

- `transcript` — 프레임 없음, 대본만
- `efficient` — 키프레임, cap 50
- `balanced` (recommended) — 장면 인식, cap 100
- `token-burner` — 장면 인식, uncapped

`.env`에 인라인 주석 없이:

```
WATCH_DETAIL=balanced
SETUP_COMPLETE=true
```

### When to use

- YouTube / Vimeo / X / TikTok / Twitch clip 등 yt-dlp 지원 URL
- 로컬 `.mp4` / `.mov` / `.mkv` / `.webm`
- `/watch <url-or-path> [question]`

### Recommended limits

- 정확도: **10분 이하** 영상이 가장 좋음
- 샘플링 상한: **2 fps**
- detail 캡: `transcript`=0, `efficient`≤50, `balanced`≤100, `token-burner`=무제한 (250+ 경고)
- 길이별 예산: ≤30s→~12–30, 30s–1m→~40, 1–3m→~60, 3–10m→~80, >10m→캡까지 성기게
- 긴 영상이면 구간(`--start`/`--end`)을 먼저 제안

### How to invoke

**Step 1 — 파싱.** 소스(URL/경로)와 질문을 분리.

**Step 2 — 실행.**

```bash
python3 "${SKILL_DIR}/scripts/watch.py" "<source>"
```

주요 플래그:

| 플래그 | 용도 |
|--------|------|
| `--detail transcript\|efficient\|balanced\|token-burner` | 충실도/속도 |
| `--start T` / `--end T` | 구간 (`SS`, `MM:SS`, `HH:MM:SS`) |
| `--timestamps T1,T2,…` | 대본 큐 시점 강제 프레임 |
| `--max-frames N` | 캡 오버라이드 |
| `--resolution W` | 너비 px (기본 512; 화면 글자는 1024) |
| `--fps F` | auto-fps 오버라이드 (≤2) |
| `--out-dir DIR` | 작업 디렉터리 |
| `--whisper groq\|openai` | Whisper 백엔드 강제 |
| `--no-whisper` | Whisper 끔 |
| `--no-dedup` | 거의 동일 프레임 유지 |

포커스 모드 예산 (`balanced` 기준): ≤5s→≤10, 5–15s→≤30, 15–30s→≤60, 30–60s→≤80, 60–180s→100.

```bash
python3 "${SKILL_DIR}/scripts/watch.py" video.mp4 --start 50 --end 60
python3 "${SKILL_DIR}/scripts/watch.py" "$URL" --start 2:15 --end 2:45 --fps 2
```

**Step 3 — 프레임 Read.** 스크립트가 나열한 JPEG 경로를 **한 메시지에서 병렬 Read**. 시간순, `t=MM:SS`.

**Step 4 — 답변.** 프레임(화면) + 대본(음성)에 근거. 질문 있으면 타임스탬프 인용 답변; 없으면 구조·핵심 장면·말한 내용 요약. `transcript` 모드에서도 **전체 대본 붙여넣기 금지** — 요약하고, 원문은 요청 시에만.

**Step 5 — 정리.** 후속 질문 없으면 작업 디렉터리 삭제 (`rm -rf` / `Remove-Item -Recurse -Force`).

### Detail and frames

- `transcript`: 자막 있으면 다운로드 생략. 없으면 오디오만 → Whisper. 실패 시 한계를 알리고 `--detail balanced` 재실행 제안.
- `efficient`: 키프레임만 (`ffmpeg -skip_frame nokey`). 키프레임 <4면 균일 샘플.
- `balanced` / `token-burner`: 장면 전환 우선, 정적 영상은 균일 폴백. JPEG 높이 ≤1998px.

### Transcript-cue frames

1. `--detail transcript` 등으로 대본 확보
2. "look here", "as you can see", "notice this" 등 **지시어** 시점 판단 (에이전트 판단; 정규식 자동 아님)
3. `--timestamps 4:32,7:10` 로 재실행. URL이면 work dir의 **로컬 파일**을 가리켜 재다운로드 방지

큐 프레임은 캡에 먼저 예약되며, `--detail transcript --timestamps …`면 큐 프레임만.

### Transcription

1. **네이티브 자막** (무료, 우선) — yt-dlp
2. **Whisper** — 모노 16 kHz 64k mp3 → Groq `whisper-large-v3` (우선) 또는 OpenAI `whisper-1`

키: `~/.config/watch/.env`의 `GROQ_API_KEY` / `OPENAI_API_KEY`.

### Failure modes

| 상황 | 대응 |
|------|------|
| 프리플라이트 실패 | `setup.py` 실행, 키는 사용자에게 물어 `.env`에 기록 |
| 대본 없음 | 프레임만으로 진행하고 알림 |
| 긴 영상 경고 | 인정 + `--start`/`--end` 제안 |
| 다운로드 실패 | 로그인/지역 제한이면 재시도 금지, 사실대로 전달 |
| Whisper 실패 | stderr 확인; `--whisper`로 다른 백엔드 재시도 |

### Token efficiency

- ~80프레임@512px ≈ 50–80k 이미지 토큰
- 대본은 상대적으로 저렴
- `--resolution 1024`는 프레임당 대략 4배
- 같은 세션 후속 질문 → **스크립트 재실행 금지**, 컨텍스트로 답변

### Security & Permissions

**하는 일:** 로컬 yt-dlp/ffmpeg; 자막 없을 때만 오디오를 Groq/OpenAI Whisper로 전송; temp(또는 `--out-dir`)에 작업 파일; `~/.config/watch/.env` 읽기/생성.

**하지 않는 일:** 영상 파일 자체 업로드 안 함; 플랫폼 로그인/쿠키/포스팅 안 함; 키를 stdout/stderr에 쓰지 않음; 작업 디렉터리와 `.env` 외 영구 저장 안 함.

**번들 스크립트:** `watch.py`, `download.py`, `frames.py`, `transcribe.py`, `whisper.py`, `setup.py`, `config.py`.

---

## 빠른 사용 예

```
/watch https://youtu.be/dQw4w9WgXcQ what happens at the 30 second mark?
/watch bug-repro.mov what's going wrong?
/watch https://youtu.be/abc --start 2:15 --end 2:45
/watch video.mp4 summarize this
```

## 이 문서와 원본의 관계

| 항목 | 위치 |
|------|------|
| 캐논 스킬 (호스트가 읽는 계약) | `skills/watch/SKILL.md` |
| 런타임 | `skills/watch/scripts/` |
| 이 포터블 가이드 | `Analysis/watch_skill.md` (본 파일) |

버전을 올릴 때는 `skills/watch/SKILL.md` frontmatter, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`과 함께 맞추세요. 이 파일을 배포용으로 복사할 때도 `version`을 동기화하세요.
