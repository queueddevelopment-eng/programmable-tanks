"""Check the viewer's JS engine against tanksim.py on random duels (walls, pits, board cards, pit stops).
Usage: python tests/parity.py [matchups] [v3|draft1] [pits_lo pits_hi]
       PARITY_TEMPLATES=1 python tests/parity.py ...   strong programs with specials spliced in
  v5     : v0.5 draft: shot clock with roles, overtime as printed card-language programs
  v4     : v0.3 rules + shot clock with roles + initiative
  v3     : current v0.3 rules (wall raised behind, Hunt avoids walls and pits)
  draft1 : the first v0.3 draft (wall ahead, old Hunt)"""
import json, random, re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataclasses import replace
from tanksim import *
from experiments import rand_program, flat
from experiments2 import layout

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSNAME = {"IF_ENEMY_BEHIND": "IF_BEHIND"}
MODE = sys.argv[2] if len(sys.argv) > 2 else "v3"
NEW = MODE in ("v3", "v4")
CLOCK = MODE in ("v4", "v5")
CARDS_OT = MODE == "v5"        # v5: overtime as printed card-language programs instead of the pathfinding attacker           # v4: shot clock (10 quiet ticks, behind attacks / leader holds) + initiative on contested squares
PLO, PHI = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 3)
rng = random.Random(99 + PLO)
cases = []; COVER = {}
TEMPLATES = os.environ.get("PARITY_TEMPLATES") == "1"
STRONG = ["WHILE_ENEMY FIRE HUNT", "IF_ENEMY FIRE IF_NEAR BACK HUNT", "WHILE_ENEMY FIRE TRACK", "WHILE_ENEMY FIRE RIGHT",
          "HUNT IF_ENEMY FIRE", "IF_ENEMY FIRE ELSE HUNT", "IF_HIT TRACK WHILE_ENEMY FIRE HUNT"]
for k in range(int(sys.argv[1]) if len(sys.argv) > 1 else 400):
    walls = layout(rng, True) if k % 3 else ((2, 2), (5, 2), (2, 5), (5, 5))
    free = [(x, y) for x in range(8) for y in range(8) if (x, y) not in walls and x + y > 1 and x + y < 13]
    pits = tuple(rng.sample(free, rng.randint(PLO, PHI)))
    deck = dict(V03_DECK); deck[BUILD] = 2; deck[BLAST] = 2
    deck.update({SHIELD: 2, SPREAD: 2, OVERCH: 2, ELSE: 2, IF_PWR: 1})       # v0.4 cards
    pfree = [q for q in free if q not in pits]
    pw = tuple((x, y, rng.choice("SDX")) for (x, y) in rng.sample(pfree, rng.randint(0, 4)))
    cfg = Config(deck=deck, cooldown=1, walls=walls, pits=pits, build_behind=NEW, hunt_avoid=NEW, powerups=pw,
                 shot_clock=10 if CLOCK else 0, clock_roles=CLOCK, initiative=CLOCK,
                 clock_path=CLOCK and not CARDS_OT, clock_cards=CARDS_OT, clock_leader=CLOCK and k % 2 == 0, clock_first=(k // 2) % 2)
    if TEMPLATES:      # strong programs with a special or Otherwise spliced in, so shields and spreads actually meet shots
        def tpl():
            q = parse(rng.choice(STRONG))
            c = rng.choice((SHIELD, SPREAD, OVERCH, ELSE, IF_PWR))
            q.insert(rng.randrange(len(q) + 1), c)
            if c in (ELSE, IF_PWR): q.insert(q.index(c) + 1, rng.choice((HUNT, FWD, FIRE, RIGHT)))
            elif rng.random() < 0.3: q.insert(q.index(c), rng.choice((REP3, WH_ENEMY)))     # a loop in front of a special
            return q[:8]
        a, b = tpl(), tpl()
    else:
        a, b = flat(rand_program(rng, cfg)), flat(rand_program(rng, cfg))
    if not a or not b or validate(a, cfg) or validate(b, cfg): continue
    patch = {}
    if k % 2:
        for side in (0, 1):
            if rng.random() < .6:
                p = flat(rand_program(rng, cfg))
                if p and not validate(p, cfg): patch[side] = [(rng.choice((11, 21)), p)]
    tr = []; r = play(a, b, cfg, trace=tr, patch=patch or None)
    for key, v in (("special used", any(r["used"])), ("shield soaked", sum(r["absorbed"])), ("pickup taken", sum(r["pickups"])),
                   ("Otherwise in a program", ELSE in a or ELSE in b), ("pit fall", sum(r["falls"])), ("shot clock ran out", r["overtime"])):
        COVER[key] = COVER.get(key, 0) + bool(v)
    w = cfg.size + 2
    rows = [[t, x % w - 1, x // w - 1, d, max(h, 0), y % w - 1, y // w - 1, e, max(g, 0)] for (t, _, _, x, d, h, y, e, g) in tr]
    nm = lambda p: [JSNAME.get(NAMES[c], NAMES[c]) for c in p]
    cases.append(dict(a=nm(a), b=nm(b), walls=walls, pits=pits, pw=pw, leader=cfg.clock_leader, first=cfg.clock_first, patch={str(s): [[t, nm(p)] for t, p in v] for s, v in patch.items()},
                      rows=rows, winner=r["winner"]))
src = open(os.path.join(HERE, "tank-match-viewer.html")).read()
engine = re.search(r"// ==== ENGINE START.*?// ==== ENGINE END ====", src, re.S).group(0)
harness = engine + """
const cases = JSON.parse(require('fs').readFileSync(0, 'utf8'));
let bad = 0;
for (const [n, c] of cases.entries()) {
  const m = newMatch([c.a, c.b], [[0,0,0],[7,7,2]], 8, c.walls, 40, RULESETS.v4, c.pits, c.pw);
  m.rules = {...RULESETS.v4, maxBuilds: 2, buildBehind: NEW, huntAvoid: NEW, shotClock: CLOCK ? 10 : 0, clockRoles: CLOCK, initiative: CLOCK,
              clockPath: CLOCK && !CARDS_OT, clockCards: CARDS_OT, clockLeader: c.leader, clockFirst: c.first};
  const rows = [];
  while (!m.over) {
    for (const s of ['0','1']) for (const [t, p] of (c.patch[s] || [])) if (t === m.tick + 1) loadProgram(m.tanks[+s], p);
    stepMatch(m);
    const [A, B] = m.tanks; rows.push([m.tick, A.x, A.y, A.d, A.armor, B.x, B.y, B.d, B.armor]);
  }
  const same = JSON.stringify(rows) === JSON.stringify(c.rows) && (m.winner ?? null) === c.winner;
  if (!same) { bad++; if (bad <= 3) { console.log('MISMATCH case', n, c.a.join(' '), '|', c.b.join(' '));
    for (let i = 0; i < Math.max(rows.length, c.rows.length); i++) if (JSON.stringify(rows[i]) !== JSON.stringify(c.rows[i])) { console.log(' js', JSON.stringify(rows[i]), ' py', JSON.stringify(c.rows[i])); break; } } }
}
console.log(`${cases.length} matchups, ${bad} mismatches`);
"""
harness = f"const NEW = {str(NEW).lower()}; const CLOCK = {str(CLOCK).lower()}; const CARDS_OT = {str(CARDS_OT).lower()};\n" + harness
out = subprocess.run(["node", "-e", harness], input=json.dumps(cases), capture_output=True, text=True)
print(MODE, out.stdout.strip(), out.stderr, "| matchups with:", ", ".join(f"{k} {v}" for k, v in COVER.items()))
