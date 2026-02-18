# Explication de `array[ORDERS, ORDERS] of bool: incompatible;`

## 📋 La ligne en question

Dans le fichier `models/allocation.mzn`, ligne 35, on trouve :

```minizinc
array[ORDERS, ORDERS] of bool: incompatible;
```

Cette ligne déclare une **matrice booléenne** qui encode les incompatibilités entre les commandes.

---

## 🧠 1️⃣ Que signifie exactement cette déclaration ?

Tu déclares :

- **Une matrice booléenne 2D**
- **indexée par** `(commande_i, commande_j)`

**Donc :**
```minizinc
incompatible[i, j] ∈ {true, false}
```

---

## 🎯 2️⃣ Interprétation métier

Elle signifie :

> **La commande `i` est incompatible avec la commande `j`.**

**Si :**
```minizinc
incompatible[2, 5] = true
```

**Alors :**
> La commande 2 et la commande 5 **ne peuvent pas être transportées ensemble**.

**Exemple concret :**
- Commande 2 : Produits chimiques (détergent)
- Commande 5 : Produits alimentaires (fruits)
- **Incompatibilité** : Les produits chimiques ne peuvent pas être transportés avec les produits alimentaires (risque de contamination)

---

## 🧠 3️⃣ Pourquoi une matrice 2D ?

Parce que l'incompatibilité est **une relation entre deux éléments**.

**Ce n'est pas une propriété individuelle.**

**Ce n'est pas :**
```minizinc
order_i incompatible = true  ❌
```

**Mais :**
```minizinc
order_i incompatible avec order_j  ✅
```

**Donc on a besoin de deux indices.**

---

## 🎯 4️⃣ Structure mathématique

**Si :**
```minizinc
ORDERS = 1..4
```

**Alors tu as une matrice :**

|       | 1   | 2   | 3   | 4   |
|-------|-----|-----|-----|-----|
| **1** | F   | T   | F   | F   |
| **2** | T   | F   | F   | T   |
| **3** | F   | F   | F   | F   |
| **4** | F   | T   | F   | F   |

**où :**
```minizinc
incompatible[1, 2] = true
```

**Signification :**
- Commande 1 incompatible avec commande 2 ✅
- Commande 2 incompatible avec commande 1 ✅ (symétrie)
- Commande 2 incompatible avec commande 4 ✅
- Commande 3 compatible avec toutes les autres ✅

---

## 🧠 5️⃣ Propriétés importantes

### 🔹 Symétrie

**En général :**
```minizinc
incompatible[i, j] = incompatible[j, i]
```

**Si 2 est incompatible avec 5, alors 5 est incompatible avec 2.**

**Exemple :**
- Produits chimiques ↔ Produits alimentaires
- La relation est **symétrique** (bidirectionnelle)

### 🔹 Diagonale

**Souvent :**
```minizinc
incompatible[i, i] = false
```

**Une commande n'est pas incompatible avec elle-même.**

**Logique :** Une commande peut toujours être transportée seule.

---

## 🎯 6️⃣ Comment elle est utilisée dans le modèle

Tu as cette contrainte (lignes 76-78) :

```minizinc
constraint forall(order_first in ORDERS, order_second in ORDERS 
    where order_first < order_second /\ incompatible[order_first, order_second]) (
    assignment[order_first] != assignment[order_second] 
    \/ assignment[order_first] == 0 
    \/ assignment[order_second] == 0
);
```

**Ce que ça veut dire :**

> Si deux commandes sont incompatibles, alors elles ne peuvent pas être assignées au même agent, **sauf si l'une des deux n'est pas assignée** (valeur 0).

**Décomposition :**
- `order_first < order_second` : Évite de vérifier deux fois la même paire
- `incompatible[order_first, order_second]` : Vérifie si elles sont incompatibles
- `assignment[order_first] != assignment[order_second]` : Doivent être sur des agents différents
- `\/ assignment[order_first] == 0` : OU la première n'est pas assignée
- `\/ assignment[order_second] == 0` : OU la seconde n'est pas assignée

**Exemple :**
- Commande 1 (chimique) incompatible avec Commande 2 (alimentaire)
- **Solution valide** :
  - Commande 1 → Agent 1, Commande 2 → Agent 2 ✅
  - Commande 1 → Agent 1, Commande 2 → Non assignée (0) ✅
  - Commande 1 → Agent 1, Commande 2 → Agent 1 ❌ (violation)

