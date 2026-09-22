"""yt-dlp argv construction for download.py.

Regression guard: ``--sub-langs all`` makes yt-dlp fetch YouTube's hundreds of
auto-translated caption tracks, which can take minutes and stalls before the
video download even starts. We only support English, so the request must stay
bounded to the English-only pattern.

Also covers YouTube HTTP 403 recovery: when the first download leaves no file,
``download_url`` retries with alternate player-client profiles.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "watch" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import download  # noqa: E402

URL = "https://www.youtube.com/watch?v=rlOpbu3Enkw"


def _capture_argv(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Stub subprocess.run inside download.py and record every argv."""
    calls: list[list[str]] = []

    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        return _Result()

    monkeypatch.setattr(download.subprocess, "run", fake_run)
    return calls


def _sub_langs(argv: list[str]) -> str:
    idx = argv.index("--sub-langs")
    return argv[idx + 1]


def _assert_english_only(langs: str) -> None:
    tokens = langs.split(",")
    assert "all" not in tokens, f"sub-langs must not request all languages, got {langs!r}"
    assert all(t.startswith("en") for t in tokens), f"sub-langs must be English-only, got {langs!r}"


def test_fetch_captions_requests_english_only(monkeypatch, tmp_path):
    calls = _capture_argv(monkeypatch)
    download.fetch_captions(URL, tmp_path / "download")
    _assert_english_only(_sub_langs(calls[0]))


def test_download_url_requests_english_only(monkeypatch, tmp_path):
    calls = _capture_argv(monkeypatch)
    # _pick_video returns None with no real file, which raises SystemExit after
    # the yt-dlp argv is already built ??? that's all we need to inspect.
    with pytest.raises(SystemExit):
        download.download_url(URL, tmp_path / "download")
    _assert_english_only(_sub_langs(calls[0]))
    # Primary + YouTube retry profiles
    assert len(calls) == 1 + len(download.YOUTUBE_RETRY_PROFILES)


def test_is_youtube_url():
    assert download.is_youtube_url("https://www.youtube.com/watch?v=abc")
    assert download.is_youtube_url("https://youtu.be/abc")
    assert download.is_youtube_url("https://m.youtube.com/watch?v=abc")
    assert not download.is_youtube_url("https://vimeo.com/123")
    assert not download.is_youtube_url(r"C:\videos\clip.mp4")


def test_youtube_403_retry_uses_tv_client(monkeypatch, tmp_path):
    calls = _capture_argv(monkeypatch)
    out = tmp_path / "download"
    out.mkdir()

    # After the first (empty) attempt, plant a file on the TV-client retry so
    # download_url succeeds without exhausting every profile.
    state = {"n": 0}

    class _Result:
        returncode = 1
        stdout = ""
        stderr = ""

    real_pick = download._pick_video

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        state["n"] += 1
        if state["n"] == 2:
            (out / "video.mp4").write_bytes(b"fake")
        return _Result()

    monkeypatch.setattr(download.subprocess, "run", fake_run)
    monkeypatch.setattr(download, "_pick_video", lambda d: real_pick(d))

    result = download.download_url(URL, out)
    assert result["downloaded"] is True
    assert Path(result["video_path"]).name == "video.mp4"
    assert any("youtube:player_client=tv,tv_simply" in arg for argv in calls for arg in argv)
    # Stopped after recovery (primary + first retry), not all profiles
    assert len(calls) == 2


def test_non_youtube_does_not_retry_profiles(monkeypatch, tmp_path):
    calls = _capture_argv(monkeypatch)
    with pytest.raises(SystemExit):
        download.download_url("https://vimeo.com/123456", tmp_path / "download")
    assert len(calls) == 1
