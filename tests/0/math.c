#include <stdio.h>

long fact(int n) {
    long r;

    for (int c = 1; c <= n; c++) {
        r = r * c;
    }

    return r;
}

int fib(int n) {
    int r;

    if (n == 0) {
        r = 0;
    } else if (n == 1) {
        r = 1;
    } else {
        r = fib(n-1) + fib(n-2);
    }

    return r;
}

int gcd(int n1, int n2) {
    int a = n1, b = n2;

    while (a != b) {
        if (a > b) {
            a -= b;
        } else {
            b -= a;
        }
    }

    return a;
}

void print_floyd_triangle(int n) {
    int i, j, c = 1;

    for (i = 1; i <= n; i++) {
        for (j = 1; j <= i; j++) {
            printf("%d ", c);
            c++;
        }
        printf("\n");
    }
}

void print_pascal_triangle(int n) {
    int i, j;

    for (i = 0; i < n; i++) {
        for (j = 0; j < (n - i - 2); j++) {
            printf(" ");
        }

        for (j = 0; j <= i; j++) {
            printf("%ld ", fact(i)/(fact(j)*fact(i-j)));
        }

        printf("\n");
    }
}
