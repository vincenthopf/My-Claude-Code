---
name: problem-definition
description: >
  Frame and clarify problems before any planning or implementation begins.
  Use when starting new work, when requirements are unclear, or when the user
  describes what they want built. This is the first step — before planning,
  before code.
---

# Problem Definition

Before planning how to build something, make sure we understand what we're building and why.

This skill exists because problem definition is not the first step of problem solving — it is a cognitively and procedurally distinct activity that degrades when fused with solving. That's not a platitude. It's supported by experimental psychology, documented in high-stakes practice (medicine, military, engineering), and visible in AI system failures. Every major AI agent framework claims to have a "planning phase," but what they actually do is task decomposition — breaking a goal into subtasks. None of them interrogate whether the goal itself is well-formed. This skill fills that gap.

Claude's default behaviour is to start producing. The instinct to generate output is strong. Resist it here. The gap between "What are we working on?" and "Here's the plan" is where the most important thinking happens — and it's the easiest step to skip.

---

## When to Use This

- At the start of any
- non-trivial piece of work
- When the user describes something they want built or changed
- When requirements feel vague, ambiguous, or assumed
- When you're about to start planning and realize you're not sure *what problem you're solving*
- When a bug needs investigation, invoke `/debugging` instead — RCA is problem definition for bugs

---

## The Process

Problem definition moves through eight steps. Not every problem needs all eight — a small feature might need steps 1, 2, and 8. A major architectural decision needs all of them. Scale the process to the problem, not the other way around.

### Step 1: Understand in the User's Words

Before refining, restating, or analysing — listen. What is the user actually saying? What's the intent behind the words? Grasp the nuance. No frameworks yet, no categorisation. Just understand.

If the request is ambiguous, ask. Don't assume. Don't fill gaps with your own interpretation. The user's framing is the starting point, not something to be corrected.

### Step 2: Problem-Type Diagnosis

What kind of problem is this? The type determines how heavy the rest of the process needs to be and which tools apply.

- **Bounded** — Clear inputs, clear expected output. Something's broken, or something specific needs to be built. The problem space is well-defined.
- **Unbounded** — We want to achieve something but the shape isn't clear yet. Multiple valid approaches exist. The problem space itself needs exploration.
- **Bug** — Something that worked doesn't anymore, or something doesn't work as expected. Hand off to `/debugging` for RCA. Don't try to define a bug and solve it in the same pass.
- **Exploration** — We're investigating, not building. The output is understanding, not code.

This isn't a rigid taxonomy — it's a diagnostic question. "What kind of thinking does this problem need?" informs every step that follows.

### Step 3: Existing-Solution Research

Before committing to build, search for whether this problem has already been solved. This is the cheapest intervention in the entire workflow — research that finds an existing solution saves weeks of implementation.

Use `/deep-research` with parallel tasks targeting:

- **Direct solutions** — Open-source projects, libraries, or tools that solve this exact problem
- **Adjacent solutions** — Projects that solve a related problem and could be adapted
- **Prior art in this codebase** — Check git history, plan files, learnings, and project memories for previous attempts

When research results come back, validate them using Codex X-High via `dispatch.py`:

```bash
python3 ~/.claude/skills/workflow-research/dispatch.py \
  --prompt "Evaluate this research: does it actually answer the question? What gaps exist? What's surface-level vs genuinely deep? Verdict: SUFFICIENT or NEEDS FOLLOW-UP with specific follow-up queries." \
  --output .building/problem-definition/research-validation.md \
  --cwd "$(pwd)" \
  --thinking xhigh \
  --context path/to/research-output.md
```

Run in background (`run_in_background: true`, `timeout: 600000`). If the validator says NEEDS FOLLOW-UP, dispatch targeted research to fill the gaps. Don't proceed with thin research on a problem that matters.

If something exists that solves 80% of the problem, building from scratch is waste. If nothing exists, that's also a valuable finding — it tells us we're in genuinely new territory and should proceed with proportional care.

If the problem is small or clearly novel, this step can be light — a quick search rather than a full research run. Use judgment on depth.

### Step 4: Cognitive Operations

This is the actual definition work. Not "define the problem" as a checkbox, but a specific set of cognitive moves:

**IS / IS-NOT boundaries.** What is the problem versus what it's adjacent to but isn't? This comes from Kepner-Tregoe and it's the one thing they got right. Drawing a clear boundary around what you're solving prevents scope from drifting and keeps the definition precise. "This IS a performance problem in the query layer. This IS NOT a schema design problem, even though the schema could be improved."

**Multiple abstraction levels.** State the problem as a symptom, as a cause, and as a systemic pattern. Are we treating the right level? A button that doesn't work might be a UI bug (symptom), a state management issue (cause), or an architectural problem with how events propagate (pattern). The level you choose to solve determines everything downstream.

**Enumerate unknowns.** What don't we know? What assumptions are we making? This is the single biggest failure mode the research identifies. Every problem definition rests on assumptions — most of them invisible. Make them visible. "We're assuming the API supports batch operations. We're assuming the user has network access. We're assuming the data fits in memory." Each assumption is a risk.

**Whose perspective is missing?** Who is affected by this problem that we haven't considered? What would someone who disagrees with this framing say? This isn't about stakeholder mapping — it's about ensuring the definition isn't blind to a perspective that would change it.

### Step 5: Adversarial Review and Context Analysis

Launch three sub-agents in parallel. Each writes its output to a file — do not load their full reports into the main context.

