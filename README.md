# My Claude Code

Personal collection of workflows, skills, plugins, and configurations for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Structure

```
.
├── workflow/             # Five-stage development workflow system
│   ├── CLAUDE.md         # Entry point — workflow stages + principles reference
│   ├── principles.md     # Global principles governing all decisions
│   ├── agents/           # 8 specialized agents (critics, synthesizers, verifiers)
│   └── skills/           # 5 workflow skills (problem-def, design, planning, impl, debug)
├── skills/               # Standalone skills (not part of the workflow)
├── plugins/              # Full plugins with hooks, scripts, and commands
├── commands/             # Slash commands for common workflows
└── settings.json         # Claude Code configuration
```

## Workflow System

A five-stage, multi-model development pipeline. Problems are defined before solutions are proposed. Proposals are generated competitively and verified against principles, not documents.

| Stage | Skill | What It Does |
|-------|-------|-------------|
| 1. Problem Definition | `/problem-definition` | Frame the problem. Three review agents attack the framing in parallel. |
| 2. Design | `/design` | Explore solution space. Codex X-High evaluates approaches. User picks direction. |
| 3. Planning | `/planning` | Two Codex High agents propose independently. Opus synthesizes. User approves. |
| 4. Implementation | `/implementation` | Sub-agents build in parallel. Opus verifies each against problem + principles. |
| 5. Debugging | `/debugging` | RCA → dual proposal (Opus + Codex) → synthesis → alignment → implement. |

### Model Routing

| Role | Model | Why |
|------|-------|-----|
| Research validation | Codex X-High (via pi) | Analytical rigor, gap detection |
| Approach evaluation | Codex X-High (via pi) | Tradeoff analysis |
| Proposal generation | Codex High x2 (via pi) | Strategy across problem space |
| Synthesis & alignment | Opus | Intent understanding, judgment |
| Verification | Opus | Divergence evaluation |
| Implementation | Claude sub-agents | Tool access, codebase interaction |

### Agents

| Agent | Model | Role |
|-------|-------|------|
| `definition-critic` | Opus | Attacks problem definitions |
| `context-analyst` | Opus | Maps landscape around a problem |
| `assumptions-auditor` | Opus | Surfaces invisible assumptions |
| `proposal-synthesizer` | Opus | Selects best proposal, justifies choices |
| `research-validator` | Codex X-High | Evaluates research quality, directs follow-up |
| `approach-evaluator` | Codex X-High | Compares solution approaches rigorously |
| `build-verifier` | Opus | Runs tests, generates adversarial cases, gates on execution |
| `integration-checker` | Opus | Verifies parallel-built pieces fit together |

### Key Design Decisions

- **Proposal as compass, not contract.** Implementation agents have latitude. Verify against the problem, not the document.
- **Select, don't merge.** The synthesizer picks the better proposal as a base. Merging is the exception.
- **Verify by executing.** Build verification runs tests and generates adversarial cases. Code review alone is rubber-stamping.
- **Scope through context, not personas.** Agent quality comes from controlling what context they receive, not from elaborate role descriptions.

## Standalone Skills

| Skill | Description |
|-------|-------------|
| **agent-browser** | Browser automation for web testing, form filling, screenshots |
| **deep-research** | Deep research using Parallel.ai API |
| **pi-agent** | Dispatch tasks to pi coding agent for cross-model work |
| **skill-creator** | Guided skill generation with validation |
| **skill-from-masters** | Create skills based on expert methodologies |
| **learnings** | Knowledge base with maturity pipeline: `[DRAFT]` → `[CONFIRMED]` → `[REGRESSION]` |
| **yt-transcribe** | YouTube transcription with smart model routing |

## Plugins

| Plugin | Description |
|--------|-------------|
| **[voice-mlx](plugins/voice-mlx/)** | Voice notifications, iTerm2 status, macOS alerts |

## Installation

```bash
# Copy the workflow system
cp workflow/CLAUDE.md ~/.claude/CLAUDE.md
cp workflow/principles.md ~/.claude/principles.md
cp -r workflow/agents/* ~/.claude/agents/
cp -r workflow/skills/* ~/.claude/skills/

# Copy a standalone skill
cp -r skills/agent-browser ~/.claude/skills/

# Install a plugin
cp -r plugins/voice-mlx ~/.claude/plugins/custom/voice-mlx
```

## Requirements

- **Workflow system**: Requires pi CLI (`npm install -g @mariozechner/pi-coding-agent`) for cross-model dispatch
- **deep-research**: Requires `PARALLEL_API_KEY`
- **agent-browser**: Requires [agent-browser](https://github.com/anthropics/agent-browser) CLI
- **voice-mlx**: Requires `edge-tts`, `ffplay`, `terminal-notifier`

## License

[CC BY-NC 4.0](LICENSE) - Share and adapt with attribution. Commercial use requires prior consent.
