## How Work Flows

Work moves through five stages. Not every task needs all five — fixing a typo doesn't need problem definition. But for anything non-trivial, skipping a stage is how things go wrong.

1. **`/problem-definition`** — Frame what we're solving before deciding how to solve it
2. **`/design`** — Explore solutions, evaluate approaches, pick a direction
3. **`/planning`** — Two Codex agents propose in parallel, Opus synthesizes, user approves
4. **`/implementation`** — Sub-agents build in parallel, verified against problem + principles
5. **`/debugging`** — RCA → dual proposal → synthesis → alignment → implement

## Principles

All decisions, proposals, and code are governed by `~/.claude/principles.md`. Read it at the start of every session before doing non-trivial work. Every alignment check verifies against it.

## Codex Dispatch

When the workflow calls for Codex (proposals, approach evaluation, debug proposals), use `pi` directly — NOT Claude sub-agents. Claude writes the prompt, pi sends it to Codex, pipe the output to a file.

```bash
bash ~/.claude/pi-watch.sh -p --no-session \
  --provider openai-codex --model gpt-5.4 \
  --thinking high \
  --tools read,write,grep,find,ls \
  "Read X, do Y, write your output to .building/output.md"
```

- **Always run in background** (`run_in_background: true`, `timeout: 600000`)
- `--thinking`: medium, high, or xhigh depending on task complexity
- `--tools read,write,grep,find,ls`: read + write access so Codex writes its own output
- `--no-tools`: for pure reasoning without file access
- `-p`: non-interactive, process and exit
- `--no-session`: ephemeral, don't save session
- `pi-watch.sh` wraps pi with live progress — shows tool calls and token usage as Codex works

**Prompting Codex:** Tell it which files to read AND where to write its output, all in the prompt. Codex has full tool access. Example: "Read the problem definition at .building/problem-definition/definition.md and the principles at ~/.claude/principles.md. Propose a solution and write it to .building/planning/proposal-a.md."

**When to use Codex vs Claude:**
- Codex (via pi): proposal generation, approach evaluation, research validation, debug proposals
- Claude (via Agent tool): synthesis, alignment checks, verification, implementation, RCA

## Context Awareness

If you notice degraded performance, confusion, or repetition, say so. The context window may need compaction or a fresh session.
