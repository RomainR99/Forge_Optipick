#!/bin/bash
# Script pour créer et configurer l'environnement virtuel

cd "$(dirname "$0")"

echo "🔧 Création de l'environnement virtuel..."

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Environnement virtuel créé"
else
    echo "ℹ️  Environnement virtuel existe déjà"
fi

# Activer l'environnement virtuel
echo "📦 Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo "⬆️  Mise à jour de pip..."
pip install --upgrade pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

# Installer les dépendances
echo "📥 Installation des dépendances depuis requirements.txt..."
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

# Installer minizinc
echo "📥 Installation de minizinc..."
pip install minizinc --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

echo ""
echo "✅ Installation terminée !"
echo ""
echo "Pour activer l'environnement virtuel :"
echo "  source venv/bin/activate"
echo ""
echo "Pour désactiver :"
echo "  deactivate"
