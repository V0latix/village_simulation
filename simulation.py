import random
import math
from typing import List, Tuple, TYPE_CHECKING

from entities import Agent, Carrot, Cow, STRATEGIES

if TYPE_CHECKING:
    from main import Config


# ── World ──────────────────────────────────────────────────────────────────────

class World:
    def __init__(self, cfg: "Config"):
        self.cfg = cfg
        self.width  = cfg.world_w
        self.height = cfg.world_h
        self.agents: List[Agent] = []
        self.carrots: List[Carrot] = []
        self.cows: List[Cow] = []
        self.day = 0
        self.next_id = 0
        self.village_capacity = cfg.tent_capacity
        self.stats: List[dict] = []

        self._init_population()
        self._spawn_resources()

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_population(self):
        cfg = self.cfg
        self.village_capacity = cfg.tent_capacity
        tents = self.tent_positions()
        for i in range(cfg.initial_population):
            s = STRATEGIES[i % len(STRATEGIES)]
            tent_idx = i % len(tents)
            x, y = _spawn_near_tent(tents[tent_idx], cfg) if cfg.show_tents else (
                random.uniform(40, self.width - 40),
                random.uniform(40, self.height - 40),
            )
            self.agents.append(self._new_agent(x, y, s, tent_idx))

    def _new_agent(self, x, y, share_pref, home_tent: int = 0) -> Agent:
        a = Agent(id=self.next_id, x=x, y=y, share_pref=share_pref, home_tent=home_tent)
        a.vx, a.vy = _random_velocity(self.cfg.agent_speed)
        self.next_id += 1
        return a

    def _spawn_resources(self):
        cfg = self.cfg
        active = sum(1 for c in self.carrots if c.active)
        for _ in range(cfg.target_carrots - active):
            self.carrots.append(Carrot(
                x=random.uniform(20, self.width - 20),
                y=random.uniform(20, self.height - 20),
            ))
        if cfg.enable_cows:
            active_cows = sum(1 for c in self.cows if c.active)
            for _ in range(cfg.target_cows - active_cows):
                cow = Cow(
                    x=random.uniform(40, self.width - 40),
                    y=random.uniform(40, self.height - 40),
                )
                cow.vx, cow.vy = _random_velocity(cfg.cow_speed)
                self.cows.append(cow)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def living_agents(self) -> List[Agent]:
        return [a for a in self.agents if a.alive]

    @property
    def active_carrots(self) -> List[Carrot]:
        return [c for c in self.carrots if c.active]

    @property
    def active_cows(self) -> List[Cow]:
        return [c for c in self.cows if c.active]

    @property
    def num_tents(self) -> int:
        return math.ceil(self.village_capacity / self.cfg.tent_capacity)

    def tent_positions(self) -> List[tuple]:
        """Grid of tent positions, centered on the world. First tent = center."""
        num = self.num_tents
        cols = min(num, 6)
        rows = math.ceil(num / cols)
        sx, sy = 110, 90
        start_x = self.width  // 2 - (cols - 1) * sx // 2
        start_y = self.height // 2 - (rows - 1) * sy // 2
        return [
            (start_x + (i % cols) * sx, start_y + (i // cols) * sy)
            for i in range(num)
        ]


# ── Simulation ─────────────────────────────────────────────────────────────────

class Simulation:
    def __init__(self, world: World):
        self.world = world

    def start_day(self):
        w = self.world
        w.day += 1
        tents = w.tent_positions()
        for a in w.living_agents:
            a.score = 0.0
            a.hunted_today = False
            a.partner_id = None
            if w.cfg.show_tents:
                tent_idx = min(a.home_tent, len(tents) - 1)
                a.x, a.y = _spawn_near_tent(tents[tent_idx], w.cfg)
            a.vx, a.vy = _random_velocity(w.cfg.agent_speed)
        w.carrots = [c for c in w.carrots if c.active]
        if w.cfg.enable_cows:
            w.cows = [c for c in w.cows if c.active]
        w._spawn_resources()

    def step(self):
        w = self.world
        _move_agents(w)
        if w.cfg.enable_cows:
            _move_cows(w)
        _collect_carrots(w)

    def end_day(self):
        w = self.world
        if w.cfg.enable_cows:
            _perform_hunts(w)
        _resolve_survival(w)
        newborns = _reproduce(w)
        _mutate(newborns, w.cfg.mutation_rate)
        _expand_village(w)
        _record_stats(w)
        if len(w.agents) > 2000:
            w.agents = w.living_agents


# ── Movement ──────────────────────────────────────────────────────────────────

def _random_velocity(speed: float) -> Tuple[float, float]:
    angle = random.uniform(0, 2 * math.pi)
    return math.cos(angle) * speed, math.sin(angle) * speed


def _move_agents(w: World):
    cfg = w.cfg
    carrots = w.active_carrots
    for a in w.living_agents:
        target = _nearest_in_range(a.x, a.y, carrots, cfg.vision_radius)
        if target is not None:
            dx = target.x - a.x
            dy = target.y - a.y
            d = math.sqrt(dx * dx + dy * dy)
            if d > 0:
                a.vx = dx / d * cfg.agent_speed
                a.vy = dy / d * cfg.agent_speed
        else:
            if random.random() < cfg.direction_change_prob:
                a.vx, a.vy = _random_velocity(cfg.agent_speed)
        a.x = (a.x + a.vx) % w.width
        a.y = (a.y + a.vy) % w.height


def _move_cows(w: World):
    cfg = w.cfg
    for c in w.active_cows:
        if random.random() < cfg.direction_change_prob:
            c.vx, c.vy = _random_velocity(cfg.cow_speed)
        c.x = (c.x + c.vx) % w.width
        c.y = (c.y + c.vy) % w.height


def _nearest_in_range(x, y, items, radius):
    best, best_d = None, radius
    for item in items:
        d = _dist(x, y, item.x, item.y)
        if d < best_d:
            best_d = d
            best = item
    return best


# ── Resource collection ────────────────────────────────────────────────────────

def _collect_carrots(w: World):
    r = w.cfg.collect_radius
    for a in w.living_agents:
        for c in w.active_carrots:
            if _dist(a.x, a.y, c.x, c.y) < r:
                a.score += w.cfg.carrot_value
                c.active = False
                break


# ── Cooperative hunting ────────────────────────────────────────────────────────

def _perform_hunts(w: World):
    available = [a for a in w.living_agents if not a.hunted_today]
    random.shuffle(available)
    for cow in w.active_cows:
        nearby = [a for a in available if _dist(a.x, a.y, cow.x, cow.y) < w.cfg.hunt_radius * 4]
        if len(nearby) < 2:
            continue
        a1, a2 = nearby[0], nearby[1]
        _resolve_hunt(a1, a2, w.cfg.cow_value)
        a1.hunted_today = a2.hunted_today = True
        a1.partner_id = a2.id
        a2.partner_id = a1.id
        cow.active = False
        available.remove(a1)
        available.remove(a2)


def _resolve_hunt(a: Agent, b: Agent, cow_value: float):
    pa, pb = a.share_pref, b.share_pref
    total = pa + pb
    if abs(total - 1.0) < 1e-9:
        a.score += cow_value * pa
        b.score += cow_value * pb
    elif total < 1.0:
        base_a, base_b = cow_value * pa, cow_value * pb
        leftover = cow_value - base_a - base_b
        if pa >= pb:
            a.score += base_a + math.ceil(leftover / 2)
            b.score += base_b + math.floor(leftover / 2)
        else:
            a.score += base_a + math.floor(leftover / 2)
            b.score += base_b + math.ceil(leftover / 2)
    else:
        a.score += cow_value / 2
        b.score += cow_value / 2


# ── Survival & reproduction ────────────────────────────────────────────────────

def _resolve_survival(w: World):
    t = w.cfg.survival_threshold
    for a in w.living_agents:
        if a.score < t:
            a.alive = False


def _reproduce(w: World) -> List[Agent]:
    t = w.cfg.survival_threshold
    newborns = []
    for a in w.living_agents:
        for _ in range(int((a.score - t) // t)):
            child = w._new_agent(
                x=a.x + random.uniform(-20, 20),
                y=a.y + random.uniform(-20, 20),
                share_pref=a.share_pref,
                home_tent=_least_populated_tent(w),
            )
            newborns.append(child)
    w.agents.extend(newborns)
    return newborns


def _least_populated_tent(w: World) -> int:
    """Return the tent index with the fewest assigned living agents."""
    num_tents = w.num_tents
    counts = [0] * num_tents
    for a in w.living_agents:
        idx = min(a.home_tent, num_tents - 1)
        counts[idx] += 1
    return counts.index(min(counts))


def _mutate(newborns: List[Agent], rate: float):
    for a in newborns:
        if random.random() < rate:
            idx = STRATEGIES.index(a.share_pref)
            if idx == 0:
                a.share_pref = STRATEGIES[1]
            elif idx == len(STRATEGIES) - 1:
                a.share_pref = STRATEGIES[-2]
            else:
                a.share_pref = STRATEGIES[idx + random.choice([-1, 1])]


# ── Village expansion ──────────────────────────────────────────────────────────

def _expand_village(w: World):
    pop = len(w.living_agents)
    while w.village_capacity < pop:
        w.village_capacity += w.cfg.tent_capacity


# ── Statistics ────────────────────────────────────────────────────────────────

def _record_stats(w: World):
    living = w.living_agents
    dist = {s: 0 for s in STRATEGIES}
    if not living:
        w.stats.append({"day": w.day, "pop": 0, "dist": dist})
        return
    for a in living:
        dist[a.share_pref] += 1
    w.stats.append({
        "day": w.day,
        "pop": len(living),
        "dist": dist,
        "mean_pref": sum(a.share_pref for a in living) / len(living),
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dist(x1, y1, x2, y2) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _spawn_near_tent(tent: tuple, cfg) -> tuple:
    """Random position within tent_spawn_radius of the tent center."""
    cx, cy = tent
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, cfg.tent_spawn_radius)
    return cx + math.cos(angle) * r, cy + math.sin(angle) * r
