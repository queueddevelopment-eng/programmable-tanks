"""
tanksim.py - rules engine for the programmable-tank card game (rules v0.1 - v0.3 draft).

Everything tunable lives in Config so rule variants can be compared.
The game is fully deterministic: same two programs -> same result, always.

CLI:
  python3 tanksim.py --replay "WHILE_ENEMY FIRE RIGHT" "IF_ENEMY FIRE IF_BLOCKED RIGHT FWD"
"""
from dataclasses import dataclass, field
import sys, random

# ---- cards -----------------------------------------------------------------
FWD, BACK, LEFT, RIGHT, FIRE, IF_ENEMY, IF_BLOCKED, IF_HIT, WH_ENEMY, WH_CLEAR, REP3, IF_PWR, \
    IF_LEFT, IF_RIGHT, IF_BEHIND, TRACK, HUNT, IF_NEAR, BUILD, BLAST, SHIELD, SPREAD, OVERCH, ELSE = range(24)
IDLE = -1
NAMES = ["FWD", "BACK", "LEFT", "RIGHT", "FIRE", "IF_ENEMY", "IF_BLOCKED", "IF_HIT",
         "WHILE_ENEMY", "WHILE_CLEAR", "REPEAT3", "IF_POWERUP",
         "IF_ENEMY_LEFT", "IF_ENEMY_RIGHT", "IF_ENEMY_BEHIND", "TRACK", "HUNT", "IF_NEAR",
         "BUILD", "BLAST", "SHIELD", "SPREAD", "OVERCHARGE", "ELSE"]
BY_NAME = {n: i for i, n in enumerate(NAMES)}
ACTIONS = (FWD, BACK, LEFT, RIGHT, FIRE, TRACK, HUNT, BUILD, BLAST, SHIELD, SPREAD, OVERCH)
ACTSET = frozenset(ACTIONS)
ONESHOT = frozenset((SHIELD, SPREAD, OVERCH))    # v0.4 specials: used once, then the card is spent and skipped
IFS = (IF_ENEMY, IF_BLOCKED, IF_HIT, IF_PWR, IF_LEFT, IF_RIGHT, IF_BEHIND, IF_NEAR, ELSE)
LOOPS = (WH_ENEMY, WH_CLEAR, REP3)

DEFAULT_DECK = {FWD: 4, BACK: 1, LEFT: 2, RIGHT: 2, FIRE: 3, IF_ENEMY: 2, IF_BLOCKED: 2,
                IF_HIT: 1, WH_ENEMY: 1, WH_CLEAR: 1, REP3: 1, IF_PWR: 0,
                IF_LEFT: 0, IF_RIGHT: 0, IF_BEHIND: 0, TRACK: 0, HUNT: 0, IF_NEAR: 0,   # v0.2 radar cards: off by default
                BUILD: 0, BLAST: 0,                                                     # v0.3 board cards: off by default
                SHIELD: 0, SPREAD: 0, OVERCH: 0, ELSE: 0}                               # v0.4 cards: off by default

# v0.2 kit: higher-level cards so a strategy fits in 8 slots
V02_DECK = {FWD: 3, BACK: 1, LEFT: 1, RIGHT: 1, FIRE: 3, HUNT: 2, TRACK: 1, IF_ENEMY: 2, IF_BLOCKED: 1,
            IF_HIT: 1, IF_NEAR: 1, IF_BEHIND: 1, WH_ENEMY: 1, REP3: 1,
            WH_CLEAR: 0, IF_PWR: 0, IF_LEFT: 0, IF_RIGHT: 0, BUILD: 0, BLAST: 0,
            SHIELD: 0, SPREAD: 0, OVERCH: 0, ELSE: 0}

# v0.3 draft: v0.2 plus the two board cards
V03_DECK = dict(V02_DECK); V03_DECK[BUILD] = 1; V03_DECK[BLAST] = 1

