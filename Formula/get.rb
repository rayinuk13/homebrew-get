# typed: false
# frozen_string_literal: true

class Get < Formula
  desc "Download YouTube videos and audio from the terminal"
  homepage "https://github.com/rayinuk13/get"
  url "https://github.com/rayinuk13/get/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "4e61d2676799e012ed238ec14ef1d221c6aba0b28456e2563c892b299dd99b67"
  license "MIT"
  version "1.0.0"

  depends_on "python@3.12"
  depends_on "ffmpeg"
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
