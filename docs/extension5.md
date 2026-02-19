# Extension 5 : Apprentissage par Renforcement (RL) pour l'Allocation Optimale

## 📋 Vue d'ensemble

L'**Extension 5** utilise l'**Apprentissage par Renforcement (RL)** pour apprendre une stratégie d'allocation optimale des commandes aux agents. Contrairement aux approches déterministes (MiniZinc, CP-SAT), le RL apprend à partir de l'expérience et peut s'adapter à des patterns complexes difficiles à modéliser explicitement.

### Contexte opérationnel

Dans un entrepôt réel :
- Les situations varient constamment (nouvelles commandes, pannes, congestion)
- Des patterns complexes émergent (certaines combinaisons commande-agent sont plus efficaces)
- L'environnement évolue (apprentissage continu)

Le RL permet d'apprendre ces patterns et de s'adapter automatiquement.

---

## 🎯 Objectifs de l'extension

1. **Apprendre une politique d'allocation** : Quelle commande assigner à quel agent dans quelles conditions
2. **Optimiser les récompenses** : Maximiser la performance globale (distance, coût, respect des deadlines)
3. **S'adapter dynamiquement** : Apprendre de nouvelles situations sans reprogrammation
4. **Intégrer avec MiniZinc** : Utiliser la politique apprise pour guider l'optimisation

---

## 🧠 Concepts du RL

### Éléments fondamentaux

1. **État (State)** : Configuration actuelle de l'entrepôt
   - Commandes en attente
   - État des agents (disponibilité, charge)
   - Zones congestionnées
   - Historique récent

2. **Action (Action)** : Décision à prendre
   - Assigner une commande à un agent
   - Ordre de visite des emplacements (pour TSP)

3. **Récompense (Reward)** : Score de performance
   - `-distance` : Minimiser la distance parcourue
   - `-coût` : Minimiser le coût opérationnel
   - `+respect_deadline` : Bonus si deadline respectée
   - Pénalités pour les échecs

4. **Politique (Policy)** : Stratégie apprise
   - Fonction qui mappe état → action
   - Apprise par essais-erreurs

---

## 🔧 Architecture proposée

### 1️⃣ Environnement RL (Gymnasium/Stable-Baselines3)

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, List, Tuple, Optional

