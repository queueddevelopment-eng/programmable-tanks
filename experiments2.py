"""
experiments2.py - test two rule ideas:
  1. reconfigurable boards (random wall layouts, symmetric or not)
  2. power-ups: pre-placed before programming (input randomness)
                vs spawning mid-round (output randomness)

Every pairing is played on both sides so lopsided boards can't fake a result.
Usage: python3 experiments2.py
"""
import random, time
from collections import Counter, deque
from dataclasses import replace
from tanksim import *
from experiments import rand_program, flat, mutate, repair

BASE = Config()
PWR_DECK = dict(DEFAULT_DECK); PWR_DECK[IF_PWR] = 2

def layout(rng, symmetric, size=8):
    while True:
        k = rng.randint(4, 8); walls = set()
        while len(walls) < k:
            x, y = rng.randrange(size), rng.randrange(size)
            if (x + y <= 1) or (x + y >= 2 * size - 3): continue          # keep start corners open
            walls.add((x, y))
            if symmetric: walls.add((size - 1 - x, size - 1 - y))
        seen, dq = {(0, 0)}, deque([(0, 0)])                              # connectivity check
        while dq:
            x, y = dq.popleft()
            for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                if 0 <= nx < size and 0 <= ny < size and (nx, ny) not in walls and (nx, ny) not in seen:
                    seen.add((nx, ny)); dq.append((nx, ny))
        if len(seen) == size * size - len(walls): return tuple(sorted(walls))

def open_squares(rng, walls, n, size=8):
    out = []
    while len(out) < n:
        x, y = rng.randrange(size), rng.randrange(size)
        if (x, y) not in walls and (x, y) not in ((0, 0), (size-1, size-1)) and (x, y) not in [o[:2] for o in out]:
            out.append((x, y, rng.choice("RD")))
    return tuple(out)

def pool(rng, kind, n=40):
    out = []
    for i in range(n):
        if kind == "fixed":            c = BASE
        elif kind == "sym walls":      c = replace(BASE, walls=layout(rng, True))
        elif kind == "asym walls":     c = replace(BASE, walls=layout(rng, False))
        elif kind == "pre-placed pwr": c = replace(BASE, deck=PWR_DECK, powerups=open_squares(rng, BASE.walls, 2))
        elif kind == "mid-round pwr":  c = replace(BASE, deck=PWR_DECK, spawn_every=6, spawn_seed=rng.randrange(10**9))
        elif kind == "asym walls + pre-placed pwr":
            w = layout(rng, False); c = replace(BASE, walls=w, deck=PWR_DECK, powerups=open_squares(rng, w, 2))
        out.append((c, c.grid()))
    return out

def duel(p, q, sc):
    """p vs q on both sides of scenario sc. Returns (points for p out of 6, [result dicts])."""
    cfg, grid = sc
    r1 = play(p, q, cfg, grid); r2 = play(q, p, cfg, grid)
    pts = (3 if r1["winner"] == 0 else 1 if r1["winner"] is None else 0) + \
          (3 if r2["winner"] == 1 else 1 if r2["winner"] is None else 0)
    return pts, (r1, r2)

def fitness(p, opps, scs, off):
    return sum(duel(p, o, scs[(i + off) % len(scs)])[0] for i, o in enumerate(opps)) / (6 * len(opps))

