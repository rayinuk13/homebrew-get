# typed: false
# frozen_string_literal: true

class Get < Formula
  desc "Download YouTube videos and audio from the terminal"
  homepage "https://github.com/rayinuk13/get"
  url "https://github.com/rayinuk13/get/archive/9659ead56e4b18818f86b87720efff1a5ddb9a81.tar.gz"
  version "1.0.0"
  sha256 "1e8d89abfc12eaf047da291b6188af0cea2138f8616a66a4693ab55bddf005ac"
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
