#!/usr/bin/env python3
"""PostToolUse hook - placeholder for post-tool-use processing."""

import json
import sys


def main():
    try:
        json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "approve"}))
        return

    print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    main()
