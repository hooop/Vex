#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct Node {
    char *data;
    struct Node *next;
} Node;



void leak_type1_simple() {
    char *str = malloc(100);
    strcpy(str, "This memory is never freed");

}

Node *create_node_leaked(const char *str) {
    Node *n = malloc(sizeof(Node));
    n->data = malloc(strlen(str) + 1);
    strcpy(n->data, str);
    n->next = NULL;
    return n;
}



void leak_type2_pointer_lost() {
    char *ptr = malloc(50);
    strcpy(ptr, "First allocation");
/*     printf("coucou"); */
    free(ptr);
    ptr = malloc(100);
    strcpy(ptr, "Second allocation - first is lost!");
    free(ptr);
}

void leak_type2_realloc_shadow() {
    char *buffer = malloc(10);
    strcpy(buffer, "small");
    
    char *shadow = buffer;
    
    buffer = realloc(buffer, 100); 
    
    strcpy(buffer, "This is now a much longer string in the reallocated buffer");
    
    free(buffer);
}


void leak_type3_all_pointers_lost() {
    char *ptr1 = malloc(64);
    char *ptr2 = ptr1;
    char *ptr3 = ptr1;
    
    strcpy(ptr1, "Shared memory");
free(ptr1);
    ptr1 = NULL;
    ptr2 = NULL;
    ptr3 = NULL;

}

void leak_type3_scope_exit() {
    {
        char *local = malloc(128);
        strcpy(local, "Memory allocated in inner scope");
       
    }
   
}


void leak_type3_broken_linked_list() {

    Node *head = create_node_leaked("first");
    head->next = create_node_leaked("second");
    head->next->next = create_node_leaked("third");
    head->next->next->next = create_node_leaked("fourth");
    
    Node *third = head->next->next;

    
    head->next = NULL;
    
    free(head->data);
    free(head);
}

/* ============================================
   MAIN: Appelle tous les types de leaks
   ============================================ */

int main() {
    printf("=== Testing different types of memory leaks ===\n\n");
    

    leak_type1_simple();
    

    leak_type2_pointer_lost();
    leak_type2_realloc_shadow();
    

    leak_type3_all_pointers_lost();
    leak_type3_scope_exit();
    leak_type3_broken_linked_list();
    

    
    return 0;
}