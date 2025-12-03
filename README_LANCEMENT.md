# 🚀 Guide de Lancement de Vex

## Prérequis
- macOS avec Colima installé
- Docker installé
- Une clé API Mistral (https://console.mistral.ai/)

---

## 🎯 Méthode Simple (Recommandée)

### 1. Cloner/Naviguer vers le projet
```bash
cd /chemin/vers/vex
```

### 2. Créer le fichier .env
```bash
echo "MISTRAL_API_KEY=ta_vraie_clé_ici" > .env
```

⚠️ **IMPORTANT** : Remplace `ta_vraie_clé_ici` par ta vraie clé API Mistral !

### 3. Rendre le script exécutable
```bash
chmod +x run_vex.sh
```

### 4. Lancer Vex
```bash
./run_vex.sh
```

Le script va :
- ✅ Vérifier que Colima tourne (et le démarrer si besoin)
- ✅ Vérifier le fichier .env
- ✅ Builder l'image Docker
- ✅ Lancer le container
- ✅ T'ouvrir un shell interactif dedans

### 5. Dans le container, lance Vex !
```bash
python3 vex.py ./leaky
```

---

## 🔧 Méthode Manuelle

Si tu préfères faire étape par étape :

### 1. Démarrer Colima
```bash
colima start
```

### 2. Créer le fichier .env
```bash
echo "MISTRAL_API_KEY=ta_clé_api_mistral" > .env
```

### 3. Builder l'image Docker
```bash
docker build -t vex:latest .
```

### 4. Lancer le container
```bash
docker run -it --rm -v "$(pwd):/app" -w /app vex:latest /bin/bash
```

### 5. Dans le container, utiliser Vex
```bash
# Tester avec le programme de test
python3 vex.py ./leaky

# Ou tester le pipeline complet
python3 test_pipeline.py

# Ou lancer Valgrind directement
valgrind --leak-check=full ./leaky
```

---

## 📝 Commandes Utiles

### Dans le container Docker

```bash
# Analyser un programme avec Vex
python3 vex.py ./mon_programme

# Analyser avec des arguments
python3 vex.py ./push_swap 3 2 1

# Tester le pipeline complet
python3 test_pipeline.py

# Tester l'extraction de code
python3 test_extractor.py

# Lancer Valgrind directement
valgrind --leak-check=full --track-origins=yes ./leaky

# Compiler un nouveau programme C
gcc -g -o mon_prog mon_prog.c

# Quitter le container
exit
```

### Sur ton Mac (hors container)

```bash
# Vérifier le statut de Colima
colima status

# Démarrer Colima
colima start

# Arrêter Colima
colima stop

# Lister les images Docker
docker images

# Lister les containers actifs
docker ps

# Supprimer l'image Vex (pour la rebuilder)
docker rmi vex:latest
```

---

## 🐛 Troubleshooting

### ❌ "Colima n'est pas démarré"
```bash
colima start
```

### ❌ "MISTRAL_API_KEY n'est pas définie"
Vérifie que ton fichier `.env` existe et contient :
```
MISTRAL_API_KEY=ta_vraie_clé
```

### ❌ "docker: command not found"
Tu dois installer Docker Desktop ou Docker CLI

### ❌ Le container ne démarre pas
```bash
# Supprimer l'ancienne image
docker rmi vex:latest

# Rebuilder
docker build -t vex:latest .
```

### ❌ "Permission denied" sur run_vex.sh
```bash
chmod +x run_vex.sh
```

---

## 📂 Structure du Projet

```
vex/
├── vex.py                  # Point d'entrée principal
├── valgrind_runner.py      # Exécute Valgrind
├── valgrind_parser.py      # Parse les rapports Valgrind
├── code_extractor.py       # Extrait le code source
├── mistral_api.py          # Communique avec Mistral AI
├── mistral_analyzer.py     # Wrapper pour l'analyse
├── display.py              # Affichage des résultats
├── leaky.c                 # Programme de test avec memory leaks
├── requirements.txt        # Dépendances Python
├── Dockerfile              # Configuration Docker
├── run_vex.sh              # Script de lancement simplifié
└── .env                    # Clé API Mistral (à créer)
```

---

## 🎓 Workflow Complet

```
1. Tu lances: ./run_vex.sh
              ↓
2. Colima démarre (si pas déjà fait)
              ↓
3. Docker build l'image avec:
   - Ubuntu 22.04
   - Valgrind
   - gcc
   - Python 3
   - Toutes les dépendances Python
              ↓
4. Container démarre avec ton projet monté en volume
              ↓
5. Tu lances: python3 vex.py ./leaky
              ↓
6. Vex exécute:
   - Valgrind sur ton programme
   - Parse le rapport
   - Extrait le code source
   - Envoie à Mistral AI
   - Affiche l'analyse pédagogique
```

---

## ✨ Exemple de Session

```bash
$ ./run_vex.sh
🚀 Lancement de Vex avec Docker + Colima

📋 Étape 1/5: Vérification de Colima...
✅ Colima est déjà démarré

📋 Étape 2/5: Vérification du fichier .env...
✅ Fichier .env trouvé

📋 Étape 3/5: Build de l'image Docker...
✅ Image buildée

📋 Étape 4/5: Lancement du container...
✅ Container démarré

📋 Étape 5/5: Ouverture du shell dans le container...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Vous êtes maintenant dans le container Docker !
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

root@abc123:/app# python3 vex.py ./leaky
🔍 Analyse de ./leaky avec Valgrind...
📝 Parsing du rapport Valgrind...
⚠️  3 erreur(s) détectée(s)

🔎 Extraction du contexte du code...
🤖 Analyse avec Mistral AI...

┌──────────────────────────────────────────────────────────┐
│ ERREUR #1/3                                              │
└──────────────────────────────────────────────────────────┘
...
```

---

## 🎯 Pour Aller Plus Loin

- Modifier `mistral_api.py` pour changer le prompt
- Ajouter d'autres programmes C de test
- Améliorer l'affichage dans `display.py`
- Tester avec tes propres projets 42 (minishell, push_swap, etc.)

---

**Bon courage pour ta candidature chez Mistral AI ! 🚀**
