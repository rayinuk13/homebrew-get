# homebrew-get

Homebrew tap for [get](https://github.com/rayinuk13/get) — download YouTube videos and audio from the terminal.

## Install

### Homebrew

```bash
brew tap rayinuk13/get
brew install get
```

### pip

```bash
pip install "git+https://github.com/rayinuk13/homebrew-get.git"
```

### npm

```bash
npm install -g github:rayinuk13/homebrew-get
```

## Usage

```bash
get --mp3 <youtube-url>                      # Audio only (MP3)
get --mp4 --quality 1080 <youtube-url>       # Video MP4 with target quality
get --best <youtube-url>                     # Auto highest quality with fallback
get <playlist-url> --all                     # Download full playlist
get <playlist-url> --range 1-10              # Download playlist range
get --mp3 --quality 320 --threads 5 <url>    # High-quality audio with faster fragments
```

## Troubleshooting `brew`

If Homebrew install/uninstall checks fail in CI, run the same lifecycle locally:

```bash
brew tap rayinuk13/get
brew install get
brew test get
brew uninstall get
brew untap rayinuk13/get
```

In this coding sandbox, `brew` is not available on `PATH`, so Homebrew validation must run in CI on a macOS runner.
