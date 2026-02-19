# EXTENSION 1 : PICKING MULTI-NIVEAUX

## Vue d'ensemble

L'extension 1 introduit une **3ᵉ dimension** dans le modèle d'allocation : la **hauteur** des étagères. Chaque emplacement d'entrepôt possède désormais un niveau (1 à 5), ce qui complexifie les décisions d'allocation car tous les agents n'ont pas les mêmes capacités d'accès.

---

## Règles métier

| Type d'agent | Niveaux accessibles | Moyen d'accès |
|--------------|---------------------|---------------|
| **Robot**    | 1-2 uniquement      | Portée physique limitée |
| **Humain**   | 1-5 (tous)          | Escabeau / échelle |
| **Chariot**  | Suit l'humain       | — |

- **Robots** : Ne peuvent accéder qu'aux niveaux 1 et 2. Une commande contenant au moins un produit sur niveau 3, 4 ou 5 **ne peut pas** leur être assignée.
- **Humains** : Peuvent atteindre tous les niveaux (avec escabeau si nécessaire).
- **Chariots** : Ne font pas le picking directement ; leur allocation dépend de l'humain qui les utilise.

---

## Impact sur l'allocation

### Complexité accrue

- Le solveur doit vérifier, pour chaque couple (commande, agent), que l'agent peut accéder à **tous** les emplacements des produits de la commande.
- Les commandes « hautes » (contenant des items sur niveaux 3-5) sont **réservées aux humains**.
- La contrainte réduit le nombre de commandes potentiellement assignables aux robots, ce qui peut augmenter la charge des humains ou le nombre de commandes non assignées si peu d'humains sont disponibles.

### Paramètre ajouté

Pour chaque commande, on calcule un booléen :

- **`order_has_high_level`** = `true` si la commande contient **au moins un** produit situé sur un niveau 3, 4 ou 5.

### Contrainte MiniZinc

```minizinc
% 7. EXTENSION 1 : Restrictions multi-niveaux (picking)
% Les robots (agent_type=0) ne peuvent accéder qu'aux niveaux 1-2.
constraint forall(order_idx in ORDERS, agent_idx in AGENTS) (
    (assignment[order_idx] == agent_idx /\ agent_type[agent_idx] == 0) ->
    (not order_has_high_level[order_idx])
);
```

**Lecture** : Si une commande est assignée à un robot, alors cette commande ne doit **pas** contenir de produit sur niveau 3, 4 ou 5.

---

## Extension future : temps d'accès par niveau

Le cahier des charges mentionne que *« le temps d'accès varie selon le niveau »*. Pour une extension ultérieure :

- Associer un coût ou un temps par niveau (ex. niveau 1 = 1 min, niveau 5 = 3 min).
- Intégrer ce coût dans la fonction objectif (ex. minimiser le temps total de picking).
- Adapter le modèle MiniZinc pour sommer ces coûts selon les commandes assignées à chaque agent.

---

## Données requises

Pour activer l'extension, chaque **produit** doit posséder un attribut `level` (1 à 5) :

```json
{
  "id": "Product_001",
  "name": "Laptop",
  "location": [1, 0],
  "level": 2
}
```

En l'absence de `level`, le solver utilise par défaut `level = 1`, donc aucune commande n'est considérée comme « haute » et la contrainte reste inactive (comportement rétrocompatible).
