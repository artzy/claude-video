# SKILL.md Cursor IDE 맞춤 수정

날짜: 2026-08-26

## 목적

`skills/watch/SKILL.md`를 멀티 호스트 중립 문서에서 **Cursor Agent Skills** 실행 계약에 맞게 재작성.

## 변경 요지

| 항목 | 이전 | Cursor용 |
|------|------|----------|
| allowed-tools | Bash, Shell, Read, AskUserQuestion | Shell, Read |
| 셸 예시 | bash 우선 + PowerShell 부록 | PowerShell 우선 + bash 동등 |
| Python | python3 기본, Windows만 치환 | Windows python 기본, Unix는 python3 |
| 사용자 질문 | AskUserQuestion 또는 채팅 | 채팅만 |
| SKILL_DIR 예 | Claude/Codex/Cursor/agents 전부 | ~/.cursor/skills, .cursor/skills만 |
| API 키 | Groq/OpenAI만 | Cursor API ≠ Whisper 명시 |
| Windows 설치 | 일반 안내 | winget 후 PATH 갱신 절차 |
| ffmpeg | (암시) | -fps_mode vs deprecated -vsync 실패 모드 |

## 유지

- Step 0–5 파이프라인, detail 모드, focus/timestamps, 보안 경계, 버전 0.2.1
- 프로젝트 junction `.cursor/skills/watch` → `skills/watch` 이므로 Cursor가 동일 파일 로드

## 검증

- [ ] 새 Agent 채팅에서 `/watch` 또는 URL로 스킬 로드
- [ ] Windows에서 `python …\setup.py --check` exit 0
- [ ] 첫 실행 질문이 채팅으로 나오는지