# OptiPick

**Optimisation de Tournées d'Entrepôt avec Coopération Humain-Robot et Gestion du Stockage**

## 👥 

- **Nermine**
- **Imen**
- **Hamid**
- **Romain**


## 📋 Description du Projet

OptiPick est un système d'optimisation pour la gestion d'un entrepôt de e-commerce moderne où coexistent différents types d'agents :
- **Préparateurs humains** : Expérimentés, flexibles, mais coûteux
- **Robots autonomes** : Rapides, infatigables, mais limités
- **Chariots semi-autonomes** : Guidés par humains, capacité accrue

L'objectif est d'organiser la **préparation optimale** des commandes clients en résolvant plusieurs défis :
1. Planification des tournées (séquence de produits à ramasser)
2. Allocation agents-commandes (qui fait quoi ?)
3. Respect des contraintes (capacité, incompatibilités, restrictions)
4. Optimisation du stockage
5. Coopération humain-robot

## 🏗️ Structure du Projet

```
forge/
│
├── data/
│   ├── warehouse.json      # Configuration de l'entrepôt (zones, dimensions)
│   ├── products.json        # Catalogue des produits (100 produits)
│   ├── agents.json          # Agents disponibles (robots, humains, chariots)
│   └── orders.json          # Commandes à préparer (20-30 par jour)
│
├── src/
│   ├── models.py            # Classes Warehouse, Product, Agent, Order
│   ├── loader.py            # Chargement des données JSON
│   ├── constraints.py       # Vérification des contraintes
│   ├── allocation.py        # Algorithmes d'allocation
│   ├── routing.py           # Optimisation des tournées (TSP)
│   ├── optimization.py      # Modèle CSP avec OR-Tools
│   ├── storage.py           # Optimisation du stockage
│   └── visualization.py     # Visualisation et dashboard
│
├── main_day1.py            # Point d'entrée (Jour 1)
├── ENONCE_PROJET_OPTIPICK.txt  # Énoncé complet du projet
└── README.md               # Ce fichier
```

## 🎯 Objectifs

### Objectif Principal
Minimiser le score total défini par :

```
Score = w₁ × Distance_totale
      + w₂ × Temps_total
      + w₃ × Coût_total
      + w₄ × Pénalité_déséquilibre
      + w₅ × Pénalité_retard
```

### Critères d'Optimisation
- ✅ **Distance totale parcourue** (minimiser)
- ✅ **Temps total de préparation** (minimiser)
- ✅ **Coût opérationnel** (minimiser)
- ✅ **Respect des deadlines** (100% obligatoire)
- ✅ **Équilibrage de charge** entre agents
- ✅ **Taux d'utilisation** des robots vs humains

## 🔒 Contraintes du Système

### Contraintes Dures (Obligatoires)
1. **Capacité des agents** : Poids et volume respectés
2. **Incompatibilités de produits** : Produits incompatibles ne peuvent pas être ensemble
3. **Restrictions des robots** :
   - Pas d'accès à la Zone C (réfrigérée)
   - Pas d'objets fragiles
   - Pas d'objets > 10kg individuellement
4. **Chariots nécessitent un humain** : Un chariot doit être assigné à un humain
5. **Deadlines** : Toutes les commandes doivent être préparées à temps
6. **Complétude** : Toutes les commandes doivent être préparées
7. **Pas de collision** : Deux agents ne peuvent pas occuper la même case simultanément

### Contraintes Souples (Optimisation)
- Minimiser la distance totale
- Minimiser le temps total
- Minimiser le coût
- Équilibrer la charge de travail
- Privilégier les robots (moins chers)
- Grouper les commandes compatibles
- Minimiser les allers-retours

## 📊 Modélisation

### Entrepôt
- Grille 2D avec 5 zones :
  - **Zone A** : Électronique (20 emplacements)
  - **Zone B** : Livres/Médias (15 emplacements)
  - **Zone C** : Alimentaire (10 emplacements) - Réfrigérée
  - **Zone D** : Hygiène/Chimie (10 emplacements)
  - **Zone E** : Textile (15 emplacements)
- Distance : Manhattan (`|x₁-x₂| + |y₁-y₂|`)
- Point d'entrée/sortie : (0, 0)

