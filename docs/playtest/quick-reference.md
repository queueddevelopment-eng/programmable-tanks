# Quick reference: v0.5 draft (one sheet, two sides)

**[open]** marks a gap in the draft's text. Where both engines (simulator and viewer) agree on an answer, it's written here so a hand referee can be checked against the viewer, but it isn't a rule until the rules draft says so.

## Side 1: the round

**Setup:** 8×8 board, A–H × 1–8. Tank A on A1 facing N, tank B on H8 facing S, 5 armor each. Default layout: walls C3, F3, C6, F6; pits D5, E4.

**Program:** you have 2 minutes. Build a rail of 1–8 cards from your chassis (Fire ×2, Hunt, Forward) plus your hand of 5. It reads left to right and **wraps**. It needs at least one action, and every loop card must sit directly before an action (the last card wraps to the first). Unused hand cards stay in your hand.

**Pit stops** happen before ticks 11 and 21:
1. Each player draws 1 card (A first).
2. In secret, each player may play 1 hand card: insert it (still 8 cards max) or replace a card (the replaced card is discarded). Or they keep the program.
3. A tank that played a card restarts at card 1, and its Repeat counters clear. Its cooldown, Hit flag, shield, Overcharge, stun and spent cards all carry over.
4. **[open]** The draft says every program restarts. Both engines restart only a tank that played a card; a kept program carries on.

**End:** a tank at 0 armor loses. After tick 40, more armor wins. Equal armor, or both destroyed on the same tick, is a draw.

### Each tick, in this order
1. **Pit stop**, if one is due.
2. **Sense** for both tanks, from the board as it stands now: in sights, blocked, near, and the enemy's direction (see side 2).
3. **Choose:** a stuck tank reads nothing and loses 1 stuck mark. If the clock track is at 10, the tank reads its **overtime card**. Otherwise it reads its rail (see side 2).
4. **Shield** (+1 charge, max 2) and **Overcharge** (arm) take effect.
5. **Shots** resolve at the same time, from where the tanks started the tick: Fire, Spread shot, Breach.
   - A front hit (the target faces the shooter) does 1 damage. A side or rear hit does 2.
   - Overcharge doubles a hit, then one shield charge soaks 1.
   - Every hit sets the target's **Hit** token, even when it's fully soaked.
6. **Breached walls** come off.
7. **If both tanks are alive:**
   - Raised walls go up first.
   - Then turns and moves. Both tanks driving for the same square: neither moves. No swapping places.
   - Driving into a pit: 2 damage, set Hit, 2 stuck marks.
8. **Cooldown:** a gun that went off this tick can't fire next tick. Mark it **G** on the sheet.
9. **Clock:** if anyone was hit or took damage this tick, the track goes to 0. If not, +1 (it stays at 10 in overtime).

**Shot clock and overtime.** At the start of a tick with the track at 10, each tank sets its rail aside and runs a printed card from its first card, with its own pointer.
- **Attacker** (more armor): `If in sights · Fire · Otherwise · Hunt`
- **Holder:** `If in sights · Fire · Otherwise · Face enemy`
- With armor level, the attacker alternates with each overtime and the first attacker rotates between rounds. **[open]** Who attacks first in round 1? (The viewer picks at random at each deal.)
- **Ending:** the tick after a hit or pit damage, the track is at 0, and both tanks go back to their own rails where they left off.

## Side 2: reading cards

### Reading the rail (start at the pointer)
- **Action:** if it's face down (spent), pass over it. Otherwise do it, and the pointer moves to the next card. Stop.
- **If… card:** if this statement's action is spent, skip the whole statement without reading the condition. Otherwise test the condition and set your **last-condition token** to T or F. On T, read on. On F, jump past the statement's action.
- **Otherwise:** true if the last-condition token shows F. It doesn't flip the token. On true, read on; on false, skip the statement.
- **If hit:** true if the Hit token is on. Reading it removes the token, whatever the result.
- **While in sights:** on true, do the next action, and the pointer **stays on the While**. On false, jump past its action.
- **Repeat ×3:** if the card has no counter, put 3 on it. Remove 1 and do the next action. While the counter is above 0, the pointer stays on the Repeat. At 0 it moves past the action.
- If the action after a loop is spent, skip both cards.
- If you read all the way around without finding an action, the tank idles.
- **[open]** The draft doesn't say whether While sets the last-condition token. The engines don't: only If… cards set it.
- **[open]** Is a condition in front of a loop re-checked on the loop's later ticks? The engines don't re-check it, because the pointer sits on the loop card.
- The last-condition token starts at T each round, so an Otherwise read before any condition is false.

### Senses
- **In sights:** the enemy is in a straight line ahead, with no wall between. Pits don't block.
- **Blocked:** the square ahead is a wall, the edge, a tank or a pit.
- **Near:** within 2 squares, counting diagonals.
- **Direction:** the enemy is *ahead* if it is at least as far forward as sideways (so the front diagonals count as ahead), *behind* if it is further back than sideways, and *left* or *right* otherwise (the rear diagonals count as a side). **[open]** The draft doesn't define the diagonals. This is what the engines do.
- **If enemy behind** = the direction is behind.

### Actions
- **Forward / Back:** move 1 square. You can't move into a wall, the edge, or the square the enemy started the tick on.
- **Turn left / Turn right:** 90° in place.
- **Fire:** hits if the enemy is in sights. It fizzles if the sheet shows G for your tank last tick. A fizzle still uses the card.
- **Breach:** removes the first wall in line ahead (not the edge). It never hurts a tank, and it uses the gun.
- **Raise wall:** a wall goes on the empty square behind you (no pit, no tank there). Max 2 per round, and failed attempts don't count.
- **Face enemy:** turn left if the enemy is left; turn right if it is right or behind. Ahead: do nothing.
- **Shield / Overcharge / Spread shot:** used once, then flip the card face down. A Spread shot fires in all 4 directions, ignores G, and sets G.

### Hunt (check in order; take the first that applies)
0. **Detour token on the tank?** Remove it. If blocked, turn right. If not, go forward.
1. **Enemy left, right or behind:** the preferred turn is left if the enemy is left; right if it's right or behind. A side is **shut** if turning would face a wall, the edge or a pit.
   - a. The preferred side isn't shut: turn that way.
   - b. The enemy is behind and the other side isn't shut: turn the other way.
   - c. You're not blocked ahead: go forward.
   - d. The other side isn't shut: turn the other way.
   - e. Everything is shut: turn the preferred way anyway.
2. **Enemy ahead:**
   - a. A wall, the edge or a pit is directly ahead: turn toward the enemy's side (right if it's exactly in line) and **place a detour token**.
   - b. A tank is directly ahead: do nothing.
   - c. Otherwise, go forward.

**[open]** Steps 0, 1b, 1e, 2a's tie-break and the detour token aren't in the draft's Hunt text. They come from the engines.

### Spent rule
A used special is spent: flip it face down, and any statement whose action is spent is skipped. It stays spent after a pit stop. **[open]** If a second copy of the same special is played at a pit stop, the engines mark the *first copy in rail order* as spent, which isn't necessarily the face-down card.
