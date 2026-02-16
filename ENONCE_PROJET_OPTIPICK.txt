═══════════════════════════════════════════════════════════════════════════════
                        UNIVERSITÉ - L2 INFORMATIQUE
                 PROGRAMMATION LOGIQUE ET PAR CONTRAINTES

                           PROJET DE FIN DE MODULE

                               OPTIPICK
                    Optimisation de Tournées d'Entrepôt
              avec Coopération Humain-Robot et Gestion du Stockage

═══════════════════════════════════════════════════════════════════════════════

TABLE DES MATIÈRES
═══════════════════════════════════════════════════════════════════════════════

1. CONTEXTE ET MOTIVATION
2. DESCRIPTION DU PROBLÈME
3. DONNÉES FOURNIES
4. CONTRAINTES DU SYSTÈME
5. OBJECTIFS ET CRITÈRES D'OPTIMISATION
6. PROGRESSION PAR JOURNÉES
7. EXTENSIONS POSSIBLES
8. LIVRABLES ATTENDUS
9. BARÈME ET ÉVALUATION
10. CONSEILS TECHNIQUES
11. RESSOURCES


═══════════════════════════════════════════════════════════════════════════════
1. CONTEXTE ET MOTIVATION
═══════════════════════════════════════════════════════════════════════════════

1.1 CONTEXTE INDUSTRIEL
───────────────────────────────────────────────────────────────────────────────

L'entreprise **OptiLog** gère un entrepôt de e-commerce moderne où coexistent :
- **Préparateurs humains** : Expérimentés, flexibles, mais coûteux
- **Robots autonomes** : Rapides, infatigables, mais limités
- **Chariots semi-autonomes** : Guidés par humains, capacité accrue

Chaque jour, des **commandes clients** arrivent. Chaque commande contient une
liste de produits à prélever dans l'entrepôt. L'objectif est d'organiser la
**préparation optimale** de ces commandes.


1.2 PROBLÉMATIQUE
───────────────────────────────────────────────────────────────────────────────

Les défis à résoudre :

1. **Planification des tournées**
   - Quelle séquence de produits ramasser pour chaque agent ?
   - Comment minimiser les distances parcourues ?

2. **Allocation agents-commandes**
   - Quelles commandes assigner aux humains vs robots ?
   - Comment équilibrer la charge de travail ?

