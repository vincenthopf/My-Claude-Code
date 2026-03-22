---
name: pi-agent
description: Dispatch tasks to the pi coding agent as a background sub-agent. Use when you want to run a coding task in parallel using a different model/provider (e.g., GPT-5, Gemini, Codex) via the pi CLI. Supports any task pi can handle — code generation, refactoring, analysis, file operations. Progress streams to stderr, final result written to a file. Trigger on requests like "use pi to...", "run this on pi", "dispatch to pi", or when parallel model diversity would help.
---

# Pi Agent — Background Sub-Agent Dispatch

Run the [pi coding agent](https://github.com/badlogic/pi-mono) as a background sub-agent from Claude Code. Pi is a provider-agnostic coding agent that supports 15+ LLM providers and hundreds of models.

## Prerequisites

- `pi` CLI installed: `npm install -g @mariozechner/pi-coding-agent`
- At least one provider configured (pi uses `github-copilot` by default on this machine)

## Defaults

**Always use `openai-codex` provider with `gpt-5.4` model unless the user specifies otherwise.** This is pi's configured default and the reason we dispatch to pi — to get a different model family working on the task.

## How It Works

The wrapper script (`pi-run.py`) launches pi in JSON streaming mode, parses events in real-time, and outputs clean progress lines to stderr while collecting the final response into an output file. This means:

- **Progress is visible** via Claude Code's background task output (tool calls, thinking, turns)
- **Verbose JSON is hidden** — you see human-readable summaries, not raw events
- **Final result lands in a file** that can be read without polluting context

## Usage

```bash
python3 <skill-dir>/scripts/pi-run.py \
  --prompt "Your task here" \
  --output /path/to/result.md \
  --provider github-copilot \
  --model claude-sonnet-4 \
  --tools read,bash,edit,write \
  --thinking high \
  --cwd /path/to/project \
  --context src/main.ts src/utils.ts
```

### Arguments

| Arg | Short | Required | Description |
|-----|-------|----------|-------------|
| `--prompt` | `-m` | Yes | The task/prompt for pi |
| `--output` | `-o` | No | Output file (default: stdout) |
| `--provider` | `-P` | No | LLM provider (default: pi's configured default) |
| `--model` | `-M` | No | Model ID |
| `--tools` | `-t` | No | Comma-separated tools: read, bash, edit, write, grep, find, ls |
| `--no-tools` | | No | Disable all tools (pure Q&A) |
| `--thinking` | | No | Thinking level: off, minimal, low, medium, high, xhigh |
| `--cwd` | | No | Working directory for pi (default: current) |
| `--system-prompt` | `-s` | No | Custom system prompt |
| `--context` | `-c` | No | Context files (passed to pi as @file references) |

### Available Providers & Models (on this machine)

Pi is configured with `github-copilot` as the default provider. Key models available:

- `claude-sonnet-4`, `claude-sonnet-4.5`, `claude-sonnet-4.6`
- `claude-opus-4.5`, `claude-opus-4.6`
- `claude-haiku-4.5`
- `gpt-5`, `gpt-5.1`, `gpt-5.2`, `gpt-5.4`
- `gpt-5.1-codex`, `gpt-5.1-codex-max`
- `gemini-2.5-pro`, `gemini-3-flash-preview`, `gemini-3-pro-preview`

Run `pi --list-models` for the full list.

## Workflow

1. User requests a task to dispatch to pi, or Claude decides pi would be useful for parallel work
2. **Confirm with the user** before dispatching:
   - What prompt/task to send
   - Which provider and model to use (recommend based on task type)
   - Whether pi should have write access (`--tools`) or be read-only
   - The working directory (`--cwd`) — usually the project root
3. Run `pi-run.py` **in the background** using `run_in_background: true` on the Bash tool
4. Inform the user the task is running
5. When the background task completes, read the output file to get the result
6. Summarize the result for the user without dumping the full content into context unless asked

### Model Selection Guidance

Default is `openai-codex/gpt-5.4`. Only override if the user asks for a specific model.

| Task Type | Model | Provider |
|-----------|-------|----------|
| Default (most tasks) | `gpt-5.4` | `openai-codex` |
| Large codex-style generation | `gpt-5.1-codex-max` | `github-copilot` |
| Quick/cheap tasks | `gpt-5-mini` | `github-copilot` |
| Cross-model validation | `claude-sonnet-4.6` | `github-copilot` |

### Safety

- For tasks that modify files, ensure `--cwd` points to the correct project directory
- Use `--tools read,grep,find,ls` for read-only analysis tasks
- Use `--no-tools` for pure Q&A where no file access is needed
- Pi has **no permission system** in its core — it will execute all tool calls without confirmation. Be deliberate about what tools you enable.

## Example Invocations

```bash
# Background code review with GPT-5
python3 <skill-dir>/scripts/pi-run.py \
  --prompt "Review src/ for security vulnerabilities. Focus on input validation and injection risks." \
  --output /tmp/pi-security-review.md \
  --provider github-copilot --model gpt-5 \
  --tools read,grep,find,ls \
  --cwd /path/to/project

# Parallel refactoring with Opus
python3 <skill-dir>/scripts/pi-run.py \
  --prompt "Refactor the auth module to use JWT tokens instead of session cookies" \
  --output /tmp/pi-refactor-result.md \
  --provider github-copilot --model claude-opus-4.6 \
  --tools read,bash,edit,write \
  --thinking high \
  --cwd /path/to/project

# Quick question, no tools
python3 <skill-dir>/scripts/pi-run.py \
  --prompt "Explain the difference between OAuth 2.0 and OIDC" \
  --output /tmp/pi-explanation.md \
  --no-tools
```
