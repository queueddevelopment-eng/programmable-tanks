# Locked decisions and owner decisions

Letters are the toolkit's citation handles; the wording of record is `CLAUDE.md`.

| | Decision | Stated | Enforced |
|---|---|---|---|
| (a) | Boards and starts are rotationally symmetric | CLAUDE.md; the claude.ai Project instructions | `experiments2.layout(symmetric=True)`, `experiments7.shuffled`, the viewer's `shuffledBoard` and the mirrored board editor; review-checklist item 3 |
| (b) | One card-language rule set, no exceptions; the rail wraps; the spent rule is the only rule specials add | CLAUDE.md; RULES draft "Spent rule" | `Tank.next_action` / `nextAction` (one code path); review-checklist item 3; game-designer's decision table |
| (c) | 8 program slots | CLAUDE.md | `Config.slots`, `SLOTS`, `validate` / `shape` |
| (d) | Randomness only before programming (layouts, pre-placed pickups, dealt hands, pit-stop draws seen before reprogramming); nothing random in a running round | CLAUDE.md; owner 2026-11-15 for pit-stop draws | `spawn_every` is legacy-only; review-checklist item 3 |
| (e) | "Loser rewrites" is the heart; protect it | CLAUDE.md; Project instructions | E1 pending: the form under dealt hands is undesigned |
| (f) | Every rule is a Config field, off by default | CLAUDE.md | `tests/fingerprints.py`; the guard hook nudges on `Config` edits |
| (g) | Both engines change together, with parity green | CLAUDE.md | `tests/parity.py`; the guard hook nudges after an engine edit; review-checklist item 1 |
| (h) | Staging order: simulator → paper playtests → cards edition → gate → one electronic tank | CLAUDE.md; Project instructions | `hardware-engineer` parked; project-manager's red lines |
| (i) | Late-teen and adult tone, no cartoon mascots | CLAUDE.md | viewer-developer, playtest-designer, tabletop-sme |
| (j) | Simulator numbers are directional; playtests referee fun and clarity | CLAUDE.md; Project instructions | experiment-method's noise rules; every agent's red lines |
| (k) | Free-for-all out of the first edition | owner 2026-11-15 | the viewer labels free-for-all modes "(not in first edition)"; `tanksim_multi.py` untouched |
| (l) | Specials in the base game, rare in the shared deck | owner 2026-11-15 | `RULESETS.v4.rarity`; RULES draft deck table |
| (m) | Shot-clock overtime in the card language (printed attacker and holder programs) | owner 2026-11-15 | `Config.clock_cards`, `clock_attack`, `clock_hold`; `RULESETS.v4.clockCards`; parity `v5` |
| (n) | Power-ups pre-placed and visible; pay off through combat, never hoarding | CLAUDE.md (from September) | the pickup kinds S, D, X; no repair in v0.5 |

## Held up (not reopened without new evidence)

8 slots; symmetric boards; pre-placed power-ups only; the debug rule is viable (a counter exists but is hard to find); reconfigurable boards as a curated layout deck. Source: `TANKS-HANDOFF.md`, "What held up" (claude.ai Project).

## Owner decisions, by date

- **2026-09-22:**
  - the staging plan;
  - target ages 14+;
  - the tank game is one product line of a STEM studio (Project addendum);
  - the passive-piece board as a possible tier.
- **2026-10-11 to 10-13 (tank chat):**
  - board elements and the draw/discard deck explored;
  - Raise wall behind and the Hunt change, both adopted after a playtest by the owner;
  - specials and pickups tried; rare + powerful = luck, so specials are one-shot and situational.
- **2026-10-25:** the shot clock adopted (leader attacks, pathfinding) after stuck rounds in the owner's play.
- **2026-11-15:**
  1. Pit-stop draws allowed.
  2. Specials in the base game with no loop exception.
  3. Overtime in the card language.
  4. Free-for-all out.
  5. Code moved to the repo `queueddevelopment-eng/programmable-tanks` (public, created by the owner).
