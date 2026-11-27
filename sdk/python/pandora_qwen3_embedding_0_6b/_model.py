import ctypes
import os
from threading import Lock
from types import MappingProxyType
from warnings import warn

import numpy as np
from tokenizers import Tokenizer

from . import _native
from ._resources import resolve_resources
from ._runtime import Runtime

_PROMPTS = {
    "query": (
        "Instruct: Given a web search query, retrieve relevant passages that answer the query"
        "\nQuery:"
    ),
    "document": "",
}
_CAPABILITIES = MappingProxyType({"text": True, "embedding_dim": 1024, "max_input_tokens": 8192})


# Keep native ownership reachable if finalization cannot complete cleanup.
_retained_models = []


class EmbeddingModel:
    """Encode text as unit vectors with Qwen3-Embedding-0.6B."""

    def __init__(self):
        raise TypeError("Load the model with EmbeddingModel.from_pretrained(model_dir)")

    @classmethod
    def from_pretrained(cls, model_dir, *, runtime=None):
        """Load a local model directory and initialize the NPU."""
        if runtime is not None and not isinstance(runtime, Runtime):
            raise TypeError("runtime must be a Runtime or None")
        model = cls.__new__(cls)
        model._handle = ctypes.c_void_p()
        model._tokenizer = None
        model._runtime = None
        model._owns_runtime = runtime is None
        model._lock = Lock()
        model._pid = os.getpid()
        try:
            model._runtime = Runtime() if runtime is None else runtime
            graph, tokenizer, embedding = resolve_resources(
                model_dir, model._runtime.status()["soc_id"],
            )
            try:
                model._tokenizer = Tokenizer.from_file(str(tokenizer))
            except Exception as exc:
                raise ValueError(f"Could not load tokenizer: {exc}") from exc
            model._tokenizer.no_truncation()
            model._tokenizer.no_padding()
            model._lib = _native.library()
            with model._runtime.borrow_handle() as native_runtime:
                _native.check(model._lib, model._lib.pandora_embedding_create(
                    os.fsencode(graph), os.fsencode(embedding), native_runtime,
                    ctypes.byref(model._handle),
                ))
        except BaseException:
            model.close()
            raise
        return model

    @property
    def capabilities(self):
        """Read-only description of inputs, vector width and token budget."""
        return _CAPABILITIES

    def encode(self, texts, *, prompt_name=None, prompt=None):
        """Return independently owned float32 unit vectors in input order."""
        self._check_process()
        with self._lock:
            if self._tokenizer is None:
                raise RuntimeError("EmbeddingModel is closed")
            single = isinstance(texts, str)
            if single:
                texts = [texts]
            if not isinstance(texts, list) or not all(isinstance(text, str) for text in texts):
                raise TypeError("texts must be a string or a list of strings")
            if not texts:
                raise ValueError("texts must not be an empty list")
            prefix = _prefix(prompt_name, prompt)
            limit = self.capabilities["max_input_tokens"]
            width = self.capabilities["embedding_dim"]
            result = np.empty(width if single else (len(texts), width), dtype=np.float32)
            for index, (text, output) in enumerate(zip(texts, result.reshape(-1, width))):
                ids = self._token_ids(text, prefix)
                if not 0 < len(ids) <= limit:
                    raise ValueError(f"texts[{index}] uses {len(ids)} tokens; expected 1 to {limit}")
                tokens = (ctypes.c_uint32 * len(ids))(*ids)
                _native.check(self._lib, self._lib.pandora_embedding_encode(
                    self._handle, tokens, len(ids), output.ctypes.data_as(_native._VECTOR_PTR), width,
                ))
            return result

    def _count_input_tokens(self, texts, *, prompt_name=None):
        """Count tokens for the demo's metrics after a successful encode."""
        self._check_process()
        with self._lock:
            if self._tokenizer is None:
                raise RuntimeError("EmbeddingModel is closed")
            prefix = _prefix(prompt_name, None)
            inputs = [texts] if isinstance(texts, str) else texts
            return sum(len(self._token_ids(text, prefix)) for text in inputs)

    def _token_ids(self, text, prefix):
        return self._tokenizer.encode(prefix + text, add_special_tokens=True).ids

    def close(self):
        """Release the model and any Runtime it created."""
        if os.getpid() != self._pid:
            return
        with self._lock:
            self._tokenizer = None
            if self._handle.value:
                _native.check(self._lib, self._lib.pandora_embedding_destroy(
                    ctypes.byref(self._handle),
                ))
            if self._owns_runtime and self._runtime is not None:
                self._runtime.close()
            self._runtime = None

    def _check_process(self):
        if os.getpid() != self._pid:
            raise RuntimeError("Load EmbeddingModel again after fork")

    def __enter__(self):
        self._check_process()
        return self

    def __exit__(self, *_):
        self.close()

    def __del__(self):
        if not hasattr(self, "_pid"):
            return
        try:
            try:
                self.close()
            except RuntimeError:
                self.close()
        except (AttributeError, OSError, RuntimeError, ValueError) as exc:
            if getattr(self, "_handle", None) and self._handle.value:
                _retained_models.append(self)
            warn(f"EmbeddingModel cleanup failed: {exc}", ResourceWarning, stacklevel=2)


def _prefix(name, prompt):
    if name is not None and not isinstance(name, str):
        raise TypeError("prompt_name must be a string or None")
    if prompt is not None and not isinstance(prompt, str):
        raise TypeError("prompt must be a string or None")
    if name is not None:
        if prompt is not None:
            raise ValueError("prompt_name and prompt are mutually exclusive")
        if name not in _PROMPTS:
            raise ValueError(f"Unknown prompt name: {name!r}")
        return _PROMPTS[name]
    return "" if prompt is None else prompt
