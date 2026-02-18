% Modèle MiniZinc pour TSP (tour le plus court)
% Utilise le fichier test.dzn pour les données
% Lancer (depuis le répertoire examples/) :
%   minizinc --solver COIN-BC test.mzn test.dzn
% Ou depuis la racine :
%   minizinc --solver COIN-BC examples/test.mzn examples/test.dzn

include "globals.mzn";

% PARAMÈTRES (définis dans test.dzn)
int: n_locations;
set of int: LOCATIONS = 1..n_locations;

array[LOCATIONS, LOCATIONS] of int: distance_matrix;

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
