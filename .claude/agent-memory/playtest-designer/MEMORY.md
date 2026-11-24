# playtest-designer memory

## Sessions run
None. Iteration 1 kit written 2026-11-24 in `docs/playtest/`. Its question: H1, losers want to rewrite under E1 variant (a); H2, a hand-run round's running time is ≤10 min.

## Gate status (2026-11-24)
All four lines are not yet tested: 0 sessions, 0 timed hand rounds.

## Timing data
- None measured.
- Desk estimate, not timed: 25–45 s per tick × 21 ticks → about 9–16 min running time per hand round, plus pit-stop minutes counted separately (2 pit stops, not estimated). 21 ticks is the plan's v0.4 October median for strong vs strong. (Corrected 2026-11-24; an earlier line said 12–20 min.)

## Recurring misreads
None recorded yet.

## Known kit constraints
- The viewer has no referee mode. Kit mode edits only before tick 0, so it has no pit stops. Deal mode accepts only its own deal (`available()`), and neither mode has the debug rule. Workaround: viewer-dealt hands for the practice and hand rounds, kit mode with no pit stops for the match.
- The viewer randomises the first overtime attacker at each deal (`deal()`, `S.clockFirst`). RULES line 128 says it "rotates".
- Engine behaviour that isn't in the RULES text: Hunt's detour memory (`Tank.detour`), the direction cones, a kept program not restarting at a pit stop, While not setting the last condition, and a respent copy going to the first copy in rail order (`Tank.load`).
