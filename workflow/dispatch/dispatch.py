#!/usr/bin/env python3
"""
dispatch.py — Workflow dispatch for Codex agents via pi.

Handles all Codex dispatches in the workflow: proposals, research validation,
approach evaluation, and debug proposals. Knows the right model, thinking level,
tools, and output paths for each type.

Usage:
    python3 dispatch.py proposal --cwd /path/to/project
    python3 dispatch.py proposal --cwd /path/to/project --id b
    python3 dispatch.py research-validate --cwd /path/to/project --research-file path/to/research.md
    python3 dispatch.py evaluate-approaches --cwd /path/to/project
    python3 dispatch.py debug-proposal --cwd /path/to/project
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


# --- Dispatch configurations ---

DISPATCH_TYPES = {
    "proposal": {
        "thinking": "high",
        "tools": "read,grep,find,ls",
        "output_template": ".building/planning/proposal-{id}.md",
        "context_files": [
            ".building/problem-definition/definition.md",
            "~/.claude/principles.md",
        ],
        "optional_context": [
            ".building/design/design.md",
            ".building/principles.md",
        ],
        "prompt": """You are generating a proposal for solving a software problem.

Read the provided context files carefully — they contain the problem definition,
design direction (if applicable), and the principles that govern how we build.

Your proposal must cover:
- Approach: the strategy and why it solves the problem
- Steps: concrete, ordered implementation steps specific enough that an
  implementation agent could follow your direction without guessing
- Decisions: choices made and alternatives rejected, with reasoning
- Risks: what could go wrong, what's uncertain
- Unresolved questions: things you couldn't determine
- Interface contracts: if the work spans multiple domains, define the data
  shapes, API signatures, and assumptions at each boundary

Write your full proposal as markdown. Be specific and concrete.""",
    },
    "research-validate": {
        "thinking": "xhigh",
        "tools": "read,grep,find,ls",
        "output_template": ".building/research-validation.md",
        "context_files": [],  # research file passed via --research-file
        "optional_context": [],
        "prompt": """You are validating research output. Read the research file provided.

Evaluate:
1. Does the research actually answer the question that was asked, or did it
   drift to adjacent topics that are easier to find but less relevant?
2. Are there obvious gaps — angles not explored, perspectives missing?
3. Is the depth appropriate — surface-level listing vs genuine analysis with
   tradeoffs, failure modes, and real-world outcomes?
4. Any contradictions or unreliable claims?
5. Is the timeframe current enough for the topic?

Output format:
## Research Validation

### Verdict: [SUFFICIENT / NEEDS FOLLOW-UP]

### Coverage Assessment
[What was well covered, what was thin, what was missing]

### Depth Assessment
[Surface-level vs genuinely analytical — with specific examples]

### Reliability Concerns
[Unsupported, contradictory, or suspiciously confident claims]

### Follow-Up Research Needed
[If NEEDS FOLLOW-UP: specific, targeted queries to fill gaps]""",
    },
    "evaluate-approaches": {
        "thinking": "xhigh",
        "tools": "read,grep,find,ls",
        "output_template": ".building/design/approach-evaluation.md",
        "context_files": [
            ".building/problem-definition/definition.md",
            "~/.claude/principles.md",
        ],
        "optional_context": [
            ".building/principles.md",
        ],
        "prompt": """You are evaluating candidate solution approaches for a defined problem.

Read the problem definition and principles provided. Research or read about
the candidate approaches in the codebase context.

For each candidate approach, analyze:
- What does it optimize for? Speed, simplicity, scalability, correctness?
- Where does it break down — not theoretically, but in practice?
- Who actually uses this in production? What do they say after living with it?
- What does it sacrifice? Every approach trades something. Name both sides.
- How does it interact with the stated principles? Natural alignment or tension?

Do NOT pick a winner. Present the real decision — the core tradeoffs the user
is choosing between. Often approaches are closer than they appear on the surface.

Output format:
## Approach Evaluation

### The Real Decision
[What the user is actually choosing between]

### Approach Analysis
[For each approach: optimizes for, breaks at, who uses it, what it sacrifices]

### Principle Alignment
[How each maps to principles — alignment and tension]

