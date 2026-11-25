# Programmable Tanks: v0.3 draft notes

*Written October 12, 2026; updated October 12 evening (playtest fixes), October 13 (v0.4 draft) and October 25 (shot clock). Read after `TANKS-HANDOFF.md` and the September 22 addendum. Covers the board-as-game-piece and draw-deck ideas, the v0.4 specials and pickups, their simulator results, and the updated viewer.*

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

## Card-language overtime stalls (E2, November 24)

**Question:** does the shot clock written in the card language (decision (m)) keep stuck rounds at or under 2% on every layout in the deck, with seat 45-55%? Pathfinding is not allowed on paper, so the printed programs behave like greedy Hunt. **Status: measured 2026-11-24, owner decision pending.** Numbers computed 2026-11-24 by sim-analyst (`experiments8.py`); directional per decision (j). Deck: the viewer's v4 47-card pile. Paired seeds as in `experiments7.py`; pairings EvE, EvN, NvE, NvN. Layouts: five presets (Pillars and pits, Four pillars, Open board, Centre block, Moat) plus Shuffled as an unjudged stress row.

| Variant | Overtime programs |
|---|---|
| K | pathfinding attacker (comparison only, not paper; decision (m)) |
| V | the rule as written in (m): leader attacks, attacker `If in sights · Fire · Otherwise · Hunt`, holder `If in sights · Fire · Otherwise · Face enemy` |
| P | attacker `If in sights · Fire · If blocked · Turn right · Hunt` |
| Q | holder `If in sights · Fire · Otherwise · Face enemy · Hunt` |
| R | P and Q together |

**Stage 2, screen** (`results/results8.txt`, 60 rounds per layout):

| | stuck overall | Pillars and pits | other four layouts | note |
|---|---|---|---|---|
| K | 0% | 0/60 | 0/60 each | |
| V | 3.3% | 10/60 = 16.7% | 0/60 each | |
| P | 4.3% | - | - | dropped |
| Q | 12.7% | - | - | skill share 11-13 points below V; dropped |
| R | 10.0% | - | - | skill share 11-13 points below V; dropped |

**Stage 3, decision** (`results/results8b.txt`, 300 rounds per layout; Open board rerun in `results/results8c.txt`, 600 rounds):

| V, layout | stuck | seat A | verdict |
|---|---|---|---|
| Pillars and pits | 49/300 = 16.3% (12.0% apart, 4.3% dance, 5.3% parked) | 51% on 126 decided | **fails**; kills 78%, draws 30%, never hit 16% |
| Four pillars | 1/300 | 50% | keep |
| Open board | 1/300 (first run); 1/600 (rerun) | 40% on 157 decided; 46% on 320 decided | keep (the 40% was inside noise; the rerun confirmed) |
| Centre block | 0/300 | 48% | keep |
| Moat | 2/300 | 49% | keep |

- V over all five presets: 3.5% stuck (1,500 rounds), kills 93%, draws 17%, autopilot share of hits 23%, skill share 84%.
- K: 0/300 stuck on every preset, seat 45-53%, kills 98-100%, autopilot share 17-18%, skill share 96%.
- The clock ran out in 98% of rounds. Overtime pit falls were 0.00 per round, so no stall ended by a fall.
- Shuffled (stress row, not judged): V 22/300 = 7.3% stuck; K 2/300.

**Stage 4, provisional** (`results/results8d.txt`; V only; the four presets other than Pillars and pits, fresh seeds with offset 50000, 300 rounds per layout):
- Stuck 0, 0, 1 and 1 of 300; seat 51%, 49%, 46% and 52%.
- Overall 0.2% stuck, kills 97%, draws 15%, autopilot share 23%, skill share 81%.
- Provisional: it only shows what the deck looks like without Pillars and pits. Dropping the layout is the owner's decision, and has not been made.

**Mechanism (from traces):** a corner trap. Greedy Hunt reaches a square whose two exits toward the enemy are both pit or pillar (D4 or D6 beside the pit pair D5/E4 on Pillars and pits). `hunt_avoid` then turns the attacker back and forth in a 2- or 6-tick loop until tick 40, while the holder only faces it. The per-pairing stuck rates are across all six boards in `results/results8b.txt`, not Pillars and pits alone: novice pairings 9.0% of 600, expert pairings 1.5% of 600. The period-6 stalls were all on Pillars and pits, per the mechanism output. Two stalls on other layouts were the same geometry built elsewhere: raised walls on Open board, and the Moat's own pit and wall pair. The pathfinder routes around the trap on the same deals.

**Rejected, do not re-propose without new evidence:**
- **P** (attacker adds `If blocked · Turn right`): 4.3% stuck overall at 60 rounds per layout (`results/results8.txt`), no better than V's 3.3%.
- **Q** (holder also Hunts): 12.7% stuck overall; **R** (P plus Q): 10.0%. Both lost 11-13 points of skill share against V, which breaches the guard rail. A holder that also Hunts recreates the rejected symmetric clock's mirror dance (see October 25 above).

**Proxy biases:** the experts are lookahead players, so their numbers are upper bounds on human play. The novices are random programs, so they stall more than a thoughtful beginner would. Treat differences under about 10 points as noise unless the run is large; the Pillars and pits failure (16.3% at N=300 against a 2% line) is far outside noise.

**Open question for the owner:** keep decision (m) as written and drop or redesign Pillars and pits (the rules draft's default layout, so a new default is needed), or adopt a different printed program. None of P, Q, R beats the rule as written. Nothing in `docs/RULES-v0.5-draft.md` has changed.

**Commands** (from the repo root; output saved to `results/`):

```
python experiments8.py 60 K V P Q R                       # stage 2 screen
python experiments8.py 300 K V                            # stage 3 decision
python experiments8.py 300 V offset=50000 boards=1,2,3,4  # stage 4: the four kept presets on fresh seeds
python experiments8.py 600 V boards=2 > results/results8c.txt  # Open board rerun
```

The Open board rerun uses seed offset 0, so its 600 rounds include the original 300 from stage 3. It extends the sample; it is not an independent one.

Runtime: on the owner's 24-core machine, 1,800 rounds took 142 s, and 3,600 rounds (300 per board per variant, 6 boards, 2 variants) took 331 s (footer of `results/results8b.txt`).

## Next steps

0. (v0.4) Playtest the v0.4 deck; test a Seek pickup card and pickup placement on Hunt paths; try Spread at ×2 and Shield at ×1 to see how the luck number moves.

1. Give the board cards a reason to exist (Breach damages a tank behind the wall; ranged Raise wall) and re-run C and F.
2. Human playtest of variant E in the viewer: does dealing feel fair, do people use pit stops, how long does a pit stop take at the table?
3. Tune hand size (4/5/6) and pit-stop ticks; test one pit stop vs two.
4. Score candidate layout cards (walls + pits) for combat frequency and novice friendliness; keep 12–16.
5. Port pits/board cards to `tanksim_multi.py` and re-test free-for-all camping with pit-stop pressure.
