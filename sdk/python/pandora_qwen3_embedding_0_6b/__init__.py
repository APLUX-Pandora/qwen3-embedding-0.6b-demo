"""Qwen3-Embedding-0.6B inference and shared hardware settings."""

from ._model import EmbeddingModel
from ._runtime import CpuOptions, QnnOptions, Runtime, RuntimeNativeError

__version__ = "1.0.0"
__all__ = ["CpuOptions", "EmbeddingModel", "QnnOptions", "Runtime", "RuntimeNativeError"]
