# Pourquoi `allocation.mzn` n'a pas de fichier `.dzn` ?

## 📋 Question

Pourquoi le fichier `models/allocation.mzn` n'a pas de fichier `.dzn` associé, alors que l'exemple `examples/test.mzn` en a un (`test_data.dzn`) ?

## 🔍 Deux approches différentes

Il existe **deux façons** de passer des données à un modèle MiniZinc :

### Approche 1 : Fichier `.dzn` (modèle autonome)

**Utilisation** : Résoudre directement avec MiniZinc depuis la ligne de commande

**Exemple** : `examples/test.mzn` (fichier autonome, données intégrées)

```bash
cd examples
minizinc --solver COIN-BC test.mzn
```

**Ou avec le chemin complet depuis la racine :**
```bash
minizinc --solver COIN-BC examples/test.mzn
```

**Note** : `test.mzn` est autonome et contient toutes les données (matrice de distances) directement dans le fichier, donc aucun fichier `.dzn` n'est nécessaire.

**Structure** :
- `test.mzn` : Déclare les paramètres (sans valeurs)
  ```minizinc
  int: n_locations;
  array[LOCATIONS, LOCATIONS] of int: distance_matrix;
  ```
- `test_data.dzn` : Définit les valeurs
  ```minizinc
  n_locations = 4;
  distance_matrix = [| 0, 3, 5, 7 | ... |];
  ```

**Avantages** :
- ✅ Modèle autonome, peut être résolu sans Python
- ✅ Facile à tester manuellement
- ✅ Partageable indépendamment du code Python

**Inconvénients** :
- ❌ Données statiques (doivent être écrites manuellement)
- ❌ Pas d'intégration avec des données dynamiques (JSON, base de données)

---

### Approche 2 : API Python (données dynamiques)

**Utilisation** : Passer les données depuis Python via l'API MiniZinc

**Exemple** : `models/allocation.mzn` (utilisé depuis `src/minizinc_solver.py`)

```python
from minizinc import Instance, Model, Solver

model = Model("models/allocation.mzn")
instance = Instance(solver, model)

# Passer les données directement depuis Python
instance["n_orders"] = len(orders)
instance["n_agents"] = len(agents)
instance["capacity_weight"] = [agent.capacity_weight for agent in agents]
instance["order_weight"] = [order.total_weight for order in orders]
# ... etc

result = instance.solve()
```

**Structure** :
- `allocation.mzn` : Déclare les paramètres (sans valeurs)
  ```minizinc
  int: n_orders;
  array[AGENTS] of float: capacity_weight;
  array[ORDERS] of float: order_weight;
  ```
- **Pas de fichier `.dzn`** : Les valeurs viennent de Python

**Avantages** :
- ✅ Données dynamiques (chargées depuis JSON, calculées, etc.)
- ✅ Intégration avec le reste du code Python
- ✅ Facile à adapter selon les données d'entrée
- ✅ Pas besoin de créer/maintenir un fichier `.dzn`

**Inconvénients** :
- ❌ Nécessite Python pour résoudre
- ❌ Ne peut pas être résolu directement avec `minizinc` en ligne de commande

---

## 📊 Comparaison

| Caractéristique | Avec `.dzn` (`test.mzn`) | Sans `.dzn` (`allocation.mzn`) |
|----------------|-------------------------|--------------------------------|
| **Résolution directe** | ✅ `minizinc test.mzn data.dzn` | ❌ Nécessite Python |
| **Données statiques** | ✅ Facile | ❌ Pas adapté |
| **Données dynamiques** | ❌ Difficile | ✅ Parfait |
| **Intégration Python** | ❌ Nécessite parsing | ✅ Directe |
| **Maintenance** | ❌ Deux fichiers à synchroniser | ✅ Un seul fichier |

---

## 🎯 Pourquoi `allocation.mzn` n'a pas de `.dzn` ?

### Raison principale : Données dynamiques

Le modèle `allocation.mzn` utilise des données qui :
1. **Viennent de fichiers JSON** (`agents.json`, `orders.json`, `products.json`)
2. **Sont calculées** (`order_weight` = somme des poids des produits × quantités)
3. **Changent à chaque exécution** (différentes commandes, différents agents)

Créer un fichier `.dzn` serait :
- ❌ Fastidieux (doit être régénéré à chaque fois)
- ❌ Redondant (les données existent déjà en JSON)
- ❌ Difficile à maintenir (risque de désynchronisation)

### Exemple concret

Si on voulait créer `allocation_data.dzn` pour 10 commandes et 6 agents :

