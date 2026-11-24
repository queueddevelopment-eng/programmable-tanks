# Session script, Iteration 1 (about 90 minutes)

**Who:** the owner as facilitator, plus 1–3 people. With 2 or more guests, guests play and the owner never takes a tank. With exactly 1 guest, the owner plays the other tank. Mark every such round "owner as opponent": it is evidence about the guest, and the owner's own play is owner play (README, "Rules for the evidence").

**Pre-freeze session.** Iteration 1 runs before the v0.5 freeze, so it does **not** count toward the step-3 gate: the plan puts the 5+ gate sessions after the freeze (`PLAN-2026-11.md`, Phase 2). Record every count anyway; they inform the rules and the kit.

**Rules under test:** v0.5 draft, no pickups, default layout. Pit stops after ticks 10 and 20. Shot clock 10 ticks.

## The session's question (write it down before the session starts)

- **H1, the debug rule:** a round's loser wants to rewrite (urge ≥4 of 5) under provisional variant (a). *Observed:* each loser's urge, what they changed, and the seconds before they touched a card.
- **H2, paper pace:** one hand-run round takes ≤10 minutes to run, not counting programming. *Observed:* the stopwatch, the ticks played, and referee errors against the viewer.

One session can't confirm either one. Record the numbers and don't draw a conclusion.

## Before people arrive (not counted in the 90 minutes)

- Build the default layout on the board. Sort the printed shared deck face up by card name (for the hand round), and keep a second, shuffled copy for the match. If you only have one copy, sort and reshuffle between phases.
- Laptop: open the viewer and choose "v0.5 draft". Check the layout matches.
- Print: 1 quick reference per person, 6 observer sheets, 2 tick sheets.
- Have a stopwatch or kitchen timer and a 2-minute sand timer. No phones at the table.

## Script

| Min | Phase | What happens | Record |
|---|---|---|---|
| 0–5 | Welcome | Explain that this tests the game, not them, that we're after confusion and boredom, and that notes are anonymous. Phones go in a pile. | group size; who has programmed before (a count, not names) |
| 5–15 | Teach (10 min, timed) | Teach from the quick reference in this order: board and facing → the rail reads left to right and wraps → actions → conditions and Otherwise → loops → Hunt (show the flowchart, don't explain it all) → shooting, front 1 / side or rear 2, cooldown → pits → specials and the spent rule → pit stops → shot clock (show the two printed overtime cards). | every question asked, tallied by rule on the observer sheet; the minute the teach ended |
| 15–25 | Practice round (viewer, **deal mode**) | The facilitator presses Deal and reads each hand out. Players take those cards from the sorted deck. Programs are open (shown face up). Run it with both pit stops on screen, so people see a pit stop happen once. | observer sheet, round 0 |
| 25–60 | Match, first to 3 (viewer, **kit mode**) | Deal physical cards from the shuffled deck. 2-minute programming in secret. The facilitator types both rails into "Full kit, no pit stops" and runs them. **No pit stops in these rounds**: the viewer can't apply table plays mid-round. Log this as a deviation. Between rounds, apply debug variant **(a)**. | one observer sheet per round. Ask the loser for their rewrite urge *before* they see their new cards. |
| 60–80 | Timed hand round (no screen) | See below. | tick sheet, stopwatch |
| 80–88 | Debrief | The four questions, asked to each player in turn, with answers written down word for word. | observer sheet, debrief block |
| 88–90 | Close | Thank them. Ask: "Would you play again?" (yes / maybe / no) if it hasn't already been answered. | |

If the match ends before minute 50, play a second short match (first to 2) with variant **(b)** or **(c)** and mark each round's variant on its observer sheet.

## Debug rule: provisional house variants [E1]

**Provisional. These are the plan's E1 candidates (`PLAN-2026-11.md`, E1), not rules.** In all three, the winner's rail is locked and reused unchanged in the next round, and only the loser rebuilds. The facilitator announces the variant before the match.

- **(a)** The loser returns its rail and hand to the deck, draws 5, and rebuilds from chassis + new hand.
- **(b)** The loser picks its rail back up into its hand, keeps its hand, and draws 2, then rebuilds from chassis + hand. *Wording pending owner confirmation.*
- **(c)** The loser redraws 5 but may keep any of its old rail cards.

Gaps in the draft. Decide at the table, write the decision on the observer sheet, and don't treat it as a rule:
- **[open]** What happens to the winner's unused hand: kept, or returned?
- **[open]** Does the deck reshuffle between rounds, and do the returned cards go back in?
- **[open]** After a draw, does anyone rewrite? Suggestion for the session: both keep their rails. Log it if a draw happens.

## Timed hand round (minutes 60–80)

1. **Deal:** in deal mode the facilitator presses Deal and reads the hands out. Players take the matching cards from the sorted deck and program openly (2 minutes). The facilitator types the rails in but doesn't run them.
2. **Overtime first attacker [open rule question]:** with armor level, the viewer picks the first overtime attacker with a hidden coin at each deal (`S.clockFirst`, not shown on screen). Before the stopwatch starts, the facilitator reads it off (browser console: `S.clockFirst`, 0 = tank A, 1 = tank B) and tells the referee, who marks the attacker marker. If it can't be read, log any level-armor overtime mismatch as "first-attacker unknown", not as a referee error.
3. **Referee:** one guest (not the owner) runs the round from the quick reference and fills in the tick sheet. The others move their own tank and tokens. The facilitator starts the stopwatch at tick 1 and only answers "the sheet says…". Every question gets logged.
4. **Pit stops:** at tick 10, the stopwatch pauses. With the screen turned away, the facilitator steps the viewer to its pit stop and reads out each tank's drawn card. Players choose their plays at the table, and the facilitator enters them. The stopwatch resumes. Do the same at tick 20.
5. **Stop** at the end of the round, or at **20 minutes** of running time. If you stop at the time limit, write down the tick reached. Either way, that is a finding.
6. **Check:** run the viewer to the end, then compare positions and armor at ticks 10, 20 and the end. Count every divergence as a referee error, and note the rule behind it, except a level-armor overtime divergence when the first attacker was unknown (step 2): log that as "first-attacker unknown".

## Debrief questions

1. What surprised you?
2. When you lost, what did you want to change?
3. Which card did you wish existed?
4. Would you play again? (yes / maybe / no)
5. Hand round only: what was the slowest thing to work out each tick?
