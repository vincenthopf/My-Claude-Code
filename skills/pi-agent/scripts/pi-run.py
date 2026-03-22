#!/usr/bin/env python3
"""
pi-run.py — Wrapper for pi coding agent that streams clean progress to stderr
and writes the final result to an output file.

Usage:
    python3 pi-run.py --prompt "Fix the bug" --output /tmp/result.md [--provider github-copilot] [--model claude-sonnet-4] [--tools read,bash,edit,write] [--cwd /path/to/project] [--thinking high] [--context file1.ts file2.ts]
"""

import argparse
import json
import subprocess
import sys
import os
import time
from datetime import datetime


# ANSI colors for stderr progress
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def log(msg, style=""):
    """Print a progress line to stderr."""
    ts = datetime.now().strftime("%H:%M:%S")
    sys.stderr.write(f"{DIM}{ts}{RESET} {style}{msg}{RESET}\n")
    sys.stderr.flush()


def run_pi(args):
    cmd = ["pi", "-p", "--no-session", "--mode", "json"]

    if args.provider:
        cmd += ["--provider", args.provider]
    if args.model:
        cmd += ["--model", args.model]
    if args.tools:
        cmd += ["--tools", args.tools]
    if args.thinking:
        cmd += ["--thinking", args.thinking]
    if args.system_prompt:
        cmd += ["--system-prompt", args.system_prompt]
    if args.no_tools:
        cmd += ["--no-tools"]

    # Add context files with @ prefix
    if args.context:
        for f in args.context:
            cmd.append(f"@{f}")

    # Add the prompt
    cmd.append(args.prompt)

    log(f"Starting pi agent", BOLD)
    log(f"  Provider: {args.provider or 'default'}")
    log(f"  Model: {args.model or 'default'}")
    log(f"  Prompt: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}")
    log("")

    start_time = time.time()
    final_text_parts = []
    current_tool = None
    turn_count = 0
    tool_count = 0
    thinking_chars = 0
    tool_calls = []        # [(name, args_summary, is_error)]
    files_modified = set()  # files touched by write/edit tools
    errors = []            # tool errors or other failures
    agent_usage = {}       # token/cost info from agent_end

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=args.cwd or None,
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

            if etype == "session":
                session_id = event.get("id", "?")[:8]
                log(f"Session: {session_id}", DIM)

            elif etype == "turn_start":
                turn_count += 1
                if turn_count > 1:
                    log(f"Turn {turn_count}", f"{DIM}{CYAN}")

            elif etype == "message_update":
                ae = event.get("assistantMessageEvent", {})
                ae_type = ae.get("type", "")

                if ae_type == "thinking_delta":
                    delta = ae.get("delta", "")
                    thinking_chars += len(delta)

                elif ae_type == "thinking_end":
                    if thinking_chars > 0:
                        log(f"  Thinking: {thinking_chars} chars", DIM)
                        thinking_chars = 0

                elif ae_type == "toolcall_start":
                    # Tool name comes in toolcall_end, but we can show activity
                    current_tool = "..."

                elif ae_type == "toolcall_end":
                    tc = ae.get("toolCall", {})
                    name = tc.get("name", "?")
                    tool_args = tc.get("arguments", {})
                    tool_count += 1

                    # Format tool args concisely
                    arg_summary = ""
                    if "command" in tool_args:
                        cmd_str = tool_args["command"]
                        if len(cmd_str) > 80:
                            cmd_str = cmd_str[:77] + "..."
                        arg_summary = f" $ {cmd_str}"
                    elif "path" in tool_args:
                        arg_summary = f" {tool_args['path']}"
                    elif "file_path" in tool_args:
                        arg_summary = f" {tool_args['file_path']}"

                    log(f"  Tool: {name}{arg_summary}", YELLOW)
                    tool_calls.append({"name": name, "summary": arg_summary.strip()})

                    # Track file modifications
                    if name in ("write", "edit"):
                        fp = tool_args.get("file_path") or tool_args.get("path") or ""
                        if fp:
                            files_modified.add(fp)

                    current_tool = None

                elif ae_type == "text_delta":
                    delta = ae.get("delta", "")
                    final_text_parts.append(delta)

                elif ae_type == "text_start":
                    log(f"  Responding...", GREEN)

            elif etype == "message_start":
                msg = event.get("message", {})
                role = msg.get("role", "")
                if role == "toolResult":
                    tool_name = msg.get("toolName", "")
                    content = msg.get("content", [])
                    result_len = 0
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and "text" in c:
                                result_len += len(c["text"])
                    elif isinstance(content, str):
                        result_len = len(content)
                    is_error = msg.get("isError", False)
                    status = f"{RED}error" if is_error else f"{DIM}ok"
                    log(f"    Result: {status} ({result_len} chars){RESET}", DIM)

                    if is_error:
                        # Extract error text
                        err_text = ""
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and "text" in c:
                                    err_text += c["text"]
                        elif isinstance(content, str):
                            err_text = content
                        errors.append(f"{tool_name}: {err_text[:200]}")

            elif etype == "agent_end":
                msg = event.get("message", {})
                usage = msg.get("usage", {})
                cost = usage.get("cost", {})
                total_cost = cost.get("total", 0)
                total_tokens = usage.get("totalTokens", 0)
                agent_usage = {
                    "total_tokens": total_tokens,
                    "input_tokens": usage.get("input", 0),
                    "output_tokens": usage.get("output", 0),
                    "cost": total_cost,
                    "model": msg.get("model", args.model or "unknown"),
                    "provider": msg.get("provider", args.provider or "unknown"),
                }

                elapsed = time.time() - start_time
                log("")
                log(f"Done in {elapsed:.1f}s | {turn_count} turns | {tool_count} tools | {total_tokens} tokens | ${total_cost:.4f}", f"{BOLD}{GREEN}")

    except KeyboardInterrupt:
        proc.kill()
        log("Interrupted", RED)
        sys.exit(130)

    proc.wait()
    exit_code = proc.returncode
    elapsed = time.time() - start_time
    final_text = "".join(final_text_parts)

    # Build structured output
    success = exit_code == 0 and len(errors) == 0
    status = "success" if success else "failed"

    sections = []

    # Header — the quick-glance summary
    sections.append(f"# Pi Agent Result\n")
    sections.append(f"**Status:** {status}  ")
    sections.append(f"**Duration:** {elapsed:.1f}s | **Turns:** {turn_count} | **Tools:** {tool_count}  ")
    if agent_usage:
        sections.append(f"**Model:** {agent_usage.get('provider', '?')}/{agent_usage.get('model', '?')}  ")
        sections.append(f"**Tokens:** {agent_usage.get('total_tokens', '?')} | **Cost:** ${agent_usage.get('cost', 0):.4f}  ")
    sections.append("")

    # Errors (if any) — surface these prominently
    if errors:
        sections.append("## Errors\n")
        for err in errors:
            sections.append(f"- {err}")
        sections.append("")

    # Files modified — critical for the main agent to know what changed
    if files_modified:
        sections.append("## Files Modified\n")
        for fp in sorted(files_modified):
            sections.append(f"- `{fp}`")
        sections.append("")

    # Tool activity log — concise record of what pi did
    if tool_calls:
        sections.append("## Tool Calls\n")
        for tc in tool_calls:
            summary = f" — {tc['summary']}" if tc["summary"] else ""
            sections.append(f"- **{tc['name']}**{summary}")
        sections.append("")

    # The actual response
    sections.append("## Response\n")
    sections.append(final_text)

    structured_output = "\n".join(sections)

    # Write output
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w") as f:
            f.write(structured_output)
        log(f"Output written to: {args.output}", DIM)
    else:
        print(structured_output)

    return exit_code


def main():
    parser = argparse.ArgumentParser(description="Run pi coding agent with clean progress output")
    parser.add_argument("--prompt", "-m", required=True, help="The task/prompt for pi")
    parser.add_argument("--output", "-o", help="Output file for the final result (default: stdout)")
    parser.add_argument("--provider", "-P", help="LLM provider (e.g., github-copilot, anthropic, openai)")
    parser.add_argument("--model", "-M", help="Model ID (e.g., claude-sonnet-4, gpt-5)")
    parser.add_argument("--tools", "-t", help="Comma-separated tools (default: read,bash,edit,write)")
    parser.add_argument("--no-tools", action="store_true", help="Disable all tools")
    parser.add_argument("--thinking", help="Thinking level: off, minimal, low, medium, high, xhigh")
    parser.add_argument("--cwd", help="Working directory for pi")
    parser.add_argument("--system-prompt", "-s", help="Custom system prompt")
    parser.add_argument("--context", "-c", nargs="+", help="Context files to include (passed as @file)")
    args = parser.parse_args()

    exit_code = run_pi(args)
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
