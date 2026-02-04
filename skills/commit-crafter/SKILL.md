---
name: commit-crafter
description: Craft high-quality git commits and PR descriptions. Use when staging changes, writing commit messages, preparing pull requests, or when asked to review changes before committing. Helps ensure atomic commits, meaningful messages, and comprehensive PR documentation.
---

# Commit Crafter

A systematic approach to crafting excellent git commits and pull request descriptions.

## When to Use

- User asks to commit changes
- User wants help writing a commit message
- User is preparing a pull request
- User wants to review staged changes before committing
- User asks for help organizing commits

## Commit Message Philosophy

Great commit messages answer three questions:
1. **What** changed? (the subject line)
2. **Why** did it change? (the body)
3. **What impact** does this have? (footer/breaking changes)

## Commit Analysis Workflow

### Step 1: Analyze the Changeset

```bash
# View staged changes
git diff --cached --stat
git diff --cached

# View unstaged changes (context)
git status
git diff --stat
```

### Step 2: Classify Changes

Categorize each changed file:

| Category | Prefix | Example |
|----------|--------|---------|
| New feature | `feat` | feat: add user authentication |
| Bug fix | `fix` | fix: resolve null pointer in parser |
| Documentation | `docs` | docs: update API reference |
| Code style | `style` | style: format with prettier |
| Refactoring | `refactor` | refactor: extract validation logic |
| Performance | `perf` | perf: optimize database queries |
| Tests | `test` | test: add unit tests for auth |
| Build/CI | `build`/`ci` | ci: add GitHub Actions workflow |
| Chores | `chore` | chore: update dependencies |

### Step 3: Check for Atomicity

A commit should be atomic - one logical change. Ask:
- Can this be split into smaller, independent commits?
- Does each change stand alone and make sense?
- If reverted, would it cleanly undo one thing?

**Split signals:**
- Multiple unrelated files changed
- Mix of features and fixes
- Commented "also" or "and" needed in message

### Step 4: Craft the Message

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Subject line rules:**
- Use imperative mood ("add" not "added")
- No period at the end
- Max 50 characters (hard limit: 72)
- Be specific, not vague

**Body guidelines:**
- Wrap at 72 characters
- Explain what and why, not how
- Include context that isn't obvious from the diff
- Reference related issues

**Footer uses:**
- `BREAKING CHANGE:` for breaking changes
- `Fixes #123` to auto-close issues
- `Co-authored-by:` for pair programming

## Message Quality Checklist

Before finalizing a commit message, verify:

- [ ] Subject uses imperative mood
- [ ] Subject is under 50 chars (72 max)
- [ ] Type prefix matches the change
- [ ] Scope (if used) is meaningful
- [ ] Body explains "why" not just "what"
- [ ] Breaking changes are clearly marked
- [ ] Related issues are referenced

## Pull Request Workflow

### PR Title

Follow same conventions as commit subjects:
```
feat(auth): implement OAuth2 login flow
```

### PR Description Template

```markdown
## Summary
[1-3 sentences explaining what this PR does and why]

## Changes
- [Bulleted list of key changes]
- [Group related changes together]

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] Edge cases considered

## Screenshots
[If UI changes, include before/after]

## Related
- Fixes #[issue]
- Related to #[issue]
```

## Common Patterns

### Feature Addition
```
feat(users): add email verification flow

Implement email verification to prevent fake accounts.
Users receive a verification link valid for 24 hours.

- Add verification token generation
- Create email template
- Add verification endpoint
- Update user status on verification

Closes #234
```

### Bug Fix
```
fix(parser): handle empty input gracefully

Previously, empty strings caused a null pointer exception
in the tokenizer. Now returns an empty result set.

Fixes #567
```

### Refactoring
```
refactor(api): extract response formatting

Move response formatting logic from individual handlers
to a shared middleware. Reduces duplication and ensures
consistent error responses.

No functional changes.
```

### Breaking Change
```
feat(api)!: change authentication header format

BREAKING CHANGE: Authorization header now requires
'Bearer ' prefix. Update all API clients.

Migration guide: docs/migrations/auth-v2.md
```

## Anti-Patterns to Avoid

| Bad | Better |
|-----|--------|
| "fix bug" | "fix: prevent crash on empty input" |
| "update code" | "refactor: simplify auth middleware" |
| "WIP" | Don't commit WIP, use branches |
| "misc changes" | Split into atomic commits |
| "review feedback" | Squash or describe the actual change |

## Quick Commands

```bash
# Amend last commit message (unpushed only)
git commit --amend

# Interactive rebase to squash/reword
git rebase -i HEAD~3

# See what would be committed
git diff --cached

# Stage specific hunks
git add -p
```

## Integration Notes

When invoked, this skill should:
1. Run `git diff --cached --stat` to see staged changes
2. Run `git diff --cached` to analyze the actual changes
3. Classify the type of change
4. Check for atomicity issues
5. Generate a commit message following the format
6. If preparing a PR, also generate description
