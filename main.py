import sys
import pygame
from simulation import World, Simulation, DAY_STEPS
from renderer import Renderer

FPS = 60
MIN_SPEED = 1
MAX_SPEED = 60
# At speed=1, 1 real minute per day  →  DAY_STEPS / 60 steps per second
STEPS_PER_SEC_BASE = DAY_STEPS / 60.0


def main():
    pygame.init()
    pygame.display.set_caption("Village Simulation")

    world = World()
    sim = Simulation(world)
    renderer = Renderer(world)
    clock = pygame.time.Clock()

    paused = False
    speed = 1           # multiplier: 1x = 1 min/jour, 2x = 30s/jour…
    step_in_day = 0
    day_started = False
    step_acc = 0.0      # fractional step accumulator

    running = True
    while running:
        # ── Events ────────────────────────────────────────────────────────────
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
                    world = World()
                    sim = Simulation(world)
                    renderer = Renderer(world)
                    step_in_day = 0
                    day_started = False
                    step_acc = 0.0
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not paused:
            # Accumulate fractional steps this frame
            step_acc += speed * STEPS_PER_SEC_BASE / FPS

            while step_acc >= 1.0:
                step_acc -= 1.0

                if not day_started:
                    sim.start_day()
                    day_started = True
                    step_in_day = 0

                sim.step()
                step_in_day += 1

                if step_in_day >= DAY_STEPS:
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
