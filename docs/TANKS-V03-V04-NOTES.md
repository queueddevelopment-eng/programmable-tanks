# Programmable Tanks: v0.3 draft notes

*Written October 12, 2026; updated October 12 evening (playtest fixes), October 13 (v0.4 draft) and October 25 (shot clock). Read after `TANKS-HANDOFF.md` and the September 22 addendum. Covers the board-as-game-piece and draw-deck ideas, the v0.4 specials and pickups, their simulator results, and the updated viewer.*

## E1: the debug rule under dealt hands (November 24)

Computed 2026-11-24 with `experiments9.py` and `results/results9.txt` (commit 4176274).

**Setup:** the 12 layouts that passed E2, 360 matches per variant, the 45-card v0.5 deck. First to 3 rounds, capped at 7 rounds. One layout per match (assumed, pending the owner).

**Variants:**
- A: the loser returns its rail and hand and draws 5.
- B: the loser picks its rail back up into its hand, keeps it, and draws 2.
- C: the loser returns its hand, keeps any old rail cards, and draws 5.
- D: as A, and the winner also returns its hand.

**Pass lines (fixed before the run):**
- P1: the round-1 loser wins round 2 in 35–60% of matches.
- P2: a counter is buildable from the loser's cards in ≥80% of deals where the round-1 winner was an expert.
- P3: the round-1 winner wins the match in <75%.

**Results** (percent; EvE = expert vs expert, NvN = novice vs novice):

| | P1 EvE | P1 NvN | P2 | P3 EvE | P3 NvN |
|---|---|---|---|---|---|
| A | 67 | 48 | 63 | 73 | 61 |
| B | 67 | 30 | 67 | 77 | 70 |
| C | 70 | 28 | 69 | 62 | 68 |
| D | 65 | 35 | 64 | 68 | 66 |

Sample sizes: EvE n≈99, NvN n≈104, P2 n=175. Noise is about ±10 points, so most differences between variants are noise.

**Verdict:** no variant passes. P2 fails on every variant.

**Where P2 fails:** where an expert beat a novice, the loser countered in 27 of 76 deals, against 83 of 99 when an expert beat an expert.

**Cause:** the 5-card hand. A search over the whole deck finds a counter for 44 of 49 misses, so the rules are not the limit.

**Cautions:**
- EvE P1 is an upper bound, because the loser proxy rebuilds with perfect foresight.
- NvN P1 for B and C is biased low, because the novice proxy gets weaker with more cards (53%, 36% and 29% with 5, 9 and 13 cards).
- Drawn rounds are common: 54–58% of drawn rounds followed a drawn round, because both sides keep their rails.

**Pending (not decided):**
- game-designer to propose a revised P2, or a variant with more card choice for the loser.
- E2 caveat: `experiments8.make_cfg` used a 41-card deck without Raise wall or Breach, so E2 may need a recheck with the full 45-card deck.

## E2: stuck rounds under card-language overtime (November 24)

Computed 2026-11-24 with `experiments8.py` (commits 9f3498d and 4ab89c2). Screen: `results/results8ABC.txt`. Confirm: `results/results8A-confirm.txt`.

**Question and pass line (fixed before the run):** under v5 card-language overtime, are stuck rounds ≤2% on every layout, with seat fairness at 45–55%?

**Screen** (30 rounds per layout, 17 layouts: 5 named and 12 generated symmetric):

| Variant | Stuck rounds |
|---|---|
| A: printed overtime | 29/510 (6%) |
| B: pathfinding (named boards only) | 0/150 |
| C: 8-card attacker (`If in sights · Fire · Otherwise · Hunt · If blocked · Turn right · Otherwise · Forward`) | 51/510 (10%) |

Seat fairness: A 51%, B 53%, C 51%. C is rejected, so the printed overtime programs of decision (m) stand unchanged.

**Confirm** (variant A, 100 rounds per layout; stuck rounds out of 100):

