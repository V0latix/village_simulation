#!/usr/bin/env python3
"""Plot simulation results from JSON files saved by the village simulation.

Usage:
    python3 plot.py                      # plots the most recent JSON in simulations/
    python3 plot.py simulations/foo.json # plots a specific file
    python3 plot.py --all                # plots every JSON in simulations/ (one window each)
"""

import sys
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

plt.style.use("dark_background")

STRATEGIES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

# Blue → teal → green → yellow → orange → red  (matches the game's agent colors)
STRAT_COLORS = [
    "#3264DC", "#3296C8", "#32C8A0", "#64C878",
    "#96C850", "#C8B432", "#C87832", "#C83C32", "#FF1414",
]


# ── Data helpers ──────────────────────────────────────────────────────────────

def load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _series(history: list, key: str, default=0):
    return [s.get(key, default) for s in history]


def _strat_matrix(history: list) -> np.ndarray:
    """Shape (n_strategies, n_days). Keys are stored as strings in JSON."""
    mat = np.zeros((len(STRATEGIES), len(history)), dtype=float)
    for j, entry in enumerate(history):
        dist = entry.get("dist", {})
        for i, s in enumerate(STRATEGIES):
            mat[i, j] = dist.get(str(s), 0)
    return mat


# ── Plot ──────────────────────────────────────────────────────────────────────

def plot(data: dict, path: Path):
    params   = data.get("parameters") or {}
    history  = data["history"]
    n_days   = len(history)

    if n_days == 0:
        print(f"Aucune donnée dans {path}")
        return

    days      = _series(history, "day")
    pop       = _series(history, "pop")
    carrots   = _series(history, "carrots")
    cows      = _series(history, "cows")
    mean_pref = [s.get("mean_pref") for s in history]
    mean_pref_clean = [v if v is not None else float("nan") for v in mean_pref]
    strat_mat = _strat_matrix(history)

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(path.stem.replace("_", "  "), fontsize=13, color="white")
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

    # ── 1. Population ─────────────────────────────────────────────────────────
    ax_pop = fig.add_subplot(gs[0, 0])
    ax_pop.plot(days, pop, color="#78DC78", linewidth=2)
    ax_pop.fill_between(days, pop, alpha=0.15, color="#78DC78")
    ax_pop.set_title("Population")
    ax_pop.set_xlabel("Jour")
    ax_pop.set_ylabel("Agents")

    # ── 2. Resources per day ──────────────────────────────────────────────────
    ax_res = fig.add_subplot(gs[0, 1])
    ax_res.plot(days, carrots, color="#FF8C00", linewidth=2, label="Carottes")
    if any(c > 0 for c in cows):
        ax_res.plot(days, cows, color="#A06E3C", linewidth=2, label="Vaches")
        ax_res.legend(fontsize=8)
    ax_res.set_title("Ressources collectées / jour")
    ax_res.set_xlabel("Jour")

    # ── 3. Mean sharing preference ────────────────────────────────────────────
    ax_pref = fig.add_subplot(gs[0, 2])
    ax_pref.plot(days, mean_pref_clean, color="#64C8FF", linewidth=2)
    ax_pref.axhline(0.5, color="white", alpha=0.25, linestyle="--", linewidth=1)
    ax_pref.set_ylim(0.05, 0.95)
    ax_pref.set_yticks([0.1, 0.3, 0.5, 0.7, 0.9])
    ax_pref.set_title("Préférence de partage moyenne")
    ax_pref.set_xlabel("Jour")

    # ── 4. Strategy distribution — stacked area ───────────────────────────────
    ax_dist = fig.add_subplot(gs[1, :])
    ax_dist.stackplot(
        days, strat_mat,
        colors=STRAT_COLORS,
        labels=[f"{int(s * 100)}%" for s in STRATEGIES],
        alpha=0.85,
    )
    ax_dist.set_title("Distribution des stratégies (empilé)")
    ax_dist.set_xlabel("Jour")
    ax_dist.set_ylabel("Agents")
    ax_dist.legend(
        loc="upper right", fontsize=8, ncol=9,
        framealpha=0.4, title="Partage →",
    )

    # ── 5. Strategy lines (individual) ────────────────────────────────────────
    ax_lines = fig.add_subplot(gs[2, :2])
    for i, (s, color) in enumerate(zip(STRATEGIES, STRAT_COLORS)):
        counts = strat_mat[i]
        if counts.max() > 0:
            ax_lines.plot(days, counts, color=color, linewidth=1.5,
                          label=f"{int(s * 100)}%", alpha=0.9)
    ax_lines.set_title("Évolution par stratégie")
    ax_lines.set_xlabel("Jour")
    ax_lines.set_ylabel("Agents")
    ax_lines.legend(fontsize=7, ncol=3, framealpha=0.3)

    # ── 6. Parameters table ───────────────────────────────────────────────────
    ax_tbl = fig.add_subplot(gs[2, 2])
    ax_tbl.axis("off")
    if params:
        rows = [
            ("Population initiale",  params.get("initial_population", "?")),
            ("Seuil survie",         params.get("survival_threshold",  "?")),
            ("Taux mutation",        params.get("mutation_rate",        "?")),
            ("Carottes cibles",      params.get("target_carrots",      "?")),
            ("Vaches cibles",        params.get("target_cows",         "?")),
            ("Vitesse agent",        params.get("agent_speed",         "?")),
            ("Valeur vache",         params.get("cow_value",           "?")),
            ("Jours simulés",        n_days),
        ]
        tbl = ax_tbl.table(
            cellText=[[str(v)] for _, v in rows],
            rowLabels=[k for k, _ in rows],
            colLabels=["Valeur"],
            loc="center",
            cellLoc="right",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1, 1.3)
        for (r, c), cell in tbl.get_celld().items():
            cell.set_facecolor("#1a1a2e" if r % 2 == 0 else "#16213e")
            cell.set_edgecolor("#444466")
        ax_tbl.set_title("Paramètres", pad=8)
    else:
        ax_tbl.text(0.5, 0.5, "Paramètres\nnon disponibles",
                    ha="center", va="center", color="grey", fontsize=10,
                    transform=ax_tbl.transAxes)

    # ── Save & show ───────────────────────────────────────────────────────────
    out = path.with_suffix(".png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Graphiques sauvegardés : {out}")
    plt.show()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if args == ["--all"]:
        paths = sorted(Path("simulations").glob("*.json"),
                       key=lambda p: p.stat().st_mtime)
        if not paths:
            print("Aucun fichier JSON dans simulations/")
            sys.exit(1)
    elif args:
        paths = [Path(a) for a in args]
    else:
        # Default: most recent file
        candidates = sorted(Path("simulations").glob("*.json"),
                            key=lambda p: p.stat().st_mtime)
        if not candidates:
            print("Aucun fichier JSON dans simulations/  —  lancez d'abord la simulation et appuyez sur [S].")
            sys.exit(1)
        paths = [candidates[-1]]

    for p in paths:
        plot(load(p), p)


if __name__ == "__main__":
    main()
