# 🚀 Guide de Déploiement Streamlit Cloud

Ce guide explique comment déployer votre application OptiPick sur **Streamlit Cloud** depuis GitHub.

## 📋 Prérequis

1. ✅ Un compte GitHub avec votre code poussé
2. ✅ Un compte Streamlit Cloud (gratuit) : https://share.streamlit.io/
3. ✅ Tous les fichiers nécessaires dans le dépôt GitHub

## 🎯 Étapes de Déploiement

### Étape 1 : Préparer votre dépôt GitHub

Assurez-vous que votre dépôt GitHub contient tous les fichiers nécessaires :

```
optipick/
├── app_streamlit.py       # ✅ Fichier principal Streamlit
├── requirements.txt        # ✅ Dépendances Python
├── main.py                # ✅ Point d'entrée (utilisé par app_streamlit.py)
├── data/                  # ✅ Données JSON (doivent être dans le repo)
│   ├── warehouse.json
│   ├── products.json
│   ├── agents.json
│   └── orders.json
├── src/                   # ✅ Code source
│   ├── models.py
│   ├── loader.py
│   ├── allocation_cpsat.py
│   ├── minizinc_solver.py
│   └── ...
├── models/                # ✅ Modèles MiniZinc (optionnel)
│   └── allocation.mzn
└── README.md              # ✅ Documentation
```

**⚠️ Important :**
- Les fichiers de données (`data/*.json`) **doivent être dans le dépôt** (pas dans `.gitignore`)
- Tous les fichiers Python nécessaires doivent être présents

### Étape 2 : Vérifier requirements.txt

Votre `requirements.txt` doit contenir toutes les dépendances :

```txt
ortools>=9.8
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
networkx>=3.1
minizinc>=0.6.0
streamlit>=1.28.0
```

**Note sur MiniZinc :**
- Le package Python `minizinc` est installé automatiquement
- Cependant, l'exécutable MiniZinc système peut ne pas être disponible sur Streamlit Cloud
- L'application gère cela automatiquement avec un fallback sur First-Fit

### Étape 3 : Créer un compte Streamlit Cloud

1. Allez sur **https://share.streamlit.io/**
2. Cliquez sur **"Sign up"** ou **"Sign in"**
3. Connectez-vous avec votre compte **GitHub**
4. Autorisez Streamlit Cloud à accéder à vos dépôts

### Étape 4 : Déployer l'application

1. **Dans Streamlit Cloud :**
   - Cliquez sur **"New app"** (bouton en haut à droite)
   - Sélectionnez votre dépôt GitHub (`optipick` ou le nom de votre repo)
   - Sélectionnez la branche (généralement `main` ou `master`)
   - **Main file path** : Entrez `app_streamlit.py`
   - Cliquez sur **"Deploy"**

2. **Attendre le déploiement :**
   - Streamlit Cloud va :
     - Installer toutes les dépendances depuis `requirements.txt`
     - Lancer votre application
     - Générer une URL publique

### Étape 5 : Accéder à votre application

Une fois déployée, vous obtiendrez une URL comme :
```
https://votre-nom-optipick.streamlit.app
```

Cette URL est **publique** et accessible à tous.

## ⚙️ Configuration Optionnelle

### Fichier de configuration Streamlit

Le fichier `.streamlit/config.toml` a été créé pour personnaliser l'apparence :

```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
```

### Variables d'environnement (Secrets)

Si vous avez besoin de variables d'environnement :

1. Dans Streamlit Cloud, allez dans **"Settings"** de votre app
2. Section **"Secrets"**
3. Ajoutez vos variables au format TOML :
   ```toml
   [secrets]
   API_KEY = "votre_clé"
   DATABASE_URL = "votre_url"
   ```

Accès dans le code :
```python
import streamlit as st
api_key = st.secrets.get("API_KEY", "default_value")
```

## 🔧 Dépannage

### ❌ Erreur : Module not found

**Problème :** Une dépendance manque dans `requirements.txt`

**Solution :**
```bash
# Générer requirements.txt automatiquement
pip freeze > requirements.txt

# Ou ajouter manuellement la dépendance manquante
```

### ❌ Erreur : File not found (data/*.json)

**Problème :** Les fichiers de données ne sont pas dans le dépôt GitHub

