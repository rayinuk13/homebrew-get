#!/usr/bin/env python3
"""
get - Download YouTube videos or audio from the command line.

Usage:
  get --mp3 <url>                     Download audio as MP3
  get --mp4 <url> --quality 1080      Download video as MP4 in 1080p
  get --best <url>                    Download highest quality with fallback
  get <playlist-url> --all            Download full playlist
  get <playlist-url> --range 1-10     Download playlist item range
"""

import argparse
import os
import shutil
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

VERSION = "1.0.2"
DEFAULT_AUDIO_QUALITY = "192"
DEFAULT_VIDEO_QUALITY = "1080"
MAX_VIDEO_HEIGHT = "2160"
VALID_AUDIO_QUALITIES = {"128", "192", "320"}
DEFAULT_ARTIST = "Unknown Artist"
DEFAULT_TITLE = "Unknown Title"
METADATA_YEAR_PATTERN = r"upload_date:(?P<year>\d{4}).*"

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
    print("  get --mp3 <url> [--quality 128|192|320]")
    print("  get --mp4 <url> [--quality 360-2160|4k]")
    print("  get --best <url>")
    print("  get <playlist-url> --all")
    print("  get <playlist-url> --range 1-10")
    print("  get <url> --threads 5")
    print()
    print("Examples:")
    print("  get --mp3 https://youtube.com/watch?v=...")
    print("  get --mp4 --quality 1080 https://youtube.com/watch?v=...")
    print("  get --best https://youtube.com/watch?v=...")
    print("  get https://youtube.com/playlist?list=... --range 1-10")
    sys.exit(0)


def check_deps():
    missing = []
    for dep in ("yt-dlp", "ffmpeg"):
        if not shutil.which(dep):
            missing.append(dep)
    if missing:
        print(f"[get] missing dependencies: {', '.join(missing)}")
        print("      install the missing tools with your system package manager.")
        sys.exit(1)


