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
pi -p --no-session \
  --provider openai-codex --model gpt-5.4 \
  --thinking high \
  --tools read,grep,find,ls \
  "Your prompt here" > .building/output.md
```

- **Always run in background** (`run_in_background: true`, `timeout: 600000`)
- `--thinking`: medium, high, or xhigh depending on task complexity
- `--tools read,grep,find,ls`: read-only access (default for proposals)
- `--no-tools`: for pure reasoning without file access
- `-p`: non-interactive, process and exit
- `--no-session`: ephemeral, don't save session
- Pipe stdout to file with `>`

**Prompting Codex:** Codex has read tools. Tell it which files to read in the prompt: "Read the problem definition at .building/problem-definition/definition.md and the principles at ~/.claude/principles.md, then propose a solution."

**When to use Codex vs Claude:**
- Codex (via pi): proposal generation, approach evaluation, research validation, debug proposals
- Claude (via Agent tool): synthesis, alignment checks, verification, implementation, RCA

## Context Awareness

If you notice degraded performance, confusion, or repetition, say so. The context window may need compaction or a fresh session.
