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
    data* result = NULL;
    int args_matched = sscanf(command, "%*1s %i %19s", &age, name);

    if(args_matched == 2) {
        result = data_new(age, name);
    }

    return result;
}

int handle_command(FILE* printFile, dll* dll, char* command) {
    data* input_data;

    switch(*command) {
    case 'i': {
        input_data = read_data(command);
        if(input_data) {
            dll_insert(dll, input_data);
        }

        break;
    } case 'e': {
        input_data = read_data(command);
        if(input_data) {
            dll_erase(dll, input_data);
        }

        data_delete(input_data);

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
        fprintf(printFile, "No such command: ");
        fprintf(printFile, "%s", command);
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
        inputAt = input + inputMaxLength - incr - 1;
        incr = INPUT_INCREMENT + 1;
    } while(1);

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
