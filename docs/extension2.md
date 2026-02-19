# Extension 2 : Gestion Dynamique avec Commandes Express Prioritaires

## 📋 Vue d'ensemble

L'**Extension 2** ajoute la capacité de gérer des commandes qui arrivent en temps réel et de prioriser les commandes express lors de la ré-optimisation.

### Contexte opérationnel

Dans un entrepôt réel, les commandes n'arrivent pas toutes en même temps au début de la journée. Elles arrivent progressivement :

- **Initialement** : 10 commandes à traiter
- **Toutes les heures** : 5 nouvelles commandes arrivent
- **Ré-optimisation** : À chaque arrivée de nouvelles commandes, il faut ré-optimiser l'allocation
- **Priorité express** : Les commandes express doivent être traitées en priorité

---

## 🎯 Objectifs de l'extension

1. **Identifier les commandes express** : Marquer certaines commandes comme prioritaires
2. **Prioriser lors de l'optimisation** : Maximiser d'abord les commandes express assignées, puis le total
3. **Ré-optimisation dynamique** : Permettre de ré-exécuter le modèle avec de nouvelles commandes

---

## 🔧 Implémentation dans `allocation.mzn`

### 1️⃣ Nouveau paramètre : `order_is_express`

```minizinc
% EXTENSION 2 : Gestion dynamique - Commandes express prioritaires
array[ORDERS] of bool: order_is_express;  % true si la commande est express (prioritaire)
```

**Rôle** : Tableau booléen indiquant pour chaque commande si elle est express (prioritaire) ou standard.

**Exemple** :
```minizinc
order_is_express = [true, false, true, false, false, true, false, false, false, false];
```
- Commande 1 : express ✅
- Commande 2 : standard
- Commande 3 : express ✅
- Commande 4 : standard
- ...

---

### 2️⃣ Variables de comptage

```minizinc
var int: num_express_assigned = sum(order_idx in ORDERS where order_is_express[order_idx]) 
    (assignment[order_idx] != 0);
var int: num_assigned = sum(order_idx in ORDERS) (assignment[order_idx] != 0);
```

**`num_express_assigned`** : Nombre de commandes express qui ont été assignées à un agent.

**`num_assigned`** : Nombre total de commandes assignées (express + standard).

**Calcul** :
- Pour `num_express_assigned` : on somme uniquement les commandes express (`where order_is_express[order_idx]`) qui sont assignées (`assignment[order_idx] != 0`)
- Pour `num_assigned` : on somme toutes les commandes assignées

---

### 3️⃣ Objectif pondéré

```minizinc
var int: weighted_objective = 1000 * num_express_assigned + num_assigned;
solve maximize weighted_objective;
```

**Stratégie de priorisation** : Utilisation d'un objectif pondéré avec un coefficient élevé (1000) pour les commandes express.

**Pourquoi 1000 ?**

Le coefficient 1000 garantit que **toutes les commandes express possibles seront assignées avant toute commande standard**, même si cela signifie assigner moins de commandes au total.

**Exemple concret** :

Scénario A : 2 express assignées + 8 standard = 2×1000 + 10 = **2010 points**

Scénario B : 1 express assignée + 9 standard = 1×1000 + 10 = **1010 points**

Scénario C : 3 express assignées + 5 standard = 3×1000 + 8 = **3008 points** ✅ **MEILLEUR**

Le solveur choisira toujours le scénario C car il maximise l'objectif pondéré.

**Propriété mathématique** :

Avec `n_orders` commandes au maximum, le nombre total de commandes assignées ne peut jamais dépasser `n_orders`. Donc :

- Si on assigne toutes les express possibles : `num_express_assigned × 1000 + num_assigned`
- Si on assigne une express de moins : `(num_express_assigned - 1) × 1000 + (num_assigned + 1)`

La différence est : `-1000 + 1 = -999` (perte nette)

**Conclusion** : Le coefficient 1000 garantit que le solveur préférera toujours assigner une express de plus, même au détriment de plusieurs commandes standard.

---

## 📊 Exemple d'utilisation

### Données d'entrée

```minizinc
n_orders = 10;
n_agents = 3;

% 4 commandes express sur 10
order_is_express = [true, false, true, false, false, true, true, false, false, false];

% Capacités des agents
capacity_weight = [20.0, 35.0, 50.0];
capacity_volume = [30.0, 50.0, 80.0];
```

### Résultat attendu

Le solveur va :
1. **D'abord** essayer d'assigner les 4 commandes express (indices 1, 3, 6, 7)
2. **Ensuite** assigner les 6 commandes standard restantes si possible
3. **Prioriser** les express même si cela signifie laisser des standard non assignées

### Sortie

```
assignment = [2, 1, 3, 0, 1, 2, 3, 0, 0, 1];
num_assigned = 6;
num_express_assigned = 4;
weighted_objective = 4006;
```

