# Config fields (tanksim.py) and their JS equivalents

Verified 2026-11-15. "v0.5" is the viewer's `RULESETS.v4` ("v0.5 draft") and `tests/parity.py v5`. Every field is off or neutral by default (f). A rule set turns fields on.

## Board and match

| Python field | Default | JS | v0.5 | Meaning |
|---|---|---|---|---|
| `size` | 8 | `MODES[2].size` | 8 | board side |
| `walls` | C3 F3 C6 F6 | `newMatch(..., walls)` | per layout | wall squares `(x, y)`, 0-based |
| `pits` | `()` | `newMatch(..., pits)` | per layout | hazard squares |
| `powerups` | `()` | `newMatch(..., pickups)` | optional pair | `(x, y, kind)`: `'S'` shield, `'D'` overcharge, `'X'` spread next Fire, `'R'` repair (legacy, rejected (n)) |
| `slots` | 8 | `SLOTS` | 8 | rail length (c) |
| `armor` | 5 | `ARMOR` | 5 | |
| `front_dmg` / `flank_dmg` | 1 / 2 | `FRONT` / `FLANK` | 1 / 2 | front = target facing the shooter |
| `max_ticks` | 40 | `MODES[2].ticks` | 40 | |
| `b_facing` | 2 (S) | `MODES[2].starts` | 2 | 3 (W) was tried as a mirror breaker; not adopted |
| `deck` | `DEFAULT_DECK` (v0.1) | `RULESETS.*.deck` | see below | per-player counts; `shared_deck()` builds the pile |

## Cards and combat

| Python field | Default | JS | v0.5 | Meaning |
|---|---|---|---|---|
| `cooldown` | 0 | `cooldown` | 1 | ticks the gun cools after a shot |
| `near` | 2 | `near` | 2 | `IF_NEAR` range (king's move) |
| `max_builds` | 2 | `maxBuilds` | 2 | Raise wall limit per tank per round |
| `build_behind` | False | `buildBehind` | true | Raise wall goes behind (False = ahead, the first draft) |
| `hunt_avoid` | False | `huntAvoid` | true | Hunt never turns to face a wall or pit (`_hunt_turn`) |
| `pit_dmg` / `pit_stun` | 2 / 2 | `pitDmg` / `pitStun` | 2 / 2 | |

## Shot clock

| Python field | Default | JS | v0.5 | Meaning |
|---|---|---|---|---|
| `shot_clock` | 0 | `shotClock` | 10 | quiet ticks before overtime (0 = off) |
| `clock_roles` | False | `clockRoles` | true | one attacker, one holder (duels only) |
| `clock_leader` | False | `clockLeader` | true | the leader attacks (False = the trailer) |
| `clock_first` | 0 | `clockFirst` | random per round in the viewer | who attacks first on a tie |
| `clock_cards` | False | `clockCards` | true | overtime runs printed programs (m) |
| `clock_attack` | `IF_ENEMY FIRE ELSE HUNT` | `clockAttack` | same | the attacker's program |
| `clock_hold` | `IF_ENEMY FIRE ELSE TRACK` | `clockHold` | same | the holder's program |
| `clock_path` | False | `clockPath` | false | pathfinding attacker (`_engage`); comparison only (m) |
| `initiative` | False | `initiative` | false | a contested square goes to A on odd ticks, B on even; tested, not adopted |

## Legacy and rejected (kept so old experiments reproduce)

`zone` (centre scoring), `spawn_every` and `spawn_seed` (mid-round spawns, rejected (d)), `repair_amt`, `shrink_start` and `shrink_every` (the shrinking arena, superseded by the shot clock). None exists in the JS engine.

## Decks

- `DEFAULT_DECK` is v0.1. `V02_DECK` is v0.2. `V03_DECK` is v0.2 + Raise wall and Breach.
- `CHASSIS = {FIRE: 2, HUNT: 1, FWD: 1}` is always available to each player.
- The v0.5 shared pile: 2 × (the per-player kit − chassis) for normal cards, plus the specials by rarity (Shield 2, Overcharge 2, Spread 1). That's 47 cards with `If pickup ahead`, 45 without.
- JS: `sharedDeck()` uses `RULESETS.v4.rarity`. Python experiments build the pile with `shared_deck(deck) + SPECIALS` (`experiments6.py`, `experiments7.py`).
