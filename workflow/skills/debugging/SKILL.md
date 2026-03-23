---
name: debugging
description: >
  Full bug-fix pipeline from root cause analysis through implementation.
  Separates investigation, proposal, alignment, and execution into
  distinct agent responsibilities. Also applies to features and refactors
  by skipping root cause analysis and starting at proposal.
---

# Debugging

Find out what's actually broken, figure out the right fix, confirm it's the right fix, then implement it — in that order. Each step is a separate concern handled by a separate agent, because mixing investigation with solution-design with implementation is how bugs get "fixed" three times.

---

## When to Use This

- When something is broken and needs to be fixed
- When behaviour is wrong but the cause isn't obvious
- When a fix attempt has already failed and we need to start fresh
- For features and refactors, the same pipeline applies — skip step 1 and start at Proposal

---

## The Pipeline

### 1. Root Cause Analysis

Launch a sub-agent to investigate. Its job is to read code, trace the failure path, reproduce the conditions mentally, and produce a root-cause report. It does NOT propose fixes. This is the hard constraint — investigation and solution-design must be separate, because an agent that's already thinking about the fix will see the codebase through the lens of the fix it wants to make.

RCA is problem definition for bugs. The same principle applies: understand the problem before solving it. A root-cause report that ends with "and here's how to fix it" has violated its mandate. The report should answer: what is failing, where does it fail, why does it fail, and what conditions trigger the failure.

### 2. Proposal

Launch two agents in parallel to independently propose a fix based on the RCA findings:

- **Opus agent** — Reads the root-cause report, the problem context, and the principles (`~/.claude/principles.md` + `.building/principles.md` if it exists). Proposes a fix with strong intent-understanding — focuses on what the code should do and why.
- **Codex High agent** — **Use `dispatch.py` to prompt Codex, NOT a Claude sub-agent:**

```bash
python3 ~/.claude/skills/workflow-research/dispatch.py \
  --prompt "Your fix proposal prompt — describe the bug, the RCA findings, and what kind of fix to propose" \
  --output .building/debugging/proposal-codex.md \
  --cwd "$(pwd)" \
  --thinking high \
  --context .building/debugging/root-cause-analysis.md ~/.claude/principles.md
```

Run in background with `run_in_background: true` and `timeout: 600000`. Claude writes the prompt based on the specific bug. Codex proposes a fix independently — may take a different approach or surface different considerations.

Each writes a design proposal — what to change, where, and why this approach over alternatives. They do NOT implement. The proposal is a document, not a diff.

For features and refactors, this is where the pipeline starts. Both agents take the problem definition or feature spec and design the approach independently.

The `proposal-synthesizer` agent (Opus) then reads both proposals and produces one coherent fix proposal, justifying every choice.

### 3. Alignment

Check the synthesized proposal — one pass, two dimensions:

- **Problem fit** — Does this fix actually address the root cause identified in step 1? Does it fix the symptom without addressing the cause, or vice versa?
- **Principles alignment** — Does the fix honour how we build? Does it leave the codebase better or equal?

The alignment agent identifies contradictions and gaps. It doesn't fix them — it reports them. If the proposal contradicts an established pattern, that's a finding. If the proposal introduces a parallel system when an existing one should be extended, that's a finding. If it looks solid, say so and move on.

### 4. Iterate

If alignment surfaces contradictions or gaps, refine the proposal and re-check. This is a loop, not a linear step. The cost of iterating on a proposal is a few minutes of agent time. The cost of implementing the wrong thing is debugging the debugging — which is where projects go to die.

Do not implement a proposal that hasn't passed alignment. If the proposal needs three rounds of refinement, it needs three rounds. The pipeline is cheap; rework is expensive.

### 5. Risk Assessment

Once the proposal is aligned, assess whether it can be implemented reliably in its current form. Launch two sub-agents in parallel:

- **Audit risk** — Can we reliably research and verify this change? Is the surface area small enough that an agent can hold the full context? Are there hidden dependencies that might be missed?
- **Alignment risk** — Can we reliably check direction during and after implementation? Will we know if the implementation has drifted from the proposal?

If either risk is too high, decompose the proposal into smaller pieces. The decision to decompose isn't driven by complexity — it's driven by risk. A complex change that's well-contained in one module might not need decomposition. A simple-looking change that touches five systems might.

### 6. Research

For each piece (or for the whole proposal if it wasn't decomposed), launch a sub-agent to research hookpoints in the codebase. Where does this change attach? What existing systems does it interact with? What patterns are already in place that this change should follow?

This step exists because the most common failure mode in implementation is building parallel systems. An agent that doesn't know about the existing error handling, or the existing event bus, or the existing validation layer, will build a new one. Research prevents that. Every piece gets codebase research before any code is written.

### 7. Implement

Only after the proposal has passed alignment, passed risk assessment, and each piece has been researched. Launch implementation sub-agents for each piece. They have the proposal, the research findings, and a clear, bounded scope. They write code, not proposals.

Implementation follows the standard implementation skill — git workflow, coding practices, verification. The debugging skill governs the pipeline; the implementation skill governs the code.

---

## Artifact Paths

All debugging artifacts are written to `.building/debugging/`. Create this directory if it doesn't exist.

- RCA report → `.building/debugging/root-cause-analysis.md`
- Opus proposal → `.building/debugging/proposal-opus.md`
- Codex proposal → `.building/debugging/proposal-codex.md`
- Synthesized proposal → `.building/debugging/proposal.md`
- Alignment check → `.building/debugging/alignment.md`
- Risk assessment → `.building/debugging/risk-assessment.md`

Each agent writes to its specified path. The next step in the pipeline reads from the previous step's path. No implicit handoffs — everything is file-based.

---

## Principles

**Separate agents for separate concerns.** RCA agents don't propose. Proposal agents don't implement. Alignment agents don't fix. Each agent has one job and produces one output. This isn't bureaucracy — it's quality control. An agent that investigates and fixes in the same pass will anchor on its first hypothesis and miss the actual root cause.

**Risk drives decomposition.** Don't decompose because something looks complex. Decompose because audit risk or alignment risk exceeds what a single agent can handle reliably. If an agent can hold the full context and we can verify its work, one piece is fine regardless of how many lines it touches.

**Alignment is directional.** It checks for contradictions and gaps at the points where mismatch is most likely. It doesn't try to anticipate every edge case or verify every detail — that's what implementation and verification are for. Alignment asks: "Is this going the right way?" If yes, move forward.

**Research before implementation.** Every piece gets codebase research to find hookpoints, existing patterns, and systems that should be extended rather than duplicated. Skipping this step is the single most reliable way to introduce technical debt.

**Iterate until it passes.** The loop between proposal, alignment, and refinement is the cheapest place to catch mistakes. Protect it. Don't shortcut it because the fix "seems obvious." Obvious fixes that skip alignment are how codebases accumulate contradictions.

---

## Connection to Other Workflows

The debugging pipeline builds on **problem definition** (RCA is problem definition for bugs) and feeds into **implementation** (which handles the actual code). **Planning** covers the broader approach for non-bug work, but for bugs, this pipeline replaces the planning phase — RCA, proposal, and alignment together serve the same function as planning does for features.

Features and refactors use the same pipeline starting at step 2 (Proposal), with the problem definition or feature spec standing in for the RCA report.
