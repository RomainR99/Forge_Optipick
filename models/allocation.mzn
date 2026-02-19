int: N_ORDERS;
int: N_AGENTS;

array[1..N_ORDERS] of int: order_weight;          % *100
array[1..N_ORDERS] of int: order_volume;          % *100
array[1..N_ORDERS] of int: order_has_fragile;     % 0/1
array[1..N_ORDERS] of int: order_has_zoneC;       % 0/1
array[1..N_ORDERS] of int: order_has_heavy_item;  % 0/1  (C3)
array[1..N_ORDERS] of int: order_is_incompatible; % 0/1  (C2)
array[1..N_ORDERS] of int: order_slack_sec;       % (C5)

array[1..N_AGENTS] of int: agent_cap_weight;      % *100
array[1..N_AGENTS] of int: agent_cap_volume;      % *100
array[1..N_AGENTS] of int: agent_is_robot;        % 0/1

% Matrice temps estimé (C5)
array[1..N_ORDERS, 1..N_AGENTS] of int: time_need_sec;

% Décision
array[1..N_ORDERS] of var 1..N_AGENTS: assign;

% --------------------
% Capacités
% --------------------
constraint
forall(a in 1..N_AGENTS)(
  sum(o in 1..N_ORDERS)(
    bool2int(assign[o] == a) * order_weight[o]
  ) <= agent_cap_weight[a]
);


constraint
forall(a in 1..N_AGENTS)(
  sum(o in 1..N_ORDERS)(
    bool2int(assign[o] == a) * order_volume[o]
  ) <= agent_cap_volume[a]
);

% --------------------
% C2 : incompatibilités
% --------------------
constraint forall(o in 1..N_ORDERS)(
  order_is_incompatible[o] = 0
);

% --------------------
% C1 déjà : fragile -> pas robot
% --------------------
constraint forall(o in 1..N_ORDERS)(
  order_has_fragile[o] = 1 -> agent_is_robot[assign[o]] = 0
);

% --------------------
% Ajout : Zone C -> pas robot
% --------------------
constraint forall(o in 1..N_ORDERS)(
  order_has_zoneC[o] = 1 -> agent_is_robot[assign[o]] = 0
);

% --------------------
% C3 : item > 10kg -> pas robot
% --------------------
constraint forall(o in 1..N_ORDERS)(
  order_has_heavy_item[o] = 1 -> agent_is_robot[assign[o]] = 0
);

% --------------------
% C5 : deadlines (simple & défendable)
% --------------------
constraint forall(o in 1..N_ORDERS)(
  time_need_sec[o, assign[o]] <= order_slack_sec[o]
);

% Objectif minimal : minimiser nombre de commandes envoyées aux humains
var int: human_orders = sum(o in 1..N_ORDERS)( 1 - agent_is_robot[assign[o]] );

solve :: int_search(assign, first_fail, indomain_min, complete)
minimize human_orders;
