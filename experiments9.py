"""
experiments9.py - E1: the debug rule ("loser rewrites", decision (e)) under dealt hands.

Question: with chassis + dealt hands (v0.5 draft rules, pickups off), which match structure keeps the debug rule
alive? The round winner's rail is LOCKED and reused; the loser rebuilds from the cards the structure gives it.

Match structure (all variants; brief from game-designer 2026-11-24, adopted):
  - first to 3 round wins, capped at 7 rounds; at the cap more wins takes the match, equal wins = match draw;
  - seats fixed, one layout per match; clock_first = (seed + round) % 2;
  - round 1: shuffle the 45-card pile, deal 5 each, both build (experiments5.build, bench as experiments8);
    round 1 (deal, builds, pit stops, result) is computed ONCE per match and shared by every variant;
  - the lock: the winner's rail as it stands at the end of the round (pit-stop plays included), reused unchanged;
    specials start unspent every round (each round is a fresh play());
  - pit stops (experiments5.STOPS, before ticks 11 and 21) run for both players in every round, with the
    existing lookahead (expert: every legal play; novice: 3 random plays) - experiments5.round_with_stops;
  - round change after a decided round: every card not on the winner's rail or in a kept hand (pit-stop
    discards included) is gathered, sorted, shuffled once with Random(f"{seed}:{round}"), then the loser draws;
  - after a drawn round both keep their rails and hands (pile + discards are reshuffled the same way, nobody draws).

Variants (MatchRules; the default = A):
  | | Loser                                                         | Winner's hand                     |
  |-|---------------------------------------------------------------|-----------------------------------|
  |A| rail + hand go back; draws 5                                  | kept                              |
  |B| picks its rail back up into its hand, keeps its hand, draws 2 | kept                              |
  |C| hand goes back; keeps its old rail cards (all); draws 5       | kept                              |
  |D| as A                                                          | returned; draws only at pit stops |

Proxies (experiments5 pieces, scored against the locked rail instead of a bench):
  expert loser : KNOWN + 60 random programs + 140 hill-climb steps; score = experiments5.value() against the locked
                 rail on this layout from its own seat, this round's clock_first, no pit stops (perfect foresight
                 of the locked program: an UPPER bound on rebuilding);
  novice loser : best of 6 random legal programs (with Fire and a mover) judged the same way (a LOWER bound);
  winner       : never rebuilds. Pairings per match cycle EvE, EvN, NvN, EvE, NvE, NvN (one pairing per match).

Pass lines (fixed 2026-11-24, before any run):
  P1: the round-1 loser wins round 2 in 35-60% of matches with a decided round 1; EvE and NvN separately
      (a drawn round 2 counts as not won);
  P2: a counter is buildable in >= 80% of deals where the round-1 winner was an expert. Counter = a legal 1-8
      card rail from chassis + the loser's round-2 cards that WINS against the locked rail on that layout from the
      loser's seat, round-2 clock_first, no pit stops. Search: KNOWN + 300 random + 700 climb steps, stop at first win;
  P3: the round-1 winner wins the match < 75%, EvE and NvN.
  Also reported, no line: the expert's match-win share in mixed matches (win 1, draw 0.5).

Seeds: seed = layout index in experiments8.LAYOUTS * 10**5 + match index; every random choice after round 1 uses
Random(f"{seed}:{round}...") so the variants see the same draws wherever their piles agree.

Rule-fired checks: asserted - the winner's starting rail equals its locked rail, the deck total is conserved
(pile + hands + rail cards + discards = the 45-card deck), every rebuilt rail is legal and uses only owned cards.
Reported - loser's card count, losers whose rail changed, winner pit-stop plays in round 2, "counter undone"
(the loser's rail beats the locked rail without pit stops but loses with them), C cards kept, D winner hand 0,
repeat draws, cap hits.

Usage: python experiments9.py <matches_per_layout> [variant letters]      (default 30 ABCD)
  python experiments9.py 6 ABCD        # smoke
  python experiments9.py 30 ABCD       # full: 360 matches (120 EvE, 120 NvN, 120 mixed)
"""
import random, sys, time
from collections import Counter
from dataclasses import dataclass, replace
from multiprocessing import Pool
from tanksim import *
from experiments import rand_program, flat, mutate
import experiments5 as X
import experiments7 as E7
import experiments8 as E8

