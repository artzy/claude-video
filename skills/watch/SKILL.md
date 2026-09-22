---
name: watch
version: "0.2.1"
description: >-
  Watch a video (URL or local path) in Cursor. Downloads with yt-dlp, extracts
  auto-scaled frames with ffmpeg, pulls a timestamped transcript from captions
  (or Whisper API fallback), then Read-s each JPEG and answers from what's on
  screen and in the audio. Use when the user pastes a YouTube/TikTok/Loom/Vimeo
  URL, a local .mp4/.mov/.mkv/.webm, types /watch, or asks what happens in a video.
argument-hint: "<video-url-or-path> [question]"
allowed-tools: Shell, Read
homepage: https://github.com/bradautomates/claude-video
repository: https://github.com/bradautomates/claude-video
author: bradautomates
license: MIT
user-invocable: true
---

# /watch (Cursor)

You don't have a video input; this skill gives you one. Bundled Python scripts download (or open a local file), pull captions, extract JPEG frames, and print paths. You `Read` every frame path (images render in Cursor), combine them with the transcript, and answer.

**Host notes (Cursor-specific):**
- Run scripts with the **Shell** tool. Ask setup questions in **normal chat** and wait for a reply (no `AskUserQuestion`).
- **Windows:** use `python` (not `python3` — Store stub). Prefer PowerShell examples below. After `winget` installs, refresh `PATH` in the same shell before calling binaries.
- **macOS / Linux Cursor:** use `python3` and bash equivalents of the same steps.
- **Cursor API key ≠ Whisper.** `CURSOR_API_KEY` / subscription does not power transcription. Whisper needs `GROQ_API_KEY` or `OPENAI_API_KEY` in `~/.config/watch/.env` (Windows: `$env:USERPROFILE\.config\watch\.env`). Native captions alone are enough for many YouTube videos; keyless setup is allowed.

## Resolve `SKILL_DIR` (before any command)

Set `SKILL_DIR` to the **absolute directory of THIS SKILL.md** (from the Read result). Scripts live at `SKILL_DIR/scripts/watch.py`.

Typical Cursor layouts:

```
Read ~/.cursor/skills/watch/SKILL.md              -> SKILL_DIR=.../skills/watch
Read <project>/.cursor/skills/watch/SKILL.md      -> SKILL_DIR=<project>/.cursor/skills/watch
```

Do **not** use `${CLAUDE_SKILL_DIR}` or other host-only env vars.

Guard once:

```powershell
$SKILL_DIR = "<absolute path of the directory containing the SKILL.md you Read>"
if (-not (Test-Path "$SKILL_DIR\scripts\watch.py")) {
  Write-Error "scripts/watch.py not found under SKILL_DIR=$SKILL_DIR"
  exit 1
}
```

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you Read>"
if [ ! -f "$SKILL_DIR/scripts/watch.py" ]; then
  echo "ERROR: scripts/watch.py not found under SKILL_DIR=$SKILL_DIR" >&2
  exit 1
