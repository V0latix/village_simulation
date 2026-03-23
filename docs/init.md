# Résumé technique de la simulation “comprendre l’égoïsme”

## 1. Idée générale

La vidéo construit une **simulation multi-agents en 2D** dans laquelle une population d’habitants évolue au fil des journées selon trois mécanismes principaux :  
1. **récolte individuelle** de ressources simples,  
2. **coopération à deux** sur une ressource plus rentable,  
3. **héritage + mutation** d’une stratégie de partage.  [oai_citation:0‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

Le but n’est pas juste de faire une animation visuelle, mais de montrer comment une règle locale très simple de partage peut faire émerger :
- un avantage initial pour les profils très égoïstes,
- puis une hausse des conflits,
- puis un retour progressif vers des stratégies plus modérées, en particulier autour du **50/50**.  [oai_citation:1‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

---

Niveau technique j'aimerai que tous sois fait en python avec le package pygame pour commencé.

## 2. Les briques du modèle

### Agents
Chaque agent représente un habitant du village. Il :
- se déplace aléatoirement dans un espace 2D,
- collecte des carottes,
- peut coopérer avec un autre agent pour chasser une vache,
- possède une **préférence de partage**,
- survit, meurt ou se reproduit selon son score journalier.  [oai_citation:2‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Ressources
Il y a deux types de ressources :

#### Carottes
- récolte individuelle,
- **1 carotte = 1 point**.  [oai_citation:3‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

#### Vaches
- nécessitent une coopération entre deux agents,
- **1 vache = 10 points** à partager entre les deux partenaires.  [oai_citation:4‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

---

## 3. Paramètres explicitement donnés dans le script

### Temps
- une journée dure **1 minute** de simulation.  [oai_citation:5‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Survie
- si un agent obtient **moins de 5 points**, il meurt,
- s’il obtient **au moins 5 points**, il survit à la journée suivante.  [oai_citation:6‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Reproduction
- après avoir atteint 5 points pour survivre, l’agent se reproduit **une fois par tranche supplémentaire de 5 points**,
- exemple donné : **23 points → 3 reproductions**.  [oai_citation:7‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Village / capacité
- une tente peut contenir **10 habitants**,
- le village s’agrandit quand la population dépasse la capacité actuelle.  [oai_citation:8‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Coopération
- **une fois par jour**, un habitant peut s’allier avec un autre,
- ils peuvent alors chasser une vache ensemble.  [oai_citation:9‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Vaches
- la simulation maintient environ **16 vaches** présentes simultanément.  [oai_citation:10‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Stratégies de partage
Chaque agent a une part “idéale” de la vache, comprise entre :
- **10 %** pour les plus généreux,
- **90 %** pour les plus égoïstes.  [oai_citation:11‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

Il y a donc **9 stratégies discrètes** :
- 10 %
- 20 %
- 30 %
- 40 %
- 50 %
- 60 %
- 70 %
- 80 %
- 90 %  [oai_citation:12‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

---

## 4. Règle centrale : le partage de la vache

C’est **le cœur de la simulation**.

Quand deux agents coopèrent sur une vache :

### Cas 1 — Parts complémentaires
Si les deux parts demandées font exactement **100 %**, chacun reçoit ce qu’il demandait.  [oai_citation:13‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

Exemple :
- A veut 40 %
- B veut 60 %
- résultat : A prend 4 points, B prend 6 points

### Cas 2 — Somme inférieure à 100 %
Si les deux parts demandées font **moins de 100 %** :
- chacun prend d’abord la part qu’il voulait,
- le reste est partagé en deux,
- si le reste est impair, **le plus égoïste prend la plus grosse moitié**.  [oai_citation:14‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

Exemple :
- A veut 20 %
- B veut 30 %
- ils demandent 5 points au total
- il reste 5 points
- on les redistribue

### Cas 3 — Somme supérieure à 100 %
Si les deux parts demandées font **plus de 100 %** :
- il y a **conflit**,
- aucun des deux n’obtient l’intersection “impossible”,
- **les deux subissent une pénalité** pour modéliser le coût du conflit.  [oai_citation:15‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

Le script ne donne pas explicitement la valeur numérique exacte de cette pénalité. Il faut donc la choisir toi-même dans ton implémentation. L’exemple “90 % contre 40 %” indique qu’un égoïste extrême obtient **5 points** après conflit, ce qui suggère un modèle entier sur 10 points avec une pénalité de type `-4` sur sa demande de 9, ou un autre schéma équivalent. Le plus important est de rester cohérent dans la règle.  [oai_citation:16‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

---

## 5. Dynamique évolutive

Quand un agent se reproduit :
- l’enfant est une **copie du parent**,
- il hérite de la **même stratégie de partage**,
- avec une **petite chance de mutation**, il devient :
  - un peu plus généreux,
  - ou un peu plus égoïste.  [oai_citation:17‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

Concrètement, comme les stratégies sont discrètes, le plus simple est :
- 40 % peut muter vers 30 % ou 50 %
- 10 % ne peut muter que vers 20 %
- 90 % ne peut muter que vers 80 %

---

## 6. Ce que la simulation montre conceptuellement

Le script met en évidence trois phases :

### Phase A — avantage initial des égoïstes
Les plus égoïstes profitent des altruistes.  
Ils obtiennent souvent un score proche du maximum même quand il y a conflit.  [oai_citation:18‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Phase B — disparition progressive des altruistes
À force d’être exploités, les agents très altruistes deviennent moins nombreux.  [oai_citation:19‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

### Phase C — retour vers les modérés
Quand il n’y a plus assez d’altruistes à exploiter, les stratégies très égoïstes deviennent moins performantes, car elles créent trop de conflits.  
La simulation converge alors progressivement vers des stratégies plus stables, surtout le **partage égal 50/50**.  [oai_citation:20‡J_ai codé une simulation pour comprendre l_égoïsme_.txt](sediment://file_00000000b9b471fda390a82c303bcb45)

---

## 7. Comment le réimplémenter proprement

## Architecture recommandée

### `Agent`
Champs minimum :
- `id`
- `x`, `y`
- `score`
- `alive`
- `share_pref` dans `{0.1, 0.2, ..., 0.9}`
- éventuellement `home_id`
- éventuellement `partner_id`

### `Carrot`
- `x`, `y`
- `active`

### `Cow`
- `x`, `y`
- `active`

### `World`
- `width`, `height`
- liste des agents
- liste des carottes
- liste des vaches
- capacité du village
- nombre cible de vaches
- durée d’une journée
- historique des statistiques

### `Simulation`
Orchestre :
1. début de journée
2. déplacement
3. collecte des carottes
4. chasse coopérative
5. calcul des scores
6. mortalité
7. reproduction
8. mutation
9. collecte des stats
10. rendu visuel

---

## 8. Boucle logique de la simulation

Le plus simple est de modéliser la simulation par journées.

### Pseudo-code haut niveau

```python
for day in range(num_days):
    reset_daily_scores()
    spawn_or_refresh_resources()

    for step in range(day_steps):
        move_agents_randomly()
        move_cows_randomly()
        collect_carrots()

    perform_hunts()
    resolve_survival()
    reproduce_survivors()
    mutate_newborns()
    expand_village_if_needed()
    record_statistics()
    render_frame()


