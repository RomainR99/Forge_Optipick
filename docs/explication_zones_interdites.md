# Explication : contrainte « zones interdites »

## 📋 La contrainte dans `allocation.mzn`

Dans le fichier `models/allocation.mzn`, la contrainte sur les zones interdites (lignes 61-63) est :

```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ order_zones[order_idx] >= 0 /\ order_zones[order_idx] < n_zones) ->
    (not forbidden_zones[agent_idx, order_zones[order_idx]])
);
```

**En français :** Pour chaque commande et chaque agent, si la commande est assignée à un robot et que la zone de la commande est valide, alors cette zone ne doit pas faire partie des zones interdites pour ce robot.

---

## 🧠 Structure logique : implication

La contrainte a la forme :

**(A ∧ B ∧ C) → D**

Où :
- **A** : `assignment[order_idx] == agent_idx` (la commande est assignée à cet agent)
- **B** : `agent_type[agent_idx] == 0` (l’agent est un robot)
- **C** : `order_zones[order_idx] >= 0 /\ order_zones[order_idx] < n_zones` (la zone de la commande est valide)
- **D** : `not forbidden_zones[agent_idx, order_zones[order_idx]]` (cette zone n’est pas interdite pour ce robot)

**Signification de l’implication `→` :**

- **Si A, B et C sont vrais** → alors **D doit être vrai**.
- **Sinon** (si au moins une des conditions A, B ou C est fausse) → on **ne force rien** sur D.

---

## 🔄 Deux boucles imbriquées

**Rappel :** La contrainte utilise deux boucles imbriquées :

```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    ...
);
```

**Signification :**
- **Boucle externe** : `order_idx in ORDERS` → Pour chaque commande
- **Boucle interne** : `agent_idx in AGENTS` → Pour chaque agent

**Résultat :** La contrainte est vérifiée pour **chaque paire** (commande, agent).

**Exemple :** Avec 3 commandes et 2 agents, la contrainte est vérifiée **6 fois** :
- (Order_1, Agent_1)
- (Order_1, Agent_2)
- (Order_2, Agent_1)
- (Order_2, Agent_2)
- (Order_3, Agent_1)
- (Order_3, Agent_2)

---

## 📊 La matrice `forbidden_zones`

### Déclaration

```minizinc
array[AGENTS, ZONES] of bool: forbidden_zones;
```

**Structure :** Matrice 2D où :
- **Première dimension** : Agents (AGENTS = 1..n_agents)
- **Deuxième dimension** : Zones (ZONES = 0..n_zones-1)

### Signification

**`forbidden_zones[a, z] = true`** signifie :

> **L’agent `a` n’a PAS le droit d’aller dans la zone `z`.**

**`forbidden_zones[a, z] = false`** signifie :

> **L’agent `a` peut aller dans la zone `z`.**

### Exemple de matrice

Avec 3 agents et 5 zones (A=0, B=1, C=2, D=3, E=4) :

|       | Zone A (0) | Zone B (1) | Zone C (2) | Zone D (3) | Zone E (4) |
|-------|------------|------------|------------|------------|------------|
| **Agent 1 (R1)** | false      | false      | **true**   | false      | false      |
| **Agent 2 (R2)** | false      | false      | **true**   | false      | false      |
| **Agent 3 (H1)** | false      | false      | false      | false      | false      |

**Interprétation :**
- R1 et R2 ne peuvent pas aller en Zone C (réfrigérée) → `forbidden_zones[1, 2] = true`, `forbidden_zones[2, 2] = true`
- H1 peut aller partout → toutes les valeurs sont `false`

---

## 🎯 Quand la contrainte s’active ou non

| Cas | Contrainte |
|-----|------------|
| **Si la commande n’est pas assignée à cet agent** (`assignment[order_idx] ≠ agent_idx`) | On ignore la règle (A est faux). |
| **Si l’agent n’est pas un robot** (`agent_type[agent_idx] ≠ 0`) | On ignore la règle (B est faux). Les humains peuvent aller partout. |
| **Si la zone n’est pas valide** (`order_zones[order_idx] < 0` ou `≥ n_zones`) | On ignore la règle (C est faux). |
| **Si la commande est assignée à un robot et la zone est valide** (A ∧ B ∧ C vrais) | La contrainte s’active : la zone ne doit pas être interdite pour ce robot (D doit être vrai). |

---

## 📊 Exemples concrets

### Exemple 1 : Contrainte activée (violation)

