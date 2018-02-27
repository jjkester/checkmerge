#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "dll.h"

#define INPUT_INCREMENT 10

void print_prompt(FILE* f) {
    fprintf(f, "\n> "); fflush(f);
}

data* read_data(char const* command) {
    int age;
    char name[NAME_LENGTH];
    sscanf(command, "%*s %i %s", &age, name);
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
    default: {
        fprintf(printFile, "No such command: ");
        fprintf(printFile, command);
        fprintf(printFile, "\n");
        break;
    }
    }
    return 0;
}

char* read_command(FILE* in) {
    int inputMaxLength = 0;
    char* input = NULL;
    char* inputAt = NULL;

    int incr = INPUT_INCREMENT;

    inputMaxLength = incr;
    input = (char*)malloc(sizeof(char) * incr);
    inputAt = input;
    do {
        inputAt[incr - 1] = 'e';
        if(fgets(inputAt, incr, in) == NULL) return NULL;
        if(inputAt[incr - 1] != '\0' || inputAt[incr - 2] == '\n') {
            break;
        }
        inputMaxLength += INPUT_INCREMENT;
        input = realloc(input, sizeof(char) * inputMaxLength);
        inputAt += incr - 1;
        incr = INPUT_INCREMENT + 1;
    } while(1);
    int len = strlen(input);
    input[len-1] = 0;
    return input;
}

int main(int argc, char* argv[]) {
    (void)argc;
    (void)argv;

    dll* dll = dll_new();

    while(1) {
        print_prompt(stdout);

        char* command = read_command(stdin);
        if(command == NULL) {
            break;
        }

        if(handle_command(stdout, dll, command)) break;
    }

    fprintf(stdout, "\nBye.\n");

}
