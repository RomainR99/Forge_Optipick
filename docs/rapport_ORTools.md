# Rapport OR-Tools — Utilisation dans OptiPick

**Projet OptiPick**

---

## Qu'est-ce qu'OR-Tools ?

**OR-Tools** (Google Optimization Tools) est une suite d'outils d'optimisation développée par Google. Elle fournit des solveurs performants pour différents types de problèmes d'optimisation.

Dans le projet OptiPick, nous utilisons **deux composants** d'OR-Tools :

1. **OR-Tools Routing** — pour résoudre le TSP (problème du voyageur de commerce)
2. **OR-Tools CP-SAT** — pour résoudre des problèmes de satisfaction de contraintes (CSP)

---

## 1. OR-Tools Routing (Jour 3)

### Fichier concerné

**`src/routing.py`**

### Utilisation

Calculer la **tournée optimale** pour chaque agent : trouver l'ordre optimal de visite des emplacements pour minimiser la distance totale.

### Code principal

```python
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve_tsp_with_ortools(locations, entry_point, time_limit_seconds=30):
    # Construire la matrice de distances
    distance_matrix = create_distance_matrix(all_locations)
    
    # Créer le gestionnaire de données pour OR-Tools
    manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)
    
    # Créer le modèle de routage
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback pour calculer la distance entre deux nœuds
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Paramètres de recherche
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    
    # Résoudre le problème
    solution = routing.SolveWithParameters(search_parameters)
    
    # Extraire la tournée optimale
    tour = [...]
    return tour, total_distance
```

### Ce que ça fait