### Produits
Chaque produit contient :
- ID unique, nom, catégorie
- Poids (kg), volume (dm³)
- Emplacement (x, y)
- Fréquence de commande (faible/moyenne/élevée)
- Incompatibilités (liste d'autres produits)
- Fragilité (booléen)

#### Incompatibilités de Produits (`incompatible_with`)

Le champ `incompatible_with` liste les produits qui **ne peuvent pas être transportés ensemble** dans le même chariot ou par le même agent simultanément.

**Règle principale :** Si un produit A est dans la liste `incompatible_with` d'un produit B, alors A et B ne peuvent pas être dans le même chariot en même temps.

**Exemples concrets :**

1. **Produits chimiques ↔ Produits électroniques**
   - `Product_042` (Détergent industriel) est incompatible avec `Product_001` (Laptop)
   - **Raison :** Risque de dommages par contact avec des produits chimiques

2. **Produits chimiques ↔ Produits alimentaires**
   - `Product_042` (Détergent) est incompatible avec `Product_036` (Lait)
   - **Raison :** Risque de contamination et problèmes de sécurité alimentaire

3. **Produits alimentaires ↔ Produits chimiques**
   - `Product_036` (Lait) a `Product_042` dans sa liste d'incompatibilités
   - **Raison :** Sécurité alimentaire - éviter tout contact avec produits chimiques

**Utilisation dans le projet :**

Cette contrainte est utilisée lors de l'allocation des commandes aux agents :
- Si une commande contient `Product_001` et `Product_042`, ils doivent être préparés séparément ou par des agents différents
- Si un agent ramasse `Product_001`, il ne peut pas ramasser `Product_042` dans la même tournée
- C'est une **contrainte dure (obligatoire)** : elle doit être respectée à 100% pour garantir la sécurité et la qualité des produits

**Exemple de vérification :**
```python
def can_combine(products):
    """Vérifie si une liste de produits peut être transportée ensemble"""
    for i, p1 in enumerate(products):
        for p2 in products[i+1:]:
            if p2['id'] in p1.get('incompatible_with', []):
                return False  # Produits incompatibles !
    return True  # Tous compatibles
```

### Agents

| Type | Quantité | Capacité | Vitesse | Coût/h | Restrictions |
|------|----------|----------|---------|--------|--------------|
| Robot | 3 | 20kg / 30dm³ | 2.0 m/s | 5€ | Pas Zone C, pas fragile, max 10kg/item |
| Humain | 2 | 35kg / 50dm³ | 1.5 m/s | 25€ | Aucune |
| Chariot | 2 | 50kg / 80dm³ | 1.2 m/s | 3€ | Nécessite un humain |

### Commandes
Chaque commande contient :
- ID commande
- Liste de produits avec quantités
- Heure de réception
- Deadline (délai de préparation)
- Priorité (standard / express)

## 🚀 Progression par Journées

### Jour 1 : Modélisation et Allocation Simple
- Chargement des données JSON
- Création des classes (Warehouse, Product, Agent, Order)
- Calcul de distance Manhattan
- Allocation naïve (First-Fit)

### Jour 2 : Respect des Contraintes Dures
- Vérification de capacité
- Vérification d'incompatibilités
- Restrictions des robots
- Gestion des chariots
- Allocation avec contraintes

### Jour 3 : Optimisation des Tournées (TSP)
- Modélisation TSP pour chaque agent
- Résolution avec heuristique (Nearest Neighbor, 2-opt, ou OR-Tools)
- Calcul du temps de tournée
- Vérification des deadlines

### Jour 4 : Allocation Optimale et Regroupement
- Modélisation CSP avec OR-Tools CP-SAT
- Optimisation globale de l'allocation
- Regroupement de commandes compatibles (batching)
- Comparaison des stratégies

### Jour 5 : Optimisation du Stockage et Analyse Avancée
- Analyse des patterns de commandes
- Réorganisation de l'entrepôt (produits fréquents près de l'entrée)
- Simulation avant/après réorganisation
- Analyse de coopération humain-robot
- Dashboard de monitoring

## 🛠️ Technologies Utilisées

### Installation de l'Environnement Virtuel

**Méthode 1 : Script automatique (recommandé)**
```bash
cd optipick
./setup_venv.sh
```

**Méthode 2 : Installation manuelle**
```bash
cd optipick

# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # Sur macOS/Linux
# ou
venv\Scripts\activate     # Sur Windows

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
pip install minizinc
```

**Activer l'environnement virtuel :**
```bash
source venv/bin/activate  # macOS/Linux
```

**Désactiver l'environnement virtuel :**
```bash
deactivate
```

### Bibliothèques Python

Le fichier `requirements.txt` contient toutes les dépendances nécessaires :

- **OR-Tools** (>=9.8) : Optimisation (CP-SAT, Routing)
- **NumPy** (>=1.24.0) : Calculs numériques
- **Pandas** (>=2.0.0) : Traitement de données
- **Matplotlib** (>=3.7.0) : Visualisation
- **Seaborn** (>=0.12.0) : Visualisation statistique
- **NetworkX** (>=3.1) : Manipulation de graphes
- **MiniZinc** (>=0.6.0) : Modélisation par contraintes

## 📁 Fichiers de Données

### warehouse.json
Configuration de l'entrepôt : dimensions, zones avec coordonnées, point d'entrée.

### products.json
Catalogue de 100 produits avec leurs caractéristiques (poids, volume, emplacement, incompatibilités).

### agents.json
Liste des agents disponibles avec leurs capacités, vitesses, coûts et restrictions.

Le fichier contient **7 agents** répartis en 3 types :

#### Structure des Agents

Chaque agent possède les champs suivants :
- `id` : Identifiant unique (R1, R2, R3, H1, H2, C1, C2)
- `type` : Type d'agent (`robot`, `human`, `cart`)
- `capacity_weight` : Capacité maximale en poids (kg)
- `capacity_volume` : Capacité maximale en volume (dm³)
- `speed` : Vitesse de déplacement (m/s)
- `cost_per_hour` : Coût d'utilisation par heure (€)
- `restrictions` : Objet contenant les restrictions spécifiques

#### Types d'Agents

**1. Robots (3 agents : R1, R2, R3)**
- **Capacité** : 20kg / 30dm³
- **Vitesse** : 2.0 m/s
- **Coût** : 5€/h (électricité + amortissement)
- **Restrictions** :
  - `no_zones: ["C"]` : Ne peut pas accéder à la Zone C (réfrigérée)
  - `no_fragile: true` : Ne peut pas transporter d'objets fragiles
  - `max_item_weight: 10` : Ne peut pas transporter d'objets > 10kg individuellement

**2. Humains (2 agents : H1, H2)**
- **Capacité** : 35kg / 50dm³
- **Vitesse** : 1.5 m/s
- **Coût** : 25€/h (salaire)
- **Restrictions** : `{}` (aucune restriction - peut tout faire)

**3. Chariots (2 agents : C1, C2)**
- **Capacité** : 50kg / 80dm³
- **Vitesse** : 1.2 m/s
- **Coût** : 3€/h (quand utilisé avec humain)
- **Restrictions** :
  - `requires_human: true` : Nécessite un humain assigné (H1 ou H2)
  - Un humain ne peut guider qu'un seul chariot à la fois

#### Exemple de Structure

```json
{
  "id": "R1",
  "type": "robot",
  "capacity_weight": 20,
  "capacity_volume": 30,
  "speed": 2.0,
  "cost_per_hour": 5,
  "restrictions": {
    "no_zones": ["C"],
    "no_fragile": true,
    "max_item_weight": 10
  }
}
```

#### Notes Importantes

- Les **robots** sont les moins chers mais ont des restrictions importantes
- Les **humains** sont les plus flexibles mais les plus coûteux
- Les **chariots** augmentent la capacité mais nécessitent un humain dédié
- L'optimisation doit équilibrer l'utilisation des robots (moins chers) avec les contraintes des commandes

