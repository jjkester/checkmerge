#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEST_DIR="${DIR}"
TEST_FILES="${TEST_DIR}/*/*.c"
error=0

echo "Building test files in ${TEST_DIR} ..."

for f in $TEST_FILES
do
    in=$f
    out="${in%.*}.ll"

    echo "  Building $(basename "${in}")..."

    echo "    Compiling $(basename "${in}")..."

    clang -S -O0 -g -emit-llvm "$in" -o "$out" > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        error=$((error + 1))
        echo "    [!] Error while compiling $(basename "${in}")!"
    else
        echo "      Generated $(basename "${out}")."

        echo "    Analyzing $(basename "${out}")..."

        opt -analyze -load="${CM_LIB}" -checkmerge "${out}" > /dev/null 2>&1

        if [ $? -ne 0 ]; then
            error=$((error + 1))
            echo "    [!] Error while analyzing $(basename "${in}")!"
        else
            echo "      Generated $(basename "${out}.cm")."
        fi
    fi
done

if [ $error -ne 0 ]; then
    echo "[!] Failed with ${error} errors."
else
    echo "Done."
fi
