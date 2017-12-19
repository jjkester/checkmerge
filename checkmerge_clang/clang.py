import ctypes.util
import platform
from ctypes import cdll


def get_library():
    """
    Finds, loads and returns a reference to the clang library.

    The exact implementation of this function has been inspired by the `get_library()` function in the LLVM Python
    bindings.

    :return: The clang library.
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

    names = [f'{pfx}clang{ext}']

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


def configure():
    """
    Configures the clang Python bindings with the library.
    """
    # Test availability of Python bindings
    try:
        import clang.cindex
    except ImportError:
        raise EnvironmentError("The clang Python bindings do not appear to be present in this environment.")

    clang.cindex.Config.set_library_file(get_library())
