"""
experiments.py - search the program space to stress-test the rules.

  1. random-population stats : how often are rounds dead / drawn / decisive?
  2. evolution               : what strategies dominate? which cards matter?
  3. counter search          : can a locked program always be beaten? (tests the debug rule)
  4. variant sweep           : re-run 1-3 under alternative rules

Usage: python3 experiments.py [--quick]
"""
import random, sys, time, json
from collections import Counter
from tanksim import *

def rand_statement(rng, room, left):
    """One statement (tuple of cards) fitting in `room` slots given remaining deck `left`."""
    for _ in range(20):
        st = []
        if room >= 2 and rng.random() < 0.55:
            ifs = [c for c in IFS if left[c] > 0]
            if ifs:
                st.append(rng.choice(ifs))
                if room >= 3 and rng.random() < 0.15:
                    ifs2 = [c for c in IFS if left[c] - st.count(c) > 0]
                    if ifs2: st.append(rng.choice(ifs2))
        if room - len(st) >= 2 and rng.random() < 0.3:
            lp = [c for c in LOOPS if left[c] > 0]
            if lp: st.append(rng.choice(lp))
        acts = [c for c in ACTIONS if left[c] > 0]
        if not acts: return None
        st.append(rng.choice(acts))
        if len(st) <= room and all(st.count(c) <= left[c] for c in st):
            return tuple(st)
    return None

def rand_program(rng, cfg):
    left = dict(cfg.deck); stmts = []; room = cfg.slots
    target = rng.randint(1, cfg.slots)
    while cfg.slots - room < target:
        s = rand_statement(rng, room, left)
        if s is None: break
        stmts.append(s); room -= len(s)
        for c in s: left[c] -= 1
    return stmts

def flat(stmts): return [c for s in stmts for c in s]

def repair(stmts, cfg):
    out, left, room = [], dict(cfg.deck), cfg.slots
    for s in stmts:
        if len(s) <= room and all(s.count(c) <= left[c] for c in set(s)):
            out.append(s); room -= len(s)
            for c in s: left[c] -= 1
    return out

def mutate(rng, stmts, cfg):
    s = list(stmts); r = rng.random()
    if r < 0.3 and s:
        s[rng.randrange(len(s))] = rand_statement(rng, 4, cfg.deck) or s[0]
    elif r < 0.55:
        ns = rand_statement(rng, 4, cfg.deck)
        if ns: s.insert(rng.randint(0, len(s)), ns)
    elif r < 0.75 and len(s) > 1:
        del s[rng.randrange(len(s))]
    elif r < 0.9 and len(s) > 1:
        i, j = rng.sample(range(len(s)), 2); s[i], s[j] = s[j], s[i]
    elif s:
        i = rng.randrange(len(s)); st = list(s[i]); st[-1] = rng.choice([c for c in ACTIONS if cfg.deck.get(c, 0)] or ACTIONS); s[i] = tuple(st)
    s = repair(s, cfg)
    return s if s else rand_program(rng, cfg)

def score(p, opponents, cfg, grid):
    pts = 0
    for o in opponents:
        w = play(p, o, cfg, grid)["winner"]
        pts += 3 if w == 0 else 1 if w is None else 0
    return pts / (3 * len(opponents))

def population_stats(rng, cfg, n_prog, n_games):
    grid = cfg.grid()
    progs = [flat(rand_program(rng, cfg)) for _ in range(n_prog)]
    dead = draw = kill = 0; ticks = 0
    for _ in range(n_games):
        a, b = rng.sample(progs, 2)
        r = play(a, b, cfg, grid)
        dead += r["first_hit"] is None; draw += r["winner"] is None; kill += r["kill"]; ticks += r["ticks"]
    return dict(dead=dead / n_games, draw=draw / n_games, kill=kill / n_games, avg_ticks=ticks / n_games)

