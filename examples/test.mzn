% Modèle MiniZinc autonome : TSP (tour le plus court)
% Lancer (avec solveur CP) :
%   minizinc --solver Gecode test.mzn

include "globals.mzn";

int: n_locations = 4;
set of int: LOCATIONS = 1..n_locations;

array[LOCATIONS, LOCATIONS] of int: distance_matrix = [|
    0,  3,  5,  7 |
    3,  0,  2,  4 |
    5,  2,  0,  2 |
    7,  4,  2,  0 |
|];

% next[i] = j : après i, on va à j
array[LOCATIONS] of var LOCATIONS: next;

% 1) Chaque location a exactement 1 sortie (implicite via next[i] défini)
% 2) Chaque location a exactement 1 entrée
constraint forall(i in LOCATIONS)(
  sum(j in LOCATIONS)(bool2int(next[j] = i)) = 1
);

% 3) Interdire les boucles i -> i
constraint forall(i in LOCATIONS)( next[i] != i );

% 4) Anti-sous-tours : impose un seul cycle qui couvre tout
constraint circuit(next);

var int: total_distance = sum(i in LOCATIONS)(distance_matrix[i, next[i]]);
solve minimize total_distance;

output [
  "\n========================================\n",
  "  TSP - Tour le plus court (MiniZinc)\n",
  "========================================\n",
  "next = ", show(next), "\n",
  "Distance totale minimale = ", show(total_distance), " unités\n",
  "========================================\n"
];