def evolve(rng, scs, pop_n=70, gens=16, panel_n=60):
    cfg = scs[0][0]
    panel = [flat(rand_program(rng, cfg)) for _ in range(panel_n)]
    pop = [rand_program(rng, cfg) for _ in range(pop_n)]; hof = []
    for g in range(gens):
        opps = panel + hof[-20:]
        scored = sorted(((fitness(flat(p), opps, scs, g), p) for p in pop), key=lambda t: -t[0])
        for _, p in scored[:3]:
            if flat(p) not in hof: hof.append(flat(p))
        elite = [p for _, p in scored[: pop_n // 4]]; pop = elite[:]
        while len(pop) < pop_n:
            if rng.random() < 0.3:
                a, b = rng.sample(elite, 2)
                child = repair(a[: rng.randint(0, len(a))] + b[rng.randint(0, len(b)):], cfg) or a
            else: child = rng.choice(elite)
            pop.append(mutate(rng, child, cfg))
    sig = {}
    for c in hof:
        sig.setdefault(tuple(play(c, o, *scs[i % len(scs)])["armor"] for i, o in enumerate(panel[:30])), c)
    strong = sorted(((fitness(c, panel, scs, 0), c) for c in sig.values()), key=lambda t: -t[0])[:10]
    return strong, panel

STARTERS = [parse("WHILE_ENEMY FIRE RIGHT"), parse("IF_ENEMY FIRE IF_BLOCKED RIGHT FWD"),
            parse("WHILE_CLEAR FWD WHILE_ENEMY FIRE LEFT")]
FIXED_CHAMP = parse("IF_ENEMY REPEAT3 FIRE FWD IF_BLOCKED RIGHT")

def report(name, rng):
    t0 = time.time(); scs = pool(rng, name)
    strong, panel = evolve(rng, scs)
    progs = [c for _, c in strong] + STARTERS
    games = kills = dead = draws = split = decided = pick = 0
    share = []                       # per pair: how concentrated are outcomes across scenarios/seeds
    for i in range(len(progs)):
        for j in range(i + 1, len(progs)):
            oc = Counter()
            for sc in scs[:20]:
                _, (r1, r2) = duel(progs[i], progs[j], sc)
                w1 = {0: "i", 1: "j", None: "d"}[r1["winner"]]; w2 = {0: "j", 1: "i", None: "d"}[r2["winner"]]
                for r, w in ((r1, w1), (r2, w2)):
                    games += 1; kills += r["kill"]; dead += r["first_hit"] is None; draws += w == "d"
                    pick += sum(r["pickups"]); oc[w] += 1
                if w1 != "d" and w2 != "d":
                    decided += 1; split += w1 != w2
            share.append(max(oc.values()) / sum(oc.values()))
    mirror = sum(play(p, p, *sc)["winner"] is None for p in progs for sc in scs[:20]) / (len(progs) * 20)
    champ_fit = fitness(FIXED_CHAMP, panel, scs, 0)
    use = Counter(c for _, p in strong for c in set(p))
    print(f"\n=== {name} ===")
    print(f"strong programs : kills {kills/games:.0%} | no shot lands {dead/games:.0%} | draws {draws/games:.0%}")
    print(f"mirror matches  : {mirror:.0%} end in a draw")
    print(f"side decides    : {split/max(decided,1):.0%} of decided pairings flip winner when players swap sides")
    print(f"same winner     : a pairing's usual result holds in {sum(share)/len(share):.0%} of games across scenarios")
    print(f"fixed-board champion scores {champ_fit:.2f} here (0.89 on the fixed board); best generalist {strong[0][0]:.2f}")
    print(f"best generalist : {show(strong[0][1])}")
    print("cards in top programs:", ", ".join(f"{NAMES[c]} {use[c]}" for c in sorted(use, key=lambda c: -use[c])))
    if pick: print(f"pickups per game: {pick/games:.2f}")
    print(f"({time.time()-t0:.0f}s)", flush=True)

if __name__ == "__main__":
    rng = random.Random(11)
    for name in ("fixed", "sym walls", "asym walls", "pre-placed pwr", "mid-round pwr", "asym walls + pre-placed pwr"):
        report(name, rng)


def per_board(rng, symmetric, n_boards=8):
    """The realistic model of a reconfigurable board: players SEE the layout, then program for it."""
    tot = Counter(); champs = []
    for _ in range(n_boards):
        c = replace(BASE, walls=layout(rng, symmetric)); scs = [(c, c.grid())]
        strong, panel = evolve(rng, scs, pop_n=50, gens=12, panel_n=40)
        progs = [p for _, p in strong]
        champs.append((strong[0][1], scs[0]))
        for i in range(len(progs)):
            for j in range(i + 1, len(progs)):
                _, (r1, r2) = duel(progs[i], progs[j], scs[0])
                w1 = {0: "i", 1: "j", None: "d"}[r1["winner"]]; w2 = {0: "j", 1: "i", None: "d"}[r2["winner"]]
                for r, w in ((r1, w1), (r2, w2)):
                    tot["games"] += 1; tot["kills"] += r["kill"]; tot["dead"] += r["first_hit"] is None; tot["draws"] += w == "d"
                if w1 != "d" and w2 != "d":
                    tot["decided"] += 1; tot["split"] += w1 != w2
    # does a board-specific champion transfer to the other boards?
    xfer = []
    for k, (p, _) in enumerate(champs):
        for m, (_, sc) in enumerate(champs):
            if m != k:
                panel = [flat(rand_program(rng, BASE)) for _ in range(30)]
                xfer.append(fitness(p, panel, [sc], 0))
    g = tot["games"]
    print(f"\n=== per-board specialists, {'symmetric' if symmetric else 'asymmetric'} layouts ({n_boards} boards) ===")
    print(f"strong programs : kills {tot['kills']/g:.0%} | no shot lands {tot['dead']/g:.0%} | draws {tot['draws']/g:.0%}")
    print(f"side decides    : {tot['split']/max(tot['decided'],1):.0%} of decided pairings flip when players swap sides")
    print(f"a board's champion scores {sum(xfer)/len(xfer):.2f} vs random programs on the OTHER boards (about 0.9 on its own)")
    print("distinct champions:", len({tuple(p) for p, _ in champs}), "of", n_boards)
