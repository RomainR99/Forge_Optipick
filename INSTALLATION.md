# Installation - Projet OptiPick

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

## Installation Rapide

### Option 1 : Script automatique (recommandé)

```bash
cd optipick
./setup_venv.sh
```

Le script va :
1. Créer l'environnement virtuel `venv/`
2. Activer l'environnement
3. Mettre à jour pip
4. Installer toutes les dépendances depuis `requirements.txt`
5. Installer MiniZinc

### Option 2 : Installation manuelle

```bash
cd optipick

# 1. Créer l'environnement virtuel
python3 -m venv venv

# 2. Activer l'environnement virtuel
source venv/bin/activate  # macOS/Linux
# ou sur Windows :
# venv\Scripts\activate

# 3. Mettre à jour pip
pip install --upgrade pip

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Installer MiniZinc
pip install minizinc
```

## Utilisation

### Activer l'environnement virtuel

```bash
source venv/bin/activate
```

Vous devriez voir `(venv)` dans votre terminal.

### Exécuter le programme

```bash
python main.py
```

### Désactiver l'environnement virtuel

```bash
deactivate
```

## Dépendances Installées

- **ortools** : Optimisation (CP-SAT, Routing)
- **numpy** : Calculs numériques
- **pandas** : Traitement de données
- **matplotlib** : Visualisation
- **seaborn** : Visualisation statistique
- **networkx** : Manipulation de graphes
- **minizinc** : Modélisation par contraintes

## Vérification de l'Installation

```bash
# Activer l'environnement
source venv/bin/activate

# Vérifier les packages installés
pip list

# Tester l'import
python -c "import ortools; import numpy; import pandas; import minizinc; print('✅ Toutes les dépendances sont installées')"
```

## Dépannage

### Problème SSL lors de l'installation

Si vous rencontrez des erreurs SSL, utilisez les flags `--trusted-host` :

```bash
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

### Réinstaller l'environnement

```bash
# Supprimer l'ancien environnement
rm -rf venv

# Recréer
./setup_venv.sh
```
