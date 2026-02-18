# Origine de `capacity_weight` dans `allocation.mzn`

## 📋 Question

Dans le fichier `models/allocation.mzn`, ligne 11, on trouve :
```minizinc
array[AGENTS] of float: capacity_weight;
```

**D'où vient cette valeur `capacity_weight` ?**

## 🔄 Flux complet des données

### 1. Source initiale : Fichier JSON

Les valeurs `capacity_weight` sont définies dans les fichiers JSON des agents, par exemple `data/agents.json` :

```json
[
  {
    "id": "R1",
    "type": "robot",
    "capacity_weight": 20,
    "capacity_volume": 30,
    ...
  },
  {
    "id": "H1",
    "type": "human",
    "capacity_weight": 35,
    "capacity_volume": 50,
    ...
  }
]
```

### 2. Chargement dans Python : `loader.py`

Le fichier `src/loader.py` lit le JSON et crée des objets Python `Agent` :

```python
def build_agent(raw: dict) -> Agent:
    """Construit un agent à partir des données JSON."""
    return Agent(
        id=raw["id"],
        type=raw.get("type", "unknown"),
        capacity_weight=float(raw.get("capacity_weight", 0.0)),  # ← Ici
        capacity_volume=float(raw.get("capacity_volume", 0.0)),
        ...
    )
```

**Résultat** : Chaque objet `Agent` a un attribut `capacity_weight` (ex. `agent.capacity_weight = 20`)

### 3. Passage à MiniZinc : `minizinc_solver.py`

Le code Python qui appelle MiniZinc extrait les valeurs depuis les objets `Agent` et les passe au modèle :

```python
from minizinc import Instance, Model, Solver

def allocate_with_minizinc(orders, agents, products, warehouse, solver_name):
    # Charger le modèle
    model = Model("models/allocation.mzn")
    instance = Instance(solver, model)
    
    # Extraire capacity_weight de chaque agent
    capacity_weight = [agent.capacity_weight for agent in agents]
    # Exemple : [20.0, 35.0, 20.0, 35.0, 50.0, 50.0]
    
    # Passer la valeur à MiniZinc
    instance["capacity_weight"] = capacity_weight
    
    # Résoudre
    result = instance.solve()
    ...
```

### 4. Utilisation dans MiniZinc : `allocation.mzn`

MiniZinc reçoit le tableau et l'utilise dans les contraintes :

```minizinc
% Déclaration du paramètre (ligne 11)
array[AGENTS] of float: capacity_weight;

% Utilisation dans la contrainte (ligne 45-47)
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) 
        (order_weight[order_idx]) <= capacity_weight[agent_idx]
);
```

## 📊 Exemple concret

Supposons 3 agents dans `agents.json` :
- R1 : `capacity_weight = 20`
- H1 : `capacity_weight = 35`
- C1 : `capacity_weight = 50`

**Flux :**

1. **JSON** → `{"capacity_weight": 20}`, `{"capacity_weight": 35}`, `{"capacity_weight": 50}`

2. **Python (loader.py)** → `agent1.capacity_weight = 20.0`, `agent2.capacity_weight = 35.0`, `agent3.capacity_weight = 50.0`

3. **Python (minizinc_solver.py)** → `capacity_weight = [20.0, 35.0, 50.0]` puis `instance["capacity_weight"] = [20.0, 35.0, 50.0]`

4. **MiniZinc** → Reçoit `capacity_weight = [20.0, 35.0, 50.0]` et utilise :
   - `capacity_weight[1] = 20.0` (agent R1)
   - `capacity_weight[2] = 35.0` (agent H1)
   - `capacity_weight[3] = 50.0` (agent C1)

## ✅ Résumé

| Étape | Fichier | Action |
|-------|---------|--------|
| 1. Source | `data/agents.json` | Valeurs définies dans JSON |
| 2. Chargement | `src/loader.py` | Création d'objets `Agent` avec `capacity_weight` |
| 3. Extraction | `src/minizinc_solver.py` | Liste Python : `[agent.capacity_weight for agent in agents]` |
| 4. Passage | `src/minizinc_solver.py` | `instance["capacity_weight"] = [...]` |
| 5. Utilisation | `models/allocation.mzn` | Paramètre utilisé dans les contraintes |

## 🔍 Références

- **Déclaration** : `models/allocation.mzn` ligne 11
- **Utilisation** : `models/allocation.mzn` ligne 46
- **Chargement** : `src/loader.py` ligne 69
- **Documentation** : `docs/rapport_day2bis.md` lignes 320-329
