#include <stdio.h>

int calc(int a, int b) {
    int c = a + b;
    printf("c=%d\n", c);
    return c + a;
}