### orders.json
Commandes à préparer avec produits, quantités, deadlines et priorités.

## 🧪 Utilisation

### Exécution du Programme
```bash
python main_day1.py
```

### Structure du Code
- **models.py** : Classes de base pour modéliser le problème
- **loader.py** : Chargement et parsing des fichiers JSON
- **constraints.py** : Vérification de toutes les contraintes
- **allocation.py** : Algorithmes d'allocation (glouton, optimisé)
- **routing.py** : Optimisation des tournées (TSP)
- **optimization.py** : Modèle CSP avec OR-Tools
- **visualization.py** : Visualisation des résultats

#### Algorithmes Principaux (Jour 1)

**1. Allocation Naïve First-Fit**

L'allocation First-Fit est une stratégie simple qui assigne chaque commande au premier agent ayant la capacité suffisante.

**Emplacement dans le code :** `main.py` - Section 3 (lignes 141-171)

**Fonctionnement :**
```python
def allocate_first_fit(orders: List[Order], agents: List[Agent]) -> Dict[str, Optional[str]]:
    assignment: Dict[str, Optional[str]] = {}
    
    for order in orders:  # ← Pour chaque commande (par ordre d'arrivée)
        assigned = False
        for agent in agents:  # ← Parcourt les agents dans l'ordre
            if agent.can_take(order):  # ← Vérifie la capacité suffisante
                agent.assign(order)
                assignment[order.id] = agent.id
                assigned = True
                break  # ← S'arrête au premier agent qui peut prendre la commande
        if not assigned:
            assignment[order.id] = None  # ← Aucun agent disponible
    
    return assignment
```

**Étapes de l'algorithme :**
1. **Tri des commandes** : Les commandes sont triées par heure de réception (`sort_orders_by_received_time`)
2. **Parcours séquentiel** : Pour chaque commande, dans l'ordre chronologique
3. **Recherche du premier agent disponible** : Parcourt les agents dans l'ordre jusqu'à trouver un agent avec capacité suffisante
4. **Assignation** : Assigne la commande au premier agent trouvé
5. **Gestion des non-assignées** : Si aucun agent ne peut prendre la commande, elle reste non assignée

**Caractéristiques :**
- ✅ **Simple et rapide** : Complexité O(n × m) où n = nombre de commandes, m = nombre d'agents
- ✅ **Déterministe** : Même résultat pour les mêmes données
- ⚠️ **Non optimale** : Ne cherche pas la meilleure allocation globale
- ⚠️ **Ignore les restrictions** : Pour l'instant, ne vérifie que la capacité (poids/volume)

**Note :** Cette version ignore les restrictions (robots, incompatibilités, etc.) pour l'instant. Ces vérifications seront ajoutées au Jour 2.

**2. Calcul de Distance Totale (Estimation)**

Le calcul de distance totale est une **estimation simple** qui additionne les distances entre l'entrée et chaque emplacement unique de chaque commande.

**Emplacement dans le code :** `main.py` - Section 4 (lignes 174-188)

**Fonctionnement :**
```python
def estimate_order_distance(warehouse: Warehouse, order: Order) -> int:
    """
    Estimation simple: somme des distances entrée <-> emplacement.
    (Pas de tournée optimisée, juste un proxy).
    """
    entry = warehouse.entry_point
    return sum(entry.manhattan(loc) for loc in order.unique_locations)

def compute_total_distance(warehouse: Warehouse, orders: List[Order]) -> int:
    return sum(estimate_order_distance(warehouse, o) for o in orders)
```

**Méthode de calcul :**
- **Distance Manhattan** : `|x₁-x₂| + |y₁-y₂|` (distance en L, pas en ligne droite)
- **Pour chaque commande** : Additionne les distances entre l'entrée (0,0) et chaque emplacement unique
- **Distance totale** : Somme des distances de toutes les commandes

**Exemple :**
```
Commande avec produits aux emplacements : (3,2), (5,1), (3,2)
Emplacements uniques : (3,2), (5,1)
Distance entrée → (3,2) : |0-3| + |0-2| = 5
Distance entrée → (5,1) : |0-5| + |0-1| = 6
Distance totale pour cette commande : 5 + 6 = 11
```

---

## 📅 Jour 2 : Respect des Contraintes Dures

### Objectifs du Jour 2

Le Jour 2 se concentre sur l'intégration de **toutes les contraintes obligatoires** dans le système d'allocation. L'objectif est de garantir que chaque allocation respecte toutes les règles métier définies.

### Contraintes Implémentées

#### 2.1) Vérification de Capacité

Pour chaque agent, vérification que :
- **Poids total** ≤ capacité en poids
- **Volume total** ≤ capacité en volume

Cette vérification était déjà présente dans le Jour 1 via la méthode `Agent.can_take()`, mais elle est maintenant intégrée dans le système complet de vérification des contraintes.

#### 2.2) Vérification d'Incompatibilités

**Fonction : `can_combine(products)`**

Vérifie qu'aucun produit dans une commande n'est incompatible avec un autre produit de la même commande.

**Implémentation :**

```python
def can_combine(products: List[Product]) -> bool:
    """
    Vérifie qu'aucun produit n'est incompatible avec un autre dans la liste.
    Retourne False si deux produits incompatibles sont présents.
    """
    product_ids = {p.id for p in products}
    
    for product in products:
        # Vérifier si ce produit est incompatible avec un autre produit de la liste
        for incompatible_id in product.incompatible_with:
            if incompatible_id in product_ids:
                return False
    
    return True
```

**Exemple :**
- Si `Product_001` a `incompatible_with: ["Product_042"]`
- Et qu'une commande contient à la fois `Product_001` et `Product_042`
- Alors `can_combine()` retourne `False` et la commande ne peut pas être assignée

#### 2.3) Restrictions des Robots

Les robots ont des restrictions spécifiques qui doivent être vérifiées :

**a) Zones interdites (`no_zones`)**
- Les robots ne peuvent pas accéder à certaines zones de l'entrepôt
- Exemple : Robot R1 ne peut pas aller en Zone C (alimentaire)

