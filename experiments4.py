"""
experiments4.py - does a higher-level card set (v0.2) fix the 'tanks wander and never fight' problem?

A 'two-minute thinker' stands in for a new player: the best of 10 random legal programs,
judged against a handful of opponents. We measure how much actually happens when thinkers meet.
"""
import random, time
from dataclasses import replace
from tanksim import *
from experiments import rand_program, flat, evolve as evolve1

def thinker(rng, cfg, grid, spar):
    best, bs = None, -1
    for _ in range(10):
        p = flat(rand_program(rng, cfg))
        if FIRE not in p or not any(c in p for c in (FWD, HUNT, BACK)): continue
        sc = 0
        for o in spar:
            w = play(p, o, cfg, grid)["winner"]; sc += 3 if w == 0 else 1 if w is None else 0
        if sc > bs: best, bs = p, sc
    return best or flat(rand_program(rng, cfg))

def run(name, cfg, rng):
    t0 = time.time(); grid = cfg.grid()
    spar = [flat(rand_program(rng, cfg)) for _ in range(8)]
    people = [thinker(rng, cfg, grid, spar) for _ in range(150)]
    n = 4000; hit = kills = draws = hits = ticks = 0
    for _ in range(n):
        a, b = rng.sample(people, 2); r = play(a, b, cfg, grid)
        hit += r["first_hit"] is not None; kills += r["kill"]; draws += r["winner"] is None
        hits += sum(r["hits"]); ticks += r["ticks"]
    print(f"\n=== {name} ===")
    print(f"new players : a shot lands in {hit/n:.0%} of rounds | {hits/n:.1f} hits per round | kills {kills/n:.0%} | draws {draws/n:.0%} | avg {ticks/n:.0f} ticks")
    final, panel, diverse = evolve1(rng, cfg, 80, 16, 60)
    d = k = dead = m = 0
    for i in range(len(diverse)):
        for j in range(i + 1, len(diverse)):
            r = play(diverse[i], diverse[j], cfg, grid); m += 1; d += r["winner"] is None; k += r["kill"]; dead += r["first_hit"] is None
    print(f"experts     : {len(diverse)} distinct strong programs | kills {k/max(m,1):.0%} | no shot lands {dead/max(m,1):.0%} | draws {d/max(m,1):.0%}")
    for sc, c in final[:3]: print(f"   {sc:.2f}  {show(c)}")
    print(f"({time.time()-t0:.0f}s)", flush=True)

if __name__ == "__main__":
    rng = random.Random(4)
    v2 = dict(V02_DECK)
    run("v0.1 (current viewer)", Config(), rng)
    run("v0.2 cards (Hunt, Track, If near, If behind)", Config(deck=v2), rng)
    run("v0.2 + gun cooldown", Config(deck=v2, cooldown=1), rng)
    run("v0.2 + cooldown + shrinking arena", Config(deck=v2, cooldown=1, shrink_start=16, shrink_every=8), rng)
    run("v0.2 + cooldown + shrinking arena, 6x6 board", Config(deck=v2, cooldown=1, shrink_start=12, shrink_every=8, size=6, walls=((1, 4), (4, 1))), rng)