**Données :**
- Commande 5 assignée à l’agent 2 : `assignment[5] = 2`
- Agent 2 est un robot : `agent_type[2] = 0`
- Zone de la commande 5 : Zone C (réfrigérée) → `order_zones[5] = 2`
- Zone valide : `2 >= 0` et `2 < 5` ✅
- Agent 2 ne peut pas aller en Zone C : `forbidden_zones[2, 2] = true`

**Vérification :**
- **A ∧ B ∧ C** sont vrais ✅
- Il faut que **D** soit vrai : `not forbidden_zones[2, 2]` doit être vrai
- Mais `forbidden_zones[2, 2] = true`, donc `not forbidden_zones[2, 2] = false` ❌
- **VIOLATION** : La contrainte n’est pas satisfaite.

**Solution :** Ne pas assigner la commande 5 à l’agent 2, ou assigner à un humain (agent_type ≠ 0).

### Exemple 2 : Contrainte non activée (humain)

**Données :**
- Commande 3 assignée à l’agent 4 : `assignment[3] = 4`
- Agent 4 est un humain : `agent_type[4] = 1`
- Zone de la commande 3 : Zone C → `order_zones[3] = 2`

**Vérification :**
- **B** est faux (agent_type[4] = 1 ≠ 0) ❌
- L’implication est automatiquement vraie, on n’impose rien.
- Un humain peut aller en Zone C même si `forbidden_zones[4, 2] = true` (car la contrainte ne s’applique qu’aux robots).

### Exemple 3 : Contrainte non activée (commande non assignée)

**Données :**
- Pour la paire (commande 1, agent 2) : `assignment[1] = 3` (commande 1 assignée à l’agent 3, pas à l’agent 2)

**Vérification :**
- **A** est faux (`assignment[1] ≠ 2`) ❌
- La contrainte ne s’applique pas pour cette paire (order_idx, agent_idx).

### Exemple 4 : Contrainte activée (satisfaite)

**Données :**
- Commande 7 assignée à l’agent 1 : `assignment[7] = 1`
- Agent 1 est un robot : `agent_type[1] = 0`
- Zone de la commande 7 : Zone A → `order_zones[7] = 0`
- Zone valide : `0 >= 0` et `0 < 5` ✅
- Agent 1 peut aller en Zone A : `forbidden_zones[1, 0] = false`

**Vérification :**
- **A ∧ B ∧ C** sont vrais ✅
- Il faut que **D** soit vrai : `not forbidden_zones[1, 0]` doit être vrai
- `forbidden_zones[1, 0] = false`, donc `not forbidden_zones[1, 0] = true` ✅
- **SATISFAIT** : La contrainte est respectée.

---

## 🔍 Détail de la condition C : validation de la zone

La condition **C** vérifie que la zone est valide :

```minizinc
order_zones[order_idx] >= 0 /\ order_zones[order_idx] < n_zones
```

**Pourquoi cette vérification ?**

- `order_zones[order_idx] >= 0` : La zone doit être positive (les zones sont numérotées à partir de 0)
- `order_zones[order_idx] < n_zones` : La zone doit être inférieure au nombre total de zones

**Exemple :** Si `n_zones = 5`, les zones valides sont `{0, 1, 2, 3, 4}`.

**Note :** Cette vérification évite les accès hors limites dans la matrice `forbidden_zones`.

---

## ✅ Résumé

| Élément | Rôle |
|--------|------|
| `assignment[order_idx] == agent_idx` | La commande est assignée à cet agent |
| `agent_type[agent_idx] == 0` | L’agent est un robot |
| `order_zones[order_idx] >= 0 /\ order_zones[order_idx] < n_zones` | La zone de la commande est valide |
| `->` | Implication : si la partie gauche est vraie, la droite doit l’être |
| `not forbidden_zones[agent_idx, order_zones[order_idx]]` | Cette zone n’est pas interdite pour ce robot |
| `forbidden_zones[a, z] = true` | L’agent `a` n’a pas le droit d’aller dans la zone `z` |

**En une phrase :** Un robot ne peut pas se voir assigner une commande dont la zone est dans sa liste de zones interdites ; pour les autres cas (autre agent, commande non assignée à ce robot, agent non robot, zone invalide), la contrainte n’impose rien.

---

## 📌 Référence

- **Contrainte** : `models/allocation.mzn` lignes 61-63
- **Déclaration** : `models/allocation.mzn` ligne 24 (`array[AGENTS, ZONES] of bool: forbidden_zones;`)
- **Paramètres** : 
  - `agent_type` (depuis `agents.json`)
  - `order_zones` (dérivé des emplacements des produits de la commande)
  - `forbidden_zones` (dérivé de `agent.restrictions["no_zones"]` dans `agents.json`)
