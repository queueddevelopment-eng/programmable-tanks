"""
experiments8.py - E2: stalls under card-language overtime (decision m).

Question: with overtime written as two printed card programs (the attacker runs
`If in sights . Fire . Otherwise . Hunt`, the holder `If in sights . Fire . Otherwise . Face enemy`),
how often does a round stall on each layout of the deck, and does the seat stay fair?
The pathfinding attacker (clock_path) is the comparison, not a candidate: it is not paper-executable (m).

Setup = the v0.5 draft as the viewer plays it (RULESETS.v4): chassis + a dealt hand of 5 from the 47-card
shared deck (v0.3 kit + Otherwise x2 + If pickup ahead x1 per player, plus Shield x2, Overcharge x2,
Spread shot x1 in the pile), two pit stops (before ticks 11 and 21), the v0.3 Hunt and wall rules, a
10-tick shot clock with roles: the tank AHEAD on armor attacks; level on armor, the first attacker
alternates by round (seed parity). Pickups off. Boards: the viewer's five presets plus shuffled mirrored
layouts (Shuffled is a generator, reported as a stress row and not judged).

Variants (letters; V is the rule as written and the control):
  K  comparison: clock_path (route search), the engine's own overtime, not paper
  V  the rule (m): attack `IF_ENEMY FIRE ELSE HUNT`, hold `IF_ENEMY FIRE ELSE TRACK`
  P  attacker turns when blocked: attack `IF_ENEMY FIRE IF_BLOCKED RIGHT HUNT`, hold as V
  Q  moving holder: attack as V, hold `IF_ENEMY FIRE ELSE TRACK HUNT`
  R  P's attacker + Q's holder

Metrics, per layout (layout_score, reused by E5): N; stuck % (experiments7.stall_info: the round ends with
clock+10 = 20 ticks of no damage and nobody destroyed), split into apart / dance / parked; seat % (tank A
wins / decided EvE+NvN) with its decided count; kills %; draws %; never hit %; overtime pit falls per round;
autopilot share (hits landed while the clock had taken over / all hits).
Per variant: stuck by pairing, expert skill share, comebacks, clock ran out %, overtime ticks per round.
Mechanism, per stuck round: seed, layout, pairing, attacker seat, armor, and the cycle period of
(square, facing) for both tanks over the tail of the quiet stretch, plus the squares each tank visited.

Pass line (docs/PLAN-2026-11.md row E2, fixed before the run, never moved): a layout is KEPT iff stuck <= 2%
at N >= 300 per layout AND seat fairness 45-55%. At 60 per layout one stuck round is 1.7%, so 60/layout can
only FAIL the line, never pass it; the 300/layout run decides.
Stage 2 screen rule: drop any variant whose ALL stuck > V's.
Guard rails for adopting an alternative program (P, Q, R): kills >= V-10 points, autopilot share <= 28%,
expert skill share within 10 points of V. A stall "fixed" by an overtime pit fall is reported as such.
Noise: at 60 per cell treat differences under ~10 points as noise (j).

Usage: python experiments8.py <rounds_per_board> <letters...> [offset=<int>] [boards=<i,j,...>]
  e.g. python experiments8.py 60 K V P Q R                      stage 2 screen
       python experiments8.py 300 K V                           stage 3 decision
       python experiments8.py 300 V offset=50000 boards=1,2,3,4  stage 4: kept presets on fresh seeds
Seeds are a function of (board index, round index) only, plus the optional offset, so every variant plays the
same deals; offset=0 and all boards is the default and reproduces results8.txt / results8b.txt exactly.
boards= takes indices into BOARDS order: 0 Pillars and pits, 1 Four pillars, 2 Open board, 3 Centre block, 4 Moat, 5 Shuffled.
"""
import random, sys, time
from collections import Counter
from dataclasses import replace
from multiprocessing import Pool
from tanksim import *
from experiments import rand_program, flat
import experiments5 as X
from experiments7 import BOARDS, shuffled, stall_info, stops_dynamic

