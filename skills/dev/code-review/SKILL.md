---
name: code-review
description: Conduct thorough, structured code reviews using expert methodologies. Use when reviewing PRs, diffs, or code changes.
model: opus
license: CC BY-NC 4.0
---

# Code Review

Systematic code review methodology based on Google's engineering practices and industry best practices.

## Quick Start

```
Review this PR: <url or diff>
```

```
Review the changes in this branch compared to main
```

```
Do a security-focused review of src/auth/
```

## Review Depth Levels

### Quick Review (< 50 lines changed)
Focus: Obvious bugs, style violations, naming
Time: 5-10 minutes equivalent effort

### Standard Review (50-500 lines)
Focus: Logic, design, tests, documentation
Time: 15-30 minutes equivalent effort

### Deep Review (500+ lines or critical paths)
Focus: Architecture, security, performance, edge cases
Time: Thorough multi-pass analysis

## Review Methodology

### Pass 1: Understand Intent
1. Read PR description/commit message
2. Identify the problem being solved
3. Understand the expected behavior change
4. Note any constraints or requirements mentioned

### Pass 2: High-Level Structure
1. Review file organization and naming
2. Check architectural fit with existing codebase
3. Identify any new dependencies
4. Assess scope creep (does change do more than stated?)

### Pass 3: Logic & Correctness
1. Trace happy path execution
2. Identify edge cases and error conditions
3. Check boundary conditions
4. Verify error handling completeness
5. Look for off-by-one errors, null checks, type coercion issues

### Pass 4: Quality Dimensions

**Security**
- Input validation and sanitization
- Authentication/authorization checks
- Secrets handling (no hardcoded credentials)
- SQL injection, XSS, CSRF vulnerabilities
- Secure defaults

**Performance**
- N+1 queries or unnecessary iterations
- Memory allocation in loops
- Missing indexes for new queries
- Caching opportunities
- Algorithmic complexity

**Maintainability**
- Clear naming (functions, variables, files)
- Single responsibility principle
- Appropriate abstractions (not over/under-engineered)
- Code duplication
- Magic numbers/strings

**Testing**
- Test coverage for new code paths
- Edge case coverage
- Test readability and maintainability
- Mocking appropriateness

### Pass 5: Polish
- Documentation accuracy
- Comment necessity and clarity
- Consistent formatting
- TODO/FIXME items addressed

## Feedback Categories

Structure feedback by severity:

### Blocking
Must fix before merge. Security vulnerabilities, data corruption risks, broken functionality.

**Format**: `[BLOCKING] <issue>: <explanation> → <suggestion>`

### Needs Discussion
Significant concerns requiring author response. Design decisions, architectural questions.

**Format**: `[DISCUSS] <question or concern>`

### Suggestion
Improvements that would strengthen the code. Not required but recommended.

**Format**: `[SUGGESTION] <improvement idea>`

### Nitpick
Minor style/preference items. Optional to address.

**Format**: `[NIT] <small thing>`

### Praise
Highlight good patterns worth noting or replicating.

**Format**: `[NICE] <what's good about it>`

## Writing Effective Feedback

### Do
- Be specific: reference exact lines and code
- Explain why: share the reasoning, not just the rule
- Suggest alternatives: provide concrete fixes
- Ask questions: "What happens if X?" invites dialogue
- Acknowledge tradeoffs: "This adds complexity but improves Y"

### Don't
- Be vague: "This is confusing" (what specifically?)
- Be personal: "You always do this" (focus on code, not author)
- Pile on: 10 comments about the same issue type
- Block on style: use linters for formatting debates
- Demand perfection: good enough to ship beats perfect never shipped

## Review Output Format

```markdown
## Summary
[1-2 sentence overall assessment]

## Scope Check
- [ ] Changes match stated intent
- [ ] No scope creep
- [ ] Appropriate size for single review

## Findings

### Blocking
[List or "None"]

### Needs Discussion
[List or "None"]

### Suggestions
[List or "None"]

### Nitpicks
[List or "None"]

### What's Good
[Highlight positive patterns]

## Verdict
[ ] Approve
[ ] Approve with suggestions
[ ] Request changes
[ ] Needs discussion before decision
```

## Special Review Types

### Security Review
Prioritize Pass 4 security checklist. Cross-reference OWASP Top 10. Check auth boundaries.

### Performance Review
Focus on hot paths, database queries, memory usage. Request benchmarks for critical changes.

### API Review
Check backwards compatibility, versioning, documentation, error responses, rate limiting considerations.

### Database Migration Review
Verify reversibility, data preservation, index impact, lock duration for large tables.

## Common Patterns to Flag

### Red Flags
- `eval()`, `exec()`, dynamic code execution
- SQL string concatenation
- Disabled security features (`verify=False`, `dangerouslySetInnerHTML`)
- Catch-all exception handlers hiding errors
- Commented-out code committed
- Credentials or secrets in code
- `TODO` without ticket reference
- Tests that always pass (no assertions, mocked everything)

### Yellow Flags
- Functions over 50 lines
- Files over 500 lines
- More than 3 levels of nesting
- Boolean parameters (consider options object)
- Optional parameters with `None` defaults mutating state
- `any` type in TypeScript without justification

## References

- [Google Engineering Practices - Code Review](references/google-code-review.md)
- [Security Checklist](references/security-checklist.md)
