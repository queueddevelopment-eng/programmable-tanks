"""PreToolUse hook (Edit|Write): block edits that must never be made by hand.

Receives the hook payload as JSON on stdin, for example:
    {"cwd": ..., "tool_name": "Edit", "tool_input": {"file_path": ..., "old_string": ..., "new_string": ...}}

Exit 2 blocks the tool call and feeds the one-line stderr message back to Claude; exit 0 allows it.
A broken hook must never block normal work, so any unexpected error exits 0.

Paths are matched relative to the project root ($CLAUDE_PROJECT_DIR, else the payload's cwd),
forward-slash and lowercased. Files outside the root are ignored. Decision letters refer to
CLAUDE.md and .claude/skills/project-map/decisions.md.

Rules:
  1. results/**             written by experiment runs only (rerun the experiment instead).
  2. tests/fingerprints.py  an existing expected fingerprint may never be changed or removed (f);
                            adding a new entry at an owner-declared freeze is allowed.
"""
import json
import os
import re
import sys

HASH = re.compile(r"\b[0-9a-f]{32}\b")


def rel(path, root):
    p = os.path.abspath(path).replace("\\", "/")
    r = os.path.abspath(root).replace("\\", "/").rstrip("/") + "/"
    if not p.lower().startswith(r.lower()):
        return None
    return p[len(r):].lower()


def main():
    data = json.load(sys.stdin)
    ti = data.get("tool_input") or {}
    path = ti.get("file_path")
    if not path:
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    r = rel(path, root)
    if r is None:
        return 0
    if r.startswith("results/"):
        print("results/ is written by experiment runs only; rerun the experiment "
              "(python experimentsN.py <N> <letters> > results/<file>.txt) instead of editing it.", file=sys.stderr)
        return 2
    if r == "tests/fingerprints.py":
        full = os.path.join(root, "tests", "fingerprints.py")
        old = open(full, encoding="utf-8").read() if os.path.isfile(full) else ""
        before = set(HASH.findall(old))
        if data.get("tool_name") == "Write":
            after = set(HASH.findall(ti.get("content") or ""))
        else:
            o, n = ti.get("old_string") or "", ti.get("new_string") or ""
            after = (before - set(HASH.findall(o))) | set(HASH.findall(n))
        if before - after:
            print("tests/fingerprints.py: an existing expected fingerprint would change or disappear. "
                  "Never edit EXPECTED to make a check pass (decision f); a FAIL means a new rule leaked "
                  "into old behaviour. New entries are added only at an owner-declared freeze.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
