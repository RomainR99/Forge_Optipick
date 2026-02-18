# Explication : contrainte « pas d'objets fragiles »

## 📋 La contrainte dans `allocation.mzn`

Dans le fichier `models/allocation.mzn`, la contrainte sur les objets fragiles (lignes 66-70) est :

```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ no_fragile[agent_idx]) ->
    (not order_has_fragile[order_idx])
);
```

**En français :** Si une commande est assignée à un agent qui est un robot et qui n’accepte pas le fragile, alors cette commande ne doit pas contenir d’objets fragiles.

---

## 🧠 Structure logique : implication

La contrainte a la forme :

**(A ∧ B ∧ C) → D**

Où :
- **A** : `assignment[order_idx] == agent_idx` (la commande est assignée à cet agent)
- **B** : `agent_type[agent_idx] == 0` (l’agent est un robot)
- **C** : `no_fragile[agent_idx]` (ce robot n’accepte pas les objets fragiles)
- **D** : `not order_has_fragile[order_idx]` (la commande ne contient pas d’objets fragiles)

**Précision :** `not order_has_fragile[order_idx]` signifie : *le booléen `order_has_fragile[order_idx]` est faux* (donc la commande ne contient pas d’objets fragiles).

**Signification de l’implication `→` :**

- **Si A, B et C sont vrais** → alors **D doit être vrai**.
- **Sinon** (si au moins une des conditions A, B ou C est fausse) → on **ne force rien** sur D.

Donc la contrainte ne s’active que dans le « bon » cas (commande assignée à un robot qui n’accepte pas le fragile).

---

## 🎯 Quand la contrainte s’active ou non

| Cas | Contrainte |
|-----|------------|
| **Si l’agent n’est pas un robot** (`agent_type ≠ 0`) | On ignore la règle (B est faux, l’implication est automatiquement vraie). |
| **Si la commande n’est pas assignée à cet agent** (`assignment[order_idx] ≠ agent_idx`) | On ignore la règle (A est faux). |
| **Si le robot accepte le fragile** (`no_fragile[agent_idx] = false`) | On ignore la règle (C est faux). |
| **Si la commande est assignée à un robot qui n’accepte pas le fragile** (A ∧ B ∧ C vrais) | La contrainte s’active : la commande **ne doit pas** contenir d’objets fragiles (D doit être vrai). |

En résumé : la contrainte ne s’active que lorsque la commande est bien assignée à un robot qui a la restriction « pas d’objets fragiles ».

---

## 📊 Exemples

### Exemple 1 : Contrainte activée

- Commande 5 assignée à l’agent 2 : `assignment[5] = 2`
- Agent 2 est un robot : `agent_type[2] = 0`
- Agent 2 n’accepte pas le fragile : `no_fragile[2] = true`

→ **A ∧ B ∧ C** sont vrais.  
→ Il faut que **D** soit vrai : `order_has_fragile[5]` doit être **false**.  
→ La commande 5 ne doit pas contenir d’objets fragiles.

### Exemple 2 : Contrainte non activée (humain)

- Commande 3 assignée à l’agent 4 : `assignment[3] = 4`
- Agent 4 est un humain : `agent_type[4] = 1`

→ **B** est faux.  
→ L’implication est vraie quoi qu’il arrive, on n’impose rien sur la commande.  
→ Un humain peut avoir une commande avec objets fragiles.

### Exemple 3 : Contrainte non activée (commande non assignée à cet agent)

- Pour la paire (commande 1, agent 2) : `assignment[1] = 3` (commande 1 assignée à l’agent 3, pas à l’agent 2)

→ **A** est faux.  
→ La contrainte ne s’applique pas pour cette paire (order_idx, agent_idx).

---

## ✅ Résumé

| Élément | Rôle |
|--------|------|
| `assignment[order_idx] == agent_idx` | La commande est assignée à cet agent |
| `agent_type[agent_idx] == 0` | L’agent est un robot |
| `no_fragile[agent_idx]` | Ce robot a la restriction « pas d’objets fragiles » |
| `->` | Implication : si la partie gauche est vraie, la droite doit l’être |
| `not order_has_fragile[order_idx]` | La commande ne contient pas d’objets fragiles |

**En une phrase :** Un robot qui n’accepte pas le fragile ne peut pas se voir assigner une commande contenant des objets fragiles ; pour les autres cas (autre agent, commande non assignée à ce robot, robot qui accepte le fragile), la contrainte n’impose rien.

---

## 📌 Référence

- **Contrainte** : `models/allocation.mzn` lignes 66-70  
- **Paramètres** : 
  - `agent_type`, `no_fragile` (depuis `agents.json`)
  - `order_has_fragile` (voir `docs/origine_order_has_fragile.md` pour l'origine depuis `products.json`)
