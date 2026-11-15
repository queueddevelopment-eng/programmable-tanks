"""
experiments7.py - stuck rounds: how often does a round stall with no engagement, why, and what fixes it?

Setup = the v0.4 draft as played in the viewer: chassis + dealt hand of 5 from a shared deck
(v0.2 kit + Otherwise x2 per player + rare specials), two pit stops, v0.3 Hunt and wall rules,
on each of the viewer's preset boards plus shuffled mirrored layouts.

A round is STUCK if it ends with no damage dealt for its last 20 ticks and nobody destroyed
(the table experience: two tanks doing nothing useful until time runs out).
Cause, read from the trace of the stuck stretch:
  apart   : the tanks never came within 2 squares of each other
  dance   : they came within 2 squares but never lined up a shot
  parked  : at least one tank didn't change square for the whole stretch
  (a round can be parked and apart/dance at once; 'parked' is reported separately)

Variants: A as is; B a 'stalemate pit stop' (an extra pit stop after 8 ticks with no damage, at most 2 extra);
C a mulligan (redraw your hand once); D tank B starts facing west instead of south, which breaks the mirror
(seats alternate between rounds in a match); E = B + D.
F a shot clock: after 10 ticks with no hit, tanks stop reading their programs and engage until someone is hit:
  the tank behind on armor attacks (fire if in sights, else Hunt), the other holds (fire if in sights, else Face enemy);
  level on armor, the roles alternate. G = F + initiative (two tanks driving into the same square: the one with
  initiative gets it, alternating each tick). H = F with the clock at 6 ticks. I = initiative only.
J = F but the attacker drives the shortest route to a firing square; K = J but the tank AHEAD on armor attacks.
L = K with a 15-tick clock; M = J with a 15-tick clock.
With armor level, the first attacker alternates by round (seed parity here).

Usage: python3 experiments7.py [rounds_per_board] [variant letters...]   (default 60)
"""
import random, sys, time, os
from collections import Counter
from dataclasses import replace
from multiprocessing import Pool
from tanksim import *
from experiments import rand_program, flat
from experiments2 import layout
import experiments5 as X

V04 = dict(V02_DECK); V04[ELSE] = 2
SPECIALS = [SHIELD] * 2 + [OVERCH] * 2 + [SPREAD]
PILLARS = ((2, 2), (5, 2), (2, 5), (5, 5))
BOARDS = {
    "Pillars and pits": (PILLARS, ((3, 4), (4, 3))),
    "Four pillars":     (PILLARS, ()),
    "Open board":       ((), ()),
    "Centre block":     (((3, 3), (3, 4), (4, 3), (4, 4)), ()),
    "Moat":             (((3, 3), (4, 4)), ((3, 4), (4, 3), (1, 4), (6, 3))),
    "Shuffled":         None,
}
STALL = 20          # ticks without damage at the end of a round = stuck

def shuffled(rng):
    w = layout(rng, True)
    free = [(x, y) for x in range(8) for y in range(8) if (x, y) not in w and 2 < x + y < 12]
    p = rng.sample(free, 1)[0]
    return w, (p, (7 - p[0], 7 - p[1])) if (7 - p[0], 7 - p[1]) not in w else ()

