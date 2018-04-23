#include <stdio.h>

long factorial(int n) {
    long r;

    for (int c = 1; c <= n; c++) {
        r = r * c;
    }

    return r;
}

int fib_rec(int n) {
    int r = n;

    if (n >= 2) {
        r = fib_rec(n-1) + fib_rec(n-2);
    }

    return r;
}

int fib_dyn(int n) {
    int f[n+1];
    int i;

    f[0] = 0;
    f[1] = 1;

    for (i = 2; i <= n; i++) {
        f[i] = f[i-1] + f[i-2];
    }

    return f[n];
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
        for (j = 0; j <= i; j++) {
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
            printf("%ld ", factorial(i)/(factorial(j)*factorial(i-j)));
        }

        printf("\n");
    }
}
