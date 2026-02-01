# My Claude Code Workflows

Personal collection of skills, commands, and configurations for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Structure

```
.
├── skills/           # Custom skills extending Claude Code capabilities
├── commands/         # Slash commands for common workflows
└── settings.json     # Claude Code configuration
```

## Skills

| Skill | Description |
|-------|-------------|
| **agent-browser** | Browser automation for web testing, form filling, screenshots, and data extraction |
| **deep-research** | Deep research using Parallel.ai API with structured query formulation |
| **skill-from-masters** | Framework for creating high-quality skills based on expert methodologies |
| **skill-creator** | Guided skill generation with proper structure and validation |

### Development Skills (`skills/dev/`)

| Skill | Description |
|-------|-------------|
| **huly-issues** | Full CRUD operations for Huly issue tracking and task management |
| **authentic-blog-writer** | Blog writing workflow |

## Installation

To use these skills in your Claude Code setup:

```bash
# Copy a skill to your Claude Code skills directory
cp -r skills/agent-browser ~/.claude/skills/

# Or symlink for easier updates
ln -s $(pwd)/skills/agent-browser ~/.claude/skills/agent-browser
```

## Commands

Custom slash commands available via `/command-name`:

- `/research` - Invoke deep research workflow

## Configuration

The `settings.json` contains my preferred Claude Code configuration:
- Default model: `opus`
- Default mode: `plan` (requires approval before implementation)

## Requirements

Some skills require additional setup:

- **deep-research**: Requires `PARALLEL_API_KEY` environment variable
- **huly-issues**: Requires Huly credentials in `.env` file
- **agent-browser**: Requires [agent-browser](https://github.com/anthropics/agent-browser) CLI installed

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)

## License

[CC BY-NC 4.0](LICENSE) - You may share and adapt with attribution. Commercial use requires prior consent.
