#!/usr/bin/env python3
"""PostToolUse hook - inject brief voice reminder after tool calls."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_common import get_voice_config, build_short_reminder


def main():
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "approve"}))
        return

    print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    main()
