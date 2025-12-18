#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct Node {
    char *data;
    struct Node *next;
} Node;



void leak_first_leak() {
    char *str = malloc(100);
    strcpy(str, "coucou");
}

Node *create_node(const char *str) {
    Node *n = malloc(sizeof(Node));
    n->data = malloc(strlen(str) + 1);
    strcpy(n->data, str);
    n->next = NULL;
    return n;
}



void leak_type2_pointer_lost() {
    char *ptr = malloc(50);
    strcpy(ptr, "First allocation");
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
        free(local);     }
   
}

char *salut(str)
{
    str = malloc(100);
    return str;
}

char *hello(str)
{
    char *str3 = salut(str);
    return str3;
}

char* coucou()
{
    char *str = malloc(50);
    char *str2 = hello(str);
    return str2;
}

void process_nodes() {

    Node *head = create_node("first");
    head->next = create_node("second");
    head->next->next = create_node("third");
    head->next->next->next = create_node("fourth");
    
    Node *third = head->next->next;

    Node *second = head->next;
    head->next = NULL;
    free(second->data);
    free(second->next->data);
    free(second->next->next->data);
    free(second->next->next);
    free(second->next);
    free(second);

    head->next = NULL;
    
    free(head->data);
    free(head);
}



typedef struct s_node
{
    char *data;
    struct s_node *next;
}   t_node;

char *level_5_alloc(void)
{
    char *data;
    
    data = malloc(100);
    return (data);
}

char *level_4(void)
{
    char *ptr;
    
    ptr = level_5_alloc();
    return (ptr);
}

t_node *level_3(void)
{
    t_node *node;
    
    node = malloc(sizeof(t_node));
    node->data = level_4(); 
    node->next = NULL;
    return (node);
}

t_node *level_2(void)
{
    t_node *buffer;
    t_node *temp;
    
    buffer = level_3();
    temp = buffer;
    return (temp);
}

void level_1(void)
{
    t_node *node;
    
    node = level_2();
   
    free(node); 
}

int main(void)
{
    level_1();
    leak_first_leak();
    return (0);
}