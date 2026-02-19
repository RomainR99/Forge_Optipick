# Extension 4 : Zones Congestionnées - Vitesses Réduites et Contraintes de Circulation

## 📋 Vue d'ensemble

L'**Extension 4** modélise les zones congestionnées de l'entrepôt qui affectent les temps de trajet et les vitesses des agents :

- **Allées étroites** : Vitesse réduite de 50%
- **Zones encombrées** : +30 secondes par passage
- **Zones à sens unique** : Contraintes de circulation

### Contexte opérationnel

Dans un entrepôt réel, toutes les zones ne sont pas équivalentes :

- **Allées étroites** : Les robots et chariots doivent ralentir pour éviter les collisions
- **Zones encombrées** : Présence de palettes, chariots, personnel → ralentissement
- **Sens unique** : Certaines allées ne peuvent être empruntées que dans un sens

Ces contraintes affectent directement les **temps de trajet** et donc les **coûts opérationnels**.

---

## 🎯 Objectifs de l'extension

1. **Modéliser les zones congestionnées** : Identifier les zones avec pénalités de temps
2. **Tenir compte des vitesses réduites** : Modéliser les facteurs de réduction de vitesse
3. **Optimiser l'allocation** : Éviter d'assigner trop de commandes dans les zones congestionnées
4. **Intégration avec TSP** : Le calcul précis se fait lors de l'optimisation des tournées

---

## 🔧 Implémentation dans `allocation.mzn`

### 1️⃣ Nouveaux paramètres

```minizinc
% EXTENSION 4 : Zones congestionnées
array[ZONES] of float: zone_congestion_penalty;  % Pénalité de temps (secondes) par zone
array[ZONES] of float: zone_speed_factor;         % Facteur de vitesse (1.0 = normal, 0.5 = -50%)
```

**`zone_congestion_penalty[zone]`** : 
- Temps supplémentaire (en secondes) pour traverser la zone
- Exemple : Zone encombrée = +30 secondes

**`zone_speed_factor[zone]`** :
- Facteur de réduction de vitesse
- `1.0` = vitesse normale
- `0.5` = vitesse réduite de 50% (allées étroites)
- `0.7` = vitesse réduite de 30%

**Exemple** :
```minizinc
% Zones : 0=A, 1=B, 2=C, 3=D, 4=E
zone_congestion_penalty = [0.0, 30.0, 0.0, 15.0, 0.0];  % Zone B encombrée (+30s), Zone D (+15s)
zone_speed_factor = [1.0, 0.5, 1.0, 0.7, 1.0];         % Zone B allée étroite (-50%), Zone D (-30%)
```

---

### 2️⃣ Calcul du coût de congestion

```minizinc
var float: congestion_cost = sum(order_idx in ORDERS where assignment[order_idx] != 0) (
    if order_zones[order_idx] >= 0 /\ order_zones[order_idx] < n_zones then
        zone_congestion_penalty[order_zones[order_idx]]
    else
        0.0
);
```

**Logique** : Pour chaque commande assignée, ajouter la pénalité de congestion de sa zone.

**Note importante** : Ce calcul est **approximatif** car :
- Une commande peut traverser plusieurs zones (pas seulement sa zone principale)
- Le chemin exact n'est pas connu dans le modèle d'allocation
- Le calcul précis se fait au niveau Python lors de l'optimisation TSP

**Utilisation** : Ce coût sert de **pénalité douce** pour éviter d'assigner trop de commandes dans les zones congestionnées.

---

### 3️⃣ Intégration dans l'objectif

```minizinc
var float: weighted_objective = 1000.0 * num_express_assigned + num_assigned - 0.01 * congestion_cost;
solve maximize weighted_objective;
```

**Stratégie** : On soustrait le coût de congestion de l'objectif (avec un facteur 0.01).

**Pourquoi 0.01 ?**

Le facteur 0.01 permet de :
- ✅ Pénaliser les zones congestionnées
- ✅ Sans dominer l'objectif principal (maximiser les commandes assignées)
- ✅ Garder la priorité aux commandes express (coefficient 1000)

**Exemple** :
- Sans pénalité : 1000 express + 10 total = **1010 points**
- Avec pénalité (congestion = 300s) : 1000 express + 10 total - 0.01×300 = **1007 points**

La différence est faible mais suffisante pour influencer le solveur à éviter les zones congestionnées quand c'est possible.

---

## 📊 Exemples d'utilisation

### Exemple 1 : Allées étroites

**Configuration** :
- Zone B : Allée étroite (vitesse réduite de 50%)
- Zone B : Zone encombrée (+30 secondes)

