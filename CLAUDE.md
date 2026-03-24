# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo structure

Each simulation version lives in its own subfolder:

| Folder | Description |
|---|---|
| `egoism_V0_1/` | Initial egoism simulation (sharing rule, evolutionary dynamics) |

## Running a simulation

```bash
cd egoism_V0_1
python3 main_egoismV0_1.py
```

Controls: `Space` = pause, `+`/`-` = speed up/down, `R` = reset, `Esc` = quit.

## Dependencies

Requires `pygame` built with SDL2_ttf support:

```bash
brew install sdl2_ttf
LDFLAGS="-L/opt/homebrew/lib" CFLAGS="-I/opt/homebrew/include" \
  pip3 install pygame --no-cache-dir --break-system-packages
```

## Architecture (egoism_V0_1)

Four files, each with a single responsibility:

| File | Role |
|---|---|
| `entities.py` | Pure data: `Agent`, `Carrot`, `Cow` dataclasses |
| `simulation.py` | All game logic: `World` (state) + `Simulation` (day orchestration) |
| `renderer.py` | All pygame drawing: world, agents, HUD, stats panel |
| `main_egoismV0_1.py` | Entry point: pygame event loop, wires the other three |

### Simulation loop (`simulation.py`)

A day runs as: `start_day()` → N × `step()` → `end_day()`.

- `step()`: move agents + cows, collect carrots
- `end_day()`: hunt cows, resolve survival (< 5 pts = death), reproduce (1 child per 5 pts above threshold), mutate newborns, expand village, record stats

### Sharing rule (the core mechanic)

When two agents cooperate on a cow (10 pts):

- **Sum == 100%** → each gets their exact share
- **Sum < 100%** → each takes their share; greedier agent gets the larger half of the leftover
- **Sum > 100%** (conflict) → both get 5 pts (forced equal split — penalizes the greedy)

### Evolutionary dynamics

Agents have a `share_pref` ∈ {0.1, 0.2, …, 0.9}. Children inherit parent's strategy; mutation shifts ±1 step with probability `MUTATION_RATE`. The simulation should exhibit three phases over ~50+ days: egoist dominance → altruist decline → convergence toward moderate strategies (40–60%).

### Key constants (all in `simulation.py`)

`SURVIVAL_THRESHOLD`, `COW_VALUE`, `CARROT_VALUE`, `TARGET_COWS`, `TARGET_CARROTS`, `MUTATION_RATE`, `DAY_STEPS`, `AGENT_SPEED`, `COLLECT_RADIUS`, `HUNT_RADIUS`.

### Renderer color scheme

Agent color encodes strategy: blue = generous (10%), red = egoist (90%), via `strategy_color()` in `renderer.py`. The right panel shows a live bar chart of the strategy distribution and a historical mean-preference line chart.
