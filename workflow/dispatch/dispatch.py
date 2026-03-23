#!/usr/bin/env python3
"""
dispatch.py — Send prompts to Codex via pi.

Claude writes the prompt. This script sends it to Codex and writes the response
to a file. Codex has read tools and can access the codebase — reference files
by path in the prompt instead of passing them as context.

Usage:
    python3 dispatch.py --prompt "Your prompt here" --output result.md --cwd /path/to/project
    python3 dispatch.py --prompt "Deep analysis" --output result.md --cwd . --thinking xhigh
    python3 dispatch.py --prompt-file prompt.txt --output result.md --cwd . --thinking high
    python3 dispatch.py --prompt "Quick check" --output result.md --cwd . --no-tools
    python3 dispatch.py --prompt "Read ~/.claude/principles.md and evaluate..." --output result.md --cwd .
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

HEARTBEAT_INTERVAL = 30  # seconds between heartbeat messages


def log(msg, style=""):
    ts = datetime.now().strftime("%H:%M:%S")
    sys.stderr.write(f"{DIM}{ts}{RESET} {style}{msg}{RESET}\n")
    sys.stderr.flush()


def drain_stderr(proc, stderr_lines):
    """Read stderr in a background thread to prevent deadlock."""
    for line in proc.stderr:
        stderr_lines.append(line)


def heartbeat(start_time, alive_flag):
    """Print periodic heartbeat to stderr so caller knows we're alive."""
    while alive_flag.is_set():
        elapsed = time.time() - start_time
        if elapsed > HEARTBEAT_INTERVAL:
            log(f"  Still running... {elapsed:.0f}s elapsed", DIM)
        alive_flag.wait(HEARTBEAT_INTERVAL)


