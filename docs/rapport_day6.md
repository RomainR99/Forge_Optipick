# Rapport Jour 6 — Interface web

**Projet OptiPick** | Extension 6

---

## Objectifs

Créer une interface utilisateur web avec :

- **Affichage en temps réel de l'entrepôt** : carte avec zones, emplacements produits, entrée
- **Animation des agents** : positions des robots, humains et chariots sur la carte (mise à jour selon l’allocation)
- **Formulaire pour ajouter des commandes** : produits, quantités, priorité, créneaux
- **Statistiques en direct** : nombre de commandes, assignées / non assignées, répartition par type d’agent

**Stack** : Flask (backend) + JavaScript (frontend).

---

## Architecture

### Backend (Flask)

- **Fichier** : `app.py` à la racine du projet.
- **Données** : chargement depuis `data/warehouse.json`, `data/products.json`, `data/agents.json`, `data/orders.json`.
- **Commandes** : les commandes sont gardées **en mémoire** (base = fichier au démarrage). L’ajout d’une commande via le formulaire ne modifie pas `data/orders.json` et est perdu au redémarrage du serveur.

### API REST

| Méthode | URL | Description |
|--------|-----|-------------|
| GET | `/api/warehouse` | Dimensions, zones, point d’entrée |
| GET | `/api/products` | Liste `{id, name, location}` pour le formulaire et la carte |
| GET | `/api/agents` | Liste des agents (id, type, capacités, etc.) |
| GET | `/api/orders` | Liste des commandes + assignment actuel |
| GET | `/api/stats` | Statistiques (n_orders, n_assigned, n_unassigned, by_type) + positions des agents pour l’affichage |
| POST | `/api/orders` | Ajout d’une commande (body JSON : `received_time`, `deadline`, `priority`, `items: [{ product_id, quantity }]`) |

### Frontend (JavaScript + CSS)

- **Templates** : `templates/index.html` (page unique).
- **Static** : `static/css/style.css`, `static/js/app.js`.
- **Carte** : dessin sur un `<canvas>` (grille, zones colorées, emplacements produits, entrée, agents avec couleurs par type).
- **Stats** : rafraîchissement périodique (polling toutes les 4 s) via `/api/stats`.
- **Formulaire** : choix de produits (liste déroulante), quantités, heure / deadline / priorité ; envoi en POST vers `/api/orders`, puis mise à jour des stats et de la carte.

---

## Utilisation

### Environnement virtuel (recommandé)

Sur macOS/Linux, si la commande `python` n’existe pas (seulement `python3`) ou pour isoler les dépendances :

```bash
cd optipick
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Après activation du venv, `python` et `pip` pointent vers l’environnement virtuel (Flask et les autres paquets y sont installés).

Sous Windows :

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Lancer l’interface web

Une fois le venv activé (ou Flask installé globalement) :

```bash
python app.py
```

ou

```bash
python main.py --day6
```

Si vous n’utilisez pas de venv et n’avez que `python3` : `python3 app.py` ou `python3 main.py --day6`.

Puis ouvrir dans un navigateur : **http://127.0.0.1:5001**

Le serveur utilise le **port 5001** par défaut (sous macOS, le port 5000 est souvent pris par AirPlay Receiver). Pour utiliser un autre port : `FLASK_PORT=8080 python app.py`.

### Version Streamlit (alternative sans JavaScript)

Une version **Streamlit** de l’interface est disponible : tout est en Python (pas de canvas JavaScript).

**Installation :** `pip install streamlit` (ou `pip install -r requirements.txt`, streamlit y est inclus).

**Lancement :**

```bash
cd optipick
streamlit run app_streamlit.py
```

Puis ouvrir **http://localhost:8501**.

**Fonctionnalités :** même logique que l’app Flask (données, allocation First-Fit ou MiniZinc, stats, carte de l’entrepôt, formulaire pour ajouter une commande). La carte est dessinée avec Matplotlib (zones + tournées des agents). Les commandes ajoutées sont conservées en session (`st.session_state`) jusqu’à fermeture de l’onglet.

### Fonctionnalités

1. **Carte de l’entrepôt** : zones A à E, point d’entrée (triangle), emplacements des produits (points), agents (cercles colorés : robot / humain / chariot) avec position dérivée de l’allocation (entrée ou premier emplacement de leur première commande).
2. **Statistiques** : nombre total de commandes, assignées, non assignées ; répartition par type d’agent (commandes et nombre d’agents).
3. **Ajout de commande** : remplir au moins une ligne produit + quantité, optionnellement heure, deadline, priorité ; cliquer sur « Créer la commande ». L’allocation First-Fit est recalculée, les stats et la carte se mettent à jour.

---

## Fichiers créés (Jour 6)

| Fichier | Rôle |
|---------|------|
| `app.py` | Application Flask, chargement des données, API, calcul d’allocation (First-Fit) et stats |
| `templates/index.html` | Page unique : carte, panneau stats, formulaire |
| `static/css/style.css` | Styles (thème sombre, grille, cartes stats, formulaire) |
| `static/js/app.js` | Appels API, dessin canvas (entrepôt + agents), formulaire, rafraîchissement stats |
| `requirements.txt` | Ajout de `flask>=3.0.0` |
| `docs/rapport_day6.md` | Ce rapport |

---

## Détails techniques

- **Allocation** : même logique que le Jour 1 (First-Fit) : `main.allocate_first_fit` après enrichissement des commandes et tri par heure de réception.
- **Positions des agents** : pour chaque agent ayant au moins une commande assignée, la position affichée est le premier emplacement à visiter de sa première commande ; sinon l’entrée.
- **Rafraîchissement** : pas de WebSocket ; le frontend interroge `/api/stats` toutes les 4 secondes pour mettre à jour les chiffres et les positions des agents.

---

*Rapport généré pour l’extension Jour 6 — Projet OptiPick*
