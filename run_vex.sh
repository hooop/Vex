#!/bin/bash

# Script de lancement de Vex avec Docker + Colima
# Usage: ./run_vex.sh

set -e

echo "🚀 Lancement de Vex avec Docker + Colima"
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier que Colima tourne
echo -e "${BLUE}📋 Étape 1/5: Vérification de Colima...${NC}"
if ! colima status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Colima n'est pas démarré. Démarrage...${NC}"
    colima start
else
    echo -e "${GREEN}✅ Colima est déjà démarré${NC}"
fi
echo ""

# 2. Vérifier le fichier .env
echo -e "${BLUE}📋 Étape 2/5: Vérification du fichier .env...${NC}"
if [ ! -f .env ] || grep -q "your_api_key_here" .env; then
    echo -e "${YELLOW}⚠️  Fichier .env manquant ou incomplet${NC}"
    echo -e "${YELLOW}   Créez un fichier .env avec votre clé API Mistral:${NC}"
    echo -e "${YELLOW}   MISTRAL_API_KEY=votre_clé_ici${NC}"
    echo ""
    read -p "Voulez-vous continuer quand même ? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Fichier .env trouvé${NC}"
fi
echo ""

# 3. Builder l'image Docker (avec support Apple Silicon)
echo -e "${BLUE}📋 Étape 3/5: Build de l'image Docker...${NC}"
docker build --platform linux/amd64 -t vex:latest .
echo -e "${GREEN}✅ Image buildée${NC}"
echo ""

# 4. Lancer le container
echo -e "${BLUE}📋 Étape 4/5: Lancement du container...${NC}"
echo -e "${GREEN}✅ Container démarré${NC}"
echo ""

# 5. Ouvrir un shell interactif
echo -e "${BLUE}📋 Étape 5/5: Ouverture du shell dans le container...${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🎯 Vous êtes maintenant dans le container Docker !${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Commandes disponibles:${NC}"
echo -e "  ${BLUE}• python3 vex.py ./leaky${NC}          → Analyser le programme de test"
echo -e "  ${BLUE}• python3 test_pipeline.py${NC}        → Tester le pipeline complet"
echo -e "  ${BLUE}• valgrind --leak-check=full ./leaky${NC} → Lancer Valgrind directement"
echo -e "  ${BLUE}• exit${NC}                            → Quitter le container"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Lancer le container avec un shell interactif (avec support Apple Silicon)
docker run --platform linux/amd64 -it --rm \
    -v "$(pwd):/app" \
    -w /app \
    vex:latest \
    /bin/bash

echo ""
echo -e "${GREEN}✨ Container arrêté. À bientôt !${NC}"