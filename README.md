# homebrew-get

Homebrew tap for [get](https://github.com/rayinuk13/get) — download YouTube videos and audio from the terminal.

## Install

```bash
brew tap rayinuk13/get
brew install get
```

## Usage

```bash
get -mp3 <youtube-url>   # Download as MP3
get -mp4 <youtube-url>   # Download as MP4
```

## Allow Copilot to test `brew`

The coding sandbox must have Homebrew installed and available on `PATH`. In my previous run, `brew` was not installed, so install/uninstall/tap checks could not run.

If you want these checks in CI, run them on a macOS runner (or any runner with Homebrew preinstalled), for example:

```bash
brew tap rayinuk13/get
brew install get
brew test get
brew uninstall get
brew untap rayinuk13/get
```
