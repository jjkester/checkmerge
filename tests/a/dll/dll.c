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
    dll* d = (dll*)malloc(sizeof(dll));
    d->head = NULL;
    d->tail = NULL;
    return d;
}

void dll_insert(dll* dll, data* data) {
    assert(dll);
    assert(data);

    node* newnode = (node*)malloc(sizeof(node));
    newnode->data = data;
    newnode->prev = NULL;
    newnode->next = NULL;

    if (dll->head == NULL) {
        dll->head = newnode;
        dll->tail = newnode;
    } else {
        if (KEEP_ORDERED) {
            if (data_compare(data, dll->head->data) < 0) {
                // insert at head
                newnode->next = dll->head;
                dll->head->prev = newnode;
                dll->head = newnode;
            } else if (data_compare(data, dll->tail->data) > 0) {
                // insert at tail
                newnode->prev = dll->tail;
                dll->tail->next = newnode;
                dll->tail = newnode;
            } else {
                node *cur = dll->head;

                while (cur != NULL && cur->next != NULL) {
                    if (data_compare(data, cur->data) > 0 && data_compare(data, cur->next->data) <= 0) {
                        // insert between
                        newnode->prev = cur;
                        newnode->next = cur->next;
                        cur->next = newnode;
                        newnode->next->prev = newnode;
                        break;
                    }

                    cur = cur->next;
                }
            }
        } else {
            node *cur = dll->head;

            while (cur->next != NULL) {
                cur = cur->next;
            }

            cur->next = newnode;
            newnode->prev = cur;
            dll->tail = newnode;
        }
    }
}

void dll_erase(dll* dll, data* data) {
    assert(dll);
    assert(data);

    node* cur = dll->head;
    node* del = NULL;

    while (cur != NULL && del == NULL) {

        if (data_compare(cur->data, data) == 0) {
            del = cur;
        }

        cur = cur->next;
    }

    if (del != NULL) {
        if (del == dll->head) {
            dll->head = del->next;
        }
        if (del == dll->tail) {
            dll->tail = del->prev;
        }
        if (del->prev != NULL) {
            del->prev->next = del->next;
        }
        if (del->next != NULL) {
            del->next->prev = del->prev;
        }

        data_delete(del->data);

        free(del);
    }
}

void dll_print(dll* dll, FILE* printFile) {
    assert(dll);
    assert(printFile);

    node* cur = dll->head;

    while (cur != NULL) {
        data_print(cur->data, printFile);
        fprintf(printFile, "\n");
        cur = cur->next;
    }
}

void dll_reverse(dll* dll) {
    assert(dll);

    node* head = dll->head;
    node* tail = dll->tail;

    node* cur = head;

    while (cur != NULL) {
        node* prev = cur->prev;
        node* next = cur->next;

        cur->prev = next;
        cur->next = prev;

        cur = next;
    }

    dll->head = tail;
    dll->tail = head;
}

void dll_delete(dll* dll) {
    assert(dll);

    node* cur = dll->head;

    while (cur != NULL) {
        node* next = cur->next;

        data_delete(cur->data);
        free(cur);

        cur = next;
    }

    free(dll);
}
