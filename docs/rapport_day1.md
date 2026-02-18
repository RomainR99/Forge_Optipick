# Rapport Jour 1 - Modélisation et Allocation Simple

**Projet OptiPick** | Ymen Nermine, Hamid, Romain 

---

## Objectifs du Jour 1

Le Jour 1 consistait à établir les fondations du projet : modéliser le problème, charger les données, et implémenter une allocation naïve pour valider l'approche.

## Choix de Modélisation

### 1. Structure des Données avec Dataclasses Python

**Choix :** Utilisation des `@dataclass` Python pour modéliser toutes les entités du système.

**Classes créées :**
- **`Location`** : Coordonnées (x, y) avec `frozen=True` pour immutabilité et hashabilité
- **`Warehouse`** : Dimensions, zones, point d'entrée
- **`Product`** : Caractéristiques (poids, volume, emplacement, incompatibilités)
- **`Order`** : Commandes avec items, deadlines, priorités
- **`Agent`** : Agents avec capacités, vitesses, coûts (Robot, Human, Cart)

**Justification :**
- Code concis et lisible (évite `__init__`, `__repr__`, `__eq__` manuels)
- Type hints pour la sécurité de type
- `Location` frozen pour utilisation comme clé dans dictionnaires
- Structure modulaire facilitant les extensions futures

### 2. Séparation des Responsabilités

**Choix :** Séparation du chargement des données dans `src/loader.py`.

**Fonctions créées :**
- `load_json()` : Chargement générique des fichiers JSON
- `parse_warehouse()` : Conversion JSON → objet Warehouse
- `parse_products()` : Conversion JSON → dictionnaire de Product
- `parse_agents()` : Conversion JSON → liste d'Agent
- `parse_orders()` : Conversion JSON → liste d'Order

**Justification :**
- Réutilisabilité du code de chargement
- Facilité de test unitaire
- Séparation claire entre données brutes et objets métier

### 3. Distance Manhattan

**Choix :** Utilisation de la distance de Manhattan : `|x₁-x₂| + |y₁-y₂|`

**Justification :**
- Modélise correctement les déplacements dans une grille (mouvements horizontaux/verticaux)
- Plus simple que la distance euclidienne pour un entrepôt
- Correspond aux contraintes réelles de déplacement dans un entrepôt

### 4. Allocation First-Fit

**Choix :** Algorithme glouton First-Fit pour l'allocation initiale.

**Fonctionnement :**
1. Tri des commandes par heure de réception
2. Pour chaque commande, assignation au premier agent ayant la capacité suffisante
3. Vérification uniquement de la capacité (poids/volume) pour l'instant

**Justification :**
- Simple à implémenter et comprendre
- Rapide : complexité O(n × m)
- Base solide pour les améliorations futures (Jour 2 : contraintes, Jour 4 : optimisation)

**Limitations acceptées (Jour 1) :**
- Pas de vérification des restrictions (robots, incompatibilités)
- Pas d'optimisation globale
- Estimation de distance (pas de TSP)

## Réalisations

### Code Produit

- **Modèles** : 6 classes dataclass (Location, Warehouse, Product, Order, OrderItem, Agent)
- **Chargement** : 5 fonctions de parsing dans `loader.py`
- **Allocation** : Algorithme First-Fit fonctionnel
- **Évaluation** : Rapport complet avec métriques (commandes assignées, distance, utilisation agents)

### Données Préparées

- **100 produits** répartis dans 5 zones (A: 20, B: 15, C: 10, D: 10, E: 15)
- **7 agents** (3 robots, 2 humains, 2 chariots)
- **30 commandes** avec priorités et deadlines variées

## Résultats

Le système permet de :
- ✅ Charger et parser tous les fichiers JSON
- ✅ Calculer les distances entre emplacements
- ✅ Allouer les commandes aux agents selon leur capacité
- ✅ Afficher un rapport détaillé avec métriques de performance

### Sortie Console - Exemple d'Exécution

**Commande à exécuter dans le terminal :**

```bash
cd /Users/romain/Desktop/forge/optipick
source venv/bin/activate
python main.py
```

(Sans option `--minizinc` : le programme utilise l’algorithme glouton First-Fit par défaut. Les données par défaut sont `data/orders.json` avec 30 commandes.)

Le programme affiche dans la console un rapport complet montrant l'allocation :

```
══════════════════════════════════════
JOUR 1 — Allocation naïve (First-Fit)
══════════════════════════════════════
Commandes totales : 30
Commandes assignées: 30
Commandes non assignées: 0
Distance totale estimée (proxy): 594

Détail par agent:
- R1 (robot)
  commandes: 7 -> ['Order_001', 'Order_002', 'Order_003', 'Order_004', 'Order_005', 'Order_006', 'Order_022']
  poids: 18.64/20.00 kg (93.2%)
  volume: 29.74/30.00 dm³ (99.1%)
  vitesse: 2.0 m/s

- R2 (robot)
  commandes: 5 -> ['Order_007', 'Order_008', 'Order_009', 'Order_010', 'Order_023']
  poids: 15.95/20.00 kg (79.8%)
  volume: 29.11/30.00 dm³ (97.0%)
  vitesse: 2.0 m/s

- R3 (robot)
  commandes: 6 -> ['Order_011', 'Order_012', 'Order_014', 'Order_015', 'Order_016', 'Order_027']
  poids: 19.80/20.00 kg (99.0%)
  volume: 29.84/30.00 dm³ (99.5%)
  vitesse: 2.0 m/s

- H1 (human)
  commandes: 5 -> ['Order_013', 'Order_017', 'Order_018', 'Order_019', 'Order_025']
  poids: 29.77/35.00 kg (85.1%)
  volume: 48.26/50.00 dm³ (96.5%)
  vitesse: 1.5 m/s

- H2 (human)
  commandes: 5 -> ['Order_020', 'Order_021', 'Order_026', 'Order_028', 'Order_029']
  poids: 16.39/35.00 kg (46.8%)
  volume: 46.79/50.00 dm³ (93.6%)
  vitesse: 1.5 m/s

- C1 (cart)
  commandes: 2 -> ['Order_024', 'Order_030']
  poids: 24.04/50.00 kg (48.1%)
  volume: 60.49/80.00 dm³ (75.6%)
  vitesse: 1.2 m/s

- C2 (cart)
  commandes: 0 -> []
  poids: 0.00/50.00 kg (0.0%)
  volume: 0.00/80.00 dm³ (0.0%)
  vitesse: 1.2 m/s

**Observations :**
- ✅ Toutes les 30 commandes ont été assignées avec succès
- ✅ Les robots sont bien utilisés (R1, R2, R3 avec utilisation élevée)
- ✅ Les humains et chariots complètent l'allocation
- ✅ Distance totale estimée : 594 unités (distance Manhattan)

## Prochaines Étapes (Jour 2)

- Intégration des contraintes dures (restrictions robots, incompatibilités)
- Vérification de la faisabilité des allocations
- Tests unitaires pour valider les contraintes

---

*Rapport généré le Jour 1 - Projet OptiPick*
