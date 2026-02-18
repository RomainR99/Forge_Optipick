# Exemple : TSP avec MiniZinc et OR-Tools

## 📁 Fichiers

- **`test.mzn`** : Modèle MiniZinc (déclare les paramètres)
- **`test.dzn`** : Données MiniZinc (valeurs des paramètres) - **peut être utilisé sans Python**
- **`test_ortools.py`** : Script Python utilisant **OR-Tools** pour résoudre le même problème
- **`data_simple.json`** : Données JSON (2 agents, 2 commandes, 2 produits) - optionnel

## 🚀 Utilisation

### Option 1 : MiniZinc (avec fichier .dzn)

**Utilisation** : `test.mzn` utilise le fichier `test.dzn` pour les données. **Aucun Python nécessaire.**

**Fichiers utilisés :**
- `test.mzn` : Modèle MiniZinc (déclare les paramètres et contraintes)
- `test.dzn` : Données MiniZinc (valeurs des paramètres : `n_locations`, `distance_matrix`)

```bash
cd examples
minizinc --solver COIN-BC test.mzn test.dzn
```

**Ou depuis la racine du projet :**
```bash
minizinc --solver COIN-BC examples/test.mzn examples/test.dzn
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

**Interprétation du résultat :**
- `next = [2, 3, 4, 1]` signifie :
  - Location 1 → Location 2
  - Location 2 → Location 3
  - Location 3 → Location 4
  - Location 4 → Location 1 (retour à l'entrée)
- Chemin complet : **1 → 2 → 3 → 4 → 1** (tour complet)
- Distance totale : **14 unités** (3 + 2 + 2 + 7 = 14)

**Note importante** : Ce résultat a été obtenu en utilisant **uniquement** les fichiers `test.mzn` et `test.dzn`, **sans Python**. C'est l'avantage de cette approche : vous pouvez résoudre le problème directement avec MiniZinc sans dépendre de Python.

**Avantage** : Vous pouvez modifier `test.dzn` pour tester avec différentes données sans toucher au modèle `test.mzn`.

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

## 📊 Données dans `test.dzn`

Les données sont maintenant dans le fichier `test.dzn` (et non plus intégrées dans `test.mzn`) :

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
| **Fichiers nécessaires** | `test.mzn` + `test.dzn` (pas de Python) | `test_ortools.py` + Python |
| **Lancement direct** | `minizinc --solver COIN-BC test.mzn test.dzn` | `python test_ortools.py` |
| **Résultat** | Chemin optimal + distance | Chemin optimal + distance |
| **Algorithme** | Programmation par contraintes | Routing avec heuristiques |
| **Performance** | Optimal (petit problème) | Très rapide (heuristiques) |

## ✅ Avantages

- **`test.mzn` + `test.dzn`** : Modèle et données séparés, peut être résolu sans Python
- **`test_ortools.py`** : Utilise OR-Tools (comme dans le projet principal), affiche les données JSON

**Note :** Le modèle MiniZinc résout un TSP complet (tour fermé qui retourne à l'entrée), donc la distance totale est de **14 unités**. Le script OR-Tools peut être configuré pour résoudre soit un chemin ouvert (sans retour) soit un tour complet selon les besoins.
