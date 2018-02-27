#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dll.h"
//Implement comparing based on reverse
int data_compare(data* d1, data* d2) {
    assert(d1);
    assert(d2);

    if(d1->age < d2->age) {
        return -1; //if not reversed and age1 < age2, return -1
    }
    if(d1->age > d2->age) {
        return 1; //if not reversed and age1 > age2, return 1
    }

    return strcmp(d1->name, d2->name); //if equal return 0
}

data* data_new(int age, char const* name) {
    data* d = (data*) malloc(sizeof(data));
    d->age = age;
    strncpy(d->name, name, NAME_LENGTH);
    return d;
}

void data_delete(data* d) {
    free(d);
}

dll* dll_new() {
    // Implement this
    dll* new_dll = malloc(sizeof(dll));

    if(new_dll) {
        new_dll->head = NULL;
        new_dll->tail = NULL;
    }

    return new_dll;
}

//Implement sorted insertion based on reverse
void dll_insert(dll* dll, data* data) {
    // Implement this
    node* new_node = malloc(sizeof(node));
    new_node->data = data;

    if(dll->head) {
        // There are already nodes, insert at end

        new_node->next = NULL;
        new_node->prev = dll->tail;
        dll->tail->next = new_node;
        dll->tail = new_node;

    } else {
        // There are no nodes yet. Insert as first
        new_node->prev = NULL;
        new_node->next = NULL;
        dll->tail = new_node;
        dll->head = new_node;
    }
}

void dll_erase(dll* dll, data* data) {
    // Implement this
    node* current = dll->head;

    while(current) {
        if(data_compare(data, current->data) == 0) {
            //Found the data! Now erase node from dll and free the memory

            // Set the head to the 2nd node in the dll
            if(current == dll->head) {
                dll->head = current->next;
            }

            // Set the tail to the 2nd to last node in the dll
            if(current == dll->tail) {
                dll->tail = current->prev;
            }

            // Set the previous of the next node to skip current
            if(current->next) {
                current->next->prev = current->prev;
            }

            // Set the next of the previous node to skip current
            if(current->prev) {
                current->prev->next = current->next;
            }

            node* next = current->next;

            // Current node is free from the dll chain, free the memory
            data_delete(current->data);
            free(current);
            current = next;
        } else {
            current = current->next;
        }
    }
}

void dll_print(dll* dll, FILE* printFile) {
    // Implement this
    node* current = dll->head;
    int i = 1;

    while(current) {
        fprintf(printFile, "{index: %d, age: %d, name: %s}\n", i, current->data->age, current->data->name);

        current = current->next;
        i++;
    }

}

void dll_reverse(dll* dll) {
    // Implement this
    node* current = dll->head;

    while(current) {
        node* old_next = current->next;

        current->next = current->prev;
        current->prev = old_next;

        current = old_next;
    }
    node* old_head = dll->head;
    dll->head = dll->tail;
    dll->tail = old_head;
}

void dll_delete(dll* dll) {
    // Implement this

    node* current = dll->head;

    while(current) {
        node* next = current->next;

        data_delete(current->data);
        free(current);

        current = next;
    }

    free(dll);
}