| Result | Layouts |
|---|---|
| Pass (≤2) | Four pillars 0, Open board 0, Centre block 0, Moat 0, Gen 01 1, Gen 02 1, Gen 05 0, Gen 07 0, Gen 08 0, Gen 09 0, Gen 10 0, Gen 11 0 |
| Inconclusive | Gen 06 4, Gen 12 3 |
| Fail | Pillars and pits 11, Gen 03 58, Gen 04 28 |

Seat fairness 50% over 928 decided rounds. Overtime was reached in 98% of rounds. Pit falls in overtime: 0.

**Mechanism:** 103 of the 106 stuck stretches had the attacker on or next to an inner "pocket": a free square with two orthogonal neighbours blocked, where the two blocked squares touch diagonally. Hunt's sidestep (`tanksim.play`, HUNT branch, `me.detour`) turns toward the second blocker, and the next tick undoes the sidestep. Two layout classifiers were tried. "No inner pockets" misclassifies 3 of 15 layouts. "Pocket closed toward the enemy's corner" misclassifies 1, but it was built after seeing the data, so it needs fresh layouts before E5 relies on it.

**Verdict:** variant A fails as a whole-deck rule, because the current default board (Pillars and pits) stalls 11%. A passes on a curated deck of 12. The pass line for the curated deck is met.

**Pending the owner (not decided):**
- Whether "no pockets" (or the directional version) becomes a layout-deck rule.
- Redesigning the default Pillars and pits layout.
- Whether the Hunt sidestep should be examined: an engine question for rules-engineer.

## Stuck rounds and the shot clock (October 25)

**Problem (from playtesting):** some rounds stall: the layout and the dealt cards leave neither tank able to engage.

**Diagnosis** (`experiments7.py`, `results7*.txt`; v0.4 rules, 60 rounds per board on the six viewer boards, experts and novices mixed). A round counts as stuck if it ends with 20+ ticks of no damage and nobody destroyed.
- 16% of rounds stuck (8% expert vs expert, 28% novice vs novice). Worst boards: Pillars and pits 22%, Shuffled 27%.
- Causes: 64% "apart": both programs only act on a condition (`If hit · Hunt`) or loop in place, so the tanks never meet. 36% "dance": the tanks get close but never line up.
- Dances are the mirror problem in play: on a mirrored board, two tanks doing the same thing stay in mirror-image squares, and mirror-image squares never share a row or column. No smarter Hunt can fix that; only asymmetry can.
- Also found a deadlock: two Hunting tanks diagonally adjacent both try to drive into the same square every tick, so neither ever moves (contested squares bump both).

**What didn't work:** an extra "stalemate pit stop" after 8 quiet ticks (19% stuck: the proxies used the extra patches defensively; real players might not), a one-time hand redraw (16%: with the chassis, the hand is rarely the problem), B starting faced west (22%; fixes seat symmetry, not stalls), initiative on contested squares (18%), and a symmetric shot clock where both tanks Hunt (two identical autopilots dance forever).

**What works: a shot clock with roles.** If nobody is hit for 10 ticks, both tanks stop reading their programs. The tank **ahead on armor must attack** (basketball-style: no sitting on a lead); the other holds. With armor level, the roles alternate, and who attacks first rotates between rounds. The attacker drives the shortest route to the nearest square with a clear shot, then turns and fires. The holder turns to face it and fires when in sights. Both hold aim while the gun cools. After the next hit, programs resume where they left off.

| | stuck | kills | draws | seat A wins | expert share vs novice | hits landed by autopilot |
|---|---|---|---|---|---|---|
| v0.4 without clock | 16% | 72% | 19% | 46% | 82% | - |
| clock, trailer attacks, greedy Hunt | 4% | 91% | 18% | 42% | 75% | - |
| clock, trailer attacks, pathfinding | 0% | 99% | 4% | 49% | 97% | - |
| **clock, leader attacks, pathfinding (adopted)** | **0%** | **99%** | **4%** | **51%** | 94% | **18%** |
| same, 15-tick clock | 0% | 95% | 7% | 55% | 94% | 18% |

