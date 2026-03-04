---
name: voice-update
description: This skill should be used when the agent needs to give a spoken voice update to the user, or when reminded by a Stop hook to provide audio feedback. Use this skill to speak a short summary of what was accomplished.
---

# Voice Update Skill

When you need to give a spoken voice update, call the say script:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/say "your summary here"
```

Or with a specific voice:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/say --voice en-AU-WilliamNeural "your summary here"
```

## Guidelines

- Keep summaries to 1-2 sentences
- Be conversational, like you're speaking to them
- Match the user's tone — if they're casual, be casual
- NEVER include file paths, UUIDs, hashes, or technical identifiers
- Use natural language instead (e.g., "the config file" not "/Users/foo/bar/config.json")

## Notes

- Uses edge-tts (Microsoft neural voices) streamed via ffplay
- Default voice: en-AU-WilliamNeural (Australian male)
- Run `edge-tts --list-voices` for all available voices
