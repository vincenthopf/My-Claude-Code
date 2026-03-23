---
name: implementation
description: >
  Execute the approved proposal. Sub-agents build in parallel, each assigned
  a domain scope. Verification checks against the problem and principles,
  not the proposal document. Two-round iteration limit on failures.
  Use after planning has produced an approved proposal.
---

# Implementation

The proposal is approved. Build it.

Implementation assigns domain-scoped sub-agents to work in parallel, each receiving the full proposal as direction — not a sub-spec. Agents have latitude to make tactical decisions. When they discover the proposal is wrong about something, they flag it rather than building the wrong thing. Verification checks against the problem and principles, not against documents.

---

## When to Use This

- After `/planning` has produced an approved proposal
- After `/debugging` has an approved fix proposal
- When resuming work from a previous session with an existing plan

---

## The Process

### Step 1: Assign Domain Scope

Read the approved proposal at `.building/planning/proposal.md`. Determine what domains the work spans — frontend, backend, API, database, infrastructure, etc.

Scope each sub-agent through **context control, not persona descriptions.** Research shows elaborate role prompts ("you are a senior backend engineer who values clean architecture") don't improve code quality and can actively harm it. What works is controlling what context each agent receives.

**Reality check:** Claude Code doesn't support per-agent tool restrictions or file access controls. All sub-agents have the same tool permissions as the parent. Scoping is advisory — enforced through what context you pass, not through hard boundaries. This means:

- **Information scoping via context:** Each agent receives only the artifacts relevant to its domain in its prompt. The backend agent gets backend-relevant files and the proposal sections about the backend. Less context means less distraction and better focus. This is soft enforcement — the agent *could* read other files, but won't if its prompt is focused.
- **Boundary definition:** Explicit interface contracts from the proposal — what data shapes cross boundaries, what APIs exist between domains, what assumptions must hold.
- **Filesystem isolation:** For projects where parallel agents might conflict on shared files (package.json, configs, build outputs), use git worktrees via the `isolation: "worktree"` parameter on the Agent tool. Each agent works on an isolated copy. Changes are merged after verification.

Each sub-agent receives:
- The proposal (compass, not contract) — filtered to relevant sections where possible
- The problem definition
- Global principles (`~/.claude/principles.md`)
- Project principles (`.building/principles.md`, if they exist)
- Its domain boundary and interface contracts
- Explicit instructions on which directories it should modify

**Interface contract format:**
```
## Interface: [Component A] → [Component B]
- Endpoint/function: [name]
- Input: [data shape with types]
- Output: [data shape with types]
- Assumptions: [what must be true]
- Error handling: [what happens on failure]
```

Keep the system prompt minimal and tool-centric. The agent's job is defined by what context it receives and what it must output, not by who it's pretending to be.

### Step 2: Build in Parallel

Sub-agents execute their domain work. Within each domain:

- **Plan before implementing.** Each agent first decomposes its domain work into concrete steps, then implements using its own plan as a scaffold. This two-phase approach produces better-structured code than single-shot generation.
- **Deterministic steps run directly.** Git operations, linting, formatting, file creation — these don't need an LLM. Run them as shell commands. Don't burn tokens on mechanical work.
- **Agent steps use reasoning.** Architectural decisions, implementation choices, handling edge cases — these need the model.
- **Edit-test-critique cycles.** After writing code, run tests immediately. If tests fail, critique the approach before editing again. Don't just patch the error — understand why it failed.
- **Flag divergence.** If the agent discovers the proposal is wrong about something in their domain — an API that doesn't work as assumed, a framework limitation not anticipated — they flag it in a structured format (file path, what was assumed, what's actually true, what they did instead) rather than building the wrong thing or silently working around it.

### Step 3: Two-Round Iteration Limit

When an implementation attempt or fix fails:

- **Round 1:** Try the fix based on the error.
- **Round 2:** Try a different approach.
- **After round 2:** Stop. Surface to the user with what was tried and why it failed. Don't spiral.

This applies to build errors, test failures, and lint failures. Two honest attempts, then human judgment.

### Step 4: Per-Agent Verification

When a sub-agent completes, dispatch a `build-verifier` agent (Opus) to check the work. The verifier does not just read the code — it **runs it:**