- Zero stuck rounds on every board, including Pillars and pits and shuffled layouts. The clock runs out in almost every round, but only 18% of hits land while it's in charge: it breaks the opening standoff and the programs do most of the fighting.
- Greedy Hunt wasn't enough as the attacker (it can't find a way around a pit next to a pillar), hence pathfinding. Software-only on a passive board; a self-driving tank needs the layout (from the layout card) to plan the route.
- Watch: comebacks got rarer (an expert behind at tick 20 won 1–5% of the time, from 8%), and expert skill matters more (94% vs 82%). The clock length is the dial; 15 ticks gives programs longer before it steps in.
- Engine: `Config.shot_clock`, `clock_roles`, `clock_leader`, `clock_path`, `clock_first`, plus `initiative` (tested, not adopted). `play()` reports `overtime` and `overtime_hits`. Viewer v0.4 has it on: countdown in the status line, a log line explaining who must attack and why, Attacking / Holding badges. Parity: 1,365 duels with the clock running out, zero mismatches (`python tests/parity.py 800 v4`).

## v0.4 draft (October 13): Otherwise, rare specials, pickups

Design principle agreed with Q: rare + powerful = luck, which fights the "build a solid program" goal. So specials are one-shot and situational, not strictly stronger cards, and the simulator checks whether holding one decides games.

**New cards**
- **Otherwise (ELSE).** Condition card, true when the most recent condition card was false. `If in sights · Fire · Otherwise · Hunt`. 2 per player. Hardware: firmware only.
- **Shield** (special). Action, used once. Next hit does 1 less damage (stacks to 2). Takes effect before that tick's shots. Hardware: firmware only (an LED shows it).
- **Overcharge** (special). Action, used once. Next hit does double damage. Hardware: firmware only (the IR hit message carries the damage value).
- **Spread shot** (special). Action, used once. Fires in all four directions, ignoring the cooldown. Hardware: three more IR emitters per tank (~$0.30 each plus driver); receivers are already on all four sides.
- **If pickup ahead.** Condition, true when a pickup lies in a clear line ahead. 1 per player.
- One-shot rule: once used, the card is spent and the tank passes over it for free (its whole statement is skipped). It stays spent after a pit stop. Loop cards can't repeat a special.
- Rarity is copies in the shared pile: Shield ×2, Overcharge ×2, Spread ×1 in a 37-card pile, so about one special per player per round.

