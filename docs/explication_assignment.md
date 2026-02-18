# Explication de `array[ORDERS] of var 0..n_agents: assignment;`

## 📋 La ligne en question

Dans le fichier `models/allocation.mzn`, ligne 40, on trouve :

```minizinc
array[ORDERS] of var 0..n_agents: assignment;
```

**Cette ligne suffit à elle seule pour déclarer la variable de décision** — mais elle ne suffit pas pour définir le comportement du modèle. On va clarifier ça.

---

## 🧠 1️⃣ Que signifie exactement cette ligne ?

### Décomposons-la :

#### 🔹 `array[ORDERS]`

On crée un **tableau indexé par les commandes**.

**Si :**
```minizinc
ORDERS = 1..5
```

**Alors :**
- `assignment[1]`
- `assignment[2]`
- `assignment[3]`
- `assignment[4]`
- `assignment[5]`

#### 🔹 `of var 0..n_agents`

Chaque case du tableau est :
- **une variable de décision** (`var`)
- dont le **domaine** est `{0, 1, 2, ..., n_agents}`

**Donc :**
```minizinc
assignment[o] ∈ {0..n_agents}
```

---

## 🎯 2️⃣ Interprétation logique

Tu encodes ici :

```
assignment[o] = a
```

**signifie :**
> La commande `o` est assignée à l'agent `a`

**Et :**
```
assignment[o] = 0
```

**signifie :**
> La commande n'est **pas assignée**

**C'est très élégant** 👌  
Tu représentes une relation "commande → agent" avec une seule variable.

---

## 🧠 3️⃣ Est-ce que cette ligne suffit ?

### ✅ Pour déclarer la variable → **OUI**

Elle suffit pour dire :
> Il existe une variable `assignment` pour chaque commande.

### ❌ Pour imposer un comportement → **NON**

**Sans contraintes supplémentaires :**
- MiniZinc peut mettre toutes les commandes à `0`
- ou toutes sur le même agent
- ou n'importe quoi

**C'est l'objectif + les contraintes qui donnent du sens.**

---

## 🎯 4️⃣ Pourquoi c'est puissant ?

Cette ligne encode implicitement :

- ✅ un problème d'**affectation**
- ✅ avec possibilité de **non-affectation** (valeur 0)
- ✅ avec domaine **borné** (0..n_agents)
- ✅ **sans créer de matrice binaire**

**Exemple concret :**

Avec 5 commandes et 3 agents :
```minizinc
assignment = [2, 1, 0, 3, 2]
```

**Interprétation :**
- Commande 1 → Agent 2
- Commande 2 → Agent 1
- Commande 3 → **Non assignée** (0)
- Commande 4 → Agent 3
- Commande 5 → Agent 2

---

## 🧠 5️⃣ Alternative plus classique (moins compacte)

On aurait pu écrire :

```minizinc
array[ORDERS, AGENTS] of var bool: x;
```

**où :**
- `x[o,a] = 1` si `o` est assignée à `a`
- `x[o,a] = 0` sinon

**Mais ta version :**
```minizinc
assignment[o] ∈ 0..n_agents
```

**est beaucoup plus compacte.**

**Comparaison :**

| Approche | Variables | Contraintes supplémentaires |
|----------|-----------|----------------------------|
| **Matrice binaire** `x[o,a]` | `n_orders × n_agents` | Une seule `x[o,a] = 1` par commande |
| **Vecteur compact** `assignment[o]` | `n_orders` | Aucune (déjà encodé) |

**Avec 10 commandes et 6 agents :**
- Matrice : **60 variables**
- Vecteur : **10 variables** ✅

---

## 🎯 6️⃣ Résumé clair

| Élément | Rôle |
|---------|------|
| `array[ORDERS]` | une variable par commande |
| `var` | variable de décision |
| `0..n_agents` | domaine possible |
| `assignment` | nom du tableau |

**En une phrase :**
> `assignment` est un tableau où chaque commande a une variable qui peut prendre une valeur entre 0 (non assignée) et n_agents (assignée à cet agent).

---

## 🔥 7️⃣ Conclusion importante

### 👉 Oui, cette ligne se suffit pour déclarer la variable.

**Mais :**
- ✅ ce sont les **contraintes** qui lui donnent un sens
- ✅ l'**objectif** pousse vers une solution intéressante

**Sans contraintes, le solveur ferait n'importe quoi.**

### Exemple dans `allocation.mzn`

**Déclaration (ligne 40) :**
```minizinc
array[ORDERS] of var 0..n_agents: assignment;
```

**Contraintes (lignes 45-78) :**
```minizinc
% Capacité en poids
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) 
        (order_weight[order_idx]) <= capacity_weight[agent_idx]
);

% Capacité en volume
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) 
        (order_volume[order_idx]) <= capacity_volume[agent_idx]
);

% Restrictions des robots (zones interdites)
% ... etc
```

**Objectif (ligne 85) :**
```minizinc
var int: num_assigned = sum(order_idx in ORDERS) (assignment[order_idx] != 0);
solve maximize num_assigned;
```

**Résultat :**
- Les contraintes garantissent que les capacités sont respectées
- L'objectif maximise le nombre de commandes assignées
- La variable `assignment` encode la solution optimale

---

## 📝 Références

- **Déclaration** : `models/allocation.mzn` ligne 40
- **Utilisation dans contraintes** : `models/allocation.mzn` lignes 45-78
- **Utilisation dans objectif** : `models/allocation.mzn` ligne 85
