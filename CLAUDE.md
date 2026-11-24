# Programmable Tanks — Project Instructions

## What this project is
A physical tabletop game in the spirit of Robocode: each player builds a short program from cards (8 slots, the rail wraps), then two tanks run their programs autonomously on an 8×8 grid and fight. Phones stay away. Ages 14+. Eventual form: microcontroller tanks reading NFC cards, IR for shooting and detection. Current form: a Python rules simulator and a browser match viewer, used to tune the rules before any hardware exists.

The owner (Q) works on this at 10–15 hours a week. Build speed is not the bottleneck; design decisions and playtesting are.

- Rules of record: `docs/RULES-v0.5-draft.md` (duels only).
- Plan, decisions and experiment queue: `docs/PLAN-2026-11.md`.
- Every October experiment with numbers: `docs/TANKS-V03-V04-NOTES.md`.
- The owner also keeps a claude.ai Project ("Programmable Tanks") holding `TANKS-HANDOFF.md` (September, v0.2; the original spec of record, now superseded on rules by the v0.5 draft) and copies of the docs above. The repo docs are the working copies. When a decision changes `docs/RULES-*` or `docs/PLAN-*`, say so in the hand-back so the owner can sync the Project.

## Staging plan (don't skip steps)
1. Tune rules in the simulator. ← **we are here (Phase 1 of the plan)**
2. Paper or cards-only playtests with real people, 5+ sessions.
3. Cards-only edition via a print-on-demand publisher (The Game Crafter).
4. Decision gate: crowdfunding, publisher pitch, classroom channel, or stop.
5. Only then: one proof-of-concept electronic tank.

## Architecture: two engines, one rule set
- **`tanksim.py` (Python)** is the measurement engine: experiments, searches and proxies run on it. `play(prog_a, prog_b, cfg, grid=None, trace=None, patch=None)` plays one duel; `Config` holds every rule.
- **`tank-match-viewer.html` (JavaScript)** is the playable engine. Its rules live between `// ==== ENGINE START` and `// ==== ENGINE END ====`; everything outside that block is UI (deal mode, pit stops, the computer opponent, the board editor). The published copy is a claude.ai artifact the owner shares: https://claude.ai/artifact/XH46tiRNNpi3RK5DYYqvDW
- **They must agree exactly.** `tests/parity.py` runs the same random duels through both and fails on any mismatch. Card names map one to one, except Python `IF_ENEMY_BEHIND` = JS `IF_BEHIND` (the `JSNAME` table in `tests/parity.py`).
- `tanksim_multi.py` (free-for-all) is v0.1-only and out of scope (decision (k)).

## Locked decisions (do not violate without asking the owner)
Cited by letter everywhere in `.claude/`; `project-map/decisions.md` says where each is stated and enforced.
- **(a)** Boards and starts are rotationally symmetric. Asymmetry made the seat decide the winner (88% of decided matchups flipped when players swapped sides).
- **(b)** The card language has one rule set with no exceptions. The rail wraps: a condition or loop at the end applies to the first card. Specials add exactly one rule, the spent rule: a used special is spent, and any statement whose action is spent is skipped (owner, 2026-11-15). Nothing may add a second exception.
- **(c)** 8 program slots. 6 was too few; 10 went unused.
- **(d)** Randomness only before programming: visible layouts, pre-placed pickups, dealt hands. A card drawn at a pit stop is seen before reprogramming, so it counts (owner, 2026-11-15). Nothing random happens during a running round. A loss should mean the code was wrong.
- **(e)** The "loser rewrites" debug rule is the heart of the game. Protect it. Its form under dealt hands is not designed yet (experiment E1).
- **(f)** Every rule is a `Config` field, **off by default**, so older rule sets keep their exact behaviour. `tests/fingerprints.py` proves it.
- **(g)** Any rule change goes into both engines in the same change, with parity green (see Commands).
- **(h)** The staging plan order above. No hardware work before the step-4 gate.
- **(i)** Late-teen and adult tone. No cartoon mascots.
- **(j)** Simulator numbers are directional. Searches are small and proxies stand in for players; differences under ~10 points between runs are noise. The simulator cannot measure fun: questions about enjoyment, misreading or which cards people reach for go to human playtests.
- **(k)** Free-for-all is out of the first edition (owner, 2026-11-15).
- **(l)** Specials (Shield, Overcharge, Spread shot) are in the base game, rare in the shared deck (owner, 2026-11-15).
- **(m)** Shot-clock overtime is written in the card language: the attacker runs `If in sights · Fire · Otherwise · Hunt`, the holder runs `If in sights · Fire · Otherwise · Face enemy` (owner, 2026-11-15). The pathfinding attacker (`clock_path`) stays in the engine as a comparison only.
- **(n)** Power-ups are pre-placed and visible, and pay off through combat, never through hoarding (repair pickups doubled quiet rounds).

Held up and not to be reopened without new evidence: 8 slots, symmetric boards, pre-placed power-ups only, the debug rule being viable (a counter usually exists but is hard to find), reconfigurable boards as a curated layout deck.

