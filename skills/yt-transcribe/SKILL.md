---
name: yt-transcribe
description: >
  Transcribe YouTube videos with high accuracy. Downloads audio via yt-dlp and
  auto-routes to parakeet-mlx (local, Apple Silicon) or AssemblyAI (speaker
  diarization for podcasts). Use when the user asks to transcribe a YouTube video,
  get a transcript from a YouTube URL, or extract text from a YouTube link.
  Also triggered by /yt-transcribe command.
---

# YouTube Transcription

Transcribe YouTube videos via `scripts/transcribe.py`. Auto-detects podcasts and routes to the appropriate backend.

## First-Time Setup

Run the init script once on a new machine:

```bash
bash <skill-dir>/scripts/init.sh
```

This installs ffmpeg, yt-dlp, parakeet-mlx (Mac only), and the AssemblyAI SDK. For podcast diarization or Linux usage, copy `.env.example` to `.env` and add an AssemblyAI API key.

## Usage

```bash
python3 <skill-dir>/scripts/transcribe.py "YOUTUBE_URL" [options]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--format`, `-f` | `txt` | Output: `txt`, `srt`, `vtt`, `json` |
| `--output-dir`, `-o` | `./yt-transcripts` | Where to save output |
| `--force-local` | off | Force parakeet-mlx (Apple Silicon only) |
| `--force-diarize` | off | Force AssemblyAI with speaker labels |
| `--keep-audio` | off | Keep the downloaded mp3 |

## Workflow

1. Run the script with the YouTube URL. For videos over 30 minutes, run in background.
2. The script prints the output file path to stdout.
3. Read the transcript file and present or summarize as the user requests.

## Backend Routing

| Platform | Non-podcast | Podcast |
|----------|-------------|---------|
| Mac (Apple Silicon) | parakeet-mlx (local) | AssemblyAI (diarization) |
| Linux | AssemblyAI | AssemblyAI (diarization) |

Podcast detection uses metadata heuristics (keywords, category, duration, channel name). If AssemblyAI is needed but no API key is set, falls back to parakeet-mlx on Mac.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Missing dependency |
| 2 | Download failure |
| 3 | Transcription failure |
| 4 | Missing AssemblyAI API key |
