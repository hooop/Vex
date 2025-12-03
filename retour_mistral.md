# Analyse et correction du memory leak en C

## 1. Explication du problème

Le memory leak se produit parce que tu alloues de la mémoire dans la fonction `create_node()` (ligne 62) mais que tu ne la libères jamais. En C, quand tu utilises `malloc()`, tu dois toujours libérer la mémoire avec `free()` quand tu n'en as plus besoin, sinon elle reste allouée et inaccessible (d'où le terme "leak").

Dans ton cas, tu crées des nœuds pour une liste chaînée dans `create_list()`, mais tu ne les libères jamais avant la fin du programme.

## 2. Lignes problématiques

Les lignes problématiques sont dans `create_node()` (ligne 62) et dans `create_list()` (lignes 44-60) :

```c
// Dans create_node()
new_node = (node *)malloc(sizeof(node));  // Allocation mémoire
// ... mais pas de free() ...

// Dans create_list()
while (i < len)
{
    new_node = create_node(ft_atoi(splitted_str[i]));  // Allocation mémoire
    // ... mais pas de free() ...
}
```

## 3. Logique du problème

Voici ce qui se passe :
1. Tu alloues de la mémoire pour chaque nœud avec `malloc()`
2. Tu remplis les champs `value`, `next` et `prev`
3. Tu utilises ces nœuds pour construire ta liste
4. À la fin du programme, tu ne libères jamais cette mémoire

Le problème est que :
- La mémoire allouée reste "perdue" (d'où "definitely lost")
- Elle ne sera jamais récupérée par le système
- Pour 72 bytes, ce n'est pas grave, mais c'est une mauvaise habitude

## 4. Solution concrète

Tu dois libérer la mémoire allouée avant la fin du programme. Voici comment faire :

### Solution 1 : Libérer la liste dans push_swap()

Dans `push_swap.c`, après avoir utilisé tes listes, ajoute une fonction pour les libérer :

```c
// Ajoute cette fonction dans linked_list_creation.c
void free_list(node *head)
{
    node *current;
    node *next;

    current = head;
    while (current != NULL)
    {
        next = current->next;  // Sauvegarde le prochain nœud
        free(current);         // Libère le nœud courant
        current = next;        // Passe au suivant
    }
}

// Puis dans push_swap.c, après printf("Nombre d'opérations : %d\n");
free_list(list_a);
free_list(list_b);
```

### Solution 2 : Libérer splitted_str

Attention, tu as aussi un autre leak potentiel avec `splitted_str` (alloué dans `input_validation()` mais jamais libéré). Tu devrais aussi libérer ce tableau :

```c
// Après free_list(list_a) et free_list(list_b)
for (int i = 0; splitted_str[i] != NULL; i++)
    free(splitted_str[i]);
free(splitted_str);
```

### Version corrigée de push_swap()

Voici comment devrait être structuré ton `push_swap()` :

```c
int push_swap(int argc, char **argv)
{
    char **splitted_str;
    node *list_a = NULL;
    node *list_b = NULL;
    int count_move = 0;

    splitted_str = input_validation(argc, argv);
    if (!splitted_str)
        return (-1);

    list_a = array_to_list(splitted_str);
    if (!list_a)
    {
        free_array(splitted_str);  // Nouvelle fonction à créer
        return (-1);
    }

    count_move = run_algo(&list_a, &list_b, count_move);
    printf("Nombre d'opérations : %d\n", count_move);

    // Libération de la mémoire
    free_list(list_a);
    free_list(list_b);
    free_array(splitted_str);  // Nouvelle fonction

    return (0);
}
```

### Nouvelle fonction free_array()

Ajoute cette fonction pour libérer le tableau de chaînes :

```c
void free_array(char **array)
{
    if (!array)
        return;

    for (int i = 0; array[i] != NULL; i++)
        free(array[i]);
    free(array);
}
```

## Explication pédagogique

Le memory leak se produit parce que :
1. En C, la mémoire n'est pas gérée automatiquement comme en C++ ou Java
2. Chaque `malloc()` doit avoir un `free()` correspondant
3. Quand tu alloues de la mémoire dans une fonction, c'est à toi de t'assurer qu'elle sera libérée

Dans ton cas :
- Tu alloues des nœuds dans `create_node()`
- Ces nœuds sont utilisés dans `create_list()`
- Mais personne ne libère cette mémoire avant la fin du programme

La solution est de :
1. Créer une fonction `free_list()` qui parcourt la liste et libère chaque nœud
2. Appeler cette fonction avant la fin du programme
3. Faire de même pour le tableau de chaînes

C'est une bonne pratique de toujours libérer la mémoire que tu alloues, même si ton programme se termine juste après. Cela évite les mauvaises habitudes et prépare à des programmes plus complexes où la mémoire doit être gérée pendant toute la durée d'exécution.
