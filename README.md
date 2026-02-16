# OptiPick

**Optimisation de Tournées d'Entrepôt avec Coopération Humain-Robot et Gestion du Stockage**

## 👥 

- **Nermine**
- **Imen**
- **Hamid**
- **Romain**


## 📋 Description du Projet

OptiPick est un système d'optimisation pour la gestion d'un entrepôt de e-commerce moderne où coexistent différents types d'agents :
- **Préparateurs humains** : Expérimentés, flexibles, mais coûteux
- **Robots autonomes** : Rapides, infatigables, mais limités
- **Chariots semi-autonomes** : Guidés par humains, capacité accrue

L'objectif est d'organiser la **préparation optimale** des commandes clients en résolvant plusieurs défis :
1. Planification des tournées (séquence de produits à ramasser)
2. Allocation agents-commandes (qui fait quoi ?)
3. Respect des contraintes (capacité, incompatibilités, restrictions)
4. Optimisation du stockage
5. Coopération humain-robot

## 🏗️ Structure du Projet

```
forge/
│
├── data/
│   ├── warehouse.json      # Configuration de l'entrepôt (zones, dimensions)
│   ├── products.json        # Catalogue des produits (100 produits)
│   ├── agents.json          # Agents disponibles (robots, humains, chariots)
│   └── orders.json          # Commandes à préparer (20-30 par jour)
│
├── src/
│   ├── models.py            # Classes Warehouse, Product, Agent, Order
│   ├── loader.py            # Chargement des données JSON
│   ├── constraints.py       # Vérification des contraintes
│   ├── allocation.py        # Algorithmes d'allocation
│   ├── routing.py           # Optimisation des tournées (TSP)
│   ├── optimization.py      # Modèle CSP avec OR-Tools
│   ├── storage.py           # Optimisation du stockage
│   └── visualization.py     # Visualisation et dashboard
│
├── main_day1.py            # Point d'entrée (Jour 1)
├── ENONCE_PROJET_OPTIPICK.txt  # Énoncé complet du projet
└── README.md               # Ce fichier
```

## 🎯 Objectifs

### Objectif Principal
Minimiser le score total défini par :

```
Score = w₁ × Distance_totale
      + w₂ × Temps_total
      + w₃ × Coût_total
      + w₄ × Pénalité_déséquilibre
      + w₅ × Pénalité_retard
```

### Critères d'Optimisation
- ✅ **Distance totale parcourue** (minimiser)
- ✅ **Temps total de préparation** (minimiser)
- ✅ **Coût opérationnel** (minimiser)
- ✅ **Respect des deadlines** (100% obligatoire)
- ✅ **Équilibrage de charge** entre agents
- ✅ **Taux d'utilisation** des robots vs humains

## 🔒 Contraintes du Système

### Contraintes Dures (Obligatoires)
1. **Capacité des agents** : Poids et volume respectés
2. **Incompatibilités de produits** : Produits incompatibles ne peuvent pas être ensemble
3. **Restrictions des robots** :
   - Pas d'accès à la Zone C (réfrigérée)
   - Pas d'objets fragiles
   - Pas d'objets > 10kg individuellement
4. **Chariots nécessitent un humain** : Un chariot doit être assigné à un humain
5. **Deadlines** : Toutes les commandes doivent être préparées à temps
6. **Complétude** : Toutes les commandes doivent être préparées
7. **Pas de collision** : Deux agents ne peuvent pas occuper la même case simultanément

### Contraintes Souples (Optimisation)
- Minimiser la distance totale
- Minimiser le temps total
- Minimiser le coût
- Équilibrer la charge de travail
- Privilégier les robots (moins chers)
- Grouper les commandes compatibles
- Minimiser les allers-retours

## 📊 Modélisation

### Entrepôt
- Grille 2D avec 5 zones :
  - **Zone A** : Électronique (20 emplacements)
  - **Zone B** : Livres/Médias (15 emplacements)
  - **Zone C** : Alimentaire (10 emplacements) - Réfrigérée
  - **Zone D** : Hygiène/Chimie (10 emplacements)
  - **Zone E** : Textile (15 emplacements)
- Distance : Manhattan (`|x₁-x₂| + |y₁-y₂|`)
- Point d'entrée/sortie : (0, 0)