3. **Respect des contraintes**
   - Capacité limitée des chariots/robots
   - Produits incompatibles (alimentaire/chimique)
   - Zones réservées (frigo accessible qu'aux humains)

4. **Optimisation du stockage**
   - Produits fréquents près de l'entrée
   - Grouper produits souvent commandés ensemble
   - Réorganiser l'entrepôt périodiquement

5. **Coopération humain-robot**
   - Tâches complexes → humains
   - Tâches répétitives → robots
   - Synchronisation et non-conflit


1.3 EXEMPLE CONCRET
───────────────────────────────────────────────────────────────────────────────

COMMANDE #42 :
- 2× Livre "Python pour débutants"
- 1× Clavier mécanique
- 1× Souris gaming

STOCKAGE :
- Livres : Zone A, étagère 3, niveau 2
- Claviers : Zone B, étagère 7, niveau 1
- Souris : Zone B, étagère 8, niveau 1

AGENTS DISPONIBLES :
- Robot R1 : Capacité 15kg, vitesse 2m/s
- Humain H1 : Capacité 30kg, vitesse 1.5m/s

DÉCISIONS À PRENDRE :
1. Qui prépare la commande ? (H1 ou R1 ?)
2. Dans quel ordre visiter les emplacements ? (A3-B7-B8 ou autre ?)
3. Peut-on grouper avec d'autres commandes ?


═══════════════════════════════════════════════════════════════════════════════
2. DESCRIPTION DU PROBLÈME
═══════════════════════════════════════════════════════════════════════════════

2.1 ENTREPÔT
───────────────────────────────────────────────────────────────────────────────

L'entrepôt est modélisé comme une **grille 2D** (pour simplifier).

ZONES :
- Zone A (Électronique) : 20 emplacements
- Zone B (Livres/Médias) : 15 emplacements
- Zone C (Alimentaire) : 10 emplacements
- Zone D (Hygiène/Chimie) : 10 emplacements
- Zone E (Textile) : 15 emplacements

DISPOSITION (exemple simplifié 10×8) :

    0   1   2   3   4   5   6   7   8   9
  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
0 │ E │ A │ A │ A │ A │ B │ B │ B │ C │ C │
  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
1 │   │ A │ A │ A │ A │ B │ B │ B │ C │ C │
  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
2 │   │   │   │   │   │   │   │   │   │   │  (allée)
  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
3 │ E │ A │ A │ A │ A │ B │ B │ B │ C │ C │
  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
4 │ E │ A │ A │ A │ A │ B │ B │ B │ C │ C │
  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
5 │   │   │   │   │   │   │   │   │   │   │  (allée)
  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
6 │ E │ D │ D │ D │ D │ E │ E │ E │ E │ E │
  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤
7 │ E │ D │ D │ D │ D │ E │ E │ E │ E │ E │
  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘

E = Entrée/Sortie

Chaque case a des coordonnées (x, y).
Distance entre deux cases = distance de Manhattan : |x₁-x₂| + |y₁-y₂|


2.2 PRODUITS
───────────────────────────────────────────────────────────────────────────────

Base de 100 produits avec :
- ID unique
- Nom
- Catégorie (électronique, livre, alimentaire, chimie, textile)
- Poids (kg)
- Volume (dm³)
- Emplacement (x, y)
- Fréquence de commande (faible/moyenne/élevée)
- Incompatibilités (liste d'autres produits)

EXEMPLE :

Product_001:
  name: "Laptop Dell XPS"
  category: "electronics"
  weight: 2.5
  volume: 8
  location: (1, 1)
  frequency: "high"
  incompatible_with: ["Product_042"]  # Produit chimique

Product_042:
  name: "Détergent industriel"
  category: "chemical"
  weight: 1.5
  volume: 3
  location: (2, 6)
  frequency: "medium"
  incompatible_with: ["Product_001", "Product_055", ...]  # Électronique, alimentaire


2.3 AGENTS (PRÉPARATEURS)
───────────────────────────────────────────────────────────────────────────────

Trois types d'agents :

┌─────────────┬──────────┬──────────┬────────┬──────────────────────────┐
│ TYPE        │ QUANTITÉ │ CAPACITÉ │ VITESSE│ RESTRICTIONS             │
│             │          │ (kg/dm³) │ (m/s)  │                          │
├─────────────┼──────────┼──────────┼────────┼──────────────────────────┤
│ Robot       │ 3        │ 20kg     │ 2.0    │ Pas de Zone C (frigo)    │
│ (R1, R2, R3)│          │ 30dm³    │        │ Produits légers only     │
│             │          │          │        │ Pas d'objets fragiles    │
├─────────────┼──────────┼──────────┼────────┼──────────────────────────┤
│ Humain      │ 2        │ 35kg     │ 1.5    │ Aucune restriction       │
│ (H1, H2)    │          │ 50dm³    │        │ Peut tout faire          │
│             │          │          │        │                          │
├─────────────┼──────────┼──────────┼────────┼──────────────────────────┤
│ Chariot     │ 2        │ 50kg     │ 1.2    │ Guidé par humain         │
│ (C1, C2)    │          │ 80dm³    │        │ Nécessite un humain      │
│             │          │          │        │ assigné (H1 ou H2)       │
└─────────────┴──────────┴──────────┴────────┴──────────────────────────┘

COÛTS D'UTILISATION (par heure) :
- Robot : 5€/h (électricité + amortissement)
- Humain : 25€/h (salaire)
- Chariot : 3€/h (quand utilisé avec humain)


2.4 COMMANDES
───────────────────────────────────────────────────────────────────────────────

Chaque journée : 20-30 commandes à préparer

STRUCTURE D'UNE COMMANDE :
- ID commande
- Liste de produits (avec quantités)
- Heure de réception
- Deadline (délai de préparation)
- Priorité (standard / express)

EXEMPLE :

Order_001:
  received: 08:00
  deadline: 10:00  (2h pour préparer)
  priority: "express"
  items:
    - product_id: Product_012
      quantity: 2
    - product_id: Product_034
      quantity: 1
    - product_id: Product_067
      quantity: 1
  total_weight: 5.5 kg
  total_volume: 12 dm³


═══════════════════════════════════════════════════════════════════════════════
3. DONNÉES FOURNIES
═══════════════════════════════════════════════════════════════════════════════

3.1 FICHIERS JSON
───────────────────────────────────────────────────────────────────────────────

warehouse.json
───────────────
{
  "dimensions": {"width": 10, "height": 8},
  "zones": {
    "A": {"name": "Electronics", "coords": [[1,0], [1,1], ...]},
    "B": {"name": "Books", "coords": [[5,0], [5,1], ...]},
    "C": {"name": "Food", "coords": [[8,0], [8,1], ...]},
    "D": {"name": "Chemical", "coords": [[1,6], [1,7], ...]},
    "E": {"name": "Textile", "coords": [[0,0], [0,3], ...]}
  },
  "entry_point": [0, 0]
}


products.json
─────────────
[
  {
    "id": "Product_001",
    "name": "Laptop Dell XPS",
    "category": "electronics",
    "weight": 2.5,
    "volume": 8,
    "location": [1, 1],
    "frequency": "high",
    "fragile": true,
    "incompatible_with": ["Product_042", "Product_055"]
  },
  {
    "id": "Product_002",
    "name": "USB Cable",
    "category": "electronics",
    "weight": 0.1,
    "volume": 0.5,
    "location": [2, 1],
    "frequency": "very_high",
    "fragile": false,
    "incompatible_with": []
  },
  ...
]


agents.json
───────────
[
  {
    "id": "R1",
    "type": "robot",
    "capacity_weight": 20,
    "capacity_volume": 30,
    "speed": 2.0,
    "cost_per_hour": 5,
    "restrictions": {
      "no_zones": ["C"],
      "no_fragile": true,
      "max_item_weight": 10
    }
  },
  {
    "id": "H1",
    "type": "human",
    "capacity_weight": 35,
    "capacity_volume": 50,
    "speed": 1.5,
    "cost_per_hour": 25,
    "restrictions": {}
  },
  {
    "id": "C1",
    "type": "cart",
    "capacity_weight": 50,
    "capacity_volume": 80,
    "speed": 1.2,
    "cost_per_hour": 3,
    "restrictions": {
      "requires_human": true
    }
  },
  ...
]


orders.json
───────────
[
  {
    "id": "Order_001",
    "received_time": "08:00",
    "deadline": "10:00",
    "priority": "express",
    "items": [
      {"product_id": "Product_012", "quantity": 2},
      {"product_id": "Product_034", "quantity": 1}
    ]
  },
  {
    "id": "Order_002",
    "received_time": "08:15",
    "deadline": "12:00",
    "priority": "standard",
    "items": [
      {"product_id": "Product_002", "quantity": 5},
      {"product_id": "Product_045", "quantity": 1},
      {"product_id": "Product_078", "quantity": 2}
    ]
  },
  ...
]


3.2 MÉTRIQUES DE PERFORMANCE
───────────────────────────────────────────────────────────────────────────────

Votre solution sera évaluée sur :

1. **Distance totale parcourue** (minimiser)
2. **Temps total de préparation** (minimiser)
3. **Coût opérationnel** (minimiser)
4. **Respect des deadlines** (100% obligatoire)
5. **Équilibrage de charge** entre agents (optimiser)
6. **Taux d'utilisation** des robots vs humains (maximiser robots = moins cher)


═══════════════════════════════════════════════════════════════════════════════
4. CONTRAINTES DU SYSTÈME
═══════════════════════════════════════════════════════════════════════════════

4.1 CONTRAINTES DURES (OBLIGATOIRES)
───────────────────────────────────────────────────────────────────────────────

C1. CAPACITÉ DES AGENTS
    Pour chaque agent, à tout moment :
    - Poids total transporté ≤ capacité_poids
    - Volume total transporté ≤ capacité_volume

C2. INCOMPATIBILITÉS DE PRODUITS
    Deux produits incompatibles ne peuvent pas être dans le même chariot
    en même temps.

    Exemple : Produit chimique + Produit alimentaire → INTERDIT

C3. RESTRICTIONS DES ROBOTS
    - Robots ne peuvent pas entrer en Zone C (réfrigérée)
    - Robots ne peuvent pas transporter objets fragiles
    - Robots ne peuvent pas transporter objets > 10kg individuellement

C4. CHARIOTS NÉCESSITENT UN HUMAIN
    Un chariot C1 ou C2 ne peut fonctionner que si :
    - Un humain (H1 ou H2) lui est assigné
    - Cet humain n'est pas assigné à autre chose simultanément

C5. DEADLINES
    Chaque commande doit être préparée avant sa deadline.

C6. COMPLÉTUDE DES COMMANDES
    Toutes les commandes doivent être préparées (aucune abandonnée).

C7. PAS DE COLLISION
    Deux agents ne peuvent pas occuper la même case simultanément.
    (Simplification : on ignore les trajectoires, on vérifie juste les zones)


4.2 CONTRAINTES SOUPLES (OPTIMISATION)
───────────────────────────────────────────────────────────────────────────────

S1. MINIMISER DISTANCE TOTALE
    Somme des distances parcourues par tous les agents.

S2. MINIMISER TEMPS TOTAL
    Temps de fin du dernier agent à terminer sa tournée.

S3. MINIMISER COÛT
    Coût = Σ(temps_utilisation_agent × coût_horaire_agent)

S4. ÉQUILIBRER LA CHARGE
    Éviter qu'un agent soit surchargé pendant que d'autres sont inactifs.

S5. PRIVILÉGIER LES ROBOTS
    Pour réduire les coûts, assigner en priorité aux robots quand possible.

S6. GROUPER LES COMMANDES
    Si deux commandes ont des produits proches, les préparer ensemble
    peut réduire la distance.

S7. MINIMISER LES ALLERS-RETOURS
    Organiser les tournées pour éviter de repasser plusieurs fois par
    le même endroit.


═══════════════════════════════════════════════════════════════════════════════
5. OBJECTIFS ET CRITÈRES D'OPTIMISATION
═══════════════════════════════════════════════════════════════════════════════

5.1 FONCTION OBJECTIF
───────────────────────────────────────────────────────────────────────────────

OBJECTIF PRINCIPAL : Minimiser le score total

Score = w₁ × Distance_totale
      + w₂ × Temps_total
      + w₃ × Coût_total
      + w₄ × Pénalité_déséquilibre
      + w₅ × Pénalité_retard

Poids suggérés :
- w₁ = 1    (distance : 1 point par mètre)
- w₂ = 10   (temps : 10 points par minute)
- w₃ = 5    (coût : 5 points par euro)
- w₄ = 50   (déséquilibre : pénalité importante)
- w₅ = 1000 (retard : pénalité TRÈS importante)

Pénalité_retard = 1000 × nombre_commandes_en_retard (à éviter absolument !)


5.2 INDICATEURS DE QUALITÉ
───────────────────────────────────────────────────────────────────────────────

Votre rapport devra inclure :

1. **Taux de respect des deadlines** : 100% obligatoire

2. **Distance moyenne par commande** : à minimiser

3. **Utilisation des agents** :
   - % temps actif pour chaque agent
   - Équilibrage (écart-type entre agents)

4. **Efficacité économique** :
   - Coût moyen par commande
   - % d'utilisation des robots vs humains

5. **Qualité des tournées** :
   - Nombre moyen d'emplacements visités par tournée
   - Efficacité du regroupement de commandes


═══════════════════════════════════════════════════════════════════════════════
6. PROGRESSION PAR JOURNÉES
═══════════════════════════════════════════════════════════════════════════════

Le projet se décompose en 5 journées de difficulté croissante.

JOUR 1 : MODÉLISATION ET ALLOCATION SIMPLE
───────────────────────────────────────────────────────────────────────────────

OBJECTIFS :
- Modéliser le problème (entrepôt, produits, agents, commandes)
- Implémenter l'allocation basique commandes → agents
- Calculer les distances

TÂCHES :

1.1) CHARGEMENT DES DONNÉES
     Lire et parser les 4 fichiers JSON fournis

1.2) MODÉLISATION OBJET
     Créer les classes Python :
     - Warehouse
     - Product
     - Agent (+ sous-classes Robot, Human, Cart)
     - Order
     - Location (x, y)

