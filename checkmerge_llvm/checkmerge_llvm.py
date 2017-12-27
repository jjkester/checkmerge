import ctypes.util
import platform
from ctypes import cdll


def get_library() -> str:
    """
    Finds, loads and returns a reference to the CheckMerge-LLVM library.

    The exact implementation of this function has been inspired by the `get_library()` function in the LLVM Python
    bindings.

    :return: The CheckMerge-LLVM library.
    """
    # Find system type
    system = platform.system()

    # Set system specifics
    if system == 'Darwin':
        pfx, ext = 'lib', '.dylib'
    elif system == 'Windows':
        pfx, ext = '', '.dll'
    else:
        pfx, ext = 'lib', '.so'

    names = [f'{pfx}CheckMerge-LLVM{ext}']

    for name in names:
        try:
            lib = cdll.LoadLibrary(name)
        except OSError:
            pass
        else:
            return lib._name

    for name in names:
        lib = ctypes.util.find_library(name)
        if lib:
            return lib

    raise EnvironmentError("The clang shared library does not appear to be present in this environment.")


def get_analysis_file(filename: str) -> str:
    """
    :param filename: The name of the file containing the source code.
    :return: The expected name of the file containing the analysis.
    """
    return filename.rsplit('.', 1)[0] + '.ll.cm'
