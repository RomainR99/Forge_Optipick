"""
Tests unitaires pour les contraintes du projet OptiPick (Jour 2).
"""
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models import (
    Location,
    Warehouse,
    Product,
    Order,
    OrderItem,
    Agent,
    Robot,
    Human,
    Cart,
)
from src.constraints import (
    get_product_zone,
    can_combine,
    check_robot_restrictions,
    check_cart_human_association,
    can_agent_take_order_with_constraints,
)


def test_get_product_zone():
    """Test de détermination de la zone d'un produit."""
    warehouse = Warehouse(
        width=10,
        height=8,
        zones={
            "A": [Location(1, 0), Location(1, 1)],
            "B": [Location(5, 0), Location(5, 1)],
        },
        entry_point=Location(0, 0)
    )
    
    assert get_product_zone(warehouse, Location(1, 0)) == "A"
    assert get_product_zone(warehouse, Location(5, 1)) == "B"
    assert get_product_zone(warehouse, Location(9, 9)) is None


def test_can_combine():
    """Test de vérification des incompatibilités entre produits."""
    # Produits compatibles
    p1 = Product("P1", "Produit 1", "cat1", 1.0, 1.0, Location(0, 0), incompatible_with=[])
    p2 = Product("P2", "Produit 2", "cat2", 2.0, 2.0, Location(1, 1), incompatible_with=[])
    
    assert can_combine([p1, p2]) == True
    
    # Produits incompatibles
    p3 = Product("P3", "Produit 3", "cat1", 1.0, 1.0, Location(0, 0), incompatible_with=["P4"])
    p4 = Product("P4", "Produit 4", "cat2", 2.0, 2.0, Location(1, 1), incompatible_with=["P3"])
    
    assert can_combine([p3, p4]) == False
    assert can_combine([p3]) == True  # Un seul produit est toujours compatible


def test_check_robot_restrictions_zones():
    """Test des restrictions de zones pour les robots."""
    warehouse = Warehouse(
        width=10,
        height=8,
        zones={
            "A": [Location(1, 0)],
            "C": [Location(8, 0)],
        },
        entry_point=Location(0, 0)
    )
    
    robot = Robot("R1", "robot", 20.0, 30.0, 2.0, 5.0, restrictions={"no_zones": ["C"]})
    
    # Commande avec produit dans zone interdite
    order_bad = Order("O1", "10:00", "12:00", "standard", [
        OrderItem("P1", 1)
    ])
    order_bad.unique_locations = [Location(8, 0)]  # Zone C interdite
    
    products = {"P1": Product("P1", "Test", "cat", 1.0, 1.0, Location(8, 0))}
    
    assert check_robot_restrictions(robot, order_bad, products, warehouse, robot.restrictions) == False
    
    # Commande avec produit dans zone autorisée
    order_good = Order("O2", "10:00", "12:00", "standard", [
        OrderItem("P2", 1)
    ])
    order_good.unique_locations = [Location(1, 0)]  # Zone A autorisée
    
    products["P2"] = Product("P2", "Test2", "cat", 1.0, 1.0, Location(1, 0))
    
    assert check_robot_restrictions(robot, order_good, products, warehouse, robot.restrictions) == True


def test_check_robot_restrictions_fragile():
    """Test des restrictions sur les objets fragiles."""
    warehouse = Warehouse(width=10, height=8, zones={}, entry_point=Location(0, 0))
    
    robot = Robot("R1", "robot", 20.0, 30.0, 2.0, 5.0, restrictions={"no_fragile": True})
    
    # Commande avec produit fragile
    order_fragile = Order("O1", "10:00", "12:00", "standard", [
        OrderItem("P1", 1)
    ])
    order_fragile.unique_locations = [Location(1, 0)]
    
    products = {
        "P1": Product("P1", "Fragile", "cat", 1.0, 1.0, Location(1, 0), fragile=True)
    }
    
    assert check_robot_restrictions(robot, order_fragile, products, warehouse, robot.restrictions) == False
    
    # Commande sans produit fragile
    order_safe = Order("O2", "10:00", "12:00", "standard", [
        OrderItem("P2", 1)
    ])
    order_safe.unique_locations = [Location(1, 0)]
    
    products["P2"] = Product("P2", "Safe", "cat", 1.0, 1.0, Location(1, 0), fragile=False)
    
    assert check_robot_restrictions(robot, order_safe, products, warehouse, robot.restrictions) == True


