# Cursor 호환성 수정 요약 (claude-video / watch)

날짜: 2026-08-05
버전: 0.2.1

## 목적

`/watch` 스킬이 Claude Code뿐 아니라 **Cursor Agent Skills**에서도 설치·발견·실행되도록 계약을 다듬었다.

## 주요 변경

1. **SKILL.md**
   - `~/.cursor/skills/watch`, `<project>/.cursor/skills/watch` 경로 명시
   - `allowed-tools`에 `Shell` 추가 (Cursor)
   - `AskUserQuestion`이 없는 호스트에서는 일반 채팅으로 동일 질문
   - Windows PowerShell용 `SKILL_DIR` 가드·정리(`Remove-Item`) 예시
   - description에 Cursor 디스커버리용 트리거 문구(`/watch`, YouTube URL, `.mp4` 등)
   - "Claude" 전용 표현을 agent 중립으로 완화

2. **README / AGENTS**
   - Cursor 전용 설치 플래그: `npx skills add … -g -a cursor -y`
   - Windows junction 설치 절차 문서화

3. **플러그인 메타**
   - `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` → `0.2.1`, agent 중립 description

4. **로컬 설치 (이 머신)**
   - 프로젝트: `d:\study\claude-video\.cursor\skills\watch` → `skills\watch` (junction)
   - 글로벌: `%USERPROFILE%\.cursor\skills\watch` → 동일 소스 (junction)
   - `.cursor/`는 `.gitignore`에 추가 (로컬 개발용)

## 사용 방법

1. Cursor에서 **새 Agent 채팅**을 연다 (스킬 목록 갱신).
2. `/watch <url-or-path> [질문]` 또는 비디오 URL을 붙여 넣는다.
3. 첫 실행 시 `ffmpeg` / `yt-dlp` / Whisper 키 안내를 따른다.
4. Windows에서는 스크립트를 `python`으로 실행한다 (`python3` 아님).

## 검증 체크리스트

- [ ] Agent 채팅에서 `watch` 스킬이 로드되는지
- [ ] `python %USERPROFILE%\.cursor\skills\watch\scripts\setup.py --json` 가 실행되는지
- [ ] `/watch` 또는 URL 붙여넣기로 파이프라인이 도는지
