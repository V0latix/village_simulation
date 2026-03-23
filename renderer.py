import math
import pygame
from entities import STRATEGIES
from simulation import World
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Config

# ── Static palette ─────────────────────────────────────────────────────────────

BG_COLOR     = (34, 85, 34)
GRID_COLOR   = (30, 75, 30)
CARROT_COLOR = (255, 140, 0)
COW_COLOR    = (160, 110, 60)
TENT_COLOR   = (200, 180, 120)
TENT_OUTLINE = (140, 110, 60)
PANEL_BG     = (20, 20, 30)
WHITE        = (240, 240, 240)
GREY         = (160, 160, 160)
DARK         = (40, 40, 55)

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
        self.screen_w = world.width + cfg.panel_w
        self.screen_h = world.height
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Village Simulation — L'égoïsme")
        self.font_s  = pygame.font.SysFont("monospace", 12)
        self.font_m  = pygame.font.SysFont("monospace", 15, bold=True)
        self.font_l  = pygame.font.SysFont("monospace", 20, bold=True)
        self.font_xl = pygame.font.SysFont("monospace", 26, bold=True)
        self.save_btn_rect = pygame.Rect(0, 0, 0, 0)
        # Pre-render vision surfaces (one per strategy)
        vr = cfg.vision_radius
        self._vision_surfs = {}
        for s, color in STRATEGY_COLORS.items():
            surf = pygame.Surface((vr * 2, vr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 20), (vr, vr), vr)
            pygame.draw.circle(surf, (*color, 55), (vr, vr), vr, 2)
            self._vision_surfs[s] = surf

    # ── Main draw ─────────────────────────────────────────────────────────────

    def draw(self, paused: bool = False, speed: int = 1, step_in_day: int = 0):
        cfg = self.cfg
        w   = self.world
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        if cfg.show_tents:
            self._draw_tents(w)
        self._draw_carrots(w)
        if cfg.enable_cows:
            self._draw_cows(w)
        self._draw_agents(w)
        self._draw_clock(w, step_in_day, cfg.day_steps)
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

    # ── Day clock ─────────────────────────────────────────────────────────────

    def _draw_clock(self, w: World, step_in_day: int, day_steps: int):
        cx = self.world.width - 58
        cy = self.screen_h - 58
        r  = 40
        progress = step_in_day / max(day_steps, 1)

        # Background disc
        pygame.draw.circle(self.screen, (20, 20, 30), (cx, cy), r)
        pygame.draw.circle(self.screen, GREY, (cx, cy), r, 2)

        # Progress arc (clockwise from 12 o'clock)
        if progress > 0.001:
            arc_rect = pygame.Rect(cx - r + 4, cy - r + 4, (r - 4) * 2, (r - 4) * 2)
            start_a  = math.pi / 2 - progress * 2 * math.pi
            end_a    = math.pi / 2
            pygame.draw.arc(self.screen, (100, 220, 120), arc_rect, start_a, end_a, 6)

        # Day number in center
        day_surf = self.font_m.render(f"J{w.day}", True, WHITE)
        self.screen.blit(day_surf, (cx - day_surf.get_width() // 2, cy - day_surf.get_height() // 2))

    # ── HUD (top-left overlay) ─────────────────────────────────────────────────

    def _draw_hud(self, w: World, paused: bool, speed: int):
        lines = [
            f"Jour {w.day}",
            f"Population: {len(w.living_agents)}",
            f"Vitesse: x{speed}  [+/-]",
        ]
        if paused:
            lines.append("PAUSE  [ESPACE]")

        y = 8
        for line in lines:
            surf = self.font_m.render(line, True, WHITE)
            pad  = 4
            bg   = pygame.Surface((surf.get_width() + pad * 2, surf.get_height() + pad), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            self.screen.blit(bg,   (8 - pad, y - pad // 2))
            self.screen.blit(surf, (8, y))
            y += surf.get_height() + 4

    # ── Stats panel ───────────────────────────────────────────────────────────

    def _draw_panel(self, w: World):
        cfg = self.cfg
        px  = w.width
        pw  = cfg.panel_w
        pygame.draw.rect(self.screen, PANEL_BG, (px, 0, pw, self.screen_h))
        pygame.draw.line(self.screen, GREY, (px, 0), (px, self.screen_h), 2)

        y = 12

        # ── Strategy distribution ──────────────────────────────────────────────
        self.screen.blit(self.font_l.render("Stratégies", True, WHITE), (px + 10, y))
        y += 32

        if w.living_agents:
            counts = {s: 0 for s in STRATEGIES}
            for a in w.living_agents:
                counts[a.share_pref] += 1
            max_count  = max(counts.values()) or 1
            bar_area_w = pw - 90
            bar_h, gap = 20, 5

            for s in STRATEGIES:
                count = counts[s]
                color = STRATEGY_COLORS[s]
                self.screen.blit(self.font_s.render(STRATEGY_LABELS[s], True, GREY), (px + 8, y + 3))
                bw = int(bar_area_w * count / max_count)
                if bw > 0:
                    pygame.draw.rect(self.screen, color, (px + 48, y, bw, bar_h))
                pygame.draw.rect(self.screen, GREY, (px + 48, y, bar_area_w, bar_h), 1)
                self.screen.blit(self.font_s.render(str(count), True, WHITE), (px + 54 + bar_area_w, y + 3))
                y += bar_h + gap

        y += 10
        _hline(self.screen, GREY, px + 8, px + pw - 8, y)
        y += 10

        # ── Today's stats ─────────────────────────────────────────────────────
        self.screen.blit(self.font_m.render("Aujourd'hui", True, WHITE), (px + 10, y))
        y += 24

        today = w.stats[-1] if w.stats else {}
        rows = [
            ("🥕 Carottes",  str(today.get("carrots", w.day_carrots))),
            ("🐄 Vaches",    str(today.get("cows",    w.day_cows))),
            ("👥 Pop",       str(today.get("pop",     len(w.living_agents)))),
        ]
        if today.get("mean_pref") is not None:
            rows.append(("⚖  Pref moy", f"{today['mean_pref']:.2f}"))

        for label, value in rows:
            lsurf = self.font_s.render(label, True, GREY)
            vsurf = self.font_s.render(value, True, WHITE)
            self.screen.blit(lsurf, (px + 10, y))
            self.screen.blit(vsurf, (px + pw - vsurf.get_width() - 10, y))
            y += 18

        y += 8
        _hline(self.screen, GREY, px + 8, px + pw - 8, y)
        y += 10

        # ── Historical charts ─────────────────────────────────────────────────
        if len(w.stats) > 1:
            chart_w = pw - 20
            # Carrots per day
            y = _draw_history_chart(
                self.screen, self.font_s, w.stats, "carrots",
                (255, 140, 0), "Carottes / jour",
                px + 10, y, chart_w, 45,
            )
            y += 8
            # Cows per day (only if cows enabled)
            if cfg.enable_cows:
                y = _draw_history_chart(
                    self.screen, self.font_s, w.stats, "cows",
                    (160, 110, 60), "Vaches / jour",
                    px + 10, y, chart_w, 40,
                )
                y += 8
            # Mean preference
            y = _draw_history_chart(
                self.screen, self.font_s, w.stats, "mean_pref",
                (100, 200, 255), "Préf. moyenne",
                px + 10, y, chart_w, 45,
                y_range=(0.1, 0.9),
            )
            y += 8
            # Population
            y = _draw_history_chart(
                self.screen, self.font_s, w.stats, "pop",
                (120, 220, 120), "Population",
                px + 10, y, chart_w, 45,
            )

        # ── Save button ───────────────────────────────────────────────────────
        btn_w, btn_h = pw - 20, 26
        btn_x = px + 10
        btn_y = self.screen_h - 82
        self.save_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (40, 100, 40), self.save_btn_rect, border_radius=4)
        pygame.draw.rect(self.screen, (80, 180, 80), self.save_btn_rect, 1, border_radius=4)
        lbl = self.font_m.render("[S]  Sauvegarder", True, WHITE)
        self.screen.blit(lbl, (btn_x + (btn_w - lbl.get_width()) // 2, btn_y + (btn_h - lbl.get_height()) // 2))

        # Controls at bottom
        ctrl_y = self.screen_h - 52
        for c in ["[ESPACE] pause", "[+/-] vitesse", "[R] reset"]:
            self.screen.blit(self.font_s.render(c, True, GREY), (px + 10, ctrl_y))
            ctrl_y += 16


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hline(surface, color, x1, x2, y):
    pygame.draw.line(surface, color, (x1, y), (x2, y))


def _draw_history_chart(surface, font, stats, key, color, title,
                        x, y, w, h, y_range=None):
    """Draw a small line chart. Returns the new y position below the chart."""
    surface.blit(font.render(title, True, GREY), (x, y))
    y += 14
    pygame.draw.rect(surface, (30, 30, 50), (x, y, w, h))
    pygame.draw.rect(surface, GREY, (x, y, w, h), 1)

    values = [s.get(key, 0) for s in stats]
    visible = values[-(w):]  # at most w data points
    if len(visible) < 2:
        return y + h

    lo, hi = y_range if y_range else (0, max(max(visible), 1))
    span = hi - lo or 1
    n    = len(visible)
    pts  = []
    for i, v in enumerate(visible):
        sx = x + i * w // (n - 1)
        sy = y + h - int((v - lo) / span * (h - 2)) - 1
        pts.append((sx, max(y + 1, min(y + h - 1, sy))))

    pygame.draw.lines(surface, color, False, pts, 2)

    # Min / max labels
    max_v = max(visible)
    lbl   = font.render(f"{max_v:.1f}" if isinstance(max_v, float) else str(max_v), True, color)
    surface.blit(lbl, (x + 2, y + 1))

    return y + h
