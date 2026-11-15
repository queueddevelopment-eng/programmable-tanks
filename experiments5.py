"""
experiments5.py - the v0.3 ideas:
  1. the board as part of the game : pits (hazard squares) and two board cards,
                                      Raise wall (BUILD) and Breach (BLAST)
  2. a shared draw deck             : a fixed chassis (Fire x2, Hunt, Forward) is always available;
                                      everything else is drawn from one pooled deck. Hand of 5.
  3. pit stops                      : at fixed ticks each tank draws a card and may play one
                                      (insert or replace); the program restarts from its first card.

Players are proxies, the same in every variant so the variants compare fairly:
  expert : the standard strategies its cards allow + 60 random programs + 140 hill-climb steps,
           scored against a bench;
           at a pit stop it tries every legal play and looks ahead (assuming the rival keeps its program).
  novice : best of 6 random programs against 4 sparring programs; at a pit stop it looks ahead
           over only 3 random plays (or skips).
Look-ahead is foresight a real player doesn't have, so pit-stop effects are upper bounds.

Usage: python3 experiments5.py [rounds_per_pairing] [variant letters...]    (default 120)
       TANKS_RULES=draft1 python3 experiments5.py ...   to rerun the first v0.3 draft (wall ahead, old Hunt)
"""
import random, sys, time
from collections import Counter
from dataclasses import replace
from multiprocessing import Pool
from tanksim import *
from experiments import rand_program, flat, mutate

import os
# v0.3 rules (wall raised behind, Hunt avoids walls and pits) unless TANKS_RULES=draft1 (the first v0.3 draft)
NEW_RULES = os.environ.get("TANKS_RULES", "v3") != "draft1"
BASE = Config(deck=dict(V02_DECK), cooldown=1, build_behind=NEW_RULES, hunt_avoid=NEW_RULES)
PITS = ((3, 4), (4, 3))                        # rotationally symmetric pair in the middle
STOPS = (11, 21)                               # pit stops before ticks 11 and 21 (after 10 and 20 ticks)
HAND = 5

VARIANTS = [
    # name,                         cfg,                                     hands, stops
    ("A  fixed kit (baseline)",     BASE,                                    False, False),
    ("B  + pits",                    replace(BASE, pits=PITS),                False, False),
    ("C  + board cards",             replace(BASE, deck=dict(V03_DECK)),      False, False),
    ("D  chassis + drawn hand",      BASE,                                    True,  False),
    ("E  D + 2 pit stops",           BASE,                                    True,  True),
    ("F  full draft: E + pits + board cards",
                                     replace(BASE, pits=PITS, deck=dict(V03_DECK)), True, True),
]

STARTERS = [parse(p) for p in ("WHILE_ENEMY FIRE HUNT", "IF_ENEMY FIRE IF_NEAR BACK HUNT", "WHILE_ENEMY FIRE TRACK",
                               "WHILE_ENEMY FIRE RIGHT", "IF_ENEMY REPEAT3 FIRE FWD IF_BLOCKED RIGHT",
                               "HUNT IF_HIT TRACK IF_ENEMY_BEHIND REPEAT3 RIGHT WHILE_ENEMY FIRE")]

EXPERT_RANDOM, EXPERT_CLIMB = 60, 140
KNOWN = STARTERS + [parse(p) for p in ("HUNT IF_ENEMY FIRE", "IF_ENEMY FIRE HUNT", "WHILE_ENEMY FIRE FWD IF_BLOCKED HUNT",
                                         "IF_HIT TRACK WHILE_ENEMY FIRE HUNT", "IF_ENEMY_BEHIND RIGHT WHILE_ENEMY FIRE HUNT")]

def stmts_of(p):
    """Split a flat program into statements (conditions/loops + their action) for the mutation operators."""
    out, cur = [], []
    for c in p:
        cur.append(c)
        if c in ACTSET: out.append(tuple(cur)); cur = []
    if cur: out.append(tuple(cur))
    return out

