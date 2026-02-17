# Rapport Jour 2bis - Flux d'Exécution et Architecture des Fichiers

**Projet OptiPick** | Ymen Nermine, Hamid, Romain

---

## 🚀 Chemin pour Lancer le Programme

### Commande principale

```bash
cd /Users/romain/Desktop/forge/optipick
python main.py
```

### Options disponibles

```bash
# Utiliser l'algorithme glouton (par défaut)
python main.py

# Utiliser MiniZinc pour l'allocation optimale
python main.py --minizinc

# Spécifier un solveur MiniZinc particulier
python main.py --minizinc --solver cbc
python main.py --minizinc --solver coin-bc
python main.py --minizinc --solver highs

# Test avec 1 commande et 1 agent
python main.py --test
python main.py --test --minizinc --solver cbc
```

### Prérequis

1. **Environnement virtuel activé** (si utilisé) :
   ```bash
   source venv/bin/activate  # macOS/Linux
   ```

2. **Dépendances installées** :
   ```bash
   pip install -r requirements.txt
   ```

3. **MiniZinc installé** (si utilisation de `--minizinc`) :
   - Télécharger depuis https://www.minizinc.org/
   - Installer la bibliothèque Python : `pip install minizinc`

---

## 📁 Fichiers Utilisés et Ordre d'Exécution

### Vue d'ensemble du flux

```
main.py (point d'entrée)
    ↓
1. Chargement des données JSON (loader.py)
    ↓
2. Parsing en objets Python (loader.py + models.py)
    ↓
3. Enrichissement des commandes (main.py)
    ↓
4. Allocation (glouton ou MiniZinc)
    ↓
5. Affichage du rapport (main.py)
```

---

## 🔄 Détail du Flux d'Exécution

### Étape 1 : Point d'entrée (`main.py`)

**Fichier :** `main.py` (lignes 267-300)

**Ce qui se passe :**
- Parsing des arguments de ligne de commande (`--minizinc`, `--solver`, `--test`)
- Appel de la fonction `main()` avec les paramètres appropriés
- Définition des chemins des fichiers de données (ou fichiers de test si `--test`)

**Fichiers de données utilisés (par défaut) :**
- `data/warehouse.json`
- `data/products.json`
- `data/agents.json`
- `data/orders.json`

**Fichiers de test (si `--test`) :**
- `data/warehouse.json` (même fichier)
- `data/products.json` (même fichier)
- `data/test_agents.json`
- `data/test_orders.json`

---

### Étape 2 : Chargement des données JSON (`src/loader.py`)

**Fichier :** `src/loader.py`

**Fonctions appelées dans l'ordre :**

1. **`load_json(Path("data/warehouse.json"))`**
   - Lit le fichier JSON brut
   - Retourne un dictionnaire Python
   - **Contenu :** dimensions, zones, point d'entrée

2. **`load_json(Path("data/products.json"))`**
   - Lit le fichier JSON brut
   - Retourne une liste de dictionnaires
   - **Contenu :** 100 produits avec leurs caractéristiques

3. **`load_json(Path("data/agents.json"))`**
   - Lit le fichier JSON brut
   - Retourne une liste de dictionnaires
   - **Contenu :** 7 agents (3 robots, 2 humains, 2 chariots)

4. **`load_json(Path("data/orders.json"))`**
   - Lit le fichier JSON brut
   - Retourne une liste de dictionnaires
   - **Contenu :** 30 commandes avec leurs items

---

### Étape 3 : Parsing en objets Python (`src/loader.py` + `src/models.py`)

**Fichiers :** `src/loader.py` et `src/models.py`

**Fonctions appelées dans l'ordre :**

1. **`parse_warehouse(wh_data)`** → Objet `Warehouse`
   - Convertit les dimensions, zones, point d'entrée
   - Crée des objets `Location` pour chaque coordonnée
   - **Utilise :** `src/models.py` → classe `Warehouse`, `Location`

