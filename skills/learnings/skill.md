---
name: learnings
description: >
  MANDATORY at two points in every session:
  (1) BEFORE debugging or investigating any non-trivial problem — search LEARNINGS.md first, the answer may already exist as a draft or confirmed fix.
  (2) AFTER solving any non-trivial problem — document it as a new draft or promote an existing draft to confirmed.
  Also invoke at session start to scan for relevant confirmed knowledge.
  This skill manages a hierarchical knowledge base where fixes earn trust through repetition:
  [DRAFT] (first observation) → [CONFIRMED] (verified a second time) → or [INVALIDATED] (proven wrong).
  Confirmed entries can regress to [REGRESSION] if they stop working.
  Triggers: debugging, fixing bugs, discovering SDK quirks, finding workarounds, performance tuning, resolving test failures, platform-specific issues.
  If you solve something and don't document it here, that knowledge is lost forever.
---

# Learnings — Hierarchical Knowledge Base

You have a shared knowledge base at `~/.claude/skills/learnings/LEARNINGS.md`. It tracks solutions, workarounds, and patterns with a maturity pipeline: `[DRAFT]` → `[CONFIRMED]` or `[INVALIDATED]`. Confirmed entries can regress to `[REGRESSION]` if they stop working.

## When to Use This

### At session start

Read `~/.claude/skills/learnings/LEARNINGS.md` to load confirmed knowledge. You don't need to memorize it — just be aware it exists so you search it when relevant.

### When you hit a problem

Before investigating from scratch:

1. **Search LEARNINGS.md** for keywords related to the issue (use Grep).
2. **`[CONFIRMED]` match found** — apply the solution directly. Mention: "Applying confirmed learning: [title]."
   - If it doesn't work → **mark `[REGRESSION]`**: change the heading, add `**Regression:** YYYY-MM-DD` and `**Context:**` explaining what changed. Then investigate fresh and add a new `[DRAFT]` with the updated fix.
3. **`[DRAFT]` match found** — try the solution.
   - If it works → **promote to `[CONFIRMED]`**: change the heading, add `**Confirmed:** YYYY-MM-DD`.
   - If it doesn't work → **mark `[INVALIDATED]`**: change the heading, strike through content, add `**Invalidated:** YYYY-MM-DD` and `**Reason:**`.
4. **No match** — investigate normally.

### After solving a non-trivial problem

1. **Search LEARNINGS.md** for existing drafts that match what you just solved.
2. **Match found** — this is a confirmation event. Promote the draft.
3. **No match** — add a new `[DRAFT]` entry.

## Entry Format

```markdown
### [DRAFT] Short descriptive title `tag1` `tag2`

**Problem:** What went wrong. Specific enough to match against in future searches.

**Solution:** What fixed it. Specific enough to reproduce without re-investigating.

**Project:** Project name
**First seen:** YYYY-MM-DD
**File:** relative/path/to/relevant/file.ext
```

### Tags

Freeform, lowercase, backtick-wrapped. Common tags:

- `platform` — browser/OS-specific issues
- `css` `typescript` `react` `nextjs` — technology
- `performance` — speed, rendering, bandwidth
- `testing` — test infrastructure, flaky tests
- `sdk` — third-party SDK quirks
- `architecture` — structural decisions
- `tooling` — build tools, dev environment

### State Transitions

**Promoting to confirmed:**
```markdown
### [CONFIRMED] Short descriptive title `tag1` `tag2`
...existing content...
**Confirmed:** YYYY-MM-DD
```

**Invalidating a draft:**
```markdown
### [INVALIDATED] Short descriptive title `tag1` `tag2`

~~**Problem:** ...~~
~~**Solution:** ...~~

**Invalidated:** YYYY-MM-DD
**Reason:** Why the original fix was wrong or situational.
```

**Regressing a confirmed entry** (it used to work but doesn't anymore):
```markdown
### [REGRESSION] Short descriptive title `tag1` `tag2`

**Problem:** ...
**Solution:** ...  ← the solution that no longer works

**First seen:** YYYY-MM-DD
**Confirmed:** YYYY-MM-DD
**Regression:** YYYY-MM-DD
**Context:** What changed — dependency update, platform change, new constraints, etc.
```

After marking a regression, investigate fresh and add a new `[DRAFT]` with the updated fix. The regression entry stays as a record of what stopped working and why.

## What to Add

- Bug fixes and workarounds that a future agent would re-encounter
- SDK quirks and non-obvious API behavior
- Performance fixes with specific thresholds
- Architecture decisions with the reasoning
- Testing patterns that prevent flaky tests

## What NOT to Add

- Trivial fixes (typos, missing imports, obvious errors)
- Project-specific business logic (that belongs in project docs)
- Setup steps (that belongs in README)
- Facts in official documentation (link to docs instead)

## If LEARNINGS.md Doesn't Exist

Create it with this header:

```markdown
# Learnings

> Hierarchical knowledge base. Entries mature through observation:
> `[DRAFT]` → `[CONFIRMED]` or `[INVALIDATED]`
>
> Search this file when hitting problems. Promote drafts when you
> re-encounter and confirm them. Add new drafts when you solve
> something non-trivial.

---
```

## Key Principles

- **Search before investigating.** The answer might already be here.
- **Draft everything non-trivial.** Better to have a draft that gets invalidated than to lose knowledge.
- **Promote honestly.** Only confirm when the same fix genuinely worked in a second encounter, not just because it seems right.
- **Invalidate without shame.** Wrong drafts are valuable — they prevent future agents from going down the same dead end.
- **Be specific.** "It didn't work" is useless. "The real cause was X, not Y" is gold.