**Interprétation** :
- ✅ **4 express assignées** (commandes 1, 3, 6, 7)
- ✅ **2 standard assignées** (commandes 2, 5)
- ❌ **4 standard non assignées** (commandes 4, 8, 9, 10)

**Score** : 4×1000 + 6 = 4006 points

---

## 🔄 Ré-optimisation dynamique

### Scénario : Nouvelles commandes arrivent

**Heure 0** : 10 commandes initiales
- 4 express, 6 standard
- Optimisation → 4 express + 2 standard assignées

**Heure 1** : 5 nouvelles commandes arrivent
- 2 express, 3 standard
- **Total** : 15 commandes (6 express, 9 standard)

**Ré-optimisation** :
1. Prendre en compte les **15 commandes** (anciennes + nouvelles)
2. Réassigner si nécessaire pour maximiser les express
3. Les commandes déjà en cours de traitement peuvent être "gelées" (contrainte supplémentaire)

### Implémentation dans le code Python

Pour gérer la ré-optimisation, le code Python doit :

```python
# 1. Charger les commandes existantes + nouvelles
all_orders = existing_orders + new_orders

# 2. Marquer les express
order_is_express = [order.priority == "express" for order in all_orders]

# 3. Optionnel : geler les commandes déjà assignées et en cours
# (nécessite une contrainte supplémentaire dans le modèle)

# 4. Ré-exécuter le solveur MiniZinc
solution = solve_allocation(all_orders, agents, order_is_express)
```

---

## 🎯 Avantages de cette approche

### ✅ Simplicité

- Un seul paramètre booléen par commande
- Pas de contraintes supplémentaires complexes
- Objectif pondéré facile à comprendre

### ✅ Garantie de priorité

- Les express sont **toujours** prioritaires grâce au coefficient 1000
- Même si cela signifie assigner moins de commandes au total

### ✅ Flexibilité

- Facile d'ajouter/supprimer des commandes express
- Compatible avec la ré-optimisation dynamique
- Peut être combiné avec d'autres extensions

---

## 🔍 Comparaison avec d'autres approches

### Approche alternative 1 : Objectif lexicographique

```minizinc
% Maximiser d'abord express, puis total
solve 
    :: seq_search([
        int_search(assignment, input_order, indomain_min),
        maximize(num_express_assigned),
        maximize(num_assigned)
    ]);
```

**Avantage** : Plus explicite sur les priorités  
**Inconvénient** : Plus complexe, nécessite des annotations de recherche

### Approche alternative 2 : Contrainte de priorité

```minizinc
% Forcer toutes les express à être assignées avant les standard
constraint forall(order_express in ORDERS where order_is_express[order_express],
                  order_std in ORDERS where not order_is_express[order_std]) (
    assignment[order_express] != 0 \/ assignment[order_std] == 0
);
```

**Avantage** : Contrainte dure garantissant la priorité  
**Inconvénient** : Peut rendre le problème infaisable si trop d'express

### ✅ Notre approche : Objectif pondéré

**Avantage** : 
- Simple et efficace
- Garantit la priorité sans rendre le problème infaisable
- Si toutes les express ne peuvent pas être assignées, on maximise quand même celles qui le peuvent

---

## 📝 Résumé

| Élément | Description |
|---------|-------------|
| **Paramètre** | `array[ORDERS] of bool: order_is_express` |
| **Variables** | `num_express_assigned`, `num_assigned`, `weighted_objective` |
| **Objectif** | `maximize (1000 * num_express_assigned + num_assigned)` |
| **Priorité** | Garantie par le coefficient 1000 |
| **Ré-optimisation** | Ré-exécuter le modèle avec nouvelles commandes |

---

## 🔗 Références

- **Modèle** : `models/allocation.mzn` (lignes 34-37, 108-112)
- **Documentation** : `docs/explication_assignment.md` (structure générale du modèle)
- **Énoncé** : `ENONCE_PROJET_OPTIPICK.txt` (section Extension 2)

---

## 💡 Notes pour l'implémentation Python

Pour utiliser cette extension dans le code Python :

1. **Ajouter le paramètre** lors de la génération du fichier `.dzn` :
   ```python
   order_is_express = [order.priority == "express" for order in orders]
   ```

2. **Parser la sortie** pour récupérer `num_express_assigned` :
   ```python
   # Dans la sortie MiniZinc
   num_express_assigned = ...  # Valeur extraite
   ```

3. **Ré-optimisation** : Ré-exécuter le solveur à chaque arrivée de nouvelles commandes

4. **Gestion des commandes en cours** : Optionnellement, ajouter une contrainte pour "geler" les commandes déjà assignées et en cours de traitement

---

## 🎓 Conclusion

L'Extension 2 permet de gérer efficacement les commandes express prioritaires dans un contexte de ré-optimisation dynamique. L'approche par objectif pondéré est simple, efficace et garantit que les commandes express sont toujours traitées en priorité, même dans des situations de capacité limitée.