1. **Definition Critic** (`definition-critic` agent) — Attacks the problem definition. Wrong problem? Wrong scope? Wrong level? Unexamined anchoring? It critiques the framing — it does not propose alternatives or solutions.

2. **Context Analyst** (`context-analyst` agent) — Maps the landscape. What already exists in the codebase? What's been tried before? What systems couple to this? What happens downstream if we solve it? It provides terrain — it does not navigate.

3. **Assumptions Auditor** (`assumptions-auditor` agent) — Surfaces every invisible assumption in the definition. Technical, scope, causal, temporal. Rates each by risk level. For high-risk assumptions, recommends how to verify them.

Invoke all three with the current problem definition. Each agent writes its output to `.building/problem-definition/`:

- Devil's advocate → `.building/problem-definition/definition-critic.md`
- Context analyst → `.building/problem-definition/context-analysis.md`
- Assumptions auditor → `.building/problem-definition/assumptions-audit.md`

Create the `.building/problem-definition/` directory if it doesn't exist. Read the summaries (verdict + key findings), not the full reports, unless a finding warrants deeper examination.

### Step 6: Iterate If Needed

If step 5 surfaces significant concerns — the devil's advocate rates the framing WEAK, the assumptions auditor finds high-risk unverified assumptions, the context analyst reveals the problem is already half-solved — update the definition.

This is a loop, not a linear step. The cost of refining a definition is minutes. The cost of building against a bad definition is days or weeks. If the framing needs to change, change it. If it needs a second round of review, run it.

Not every problem will need iteration. If the three agents come back clean, move on.

### Step 7: Produce the Definition Artifact

The output of problem definition is a structured artifact written to `.building/problem-definition/definition.md`. This file survives handoff between agents and between sessions — it's what the planning skill reads when it starts. Everything not written here is lost. There is no tacit knowledge channel between agents.

If existing-solution research was performed in step 3, write those findings to `.building/problem-definition/existing-solutions.md`.

The artifact captures not just the conclusion but the reasoning behind it:

- **Problem statement** — What we're solving, in clear language
- **Problem type** — Bounded, unbounded, exploration (bugs go to `/debugging`)
- **Rationale** — Why this framing and not another. What led us here.
- **Rejected alternatives** — What framings we considered and dismissed, and why. This is critical — without it, future agents or sessions will re-explore paths already ruled out.
- **Uncertainties** — What we're not sure about. What could change the approach.
- **Assumptions** — The key assumptions this definition rests on, especially any that are unverified.
- **Constraints** — What's non-negotiable. Technical, time, resource, or design constraints.
- **Scope** — What's in, what's explicitly out.
- **Existing solutions** — What the research found. Libraries, tools, or prior art that could be used.
- **Success criteria** — How we'll know the problem is solved.

The format scales with the problem. A small feature might be a short paragraph covering statement, scope, and constraints. A major piece of work gets the full artifact. The principle is: write enough that a different agent in a different session could pick this up and understand not just *what* the problem is, but *why it was framed this way*.

The `.building/` directory is the shared workspace for all agentic workflow artifacts. Problem definition writes to `.building/problem-definition/`. Planning will write to `.building/planning/`. Implementation research goes to `.building/implementation/research/`. Debugging writes to `.building/debugging/`. This convention means every skill knows where to find what came before it.

### Step 8: Confirm with the User

The definition isn't done until the user says it's done. Restate the problem. Check for alignment. This is the read-back step from handoff research — the receiver (in this case, the user) synthesises what they've heard, and discrepancies are resolved before work begins.

If the user's response reveals a misalignment, go back to the appropriate step. Don't proceed with a definition the user hasn't confirmed.

---

## What This Is Not

- Not a requirements gathering template to fill out mechanically. The steps are cognitive operations, not form fields. Skip what doesn't apply, go deep where it matters.
- Not a gate that blocks quick, obvious tasks. Fixing a typo doesn't need problem definition. Neither does a change that's clearly implied by the conversation. Use judgment.
- Not a substitute for the user's judgment about what to build. It's a tool for making that judgment sharper.
- Not solution design. This skill defines the problem. `/planning` designs the solution. `/implementation` builds it. Keep them separate — the research is unambiguous that fusing definition with solving degrades both.

---

## Connection to Other Workflows

Problem definition is the first phase. It feeds into **design** (`/design`) which explores solutions and picks a direction, then **planning** (`/planning`) which produces a concrete proposal, and then **implementation** (`/implementation`) which builds it. For bounded problems where the approach is obvious, skip design and go straight to planning. For bugs, **debugging** (`/debugging`) replaces this skill — RCA is problem definition for bugs.

The definition artifact produced in step 7 becomes the input to design or planning. If the artifact is thin, everything downstream is guesswork. If it's clear, the direction becomes obvious.

---

## Research Basis

This skill is informed by a coordinated research effort covering cognitive science (Einstellung effect, expert vs novice problem framing, representational change theory), high-stakes disciplines (medical differential diagnosis, military ADM, NASA requirements engineering), AI agent systems (failure modes in CrewAI, LangChain, AutoGPT), framework analysis (Kepner-Tregoe, 5 Whys, Cynefin, MECE, Design Thinking, Systems Thinking, TOC, PSMs), and handoff information loss (I-PASS, SBAR, boundary objects, the five categories of handoff loss). Full research at `~/Documents/ccexplore/07-03-2026/testingprogressive/research/`.
