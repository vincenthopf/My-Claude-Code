#!/usr/bin/env python3
"""
Parallel AI Deep Research Script

Submits a deep research query to the Parallel Task API, streams progress via SSE,
and writes the final result to a markdown file — all without loading results into
the caller's context window.

Exit codes:
  0 = success
  1 = auth error (missing or invalid API key)
  2 = API error (bad request, rate limit, server error)
  3 = timeout (task did not complete within max wait)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://api.parallel.ai"
SSE_BETA = "events-sse-2025-07-24"
MAX_POLL_WAIT = 5400  # 90 minutes (ultra8x can take up to 2h, but be reasonable)
POLL_INTERVAL = 10

PROCESSORS = [
    "lite", "base", "core", "core2x", "pro", "ultra",
    "ultra2x", "ultra4x", "ultra8x",
    "lite-fast", "base-fast", "core-fast", "core2x-fast",
    "pro-fast", "ultra-fast", "ultra2x-fast", "ultra4x-fast", "ultra8x-fast",
]


def get_api_key():
    key = os.environ.get("PARALLEL_API_KEY")
    if not key:
        # Look for .env file in the skill directory (one level up from scripts/)
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "PARALLEL_API_KEY":
                    key = v.strip()
                    break
    if not key:
        print("ERROR: PARALLEL_API_KEY not found in environment or .env file.", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(method, path, api_key, body=None, headers=None):
    url = f"{API_BASE}{path}"
    hdrs = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    if headers:
        hdrs.update(headers)

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            err_body = json.loads(e.read().decode())
        except Exception:
            err_body = {"error": {"message": str(e)}}

        if status == 401:
            print(f"ERROR: Authentication failed (401). Check your API key.", file=sys.stderr)
            sys.exit(1)
        elif status == 429:
            print(f"ERROR: Rate limited (429). Try again later.", file=sys.stderr)
            sys.exit(2)
        else:
            msg = err_body.get("error", {}).get("message", str(e))
            print(f"ERROR: API returned {status}: {msg}", file=sys.stderr)
            sys.exit(2)
    except urllib.error.URLError as e:
        print(f"ERROR: Network error: {e.reason}", file=sys.stderr)
        sys.exit(2)


def create_task(api_key, query, processor):
    body = {
        "processor": processor,
        "input": query,
        "enable_events": True,
    }
    return api_request("POST", "/v1/tasks/runs", api_key, body=body,
                       headers={"parallel-beta": SSE_BETA})


SSE_CONNECT_TIMEOUT = 600  # Just above server's 570s auto-close
SSE_MAX_RECONNECTS = 25    # ~4 hours of coverage


def stream_sse(api_key, run_id):
    """Stream SSE progress with automatic reconnection. Returns final output or None."""
    url = f"{API_BASE}/v1beta/tasks/runs/{run_id}/events"
    seen_events = set()
    final_output = None

    for attempt in range(SSE_MAX_RECONNECTS):
        if attempt > 0:
            print(f"  [sse] Reconnecting (attempt {attempt + 1})...", file=sys.stderr)

        req = urllib.request.Request(url, headers={
            "x-api-key": api_key,
            "Accept": "text/event-stream",
            "parallel-beta": SSE_BETA,
        })

        try:
            resp = urllib.request.urlopen(req, timeout=SSE_CONNECT_TIMEOUT)
        except Exception as e:
            if attempt == 0:
                print(f"SSE connection failed, falling back to polling: {e}", file=sys.stderr)
            else:
                print(f"SSE reconnection failed, falling back to polling: {e}", file=sys.stderr)
            return None

        got_terminal = False
        try:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")
                if not line.startswith("data: "):
                    continue
                try:
                    event = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue

                etype = event.get("type", "")

                if etype == "task_run.progress_msg.exec_status":
                    msg = event.get("message", "")
                    key = ("progress_msg", msg)
                    if key not in seen_events:
                        seen_events.add(key)
                        print(f"  [progress] {msg}", file=sys.stderr)

                elif etype == "task_run.progress_stats":
                    meter = event.get("progress_meter", "")
                    key = ("progress_stats", str(meter))
                    if key not in seen_events:
                        seen_events.add(key)
                        stats = event.get("source_stats", {})
                        read = stats.get("num_sources_read", 0)
                        print(f"  [progress] {meter}% — {read} sources read", file=sys.stderr)

                elif etype == "task_run.state":
                    run = event.get("run", {})
                    status = run.get("status", "")
                    if status == "completed":
                        final_output = event.get("output")
                        got_terminal = True
                        break
                    elif status == "failed":
                        err = run.get("error", {})
                        print(f"ERROR: Task failed: {err}", file=sys.stderr)
                        sys.exit(2)

                elif etype == "error":
                    print(f"ERROR: SSE error: {event.get('message', '')}", file=sys.stderr)
                    return None
        except Exception as e:
            print(f"  [sse] Stream ended: {e}", file=sys.stderr)
        finally:
            resp.close()

        if got_terminal:
            return final_output
        # Stream ended without terminal state — reconnect

    print("  [sse] Max reconnection attempts reached, falling back to polling.", file=sys.stderr)
    return None


def poll_until_complete(api_key, run_id):
    """Poll the task status until completion."""
    start = time.time()
    while time.time() - start < MAX_POLL_WAIT:
        result = api_request("GET", f"/v1/tasks/runs/{run_id}", api_key)
        status = result.get("status", "")
        print(f"  [poll] status={status}", file=sys.stderr)

        if status == "completed":
            result = api_request("GET", f"/v1/tasks/runs/{run_id}/result", api_key)
            return result.get("output")
        elif status == "failed":
            err = result.get("error", {})
            print(f"ERROR: Task failed: {err}", file=sys.stderr)
            sys.exit(2)
        elif status == "cancelled":
            print("ERROR: Task was cancelled.", file=sys.stderr)
            sys.exit(2)

        time.sleep(POLL_INTERVAL)

    print("ERROR: Task timed out.", file=sys.stderr)
    sys.exit(3)


def format_dict_as_table(items):
    """Render a list of dicts as a markdown table. Returns lines."""
    if not items:
        return []
    # Collect all keys in order of appearance
    keys = []
    for item in items:
        for k in item:
            if k not in keys:
                keys.append(k)
    # Build table
    headers = [k.replace("_", " ").title() for k in keys]
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in keys) + " |")
    for item in items:
        row = []
        for k in keys:
            val = item.get(k, "")
            # Flatten to single line for table cell
            cell = str(val).replace("\n", " ").replace("|", "\\|")
            row.append(cell)
        lines.append("| " + " | ".join(row) + " |")
    return lines


def format_single_dict(d):
    """Render a single dict as a key-value list. Returns lines."""
    lines = []
    for k, v in d.items():
        label = k.replace("_", " ").title()
        val = str(v).replace("\n", " ")
        lines.append(f"**{label}:** {val}")
        lines.append("")
    return lines


def format_markdown(query, processor, run_id, output_data, created_at, include_basis=True):
    """Format the research output as markdown with frontmatter."""
    lines = []

    # Frontmatter
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append("---")
    lines.append(f"query: \"{query}\"")
    lines.append(f"processor: {processor}")
    lines.append(f"run_id: {run_id}")
    lines.append(f"created_at: {created_at}")
    lines.append(f"retrieved_at: {now}")
    lines.append("---")
    lines.append("")

    # Title
    lines.append(f"# Research: {query}")
    lines.append("")

    if output_data is None:
        lines.append("*No output returned.*")
        return "\n".join(lines)

    content = output_data.get("content")
    basis = output_data.get("basis", [])

    # Content section
    if isinstance(content, str):
        lines.append(content)
    elif isinstance(content, dict):
        lines.append("## Findings")
        lines.append("")
        for key, value in content.items():
            lines.append(f"### {key.replace('_', ' ').title()}")
            lines.append("")
            if isinstance(value, str):
                lines.append(value)
            elif isinstance(value, list):
                # Check if all items are dicts — render as table
                if value and all(isinstance(item, dict) for item in value):
                    lines.extend(format_dict_as_table(value))
                else:
                    for item in value:
                        if isinstance(item, dict):
                            lines.extend(format_single_dict(item))
                        else:
                            lines.append(f"- {item}")
            elif isinstance(value, dict):
                lines.extend(format_single_dict(value))
            else:
                lines.append(str(value))
            lines.append("")
    else:
        lines.append(str(content))

    # Citations section
    if include_basis and basis:
        lines.append("")
        lines.append("## Research Basis")
        lines.append("")
        for entry in basis:
            field = entry.get("field", "unknown")
            reasoning = entry.get("reasoning", "")
            confidence = entry.get("confidence", "")
            citations = entry.get("citations", [])

            lines.append(f"### {field}")
            if confidence:
                lines.append(f"**Confidence:** {confidence}")
            if reasoning:
                lines.append(f"\n{reasoning}")
            if citations:
                lines.append("")
                for cite in citations:
                    url = cite.get("url", "")
                    title = cite.get("title", url)
                    excerpts = cite.get("excerpts", [])
                    lines.append(f"- [{title}]({url})")
                    for exc in excerpts:
                        lines.append(f"  > {exc}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run a Parallel AI deep research task")
    parser.add_argument("--query", "-q", required=True, help="The research question")
    parser.add_argument("--output", "-o", required=True, help="Output markdown file path")
    parser.add_argument("--processor", "-p", default="pro", choices=PROCESSORS,
                        help="Processor tier (default: pro)")
    parser.add_argument("--no-basis", action="store_true",
                        help="Exclude the Research Basis section (citations and reasoning)")
    args = parser.parse_args()

    api_key = get_api_key()

    # Ensure output directory exists
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the task
    print(f"Submitting research task (processor={args.processor})...", file=sys.stderr)
    task = create_task(api_key, args.query, args.processor)
    run_id = task["run_id"]
    created_at = task.get("created_at", "")
    print(f"Task created: {run_id}", file=sys.stderr)

    # Try SSE first, fall back to polling
    print("Streaming progress...", file=sys.stderr)
    output = stream_sse(api_key, run_id)

    if output is None:
        print("Polling for result...", file=sys.stderr)
        output = poll_until_complete(api_key, run_id)

    # Write markdown
    md = format_markdown(args.query, args.processor, run_id, output, created_at,
                         include_basis=not args.no_basis)
    out_path.write_text(md, encoding="utf-8")
    print(f"Research written to: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
