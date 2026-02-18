# Origine de `order_weight` dans `allocation.mzn`

## 📋 Question

Dans le fichier `models/allocation.mzn`, ligne 16, on trouve :
```minizinc
array[ORDERS] of float: order_weight;
```

**D'où vient cette valeur `order_weight` ?**

## 🔄 Flux complet des données

### 1. Source initiale : Fichiers JSON

Les valeurs `order_weight` sont **calculées** à partir de deux fichiers JSON :

#### a) `data/orders.json` - Liste des commandes avec leurs items
```json
[
  {
    "id": "Order_001",
    "received_time": "08:00",
    "deadline": "11:32",
    "priority": "standard",
    "items": [
      {"product_id": "Product_026", "quantity": 1},
      {"product_id": "Product_035", "quantity": 3}
    ]
  }
]
```

#### b) `data/products.json` - Informations sur les produits (poids, volume)
```json
[
  {
    "id": "Product_026",
    "name": "Laptop",
    "weight": 2.5,
    "volume": 8,
    ...
  },
  {
    "id": "Product_035",
    "name": "USB Cable",
    "weight": 0.1,
    "volume": 0.5,
    ...
  }
]
```

### 2. Chargement dans Python : `loader.py`

Le fichier `src/loader.py` lit les JSON et crée des objets Python :

```python
# Chargement des produits
def parse_products(data: list) -> Dict[str, Product]:
    products: Dict[str, Product] = {}
    for product_data in data:
        products[product_id] = Product(
            id=product_id,
            weight=float(product_data.get("weight", 0.0)),  # ← Poids du produit
            volume=float(product_data.get("volume", 0.0)),
            ...
        )
    return products

# Chargement des commandes
def parse_orders(data: list) -> List[Order]:
    orders = []
    for order_data in data:
        items = [OrderItem(product_id=item["product_id"], 
                          quantity=item["quantity"]) 
                for item in order_data["items"]]
        orders.append(Order(
            id=order_data["id"],
            items=items,  # ← Liste des items (product_id + quantity)
            ...
        ))
    return orders
```

**Résultat** : 
- Objets `Product` avec `product.weight` (ex. `Product_026.weight = 2.5`)
- Objets `Order` avec `order.items` (liste de `OrderItem`)

### 3. Calcul du poids total : `_enrich_orders()`

Le poids total d'une commande est **calculé** en multipliant le poids de chaque produit par sa quantité :

```python
def _enrich_orders(orders: List[Order], products_by_id: Dict[str, Product]) -> None:
    """Calcule total_weight et total_volume pour chaque commande."""
    for order in orders:
        total_w = 0.0
        total_v = 0.0
        for item in order.items:
            product = products_by_id.get(item.product_id)
            if product:
                total_w += product.weight * item.quantity  # ← Calcul du poids
                total_v += product.volume * item.quantity
        order.total_weight = total_w  # ← Stocké dans l'objet Order
        order.total_volume = total_v
```

**Exemple de calcul** :
- Order_001 avec items :
  - `Product_026` × 1 → `2.5 × 1 = 2.5 kg`
  - `Product_035` × 3 → `0.1 × 3 = 0.3 kg`
- **Total** : `order.total_weight = 2.5 + 0.3 = 2.8 kg`

### 4. Passage à MiniZinc : `minizinc_solver.py`

Le code Python qui appelle MiniZinc extrait `total_weight` depuis chaque objet `Order` et le passe au modèle :

```python
from minizinc import Instance, Model, Solver

def allocate_with_minizinc(orders, agents, products, warehouse, solver_name):
    # Enrichir les commandes (calculer total_weight)
    _enrich_orders(orders, products_by_id)
    
    # Charger le modèle
    model = Model("models/allocation.mzn")
    instance = Instance(solver, model)
    
    # Extraire order_weight de chaque commande
    order_weight = [order.total_weight for order in orders]
    # Exemple : [2.8, 1.5, 5.2, 3.1, ...]
    
    # Passer la valeur à MiniZinc
    instance["order_weight"] = order_weight
    
    # Résoudre
    result = instance.solve()
    ...
```

### 5. Utilisation dans MiniZinc : `allocation.mzn`

MiniZinc reçoit le tableau et l'utilise dans les contraintes :

```minizinc
% Déclaration du paramètre (ligne 16)
array[ORDERS] of float: order_weight;

% Utilisation dans la contrainte (ligne 45-47)
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) 
        (order_weight[order_idx]) <= capacity_weight[agent_idx]
);
```

## 📊 Exemple concret

Supposons 2 commandes :

**Order_001** :
- Item 1 : `Product_026` (weight=2.5) × quantity=1 → `2.5 kg`
- Item 2 : `Product_035` (weight=0.1) × quantity=3 → `0.3 kg`
- **Total** : `order.total_weight = 2.8 kg`

**Order_002** :
- Item 1 : `Product_089` (weight=0.5) × quantity=3 → `1.5 kg`
- **Total** : `order.total_weight = 1.5 kg`

**Flux :**

1. **JSON** → 
   - `orders.json` : `{"items": [{"product_id": "Product_026", "quantity": 1}, ...]}`
   - `products.json` : `{"id": "Product_026", "weight": 2.5, ...}`

2. **Python (loader.py)** → 
   - `order1.items = [OrderItem(product_id="Product_026", quantity=1), ...]`
   - `product_026.weight = 2.5`

3. **Python (_enrich_orders)** → 
   - `order1.total_weight = 2.5 * 1 + 0.1 * 3 = 2.8`
   - `order2.total_weight = 0.5 * 3 = 1.5`

4. **Python (minizinc_solver.py)** → 
   - `order_weight = [2.8, 1.5]` puis `instance["order_weight"] = [2.8, 1.5]`

5. **MiniZinc** → Reçoit `order_weight = [2.8, 1.5]` et utilise :
   - `order_weight[1] = 2.8` (Order_001)
   - `order_weight[2] = 1.5` (Order_002)

## ✅ Résumé

| Étape | Fichier | Action |
|-------|---------|--------|
| 1. Source | `data/orders.json` + `data/products.json` | Items de commandes + poids des produits |
| 2. Chargement | `src/loader.py` | Création d'objets `Order` et `Product` |
| 3. Calcul | `_enrich_orders()` (dans `day5_simulation.py` ou similaire) | `total_weight = Σ(product.weight × quantity)` |
| 4. Extraction | `src/minizinc_solver.py` | Liste Python : `[order.total_weight for order in orders]` |
| 5. Passage | `src/minizinc_solver.py` | `instance["order_weight"] = [...]` |
| 6. Utilisation | `models/allocation.mzn` | Paramètre utilisé dans les contraintes |

## 🔍 Formule de calcul

```
order_weight[order_idx] = Σ (product.weight × item.quantity)
                          pour chaque item dans order.items
```

**Où** :
- `product.weight` vient de `products.json`
- `item.quantity` vient de `orders.json`

## 📝 Références

- **Déclaration** : `models/allocation.mzn` ligne 16
- **Utilisation** : `models/allocation.mzn` ligne 46
- **Calcul** : `src/day5_simulation.py` fonction `_enrich_orders()` lignes 40-57
- **Chargement** : `src/loader.py` fonctions `parse_orders()` et `parse_products()`
- **Documentation** : `docs/rapport_day4.md` ligne 100
