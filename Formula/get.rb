# typed: false
# frozen_string_literal: true

class Get < Formula
  desc "Download YouTube videos and audio from the terminal"
  homepage "https://github.com/rayinuk13/homebrew-get"
  url "https://github.com/rayinuk13/homebrew-get/archive/14ede8f46c9785567ceb34421028e9bbd86134d6.tar.gz"
  version "1.0.2"
  sha256 "a89bdf99d5a212a88ecbe08fb06244e5da74282e3dab165804777381bef03888"
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
