# typed: false
# frozen_string_literal: true

class Get < Formula
  desc "Download YouTube videos and audio from the terminal"
  homepage "https://github.com/rayinuk13/homebrew-get"
  url "https://github.com/rayinuk13/homebrew-get/archive/905bee4125b047a69f0623d4191109d3c530b9fb.tar.gz"
  version "1.1.0"
  sha256 "7075fbef55f692c6358230c0f1ff15ba56287c177299e900c360c8d64c8700cf"
  license "MIT"

  depends_on "aria2"
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
