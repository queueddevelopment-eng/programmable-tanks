"""
Regression fingerprints: prove that a rule change left the older rule sets alone.

Every new rule is a Config field that is off by default (CLAUDE.md, decision (f)), so with the new
field off the engine must reproduce old results exactly. This plays fixed random matchups under
each frozen rule set and compares an md5 of the outcomes with the value recorded when that rule
set was frozen. A mismatch means a "default off" change leaked into old behaviour.

    python tests/fingerprints.py          # check
    python tests/fingerprints.py --print  # print current values (only to record a NEW frozen set)

Never update an expected value to make a red check pass. Add a new entry when a new rule set
freezes (v0.5 at the freeze), and leave the old entries as they are.
"""
import hashlib, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tanksim import *
from experiments import rand_program, flat

def legacy():
    """v0.1 and v0.2 decks, shrinking arena, power-ups, mid-round spawns, one pit-stop patch."""
    rng = random.Random(5)
    cfgs = [Config(), Config(deck=dict(V02_DECK), cooldown=1),
            Config(deck=dict(V02_DECK), cooldown=1, shrink_start=16),
            Config(powerups=((3, 3, 'R'), (4, 4, 'D'))), Config(spawn_every=6, spawn_seed=3)]
    out = []
    for cfg in cfgs:
        for _ in range(600):
            a = flat(rand_program(rng, cfg)); b = flat(rand_program(rng, cfg))
            tr = []; r = play(a, b, cfg, trace=tr)
            out.append((r['winner'], r['armor'], tr))
        for _ in range(100):
            a = flat(rand_program(rng, cfg)); b = flat(rand_program(rng, cfg)); c = flat(rand_program(rng, cfg))
            out.append(play(a, b, cfg, patch={0: (10, c)})['armor'])
    return hashlib.md5(json.dumps(out).encode()).hexdigest()

def v04():
    """v0.4 draft: specials, Otherwise, pickups, pits, shot clock with the pathfinding attacker.
    Programs with a loop in front of a special are excluded: v0.4 rejected them."""
    rng = random.Random(9); d = dict(V02_DECK); d.update({ELSE: 2, SHIELD: 1, SPREAD: 1, OVERCH: 1})
    cfg = Config(deck=d, cooldown=1, build_behind=True, hunt_avoid=True, shot_clock=10, clock_roles=True,
                 clock_path=True, clock_leader=True, pits=((3, 4), (4, 3)), powerups=((1, 5, 'S'), (6, 2, 'S')))
    out = []
    for _ in range(1500):
        a = flat(rand_program(rng, cfg)); b = flat(rand_program(rng, cfg))
        if validate(a, cfg) or validate(b, cfg): continue
        if any(c in LOOPS and q[(i + 1) % len(q)] in ONESHOT for q in (a, b) for i, c in enumerate(q)): continue
        out.append(play(a, b, cfg)['armor'])
    return hashlib.md5(json.dumps([len(out), out]).encode()).hexdigest()

EXPECTED = {   # recorded when each rule set froze; never edit to make a check pass
    "legacy v0.1-v0.2 (Oct 2026)": (legacy, "dc060626c7df1f1b73250ffa8687feef"),
    "v0.4 draft (Nov 15 2026)":    (v04,    "6c91e5f7c03bef3b173eabd47c3445a6"),
}

if __name__ == "__main__":
    bad = 0
    for name, (fn, want) in EXPECTED.items():
        got = fn()
        if "--print" in sys.argv: print(f"{name}: {got}"); continue
        ok = got == want; bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f"  (expected {want}, got {got})"))
    sys.exit(1 if bad else 0)
