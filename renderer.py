import math
import pygame
from simulation import World, STRATEGIES, TENT_CAPACITY

# ── Palette ────────────────────────────────────────────────────────────────────

BG_COLOR        = (34, 85, 34)      # dark grass
GRID_COLOR      = (30, 75, 30)
CARROT_COLOR    = (255, 140, 0)
COW_COLOR       = (160, 110, 60)
TENT_COLOR      = (200, 180, 120)
TENT_OUTLINE    = (140, 110, 60)
HUD_BG          = (20, 20, 30, 180)
PANEL_BG        = (20, 20, 30)
WHITE           = (240, 240, 240)
GREY            = (160, 160, 160)

PANEL_W = 280   # right-side stats panel width


def strategy_color(pref: float) -> tuple:
    """Blue (generous 0.1) → green (0.5) → red (egoist 0.9)."""
    t = (pref - 0.1) / 0.8  # 0..1
    if t < 0.5:
        s = t * 2  # 0..1
        r = int(0 + s * 50)
        g = int(100 + s * 100)
        b = int(220 - s * 120)
    else:
        s = (t - 0.5) * 2  # 0..1
        r = int(50 + s * 205)
        g = int(200 - s * 160)
        b = int(100 - s * 100)
    return (r, g, b)


STRATEGY_COLORS = {s: strategy_color(s) for s in STRATEGIES}

# Label names for strategies
STRATEGY_LABELS = {
    0.1: "10%", 0.2: "20%", 0.3: "30%", 0.4: "40%", 0.5: "50%",
    0.6: "60%", 0.7: "70%", 0.8: "80%", 0.9: "90%",
}


