# Guide d'utilisation de MiniZinc dans OptiPick

## Installation

### 1. Installer MiniZinc

Téléchargez et installez MiniZinc depuis : https://www.minizinc.org/

**macOS :**
```bash
brew install minizinc
```

**Linux :**
```bash
sudo apt-get install minizinc
```

**Windows :**
Téléchargez l'installateur depuis le site officiel.

### 2. Installer la bibliothèque Python

```bash
pip install minizinc
```

### 3. Vérifier l'installation

```bash
python -c "from minizinc import Solver; print('✅ MiniZinc installé')"
```

## Utilisation

### Méthode 1 : Via la ligne de commande

```bash
# Utiliser l'algorithme glouton (par défaut)
python main.py

# Utiliser MiniZinc pour l'allocation optimale
python main.py --minizinc

# Spécifier un solveur particulier
python main.py --minizinc --solver gecode
python main.py --minizinc --solver chuffed
```

### Méthode 2 : Depuis le code Python

```python
from src.minizinc_solver import allocate_with_minizinc

# Résoudre avec MiniZinc
assignment = allocate_with_minizinc(
    orders=orders,
    agents=agents,
    products_by_id=products_by_id,
    warehouse=warehouse,
    solver_name="gecode"
)
```

## Solveurs disponibles

MiniZinc supporte plusieurs solveurs. Les plus courants sont :

- **gecode** : Solveur par défaut, rapide et fiable
- **chuffed** : Solveur avec apprentissage de clauses, souvent plus rapide
- **or-tools** : Solveur de Google OR-Tools (si installé)

Pour lister les solveurs disponibles :

```python
from minizinc import Solver
print(Solver.list())
```

## Modèle MiniZinc

Le modèle se trouve dans `models/allocation.mzn`. Il définit :

- **Variables de décision** : `assignment[o]` = agent assigné à la commande `o`
- **Contraintes** :
  - Capacité poids/volume
  - Zones interdites pour robots
  - Objets fragiles interdits pour robots
  - Poids max par item pour robots
  - Incompatibilités entre produits
- **Objectif** : Maximiser le nombre de commandes assignées

## Comparaison des méthodes

| Critère | Glouton | MiniZinc |
|---------|---------|----------|
| Vitesse | ⚡ Très rapide | 🐢 Plus lent |
| Optimalité | ❌ Sous-optimal | ✅ Optimal |
| Contraintes | ✅ Toutes | ✅ Toutes |
| Complexité | Simple | Modélisation |

## Dépannage

### Erreur : "MiniZinc n'est pas disponible"

Vérifiez que :
1. MiniZinc est installé : `minizinc --version`
2. La bibliothèque Python est installée : `pip install minizinc`
3. Le chemin MiniZinc est dans votre PATH

### Erreur : "Solveur non trouvé"

Vérifiez les solveurs disponibles :
```python
from minizinc import Solver
print(Solver.list())
```

Installez un solveur si nécessaire (Gecode est généralement inclus avec MiniZinc).

### Erreur lors de la résolution

Si MiniZinc échoue, le programme bascule automatiquement vers l'algorithme glouton.

Pour déboguer, vérifiez :
- Les données d'entrée (JSON valides)
- Le modèle MiniZinc (`models/allocation.mzn`)
- Les logs MiniZinc (ajoutez `verbose=True` dans `instance.solve()`)

## Exemples

### Exemple 1 : Allocation simple

```bash
python main.py --minizinc
```

### Exemple 2 : Avec solveur spécifique

```bash
python main.py --minizinc --solver chuffed
```

### Exemple 3 : Comparaison glouton vs MiniZinc

```bash
# Glouton
python main.py > result_glouton.txt

# MiniZinc
python main.py --minizinc > result_minizinc.txt

# Comparer les résultats
diff result_glouton.txt result_minizinc.txt
```

## Notes

- MiniZinc peut être plus lent que l'algorithme glouton pour de grandes instances
- L'algorithme glouton reste disponible comme solution de repli
- Le modèle MiniZinc peut être étendu avec d'autres contraintes si nécessaire
