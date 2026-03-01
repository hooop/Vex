#include <stdlib.h>
#include <string.h>

void type1_example() {
    int size = 100;
    char* buffer = malloc(size);
    strcpy(buffer, "data");

    char* temp = malloc(size + 50);
    strcpy(temp, buffer);
    strcat(temp, "extra");

    free(buffer);
    
}

int main() {
    type1_example();
    return 0;
}