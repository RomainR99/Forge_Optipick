# Origine de `order_has_fragile` dans `allocation.mzn`

## 📋 Question

Dans le fichier `models/allocation.mzn`, ligne 31, on trouve :

```minizinc
array[ORDERS] of bool: order_has_fragile;
```

**D'où vient cette valeur `order_has_fragile` ?**

## 🔄 Flux complet des données

### 1. Source initiale : Fichier JSON `products.json`

Chaque produit dans `products.json` a un champ `fragile` (booléen) :

```json
{
  "id": "Product_001",
  "name": "Laptop Dell XPS 15",
  "category": "electronics",
  "weight": 2.5,
  "volume": 8,
  "location": [1, 0],
  "frequency": "high",
  "fragile": true,  ← Champ fragile pour ce produit
  "incompatible_with": [...]
},
{
  "id": "Product_002",
  "name": "Câble USB-C",
  "category": "electronics",
  "weight": 0.1,
  "volume": 0.5,
  "location": [2, 0],
  "frequency": "very_high",
  "fragile": false,  ← Ce produit n'est pas fragile
  "incompatible_with": []
}
```

### 2. Chargement dans Python : `loader.py`

Le fichier `src/loader.py` lit le JSON et crée des objets Python `Product` :

```python
def parse_products(data: list) -> Dict[str, Product]:
    """Parse les données JSON des produits."""
    products: Dict[str, Product] = {}
    for product_data in data:
        products[product_id] = Product(
            id=product_id,
            name=product_data.get("name", product_id),
            category=product_data.get("category", "unknown"),
            weight=float(product_data.get("weight", 0.0)),
            volume=float(product_data.get("volume", 0.0)),
            location=Location(location_coords[0], location_coords[1]),
            frequency=product_data.get("frequency", "unknown"),
            fragile=bool(product_data.get("fragile", False)),  # ← Chargé depuis JSON
            incompatible_with=list(product_data.get("incompatible_with", [])),
        )
    return products
```

**Résultat** : Chaque objet `Product` a un attribut `fragile` (ex. `product.fragile = True`)

### 3. Calcul de `order_has_fragile` : Code Python

Pour chaque commande, on vérifie si **au moins un produit** dans la commande a `fragile = true` :

```python
def build_order_has_fragile(orders: List[Order], products_by_id: Dict[str, Product]) -> List[bool]:
    """
    Construit le tableau order_has_fragile pour MiniZinc.
    
    Args:
        orders: Liste des commandes
        products_by_id: Dictionnaire des produits par ID
    
    Returns:
        Liste de booléens : True si la commande contient au moins un produit fragile
    """
    order_has_fragile = []
    
    for order in orders:
        has_fragile = False
        
        # Parcourir tous les items de la commande
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product and product.fragile:  # ← Vérifier si le produit est fragile
                has_fragile = True
                break  # On peut s'arrêter dès qu'on trouve un fragile
        
        order_has_fragile.append(has_fragile)
    
    return order_has_fragile
```

**Logique** : Une commande contient du fragile si **au moins un** de ses produits a `fragile = true`.

### 4. Passage à MiniZinc : `minizinc_solver.py`

Le code Python qui appelle MiniZinc passe ce tableau au modèle :

```python
from minizinc import Instance, Model, Solver

def allocate_with_minizinc(orders, agents, products, warehouse, solver_name):
    # Construire order_has_fragile
    products_by_id = {p.id: p for p in products}
    order_has_fragile = build_order_has_fragile(orders, products_by_id)
    
    # Charger le modèle
    model = Model("models/allocation.mzn")
    instance = Instance(solver, model)
    
    # Passer order_has_fragile à MiniZinc
    instance["order_has_fragile"] = order_has_fragile
    
    # Résoudre
    result = instance.solve()
    ...
```

### 5. Utilisation dans MiniZinc : `allocation.mzn`

MiniZinc reçoit le tableau et l'utilise dans les contraintes :

```minizinc
% Déclaration du paramètre (ligne 31)
array[ORDERS] of bool: order_has_fragile;

% Utilisation dans la contrainte (lignes 66-70)
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ no_fragile[agent_idx]) ->
    (not order_has_fragile[order_idx])
);
```

## 📊 Exemple concret

### Données JSON

**`products.json` :**
```json
[
  {"id": "Product_001", "fragile": true},
  {"id": "Product_002", "fragile": false},
  {"id": "Product_003", "fragile": true}
]
```

**`orders.json` :**
```json
[
  {
    "id": "Order_001",
    "items": [
      {"product_id": "Product_001", "quantity": 1},  // fragile = true
      {"product_id": "Product_002", "quantity": 2}   // fragile = false
    ]
  },
  {
    "id": "Order_002",
    "items": [
      {"product_id": "Product_002", "quantity": 1}   // fragile = false
    ]
  },
  {
    "id": "Order_003",
    "items": [
      {"product_id": "Product_003", "quantity": 1}   // fragile = true
    ]
  }
]
```

### Calcul en Python

**Pour Order_001 :**
- Item 1 : `Product_001` → `product.fragile = True` ✅
- Item 2 : `Product_002` → `product.fragile = False`
- **Résultat** : `order_has_fragile[0] = True` (au moins un produit fragile)

**Pour Order_002 :**
- Item 1 : `Product_002` → `product.fragile = False`
- **Résultat** : `order_has_fragile[1] = False` (aucun produit fragile)

**Pour Order_003 :**
- Item 1 : `Product_003` → `product.fragile = True` ✅
- **Résultat** : `order_has_fragile[2] = True` (au moins un produit fragile)

**Tableau final :**
```python
order_has_fragile = [True, False, True]
```

### Passage à MiniZinc

```python
instance["order_has_fragile"] = [True, False, True]
```

MiniZinc reçoit :
- `order_has_fragile[1] = True` (Order_001 contient du fragile)
- `order_has_fragile[2] = False` (Order_002 ne contient pas de fragile)
- `order_has_fragile[3] = True` (Order_003 contient du fragile)

## ✅ Résumé

| Étape | Fichier | Action |
|-------|---------|--------|
| 1. Source | `data/products.json` | Champ `fragile` (booléen) pour chaque produit |
| 2. Chargement | `src/loader.py` | Création d'objets `Product` avec `product.fragile` |
| 3. Calcul | Code Python (fonction `build_order_has_fragile`) | Pour chaque commande : vérifier si au moins un produit a `fragile = true` |
| 4. Extraction | `src/minizinc_solver.py` | Liste Python : `[True, False, True, ...]` |
| 5. Passage | `src/minizinc_solver.py` | `instance["order_has_fragile"] = [...]` |
| 6. Utilisation | `models/allocation.mzn` | Paramètre utilisé dans la contrainte ligne 69 |

## 🔍 Formule de calcul

```
order_has_fragile[order_idx] = ∃ (produit dans order.items) tel que produit.fragile == true
```

**En Python :**
```python
order_has_fragile[order_idx] = any(
    products_by_id[item.product_id].fragile 
    for item in order.items 
    if item.product_id in products_by_id
)
```

## 📝 Références

- **Déclaration** : `models/allocation.mzn` ligne 31
- **Utilisation** : `models/allocation.mzn` ligne 69
- **Source** : `data/products.json` champ `fragile`
- **Chargement** : `src/loader.py` ligne 58
- **Documentation** : `docs/rapport_day4.md` ligne 101, `docs/rapport_day2bis.md` ligne 522
