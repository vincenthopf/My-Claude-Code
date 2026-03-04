---
allowed-tools: Bash, Read, Write, Edit
arguments: voice
---
Enable, disable, or configure voice feedback.

**Commands:**
- `/speak` - Enable voice feedback with current voice
- `/speak <voice>` - Set voice (any edge-tts voice ID, e.g. en-AU-WilliamNeural) and enable
- `/speak stop` - Disable voice feedback
- `/speak prompt <text>` - Set custom instruction for voice summaries
- `/speak prompt` - Clear custom prompt
- `/speak voices` - List popular voice options

**Config file:** `~/.claude/voice.local.md`

```yaml
---
voice: en-AU-WilliamNeural
enabled: true
notifications: true
prompt: "always end with 'peace out'"
---
```

**Behavior:**
- When no argument: Set `enabled: true` and tell user:
  "Voice feedback enabled. Use `/speak stop` to disable, or `/speak <name>` to change voice."
- When voice name given: Set `voice: <name>` and `enabled: true`, tell user:
  "Voice set to <name> and enabled. Use `/speak stop` to disable."
- When `stop`: Set `enabled: false` AND `just_disabled: true` (voice unchanged), tell user:
  "Voice feedback disabled. Use `/speak` to re-enable."
- When `prompt <text>`: Set `prompt: <text>`, tell user:
  "Custom prompt set: <text>"
- When `prompt` (no text): Clear the prompt field, tell user:
  "Custom prompt cleared."
- When `voices`: List these popular options:
  - en-AU-WilliamNeural (Australian male) — default
  - en-AU-NatashaNeural (Australian female)
  - en-GB-RyanNeural (British male)
  - en-IE-ConnorNeural (Irish male)
  - en-NZ-MitchellNeural (New Zealand male)
  - Run `edge-tts --list-voices` for the full list.

Create the config file if it doesn't exist (default voice: en-AU-WilliamNeural).