1. **Prend** la liste des emplacements à visiter pour un agent (plus l'entrée)
2. **Calcule** la matrice de distances (Manhattan entre toutes les paires)
3. **Modélise** comme un problème TSP (voyageur de commerce)
4. **Trouve** l'ordre optimal pour minimiser la distance totale
5. **Retourne** la tournée (ordre de visite) et la distance totale

### Quand c'est utilisé

- Ligne de commande : `python main.py --routing`
- Interface web : option de routage activée (paramètre `use_routing=True`)
- Jour 3 : optimisation des tournées après allocation des commandes

### Fonction principale

**`compute_route_for_agent(agent, assigned_orders, warehouse, products_by_id)`**

- Extrait les emplacements uniques des commandes assignées à l'agent
- Résout le TSP avec `solve_tsp_with_ortools()`
- Calcule le temps total (déplacement + ramassage : 30 s par produit)
- Retourne `(route_locations, distance, time)`

---

## 2. OR-Tools CP-SAT (Jour 4)

### Fichier concerné

**`src/allocation_cpsat.py`**

### Utilisation

Allocation optimale des commandes aux agents (au lieu de l'algorithme glouton First-Fit).

### Code principal

```python
from ortools.sat.python import cp_model

def allocate_with_cpsat(orders, agents, products_by_id, warehouse, objective="cost"):
    model = cp_model.CpModel()
    
    # Variables : x[i][j] = 1 si commande i assignée à agent j (j=0 = non assigné)
    x = [[model.NewBoolVar(f"x_{i}_{j}") for j in range(n_agents + 1)]
         for i in range(n_orders)]
    
    # Contraintes : capacité poids/volume
    for j in range(n_agents):
        model.Add(sum(x[i][j+1] * orders[i].total_weight for i in range(n_orders))
                  <= agents[j].capacity_weight)
        model.Add(sum(x[i][j+1] * orders[i].total_volume for i in range(n_orders))
                  <= agents[j].capacity_volume)
    
    # Contraintes : chaque commande assignée au plus une fois
    for i in range(n_orders):
        model.Add(sum(x[i]) == 1)
    
    # Contraintes : incompatibilités
    for (i1, i2) in incompatible_pairs:
        for j in range(n_agents):
            model.Add(x[i1][j+1] + x[i2][j+1] <= 1)
    
    # Objectif : minimiser coût total ou maximiser nombre assigné
    if objective == "cost":
        model.Minimize(sum(...))  # coût total
    else:
        model.Maximize(sum(...))  # nombre assigné
    
    # Résoudre
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    status = solver.Solve(model)
    
    # Extraire l'assignment
    assignment = {}
    for i in range(n_orders):
        for j in range(n_agents):
            if solver.Value(x[i][j+1]) == 1:
                assignment[orders[i].id] = agents[j].id
                break
        else:
            assignment[orders[i].id] = None
    
    return assignment
```

### Ce que ça fait

1. **Modélise** l'allocation comme un problème CSP (satisfaction de contraintes)
2. **Variables** : `x[i][j]` = 1 si la commande `i` est assignée à l'agent `j` (j=0 = non assignée)
3. **Contraintes** :
   - Capacité poids/volume de chaque agent
   - Chaque commande assignée exactement une fois (ou non assignée)
   - Incompatibilités : deux commandes incompatibles ne peuvent pas aller au même agent
   - Restrictions : zones interdites, produits fragiles, poids max par article
4. **Objectif** : minimiser le coût total (temps × coût horaire) ou maximiser le nombre de commandes assignées
5. **Résout** avec CP-SAT pour trouver une solution optimale

### Quand c'est utilisé

- Interface web : sélectionner "MiniZinc (optimale, .mzn)" dans le menu déroulant (utilise en fait CP-SAT si disponible)
- Jour 4 : comparaison des stratégies (`python main.py --day4`)
- Alternative à MiniZinc pour l'allocation optimale

### Fonction principale

**`allocate_with_cpsat(orders, agents, products_by_id, warehouse, objective="cost")`**

- Retourne `{order_id: agent_id or None}`
- Limite de temps par défaut : 30 secondes
- Gère les erreurs : si CP-SAT n'est pas disponible, lève une exception

---

## Comparaison : OR-Tools CP-SAT vs MiniZinc

| Aspect | OR-Tools CP-SAT | MiniZinc |
|--------|------------------|----------|
| **Langage** | Python (API) | Langage de modélisation dédié |
| **Fichier** | Code Python (`src/allocation_cpsat.py`) | Fichier `.mzn` (`models/allocation.mzn`) |
| **Solveur** | CP-SAT intégré | Plusieurs solveurs (cbc, gecode, highs, etc.) |
| **Utilisation** | `allocate_with_cpsat()` | `allocate_with_minizinc()` |
| **Avantages** | Intégration Python directe, rapide | Modélisation déclarative, portable |
| **Dans le projet** | Jour 4 (allocation optimale) | Jour 2 (allocation optimale) |

### Dans OptiPick

- **Jour 2** : MiniZinc (`models/allocation.mzn`) — allocation optimale avec contraintes
- **Jour 4** : OR-Tools CP-SAT (`src/allocation_cpsat.py`) — même problème, autre solveur
- **Jour 4** : Comparaison First-Fit / MiniZinc / CP-SAT / Batching+CP-SAT

Les deux approches résolvent le même problème d'allocation, mais avec des outils différents.

---

## Installation

```bash
pip install ortools
```

Dans `requirements.txt` : `ortools>=9.8`

### Vérification de la disponibilité

Le code vérifie si OR-Tools est installé :

```python
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

try:
    from ortools.sat.python import cp_model
    CPSAT_AVAILABLE = True
except ImportError:
    CPSAT_AVAILABLE = False
```

Si OR-Tools n'est pas disponible :
- **Routing** : l'optimisation TSP n'est pas disponible (message d'avertissement)
- **CP-SAT** : l'allocation optimale n'est pas disponible (exception levée)

---

## Résumé des utilisations dans OptiPick

| Composant | Fichier | Jour | Utilisation |
|-----------|---------|------|-------------|
| **OR-Tools Routing** | `src/routing.py` | Jour 3 | Optimisation TSP des tournées pour chaque agent |
| **OR-Tools CP-SAT** | `src/allocation_cpsat.py` | Jour 4 | Allocation optimale des commandes aux agents |

### Commandes associées

- `python main.py --routing` → utilise OR-Tools Routing pour les tournées
- `python main.py --day4` → compare First-Fit, MiniZinc, CP-SAT, Batching+CP-SAT
- Interface web : menu "Allocation : MiniZinc (optimale, .mzn)" → utilise CP-SAT si disponible

---

## Documentation officielle

- **OR-Tools** : https://developers.google.com/optimization/
- **Routing** : https://developers.google.com/optimization/routing
- **CP-SAT** : https://developers.google.com/optimization/cp/cp_solver

---

*Rapport généré pour le projet OptiPick — Utilisation d'OR-Tools*