# v0.3 draft card mechanic: every tank always has the CHASSIS; everything else is drawn from a shared deck
CHASSIS = {FIRE: 2, HUNT: 1, FWD: 1}
def shared_deck(per_player, players=2):
    """The draw pile: each player's kit minus the chassis, pooled. Returns a list of cards."""
    return [c for c, k in per_player.items() for _ in range(players * max(0, k - CHASSIS.get(c, 0)))]


@dataclass
class Config:
    size: int = 8
    walls: tuple = ((2, 2), (5, 2), (2, 5), (5, 5))     # C3 F3 C6 F6
    slots: int = 8
    armor: int = 5
    front_dmg: int = 1
    flank_dmg: int = 2
    max_ticks: int = 40
    zone: tuple = ()            # scoring squares, e.g. centre 4; 1 point per tick ended there
    b_facing: int = 2           # tank B start facing (2 = S, the symmetric default)
    powerups: tuple = ()        # pre-placed before programming: ((x, y, kind), ...)  kind: 'R' repair, 'D' double (Overcharge),
                                #   'S' shield charge, 'X' next Fire is a spread shot
    spawn_every: int = 0        # >0: a random power-up appears every N ticks DURING the round
    spawn_seed: int = 0
    repair_amt: int = 2
    cooldown: int = 0           # ticks the gun needs after a shot (a FIRE during cooldown fizzles)
    near: int = 2               # IF_NEAR is true within this many squares (king's-move distance)
    shrink_start: int = 0       # >0: from this tick the outer ring turns to danger zone...
    shrink_every: int = 8       # ...and another ring follows every N ticks (1 damage per tick spent on it)
    pits: tuple = ()            # v0.3: hazard squares ((x, y), ...). Driving in costs pit_dmg and pit_stun lost ticks
    pit_dmg: int = 2
    pit_stun: int = 2
    max_builds: int = 2         # v0.3: walls one tank may raise per round with BUILD
    build_behind: bool = False  # v0.3: BUILD raises the wall on the square BEHIND the tank (False = ahead, the first draft)
    hunt_avoid: bool = False    # v0.3: HUNT won't turn to face a wall or pit; it drives on or turns the other way instead
    shot_clock: int = 0         # >0: after this many ticks with no hit and no damage, every tank ignores its program and
                                #     runs 'fire if in sights, else Hunt' until someone is hit (then programs resume)
    clock_roles: bool = False   # shot clock with roles: the tank behind on armor attacks (Hunt), the other holds (Face enemy);
                                #     level on armor: the roles alternate each time the clock runs out (seat A attacks first)
    clock_first: int = 0        # which seat attacks first when the clock runs out with armor level (rotate between rounds)
    clock_leader: bool = False  # True: the tank AHEAD on armor must attack (basketball-style: no sitting on a lead)
    clock_path: bool = False    # the attacker drives the shortest route to the nearest square with a clear shot (not greedy Hunt)
    clock_cards: bool = False   # v0.5: overtime is written in the card language. Each tank's program is swapped for a printed
                                #     one (read from its first card) until the next hit, then its own program resumes
    clock_attack: str = "IF_ENEMY FIRE ELSE HUNT"    # the attacker's printed overtime program
    clock_hold: str = "IF_ENEMY FIRE ELSE TRACK"     # the holder's printed overtime program
    initiative: bool = False    # two tanks driving into the same square: the one with initiative gets it
                                #     (A on odd ticks, B on even ticks) instead of both bumping
    deck: dict = field(default_factory=lambda: dict(DEFAULT_DECK))

    def grid(self):
        """Flat padded grid: 1 = wall/edge, 0 = open. Returns (grid, stride)."""
        w = self.size + 2
        g = bytearray(w * w)
        for i in range(w):
            g[i] = g[w * (w - 1) + i] = g[i * w] = g[i * w + w - 1] = 1
        for (x, y) in self.walls:
            g[(y + 1) * w + (x + 1)] = 1
        return g, w


DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))     # N E S W as (dx, dy)


def parse(text):
    return [BY_NAME[t.upper()] for t in text.replace(",", " ").split()]


