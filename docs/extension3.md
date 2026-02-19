# Extension 3 : Pannes et Aléas - Robustesse et Résilience

## 📋 Vue d'ensemble

L'**Extension 3** ajoute la capacité de gérer les imprévus et aléas dans un environnement d'entrepôt réel :

- **Robots en panne** : 20% de chance qu'un robot soit indisponible
- **Humains en pause** : Toutes les 2h, pause de 15 minutes
- **Rupture de stock** : Certains produits peuvent être en rupture, rendant certaines commandes non traitables

### Contexte opérationnel

Dans un entrepôt réel, les imprévus sont fréquents :

- **Pannes matérielles** : Les robots peuvent tomber en panne à tout moment
- **Ressources humaines** : Les humains ont besoin de pauses régulières
- **Gestion des stocks** : Les produits peuvent être en rupture de stock

L'objectif est de rendre le système **robuste** et **résilient** : même face à ces aléas, le système doit continuer à fonctionner et réassigner les commandes de manière optimale.

---

## 🎯 Objectifs de l'extension

1. **Gérer les agents indisponibles** : Empêcher l'assignation de commandes aux agents en panne ou en pause
2. **Gérer les ruptures de stock** : Empêcher l'assignation de commandes contenant des produits en rupture
3. **Réassignation automatique** : Le solveur ré-optimise automatiquement pour contourner les problèmes

---

## 🔧 Implémentation dans `allocation.mzn`

### 1️⃣ Nouveaux paramètres

```minizinc
% EXTENSION 3 : Pannes et aléas - Robustesse et résilience
array[AGENTS] of bool: agent_available;          % true si l'agent est disponible
array[ORDERS] of bool: order_available;          % true si la commande peut être traitée
```

**`agent_available[agent_idx]`** : 
- `true` si l'agent est disponible (opérationnel, pas en pause)
- `false` si l'agent est indisponible (en panne, en pause, etc.)

**`order_available[order_idx]`** :
- `true` si la commande peut être traitée (tous les produits en stock)
- `false` si la commande est en rupture de stock (au moins un produit manquant)

**Exemple** :
```minizinc
% 3 agents : R1, R2, H1
agent_available = [false, true, true];  % R1 en panne, R2 et H1 disponibles

% 5 commandes
order_available = [true, true, false, true, true];  % Commande 3 en rupture de stock
```

---

### 2️⃣ Contrainte 9 : Agents indisponibles

```minizinc
% 9. EXTENSION 3 : Agents indisponibles (pannes, pauses)
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx) ->
    agent_available[agent_idx]
);
```

**Logique** : Si une commande est assignée à un agent, alors cet agent doit être disponible.

**Formulation équivalente** :
- Si `assignment[order_idx] = agent_idx`, alors `agent_available[agent_idx] = true`
- Si `agent_available[agent_idx] = false`, alors `assignment[order_idx] ≠ agent_idx` pour toutes les commandes

**Effet** : Un agent indisponible ne peut recevoir aucune commande. Le solveur doit trouver d'autres agents pour les commandes qui lui étaient initialement assignées.

---

### 3️⃣ Contrainte 10 : Commandes en rupture de stock

```minizinc
% 10. EXTENSION 3 : Commandes en rupture de stock
constraint forall(order_idx in ORDERS) (
    (not order_available[order_idx]) ->
    (assignment[order_idx] == 0)
);
```

**Logique** : Si une commande n'est pas disponible (rupture de stock), alors elle ne peut pas être assignée.

**Formulation équivalente** :
- Si `order_available[order_idx] = false`, alors `assignment[order_idx] = 0`
- Si `order_available[order_idx] = true`, alors la commande peut être assignée normalement

**Effet** : Les commandes en rupture de stock restent non assignées. Le solveur optimise avec les commandes disponibles uniquement.

---

## 📊 Exemples d'utilisation

### Exemple 1 : Robot en panne

**Situation initiale** :
- 3 agents : R1 (robot), R2 (robot), H1 (humain)
- 5 commandes à assigner
- Tous les agents disponibles, toutes les commandes disponibles

**Optimisation initiale** :
```
assignment = [1, 1, 2, 2, 3]
```
- Commandes 1-2 → R1
- Commandes 3-4 → R2
- Commande 5 → H1

**Aléa** : R1 tombe en panne (20% de chance)

**Données mises à jour** :
```minizinc
agent_available = [false, true, true];  % R1 indisponible
```

**Ré-optimisation** :
```
assignment = [2, 2, 2, 3, 3]
```
- Les commandes 1-2 initialement sur R1 sont réassignées à R2
- Commande 5 reste sur H1
- R2 est plus chargé, mais toutes les commandes sont traitées

**Résultat** : ✅ Système résilient, toutes les commandes assignées malgré la panne

---

### Exemple 2 : Rupture de stock

**Situation initiale** :
- 3 agents disponibles
- 4 commandes à traiter
- Commande 2 contient un produit en rupture de stock

**Données** :
```minizinc
order_available = [true, false, true, true];  % Commande 2 en rupture
```

