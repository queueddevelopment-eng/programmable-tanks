"""
experiments6.py - v0.4 ideas on top of the v0.3 core (chassis + dealt hand + two pit stops):
  B. Otherwise (ELSE) card      : a plain control card, 2 per player in the shared deck
  C. rare special cards         : one-shot Shield x2, Overcharge x2, Spread shot x1 shuffled into the shared deck
  D. pre-placed pickups         : one mirrored pair on the board, visible before programming, same kind both sides
                                  (shield charge, overcharge, or next Fire is a spread shot), plus If pickup ahead x1 each
  E. Otherwise + pickups

The question for C and D: does luck (holding a special, grabbing a pickup) start deciding games?
Same expert / novice proxies as experiments5.py.

Usage: python3 experiments6.py [rounds_per_pairing] [variant letters...]   (default 100)
"""
import random, sys, time
from collections import Counter
from dataclasses import replace
from multiprocessing import Pool
from tanksim import *
from experiments import rand_program, flat
import experiments5 as X

BASE = Config(deck=dict(V02_DECK), cooldown=1, build_behind=True, hunt_avoid=True)
ELSE_DECK = dict(V02_DECK); ELSE_DECK[ELSE] = 2
PWR_DECK = dict(V02_DECK); PWR_DECK[IF_PWR] = 1
BOTH_DECK = dict(ELSE_DECK); BOTH_DECK[IF_PWR] = 1
SPECIALS = [SHIELD] * 2 + [OVERCH] * 2 + [SPREAD]
STOPS = X.STOPS; HAND = X.HAND

VARIANTS = [   # name, per-player deck, extra cards in the pile, pickups on the board
    ("A  v0.3 core (control)",       dict(V02_DECK), [],       False),
    ("B  + Otherwise card",          ELSE_DECK,      [],       False),
    ("C  + rare specials in the deck", dict(V02_DECK), SPECIALS, False),
    ("D  + pre-placed pickups",      PWR_DECK,       [],       True),
    ("E  + Otherwise + pickups",     BOTH_DECK,      [],       True),
]
KIND_NAME = {"S": "shield", "D": "overcharge", "X": "spread"}

def pickup_pair(rng, walls):
    while True:
        x, y = rng.randrange(8), rng.randrange(8)
        mx, my = 7 - x, 7 - y
        if (x, y) in walls or (x, y) == (mx, my): continue
        if max(x, y) <= 2 or min(x, y) >= 5: continue          # not on top of a start corner
        k = rng.choice("SDX")
        return ((x, y, k), (mx, my, k))

def one_round(args):
    vi, kind, seed = args
    name, deck, extra, pickups = VARIANTS[vi]
    rng = random.Random(seed)
    cfg = replace(BASE, deck=dict(deck))
    if extra:
        d = dict(deck)
        for c in extra: d[c] = d.get(c, 0) + 1                # so programs may hold what was dealt
        cfg = replace(cfg, deck=d)
    if pickups:
        cfg = replace(cfg, powerups=pickup_pair(rng, cfg.walls))
    grid = cfg.grid()
    brng = random.Random(1000 + vi)
    bcfg = replace(cfg, deck=dict(deck))
    bench = X.STARTERS + [flat(rand_program(brng, bcfg)) for _ in range(4)]
    spar = [flat(rand_program(brng, bcfg)) for _ in range(4)]
    skills = {"EvE": ("expert", "expert"), "EvN": ("expert", "novice"), "NvE": ("novice", "expert"),
              "NvN": ("novice", "novice")}[kind]
    pile = shared_deck(deck) + list(extra); rng.shuffle(pile)
    hands = [[pile.pop() for _ in range(HAND)] for _ in (0, 1)]
    seen = [sum(c in ONESHOT for c in h) for h in hands]
    draws = pile[::-1][:2 * len(STOPS)]                      # who will draw what at the pit stops
    for i, c in enumerate(draws): seen[i % 2] += c in ONESHOT
    progs, qual = [], []
    for s in (0, 1):
        avail = {c: CHASSIS.get(c, 0) + hands[s].count(c) for c in cfg.deck}
        p, q = X.build(rng, avail, cfg, grid, bench, spar, skills[s])
        progs.append(p); qual.append(q)
        left = Counter(hands[s])
        for c, k in Counter(p).items(): left[c] -= max(0, k - CHASSIS.get(c, 0))
        hands[s] = [c for c, k in left.items() for _ in range(max(0, k))]
    base = play(progs[0], progs[1], cfg, grid)
    r, sched, log = X.round_with_stops(rng, progs, hands, pile, cfg, grid, skills, STOPS)
    return vi, dict(kind=kind, skills=skills, qual=qual, final=r, base=base, played=sum(log), stops=len(log),
                    seen=seen, kindpw=cfg.powerups[0][2] if cfg.powerups else None,
                    trail=X.armor_at(progs, cfg, grid, {}, STOPS[-1]), progs=[show(p) for p in progs],
                    prog_cards=[p for p in progs] + [q for s in (0, 1) for (_, q) in sched[s]])

def luck(rows, key):
    """Of decided rounds where the two sides differ on `key`, how often the side with more wins."""
    n = w = 0
    for o in rows:
        a, b = key(o)
        if a == b or o["final"]["winner"] is None: continue
        n += 1; w += (o["final"]["winner"] == 0) == (a > b)
    return (w / n if n else float("nan")), n

