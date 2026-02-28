# Rapport OptiPick — Optimisation de Tournées d'Entrepôt avec Coopération Humain-Robot

*Module Programmation Logique et par Contraintes — L2 Informatique*

---

## Page 1 — Résumé (Abstract)

OptiPick est un système d'optimisation conçu pour la gestion de la préparation de commandes dans un entrepôt de e-commerce où coexistent différents types d'agents : des préparateurs humains, des robots autonomes et des chariots semi-autonomes guidés par des humains. Le projet vise à résoudre plusieurs défis combinés : l'allocation optimale des commandes aux agents, le respect des contraintes de capacité et de compatibilité (incompatibilités de produits, restrictions des robots), l'optimisation des tournées de picking (problème du voyageur de commerce, TSP), et la minimisation du coût opérationnel global. Nous avons développé une approche hybride combinant la modélisation par contraintes (MiniZinc), les solveurs d'optimisation (OR-Tools CP-SAT et Routing), et un moteur Python pour le chargement des données, la validation des contraintes et la visualisation. Les résultats montrent que l'allocation optimisée (MiniZinc, CP-SAT) réduit significativement la distance parcourue et le coût par rapport à une heuristique gloutonne First-Fit, tout en garantissant le respect des contraintes dures. Le projet inclut une interface web (Streamlit/Flask) déployée en ligne pour la visualisation en temps réel et cinq extensions avancées : picking multi-niveaux, gestion dynamique des commandes express, gestion des pannes et aléas, zones congestionnées, et intégration d'apprentissage par renforcement.

---

## Page 2 — Problématique : comment nous nous y sommes pris

### Contexte et objectifs

La problématique centrale est de préparer un ensemble de commandes clients de manière optimale en assignant chaque commande à un agent capable de la traiter, tout en respectant de nombreuses contraintes et en minimisant un score composite (distance, temps, coût). Les agents ont des capacités et restrictions différentes : les robots sont rapides et peu coûteux mais ne peuvent pas accéder à la zone réfrigérée, transporter des objets fragiles ou des articles de plus de 10 kg ; les humains sont flexibles mais coûteux ; les chariots nécessitent un humain dédié. De plus, certains produits sont incompatibles entre eux (chimiques vs alimentaires, électroniques vs détergents, etc.).

### Approche méthodologique

Nous avons suivi une progression en six journées :

1. **Modélisation et allocation simple** : définition des classes (Warehouse, Product, Agent, Order), chargement des données JSON, calcul de distance Manhattan, allocation naïve First-Fit.
2. **Respect des contraintes dures** : vérification de capacité, incompatibilités, restrictions des robots, gestion des chariots ; intégration dans un module `constraints.py`.
3. **Optimisation des tournées (TSP)** : modélisation du problème du voyageur de commerce pour chaque agent, résolution via OR-Tools Routing, calcul du temps de tournée et vérification des deadlines.
4. **Allocation optimale et regroupement** : modélisation CSP avec OR-Tools CP-SAT et MiniZinc ; stratégie de batching (regroupement de commandes compatibles) ; comparaison First-Fit, MiniZinc, CP-SAT, Batching+CP-SAT.
5. **Optimisation du stockage et analyse** : analyse des patterns de commandes, réorganisation de l'entrepôt (produits fréquents près de l'entrée), simulation avant/après, analyse de coopération humain-robot.
6. **Interface web interactive** : application Flask et Streamlit avec visualisation en temps réel, animation des agents, formulaire d'ajout de commandes, choix de la méthode d'allocation.

Cette approche incrémentale nous a permis de valider chaque couche avant de passer à la suivante et d'obtenir un système complet et opérationnel.

---

## Page 3 — Matériel et méthode

### Environnement technique

- **Langage** : Python 3.8+
- **Moteur principal** : `main.py` orchestre le flux : chargement JSON → enrichissement des commandes → allocation (glouton ou optimisé) → calcul des métriques → rapport ou interface web.
- **Modules clés** : `loader.py` (parsing JSON), `models.py` (dataclasses), `constraints.py` (vérification), `allocation.py` (First-Fit et algorithmes gloutons), `allocation_cpsat.py` (OR-Tools CP-SAT), `minizinc_solver.py` (interface MiniZinc), `routing.py` (TSP avec OR-Tools), `batching.py` (regroupement de commandes).

