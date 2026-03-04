# Voice MLX Plugin

Voice notifications and terminal status for Claude Code on macOS. Speaks summaries aloud using edge-tts (Microsoft neural voices) and sets iTerm2 per-pane title bars to show session status.

## Features

- **Voice notifications**: Speaks when Claude finishes, needs permission, or has a question
- **Terminal status**: Sets iTerm2 pane titles showing status (WORKING, DONE, PERMISSION, QUESTION, ATTENTION)
- **LLM-powered titles**: Uses Inception Labs Mercury-2 API for concise, descriptive titles
- **Banner alerts**: macOS notifications via terminal-notifier with click-to-focus
- **Audio locking**: Prevents overlapping speech from multiple sessions
- **Markdown stripping**: Strips formatting characters so TTS reads naturally

## Requirements

- macOS with iTerm2
- `edge-tts` — `pip install edge-tts` (or `uv add edge-tts`)
- `ffplay` — from ffmpeg (`brew install ffmpeg`)
- `terminal-notifier` — `brew install terminal-notifier`
- Python 3.10+
- (Optional) `iterm2` Python package for click-to-focus notifications
- (Optional) Inception Labs API key for Mercury-2 powered titles

## Installation

Copy the plugin to your Claude Code plugins directory:

```bash
cp -r plugins/voice-mlx ~/.claude/plugins/custom/voice-mlx
```

Or symlink:

```bash
ln -s "$(pwd)/plugins/voice-mlx" ~/.claude/plugins/custom/voice-mlx
```

### Terminal Status Setup

To prevent Claude Code from overriding pane titles:

```bash
echo 'export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1' >> ~/.zshrc
```

Enable per-pane title bars in iTerm2:
**Settings → Appearance → Panes → Show per-pane title bar with split panes**

### Mercury API (Optional)

For LLM-generated titles instead of keyword extraction:

```bash
echo 'your-api-key' > ~/.claude/inception_api_key
chmod 600 ~/.claude/inception_api_key
```

Get a key from [Inception Labs](https://www.inceptionlabs.ai/).

## Commands

- `/speak` — Enable voice feedback
- `/speak stop` — Disable voice feedback
- `/speak <voice>` — Change voice (e.g., `en-GB-RyanNeural`)
- `/speak voices` — List available voices
- `/speak prompt <text>` — Set custom voice instruction

## Configuration

Edit `~/.claude/voice.local.md`:

```yaml
---
voice: en-AU-WilliamNeural
enabled: true
notifications: true
prompt: "keep summaries casual"
---
```

## How It Works

| Hook | Status | What Happens |
|------|--------|-------------|
| UserPromptSubmit | `WORKING...` | Sets pane title with Mercury-generated task summary |
| Stop | `DONE` | Sets completion summary, speaks result |
| Notification (permission) | `PERMISSION` | Sets title, speaks what permission is needed |
| Notification (question) | `QUESTION` | Sets title, speaks the question |
| Notification (idle) | — | Preserves previous status (agents may still run) |

Title shows the summary text (e.g., `Debug auth token refresh in login API`). Status is conveyed via tab color: blue = working, green = done, red = permission, yellow = question, orange = attention.
