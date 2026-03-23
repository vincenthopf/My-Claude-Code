# Codex Dispatch Patterns

When the workflow calls for Codex agents (proposals, research validation, approach evaluation), use these exact patterns. Do NOT fall back to Claude sub-agents for tasks that should run on Codex.

The pi-agent skill at `~/.claude/skills/pi-agent/` handles dispatch. The script is at `~/.claude/skills/pi-agent/scripts/pi-run.py`.

---

## When to Use Codex vs Claude

| Task | Use Codex (via pi) | Use Claude (Agent tool) |
|------|-------------------|------------------------|
| Proposal generation | Yes — Codex High | No |
| Research validation | Yes — Codex X-High | No |
| Approach evaluation | Yes — Codex X-High | No |
| Proposal synthesis | No | Yes — Opus |
| Alignment checks | No | Yes — Opus |
| Build verification | No | Yes — Opus |
| Integration checking | No | Yes — Opus |
| Implementation | No | Yes — Claude sub-agents |
| RCA / investigation | No | Yes — Opus |

**Rule: If the model column in the workflow says "Codex", dispatch via pi. If it says "Opus", use the Agent tool.**

---

## Dispatch Templates

### Dual Proposal Generation (Planning Stage)

Run TWO of these in parallel as background tasks:

```bash
python3 ~/.claude/skills/pi-agent/scripts/pi-run.py \
  --prompt "$(cat <<'PROMPT'
You are generating a proposal for solving a software problem. Read the provided context files carefully.

Your proposal must cover:
- Approach: the strategy and why it solves the problem
- Steps: concrete, ordered implementation steps
- Decisions: choices made and alternatives rejected, with reasoning
- Risks: what could go wrong, what's uncertain
- Unresolved questions: things you couldn't determine

Write your full proposal as markdown. Be specific — an implementation agent should be able to follow your direction without guessing.
PROMPT
)" \
  --output .building/planning/proposal-a.md \
  --provider openai-codex --model gpt-5.4 \
  --thinking high \
  --tools read,grep,find,ls \
  --cwd "$(pwd)" \
  --context .building/problem-definition/definition.md ~/.claude/principles.md
```

Second proposal — same prompt, different output file:
```bash
# Same command but with: --output .building/planning/proposal-b.md
```

**Important:**
- Both run in background (`run_in_background: true`)
- Both get `--tools read,grep,find,ls` (read-only — proposals don't modify code)
- Both get the same context files
- They produce independent proposals because pi runs are stateless
- Add `.building/design/design.md` to `--context` if design phase was done
- Add `.building/principles.md` to `--context` if project principles exist

### Research Validation (Any Stage)

```bash
python3 ~/.claude/skills/pi-agent/scripts/pi-run.py \
  --prompt "$(cat <<'PROMPT'
You are validating research output. Read the research file provided.

Evaluate:
1. Does the research actually answer the question that was asked?
2. Are there obvious gaps — angles not explored, perspectives missing?
3. Is the depth appropriate — surface-level listing vs genuine analysis?
4. Any contradictions or unreliable claims?

Verdict: SUFFICIENT or NEEDS FOLLOW-UP
If NEEDS FOLLOW-UP, provide specific targeted queries to fill the gaps.
PROMPT
)" \
  --output .building/research-validation.md \
  --provider openai-codex --model gpt-5.4 \
  --thinking xhigh \
  --tools read,grep,find,ls \
  --cwd "$(pwd)" \
  --context path/to/research-output.md
```

**Note:** Research validation uses `--thinking xhigh` for maximum analytical depth.

### Approach Evaluation (Design Stage)

```bash
python3 ~/.claude/skills/pi-agent/scripts/pi-run.py \
  --prompt "$(cat <<'PROMPT'
You are evaluating candidate solution approaches for a defined problem. Read the problem definition and research provided.

For each candidate approach, analyze:
- What does it optimize for?
- Where does it break down in practice?
- Who uses it in production and what do they say?
- What does it sacrifice?
- How does it align with the stated principles?

Do NOT pick a winner. Present the real decision — the core tradeoffs.
PROMPT
)" \
  --output .building/design/approach-evaluation.md \
  --provider openai-codex --model gpt-5.4 \
  --thinking xhigh \
  --tools read,grep,find,ls \
  --cwd "$(pwd)" \
  --context .building/problem-definition/definition.md ~/.claude/principles.md
```

### Debugging — Codex Proposal (Debugging Stage)

```bash
python3 ~/.claude/skills/pi-agent/scripts/pi-run.py \
  --prompt "$(cat <<'PROMPT'
You are proposing a fix for a bug. Read the root cause analysis provided.

Your proposal must cover:
- What to change, where, and why
- Why this approach over alternatives
- Risks of this fix
- What could go wrong

Write a design proposal — what to change and why. Do NOT implement. The proposal is a document, not a diff.
PROMPT
)" \
  --output .building/debugging/proposal-codex.md \
  --provider openai-codex --model gpt-5.4 \
  --thinking high \
  --tools read,grep,find,ls \
  --cwd "$(pwd)" \
  --context .building/debugging/root-cause-analysis.md ~/.claude/principles.md
```

---

## Reading Results Back

After a pi background task completes, read the output file to get the result. Do NOT dump the full content into the main context unless it's short. For proposals (which can be long), read the file and summarize the key points, or pass it directly to the next agent (e.g., the proposal-synthesizer).

```python
# Pattern: read the file, pass to next stage
# Don't: Read("/path/to/proposal-a.md") and paste into conversation
# Do: Pass the file path to the next agent and let it read directly
```

---

## Troubleshooting

- **Pi not found:** `npm install -g @mariozechner/pi-coding-agent`
- **Auth error:** Pi uses `github-copilot` provider. Check `~/.pi/agent/auth.json`
- **Model not available:** Run `pi --list-models` to see what's accessible
- **Timeout:** Default is 120s. For complex proposals, the Bash tool timeout should be set higher: `timeout: 600000`
- **Two proposals collide:** Always use distinct output filenames (`proposal-a.md`, `proposal-b.md`)
