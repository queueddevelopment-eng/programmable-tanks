# Programmable Tanks: rules, v0.5 draft (playtest candidate)

*November 15, 2026. Duel rules only; free-for-all is out of the first edition. This is the draft that Phase 1 experiments will tune and then freeze. Items marked **[E1]**–**[E5]** are pending those experiments (see `PLAN-2026-11.md`). Implemented in `tanksim.py` and in the viewer's "v0.5 draft" card set; the two engines are checked against each other by `tests/parity.py v5`.*

## Components

- **Board:** 8×8 grid, columns A–H, rows 1–8. Tank A starts on A1 facing north; tank B starts on H8 facing south.
- **Layout cards:** each sets the walls and pits for a round. Every layout is rotationally symmetric. **[E5]** The deck of 12 is pending; the default is four pillars (C3, F3, C6, F6) with pits at D5 and E4.
- **Wall blocks and pit tiles:** for building the layout and for the two board cards.
- **Two tanks:** 5 armor each, facing N/E/S/W.
- **Program cards:**
  - Each player has a **chassis** of 4 cards that are always available: Fire ×2, Hunt, Forward.
  - Everything else is in one **shared deck** of 47 cards, listed below. **[E4]** The card audit may trim it.
- **Pickup tokens (optional module):** one mirrored pair, both the same kind.
- **Optional aids:** a tick sheet and markers for armor, cooldown, stun, Hit, shield and spent cards.

## Shared deck (47 cards; 45 without the pickup module)

| Card | Copies | Card | Copies |
|---|---|---|---|
| Hunt | 2 | If in sights | 4 |
| Face enemy | 2 | If enemy near | 2 |
| Forward | 4 | If enemy behind | 2 |
| Back | 2 | If blocked | 2 |
| Turn left | 2 | If hit | 2 |
| Turn right | 2 | Otherwise | 4 |
| Fire | 2 | If pickup ahead | 2 (only with the pickup module) |
| Raise wall | 2 | While in sights | 2 |
| Breach | 2 | Repeat ×3 | 2 |
| **Shield** (special) | 2 | **Overcharge** (special) | 2 |
| **Spread shot** (special) | 1 | | |

## Round

1. **Setup.** Draw a layout card and place its walls and pits. If playing with pickups, place the pair.
2. **Deal.** Shuffle the shared deck and deal 5 cards to each player.
3. **Program.** You have 2 minutes, in secret. Lay out a rail of 1–8 cards from your chassis and your hand, read left to right and looping forever.
   - Validity: at least one action, and every loop card sits directly before an action (the rail wraps).
   - Hand cards you don't use stay in your hand for the pit stops.
4. **Reveal and run.** The tanks run until one is destroyed or 40 ticks have passed.
5. **Pit stops** happen after ticks 10 and 20:
   - Each player draws 1 card (A first).
   - Then, at the same time and in secret, each player may play one card from their hand: insert it anywhere in the rail, or replace a card (the replaced card is discarded). Or they keep the program.
   - Both reveal, and each program restarts from its first card.
   - A spent special stays spent.
6. **Result.**
   - A destroyed tank loses.
   - At 40 ticks, the tank with more armor wins.
   - Equal armor, or both destroyed on the same tick, is a draw.

## Match

First to 3 round wins.

**Debug rule [E1]:** the round winner's program is locked, and only the loser may rewrite. This is the heart of the game, but it isn't designed yet for dealt hands. The first simulator run (2026-11-24, `experiments9.py`, `results/results9.txt`) found that no variant passes. The open question is how the loser gets enough card choice to build a counter. Variants tested:

- **(a)** The winner keeps its rail. The loser returns its rail and hand to the deck, draws 5, and rebuilds from chassis + hand.
- **(b)** The loser picks its rail back up into its hand, keeps it, and draws 2.
- **(c)** The loser returns its hand, keeps any old rail cards, and draws 5.
- **(d)** As (a), and the winner also returns its hand.

The 5-card hand limits the loser. A search over the whole deck found a counter for 44 of 49 misses. Nothing here is decided. See `docs/TANKS-V03-V04-NOTES.md`.

## Cards

**Actions** (each uses one tick):
- **Forward / Back:** move one square. You stay put if a wall, the edge or a tank is there. Driving into a pit is allowed and hurts (see Pits).
- **Turn left / Turn right:** rotate 90° in place.
- **Fire:** shoot straight ahead at any range. Walls block shots; pits don't. The gun then needs 1 tick to cool, and a Fire during cooldown fizzles.
- **Hunt:** close in on the nearest enemy.
  - If the enemy is to your side or behind, turn toward them. But never turn to face a wall or pit: drive forward instead if the way is clear, otherwise turn the other way.
  - If the enemy is ahead, drive forward. If a wall or pit is directly ahead, sidestep toward the enemy's side.
