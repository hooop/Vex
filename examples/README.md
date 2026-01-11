# Test Cases Documentation

Ce dossier contient les cas de test utilisés pour valider Vex durant le développement et la démonstration.

## Fichier : leaky.c

Programme C contenant volontairement plusieurs memory leaks de complexité variable pour tester les capacités d'analyse de Vex.

### Test 1 : init_buffer()

**Type de leak** : Type 1 (malloc sans free)

**Complexité** : Triviale

**Description** :
Allocation simple de 100 bytes qui n'est jamais libérée. Variable locale détruite en fin de fonction sans libération préalable.

**Ce que ça teste** :
- Détection basique d'une allocation orpheline
- Compréhension de la portée des variables locales
- Identification du point d'insertion du free manquant

**Résolution attendue** :
```c
void init_buffer(void)
{
    char *buffer = malloc(100);
    strcpy(buffer, "data");
    free(buffer);  // À ajouter
}
```

---

### Test 2 : process_nodes()

**Type de leak** : Type 3 (conteneur libéré avant contenu)

**Complexité** : Élevée

**Description** :
Création d'une liste chaînée de 4 nœuds avec allocation séparée pour chaque `node->data`. Utilisation d'alias (`Node *third`, `Node *second`) et libération partielle : le `data` du nœud "third" n'est jamais libéré.

**Ce que ça teste** :
- Compréhension des listes chaînées
- Gestion des alias de pointeurs
- Identification précise de quel `data` parmi plusieurs n'est pas libéré
- Traduction correcte des chemins de déréférencement (`second->next->data`)

**Résolution attendue** :
```c
free(third->data);       // OU : free(second->next->data);
free(second->next->next);
```

---

### Test 3 : level_1() → level_5_alloc()

**Type de leak** : Type 3 (conteneur libéré avant contenu)

**Complexité** : Très élevée

**Description** :
Call stack profonde sur 5 niveaux où un malloc est effectué dans `level_5_alloc()`, retourné à travers 4 fonctions intermédiaires, puis stocké dans le champ `data` d'une structure `t_node`. La structure est libérée dans `level_1()` mais pas son contenu.

**Ce que ça teste** :
- Remontée complète d'une call stack profonde
- Suivi d'un pointeur à travers plusieurs returns successifs
- Identification d'une mémoire EMBEDDED dans une structure
- Détection d'un free incomplet (conteneur libéré, contenu oublié)

**Résolution attendue** :
```c
void level_1(void)
{
    t_node *node;
    
    node = level_2();
    free(node->data);  // ← À ajouter
    free(node);
}
```

---

## Notes techniques

- Aucun commentaire explicatif dans le code pour ne pas guider l'IA
- Noms de fonctions volontairement neutres