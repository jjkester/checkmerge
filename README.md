# CheckMerge Analysis Framework

CheckMerge is a framework for static analysis of code merges. It was
created as gradutation project in order to test the feasability of such
a system.

## Using CheckMerge

CheckMerge has a command line interface that can be accessed by running
the following command from the project root directory:

```bash
python -m checkmerge.cli
```

The command line is self documented. Information on the different
commands can be found by running:

```bash
python -m checkmerge.cli help
```

## Running tests

Before the tests can be executed, they need to be built. The tests use
the [CheckMerge LLVM Analysis Pass](https://github.com/jjkester/checkmerge-llvm).
Please make sure this is compiled and configured before continuing.

Instructions on building the test suite are available in the `README.md`
file in the `tests` directory.

A test case can be executed with the following command:

```bash
python -m checkmerge.cli test ${TEST_DIR} ${TEST_CASE}
```

Replace `${TEST_DIR}` with the name of the test directory (`tests`) and
replace `${TEST_CASE}` with the name of the test case in the `tests`
directory. Examples of valid test cases are `calc_2.c` and `dll/dll.c`.