1.3) CALCUL DE DISTANCE
     Implémenter distance de Manhattan entre deux emplacements

1.4) ALLOCATION NAÏVE
     Stratégie simple : First-Fit
     - Pour chaque commande (par ordre d'arrivée)
     - Assigner au premier agent ayant la capacité suffisante
     - Ignorer les restrictions pour l'instant

1.5) ÉVALUATION
     Calculer et afficher :
     - Nombre de commandes assignées
     - Distance totale estimée (somme des distances produits-entrée)
     - Utilisation de chaque agent

LIVRABLE JOUR 1 :
- Code Python fonctionnel
- Sortie console montrant l'allocation
- Rapport court (1 page) : choix de modélisation


JOUR 2 : RESPECT DES CONTRAINTES DURES
───────────────────────────────────────────────────────────────────────────────

OBJECTIFS :
- Intégrer toutes les contraintes obligatoires
- Vérifier la faisabilité des allocations

TÂCHES :

2.1) VÉRIFICATION DE CAPACITÉ
     Pour chaque agent, vérifier :
     - Poids total ≤ capacité
     - Volume total ≤ capacité

2.2) VÉRIFICATION D'INCOMPATIBILITÉS
     Implémenter la fonction :
     can_combine(products) → bool
     Retourne False si deux produits incompatibles