### Recommendation Context
[If you care about X, approach A; if Y, approach B. Let priorities decide.]""",
    },
    "debug-proposal": {
        "thinking": "high",
        "tools": "read,grep,find,ls",
        "output_template": ".building/debugging/proposal-codex.md",
        "context_files": [
            ".building/debugging/root-cause-analysis.md",
            "~/.claude/principles.md",
        ],
        "optional_context": [
            ".building/principles.md",
        ],
        "prompt": """You are proposing a fix for a bug. Read the root cause analysis provided.

Your proposal must cover:
- What to change, where, and why
- Why this approach over alternatives you considered
- Risks of this fix — what could go wrong
- Whether this fix addresses the root cause or just the symptom
- Any tests that should be added to prevent regression

Write a design proposal. Do NOT implement — no code, no diffs. The proposal
is a document describing what to change and why. An implementation agent
will execute it.""",
    },
}


def resolve_path(path, cwd):
    """Resolve ~ and make relative paths absolute against cwd."""
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    return path


def build_context(dispatch_type, cwd, extra_context=None):
    """Build the list of context files, skipping missing optional ones."""
    config = DISPATCH_TYPES[dispatch_type]
    context = []

    for f in config["context_files"]:
        resolved = resolve_path(f, cwd)
        if not os.path.exists(resolved):
            log(f"  Required context missing: {f}", RED)
            sys.exit(1)
        context.append(resolved)

    for f in config["optional_context"]:
        resolved = resolve_path(f, cwd)
        if os.path.exists(resolved):
            context.append(resolved)
            log(f"  Optional context found: {f}", DIM)

    if extra_context:
        for f in extra_context:
            resolved = resolve_path(f, cwd)
            if os.path.exists(resolved):
                context.append(resolved)
            else:
                log(f"  Extra context missing: {f}", YELLOW)

    return context


def run_dispatch(dispatch_type, cwd, proposal_id="a", research_file=None,
                 extra_context=None, custom_output=None):
    config = DISPATCH_TYPES[dispatch_type]

    # Build output path
    if custom_output:
        output = resolve_path(custom_output, cwd)
    else:
        output_template = config["output_template"]
        output = resolve_path(output_template.format(id=proposal_id), cwd)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)

    # Build context
    extra = list(extra_context or [])
    if research_file:
        extra.append(research_file)

    context_files = build_context(dispatch_type, cwd, extra)

    # Build pi command
    cmd = [
        "pi", "-p", "--no-session", "--mode", "json",
        "--provider", "openai-codex",
        "--model", "gpt-5.4",
        "--thinking", config["thinking"],
        "--tools", config["tools"],
    ]

    for f in context_files:
        cmd.append(f"@{f}")

    cmd.append(config["prompt"])

    log(f"Dispatching: {dispatch_type}", BOLD)
    log(f"  Model: openai-codex/gpt-5.4")
    log(f"  Thinking: {config['thinking']}")
    log(f"  Output: {output}")
    log(f"  Context: {len(context_files)} files")
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
        cwd=cwd,
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
                        cmd_str = tool_args["command"][:80]
                        arg_summary = f" $ {cmd_str}"
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
                    "total_tokens": usage.get("totalTokens", 0),
                    "cost": cost.get("total", 0),
                }
                elapsed = time.time() - start_time
                log(f"Done in {elapsed:.1f}s | {turn_count} turns | {tool_count} tools | {agent_usage['total_tokens']} tokens | ${agent_usage['cost']:.4f}", f"{BOLD}{GREEN}")

    except KeyboardInterrupt:
        proc.kill()
        log("Interrupted", RED)
        sys.exit(130)

    proc.wait()
    final_text = "".join(final_text_parts)

    # Write output
    with open(output, "w") as f:
        f.write(final_text)

    log(f"Written to: {output}", DIM)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Workflow dispatch — run Codex agents for workflow stages"
    )
    parser.add_argument(
        "type",
        choices=list(DISPATCH_TYPES.keys()),
        help="Dispatch type"
    )
    parser.add_argument("--cwd", required=True, help="Project working directory")
    parser.add_argument("--id", default="a", help="Proposal ID (a or b) — for dual proposals")
    parser.add_argument("--research-file", help="Research file to validate (for research-validate)")
    parser.add_argument("--context", nargs="+", help="Additional context files")
    parser.add_argument("--output", help="Override output path")

    args = parser.parse_args()

    exit_code = run_dispatch(
        dispatch_type=args.type,
        cwd=args.cwd,
        proposal_id=args.id,
        research_file=args.research_file,
        extra_context=args.context,
        custom_output=args.output,
    )
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
