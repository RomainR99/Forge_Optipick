int: N_ORDERS;
int: N_AGENTS;

array[1..N_ORDERS] of int: order_weight;       % *100
array[1..N_ORDERS] of int: order_volume;       % *100
array[1..N_ORDERS] of int: order_has_fragile;  % 0/1
array[1..N_ORDERS] of int: order_has_zoneC;    % 0/1

array[1..N_AGENTS] of int: agent_cap_weight;   % *100
array[1..N_AGENTS] of int: agent_cap_volume;   % *100
array[1..N_AGENTS] of int: agent_is_robot;     % 0/1

% décision : pour chaque commande, quel agent ?
array[1..N_ORDERS] of var 1..N_AGENTS: assign;

% --- Capacités (poids)
constraint
forall(a in 1..N_AGENTS)(
  sum(o in 1..N_ORDERS)(
    bool2int(assign[o] == a) * order_weight[o]
  ) <= agent_cap_weight[a]
);

% --- Capacités (volume)
constraint
forall(a in 1..N_AGENTS)(
  sum(o in 1..N_ORDERS)(
    bool2int(assign[o] == a) * order_volume[o]
  ) <= agent_cap_volume[a]
);

% --- Fragile => PAS robot
constraint
forall(o in 1..N_ORDERS)(
  order_has_fragile[o] = 1 ->
    agent_is_robot[assign[o]] = 0
);

% --- Zone C => PAS robot
constraint
forall(o in 1..N_ORDERS)(
  order_has_zoneC[o] = 1 ->
    agent_is_robot[assign[o]] = 0
);

% Objectif ultra simple : minimiser les commandes envoyées aux humains
var int: human_orders =
  sum(o in 1..N_ORDERS)( 1 - agent_is_robot[assign[o]] );

solve :: int_search(assign, first_fail, indomain_min, complete)
minimize human_orders;