2.3) RESTRICTIONS DES ROBOTS
     Vérifier :
     - Pas de zone interdite
     - Pas d'objets fragiles
     - Pas d'objets trop lourds

2.4) GESTION DES CHARIOTS
     Implémenter :
     - Association chariot ↔ humain
     - Vérifier qu'un humain n'est pas sur-assigné

2.5) ALLOCATION AVEC CONTRAINTES
     Modifier l'allocation du Jour 1 pour respecter toutes les contraintes.
     Algorithme glouton amélioré :
     - Pour chaque commande
     - Tester chaque agent dans l'ordre (robots d'abord)
     - Vérifier toutes les contraintes
     - Assigner au premier agent valide

LIVRABLE JOUR 2 :
- Code mis à jour
- Tests unitaires pour les contraintes
- Rapport (1-2 pages) : gestion des contraintes


JOUR 3 : OPTIMISATION DES TOURNÉES (TSP)
───────────────────────────────────────────────────────────────────────────────

OBJECTIFS :
- Optimiser l'ordre de visite des emplacements pour chaque agent
- Résoudre un TSP (Traveling Salesman Problem) par agent

TÂCHES :

3.1) MODÉLISATION TSP
     Pour un agent avec une liste de produits à ramasser :
     - Extraire les emplacements uniques
     - Ajouter l'entrée (point de départ et retour)
     - Calculer la matrice de distances

