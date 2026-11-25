# Register of experiments (as of 2026-11-15)

Numbers are directional (j). Each line names the file and where the numbers live: H = `TANKS-HANDOFF.md` in the claude.ai Project (September), N = `docs/TANKS-V03-V04-NOTES.md`, R = `results/`.

## September (v0.1 → v0.2), source H

| File | Question | Verdict |
|---|---|---|
| `experiments.py` | Which strategies dominate? Can a locked program be countered? Rule sweep (slots, ticks, board size, zone, asymmetric start) | 8 slots right; every top program has a counter, but ~1% of random programs beat it (debug rule viable); rock-paper-scissors exists |
| `experiments2.py` | Reconfigurable boards; pre-placed vs mid-round power-ups | Board-specific champions (good). Asymmetric boards: the seat decides 88% → (a). Mid-round spawns break the debug rule → rejected (d). Repair pickups raise quiet rounds 32% → 58% → rejected (n) |
| `experiments3.py` | Random hands; pit-stop patch; free-for-all | Median hand ≈ full kit, but the worst 10% top out at 0.33 and 1 in 10 hands has no Fire → chassis idea. A loser-only pit stop at tick 10 flips 63%; both sides at tick 20 flip 2% (upper bounds). Free-for-all rewards camping (open problem 3) |
| `experiments4.py` | v0.1 vs v0.2 cards with the new-player proxy; cooldown; shrinking arena | v0.2 plus cooldown: new-player rounds with a hit 11% → 40%, expert kills 42% → 95%. Shrinking arena: tanks died in the zone → rejected |

## October (v0.3–v0.4), sources N and R

| File | Question | Verdict |
|---|---|---|
| `experiments5.py` (`results5.txt` first draft, `results5b.txt` v0.3) | Pits, board cards, chassis + dealt hand, two pit stops, full draft | **Chassis + hand:** novice rounds with a hit 22% → 77–82%, expert share 88–90%. **Pit stops:** expert draws 67% → 40–42%; a trailer at the last stop wins 31% (vs 2%). Raise wall ahead walled tanks in → moved behind. Breach used 37% → 6–10% after the Hunt change. Pits reshape routes; experts rarely fall in |
| (paired check, N) | The v0.3 Hunt (`hunt_avoid`) on identical programs | Neutral to slightly better (hits land 8% → 10%; 4% of results change) → adopted |
| `experiments6.py` (`results6.txt`) | Otherwise; rare specials; pre-placed pickups | **Specials:** expert draws 51% → 21%, quiet rounds 29% → 12%, skill share kept (87%). Luck: the expert dealt more specials won 60% of 57 decided rounds (±13), which is mild. **Otherwise:** small gain, kept for teaching. **Pickups:** taken in only ~1/3 of rounds (no card steers to them) → optional module |
| `experiments7.py` (`results7.txt`, `7b`, `7c`, `7d`) | Stuck rounds: cause and fixes | **Diagnosis:** 16% stuck (28% NvN); 64% apart, 36% dance. Dances are mirror symmetry: mirror-image squares never share a row or column. A contested-square deadlock was found. **Rejected:** stalemate pit stop (19%), mulligan (16%), B faces west (22%; seat fair 50%), initiative (18%), a symmetric shot clock (identical autopilots dance). **Works:** a clock with roles: trailer attacks + greedy Hunt 4%; + pathfinding 0%; **leader attacks + pathfinding 0% stuck, 99% kills, 4% draws, seat 51%, 18% of hits on autopilot** (adopted, then made card-language by (m)). A 15-tick clock is also 0% stuck, with seat 55% |
| (check, 2026-11-15) | Mirror matches under the clock | Same program both sides on 9 boards: 90/90 draws without the clock, 29/90 with it |

## November (v0.5), sources N and R

| File | Question | Verdict |
|---|---|---|
| `experiments8.py` (`results8.txt`, `8b`, `8c`, `8d`), 2026-11-24 | E2: stalls under card-language overtime (`clock_cards`) | **Measured; owner decision pending.** V (rule as written in (m)) fails on Pillars and pits: 49/300 = 16.3% stuck (`results8b.txt`); keeps on Four pillars, Centre block, Moat, and Open board (1/600 at the rerun, `results8c.txt`). V over five presets 3.5% stuck; K (pathfinder) 0/300 everywhere. Provisional without Pillars and pits: 0.2% stuck (`results8d.txt`). Cause: a corner trap for greedy Hunt. Pass line (≤2% on every layout) not met on the default layout. **Rejected printed programs** (`results8.txt`, 60 rounds per layout): P attacker `If in sights · Fire · If blocked · Turn right · Hunt` (4.3% stuck overall vs V 3.3%); Q holder `If in sights · Fire · Otherwise · Face enemy · Hunt` (12.7%); R = P+Q (10.0%); Q and R lost 11–13 points of skill share, and a Hunting holder recreates the symmetric clock's mirror dance |

## Open (Phase 1 of `docs/PLAN-2026-11.md`)

- **E2:** measured 2026-11-24 (see the table above); the layout decision (drop or redesign Pillars and pits, or another printed program) is the owner's.
- **E1:** the debug rule under dealt hands, options (a)/(b)/(c). Pass: round-1 loser wins round 2 in 35–60%; a counter is buildable in ≥80% of deals; the round-1 winner wins the match < 75%.
- **E3:** mirror draws under the frozen rules: ≤35% draws, none from stalls.
- **E4:** the card audit for print: usage per card, cutting anything under ~5% unless it teaches something.
- **E5:** the layout deck: 12 layouts, each with stuck ≤2% and seat 45–55%, and ≥8 distinct champions.
