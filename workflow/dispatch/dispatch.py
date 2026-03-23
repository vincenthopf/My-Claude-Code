#!/usr/bin/env python3
"""
dispatch.py — Send a prompt to Codex via pi. Write the response to a file.

Usage:
    python3 dispatch.py --prompt "Read X and do Y" --output result.md --cwd .
    python3 dispatch.py --prompt "Analyze this" --output result.md --cwd . --thinking xhigh
    python3 dispatch.py --prompt-file prompt.txt --output result.md --cwd .
    python3 dispatch.py --prompt "Pure reasoning" --output result.md --cwd . --no-tools
"""

import argparse
import json
import subprocess
import sys
import os
import time
import threading
from datetime import datetime

DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def log(msg, style=""):
    ts = datetime.now().strftime("%H:%M:%S")
    sys.stderr.write(f"{DIM}{ts}{RESET} {style}{msg}{RESET}\n")
    sys.stderr.flush()


def run(args):
    cwd = os.path.abspath(os.path.expanduser(args.cwd))
    output = args.output if os.path.isabs(args.output) else os.path.join(cwd, args.output)

    # Get prompt
    if args.prompt_file:
        path = os.path.expanduser(args.prompt_file)
        if not os.path.isabs(path):
            path = os.path.join(cwd, path)
        with open(path, "r") as f:
            prompt = f.read()
    else:
        prompt = args.prompt

    # Build command
    cmd = [
        "pi", "-p", "--no-session", "--mode", "json",
        "--provider", args.provider, "--model", args.model,
        "--thinking", args.thinking,
    ]

    if args.no_tools:
        cmd.append("--no-tools")
    else:
        cmd += ["--tools", "read,grep,find,ls"]

    if prompt.startswith("@"):
        prompt = " " + prompt
    cmd.append(prompt)

    log(f"Dispatching to {args.provider}/{args.model} ({args.thinking})", BOLD)
    log(f"  Output: {output}", DIM)

    start_time = time.time()
    current_turn_text = []
    all_turns_text = []
    turn_count = 0
    tool_count = 0

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, text=True, bufsize=1,
    )

    # Drain stderr to prevent deadlock
    stderr_lines = []
    threading.Thread(target=lambda: [stderr_lines.append(l) for l in proc.stderr], daemon=True).start()

    # Heartbeat so caller knows we're alive
    def heartbeat():
        while proc.poll() is None:
            time.sleep(30)
            if proc.poll() is None:
                log(f"  Still running... {time.time() - start_time:.0f}s", DIM)
    threading.Thread(target=heartbeat, daemon=True).start()

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        etype = event.get("type", "")

        if etype == "turn_start":
            if current_turn_text:
                all_turns_text.append("".join(current_turn_text))
            current_turn_text = []
            turn_count += 1

        elif etype == "message_update":
            ae = event.get("assistantMessageEvent", {})
            if ae.get("type") == "toolcall_end":
                tool_count += 1
                tc = ae.get("toolCall", {})
                name = tc.get("name", "?")
                ta = tc.get("arguments", {})
                hint = ta.get("path") or ta.get("file_path") or ta.get("command", "")[:60]
                log(f"  {name} {hint}", YELLOW)
            elif ae.get("type") == "text_delta":
                current_turn_text.append(ae.get("delta", ""))
            elif ae.get("type") == "text_start":
                log(f"  Responding...", GREEN)

    proc.wait()

    if current_turn_text:
        all_turns_text.append("".join(current_turn_text))

    final_text = all_turns_text[-1] if all_turns_text else ""
    elapsed = time.time() - start_time

    if proc.returncode != 0:
        log(f"Failed (exit {proc.returncode}) after {elapsed:.1f}s", RED)
        for l in stderr_lines[-5:]:
            log(f"  {l.rstrip()}", RED)
        sys.exit(proc.returncode)

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    tmp = output + ".tmp"
    with open(tmp, "w") as f:
        f.write(final_text)
    os.replace(tmp, output)

    log(f"Done in {elapsed:.1f}s | {turn_count} turns | {tool_count} tools", f"{BOLD}{GREEN}")


def main():
    p = argparse.ArgumentParser(description="Send a prompt to Codex via pi")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt", "-m")
    g.add_argument("--prompt-file", "-f")
    p.add_argument("--output", "-o", required=True)
    p.add_argument("--cwd", required=True)
    p.add_argument("--thinking", "-t", default="high",
                   choices=["off", "minimal", "low", "medium", "high", "xhigh"])
    p.add_argument("--no-tools", action="store_true")
    p.add_argument("--provider", default="openai-codex")
    p.add_argument("--model", default="gpt-5.4")
    args = p.parse_args()
    run(args)


if __name__ == "__main__":
    main()