### Produits
Chaque produit contient :
- ID unique, nom, catégorie
- Poids (kg), volume (dm³)
- Emplacement (x, y)
- Fréquence de commande (faible/moyenne/élevée)
- Incompatibilités (liste d'autres produits)
- Fragilité (booléen)

#### Incompatibilités de Produits (`incompatible_with`)

Le champ `incompatible_with` liste les produits qui **ne peuvent pas être transportés ensemble** dans le même chariot ou par le même agent simultanément.

**Règle principale :** Si un produit A est dans la liste `incompatible_with` d'un produit B, alors A et B ne peuvent pas être dans le même chariot en même temps.

**Exemples concrets :**

1. **Produits chimiques ↔ Produits électroniques**
   - `Product_042` (Détergent industriel) est incompatible avec `Product_001` (Laptop)
   - **Raison :** Risque de dommages par contact avec des produits chimiques

2. **Produits chimiques ↔ Produits alimentaires**
   - `Product_042` (Détergent) est incompatible avec `Product_036` (Lait)
   - **Raison :** Risque de contamination et problèmes de sécurité alimentaire

3. **Produits alimentaires ↔ Produits chimiques**
   - `Product_036` (Lait) a `Product_042` dans sa liste d'incompatibilités
   - **Raison :** Sécurité alimentaire - éviter tout contact avec produits chimiques

**Utilisation dans le projet :**

Cette contrainte est utilisée lors de l'allocation des commandes aux agents :
- Si une commande contient `Product_001` et `Product_042`, ils doivent être préparés séparément ou par des agents différents
- Si un agent ramasse `Product_001`, il ne peut pas ramasser `Product_042` dans la même tournée
- C'est une **contrainte dure (obligatoire)** : elle doit être respectée à 100% pour garantir la sécurité et la qualité des produits

**Exemple de vérification :**
```python
def can_combine(products):
    """Vérifie si une liste de produits peut être transportée ensemble"""
    for i, p1 in enumerate(products):
        for p2 in products[i+1:]:
            if p2['id'] in p1.get('incompatible_with', []):
                return False  # Produits incompatibles !
    return True  # Tous compatibles
```

### Agents

| Type | Quantité | Capacité | Vitesse | Coût/h | Restrictions |
|------|----------|----------|---------|--------|--------------|
| Robot | 3 | 20kg / 30dm³ | 2.0 m/s | 5€ | Pas Zone C, pas fragile, max 10kg/item |
| Humain | 2 | 35kg / 50dm³ | 1.5 m/s | 25€ | Aucune |
| Chariot | 2 | 50kg / 80dm³ | 1.2 m/s | 3€ | Nécessite un humain |

### Commandes
Chaque commande contient :
- ID commande
- Liste de produits avec quantités
- Heure de réception
- Deadline (délai de préparation)
- Priorité (standard / express)

## 🚀 Progression par Journées

### Jour 1 : Modélisation et Allocation Simple
- Chargement des données JSON
- Création des classes (Warehouse, Product, Agent, Order)
- Calcul de distance Manhattan
- Allocation naïve (First-Fit)

### Jour 2 : Respect des Contraintes Dures
- Vérification de capacité
- Vérification d'incompatibilités
- Restrictions des robots
- Gestion des chariots
- Allocation avec contraintes

### Jour 3 : Optimisation des Tournées (TSP)
- Modélisation TSP pour chaque agent
- Résolution avec heuristique (Nearest Neighbor, 2-opt, ou OR-Tools)
- Calcul du temps de tournée
- Vérification des deadlines

### Jour 4 : Allocation Optimale et Regroupement
- Modélisation CSP avec OR-Tools CP-SAT
- Optimisation globale de l'allocation
- Regroupement de commandes compatibles (batching)
- Comparaison des stratégies

### Jour 5 : Optimisation du Stockage et Analyse Avancée
- Analyse des patterns de commandes
- Réorganisation de l'entrepôt (produits fréquents près de l'entrée)
- Simulation avant/après réorganisation
- Analyse de coopération humain-robot
- Dashboard de monitoring

## 🛠️ Technologies Utilisées

### Bibliothèques Python Recommandées
```bash
pip install ortools numpy pandas matplotlib seaborn networkx
```

- **OR-Tools** : Optimisation (CP-SAT, Routing)
- **NumPy/Pandas** : Traitement de données
- **Matplotlib/Seaborn** : Visualisation
- **NetworkX** : Graphes (optionnel)

## 📁 Fichiers de Données

### warehouse.json
Configuration de l'entrepôt : dimensions, zones avec coordonnées, point d'entrée.