def show(prog):
    return " · ".join(NAMES[c] for c in prog)


def validate(prog, cfg):
    """Return None if legal, else a reason string."""
    if not prog:
        return "empty"
    if len(prog) > cfg.slots:
        return "too long"
    if not any(c in ACTSET for c in prog):
        return "needs at least one action card"
    for c in set(prog):
        if prog.count(c) > cfg.deck.get(c, 0):
            return f"too many {NAMES[c]}"
    for i, c in enumerate(prog):
        if c in LOOPS and prog[(i + 1) % len(prog)] not in ACTIONS:       # the rail is a loop: last card wraps to the first
            return "loop card must sit immediately before an action (the last card wraps to the first)"
    return None


def _skips(prog):
    """For each IF: index to jump to when false (just past the statement's action)."""
    n = len(prog)
    out = [0] * n
    for i, c in enumerate(prog):
        if c in IFS:
            j = (i + 1) % n
            while prog[j] not in ACTIONS:
                j = (j + 1) % n
            out[i] = (j + 1) % n
    return out


class Tank:
    __slots__ = ("prog", "skip", "n", "ptr", "hit", "rep", "pos", "d", "armor",
                 "shots", "hits", "moves", "idles", "zone", "double", "pickups", "detour", "cool",
                 "stun", "falls", "builds", "blasts", "shield", "spreadnext", "used", "spent", "last_cond", "absorbed")

    def __init__(self, prog, pos, d, armor):
        self.hit = False
        self.used = {}              # one-shot cards used so far this round, by kind
        self.last_cond = True       # result of the most recent condition card (for ELSE)
        self.load(prog)
        self.pos, self.d, self.armor = pos, d, armor
        self.shots = self.hits = self.moves = self.idles = self.zone = self.pickups = 0
        self.double = False
        self.detour = self.cool = 0
        self.stun = self.falls = self.builds = self.blasts = 0
        self.shield = self.absorbed = 0
        self.spreadnext = False

    def load(self, prog):
        """(Re)load a program: pointer back to the first card, loop counters cleared."""
        self.prog, self.skip, self.n = prog, _skips(prog), len(prog)
        self.ptr, self.rep = 0, [0] * len(prog)
        self.spent = set()          # a used special stays used after a pit stop: mark that many copies spent
        for k, cnt in self.used.items():
            for i, c in enumerate(prog):
                if cnt and c == k:
                    self.spent.add(i); cnt -= 1

    def _take(self, i):
        """Return the action at i; a special is spent by using it, however it was reached."""
        c = self.prog[i]
        if c in ONESHOT:
            self.spent.add(i); self.used[c] = self.used.get(c, 0) + 1
        return c

    def next_action(self, sees, blocked, sees_pwr=False, side=0, near=False):
        prog, n, p = self.prog, self.n, self.ptr
        for _ in range(n):
            c = prog[p]
            if c in ACTSET:
                if p in self.spent:                    # spent special: passed over for free
                    p = (p + 1) % n
                    continue
                self.ptr = (p + 1) % n
                if c in ONESHOT:
                    self.spent.add(p); self.used[c] = self.used.get(c, 0) + 1
                return c
            if c in IFS and self.spent and (self.skip[p] - 1) % n in self.spent:
                p = self.skip[p]                       # the statement's action is spent: skip the whole statement
                continue
            if c == ELSE:
                t = not self.last_cond
                p = (p + 1) % n if t else self.skip[p]
                continue
            if c == IF_ENEMY:
                t = sees
            elif c == IF_BLOCKED:
                t = blocked
            elif c == IF_HIT:
                t = self.hit
                self.hit = False
            elif c == IF_PWR:
                t = sees_pwr
            elif c == IF_LEFT:
                t = side == 3
            elif c == IF_RIGHT:
                t = side == 1
            elif c == IF_BEHIND:
                t = side == 2
            elif c == IF_NEAR:
                t = near
            elif c == WH_ENEMY or c == WH_CLEAR:
                if self.spent and (p + 1) % n in self.spent:   # the loop's action is a spent special: skip the statement
                    p = (p + 2) % n
                    continue
                if (sees if c == WH_ENEMY else not blocked):
                    self.ptr = p
                    return self._take((p + 1) % n)
                p = (p + 2) % n
                continue
            else:  # REP3
                if self.spent and (p + 1) % n in self.spent:
                    self.rep[p] = 0
                    p = (p + 2) % n
                    continue
                if self.rep[p] == 0:
                    self.rep[p] = 3
                self.rep[p] -= 1
                self.ptr = p if self.rep[p] else (p + 2) % n
                return self._take((p + 1) % n)
            self.last_cond = t
            p = (p + 1) % n if t else self.skip[p]
        self.ptr = p
        return IDLE


