"""PostToolUse hook (Edit|Write): read the edited file back and nudge on house rules.

The edit has already happened, so this is feedback, not a block: exit 2 with a short stderr list
(Claude Code shows it to Claude), exit 0 when there is nothing to say. Any unexpected error exits 0.

Paths are matched relative to the project root ($CLAUDE_PROJECT_DIR, else the payload's cwd).
Decision letters refer to CLAUDE.md and .claude/skills/project-map/decisions.md.

Nudges:
  (g) tanksim.py edited, or the viewer's ENGINE block edited: mirror the rule in the other engine,
      extend tests/parity.py, run the gate.
  (f) a Config field in tanksim.py defaulting to True (new rules must be off by default).
  (b)(d) Math.random or random. inside the viewer's ENGINE block / tanksim.play.
  experiments*.py without a pass line in its docstring.
  docs/RULES-* or docs/PLAN-* edited: tell the owner to sync the claude.ai Project copy.
  public repo: an email address in an edited file (other than noreply@anthropic.com).
"""
import json
import os
import re
import sys

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOWED_EMAILS = {"noreply@anthropic.com"}
CONFIG_TRUE = re.compile(r"^\s{4}([a-z_]+):\s*bool\s*=\s*True\b", re.M)


def rel(path, root):
    p = os.path.abspath(path).replace("\\", "/")
    r = os.path.abspath(root).replace("\\", "/").rstrip("/") + "/"
    if not p.lower().startswith(r.lower()):
        return None
    return p[len(r):].lower()


def engine_block(text):
    a = text.find("// ==== ENGINE START")
    b = text.find("// ==== ENGINE END", a + 1)
    return (a, b) if a >= 0 and b > a else (None, None)


def main():
    data = json.load(sys.stdin)
    ti = data.get("tool_input") or {}
    path = ti.get("file_path")
    if not path:
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    r = rel(path, root)
    if r is None or not os.path.isfile(path):
        return 0
    text = open(path, encoding="utf-8", errors="replace").read()
    edited = ti.get("new_string") or ti.get("content") or ""
    hits = []

    if r == "tanksim.py":
        hits.append("(g) tanksim.py changed: if a rule path moved, mirror it in the viewer's ENGINE block in this "
                    "change, extend tests/parity.py (mode + COVER count), and run the gate (CLAUDE.md Commands).")
        cfg = text[text.find("class Config"):text.find("def grid", text.find("class Config"))]
        for name in CONFIG_TRUE.findall(cfg):
            hits.append(f"(f) Config.{name} defaults to True; new rules must be off by default so older rule sets "
                        "keep their behaviour (python tests/fingerprints.py).")
        play = text[text.find("def play("):text.find("def replay(")]
        if re.search(r"\brandom\.(random|randrange|choice|shuffle|randint)\(", play) and "srng" not in edited:
            hits.append("(d) a random call inside play(): nothing random may happen during a running round.")

    if r == "tank-match-viewer.html":
        a, b = engine_block(text)
        if a is not None:
            pos = text.find(edited) if edited and len(edited) < 20000 else -1
            if pos == -1 or a <= pos <= b:
                hits.append("(g) the viewer's ENGINE block may have changed: mirror the rule in tanksim.py in this "
                            "change and run the gate (CLAUDE.md Commands).")
            if "Math.random" in text[a:b]:
                hits.append("(d) Math.random inside the ENGINE block: randomness belongs in UI code (deal, layouts, "
                            "pickups), never in a running round.")

    if re.fullmatch(r"experiments\d*\.py", r):
        doc = text[:3000].lower()
        if "pass" not in doc:
            hits.append("experiments: write the pass line in the docstring before the run "
                        "(.claude/skills/experiment-method/SKILL.md).")

    if r.startswith("docs/rules-") or r.startswith("docs/plan-") or r.startswith("docs/tanks-"):
        hits.append("docs: this doc has a copy in the owner's claude.ai Project; say in the hand-back that it "
                    "changed so the owner can sync it.")

    for m in set(EMAIL.findall(edited)):
        if m.lower() not in ALLOWED_EMAILS:
            hits.append(f"public repo: an email address ({m}) was written; keep personal data out of the repo.")
            break

    if hits:
        print("\n".join("- " + h for h in hits[:5]), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
