<pre>
          ████
██  ██  ██      ██  ██
██  ██  ████      ██
  ██    ██      ██  ██
          ████
</pre>

# Vex - Valgrind Error eXplorer

**Vex** analyse automatiquement votre programme avec Valgrind, explique et propose une solution aux erreurs mémoire détectées.

## Le problème

Durant mes études à l'école 42, résoudre les memory leaks fut une tâche ardue.
Valgrind détecte les fuites et indique où la mémoire a été allouée, mais il n'explique pas comment les corriger. Il faut remonter la pile d'appel, comprendre le contexte, identifier la vraie cause.

**Vex** fait ce travail d'analyse automatiquement :

- Quelle ligne cause réellement le problème
- Pourquoi cette ligne crée un leak
- Comment le corriger concrètement

## Fonctionnalités

- **Analyse automatique** : Lance Valgrind, parse le rapport, extrait le contexte du code
- **Explications IA** : Utilise Mistral AI pour fournir des diagnostics pédagogiques
- **Interface soignée** : Affichage terminal propre avec formatage ANSI
- **Workflow interactif** : Analyse un leak à la fois pour corriger progressivement
- **Catégorisation intelligente** : Identifie 3 types de leaks (mémoire jamais free, pointeur perdu, mémoire inaccessible)
- **Focus "definitely lost"** : Se concentre sur les fuites mémoire critiques (v1.0)

<p align="center" width="100%">
<video src="https://github.com/user-attachments/assets/7be31c2f-237b-4f91-84b4-e52598e19091" width="100%" controls></video>
</p>

## Installation & Usage

### Prérequis

- Docker
- Make
- Clé API Mistral (créez un fichier `.env` avec `MISTRAL_API_KEY=votre_clé`)

### Lancement

```bash
# Premier build (2-3 min, mis en cache ensuite)
make build

# Lancer l'analyse sur le programme d'exemple
make run
```

Le programme analyse automatiquement `examples/leaky.c`, un fichier de test contenant plusieurs types de memory leaks.

### Structure du projet

```
vex/
├── Dockerfile           # Configuration Docker (Ubuntu + Valgrind)
├── Makefile             # Point d'entrée (build, run, shell)
├── requirements.txt     # Dépendances Python
├── srcs/                # Code source Python
│   ├── vex.py          # Point d'entrée principal
│   ├── valgrind_runner.py
│   ├── valgrind_parser.py
│   ├── code_extractor.py
│   ├── mistral_analyzer.py
│   └── display.py
└── examples/            # Programmes de test
    ├── Makefile
    └── leaky.c         # Programme avec memory leaks
```

## À qui s'adresse Vex ?

**Vex** est conçu pour tous ceux qui apprennent ou utilisent le C. L'objectif n'est pas de masquer les erreurs mais d'apprendre en comprenant.

Chaque analyse explique :
- Le concept mémoire sous-jacent
- L'erreur concrète dans votre code
- La solution recommandée

<img src="leak.png" alt="Aperçu Valgrind Error eXplorer" width="800">

## Roadmap

### Version actuelle (v1.0)
- Analyse de programmes simples
- Catégorisation des leaks (Type 1, 2, 3)
- Focus sur "definitely lost" leaks
- Workflow interactif avec recompilation
- Limité à `examples/leaky.c` pour la démo

### À venir
- **Utilisation générique** : `vex ./mon_prog [args]` pour n'importe quel programme
- **Support des free() externes** : Détecter les fonctions de nettoyage personnalisées
- **Analyse multi-fichiers** : Projets C complexes avec plusieurs sources
- **Export des analyses** : Sauvegarde des diagnostics en Markdown

## Architecture technique

**Pipeline d'analyse :**
1. `valgrind_runner.py` : Exécute Valgrind avec les bons flags
2. `valgrind_parser.py` : Parse le rapport, extrait la backtrace
3. `code_extractor.py` : Récupère le contexte complet des fonctions
4. `mistral_analyzer.py` : Envoie à Mistral AI pour analyse
5. `display.py` : Formate et affiche le diagnostic

**Prompt engineering :**
Le prompt Mistral utilise un système de "labels" (OWNER, EMBEDDED, TRANSFERRED, FREED, LEAK) pour tracer la responsabilité de libération mémoire à travers la call stack.

## Notes techniques

- Développé sur Mac M3 (ARM64), utilise Docker avec émulation x86_64 pour Valgrind
- Détection automatique de l'architecture dans le Makefile
- Fonctionne nativement sur Linux x86_64

---

**Projet réalisé dans le cadre d'une candidature stage chez Mistral AI**