**Solution :**
1. Vérifiez que `data/` n'est pas dans `.gitignore`
2. Ajoutez les fichiers :
   ```bash
   git add data/*.json
   git commit -m "Add data files"
   git push
   ```

### ❌ Erreur : MiniZinc not available

**Problème :** MiniZinc nécessite l'exécutable système qui peut ne pas être disponible

**Solution :** ✅ **Déjà géré dans le code !**
- L'application fait automatiquement un fallback sur First-Fit si MiniZinc n'est pas disponible
- Vous pouvez toujours utiliser First-Fit qui fonctionne sans MiniZinc

### ❌ L'application ne se met pas à jour

**Problème :** Les changements ne sont pas visibles

**Solution :**
1. Vérifiez que vous avez poussé vos changements sur GitHub :
   ```bash
   git add .
   git commit -m "Update app"
   git push
   ```
2. Streamlit Cloud redéploie automatiquement à chaque push
3. Attendez quelques secondes pour le redéploiement
4. Vous pouvez forcer un redéploiement depuis l'interface Streamlit Cloud (bouton "Reboot app")

### ❌ Erreur : Import error (main.py)

**Problème :** `app_streamlit.py` importe `main.py` qui n'est pas trouvé

**Solution :** Assurez-vous que `main.py` est dans le dépôt GitHub à la racine

## 📝 Checklist de Déploiement

Avant de déployer, vérifiez :

- [ ] Code poussé sur GitHub
- [ ] `app_streamlit.py` présent dans le dépôt
- [ ] `requirements.txt` à jour avec toutes les dépendances
- [ ] Fichiers de données (`data/*.json`) dans le dépôt (pas dans `.gitignore`)
- [ ] Code source (`src/`, `main.py`) dans le dépôt
- [ ] `README.md` présent
- [ ] Compte Streamlit Cloud créé et connecté à GitHub
- [ ] Application déployée avec succès
- [ ] Test de l'application en ligne

## 🎨 Personnalisation

### Changer le thème

Modifiez `.streamlit/config.toml` :

```toml
[theme]
primaryColor = "#FF6B6B"      # Couleur principale
backgroundColor = "#FFFFFF"    # Fond principal
secondaryBackgroundColor = "#F0F2F6"  # Fond secondaire
textColor = "#262730"          # Couleur du texte
font = "sans serif"            # Police
```

### Ajouter un favicon

Créez `.streamlit/favicon.png` (image 32x32 pixels)

## 🔗 Commandes Utiles

### Tester localement avant de déployer

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer Streamlit localement
streamlit run app_streamlit.py

# Vérifier que tout fonctionne
```

### Mettre à jour le déploiement

```bash
# Faire vos modifications
# ...

# Pousser sur GitHub
git add .
git commit -m "Update app"
git push

# Streamlit Cloud redéploie automatiquement
```

## 📊 Ressources

- **Streamlit Cloud** : https://share.streamlit.io/
- **Documentation officielle** : https://docs.streamlit.io/streamlit-community-cloud
- **Guide de déploiement** : https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app
- **Forum communautaire** : https://discuss.streamlit.io/

## 💡 Astuces

1. **Testez localement d'abord** : Assurez-vous que `streamlit run app_streamlit.py` fonctionne localement avant de déployer

2. **Consultez les logs** : Dans Streamlit Cloud, cliquez sur "Manage app" → "Logs" pour voir les erreurs

3. **Performance** : Streamlit Cloud a des limites de ressources. Pour des applications très lourdes, considérez d'autres solutions (Heroku, Railway, etc.)

4. **Sécurité** : Ne commitez jamais de secrets dans le code. Utilisez `st.secrets` pour les variables sensibles

5. **Mise à jour automatique** : Chaque push sur la branche principale redéploie automatiquement l'application

6. **Branches multiples** : Vous pouvez déployer plusieurs branches (ex: `main`, `dev`) comme applications séparées

## 🎯 Résumé Rapide

```bash
# 1. Préparer le dépôt
git add .
git commit -m "Prepare for Streamlit Cloud"
git push

# 2. Aller sur https://share.streamlit.io/
# 3. Cliquer sur "New app"
# 4. Sélectionner votre repo et branche
# 5. Entrer "app_streamlit.py" comme main file
# 6. Cliquer sur "Deploy"
# 7. Attendre et profiter ! 🎉
```

---

**Bon déploiement ! 🚀**

Votre application sera accessible publiquement sur une URL Streamlit Cloud.