**b) Objets fragiles (`no_fragile`)**
- Les robots ne peuvent pas transporter d'objets fragiles
- Vérification du champ `fragile: true` dans les produits

**c) Poids maximum par item (`max_item_weight`)**
- Chaque robot a une limite de poids par item individuel
- Exemple : Robot R1 ne peut pas prendre d'item > 10 kg

**Implémentation :**

```python
def check_robot_restrictions(
    agent: Agent,
    order: Order,
    products_by_id: Dict[str, Product],
    warehouse: Warehouse,
    restrictions: Dict
) -> bool:
    """
    Vérifie toutes les restrictions spécifiques aux robots.
    """
    if agent.type != "robot":
        return True  # Les restrictions ne s'appliquent qu'aux robots
    
    # Vérifier les zones interdites
    no_zones = restrictions.get("no_zones", [])
    if no_zones:
        for location in order.unique_locations:
            zone = get_product_zone(warehouse, location)
            if zone in no_zones:
                return False
    
    # Vérifier les objets fragiles
    if restrictions.get("no_fragile", False):
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product and product.fragile:
                return False
    
    # Vérifier le poids maximum par item
    max_item_weight = restrictions.get("max_item_weight")
    if max_item_weight is not None:
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product and product.weight > max_item_weight:
                return False
    
    return True
```

#### 2.4) Gestion des Chariots

**Association chariot ↔ humain**

Les chariots nécessitent qu'un humain soit disponible pour les gérer. Un humain peut gérer un chariot, mais doit avoir la capacité suffisante pour la commande.

**Implémentation :**

```python
def check_cart_human_association(
    agent: Agent,
    order: Order,
    agents: List[Agent],
    assignment: Dict[str, Optional[str]]
) -> bool:
    """
    Vérifie qu'un chariot peut être assigné à une commande.
    Un chariot nécessite qu'un humain soit disponible pour le gérer.
    """
    if agent.type != "cart":
        return True  # Cette vérification ne s'applique qu'aux chariots
    
    # Trouver tous les humains disponibles
    humans = [a for a in agents if a.type == "human"]
    
    # Vérifier qu'il existe au moins un humain disponible avec capacité suffisante
    if not humans:
        return False
    
    for human in humans:
        if human.can_take(order):
            return True
    
    return False
```

#### 2.5) Allocation avec Contraintes

**Algorithme glouton amélioré :**

L'allocation du Jour 1 a été modifiée pour intégrer toutes les contraintes :

```python
def allocate_first_fit(
    orders: List[Order],
    agents: List[Agent],
    products_by_id: Dict[str, Product],
    warehouse: Warehouse
) -> Dict[str, Optional[str]]:
    """
    JOUR 2 : Allocation avec toutes les contraintes dures.
    Algorithme glouton amélioré :
    - Pour chaque commande (par ordre d'arrivée)
    - Tester chaque agent dans l'ordre (robots d'abord)
    - Vérifier toutes les contraintes
    - Assigner au premier agent valide
    """
    assignment: Dict[str, Optional[str]] = {}
    agents_sorted = sort_agents_by_priority(agents)  # Robots en premier

    for order in orders:
        assigned = False
        for agent in agents_sorted:
            # Vérifier toutes les contraintes (Jour 2)
            if can_agent_take_order_with_constraints(
                agent=agent,
                order=order,
                products_by_id=products_by_id,
                warehouse=warehouse,
                restrictions=agent.restrictions,
                agents=agents,
                assignment=assignment
            ):
                agent.assign(order)
                assignment[order.id] = agent.id
                assigned = True
                break
        if not assigned:
            assignment[order.id] = None  # Aucun agent disponible respectant les contraintes

    return assignment
```

**Priorité des agents :**
1. **Robots** (priorité 0) : Testés en premier car moins coûteux
2. **Humains** (priorité 1) : Testés ensuite
3. **Chariots** (priorité 2) : Testés en dernier car nécessitent un humain

### Module `src/constraints.py`

Le module `constraints.py` centralise toutes les fonctions de vérification des contraintes :

- `get_product_zone()` : Détermine la zone d'un produit
- `can_combine()` : Vérifie les incompatibilités entre produits
- `check_robot_restrictions()` : Vérifie les restrictions spécifiques aux robots
- `check_cart_human_association()` : Vérifie l'association chariot-humain
- `can_agent_take_order_with_constraints()` : Fonction principale qui combine toutes les vérifications

### Tests Unitaires

Des tests unitaires complets ont été créés dans `tests/test_constraints.py` pour vérifier :

- ✅ Détermination des zones
- ✅ Vérification des incompatibilités
- ✅ Restrictions de zones pour les robots
- ✅ Restrictions sur les objets fragiles
- ✅ Restrictions de poids maximum
- ✅ Association chariot-humain
- ✅ Vérification complète de toutes les contraintes

**Exécution des tests :**

```bash
python tests/test_constraints.py
```

### Modifications du Modèle Agent

Le modèle `Agent` a été enrichi pour stocker les restrictions :

```python
@dataclass
class Agent:
    # ... autres champs ...
    restrictions: Dict = field(default_factory=dict)  # Restrictions spécifiques (Jour 2)
```

Les restrictions sont chargées depuis `agents.json` dans `loader.py` :

```python
def build_agent(raw: dict) -> Agent:
    base_kwargs = dict(
        # ... autres champs ...
        restrictions=dict(raw.get("restrictions", {})),  # Charger les restrictions
    )
    # ...
```

### Résultats du Jour 2

Le système affiche maintenant :

```
══════════════════════════════════════
JOUR 2 — Allocation avec contraintes
══════════════════════════════════════
Commandes totales : 30
Commandes assignées: X
Commandes non assignées: Y
Distance totale estimée (proxy): Z
```

Les commandes non assignées indiquent maintenant les cas où **aucune contrainte n'a pu être respectée**, pas seulement les problèmes de capacité.

---

## 🔧 Intégration de MiniZinc (Jour 2+)

### Utilisation de MiniZinc pour l'Allocation Optimale

