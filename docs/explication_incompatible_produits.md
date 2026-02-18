# Explication : contrainte « incompatibilités entre produits »

## 📋 La contrainte dans `allocation.mzn`

Dans le fichier `models/allocation.mzn`, la contrainte sur les incompatibilités (lignes 78-82) est :

```minizinc
% 6. Incompatibilités entre produits
% Si deux commandes sont incompatibles, elles ne peuvent pas être assignées au même agent
constraint forall(order_first in ORDERS, order_second in ORDERS where order_first < order_second /\ incompatible[order_first, order_second]) (
    assignment[order_first] != assignment[order_second] \/ assignment[order_first] == 0 \/ assignment[order_second] == 0
);
```

**En français :** Si deux commandes sont incompatibles, elles ne peuvent pas être assignées au même agent (sauf si l'une des deux n'est pas assignée).

---

## Rappel : la matrice `incompatible`

```minizinc
array[ORDERS, ORDERS] of bool: incompatible;
```

**`incompatible`** est un **booléen** : pour chaque paire (order_i, order_j), `incompatible[i, j]` vaut `true` ou `false`.

- **`incompatible[order_first, order_second] = true`** → les deux commandes sont incompatibles (ne doivent pas être sur le même agent).

---

## Étape 1 — Le `forall`

```minizinc
forall(order_first in ORDERS, order_second in ORDERS 
    where order_first < order_second /\ incompatible[order_first, order_second])
```

On parcourt **toutes les paires de commandes** :

- **`order_first`** : première commande de la paire  
- **`order_second`** : deuxième commande de la paire  

**Mais seulement si :**

1. **`order_first < order_second`**  
   → Pour éviter de vérifier deux fois la même paire (ex. (1,2) et (2,1)).

2. **`incompatible[order_first, order_second]` est vrai**  
   → Donc uniquement les paires **réellement incompatibles**.

---

## Étape 2 — La contrainte logique

```minizinc
assignment[order_first] != assignment[order_second] 
\/ assignment[order_first] == 0 
\/ assignment[order_second] == 0
```

C'est un **OU logique** (`\/`).

**Signification :** Au moins **une** des conditions suivantes doit être vraie :

1. **Les deux commandes ne sont pas assignées au même agent**  
   `assignment[order_first] != assignment[order_second]`

2. **La première commande n'est pas assignée**  
   `assignment[order_first] == 0`

3. **La deuxième commande n'est pas assignée**  
   `assignment[order_second] == 0`

Si les deux commandes sont incompatibles et toutes les deux assignées, alors elles **ne doivent pas** être sur le même agent (condition 1 doit être vraie).

---

## Où et comment on parcourt toutes les paires

Regardons précisément :

```minizinc
forall(order_first in ORDERS, order_second in ORDERS 
       where order_first < order_second /\ incompatible[order_first, order_second])
```

### 1️⃣ Où se fait le parcours ?

**Dans le `forall`.**

`forall(...)` signifie : **pour toutes les valeurs possibles** des variables entre parenthèses (en ne gardant que celles qui satisfont le `where`).

### 2️⃣ Comment MiniZinc parcourt ?

```minizinc
order_first in ORDERS,
order_second in ORDERS
```

C'est équivalent à une **double boucle** :

```python
for order_first in ORDERS:
    for order_second in ORDERS:
        ...
```

MiniZinc génère donc **toutes les combinaisons** (order_first, order_second).

### 3️⃣ Exemple concret

**Si :**
```minizinc
ORDERS = {1, 2, 3}
```

**Alors MiniZinc génère d'abord toutes les paires :**

| order_first | order_second |
|-------------|--------------|
| 1           | 1            |
| 1           | 2            |
| 1           | 3            |
| 2           | 1            |
| 2           | 2            |
| 2           | 3            |
| 3           | 1            |
| 3           | 2            |
| 3           | 3            |

Soit : **(1,1), (1,2), (1,3), (2,1), (2,2), (2,3), (3,1), (3,2), (3,3)**.

### 4️⃣ Pourquoi `where order_first < order_second` ?

Pour ne garder que les **paires différentes, sans doublon**.

**Avec** `order_first < order_second`, on garde **seulement** :

- (1, 2)  
- (1, 3)  
- (2, 3)  

**On élimine :**

- (2, 1) — doublon de (1, 2)  
- (3, 1) — doublon de (1, 3)  
- (3, 2) — doublon de (2, 3)  
- (1, 1), (2, 2), (3, 3) — comparaison avec soi-même  

**Effet :**

- Pas de doublons  
- Pas de comparaison d'une commande avec elle-même  

### 5️⃣ Et `/\ incompatible[order_first, order_second]` ?

MiniZinc ne garde que les paires qui vérifient **en plus** :

- **`order_first < order_second`**  
- **ET** **`incompatible[order_first, order_second]`** = true  

Donc on ne traite que :

- Les paires **différentes**  
- **Et** **réellement incompatibles**  

---

## Résumé du flux

| Étape | Action |
|-------|--------|
| 1 | Générer toutes les paires (order_first, order_second) avec la double boucle |
| 2 | Filtrer avec `order_first < order_second` → pas de doublons, pas de (i, i) |
| 3 | Filtrer avec `incompatible[order_first, order_second]` → seulement les paires incompatibles |
| 4 | Pour chaque paire restante, imposer : pas même agent OU l'une des deux non assignée |

---

## Exemple complet

**Données :**

- ORDERS = {1, 2, 3}  
- Incompatibilités : (1,2) et (2,3) incompatibles → `incompatible[1,2]=true`, `incompatible[2,3]=true`  

**Paires concernées par la contrainte :**

- (1, 2) : `order_first=1 < order_second=2` et `incompatible[1,2]=true` ✅  
- (2, 3) : `order_first=2 < order_second=3` et `incompatible[2,3]=true` ✅  
- (1, 3) : si `incompatible[1,3]=false` → paire ignorée  

**Contrainte pour (1, 2) :**  
Il faut :  
`assignment[1] != assignment[2]` **ou** `assignment[1] == 0` **ou** `assignment[2] == 0`.  

**Exemple de violation :**  
`assignment = [1, 1, 2]` → commandes 1 et 2 sur l'agent 1 alors qu'elles sont incompatibles ❌  

**Exemple de solution valide :**  
`assignment = [1, 2, 2]` → commandes 1 et 2 sur des agents différents ✅  

---

## Références

- **Contrainte** : `models/allocation.mzn` lignes 78-82  
- **Déclaration de `incompatible`** : `models/allocation.mzn` ligne 35  
- **Origine de la matrice `incompatible`** : `docs/explication_incompatible.md` (construction depuis `orders.json` et `products.json`)
