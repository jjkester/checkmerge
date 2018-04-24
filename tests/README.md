## CheckMerge test files

This directory contains source code files for testing CheckMerge.

**Directory structure**

The directories `./a` and `./b` contain the different versions of the tests.
For each file in `./a`, a slightly different version of that file should be present in `./b`.

**Compiling tests**

The `./build-tests.sh` script is provided to run the analysis required to prepare the tests. The script requires you
to configure the `CM_LIB` variable, pointing to the compiled CheckMerge LLVM extension library.

In order to override the specific commands used for `clang` and `opt`, configure the `CLANG` and `OPT` environment
variables. This might be necessary when specific versions of Clang and LLVM are installed through a package manager.