def summarize(vi, rows):
    name, deck, extra, pickups = VARIANTS[vi]
    print(f"\n=== {name} ===")
    eve = [o for o in rows if o["kind"] == "EvE"]; nvn = [o for o in rows if o["kind"] == "NvN"]
    mix = [o for o in rows if o["kind"] in ("EvN", "NvE")]; f = lambda o: o["final"]; n = len(eve); m = len(nvn)
    print(f"experts vs experts : kills {sum(f(o)['kill'] for o in eve)/n:.0%} | no shot lands {sum(f(o)['first_hit'] is None for o in eve)/n:.0%}"
          f" | draws {sum(f(o)['winner'] is None for o in eve)/n:.0%} | avg {sum(f(o)['ticks'] for o in eve)/n:.0f} ticks")
    fav, fn = luck(eve, lambda o: o["qual"])
    print(f"skill              : better pre-round program wins {fav:.0%} of decided rounds ({fn})", end="")
    share = sum(1 if f(o)["winner"] == (0 if o["skills"][0] == "expert" else 1) else 0.5 if f(o)["winner"] is None else 0 for o in mix)
    print(f" | expert takes {share/len(mix):.0%} of points vs novices")
    print(f"novices vs novices : a shot lands in {sum(f(o)['first_hit'] is not None for o in nvn)/m:.0%} | kills {sum(f(o)['kill'] for o in nvn)/m:.0%}"
          f" | draws {sum(f(o)['winner'] is None for o in nvn)/m:.0%}")
    cb = cbb = tr = 0
    for o in eve:
        a0, b0 = o["trail"]
        if a0 == b0: continue
        t = 0 if a0 < b0 else 1; tr += 1; cb += f(o)["winner"] == t; cbb += o["base"]["winner"] == t
    if tr: print(f"comebacks          : trailer at the last pit stop wins {cbb/tr:.0%} without pit stops, {cb/tr:.0%} with ({tr} rounds)")
    if extra:
        allr = eve + nvn + mix
        used = Counter(); 
        for o in allr:
            for s in (0, 1):
                for c, k in f(o)["used"][s].items(): used[NAMES[c]] += k
        held = sum(sum(o["seen"]) for o in eve) / n
        lk, ln = luck(eve, lambda o: o["seen"])
        print(f"specials           : {held:.2f} dealt per expert round | used per round: " +
              ", ".join(f"{k} {v/len(allr):.2f}" for k, v in used.most_common()) +
              f" | shield damage soaked {sum(sum(f(o)['absorbed']) for o in allr)/len(allr):.2f}")
        print(f"LUCK               : the expert dealt more specials wins {lk:.0%} of decided rounds ({ln} rounds)")
    if pickups:
        allr = eve + nvn + mix
        took = sum(sum(f(o)["pickups"]) > 0 for o in allr) / len(allr)
        lk, ln = luck(eve, lambda o: o["final"]["pickups"])
        ek = sum(sum(f(o)["pickups"]) for o in eve) / n; nk = sum(sum(f(o)["pickups"]) for o in nvn) / m
        print(f"pickups            : grabbed in {took:.0%} of rounds | per round experts {ek:.2f}, novices {nk:.2f}"
              f" | IF_POWERUP in {sum('IF_POWERUP' in p for o in eve for p in o['progs'])/(2*n):.0%} of expert programs")
        print(f"LUCK               : the expert who grabbed more pickups wins {lk:.0%} of decided rounds ({ln} rounds)")
        byk = Counter(); byn = Counter()
        for o in eve:
            byn[o["kindpw"]] += 1; byk[o["kindpw"]] += f(o)["winner"] is None
        print("draw rate by pickup kind: " + ", ".join(f"{KIND_NAME[k]} {byk[k]/byn[k]:.0%}" for k in byn))
    if deck.get(ELSE):
        print(f"Otherwise          : in {sum('ELSE' in p for o in eve for p in o['progs'])/(2*n):.0%} of expert programs, "
              f"{sum('ELSE' in p for o in nvn for p in o['progs'])/(2*m):.0%} of novice programs")
    use = Counter(c for o in eve for p in o["progs"] for c in set(p.split(" · ")))
    print("cards in expert programs:", ", ".join(f"{c} {use[c]/(2*n):.0%}" for c in sorted(use, key=lambda c: -use[c])))
    for o in [o for o in eve if f(o)["kill"]][:2]: print("   e.g.", o["progs"][0], "  vs  ", o["progs"][1])

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    only = sys.argv[2:]
    t0 = time.time(); jobs = []
    for vi in range(len(VARIANTS)):
        if only and not any(VARIANTS[vi][0].startswith(x) for x in only): continue
        for k in range(N):
            for kind in ("EvE", "NvN"): jobs.append((vi, kind, vi * 10**6 + k * 10 + (kind == "NvN")))
            jobs.append((vi, "EvN" if k % 2 == 0 else "NvE", vi * 10**6 + k * 10 + 5))
    res = {}
    with Pool() as pool:
        for vi, out in pool.imap_unordered(one_round, jobs, chunksize=4): res.setdefault(vi, []).append(out)
    for vi in sorted(res): summarize(vi, res[vi])
    print(f"\n({time.time()-t0:.0f}s, {N} rounds per pairing type per variant)")