## Commands
Run from the repo root. The owner is on Windows: `python` or `py`, never `python3` (in Git Bash an env var prefix works; in PowerShell use `$env:PARITY_TEMPLATES=1; python ...`). Node is needed for parity.

```
python tests/parity.py 800 v5                     # the gate: current rules, both engines
PARITY_TEMPLATES=1 python tests/parity.py 800 v5  # strong programs with specials spliced in, so shields meet shots
python tests/parity.py 600 v5 3 9                 # many pits
python tests/parity.py 600 v4                     # v0.4 (pathfinding overtime)
python tests/parity.py 600 v3
python tests/parity.py 300 draft1
python tests/fingerprints.py                      # older rule sets unchanged (takes about a minute)
python experiments7.py 60 K                       # an experiment: <rounds per board> <variant letters>
```

The **gate** before any commit that touches a rule: all six parity lines print `0 mismatches`, and `tests/fingerprints.py` prints `ok` for every entry. A UI-only viewer change needs a browser check (open the file, run a dealt round with both pit stops), not parity.

## Repo layout
```
tanksim.py                 # Python rules engine (Config, Tank, play)
tank-match-viewer.html     # JS engine (ENGINE block) + playable viewer UI
tanksim_multi.py           # free-for-all, v0.1 only, out of scope (k)
experiments.py … experiments7.py   # one question per file; docstring says what and how; outputs in results/
results/                   # raw experiment outputs, never hand-edited (the protect hook blocks it)
tests/parity.py            # JS vs Python on identical duels
tests/fingerprints.py      # older rule sets unchanged
docs/                      # rules draft, plan, experiment notes, playtest kit (docs/playtest/, to come)
.claude/                   # the agent toolkit: see .claude/README.md
```

## Working agreements
- **Simulator first.** A rule idea is a `Config` field and an experiment with a pass/fail line written *before* it runs, not an argument. Propose the experiment, run it or reason about it, then decide.
- **Same seeds across variants.** Compare variants on paired seeds, so a difference is the rule and not the dealing. Report sample sizes, and treat anything inside ±10 points as noise unless the run is bigger.
- **Never report a number you did not compute this session.** Old numbers carry their date and file (`results/…`, `docs/TANKS-V03-V04-NOTES.md`).
- **Experiments are reproducible:** one file per question, the variants in a table at the top, the output saved to `results/<name>.txt`, and the conclusion written into the plan or notes with the numbers.
- **Paper executability counts.** Steps 2–3 have people running programs by hand. A rule that only a computer can apply (pathfinding, hidden memory, long lookahead) needs a paper form or a reason.
- **The physical playtest is the final referee.** Nothing is "fun", "clear" or "balanced" because the simulator says so.
- **The repo is public.** No personal data, emails, or anything from the owner's other projects goes into commits, docs or agent memory.
- When a task is ambiguous between two rule designs, ask the owner rather than picking one.

## Agent economy
Lessons carried over from the owner's other projects, where session limits bit hard:
- One deliverable per spawn, with a tight brief: files, goal, what is already ruled out, and the gate it must pass.
- At most two agents at once.
- Resume an agent at most twice. Past about 100k tokens of transcript, spawn a fresh one with a memory file instead.
- At ~60 tool calls an agent writes its state to its memory file and hands back.
- Reports are bounded (about 300 words) and cite `file` and symbol.
- Searches go to Explore. Never spawn a general-purpose agent to "act as" a rostered one; if a role is unregistered, tell the owner to run `/agents`.
- **Reads:** never read `tank-match-viewer.html` (69 KB) or a results file whole. Grep, then read with offset and limit; the engine block is lines ~175–461.
- **Runs:** start an experiment run in the background and read its results file when it finishes. Full experiment runs take 10–20 minutes on two cores; smoke-test with a small round count first.
- The main session runs `/compact` at the end of each slice, and starts a new session after two slices or past ~150k context. Slice state lives in `.claude/agent-memory/project-manager/`.

## Current phase
- **Built (2026-11-15, `main`):**
  - The v0.5 draft rules in both engines: chassis plus a dealt hand of 5 from a 47-card shared deck, two pit stops, pits, Breach and Raise wall, Otherwise, the specials with the spent rule, optional pickups, and a 10-tick shot clock with card-language overtime.
  - Parity green on 3,920 duels; fingerprints ok.
- **Experiments (2026-11-24):**
  - E2 done: a curated deck of 12 layouts passes; the default board fails.
  - E1 first run done: no variant passes.
- **Next (Phase 1, from `docs/PLAN-2026-11.md`):**
  - The owner's decisions: layout pocket rule, default board, one layout per match, debug-rule direction.
  - An E1 redesign.
  - An E2 recheck with the 45-card deck.
  - Then E3 (mirror draws), E4 (card audit for print) and E5 (12-layout deck), and the v0.5 freeze.
- **Verified:** the Iteration 1 playtest kit exists in `docs/playtest/` and has not been used yet.
- **Not verified:**
  - Nobody but the owner has played. Nobody has run a round by hand on paper or timed one.
  - The 47-card deck is not trimmed for print.
