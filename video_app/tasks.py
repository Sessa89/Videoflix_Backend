"""
Background tasks for media processing.

The example task runs an ffmpeg command to produce a 480p version of the
source file. This is intentionally minimal and synchronous from the
worker's perspective.

Security note: we build the shell command via format string. For untrusted
paths or user input, prefer `subprocess.run([...], check=True)` with a list
of arguments and avoid `shell=True`.
"""

import subprocess

def convert_480p(source):
    """
    Convert a given video file to a 480p H.264/AAC MP4.

    Args:
        source: Absolute path to the input video file on disk.

    Side-effects:
        Writes a sibling file with suffix `_480p.mp4`.
    """

    target = source + '_480p.mp4'
    cmd = 'ffmpeg -i "{}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, target)
    subprocess.run(cmd)