V05 = dict(V03_DECK); V05[ELSE] = 2; V05[IF_PWR] = 1          # per-player kit; viewer RULESETS.v4.deck minus specials
SPECIALS = [SHIELD] * 2 + [OVERCH] * 2 + [SPREAD]              # viewer RULESETS.v4.rarity: in the pile once each
PRESETS = [b for b in BOARDS if BOARDS[b] is not None]         # the layout deck for E2; Shuffled is a stress row
ATTACK = "IF_ENEMY FIRE ELSE HUNT"
HOLD = "IF_ENEMY FIRE ELSE TRACK"
KINDS = ("EvE", "EvN", "NvN", "EvE", "NvE", "NvN")             # as experiments7: experts sit in both seats

VARIANTS = {
    "K": ("comparison: pathfinding attacker (clock_path), not paper",
          dict(clock_path=True)),
    "V": ("the rule as written (m): attack IF_ENEMY FIRE ELSE HUNT | hold IF_ENEMY FIRE ELSE TRACK",
          dict(clock_cards=True, clock_attack=ATTACK, clock_hold=HOLD)),
    "P": ("attacker turns when blocked: attack IF_ENEMY FIRE IF_BLOCKED RIGHT HUNT | hold as V",
          dict(clock_cards=True, clock_attack="IF_ENEMY FIRE IF_BLOCKED RIGHT HUNT", clock_hold=HOLD)),
    "Q": ("moving holder: attack as V | hold IF_ENEMY FIRE ELSE TRACK HUNT",
          dict(clock_cards=True, clock_attack=ATTACK, clock_hold="IF_ENEMY FIRE ELSE TRACK HUNT")),
    "R": ("P's attacker + Q's holder",
          dict(clock_cards=True, clock_attack="IF_ENEMY FIRE IF_BLOCKED RIGHT HUNT", clock_hold="IF_ENEMY FIRE ELSE TRACK HUNT")),
}