3.2) RÉSOLUTION TSP - HEURISTIQUE
     Implémenter au moins une méthode :

     Option A : Plus proche voisin (Nearest Neighbor)
     - Commencer à l'entrée
     - À chaque étape, aller à l'emplacement non visité le plus proche
     - Retourner à l'entrée

     Option B : 2-opt
     - Partir d'une solution initiale
     - Améliorer en échangeant des paires d'arêtes

     Option C : Utiliser OR-Tools (recommandé)
     - Modéliser comme TSP avec OR-Tools Routing

3.3) CALCUL DU TEMPS DE TOURNÉE
     Pour chaque agent :
     - Temps = distance_totale / vitesse_agent
     - Ajouter temps de ramassage (ex: 30s par produit)

3.4) INTÉGRATION
     Modifier l'allocation pour :
     - Assigner les commandes
     - Calculer la tournée optimale pour chaque agent
     - Vérifier que toutes les deadlines sont respectées

LIVRABLE JOUR 3 :
- Code avec optimisation TSP
- Comparaison avant/après optimisation
- Visualisation des tournées (optionnel mais apprécié)


JOUR 4 : ALLOCATION OPTIMALE ET REGROUPEMENT
───────────────────────────────────────────────────────────────────────────────

OBJECTIFS :
- Optimiser l'allocation commandes → agents (pas juste glouton)
- Grouper des commandes compatibles pour réduire la distance

