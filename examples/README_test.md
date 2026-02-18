# Exemple : TSP avec MiniZinc et OR-Tools

## 📁 Fichiers

- **`test.mzn`** : Modèle MiniZinc **autonome** avec toutes les données intégrées (un seul fichier)
- **`test_ortools.py`** : Script Python utilisant **OR-Tools** pour résoudre le même problème
- **`data_simple.json`** : Données JSON (2 agents, 2 commandes, 2 produits) - optionnel

## 🚀 Utilisation

### Option 1 : MiniZinc (fichier autonome)

```bash
cd examples
minizinc --solver COIN-BC test.mzn
```

**Résultat obtenu :**
```
========================================
  TSP - Tour le plus court (MiniZinc)
========================================
next = [2, 3, 4, 1]
Distance totale minimale = 14 unités
========================================
```

**Interprétation :**
- `next = [2, 3, 4, 1]` signifie :
  - Location 1 → Location 2
  - Location 2 → Location 3
  - Location 3 → Location 4
  - Location 4 → Location 1 (retour à l'entrée)
- Chemin complet : **1 → 2 → 3 → 4 → 1** (tour complet)
- Distance totale : **14 unités**

### Option 2 : OR-Tools (Python)

```bash
cd examples
python test_ortools.py
```

**Résultat attendu :**
```
========================================
✅ RÉSULTAT : Chemin le plus court (OR-Tools)
========================================

Départ : Location 0 (Entrée)
Chemin optimal :
  Entrée → P1 → P2 → P4

  (Indices : 0 → 1 → 2 → 3)

Distance totale minimale = 7 unités
========================================
```

## 📊 Données intégrées dans `test.mzn`

- **4 locations** : Entrée (0,0), P1 (2,0), P2 (3,1), P4 (5,2)
- **Matrice de distances** :
  ```
        Entrée  P1   P2   P4
  Entrée    0     3    5    7
  P1        3     0    2    4
  P2        5     2    0    2
  P4        7     4    2    0
  ```

## 🔍 Comparaison MiniZinc vs OR-Tools

| Caractéristique | MiniZinc (`test.mzn`) | OR-Tools (`test_ortools.py`) |
|----------------|----------------------|------------------------------|
| **Fichier autonome** | ✅ Oui (toutes données intégrées) | ❌ Nécessite Python |
| **Lancement direct** | `minizinc --solver COIN-BC test.mzn` | `python test_ortools.py` |
| **Résultat** | Chemin optimal + distance | Chemin optimal + distance |
| **Algorithme** | Programmation par contraintes | Routing avec heuristiques |
| **Performance** | Optimal (petit problème) | Très rapide (heuristiques) |

## ✅ Avantages

- **`test.mzn`** : Fichier unique, autonome, peut être résolu sans Python
- **`test_ortools.py`** : Utilise OR-Tools (comme dans le projet principal), affiche les données JSON

**Note :** Le modèle MiniZinc résout un TSP complet (tour fermé qui retourne à l'entrée), donc la distance totale est de **14 unités**. Le script OR-Tools peut être configuré pour résoudre soit un chemin ouvert (sans retour) soit un tour complet selon les besoins.