class WarehouseAllocationEnv(gym.Env):
    """
    Environnement RL pour l'allocation de commandes dans un entrepôt.
    """
    
    def __init__(
        self,
        warehouse: Warehouse,
        agents: List[Agent],
        orders: List[Order],
        products_by_id: Dict[str, Product]
    ):
        super().__init__()
        
        self.warehouse = warehouse
        self.agents = agents
        self.orders = orders
        self.products_by_id = products_by_id
        
        # Espace d'observation (état)
        # Vecteur de features : [commandes_features, agents_features, zones_features]
        n_order_features = 10  # poids, volume, zone, express, etc.
        n_agent_features = 8   # capacité, vitesse, type, charge, etc.
        n_zone_features = 5    # congestion par zone
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(len(orders) * n_order_features + len(agents) * n_agent_features + n_zone_features,),
            dtype=np.float32
        )
        
        # Espace d'action : (order_idx, agent_idx)
        # Action discrète : index dans la matrice order×agent
        self.action_space = spaces.Discrete(len(orders) * len(agents))
        
        # État initial
        self.reset()
    
    def reset(self, seed=None, options=None):
        """Réinitialise l'environnement."""
        super().reset(seed=seed)
        
        # Réinitialiser les agents
        for agent in self.agents:
            agent.assigned_orders = []
            agent.used_weight = 0.0
            agent.used_volume = 0.0
        
        # Commandes non assignées
        self.pending_orders = self.orders.copy()
        self.assigned_orders = []
        
        # Métriques
        self.total_distance = 0.0
        self.total_cost = 0.0
        self.missed_deadlines = 0
        
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def step(self, action: int):
        """
        Exécute une action et retourne (observation, reward, terminated, truncated, info).
        """
        # Décoder l'action : (order_idx, agent_idx)
        order_idx = action // len(self.agents)
        agent_idx = action % len(self.agents)
        
        # Vérifier la validité de l'action
        if order_idx >= len(self.pending_orders):
            # Action invalide : pénalité
            reward = -100.0
            terminated = False
            truncated = False
            info = {"invalid_action": True}
            return self._get_observation(), reward, terminated, truncated, info
        
        order = self.pending_orders[order_idx]
        agent = self.agents[agent_idx]
        
        # Vérifier les contraintes
        valid, reason = self._check_constraints(order, agent)
        
        if not valid:
            # Contrainte violée : pénalité
            reward = -50.0
            terminated = False
            truncated = False
            info = {"constraint_violated": reason}
            return self._get_observation(), reward, terminated, truncated, info
        
        # Assigner la commande
        agent.assign(order)
        self.pending_orders.remove(order)
        self.assigned_orders.append(order)
        
        # Calculer la récompense
        reward = self._calculate_reward(order, agent)
        
        # Vérifier si terminé (toutes les commandes assignées ou impossibles)
        terminated = len(self.pending_orders) == 0
        truncated = False
        
        # Mettre à jour les métriques
        info = {
            "assigned": True,
            "order_id": order.id,
            "agent_id": agent.id,
            "total_assigned": len(self.assigned_orders)
        }
        
        observation = self._get_observation()
        return observation, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """
        Construit le vecteur d'observation (état).
        """
        features = []
        
        # Features des commandes en attente
        for order in self.pending_orders:
            features.extend([
                order.total_weight,
                order.total_volume,
                float(order.priority == "express"),
                float(len(order.items)),
                # Zone principale
                float(self._get_order_zone(order)),
                # Temps restant avant deadline (normalisé)
                self._get_time_until_deadline(order),
                # Fragile
                float(any(self.products_by_id.get(item.product_id, Product(...)).fragile 
                         for item in order.items)),
                # Poids max item
                max((self.products_by_id.get(item.product_id, Product(...)).weight 
                     for item in order.items), default=0.0),
                # Nombre de locations uniques
                float(len(order.unique_locations)),
                0.0  # Padding
            ])
        
        # Padding pour les commandes manquantes
        max_orders = len(self.orders)
        while len(features) < max_orders * 10:
            features.extend([0.0] * 10)
        
        # Features des agents
        for agent in self.agents:
            features.extend([
                agent.capacity_weight,
                agent.capacity_volume,
                agent.speed,
                agent.cost_per_hour,
                float(agent.type == "robot"),
                float(agent.type == "human"),
                agent.used_weight / agent.capacity_weight if agent.capacity_weight > 0 else 0.0,
                agent.used_volume / agent.capacity_volume if agent.capacity_volume > 0 else 0.0
            ])
        
        # Features des zones (congestion)
        zone_features = [0.0] * 5  # À remplir avec les données de congestion réelles
        features.extend(zone_features)
        
        return np.array(features, dtype=np.float32)
    
    def _check_constraints(self, order: Order, agent: Agent) -> Tuple[bool, str]:
        """Vérifie si l'assignation respecte les contraintes."""
        # Capacité
        if not agent.can_take(order):
            return False, "capacity_exceeded"
        
        # Restrictions des robots (simplifié)
        if agent.type == "robot":
            # Vérifier zones interdites, fragile, etc.
            # (implémentation détaillée)
            pass
        
        return True, "ok"
    
    def _calculate_reward(self, order: Order, agent: Agent) -> float:
        """
        Calcule la récompense pour une assignation.
        Récompense = -distance -coût +respect_deadline
        """
        reward = 0.0
        
        # Distance estimée (simplifiée)
        distance = self._estimate_order_distance(order)
        reward -= distance * 0.1  # Pénalité distance
        
        # Coût opérationnel
        time_estimate = distance / agent.speed if agent.speed > 0 else 0
        cost = time_estimate * agent.cost_per_hour / 3600
        reward -= cost * 10.0  # Pénalité coût
        
        # Respect des deadlines
        if self._check_deadline(order, time_estimate):
            reward += 100.0  # Bonus deadline respectée
        
        # Bonus pour express
        if order.priority == "express":
            reward += 50.0
        
        return reward
    
    def _estimate_order_distance(self, order: Order) -> float:
        """Estime la distance pour préparer une commande."""
        entry = self.warehouse.entry_point
        return sum(entry.manhattan(loc) for loc in order.unique_locations)
    
    def _check_deadline(self, order: Order, time_estimate: float) -> bool:
        """Vérifie si la deadline peut être respectée."""
        # Implémentation simplifiée
        return True  # À implémenter avec les vraies deadlines
    
    def _get_order_zone(self, order: Order) -> int:
        """Retourne la zone principale de la commande."""
        # Implémentation simplifiée
        return 0
    
    def _get_time_until_deadline(self, order: Order) -> float:
        """Retourne le temps restant avant deadline (normalisé)."""
        # Implémentation simplifiée
        return 1.0