TÂCHES :

4.1) MODÉLISATION CSP
     Modéliser l'allocation comme un problème de satisfaction de contraintes :

     Variables :
     - assign[order_i] ∈ {agents disponibles}

     Contraintes :
     - Capacité des agents respectée
     - Incompatibilités respectées
     - Restrictions respectées
     - Deadlines respectées

     Objectif :
     - Minimiser distance totale ou coût total

4.2) RÉSOLUTION AVEC OR-TOOLS CP-SAT
     Implémenter le modèle avec OR-Tools :
     - Définir les variables
     - Ajouter toutes les contraintes
     - Fonction objectif : minimiser distance ou coût
     - Résoudre

4.3) REGROUPEMENT DE COMMANDES (BATCHING)
     Stratégie :
     - Identifier les commandes avec des produits proches
     - Grouper si :
       * Même deadline (ou compatibles)
       * Capacité agent suffisante
       * Pas d'incompatibilités
     - Calculer la tournée pour le groupe

4.4) COMPARAISON DES STRATÉGIES
     Comparer :
     - Allocation gloutonne (Jour 2)
     - Allocation optimisée (CP-SAT)
     - Avec/sans regroupement

     Métriques : distance, temps, coût

LIVRABLE JOUR 4 :
- Code avec optimisation complète
- Comparaison quantitative des approches
- Graphiques de performance


JOUR 5 : OPTIMISATION DU STOCKAGE ET ANALYSE AVANCÉE
───────────────────────────────────────────────────────────────────────────────

OBJECTIFS :
- Réorganiser l'entrepôt pour améliorer les performances futures
- Analyse de données et recommandations

TÂCHES :

5.1) ANALYSE DES PATTERNS DE COMMANDES
     À partir de l'historique :
     - Produits les plus commandés
     - Paires de produits souvent commandées ensemble
     - Zones les plus visitées

5.2) OPTIMISATION DU STOCKAGE
     Proposer une réorganisation :

     Règle 1 : Produits fréquents près de l'entrée
     - Calculer fréquence de chaque produit
     - Placer top 20% en Zone A (proche entrée)

     Règle 2 : Grouper produits souvent co-commandés
     - Calculer affinités entre produits (combien de fois ensemble ?)
     - Placer produits affinitaires dans emplacements voisins

     Règle 3 : Respecter les contraintes de zones
     - Alimentaire reste en zone réfrigérée (C)
     - Chimie séparée (D)

5.3) SIMULATION AVANT/APRÈS
     - Générer 50 commandes test
     - Simuler avec stockage actuel
     - Simuler avec stockage optimisé
     - Comparer les performances

5.4) ANALYSE COOPÉRATION HUMAIN-ROBOT
     Analyser :
     - % de commandes traitées par robots vs humains
     - Types de commandes mieux adaptées à chaque type d'agent
     - Recommandations pour améliorer la répartition

     Questions à répondre :
     - Faut-il acheter plus de robots ?
     - Quels types de produits automatiser en priorité ?
     - Comment former les humains pour tâches à plus forte valeur ?

5.5) DASHBOARD DE MONITORING
     Créer une visualisation (matplotlib ou autre) montrant :
     - Carte de l'entrepôt avec emplacements
     - Tournées des agents (trajets)
     - Statistiques en temps réel
     - Heatmap des zones visitées

LIVRABLE JOUR 5 :
- Proposition de réorganisation de l'entrepôt
- Résultats de simulation avant/après
- Dashboard de visualisation
- Rapport d'analyse (3-5 pages)


═══════════════════════════════════════════════════════════════════════════════
7. EXTENSIONS POSSIBLES
═══════════════════════════════════════════════════════════════════════════════

Pour les groupes qui terminent en avance ou veulent aller plus loin :

EXTENSION 1 : PICKING MULTI-NIVEAUX
───────────────────────────────────────────────────────────────────────────────
Ajouter une 3ème dimension :
- Chaque étagère a plusieurs niveaux (1-5)
- Robots ne peuvent accéder qu'aux niveaux 1-2
- Humains peuvent atteindre tous les niveaux (avec escabeau)
- Temps d'accès varie selon le niveau

