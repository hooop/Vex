#include <stdlib.h>

char *ft_b(char *x)
{
    char *r;
    
    r = malloc(30);
    r[0] = x[0];
    r[1] = '\0';
    x = r;
    return (x);
}

char *ft_a(int n)
{
    char *p;
    char *q;
    char *t;

    p = malloc(n);
    p[0] = 'x';
    p[1] = '\0';
    q = malloc(n * 2);
    q[0] = 'y';
    q[1] = '\0';
    t = ft_b(p);
    p = q;
    return (t);
}

int main(void)
{
    char *s;

    s = ft_a(50);
    free(s);
    return (0);
}