# ---------------------------------------------------------------- trace readers
def sq(p, w=10):
    """Padded grid index -> 'C4' style square."""
    return "ABCDEFGH"[p % w - 1] + str(p // w)

def clock_timeline(tr, cfg):
    """Per trace row: was the shot clock out on that tick? Recomputed from armor changes, as stall_info does.
    (A shielded hit that costs no armor also resets the engine's clock but is invisible here, so in rare
    rounds this is off by a period. r['overtime'] from the engine is exact and is what the summary uses.)
    Returns (list of bools, number of overtime periods)."""
    out = []; last = 0; periods = 0; was = False; prev = (cfg.armor, cfg.armor)
    for row in tr:
        co = bool(cfg.shot_clock) and row[0] - 1 - last >= cfg.shot_clock
        if co and not was: periods += 1
        was = co; out.append(co)
        if (row[5], row[8]) != prev: last = row[0]
        prev = (row[5], row[8])
    return out, periods

def attacker_at_end(tr, cfg, periods):
    """Which seat the engine made the attacker in the final period (clock_leader rules)."""
    a, b = tr[-1][5], tr[-1][8]
    if a == b: return (max(periods, 1) - 1 + cfg.clock_first) % 2
    return 0 if a > b else 1

def overtime_falls(tr, cfg, out):
    """Pit falls while the clock was out: a tank changed square onto a pit on an overtime tick."""
    w = cfg.size + 2; pits = {(y + 1) * w + (x + 1) for (x, y) in cfg.pits}
    n = 0
    for i in range(1, len(tr)):
        if not out[i]: continue
        for j in (3, 6):
            if tr[i][j] != tr[i - 1][j] and tr[i][j] in pits: n += 1
    return n

def cycle(tr, last_dmg, tail=16):
    """Smallest period of the (posA, dA, posB, dB) sequence over the last `tail` ticks of the quiet stretch.
    1 = both tanks frozen; None = no repetition found in the window."""
    states = [(r[3], r[4], r[6], r[7]) for r in tr if r[0] > last_dmg][-tail:]
    for p in range(1, len(states) // 2 + 1):
        if all(states[i] == states[i + p] for i in range(len(states) - p)): return p
    return None

def mechanism(tr, cfg):
    """Why this round was stuck: attacker seat, cycle period, squares visited in the quiet stretch."""
    out, periods = clock_timeline(tr, cfg)
    last = 0; prev = (cfg.armor, cfg.armor)
    for row in tr:
        if (row[5], row[8]) != prev: last = row[0]
        prev = (row[5], row[8])
    stretch = [r for r in tr if r[0] > last]
    return dict(attacker="AB"[attacker_at_end(tr, cfg, periods)], armor=(tr[-1][5], tr[-1][8]),
                period=cycle(tr, last), periods=periods, quiet=len(stretch),
                a_sq=sorted({sq(r[3]) for r in stretch}), b_sq=sorted({sq(r[6]) for r in stretch}),
                a_face=sorted({"NESW"[r[4]] for r in stretch}), b_face=sorted({"NESW"[r[7]] for r in stretch}))

# ---------------------------------------------------------------- one round
def one_round(args):
    vk, bname, kind, seed = args
    opt = VARIANTS[vk][1]
    rng = random.Random(seed)
    if BOARDS[bname] is None: walls, pits = shuffled(random.Random(seed ^ 0xBEEF))
    else: walls, pits = BOARDS[bname]
    deck = dict(V05)
    for c in SPECIALS: deck[c] = deck.get(c, 0) + 1
    cfg = Config(deck=deck, cooldown=1, build_behind=True, hunt_avoid=True, walls=walls, pits=pits,
                 shot_clock=10, clock_roles=True, clock_leader=True, clock_first=seed % 2, initiative=False, **opt)
    grid = cfg.grid()
    brng = random.Random(77)
    bcfg = replace(cfg, deck=dict(V05))
    bench = X.STARTERS + [flat(rand_program(brng, bcfg)) for _ in range(4)]
    spar = [flat(rand_program(brng, bcfg)) for _ in range(4)]
    skills = {"EvE": ("expert", "expert"), "EvN": ("expert", "novice"), "NvE": ("novice", "expert"), "NvN": ("novice", "novice")}[kind]
    pile = shared_deck(V05) + list(SPECIALS); rng.shuffle(pile)
    assert len(pile) + 0 == 47, len(pile)
    hands = [[pile.pop() for _ in range(X.HAND)] for _ in (0, 1)]
    progs = []
    for s in (0, 1):
        avail = {c: CHASSIS.get(c, 0) + hands[s].count(c) for c in cfg.deck}
        p, q = X.build(rng, avail, cfg, grid, bench, spar, skills[s])
        progs.append(p)
        left = Counter(hands[s])
        for c, k in Counter(p).items(): left[c] -= max(0, k - CHASSIS.get(c, 0))
        hands[s] = [c for c, k in left.items() for _ in range(max(0, k))]
    r, tr, stops = stops_dynamic(rng, progs, hands, pile, cfg, grid, skills, X.STOPS, None)
    t20 = next((row for row in tr if row[0] == 20), tr[-1])
    out, periods = clock_timeline(tr, cfg)
    stall = stall_info(tr, cfg.shot_clock)
    o = dict(r=r, trail=(t20[5], t20[8]), stall=stall, stops=len(stops), seed=seed,
             ot_falls=overtime_falls(tr, cfg, out), progs=[show(p) for p in progs])
    if stall: o["mech"] = mechanism(tr, cfg)
    return vk, bname, kind, o

# ---------------------------------------------------------------- scoring
def layout_score(rs):
    """Per-layout scorecard from a list of round dicts. Fractions, plus the counts they rest on."""
    n = len(rs)
    st = [o for o in rs if o["stall"]]
    dec = [o for o in rs if o["kind"] in ("EvE", "NvN") and o["r"]["winner"] is not None]
    hits = sum(sum(o["r"]["hits"]) for o in rs); oth = sum(o["r"]["overtime_hits"] for o in rs)
    return dict(n=n, stuck=len(st) / n,
                apart=sum(o["stall"]["cause"] == "apart" for o in st) / n,
                dance=sum(o["stall"]["cause"] == "dance" for o in st) / n,
                parked=sum(o["stall"]["parked"] for o in st) / n,
                seat=sum(o["r"]["winner"] == 0 for o in dec) / max(len(dec), 1), dec=len(dec),
                kills=sum(o["r"]["kill"] for o in rs) / n, draws=sum(o["r"]["winner"] is None for o in rs) / n,
                never_hit=sum(o["r"]["first_hit"] is None for o in rs) / n,
                ot_falls=sum(o["ot_falls"] for o in rs) / n, autopilot=oth / max(hits, 1))

def verdict(s, judged=True):
    if not judged: return "stress row"
    if s["stuck"] > 0.02: return "FAIL stuck"
    if s["n"] < 300: return "open (N<300)"
    return "KEEP" if 0.45 <= s["seat"] <= 0.55 else "FAIL seat"

def report(vk, rows):
    print(f"\n=== {vk}. {VARIANTS[vk][0]} ===")
    print(f"{'layout':18} {'N':>4} {'stuck':>6} {'apart':>6} {'dance':>6} {'parked':>6} {'seat':>5} {'(dec)':>5} "
          f"{'kills':>6} {'draws':>6} {'nohit':>6} {'otfall':>6} {'auto':>5}  verdict")
    allrows = []; npre = 0
    for b in BOARDS:
        rs = [dict(o, kind=k) for (bb, k, o) in rows if bb == b]
        if not rs: continue
        s = layout_score(rs)
        if b in PRESETS: allrows += rs; npre += 1
        print(f"{b:18} {s['n']:>4} {s['stuck']:>6.1%} {s['apart']:>6.1%} {s['dance']:>6.1%} {s['parked']:>6.1%} "
              f"{s['seat']:>5.0%} {s['dec']:>5} {s['kills']:>6.0%} {s['draws']:>6.0%} {s['never_hit']:>6.0%} "
              f"{s['ot_falls']:>6.2f} {s['autopilot']:>5.0%}  {verdict(s, b in PRESETS)}")
    s = layout_score(allrows)
    print(f"{f'ALL ({npre} presets)':18} {s['n']:>4} {s['stuck']:>6.1%} {s['apart']:>6.1%} {s['dance']:>6.1%} {s['parked']:>6.1%} "
          f"{s['seat']:>5.0%} {s['dec']:>5} {s['kills']:>6.0%} {s['draws']:>6.0%} {s['never_hit']:>6.0%} "
          f"{s['ot_falls']:>6.2f} {s['autopilot']:>5.0%}")
    for kind, lab in (("EvE", "experts"), ("mix", "expert v novice"), ("NvN", "novices")):
        rs = [o for (b, k, o) in rows if k == kind or (kind == "mix" and k in ("EvN", "NvE"))]
        if rs: print(f"   {lab}: stuck {sum(o['stall'] is not None for o in rs)/len(rs):.1%} ({len(rs)})", end="")
    print()
    mix = [(k, o) for (b, k, o) in rows if k in ("EvN", "NvE")]
    ex = sum(1 if o["r"]["winner"] == (0 if k == "EvN" else 1) else 0.5 if o["r"]["winner"] is None else 0 for k, o in mix) / max(len(mix), 1)
    cb = [o for (b, k, o) in rows if k == "EvE" and o["trail"][0] != o["trail"][1]]
    cbw = sum(o["r"]["winner"] == (0 if o["trail"][0] < o["trail"][1] else 1) for o in cb) / max(len(cb), 1)
    ot = [o["r"]["overtime"] for (b, k, o) in rows]
    hits = sum(sum(o["r"]["hits"]) for (b, k, o) in rows); oth = sum(o["r"]["overtime_hits"] for (b, k, o) in rows)
    fh = sorted(o["r"]["first_hit"] for (b, k, o) in rows if o["r"]["first_hit"])
    print(f"skill: expert takes {ex:.0%} of points vs novice ({len(mix)}) | comebacks: expert behind at tick 20 wins {cbw:.0%} ({len(cb)})")
    print(f"rule fired: shot clock ran out in {sum(x > 0 for x in ot)/len(ot):.0%} of rounds | {sum(ot)/len(ot):.1f} overtime ticks per round"
          f" | autopilot share {oth/max(hits,1):.0%} of {hits} hits | median first hit tick {fh[len(fh)//2] if fh else '-'}"
          f" | overtime pit falls {sum(o['ot_falls'] for (b,k,o) in rows)/len(rows):.2f} per round"
          f" | pit stops per round {sum(o['stops'] for (b,k,o) in rows)/len(rows):.1f}")
    stuck = [(b, k, o) for (b, k, o) in rows if o["stall"]]
    if stuck:
        per = Counter(o["mech"]["period"] for (b, k, o) in stuck)
        print(f"stuck mechanism: {len(stuck)} rounds; cycle period of (square, facing) over the last 16 quiet ticks: "
              + ", ".join(f"{p if p else 'none'}x{c}" for p, c in sorted(per.items(), key=lambda t: (t[0] is None, t[0]))))
        for b, k, o in sorted(stuck, key=lambda t: (t[0], t[2]["seed"]))[:40]:
            m = o["mech"]; st = o["stall"]
            print(f"   seed {o['seed']:>6} {b:16} {k} attacker {m['attacker']} armor {m['armor']} period {m['period']} "
                  f"quiet {m['quiet']} [{st['cause']}{', parked' if st['parked'] else ''}{', never hit' if st['never_hit'] else ''}]"
                  f" A@{'/'.join(m['a_sq'])}{''.join(m['a_face'])} B@{'/'.join(m['b_sq'])}{''.join(m['b_face'])}")
            print(f"          {o['progs'][0]}   vs   {o['progs'][1]}")
    return dict(all=s, skill=ex)

def guard_rails(summ):
    """Stage-2 screen and adoption guard rails, all relative to V (the rule as written)."""
    if "V" not in summ: return
    v = summ["V"]
    print("\n=== screen and guard rails vs V ===")
    for vk, s in summ.items():
        if vk == "V": continue
        a = s["all"]; notes = []
        if a["stuck"] > v["all"]["stuck"]: notes.append("DROP: ALL stuck > V")
        if a["kills"] < v["all"]["kills"] - 0.10: notes.append("guard: kills < V-10")
        if a["autopilot"] > 0.28: notes.append("guard: autopilot share > 28%")
        if abs(s["skill"] - v["skill"]) > 0.10: notes.append("guard: skill share moved > 10 from V")
        print(f"{vk}: stuck {a['stuck']:.1%} vs {v['all']['stuck']:.1%} | kills {a['kills']:.0%} vs {v['all']['kills']:.0%}"
              f" | autopilot {a['autopilot']:.0%} | skill {s['skill']:.0%} vs {v['skill']:.0%}  {'; '.join(notes) or 'clear'}")

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    opts = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    keys = [a for a in sys.argv[2:] if "=" not in a] or list(VARIANTS)
    offset = int(opts.get("offset", 0))                                  # fresh seeds for a confirmation run
    which = [int(i) for i in opts["boards"].split(",")] if "boards" in opts else list(range(len(BOARDS)))
    t0 = time.time(); jobs = []
    for vk in keys:
        for bi, b in enumerate(BOARDS):
            if bi not in which: continue
            for k in range(N):
                jobs.append((vk, b, KINDS[k % 6], bi * 10**5 + k + offset))   # same seeds for every variant: paired comparison
    res = {}
    with Pool() as pool:
        for vk, b, kind, o in pool.imap_unordered(one_round, jobs, chunksize=3): res.setdefault(vk, []).append((b, kind, o))
    summ = {vk: report(vk, res[vk]) for vk in keys}
    guard_rails(summ)
    print(f"\n({time.time()-t0:.0f}s, {N} rounds per board per variant, {len(jobs)} rounds, seed offset {offset}, "
          f"boards {','.join(str(i) for i in which)}; pairings cycle {' '.join(KINDS)})")