**Optimisation** :
```
assignment = [1, 0, 2, 3]
```
- Commande 1 → Agent 1 ✅
- Commande 2 → Non assignée (rupture) ❌
- Commande 3 → Agent 2 ✅
- Commande 4 → Agent 3 ✅

**Résultat** : ✅ Les commandes disponibles sont assignées, la commande en rupture est ignorée

---

### Exemple 3 : Humain en pause

**Situation** :
- 2 robots (R1, R2) et 1 humain (H1)
- H1 prend une pause de 15 minutes toutes les 2h
- Pendant la pause, H1 est indisponible

**Données pendant la pause** :
```minizinc
agent_available = [true, true, false];  % H1 en pause
```

**Effet** :
- Les robots continuent à fonctionner
- Les commandes nécessitant un humain (niveaux élevés, objets fragiles) ne peuvent pas être assignées pendant la pause
- Après la pause, H1 redevient disponible et les commandes peuvent être réassignées

---

## 🔄 Ré-optimisation dynamique

### Scénario complet : Panne + Rupture de stock

**Heure 0** : État initial
- 3 agents disponibles : R1, R2, H1
- 5 commandes disponibles
- Optimisation → Toutes assignées

**Heure 1** : Aléas
- R1 tombe en panne (20% de chance)
- Commande 3 : rupture de stock

**Données mises à jour** :
```minizinc
agent_available = [false, true, true];   % R1 en panne
order_available = [true, true, false, true, true];  % Commande 3 en rupture
```

**Ré-optimisation** :
1. Les commandes initialement sur R1 sont réassignées à R2 ou H1
2. La commande 3 est retirée (rupture de stock)
3. Les autres commandes sont réassignées si nécessaire

**Résultat** : ✅ Système robuste, optimisation adaptée aux contraintes actuelles

---

## 🎯 Avantages de cette approche

### ✅ Simplicité

- Deux paramètres booléens simples
- Contraintes logiques faciles à comprendre
- Pas de modélisation temporelle complexe (gérée au niveau Python)

### ✅ Flexibilité

- Peut gérer n'importe quel type d'indisponibilité (panne, pause, maintenance)
- Compatible avec les autres extensions
- Facile d'ajouter d'autres types d'aléas

### ✅ Robustesse

- Le solveur ré-optimise automatiquement
- Aucune commande n'est assignée à un agent indisponible
- Les commandes en rupture sont automatiquement exclues

### ✅ Résilience

- Le système continue à fonctionner malgré les aléas
- Réassignation automatique des commandes
- Maximisation du nombre de commandes traitées dans les limites possibles

---

## 🔍 Détails d'implémentation

### Gestion des probabilités (niveau Python)

L'extension 3 utilise des paramètres booléens, mais la **génération de ces paramètres** se fait au niveau Python avec des probabilités :

```python
import random

def generate_agent_availability(agents, panne_probability=0.2):
    """
    Génère la disponibilité des agents.
    - Robots : 20% de chance de panne
    - Humains : Disponibles sauf pendant les pauses (géré temporellement)
    """
    agent_available = []
    for agent in agents:
        if agent.type == "robot":
            # 20% de chance de panne
            available = random.random() > panne_probability
        elif agent.type == "human":
            # Disponible sauf pendant les pauses (vérifié temporellement)
            available = not is_on_break(agent, current_time)
        else:
            available = True
        agent_available.append(available)
    return agent_available

def generate_order_availability(orders, stock_status):
    """
    Génère la disponibilité des commandes basée sur le stock.
    """
    order_available = []
    for order in orders:
        # Vérifier si tous les produits sont en stock
        all_in_stock = all(
            stock_status.get(item.product_id, 0) >= item.quantity
            for item in order.items
        )
        order_available.append(all_in_stock)
    return order_available
```

### Gestion temporelle des pauses

Pour les pauses des humains (toutes les 2h, 15min), la logique temporelle est gérée au niveau Python :

```python
def is_on_break(agent, current_time):
    """
    Vérifie si un humain est en pause.
    Pauses : toutes les 2h, durée 15 minutes
    """
    if agent.type != "human":
        return False
    
    # Calculer le cycle de pause (toutes les 2h = 120 minutes)
    cycle_minutes = 120
    pause_duration = 15
    
    # Temps depuis le début de la journée (en minutes)
    minutes_since_start = current_time.hour * 60 + current_time.minute
    
    # Position dans le cycle
    position_in_cycle = minutes_since_start % cycle_minutes
    
    # En pause si dans les 15 premières minutes du cycle
    return position_in_cycle < pause_duration
```

---

## 📝 Comparaison avec d'autres approches

### Approche alternative 1 : Variables de disponibilité temporelle

```minizinc
% Modélisation temporelle complète
array[AGENTS, TIME_SLOTS] of bool: agent_available_time;
```

**Avantage** : Modélisation précise des disponibilités temporelles  
**Inconvénient** : Complexité accrue, nécessite une modélisation temporelle complète

### Approche alternative 2 : Contraintes de réassignation