```minizinc
n_orders = 10;
n_agents = 6;
capacity_weight = [20.0, 20.0, 20.0, 35.0, 35.0, 50.0];
capacity_volume = [30.0, 30.0, 30.0, 50.0, 50.0, 80.0];
order_weight = [2.8, 1.5, 5.2, 3.1, 4.7, 2.3, 1.9, 6.1, 3.5, 2.0];
order_volume = [8.5, 3.2, 12.1, 9.3, 15.2, 7.8, 5.4, 18.9, 10.1, 6.2];
% ... et beaucoup d'autres paramètres
```

**Problèmes** :
- Doit être régénéré à chaque changement de données
- Difficile à maintenir
- Redondant avec les fichiers JSON existants

---

## ✅ Quand utiliser un fichier `.dzn` ?

Utilisez un fichier `.dzn` quand :
- ✅ Vous voulez tester le modèle **indépendamment** de Python
- ✅ Les données sont **statiques** (ne changent pas souvent)
- ✅ Vous voulez partager le modèle avec des **données d'exemple**
- ✅ Vous avez besoin de **plusieurs jeux de données** pour tester

**Exemple** : `test.mzn` + `test_data.dzn` pour un exemple simple et autonome.

---

## ✅ Quand NE PAS utiliser de fichier `.dzn` ?

N'utilisez PAS de fichier `.dzn` quand :
- ✅ Les données viennent de **fichiers JSON** ou bases de données
- ✅ Les données sont **calculées dynamiquement**
- ✅ Le modèle est **intégré dans une application Python**
- ✅ Les données changent **fréquemment**

**Exemple** : `allocation.mzn` utilisé depuis le code Python du projet.

---

## 🔧 Créer un `.dzn` pour `allocation.mzn` (optionnel)

Si vous voulez quand même créer un fichier `.dzn` pour tester `allocation.mzn` directement, vous pouvez :

1. **Extraire les données depuis Python** :
   ```python
   # Script pour générer allocation_data.dzn
   orders = load_orders("data/orders.json")
   agents = load_agents("data/agents.json")
   products = load_products("data/products.json")
   
   # Générer le fichier .dzn
   with open("allocation_data.dzn", "w") as f:
       f.write(f"n_orders = {len(orders)};\n")
       f.write(f"n_agents = {len(agents)};\n")
       f.write(f"capacity_weight = [{', '.join(str(a.capacity_weight) for a in agents)}];\n")
       # ... etc
   ```

2. **Résoudre directement** :
   ```bash
   minizinc --solver COIN-BC models/allocation.mzn allocation_data.dzn
   ```

Mais ce n'est **pas nécessaire** car le code Python fait déjà tout automatiquement !

---

## 📝 Résumé

| Modèle | Fichier `.dzn` ? | Pourquoi ? |
|--------|------------------|------------|
| `test.mzn` | ✅ Oui (`test_data.dzn`) | Exemple autonome, données statiques |
| `allocation.mzn` | ❌ Non | Données dynamiques depuis Python/JSON |

**Conclusion** : `allocation.mzn` n'a pas de `.dzn` car il est conçu pour être utilisé depuis Python avec des données dynamiques, pas comme un modèle autonome.

---

## 🏗️ Architecture correcte : Flux de données

### 📋 Architecture recommandée

Dans ton code Python, l'architecture correcte devrait être :

```
products.json
orders.json
agents.json
        ↓
    Python
        ↓
construction des arrays
        ↓
génération d'un fichier .dzn
        ↓
allocation.mzn + fichier .dzn créé
```

### 🔄 Flux détaillé

#### Étape 1 : Chargement des données JSON

```python
# Charger les fichiers JSON
products = load_products("data/products.json")
orders = load_orders("data/orders.json")
agents = load_agents("data/agents.json")
```

#### Étape 2 : Construction des arrays en Python

```python
# Calculer les valeurs nécessaires
n_orders = len(orders)
n_agents = len(agents)

# Construire les arrays
capacity_weight = [agent.capacity_weight for agent in agents]
order_weight = [order.total_weight for order in orders]
# ... etc
```

#### Étape 3 : Génération du fichier `.dzn`