- Executes existing tests. Failures are immediate findings.
- Generates adversarial test cases — edge cases, boundary conditions, integration points the builder likely missed. Runs them.
- Checks against the problem definition — does this actually solve its piece? Grounded in test results, not opinion.
- Checks against the principles — built the right way?
- Checks for divergence — compares behaviour, not code structure. A correct solution that looks nothing like the proposal is fine. A solution that matches the proposal's structure but produces wrong behaviour is a failure.
- Checks structural impact — coupling, duplication, inconsistency.

**Approval is gated on execution results.** A verifier that approves without running tests has failed at its job.

If the verifier returns FAIL, the sub-agent gets structured feedback (file:line references, failing test output, specific issues) and tries again (within the iteration limit).

If the verifier returns PASS WITH FINDINGS, the findings are noted for the integration check.

### Step 5: Integration Check

After all sub-agents pass verification, dispatch the `integration-checker` agent (Opus) to verify the pieces fit together:

- Do interfaces match across domain boundaries?
- Did any agent's divergence break another agent's assumptions?
- Is there anything that falls between the pieces — something no agent owned?
- Do system-level concerns (performance, security, consistency) hold?

If the integration check finds issues, the relevant sub-agents fix their pieces.

### Step 6: Completion Check

Before reporting done, verify:

- The build succeeds (no errors)
- The change does what was intended
- No obvious regressions in surrounding functionality
- The codebase is left better or equal, never worse — no new coupling, duplication, or inconsistency introduced

---

## Git Workflow

NEVER commit directly to main. All work happens on branches.

### Before Making Changes

1. Ask: "Should I create a new branch, or are we on an existing one?"
2. If new branch needed, suggest a name: `feature/description`, `fix/description`
3. Wait for confirmation before creating
4. Create branch and confirm before proceeding

### When Work is Complete

1. Commit with clear messages
2. Push the branch
3. Ask Vince how he'd like to proceed (merge, PR, or further review)

---

## Python Environment (Non-Negotiable)

**NEVER install Python packages globally. NEVER run `pip install` outside a managed environment.**

All Python projects use **uv** for environment and dependency management. No exceptions.

1. Every project gets its own environment. No shared environments.
2. Use `uv` for everything: `uv init`, `uv add`, `uv run`, `uv sync`.
3. Every project must have a `pyproject.toml` with dependencies declared.
4. Never modify the global Python environment.
5. If a project has no `pyproject.toml`, create one with `uv init` before writing code.

---

## Coding Practices

- **Docstrings:** Add to complex functions where the name alone doesn't make purpose, inputs, and outputs obvious. Google style. Simple functions don't need them.
- **Comments:** Explain why, not what. The code shows what; comments explain intent and edge cases.
- **Type hints:** Use them in Python.
- **Modular:** Small, single-purpose functions. If a function does two things, split it.
- **Descriptive names:** Self-explanatory functions and variables. Avoid abbreviations.

### Naming Conventions

- Python files: `snake_case.py`
- JavaScript/TypeScript files: `kebab-case.ts` (or `PascalCase.tsx` for React components)
- Directories: `kebab-case`
- No spaces, no uppercase in directory names

---

## Dev Workflow

### Sharing Local Dev Servers

Use the named **Cloudflare Tunnel** (`dev`) — already configured and authenticated.

```bash
cloudflared tunnel run dev
```

Wildcard DNS: `*.dev.tuesdaystudio.com.au` → this tunnel. Config at `~/.cloudflared/config.yml`.

Tunnel ID: `f8895dc6-de3d-4573-a769-f3ea3526373a`. Current routes: `app` → 3000, `api` → 8080, `admin` → 5173.

---

## Scope Discipline

Do what was asked. Don't produce unrequested work. Don't refactor surrounding code when fixing a bug. Don't add features that weren't asked for. Don't "improve" code you weren't asked to touch. If you're thinking "I should also..." — stop and ask whether Vince wants that.

Non-negotiable. Unsolicited changes erode trust.

---

## Connection to Other Workflows

Implementation follows **planning** (which produced the proposal) and **problem definition** (which established what we're solving). If you're unsure what to build, the problem definition was incomplete. If you're unsure how to approach it, the proposal was incomplete. Go back.

The proposal is direction, not a document to conform to. If you discover it's wrong about something, flag it. Justified divergence is good. Unjustified drift is failure.