```

---

## 🚀 Implémentation avec Stable-Baselines3

### Installation

```bash
pip install stable-baselines3[extra] gymnasium
```

### Entraînement

```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback

# Créer l'environnement
env = WarehouseAllocationEnv(warehouse, agents, orders, products_by_id)

# Créer un environnement vectorisé (pour parallélisation)
vec_env = make_vec_env(
    lambda: WarehouseAllocationEnv(warehouse, agents, orders, products_by_id),
    n_envs=4  # 4 environnements en parallèle
)

# Créer le modèle (PPO = Proximal Policy Optimization)
model = PPO(
    "MlpPolicy",
    vec_env,
    verbose=1,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    tensorboard_log="./logs/"
)

# Callback pour évaluation
eval_callback = EvalCallback(
    env,
    best_model_save_path="./models/best_rl_policy/",
    log_path="./logs/eval/",
    eval_freq=10000,
    deterministic=True,
    render=False
)

# Entraîner
model.learn(
    total_timesteps=1_000_000,  # 1 million de steps
    callback=eval_callback,
    progress_bar=True
)

# Sauvegarder le modèle
model.save("./models/rl_allocation_policy")
```

---

## 🔗 Intégration avec MiniZinc

### Utilisation de la politique apprise

Une fois la politique RL entraînée, on peut l'utiliser pour guider l'optimisation MiniZinc :

```python
def get_rl_preference_scores(
    orders: List[Order],
    agents: List[Agent],
    rl_model: PPO,
    warehouse: Warehouse
) -> List[List[float]]:
    """
    Génère les scores de préférence RL pour chaque paire (commande, agent).
    """
    scores = []
    
    for order in orders:
        order_scores = []
        for agent in agents:
            # Construire l'état pour cette assignation
            state = build_state_for_assignment(order, agent, warehouse)
            
            # Obtenir la probabilité d'action depuis le modèle RL
            # (simplifié : utiliser la politique déterministe)
            action = rl_model.predict(state, deterministic=True)[0]
            
            # Score basé sur la probabilité ou la valeur Q
            score = get_action_score(rl_model, state, action)
            order_scores.append(score)
        
        scores.append(order_scores)
    
    return scores

