# Explication de la section OUTPUT dans `allocation.mzn`

## 📋 Vue d'ensemble

La section `OUTPUT` (lignes 182-191) du modèle `allocation.mzn` définit ce que MiniZinc affiche après avoir résolu le problème d'allocation optimale. Cette sortie contient la solution principale ainsi que des métriques importantes pour l'analyse et l'intégration avec le code Python.

---

## 🔧 Structure générale

```minizinc
output [
    "texte", show(variable), ";\n",
    ...
];
```

**Éléments clés** :
- `output [...]` : Bloc de sortie MiniZinc
- `show(variable)` : Fonction qui convertit une variable en chaîne de caractères
- `";\n"` : Point-virgule et saut de ligne (format de sortie standard)

---

## 📊 Détail ligne par ligne

### Ligne 183 : `"assignment = ", show(assignment), ";\n"`

**Rôle** : Affiche la solution principale - l'assignation de chaque commande à un agent.

**Exemple de sortie** :
```
assignment = [2, 1, 0, 3, 2, 1, 0, 3, 2, 1];
```

**Interprétation** :
- `assignment[1] = 2` → Commande 1 assignée à l'agent 2
- `assignment[2] = 1` → Commande 2 assignée à l'agent 1
- `assignment[3] = 0` → Commande 3 **non assignée**
- `assignment[4] = 3` → Commande 4 assignée à l'agent 3
- etc.

**Structure** :
- Tableau de taille `n_orders`
- Chaque élément est dans `{0, 1, 2, ..., n_agents}`
- `0` = commande non assignée
- `1..n_agents` = index de l'agent assigné

**Utilité** :
- ✅ C'est la **solution principale** utilisée par le code Python
- ✅ Permet de savoir exactement quelle commande va à quel agent
- ✅ Identifie les commandes non assignées (valeur 0)

---

### Ligne 184 : `"num_assigned = ", show(num_assigned), ";\n"`

**Rôle** : Affiche le nombre total de commandes assignées.

**Exemple de sortie** :
```
num_assigned = 8;
```

**Interprétation** :
- Sur 10 commandes au total, 8 ont été assignées avec succès
- 2 commandes n'ont pas pu être assignées (contraintes non satisfaites)

**Calcul** :
```minizinc
var int: num_assigned = sum(order_idx in ORDERS) (assignment[order_idx] != 0);
```

**Utilité** :
- ✅ **Métrique de performance** rapide
- ✅ Permet de voir rapidement le taux de succès
- ✅ Utile pour comparer différentes configurations

---

### Ligne 185 : `"num_express_assigned = ", show(num_express_assigned), ";\n"`

**Rôle** : Affiche le nombre de commandes express assignées (Extension 2).

**Exemple de sortie** :
```
num_express_assigned = 3;
```

**Interprétation** :
- Sur 4 commandes express au total, 3 ont été assignées
- 1 commande express n'a pas pu être assignée

**Calcul** :
```minizinc
var int: num_express_assigned = sum(order_idx in ORDERS where order_is_express[order_idx]) 
    (assignment[order_idx] != 0);
```

**Utilité** :
- ✅ Vérifie que les **commandes express sont prioritaires** (Extension 2)
- ✅ Permet de mesurer l'efficacité de la priorisation
- ✅ Important pour respecter les SLA (Service Level Agreement)

---

### Ligne 186 : `"weighted_objective = ", show(weighted_objective), ";\n"`

**Rôle** : Affiche la valeur de l'objectif pondéré qui a été maximisé.

**Exemple de sortie** :
```
weighted_objective = 3008.5;
```

**Interprétation** :
L'objectif pondéré est calculé comme suit :
```minizinc
var float: weighted_objective = 
    1000.0 * num_express_assigned    % Priorité express (coefficient 1000)
    + num_assigned                   % Nombre total assigné
    - 0.01 * congestion_cost         % Pénalité congestion (Extension 4)
    + 0.1 * rl_bonus;                % Bonus RL (Extension 5)
```

**Exemple de calcul** :
- `num_express_assigned = 3` → contribution : `1000 × 3 = 3000`
- `num_assigned = 8` → contribution : `8`
- `congestion_cost = 50.0` → pénalité : `-0.01 × 50 = -0.5`
- `rl_bonus = 85.0` → bonus : `0.1 × 85 = 8.5`
- **Total** : `3000 + 8 - 0.5 + 8.5 = 3016.0`

**Utilité** :
- ✅ Permet de **comparer différentes solutions**
- ✅ Mesure la qualité globale de l'allocation
- ✅ Utile pour le debugging et l'optimisation
- ✅ Vérifie que l'objectif est bien maximisé

---

## 📝 Exemple de sortie complète

Voici un exemple complet de ce que produit la section OUTPUT :