---

## 🧠 7️⃣ Interprétation logique

C'est une contrainte du type :

```
SI incompatible[i, j] = true
ALORS assignment[i] ≠ assignment[j]
```

**En logique propositionnelle :**
```
incompatible[i, j] → (assignment[i] ≠ assignment[j] ∨ assignment[i] = 0 ∨ assignment[j] = 0)
```

**Équivalent à :**
```
¬ incompatible[i, j] ∨ (assignment[i] ≠ assignment[j] ∨ assignment[i] = 0 ∨ assignment[j] = 0)
```

---

## 🎯 8️⃣ En résumé

| Élément | Signification |
|---------|---------------|
| `array[ORDERS, ORDERS]` | matrice 2D |
| `of bool` | vrai / faux |
| `incompatible[i, j]` | relation entre deux commandes |
| **Utilité** | empêcher co-affectation |

**En une phrase :**
> `incompatible` est une matrice booléenne où `incompatible[i, j] = true` signifie que les commandes `i` et `j` ne peuvent pas être assignées au même agent.

---

## 🔥 9️⃣ Vision plus avancée

Cette matrice définit en réalité :

### 👉 Un graphe d'incompatibilité

- **chaque commande** = un nœud
- **une incompatibilité** = une arête

**Exemple visuel :**

```
Commande 1 (chimique) ──╳── Commande 2 (alimentaire)
         │                    │
         │                    │
Commande 3 (électronique)    Commande 4 (alimentaire)
```

**Où `╳` représente une incompatibilité.**

**Et ton problème devient proche d'un :**

- **problème de coloration de graphe**
- **sous contrainte de capacité**

**Analogie :**
- **Coloration** : Assigner chaque nœud (commande) à une couleur (agent)
- **Contrainte** : Deux nœuds adjacents (incompatibles) ne peuvent pas avoir la même couleur
- **Capacité** : Chaque couleur (agent) a une capacité limitée (poids/volume)

---

## 📊 10️⃣ Exemple complet

**Données :**
- 4 commandes
- 2 agents (R1, H1)
- Incompatibilités :
  - Commande 1 ↔ Commande 2 (chimique vs alimentaire)
  - Commande 2 ↔ Commande 4 (alimentaire vs alimentaire différent)

**Matrice `incompatible` :**

|       | 1   | 2   | 3   | 4   |
|-------|-----|-----|-----|-----|
| **1** | F   | T   | F   | F   |
| **2** | T   | F   | F   | T   |
| **3** | F   | F   | F   | F   |
| **4** | F   | T   | F   | F   |

**Solution possible :**
```minizinc
assignment = [1, 2, 1, 2]
```

**Vérification :**
- Commande 1 (agent 1) ≠ Commande 2 (agent 2) ✅
- Commande 2 (agent 2) ≠ Commande 4 (agent 2) ❌ **VIOLATION !**

**Solution corrigée :**
```minizinc
assignment = [1, 2, 1, 1]  % Commande 4 sur agent 1
```

**Vérification :**
- Commande 1 (agent 1) ≠ Commande 2 (agent 2) ✅
- Commande 2 (agent 2) ≠ Commande 4 (agent 1) ✅

---

## 📝 Références

- **Déclaration** : `models/allocation.mzn` ligne 35
- **Utilisation dans contrainte** : `models/allocation.mzn` lignes 76-78
- **Source des données** : Calculée depuis `products.json` via les incompatibilités entre produits

---

## 🔍 Comment les incompatibilités sont calculées ?

### 📋 Les fichiers JSON : la pièce manquante

Ton `orders.json` est la **pièce manquante** pour construire une matrice `incompatible[order_i, order_j]`.

**Pourquoi ?**

- Le **JSON produit** (`products.json`) te donne : `incompatible_with` (relation **produit ↔ produit**)
- Le **JSON order** (`orders.json`) te donne : quels `product_id` sont dans chaque commande (relation **commande ↔ produits**)

**Donc tu peux déduire une relation commande ↔ commande.**

---

### 🧠 Comment on passe "produit↔produit" à "commande↔commande" ?

**Idée générale :**

Pour deux commandes A et B :

1. **Récupérer l'ensemble des produits de A :**
   ```
   Products(A) = {Product_031, Product_014, Product_050}
   ```

2. **Récupérer l'ensemble des produits de B :**
   ```
   Products(B) = {Product_042, Product_001}
   ```

