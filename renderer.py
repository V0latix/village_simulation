import math
import pygame
from entities import STRATEGIES
from simulation import World
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Config

# ── Static palette (not user-tunable) ─────────────────────────────────────────

BG_COLOR     = (34, 85, 34)
GRID_COLOR   = (30, 75, 30)
CARROT_COLOR = (255, 140, 0)
COW_COLOR    = (160, 110, 60)
TENT_COLOR   = (200, 180, 120)
TENT_OUTLINE = (140, 110, 60)
PANEL_BG     = (20, 20, 30)
WHITE        = (240, 240, 240)
GREY         = (160, 160, 160)

STRATEGY_LABELS = {
    0.1: "10%", 0.2: "20%", 0.3: "30%", 0.4: "40%", 0.5: "50%",
    0.6: "60%", 0.7: "70%", 0.8: "80%", 0.9: "90%",
}


def _strategy_color(pref: float) -> tuple:
    t = (pref - 0.1) / 0.8
    if t < 0.5:
        s = t * 2
        return (int(s * 50), int(100 + s * 100), int(220 - s * 120))
    else:
        s = (t - 0.5) * 2
        return (int(50 + s * 205), int(200 - s * 160), int(100 - s * 100))


STRATEGY_COLORS = {s: _strategy_color(s) for s in STRATEGIES}


class Renderer:
    def __init__(self, world: World, cfg: "Config"):
        self.world = world
        self.cfg = cfg
        pw = cfg.panel_w
        self.screen_w = world.width + pw
        self.screen_h = world.height
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Village Simulation — L'égoïsme")
        self.font_s = pygame.font.SysFont("monospace", 12)
        self.font_m = pygame.font.SysFont("monospace", 15, bold=True)
        self.font_l = pygame.font.SysFont("monospace", 20, bold=True)
        # Pre-render vision surfaces (one per strategy)
        vr = cfg.vision_radius
        self._vision_surfs = {}
        for s, color in STRATEGY_COLORS.items():
            surf = pygame.Surface((vr * 2, vr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 20), (vr, vr), vr)
            pygame.draw.circle(surf, (*color, 55), (vr, vr), vr, 2)
            self._vision_surfs[s] = surf

    def draw(self, paused: bool = False, speed: int = 1):
        cfg = self.cfg
        w = self.world
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        if cfg.show_tents:
            self._draw_tents(w)
        self._draw_carrots(w)
        if cfg.enable_cows:
            self._draw_cows(w)
        self._draw_agents(w)
        self._draw_hud(w, paused, speed)
        self._draw_panel(w)
        pygame.display.flip()

    # ── World elements ────────────────────────────────────────────────────────

    def _draw_grid(self):
        w = self.world
        for x in range(0, w.width, 80):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, w.height))
        for y in range(0, w.height, 80):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (w.width, y))

    def _draw_tents(self, w: World):
        for cx, cy in w.tent_positions():
            roof = [(cx, cy - 22), (cx - 22, cy + 5), (cx + 22, cy + 5)]
            pygame.draw.polygon(self.screen, TENT_COLOR, roof)
            pygame.draw.polygon(self.screen, TENT_OUTLINE, roof, 2)
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
            pygame.draw.circle(self.screen, COW_COLOR, (x + 12, y - 4), 8)
            pygame.draw.circle(self.screen, (100, 70, 30), (x + 12, y - 4), 8, 2)

    def _draw_agents(self, w: World):
        vr = self.cfg.vision_radius
        for a in w.living_agents:
            x, y = int(a.x), int(a.y)
            color = STRATEGY_COLORS[a.share_pref]
            self.screen.blit(self._vision_surfs[a.share_pref], (x - vr, y - vr))
            pygame.draw.circle(self.screen, color, (x, y), 7)
            pygame.draw.circle(self.screen, WHITE, (x, y), 7, 1)
            if a.partner_id is not None:
                pygame.draw.circle(self.screen, (255, 255, 100), (x, y), 9, 2)

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, w: World, paused: bool, speed: int):
        lines = [
            f"Jour {w.day}",
            f"Population: {len(w.living_agents)}",
            f"Tentes: {w.num_tents}  (cap {w.village_capacity})",
            f"Vitesse: x{speed}  [+/-]",
        ]
        if paused:
            lines.append("PAUSE  [ESPACE]")
        if w.stats:
            lines.append(f"Pref moy: {w.stats[-1].get('mean_pref', 0.5):.2f}")
        y = 8
        for line in lines:
            surf = self.font_m.render(line, True, WHITE)
            pad = 4
            bg = pygame.Surface((surf.get_width() + pad * 2, surf.get_height() + pad), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            self.screen.blit(bg, (8 - pad, y - pad // 2))
            self.screen.blit(surf, (8, y))
            y += surf.get_height() + 4

    # ── Stats panel ───────────────────────────────────────────────────────────

    def _draw_panel(self, w: World):
        cfg = self.cfg
        px = w.width
        pw = cfg.panel_w
        pygame.draw.rect(self.screen, PANEL_BG, (px, 0, pw, self.screen_h))
        pygame.draw.line(self.screen, GREY, (px, 0), (px, self.screen_h), 2)

        y = 14
        self.screen.blit(self.font_l.render("Stratégies", True, WHITE), (px + 10, y))
        y += 36

        if not w.living_agents:
            return

        counts = {s: 0 for s in STRATEGIES}
        for a in w.living_agents:
            counts[a.share_pref] += 1
        max_count = max(counts.values()) or 1
        bar_area_w = pw - 90
        bar_h, gap = 22, 6

        for s in STRATEGIES:
            count = counts[s]
            color = STRATEGY_COLORS[s]
            self.screen.blit(self.font_s.render(STRATEGY_LABELS[s], True, GREY), (px + 8, y + 4))
            bw = int(bar_area_w * count / max_count)
            if bw > 0:
                pygame.draw.rect(self.screen, color, (px + 48, y, bw, bar_h))
            pygame.draw.rect(self.screen, GREY, (px + 48, y, bar_area_w, bar_h), 1)
            self.screen.blit(self.font_s.render(str(count), True, WHITE), (px + 54 + bar_area_w, y + 4))
            y += bar_h + gap

        if len(w.stats) > 1:
            y += 36
            self.screen.blit(self.font_s.render("Préférence moyenne", True, GREY), (px + 10, y))
            y += 16
            chart_h, chart_w = 80, pw - 20
            pygame.draw.rect(self.screen, (30, 30, 50), (px + 10, y, chart_w, chart_h))
            pygame.draw.rect(self.screen, GREY, (px + 10, y, chart_w, chart_h), 1)
            prefs = [s.get("mean_pref", 0.5) for s in w.stats][-chart_w:]
            pts = [
                (px + 10 + i * chart_w // max(len(prefs), 1),
                 y + chart_h - int((p - 0.1) / 0.8 * chart_h))
                for i, p in enumerate(prefs)
            ]
            if len(pts) >= 2:
                pygame.draw.lines(self.screen, (100, 200, 255), False, pts, 2)
            ref_y = y + chart_h - int((0.5 - 0.1) / 0.8 * chart_h)
            pygame.draw.line(self.screen, (80, 80, 80), (px + 10, ref_y), (px + 10 + chart_w, ref_y))
            self.screen.blit(self.font_s.render("0.5", True, GREY), (px + 14, ref_y - 10))

        y = self.screen_h - 52
        for c in ["[ESPACE] pause", "[+/-] vitesse", "[R] reset"]:
            self.screen.blit(self.font_s.render(c, True, GREY), (px + 10, y))
            y += 16