@dataclass(frozen=True)
class MatchRules:
    loser_keep_rail: bool = False     # the loser keeps its old rail's deck cards to rebuild with
    loser_keep_hand: bool = False     # the loser keeps its hand
    loser_draw: int = 5               # cards the loser draws at the round change
    winner_keep_hand: bool = True     # False: the winner's hand goes back into the pile

VARIANTS = {
    "A": ("loser returns rail + hand, draws 5; winner keeps hand", MatchRules()),
    "B": ("loser picks rail up, keeps hand, draws 2",               MatchRules(loser_keep_rail=True, loser_keep_hand=True, loser_draw=2)),
    "C": ("loser returns hand, keeps old rail cards, draws 5",      MatchRules(loser_keep_rail=True)),
    "D": ("as A, but the winner's hand goes back",                  MatchRules(winner_keep_hand=False)),
}

DECK_LAYOUTS = ["Four pillars", "Open board", "Centre block", "Moat", "Gen 01 (pocket)", "Gen 02 (pocket)",
                "Gen 05 (pocket)", "Gen 07", "Gen 08", "Gen 09", "Gen 10", "Gen 11"]   # passed the E2 confirm
WINS, CAP = 3, 7
PAIRS = ("EvE", "EvN", "NvN", "EvE", "NvE", "NvN")
SKILLS = {"EvE": ("expert", "expert"), "EvN": ("expert", "novice"), "NvE": ("novice", "expert"), "NvN": ("novice", "novice")}
EXPERT = (X.EXPERT_RANDOM, X.EXPERT_CLIMB)      # 60, 140
COUNTER = (300, 700)

# the v0.5 shared deck without the pickup module: v0.3 kit + Otherwise x2 per player, plus the 5 rare specials = 45
V05 = dict(V03_DECK); V05[ELSE] = 2
FULL = Counter(shared_deck(V05) + list(E7.SPECIALS))
DECK = dict(V05)
for c in E7.SPECIALS: DECK[c] = DECK.get(c, 0) + 1
assert sum(FULL.values()) == 45

def cfg_for(walls, pits, seed, rnd):
    """experiments8.make_cfg (v5 rules: clock 10, roles, leader attacks, card-language overtime), the v0.5 deck,
    clock_first by (seed + round)."""
    return replace(E8.make_cfg("A", walls, pits, seed), deck=DECK, clock_first=(seed + rnd) % 2)

def deckpart(p):
    """The deck cards on a rail: chassis copies are used first."""
    return Counter({c: k - CHASSIS.get(c, 0) for c, k in Counter(p).items() if k > CHASSIS.get(c, 0)})

def avail_of(cards):
    cards = Counter(cards)
    return {c: CHASSIS.get(c, 0) + cards.get(c, 0) for c in DECK}

def sub(a, b):
    """Multiset a - b, asserting b is contained in a."""
    a, b = Counter(a), Counter(b)
    assert not (b - a), f"card not owned: {b - a}"
    return a - b

def vs_locked(p, locked, seat, cfg, grid, patch=None):
    return play(p, locked, cfg, grid, patch=patch) if seat == 0 else play(locked, p, cfg, grid, patch=patch)

