#!/usr/bin/env python3
"""Download a video via yt-dlp, or resolve a local file path.

Also fetches subtitles (manual first, then auto-generated) in VTT format so
transcribe.py can parse them without needing Whisper.

YouTube occasionally returns HTTP 403 on the first format/client choice.
``download_url`` retries with alternate ``--extractor-args`` / format profiles
before giving up.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi", ".flv", ".wmv"}

# Default format: ?‰¤720p video+audio, then any best under 720, then unrestricted.
DEFAULT_FMT = "bv*[height<=720]+ba/b[height<=720]/bv+ba/b"
AUDIO_FMT = "ba/bestaudio"
# iOS HLS often survives when progressive URLs 403.
IOS_HLS_FMT = (
    "bv*[protocol=m3u8_native]+ba[protocol=m3u8_native]/"
    "b[protocol=m3u8_native]/bv*+ba/b"
)

# Ordered YouTube fallbacks after a failed primary download (no output file).
# Empty dict = stock yt-dlp defaults (same as the first attempt's base flags).
YOUTUBE_RETRY_PROFILES: list[dict] = [
    {
        "label": "tv client",
        "extractor_args": "youtube:player_client=tv,tv_simply",
    },
    {
        "label": "android+web (no android_sdkless)",
        "extractor_args": "youtube:player_client=android,web,mweb,-android_sdkless",
    },
    {
        "label": "ios HLS",
        "extractor_args": "youtube:player_client=ios;formats=missing_pot",
        "format": IOS_HLS_FMT,
    },
]


def is_url(source: str) -> bool:
    if source.startswith("-"):
        return False
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_youtube_url(source: str) -> bool:
    if not is_url(source):
        return False
    host = (urlparse(source).hostname or "").lower()
    return (
        host in ("youtu.be", "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com")
        or host.endswith(".youtube.com")
    )


def resolve_local(path: str) -> dict:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise SystemExit(f"File not found: {p}")
    if p.suffix.lower() not in VIDEO_EXTS:
        print(
            f"[watch] warning: {p.suffix} is not a known video extension, proceeding anyway",
            file=sys.stderr,
        )
    return {
        "video_path": str(p),
        "subtitle_path": None,
        "info": {"title": p.name, "url": str(p)},
        "downloaded": False,
    }


def _pick_subtitle(out_dir: Path) -> Path | None:
    candidates = sorted(out_dir.glob("video*.vtt"))
    if not candidates:
        return None
    preferred = [
        c for c in candidates
        if any(marker in c.name for marker in (".en.", ".en-US.", ".en-GB.", ".en-orig."))
    ]
    return preferred[0] if preferred else candidates[0]


def _pick_video(out_dir: Path) -> Path | None:
    for ext in (".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3", ".opus"):
        for candidate in out_dir.glob(f"video*{ext}"):
            # Ignore incomplete/partial names like video.f398.mp4.part ??? glob
            # already requires the extension to be last, but skip .part siblings.
            if candidate.name.endswith(".part"):
                continue
            return candidate
    for candidate in out_dir.glob("video.*"):
        if candidate.suffix.lower() in VIDEO_EXTS:
            return candidate
    return None


def _clear_partial_media(out_dir: Path) -> None:
    """Remove incomplete media so a retry does not pick a half-written file."""
    if not out_dir.exists():
        return
    keep_suffixes = {".vtt", ".json", ".srt", ".ttml"}
    for path in out_dir.iterdir():
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".part") or name.endswith(".ytdl"):
            path.unlink(missing_ok=True)
            continue
        if path.suffix.lower() in keep_suffixes:
            continue
        # Drop media from the failed attempt (merged or split: video.mp4, video.f398.mp4)
        if name.startswith("video"):
            path.unlink(missing_ok=True)


def _build_yt_dlp_cmd(
    url: str,
    output_template: str,
    *,
    audio_only: bool = False,
    format_override: str | None = None,
    extractor_args: str | None = None,
    js_runtimes: str | None = None,
    skip_download: bool = False,
) -> list[str]:
    fmt = format_override or (AUDIO_FMT if audio_only else DEFAULT_FMT)
    cmd = ["yt-dlp"]
    if skip_download:
        cmd.append("--skip-download")
    else:
        cmd += ["-N", "8", "-f", fmt, "--merge-output-format", "mp4"]
    if extractor_args:
        cmd += ["--extractor-args", extractor_args]
    if js_runtimes:
        cmd += ["--js-runtimes", js_runtimes]
    cmd += [
        "--write-info-json",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", "en.*",
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "--no-playlist",
        "--ignore-errors",
        "-o", output_template,
        "--",
        url,
    ]
    return cmd


def fetch_captions(url: str, out_dir: Path) -> dict:
    """Fetch metadata and best available VTT captions without downloading video."""
    if shutil.which("yt-dlp") is None:
        raise SystemExit("yt-dlp is not installed. Install with: brew install yt-dlp")

    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / "video.%(ext)s")
    cmd = _build_yt_dlp_cmd(url, output_template, skip_download=True)
    subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    subtitle = _pick_subtitle(out_dir)
    info = _read_info(out_dir / "video.info.json", url)
    return {
        "video_path": None,
        "subtitle_path": str(subtitle) if subtitle else None,
        "info": info or {"url": url},
        "downloaded": False,
    }


def _read_info(info_path: Path, url: str) -> dict:
    info: dict = {}
    if info_path.exists():
        try:
            raw = json.loads(info_path.read_text(encoding="utf-8"))
            info = {
                "title": raw.get("title"),
                "uploader": raw.get("uploader") or raw.get("channel"),
                "duration": raw.get("duration"),
                "url": raw.get("webpage_url") or url,
            }
        except Exception as exc:
            print(f"[watch] info.json parse failed: {exc}", file=sys.stderr)
            info = {"url": url}
    return info


def _run_download_once(
    url: str,
    out_dir: Path,
    *,
    audio_only: bool = False,
    format_override: str | None = None,
    extractor_args: str | None = None,
    js_runtimes: str | None = None,
) -> tuple[Path | None, int]:
    output_template = str(out_dir / "video.%(ext)s")
    cmd = _build_yt_dlp_cmd(
        url,
        output_template,
        audio_only=audio_only,
        format_override=format_override,
        extractor_args=extractor_args,
        js_runtimes=js_runtimes,
    )
    # yt-dlp may exit non-zero if a subtitle variant fails (e.g. 429) even when
    # the video itself downloaded fine. Treat "video file present" as success.
    result = subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    return _pick_video(out_dir), result.returncode


def download_url(
    url: str,
    out_dir: Path,
    audio_only: bool = False,
) -> dict:
    if shutil.which("yt-dlp") is None:
        raise SystemExit("yt-dlp is not installed. Install with: brew install yt-dlp")

    out_dir.mkdir(parents=True, exist_ok=True)

    video, returncode = _run_download_once(url, out_dir, audio_only=audio_only)

    if video is None and is_youtube_url(url) and not audio_only:
        for profile in YOUTUBE_RETRY_PROFILES:
            label = profile.get("label", "retry")
            print(
                f"[watch] YouTube download missing file ??? retrying with {label}???",
                file=sys.stderr,
            )
            _clear_partial_media(out_dir)
            video, returncode = _run_download_once(
                url,
                out_dir,
                audio_only=audio_only,
                format_override=profile.get("format"),
                extractor_args=profile.get("extractor_args"),
                js_runtimes=profile.get("js_runtimes"),
            )
            if video is not None:
                print(f"[watch] download recovered via {label}", file=sys.stderr)
                break

    if video is None:
        raise SystemExit(
            f"yt-dlp did not produce a video file in {out_dir} (exit {returncode}). "
            "For YouTube 403s, update yt-dlp, install a JS runtime (deno), or pass cookies."
        )

    subtitle = _pick_subtitle(out_dir)
    info = _read_info(out_dir / "video.info.json", url)

    return {
        "video_path": str(video),
        "subtitle_path": str(subtitle) if subtitle else None,
        "info": info or {"url": url},
        "downloaded": True,
    }


def download(
    source: str,
    out_dir: Path,
    audio_only: bool = False,
) -> dict:
    if is_url(source):
        return download_url(source, out_dir, audio_only=audio_only)
    return resolve_local(source)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: download.py <url-or-path> <out-dir>", file=sys.stderr)
        raise SystemExit(2)
    result = download(sys.argv[1], Path(sys.argv[2]))
    print(json.dumps(result, indent=2))
