# Rapport explicatif — `models/allocation.mzn`

**Projet OptiPick** | Modèle MiniZinc pour l'allocation optimale

---

## Vue d'ensemble

Le fichier `models/allocation.mzn` est un **modèle MiniZinc** qui résout le problème d'allocation des commandes aux agents de manière optimale. Il définit des **paramètres** (données d'entrée), des **variables de décision**, des **contraintes** (règles à respecter) et un **objectif** (ce qu'on veut optimiser).

---

## 1. Déclarations de paramètres

### `int: n_orders;` et `int: n_agents;`

**Explication** : Ces deux entiers représentent respectivement le **nombre de commandes** à assigner et le **nombre d'agents** disponibles dans l'entrepôt. Ce sont des valeurs fixes fournies par le code Python qui appelle le modèle.

**Où MiniZinc va chercher ces valeurs** : MiniZinc ne lit pas ces valeurs depuis un fichier. Elles sont **calculées dans le code Python** et **passées au modèle** lors de la résolution :

1. **Dans Python** (`src/minizinc_solver.py`) :
   ```python
   n_orders = len(orders)  # Calcule le nombre de commandes
   n_agents = len(agents)  # Calcule le nombre d'agents
   
   instance = Instance(solver, model)
   instance["n_orders"] = n_orders  # Passe la valeur à MiniZinc
   instance["n_agents"] = n_agents   # Passe la valeur à MiniZinc
   ```

2. **MiniZinc reçoit** ces valeurs et les utilise dans le modèle pour définir les tailles des tableaux et les ensembles.

**Exemple** : Si on a 10 commandes et 3 agents, Python calcule `n_orders = 10` et `n_agents = 3`, puis les passe à MiniZinc via `instance["n_orders"] = 10` et `instance["n_agents"] = 3`.

---

### `set of int: ORDERS = 1..n_orders;` et `set of int: AGENTS = 1..n_agents;`

**Explication** : Ces ensembles définissent les **indices** utilisables pour référencer les commandes et les agents. `ORDERS` contient les nombres de 1 à `n_orders` (par exemple {1, 2, 3, ..., 10}), et `AGENTS` contient les nombres de 1 à `n_agents` (par exemple {1, 2, 3}).

**Pourquoi** : En MiniZinc, les tableaux sont indexés à partir de 1, donc ces ensembles permettent d'itérer facilement sur toutes les commandes ou tous les agents.

---

### `array[AGENTS] of float: capacity_weight;` et `array[AGENTS] of float: capacity_volume;`

**Explication** : Ces deux tableaux stockent les **capacités maximales** de chaque agent en poids (en kilogrammes) et en volume (en décimètres cubes). Chaque agent a une limite de poids et de volume qu'il peut transporter.

**Exemple** : Si `capacity_weight[1] = 20.0`, cela signifie que l'agent numéro 1 peut transporter au maximum 20 kg.

---

### `array[AGENTS] of int: agent_type;`

**Explication** : Ce tableau indique le **type de chaque agent** sous forme d'entier : 0 = robot, 1 = humain, 2 = chariot. Cette information est utilisée pour appliquer des restrictions spécifiques (par exemple, les robots ont des contraintes particulières).

---

### `array[ORDERS] of float: order_weight;` et `array[ORDERS] of float: order_volume;`

**Explication** : Ces tableaux contiennent le **poids total** et le **volume total** de chaque commande. Ces valeurs sont calculées en additionnant le poids et le volume de tous les produits dans la commande, multipliés par leurs quantités.

**Exemple** : Si `order_weight[1] = 5.2`, cela signifie que la commande numéro 1 pèse 5,2 kg au total.

---

### `int: n_zones = 5;` et `set of int: ZONES = 0..n_zones-1;`

**Explication** : `n_zones` fixe le nombre de zones dans l'entrepôt (5 zones : A, B, C, D, E). `ZONES` est l'ensemble {0, 1, 2, 3, 4} qui représente ces zones sous forme d'entiers (0 = Zone A, 1 = Zone B, 2 = Zone C, 3 = Zone D, 4 = Zone E).

**Pourquoi des entiers** : MiniZinc travaille mieux avec des entiers pour les indices de tableaux, donc on encode les zones comme des nombres plutôt que des chaînes de caractères.

---

### `array[AGENTS, ZONES] of bool: forbidden_zones;`

**Explication** : Cette matrice booléenne indique quelles **zones sont interdites** pour chaque agent. Si `forbidden_zones[agent_idx, zone] = true`, alors cet agent ne peut pas aller dans cette zone.

**Exemple** : Si `forbidden_zones[1, 2] = true`, cela signifie que l'agent numéro 1 (un robot) ne peut pas aller dans la zone 2 (Zone C, réfrigérée).

---

### `array[AGENTS] of bool: no_fragile;`

**Explication** : Ce tableau indique si un agent **ne peut pas transporter d'objets fragiles**. Si `no_fragile[agent_idx] = true`, alors cet agent ne peut pas prendre de commandes contenant des produits fragiles.

**Exemple** : Les robots ont souvent `no_fragile[robot_idx] = true` car ils ne peuvent pas manipuler les objets fragiles avec précaution.

---

### `array[AGENTS] of float: max_item_weight;`

**Explication** : Ce tableau donne le **poids maximum** qu'un article individuel peut avoir pour être transporté par un agent. Si `max_item_weight[agent_idx] = 10.0`, alors cet agent ne peut pas prendre de commande contenant un produit pesant plus de 10 kg.

**Note** : Si la valeur est 0, cela signifie qu'il n'y a pas de limite de poids par article pour cet agent.

---

### `array[ORDERS] of int: order_zones;`

**Explication** : Ce tableau indique dans quelle **zone** se trouve chaque commande (ou plutôt, dans quelle zone se trouvent les produits de la commande). Les valeurs sont des entiers de 0 à 4 (A à E).

**Note importante** : La valeur 0 peut signifier soit la Zone A, soit une zone non définie. Par défaut, on considère que 0 = Zone A pour éviter les erreurs d'accès hors limites.

---

### `array[ORDERS] of bool: order_has_fragile;`

**Explication** : Ce tableau indique si une commande **contient des objets fragiles**. Si `order_has_fragile[order_idx] = true`, alors cette commande contient au moins un produit marqué comme fragile.

---

### `array[ORDERS] of float: order_max_item_weight;`

**Explication** : Ce tableau donne le **poids maximum d'un article individuel** dans chaque commande. Cela permet de vérifier si un agent peut prendre la commande en fonction de sa restriction `max_item_weight`.

**Exemple** : Si une commande contient un produit de 12 kg et que l'agent a `max_item_weight = 10.0`, alors cette commande ne peut pas être assignée à cet agent.

---

### `array[ORDERS, ORDERS] of bool: incompatible;`

**Explication** : Cette matrice booléenne indique quelles **commandes sont incompatibles** entre elles. Si `incompatible[order_i, order_j] = true`, alors ces deux commandes ne peuvent pas être assignées au même agent (par exemple, parce que leurs produits sont chimiquement incompatibles).

**Note** : La matrice est symétrique : si la commande i est incompatible avec la commande j, alors j est aussi incompatible avec i.

---

## 2. Variables de décision

### `array[ORDERS] of var 0..n_agents: assignment;`

**Explication** : C'est la **variable principale** que le solveur MiniZinc va déterminer. `assignment[order_idx]` indique à quel agent la commande `order_idx` est assignée.

**Valeurs possibles** :
- Si `assignment[order_idx] = 0`, la commande n'est **pas assignée** (aucun agent ne peut la prendre).
- Si `assignment[order_idx] = k` (où k est entre 1 et n_agents), la commande est assignée à l'agent numéro k.

**Exemple** : Si `assignment[1] = 2`, cela signifie que la commande numéro 1 est assignée à l'agent numéro 2.

---

## 3. Contraintes

### Contrainte 1 : Capacité en poids

```minizinc
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) (order_weight[order_idx]) <= capacity_weight[agent_idx]
);
```

**Explication** : Pour chaque agent, la **somme des poids** de toutes les commandes qui lui sont assignées ne doit pas dépasser sa capacité maximale en poids. Cette contrainte garantit qu'un agent ne sera jamais surchargé.

**En français** : "Pour chaque agent, le poids total des commandes qu'il transporte doit être inférieur ou égal à sa capacité maximale."

---

### Contrainte 2 : Capacité en volume

```minizinc
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) (order_volume[order_idx]) <= capacity_volume[agent_idx]
);
```

**Explication** : Similaire à la contrainte de poids, mais pour le **volume**. Pour chaque agent, la somme des volumes de toutes les commandes assignées ne doit pas dépasser sa capacité maximale en volume.

**En français** : "Pour chaque agent, le volume total des commandes qu'il transporte doit être inférieur ou égal à sa capacité maximale en volume."

---

### Contrainte 3 : Zones interdites pour les robots

```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ order_zones[order_idx] >= 0 /\ order_zones[order_idx] < n_zones) ->
    (not forbidden_zones[agent_idx, order_zones[order_idx]])
);
```

**Explication** : Si une commande est assignée à un agent qui est un robot (`agent_type[agent_idx] == 0`), et si la zone de la commande est valide (entre 0 et 4), alors cette zone ne doit pas être interdite pour ce robot. Le symbole `->` signifie "implique" (si la condition de gauche est vraie, alors celle de droite doit aussi être vraie).

**En français** : "Si une commande est assignée à un robot, et si la commande se trouve dans une zone valide, alors cette zone ne doit pas être dans la liste des zones interdites pour ce robot."

**Exemple** : Si un robot a `forbidden_zones[robot_idx, 2] = true` (Zone C interdite), alors aucune commande de la Zone C ne peut lui être assignée.

---

### Contrainte 4 : Pas d'objets fragiles pour certains robots

```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ no_fragile[agent_idx]) ->
    (not order_has_fragile[order_idx])
);
```

**Explication** : Si une commande est assignée à un robot qui ne peut pas transporter d'objets fragiles (`no_fragile[agent_idx] = true`), alors cette commande ne doit pas contenir d'objets fragiles.

**En français** : "Si une commande est assignée à un robot qui ne peut pas transporter de produits fragiles, alors cette commande ne doit pas contenir de produits fragiles."

---

### Contrainte 5 : Poids maximum par article pour les robots

```minizinc
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ max_item_weight[agent_idx] > 0) ->
    (order_max_item_weight[order_idx] <= max_item_weight[agent_idx])
);
```

**Explication** : Si une commande est assignée à un robot qui a une limite de poids par article (`max_item_weight[agent_idx] > 0`), alors le poids maximum d'un article dans cette commande ne doit pas dépasser cette limite.

**En français** : "Si une commande est assignée à un robot qui a une limite de poids par article, alors aucun article de cette commande ne doit peser plus que cette limite."

**Exemple** : Si un robot a `max_item_weight = 10.0` et qu'une commande contient un produit de 12 kg, cette commande ne peut pas être assignée à ce robot.

---

### Contrainte 6 : Incompatibilités entre produits

```minizinc
constraint forall(order_first in ORDERS, order_second in ORDERS where order_first < order_second /\ incompatible[order_first, order_second]) (
    assignment[order_first] != assignment[order_second] \/ assignment[order_first] == 0 \/ assignment[order_second] == 0
);
```

**Explication** : Si deux commandes sont incompatibles (`incompatible[order_first, order_second] = true`), alors elles ne peuvent pas être assignées au même agent. Le symbole `\/` signifie "ou" : soit les deux commandes sont assignées à des agents différents, soit au moins l'une des deux n'est pas assignée (valeur 0).

**En français** : "Si deux commandes sont incompatibles, alors elles ne peuvent pas être assignées au même agent. L'une ou les deux peuvent ne pas être assignées."

**Exemple** : Si la commande 1 (produits électroniques) est incompatible avec la commande 2 (produits chimiques), alors elles ne peuvent pas aller dans le même chariot. Elles doivent aller à des agents différents, ou au moins l'une d'elles reste non assignée.

---

## 4. Objectif

### `var int: num_assigned = sum(order_idx in ORDERS) (assignment[order_idx] != 0);`

**Explication** : Cette variable calcule le **nombre de commandes assignées** en comptant toutes les commandes dont `assignment[order_idx] != 0` (c'est-à-dire assignées à un agent, pas à 0).

---

### `solve maximize num_assigned;`

**Explication** : L'objectif du modèle est de **maximiser le nombre de commandes assignées**. Le solveur MiniZinc va chercher une solution qui respecte toutes les contraintes et qui assigne le plus grand nombre possible de commandes aux agents.

**Pourquoi maximiser** : L'objectif est de traiter le maximum de commandes possible tout en respectant toutes les contraintes (capacités, restrictions, incompatibilités).

---

## 5. Sortie (output)

```minizinc
output [
    "assignment = ", show(assignment), ";\n",
    "num_assigned = ", show(num_assigned), ";\n"
];
```

**Explication** : Cette section définit ce qui sera affiché à la fin de la résolution. Elle affiche le tableau `assignment` (qui indique quelle commande va à quel agent) et le nombre total de commandes assignées (`num_assigned`).

**Exemple de sortie** :
```
assignment = [2, 1, 0, 3, 2, ...];
num_assigned = 8;
```

Cela signifie que la commande 1 est assignée à l'agent 2, la commande 2 à l'agent 1, la commande 3 n'est pas assignée (0), etc., et qu'au total 8 commandes ont été assignées.

---

## Résumé du flux

1. **Paramètres** : Le code Python fournit toutes les données (nombre de commandes, capacités, restrictions, etc.)
2. **Variables** : Le modèle définit `assignment` comme variable à déterminer
3. **Contraintes** : Le modèle impose toutes les règles (capacités, restrictions, incompatibilités)
4. **Objectif** : Maximiser le nombre de commandes assignées
5. **Résolution** : Le solveur MiniZinc trouve une solution optimale
6. **Sortie** : Le résultat (`assignment`) est retourné au code Python qui l'interprète

---

*Rapport généré pour le projet OptiPick — Explication du modèle `allocation.mzn`*