**Données** :
```minizinc
zone_congestion_penalty = [0.0, 30.0, 0.0, 0.0, 0.0];  % Zone B : +30s
zone_speed_factor = [1.0, 0.5, 1.0, 1.0, 1.0];         % Zone B : -50% vitesse
```

**Effet** :
- Les commandes dans la Zone B ont une pénalité de 30 secondes
- Le solveur préférera assigner les commandes des autres zones si possible
- Si toutes les commandes sont en Zone B, elles seront quand même assignées (contrainte douce)

---

### Exemple 2 : Zones à sens unique

**Configuration** :
- Zone C : Sens unique (contrainte de circulation)
- Pénalité : +20 secondes (temps d'attente pour entrer)

**Données** :
```minizinc
zone_congestion_penalty = [0.0, 0.0, 20.0, 0.0, 0.0];  % Zone C : +20s
zone_speed_factor = [1.0, 1.0, 1.0, 1.0, 1.0];         % Vitesse normale
```

**Effet** :
- Les commandes en Zone C ont une pénalité de 20 secondes
- Le solveur préférera éviter la Zone C si possible
- La contrainte de sens unique est gérée au niveau Python lors du calcul TSP

---

### Exemple 3 : Combinaison de contraintes

**Configuration** :
- Zone B : Allée étroite (-50% vitesse) + Encombrée (+30s)
- Zone D : Zone normale mais avec pénalité légère (+15s)

**Données** :
```minizinc
zone_congestion_penalty = [0.0, 30.0, 0.0, 15.0, 0.0];
zone_speed_factor = [1.0, 0.5, 1.0, 1.0, 1.0];
```

**Commandes** :
- Commande 1 : Zone A (pas de pénalité)
- Commande 2 : Zone B (pénalité 30s)
- Commande 3 : Zone D (pénalité 15s)
- Commande 4 : Zone A (pas de pénalité)

**Optimisation** :
Le solveur préférera assigner les commandes 1 et 4 (zones sans pénalité) en priorité, puis les commandes 3 et 2 si nécessaire.

---

## 🔄 Intégration avec le calcul TSP (niveau Python)

### Calcul approximatif dans le modèle MiniZinc

Le modèle d'allocation calcule une **pénalité approximative** basée uniquement sur la zone principale de chaque commande.

### Calcul précis dans le code Python

Le calcul précis se fait lors de l'optimisation TSP :

```python
def calculate_travel_time_with_congestion(
    path: List[Location],
    agent_speed: float,
    warehouse: Warehouse,
    zone_congestion_penalty: Dict[str, float],
    zone_speed_factor: Dict[str, float]
) -> float:
    """
    Calcule le temps de trajet en tenant compte des zones congestionnées.
    """
    total_time = 0.0
    
    for i in range(len(path) - 1):
        loc1 = path[i]
        loc2 = path[i + 1]
        
        # Zone de départ et d'arrivée
        zone1 = get_product_zone(warehouse, loc1)
        zone2 = get_product_zone(warehouse, loc2)
        
        # Distance Manhattan
        distance = loc1.manhattan(loc2)
        
        # Vitesse effective (facteur de réduction)
        speed_factor = min(
            zone_speed_factor.get(zone1, 1.0),
            zone_speed_factor.get(zone2, 1.0)
        )
        effective_speed = agent_speed * speed_factor
        
        # Temps de trajet
        travel_time = distance / effective_speed if effective_speed > 0 else 0
        
        # Ajouter pénalité de congestion
        penalty1 = zone_congestion_penalty.get(zone1, 0.0)
        penalty2 = zone_congestion_penalty.get(zone2, 0.0)
        congestion_penalty = max(penalty1, penalty2)  # Prendre le maximum
        
        total_time += travel_time + congestion_penalty
    
    return total_time
```

**Points clés** :
1. **Vitesse effective** : Prendre le minimum des facteurs de vitesse des zones traversées
2. **Pénalité de congestion** : Ajouter la pénalité maximale des zones traversées
3. **Calcul par segment** : Calculer pour chaque segment du chemin

---

## 🎯 Modélisation : Graphe avec poids variables

### Concept

L'entrepôt est modélisé comme un **graphe** où :
- **Nœuds** : Emplacements des produits
- **Arêtes** : Chemins entre emplacements
- **Poids des arêtes** : Temps de trajet (variable selon les zones)

### Calcul des poids

Pour une arête entre deux emplacements `(loc1, loc2)` :

```
temps = distance / (vitesse_agent × facteur_vitesse_min) + pénalité_max
```

Où :
- `facteur_vitesse_min` = minimum des facteurs de vitesse des zones traversées
- `pénalité_max` = maximum des pénalités de congestion des zones traversées

### Exemple

**Configuration** :
- Agent : Robot (vitesse 2.0 m/s)
- Zone A → Zone B : distance 10m
- Zone A : vitesse normale (facteur 1.0), pas de pénalité
- Zone B : allée étroite (facteur 0.5), encombrée (+30s)

**Calcul** :
```
facteur_vitesse_min = min(1.0, 0.5) = 0.5
vitesse_effective = 2.0 × 0.5 = 1.0 m/s
temps_trajet = 10 / 1.0 = 10 secondes
pénalité_max = max(0, 30) = 30 secondes
temps_total = 10 + 30 = 40 secondes
```

---

## 🔍 Détails d'implémentation

### 1. Génération des paramètres (niveau Python)

```python
def generate_zone_congestion_data(warehouse: Warehouse) -> Tuple[Dict, Dict]:
    """
    Génère les données de congestion par zone.
    """
    zone_congestion_penalty = {}
    zone_speed_factor = {}
    
    for zone_name in ["A", "B", "C", "D", "E"]:
        zone_info = warehouse.zones.get(zone_name, {})
        
        # Pénalité de congestion
        if zone_info.get("narrow_aisle", False):
            zone_congestion_penalty[zone_name] = 30.0  # Allée étroite
        elif zone_info.get("congested", False):
            zone_congestion_penalty[zone_name] = 30.0  # Zone encombrée
        elif zone_info.get("one_way", False):
            zone_congestion_penalty[zone_name] = 20.0  # Sens unique
        else:
            zone_congestion_penalty[zone_name] = 0.0
        
        # Facteur de vitesse
        if zone_info.get("narrow_aisle", False):
            zone_speed_factor[zone_name] = 0.5  # -50% vitesse
        elif zone_info.get("congested", False):
            zone_speed_factor[zone_name] = 0.7  # -30% vitesse
        else:
            zone_speed_factor[zone_name] = 1.0  # Vitesse normale
    
    return zone_congestion_penalty, zone_speed_factor
```

### 2. Conversion pour MiniZinc

```python
def convert_to_minizinc_format(zone_congestion_penalty, zone_speed_factor):
    """
    Convertit les dictionnaires Python en format MiniZinc.
    Zones : 0=A, 1=B, 2=C, 3=D, 4=E
    """
    zone_map = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
    
    penalty_array = [0.0] * 5
    speed_array = [1.0] * 5
    
    for zone_name, zone_idx in zone_map.items():
        penalty_array[zone_idx] = zone_congestion_penalty.get(zone_name, 0.0)
        speed_array[zone_idx] = zone_speed_factor.get(zone_name, 1.0)
    
    return penalty_array, speed_array
```

### 3. Utilisation dans le solveur

```python
def solve_with_congestion(orders, agents, warehouse):
    """
    Résout le problème d'allocation en tenant compte des zones congestionnées.
    """
    # Générer les données de congestion
    penalty_dict, speed_dict = generate_zone_congestion_data(warehouse)
    penalty_array, speed_array = convert_to_minizinc_format(penalty_dict, speed_dict)
    
    # Résoudre avec MiniZinc
    solution = solve_minizinc(
        orders=orders,
        agents=agents,
        zone_congestion_penalty=penalty_array,
        zone_speed_factor=speed_array
    )
    
    # Optimiser les tournées avec TSP (calcul précis)
    for agent_id, assigned_orders in solution.items():
        path = optimize_tsp_with_congestion(
            assigned_orders,
            agent_id,
            warehouse,
            penalty_dict,
            speed_dict
        )
        solution[agent_id]["path"] = path
    
    return solution
```

---

## 📊 Métriques de performance

Pour évaluer l'impact des zones congestionnées :

1. **Temps total de trajet** :
   ```
   temps_total = Σ(temps_trajet_agent_i)
   ```

2. **Coût de congestion** :
   ```
   coût_congestion = Σ(pénalités_zones_traversées)
   ```

3. **Réduction de vitesse moyenne** :
   ```
   vitesse_moyenne = Σ(vitesse_effective_i) / n_agents
   ```

4. **Distribution des commandes par zone** :
   ```
   commandes_par_zone[zone] = nombre de commandes assignées dans cette zone
   ```

---

## 🎓 Cas d'usage avancés

### Cas 1 : Éviter les zones congestionnées

**Scénario** : Zone B très congestionnée, mais des commandes alternatives dans Zone A.

**Comportement** : Le solveur préférera assigner les commandes de Zone A, réduisant le coût total.

### Cas 2 : Répartition équilibrée

**Scénario** : Toutes les zones ont des pénalités similaires.

**Comportement** : Le solveur répartit équitablement les commandes entre les zones.

### Cas 3 : Zones critiques

**Scénario** : Zone B critique (allée étroite + encombrée), mais nécessaire pour certaines commandes.

**Comportement** : Le solveur assigne les commandes de Zone B uniquement si nécessaire, en minimisant leur nombre.

---

## 📝 Résumé

| Élément | Description |
|---------|-------------|
| **Paramètres** | `zone_congestion_penalty[ZONES]`, `zone_speed_factor[ZONES]` |
| **Coût** | `congestion_cost` = somme des pénalités des zones des commandes assignées |
| **Objectif** | `weighted_objective` inclut une pénalité pour les zones congestionnées |
| **Calcul précis** | Effectué au niveau Python lors de l'optimisation TSP |
| **Modélisation** | Graphe avec poids variables selon les zones |

---

## 🔗 Références

- **Modèle** : `models/allocation.mzn` (lignes 43-46, 145-151)
- **Documentation** : `docs/explication_assignment.md` (structure générale)
- **Énoncé** : `ENONCE_PROJET_OPTIPICK.txt` (section Extension 4)

---

## 💡 Notes pour l'implémentation Python

### 1. Structure de données recommandée

```python
class ZoneCongestion:
    """Représente les caractéristiques de congestion d'une zone."""
    def __init__(self, name: str):
        self.name = name
        self.narrow_aisle = False      # Allée étroite
        self.congested = False         # Zone encombrée
        self.one_way = False          # Sens unique
        self.penalty_seconds = 0.0     # Pénalité en secondes
        self.speed_factor = 1.0        # Facteur de vitesse (1.0 = normal)
```

### 2. Calcul du temps de trajet avec congestion

```python
def calculate_congested_travel_time(
    from_loc: Location,
    to_loc: Location,
    agent_speed: float,
    warehouse: Warehouse,
    zone_congestion: Dict[str, ZoneCongestion]
) -> float:
    """
    Calcule le temps de trajet en tenant compte des zones congestionnées.
    """
    zone_from = get_product_zone(warehouse, from_loc)
    zone_to = get_product_zone(warehouse, to_loc)
    
    # Facteur de vitesse (prendre le minimum)
    speed_factor = min(
        zone_congestion[zone_from].speed_factor,
        zone_congestion[zone_to].speed_factor
    )
    effective_speed = agent_speed * speed_factor
    
    # Distance et temps de base
    distance = from_loc.manhattan(to_loc)
    base_time = distance / effective_speed if effective_speed > 0 else 0
    
    # Pénalité de congestion (prendre le maximum)
    penalty = max(
        zone_congestion[zone_from].penalty_seconds,
        zone_congestion[zone_to].penalty_seconds
    )
    
    return base_time + penalty
```

### 3. Intégration avec TSP

```python
def optimize_tsp_with_congestion(
    orders: List[Order],
    agent: Agent,
    warehouse: Warehouse,
    zone_congestion: Dict[str, ZoneCongestion]
) -> List[Location]:
    """
    Optimise la tournée TSP en tenant compte des zones congestionnées.
    """
    # Construire la matrice de distances avec congestion
    locations = [warehouse.entry_point] + [loc for order in orders for loc in order.unique_locations]
    n = len(locations)
    
    distance_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                time = 0.0
            else:
                time = calculate_congested_travel_time(
                    locations[i],
                    locations[j],
                    agent.speed,
                    warehouse,
                    zone_congestion
                )
            row.append(time)
        distance_matrix.append(row)
    
    # Résoudre le TSP avec cette matrice
    tour = solve_tsp(distance_matrix)
    
    # Retourner le chemin optimisé
    return [locations[i] for i in tour]
```

---

## 🎓 Conclusion

L'Extension 4 modélise les zones congestionnées de l'entrepôt :

- ✅ **Allées étroites** : Vitesse réduite de 50%
- ✅ **Zones encombrées** : Pénalité de temps (+30s)
- ✅ **Sens unique** : Contraintes de circulation
- ✅ **Optimisation** : Le solveur évite les zones congestionnées quand possible
- ✅ **Intégration TSP** : Le calcul précis se fait lors de l'optimisation des tournées

Le système optimise l'allocation en tenant compte de ces contraintes, réduisant les temps de trajet et les coûts opérationnels.
