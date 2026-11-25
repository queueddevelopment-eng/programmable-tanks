---
name: experiment-method
description: How Programmable Tanks measures rules - the expert and novice proxies and their biases, pit-stop lookahead, metric definitions (stuck, never hit, kills, draws, skill share, seat fairness, comebacks, luck, autopilot share), pass lines written before the run, paired seeds, noise rules of thumb, runtimes, and the file and results conventions; plus a register of every past experiment and its verdict. Loads on "experiment", "pass line", "proxy", "noise", "how many rounds", "is this significant", "has this been tried", "results file".
when_to_use: Before designing, running, reviewing or quoting an experiment; before proposing a rule (check the register for prior attempts).
user-invocable: true
allowed-tools: Read, Grep, Glob
---

# Experiment method

A map, not a second authority: `CLAUDE.md` wins (decision (j): numbers are directional; the simulator can't measure fun). Verified 2026-11-15.

## The loop

1. **Question** in measurable terms, from game-designer or the plan.
2. **Pass line written first**, for example "stuck ≤ 2% on every layout; seat 45–55%". Never move it after the run.
3. **Variants table** with a control, keyed by letter at the top of the file.
4. **Paired seeds:** the seed is a function of (board, round index) only, so every variant plays the same deals.
5. **Smoke test** with N of 4–6, then the full run in the background to `results/<file><letters>.txt`.
6. **Check the rule fired** (the clock ran out in X%; specials used Y per round).
7. **Verdict:** pass, fail, or inconclusive. Then the numbers with N, any surprise with its mechanism, and the conclusion into the plan or notes.

## Proxies (from `experiments5.py`)

- **Expert:** the standard strategies its cards allow (`KNOWN`), plus 60 random programs, plus 140 hill-climb steps, scored against a bench (`STARTERS` plus 4 random programs, both seats). At pit stops it tries every legal play with lookahead (`round_with_stops`, `plays_for`, `value`), assuming the rival keeps its program.
- **Novice:** the best of 6 random legal programs that contain Fire and a mover, judged against 4 sparring programs. At pit stops it looks ahead over 3 random plays.
- **Known biases:**
  - Lookahead is foresight no player has, so pit-stop effects are **upper bounds**.
  - Experts optimise points: they patch *defensively* when given extra stops. That's why the stalemate pit stop made stalls worse.
  - Novices are random programs, not people; a person who reads "Hunt" does better.
  - Skill-share numbers rise when a rule rewards search.
- Pairings: EvE, EvN and NvE (experts in both seats), and NvN. `experiments7.py` cycles `EvE, EvN, NvN, EvE, NvE, NvN`.

## Metrics (as coded)

| Metric | Definition | Where |
|---|---|---|
| stuck | the round ends with ≥ 20 ticks of no damage (with a clock: ≥ clock + 10), nobody destroyed | `experiments7.stall_info` |
| stuck cause | apart (never within 2 squares in the quiet stretch), dance (close, never lined up), parked (a tank never left its square) | same |
| no shot lands / never hit | `first_hit is None` | `play()` result |
| kills, draws | `kill`, `winner is None` | `play()` |
| skill share | the expert's points against a novice (win 1, draw 0.5) | EvN/NvE rows |
| better program wins | among decided EvE rounds, the side with the higher bench score wins | `experiments6.luck` on `qual` |
| seat fairness | tank A wins / decided even matchups (EvE, NvN); fair is 45–55% | `experiments7.report` |
| comebacks | an expert behind on armor at tick 20 (or the last pit stop) still wins | `trail` |
| luck | the side dealt more specials, or grabbing more pickups, wins / decided rounds where they differ | `experiments6.luck` |
| autopilot share | hits landed while the shot clock had taken over / all hits | `overtime_hits` |

## Noise, sample size, runtime

- At 60–100 rounds per cell, treat differences under **~10 points** as noise. At 57 decided rounds, a 60% rate is ±13. Two identical-looking runs of the "v0.3 core" gave 40% and 51% draws.
- Report N beside every percentage. Rerun bigger only if the decision depends on a gap inside the noise.
- Runtime on 2 cores: `experiments5` and `experiments6` at 100 rounds per pairing take about 15 minutes for 5–6 variants. `experiments7` at 60 rounds per board takes about 4 minutes per variant (6 boards × 60), and longer with dynamic stops. Lookahead pit stops dominate the cost.
- The owner's current machine has 24 cores and runs `experiments8` at 300 rounds × 6 boards (5 presets plus the Shuffled stress row) × 2 variants in about 5.5 minutes (3,600 rounds took 331 s on 2026-11-24, footer of `results/results8b.txt`), so the two-core figures above are upper bounds.
- Use `multiprocessing.Pool` with `imap_unordered` and `chunksize` 3–4. Never more than two heavy runs at once.

## File conventions

- One question per `experimentsN.py`. The docstring states the question, variants, metrics, usage line and pass lines.
- Variants as a dict or list keyed by letter. `python experimentsN.py <N> <letters>` reruns a subset.
- Reuse `experiments5.build`, `round_with_stops`, `legal` and `plays_for`, and `experiments7.BOARDS`, `shuffled` and `stall_info`. Don't write new proxies.
- Results are raw stdout in `results/`, never hand-edited (the protect hook blocks it).
- Conclusions go to `docs/PLAN-2026-11.md` (verdicts) and `docs/TANKS-V03-V04-NOTES.md` (detail).

## Register

`past-experiments.md` lists every experiment so far, with its verdict. **Read it before proposing a rule**, so nothing rejected comes back without new evidence.
