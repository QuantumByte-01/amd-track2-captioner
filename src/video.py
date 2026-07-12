"""Video download and frame extraction via ffmpeg."""

from __future__ import annotations

import base64
import glob
import os
import subprocess
from pathlib import Path

import requests

from src import config


def download(url: str, dest: str, retries: int = 3) -> str:
    """Stream-download a video URL to dest; verify size > 100KB."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
            if os.path.getsize(dest) > 100 * 1024:
                return dest
            raise ValueError(f"downloaded file too small: {dest}")
        except Exception as e:
            last_err = e
            if os.path.exists(dest):
                os.remove(dest)
    if last_err:
        raise last_err
    raise RuntimeError(f"download failed for {url}")


def duration(path: str) -> float:
    """Return video duration in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def _seek_frame(path: str, out_path: str, t: float) -> bool:
    cmd = [
        "ffmpeg",
        "-ss",
        f"{t:.2f}",
        "-i",
        path,
        "-frames:v",
        "1",
        "-vf",
        "scale=768:-2",
        "-q:v",
        "3",
        "-y",
        "-loglevel",
        "error",
        out_path,
    ]
    subprocess.run(cmd, check=False)
    return os.path.exists(out_path) and os.path.getsize(out_path) > 0


def _fps_fallback(path: str, out_dir: str, n: int, d: float) -> list[str]:
    pattern = os.path.join(out_dir, "f_%02d.jpg")
    fps = max(n / max(d, 1.0), 0.1)
    cmd = [
        "ffmpeg",
        "-i",
        path,
        "-vf",
        f"fps={fps},scale=768:-2",
        "-q:v",
        "3",
        "-y",
        "-loglevel",
        "error",
        pattern,
    ]
    subprocess.run(cmd, check=False)
    frames = sorted(glob.glob(os.path.join(out_dir, "f_*.jpg")))
    return frames[:n]


def extract_frames(path: str, out_dir: str, n: int | None = None) -> list[str]:
    """Extract n uniformly spaced frames using fast input-side seek."""
    n = n or config.FRAMES_PER_CLIP
    os.makedirs(out_dir, exist_ok=True)
    d = duration(path)

    if n <= 1:
        timestamps = [d * 0.5]
    else:
        timestamps = [d * (0.05 + 0.90 * i / (n - 1)) for i in range(n)]

    frames: list[str] = []
    for i, t in enumerate(timestamps):
        out_path = os.path.join(out_dir, f"f_{i:02d}.jpg")
        if _seek_frame(path, out_path, t):
            frames.append(out_path)

    if len(frames) < 3:
        for f in glob.glob(os.path.join(out_dir, "f_*.jpg")):
            os.remove(f)
        frames = _fps_fallback(path, out_dir, n, d)

    return sorted(frames)


def fetch_frames_direct(url: str, out_dir: str, n: int | None = None) -> list[str]:
    """Extract frames directly from a URL without a prior download."""
    n = n or config.FRAMES_PER_CLIP
    os.makedirs(out_dir, exist_ok=True)

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        d = float(probe.stdout.strip())
    except ValueError:
        d = 60.0

    if n <= 1:
        timestamps = [d * 0.5]
    else:
        timestamps = [d * (0.05 + 0.90 * i / (n - 1)) for i in range(n)]

    frames: list[str] = []
    for i, t in enumerate(timestamps):
        out_path = os.path.join(out_dir, f"f_{i:02d}.jpg")
        if _seek_frame(url, out_path, t):
            frames.append(out_path)

    if len(frames) < 3:
        for f in glob.glob(os.path.join(out_dir, "f_*.jpg")):
            os.remove(f)
        frames = _fps_fallback(url, out_dir, n, d)

    return sorted(frames)


def b64(path: str) -> str:
    """Read a JPEG and return base64-encoded bytes."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")
