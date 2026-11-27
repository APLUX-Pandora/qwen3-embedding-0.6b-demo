# Qwen3-Embedding-0.6B SDK

Load Qwen3-Embedding-0.6B and encode text as unit vectors for semantic search.

## What's included

| Path | Content |
| --- | --- |
| `python/pandora_qwen3_embedding_0_6b/` | Python package (`from pandora_qwen3_embedding_0_6b import EmbeddingModel`) |
| `include/` | C header |
| `lib/` | Prebuilt native library with its QNN runtime |
| `SHA256SUMS` | Checksums of the shipped files |

## Install

In your application's activated Python 3.10–3.12 environment, from the Demo root:

```bash
python -m pip install sdk/wheels/pandora_runtime-*.whl
python -m pip install ./sdk
```

The device must pass `sudo lms check`. The SDK does not install LMS or drivers and does not download models; see [Get the model](../README.md#2-get-the-model).

To run the linked download commands, install the Hugging Face CLI in the same environment.

```bash
python -m pip install "huggingface_hub>=1.0,<2"
```

## Usage

```python
from pandora_qwen3_embedding_0_6b import EmbeddingModel

with EmbeddingModel.from_pretrained("models") as model:
    query = model.encode("How can I cancel inference?", prompt_name="query")
    documents = model.encode(["Click Stop to cancel inference.", "Model files are stored locally."])

scores = documents @ query
print(scores)
```

## Documentation

- [Python API](PYTHON_API.md)
- [C ABI](../docs/C_ABI.md)
- [Examples](../examples/README.md)
- [Licensing](../LICENSING.md)