def search_vs(rng, cards, cfg, grid, locked, seat, n_rand, n_climb, stop_win):
    """experiments5.build's expert search (KNOWN + random + climb), scored by value() against the locked rail.
    Returns (rail, value, wins, evaluations)."""
    av = avail_of(cards); hc = replace(cfg, deck=av); ev = 0
    def score(st):
        nonlocal ev
        ev += 1; r = vs_locked(flat(st), locked, seat, cfg, grid)
        return X.value(r, seat), r["winner"] == seat
    best = None
    def consider(st):
        nonlocal best
        v, w = score(st)
        if best is None or v > best[0]: best = (v, w, st)
        return w and stop_win
    for p in X.KNOWN:
        if all(p.count(c) <= av.get(c, 0) for c in set(p)) and X.legal(p):
            if consider(X.stmts_of(p)): return flat(best[2]), best[0], True, ev
    for _ in range(n_rand):
        st = rand_program(rng, hc)
        if X.legal(flat(st)) and consider(st): return flat(best[2]), best[0], True, ev
    if best is None:                                   # nothing legal yet: fall back on a chassis rail
        consider(X.stmts_of([HUNT, FIRE]))
    cur_v, cur_w, cur = best
    for _ in range(n_climb):
        nx = mutate(rng, cur, hc)
        if not X.legal(flat(nx)): continue
        v, w = score(nx)
        if w and stop_win: return flat(nx), v, True, ev
        if v >= cur_v: cur_v, cur_w, cur = v, w, nx
    return flat(cur), cur_v, cur_w, ev

def novice_vs(rng, cards, cfg, grid, locked, seat):
    """experiments5.build's novice (best of 6 random legal programs with Fire and a mover), judged against the
    locked rail by value() instead of against sparring programs."""
    hc = replace(cfg, deck=avail_of(cards)); best, bs = None, None
    for _ in range(6):
        p = flat(rand_program(rng, hc))
        if not X.legal(p) or FIRE not in p or not any(c in p for c in (FWD, HUNT, BACK)): continue
        v = X.value(vs_locked(p, locked, seat, cfg, grid), seat)
        if bs is None or v > bs: best, bs = p, v
    if best is None:
        for _ in range(100):
            p = flat(rand_program(rng, hc))
            if X.legal(p): best = p; break
        else: best = [HUNT, FIRE]
    return best

def run_round(rnd, seed, rails, hands, pile, cfg, grid, skills):
    """One round with both pit stops (experiments5.round_with_stops). Mutates hands and pile.
    Returns (result, final rails, discards, plays per seat)."""
    start = [list(p) for p in rails]
    before = [deckpart(start[s]) + Counter(hands[s]) for s in (0, 1)]
    pile_before = Counter(pile)
    r, sched, log = X.round_with_stops(random.Random(f"{seed}:{rnd}:pit"), start, hands, pile, cfg, grid, skills, X.STOPS)
    drawn = pile_before - Counter(pile)
    final = [list(sched[s][-1][1]) if sched[s] else start[s] for s in (0, 1)]
    for s in (0, 1): assert X.legal(final[s])
    # discards: everything the two players held or drew that is no longer on a rail or in a hand
    held = before[0] + before[1] + drawn
    now = deckpart(final[0]) + deckpart(final[1]) + Counter(hands[0]) + Counter(hands[1])
    disc = sub(held, now)                              # asserts nothing was created
    return r, final, disc, (len(sched[0]), len(sched[1]))

def conserved(pile, hands, rails, disc):
    tot = Counter(pile) + Counter(hands[0]) + Counter(hands[1]) + deckpart(rails[0]) + deckpart(rails[1]) + disc
    assert tot == FULL, f"deck not conserved: +{tot - FULL} -{FULL - tot}"

