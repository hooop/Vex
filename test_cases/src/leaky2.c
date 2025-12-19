#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct Node {
    char *data;
    int value;
    struct Node *next;
} Node;

typedef struct Container {
    Node *head;
    char *label;
    int count;
} Container;

char *ft_strdup(const char *s) {
    size_t len = strlen(s);
    char *dup = malloc(len + 1);
    if (!dup)
        return NULL;
    strcpy(dup, s);
    return dup;
}

char *ft_strjoin(const char *s1, const char *s2) {
    if (!s1 || !s2)
        return NULL;
    
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char *result = malloc(len1 + len2 + 1);
    
    if (!result)
        return NULL;
    
    strcpy(result, s1);
    strcat(result, s2);
    return result;
}

Node *allocate_node(int value) {
    Node *node = malloc(sizeof(Node));
    if (!node)
        return NULL;
    
    node->data = NULL;
    node->value = value;
    node->next = NULL;
    return node;
}

Node *create_node_with_data(const char *prefix, int value) {
    Node *node = allocate_node(value);
    if (!node)
        return NULL;
    
    char num_str[20];
    sprintf(num_str, "%d", value);
    node->data = ft_strjoin(prefix, num_str);
    
    return node;
}

Container *init_container(const char *label) {
    Container *c = malloc(sizeof(Container));
    if (!c)
        return NULL;
    
    c->head = NULL;
    c->label = ft_strdup(label);
    c->count = 0;
    return c;
}

void add_node_to_container(Container *container, Node *node) {
    if (!container || !node)
        return;
    
    if (!container->head) {
        container->head = node;
    } else {
        Node *current = container->head;
        while (current->next)
            current = current->next;
        current->next = node;
    }
    container->count++;
}

void scenario_type1_deep_backtrace() {
    Container *c = init_container("numbers");
    
    Node *n1 = create_node_with_data("item_", 1);
    Node *n2 = create_node_with_data("item_", 2);
    Node *n3 = create_node_with_data("item_", 3);
    
    add_node_to_container(c, n1);
    add_node_to_container(c, n2);
    add_node_to_container(c, n3);
    
    printf("Container '%s' has %d nodes\n", c->label, c->count);
    
    free(c->label);
    free(c);
}

void scenario_type2_pointer_overwrite() {
    Container *c = init_container("data");
    
    Node *original = create_node_with_data("original_", 42);
    add_node_to_container(c, original);
    
    printf("Container has %d nodes\n", c->count);
    
    c->head = create_node_with_data("replacement_", 99);
    
    free(c->head->data);
    free(c->head);
    free(c->label);
    free(c);
}

void scenario_type3_broken_chain() {
    Container *c = init_container("chain");
    
    Node *n1 = create_node_with_data("first_", 1);
    Node *n2 = create_node_with_data("second_", 2);
    Node *n3 = create_node_with_data("third_", 3);
    Node *n4 = create_node_with_data("fourth_", 4);
    
    add_node_to_container(c, n1);
    add_node_to_container(c, n2);
    add_node_to_container(c, n3);
    add_node_to_container(c, n4);
    
    printf("Container '%s' has %d nodes\n", c->label, c->count);
    
    Node *second = c->head->next;
    second->next = NULL;
    
    Node *current = c->head;
    while (current) {
        Node *next = current->next;
        free(current->data);
        free(current);
        current = next;
    }
    
    free(c->label);
    free(c);
}

void scenario_type2_strdup_lost() {
    char *base = ft_strdup("base_string");
    char *extended = ft_strjoin(base, "_extension");
    
    printf("Extended: %s\n", extended);
    
    base = ft_strdup("new_base");
    
    free(base);
    free(extended);
}

int main() {
    printf("=== Complex Memory Leak Scenarios ===\n\n");
    

    scenario_type1_deep_backtrace();
    
  
    scenario_type2_pointer_overwrite();
    

    scenario_type3_broken_chain();
    

    scenario_type2_strdup_lost();
    
    printf("\n=== All scenarios completed ===\n");
    
    return 0;
}