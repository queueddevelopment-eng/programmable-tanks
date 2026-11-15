"""
experiments3.py - three more rule ideas:
  1. random hands  : draw 10 of your 20 cards, build from those (vs the fixed full kit)
  2. pit-stop patch: one card inserted/replaced mid-round - how much comeback does it give?
  3. free-for-all  : 4 and 6 tanks - does fighting or hiding win? does scoring fix it?
"""
import random, itertools, time
from collections import Counter
from dataclasses import replace
from tanksim import *
from tanksim_multi import *
from experiments import rand_program, flat, evolve as evolve1

BASE = Config(); GRID = BASE.grid()
rng = random.Random(21)
STARTERS = {"Turret": parse("WHILE_ENEMY FIRE RIGHT"), "Patrol": parse("IF_ENEMY FIRE IF_BLOCKED RIGHT FWD"),
            "Charger": parse("WHILE_CLEAR FWD WHILE_ENEMY FIRE LEFT"), "LaneCamper": parse("RIGHT WHILE_CLEAR FIRE")}

def pts(p, opps, cfg=BASE, grid=GRID):
    s = 0
    for o in opps:
        w = play(p, o, cfg, grid)["winner"]; s += 3 if w == 0 else 1 if w is None else 0
    return s / (3 * len(opps))

print("evolving a reference set of strong programs...", flush=True)
_, panel, strong = evolve1(rng, BASE, 80, 16, 60)
REF = strong + list(STARTERS.values())
BENCH = panel[:40] + REF

# ---------------------------------------------------------------- 1. random hands
def best_from_hand(hand, slots):
    cfg = replace(BASE, deck=hand, slots=slots)
    cands = {tuple(flat(rand_program(rng, cfg))) for _ in range(260)}
    quick = sorted(cands, key=lambda c: -pts(list(c), BENCH[::3]))[:5]
    return max(pts(list(c), BENCH) for c in quick)

def hands_test(slots, n=70):
    full = best_from_hand(dict(BASE.deck), slots)
    deck = [c for c, k in DEFAULT_DECK.items() for _ in range(k)]
    res = []; nofire = 0
    for _ in range(n):
        h = Counter(rng.sample(deck, 10)); hand = {c: h.get(c, 0) for c in DEFAULT_DECK}
        nofire += hand[FIRE] == 0
        res.append(best_from_hand(hand, slots))
    res.sort()
    print(f"\n=== random hand of 10, programs up to {slots} cards ===")
    print(f"best program from the full kit scores {full:.2f}")
    print(f"best program from a random hand: worst 10% {res[n//10]:.2f} | median {res[n//2]:.2f} | best 10% {res[-n//10]:.2f}")
    print(f"hands with no FIRE card: {nofire/n:.0%} | hands whose best program scores under 0.5: {sum(r < .5 for r in res)/n:.0%}")

# ---------------------------------------------------------------- 2. pit-stop patch
def patches(p, cfg):
    left = {c: cfg.deck[c] - p.count(c) for c in DEFAULT_DECK}
    out = []
    for c in DEFAULT_DECK:
        if left[c] <= 0: continue
        for i in range(len(p) + 1):
            q = p[:i] + [c] + p[i:]
            if validate(q, replace(cfg, slots=cfg.slots + 1)) is None: out.append(q)
        for i in range(len(p)):
            q = p[:i] + [c] + p[i + 1:]
            if q != p and validate(q, cfg) is None: out.append(q)
    return out

def patch_test(tick):
    lost = win = draw = 0; both_lost = both_win = 0
    for p, q in itertools.permutations(REF, 2):
        if play(p, q, BASE, GRID)["winner"] != 1: continue
        lost += 1
        outs = [play(p, q, BASE, GRID, patch={0: (tick, x)})["winner"] for x in patches(p, BASE)]
        win += 0 in outs; draw += (0 not in outs) and (None in outs)
        # if the leader may patch too: does the loser have a patch that survives EVERY reply?
        qs = patches(q, BASE)[::4]
        ok = False
        for x in patches(p, BASE)[::3]:
            if all(play(p, q, BASE, GRID, patch={0: (tick, x), 1: (tick, y)})["winner"] == 0 for y in qs + [q]):
                ok = True; break
        both_lost += 1; both_win += ok
    print(f"\n=== one-card pit stop at tick {tick} (loser patches) ===")
    print(f"losing matchups: {lost} | loser can flip to a WIN with one card: {win/lost:.0%} | to a draw: {draw/lost:.0%}")
    print(f"...and a patch that still wins whatever one-card reply the leader makes: {both_win/both_lost:.0%}")

# ---------------------------------------------------------------- 3. free-for-all
def ffa_test(cfg, starts, n_games):
    grid = cfg.grid(); k = len(starts)
    named = dict(STARTERS); named.update({f"Evolved{i+1}": p for i, p in enumerate(strong[:4])})
    pool = list(named.items()) + [(f"junk{i}", flat(rand_program(rng, BASE))) for i in range(6)]
    surv, dmg, played, mv = Counter(), Counter(), Counter(), Counter()
    sole = dead = 0; kills = 0; ticks = 0
    for _ in range(n_games):
        seats = rng.sample(pool, k)
        r = play_multi([p for _, p in seats], cfg, starts, grid)
        ticks += r["ticks"]; kills += sum(r["kills"]); sole += len(r["alive"]) == 1; dead += sum(r["dealt"]) == 0
        top_a = max(r["armor"]); top_d = max(r["dealt"])
        for i, (nm, _) in enumerate(seats):
            played[nm] += 1; mv[nm] += r["moves"][i] / r["ticks"]
            if r["armor"][i] == top_a and r["armor"].count(top_a) == 1: surv[nm] += 1
            if top_d > 0 and r["dealt"][i] == top_d and r["dealt"].count(top_d) == 1: dmg[nm] += 1
    print(f"\n=== free-for-all, {k} tanks on {cfg.size}x{cfg.size} ({n_games} games, fair share of wins = {1/k:.0%}) ===")
    print(f"avg kills per game {kills/n_games:.1f} of {k-1} possible | last-tank-standing finish {sole/n_games:.0%} | nobody hit {dead/n_games:.0%} | avg ticks {ticks/n_games:.0f}")
    print(f"{'program':11} {'mobility':>8} {'wins: most armor left':>22} {'wins: most damage dealt':>24}")
    for nm in named:
        print(f"{nm:11} {mv[nm]/played[nm]:>8.2f} {surv[nm]/played[nm]:>21.0%} {dmg[nm]/played[nm]:>23.0%}")

if __name__ == "__main__":
    t0 = time.time()
    hands_test(8); hands_test(5); print(f"({time.time()-t0:.0f}s)", flush=True)
    patch_test(10); patch_test(20); print(f"({time.time()-t0:.0f}s)", flush=True)
    ffa_test(CFG_4, STARTS_4, 4000); ffa_test(CFG_6, STARTS_6, 2500)
    print(f"({time.time()-t0:.0f}s)")