def parse_args(args):
    parser = argparse.ArgumentParser(add_help=False, prog="get")
    parser.add_argument("url", nargs="?")
    parser.add_argument("--quality")
    parser.add_argument("--all", action="store_true", dest="playlist_all")
    parser.add_argument("--range", dest="playlist_range")
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--best", action="store_true")
    parser.add_argument("--mp3", "-mp3", action="store_true")
    parser.add_argument("--mp4", "-mp4", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    parsed = parser.parse_args(args)

    if parsed.help or not parsed.url:
        usage()

    selected_modes = [parsed.mp3, parsed.mp4, parsed.best]
    if sum(1 for mode in selected_modes if mode) > 1:
        print("[get] error: choose only one format flag: --mp3, --mp4, or --best")
        sys.exit(1)

    if parsed.mp3:
        mode = "mp3"
    elif parsed.mp4:
        mode = "mp4"
    else:
        mode = "best"

    if parsed.playlist_all and parsed.playlist_range:
        print("[get] error: use either --all or --range, not both")
        sys.exit(1)

    if parsed.threads < 1:
        print("[get] error: --threads must be at least 1")
        sys.exit(1)

    quality = parsed.quality
    if mode == "mp3":
        if quality is None:
            quality = DEFAULT_AUDIO_QUALITY
        elif quality not in VALID_AUDIO_QUALITIES:
            print("[get] error: audio quality must be one of 128, 192, or 320")
            sys.exit(1)
    elif quality is None:
        quality = MAX_VIDEO_HEIGHT if mode == "best" else DEFAULT_VIDEO_QUALITY
    elif quality.lower() == "4k":
        quality = MAX_VIDEO_HEIGHT
    elif not quality.isdigit():
        print("[get] error: video quality must be a number between 360 and 2160, or 4k")
        sys.exit(1)
    else:
        quality_int = int(quality)
        if quality_int < 360 or quality_int > int(MAX_VIDEO_HEIGHT):
            print("[get] error: video quality out of range; choose 360-2160 or 4k")
            sys.exit(1)

    playlist_items = None
    if parsed.playlist_range:
        if parsed.playlist_range.count("-") != 1:
            print("[get] error: --range must be in start-end format, e.g. 1-10")
            sys.exit(1)
        start, end = parsed.playlist_range.split("-", 1)
        if not start.isdigit() or not end.isdigit():
            print("[get] error: --range values must be numeric (example: 1-10)")
            sys.exit(1)
        start_num, end_num = int(start), int(end)
        if start_num < 1:
            print("[get] error: --range start must be >= 1")
            sys.exit(1)
        if end_num < start_num:
            print("[get] error: --range end must be >= start")
            sys.exit(1)
        playlist_items = f"{start_num}-{end_num}"

    return {
        "mode": mode,
        "url": parsed.url,
        "quality": quality,
        "threads": parsed.threads,
        "playlist_all": parsed.playlist_all,
        "playlist_items": playlist_items,
    }


def build_command(config, out_dir):
    out_template = f"{out_dir}/%(uploader|{DEFAULT_ARTIST})s - %(title|{DEFAULT_TITLE})s.%(ext)s"
    common = [
        "yt-dlp",
        "--windows-filenames",
        "--add-metadata",
        "--progress",
        "--concurrent-fragments",
        str(config["threads"]),
    ]

    normalized_url = config["url"] if "://" in config["url"] else f"https://{config['url']}"
    parsed_url = urlparse(normalized_url)
    query = parse_qs(parsed_url.query)
    hostname = (parsed_url.hostname or "").lower()
    is_youtube_domain = (
        hostname in {"youtube.com", "youtu.be", "youtube-nocookie.com"}
        or hostname.endswith(".youtube.com")
        or hostname.endswith(".youtube-nocookie.com")
    )
    is_playlist_url = is_youtube_domain and (
        "list" in query or parsed_url.path.rstrip("/").endswith("/playlist")
    )
    if config["playlist_all"] or config["playlist_items"] or is_playlist_url:
        common.append("--yes-playlist")
        if config["playlist_items"]:
            common.extend(["--playlist-items", config["playlist_items"]])

    mode = config["mode"]
    if mode == "mp3":
        return common + [
            "--extract-audio",
            "--audio-format",
            "mp3",
            "--audio-quality",
            f"{config['quality']}K",
            "--embed-thumbnail",
            "--parse-metadata",
            "playlist_title:%(album)s",
            "--parse-metadata",
            METADATA_YEAR_PATTERN,
            "--output",
            out_template,
            normalized_url,
        ]

    height = MAX_VIDEO_HEIGHT if mode == "best" else config["quality"]
    format_chain = (
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"best[height<={height}][ext=mp4]/"
        f"best[height<={height}]/best"
    )
    return common + [
        "--format",
        format_chain,
        "--merge-output-format",
        "mp4",
        "--embed-thumbnail",
        "--output",
        out_template,
        normalized_url,
    ]


def download(config):
    out_dir = os.path.expanduser("~/Downloads")
    os.makedirs(out_dir, exist_ok=True)

    mode = config["mode"]
    label = "audio (MP3)" if mode == "mp3" else "video (MP4)"
    if mode == "best":
        label = "best available format"
    print(f"[get] downloading {label}")
    print(f"[get] url: {config['url']}")
    print(f"[get] destination: {out_dir}/")
    print(f"[get] quality: {config['quality']}")
    print(f"[get] threads: {config['threads']}")
    print()

    cmd = build_command(config, out_dir)
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"\n[get] ✓ done — saved to {out_dir}/")
    else:
        print(f"\n[get] ✗ download failed (exit {result.returncode})")
        sys.exit(result.returncode)


def main():
    config = parse_args(sys.argv[1:])
    check_deps()
    download(config)


if __name__ == "__main__":
    main()
