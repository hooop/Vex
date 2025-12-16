<pre>
          ████
██  ██  ██      ██  ██
██  ██  ████      ██
  ██    ██      ██  ██
          ████
</pre>

# Vex - Valgrind Error eXplorer

**Vex** analyse automatiquement votre programme avec Valgrind, explique et propose une solution aux erreurs mémoire détectées.

<sub>
TO DO : <br>
Dec 25 : Gérer les appels aux fonctions de free externe au leak<br>
         Fusionner les étapes (affichage de debug) et l'analyse
         Améliorer ergonomie lancement : vex ./mon_prog
</sub>

## Vex ?

Durant mes études à l’école 42, résoudre les memory leaks fut une tâche ardue.
Valgrind détecte les fuites et indique où la mémoire a été allouée, mais il n'explique pas comment les corriger. Il faut remonter la pile d'appel, comprendre le contexte, identifier la vraie cause.

J’ai créé **Vex** pour faire ce travail d’analyse automatiquement :

- Quelle ligne cause réellement le problème
- Pourquoi cette ligne crée un leak
- Comment le corriger concrètement
    
## Fonctionnalités

- Analyse automatique : Lance Valgrind, parse le rapport, extrait le contexte du code
- Explications IA : Utilise Mistral AI pour fournir des diagnostics pédagogiques
- Interface soignée : Affichage terminal propre avec formatage ANSI
- Workflow interactif : Analyse un leak à la fois pour corriger progressivement
- Catégorisation intelligente : Identifie 3 types de leaks (mémoire jamais free, pointeur perdu, mémoire inaccessible)
- Focus "definitely lost" : Se concentre sur les fuites mémoire critiques (v1.0)

<img src="accueil_vex.png" alt="Aperçu Valgrind Error eXplorer" width="700">

## À qui s'adresse Vex ?

**Vex** est conçu pour tous ceux qui apprennent ou utilisent le C. L'objectif n'est pas de masquer les erreurs mais d'apprendre en comprenant.
Chaque analyse explique :

- Le concept mémoire sous-jacent
- L'erreur concrète dans votre code
- La solution recommandée

<img src="leak.png" alt="Aperçu Valgrind Error eXplorer" width="800">
