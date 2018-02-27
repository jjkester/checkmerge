#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dll.h"

#define INPUT_INCREMENT 10

void print_prompt(FILE* f) {
    fprintf(f, "\n> "); fflush(f);
}

data* read_data(char const* command) {
    int age = 0;
    char name[NAME_LENGTH] = "";
    sscanf(command, "%*s %i %19s", &age, name);
    return data_new(age, name);
}

int handle_command(FILE* printFile, dll* dll, char* command) {
    switch(*command) {
    case 'i': {
        dll_insert(dll, read_data(command));
        break;
    } case 'e': {
        dll_erase(dll, read_data(command));
        break;
    } case 'r':
        dll_reverse(dll);
        break;
    case 'p':
        dll_print(dll, printFile);
        break;
    case 'x':
        return 1;
        break;
    case 't':
        test(printFile);
        break;
    default: {
        fprintf(printFile, "No such command: %s\n", command);
        break;
    }
    }
    return 0;
}

char* read_command(FILE* in) {
    char* input = NULL;
    char* temp = NULL;
    size_t index = 0, size = 0;
    unsigned int incr = INPUT_INCREMENT;

    input = (char*)calloc(incr, sizeof(char));
    size = incr;

    do {
        if(fgets(&input[index], incr, in) == NULL) {
            free(input);
            return NULL;
        }

        if(input[strlen(input) - 1] == '\n') {
            break;
        }

        size += incr;
        temp = (char*)realloc(input, sizeof(char) * size);

        if (temp == NULL) {
            free(input);
            fprintf(stderr, "Memory error.");
        }

        input = temp;
        index += incr - 1;
        incr = INPUT_INCREMENT + 1;
    } while(input != NULL);


    if (input != NULL) {
        size = strlen(input);
        temp = (char*)realloc(input, sizeof(char) * size + 1);

        if (temp == NULL) {
            free(input);
            fprintf(stderr, "Memory error.");
        }

        input = temp;
    }

    return input;
}

int main(int argc, char* argv[]) {
    (void)argc;
    (void)argv;
    char* command;

    dll* dll = dll_new();

    while(1) {
        print_prompt(stdout);

        command = read_command(stdin);
        if(command == NULL) {
            break;
        }

        if(handle_command(stdout, dll, command)) break;

        free(command);
    }

    free(command);

    dll_delete(dll);

    fprintf(stdout, "\nBye.\n");

}