def pts(r, side):
    w = r["winner"]
    return 3 if w == side else 1 if w is None else 0

def bench_score(p, cfg, grid, bench):
    s = 0
    for o in bench:
        s += pts(play(p, o, cfg, grid), 0) + pts(play(o, p, cfg, grid), 1)
    return s / (6 * len(bench))

def legal(p):
    if not p or len(p) > 8 or not any(c in ACTSET for c in p): return False
    return all(p[(i + 1) % len(p)] in ACTSET for i, c in enumerate(p) if c in LOOPS)

def build(rng, avail, cfg, grid, bench, spar, skill):
    """Make a program from the multiset `avail`. Returns (program, bench score)."""
    hc = replace(cfg, deck=avail)
    if skill == "novice":
        best, bs = None, -1
        for _ in range(6):
            p = flat(rand_program(rng, hc))
            if not legal(p): continue
            if FIRE not in p or not any(c in p for c in (FWD, HUNT, BACK)): continue
            s = sum(pts(play(p, o, cfg, grid), 0) for o in spar)
            if s > bs: best, bs = p, s
        best = best or flat(rand_program(rng, hc))
        return best, bench_score(best, cfg, grid, bench)
    cands = []
    for p in KNOWN:                             # an expert knows the standard strategies, if its cards allow them
        if all(p.count(c) <= avail.get(c, 0) for c in set(p)) and legal(p):
            cands.append(stmts_of(p))
    for _ in range(EXPERT_RANDOM):
        st = rand_program(rng, hc)
        if legal(flat(st)): cands.append(st)
    scored = [(bench_score(flat(st), cfg, grid, bench), st) for st in cands]
    cur_s, cur = max(scored, key=lambda t: t[0])
    for _ in range(EXPERT_CLIMB):
        nx = mutate(rng, cur, hc)
        if not legal(flat(nx)): continue
        s = bench_score(flat(nx), cfg, grid, bench)
        if s >= cur_s: cur_s, cur = s, nx
    return flat(cur), cur_s

def plays_for(prog, hand):
    """Every legal one-card pit-stop play: (new_program, card_used)."""
    out = []
    for c in set(hand):
        for i in range(len(prog) + 1):
            q = prog[:i] + [c] + prog[i:]
            if legal(q): out.append((q, c))
        for i in range(len(prog)):
            if prog[i] == c: continue
            q = prog[:i] + [c] + prog[i + 1:]
            if legal(q): out.append((q, c))
    return out

def value(r, side):
    return pts(r, side) * 100 + (r["armor"][side] - r["armor"][1 - side])

def round_with_stops(rng, progs, hands, pile, cfg, grid, skills, stops):
    """Play a round, making pit-stop decisions. Returns (result, sched, stop_log)."""
    sched = {0: [], 1: []}; cur = [progs[0], progs[1]]; log = []
    for t in stops:
        for s in (0, 1):
            if pile: hands[s].append(pile.pop())
        decisions = []
        for s in (0, 1):
            opts = plays_for(cur[s], hands[s])
            if skills[s] == "novice": opts = rng.sample(opts, min(3, len(opts)))
            best = None; bv = None
            for q, c in [(None, None)] + opts:
                trial = {0: list(sched[0]), 1: list(sched[1])}
                if q is not None: trial[s].append((t, q))
                r = play(progs[0], progs[1], cfg, grid, patch=trial)
                v = value(r, s)
                if bv is None or v > bv: best, bv = (q, c), v
            decisions.append(best)
        for s, (q, c) in enumerate(decisions):
            if q is not None:
                sched[s].append((t, q)); hands[s].remove(c); cur[s] = q
            log.append(q is not None)
    r = play(progs[0], progs[1], cfg, grid, patch=sched)
    return r, sched, log

