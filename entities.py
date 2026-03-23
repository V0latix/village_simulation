from dataclasses import dataclass, field
from typing import Optional


STRATEGIES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


@dataclass
class Agent:
    id: int
    x: float
    y: float
    share_pref: float = 0.5   # one of STRATEGIES
    score: float = 0.0
    alive: bool = True
    hunted_today: bool = False
    partner_id: Optional[int] = None
    home_tent: int = 0
    # velocity
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class Carrot:
    x: float
    y: float
    active: bool = True


@dataclass
class Cow:
    x: float
    y: float
    active: bool = True
    vx: float = 0.0
    vy: float = 0.0
