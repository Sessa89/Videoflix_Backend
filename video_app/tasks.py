"""
Background tasks for media processing.

The example task runs an ffmpeg command to produce a 480p version of the
source file. This is intentionally minimal and synchronous from the
worker's perspective.

Security note: we build the shell command via format string. For untrusted
paths or user input, prefer `subprocess.run([...], check=True)` with a list
of arguments and avoid `shell=True`.
"""

import os
import shlex
import subprocess
from pathlib import Path
from django.conf import settings

def _run(cmd: str):
    proc = subprocess.run(
        shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({proc.returncode}):\n{proc.stdout}")
    return proc.stdout

def _res_to_height(res: str) -> int:
    try:
        return int(res.lower().replace('p', ''))
    except Exception:
        raise ValueError(f"Invalid resolution: {res}")

def transcode_to_hls(video_id: int, source_path: str, resolutions=None, seg_seconds: int = None):
    if not source_path or not os.path.exists(source_path):
        raise FileNotFoundError(f"Video file not found: {source_path}")

    hls_root = Path(getattr(settings, 'HLS_ROOT', Path.cwd() / 'hls'))
    seg_seconds = seg_seconds or int(getattr(settings, 'HLS_SEGMENT_SECONDS', 6))
    allowed = getattr(settings, 'HLS_ALLOWED_RESOLUTIONS', {'480p', '720p'})
    if resolutions:
        resolutions = [r for r in resolutions if r in allowed]
    else:
        resolutions = sorted(allowed, key=lambda r: _res_to_height(r))

    for res in resolutions:
        height = _res_to_height(res)
        outdir = hls_root / str(video_id) / res
        outdir.mkdir(parents=True, exist_ok=True)

        cmd = (
            f'ffmpeg -y -i "{source_path}" '
            f'-vf "scale=-2:{height}" -c:v libx264 -preset veryfast -crf 23 '
            f'-c:a aac -ac 2 -ar 48000 -b:a 128k '
            f'-hls_time {seg_seconds} -hls_playlist_type vod '
            f'-hls_segment_filename "{outdir}/%03d.ts" "{outdir}/index.m3u8"'
        )
        _run(cmd)