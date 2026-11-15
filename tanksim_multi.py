"""tanksim_multi.py - free-for-all version of the engine (3-6 tanks). Same cards, same tick order."""
from tanksim import *

STARTS_4 = ((1, 0, 0), (7, 1, 3), (6, 7, 2), (0, 6, 1))     # 4-fold symmetric, nobody starts in a firing lane
CFG_4 = Config(max_ticks=60)
STARTS_6 = ((1, 0, 0), (9, 1, 3), (8, 9, 2), (0, 8, 1), (0, 4, 1), (9, 5, 3))   # 10x10, no shared lanes at start
CFG_6 = Config(size=10, max_ticks=80, walls=((2, 2), (7, 2), (2, 7), (7, 7), (4, 4), (5, 5), (4, 7), (5, 2)))

def play_multi(progs, cfg, starts, grid=None):
    g, w = grid if grid else cfg.grid()
    delta = (w, 1, -w, -1)
    tanks = [Tank(p, (y + 1) * w + (x + 1), d, cfg.armor) for p, (x, y, d) in zip(progs, starts)]
    n = len(tanks); dealt = [0] * n; kills = [0] * n; died_at = [None] * n
    alive = list(range(n)); tick = 0
    while tick < cfg.max_ticks and len(alive) > 1:
        tick += 1
        occ = {tanks[i].pos: i for i in alive}
        acts, target = {}, {}
        for i in alive:
            t = tanks[i]; dl = delta[t.d]; q = t.pos + dl
            blocked = bool(g[q]) or q in occ
            seen = None
            while not g[q]:
                if q in occ: seen = occ[q]; break
                q += dl
            acts[i] = t.next_action(seen is not None, blocked); target[i] = seen
        for i in alive:                                   # 1. all fire resolves together
            if acts[i] == FIRE and target[i] is not None:
                me, en = tanks[i], tanks[target[i]]
                dmg = cfg.front_dmg if en.d == (me.d + 2) % 4 else cfg.flank_dmg
                was_alive = en.armor > 0
                en.armor -= dmg; en.hit = True; dealt[i] += dmg
                if was_alive and en.armor <= 0: kills[i] += 1
        for i in alive:
            if tanks[i].armor <= 0: died_at[i] = tick
        alive = [i for i in alive if tanks[i].armor > 0]
        occ = {tanks[i].pos: i for i in alive}
        want = {}
        for i in alive:                                   # 2. turns and moves
            t, a = tanks[i], acts[i]
            if a == LEFT: t.d = (t.d - 1) % 4
            elif a == RIGHT: t.d = (t.d + 1) % 4
            elif a == FWD or a == BACK:
                q = t.pos + (delta[t.d] if a == FWD else -delta[t.d])
                if not g[q] and q not in occ: want.setdefault(q, []).append(i)
        for q, who in want.items():
            if len(who) == 1:
                tanks[who[0]].pos = q; tanks[who[0]].moves += 1
    armor = [max(t.armor, 0) for t in tanks]
    return dict(ticks=tick, armor=armor, dealt=dealt, kills=kills, died_at=died_at, alive=alive,
                moves=[t.moves for t in tanks])
