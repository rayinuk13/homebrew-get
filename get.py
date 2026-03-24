#!/usr/bin/env python3
"""
get - Download YouTube videos or audio from the command line.

Usage:
  get -mp3 <url>   Download audio as MP3
  get -mp4 <url>   Download video as MP4
"""

import os
import shutil
import subprocess
import sys

VERSION = "1.0.0"

BANNER = r"""
  __ _  ___| |_
 / _` |/ _ \ __|
| (_| |  __/ |_
 \__, |\___|\__|
 |___/
"""


def usage():
    print(BANNER.strip())
    print(f"\nget v{VERSION} — YouTube downloader\n")
    print("Usage:")
    print("  get -mp3 <url>   Download audio as MP3")
    print("  get -mp4 <url>   Download video as MP4 (best quality)")
    print()
    print("Examples:")
    print("  get -mp3 https://youtube.com/watch?v=...")
    print("  get -mp4 https://youtube.com/watch?v=...")
    sys.exit(0)


def check_deps():
    missing = []
    for dep in ("yt-dlp", "ffmpeg"):
        if not shutil.which(dep):
            missing.append(dep)
    if missing:
        print(f"[get] missing dependencies: {', '.join(missing)}")
        print("      install with: brew install " + " ".join(missing))
        sys.exit(1)


def download(mode, url):
    out_dir = os.path.expanduser("~/Downloads")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[get] downloading {'audio (MP3)' if mode == 'mp3' else 'video (MP4)'}")
    print(f"[get] url: {url}")
    print(f"[get] destination: {out_dir}/")
    print()

    if mode == "mp3":
        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "0",
            "--embed-thumbnail",
            "--add-metadata",
            "--output",
            f"{out_dir}/%(title)s.%(ext)s",
            url,
        ]
    else:
        cmd = [
            "yt-dlp",
            "--format",
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format",
            "mp4",
            "--embed-thumbnail",
            "--add-metadata",
            "--output",
            f"{out_dir}/%(title)s.%(ext)s",
            url,
        ]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"\n[get] ✓ done — saved to {out_dir}/")
    else:
        print(f"\n[get] ✗ download failed (exit {result.returncode})")
        sys.exit(result.returncode)


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        usage()

    if len(args) < 2:
        print("[get] error: expected a flag and a URL")
        print("      usage: get -mp3 <url>  or  get -mp4 <url>")
        sys.exit(1)

    flag, url = args[0], args[1]

    if flag == "-mp3":
        mode = "mp3"
    elif flag == "-mp4":
        mode = "mp4"
    else:
        print(f"[get] unknown flag: {flag}")
        print("      valid flags: -mp3, -mp4")
        sys.exit(1)

    check_deps()
    download(mode, url)


if __name__ == "__main__":
    main()
