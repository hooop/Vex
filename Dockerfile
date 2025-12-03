FROM --platform=linux/amd64 ubuntu:22.04

# Éviter les questions interactives pendant l'installation
ENV DEBIAN_FRONTEND=noninteractive

# Installer Valgrind, gcc, Python et les outils nécessaires
RUN apt-get update && apt-get install -y \
    valgrind \
    gcc \
    python3 \
    python3-pip \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copier les requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copier tous les fichiers du projet
COPY . .

# Créer un fichier .env template si il n'existe pas
RUN if [ ! -f .env ]; then \
    echo "MISTRAL_API_KEY=your_api_key_here" > .env; \
    fi

# Compiler le programme de test
# RUN gcc -g -o leaky leaky.c

# Par défaut, ouvrir un shell bash
CMD ["/bin/bash"]