def test_check_robot_restrictions_max_weight():
    """Test des restrictions de poids maximum par item."""
    warehouse = Warehouse(width=10, height=8, zones={}, entry_point=Location(0, 0))
    
    robot = Robot("R1", "robot", 20.0, 30.0, 2.0, 5.0, restrictions={"max_item_weight": 10.0})
    
    # Commande avec produit trop lourd
    order_heavy = Order("O1", "10:00", "12:00", "standard", [
        OrderItem("P1", 1)
    ])
    order_heavy.unique_locations = [Location(1, 0)]
    
    products = {
        "P1": Product("P1", "Heavy", "cat", 15.0, 1.0, Location(1, 0))  # 15kg > 10kg max
    }
    
    assert check_robot_restrictions(robot, order_heavy, products, warehouse, robot.restrictions) == False
    
    # Commande avec produit acceptable
    order_ok = Order("O2", "10:00", "12:00", "standard", [
        OrderItem("P2", 1)
    ])
    order_ok.unique_locations = [Location(1, 0)]
    
    products["P2"] = Product("P2", "OK", "cat", 8.0, 1.0, Location(1, 0))  # 8kg <= 10kg max
    
    assert check_robot_restrictions(robot, order_ok, products, warehouse, robot.restrictions) == True


def test_check_cart_human_association():
    """Test de l'association chariot-humain."""
    warehouse = Warehouse(width=10, height=8, zones={}, entry_point=Location(0, 0))
    
    cart = Cart("C1", "cart", 50.0, 80.0, 1.2, 3.0, restrictions={"requires_human": True})
    human = Human("H1", "human", 35.0, 50.0, 1.5, 25.0, restrictions={})
    
    order = Order("O1", "10:00", "12:00", "standard", [
        OrderItem("P1", 1)
    ])
    order.total_weight = 10.0
    order.total_volume = 10.0
    order.unique_locations = [Location(1, 0)]
    
    agents = [cart, human]
    assignment = {}
    
    # Le chariot peut être assigné car un humain est disponible
    assert check_cart_human_association(cart, order, agents, assignment) == True
    
    # Sans humain disponible
    agents_no_human = [cart]
    assert check_cart_human_association(cart, order, agents_no_human, assignment) == False


def test_can_agent_take_order_with_constraints():
    """Test complet de toutes les contraintes."""
    warehouse = Warehouse(
        width=10,
        height=8,
        zones={"A": [Location(1, 0)], "C": [Location(8, 0)]},
        entry_point=Location(0, 0)
    )
    
    products = {
        "P1": Product("P1", "Safe", "cat", 5.0, 5.0, Location(1, 0), fragile=False, incompatible_with=[]),
        "P2": Product("P2", "Fragile", "cat", 3.0, 3.0, Location(1, 0), fragile=True, incompatible_with=[]),
        "P3": Product("P3", "Incompatible1", "cat", 2.0, 2.0, Location(1, 0), incompatible_with=["P4"]),
        "P4": Product("P4", "Incompatible2", "cat", 2.0, 2.0, Location(1, 0), incompatible_with=["P3"]),
    }
    
    # Robot avec restrictions
    robot = Robot("R1", "robot", 20.0, 30.0, 2.0, 5.0, restrictions={
        "no_zones": ["C"],
        "no_fragile": True,
        "max_item_weight": 10.0
    })
    
    # Commande valide
    order_valid = Order("O1", "10:00", "12:00", "standard", [
        OrderItem("P1", 1)
    ])
    order_valid.total_weight = 5.0
    order_valid.total_volume = 5.0
    order_valid.unique_locations = [Location(1, 0)]
    
    agents = [robot]
    assignment = {}
    
    assert can_agent_take_order_with_constraints(
        robot, order_valid, products, warehouse, robot.restrictions, agents, assignment
    ) == True
    
    # Commande avec produit fragile (interdit pour robot)
    order_fragile = Order("O2", "10:00", "12:00", "standard", [
        OrderItem("P2", 1)
    ])
    order_fragile.total_weight = 3.0
    order_fragile.total_volume = 3.0
    order_fragile.unique_locations = [Location(1, 0)]
    
    assert can_agent_take_order_with_constraints(
        robot, order_fragile, products, warehouse, robot.restrictions, agents, assignment
    ) == False
    
    # Commande avec produits incompatibles
    order_incompatible = Order("O3", "10:00", "12:00", "standard", [
        OrderItem("P3", 1),
        OrderItem("P4", 1)
    ])
    order_incompatible.total_weight = 4.0
    order_incompatible.total_volume = 4.0
    order_incompatible.unique_locations = [Location(1, 0)]
    
    assert can_agent_take_order_with_constraints(
        robot, order_incompatible, products, warehouse, robot.restrictions, agents, assignment
    ) == False


if __name__ == "__main__":
    print("🧪 Exécution des tests unitaires pour les contraintes...")
    
    test_get_product_zone()
    print("✅ test_get_product_zone")
    
    test_can_combine()
    print("✅ test_can_combine")
    
    test_check_robot_restrictions_zones()
    print("✅ test_check_robot_restrictions_zones")
    
    test_check_robot_restrictions_fragile()
    print("✅ test_check_robot_restrictions_fragile")
    
    test_check_robot_restrictions_max_weight()
    print("✅ test_check_robot_restrictions_max_weight")
    
    test_check_cart_human_association()
    print("✅ test_check_cart_human_association")
    
    test_can_agent_take_order_with_constraints()
    print("✅ test_can_agent_take_order_with_constraints")
    
    print("\n🎉 Tous les tests sont passés avec succès !")