class Renderer:
    def __init__(self, world: World):
        self.world = world
        self.screen_w = world.width + PANEL_W
        self.screen_h = world.height
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Village Simulation — L'égoïsme")
        self.font_s = pygame.font.SysFont("monospace", 12)
        self.font_m = pygame.font.SysFont("monospace", 15, bold=True)
        self.font_l = pygame.font.SysFont("monospace", 20, bold=True)

    def draw(self, paused: bool = False, speed: int = 1):
        w = self.world
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        self._draw_tents(w)
        self._draw_carrots(w)
        self._draw_cows(w)
        self._draw_agents(w)
        self._draw_hud(w, paused, speed)
        self._draw_panel(w)
        pygame.display.flip()

    # ── World elements ────────────────────────────────────────────────────────

    def _draw_grid(self):
        w = self.world
        step = 80
        for x in range(0, w.width, step):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, w.height))
        for y in range(0, w.height, step):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (w.width, y))

    def _draw_tents(self, w: World):
        for cx, cy in w.tent_positions():
            # Triangle roof
            roof = [(cx, cy - 22), (cx - 22, cy + 5), (cx + 22, cy + 5)]
            pygame.draw.polygon(self.screen, TENT_COLOR, roof)
            pygame.draw.polygon(self.screen, TENT_OUTLINE, roof, 2)
            # Body rectangle
            pygame.draw.rect(self.screen, TENT_COLOR, (cx - 18, cy + 5, 36, 20))
            pygame.draw.rect(self.screen, TENT_OUTLINE, (cx - 18, cy + 5, 36, 20), 2)

    def _draw_carrots(self, w: World):
        for c in w.active_carrots:
            pygame.draw.circle(self.screen, CARROT_COLOR, (int(c.x), int(c.y)), 4)

    def _draw_cows(self, w: World):
        for c in w.active_cows:
            x, y = int(c.x), int(c.y)
            pygame.draw.ellipse(self.screen, COW_COLOR, (x - 14, y - 9, 28, 18))
            pygame.draw.ellipse(self.screen, (100, 70, 30), (x - 14, y - 9, 28, 18), 2)
            # Head
            pygame.draw.circle(self.screen, COW_COLOR, (x + 12, y - 4), 8)
            pygame.draw.circle(self.screen, (100, 70, 30), (x + 12, y - 4), 8, 2)

    def _draw_agents(self, w: World):
        for a in w.living_agents:
            x, y = int(a.x), int(a.y)
            color = STRATEGY_COLORS[a.share_pref]
            pygame.draw.circle(self.screen, color, (x, y), 7)
            pygame.draw.circle(self.screen, WHITE, (x, y), 7, 1)
            # Show hunt partnership
            if a.partner_id is not None:
                pygame.draw.circle(self.screen, (255, 255, 100), (x, y), 9, 2)

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, w: World, paused: bool, speed: int):
        pop = len(w.living_agents)
        lines = [
            f"Jour {w.day}",
            f"Population: {pop}",
            f"Tentes: {w.num_tents}  (cap {w.village_capacity})",
            f"Vitesse: x{speed}  [+/-]",
        ]
        if paused:
            lines.append("PAUSE  [ESPACE]")
        if w.stats:
            mean = w.stats[-1].get("mean_pref", 0.5)
            lines.append(f"Pref moy: {mean:.2f}")

        y = 8
        for line in lines:
            surf = self.font_m.render(line, True, WHITE)
            # Dark background chip
            pad = 4
            bg = pygame.Surface((surf.get_width() + pad * 2, surf.get_height() + pad), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            self.screen.blit(bg, (8 - pad, y - pad // 2))
            self.screen.blit(surf, (8, y))
            y += surf.get_height() + 4

    # ── Stats panel ───────────────────────────────────────────────────────────

    def _draw_panel(self, w: World):
        px = w.width
        pygame.draw.rect(self.screen, PANEL_BG, (px, 0, PANEL_W, self.screen_h))
        pygame.draw.line(self.screen, GREY, (px, 0), (px, self.screen_h), 2)

        y = 14
        title = self.font_l.render("Stratégies", True, WHITE)
        self.screen.blit(title, (px + 10, y))
        y += 36

        # Bar chart of strategy distribution
        if not w.living_agents:
            return
        counts = {s: 0 for s in STRATEGIES}
        for a in w.living_agents:
            counts[a.share_pref] += 1
        max_count = max(counts.values()) or 1
        bar_area_w = PANEL_W - 90
        bar_h = 22
        gap = 6

        for s in STRATEGIES:
            count = counts[s]
            bar_w = int(bar_area_w * count / max_count)
            color = STRATEGY_COLORS[s]

            # Label
            label = self.font_s.render(STRATEGY_LABELS[s], True, GREY)
            self.screen.blit(label, (px + 8, y + 4))

            # Bar
            if bar_w > 0:
                pygame.draw.rect(self.screen, color, (px + 48, y, bar_w, bar_h))
            pygame.draw.rect(self.screen, GREY, (px + 48, y, bar_area_w, bar_h), 1)

            # Count
            cnt_surf = self.font_s.render(str(count), True, WHITE)
            self.screen.blit(cnt_surf, (px + 54 + bar_area_w, y + 4))

            y += bar_h + gap

        # Phase indicator
        y += 14
        phase_label, phase_color = _detect_phase(w)
        phase_surf = self.font_m.render(f"Phase: {phase_label}", True, phase_color)
        self.screen.blit(phase_surf, (px + 10, y))

        # Mini time-series: mean preference over time
        if len(w.stats) > 1:
            y += 36
            header = self.font_s.render("Préférence moyenne (historique)", True, GREY)
            self.screen.blit(header, (px + 10, y))
            y += 16
            chart_h = 80
            chart_w = PANEL_W - 20
            pygame.draw.rect(self.screen, (30, 30, 50), (px + 10, y, chart_w, chart_h))
            pygame.draw.rect(self.screen, GREY, (px + 10, y, chart_w, chart_h), 1)

            prefs = [s.get("mean_pref", 0.5) for s in w.stats]
            # Draw line
            pts = []
            for i, p in enumerate(prefs[-chart_w:]):
                sx = px + 10 + i * chart_w // max(len(prefs[-chart_w:]), 1)
                sy = y + chart_h - int((p - 0.1) / 0.8 * chart_h)
                pts.append((sx, sy))
            if len(pts) >= 2:
                pygame.draw.lines(self.screen, (100, 200, 255), False, pts, 2)
            # 50% reference line
            ref_y = y + chart_h - int((0.5 - 0.1) / 0.8 * chart_h)
            pygame.draw.line(self.screen, (80, 80, 80), (px + 10, ref_y), (px + 10 + chart_w, ref_y), 1)
            lbl = self.font_s.render("0.5", True, GREY)
            self.screen.blit(lbl, (px + 14, ref_y - 10))

        # Legend
        y = self.screen_h - 14 * 3 - 10
        controls = ["[ESPACE] pause", "[+/-] vitesse", "[R] reset"]
        for c in controls:
            surf = self.font_s.render(c, True, GREY)
            self.screen.blit(surf, (px + 10, y))
            y += 16


def _detect_phase(w: World):
    if not w.stats:
        return "—", WHITE
    dist = w.stats[-1].get("dist", {})
    pop = w.stats[-1].get("pop", 0)
    if pop == 0:
        return "—", WHITE
    egoist_count = sum(dist.get(s, 0) for s in [0.7, 0.8, 0.9])
    generous_count = sum(dist.get(s, 0) for s in [0.1, 0.2, 0.3])
    moderate_count = sum(dist.get(s, 0) for s in [0.4, 0.5, 0.6])
    dominant = max(egoist_count, generous_count, moderate_count)
    if dominant == egoist_count and egoist_count > pop * 0.4:
        return "A — égoïstes dominent", (255, 100, 100)
    if dominant == moderate_count and moderate_count > pop * 0.4:
        return "C — équilibre", (100, 255, 100)
    return "B — transition", (255, 200, 60)
