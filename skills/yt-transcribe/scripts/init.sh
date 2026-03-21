#!/usr/bin/env bash
set -euo pipefail

# yt-transcribe dependency installer
# Detects platform, checks what's installed, installs what's missing.
# Idempotent — safe to run multiple times.

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALLED=()
SKIPPED=()
WARNINGS=()

log() { echo "[yt-transcribe init] $1"; }
ok()  { log "✓ $1"; }
warn() { WARNINGS+=("$1"); log "⚠ $1"; }

command_exists() { command -v "$1" &>/dev/null; }

PLATFORM="$(uname -s)"
ARCH="$(uname -m)"

log "Platform: $PLATFORM ($ARCH)"
echo ""

# --- ffmpeg ---
if command_exists ffmpeg; then
    ok "ffmpeg already installed"
    SKIPPED+=("ffmpeg")
else
    if [[ "$PLATFORM" == "Darwin" ]]; then
        if command_exists brew; then
            log "Installing ffmpeg via Homebrew..."
            brew install ffmpeg
            INSTALLED+=("ffmpeg")
        else
            warn "Homebrew not found. Install ffmpeg manually: https://ffmpeg.org"
        fi
    else
        if command_exists apt-get; then
            log "Installing ffmpeg via apt..."
            sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg
            INSTALLED+=("ffmpeg")
        elif command_exists dnf; then
            log "Installing ffmpeg via dnf..."
            sudo dnf install -y ffmpeg
            INSTALLED+=("ffmpeg")
        elif command_exists pacman; then
            log "Installing ffmpeg via pacman..."
            sudo pacman -S --noconfirm ffmpeg
            INSTALLED+=("ffmpeg")
        else
            warn "Could not detect package manager. Install ffmpeg manually."
        fi
    fi
fi

# --- yt-dlp ---
if command_exists yt-dlp; then
    ok "yt-dlp already installed"
    SKIPPED+=("yt-dlp")
else
    if [[ "$PLATFORM" == "Darwin" ]] && command_exists brew; then
        log "Installing yt-dlp via Homebrew..."
        brew install yt-dlp
        INSTALLED+=("yt-dlp")
    else
        log "Installing yt-dlp via pip..."
        pip install yt-dlp
        INSTALLED+=("yt-dlp")
    fi
fi

# --- JavaScript runtime (needed by yt-dlp for YouTube) ---
if command_exists deno || command_exists node || command_exists bun; then
    ok "JavaScript runtime available ($(command_exists deno && echo deno || (command_exists node && echo node || echo bun)))"
    SKIPPED+=("js-runtime")
else
    if [[ "$PLATFORM" == "Darwin" ]] && command_exists brew; then
        log "Installing deno (required by yt-dlp for YouTube)..."
        brew install deno
        INSTALLED+=("deno")
    else
        warn "No JavaScript runtime found. yt-dlp needs deno/node/bun for YouTube."
        warn "Install one: https://deno.land or https://nodejs.org"
    fi
fi

# --- parakeet-mlx (macOS Apple Silicon only) ---
if [[ "$PLATFORM" == "Darwin" && "$ARCH" == "arm64" ]]; then
    if command_exists parakeet-mlx; then
        ok "parakeet-mlx already installed"
        SKIPPED+=("parakeet-mlx")
    else
        if command_exists uv; then
            log "Installing parakeet-mlx via uv..."
            uv tool install parakeet-mlx -U
            INSTALLED+=("parakeet-mlx")
        else
            log "Installing parakeet-mlx via pip..."
            pip install parakeet-mlx
            INSTALLED+=("parakeet-mlx")
        fi
        log "Note: First transcription will download ~1.2GB model from HuggingFace"
    fi
else
    log "Skipping parakeet-mlx (Apple Silicon only)"
    SKIPPED+=("parakeet-mlx")
fi

# --- AssemblyAI SDK ---
if python3 -c "import assemblyai" 2>/dev/null; then
    ok "assemblyai SDK already installed"
    SKIPPED+=("assemblyai")
else
    log "Installing assemblyai SDK..."
    pip install assemblyai
    INSTALLED+=("assemblyai")
fi

# --- python-dotenv ---
if python3 -c "import dotenv" 2>/dev/null; then
    ok "python-dotenv already installed"
    SKIPPED+=("python-dotenv")
else
    log "Installing python-dotenv..."
    pip install python-dotenv
    INSTALLED+=("python-dotenv")
fi

# --- API key check ---
echo ""
ENV_FILE="$SKILL_DIR/.env"
if [[ -f "$ENV_FILE" ]] && grep -q "ASSEMBLYAI_API_KEY=" "$ENV_FILE" && ! grep -q "your-api-key-here" "$ENV_FILE"; then
    ok "AssemblyAI API key configured"
else
    if [[ "$PLATFORM" != "Darwin" || "$ARCH" != "arm64" ]]; then
        warn "ASSEMBLYAI_API_KEY not set — required on this platform (no local transcription available)"
    else
        log "AssemblyAI API key not set (optional on Apple Silicon, required for podcast diarization)"
    fi
    log "To configure: copy $SKILL_DIR/.env.example to $SKILL_DIR/.env and add your key"
    log "Get a key at https://www.assemblyai.com/ (\$50 free credits)"
fi

# --- Summary ---
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Setup complete"
if [[ ${#INSTALLED[@]} -gt 0 ]]; then
    log "Installed: ${INSTALLED[*]}"
fi
if [[ ${#SKIPPED[@]} -gt 0 ]]; then
    log "Already present: ${SKIPPED[*]}"
fi
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    log "Warnings:"
    for w in "${WARNINGS[@]}"; do
        log "  ⚠ $w"
    done
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
