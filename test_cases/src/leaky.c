#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct s_node
{
    char            *data;
    struct s_node   *next;
} t_node;

typedef struct s_block
{
    void            *payload;
    struct s_block  *ref;
} t_block;

t_node *create_node(const char *str)
{
    t_node *n = malloc(sizeof(t_node));
    n->data = malloc(strlen(str) + 1);
    
    strcpy(n->data, str);
    n->next = NULL;

    return (n);
}

void process_nodes()
{

    t_node *head = create_node("first");
    head->next = create_node("second");
    head->next->next = create_node("third");
    head->next->next->next = create_node("fourth");

    t_node *third = head->next->next;
    t_node *second = head->next;

    head->next = NULL;

    free(second->next->next->data);
    free(second->next->next);
    free(second->next);
    free(second->data);
    free(second);
    free(head->data);
    free(head);
}

void init_buffer(void)
{
    char    *buffer = malloc(100);
    
    strcpy(buffer, "data");
}

char *level_5_alloc(void)
{
    char *data = malloc(100);

    return (data);
}

char *level_4(void)
{
    char *ptr = level_5_alloc();

    return (ptr);
}

t_node *level_3(void)
{
    t_node *node = malloc(sizeof(t_node));

    node->data = level_4();
    node->next = NULL;

    return (node);
}

t_node *level_2(void)
{
    t_node *buffer = level_3();
    t_node *temp = buffer;

    return (temp);
}

void level_1(void)
{
    t_node *node = level_2();

    free(node);
}

t_block *alloc_block(size_t size)
{
    t_block *b = malloc(sizeof(t_block));
    b->payload = malloc(size);

    b->ref = NULL;

    return (b);
}

void consume(t_block *x)
{
    free(x->payload);
    free(x);
}

void example(void)
{
    t_block *a = alloc_block(32);
    t_block *b = alloc_block(64);
    t_block *c = alloc_block(128);

    a->ref = b;
    b->ref = c;

    t_block *saved = c;

    consume(b);

    free(a->payload);
    free(a);
}


int main(void)
{
    example();

    process_nodes();

    return (0);
}