fi
```

Below, `python` means Windows Cursor; on macOS/Linux Cursor substitute `python3`. Paths may use `/` or `\`.

## Step 0 — Setup preflight (every `/watch`, silent on success)

First `/watch` in a session — structured preflight:

```powershell
python "$SKILL_DIR\scripts\setup.py" --json
```

Branch:

- **`can_proceed: true` and `first_run: false`** -> proceed to Step 1 with no status chatter.
- **`first_run: true`** -> in order:
  1. If `missing_binaries` is non-empty, run the installer and confirm binaries exist. **Do not skip to preferences.** On Windows the installer prints `winget` / `pip` commands — run them, then refresh PATH:
     ```powershell
     $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
     ```
  2. Re-run the installer if needed so it scaffolds `~/.config/watch/.env` **before** you write values.
  3. In chat: encourage a Groq (preferred) or OpenAI Whisper key; ask the detail preference below; write selections into `.env` and set `SETUP_COMPLETE=true`. User may decline the key — then keyless + `--no-whisper` when captions are missing is fine.
- **`can_proceed: false` and `first_run: false`** -> environment regressed; run installer to remediate. Do not re-ask preferences.

Follow-up `/watch` in the same session:

```powershell
python "$SKILL_DIR\scripts\setup.py" --check
```

Exit 0 -> proceed silently (includes keyless completed setup). **Do not** announce "setup is complete." Non-zero:

| Exit | Meaning | Action |
|------|---------|--------|
| `2` | Missing `ffmpeg` / `ffprobe` / `yt-dlp` | Run installer |
| `3` | First run, no Whisper key | Scaffold `.env`, encourage key (may decline) |
| `4` | Both | Installer, then encourage key |

Installer (idempotent):

```powershell
python "$SKILL_DIR\scripts\setup.py"
```

**Whisper key (optional):** chat-ask Groq ([console.groq.com/keys](https://console.groq.com/keys)) or OpenAI. Write `GROQ_API_KEY=...` or `OPENAI_API_KEY=...` on its own line in `~/.config/watch/.env`. No key -> proceed; captionless videos are frames-only unless Whisper is added later.

**First-run detail** — present in this order (keep `(recommended)` on `balanced`):

- `transcript` — transcript only (skips video download when captions exist)
- `efficient` — keyframes, cap 50
- `balanced` (recommended) — scene-aware, cap 100
- `token-burner` — scene-aware, uncapped

Write bare lines (no trailing `# comment`):

```
WATCH_DETAIL=balanced
SETUP_COMPLETE=true
```

Skip the preference question when `SETUP_COMPLETE=true`. Default to `balanced` if the user skips.

`--json` fields: `{status, can_proceed, first_run, setup_complete, missing_binaries, whisper_backend, has_api_key, config_file, watch_detail, platform}` — `status` is aspirational (`needs_key` even when keyless is OK); gate on `can_proceed` / `first_run`.

## When to use

- User pastes a video URL (YouTube, Vimeo, X, TikTok, Twitch clip, yt-dlp sites) and asks about it
- Local video (`.mp4`, `.mov`, `.mkv`, `.webm`, …)
- `/watch <url-or-path> [question]`

## Recommended limits

- Best under **10 minutes**. Cap **2 fps**. Detail caps: `transcript` 0 / `efficient` 50 / `balanced` 100 / `token-burner` uncapped (`--max-frames` overrides).
- Duration budgets (scene fill <= detail cap): <=30s ~12–30; 30s–1m ~40; 1–3m ~60; 3–10m ~80; >10m sparse + warning — offer `--start`/`--end` for long clips.

## How to invoke

**Step 1 — parse.** Source vs question. Example: `/watch https://youtu.be/abc what language?` -> source URL, question = language.

