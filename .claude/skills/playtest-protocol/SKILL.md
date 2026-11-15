---
name: playtest-protocol
description: How Programmable Tanks runs human playtests - the two session kinds (viewer as referee; hand execution with a tick sheet), a session script, what an observer records per round, the tick sheet and quick-reference contents, the findings table, and the step-3 gate. Loads on "playtest", "session", "observer sheet", "tick sheet", "quick reference", "print and play", "paper", "by hand", "gate to print".
when_to_use: When preparing, running or debriefing a playtest; when judging whether a rule can be run by hand; before the print edition.
user-invocable: true
allowed-tools: Read, Grep, Glob
---

# Playtest protocol

From `docs/PLAN-2026-11.md` Phase 2. `CLAUDE.md` wins. Playtests referee fun, clarity and pace (j); the simulator can't.

## Two kinds of session

1. **Decision playtests:** physical cards, with the viewer as referee. The facilitator enters both programs (deal mode, pit stops in the viewer); players watch. This tests the design: the urge to rewrite, which cards people reach for, whether the shot clock feels fair. The laptop is test equipment run by the facilitator, so phones stay away from the players.
2. **Hand-execution playtests:** cards, the board, tokens, the tick sheet and the quick reference. No screen. This tests whether a cards-only edition is viable. Time it.

## Session script (about 90 minutes)

1. 10 minutes: teach, from the quick reference. Note every question asked.
2. A practice round with open programs.
3. A match: first to 3, with the debug rule as the rules draft states it (or the E1 variant under test).
4. 5 minutes of debrief questions:
   - What surprised you?
   - When you lost, what did you want to change?
   - Which card did you wish existed?
   - Would you play again?

## Observer sheet, per round

- Round number, layout card, both programs as revealed, the pit-stop plays.
- Minutes: programming, then running (by hand or by viewer).
- Rules misread (which rule, what they did instead).
- Questions asked.
- Did a shot land before the shot clock? Did the clock run out? Did it feel fair (ask the loser, 1–5)?
- **Loser's urge to rewrite** (1–5) and what they changed.
- Cards reached for that don't exist.
- Any stall felt.

## Tick sheet (hand execution)

One row per tick. Per tank:
- the pointer (card index);
- the card read;
- the action;
- position and facing;
- armor;
- gun cooldown;
- stun;
- the Hit flag;
- the last condition (for Otherwise);
- shield charges;
- the shot-clock count.

Spent specials are flipped face down on the rail. Repeat counters go on a token on the card.

## Quick reference

One page. Tick order (the rules draft's 7 steps), card text, the spent rule, pit stops, the shot clock and the two printed overtime programs.

## Debrief into findings

`finding | count | quote or observation | rule or card | severity | owner agent`. What players did is kept apart from what they said. Players are "Player A" and "Group 2", never names. The repo is public.

## Gate to step 3

All must hold:
1. A hand-run round fits in about 10 minutes, or a simpler paper model has been identified.
2. Losers rewrite willingly in most sessions.
3. No rule is misread in more than one session after the quick reference is fixed.
4. At least 3 of 5 groups would play again.

The owner's solo play is recorded as owner play, not a session.
