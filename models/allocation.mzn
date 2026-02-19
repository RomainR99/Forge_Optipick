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
set of int: ZONES = 0..n_zones-1; %Les zones sont numérotées à partir de 0 
array[AGENTS, ZONES] of bool: forbidden_zones;  % true si zone interdite pour cet agent
array[AGENTS] of bool: no_fragile;              % Pas d'objets fragiles
array[AGENTS] of float: max_item_weight;         % Poids max par item (0 si pas de limite)

% Zones des commandes (encodées comme entiers: 0=A, 1=B, 2=C, 3=D, 4=E)
% Note: 0 peut signifier Zone A ou zone non définie (par défaut Zone A pour éviter les accès hors limites)
array[ORDERS] of int: order_zones;
array[ORDERS] of bool: order_has_fragile;       % La commande contient des objets fragiles
array[ORDERS] of float: order_max_item_weight;   % Poids max d'un item dans la commande

% EXTENSION 1 : Picking multi-niveaux
% Chaque étagère a des niveaux 1-5. Robots accèdent uniquement aux niveaux 1-2,
% humains à tous les niveaux (avec escabeau).
array[ORDERS] of bool: order_has_high_level;    % Commande contient au moins un produit sur niveau 3, 4 ou 5

% EXTENSION 2 : Gestion dynamique - Commandes express prioritaires
% Les commandes express doivent être traitées en priorité lors de la ré-optimisation
array[ORDERS] of bool: order_is_express;        % true si la commande est express (prioritaire)

% EXTENSION 3 : Pannes et aléas - Robustesse et résilience
% Gestion des imprévus : agents indisponibles (pannes, pauses) et commandes en rupture de stock
array[AGENTS] of bool: agent_available;          % true si l'agent est disponible (pas en panne/pause)
array[ORDERS] of bool: order_available;         % true si la commande peut être traitée (pas en rupture de stock)

% EXTENSION 4 : Zones congestionnées - Vitesses réduites et contraintes de circulation
% Certaines zones sont plus lentes : allées étroites (-50% vitesse), zones encombrées (+30s), sens unique
% Matrice de pénalités de temps par zone [zone] en secondes
% Pénalité = temps supplémentaire pour traverser la zone (en secondes)
array[ZONES] of float: zone_congestion_penalty;  % Pénalité de temps (secondes) pour traverser chaque zone
% Facteur de réduction de vitesse par zone [zone] (1.0 = vitesse normale, 0.5 = vitesse réduite de 50%)
array[ZONES] of float: zone_speed_factor;        % Facteur de vitesse (1.0 = normal, 0.5 = -50%, etc.)

% EXTENSION 5 : Apprentissage par renforcement - Politique apprise
% Le RL apprend une politique d'allocation optimale. Les poids appris peuvent être intégrés ici.
% Matrice de préférences apprises [order_idx, agent_idx] : score de préférence (plus élevé = meilleur)
% Note: Ces valeurs sont apprises par RL et peuvent guider l'optimisation
array[ORDERS, AGENTS] of float: rl_preference_scores;  % Scores de préférence appris par RL (optionnel, peut être rempli de 0.0)

% Incompatibilités entre produits (matrice: order_i incompatible avec order_j)
array[ORDERS, ORDERS] of bool: incompatible;

% VARIABLES DE DÉCISION
% assignment[order_idx] = agent_idx signifie que la commande order_idx est assignée à l'agent agent_idx
% assignment[order_idx] = 0 signifie que la commande order_idx n'est pas assignée
array[ORDERS] of var 0..n_agents: assignment;

% CONTRAINTES

% 1. Capacité en poids
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) (order_weight[order_idx]) <= capacity_weight[agent_idx]
);
%On parcourt chaque agent un par un.
%Pour chacun, on additionne le poids de toutes les commandes qui lui sont assignées.
%On impose que ce poids total ne dépasse pas la capacité maximale de l’agent.


% 2. Capacité en volume
constraint forall(agent_idx in AGENTS) (
    sum(order_idx in ORDERS where assignment[order_idx] == agent_idx) (order_volume[order_idx]) <= capacity_volume[agent_idx]
);

% 3. Restrictions des robots (zones interdites)
% Note: order_zones[order_idx] = 0 peut signifier Zone A ou zone non définie (par défaut Zone A)
% On vérifie seulement si la zone est dans la plage valide [0..4]
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ 
    agent_type[agent_idx] == 0 /\ 
    order_zones[order_idx] >= 0 /\ 
    order_zones[order_idx] < n_zones) ->
    (not forbidden_zones[agent_idx, order_zones[order_idx]])
);

% 4. Restrictions des robots (pas d'objets fragiles)
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ no_fragile[agent_idx]) ->
    (not order_has_fragile[order_idx])
);

% 5. Restrictions des robots (poids max par item)
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0 /\ max_item_weight[agent_idx] > 0) ->
    (order_max_item_weight[order_idx] <= max_item_weight[agent_idx])
);