Le projet intègre maintenant **MiniZinc**, un langage de modélisation par contraintes, pour résoudre le problème d'allocation de manière optimale.

#### Installation

MiniZinc doit être installé séparément :

1. **Installer MiniZinc** : Téléchargez depuis https://www.minizinc.org/
2. **Installer la bibliothèque Python** : `pip install minizinc`

#### Modèle MiniZinc (`models/allocation.mzn`)

Le modèle MiniZinc définit le problème d'allocation comme un problème de satisfaction de contraintes :

**Variables de décision :**
- `assignment[o]` : Agent assigné à la commande `o` (0 = non assignée)

**Contraintes modélisées :**
1. Capacité en poids et volume
2. Zones interdites pour les robots
3. Interdiction des objets fragiles pour les robots
4. Limite de poids par item pour les robots
5. Incompatibilités entre produits

**Objectif :** Maximiser le nombre de commandes assignées

#### Module `src/minizinc_solver.py`

Le module `minizinc_solver.py` fournit la fonction `allocate_with_minizinc()` qui :

1. Charge le modèle MiniZinc
2. Prépare les données (capacités, restrictions, incompatibilités)
3. Résout le problème avec un solveur MiniZinc (Gecode, Chuffed, etc.)
4. Retourne l'allocation optimale

**Exemple d'utilisation :**

```python
from src.minizinc_solver import allocate_with_minizinc

assignment = allocate_with_minizinc(
    orders=orders,
    agents=agents,
    products_by_id=products_by_id,
    warehouse=warehouse,
    solver_name="gecode"  # ou "chuffed", etc.
)
```

#### Utilisation dans `main.py`

Le programme principal peut utiliser MiniZinc via l'option `--minizinc` :

```bash
# Utiliser l'algorithme glouton (par défaut)
python main.py

# Utiliser MiniZinc pour l'allocation optimale
python main.py --minizinc

# Spécifier un solveur MiniZinc particulier
python main.py --minizinc --solver chuffed
```

#### Avantages de MiniZinc

- ✅ **Optimisation globale** : Trouve la meilleure solution possible (maximise le nombre de commandes assignées)
- ✅ **Garantie de respect des contraintes** : Toutes les contraintes sont vérifiées simultanément
- ✅ **Flexibilité** : Facile d'ajouter de nouvelles contraintes au modèle
- ✅ **Comparaison de solveurs** : Possibilité de tester différents solveurs (Gecode, Chuffed, etc.)

#### Limitations

- ⚠️ **Temps de résolution** : Peut être plus lent que l'algorithme glouton pour de grandes instances
- ⚠️ **Dépendance externe** : Nécessite l'installation de MiniZinc
- ⚠️ **Gestion des chariots** : Simplifiée dans le modèle (vérifiée après résolution)

#### Comparaison Glouton vs MiniZinc

| Critère | Algorithme Glouton | MiniZinc |
|---------|-------------------|----------|
| Vitesse | ⚡ Rapide | 🐢 Plus lent |
| Optimalité | ❌ Sous-optimal | ✅ Optimal |
| Contraintes | ✅ Toutes vérifiées | ✅ Toutes vérifiées |
| Complexité | Simple | Modélisation requise |

**Limitations (Jour 1) :**
- ⚠️ **Pas d'optimisation de tournée** : Ne calcule pas le chemin optimal entre les emplacements
- ⚠️ **Pas de retour à l'entrée** : Ne compte pas le retour à l'entrée après la dernière collecte
- ⚠️ **Estimation** : C'est une approximation, pas la vraie distance parcourue

**Amélioration prévue (Jour 3) :**
- Optimisation TSP (Traveling Salesman Problem) pour calculer le chemin optimal
- Prise en compte du retour à l'entrée
- Calcul de la distance réelle parcourue par chaque agent

**3. Évaluation et Affichage des Résultats**

La fonction d'évaluation calcule et affiche les métriques de performance du système.

**Emplacement dans le code :** `main.py` - Section 5 (lignes 195-230)

**Fonction principale :** `print_report()`

**Métriques calculées et affichées :**

**1. Nombre de commandes assignées (lignes 200-202) :**
```python
total = len(orders)  # Nombre total de commandes
assigned = sum(1 for oid, aid in assignment.items() if aid is not None)  # Commandes assignées
unassigned = total - assigned  # Commandes non assignées
```
- Affiche le nombre total de commandes
- Affiche le nombre de commandes assignées avec succès
- Affiche le nombre de commandes non assignées (capacité insuffisante)

**2. Distance totale estimée (ligne 204) :**
```python
dist_total = compute_total_distance(warehouse, orders)
```
- Calcule la distance totale estimée en utilisant la fonction de la section 4
- Affiche le résultat comme "Distance totale estimée (proxy)"

**3. Utilisation de chaque agent (lignes 215-222) :**
```python
print("Détail par agent:")
for a in agents:
    util_w = (a.used_weight / a.capacity_weight) * 100  # % utilisation poids
    util_v = (a.used_volume / a.capacity_volume) * 100   # % utilisation volume
    print(f"- {a.id} ({a.type})")
    print(f"  commandes: {len(a.assigned_orders)} -> {a.assigned_orders}")
    print(f"  poids: {a.used_weight:.2f}/{a.capacity_weight:.2f} kg ({util_w:.1f}%)")
    print(f"  volume: {a.used_volume:.2f}/{a.capacity_volume:.2f} dm³ ({util_v:.1f}%)")
```

**Pour chaque agent, affiche :**
- **ID et type** : Identifiant et type d'agent (robot, human, cart)
- **Commandes assignées** : Nombre et liste des IDs des commandes assignées
- **Utilisation du poids** : Poids utilisé / capacité totale (en kg et pourcentage)
- **Utilisation du volume** : Volume utilisé / capacité totale (en dm³ et pourcentage)

**4. Liste des commandes non assignées (lignes 225-230) :**
```python
if unassigned > 0:
    print("Commandes non assignées (capacité insuffisante avec ce First-Fit):")
    for oid, aid in assignment.items():
        if aid is None:
            print(f"- {oid}")
```
- Affiche la liste des commandes qui n'ont pas pu être assignées
- Utile pour identifier les problèmes de capacité