### MiniZinc

Le modèle principal `models/allocation.mzn` formalise le problème d'allocation comme un CSP/COP. Les variables de décision `assignment[order] = agent` indiquent quelle commande est assignée à quel agent (0 = non assignée). Les contraintes incluent : capacité poids/volume, zones interdites par agent, objets fragiles, poids maximal par item, incompatibilités entre commandes, et les cinq extensions (multi-niveaux, express, pannes/aléas, congestion, RL). La fonction objectif pondère le nombre de commandes assignées, la priorité express, et les pénalités. Les données sont injectées dynamiquement depuis Python via l'API `minizinc` ; il n'y a pas de fichier `.dzn` fixe car les données proviennent des JSON et varient à chaque exécution. Solveurs supportés : CBC, Gecode, Chuffed, HiGHS.

### OR-Tools

- **CP-SAT** (`allocation_cpsat.py`) : résolution du problème d'allocation par programmation par contraintes entières. Variables binaires `x[i][j]` indiquant si la commande `i` est assignée à l'agent `j`. Contraintes de capacité, incompatibilités et restrictions. Objectif : minimiser coût ou distance.
- **Routing** (`routing.py`) : résolution du TSP pour calculer les tournées optimales de chaque agent. Utilise `create_distance_matrix()` (distance Manhattan) et `solve_tsp_with_ortools()` pour produire des séquences de collecte optimisées et vérifier les deadlines.

### Flux de données

Les fichiers `warehouse.json`, `products.json`, `agents.json`, `orders.json` sont chargés par `loader.py`, enrichis (poids, volume, zones, fragilité, incompatibilités), puis passés soit à l'algorithme First-Fit, soit à MiniZinc ou CP-SAT. Les résultats sont des dictionnaires `{order_id: agent_id}` utilisés pour le calcul des métriques (distance, temps, coût) et l'affichage dans l'interface web.

---

## Page 4 — Résultats : limites et performance

### Comparaison des méthodes d'allocation

Sur un jeu de 10 commandes (données de test), les métriques observées sont les suivantes :

| Méthode         | Commandes assignées | Distance (proxy) | Temps (min) | Coût (€) |
|-----------------|---------------------|------------------|-------------|----------|
| First-Fit       | 10/10               | 182              | 15,3        | 3,82     |
| MiniZinc        | 9/10                | 163              | 13,1        | 2,18     |
| CP-SAT          | 9/10                | 167              | 14,4        | 1,68     |
| Batching + CP-SAT | 9/10              | 167              | 14,8        | 0,74     |

- **First-Fit** : rapide et garantit souvent d'assigner toutes les commandes, mais sans optimisation ; distance et coût plus élevés.
- **MiniZinc et CP-SAT** : réduisent la distance d'environ 10–18 % et le coût de 40–60 %, au prix parfois de commandes non assignées lorsque les contraintes sont trop strictes.
- **Batching + CP-SAT** : permet le regroupement de commandes compatibles ; dans nos tests, le coût chute à 0,74 € grâce à une meilleure utilisation des agents.

### Optimisation TSP

L'optimisation des tournées avec OR-Tools Routing réduit typiquement la distance de 15–20 % par rapport à une simple estimation par somme des distances entrée ↔ emplacement. La vérification des deadlines (`check_deadlines`) permet de s'assurer que les tournées respectent les contraintes temporelles.

### Limites

1. **Évolutivité** : Pour un grand nombre de commandes et d'agents, les solveurs MiniZinc et CP-SAT peuvent devenir lents ; des heuristiques ou des timeouts sont nécessaires.
2. **Données synthétiques** : Les données (warehouse, products, agents, orders) sont simulées ; une validation sur des données réelles d'entrepôt reste à faire.
3. **Modélisation simplifiée** : La distance utilisée reste une estimation ou une proxy ; les temps de picking réels (ramassage, scan) ne sont pas détaillés.
4. **Extensions** : Les extensions (multi-niveaux, congestion, RL) sont implémentées dans le modèle MiniZinc mais n'ont pas été évaluées exhaustivement en termes de gain mesurable.
5. **Interface temps réel** : L'animation des agents est une visualisation indicative ; elle ne reflète pas un suivi GPS ou un système de localisation réel.