### products.json
Catalogue de 100 produits avec leurs caractéristiques (poids, volume, emplacement, incompatibilités).

### agents.json
Liste des agents disponibles avec leurs capacités, vitesses, coûts et restrictions.

Le fichier contient **7 agents** répartis en 3 types :

#### Structure des Agents

Chaque agent possède les champs suivants :
- `id` : Identifiant unique (R1, R2, R3, H1, H2, C1, C2)
- `type` : Type d'agent (`robot`, `human`, `cart`)
- `capacity_weight` : Capacité maximale en poids (kg)
- `capacity_volume` : Capacité maximale en volume (dm³)
- `speed` : Vitesse de déplacement (m/s)
- `cost_per_hour` : Coût d'utilisation par heure (€)
- `restrictions` : Objet contenant les restrictions spécifiques

#### Types d'Agents

**1. Robots (3 agents : R1, R2, R3)**
- **Capacité** : 20kg / 30dm³
- **Vitesse** : 2.0 m/s
- **Coût** : 5€/h (électricité + amortissement)
- **Restrictions** :
  - `no_zones: ["C"]` : Ne peut pas accéder à la Zone C (réfrigérée)
  - `no_fragile: true` : Ne peut pas transporter d'objets fragiles
  - `max_item_weight: 10` : Ne peut pas transporter d'objets > 10kg individuellement

**2. Humains (2 agents : H1, H2)**
- **Capacité** : 35kg / 50dm³
- **Vitesse** : 1.5 m/s
- **Coût** : 25€/h (salaire)
- **Restrictions** : `{}` (aucune restriction - peut tout faire)

**3. Chariots (2 agents : C1, C2)**
- **Capacité** : 50kg / 80dm³
- **Vitesse** : 1.2 m/s
- **Coût** : 3€/h (quand utilisé avec humain)
- **Restrictions** :
  - `requires_human: true` : Nécessite un humain assigné (H1 ou H2)
  - Un humain ne peut guider qu'un seul chariot à la fois

#### Exemple de Structure

```json
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
}
```

#### Notes Importantes

- Les **robots** sont les moins chers mais ont des restrictions importantes
- Les **humains** sont les plus flexibles mais les plus coûteux
- Les **chariots** augmentent la capacité mais nécessitent un humain dédié
- L'optimisation doit équilibrer l'utilisation des robots (moins chers) avec les contraintes des commandes

### orders.json
Commandes à préparer avec produits, quantités, deadlines et priorités.

## 🧪 Utilisation

### Exécution du Programme
```bash
python main_day1.py
```

### Structure du Code
- **models.py** : Classes de base pour modéliser le problème
- **loader.py** : Chargement et parsing des fichiers JSON
- **constraints.py** : Vérification de toutes les contraintes
- **allocation.py** : Algorithmes d'allocation (glouton, optimisé)
- **routing.py** : Optimisation des tournées (TSP)
- **optimization.py** : Modèle CSP avec OR-Tools
- **visualization.py** : Visualisation des résultats

## 📈 Métriques de Performance

Le système évalue les solutions sur :
1. **Distance totale parcourue** (mètres)
2. **Temps total de préparation** (minutes)
3. **Coût opérationnel** (euros)
4. **Taux de respect des deadlines** (%)
5. **Équilibrage de charge** (écart-type entre agents)
6. **Taux d'utilisation** des robots vs humains

## 🎓 Contexte Académique

Ce projet fait partie du module **Programmation Logique et par Contraintes** (L2 Informatique).

Il combine :
- **Satisfaction de Contraintes (CSP)** : Modélisation et résolution avec OR-Tools
- **Optimisation Combinatoire** : TSP, allocation optimale
- **Algorithmes Gloutons** : Stratégies d'allocation rapides
- **Analyse de Données** : Patterns de commandes, optimisation du stockage

## 📚 Ressources

- [Documentation OR-Tools](https://developers.google.com/optimization)
- [CP-SAT Guide](https://developers.google.com/optimization/cp)
- [Routing (TSP/VRP)](https://developers.google.com/optimization/routing)
- [TSPLIB](http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/)

## 📝 Notes

- Le projet suit une progression sur 5 journées avec difficulté croissante
- Les contraintes dures doivent être respectées à 100%
- Les contraintes souples sont optimisées selon la fonction objectif
- La visualisation est fortement recommandée pour comprendre les résultats

---

Pour plus de détails, consultez le fichier `ENONCE_PROJET_OPTIPICK.txt`.