**Pickups** (Q's idea): a mirrored pair, same kind, placed at round start and visible while programming (the handoff already found mid-round spawns break the debug rule). Drive over one to take it: shield charge, overcharge, or the next Fire becomes a spread shot. Physical form: a token the board lights; on a passive board it's free, with self-driving tanks the board or a hub has to know where the tanks are.

**Simulator results** (`experiments6.py`, `results6.txt`, 100 rounds per pairing; base = v0.3 core: chassis + dealt hand + 2 pit stops, v0.3 Hunt and wall rules, pillars board, no board cards)

| Variant | Experts: kills | Experts: no shot lands | Experts: draws | Better program wins | Expert's share vs novice | Comeback with pit stops |
|---|---|---|---|---|---|---|
| A. v0.3 core (control) | 68% | 29% | 51% | 59% | 86% | 37% |
| B. + Otherwise | 71% | 27% | 43% | 57% | 86% | 45% |
| C. + rare specials | **84%** | **12%** | **21%** | 63% | 87% | 41% |
| D. + pre-placed pickups | 74% | 23% | 47% | 53% | 86% | 44% |
| E. + Otherwise + pickups | 85% | 12% | 29% | 54% | 82% | 52% |

- **Rare specials are the biggest win so far for decisiveness, and skill survives.** Draws halved (51% → 21%) and quiet rounds fell to 12%, while the expert's edge over novices held (87%) and the better pre-round program still won 63%. Specials break mirror matches: one Shield is enough to make two identical hunters stop drawing.
- **Luck check:** the expert dealt more specials won 60% of decided rounds (57 rounds, roughly ±13%). That's an effect about the size of program quality itself (63%), not a dominating one. Worth watching in playtests; the dial is rarity (copies in the pile).
- **Specials actually get played:** about 1.4 per round (Overcharge 0.60, Shield 0.50, Spread 0.28). Overcharge and Shield are in about a quarter of expert programs; Spread in 11%.
- **Otherwise is a small, clean improvement:** in 18% of expert programs, draws down 8 points, no skill cost. It also teaches if/else, so keep it on educational grounds.
- **Pickups alone are incidental:** taken in only a third of rounds, because no card steers a tank toward a pickup (If pickup ahead only reacts when one is already in line). When one side did grab more, it won 65% of 20–23 rounds (too few to read much into). To get the "race to the item" Q described, the game needs a way to go for them: a Seek pickup card (Hunt, but toward the nearest pickup), or layouts that put pickups on the natural Hunt paths.
- A is noisier than it looks: the same "v0.3 core" scored 40% draws in results5b. Differences under ~10 points between runs are search noise.

**Suggested v0.4 core:** v0.3 core + Otherwise + rare specials. Pickups stay an optional board module until a Seek card is tested.

## Walls on a physical board (discussion, October 13)

- Recommended: physical wall blocks and pit tiles with a magnet in the base, placed and lifted by hand when the board lights the square; the board's Hall sensors confirm. No motors.
- Breach and Raise wall still work: the board announces the change and lights the square, a player lifts or places the block. Passive board: just one more hand move. Self-driving tanks: the match pauses until the board senses the block placed or removed. Board cards are rare (well under one wall change per round in the simulator), so pauses are infrequent.
- Placement is never free: Raise wall goes on the square directly behind the tank (if empty, max 2 per tank per round), Breach removes the first wall in the line of fire, and the starting layout comes from a mirrored layout card. The program decides where; that's the point.

## What changed in the rules (v0.3 draft)

**Board elements**
- **Pits.** Hazard squares. Driving in (Forward or Back) costs 2 armor and the next 2 ticks (no card is read). Shots pass over pits. "If blocked" is true for a pit ahead, and Hunt steers around pits like walls. Hardware: a pit can be a black square the tank's line sensor already sees.
- **Raise wall (BUILD).** Action. Puts a wall on the empty square **behind** the tank (cover from chasers). Max 2 per tank per round. Resolves after fire, before movement. *Changed after playtest: the first draft built ahead, and a program that raised a wall then drove forward walled itself in.*
- **Breach (BLAST).** Action. Fires a round that removes the first wall in line. Uses the gun, so it shares Fire's cooldown. Harmless to tanks; stops at a tank.

**Hunt (v0.3 change)**
- Hunt never turns to face a wall or pit. When turning toward the enemy would face one: if the enemy is behind, it tries the other turn; otherwise it drives forward if the way ahead is clear; if ahead is blocked too, it turns the other way; only if boxed in on all sides does it turn toward the enemy anyway. *Changed after playtest: `If blocked · Turn left · Hunt` ping-ponged, because Hunt turned straight back to face the wall.*
- Hardware: the tank needs to know whether the squares to its sides are blocked. Either side proximity sensors, or the tank knows the wall layout (from the layout card, or from the board in the passive-board format).

**Card mechanic**
- **Chassis:** Fire ×2, Hunt, Forward. Always available to every tank.
- **Shared deck:** each player's v0.2/v0.3 kit minus the chassis, pooled (32 cards with v0.2, 36 with board cards). Each player draws a hand of 5 and builds a program of up to 8 cards from chassis + hand.
- **Pit stops** before ticks 11 and 21 (after ticks 10 and 20). Each tank draws 1, then may play one card from its hand: insert it, or replace a card (the replaced card is discarded). The program restarts from its first card; armor, position, facing, cooldown and the HIT flag carry over.

**Rule fix:** both tanks destroyed on the same tick is now a draw in the Python engine too (it used to award the tank with less overkill). The viewer already worked this way.

## Simulator results, current v0.3 rules (results5b.txt, 100 rounds per pairing per variant)

Same proxies and variants as the first-draft run below, with the wall raised behind and the new Hunt.

| Variant | Experts: kills | Experts: no shot lands | Experts: draws | Expert's share vs novice | Novices: a shot lands | Novices: kills |
|---|---|---|---|---|---|---|
| A. fixed kit | 47% | 53% | 71% | 92% | 21% | 13% |
| B. + pits | 31% | 54% | 55% | 80% | 15% | 14% |
| C. + board cards | 44% | 56% | 81% | 94% | 19% | 13% |
| D. chassis + drawn hand | 47% | 53% | 60% | 90% | **79%** | 53% |
| E. D + 2 pit stops | 69% | 26% | 40% | 80% | **82%** | **61%** |
| F. E + pits + board cards | **71%** | **13%** | **20%** | 74% | 56% | 41% |

- **The conclusions hold and the full draft got better.** F now has the fewest quiet expert rounds (13%, was 23%) and draws (20%, was 29%), and new-player rounds where a shot lands rose from 46% to 56%.
- **Pit stops create real comebacks.** With the metric fixed (armor at the last pit stop), the trailing expert wins 2% of the time without pit stops and 31% with them (variant E); 16% → 46% in the full draft. Result changed by pit stops in 39–49% of rounds.
- **The new Hunt is not a balance change.** On 1,500 identical program pairs, old vs new Hunt: shots land 8% vs 10%, kills 6% vs 6%, and 4% of results change. The swings between this table and the first-draft table in A–D (±10 points) are search noise from the expert proxy.
- **Raise wall no longer traps you, but experts still rarely use it** (6% of programs). Breach fell from 37% to 6–10% of expert programs, because Hunt now routes around pillars instead of needing to blast through. Both board cards look like flavour rather than strategy so far; candidates: make Breach also damage a tank directly behind the wall, or let Raise wall go up at range.

## First-draft results (results5.txt: wall raised ahead, old Hunt)

Same player proxies in every variant so the variants compare fairly: an "expert" searches ~200 programs against a bench (and knows the standard strategies if its cards allow them) and looks ahead at pit stops; a "novice" takes the best of 6 random programs and looks at only 3 random pit-stop plays. These proxies are not the evolved sets from earlier files, so compare within this table, not with the v0.2 table in the handoff.

| Variant | Experts: kills | Experts: no shot lands | Experts: draws | Expert's share vs novice | Novices: a shot lands | Novices: kills |
|---|---|---|---|---|---|---|
| A. v0.2 fixed kit | 56% | 44% | 76% | 94% | 22% | 13% |
| B. + pits | 35% | 47% | 47% | 82% | 14% | 13% |
| C. + board cards | 62% | 37% | 72% | 92% | 13% | 9% |
| D. chassis + drawn hand | 60% | 39% | 67% | 88% | **77%** | **49%** |
| E. D + 2 pit stops | 69% | 29% | 42% | 80% | 78% | 52% |
| F. E + pits + board cards | 67% | **23%** | **29%** | 73% | 46% | 33% |

**Findings**
1. **The chassis + drawn hand is the biggest win of the project so far for new players.** Quiet novice rounds dropped from 78% to 23%. The chassis guarantees every program can shoot and close distance, which is exactly what new players were failing to build. Skill still dominates (experts take 88% of points vs novices).
2. **Pit stops make the game more decisive without making it random.** Expert draws fell from 67% to 42%, kills rose, and pit stops changed the result in 36% of rounds. Experts played a card at only 37% of stops, so "keep my program" is a real choice. Skill share fell modestly (88% → 80%). Effects are upper bounds (look-ahead).
3. **The full draft (F) is the most decisive version:** lowest draws (29%) and fewest rounds with no hit (23%). It costs some skill share (73%) and new-player activity (46% of novice rounds see a hit vs 78% in E), because pits and board cards are extra ways for a beginner's program to hurt itself.
4. **Pits reshape play more than they hurt.** Experts almost never fall in (0.05–0.17 falls per round); instead programs shift toward Forward / If blocked / Repeat routes and away from pure Hunt (Hunt usage 100% → 72%). Pits belong in curated layout cards, not on every board.
5. **Breach works; Raise wall doesn't.** Breach appeared in 37% of expert programs (opening lanes through pillars). Raise wall appeared in 4%: a wall in front blocks your own gun. Redesign candidates: raise the wall behind you (rear cover, blocks chasers), or drop it on the square you leave.
6. **Mirror draws are effectively gone with dealt hands:** identical programs in expert-vs-expert rounds were 1–8%, and overall draws fell to 29% in F. A shared, shuffled deck is the mirror-draw fix that doesn't make the seat decide.

**Suggested v0.3 core:** chassis + drawn hand + two pit stops (variant E). Add Breach and curated pit layouts as the "advanced" board. Redesign Raise wall before including it.

## Viewer (tank-match-viewer.html)

- Card sets v0.3 draft / v0.2 / v0.1. Duel or 4/6-tank free-for-all.
- **Cards:** "Deal hands, pit stops" (duel) or "Full kit". In deal mode the palette shows chassis and hand cards; "Lock in, face down" hides a program for hot-seat play; programs are revealed when the match starts.
- **Pit stops** pause the match: pick a hand card, tap a + to insert it or a card to replace it, or keep the program. The computer's choice stays secret until the match resumes.
- **Computer opponent** for either duel tank: searches for a program from what it holds and looks ahead at pit stops.
- **Board editor:** "Edit board", tap squares to cycle empty → wall → pit, mirrored by default. Presets include Pillars and pits, and Moat.
- Raised walls draw with a dashed outline; Breach shots draw as dashed beams.
- The JS engine matches `tanksim.py` on 1,200 random duels with walls, pits, board cards and pit stops (`tests/parity.py`), zero mismatches.

## Files added or changed

- v0.4: `tanksim.py` adds SHIELD, SPREAD, OVERCHARGE (one-shots, `ONESHOT`), ELSE, pickup kinds 'S' and 'X', and reports `used` and `absorbed`. `experiments6.py` + `results6.txt`. `tests/parity.py` now covers specials, Otherwise and pickups; `PARITY_TEMPLATES=1` splices specials into strong programs so shields meet shots (730 targeted + 900 random duels, zero mismatches). Viewer: v0.4 card set (default), Pickups selector, spent cards struck through, Shield / Overcharged / Spread loaded badges.

- `tanksim.py`: BUILD/BLAST cards, `V03_DECK`, `CHASSIS`, `shared_deck()`, Config fields `pits`, `pit_dmg`, `pit_stun`, `max_builds`; `play()` accepts several pit-stop patches per side (`{side: [(tick, prog), ...]}`) and reports `falls`, `builds`, `blasts`. Old rules are unchanged (regression-checked).
- `experiments5.py`: the six-variant comparison above. `python experiments5.py [rounds] [variant letters…]`, e.g. `python experiments5.py 40 D E`.
- `experiments.py`: mutation now only picks action cards that are in the deck.
- `tests/parity.py`: JS-vs-Python engine check (`python tests/parity.py 600 [v3|draft1] [min_pits max_pits]`, needs Node). Current rules: 1,200 duels, zero mismatches; first draft: 400, zero mismatches.
- `results5.txt`: raw output of the first-draft run. `results5b.txt`: raw output of the current-rules run. Rerun the first draft with `TANKS_RULES=draft1 python experiments5.py 100`.
- Config fields `build_behind` and `hunt_avoid` (both off by default so old experiments reproduce exactly; on in experiments5 and in the viewer's v0.3 card set). The viewer's v0.2 and v0.1 sets keep the old rules.

## Next steps

0. (v0.4) Playtest the v0.4 deck; test a Seek pickup card and pickup placement on Hunt paths; try Spread at ×2 and Shield at ×1 to see how the luck number moves.

1. Give the board cards a reason to exist (Breach damages a tank behind the wall; ranged Raise wall) and re-run C and F.
2. Human playtest of variant E in the viewer: does dealing feel fair, do people use pit stops, how long does a pit stop take at the table?
3. Tune hand size (4/5/6) and pit-stop ticks; test one pit stop vs two.
4. Score candidate layout cards (walls + pits) for combat frequency and novice friendliness; keep 12–16.
5. Port pits/board cards to `tanksim_multi.py` and re-test free-for-all camping with pit-stop pressure.