```python
def generate_dzn_file(orders, agents, products, warehouse, output_path):
    """Génère un fichier .dzn avec toutes les données pour allocation.mzn"""
    with open(output_path, 'w') as f:
        # Paramètres scalaires
        f.write(f"n_orders = {len(orders)};\n")
        f.write(f"n_agents = {len(agents)};\n\n")
        
        # Arrays
        f.write("capacity_weight = [")
        f.write(", ".join(str(a.capacity_weight) for a in agents))
        f.write("];\n\n")
        
        f.write("order_weight = [")
        f.write(", ".join(str(o.total_weight) for o in orders))
        f.write("];\n\n")
        
        # ... autres paramètres
```

#### Étape 4 : Résolution avec MiniZinc

```python
# Option 1 : Via ligne de commande
subprocess.run(["minizinc", "--solver", "COIN-BC", 
                "models/allocation.mzn", "allocation_data.dzn"])

# Option 2 : Via API Python (mais avec fichier .dzn)
from minizinc import Instance, Model, Solver
model = Model("models/allocation.mzn")
instance = Instance(solver, model)
instance.add_file("allocation_data.dzn")  # ← Utilise le .dzn généré
result = instance.solve()
```

### ✅ Avantages de cette architecture

1. **Séparation claire** : Python gère les données, MiniZinc résout
2. **Débogage facile** : Le fichier `.dzn` peut être inspecté
3. **Réutilisabilité** : Le `.dzn` peut être partagé ou réutilisé
4. **Traçabilité** : On voit exactement quelles données sont passées à MiniZinc
5. **Testabilité** : On peut tester `allocation.mzn` indépendamment avec différents `.dzn`

### 🔄 Architecture actuelle vs Architecture recommandée

| Aspect | Architecture actuelle | Architecture recommandée |
|--------|----------------------|------------------------|
| **Passage de données** | Direct via `instance["param"]` | Fichier `.dzn` généré |
| **Visibilité** | Données cachées dans Python | Fichier `.dzn` visible |
| **Débogage** | Difficile (données dans Python) | Facile (fichier `.dzn` lisible) |
| **Réutilisabilité** | Nécessite Python | `.dzn` autonome |
| **Testabilité** | Nécessite Python | `minizinc model.mzn data.dzn` |

### 💡 Implémentation recommandée

**Script Python (`generate_allocation_data.py`) :**

```python
#!/usr/bin/env python3
"""Génère allocation_data.dzn depuis les fichiers JSON"""

from src.loader import load_products, load_orders, load_agents, load_warehouse
from src.day5_simulation import _enrich_orders

def generate_allocation_dzn(
    products_path: str,
    orders_path: str,
    agents_path: str,
    warehouse_path: str,
    output_path: str = "allocation_data.dzn"
):
    # 1. Charger les données
    products = load_products(products_path)
    orders = load_orders(orders_path)
    agents = load_agents(agents_path)
    warehouse = load_warehouse(warehouse_path)
    
    # 2. Enrichir les commandes (calculer total_weight, etc.)
    products_by_id = {p.id: p for p in products}
    _enrich_orders(orders, products_by_id)
    
    # 3. Construire les arrays
    n_orders = len(orders)
    n_agents = len(agents)
    
    capacity_weight = [a.capacity_weight for a in agents]
    capacity_volume = [a.capacity_volume for a in agents]
    order_weight = [o.total_weight for o in orders]
    order_volume = [o.total_volume for o in orders]
    
    # ... construire autres arrays (agent_type, order_zones, etc.)
    
    # 4. Générer le fichier .dzn
    with open(output_path, 'w') as f:
        f.write(f"% Données pour allocation.mzn\n")
        f.write(f"% Généré automatiquement depuis les fichiers JSON\n\n")
        
        f.write(f"n_orders = {n_orders};\n")
        f.write(f"n_agents = {n_agents};\n\n")
        
        f.write("capacity_weight = [")
        f.write(", ".join(str(w) for w in capacity_weight))
        f.write("];\n\n")
        
        # ... écrire tous les autres paramètres
    
    print(f"✅ Fichier {output_path} généré avec succès")

if __name__ == "__main__":
    generate_allocation_dzn(
        "data/products.json",
        "data/orders.json",
        "data/agents.json",
        "data/warehouse.json"
    )
```

**Utilisation :**

```bash
# Générer le fichier .dzn
python generate_allocation_data.py

# Résoudre avec MiniZinc
minizinc --solver COIN-BC models/allocation.mzn allocation_data.dzn
```

### 📝 Conclusion

**Architecture actuelle** : Python → API MiniZinc (pas de `.dzn`)  
**Architecture recommandée** : Python → Génération `.dzn` → MiniZinc

L'architecture recommandée offre une meilleure séparation des responsabilités et facilite le débogage, même si l'architecture actuelle fonctionne aussi.
