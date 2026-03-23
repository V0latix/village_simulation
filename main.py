import sys
from dataclasses import dataclass
import pygame
from simulation import World, Simulation
from renderer import Renderer


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG — all simulation parameters live here
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Config:
    # ── Feature flags ─────────────────────────────────────────────────────────
    enable_cows:  bool  = False  # cooperative cow hunting
    show_tents:   bool  = True   # draw tents + reset agents there each morning

    # ── World ─────────────────────────────────────────────────────────────────
    world_w:      int   = 900
    world_h:      int   = 700

    # ── Resources ─────────────────────────────────────────────────────────────
    target_carrots:     int   = 300
    target_cows:        int   = 16
    carrot_value:       float = 1.0
    cow_value:          float = 10.0

    # ── Agents ────────────────────────────────────────────────────────────────
    agent_speed:        float = 3.5
    vision_radius:      int   = 25    # px — how far an agent can spot a carrot
    collect_radius:     int   = 5    # px — pickup distance
    direction_change_prob: float = 0.04  # low = long straight runs

    # ── Survival & reproduction ───────────────────────────────────────────────
    survival_threshold: float = 5.0   # points needed to survive the day
    mutation_rate:      float = 0.15  # probability a child mutates ±1 strategy

    # ── Village ───────────────────────────────────────────────────────────────
    tent_capacity:      int   = 10    # inhabitants per tent
    tent_spawn_radius:  int   = 30    # px — random scatter around tent at day start
    day_steps:          int   = 250   # simulation ticks per day

    # ── Cows (used only when enable_cows=True) ────────────────────────────────
    cow_speed:          float = 1.2
    hunt_radius:        int   = 50

    # ── Display ───────────────────────────────────────────────────────────────
    panel_w:            int   = 280   # width of the right stats panel


# Edit the values above to tune the simulation
cfg = Config()

# ══════════════════════════════════════════════════════════════════════════════

FPS = 60
MIN_SPEED = 1
MAX_SPEED = 60
# At speed=1 → 1 real minute per day
STEPS_PER_SEC_BASE = cfg.day_steps / 60.0


def main():
    pygame.init()
    pygame.display.set_caption("Village Simulation")

    world = World(cfg)
    sim = Simulation(world)
    renderer = Renderer(world, cfg)
    clock = pygame.time.Clock()

    paused = False
    speed = 1
    step_in_day = 0
    day_started = False
    step_acc = 0.0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed = min(speed * 2, MAX_SPEED)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed = max(speed // 2, MIN_SPEED)
                elif event.key == pygame.K_r:
                    world = World(cfg)
                    sim = Simulation(world)
                    renderer = Renderer(world, cfg)
                    step_in_day = 0
                    day_started = False
                    step_acc = 0.0
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not paused:
            step_acc += speed * STEPS_PER_SEC_BASE / FPS
            while step_acc >= 1.0:
                step_acc -= 1.0
                if not day_started:
                    sim.start_day()
                    day_started = True
                    step_in_day = 0
                sim.step()
                step_in_day += 1
                if step_in_day >= cfg.day_steps:
                    sim.end_day()
                    day_started = False
                    if not world.living_agents:
                        paused = True
                        step_acc = 0.0
                        break

        renderer.draw(paused=paused, speed=speed)
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
