---
name: huly-issues
description: Manage Huly issues and cards with full CRUD operations, status changes, and chat/comments. Use when Claude needs to (1) list, create, update, or delete issues in Huly, (2) change issue status or priority, (3) add or read comments on issues/cards, (4) search for issues, or (5) manage projects. Triggers on requests involving Huly, issue tracking, task management, or card comments.
---

# Huly Issues

Run scripts from `~/.claude/skills/huly-issues/scripts/`.

## Setup (first time only)

```bash
cd ~/.claude/skills/huly-issues
cp .env.example .env   # Edit with your credentials
cd scripts && npm install
```

## Scripts

### Auth & Projects
```bash
node auth.js              # Test connection
node projects.js          # List projects
```

### Issues
```bash
node issues-list.js [--project X] [--limit N]
node issues-get.js PROJ-123
node issues-create.js --project PROJ --title "Title" [--priority High]
node issues-update.js PROJ-123 --status Done [--priority Urgent]
node issues-delete.js PROJ-123
```

### Comments
```bash
node comment-add.js PROJ-123 "Message"
node comments-list.js PROJ-123
```

### Search
```bash
node search.js "query" [--limit N]
```

## Output Format

Compact, one line per item:
```
PROJ-1: [In Progress] Fix login bug (H) @john
PROJ-2: [Todo] Add dark mode (M)
```

## Values

**Status**: `Backlog`, `Todo`, `In Progress`, `Done`, `Canceled`
**Priority**: `Low`, `Medium`, `High`, `Urgent`

## API Reference

See [references/api-reference.md](references/api-reference.md) for detailed documentation.
