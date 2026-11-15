---
name: review-checklist
description: Programmable Tanks' ordered review checklist with runnable checks - both engines changed together, parity extended and green with coverage, default-off Config and fingerprints ok, locked decisions (a)-(n), experiment hygiene (pass line, paired seeds, results untouched), viewer separation, docs sync, and the public-repo rule. Loads on "review", "check this diff", "before commit", "is this ready".
when_to_use: Before any commit or push; when reviewing a diff, branch or PR.
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash(git status*), Bash(git diff*), Bash(git log*), Bash(python tests/parity.py*), Bash(python tests/fingerprints.py)
---

# Review checklist

Work through the items in order. `CLAUDE.md` wins; decision letters are in `project-map/decisions.md`.

1. **Both engines (g).** Did `tanksim.py` change in a rule path (`Config`, `Tank`, `_hit`, `_engage`, `_hunt_turn`, `play`, `validate`, `_skips`)? Then the ENGINE block of `tank-match-viewer.html` must change in the same diff, and the reverse.
   - Check: `git diff --stat` lists both files, or the change is provably engine-local (a comment, or experiment helpers).
   - Check: `git diff tank-match-viewer.html` hunks between `ENGINE START` and `ENGINE END` match the Python intent and order.
2. **Gate run and pasted.** All parity lines from CLAUDE.md print `0 mismatches`, and the new rule's coverage count is above 0. `python tests/fingerprints.py` prints all `ok`.
   - Missing output is blocking.
   - Coverage 0 means the rule wasn't tested: blocking.
3. **Locked decisions.**
   - (a) layouts or starts stay rotationally symmetric;
   - (b) no second card-language exception: grep `next_action` / `nextAction` for a new special case keyed on card kind;
   - (c) slots stay 8;
   - (d) no random draw inside `play` or `stepMatch` (`random`, `Math.random` in the ENGINE block);
   - (e) any change to the round or match structure touches the debug rule, so it's owner-decided.
   - Check: `grep -n "Math.random" tank-match-viewer.html` → only UI functions (`shuffle`, `placePickups`, `shuffledBoard`, `randProgram`, `mutateProg`, `deal`, `setMode`), never inside the ENGINE block.
4. **Default off (f).** Every new `Config` field defaults to the old behaviour. `EXPECTED` in `tests/fingerprints.py` is unchanged, unless this is an owner-declared freeze adding an entry (old entries untouched).
5. **Parity harness.** A new rule is set in a parity mode, passed into the JS rules object in the harness, and counted in `COVER`. Templates are added if random programs rarely reach it.
6. **Viewer separation.** No rule logic outside the ENGINE block (a branch on game state in `renderTanks` or `tickOnce` that changes an outcome is a finding). No UI code inside it. A new card has `CARDS` text, a log line in `describe` if it emits an event, and tooltip wording that matches the rules draft.
7. **Experiments.**
   - The docstring has the question, the variants and the pass line written before the run.
   - Seeds are paired across variants.
   - N is reported.
   - A results file exists for every quoted number, and `results/` was written by a run, not edited.
   - Any conclusion into the plan or notes carries N and the file.
8. **Docs sync.**
   - A rule change updates `docs/RULES-v0.5-draft.md` (card text, tick order, deck table).
   - A verdict updates `docs/PLAN-2026-11.md`.
   - A command change updates `README.md` and CLAUDE.md Commands.
   - A phase move updates CLAUDE.md Current phase.
   - A roster or skill change updates `.claude/README.md`.
   - The owner is told which docs to sync to the claude.ai Project.
9. **Public repo.** No email addresses, real names of playtesters, or anything from the owner's other projects in code, docs, commits or agent memory. Check: `git diff | grep -nE "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"` → only `noreply@anthropic.com` in commit trailers.
10. **Hygiene.** No `__pycache__`, no scratch scripts, no `.claude/settings.local.json` or `.claude/agent-memory-local/` staged. Commit message in `git-flow` form with the trailer.

**Blocking:** items 1–5, a hand-edited `results/` or `EXPECTED`, an unsourced number, personal data.
**Non-blocking:** wording, docstrings, a missing coverage count on a rule that visibly fired in the edge-case output.