def one_match(args):
    bname, li, k, vks = args
    seed = li * 10**5 + k
    walls, pits = E8.LAYOUTS[bname]
    kind = PAIRS[k % 6]; skills = SKILLS[kind]
    cfg1 = cfg_for(walls, pits, seed, 1); grid = cfg1.grid()
    # ---- round 1, shared by every variant
    rng = random.Random(seed)
    brng = random.Random(77)                               # the same bench and sparring set as experiments7/8
    bcfg = Config(deck=dict(E7.V04), cooldown=1, build_behind=True, hunt_avoid=True)
    bench = X.STARTERS + [flat(rand_program(brng, bcfg)) for _ in range(4)]
    spar = [flat(rand_program(brng, bcfg)) for _ in range(4)]
    pile = sorted(FULL.elements()); rng.shuffle(pile)
    hands = [[pile.pop() for _ in range(X.HAND)] for _ in (0, 1)]
    rails = []
    for s in (0, 1):
        p, q = X.build(rng, avail_of(hands[s]), cfg1, grid, bench, spar, skills[s])
        rails.append(p); hands[s] = list(sub(hands[s], deckpart(p)).elements())
    conserved(pile, hands, rails, Counter())
    r1, rails1, disc1, plays1 = run_round(1, seed, rails, hands, pile, cfg1, grid, skills)
    conserved(pile, hands, rails1, disc1)
    out = {}
    for vk in vks:
        mr = VARIANTS[vk][1]
        R, H, P, D = [list(p) for p in rails1], [list(h) for h in hands], list(pile), Counter(disc1)
        wins = [0, 0]; hist = [r1["winner"]]
        if r1["winner"] is not None: wins[r1["winner"]] += 1
        rec = dict(kind=kind, skills=skills, layout=bname, seed=seed, rounds=[], r1=r1["winner"])
        rnd = 1
        while max(wins) < WINS and rnd < CAP:
            rnd += 1; prev = hist[-1]
            cfg = cfg_for(walls, pits, seed, rnd)
            info = dict(rnd=rnd)
            if prev is None:                               # drawn round: both keep rails and hands
                P = sorted(P + list(D.elements())); random.Random(f"{seed}:{rnd}").shuffle(P); D = Counter()
            else:
                w, l = prev, 1 - prev; locked = list(R[w])
                wkeep = list(H[w]) if mr.winner_keep_hand else []
                lkeep = Counter()
                if mr.loser_keep_rail: lkeep += deckpart(R[l])
                if mr.loser_keep_hand: lkeep += Counter(H[l])
                P = sorted(sub(sub(sub(FULL, deckpart(locked)), wkeep), lkeep).elements())
                random.Random(f"{seed}:{rnd}").shuffle(P)
                drawn = [P.pop() for _ in range(min(mr.loser_draw, len(P)))]
                cards = lkeep + Counter(drawn)
                brng2 = random.Random(f"{seed}:{rnd}:build")
                if skills[l] == "expert":
                    new, v, beat, _ = search_vs(brng2, cards, cfg, grid, locked, l, *EXPERT, False)
                else:
                    new = novice_vs(brng2, cards, cfg, grid, locked, l)
                assert X.legal(new)
                old_l = R[l]
                R[l] = new; H[l] = list(sub(cards, deckpart(new)).elements()); H[w] = wkeep; D = Counter()
                conserved(P, H, R, D)
                assert R[w] == locked                       # the winner's starting rail is its locked rail
                pre = vs_locked(new, locked, l, cfg, grid)
                info.update(w=w, l=l, ncards=sum(cards.values()), changed=new != old_l, whand=len(H[w]),
                            kept=sum(deckpart(old_l).values()) if mr.loser_keep_rail else None,
                            kept_used=sum((deckpart(old_l) & deckpart(new)).values()) if mr.loser_keep_rail else None,
                            pre_win=pre["winner"] == l, locked=show(locked), new=show(new))
                if rnd == 2:                                # P2: is a counter buildable from these cards at all?
                    cv = search_vs(random.Random(f"{seed}:counter"), cards, cfg, grid, locked, l, *COUNTER, True)
                    info.update(counter=cv[2], counter_evals=cv[3], counter_rail=show(cv[0]) if cv[2] else None)
            r, R, D, plays = run_round(rnd, seed, R, H, P, cfg, grid, skills)
            conserved(P, H, R, D)
            info.update(winner=r["winner"], plays=plays, repeat_draw=r["winner"] is None and prev is None)
            rec["rounds"].append(info)
            hist.append(r["winner"])
            if r["winner"] is not None: wins[r["winner"]] += 1
        rec.update(wins=tuple(wins), n=rnd, cap=max(wins) < WINS,
                   match=0 if wins[0] > wins[1] else 1 if wins[1] > wins[0] else None)
        out[vk] = rec
    return out

