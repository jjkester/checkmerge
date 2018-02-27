#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dll.h"

int data_compare(data* d1, data* d2) {
    assert(d1);
    assert(d2);
    if(d1->age < d2->age) return -1;
    if(d1->age > d2->age) return 1;
    return strcmp(d1->name, d2->name);
}

void data_print(data* d, FILE* f) {
    fprintf(f, "%i %s", d->age, d->name);
}

data* data_new(int age, char const* name) {
    data* d = (data*)malloc(sizeof(data));
    d->age = age;
    strncpy(d->name, name, NAME_LENGTH);
    return d;
}

void data_delete(data* d) {
    free(d);
}

dll* dll_new() {
    // Implement this
}

void dll_insert(dll* dll, data* data) {
    // Implement this
}

void dll_erase(dll* dll, data* data) {
    // Implement this
}

void dll_print(dll* dll, FILE* printFile) {
    // Implement this
}

void dll_reverse(dll* dll) {
    // Implement this
}

void dll_delete(dll* dll) {
    // Implement this
}