```
assignment = [2, 1, 0, 3, 2, 1, 0, 3, 2, 1];
num_assigned = 8;
num_express_assigned = 3;
weighted_objective = 3008.5;
% EXTENSION 3 : Agents indisponibles = [1];
% EXTENSION 3 : Commandes en rupture = [3, 7];
% EXTENSION 4 : Coût congestion = 50.0;
% EXTENSION 5 : Bonus RL = 85.0;
```

**Analyse** :
- ✅ 8 commandes assignées sur 10
- ✅ 3 commandes express assignées (priorité respectée)
- ✅ Agent 1 indisponible (Extension 3)
- ✅ Commandes 3 et 7 en rupture de stock (Extension 3)
- ✅ Coût de congestion de 50 secondes (Extension 4)
- ✅ Bonus RL de 85 points (Extension 5)

---

## 🔍 Lignes supplémentaires (Extensions)

### Ligne 187 : Agents indisponibles
```minizinc
"% EXTENSION 3 : Agents indisponibles = ", show([agent_idx | agent_idx in AGENTS where not agent_available[agent_idx]]), ";\n"
```
Affiche la liste des agents qui étaient indisponibles (en panne ou en pause).

### Ligne 188 : Commandes en rupture
```minizinc
"% EXTENSION 3 : Commandes en rupture = ", show([order_idx | order_idx in ORDERS where not order_available[order_idx]]), ";\n"
```
Affiche la liste des commandes qui étaient en rupture de stock.

### Ligne 189 : Coût de congestion
```minizinc
"% EXTENSION 4 : Coût congestion = ", show(congestion_cost), ";\n"
```
Affiche le coût total lié aux zones congestionnées.

### Ligne 190 : Bonus RL
```minizinc
"% EXTENSION 5 : Bonus RL = ", show(rl_bonus), ";\n"
```
Affiche le bonus obtenu grâce aux préférences apprises par RL.

---

## 💡 Pourquoi cette structure ?

### 1. **Lisibilité**
- Format structuré et facile à lire
- Commentaires explicatifs pour chaque métrique
- Séparation claire entre solution principale et métriques

### 2. **Debugging**
- Permet de voir rapidement ce qui s'est passé
- Identifie les problèmes (agents indisponibles, ruptures, etc.)
- Facilite la compréhension des décisions du solveur

### 3. **Intégration Python**
- Le code Python parse cette sortie pour récupérer `assignment`
- Les métriques permettent d'évaluer la qualité de la solution
- Format standardisé facilite le parsing automatique

### 4. **Traçabilité**
- Historique des décisions prises
- Métriques pour analyse post-mortem
- Documentation des extensions utilisées

---

## 🔧 Notes techniques

### Fonction `show()`
- Convertit n'importe quel type de variable MiniZinc en chaîne de caractères
- Gère automatiquement les tableaux, booléens, entiers, flottants
- Format standardisé pour la sortie

### Format de sortie
- Le point-virgule `;` indique la fin d'une instruction
- Le saut de ligne `\n` améliore la lisibilité
- Les commentaires `%` ajoutent du contexte sans affecter le parsing

### Parsing côté Python
Le code Python dans `minizinc_solver.py` parse cette sortie pour extraire :
```python
assign_arr = result["assignment"]  # Récupère le tableau assignment
```

---

## 📊 Utilisation pratique

### Dans le code Python

```python
# Après résolution MiniZinc
result = instance.solve()

# Récupérer l'assignation
assignment_array = result["assignment"]
# assignment_array = [2, 1, 0, 3, ...]

# Récupérer les métriques
num_assigned = result["num_assigned"]  # 8
num_express = result["num_express_assigned"]  # 3
objective = result["weighted_objective"]  # 3008.5

# Construire le dictionnaire final
assignment = {}
for i, order in enumerate(orders):
    agent_idx = assignment_array[i]
    if agent_idx > 0:
        assignment[order.id] = agents[agent_idx - 1].id
    else:
        assignment[order.id] = None
```

### Analyse des résultats

```python
# Vérifier le taux de succès
success_rate = num_assigned / len(orders)  # 8/10 = 80%

# Vérifier la priorisation express
express_rate = num_express / total_express  # 3/4 = 75%

# Comparer avec d'autres solutions
if objective > previous_best:
    print("Nouvelle meilleure solution trouvée!")
```

---

## 🎓 Conclusion

La section OUTPUT est **essentielle** pour :

- ✅ **Fournir la solution** : L'assignation optimale des commandes
- ✅ **Donner des métriques** : Performance et qualité de la solution
- ✅ **Faciliter le debugging** : Comprendre pourquoi certaines décisions ont été prises
- ✅ **Permettre l'intégration** : Parser facilement les résultats dans le code Python

Cette structure bien pensée permet une intégration fluide entre le modèle d'optimisation MiniZinc et le reste du système Python.

---

## 🔗 Références

- **Modèle** : `models/allocation.mzn` (lignes 181-191)
- **Code Python** : `src/minizinc_solver.py` (parsing de la sortie)
- **Documentation MiniZinc** : https://www.minizinc.org/doc-latest/en/standard-library.html#output