# Utiliser dans MiniZinc
rl_scores = get_rl_preference_scores(orders, agents, model, warehouse)
instance["rl_preference_scores"] = rl_scores
```

---

## 📊 Métriques et évaluation

### Métriques à suivre pendant l'entraînement

1. **Récompense moyenne** : Performance globale
2. **Taux d'assignation** : % de commandes assignées
3. **Distance moyenne** : Distance parcourue par commande
4. **Coût moyen** : Coût opérationnel par commande
5. **Taux de respect des deadlines** : % de deadlines respectées

### Comparaison avec MiniZinc

```python
def compare_rl_vs_minizinc(orders, agents, warehouse):
    """Compare les performances RL vs MiniZinc."""
    
    # Solution RL
    rl_assignment = solve_with_rl(orders, agents, warehouse)
    rl_metrics = evaluate_assignment(rl_assignment, orders, agents, warehouse)
    
    # Solution MiniZinc
    minizinc_assignment = allocate_with_minizinc(orders, agents, products_by_id, warehouse)
    minizinc_metrics = evaluate_assignment(minizinc_assignment, orders, agents, warehouse)
    
    print("Comparaison RL vs MiniZinc:")
    print(f"RL - Distance: {rl_metrics['distance']:.2f}, Coût: {rl_metrics['cost']:.2f}")
    print(f"MiniZinc - Distance: {minizinc_metrics['distance']:.2f}, Coût: {minizinc_metrics['cost']:.2f}")
```

---

## 🎓 Avantages et limitations

### ✅ Avantages du RL

1. **Adaptabilité** : S'adapte à de nouvelles situations
2. **Patterns complexes** : Apprend des patterns difficiles à modéliser
3. **Apprentissage continu** : Améliore avec le temps
4. **Robustesse** : Gère bien les imprévus

### ❌ Limitations

1. **Temps d'entraînement** : Nécessite beaucoup de données et de temps
2. **Exploration** : Peut prendre de mauvaises décisions pendant l'apprentissage
3. **Interprétabilité** : Difficile de comprendre pourquoi une décision est prise
4. **Stabilité** : Peut nécessiter un réentraînement régulier

---

## 📝 Résumé

| Élément | Description |
|---------|-------------|
| **État** | Configuration entrepôt + commandes en attente |
| **Action** | Assigner commande à agent |
| **Récompense** | `-distance -coût +respect_deadline` |
| **Algorithme** | PPO (Proximal Policy Optimization) |
| **Outil** | Stable-Baselines3 |
| **Intégration** | Scores de préférence dans MiniZinc |

---

## 🔗 Références

- **Modèle** : `models/allocation.mzn` (lignes 48-50, 162-165)
- **Documentation Stable-Baselines3** : https://stable-baselines3.readthedocs.io/
- **Gymnasium** : https://gymnasium.farama.org/

---

## 💡 Exemple complet d'utilisation

```python
from stable_baselines3 import PPO
from src.models import Warehouse, Agent, Order, Product
from src.rl_env import WarehouseAllocationEnv

# Charger les données
warehouse = load_warehouse("data/warehouse.json")
agents = load_agents("data/agents.json")
orders = load_orders("data/orders.json")
products_by_id = load_products("data/products.json")

# Créer l'environnement
env = WarehouseAllocationEnv(warehouse, agents, orders, products_by_id)

# Entraîner le modèle
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=1_000_000)
model.save("models/rl_policy")

# Utiliser la politique
obs, info = env.reset()
done = False
while not done:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated

# Évaluer les performances
print(f"Commandes assignées: {len(env.assigned_orders)}/{len(orders)}")
print(f"Distance totale: {env.total_distance:.2f}")
print(f"Coût total: {env.total_cost:.2f}")
```

---

## 🎓 Conclusion

L'Extension 5 apporte une approche d'apprentissage par renforcement pour l'allocation optimale :

- ✅ **Apprentissage adaptatif** : S'adapte aux patterns complexes
- ✅ **Optimisation continue** : Améliore avec l'expérience
- ✅ **Intégration flexible** : Peut guider MiniZinc ou fonctionner indépendamment
- ✅ **Robustesse** : Gère bien les imprévus et situations nouvelles

Le RL complète les approches déterministes (MiniZinc, CP-SAT) en apportant de l'adaptabilité et de l'apprentissage continu, particulièrement utile dans des environnements dynamiques et changeants.