def run(args):
    # Validate cwd
    cwd = os.path.abspath(os.path.expanduser(args.cwd))
    if not os.path.isdir(cwd):
        log(f"Working directory does not exist: {cwd}", RED)
        sys.exit(1)

    # Resolve output relative to cwd
    output = args.output
    if not os.path.isabs(output):
        output = os.path.join(cwd, output)
    output = os.path.abspath(output)

    # Get prompt from --prompt or --prompt-file
    if args.prompt_file:
        prompt_path = os.path.expanduser(args.prompt_file)
        if not os.path.isabs(prompt_path):
            prompt_path = os.path.join(cwd, prompt_path)
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:
        prompt = args.prompt

    if not prompt:
        log("No prompt provided", RED)
        sys.exit(1)

    # Build pi command
    cmd = [
        "pi", "-p", "--no-session", "--mode", "json",
        "--provider", args.provider,
        "--model", args.model,
        "--thinking", args.thinking,
    ]

    if args.no_tools:
        cmd.append("--no-tools")
    elif args.tools:
        cmd += ["--tools", args.tools]
    else:
        cmd += ["--tools", "read,grep,find,ls"]

    if args.system_prompt:
        cmd += ["--system-prompt", args.system_prompt]

    # Context files — passed to pi as @file references for small, critical files
    # For large context, prefer mentioning file paths in the prompt and letting
    # Codex read them with its tools instead
    if args.context:
        for f in args.context:
            resolved = os.path.expanduser(f)
            if not os.path.isabs(resolved):
                resolved = os.path.join(cwd, resolved)
            if os.path.exists(resolved):
                cmd.append(f"@{resolved}")
                log(f"  Context: {f}", DIM)
            elif args.allow_missing_context:
                log(f"  Context missing (skipped): {f}", YELLOW)
            else:
                log(f"  Required context missing: {f}", RED)
                log(f"  Use --allow-missing-context to skip missing files", DIM)
                sys.exit(1)

    # Prevent prompt starting with @ from being interpreted as file include
    if prompt.startswith("@"):
        prompt = " " + prompt

    cmd.append(prompt)

    log(f"Dispatching to Codex", BOLD)
    log(f"  Model: {args.provider}/{args.model}")
    log(f"  Thinking: {args.thinking}")
    log(f"  Output: {output}")
    log("")

    start_time = time.time()
    current_turn_text = []
    all_turns_text = []
    turn_count = 0
    tool_count = 0
    last_activity = time.time()
    agent_usage = {}

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True,
        bufsize=1,
        encoding="utf-8",
    )

    # Drain stderr in background thread to prevent deadlock
    stderr_lines = []
    stderr_thread = threading.Thread(target=drain_stderr, args=(proc, stderr_lines))
    stderr_thread.daemon = True
    stderr_thread.start()

    # Heartbeat thread so caller knows we're alive
    alive_flag = threading.Event()
    alive_flag.set()
    heartbeat_thread = threading.Thread(target=heartbeat, args=(start_time, alive_flag))
    heartbeat_thread.daemon = True
    heartbeat_thread.start()

    try:
        for line in proc.stdout:
            last_activity = time.time()
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
                ae_type = ae.get("type", "")

                if ae_type == "toolcall_end":
                    tc = ae.get("toolCall", {})
                    name = tc.get("name", "?")
                    tool_args = tc.get("arguments", {})
                    tool_count += 1
                    arg_summary = ""
                    if "path" in tool_args or "file_path" in tool_args:
                        arg_summary = f" {tool_args.get('path') or tool_args.get('file_path')}"
                    elif "command" in tool_args:
                        arg_summary = f" $ {tool_args['command'][:80]}"
                    log(f"  Tool: {name}{arg_summary}", YELLOW)

                elif ae_type == "text_delta":
                    current_turn_text.append(ae.get("delta", ""))

                elif ae_type == "text_start":
                    log(f"  Responding...", GREEN)

            elif etype == "message_end":
                msg = event.get("message", {})
                usage = msg.get("usage", {})
                if usage:
                    cost = usage.get("cost", {})
                    agent_usage = {
                        "tokens": usage.get("totalTokens", 0),
                        "cost": cost.get("total", 0) if isinstance(cost, dict) else 0,
                    }

            elif etype == "agent_end":
                messages = event.get("messages", [])
                if messages and not agent_usage:
                    last_msg = messages[-1] if isinstance(messages, list) else {}
                    usage = last_msg.get("usage", {})
                    cost = usage.get("cost", {})
                    agent_usage = {
                        "tokens": usage.get("totalTokens", 0),
                        "cost": cost.get("total", 0) if isinstance(cost, dict) else 0,
                    }

                elapsed = time.time() - start_time
                tokens = agent_usage.get("tokens", 0)
                cost_val = agent_usage.get("cost", 0)
                log(f"Done in {elapsed:.1f}s | {turn_count} turns | {tool_count} tools | {tokens} tokens | ${cost_val:.4f}", f"{BOLD}{GREEN}")

    except KeyboardInterrupt:
        proc.kill()
        log("Interrupted", RED)
        sys.exit(130)
    finally:
        alive_flag.clear()

    proc.wait()
    stderr_thread.join(timeout=5)

    # Capture the last turn's text
    if current_turn_text:
        all_turns_text.append("".join(current_turn_text))

    # Use only the last turn's text as the final answer
    final_text = all_turns_text[-1] if all_turns_text else ""

    # Check for failure
    if proc.returncode != 0:
        log(f"Pi exited with code {proc.returncode}", RED)
        if stderr_lines:
            log(f"stderr tail:", RED)
            for line in stderr_lines[-10:]:
                log(f"  {line.rstrip()}", RED)
        sys.exit(proc.returncode)

    if not final_text.strip():
        log(f"Warning: empty response from Codex", YELLOW)
        if stderr_lines:
            log(f"stderr tail:", YELLOW)
            for line in stderr_lines[-5:]:
                log(f"  {line.rstrip()}", YELLOW)

    # Write output atomically
    os.makedirs(os.path.dirname(output), exist_ok=True)
    tmp_output = output + ".tmp"
    with open(tmp_output, "w", encoding="utf-8") as f:
        f.write(final_text)
    os.replace(tmp_output, output)

    log(f"Written to: {output}", DIM)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Send a prompt to Codex via pi")
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", "-m", help="The prompt to send")
    prompt_group.add_argument("--prompt-file", "-f", help="File containing the prompt")

    parser.add_argument("--output", "-o", required=True, help="Output file for response")
    parser.add_argument("--cwd", required=True, help="Working directory")
    parser.add_argument("--thinking", "-t", default="high",
                        choices=["off", "minimal", "low", "medium", "high", "xhigh"],
                        help="Reasoning depth (default: high)")

    tools_group = parser.add_mutually_exclusive_group()
    tools_group.add_argument("--tools", help="Override tools (default: read,grep,find,ls)")
    tools_group.add_argument("--no-tools", action="store_true", help="Disable all tools")

    parser.add_argument("--context", "-c", nargs="+",
                        help="Small context files to inline. For large files, mention paths "
                             "in the prompt and let Codex read them with its tools instead.")
    parser.add_argument("--allow-missing-context", action="store_true",
                        help="Skip missing context files instead of failing")
    parser.add_argument("--system-prompt", "-s", help="Custom system prompt")
    parser.add_argument("--provider", default="openai-codex", help="Provider (default: openai-codex)")
    parser.add_argument("--model", default="gpt-5.4", help="Model (default: gpt-5.4)")

    args = parser.parse_args()
    exit_code = run(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
