int run(int n) {
    int r = 0;
    if (n >= 1) {
        for (int i = 1; i < 10; i++) {
            r += i;
        }
    }
    return r;
}

int test(int actual, int expected) {
    int diff = actual - expected;
    if (diff < 0) {
        return 0 - diff;
    }
    return 0;
}

int main() {
    return test(run(5), 10) + test(run(10), 20);
}