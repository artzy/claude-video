# YouTube 403 시 yt-dlp 재시도

날짜: 2026-08-26

## 문제

`balanced`/`efficient` 다운로드가 `HTTP Error 403: Forbidden`으로 실패해 프레임 추출이 불가했음 (예: `tLoFe65IFaE`, format `398+251`).

## 해결

`skills/watch/scripts/download.py`:

1. 1차: 기존 기본 yt-dlp 호출
2. YouTube이고 출력 파일이 없으면 순차 재시도:
   - `player_client=tv,tv_simply` (실측 성공)
   - `android,web,mweb,-android_sdkless`
   - `ios` + HLS formats
3. 재시도 전 `.part` / 실패 미디어만 삭제 (자막·info.json 유지)

`SKILL.md` Failure modes: 첫 403 후 transcript-only로 포기하지 말고 스크립트 재시도 체인을 끝까지 맡김.

## 검증

- `tests/test_download.py` 5 passed
- `watch.py … tLoFe65IFaE --detail efficient` → `video.mp4` + 프레임 생성