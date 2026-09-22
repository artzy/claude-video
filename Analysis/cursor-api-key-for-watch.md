# watch에서 Cursor API 키 사용 가능 여부

날짜: 2026-08-05

## 결론

**불가.** `/watch`의 Whisper 폴백은 Groq / OpenAI 음성 전사 API만 지원하며, Cursor API 키(`CURSOR_API_KEY`)는 에이전트 실행(SDK)용이라 경로가 다르다.

## 근거

| 키 | 용도 | 엔드포인트 |
|----|------|------------|
| `GROQ_API_KEY` | Whisper 전사 (권장) | `api.groq.com/.../audio/transcriptions` |
| `OPENAI_API_KEY` | Whisper 전사 (폴백) | `api.openai.com/.../audio/transcriptions` |
| `CURSOR_API_KEY` | Cursor Agent SDK | 에이전트 실행 (Whisper 없음) |

구현: `skills/watch/scripts/whisper.py`의 `load_api_key()`는 `GROQ_API_KEY` / `OPENAI_API_KEY`만 읽는다.

## 실제 비용 구조

- **프레임 + 요약:** Cursor 채팅/구독 토큰으로 이미 처리됨 (에이전트가 JPEG를 `Read`하고 답변).
- **Whisper 키:** 플랫폼 자막이 없을 때만 필요. YouTube는 보통 자막이 있어 키 없이 진행 가능한 경우가 많음.

## 선택지

1. 키 없이 진행 (`SETUP_COMPLETE=true`, 자막 없으면 프레임만).
2. 무료/저렴한 Groq 키를 `~/.config/watch/.env`에 설정.
3. 로컬 Whisper 등은 현재 스킬에 없음 (별도 확장 필요).