```minizinc
% Forcer la réassignation des commandes d'agents indisponibles
constraint forall(agent_idx in AGENTS where not agent_available[agent_idx]) (
    sum(order_idx in ORDERS where previous_assignment[order_idx] == agent_idx) 
        (assignment[order_idx] != agent_idx) >= 1
);
```

**Avantage** : Force explicitement la réassignation  
**Inconvénient** : Nécessite de connaître l'assignation précédente, plus complexe

### ✅ Notre approche : Contraintes simples de disponibilité

**Avantage** :
- Simple et efficace
- Le solveur ré-optimise automatiquement
- Pas besoin de connaître l'état précédent
- Compatible avec l'optimisation initiale et la ré-optimisation

---

## 🎓 Cas d'usage avancés

### Cas 1 : Panne en cascade

**Scénario** : Un robot tombe en panne, puis un autre robot tombe en panne peu après.

**Gestion** : À chaque panne, ré-exécuter le solveur avec les agents disponibles mis à jour. Le système s'adapte progressivement.

### Cas 2 : Rupture de stock temporaire

**Scénario** : Un produit est en rupture, puis revient en stock.

**Gestion** : 
1. Ré-optimiser avec `order_available` mis à jour
2. Les commandes précédemment en rupture peuvent maintenant être assignées

### Cas 3 : Maintenance préventive

**Scénario** : Un robot est mis en maintenance préventive (indisponible pendant 1h).

**Gestion** : Marquer l'agent comme indisponible (`agent_available = false`) pendant la période de maintenance. Après la maintenance, remettre à `true` et ré-optimiser.

---

## 📊 Métriques de robustesse

Pour évaluer la robustesse du système, on peut mesurer :

1. **Taux de commandes assignées malgré les aléas** :
   ```
   taux = (commandes assignées) / (commandes disponibles)
   ```

2. **Nombre d'agents indisponibles gérés** :
   ```
   agents_indisponibles = sum(agent_idx in AGENTS where not agent_available[agent_idx])
   ```

3. **Nombre de commandes en rupture** :
   ```
   commandes_rupture = sum(order_idx in ORDERS where not order_available[order_idx])
   ```

4. **Dégradation de performance** :
   ```
   dégradation = (num_assigned_initial - num_assigned_après_aléas) / num_assigned_initial
   ```

---

## 📝 Résumé

| Élément | Description |
|---------|-------------|
| **Paramètres** | `agent_available[AGENTS]`, `order_available[ORDERS]` |
| **Contrainte 9** | Agents indisponibles ne peuvent recevoir de commandes |
| **Contrainte 10** | Commandes en rupture ne peuvent pas être assignées |
| **Robustesse** | Ré-optimisation automatique face aux aléas |
| **Résilience** | Système continue à fonctionner malgré les problèmes |

---

## 🔗 Références

- **Modèle** : `models/allocation.mzn` (lignes 39-42, 109-120)
- **Documentation** : `docs/explication_assignment.md` (structure générale)
- **Énoncé** : `ENONCE_PROJET_OPTIPICK.txt` (section Extension 3)

---

## 💡 Notes pour l'implémentation Python

### 1. Génération des paramètres

```python
# Générer agent_available avec probabilités
agent_available = []
for agent in agents:
    if agent.type == "robot":
        # 20% de chance de panne
        available = random.random() > 0.2
    elif agent.type == "human":
        # Vérifier si en pause (toutes les 2h, 15min)
        available = not is_human_on_break(agent, current_time)
    else:
        available = True
    agent_available.append(available)

# Générer order_available basé sur le stock
order_available = []
for order in orders:
    available = all_products_in_stock(order, stock_status)
    order_available.append(available)
```

### 2. Ré-optimisation périodique

```python
# Ré-optimiser toutes les heures ou à chaque aléa
def reoptimize_on_aléas(orders, agents, current_time, stock_status):
    # Mettre à jour les disponibilités
    agent_available = generate_agent_availability(agents, current_time)
    order_available = generate_order_availability(orders, stock_status)
    
    # Ré-exécuter le solveur
    solution = solve_allocation(
        orders, agents,
        agent_available=agent_available,
        order_available=order_available
    )
    
    return solution
```

### 3. Gestion des pauses humaines

```python
def is_human_on_break(agent, current_time):
    """Vérifie si un humain est en pause."""
    if agent.type != "human":
        return False
    
    # Pauses toutes les 2h (120 min), durée 15 min
    total_minutes = current_time.hour * 60 + current_time.minute
    cycle_position = total_minutes % 120
    
    return cycle_position < 15
```

---

## 🎓 Conclusion

L'Extension 3 rend le système **robuste** et **résilient** face aux aléas courants dans un entrepôt :

- ✅ **Gestion des pannes** : Les robots en panne sont automatiquement exclus
- ✅ **Gestion des pauses** : Les humains en pause ne reçoivent pas de commandes
- ✅ **Gestion des ruptures** : Les commandes en rupture sont automatiquement exclues
- ✅ **Ré-optimisation** : Le solveur s'adapte automatiquement aux contraintes changeantes

Le système continue à fonctionner de manière optimale même face à ces imprévus, garantissant une **résilience opérationnelle** maximale.
