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
import time
from urllib.parse import parse_qs, urlparse

VERSION = "1.1.0"
DEFAULT_AUDIO_QUALITY = "192"
DEFAULT_VIDEO_QUALITY = "1080"
MAX_VIDEO_HEIGHT = "2160"
VALID_AUDIO_QUALITIES = {"128", "192", "320"}
DEFAULT_ARTIST = "Unknown Artist"
DEFAULT_TITLE = "Unknown Title"
METADATA_YEAR_PATTERN = r"upload_date:(?P<year>\d{4}).*"
PROJECT_REPO_GIT_URL = "https://github.com/rayinuk13/homebrew-get.git"
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"

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
    print("  get search \"query\"")
    print("  get update")
    print("  get <playlist-url> --all")
    print("  get <playlist-url> --range 1-10")
    print("  get <url> --threads 5")
    print()
    print("Examples:")
    print("  get --mp3 https://youtube.com/watch?v=...")
    print("  get --mp4 --quality 1080 https://youtube.com/watch?v=...")
    print("  get --best https://youtube.com/watch?v=...")
    print("  get search \"audiox\"")
    print("  get update")
    print("  get https://youtube.com/playlist?list=... --range 1-10")
    sys.exit(0)


def supports_color():
    return sys.stdout.isatty() and os.environ.get("TERM", "").lower() != "dumb"


def colorize(text, color):
    if not supports_color():
        return text
    return f"{color}{text}{COLOR_RESET}"


def log_success(message):
    print(colorize(f"[get] {message}", COLOR_GREEN))


def log_error(message):
    print(colorize(f"[get] {message}", COLOR_RED))


def log_warning(message):
    print(colorize(f"[get] {message}", COLOR_YELLOW))


def check_deps(require_ffmpeg=True, require_aria2=True):
    missing = []
    deps = ["yt-dlp"]
    if require_ffmpeg:
        deps.append("ffmpeg")
    if require_aria2:
        deps.append("aria2c")
    for dep in deps:
        if not shutil.which(dep):
            missing.append(dep)
    if missing:
        log_error(f"missing dependencies: {', '.join(missing)}")
        log_warning("install the missing tools with your system package manager.")
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

    if parsed.url and len(parsed.url) > 1 and parsed.url[0] in ("'", '"') and parsed.url[0] == parsed.url[-1]:
        parsed.url = parsed.url[1:-1]

    if parsed.help or not parsed.url:
        usage()

    selected_modes = [parsed.mp3, parsed.mp4, parsed.best]
    if sum(1 for mode in selected_modes if mode) > 1:
        log_error("error: choose only one format flag: --mp3, --mp4, or --best")
        sys.exit(1)

    if parsed.mp3:
        mode = "mp3"
    elif parsed.mp4:
        mode = "mp4"
    else:
        mode = "best"

    if parsed.playlist_all and parsed.playlist_range:
        log_error("error: use either --all or --range, not both")
        sys.exit(1)

    if parsed.threads < 1:
        log_error("error: --threads must be at least 1")
        sys.exit(1)

    quality = parsed.quality
    if mode == "mp3":
        if quality is None:
            quality = DEFAULT_AUDIO_QUALITY
        elif quality not in VALID_AUDIO_QUALITIES:
            log_error("error: audio quality must be one of 128, 192, or 320")
            sys.exit(1)
    elif quality is None:
        quality = MAX_VIDEO_HEIGHT if mode == "best" else DEFAULT_VIDEO_QUALITY
    elif quality.lower() == "4k":
        quality = MAX_VIDEO_HEIGHT
    elif not quality.isdigit():
        log_error("error: video quality must be a number between 360 and 2160, or 4k")
        sys.exit(1)
    else:
        quality_int = int(quality)
        if quality_int < 360 or quality_int > int(MAX_VIDEO_HEIGHT):
            log_error("error: video quality out of range; choose 360-2160 or 4k")
            sys.exit(1)

    playlist_items = None
    if parsed.playlist_range:
        if parsed.playlist_range.count("-") != 1:
            log_error("error: --range must be in start-end format, e.g. 1-10")
            sys.exit(1)
        start, end = parsed.playlist_range.split("-", 1)
        if not start.isdigit() or not end.isdigit():
            log_error("error: --range values must be numeric (example: 1-10)")
            sys.exit(1)
        start_num, end_num = int(start), int(end)
        if start_num < 1:
            log_error("error: --range start must be >= 1")
            sys.exit(1)
        if end_num < start_num:
            log_error("error: --range end must be >= start")
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
        "--downloader",
        "aria2c",
        "--downloader-args",
        f"aria2c:-x{config['threads']} -s{config['threads']} -k1M",
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
    if sys.stdout.isatty():
        label_text = colorize("downloading...", COLOR_YELLOW)
        process = subprocess.Popen(cmd)
        frame_idx = 0
        spinner_frame_count = len(SPINNER_FRAMES)
        while process.poll() is None:
            sys.stdout.write(f"\r{SPINNER_FRAMES[frame_idx % spinner_frame_count]} {label_text}")
            sys.stdout.flush()
            frame_idx += 1
            time.sleep(0.1)
        sys.stdout.write("\r" + (" " * (len(label_text) + 4)) + "\r")
        sys.stdout.flush()
        return_code = process.returncode
    else:
        result = subprocess.run(cmd)
        return_code = result.returncode
    if return_code == 0:
        log_success(f"✓ done — saved to {out_dir}/")
    else:
        log_error(f"✗ download failed (exit {return_code})")
        sys.exit(return_code)


def search_youtube(query):
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print",
        "%(title)s\t%(id)s\t%(duration_string)s",
        f"ytsearch10:{query}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_error("search failed")
        if result.stderr.strip():
            log_warning(result.stderr.strip().splitlines()[-1])
        sys.exit(result.returncode)

    rows = [line for line in result.stdout.splitlines() if line.strip()]
    if not rows:
        log_warning("no results found")
        return

    log_success(f"results for \"{query}\":")
    for idx, row in enumerate(rows, start=1):
        parts = row.split("\t")
        if len(parts) < 2:
            continue
        title = parts[0]
        video_id = parts[1]
        duration = parts[2] if len(parts) > 2 else ""
        video_url = (
            video_id
            if video_id.startswith("http://") or video_id.startswith("https://")
            else f"https://www.youtube.com/watch?v={video_id}"
        )
        duration_text = f" [{duration}]" if duration else ""
        print(f"{idx:>2}. {title}{duration_text}")
        print(f"    {video_url}")


def update_app():
    log_warning("updating get via pip...")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", f"git+{PROJECT_REPO_GIT_URL}"]
    result = subprocess.run(cmd)
    if result.returncode == 0:
        log_success("update complete")
        return
    log_error("update failed")
    log_warning("try one of these manually:")
    print('  brew upgrade get')
    print(f'  pip install --upgrade "git+{PROJECT_REPO_GIT_URL}"')
    print("  npm install -g github:rayinuk13/homebrew-get")
    sys.exit(result.returncode)


def main():
    args = sys.argv[1:]
    if args and args[0] == "update":
        update_app()
        return
    if args and args[0] == "search":
        if len(args) < 2:
            log_error('error: search query required. Example: get search "audiox"')
            sys.exit(1)
        check_deps(require_ffmpeg=False, require_aria2=False)
        search_youtube(" ".join(args[1:]))
        return

    config = parse_args(args)
    check_deps()
    download(config)


if __name__ == "__main__":
    main()
