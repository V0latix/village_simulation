import random
import math
from typing import List, Tuple
from entities import Agent, Carrot, Cow, STRATEGIES

# ── Constants ──────────────────────────────────────────────────────────────────

WORLD_W = 900
WORLD_H = 700

SURVIVAL_THRESHOLD = 5
COW_VALUE = 10
CARROT_VALUE = 1
TARGET_COWS = 16
TARGET_CARROTS = 180
TENT_CAPACITY = 10
COLLECT_RADIUS = 28
HUNT_RADIUS = 50
AGENT_SPEED = 3.5
COW_SPEED = 1.2
MUTATION_RATE = 0.15
DIRECTION_CHANGE_PROB = 0.06  # probability to change direction each step
DAY_STEPS = 120               # simulation steps per day


# ── World ──────────────────────────────────────────────────────────────────────

class World:
    def __init__(self):
        self.width = WORLD_W
        self.height = WORLD_H
        self.agents: List[Agent] = []
        self.carrots: List[Carrot] = []
        self.cows: List[Cow] = []
        self.day = 0
        self.next_id = 0
        self.village_capacity = TENT_CAPACITY  # total village cap
        self.stats: List[dict] = []            # one dict per day

        self._init_population()
        self._spawn_resources()

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_population(self):
        # Start with one agent of each strategy
        self.village_capacity = max(TENT_CAPACITY, len(STRATEGIES))
        tents = self.tent_positions()
        for i, s in enumerate(STRATEGIES):
            tent_idx = i % len(tents)
            cx, cy = tents[tent_idx]
            a = self._new_agent(
                x=cx + random.uniform(-10, 10),
                y=cy + random.uniform(-5, 5),
                share_pref=s,
                home_tent=tent_idx,
            )
            self.agents.append(a)

    def _new_agent(self, x, y, share_pref, home_tent: int = 0) -> Agent:
        a = Agent(id=self.next_id, x=x, y=y, share_pref=share_pref, home_tent=home_tent)
        a.vx, a.vy = _random_velocity(AGENT_SPEED)
        self.next_id += 1
        return a

    def _spawn_resources(self):
        # Top up carrots
        active_carrots = sum(1 for c in self.carrots if c.active)
        for _ in range(TARGET_CARROTS - active_carrots):
            self.carrots.append(Carrot(
                x=random.uniform(20, self.width - 20),
                y=random.uniform(20, self.height - 20),
            ))
        # Top up cows
        active_cows = sum(1 for c in self.cows if c.active)
        for _ in range(TARGET_COWS - active_cows):
            cow = Cow(
                x=random.uniform(40, self.width - 40),
                y=random.uniform(40, self.height - 40),
            )
            cow.vx, cow.vy = _random_velocity(COW_SPEED)
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
        return math.ceil(self.village_capacity / TENT_CAPACITY)

    def tent_positions(self) -> List[tuple]:
        """Returns (cx, cy) for each tent — shared by simulation and renderer."""
        num = self.num_tents
        cols = max(1, min(num, 6))
        margin_x = 60
        margin_y = 30
        spacing_x = (self.width - 2 * margin_x) // max(cols, 1)
        spacing_y = 70
        positions = []
        for i in range(num):
            col = i % cols
            row = i // cols
            cx = margin_x + col * spacing_x
            cy = margin_y + row * spacing_y
            positions.append((cx, cy))
        return positions


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
            # Place agent back at their home tent
            tent_idx = min(a.home_tent, len(tents) - 1)
            cx, cy = tents[tent_idx]
            a.x = cx + random.uniform(-12, 12)
            a.y = cy + random.uniform(-8, 8)
            a.vx, a.vy = _random_velocity(AGENT_SPEED)
        # Remove spent resources
        w.carrots = [c for c in w.carrots if c.active]
        w.cows = [c for c in w.cows if c.active]
        w._spawn_resources()

    def step(self):
        """One movement + collection tick."""
        w = self.world
        _move_agents(w)
        _move_cows(w)
        _collect_carrots(w)

    def end_day(self):
        w = self.world
        _perform_hunts(w)
        _resolve_survival(w)
        newborns = _reproduce(w)
        _mutate(newborns)
        _expand_village(w)
        _record_stats(w)
        # Compact dead agents periodically
        if len(w.agents) > 2000:
            w.agents = w.living_agents


# ── Movement ──────────────────────────────────────────────────────────────────

