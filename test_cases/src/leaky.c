#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct Node {
    char *data;
    struct Node *next;
} Node;

void init_buffer(void)
{
    char *buffer = malloc(100);
    strcpy(buffer, "data");
}

Node *create_node(const char *str) {
    Node *n = malloc(sizeof(Node));
    n->data = malloc(strlen(str) + 1);
    strcpy(n->data, str);
    n->next = NULL;
    return n;
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

    free(second->next->next->data);
    free(second->next->next);
    free(second->next);
    free(second);

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
    init_buffer();
    process_nodes();
    level_1();
    return (0);
}