**Exemple de sortie :**
```
══════════════════════════════════════
JOUR 1 — Allocation naïve (First-Fit)
══════════════════════════════════════
Commandes totales : 30
Commandes assignées: 28
Commandes non assignées: 2
Distance totale estimée (proxy): 245

Détail par agent:
- R1 (robot)
  commandes: 5 -> ['Order_001', 'Order_003', 'Order_007', 'Order_012', 'Order_015']
  poids: 18.50/20.00 kg (92.5%)
  volume: 25.30/30.00 dm³ (84.3%)
- H1 (human)
  commandes: 8 -> ['Order_002', 'Order_004', ...]
  poids: 32.10/35.00 kg (91.7%)
  volume: 45.20/50.00 dm³ (90.4%)
...
```

**Utilisation :**
La fonction `print_report()` est appelée à la fin de `main()` (ligne 259) pour afficher le rapport complet après l'allocation.

#### Modèles et Dataclasses

Le projet utilise les **dataclasses Python** pour modéliser les entités (Warehouse, Product, Agent, Order, Location).

**`@dataclass` - Décorateur Python :**

Le décorateur `@dataclass` (introduit dans Python 3.7) simplifie la création de classes qui servent principalement à stocker des données. Il génère automatiquement des méthodes spéciales basées sur les annotations de type.

**Sans `@dataclass` (code verbeux) :**
```python
class Location:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Location(x={self.x}, y={self.y})"
    
    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        return self.x == other.x and self.y == other.y
```

**Avec `@dataclass` (code concis) :**
```python
@dataclass
class Location:
    x: int
    y: int
```

**Méthodes générées automatiquement par `@dataclass` :**
1. **`__init__()`** : Constructeur avec tous les champs
2. **`__repr__()`** : Représentation lisible de l'objet
3. **`__eq__()`** : Comparaison d'égalité basée sur les valeurs des champs
4. **`__hash__()`** : Si `frozen=True`, permet d'utiliser l'objet comme clé

**Avantages de `@dataclass` :**
- ✅ **Moins de code** : Évite d'écrire manuellement `__init__`, `__repr__`, `__eq__`
- ✅ **Type hints** : Encourage l'utilisation d'annotations de type
- ✅ **Lisibilité** : Code plus clair et maintenable
- ✅ **Valeurs par défaut** : Support facile des valeurs par défaut avec `field()`
- ✅ **Ordre des champs** : Respecte l'ordre de déclaration

**Exemple complet dans le projet :**
```python
@dataclass
class Product:
    id: str
    name: str
    category: str
    weight: float
    volume: float
    location: Location
    frequency: str = "unknown"  # Valeur par défaut
    fragile: bool = False
    incompatible_with: List[str] = field(default_factory=list)  # Liste vide par défaut
```

**`frozen=True` dans les dataclasses :**

Le paramètre `frozen=True` rend les instances de la classe **immuables** (non modifiables) après leur création.

**Exemple :**
```python
@dataclass(frozen=True)
class Location:
    x: int
    y: int
    
    def manhattan(self, other: "Location") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)
```

**Avantages de `frozen=True` :**
1. **Sécurité** : Empêche les modifications accidentelles des coordonnées
2. **Hashable** : Les objets peuvent être utilisés comme clés dans des dictionnaires ou dans des sets
3. **Thread-safe** : Pas de risque de modification concurrente
4. **Sémantique claire** : Indique que l'objet représente une valeur fixe

**Dans le projet OptiPick :**
- `Location` est `frozen=True` car les coordonnées ne doivent jamais changer après création
- Les autres classes (`Warehouse`, `Product`, `Agent`, `Order`) ne sont pas frozen car elles peuvent être modifiées (ex: `Agent.used_weight`, `Order.total_weight`)

**Exemple d'utilisation :**
```python
# Création d'une location
loc1 = Location(x=5, y=3)

# ✅ Utilisation normale
loc2 = Location(x=7, y=2)
distance = loc1.manhattan(loc2)  # Calcule la distance

# ✅ Utilisation comme clé dans un dictionnaire (grâce à frozen=True)
locations_dict = {loc1: "Zone A", loc2: "Zone B"}

# ❌ Modification impossible (erreur)
# loc1.x = 10  # Raises FrozenInstanceError
```

**Méthode `manhattan()` - Distance de Manhattan :**

La classe `Location` possède une méthode `manhattan()` pour calculer la distance entre deux emplacements.

```python
def manhattan(self, other: "Location") -> int:
    return abs(self.x - other.x) + abs(self.y - other.y)
```

**Rôle :** Calcule la distance de Manhattan entre deux emplacements dans la grille de l'entrepôt.

**Formule :** Distance = `|x₁ - x₂| + |y₁ - y₂|`

Où :
- `self.x` et `self.y` : Coordonnées du premier point
- `other.x` et `other.y` : Coordonnées du second point
- `abs()` : Fonction valeur absolue

**Pourquoi "Manhattan" ?**

Nommée ainsi car elle correspond aux déplacements dans un quadrillage (comme les rues de Manhattan) : on ne peut se déplacer qu'horizontalement ou verticalement, pas en diagonale.

**Exemple visuel :**

```
    0   1   2   3   4
  ┌───┬───┬───┬───┬───┐
0 │   │   │   │   │   │
  ├───┼───┼───┼───┼───┤
1 │ A │   │   │   │   │  A = (1, 1)
  ├───┼───┼───┼───┼───┤
2 │   │   │   │   │   │
  ├───┼───┼───┼───┼───┤
3 │   │   │   │ B │   │  B = (3, 3)
  └───┴───┴───┴───┴───┘

Distance A → B :
|1-3| + |1-3| = 2 + 2 = 4 cases
```

**Exemple de code :**

```python
# Création de deux emplacements
loc1 = Location(x=1, y=1)  # Zone A
loc2 = Location(x=3, y=3)   # Zone B

# Calcul de la distance
distance = loc1.manhattan(loc2)
# distance = |1-3| + |1-3| = 2 + 2 = 4
```