def stall_info(tr, clock=0, size=8):
    """Classify the final no-damage stretch of a round from its trace."""
    w = size + 2
    last_dmg = 0
    for i, row in enumerate(tr):
        if i and (row[5] != tr[i - 1][5] or row[8] != tr[i - 1][8]): last_dmg = row[0]
    if tr[-1][5] <= 0 or tr[-1][8] <= 0 or tr[-1][0] - last_dmg < (STALL if not clock else clock + 10):
        return None
    stretch = [r for r in tr if r[0] > last_dmg]
    xy = lambda p: (p % w - 1, p // w - 1)
    close = any(max(abs(xy(r[3])[0] - xy(r[6])[0]), abs(xy(r[3])[1] - xy(r[6])[1])) <= 2 for r in stretch)
    parked = len({r[3] for r in stretch}) == 1 or len({r[6] for r in stretch}) == 1
    return dict(cause="dance" if close else "apart", parked=parked, never_hit=last_dmg == 0)

# ---------------------------------------------------------------- fixes
def stops_dynamic(rng, progs, hands, pile, cfg, grid, skills, fixed, stall_stop, max_extra=2):
    """Like experiments5.round_with_stops, but can also call an extra 'stalemate pit stop'
    after `stall_stop` ticks with no damage (counted from the last damage or the last stop)."""
    sched = {0: [], 1: []}; cur = [progs[0], progs[1]]; done = []; extra = 0
    while True:
        tr = []; play(progs[0], progs[1], cfg, grid, trace=tr, patch=sched)
        last = max(done) if done else 0
        nxt = min([t for t in fixed if t > last], default=None)
        if stall_stop and extra < max_extra:
            quiet_since = last
            for i, row in enumerate(tr):
                if row[0] <= last: continue
                if i and (row[5] != tr[i - 1][5] or row[8] != tr[i - 1][8]): quiet_since = row[0]
                if row[0] - quiet_since >= stall_stop:
                    t = row[0] + 1
                    if (nxt is None or t < nxt) and t <= cfg.max_ticks and tr[-1][0] >= row[0]:
                        nxt = t; extra += 1
                    break
        if nxt is None or nxt > tr[-1][0]: break
        done.append(nxt)
        for s in (0, 1):
            if pile: hands[s].append(pile.pop())
        dec = []
        for s in (0, 1):
            opts = X.plays_for(cur[s], hands[s])
            if skills[s] == "novice": opts = rng.sample(opts, min(3, len(opts)))
            best = None; bv = None
            for q, c in [(None, None)] + opts:
                trial = {0: list(sched[0]), 1: list(sched[1])}
                if q is not None: trial[s].append((nxt, q))
                v = X.value(play(progs[0], progs[1], cfg, grid, patch=trial), s)
                if bv is None or v > bv: best, bv = (q, c), v
            dec.append(best)
        for s, (q, c) in enumerate(dec):
            if q is not None: sched[s].append((nxt, q)); hands[s].remove(c); cur[s] = q
    tr = []; r = play(progs[0], progs[1], cfg, grid, trace=tr, patch=sched)
    return r, tr, done

VARIANTS = {
    "A": ("v0.4 as is",                                dict()),
    "B": ("+ stalemate pit stop after 8 quiet ticks",  dict(stall_stop=8)),
    "C": ("+ mulligan: redraw a hand once",            dict(mulligan=True)),
    "D": ("+ B starts facing west (mirror breaker)",   dict(b_facing=3)),
    "E": ("B + D",                                     dict(stall_stop=8, b_facing=3)),
    "F": ("+ shot clock (10 quiet ticks), behind attacks / leader holds", dict(shot_clock=10, roles=True)),
    "G": ("F + initiative on contested squares",       dict(shot_clock=10, roles=True, initiative=True)),
    "H": ("shot clock at 6 quiet ticks, with roles",   dict(shot_clock=6, roles=True)),
    "I": ("initiative on contested squares only",      dict(initiative=True)),
    "J": ("shot clock 10, behind attacks, attacker pathfinds",  dict(shot_clock=10, roles=True, path=True)),
    "K": ("shot clock 10, LEADER attacks, attacker pathfinds",  dict(shot_clock=10, roles=True, path=True, leader=True)),
    "L": ("K with the clock at 15 ticks",                       dict(shot_clock=15, roles=True, path=True, leader=True)),
    "M": ("J with the clock at 15 ticks",                       dict(shot_clock=15, roles=True, path=True)),
}

def one_round(args):
    vk, bname, kind, seed = args
    opt = VARIANTS[vk][1]
    rng = random.Random(seed)
    if BOARDS[bname] is None: walls, pits = shuffled(random.Random(seed ^ 0xBEEF))
    else: walls, pits = BOARDS[bname]
    deck = dict(V04)
    for c in SPECIALS: deck[c] = deck.get(c, 0) + 1
    cfg = Config(deck=deck, cooldown=1, build_behind=True, hunt_avoid=True, walls=walls, pits=pits,
                 b_facing=opt.get("b_facing", 2), shot_clock=opt.get("shot_clock", 0),
                 clock_roles=opt.get("roles", False), initiative=opt.get("initiative", False),
                 clock_path=opt.get("path", False), clock_leader=opt.get("leader", False), clock_first=seed % 2)
    grid = cfg.grid()
    brng = random.Random(77)
    bcfg = replace(cfg, deck=dict(V04))
    bench = X.STARTERS + [flat(rand_program(brng, bcfg)) for _ in range(4)]
    spar = [flat(rand_program(brng, bcfg)) for _ in range(4)]
    skills = {"EvE": ("expert", "expert"), "EvN": ("expert", "novice"), "NvE": ("novice", "expert"), "NvN": ("novice", "novice")}[kind]
    pile = shared_deck(V04) + list(SPECIALS); rng.shuffle(pile)
    hands = [[pile.pop() for _ in range(X.HAND)] for _ in (0, 1)]
    progs = []; redrew = 0
    for s in (0, 1):
        avail = {c: CHASSIS.get(c, 0) + hands[s].count(c) for c in cfg.deck}
        p, q = X.build(rng, avail, cfg, grid, bench, spar, skills[s])
        if opt.get("mulligan") and (q < 0.5 if skills[s] == "expert" else rng.random() < 0.3):
            pile = [*hands[s], *pile]; rng.shuffle(pile)                 # shuffle the hand back, draw a new one
            hands[s] = [pile.pop() for _ in range(X.HAND)]; redrew += 1
            avail = {c: CHASSIS.get(c, 0) + hands[s].count(c) for c in cfg.deck}
            p, q = X.build(rng, avail, cfg, grid, bench, spar, skills[s])
        progs.append(p)
        left = Counter(hands[s])
        for c, k in Counter(p).items(): left[c] -= max(0, k - CHASSIS.get(c, 0))
        hands[s] = [c for c, k in left.items() for _ in range(max(0, k))]
    r, tr, stops = stops_dynamic(rng, progs, hands, pile, cfg, grid, skills, X.STOPS, opt.get("stall_stop"))
    t20 = next((row for row in tr if row[0] == 20), tr[-1])
    return vk, bname, kind, dict(r=r, trail=(t20[5], t20[8]), stall=stall_info(tr, cfg.shot_clock), stops=len(stops), redrew=redrew, progs=[show(p) for p in progs])

def report(vk, rows):
    print(f"\n=== {vk}. {VARIANTS[vk][0]} ===")
    print(f"{'board':18} {'stuck':>6} {'never hit':>10} {'kills':>6} {'draws':>6}")
    tot = Counter()
    for b in BOARDS:
        rs = [o for (bb, k, o) in rows if bb == b]
        if not rs: continue
        n = len(rs); st = sum(o["stall"] is not None for o in rs)
        nh = sum(o["r"]["first_hit"] is None for o in rs); kl = sum(o["r"]["kill"] for o in rs); dr = sum(o["r"]["winner"] is None for o in rs)
        print(f"{b:18} {st/n:>6.0%} {nh/n:>10.0%} {kl/n:>6.0%} {dr/n:>6.0%}")
        tot.update(n=n, st=st, nh=nh, kl=kl, dr=dr)
    n = tot["n"]
    print(f"{'ALL':18} {tot['st']/n:>6.0%} {tot['nh']/n:>10.0%} {tot['kl']/n:>6.0%} {tot['dr']/n:>6.0%}")
    stuck = [o for (b, k, o) in rows if o["stall"]]
    if stuck:
        c = Counter(o["stall"]["cause"] for o in stuck); pk = sum(o["stall"]["parked"] for o in stuck)
        print(f"why stuck: never within 2 squares {c['apart']/len(stuck):.0%} | close but never lined up {c['dance']/len(stuck):.0%}"
              f" | a tank parked on one square {pk/len(stuck):.0%}")
    for kind, lab in (("EvE", "experts"), ("mix", "expert v novice"), ("NvN", "novices")):
        rs = [o for (b, k, o) in rows if k == kind or (kind == "mix" and k in ("EvN", "NvE"))]
        if rs: print(f"   {lab}: stuck {sum(o['stall'] is not None for o in rs)/len(rs):.0%}", end="")
    print()
    mix = [(k, o) for (b, k, o) in rows if k in ("EvN", "NvE")]
    ex = sum(1 if o["r"]["winner"] == (0 if k == "EvN" else 1) else 0.5 if o["r"]["winner"] is None else 0 for k, o in mix) / len(mix)
    cb = [o for (b, k, o) in rows if k == "EvE" and o.get("trail") and o["trail"][0] != o["trail"][1]]
    if cb: print(f"comebacks: expert behind on armor at tick 20 still wins {sum(o['r']['winner'] == (0 if o['trail'][0] < o['trail'][1] else 1) for o in cb)/len(cb):.0%} ({len(cb)} rounds)")
    dec = [o for (b, k, o) in rows if k in ("EvE", "NvN") and o["r"]["winner"] is not None]
    seat = sum(o["r"]["winner"] == 0 for o in dec) / max(len(dec), 1)
    print(f"skill: expert takes {ex:.0%} of points vs novice | seat fairness: tank A wins {seat:.0%} of decided even matchups ({len(dec)})", end="")
    ex_st = sum(o["stops"] for (b, k, o) in rows) / len(rows)
    if VARIANTS[vk][1].get("shot_clock"):
        ot = [o["r"]["overtime"] for (b, k, o) in rows]
        print(f" | shot clock ran out in {sum(x > 0 for x in ot)/len(ot):.0%} of rounds, {sum(ot)/len(ot):.1f} ticks of auto-engage per round", end="")
        hits = sum(sum(o["r"]["hits"]) for (b, k, o) in rows); oth = sum(o["r"]["overtime_hits"] for (b, k, o) in rows)
        fh = [o["r"]["first_hit"] for (b, k, o) in rows if o["r"]["first_hit"]]
        print(f"\nautopilot share  : {oth/max(hits,1):.0%} of all hits landed while the shot clock had taken over"
              f" | median first hit at tick {sorted(fh)[len(fh)//2] if fh else '-'}", end="")
    print(f" | pit stops per round {ex_st:.1f}" + (f" | hands redrawn per round {sum(o['redrew'] for (b,k,o) in rows)/len(rows):.2f}" if VARIANTS[vk][1].get("mulligan") else ""))
    for o in stuck[:3]: print("   stuck e.g.", o["progs"][0], "  vs  ", o["progs"][1], f"[{o['stall']['cause']}{', parked' if o['stall']['parked'] else ''}]")

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    keys = [a for a in sys.argv[2:]] or list(VARIANTS)
    t0 = time.time(); jobs = []
    for vk in keys:
        for bi, b in enumerate(BOARDS):
            for k in range(N):
                kind = ("EvE", "EvN", "NvN", "EvE", "NvE", "NvN")[k % 6]     # experts sit in both seats
                jobs.append((vk, b, kind, bi * 10**5 + k))      # same seeds for every variant: paired comparison
    res = {}
    with Pool() as pool:
        for vk, b, kind, o in pool.imap_unordered(one_round, jobs, chunksize=3): res.setdefault(vk, []).append((b, kind, o))
    for vk in keys: report(vk, res[vk])
    print(f"\n({time.time()-t0:.0f}s, {N} rounds per board per variant; mix of expert-expert, expert-novice, novice-novice)")