# ---------------------------------------------------------------- report
def pct(a, b): return f"{100 * a / b:.0f}%" if b else "-"

def near(x, lo=None, hi=None):
    return (lo is not None and abs(x - lo) <= 5) or (hi is not None and abs(x - hi) <= 5)

def report(vk, recs):
    print(f"\n=== {vk}. {VARIANTS[vk][0]} ===")
    dec = [m for m in recs if m["r1"] is not None]
    print(f"matches {len(recs)}, round 1 decided {len(dec)} ({pct(len(dec), len(recs))})")
    for lab, kinds in (("EvE", ("EvE",)), ("NvN", ("NvN",)), ("mixed", ("EvN", "NvE")), ("all", tuple(SKILLS))):
        ms = [m for m in dec if m["kind"] in kinds]
        if not ms: continue
        p1 = sum(m["rounds"][0]["winner"] == m["rounds"][0]["l"] for m in ms)
        r2d = sum(m["rounds"][0]["winner"] is None for m in ms)
        p3 = sum(m["match"] == m["r1"] for m in ms)
        md = sum(m["match"] is None for m in ms)
        f1, f3 = 100 * p1 / len(ms), 100 * p3 / len(ms)
        v1 = "pass" if 35 <= f1 <= 60 else "FAIL"; v3 = "pass" if f3 < 75 else "FAIL"
        tag = lab in ("EvE", "NvN")
        print(f"  {lab:5} P1 loser wins round 2 {p1:>3}/{len(ms):<3} {pct(p1, len(ms)):>4}"
              f"{' ' + v1 + (' (within 5 of a line)' if near(f1, 35, 60) else '') if tag else ''}"
              f" | round 2 drawn {r2d} | P3 round-1 winner wins match {p3:>3}/{len(ms):<3} {pct(p3, len(ms)):>4}"
              f"{' ' + v3 + (' (within 5 of the line)' if near(f3, hi=75) else '') if tag else ''} | match draws {md}")
    ex = [m for m in dec if m["skills"][m["r1"]] == "expert"]
    cf = sum(m["rounds"][0]["counter"] for m in ex)
    if ex:
        f2 = 100 * cf / len(ex)
        print(f"  P2 counter buildable (round-1 winner expert): {cf}/{len(ex)} {pct(cf, len(ex))} "
              f"{'pass' if f2 >= 80 else 'FAIL'}{' (within 5 of the line)' if near(f2, 80) else ''}"
              + "".join(f" | {lab} {sum(m['rounds'][0]['counter'] for m in ms)}/{len(ms)}" for lab, ms in
                        (("EvE", [m for m in ex if m["kind"] == "EvE"]), ("expert beat novice", [m for m in ex if m["kind"] != "EvE"]))))
        ev = sorted(m["rounds"][0]["counter_evals"] for m in ex if m["rounds"][0]["counter"])
        if ev: print(f"     evaluations to the first counter: median {ev[len(ev)//2]}, 90th pct {ev[int(len(ev)*0.9)]}, max {ev[-1]} (of <= ~1000)")
    nx = [m for m in dec if m["skills"][m["r1"]] == "novice"]
    if nx: print(f"     (aside, round-1 winner novice: counter {sum(m['rounds'][0]['counter'] for m in nx)}/{len(nx)})")
    mix = [m for m in recs if m["kind"] in ("EvN", "NvE")]
    if mix:
        sh = sum(1 if m["match"] == m["skills"].index("expert") else 0.5 if m["match"] is None else 0 for m in mix)
        print(f"  expert match-win share in mixed matches: {sh:g}/{len(mix)} = {pct(sh, len(mix))} (no line)")
    # rule-fired
    r2 = [m["rounds"][0] for m in dec]
    reb = [x for m in recs for x in m["rounds"] if "l" in x]
    print(f"  rule fired: loser cards at the round-2 rebuild mean {sum(x['ncards'] for x in r2)/len(r2):.1f}"
          f" (all rebuilds {sum(x['ncards'] for x in reb)/len(reb):.1f}, n={len(reb)})"
          f" | loser's rail changed {sum(x['changed'] for x in reb)}/{len(reb)} = {pct(sum(x['changed'] for x in reb), len(reb))}")
    wp = [x["plays"][x["w"]] for x in r2]
    print(f"     round-2 winner (locked side) pit-stop plays: {sum(wp)/len(wp):.2f} per round, >=1 play in {sum(p > 0 for p in wp)}/{len(wp)}"
          f" | loser plays {sum(x['plays'][x['l']] for x in r2)/len(r2):.2f}")
    pre = [x for x in r2 if x["pre_win"]]
    und = sum(x["winner"] == x["w"] for x in pre); und_d = sum(x["winner"] is None for x in pre)
    print(f"     round 2: loser's new rail beats the locked rail without pit stops {len(pre)}/{len(r2)} = {pct(len(pre), len(r2))};"
          f" counter undone by pit stops: loses {und}/{len(pre)} = {pct(und, len(pre))}, draws {und_d}")
    for lab, kinds in (("EvE", ("EvE",)), ("NvN", ("NvN",))):
        p = [m["rounds"][0] for m in dec if m["kind"] in kinds and m["rounds"][0]["pre_win"]]
        if p: print(f"       {lab}: beats without stops {len(p)}, undone (loses) {sum(x['winner'] == x['w'] for x in p)}, drawn {sum(x['winner'] is None for x in p)}")
    if VARIANTS[vk][1].loser_keep_rail:
        print(f"     old rail deck cards kept: mean {sum(x['kept'] for x in reb)/len(reb):.1f}, of which reused in the new rail"
              f" {sum(x['kept_used'] for x in reb)/len(reb):.1f}")
    print(f"     winner's hand at round start after a decided round: 0 in {sum(x['whand'] == 0 for x in reb)}/{len(reb)},"
          f" mean {sum(x['whand'] for x in reb)/len(reb):.1f}")
    allr = [x for m in recs for x in m["rounds"]]
    print(f"     rounds after round 1 {len(allr)}, drawn {sum(x['winner'] is None for x in allr)}, repeat draws (drawn after a draw)"
          f" {sum(x['repeat_draw'] for x in allr)} | cap hits {sum(m['cap'] for m in recs)}/{len(recs)}"
          f" | match length mean {sum(m['n'] for m in recs)/len(recs):.1f} rounds")
    for x in [x for x in r2 if x["pre_win"] and x["winner"] == x["w"]][:2]:
        print(f"     undone e.g. locked {x['locked']}  vs  new {x['new']}")

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    keys = list(sys.argv[2]) if len(sys.argv) > 2 else list(VARIANTS)
    lay = list(E8.LAYOUTS)
    print(f"E1 debug rule under dealt hands | {N} matches per layout x {len(DECK_LAYOUTS)} layouts | variants {''.join(keys)}"
          f" | first to {WINS}, cap {CAP} | deck {sum(FULL.values())} cards")
    t0 = time.time()
    jobs = [(b, lay.index(b), k, keys) for b in DECK_LAYOUTS for k in range(N)]
    res = []
    with Pool() as pool:
        for o in pool.imap_unordered(one_match, jobs, chunksize=1): res.append(o)
    r1 = Counter(o[keys[0]]["r1"] for o in res)
    print(f"round 1 (shared by all variants): seat A wins {r1[0]}, seat B wins {r1[1]}, drawn {r1[None]}")
    for vk in keys: report(vk, [o[vk] for o in res])
    if len(keys) > 1:
        a = keys[0]
        for vk in keys[1:]:
            same = sum(o[a]["rounds"][0]["winner"] == o[vk]["rounds"][0]["winner"] for o in res)
            print(f"paired: round-2 result same under {a} and {vk} in {same}/{len(res)}")
    print(f"\n({time.time()-t0:.0f}s, {len(jobs)} matches)")
