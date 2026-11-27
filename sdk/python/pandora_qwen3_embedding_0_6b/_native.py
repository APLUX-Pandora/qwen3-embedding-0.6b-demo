import ctypes as _ct
from functools import lru_cache
from pathlib import Path

from pandora_runtime import load_library

_TOKEN_PTR = _ct.POINTER(_ct.c_uint32)
_VECTOR_PTR = _ct.POINTER(_ct.c_float)


@lru_cache(maxsize=1)
def library():
    load_library()
    lib = _ct.CDLL(str(Path(__file__).parent / "_lib" / "libpandora_embedding.so"))
    lib.pandora_embedding_create.argtypes = [
        _ct.c_char_p, _ct.c_char_p, _ct.c_void_p, _ct.POINTER(_ct.c_void_p),
    ]
    lib.pandora_embedding_create.restype = _ct.c_int
    lib.pandora_embedding_encode.argtypes = [
        _ct.c_void_p, _TOKEN_PTR, _ct.c_size_t, _VECTOR_PTR, _ct.c_size_t,
    ]
    lib.pandora_embedding_encode.restype = _ct.c_int
    lib.pandora_embedding_destroy.argtypes = [_ct.POINTER(_ct.c_void_p)]
    lib.pandora_embedding_destroy.restype = _ct.c_int
    lib.pandora_embedding_last_error.argtypes = []
    lib.pandora_embedding_last_error.restype = _ct.c_char_p
    return lib


def check(lib, code):
    if code:
        message = lib.pandora_embedding_last_error().decode("utf-8", errors="replace")
        error = {-1: ValueError, -2: OSError, -3: PermissionError}.get(code, RuntimeError)
        raise error(message)