% 6. Incompatibilités entre produits
% Si deux commandes sont incompatibles, elles ne peuvent pas être assignées au même agent
constraint forall(order_first in ORDERS, order_second in ORDERS where order_first < order_second /\ 
    incompatible[order_first, order_second]) (
    assignment[order_first] != assignment[order_second] \/ 
    assignment[order_first] == 0 \/ 
    assignment[order_second] == 0
);

% 7. EXTENSION 1 : Restrictions multi-niveaux (picking)
% Les robots (agent_type=0) ne peuvent accéder qu'aux niveaux 1-2.
% Une commande contenant des produits sur niveaux 3, 4 ou 5 doit être assignée à un humain.
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0) ->
    (not order_has_high_level[order_idx])
);
% Équivalent : (robot assigné ET order_has_high_level) -> impossible
% Les humains (agent_type=1) et chariots (agent_type=2) peuvent traiter toutes les commandes.

% 8. Gestion des chariots (simplifiée: un chariot nécessite qu'un humain soit disponible)
% Cette contrainte est vérifiée après résolution dans le code Python

% 9. EXTENSION 3 : Agents indisponibles (pannes, pauses)
% Un agent indisponible ne peut recevoir aucune commande
% Si agent_available[agent_idx] = false, alors aucune commande ne peut lui être assignée
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx) ->
    agent_available[agent_idx]
);
% Équivalent : si assignment[order_idx] = agent_idx, alors agent_available[agent_idx] doit être true

% 10. EXTENSION 3 : Commandes en rupture de stock
% Une commande en rupture de stock ne peut pas être assignée
% Si order_available[order_idx] = false, alors la commande doit rester non assignée (assignment = 0)
constraint forall(order_idx in ORDERS) (
    (not order_available[order_idx]) ->
    (assignment[order_idx] == 0)
);
% Équivalent : si order_available[order_idx] = false, alors assignment[order_idx] = 0

% OBJECTIF: Maximiser le nombre de commandes assignées avec priorité aux express
% EXTENSION 2 : Priorisation des commandes express
% On maximise d'abord les commandes express assignées, puis le total
% Utilisation d'un poids élevé (1000) pour garantir que les express sont toujours prioritaires
var int: num_express_assigned = sum(order_idx in ORDERS where order_is_express[order_idx]) 
    (assignment[order_idx] != 0);
var int: num_assigned = sum(order_idx in ORDERS) (assignment[order_idx] != 0);

% EXTENSION 4 : Coût des zones congestionnées
% Calculer le coût total lié aux zones congestionnées pour les commandes assignées
% Coût = somme des pénalités de temps pour les zones traversées
% Note: Ce coût est approximatif car on ne connaît pas le chemin exact dans ce modèle d'allocation
% Le calcul précis se fait au niveau Python lors de l'optimisation TSP
var float: congestion_cost = sum(order_idx in ORDERS where assignment[order_idx] != 0 /\ 
    order_zones[order_idx] >= 0 /\ order_zones[order_idx] < n_zones) (
    zone_congestion_penalty[order_zones[order_idx]]
);

% EXTENSION 5 : Bonus pour les allocations préférées par la politique RL
% Ajouter un bonus basé sur les scores de préférence RL pour les assignations effectuées
% Cela guide le solveur vers les allocations apprises comme optimales par le RL
var float: rl_bonus = sum(order_idx in ORDERS, agent_idx in AGENTS where assignment[order_idx] == agent_idx) (
    rl_preference_scores[order_idx, agent_idx]
);

% Objectif pondéré : 1000 * express + total - coût congestion + bonus RL
% On maximise l'objectif, donc on soustrait le coût de congestion et on ajoute le bonus RL
% Le facteur 0.01 permet de pénaliser les zones congestionnées sans dominer l'objectif principal
% Le facteur 0.1 pour le bonus RL permet de guider sans dominer les contraintes dures
var float: weighted_objective = 1000.0 * num_express_assigned + num_assigned - 0.01 * congestion_cost + 0.1 * rl_bonus;
solve maximize weighted_objective;

% OUTPUT
output [
    "assignment = ", show(assignment), ";\n",
    "num_assigned = ", show(num_assigned), ";\n",
    "num_express_assigned = ", show(num_express_assigned), ";\n",
    "weighted_objective = ", show(weighted_objective), ";\n",
    "% EXTENSION 3 : Agents indisponibles = ", show([agent_idx | agent_idx in AGENTS where not agent_available[agent_idx]]), ";\n",
    "% EXTENSION 3 : Commandes en rupture = ", show([order_idx | order_idx in ORDERS where not order_available[order_idx]]), ";\n",
    "% EXTENSION 4 : Coût congestion = ", show(congestion_cost), ";\n",
    "% EXTENSION 5 : Bonus RL = ", show(rl_bonus), ";\n"
];
