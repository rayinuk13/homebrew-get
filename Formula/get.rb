# typed: false
# frozen_string_literal: true

class Get < Formula
  desc "Download YouTube videos and audio from the terminal"
  homepage "https://github.com/rayinuk13/homebrew-get"
  url "https://github.com/rayinuk13/homebrew-get/archive/73346d88189f928cc459a06b8aed7337b4c8d270.tar.gz"
  version "1.2.0"
  sha256 "d5f4aae7abd759a1d47e7a000931e44320f89c311f922245e8ce1e3eb78304da"

  license "MIT"

  depends_on "aria2"
  depends_on "ffmpeg"
  depends_on "python@3.12"
  depends_on "yt-dlp"

  def install
    # ensure script uses the correct python version
    inreplace "get.py", "#!/usr/bin/env python3",
              "#!#{Formula["python@3.12"].opt_bin}/python3.12"

    # install the script as `get` into Homebrew bin
    bin.install "get.py" => "get"
  end

  test do
    output = shell_output("#{bin}/get --help")
    assert_match "get", output
  end
end