**Pourquoi cette distance dans le projet ?**

- ✅ **Modélise correctement** les déplacements dans une grille (pas de diagonale)
- ✅ **Plus simple** que la distance euclidienne
- ✅ **Correspond aux contraintes réelles** d'un entrepôt (allées horizontales/verticales)

**Comparaison avec d'autres distances :**

**Distance euclidienne** (ligne droite) :
```
√((x₁-x₂)² + (y₁-y₂)²) = √(2² + 2²) = √8 ≈ 2.83
```

**Distance de Manhattan** (en L) :
```
|x₁-x₂| + |y₁-y₂| = 2 + 2 = 4
```

Dans un entrepôt, la distance de Manhattan est plus réaliste car les agents suivent les allées.

**Utilisation dans le projet :**

Cette méthode est utilisée pour :
- Calculer la distance entre l'entrée et un emplacement de produit
- Estimer la distance totale d'une tournée
- Optimiser les parcours (Jour 3 : TSP)

**Exemple dans le code :**
```python
entry = warehouse.entry_point  # Location(0, 0)
product_loc = Location(5, 3)

distance = entry.manhattan(product_loc)
# distance = |0-5| + |0-3| = 5 + 3 = 8 cases
```

#### Classe Agent - Détails

La classe `Agent` est au cœur du système d'allocation. Elle représente un agent (robot, humain ou chariot) et gère son état de chargement.

**Structure de la classe :**

```python
@dataclass
class Agent:
    id: str                    # Identifiant unique (ex: "R1", "H1", "C1")
    type: str                 # Type d'agent : "robot", "human" ou "cart"
    capacity_weight: float    # Capacité maximale en poids (kg)
    capacity_volume: float   # Capacité maximale en volume (dm³)
    speed: float             # Vitesse de déplacement (m/s)
    cost_per_hour: float     # Coût d'utilisation par heure (€)
    
    # Attributs d'affectation (mis à jour dynamiquement)
    assigned_orders: List[str] = field(default_factory=list)
    used_weight: float = 0.0
    used_volume: float = 0.0
```

**Attributs d'affectation :**

- **`assigned_orders`** : Liste des IDs des commandes assignées à cet agent
  - `field(default_factory=list)` : Initialise une nouvelle liste vide pour chaque instance
  - Permet de suivre quelles commandes sont assignées à quel agent
  
- **`used_weight`** : Poids total actuellement transporté (en kg)
  - Commence à 0.0 et augmente à chaque assignation
  
- **`used_volume`** : Volume total actuellement transporté (en dm³)
  - Commence à 0.0 et augmente à chaque assignation

**Méthode `can_take()` :**

```python
def can_take(self, order: Order) -> bool:
    return (
        self.used_weight + order.total_weight <= self.capacity_weight
        and self.used_volume + order.total_volume <= self.capacity_volume
    )
```

**Rôle :** Vérifie si l'agent peut prendre une commande supplémentaire.

**Vérifications :**
- **Condition poids** : `used_weight + order.total_weight <= capacity_weight`
- **Condition volume** : `used_volume + order.total_volume <= capacity_volume`
- Retourne `True` seulement si **les deux conditions** sont respectées

**Exemple :**
```python
robot = Agent(id="R1", capacity_weight=20, capacity_volume=30, ...)
robot.used_weight = 15.0  # Déjà 15kg chargés
order = Order(total_weight=8.0, total_volume=10.0, ...)

robot.can_take(order)  # False car 15 + 8 = 23 > 20 (capacité dépassée)
```

**Méthode `assign()` :**

```python
def assign(self, order: Order) -> None:
    self.assigned_orders.append(order.id)
    self.used_weight += order.total_weight
    self.used_volume += order.total_volume
```

**Rôle :** Assigne une commande à l'agent et met à jour les compteurs.

**Actions :**
1. Ajoute l'ID de la commande à `assigned_orders`
2. Ajoute le poids de la commande à `used_weight`
3. Ajoute le volume de la commande à `used_volume`

**Exemple :**
```python
robot = Agent(id="R1", capacity_weight=20, capacity_volume=30, ...)
order = Order(id="Order_001", total_weight=5.0, total_volume=8.0, ...)

robot.assign(order)
# Maintenant :
# robot.assigned_orders = ["Order_001"]
# robot.used_weight = 5.0
# robot.used_volume = 8.0
```

**Utilisation dans l'algorithme First-Fit :**

```python
for order in orders:
    for agent in agents:
        if agent.can_take(order):  # ← Vérifie la capacité
            agent.assign(order)    # ← Assigne et met à jour les compteurs
            break
```

#### Module loader.py - Détails

Le module `loader.py` est responsable du chargement et de la conversion des fichiers JSON en objets Python typés.

**Vue d'ensemble :**

Ce module transforme les données JSON brutes en objets Python utilisables par le reste du programme. Il sépare le chargement des données de la logique métier.

**Fonction 1 : `load_json()`**

```python
def load_json(path: Path) -> dict | list:
    """Charge un fichier JSON et retourne son contenu."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
```

**Rôle :** Fonction générique qui charge n'importe quel fichier JSON.

- **Paramètre** : `path` (chemin du fichier)
- **Retourne** : Contenu JSON (dictionnaire ou liste)
- **Utilisation** : Fonction de base utilisée par toutes les autres fonctions de parsing

**Fonction 2 : `parse_warehouse()`**

```python
def parse_warehouse(data: dict) -> Warehouse:
    width = data["dimensions"]["width"]
    height = data["dimensions"]["height"]
    
    zones: Dict[str, List[Location]] = {}
    for zname, zinfo in data.get("zones", {}).items():
        coords = zinfo.get("coords", [])
        zones[zname] = [Location(x=c[0], y=c[1]) for c in coords]
    
    entry = data.get("entry_point", [0, 0])
    entry_point = Location(x=entry[0], y=entry[1])
    
    return Warehouse(width=width, height=height, zones=zones, entry_point=entry_point)
```

**Rôle :** Convertit les données JSON de l'entrepôt en objet `Warehouse`.