def _hit(me, en, dmg):
    """Resolve one hit: Overcharge doubles it, a shield charge soaks 1 damage."""
    if me.double:
        dmg *= 2
        me.double = False
    if en.shield and dmg > 0:
        dmg -= 1; en.shield -= 1; en.absorbed += 1
    en.armor -= dmg
    en.hit = True


def _engage(me, en, g, pits, w):
    """Shot-clock attacker: shortest route (breadth-first, neighbours N E S W) to the nearest square
    from which the enemy is in a clear straight line, then turn to face them. No route: Hunt."""
    delta = (w, 1, -w, -1)
    def shot_from(c):
        for d in range(4):
            q = c + delta[d]
            while not g[q]:
                if q == en.pos: return d
                q += delta[d]
        return None
    def turn_to(d):
        return IDLE if d == me.d else LEFT if d == (me.d - 1) % 4 else RIGHT
    d = shot_from(me.pos)
    if d is not None:
        return turn_to(d)
    first = {me.pos: None}; queue = [me.pos]; i = 0
    while i < len(queue):
        c = queue[i]; i += 1
        for k in range(4):
            n = c + delta[k]
            if n in first or g[n] or n in pits or n == en.pos: continue
            first[n] = k if c == me.pos else first[c]
            if shot_from(n) is not None:
                k0 = first[n]
                return FWD if k0 == me.d else turn_to(k0)
            queue.append(n)
    return HUNT


def _hunt_turn(turn, side, me, g, pits, delta, blocked_ahead, enemy_pos):
    """v0.3 Hunt: about to turn toward the enemy. Don't turn to face a wall or pit.
    Enemy behind: try the other turn first. Otherwise drive on if the way ahead is clear,
    else turn away; if every way is shut, turn toward the enemy anyway."""
    face = lambda t: (me.d + (1 if t == RIGHT else -1)) % 4
    shut = lambda t: bool(g[me.pos + delta[face(t)]]) or (me.pos + delta[face(t)]) in pits
    other = LEFT if turn == RIGHT else RIGHT
    if not shut(turn):
        return turn
    if side == 2 and not shut(other):
        return other
    if not blocked_ahead:
        return FWD
    if not shut(other):
        return other
    return turn


