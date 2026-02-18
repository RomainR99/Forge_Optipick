# Explication de la contrainte de capacité en poids

## 📋 La contrainte dans `allocation.mzn`

Dans le fichier `models/allocation.mzn`, la contrainte de capacité en poids (lignes 45-47) est :

```minizinc
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) (order_weight[order_idx]) <= capacity_weight[agent_idx]
);
```

**En français :** Pour chaque agent, la somme des poids des commandes qui lui sont assignées ne doit pas dépasser sa capacité en poids.

---

## 🎯 Exemple concret

### Données

Supposons :

- **ORDERS** = {1, 2, 3}
- **AGENTS** = {1, 2}

**Poids des commandes :**
```minizinc
order_weight = [5, 8, 4]
```
- Commande 1 → 5 kg  
- Commande 2 → 8 kg  
- Commande 3 → 4 kg  

**Affectation :**
```minizinc
assignment = [1, 2, 1]
```
- Commande 1 → Agent 1  
- Commande 2 → Agent 2  
- Commande 3 → Agent 1  

---

### 🔹 Pour l’agent 1

**Commandes assignées :**
- Commande 1 (poids 5)
- Commande 3 (poids 4)

**Somme :** 5 + 4 = **9**

**Vérification :**
```minizinc
9 <= capacity_weight[1]
```
Si `capacity_weight[1] = 12`, alors **9 ≤ 12** ✔

---

### 🔹 Pour l’agent 2

**Commande assignée :**
- Commande 2 (poids 8)

**Somme :** **8**

**Vérification :**
```minizinc
8 <= capacity_weight[2]
```
Si `capacity_weight[2] = 10`, alors **8 ≤ 10** ✔

---

## 🧠 Ce que MiniZinc fait en interne

L’écriture avec **`where`** :

```minizinc
sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) (order_weight[order_idx])
```

est équivalente à :

```minizinc
sum(order_idx in ORDERS)(
    bool2int(assignment[order_idx] == agent_idx)
    * order_weight[order_idx]
)
```

**Explication :**
- `bool2int(condition)` vaut 1 si la condition est vraie, 0 sinon.
- On ne compte donc que le poids des commandes dont `assignment[order_idx] == agent_idx`.

La version avec **`where`** est plus lisible : on somme uniquement les commandes assignées à l’agent considéré.

---

## 📊 Exemple simple pas à pas

**Données :**
- **ORDERS** = {1, 2, 3}
- **assignment** = [1, 2, 1]

**Pour `agent_idx = 1` :**

La condition `assignment[order_idx] == 1` est vraie pour :
- **order 1** (assignment[1] = 1)
- **order 3** (assignment[3] = 1)

Donc la somme devient :
```minizinc
order_weight[1] + order_weight[3]
```

Avec `order_weight = [5, 8, 4]` :
- `order_weight[1]` = 5  
- `order_weight[3]` = 4  
- **Somme = 5 + 4 = 9**

---

## ✅ Exemple concret complet

**Données :**
- `order_weight = [5, 8, 4]`
- `assignment = [1, 2, 1]`
- `capacity_weight[1] = 12`

**Pour l’agent 1 :**

- **Commandes assignées :** commande 1 (poids 5), commande 3 (poids 4).
- **Poids total :** 5 + 4 = **9**
- **Vérification :** 9 ≤ 12 ✔

La contrainte est satisfaite pour l’agent 1.

---

## 📝 Résumé

| Élément | Rôle |
|--------|------|
| `forall(agent_idx in AGENTS)` | On vérifie la contrainte pour chaque agent |
| `sum(... where assignment[order_idx] == agent_idx)` | Somme des poids des commandes assignées à cet agent |
| `order_weight[order_idx]` | Poids de la commande `order_idx` |
| `<= capacity_weight[agent_idx]` | Le total ne doit pas dépasser la capacité de l’agent |

**En une phrase :** Pour chaque agent, le poids total des commandes qui lui sont affectées ne doit pas dépasser sa capacité (`capacity_weight`).

---

## 📌 Référence

- **Contrainte** : `models/allocation.mzn` lignes 45-47  
- **Paramètres** : `order_weight` (voir `docs/origine_order_weight.md`), `capacity_weight` (voir `docs/origine_capacity_weight.md`)
