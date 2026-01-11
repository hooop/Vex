#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct s_data {
    char *content;
    int size;
} t_data;

typedef struct s_container {
    void *item;
    struct s_container *next;
} t_container;

void func_a(void) {
    t_data *info = malloc(sizeof(t_data));
    info->content = malloc(256);
    info->size = 256;

    strcpy(info->content, "This data will never be freed");

    if (info->size > 0) {
        info->content[0] = 'X';
    }
}

void func_b(void) {
    t_container *first = malloc(sizeof(t_container));
    t_container *second = malloc(sizeof(t_container));
    t_container *third = malloc(sizeof(t_container));

    first->item = malloc(64);
    second->item = malloc(128);
    third->item = malloc(256);

    first->next = second;
    second->next = third;
    third->next = NULL;

    t_container *backup = third;

    free(second->item);
    free(second);

    free(first->item);
    free(first);
}

int main(void) {
    func_a();
    func_b();

    return (0);
}