def armor_at(progs, cfg, grid, sched, tick):
    tr = []; play(progs[0], progs[1], cfg, grid, trace=tr, patch=sched)
    for row in tr:
        if row[0] == tick - 1: return row[5], row[8]
    return tr[-1][5], tr[-1][8]

def one_round(args):
    vi, kind, seed = args
    name, cfg, hands_on, stops_on = VARIANTS[vi]
    rng = random.Random(seed); grid = cfg.grid()
    brng = random.Random(1000 + vi)            # the same bench and sparring set for every round of a variant
    bench = STARTERS + [flat(rand_program(brng, cfg)) for _ in range(4)]
    spar = [flat(rand_program(brng, cfg)) for _ in range(4)]
    skills = {"EvE": ("expert", "expert"), "EvN": ("expert", "novice"), "NvE": ("novice", "expert"),
              "NvN": ("novice", "novice")}[kind]
    if hands_on:
        pile = shared_deck(cfg.deck); rng.shuffle(pile)
        hands = [[pile.pop() for _ in range(HAND)] for _ in (0, 1)]
        progs, qual = [], []
        for s in (0, 1):
            avail = dict(CHASSIS); avail = {c: avail.get(c, 0) + hands[s].count(c) for c in cfg.deck}
            p, q = build(rng, avail, cfg, grid, bench, spar, skills[s])
            progs.append(p); qual.append(q)
            for c in p:                         # cards used from the hand leave it; chassis cards first
                pass
            used = Counter(p); left = Counter(hands[s])
            for c, k in used.items():
                extra = max(0, k - CHASSIS.get(c, 0))
                left[c] -= extra
            hands[s] = [c for c, k in left.items() for _ in range(max(0, k))]
    else:
        pile, hands = [], [[], []]
        progs, qual = [], []
        for s in (0, 1):
            p, q = build(rng, dict(cfg.deck), cfg, grid, bench, spar, skills[s]); progs.append(p); qual.append(q)
    base = play(progs[0], progs[1], cfg, grid)
    out = dict(kind=kind, skills=skills, qual=qual, identical=progs[0] == progs[1], base=base,
               progs=[show(p) for p in progs])
    if stops_on:
        r, sched, log = round_with_stops(rng, progs, hands, pile, cfg, grid, skills, STOPS)
        out.update(final=r, played=sum(log), stops=len(log),
                   trail_base=armor_at(progs, cfg, grid, {}, STOPS[-1]),
                   cards=[NAMES[q[c]] for s in (0, 1) for (_, q) in sched[s] for c in range(len(q))])
        out["sched"] = {s: [(t, show(q)) for t, q in sched[s]] for s in (0, 1)}
    else:
        out.update(final=base)
    return vi, out

