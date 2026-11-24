# Playtest kit, Iteration 1

This kit is for the first sessions with real people (staging plan step 2). It tests the **v0.5 draft as it stands** (`docs/RULES-v0.5-draft.md`, 2026-11-15) while E1 and E2 are still open. It is not a frozen ruleset. Anything marked **[open]** is a question for the rules, not an answer.

The simulator can't tell us whether this is fun, clear, or quick enough to run by hand (decision (j)). Sessions like this one can.

## Two kinds of session

| | Decision playtest | Hand-execution timing test |
|---|---|---|
| Tests | the design: the urge to rewrite, which cards people reach for, whether the shot clock feels fair | whether a cards-only edition is viable: can a person run a round without a computer, and how long does it take? |
| Referee | the viewer on a laptop, run by the facilitator only | a player with the quick reference and the tick sheet. No screen. |
| Kit | cards, board, layout, quick reference, observer sheet | the same, plus tokens, a tank mat each and a tick sheet |
| Measures | minutes spent programming, rewrite urge (1–5), misreads, missing cards, shot-clock fairness, stalls | minutes per round, seconds per tick, referee errors against the viewer replay |

Phones stay away from the players. The laptop is test equipment, and only the facilitator touches it.

## What Iteration 1 runs

**One decision session (the owner facilitates, with 1–3 other people), plus ONE timed hand-run round in the same sitting.** Nobody has run a round on paper or timed one yet, so even one timed round is the most valuable number we can collect.

- Script: `session-script-iter1.md` (about 90 minutes).
- Per round: `observer-sheet.md`.
- Hand-run round: `tick-sheet.md` and `quick-reference.md`.
- After the session: `findings-template.md`. Copy it to `sessions/YYYY-MM-DD-<n>.md` and fill it in.

## Known limits of this iteration

- **The viewer can't yet referee table-dealt cards with pit stops.** It has no referee mode: kit mode ("Full kit, no pit stops") accepts any rail but has no pit stops, and deal mode only accepts the viewer's own deal. Neither mode has the debug rule. For the workarounds, see the script. This is handed to viewer-developer.
- **The debug rule is undesigned for dealt hands [E1].** The script uses provisional house variants taken from the plan's E1 options.
- **One layout.** Use the default (pillars C3, F3, C6, F6; pits D5, E4). The 12-layout deck is pending [E5].
- **No pickups.** The module is optional, and leaving it out removes a card and three state tokens from the teach. That leaves 45 cards in the shared deck.

## Rules for the evidence

- Players are "Player A", "Player B" and so on. Groups are "Group 1" and so on. No names or personal details: the repo is public.
- Record what players **did** separately from what they **said**.
- When the owner plays as a contestant, it counts as owner play and doesn't count toward the gate. The owner facilitating a session with other people does count.
- A session that isn't written down in `sessions/` didn't happen.