Impact : Complexité accrue de l'allocation


EXTENSION 2 : GESTION DYNAMIQUE
───────────────────────────────────────────────────────────────────────────────
Nouvelles commandes arrivent en temps réel :
- Initialement : 10 commandes
- Toutes les heures : 5 nouvelles commandes
- Il faut ré-optimiser à chaque arrivée
- Commandes express prioritaires

Défi : Replanning rapide


EXTENSION 3 : PANNES ET ALÉAS
───────────────────────────────────────────────────────────────────────────────
Gérer les imprévus :
- Un robot tombe en panne (20% de chance)
- Un humain prend une pause (toutes les 2h, 15min)
- Un produit est en rupture de stock (réassigner commande)

Solution : Robustesse et résilience


EXTENSION 4 : ZONES CONGESTIONNÉES
───────────────────────────────────────────────────────────────────────────────
Certaines zones sont plus lentes :
- Allées étroites : vitesse réduite de 50%
- Zones encombrées : +30s par passage
- Zones à sens unique : contraintes de circulation

Modélisation : Graphe avec poids variables


EXTENSION 5 : APPRENTISSAGE PAR RENFORCEMENT
───────────────────────────────────────────────────────────────────────────────
Utiliser RL pour apprendre la stratégie :
- État : configuration entrepôt + commandes en attente
- Actions : assigner commande à agent, ordre de visite
- Récompense : -distance -coût +respect_deadline

Outil : Stable-Baselines3 ou similaire


EXTENSION 6 : INTERFACE WEB
───────────────────────────────────────────────────────────────────────────────
Créer une interface utilisateur :
- Affichage en temps réel de l'entrepôt
- Animation des agents
- Formulaire pour ajouter des commandes
- Statistiques en direct

Framework : Flask/Django + JavaScript


═══════════════════════════════════════════════════════════════════════════════
8. LIVRABLES ATTENDUS
═══════════════════════════════════════════════════════════════════════════════

8.1 CODE SOURCE
───────────────────────────────────────────────────────────────────────────────

STRUCTURE ATTENDUE :

optipick/
│
├── data/
│   ├── warehouse.json
│   ├── products.json
│   ├── agents.json
│   └── orders.json
│
├── src/
│   ├── __init__.py
│   ├── models.py          # Classes Warehouse, Product, Agent, Order
│   ├── loader.py          # Chargement des données JSON
│   ├── constraints.py     # Vérification des contraintes
│   ├── allocation.py      # Algorithmes d'allocation
│   ├── routing.py         # Optimisation des tournées (TSP)
│   ├── optimization.py    # Modèle CSP avec OR-Tools
│   ├── storage.py         # Optimisation du stockage
│   ├── visualization.py   # Visualisation et dashboard
│   └── utils.py           # Fonctions utilitaires
│
├── tests/
│   ├── test_constraints.py
│   ├── test_allocation.py
│   └── test_routing.py
│
├── results/
│   ├── allocation_results.json
│   ├── routes.json
│   └── metrics.json
│
├── docs/
│   └── rapport.pdf
│
├── requirements.txt
├── README.md
└── main.py               # Point d'entrée du programme


QUALITÉ DU CODE :
- Code commenté et bien structuré
- Respect PEP 8 (style Python)
- Fonctions courtes et modulaires
- Tests unitaires (au moins 10 tests)


8.2 RAPPORT TECHNIQUE
───────────────────────────────────────────────────────────────────────────────

FORMAT : PDF, 10-15 pages

CONTENU OBLIGATOIRE :

1. INTRODUCTION
   - Présentation du problème
   - Objectifs du projet

2. MODÉLISATION
   - Choix de représentation des données
   - Formalisation mathématique du problème
   - Variables de décision
   - Contraintes (dures et souples)
   - Fonction objectif

3. APPROCHES ET ALGORITHMES
   - Allocation : méthodes testées
   - Optimisation des tournées (TSP) : algorithme choisi
   - Optimisation globale (CSP) : modèle OR-Tools
   - Regroupement de commandes
   - Optimisation du stockage

4. RÉSULTATS ET ANALYSE
   - Métriques de performance
   - Comparaison des différentes approches
   - Graphiques et tableaux
   - Analyse de la coopération humain-robot
   - Impact de la réorganisation du stockage