def _random_velocity(speed: float) -> Tuple[float, float]:
    angle = random.uniform(0, 2 * math.pi)
    return math.cos(angle) * speed, math.sin(angle) * speed


def _move_agents(w: World):
    for a in w.living_agents:
        if random.random() < DIRECTION_CHANGE_PROB:
            a.vx, a.vy = _random_velocity(AGENT_SPEED)
        a.x = (a.x + a.vx) % w.width
        a.y = (a.y + a.vy) % w.height


def _move_cows(w: World):
    for c in w.active_cows:
        if random.random() < DIRECTION_CHANGE_PROB:
            c.vx, c.vy = _random_velocity(COW_SPEED)
        c.x = (c.x + c.vx) % w.width
        c.y = (c.y + c.vy) % w.height


# ── Resource collection ────────────────────────────────────────────────────────

def _collect_carrots(w: World):
    for a in w.living_agents:
        for c in w.active_carrots:
            if _dist(a.x, a.y, c.x, c.y) < COLLECT_RADIUS:
                a.score += CARROT_VALUE
                c.active = False
                break  # one carrot per step


# ── Cooperative hunting ────────────────────────────────────────────────────────

def _perform_hunts(w: World):
    """Greedily pair agents that are close to a cow and haven't hunted today."""
    available = [a for a in w.living_agents if not a.hunted_today]
    random.shuffle(available)

    for cow in w.active_cows:
        # Find up to 2 available agents near this cow
        nearby = [a for a in available if _dist(a.x, a.y, cow.x, cow.y) < HUNT_RADIUS * 4]
        if len(nearby) < 2:
            continue
        a1, a2 = nearby[0], nearby[1]
        _resolve_hunt(a1, a2)
        a1.hunted_today = True
        a2.hunted_today = True
        a1.partner_id = a2.id
        a2.partner_id = a1.id
        cow.active = False
        available.remove(a1)
        available.remove(a2)


def _resolve_hunt(a: Agent, b: Agent):
    """Apply sharing rules and update scores."""
    pa, pb = a.share_pref, b.share_pref
    total = pa + pb

    if abs(total - 1.0) < 1e-9:
        # Case 1: complementary — exact split
        a.score += COW_VALUE * pa
        b.score += COW_VALUE * pb
    elif total < 1.0:
        # Case 2: under-claimed — each takes their share, split the rest
        base_a = COW_VALUE * pa
        base_b = COW_VALUE * pb
        leftover = COW_VALUE - base_a - base_b
        # Split leftover; greedier gets the bigger half if it can't split evenly
        if pa >= pb:
            a.score += base_a + math.ceil(leftover / 2)
            b.score += base_b + math.floor(leftover / 2)
        else:
            a.score += base_a + math.floor(leftover / 2)
            b.score += base_b + math.ceil(leftover / 2)
    else:
        # Case 3: conflict — forced equal split (penalizes the greedy)
        a.score += COW_VALUE / 2
        b.score += COW_VALUE / 2


# ── Survival & reproduction ────────────────────────────────────────────────────

def _resolve_survival(w: World):
    for a in w.living_agents:
        if a.score < SURVIVAL_THRESHOLD:
            a.alive = False


def _reproduce(w: World) -> List[Agent]:
    newborns = []
    for a in w.living_agents:
        num_children = int((a.score - SURVIVAL_THRESHOLD) // SURVIVAL_THRESHOLD)
        for _ in range(num_children):
            child = w._new_agent(
                x=a.x + random.uniform(-20, 20),
                y=a.y + random.uniform(-20, 20),
                share_pref=a.share_pref,
                home_tent=a.home_tent,
            )
            newborns.append(child)
    w.agents.extend(newborns)
    return newborns


def _mutate(newborns: List[Agent]):
    for a in newborns:
        if random.random() < MUTATION_RATE:
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
        w.village_capacity += TENT_CAPACITY


# ── Statistics ────────────────────────────────────────────────────────────────

def _record_stats(w: World):
    living = w.living_agents
    if not living:
        w.stats.append({"day": w.day, "pop": 0, "dist": {s: 0 for s in STRATEGIES}})
        return
    dist = {s: 0 for s in STRATEGIES}
    for a in living:
        dist[a.share_pref] = dist.get(a.share_pref, 0) + 1
    w.stats.append({
        "day": w.day,
        "pop": len(living),
        "dist": dist,
        "mean_pref": sum(a.share_pref for a in living) / len(living),
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dist(x1, y1, x2, y2) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