**Step 2 — run** (quote the source; don't over-escape):

```powershell
python "$SKILL_DIR\scripts\watch.py" "<source>"
```

Useful flags:

- `--detail transcript|efficient|balanced|token-burner`
- `--start T` / `--end T` — `SS` | `MM:SS` | `HH:MM:SS` (denser focused budgets)
- `--timestamps T1,T2,…` — force frames at absolute times (after scanning transcript for "look here" cues)
- `--max-frames N`, `--resolution W` (default 512; 1024 only to read on-screen text), `--fps F` (<=2)
- `--out-dir DIR`, `--whisper groq|openai`, `--no-whisper`, `--no-dedup`

Focused budgets (`balanced` cap 100): <=5s <=10f; 5–15s <=30; 15–30s <=60; 30–60s <=80; 60–180s <=100. Use for named moments or long videos with a narrow question. Transcript is range-filtered; frame times stay absolute.

```powershell
python "$SKILL_DIR\scripts\watch.py" video.mp4 --start 50 --end 60
python "$SKILL_DIR\scripts\watch.py" "$URL" --start 2:15 --end 2:45 --fps 2
python "$SKILL_DIR\scripts\watch.py" "$URL" --start 1:12:00
```

**Step 3 — Read every listed frame** in one turn (parallel `Read` calls). Align `t=MM:SS` to the transcript.

**Step 4 — answer.** Use frames + transcript (`captions` | `whisper (groq)` | `whisper (openai)`). **Never** paste the full raw transcript unless the user asked for it. Even in `transcript` detail mode, write a structured summary (below), not a caption dump.

### Answer format (required for summaries)

When the user asks to summarize, watch, or does not ask a narrow factual question, answer in the user's language with **exactly this section order**. Korean users -> keep these headings; other languages -> translate the three headings only, keep the same order and depth.

1. **한줄 요약** — One or two sentences: what the video is and the main takeaway (title/uploader/duration optional in a short lead line above or inside).
2. **핵심정리** — Bullet list of the main points only (claims, numbers, comparisons, conclusions). Dense and skimmable; cite key timestamps where useful (`MM:SS`).
3. **내용** — **Write this section as thoroughly as possible.** Expand with everything grounded in the frames and transcript: section-by-section or chronological walkthrough, on-screen visuals, spoken arguments, names/products/prices/metrics, tradeoffs, and how the ending lands. Prefer more detail over brevity here — add substance from both streams of evidence; do not stop at a thin paraphrase of 핵심정리. Use timestamps liberally. Quote only short lines that matter.

If the user asked a **specific question**, lead with a direct answer (with timestamps), then still add **한줄 요약 → 핵심정리 → 내용** when a full watch/summary is implied; for a pure pinpoint question, a short cited answer is enough.

**Step 5 — clean up** when no follow-ups:

```powershell
Remove-Item -Recurse -Force <workdir>
```

```bash
rm -rf <workdir>
```

## Detail and frames

From `WATCH_DETAIL` in `~/.config/watch/.env` (default `balanced`):

- `transcript` — captions (or Whisper audio-only); no frames unless `--timestamps`
- `efficient` — keyframes (`ffmpeg -skip_frame nokey`); <4 keys -> uniform fallback
- `balanced` / `token-burner` — scene-aware (uniform if static); caps 100 / none. Heights clamped to 1998px for Cursor `Read`.

## Transcript-cue frames

Scene/keyframe selection can miss "look here" moments. After a transcript pass:

1. Pick deictic cues (skip rhetorical "look, the point is…")
2. Re-run with `--timestamps 4:32,7:10` on the **local downloaded file** in the work dir (avoid re-download)

Cue frames (`reason=transcript-cue`) are additive, reserved against the cap first, dropped if outside `--start`/`--end`. `--detail transcript --timestamps …` returns cue frames only (downloads video for pixels).

## Transcription

1. **Native captions** (preferred) via yt-dlp
2. **Whisper** if no captions / local file: mono 16 kHz mp3 -> Groq `whisper-large-v3` or OpenAI `whisper-1`. Prefer Groq when both keys set. `--no-whisper` skips fallback.

## Failure modes

- Setup failed -> run `setup.py`; ask for key in chat if needed
- No transcript -> frames-only; say so
- Long-video warning -> offer focused `--start`/`--end`
- **YouTube HTTP 403 / missing video file** -> `download.py` already retries yt-dlp with alternate player clients (`tv,tv_simply` -> android/web -> ios HLS). Do **not** fall back to transcript-only after the first 403; let the script finish its retry chain. If every attempt fails, tell the user to update yt-dlp, install Deno (JS runtime), or pass cookies — don't invent extra manual yt-dlp loops in chat.
- Download fail (login/region / non-YouTube) -> tell user; don't retry loops beyond what the script does
- Whisper fail -> stderr; retry other backend; chunked uploads tolerate length; "none available" only if all chunks fail
- Frame extract fails on very new ffmpeg -> ensure skill scripts use `-fps_mode vfr` (not deprecated `-vsync`)

## Token efficiency

Cost is mostly frames (~50–80k image tokens for ~80x512px). Transcript is cheap. Don't re-run `/watch` for follow-ups in the same session — reuse frames + transcript already in context.

## Security & Permissions

**Does:** local `yt-dlp` + `ffmpeg`/`ffprobe`; optional audio upload to Groq or OpenAI Whisper only; writes workdir under system temp (or `--out-dir`); reads/writes `~/.config/watch/.env` (and cwd `.env` fallback).

**Does not:** upload the video file; use platform logins; send keys across providers; use Cursor API for Whisper; persist outside workdir + `.env`.

**Bundled scripts:** `watch.py`, `download.py`, `frames.py`, `transcribe.py`, `whisper.py`, `setup.py`, `config.py`.