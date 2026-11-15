---
name: rules-engine
description: Map of Programmable Tanks' two rules engines - tanksim.py (Python) and the ENGINE block of tank-match-viewer.html (JavaScript) - the tick order as coded, card semantics in next_action (statements, skip tables, WHILE and Repeat, the spent rule, Otherwise's last condition, the rail wrap), the shot clock and overtime programs, the parity harness and its name map, and the Config fields with their JS equivalents. Loads on "tick order", "what does the engine do", "next_action", "parity", "Config field", "add a rule", "both engines", "ENGINE block".
when_to_use: Before implementing, reviewing or reasoning about a rule; when parity or fingerprints fail; when an experiment needs to know exactly what a Config field does.
user-invocable: false
allowed-tools: Read, Grep, Glob
---

# Rules engine

A map, not a second authority: `CLAUDE.md` wins on rules for working, and the code wins on behaviour. If this skill disagrees with the code, it is stale; tell docs-writer. Verified against `main` on 2026-11-15.

## Two engines, one rule set

| | Python `tanksim.py` (540 lines) | JS `tank-match-viewer.html` ENGINE block (~lines 175–461 of 1034) |
|---|---|---|
| Rules | `Config` dataclass | `RULESETS.v4` ("v0.5 draft"), `v3`, `v2`, `v1` objects |
| One duel | `play(prog_a, prog_b, cfg, grid=None, trace=None, patch=None)` | `newMatch(progs, starts, size, walls, maxTicks, rules, pits, pickups)`, then `stepMatch(m)` per tick |
| Tank state | `class Tank` (`load`, `_take`, `next_action`) | `makeTank`, `loadProgram`, `take`, `nextAction` |
| Board | padded flat `bytearray` grid (`Config.grid()`), positions as ints, `delta = (w, 1, -w, -1)` N E S W | `Set` of `"x,y"` strings; `DX`, `DY` arrays N E S W |
| Free-for-all | `tanksim_multi.py`, v0.1 only, out of scope (k) | `stepMatch` handles N tanks; roles only in duels |

Card names match one to one, except Python `IF_ENEMY_BEHIND` is JS `IF_BEHIND`. Python `OVERCH` prints as `OVERCHARGE`, and `ELSE` is `Otherwise` on the card.

## Tick order (both engines)

1. Increment the tick. Snapshot armor and hits for the shot-clock bookkeeping.
2. **Shot clock:** `clock_out` = shot clock on and (tick − 1 − last damage tick) ≥ `shot_clock`. On a new period: `periods += 1`, roles are set (`clock_roles`; tie → `(periods − 1 + clock_first) % 2`; otherwise the leader attacks if `clock_leader`, else the trailer), and with `clock_cards` each tank gets a fresh `Tank` runner for its printed program.
3. **Pit-stop patches** scheduled for this tick load: `Tank.load`, with the pointer back to the first card and loop counters cleared. Spent specials are carried by kind (`used`).
4. **Sensing at start of tick:**
   - sees (a clear line ahead to the enemy; walls block, pits don't);
   - blocked (a wall, edge, tank or pit ahead);
   - sees pickup;
   - side (0 ahead cone, 1 right, 2 behind, 3 left);
   - near (Chebyshev distance ≤ `near`).
5. **Action choice per tank:**
   - stunned → `IDLE` (stun − 1);
   - clock out with `clock_cards` → the runner's `next_action`;
   - clock out without it → the built-in autopilot (sees → `FIRE` or `IDLE` while cooling; holder → `TRACK`; `clock_path` → `_engage` route; else `HUNT`);
   - otherwise the tank's own `next_action`.
6. **Shield and Overcharge** take effect (`shield` max 2; `double`).
7. **Shots resolve at the same time, from start-of-tick state:**
   - `SPREAD`, or `FIRE` with `spreadnext` and a cool gun → four rays, ignoring the cooldown;
   - `FIRE` and `BLAST` during cooldown fizzle;
   - `FIRE` hits if it sees: front 1 or flank 2, through `_hit` (double, then shield soaks 1), which sets `hit`;
   - `BLAST` marks the first wall in line.
8. **Breached walls are removed.**
9. **If both tanks are alive:**
   - raised walls go up (`build_behind`: the square behind; max `max_builds`);
   - turns and moves resolve, including `HUNT` (with `hunt_avoid`: `_hunt_turn`) and `TRACK`;
   - if both tanks want the same square, neither moves (`initiative` changes this);
   - pit falls: `pit_dmg` damage and `pit_stun`;
   - pickups.
10. **Cooldowns count down.** Then: armor or hits changed → `last_dmg = tick`; record the trace; stop if a tank is destroyed.

Result: armor clamped at 0; equal armor is a draw (both destroyed is 0 = 0).

## Card semantics (`Tank.next_action`)

- It reads up to `n` cards from `ptr`. An **action** is taken and advances `ptr`.
- An **IF** true continues reading for free. False jumps to `skip[p]` (just past the statement's action, precomputed by `_skips`; it wraps).
- **WHILE** true returns its action and stays on the WHILE; false skips past the action. **Repeat ×3** counts down `rep[p]`.
- **The rail wraps:** a condition or loop at the end applies to the first card.
- **ELSE (Otherwise):** true iff `last_cond` is false. `last_cond` is set by every other condition read; ELSE itself doesn't set it.
- **Spent rule (the only special rule, decision b):** `_take` marks a special spent when it's used, however it was reached. Then:
  - a spent action is passed over for free;
  - an IF whose statement action is spent skips the whole statement;
  - a WHILE or Repeat whose action is spent skips it (Repeat resets its counter).
- Nothing found after `n` reads → `IDLE`.

## Where the detail lives

| File | Read when |
|---|---|
| `config.md` | You need a field's meaning, its default, its JS key, or which rule set turns it on |
| `add-a-rule.md` | You are implementing or reviewing a new rule: the step-by-step checklist, parity coverage, fingerprints |

## Parity harness (`tests/parity.py`)

`python tests/parity.py <N> <mode> [pits_lo pits_hi]`.

| Mode | Rules tested |
|---|---|
| `v5` | v0.3 rules + shot clock with roles + card-language overtime + initiative |
| `v4` | the same, with the pathfinding attacker |
| `v3` | v0.3 rules, no clock |
| `draft1` | the first v0.3 draft (wall ahead, old Hunt) |

How it works:
- Every mode deals specials, ELSE, `IF_POWERUP` and random pickups.
- Random symmetric layouts on 2 of every 3 matchups; random pits; pit-stop patches on half the matchups.
- `PARITY_TEMPLATES=1` splices specials (sometimes behind a loop) into strong programs, so shields actually meet shots.
- It compares per-tick traces (positions, facings, armor) and winners, and prints coverage counts. A rule whose count is 0 wasn't tested.
- The JS side is extracted between the ENGINE markers and run in Node.
