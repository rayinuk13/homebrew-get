# typed: false
# frozen_string_literal: true

class Get < Formula
  desc "Download YouTube videos and audio from the terminal"
  homepage "https://github.com/rayinuk13/homebrew-get"
  url "https://github.com/rayinuk13/homebrew-get/archive/8e0f7aeb1723c8a62baaf7d5b545622a2afe2df5.tar.gz"
  version "1.0.1"
  sha256 "323b7e3f2016e9f05781bd09e1f9fd49202f23dfbfb38ab7d1628777bad211bb"
  license "MIT"

  depends_on "ffmpeg"
  depends_on "python@3.12"
  depends_on "yt-dlp"

  def install
    inreplace "get.py", "#!/usr/bin/env python3",
              "#!#{Formula["python@3.12"].opt_bin}/python3.12"
    bin.install "get.py" => "get"
  end

  test do
    output = shell_output("#{bin}/get --help")
    assert_match "get", output
  end
end
