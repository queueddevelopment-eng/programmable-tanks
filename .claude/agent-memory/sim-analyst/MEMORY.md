# sim-analyst memory

## Experiments

### E2 — experiments8.py (2026-11-24, uncommitted at time of writing; base commit edfdcc5)
- Question: stalls under v0.5 card-language overtime. Variants A (v5 control), B (clock_path), C (8-card attacker
  `IF_ENEMY FIRE ELSE HUNT IF_BLOCKED RIGHT ELSE FWD`).
- Layouts: 5 named (experiments7.BOARDS minus Shuffled) + 12 from `gen_deck(seed=8)` (6 with inner pockets, 6 without).
  Reusable for E5: `gen_layout`, `pockets`, `connected`, `score_layout`, `draw`.
- Design: one job per (layout, seed) builds the programs ONCE under A's rules, then plays every variant (paired).
  Seed = layout_index * 1e5 + round. Pit-stop RNG = Random(seed ^ 0x5EED00) per variant.
- Smoke `python experiments8.py 4 ABC`: 18 s on 4 cores (68 jobs x 3 variants). Building is cheap here; the
  13-min estimate in the brief was far too high.
- Screen `python experiments8.py 30 AC B:named` -> results/results8ABC.txt (98 s, 510 jobs). Verdict (screen):
  A stuck 29/510 = 6%; flagged Pillars and pits 2/30, Gen 03 16/30, Gen 04 8/30, Gen 12 2/30 (Gen 06 1/30).
  27/29 A stuck stretches have the attacker on/next to an inner pocket. C worse: 51/510, 8 layouts flagged incl.
  pocket-free Gen 10/11/12. B 0/150 (named only). Seat A: A 51% (269), C 51% (293), B 53% (96). Autopilot A 22%, C 22%.
  Outcome 2 (pockets explain it, curate). Confirm proposed: `python experiments8.py 100 A` (not yet run).
- Post-hoc (hypothesis, not a result): pockets closed TOWARD the enemy's start (blocked N+E or S+W) separate better:
  Gen 01/02 have pockets closed the other way and 0/30 stuck; Gen 05 has 2 such pockets and 0/30 (not sufficient).

## Runtimes
- experiments8: ~0.25 s CPU per job per variant-set; 510-job screen ~ a few minutes on 4 cores.

## Proxy and tooling notes
- Rebuilt per-tick overtime from a trace (armor-only) mismatches play()['overtime'] only when a Shield soaks a hit
  (hits change, armor doesn't): checked 6/6 cases, 2026-11-24.
- Attacker seat in an overtime stretch is read from actions: holder plays only FIRE/TRACK/IDLE.

## Reproducible rounds
- Period-2 pocket wiggle (A): Gen 03 seeds 700002 (attacker A at (3,3), N/E pits) and 700005 (attacker B at (5,3)).
  Hunt sidestep (`elif wb: act = LEFT if rr < 0 else RIGHT; detour = 1`) ignores hunt_avoid and turns into the other
  blocker; next tick the detour branch sees it blocked and turns RIGHT back. Engine matter -> rules-engineer, not me.
- Gen 12 stalls (no inner pockets, attacker roams 9-16 squares, apart): not traced yet.
- Pocket loop (hypothesis confirmed): mirror `IF_HIT HUNT IF_ENEMY FIRE` on Pillars and pits, variant A, clock_first 0:
  attacker A cycles (3,3)N -> sidestep RIGHT to E (faces pit 4,3) -> detour blocked, RIGHT to S -> FWD (3,2) ->
  enemy behind, LEFT to E -> LEFT to N -> FWD (3,3); period 6, ticks 18-40, 5-5 draw. clock_first 1 mirrors it at (4,4)/(4,5).
  Under C both clock_first values end in a kill (the FWD half breaks the loop).

### E2 confirm (2026-11-24, HEAD a7e7249, experiments8.py as committed in 9f3498d)
- `python experiments8.py 100 A` -> results/results8A-confirm.txt (1700 rounds, ~4-5 min on 4 cores).
- Pass line (coordinator, before run): <=2 stuck/100 pass, 3-4 inconclusive, >=5 fail; seat 45-55% pooled.
- PASS (12): Four pillars, Open board, Centre block, Moat, Gen 01 (1), Gen 02 (1), Gen 05, 07, 08, 09, 10, 11.
  INCONCLUSIVE: Gen 06 4/100, Gen 12 3/100. FAIL: Pillars and pits 11/100, Gen 03 58/100, Gen 04 28/100.
  Seat 50% (928) pass. 103/106 stuck stretches attacker by an inner pocket.
- Classifiers over the 15 decided layouts: "no inner pockets" misclassifies 3 (Gen 01, 02, 05);
  "closed toward the enemy's corner" (N+E or S+W blocked) misclassifies 1 (Gen 05). Post-hoc, same layouts.
- Gen 12 stall seed 1600009: attacker B U-turns at edge pocket (3,0), roams 27 ticks, reaches A at t38;
  last two FIREs soaked by shields (hits, no armor change) -> counts as stuck.