def summarize(vi, rows):
    name, cfg, hands_on, stops_on = VARIANTS[vi]
    print(f"\n=== {name} ===")
    eve = [o for o in rows if o["kind"] == "EvE"]
    nvn = [o for o in rows if o["kind"] == "NvN"]
    mix = [o for o in rows if o["kind"] in ("EvN", "NvE")]
    f = lambda o: o["final"]
    n = len(eve)
    kills = sum(f(o)["kill"] for o in eve); dead = sum(f(o)["first_hit"] is None for o in eve)
    draws = sum(f(o)["winner"] is None for o in eve); ticks = sum(f(o)["ticks"] for o in eve)
    ident = sum(o["identical"] for o in eve)
    print(f"experts vs experts : kills {kills/n:.0%} | no shot lands {dead/n:.0%} | draws {draws/n:.0%} | avg {ticks/n:.0f} ticks"
          f" | identical programs {ident/n:.0%}")
    dec = [o for o in eve if f(o)["winner"] is not None and o["qual"][0] != o["qual"][1]]
    fav = sum((o["qual"][0] > o["qual"][1]) == (f(o)["winner"] == 0) for o in dec)
    if dec: print(f"pre-round favourite: the player whose program scored better against the bench won {fav/len(dec):.0%} of decided rounds")
    share = 0
    for o in mix:
        es = 0 if o["skills"][0] == "expert" else 1; w = f(o)["winner"]
        share += 1 if w == es else 0.5 if w is None else 0
    print(f"skill check        : expert vs novice, expert takes {share/len(mix):.0%} of the points")
    m = len(nvn)
    print(f"novices vs novices : a shot lands in {sum(f(o)['first_hit'] is not None for o in nvn)/m:.0%} of rounds"
          f" | kills {sum(f(o)['kill'] for o in nvn)/m:.0%} | draws {sum(f(o)['winner'] is None for o in nvn)/m:.0%}")
    allr = eve + nvn + mix
    if cfg.pits:
        print(f"pits               : {sum(sum(f(o)['falls']) for o in allr)/len(allr):.2f} falls per round"
              f" (experts {sum(sum(f(o)['falls']) for o in eve)/n:.2f}, novices {sum(sum(f(o)['falls']) for o in nvn)/m:.2f})")
    if cfg.deck.get(BUILD):
        progs = [p for o in allr for p in o["progs"]]
        eprogs = [p for o in eve for p in o["progs"]]
        print(f"board cards        : Raise wall in {sum('BUILD' in p for p in eprogs)/len(eprogs):.0%} of expert programs, "
              f"Breach in {sum('BLAST' in p for p in eprogs)/len(eprogs):.0%}"
              f" | per round: {sum(sum(f(o)['builds']) for o in allr)/len(allr):.2f} walls raised, {sum(sum(f(o)['blasts']) for o in allr)/len(allr):.2f} walls breached")
    if stops_on:
        played = sum(o["played"] for o in allr); stops = sum(o["stops"] for o in allr)
        changed = sum(o["final"]["winner"] != o["base"]["winner"] for o in allr)
        print(f"pit stops          : a card was played at {played/stops:.0%} of stops | result differs from the no-stop round in {changed/len(allr):.0%} of rounds")
        cb = cb_base = trail = 0
        for o in eve:
            a0, b0 = o["trail_base"]
            if a0 == b0: continue
            trailer = 0 if a0 < b0 else 1; trail += 1
            cb += o["final"]["winner"] == trailer; cb_base += o["base"]["winner"] == trailer
        if trail: print(f"comebacks (experts): trailing on armor at the last pit stop, the trailer still wins {cb_base/trail:.0%} without pit stops, {cb/trail:.0%} with them ({trail} rounds)")
        cards = Counter(c for o in eve for s in (0, 1) for (_, q) in o["sched"][s] for c in q.split(" · "))
    use = Counter(c for o in eve for p in o["progs"] for c in set(p.split(" · ")))
    print("cards in expert programs:", ", ".join(f"{c} {use[c]/(2*n):.0%}" for c in sorted(use, key=lambda c: -use[c])))
    ex = [o for o in eve if f(o)["kill"]][:2]
    for o in ex: print("   e.g.", o["progs"][0], "  vs  ", o["progs"][1])

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    only = [a for a in sys.argv[2:]]
    t0 = time.time()
    jobs = []
    for vi in range(len(VARIANTS)):
        if only and not any(VARIANTS[vi][0].startswith(x) for x in only): continue
        for k in range(N):
            for kind in ("EvE", "NvN"):
                jobs.append((vi, kind, vi * 10**6 + k * 10 + (kind == "NvN")))
            jobs.append((vi, "EvN" if k % 2 == 0 else "NvE", vi * 10**6 + k * 10 + 5))
    res = {}
    with Pool() as pool:
        for vi, out in pool.imap_unordered(one_round, jobs, chunksize=4):
            res.setdefault(vi, []).append(out)
    for vi in sorted(res):
        summarize(vi, res[vi])
    print(f"\n({time.time()-t0:.0f}s, {N} rounds per pairing type per variant, rules: {'v0.3' if NEW_RULES else 'first v0.3 draft'})")