def evolve(rng, cfg, pop_n, gens, panel_n, log=False):
    grid = cfg.grid()
    panel = [flat(rand_program(rng, cfg)) for _ in range(panel_n)]
    pop = [rand_program(rng, cfg) for _ in range(pop_n)]
    hof = []
    for g in range(gens):
        opps = panel + hof[-30:]
        scored = sorted(((score(flat(p), opps, cfg, grid), p) for p in pop), key=lambda t: -t[0])
        for sc, p in scored[:3]:
            if flat(p) not in hof: hof.append(flat(p))
        if log: print(f"  gen {g:2d} best {scored[0][0]:.3f}  {show(flat(scored[0][1]))}", flush=True)
        elite = [p for _, p in scored[: pop_n // 4]]
        pop = elite[:]
        while len(pop) < pop_n:
            if rng.random() < 0.3:
                a, b = rng.sample(elite, 2)
                child = repair(a[: rng.randint(0, len(a))] + b[rng.randint(0, len(b)):], cfg) or a
            else:
                child = rng.choice(elite)
            pop.append(mutate(rng, child, cfg))
    # final ranking: top candidates round-robin among themselves + panel
    cands = []
    for _, p in scored[:25]:
        if flat(p) not in cands: cands.append(flat(p))
    final = sorted(((score(c, panel + cands, cfg, grid), c) for c in cands), key=lambda t: -t[0])
    sig = {}
    for c in hof:
        k = tuple(play(c, o, cfg, grid)["armor"] for o in panel[:40])
        sig.setdefault(k, c)
    diverse = sorted(((score(c, panel, cfg, grid), c) for c in sig.values()), key=lambda t: -t[0])[:12]
    return final, panel, [c for _, c in diverse]

def find_counter(rng, target, cfg, tries):
    """Random search + hill-climb for a program that beats `target`. Returns (density, best)."""
    grid = cfg.grid(); wins = 0; best = None; best_margin = -99; shortest = None
    for _ in range(tries):
        st = rand_program(rng, cfg); c = flat(st)
        r = play(c, target, cfg, grid); m = r["armor"][0] - r["armor"][1]
        if r["winner"] == 0:
            wins += 1
            if shortest is None or len(c) < len(shortest): shortest = c
        if m > best_margin: best_margin, best = m, st
    if wins == 0:                                   # hill-climb from best loser
        cur, cm = best, best_margin
        for _ in range(tries):
            nx = mutate(rng, cur, cfg); r = play(flat(nx), target, cfg, grid)
            m = r["armor"][0] - r["armor"][1]
            if m >= cm: cur, cm = nx, m
            if r["winner"] == 0: shortest = flat(nx); break
    return wins / tries, shortest

def style(p, panel, cfg):
    grid = cfg.grid(); mv = tk = 0
    for o in panel[:40]:
        r = play(p, o, cfg, grid); mv += r["moves"][0]; tk += r["ticks"]
    return mv / tk

def run_variant(name, cfg, rng, quick):
    t0 = time.time()
    print(f"\n=== {name} ===", flush=True)
    ps = population_stats(rng, cfg, 400, 6000 if quick else 20000)
    print(f"random programs : dead rounds {ps['dead']:.0%} | draws {ps['draw']:.0%} | kills {ps['kill']:.0%} | avg ticks {ps['avg_ticks']:.0f}")
    final, panel, diverse = evolve(rng, cfg, 60 if quick else 100, 12 if quick else 22, 60 if quick else 80, log=(name == "baseline"))
    top = [c for _, c in final[:10]]
    grid = cfg.grid()
    print("top evolved programs:")
    for sc, c in final[:5]:
        print(f"  {sc:.3f}  len {len(c)}  mobility {style(c, panel, cfg):.2f}  {show(c)}")
    # elite-vs-elite: is the top of the meta decisive or drawn?
    d = n = dead = 0
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            r = play(top[i], top[j], cfg, grid); n += 1; d += r["winner"] is None; dead += r["first_hit"] is None
    print(f"elite vs elite  : draws {d / n:.0%} | dead rounds {dead / n:.0%}   (converged clones - mirror-ish)")
    d2 = n2 = dead2 = k2 = 0
    for i in range(len(diverse)):
        for j in range(i + 1, len(diverse)):
            r = play(diverse[i], diverse[j], cfg, grid); n2 += 1; d2 += r["winner"] is None; dead2 += r["first_hit"] is None; k2 += r["kill"]
    if n2: print(f"diverse strong programs ({len(diverse)}): draws {d2 / n2:.0%} | no shot lands {dead2 / n2:.0%} | kills {k2 / n2:.0%}")
    use = Counter(c for p in top for c in set(p))
    print("card usage in top 10:", ", ".join(f"{NAMES[c]} {use[c]}" for c in sorted(use, key=lambda c: -use[c])))
    print(f"avg length top 10: {sum(map(len, top)) / len(top):.1f} of {cfg.slots} slots")
    dens = []; uncountered = 0
    for c in top[:5]:
        den, sh = find_counter(rng, c, cfg, 1500 if quick else 4000)
        dens.append(den); uncountered += sh is None
    print(f"counterability  : top-5 each beaten by {min(dens):.1%}-{max(dens):.1%} of random programs; uncounterable: {uncountered}/5")
    print(f"({time.time() - t0:.0f}s)", flush=True)
    return dict(name=name, pop=ps, top=[show(c) for c in top[:5]], elite_draw=d / n, counter=dens)

if __name__ == "__main__":
    quick = "--quick" in sys.argv
    rng = random.Random(7)
    variants = [("baseline", Config())]
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--sweep" in sys.argv:
        variants += [
            ("flank damage 1 (no flank bonus)", Config(flank_dmg=1)),
            ("6 slots", Config(slots=6)),
            ("10 slots", Config(slots=10)),
            ("60 ticks", Config(max_ticks=60)),
            ("6x6 board, 2 pillars", Config(size=6, walls=((1, 4), (4, 1)))),
            ("centre scoring zone (8x8)", Config(zone=((3, 3), (4, 3), (3, 4), (4, 4)))),
            ("centre zone + 6x6", Config(size=6, walls=((1, 4), (4, 1)), zone=((2, 2), (3, 2), (2, 3), (3, 3)))),
            ("asymmetric start (B faces W)", Config(b_facing=3)),
        ]
    if only: variants = [v for v in variants if any(o in v[0] for o in only)]
    out = [run_variant(n, c, rng, quick) for n, c in variants]
    json.dump(out, open("results.json", "w"), indent=1)