---

## Page 5 — Conclusion : enseignements et perspectives

### Enseignements

- **Programmation par contraintes** : La modélisation en CSP/COP (MiniZinc, CP-SAT) est adaptée à l'allocation avec contraintes complexes (capacité, incompatibilités, restrictions). La séparation entre modèle et données facilite l'évolution et la maintenance.
- **Hybridation** : Combiner une heuristique rapide (First-Fit) pour les cas simples et des solveurs exacts (MiniZinc, CP-SAT) pour l'optimisation offre un bon compromis performance/qualité.
- **TSP et routing** : L'optimisation des tournées apporte un gain mesurable sur la distance ; OR-Tools Routing est facilement intégrable dans un pipeline Python.
- **Architecture modulaire** : Le découpage loader → models → constraints → allocation → routing permet des tests unitaires et l'ajout de nouvelles méthodes sans réécriture majeure.

### Si l'on continuait le projet

1. **Validation sur données réelles** : Partenariat avec un entrepôt pour tester sur des flux de commandes et des configurations réelles.
2. **Optimisation multi-objectif** : Ponderer explicitement distance, temps, coût et équilibrage de charge avec des méthodes Pareto ou des poids configurables par l'utilisateur.
3. **Temps de résolution** : Fixer des timeouts, des objectifs de gap, et des stratégies de dégradation (fallback vers First-Fit si le solveur dépasse le temps imparti).
4. **Extensions opérationnelles** : Intégrer les pannes, la congestion et la dynamique des commandes dans un environnement de simulation continu pour évaluer la robustesse.
5. **Apprentissage par renforcement** : Pousser l'extension RL pour apprendre des politiques d'allocation adaptatives à partir de données historiques.
6. **Interface et déploiement** : Améliorer l'ergonomie de l'interface Streamlit, ajouter des tableaux de bord de suivi et une API REST pour une intégration avec des systèmes de gestion d'entrepôt (WMS).

En résumé, OptiPick démontre la faisabilité d'un système d'optimisation de tournées d'entrepôt fondé sur la programmation par contraintes et l'optimisation combinatoire, avec une base technique solide et des pistes claires pour une industrialisation future.

---

## Bibliographie

[1] R. Rossi, F. Stuckey, P. J. Stuckey, and G. Tack. *MiniZinc 2.0: A declarative modeling language for constraint programming*. In Proc. of the Workshop on CP Solvers: Modeling, Applications, Integration, and Standardization, 2012.

[2] L. Perron and V. Furnon. *OR-Tools*. Google. https://developers.google.com/optimization, 2024.

[3] J.-C. Régin and T. A. LePape. *Combining constraint programming and local search for the job-shop problem*. In Proc. CP’98, LNCS 1520, pp. 271–285. Springer, 1998.

[4] G. L. Nemhauser and L. A. Wolsey. *Integer and Combinatorial Optimization*. Wiley, 1988.

[5] G. Gutin and A. P. Punnen (eds.). *The Traveling Salesman Problem and Its Variations*. Springer, 2006.

[6] W. J. van Hoeve. *The All Different constraint: A survey*. Artificial Intelligence, 174(12-13):852–864, 2010.

[7] A. Verstichel et al. *A combinatorial Benders’ decomposition for the lock scheduling problem*. Computers & Operations Research, 54:117–128, 2015.

[8] M. W. P. Savelsbergh and M. Sol. *The general pickup and delivery problem*. Transportation Science, 29(1):17–29, 1995.

[9] Python Software Foundation. *Python 3.8+ Documentation*. https://docs.python.org/3/, 2024.

[10] Streamlit Inc. *Streamlit Documentation*. https://docs.streamlit.io/, 2024.

---

*Projet OptiPick — Contributeurs : Nermine, Imen, Hamid, Romain*