2. **`parse_products(pr_data)`** → Dictionnaire `{product_id: Product}`
   - Pour chaque produit JSON, crée un objet `Product`
   - Convertit les types (float, bool, list)
   - Crée des objets `Location` pour les emplacements
   - **Utilise :** `src/models.py` → classe `Product`, `Location`

3. **`parse_agents(ag_data)`** → Liste `[Agent, ...]`
   - Pour chaque agent JSON, appelle `build_agent(raw)`
   - `build_agent` crée un `Robot`, `Human` ou `Cart` selon le type
   - Charge les `restrictions` depuis le JSON
   - **Utilise :** `src/models.py` → classes `Agent`, `Robot`, `Human`, `Cart`

4. **`parse_orders(or_data)`** → Liste `[Order, ...]`
   - Pour chaque commande JSON, crée un objet `Order`
   - Crée des objets `OrderItem` pour chaque item
   - **Utilise :** `src/models.py` → classes `Order`, `OrderItem`

**Résultat de cette étape :**
- `warehouse` : objet `Warehouse`
- `products_by_id` : dictionnaire `{str: Product}`
- `agents` : liste `[Agent, ...]`
- `orders` : liste `[Order, ...]`

---

### Étape 4 : Enrichissement des commandes (`main.py`)

**Fichier :** `main.py` (lignes 35-57)

**Fonction :** `enrich_orders(orders, products_by_id)`

**Ce qui se passe :**
- Pour chaque commande, calcule :
  - `total_weight` : somme des poids des produits × quantités
  - `total_volume` : somme des volumes des produits × quantités
  - `unique_locations` : liste des emplacements uniques (sans doublons)

**Utilise :**
- `products_by_id` pour récupérer les produits par leur ID
- Les objets `Product` pour accéder à `weight`, `volume`, `location`

**Résultat :**
- Les objets `Order` sont modifiés en place (ajout des attributs calculés)

---

### Étape 5 : Tri des commandes (`main.py`)

**Fichier :** `main.py` (lignes 66-72)

**Fonction :** `sort_orders_by_received_time(orders)`

**Ce qui se passe :**
- Convertit `received_time` (format "HH:MM") en minutes
- Trie les commandes par ordre chronologique d'arrivée
- Retourne la liste triée

**Résultat :**
- `orders_sorted` : liste des commandes triées par heure de réception

---

### Étape 6 : Allocation (`main.py` ou `src/minizinc_solver.py`)

**Deux chemins possibles selon l'option `--minizinc` :**

#### Chemin A : Algorithme Glouton (`main.py`)

**Fichier :** `main.py` (lignes 95-141)

**Fonction :** `allocate_first_fit(orders_sorted, agents, products_by_id, warehouse)`

