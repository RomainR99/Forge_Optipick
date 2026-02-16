% Modèle MiniZinc pour l'allocation optimale des commandes aux agents
% Projet OptiPick - Jour 2 avec MiniZinc

% PARAMÈTRES
int: n_orders;           % Nombre de commandes
int: n_agents;           % Nombre d'agents
set of int: ORDERS = 1..n_orders;
set of int: AGENTS = 1..n_agents;

% Capacités des agents
array[AGENTS] of float: capacity_weight;
array[AGENTS] of float: capacity_volume;
array[AGENTS] of int: agent_type;  % 0=robot, 1=human, 2=cart

% Poids et volumes des commandes
array[ORDERS] of float: order_weight;
array[ORDERS] of float: order_volume;

% Restrictions des robots
% Zones interdites: matrice booléenne [agent, zone] = true si zone interdite
% Zones: 0=A, 1=B, 2=C, 3=D, 4=E
int: n_zones = 5;
set of int: ZONES = 0..n_zones-1;
array[AGENTS, ZONES] of bool: forbidden_zones;  % true si zone interdite pour cet agent
array[AGENTS] of bool: no_fragile;              % Pas d'objets fragiles
array[AGENTS] of float: max_item_weight;         % Poids max par item (0 si pas de limite)

% Zones des commandes (encodées comme entiers: 0=A, 1=B, 2=C, 3=D, 4=E, -1=aucune)
array[ORDERS] of int: order_zones;
array[ORDERS] of bool: order_has_fragile;       % La commande contient des objets fragiles
array[ORDERS] of float: order_max_item_weight;   % Poids max d'un item dans la commande

% Incompatibilités entre produits (matrice: order_i incompatible avec order_j)
array[ORDERS, ORDERS] of bool: incompatible;

% VARIABLES DE DÉCISION
% assignment[o] = a signifie que la commande o est assignée à l'agent a
% assignment[o] = 0 signifie que la commande o n'est pas assignée
array[ORDERS] of var 0..n_agents: assignment;

% CONTRAINTES

% 1. Capacité en poids
constraint forall(a in AGENTS) (
    sum(o in ORDERS where assignment[o] == a) (order_weight[o]) <= capacity_weight[a]
);

% 2. Capacité en volume
constraint forall(a in AGENTS) (
    sum(o in ORDERS where assignment[o] == a) (order_volume[o]) <= capacity_volume[a]
);

% 3. Restrictions des robots (zones interdites)
constraint forall(o in ORDERS, a in AGENTS) (
    (assignment[o] == a /\ agent_type[a] == 0 /\ order_zones[o] != -1) ->
    (not forbidden_zones[a, order_zones[o]])
);

% 4. Restrictions des robots (pas d'objets fragiles)
constraint forall(o in ORDERS, a in AGENTS) (
    (assignment[o] == a /\ agent_type[a] == 0 /\ no_fragile[a]) ->
    (not order_has_fragile[o])
);

% 5. Restrictions des robots (poids max par item)
constraint forall(o in ORDERS, a in AGENTS) (
    (assignment[o] == a /\ agent_type[a] == 0 /\ max_item_weight[a] > 0) ->
    (order_max_item_weight[o] <= max_item_weight[a])
);

% 6. Incompatibilités entre produits
% Si deux commandes sont incompatibles, elles ne peuvent pas être assignées au même agent
constraint forall(o1, o2 in ORDERS where o1 < o2 /\ incompatible[o1, o2]) (
    assignment[o1] != assignment[o2] \/ assignment[o1] == 0 \/ assignment[o2] == 0
);

% 7. Gestion des chariots (simplifiée: un chariot nécessite qu'un humain soit disponible)
% Cette contrainte est vérifiée après résolution dans le code Python

% OBJECTIF: Maximiser le nombre de commandes assignées
var int: num_assigned = sum(o in ORDERS) (assignment[o] != 0);
solve maximize num_assigned;

% OUTPUT
output [
    "assignment = ", show(assignment), ";\n",
    "num_assigned = ", show(num_assigned), ";\n"
];