5. EXTENSIONS RÉALISÉES
   - Description des extensions implémentées
   - Résultats

6. CONCLUSION
   - Bilan
   - Limites de la solution
   - Perspectives d'amélioration

ANNEXES (optionnel) :
- Exemples de tournées détaillées
- Code source de fonctions clés


8.3 PRÉSENTATION ORALE
───────────────────────────────────────────────────────────────────────────────

DURÉE : 15 minutes + 5 minutes de questions

SUPPORT : Slides (PowerPoint, PDF, ou équivalent)

CONTENU :
1. Présentation du problème (2 min)
2. Approche de résolution (3 min)
3. Démonstration du code en action (5 min)
4. Résultats et analyse (3 min)
5. Conclusion (2 min)

DÉMONSTRATION LIVE :
- Montrer le programme en fonctionnement
- Afficher la visualisation des tournées
- Présenter le dashboard de métriques

═══════════════════════════════════════════════════════════════════════════════
10. CONSEILS TECHNIQUES
═══════════════════════════════════════════════════════════════════════════════

10.1 BIBLIOTHÈQUES PYTHON RECOMMANDÉES
───────────────────────────────────────────────────────────────────────────────

OBLIGATOIRES :
```python
# Traitement de données
import json
import numpy as np
import pandas as pd

# Optimisation
from ortools.sat.python import cp_model
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Visualisation
import matplotlib.pyplot as plt
import seaborn as sns
```

OPTIONNELLES :
```python
# Graphes
import networkx as nx

# Interface
import streamlit  # Pour dashboard web rapide

# Apprentissage (extensions)
import gym
from stable_baselines3 import PPO
```

Installation :
```bash
pip install ortools numpy pandas matplotlib seaborn networkx
```

10.2 CONSEILS D'OPTIMISATION
───────────────────────────────────────────────────────────────────────────────

1. **Commencez simple**
   - Jour 1-2 : Implémentation fonctionnelle, même non optimale
   - Jour 3-4 : Optimisation progressive
   - Jour 5 : Raffinements

2. **Testez fréquemment**
   - Créez des jeux de données de test réduits (3-5 commandes)
   - Validez chaque fonctionnalité séparément
   - Tests unitaires dès le début

3. **Visualisez tôt**
   - Affichez l'entrepôt et les emplacements dès le Jour 1
   - Visualisez les tournées pour détecter les problèmes
   - Graphiques de métriques pour comparer les approches

4. **Modularité**
   - Séparez bien allocation / routing / optimisation
   - Fonctions réutilisables
   - Interface claire entre modules

5. **Performance**
   - Utilisez numpy pour les calculs matriciels
   - Pré-calculez les distances (matrice complète)
   - Limitez les appels à OR-Tools (coûteux)

6. **Debugging**
   - Loggez les décisions importantes
   - Affichez les violations de contraintes clairement
   - Mode verbose pour tracer l'exécution


═══════════════════════════════════════════════════════════════════════════════
11. RESSOURCES
═══════════════════════════════════════════════════════════════════════════════

DOCUMENTATION OR-TOOLS
───────────────────────────────────────────────────────────────────────────────
- Guide CP-SAT : https://developers.google.com/optimization/cp
- Routing (TSP/VRP) : https://developers.google.com/optimization/routing
- Exemples Python : https://github.com/google/or-tools/tree/stable/examples/python

ARTICLES ET TUTORIELS
───────────────────────────────────────────────────────────────────────────────
- Bin Packing Problem : https://en.wikipedia.org/wiki/Bin_packing_problem
- Vehicle Routing Problem : https://en.wikipedia.org/wiki/Vehicle_routing_problem
- Order Picking : rechercher "warehouse order picking optimization"

DATASETS RÉELS
───────────────────────────────────────────────────────────────────────────────
- TSPLIB : http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/
- Capacitated VRP instances : http://vrp.atd-lab.inf.puc-rio.br/

INSPIRATION
───────────────────────────────────────────────────────────────────────────────
- Amazon Robotics : https://www.amazonrobotics.com/
- Kiva Systems (racheté par Amazon)
- Ocado automated warehouse