**Ce qui se passe :**
1. Trie les agents par priorité (robots → humains → chariots)
2. Pour chaque commande (dans l'ordre) :
   - Parcourt les agents dans l'ordre de priorité
   - Appelle `can_agent_take_order_with_constraints()` pour vérifier toutes les contraintes
   - Si un agent peut prendre la commande, l'assigne et passe à la suivante

**Utilise :**
- `src/constraints.py` → `can_agent_take_order_with_constraints()`
- `src/models.py` → méthode `Agent.assign()`

**Résultat :**
- `assignment` : dictionnaire `{order_id: agent_id or None}`

#### Chemin B : MiniZinc (`src/minizinc_solver.py`)

**Fichier :** `src/minizinc_solver.py`

**Fonction :** `allocate_with_minizinc(orders_sorted, agents, products_by_id, warehouse, solver_name)`

**Ce qui se passe :**
1. Charge le modèle MiniZinc : `models/allocation.mzn`
2. Prépare les données pour MiniZinc :
   - Extrait les capacités, poids, volumes depuis les objets Python
   - Construit la matrice d'incompatibilités
   - Détermine les zones des commandes
   - Prépare les restrictions des robots
3. Crée une instance MiniZinc avec le solveur demandé
4. Injecte toutes les données dans l'instance
5. Résout le problème avec le solveur (ex. `cbc`, `coin-bc`, `highs`)
6. Convertit la solution MiniZinc en dictionnaire Python

**Utilise :**
- `models/allocation.mzn` : modèle MiniZinc
- `src/constraints.py` → `get_product_zone()`, `can_combine()` pour préparer les données
- Bibliothèque `minizinc` (Python) pour l'interface avec MiniZinc

**Résultat :**
- `assignment` : dictionnaire `{order_id: agent_id or None}`

---

### Étape 7 : Affichage du rapport (`main.py`)

**Fichier :** `main.py` (lignes 169-203)

**Fonction :** `print_report(warehouse, orders_sorted, agents, assignment, use_minizinc)`

**Ce qui se passe :**
1. Calcule les statistiques :
   - Nombre total de commandes
   - Nombre de commandes assignées / non assignées
   - Distance totale estimée
2. Affiche le titre (glouton ou MiniZinc)
3. Affiche les statistiques globales
4. Affiche le détail par agent :
   - Nombre de commandes assignées
   - Liste des IDs des commandes
   - Utilisation poids/volume (en kg/dm³ et pourcentage)
5. Liste les commandes non assignées (si présentes)

**Utilise :**
- `warehouse` pour calculer les distances
- `orders_sorted` pour la distance totale
- `agents` pour afficher les détails
- `assignment` pour les statistiques

---

## 📋 Explication Détaillée des Paramètres MiniZinc

Cette section explique en détail les principaux paramètres du modèle MiniZinc (`models/allocation.mzn`).

---

### 1. `array[AGENTS] of float: capacity_weight;` (ligne 11)

#### Structure de la déclaration

- **`array[AGENTS]`** : Tableau indexé par l'ensemble `AGENTS`
  - `AGENTS` est défini ligne 8 : `set of int: AGENTS = 1..n_agents;`
  - C'est un ensemble d'entiers de 1 à `n_agents` (ex. si `n_agents = 7`, alors `AGENTS = {1, 2, 3, 4, 5, 6, 7}`)

- **`of float`** : Chaque élément est un nombre décimal (ex. `10.5`, `25.0`)

- **`capacity_weight`** : Nom du paramètre (capacité en poids de chaque agent)

#### Signification

Cette ligne déclare un **paramètre** (donnée d'entrée) : un tableau de nombres décimaux, un par agent.

**Exemple avec 3 agents :**
```minizinc
capacity_weight = [10.5, 25.0, 15.3];
```
- `capacity_weight[1] = 10.5` (agent 1)
- `capacity_weight[2] = 25.0` (agent 2)
- `capacity_weight[3] = 15.3` (agent 3)

#### Utilisation dans le modèle

Utilisé dans la contrainte de capacité (ligne 45) :
```minizinc
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) (order_weight[order_idx]) 
    <= capacity_weight[agent_idx]
);
```

Cette contrainte garantit que le poids total des commandes assignées à un agent ne dépasse pas sa capacité.

#### D'où viennent les valeurs ?

Les valeurs proviennent de `agents.json` via Python :
1. `main.py` charge `agents.json` via `loader.py`
2. `loader.py` crée des objets `Agent` avec `capacity_weight`
3. `minizinc_solver.py` extrait ces valeurs et les injecte dans MiniZinc :
   ```python
   capacity_weight = [agent.capacity_weight for agent in agents]
   instance["capacity_weight"] = capacity_weight
   ```

---

### 2. `set of int: ZONES = 0..n_zones-1;` (ligne 23)

#### Explication du `-1`

Le `-1` ici n'est **pas une valeur littérale** mais une **soustraction** : `n_zones - 1`.

#### Calcul pas à pas

1. **Ligne 22** : `int: n_zones = 5;`
   - `n_zones` vaut `5`

2. **Ligne 23** : `set of int: ZONES = 0..n_zones-1;`
   - `n_zones - 1` = `5 - 1` = `4`
   - `0..4` crée l'ensemble `{0, 1, 2, 3, 4}`

#### Pourquoi `n_zones - 1` ?

Les zones sont numérotées à partir de 0 :
- Zone A = 0
- Zone B = 1
- Zone C = 2
- Zone D = 3
- Zone E = 4

Avec 5 zones (0 à 4), l'ensemble doit aller de 0 à 4, donc `0..(5-1)` = `0..4`.

#### Résultat

```minizinc
ZONES = {0, 1, 2, 3, 4}
```

Cela correspond aux 5 zones A, B, C, D, E.

#### Utilisation dans le modèle

Utilisé ligne 24 pour déclarer la matrice des zones interdites :
```minizinc
array[AGENTS, ZONES] of bool: forbidden_zones;
```

Cette matrice a :
- Une ligne par agent (`AGENTS`)
- Une colonne par zone (`ZONES = {0, 1, 2, 3, 4}`)

#### Note importante

Le `-1` de la ligne 28 est différent :
```minizinc
% Zones des commandes (encodées comme entiers: 0=A, 1=B, 2=C, 3=D, 4=E, -1=aucune)
array[ORDERS] of int: order_zones;
```

Ici, `-1` est une **valeur littérale** utilisée pour indiquer "aucune zone" (quand un produit n'est dans aucune zone définie).

---

### 3. Paramètres des commandes (lignes 29-31)

#### Vue d'ensemble

Ces trois lignes déclarent des **paramètres** (données d'entrée) qui décrivent les caractéristiques de chaque commande, nécessaires pour vérifier les restrictions des robots.

```minizinc
array[ORDERS] of int: order_zones;
array[ORDERS] of bool: order_has_fragile;       % La commande contient des objets fragiles
array[ORDERS] of float: order_max_item_weight;   % Poids max d'un item dans la commande
```

---

#### 3.1. `array[ORDERS] of int: order_zones;` (ligne 29)

**Structure :**
- `array[ORDERS]` : Tableau indexé par l'ensemble des commandes
- `of int` : Chaque valeur est un entier
- `order_zones` : Nom du paramètre

**Signification :**
Indique la zone principale de chaque commande, encodée comme un entier :
- `0` = Zone A
- `1` = Zone B
- `2` = Zone C
- `3` = Zone D
- `4` = Zone E
- `-1` = Aucune zone (produit non assigné à une zone)

**Exemple :**
Si vous avez 3 commandes :
```minizinc
order_zones = [1, 3, -1];
```
- Commande 1 → Zone B (1)
- Commande 2 → Zone D (3)
- Commande 3 → Aucune zone (-1)

**Utilisation dans le modèle :**
Utilisé ligne 55-56 pour vérifier les zones interdites des robots :
```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ order_zones[order_idx] != -1) ->
    (not forbidden_zones[agent_idx, order_zones[order_idx]])
);
```

Cette contrainte dit : "Si une commande est assignée à un robot ET que la commande a une zone définie, alors cette zone ne doit pas être interdite pour ce robot."

---

#### 3.2. `array[ORDERS] of bool: order_has_fragile;` (ligne 30)

**Structure :**
- `array[ORDERS]` : Tableau indexé par les commandes
- `of bool` : Chaque valeur est booléenne (`true` ou `false`)
- `order_has_fragile` : Nom du paramètre

**Signification :**
Indique si une commande contient au moins un produit fragile.

**Exemple :**
```minizinc
order_has_fragile = [false, true, false];
```
- Commande 1 → Pas d'objets fragiles
- Commande 2 → Contient des objets fragiles
- Commande 3 → Pas d'objets fragiles

**Utilisation dans le modèle :**
Utilisé lignes 60-62 pour vérifier la restriction "pas d'objets fragiles" :
```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ no_fragile[agent_idx]) ->
    (not order_has_fragile[order_idx])
);
```

Cette contrainte dit : "Si une commande est assignée à un robot ET que ce robot ne peut pas prendre d'objets fragiles, alors la commande ne doit pas contenir d'objets fragiles."

---

#### 3.3. `array[ORDERS] of float: order_max_item_weight;` (ligne 31)

**Structure :**
- `array[ORDERS]` : Tableau indexé par les commandes
- `of float` : Chaque valeur est un nombre décimal
- `order_max_item_weight` : Nom du paramètre

**Signification :**
Indique le poids maximum d'un seul item dans chaque commande (en kg).

**Exemple :**
```minizinc
order_max_item_weight = [2.5, 15.0, 0.8];
```
- Commande 1 → L'item le plus lourd pèse 2.5 kg
- Commande 2 → L'item le plus lourd pèse 15.0 kg
- Commande 3 → L'item le plus lourd pèse 0.8 kg

**Utilisation dans le modèle :**
Utilisé lignes 66-68 pour vérifier la restriction de poids maximum par item :
```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ max_item_weight[agent_idx] > 0) ->
    (order_max_item_weight[order_idx] <= max_item_weight[agent_idx])
);
```

Cette contrainte dit : "Si une commande est assignée à un robot ET que ce robot a une limite de poids par item, alors le poids maximum d'un item dans la commande ne doit pas dépasser cette limite."

---

### Résumé des paramètres

| Paramètre | Type | Signification | Utilisé pour |
|-----------|------|---------------|--------------|
| `capacity_weight` | `array[AGENTS] of float` | Capacité en poids de chaque agent (kg) | Vérifier la contrainte de capacité en poids |
| `ZONES` | `set of int` | Ensemble des zones {0, 1, 2, 3, 4} | Indexer les matrices de zones interdites |
| `order_zones` | `array[ORDERS] of int` | Zone principale de la commande (0-4 ou -1) | Vérifier les zones interdites des robots |
| `order_has_fragile` | `array[ORDERS] of bool` | La commande contient-elle des objets fragiles ? | Vérifier la restriction "pas d'objets fragiles" |
| `order_max_item_weight` | `array[ORDERS] of float` | Poids maximum d'un item dans la commande (kg) | Vérifier la limite de poids par item |

---

### D'où viennent ces valeurs ?

Ces valeurs sont calculées dans `minizinc_solver.py` à partir des objets Python :

1. **`capacity_weight`** : Extrait directement depuis `agent.capacity_weight` pour chaque agent
2. **`order_zones`** : Déterminé en analysant les emplacements des produits de la commande et en utilisant `get_product_zone()` de `constraints.py`
3. **`order_has_fragile`** : Vérifie si au moins un produit de la commande a `fragile = true`
4. **`order_max_item_weight`** : Trouve le poids maximum parmi tous les produits de la commande

Ces paramètres permettent au modèle MiniZinc de vérifier automatiquement toutes les restrictions des robots lors de l'allocation optimale.

---

## 📊 Schéma du Flux Complet

```
┌─────────────────────────────────────────────────────────────┐
│                    main.py (point d'entrée)                   │
│  - Parse arguments (--minizinc, --solver, --test)            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              ÉTAPE 1 : Chargement JSON                      │
│  loader.py → load_json()                                    │
│  • warehouse.json → wh_data (dict)                          │
│  • products.json → pr_data (list)                           │
│  • agents.json → ag_data (list)                             │
│  • orders.json → or_data (list)                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         ÉTAPE 2 : Parsing en objets Python                 │
│  loader.py + models.py                                      │
│  • parse_warehouse() → Warehouse                            │
│  • parse_products() → {id: Product}                         │
│  • parse_agents() → [Agent, ...]                            │
│  • parse_orders() → [Order, ...]                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│        ÉTAPE 3 : Enrichissement des commandes               │
│  main.py → enrich_orders()                                  │
│  • Calcule total_weight, total_volume                      │
│  • Extrait unique_locations                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           ÉTAPE 4 : Tri des commandes                       │
│  main.py → sort_orders_by_received_time()                   │
│  • Trie par heure de réception                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  GLOUTON         │          │   MINIZINC      │
│  (par défaut)    │          │  (--minizinc)   │
│                  │          │                  │
│  main.py         │          │  minizinc_solver│
│  allocate_first_ │          │  .py             │
│  fit()           │          │  allocate_with_ │
│                  │          │  minizinc()      │
│  Utilise:        │          │                  │
│  • constraints.py│          │  Utilise:        │
│  • models.py     │          │  • allocation.mzn│
│                  │          │  • constraints.py│
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         └───────────────┬─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ÉTAPE 5 : Affichage du rapport                 │
│  main.py → print_report()                                   │
│  • Statistiques globales                                    │
│  • Détail par agent                                         │
│  • Commandes non assignées                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Dépendances entre Fichiers

### Fichiers Python

| Fichier | Dépend de | Utilisé par |
|---------|-----------|-------------|
| `main.py` | `src.loader`, `src.models`, `src.constraints`, `src.minizinc_solver` | Point d'entrée |
| `src/loader.py` | `src.models` | `main.py` |
| `src/models.py` | Aucun (définitions de base) | `loader.py`, `constraints.py`, `minizinc_solver.py`, `main.py` |
| `src/constraints.py` | `src.models` | `main.py`, `minizinc_solver.py` |
| `src/minizinc_solver.py` | `src.models`, `src.constraints`, `minizinc` | `main.py` |

### Fichiers de données

| Fichier | Format | Utilisé par |
|---------|--------|-------------|
| `data/warehouse.json` | JSON | `loader.py` → `parse_warehouse()` |
| `data/products.json` | JSON | `loader.py` → `parse_products()` |
| `data/agents.json` | JSON | `loader.py` → `parse_agents()` |
| `data/orders.json` | JSON | `loader.py` → `parse_orders()` |
| `data/test_agents.json` | JSON | `loader.py` (si `--test`) |
| `data/test_orders.json` | JSON | `loader.py` (si `--test`) |

### Fichiers MiniZinc

| Fichier | Format | Utilisé par |
|---------|--------|-------------|
| `models/allocation.mzn` | MiniZinc | `minizinc_solver.py` → `Model()` |
| `models/allocation_example.dzn` | MiniZinc Data | Optionnel (test direct) |

---

## 🔍 Ordre d'Exécution Détaillé (Ligne par Ligne)

### Dans `main.py` (fonction `main()`)

1. **Lignes 218-221** : Chargement JSON brut
   ```python
   wh_data = load_json(Path(warehouse_path))
   pr_data = load_json(Path(products_path))
   ag_data = load_json(Path(agents_path))
   or_data = load_json(Path(orders_path))
   ```

2. **Lignes 223-226** : Parsing en objets Python
   ```python
   warehouse = parse_warehouse(wh_data)
   products_by_id = parse_products(pr_data)
   agents = parse_agents(ag_data)
   orders = parse_orders(or_data)
   ```

3. **Ligne 228** : Enrichissement des commandes
   ```python
   enrich_orders(orders, products_by_id)
   ```

4. **Ligne 231** : Tri des commandes
   ```python
   orders_sorted = sort_orders_by_received_time(orders)
   ```

5. **Lignes 234-256** : Allocation (glouton ou MiniZinc)
   ```python
   if use_minizinc and MINIZINC_AVAILABLE:
       assignment = allocate_with_minizinc(...)
   else:
       assignment = allocate_first_fit(...)
   ```

6. **Ligne 264** : Affichage du rapport
   ```python
   print_report(warehouse, orders_sorted, agents, assignment, ...)
   ```

---

## ✅ Vérification du Fonctionnement

Pour vérifier que tout fonctionne avec 1 commande et 1 agent :

```bash
# Test simple avec script Python
python test_simple.py

# Test avec fichiers JSON de test
python main.py --test

# Test avec MiniZinc
python main.py --test --minizinc --solver cbc
```

**Résultat attendu :**
- ✅ 1 commande assignée sur 1
- ✅ Agent R1 avec 1 commande
- ✅ Pas d'erreur
- ✅ Rapport affiché correctement

---

*Rapport généré pour le Jour 2bis - Projet OptiPick*
