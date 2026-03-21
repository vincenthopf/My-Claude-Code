#!/usr/bin/env python3
"""YouTube video transcription pipeline.

Downloads audio via yt-dlp, auto-detects podcast content,
and routes to parakeet-mlx (local) or AssemblyAI (diarization).

All progress/decisions go to stderr. Only the output file path goes to stdout.
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path


# --- Podcast detection ---

PODCAST_STRONG_KEYWORDS = {"podcast", "episode", "ep."}
PODCAST_WEAK_KEYWORDS = {
    "interview", "conversation", "feat.", "ft.", "guest",
    "hosted by", "co-host", "panel", "roundtable", "q&a",
}
PODCAST_CATEGORIES = {"People & Blogs", "Education"}
PODCAST_THRESHOLD = 3
PODCAST_DURATION_THRESHOLD = 1200  # 20 minutes


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def find_env_file() -> Path | None:
    """Check skill dir .env, then cwd .env, then home .env."""
    candidates = [
        Path(__file__).resolve().parent.parent / ".env",
        Path.cwd() / ".env",
        Path.home() / ".env",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def load_env() -> None:
    """Load .env file into os.environ."""
    env_file = find_env_file()
    if not env_file:
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        # Manual fallback
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def check_command(cmd: str) -> bool:
    """Check if a command is available on PATH."""
    try:
        subprocess.run(
            ["which", cmd], capture_output=True, check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_dependencies(backend: str) -> None:
    """Verify required tools are installed."""
    missing = []
    for cmd in ("yt-dlp", "ffmpeg"):
        if not check_command(cmd):
            missing.append(cmd)

    if backend == "local" and not check_command("parakeet-mlx"):
        missing.append("parakeet-mlx")

    if missing:
        log(f"Error: Missing dependencies: {', '.join(missing)}")
        log("Run the init script first: bash <skill-dir>/scripts/init.sh")
        sys.exit(1)


def get_metadata(url: str) -> dict:
    """Fetch video metadata via yt-dlp without downloading."""
    log("Fetching video metadata...")
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-warnings", url],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            log(f"Error: yt-dlp metadata fetch failed:\n{result.stderr.strip()}")
            sys.exit(2)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        log("Error: Metadata fetch timed out after 60s")
        sys.exit(2)
    except json.JSONDecodeError:
        log("Error: Could not parse yt-dlp metadata output")
        sys.exit(2)


def is_podcast(metadata: dict) -> tuple[bool, int, list[str]]:
    """Score-based podcast detection. Returns (is_podcast, score, reasons)."""
    score = 0
    reasons = []

    title = metadata.get("title", "").lower()
    description = metadata.get("description", "").lower()
    tags = [t.lower() for t in metadata.get("tags", []) or []]
    channel = metadata.get("channel", "").lower()
    category = metadata.get("categories", [None])[0] if metadata.get("categories") else None
    duration = metadata.get("duration", 0) or 0

    searchable = f"{title} {description} {' '.join(tags)}"

    # Strong keywords (+2 each)
    for kw in PODCAST_STRONG_KEYWORDS:
        if kw in searchable:
            score += 2
            reasons.append(f'"{kw}" found in metadata (+2)')
            break  # Only count once for the strong group

    # Weak keywords (+1 each, max +2)
    weak_hits = 0
    for kw in PODCAST_WEAK_KEYWORDS:
        if kw in searchable and weak_hits < 2:
            score += 1
            weak_hits += 1
            reasons.append(f'"{kw}" found in metadata (+1)')

    # Category
    if category and category in PODCAST_CATEGORIES:
        score += 1
        reasons.append(f'category "{category}" (+1)')

    # Duration
    if duration > PODCAST_DURATION_THRESHOLD:
        score += 1
        mins = duration // 60
        reasons.append(f"duration {mins}min > 20min threshold (+1)")

    # Channel name
    if "podcast" in channel:
        score += 1
        reasons.append(f'channel name contains "podcast" (+1)')

    detected = score >= PODCAST_THRESHOLD
    return detected, score, reasons


def select_backend(
    metadata: dict,
    force_local: bool,
    force_diarize: bool,
) -> str:
    """Decide which transcription backend to use."""
    is_mac = platform.system() == "Darwin"
    is_apple_silicon = is_mac and platform.machine() == "arm64"

    if force_local:
        if not is_apple_silicon:
            log("Error: --force-local requires Apple Silicon Mac (parakeet-mlx is MLX-only)")
            sys.exit(1)
        log("Backend: parakeet-mlx (forced via --force-local)")
        return "local"

    if force_diarize:
        api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
        if not api_key or api_key == "your-api-key-here":
            log("Error: --force-diarize requires ASSEMBLYAI_API_KEY")
            log("Set it in .env or run: export ASSEMBLYAI_API_KEY=your-key")
            sys.exit(4)
        log("Backend: AssemblyAI with diarization (forced via --force-diarize)")
        return "assemblyai"

    # Auto-detect
    detected, score, reasons = is_podcast(metadata)
    log(f"\nPodcast detection (score: {score}/{PODCAST_THRESHOLD} threshold):")
    if reasons:
        for r in reasons:
            log(f"  {r}")
    else:
        log("  No podcast signals detected")

    if not is_apple_silicon:
        log(f"\nBackend: AssemblyAI (not Apple Silicon — parakeet-mlx unavailable)")
        api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
        if not api_key or api_key == "your-api-key-here":
            log("Error: ASSEMBLYAI_API_KEY required on non-Apple-Silicon platforms")
            log("Set it in .env or run: export ASSEMBLYAI_API_KEY=your-key")
            sys.exit(4)
        return "assemblyai"

    if detected:
        api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
        if not api_key or api_key == "your-api-key-here":
            log(f"\nPodcast detected but no ASSEMBLYAI_API_KEY set.")
            log("Falling back to parakeet-mlx (no speaker diarization)")
            return "local"
        log(f"\nBackend: AssemblyAI with diarization (podcast detected)")
        return "assemblyai"

    log(f"\nBackend: parakeet-mlx (non-podcast, local transcription)")
    return "local"


def download_audio(url: str, output_dir: Path) -> Path:
    """Download audio from YouTube URL via yt-dlp."""
    output_dir.mkdir(parents=True, exist_ok=True)

    log("\nDownloading audio...")
    result = subprocess.run(
        [
            "yt-dlp",
            "-x", "--audio-format", "mp3", "--audio-quality", "5",
            "-o", str(output_dir / "%(title).200B.%(ext)s"),
            "--print", "after_move:filepath",
            "--no-warnings",
            url,
        ],
        capture_output=True, text=True, timeout=600,
    )

    if result.returncode != 0:
        log(f"Error: Audio download failed:\n{result.stderr.strip()}")
        sys.exit(2)

    filepath = result.stdout.strip().splitlines()[-1]
    audio_path = Path(filepath)

    if not audio_path.exists():
        log(f"Error: Expected audio file not found at {audio_path}")
        sys.exit(2)

    log(f"Audio saved: {audio_path.name}")
    return audio_path


def transcribe_local(audio_path: Path, output_format: str) -> Path:
    """Transcribe using parakeet-mlx (local, Apple Silicon)."""
    log(f"\nTranscribing with parakeet-mlx ({output_format} format)...")
    output_dir = audio_path.parent

    result = subprocess.run(
        [
            "parakeet-mlx", str(audio_path),
            "--output-format", output_format,
            "--output-dir", str(output_dir),
        ],
        capture_output=True, text=True, timeout=1800,  # 30min timeout
    )

    if result.returncode != 0:
        log(f"Error: parakeet-mlx failed:\n{result.stderr.strip()}")
        sys.exit(3)

    # parakeet-mlx outputs to <filename>.<format>
    stem = audio_path.stem
    output_path = output_dir / f"{stem}.{output_format}"

    if not output_path.exists():
        # Try to find the output file
        candidates = list(output_dir.glob(f"{stem}.*"))
        candidates = [c for c in candidates if c.suffix != ".mp3"]
        if candidates:
            output_path = candidates[0]
        else:
            log("Error: Transcription output file not found")
            sys.exit(3)

    log(f"Transcription complete: {output_path.name}")
    return output_path


def transcribe_assemblyai(audio_path: Path, output_format: str) -> Path:
    """Transcribe using AssemblyAI with speaker diarization."""
    try:
        import assemblyai as aai
    except ImportError:
        log("Error: assemblyai package not installed")
        log("Run: pip install assemblyai")
        sys.exit(1)

    api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
    if not api_key or api_key == "your-api-key-here":
        log("Error: ASSEMBLYAI_API_KEY not set")
        sys.exit(4)

    aai.settings.api_key = api_key

    log(f"\nTranscribing with AssemblyAI (speaker diarization enabled)...")
    log("Uploading audio and processing...")

    config = aai.TranscriptionConfig(speaker_labels=True)
    transcript = aai.Transcriber().transcribe(str(audio_path), config=config)

    if transcript.status == aai.TranscriptStatus.error:
        log(f"Error: AssemblyAI transcription failed: {transcript.error}")
        sys.exit(3)

    # Write output
    output_dir = audio_path.parent
    stem = audio_path.stem

    if output_format == "json":
        output_path = output_dir / f"{stem}.json"
        utterances = []
        for u in transcript.utterances:
            utterances.append({
                "speaker": u.speaker,
                "text": u.text,
                "start": u.start,
                "end": u.end,
                "confidence": u.confidence,
            })
        with open(output_path, "w") as f:
            json.dump({"utterances": utterances, "text": transcript.text}, f, indent=2)

    elif output_format == "srt":
        output_path = output_dir / f"{stem}.srt"
        lines = []
        for i, u in enumerate(transcript.utterances, 1):
            start = _ms_to_srt_time(u.start)
            end = _ms_to_srt_time(u.end)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(f"[Speaker {u.speaker}] {u.text}")
            lines.append("")
        with open(output_path, "w") as f:
            f.write("\n".join(lines))

    elif output_format == "vtt":
        output_path = output_dir / f"{stem}.vtt"
        lines = ["WEBVTT", ""]
        for u in transcript.utterances:
            start = _ms_to_vtt_time(u.start)
            end = _ms_to_vtt_time(u.end)
            lines.append(f"{start} --> {end}")
            lines.append(f"[Speaker {u.speaker}] {u.text}")
            lines.append("")
        with open(output_path, "w") as f:
            f.write("\n".join(lines))

    else:  # txt
        output_path = output_dir / f"{stem}.txt"
        lines = []
        for u in transcript.utterances:
            lines.append(f"Speaker {u.speaker}: {u.text}")
        with open(output_path, "w") as f:
            f.write("\n\n".join(lines) + "\n")

    log(f"Transcription complete: {output_path.name}")
    return output_path


def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format."""
    s, ms_rem = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms_rem:03d}"