- **Face enemy:** turn 90° toward the nearest enemy. Does nothing if they're already ahead.
- **Raise wall:** place a wall on the empty square directly behind you (not a pit or a tank). Limit 2 per tank per round.
- **Breach:** fire a round that removes the first wall in line. It cannot hurt a tank and stops at one. It uses the gun and its cooldown.

**Specials** (actions, used once; rare in the deck):
- **Shield:** soak 1 damage from the next hit. Stacks to 2. It takes effect before that tick's shots.
- **Overcharge:** your next hit does double damage.
- **Spread shot:** fire in all four directions at once, even while the gun is cooling. Then the gun cools.

**Spent rule** (the only rule specials add): a special is spent once used. Any statement whose action is spent is skipped. So a loop in front of a special fires it once, and from then on the whole statement is passed over. A spent card stays spent after a pit stop.

**Conditions** (free; each guards the statement that follows):
- **If in sights:** an enemy is in a clear straight line ahead.
- **If enemy near:** the nearest enemy is within 2 squares, counting diagonals.
- **If enemy behind:** the enemy is in the rear 90° cone.
- **If blocked:** the square ahead is a wall, the edge, a tank or a pit.
- **If hit:** you took damage since this card was last read. Reading it clears it.
- **Otherwise:** true when the most recent condition read was false. Example: `If in sights · Fire · Otherwise · Hunt`.
- **If pickup ahead:** a pickup lies in a clear line ahead. Pickup module only.

**Loops** (each must sit directly before an action):
- **While in sights:** repeat the next action every tick while it's true.
- **Repeat ×3:** run the next action on three ticks in a row.

## Program semantics

- A **statement** is a chain of condition and loop cards ending in one action.
- An **action**: do it and advance.
- **IF true:** keep reading, for free. **IF false:** skip the whole statement. Two IFs in a row act as AND.
- **WHILE true:** do its action and stay on the WHILE. **WHILE false:** skip past its action.
- **The rail wraps:** a condition or loop at the end applies to the first card.
- Reading all the way around without finding an action means the tank idles that tick.
- Sensors read the board as it stands at the start of the tick.

## Tick order

1. **Pit stop.** If one is due, apply it before the tick.
2. **Choose actions.**
   - A tank that is stuck in a pit reads nothing this tick.
   - If the shot clock has run out, the tank runs its printed overtime program.
   - Otherwise the tank reads its own rail.
3. **Shield and Overcharge** take effect.
4. **Shots resolve at the same time, from start-of-tick positions.** This covers Fire, Spread shot and Breach. Both tanks can hit; you can't dodge a same-tick shot.
   - A front hit (the target is facing the shooter) does 1 damage. A side or rear hit does 2.
   - Overcharge doubles a hit, then a shield charge soaks 1.
   - Every hit sets the target's Hit flag.
5. **Breached walls** are removed.
6. **If both tanks are still alive:**
   - Raised walls go up.
   - Then turns and moves resolve. If both tanks drive for the same square, neither moves. Tanks can't swap places.
   - A tank that drives into a pit takes 2 damage and is stuck for the next 2 ticks.
   - A tank that drives onto a pickup takes it.
7. **Gun cooldowns** count down.

## Shot clock

If nobody is hit for 10 ticks, each tank's program is set aside, and it runs a printed overtime program from that program's first card.

- **Attacker:** the tank ahead on armor must attack, so nobody can sit on a lead. With armor level, the roles alternate, and who attacks first rotates between rounds. The attacker runs `If in sights · Fire · Otherwise · Hunt`.
- **Holder:** the other tank runs `If in sights · Fire · Otherwise · Face enemy`.
- **Ending:** after the next hit (or pit damage), both tanks go back to their own programs where they left off.

**[E2]** Measured 2026-11-24 (`results/results8A-confirm.txt`, 100 rounds per layout): with these printed programs, a curated deck of 12 layouts passes the ≤2% stuck line. The default layout, Pillars and pits, fails at 11 stuck rounds in 100. Whether the layout deck gets a rule against inner pockets, and whether the default layout is redesigned, is pending the owner's decision. The printed programs are unchanged. Details: `docs/TANKS-V03-V04-NOTES.md`.

## Pickups (optional module)

- A mirrored pair of the same kind is placed at setup and is visible while programming.
- Kinds:
  - **Shield charge:** soaks 1 damage.
  - **Overcharge:** the next hit is doubled.
  - **Spread:** your next Fire is a spread shot.
- Drive over a pickup to take it.
- No pickup ever appears mid-round.

## Out of the first edition

Free-for-all (3–6 tanks); the ammo, mine and repair ideas; the Seek pickup card.