**Étapes :**
1. Extraction des dimensions (largeur et hauteur)
2. Parsing des zones : convertit chaque coordonnée `[x, y]` en objet `Location`
3. Point d'entrée : crée un `Location` pour l'entrée (par défaut [0, 0])
4. Création de l'objet `Warehouse` avec toutes les données

**Fonction 3 : `parse_products()`**

```python
def parse_products(data: list) -> Dict[str, Product]:
    products: Dict[str, Product] = {}
    for p in data:
        pid = p["id"]
        loc = p.get("location", [0, 0])
        products[pid] = Product(
            id=pid,
            name=p.get("name", pid),
            category=p.get("category", "unknown"),
            weight=float(p.get("weight", 0.0)),
            volume=float(p.get("volume", 0.0)),
            location=Location(loc[0], loc[1]),
            frequency=p.get("frequency", "unknown"),
            fragile=bool(p.get("fragile", False)),
            incompatible_with=list(p.get("incompatible_with", [])),
        )
    return products
```

**Rôle :** Convertit une liste JSON de produits en dictionnaire `{product_id: Product}`.

**Points importants :**
- Retourne un **dictionnaire** indexé par ID pour accès rapide (O(1))
- Utilise `.get()` avec valeurs par défaut pour gérer les champs optionnels
- Convertit les types (float, bool, list)
- Crée un objet `Location` à partir de `[x, y]`

**Fonction 4 : `build_agent()`**

```python
def build_agent(raw: dict) -> Agent:
    base_kwargs = dict(
        id=raw["id"],
        type=raw.get("type", "unknown"),
        capacity_weight=float(raw.get("capacity_weight", 0.0)),
        capacity_volume=float(raw.get("capacity_volume", 0.0)),
        speed=float(raw.get("speed", 0.0)),
        cost_per_hour=float(raw.get("cost_per_hour", 0.0)),
    )
    t = base_kwargs["type"]
    if t == "robot":
        return Robot(**base_kwargs)
    if t == "human":
        return Human(**base_kwargs)
    if t == "cart":
        return Cart(**base_kwargs)
    return Agent(**base_kwargs)
```

**Rôle :** Crée un agent du bon type (`Robot`, `Human`, ou `Cart`) selon le type dans les données JSON.

**Fonctionnement :**
1. Prépare les arguments communs à tous les types d'agents
2. Détecte le type d'agent
3. Instancie la bonne sous-classe (`Robot`, `Human`, ou `Cart`)

**Fonction 5 : `parse_agents()`**

```python
def parse_agents(data: list) -> List[Agent]:
    return [build_agent(a) for a in data]
```

**Rôle :** Convertit une liste JSON d'agents en liste d'objets `Agent`.

- Utilise une list comprehension pour traiter tous les agents
- Appelle `build_agent()` pour chaque agent JSON

**Fonction 6 : `parse_orders()`**

```python
def parse_orders(data: list) -> List[Order]:
    orders: List[Order] = []
    for o in data:
        items = [
            OrderItem(product_id=it["product_id"], quantity=int(it["quantity"]))
            for it in o.get("items", [])
        ]
        orders.append(
            Order(
                id=o["id"],
                received_time=o.get("received_time", "00:00"),
                deadline=o.get("deadline", "23:59"),
                priority=o.get("priority", "standard"),
                items=items,
            )
        )
    return orders
```

**Rôle :** Convertit une liste JSON de commandes en liste d'objets `Order`.

**Étapes :**
1. Parsing des items : crée des objets `OrderItem` pour chaque produit dans la commande
2. Création de la commande : crée un objet `Order` avec tous ses items

**Utilisation dans `main.py` :**

```python
# Chargement des fichiers JSON
wh_data = load_json(Path("data/warehouse.json"))
pr_data = load_json(Path("data/products.json"))
ag_data = load_json(Path("data/agents.json"))
or_data = load_json(Path("data/orders.json"))

# Conversion en objets Python
warehouse = parse_warehouse(wh_data)
products_by_id = parse_products(pr_data)
agents = parse_agents(ag_data)
orders = parse_orders(or_data)
```

**Avantages de cette architecture :**
- ✅ **Séparation des responsabilités** : Le chargement est séparé de la logique métier
- ✅ **Réutilisabilité** : Les fonctions peuvent être réutilisées ailleurs
- ✅ **Testabilité** : Chaque fonction peut être testée indépendamment
- ✅ **Maintenabilité** : Si le format JSON change, seul `loader.py` doit être modifié
- ✅ **Gestion d'erreurs** : Utilisation de `.get()` avec valeurs par défaut pour éviter les erreurs

## 📈 Métriques de Performance

Le système évalue les solutions sur :
1. **Distance totale parcourue** (mètres)
2. **Temps total de préparation** (minutes)
3. **Coût opérationnel** (euros)
4. **Taux de respect des deadlines** (%)
5. **Équilibrage de charge** (écart-type entre agents)
6. **Taux d'utilisation** des robots vs humains

## 🎓 Contexte Académique

Ce projet fait partie du module **Programmation Logique et par Contraintes** (L2 Informatique).

Il combine :
- **Satisfaction de Contraintes (CSP)** : Modélisation et résolution avec OR-Tools
- **Optimisation Combinatoire** : TSP, allocation optimale
- **Algorithmes Gloutons** : Stratégies d'allocation rapides
- **Analyse de Données** : Patterns de commandes, optimisation du stockage

## 📚 Ressources

- [Documentation OR-Tools](https://developers.google.com/optimization)
- [CP-SAT Guide](https://developers.google.com/optimization/cp)
- [Routing (TSP/VRP)](https://developers.google.com/optimization/routing)
- [TSPLIB](http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/)

## 📝 Notes

- Le projet suit une progression sur 5 journées avec difficulté croissante
- Les contraintes dures doivent être respectées à 100%
- Les contraintes souples sont optimisées selon la fonction objectif
- La visualisation est fortement recommandée pour comprendre les résultats

---

Pour plus de détails, consultez le fichier `ENONCE_PROJET_OPTIPICK.txt`.
