typedef int T;

int main() {
    T a = 1;
    T b = 2;
    T c = a + b;
    a = b;
    b = c;
    c = a;
}
