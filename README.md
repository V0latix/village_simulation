# Village Simulation — Comprendre l'égoïsme

Une simulation multi-agents 2D qui modélise l'évolution des stratégies de partage dans une population. Basée sur la théorie des jeux évolutionnaires.

## L'idée

Des villageois récoltent des carottes seuls et chassent des vaches en coopération. Chaque agent possède une **préférence de partage** (de 10 % à 90 %). Les agents qui accumulent assez de points survivent, se reproduisent et transmettent leur stratégie à leurs enfants (avec une chance de mutation).

La simulation révèle trois phases :

| Phase | Ce qui se passe |
|---|---|
| **A — Domination égoïste** | Les agents gourmands profitent des altruistes |
| **B — Déclin des altruistes** | À force d'être exploités, les généreux disparaissent |
| **C — Équilibre** | Sans altruistes à exploiter, les égoïstes s'entre-déchirent et les stratégies modérées (≈ 50/50) s'imposent |

## Installation

**Prérequis : macOS avec Homebrew**

```bash
# Bibliothèque de polices pour Pygame
brew install sdl2_ttf

# Installer Pygame
LDFLAGS="-L/opt/homebrew/lib" CFLAGS="-I/opt/homebrew/include" \
  pip3 install pygame --no-cache-dir

# Lancer
python3 main.py
```

## Contrôles

| Touche | Action |
|---|---|
| `Espace` | Pause / reprendre |
| `+` | Doubler la vitesse |
| `-` | Diviser la vitesse par 2 |
| `R` | Réinitialiser |
| `Échap` | Quitter |

Par défaut **1 journée = 1 minute** en temps réel. Appuyer sur `+` plusieurs fois pour accélérer (x2, x4, x8…).

## Mécanique centrale — le partage de la vache

Quand deux agents coopèrent sur une vache (10 points) :

- **Somme des parts = 100 %** → chacun reçoit exactement ce qu'il demandait
- **Somme < 100 %** → chacun prend sa part, le surplus est divisé (l'agent le plus gourmand prend la moitié supérieure)
- **Somme > 100 %** → **conflit** : partage forcé 50/50, l'agent gourmand est pénalisé

## Structure

```
main.py          # Boucle pygame, gestion des événements
simulation.py    # Toute la logique : World, Simulation, règles d'évolution
renderer.py      # Rendu visuel, HUD, panneau de statistiques
entities.py      # Dataclasses Agent, Carrot, Cow
docs/init.md     # Spécification technique détaillée
```

## Paramètres

Tous les paramètres sont dans `simulation.py` :

| Constante | Valeur par défaut | Rôle |
|---|---|---|
| `SURVIVAL_THRESHOLD` | 5 pts | Score minimum pour survivre |
| `COW_VALUE` | 10 pts | Gain d'une chasse coopérative |
| `MUTATION_RATE` | 15 % | Probabilité de mutation à la naissance |
| `DAY_STEPS` | 120 | Étapes de simulation par journée |
| `TARGET_CARROTS` | 180 | Carottes présentes simultanément |
| `TARGET_COWS` | 16 | Vaches présentes simultanément |