3. **Dire que A est incompatible avec B si :**
   > Il existe `p ∈ Products(A)` et `q ∈ Products(B)` tels que :
   > - `q` est dans `incompatible_with[p]` **OU**
   > - `p` est dans `incompatible_with[q]` (souvent on symétrise)

4. **➡️ Si oui** ⇒ `incompatible[A, B] = true` et `incompatible[B, A] = true`

---

### 📊 Exemple concret pas à pas

#### Étape 1 : Données JSON

**`products.json` :**
```json
{
  "id": "Product_001",
  "name": "Laptop",
  "incompatible_with": ["Product_042", "Product_043"]
},
{
  "id": "Product_042",
  "name": "Détergent chimique",
  "incompatible_with": ["Product_001", "Product_055"]
}
```

**`orders.json` :**
```json
{
  "id": "Order_001",
  "items": [
    {"product_id": "Product_001", "quantity": 1},
    {"product_id": "Product_002", "quantity": 2}
  ]
},
{
  "id": "Order_002",
  "items": [
    {"product_id": "Product_042", "quantity": 1}
  ]
}
```

#### Étape 2 : Extraire les produits de chaque commande

- **Order_001** → `Products(Order_001) = {Product_001, Product_002}`
- **Order_002** → `Products(Order_002) = {Product_042}`

#### Étape 3 : Vérifier les incompatibilités

**Pour Order_001 et Order_002 :**

- `Product_001` (dans Order_001) a `incompatible_with = ["Product_042", ...]`
- `Product_042` (dans Order_002) est dans cette liste ✅
- **Résultat** : `incompatible[Order_001, Order_002] = true`

**Pour Order_002 et Order_001 :**

- `Product_042` (dans Order_002) a `incompatible_with = ["Product_001", ...]`
- `Product_001` (dans Order_001) est dans cette liste ✅
- **Résultat** : `incompatible[Order_002, Order_001] = true` (symétrie)

---

### 💻 Algorithme Python (pseudo-code)

```python
def build_incompatible_matrix(orders, products_by_id):
    """
    Construit la matrice incompatible[order_i, order_j]
    à partir des incompatibilités entre produits.
    """
    n_orders = len(orders)
    incompatible = [[False] * n_orders for _ in range(n_orders)]
    
    # Pour chaque paire de commandes
    for i in range(n_orders):
        for j in range(i + 1, n_orders):  # Évite les doublons
            order_i = orders[i]
            order_j = orders[j]
            
            # Extraire les produits de chaque commande
            products_i = {item.product_id for item in order_i.items}
            products_j = {item.product_id for item in order_j.items}
            
            # Vérifier s'il existe une incompatibilité
            is_incompatible = False
            for product_id_i in products_i:
                product_i = products_by_id[product_id_i]
                for product_id_j in products_j:
                    # Vérifier si product_j est incompatible avec product_i
                    if product_id_j in product_i.incompatible_with:
                        is_incompatible = True
                        break
                    # Vérifier si product_i est incompatible avec product_j
                    product_j = products_by_id[product_id_j]
                    if product_id_i in product_j.incompatible_with:
                        is_incompatible = True
                        break
                if is_incompatible:
                    break
            
            # Remplir la matrice (symétrique)
            if is_incompatible:
                incompatible[i][j] = True
                incompatible[j][i] = True  # Symétrie
    
    return incompatible
```

---

### 🎯 Résumé du processus

| Étape | Action | Source |
|-------|--------|--------|
| 1. | Lire `products.json` | `incompatible_with` pour chaque produit |
| 2. | Lire `orders.json` | `items` avec `product_id` pour chaque commande |
| 3. | Pour chaque paire (Order_i, Order_j) | Extraire les produits de chaque commande |
| 4. | Vérifier incompatibilité | Si un produit de Order_i est incompatible avec un produit de Order_j |
| 5. | Remplir matrice | `incompatible[i, j] = true` (et `incompatible[j, i] = true`) |

---

### 📝 Références dans le code

- **Construction** : `src/constraints.py` fonction `can_combine()` (lignes 42-46)
- **Utilisation** : `src/allocation_cpsat.py` fonction `_build_incompatible_pairs()` (ligne 57)
- **Données sources** : 
  - `data/products.json` : champ `incompatible_with`
  - `data/orders.json` : champ `items` avec `product_id`
