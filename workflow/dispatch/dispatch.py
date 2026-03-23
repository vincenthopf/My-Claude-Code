#!/usr/bin/env python3
"""
dispatch.py — Send prompts to Codex via pi.

Claude writes the prompt. This script sends it to Codex and writes the response
to a file. That's it.

Usage:
    python3 dispatch.py --prompt "Your prompt here" --output result.md --cwd /path/to/project
    python3 dispatch.py --prompt "Deep analysis" --output result.md --cwd . --thinking xhigh
    python3 dispatch.py --prompt "Quick check" --output result.md --cwd . --context file1.md file2.md
"""

import argparse
import json
import subprocess
import sys
import os
import time
from datetime import datetime

DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def log(msg, style=""):
    ts = datetime.now().strftime("%H:%M:%S")
    sys.stderr.write(f"{DIM}{ts}{RESET} {style}{msg}{RESET}\n")
    sys.stderr.flush()


def run(args):
    cmd = [
        "pi", "-p", "--no-session", "--mode", "json",
        "--provider", "openai-codex",
        "--model", "gpt-5.4",
        "--thinking", args.thinking,
    ]

    if args.tools:
        cmd += ["--tools", args.tools]
    else:
        cmd += ["--tools", "read,grep,find,ls"]

    if args.system_prompt:
        cmd += ["--system-prompt", args.system_prompt]

    # Add context files
    if args.context:
        for f in args.context:
            resolved = os.path.expanduser(f)
            if not os.path.isabs(resolved):
                resolved = os.path.join(args.cwd, resolved)
            if os.path.exists(resolved):
                cmd.append(f"@{resolved}")
                log(f"  Context: {f}", DIM)
            else:
                log(f"  Context missing: {f}", YELLOW)

    # Add the prompt
    cmd.append(args.prompt)

    log(f"Dispatching to Codex", BOLD)
    log(f"  Thinking: {args.thinking}")
    log(f"  Output: {args.output}")
    log("")

    start_time = time.time()
    final_text_parts = []
    turn_count = 0
    tool_count = 0
    agent_usage = {}

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=args.cwd,
        text=True,
        bufsize=1,
    )

    try:
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
                turn_count += 1

            elif etype == "message_update":
                ae = event.get("assistantMessageEvent", {})
                ae_type = ae.get("type", "")

                if ae_type == "toolcall_end":
                    tc = ae.get("toolCall", {})
                    name = tc.get("name", "?")
                    tool_args = tc.get("arguments", {})
                    tool_count += 1
                    arg_summary = ""
                    if "command" in tool_args:
                        arg_summary = f" $ {tool_args['command'][:80]}"
                    elif "path" in tool_args or "file_path" in tool_args:
                        arg_summary = f" {tool_args.get('path') or tool_args.get('file_path')}"
                    log(f"  Tool: {name}{arg_summary}", YELLOW)

                elif ae_type == "text_delta":
                    final_text_parts.append(ae.get("delta", ""))

                elif ae_type == "text_start":
                    log(f"  Responding...", GREEN)

            elif etype == "agent_end":
                msg = event.get("message", {})
                usage = msg.get("usage", {})
                cost = usage.get("cost", {})
                agent_usage = {
                    "tokens": usage.get("totalTokens", 0),
                    "cost": cost.get("total", 0),
                }
                elapsed = time.time() - start_time
                log(f"Done in {elapsed:.1f}s | {turn_count} turns | {tool_count} tools | {agent_usage['tokens']} tokens | ${agent_usage['cost']:.4f}", f"{BOLD}{GREEN}")

    except KeyboardInterrupt:
        proc.kill()
        log("Interrupted", RED)
        sys.exit(130)

    proc.wait()
    final_text = "".join(final_text_parts)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(final_text)

    log(f"Written to: {args.output}", DIM)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Send a prompt to Codex via pi")
    parser.add_argument("--prompt", "-m", required=True, help="The prompt to send")
    parser.add_argument("--output", "-o", required=True, help="Output file for response")
    parser.add_argument("--cwd", required=True, help="Working directory")
    parser.add_argument("--thinking", "-t", default="high",
                        choices=["medium", "high", "xhigh"],
                        help="Reasoning depth (default: high)")
    parser.add_argument("--context", "-c", nargs="+", help="Context files to include")
    parser.add_argument("--tools", help="Override tools (default: read,grep,find,ls)")
    parser.add_argument("--system-prompt", "-s", help="Custom system prompt")
    args = parser.parse_args()

    exit_code = run(args)
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
