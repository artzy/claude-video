# watch 스킬 유저(전역) 설치

날짜: 2026-08-26

## 설치

```
C:\Users\PM\.cursor\skills\watch  →  (junction)  d:\study\claude-video\skills\watch
```

프로젝트용 `.cursor/skills/watch`와 동일한 소스를 가리킴. 저장소의 `SKILL.md` / `scripts/` 수정이 전역에도 즉시 반영됨.

## 사용

1. Cursor에서 **새 Agent 채팅** 열기 (스킬 목록 갱신)
2. `/watch <url>` 또는 YouTube URL 붙여넣기
3. 요약은 **한줄 요약 → 핵심정리 → 내용** 형식

## 확인

- `python %USERPROFILE%\.cursor\skills\watch\scripts\setup.py --check` → exit 0