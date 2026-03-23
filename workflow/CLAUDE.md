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

When the workflow calls for Codex (proposals, approach evaluation, debug proposals), use `dispatch.py` — NOT Claude sub-agents. Claude writes the prompt, dispatch.py sends it to Codex, the response lands in a file.

```bash
python3 ~/.claude/skills/workflow-research/dispatch.py \
  --prompt "Your prompt here" \
  --output .building/output.md \
  --cwd "$(pwd)" \
  --thinking high \
  --context file1.md file2.md
```

- **Always run in background** (`run_in_background: true`, `timeout: 600000`)
- `--thinking`: medium, high, or xhigh depending on task complexity
- `--context`: pass problem definitions, principles, and relevant artifacts
- `--no-tools`: for pure reasoning without file access
- `--allow-missing-context`: skip missing context files instead of failing
- Codex response is written to `--output`. Read the file when the task completes.

**When to use Codex vs Claude:**
- Codex (via dispatch.py): proposal generation, approach evaluation, research validation, debug proposals
- Claude (via Agent tool): synthesis, alignment checks, verification, implementation, RCA

## Context Awareness

If you notice degraded performance, confusion, or repetition, say so. The context window may need compaction or a fresh session.