def _ms_to_vtt_time(ms: int) -> str:
    """Convert milliseconds to VTT timestamp format."""
    s, ms_rem = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms_rem:03d}"


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe YouTube videos with smart backend routing"
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--format", "-f", default="txt",
        choices=["txt", "srt", "vtt", "json"],
        help="Output format (default: txt)"
    )
    parser.add_argument(
        "--output-dir", "-o", default="./yt-transcripts",
        help="Output directory (default: ./yt-transcripts)"
    )
    parser.add_argument(
        "--force-local", action="store_true",
        help="Force local transcription (parakeet-mlx, Apple Silicon only)"
    )
    parser.add_argument(
        "--force-diarize", action="store_true",
        help="Force AssemblyAI with speaker diarization"
    )
    parser.add_argument(
        "--keep-audio", action="store_true",
        help="Keep the downloaded audio file after transcription"
    )
    args = parser.parse_args()

    load_env()

    output_dir = Path(args.output_dir)

    # Step 1: Fetch metadata
    metadata = get_metadata(args.url)
    title = metadata.get("title", "Unknown")
    duration = metadata.get("duration", 0) or 0
    log(f'\nVideo: "{title}" ({duration // 60}m {duration % 60}s)')

    # Step 2: Select backend
    backend = select_backend(metadata, args.force_local, args.force_diarize)
    check_dependencies(backend)

    # Step 3: Download audio
    audio_path = download_audio(args.url, output_dir)

    # Step 4: Transcribe
    if backend == "local":
        output_path = transcribe_local(audio_path, args.format)
    else:
        output_path = transcribe_assemblyai(audio_path, args.format)

    # Step 5: Cleanup
    if not args.keep_audio and audio_path.exists():
        audio_path.unlink()
        log("Audio file cleaned up")

    # Print output path to stdout (for Claude to capture)
    print(str(output_path))


if __name__ == "__main__":
    main()
