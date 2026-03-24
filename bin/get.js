#!/usr/bin/env node

const { spawn } = require("node:child_process");
const path = require("node:path");

const script = path.resolve(__dirname, "..", "get.py");
const child = spawn("python3", [script, ...process.argv.slice(2)], {
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

child.on("error", (err) => {
  console.error("[get] failed to start python3:", err.message);
  process.exit(1);
});
