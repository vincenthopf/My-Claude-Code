---
name: design
description: >
  Explore the solution space after the problem is defined. Evaluate approaches,
  form project-specific principles, and pick a direction. Sits between problem
  definition and planning. Use when the problem is defined but the approach
  isn't decided yet.
---

# Design

The problem is defined. Now figure out what kind of solution we're building — not the implementation details, but the direction. Build vs buy. This framework vs that one. Monolith vs services. The decisions that shape everything downstream.

Design is where you explore options with open eyes, evaluate them rigorously, and let the user's principles decide the direction. It is not planning — planning produces a concrete proposal. Design produces a direction that planning proposes against.

---

## When to Use This

- After `/problem-definition` has produced a confirmed definition
- When the solution approach isn't obvious — multiple valid directions exist
- When technology choices need evaluation before committing
- When build vs buy needs investigation

Skip this for bounded problems where the approach is obvious. If the problem definition makes the solution direction clear, go straight to `/planning`.

---

## The Process

### Step 1: Receive the Definition

Read the definition artifact at `.building/problem-definition/definition.md` and supporting files. Do a read-back — restate the problem in your own words. If existing-solution research was done during problem definition, read `.building/problem-definition/existing-solutions.md`.

If the definition is missing or incomplete, stop. Don't design against a vague problem.

### Step 2: Research the Solution Space

Explore what's out there. This is not "find the answer" — it's "map the terrain."

- What approaches exist for this kind of problem?
- Who's solved something similar? How? What worked, what didn't?
- What tools, frameworks, or libraries could apply?
- What's the build-vs-buy landscape?

Dispatch research to deep-research. When results come back, send them to the `research-validator` agent (Codex X-High) to evaluate quality and identify gaps. If the validator says the research needs follow-up, dispatch targeted queries to fill the gaps.

Don't propose anything yet. Just explore.

### Step 3: Evaluate Approaches

From the research, identify the candidate approaches — typically 2-4 viable options.

**IMPORTANT: Use pi dispatch for approach evaluation, NOT a Claude sub-agent.** This runs on Codex X-High, not Claude.

```bash
python3 ~/.claude/skills/pi-agent/scripts/pi-run.py \
  --prompt "[approach evaluation prompt — see codex-dispatch.md]" \
  --output .building/design/approach-evaluation.md \
  --provider openai-codex --model gpt-5.4 \
  --thinking xhigh \
  --tools read,grep,find,ls \
  --cwd "$(pwd)" \
  --context .building/problem-definition/definition.md ~/.claude/principles.md
```

Run in background with `run_in_background: true` and `timeout: 600000`. Full dispatch patterns at `~/.claude/skills/workflow-research/codex-dispatch.md`.

The evaluator does not pick a winner. It presents the real decision — the core tradeoffs the user is choosing between.

### Step 4: Form Project Principles

This is where the user's reactions to the research and evaluation crystallise into project-specific principles. Not every project needs these — the global principles at `~/.claude/principles.md` cover most situations.

But if the user has strong reactions — "I refuse to use a framework that heavy," "offline-first is non-negotiable for this," "speed of iteration matters more than scalability here" — those become project principles written to `.building/principles.md`.

Don't force this step. If the user doesn't have strong project-specific values, the global principles are sufficient. Ask: "Anything you specifically care about for this project that isn't covered by our general principles?"

### Step 5: Pick a Direction

Present the evaluation to the user. Let them decide the direction based on their principles and the analysis.

The output is a direction, not a plan. "We're building a REST API with PostgreSQL, not using an existing BaaS" is a direction. The specific endpoints, schema, and architecture come in planning.

### Step 6: Produce the Design Artifact

Write the design decision to `.building/design/design.md`. This captures:

- **Direction chosen** — What approach we're going with
- **Why this direction** — How it maps to the problem and principles
- **Alternatives considered** — What was evaluated and rejected, and why
- **Project principles** — If any were formed, reference `.building/principles.md`
- **Open questions** — Things the design doesn't resolve that planning will need to address
- **Constraints discovered** — Technical or practical constraints found during evaluation

This artifact feeds into planning. A clear design decision makes the planning proposal straightforward. A vague design decision makes planning guess.

---

## What This Is Not

- Not planning. Design picks a direction. Planning produces a concrete proposal for that direction.
- Not research for its own sake. Research serves the evaluation. Don't keep exploring once you have enough to decide.
- Not a technology comparison blog post. The evaluation is for this specific problem against these specific principles.

---

## Connection to Other Workflows

Design receives the definition from **problem definition** (`/problem-definition`) and produces a direction that **planning** (`/planning`) proposes against. For bugs, **debugging** (`/debugging`) handles its own approach selection — design is for when the solution space is genuinely open.

All artifacts are written to `.building/design/`. Planning reads from here to understand the chosen direction.