def play(prog_a, prog_b, cfg, grid=None, trace=None, patch=None):
    """Run one round. Returns dict(winner=0|1|None, ticks, armor=(a,b), ...).
    patch: optional {side: (tick, new_program)} or {side: [(tick, prog), ...]} - mid-round "pit stop" reprograms.
    A patch for tick T is loaded before tick T is played: pointer to the first card, loop counters cleared."""
    g, w = grid if grid else cfg.grid()
    g = bytearray(g)                            # walls can change mid-round (BUILD / BLAST), so work on a copy
    delta = (w, 1, -w, -1)                      # N E S W
    a = Tank(prog_a, 1 * w + 1, 0, cfg.armor)                       # A1 facing N
    b = Tank(prog_b, cfg.size * w + cfg.size, cfg.b_facing, cfg.armor)  # H8 facing S
    zone = {(y + 1) * w + (x + 1) for (x, y) in cfg.zone}
    pw = {(y + 1) * w + (x + 1): k for (x, y, k) in cfg.powerups}
    pits = {(y + 1) * w + (x + 1) for (x, y) in cfg.pits}
    srng = random.Random(cfg.spawn_seed) if cfg.spawn_every else None
    sched = {}
    if patch:
        for side, v in patch.items():
            for tk_, prog in ([v] if isinstance(v, tuple) else v):
                sched[(side, tk_)] = prog
    first_hit = None
    last_dmg = 0; overtime = 0; periods = 0; was_out = False; ot_hits = 0
    tick = 0
    while tick < cfg.max_ticks:
        tick += 1
        start = (a.armor, b.armor, a.hits + b.hits)
        clock_out = cfg.shot_clock and tick - 1 - last_dmg >= cfg.shot_clock
        if clock_out and not was_out:
            periods += 1
        if cfg.clock_roles:
            lo, hi = (0, 1) if a.armor < b.armor else (1, 0)
            attacker = (periods - 1 + cfg.clock_first) % 2 if a.armor == b.armor else (hi if cfg.clock_leader else lo)
        else:
            attacker = -1
        if clock_out and not was_out and cfg.clock_cards:     # hand each tank its printed overtime program
            runners = [Tank(parse(cfg.clock_attack if attacker in (-1, s) else cfg.clock_hold), 0, 0, 0) for s in (0, 1)]
        was_out = clock_out
        if sched:
            for side, tk in ((0, a), (1, b)):
                p_ = sched.get((side, tick))
                if p_ is not None:
                    tk.load(p_)
        sens = []; rs = []
        for me, en in ((a, b), (b, a)):
            dl = delta[me.d]
            q = me.pos + dl
            blocked = bool(g[q]) or q == en.pos or q in pits
            sees = sees_pwr = False
            while not g[q]:
                if q == en.pos:
                    sees = True
                    break
                if q in pw:
                    sees_pwr = True
                q += dl
            dx, dy = en.pos % w - me.pos % w, en.pos // w - me.pos // w
            fx, fy = DIRS[me.d]; rx, ry = DIRS[(me.d + 1) % 4]
            f, r = dx * fx + dy * fy, dx * rx + dy * ry
            side = 0 if (f > 0 and abs(r) <= f) else 2 if (f < 0 and abs(r) < -f) else 1 if r > 0 else 3
            sens.append((sees, blocked, sees_pwr, side, max(abs(dx), abs(dy)) <= cfg.near))
            rs.append(r)
        acts = []
        for seat, me, sn in ((0, a, sens[0]), (1, b, sens[1])):
            if me.stun > 0:                        # climbing out of a pit: no card is read
                me.stun -= 1
                acts.append(IDLE)
            elif clock_out and cfg.clock_cards:    # shot clock ran out: run the printed overtime program
                acts.append(runners[seat].next_action(*sn))
            elif clock_out:                        # shot clock ran out: the tank engages on its own
                en = b if seat == 0 else a
                if sn[0]: acts.append(FIRE if me.cool == 0 else IDLE)                 # aim held while the gun cools
                elif attacker not in (-1, seat): acts.append(TRACK)                   # holder: face the attacker
                elif cfg.clock_path: acts.append(_engage(me, en, g, pits, w))
                else: acts.append(HUNT)
            else:
                acts.append(me.next_action(*sn))
        act_a, act_b = acts
        overtime += bool(clock_out)
        wallblk = [bool(g[t.pos + delta[t.d]]) or (t.pos + delta[t.d]) in pits for t in (a, b)]
        # 1. fire (and breach), from start-of-tick state. Shield and Overcharge take effect first.
        for me, act in ((a, act_a), (b, act_b)):
            if act == SHIELD: me.shield = min(me.shield + 1, 2)
            elif act == OVERCH: me.double = True
        breached = []
        for me, en, act, (sees, _, _p, _s, _n) in ((a, b, act_a, sens[0]), (b, a, act_b, sens[1])):
            if act == SPREAD or (act == FIRE and me.spreadnext and me.cool == 0):
                me.spreadnext = me.spreadnext and act != FIRE
                me.shots += 1                          # spread shot: all four directions; a special ignores the cooldown
                me.cool = cfg.cooldown + 1
                for dd in range(4):
                    dl = delta[dd]; q = me.pos + dl
                    while not g[q] and q != en.pos:
                        q += dl
                    if q == en.pos:
                        me.hits += 1
                        _hit(me, en, cfg.front_dmg if en.d == (dd + 2) % 4 else cfg.flank_dmg)
                        if first_hit is None: first_hit = tick
            elif (act == FIRE or act == BLAST) and me.cool > 0:
                pass                                   # gun still cooling: the shot fizzles
            elif act == FIRE:
                me.shots += 1
                me.cool = cfg.cooldown + 1
                if sees:
                    me.hits += 1
                    _hit(me, en, cfg.front_dmg if en.d == (me.d + 2) % 4 else cfg.flank_dmg)
                    if first_hit is None:
                        first_hit = tick
            elif act == BLAST:                         # demolition round: removes the first wall in line, harmless to tanks
                me.cool = cfg.cooldown + 1
                dl = delta[me.d]; q = me.pos + dl
                while not g[q] and q != en.pos:
                    q += dl
                if g[q] and 1 <= q % w <= cfg.size and 1 <= q // w <= cfg.size:
                    breached.append(q)
                    me.blasts += 1
        for q in breached:
            g[q] = 0
        # 2. raised walls, then turns and moves
        if a.armor > 0 and b.armor > 0:
            raised = []
            for me, en, act in ((a, b, act_a), (b, a, act_b)):
                if act == BUILD:
                    t = me.pos - delta[me.d] if cfg.build_behind else me.pos + delta[me.d]
                    if me.builds < cfg.max_builds and not g[t] and t not in pits and t != en.pos:
                        raised.append(t)
                        me.builds += 1
            for t in raised:
                g[t] = 1
            new = []
            for me, en, act, sd, blk, wb, rr in ((a, b, act_a, sens[0][3], sens[0][1], wallblk[0], rs[0]),
                                                (b, a, act_b, sens[1][3], sens[1][1], wallblk[1], rs[1])):
                np_ = me.pos
                if act == HUNT:                        # close in on the enemy, stepping around walls and pits
                    if me.detour > 0:
                        if blk: act = RIGHT; me.detour = 0
                        else: act = FWD; me.detour -= 1
                    elif sd in (1, 2, 3):
                        act = LEFT if sd == 3 else RIGHT
                        if cfg.hunt_avoid:
                            act = _hunt_turn(act, sd, me, g, pits, delta, blk, en.pos)
                    elif wb: act = LEFT if rr < 0 else RIGHT; me.detour = 1   # sidestep toward the enemy's side
                    elif blk: act = IDLE
                    else: act = FWD
                if act == TRACK:                       # turn 90 degrees toward the enemy; nothing if already ahead
                    act = LEFT if sd == 3 else RIGHT if sd in (1, 2) else IDLE
                if act == LEFT:
                    me.d = (me.d - 1) % 4
                elif act == RIGHT:
                    me.d = (me.d + 1) % 4
                elif act == FWD or act == BACK:
                    t = me.pos + (delta[me.d] if act == FWD else -delta[me.d])
                    if not g[t] and t != en.pos:
                        np_ = t
                elif act == IDLE:
                    me.idles += 1
                new.append(np_)
            if new[0] == new[1] and cfg.initiative:      # both drive for the same square: initiative decides
                if tick % 2: new[1] = b.pos
                else: new[0] = a.pos
            if new[0] != new[1]:
                if new[0] != a.pos: a.moves += 1
                if new[1] != b.pos: b.moves += 1
                for me, np_ in ((a, new[0]), (b, new[1])):
                    if np_ != me.pos and np_ in pits:      # drove into a pit
                        me.armor -= cfg.pit_dmg
                        me.hit = True
                        me.stun = cfg.pit_stun
                        me.falls += 1
                a.pos, b.pos = new
            if pw:
                for me in (a, b):
                    k = pw.pop(me.pos, None)
                    if k:
                        me.pickups += 1
                        if k == 'R': me.armor += cfg.repair_amt
                        elif k == 'S': me.shield = min(me.shield + 1, 2)
                        elif k == 'X': me.spreadnext = True
                        else: me.double = True
            if srng and tick % cfg.spawn_every == 0:
                for _ in range(20):
                    q = srng.randrange(len(g))
                    if not g[q] and q != a.pos and q != b.pos and q not in pw:
                        pw[q] = srng.choice('RD')
                        break
            if zone:
                a.zone += a.pos in zone
                b.zone += b.pos in zone
        if cfg.shrink_start and tick >= cfg.shrink_start and a.armor > 0 and b.armor > 0:
            rings = min(1 + (tick - cfg.shrink_start) // cfg.shrink_every, cfg.size // 2 - 1)
            for me in (a, b):
                x, y = me.pos % w - 1, me.pos // w - 1
                if min(x, y, cfg.size - 1 - x, cfg.size - 1 - y) < rings:
                    me.armor -= 1
                    me.hit = True
        if a.cool: a.cool -= 1
        if b.cool: b.cool -= 1
        if (a.armor, b.armor, a.hits + b.hits) != start:
            last_dmg = tick
        if clock_out: ot_hits += a.hits + b.hits - start[2]
        if trace is not None:
            trace.append((tick, act_a, act_b, a.pos, a.d, a.armor, b.pos, b.d, b.armor))
        if a.armor <= 0 or b.armor <= 0:
            break
    if a.armor <= 0 or b.armor <= 0 or not zone:
        ka, kb = max(a.armor, 0), max(b.armor, 0)        # a destroyed tank has 0 armor; both destroyed = draw
    else:                                   # timeout with a zone: zone points first, armor breaks ties
        ka, kb = (a.zone, a.armor), (b.zone, b.armor)
    winner = None if ka == kb else (0 if ka > kb else 1)
    return dict(winner=winner, ticks=tick, armor=(a.armor, b.armor), first_hit=first_hit,
                shots=(a.shots, b.shots), hits=(a.hits, b.hits), moves=(a.moves, b.moves),
                idles=(a.idles, b.idles), zone=(a.zone, b.zone), pickups=(a.pickups, b.pickups),
                falls=(a.falls, b.falls), builds=(a.builds, b.builds), blasts=(a.blasts, b.blasts),
                used=(dict(a.used), dict(b.used)), absorbed=(a.absorbed, b.absorbed), overtime=overtime, overtime_hits=ot_hits,
                kill=(a.armor <= 0 or b.armor <= 0))


def replay(prog_a, prog_b, cfg):
    g, w = cfg.grid()
    tr = []
    res = play(prog_a, prog_b, cfg, trace=tr)
    arrows = "^>v<"
    for (tick, aa, ab, pa, da, ha, pb, db, hb) in tr:
        print(f"\ntick {tick:2d}  A:{NAMES[aa] if aa >= 0 else 'IDLE':<6} armor {ha}   "
              f"B:{NAMES[ab] if ab >= 0 else 'IDLE':<6} armor {hb}")
        for y in range(cfg.size, 0, -1):
            row = ""
            for x in range(1, cfg.size + 1):
                i = y * w + x
                row += ("A" + arrows[da] if i == pa else "B" + arrows[db] if i == pb
                        else "##" if g[i] else " .")
            print("  " + row)
    print("\nresult:", res)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--replay":
        cfg = Config()
        pa, pb = parse(sys.argv[2]), parse(sys.argv[3])
        for p in (pa, pb):
            err = validate(p, cfg)
            if err:
                sys.exit(f"illegal program ({err}): {show(p)}")
        replay(pa, pb, cfg)
    else:
        print(__doc__)
