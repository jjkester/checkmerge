#!/bin/bash

shopt -s globstar

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEST_DIR="${DIR}"
TEST_FILES="${TEST_DIR}/*/**/*.c"
error=0

if [ -z ${CLANG} ]; then CLANG="clang"; fi
if [ -z ${OPT} ]; then OPT="opt"; fi

if [ -z ${CM_LIB+x} ]; then echo "CM_LIB environment variable not set!"; exit 1; fi

echo "Building test files in ${TEST_DIR}..."

for f in $TEST_FILES
do
    in=$f
    out="${in%.*}.ll"

    printf "  Building %s:\n" ${in#${TEST_DIR}/}

    printf "    Compiling %s... " $(basename ${in})

    ${CLANG} -S -O0 -g -emit-llvm "$in" -o "$out" > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        error=$((error + 1))
        printf "[!] Error!\n"
    else
        printf "Done.\n"
        printf "      Generated %s.\n" ${out#${TEST_DIR}/}

        printf "    Analyzing %s... " $(basename ${out})

        ${OPT} -analyze -load=${CM_LIB} -checkmerge ${out} > /dev/null 2>&1

        if [ $? -ne 0 ]; then
            error=$((error + 1))
            printf "[!] Error!\n"
        else
            printf "Done.\n"
            printf "      Generated %s.\n" "${out#${TEST_DIR}/}.cm"
        fi

        printf "    Cleaning up %s... " $(basename ${out})
        rm ${out}
        printf "Done.\n"

    fi
done

if [ $error -ne 0 ]; then
    echo "[!] Failed with ${error} errors."
else
    echo "Completed."
fi
