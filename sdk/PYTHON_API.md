# Python API

`pandora_qwen3_embedding_0_6b` · Text embeddings for semantic search.

## Quick start

```python
from pandora_qwen3_embedding_0_6b import EmbeddingModel

with EmbeddingModel.from_pretrained("models") as model:
    query = model.encode("How can I cancel inference?", prompt_name="query")
    documents = model.encode(["Click Stop to cancel inference.", "Model files are stored locally."])

scores = documents @ query
print(scores)
```

## API overview

| Name | Signature | Returns | Purpose |
| --- | --- | --- | --- |
| `EmbeddingModel.from_pretrained` | `(model_dir, *, runtime=None)` | `EmbeddingModel` | Load a local model folder and select the device target |
| `capabilities` | Read-only property | Mapping | Describes text support, vector width and token budget |
| `encode` | `(texts, *, prompt_name=None, prompt=None)` | `numpy.ndarray` | Encode one string or a list of strings |
| `close` | `()` | `None` | Release the model; safe to call twice |

## Parameters

### `from_pretrained`

| Parameter | Type | Default | Range / unit | Meaning |
| --- | --- | --- | --- | --- |
| `model_dir` | `str` or path-like | Required | Local directory | Folder with the manifest, tokenizer, token embedding table and matching device target |
| `runtime` | `Runtime` or `None` | `None` | A Runtime in this process | By default the model creates and owns its Runtime |

### `encode`

| Parameter | Type | Default | Range / unit | Meaning |
| --- | --- | --- | --- | --- |
| `texts` | `str` or `list[str]` | Required | Nonempty list or one string | Each text has a maximum of 8192 tokens, including the prefix and special tokens. The model reports inputs that exceed the limit. |
| `prompt_name` | `str` or `None` | `None` | `"query"` or `"document"` | Select a named prefix. The document prefix is empty. |
| `prompt` | `str` or `None` | `None` | Complete prefix | Prepended verbatim. Supply a named or custom prefix at most once. |

With neither prompt option, the text is encoded as supplied. The query option prepends the model's [upstream instruction](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/main/config_sentence_transformers.json) verbatim. It ends with a newline followed by `Query:`. Include any desired spacing or separator in the custom prefix. For inputs already formatted with an instruction, pass the formatted string on its own.

## Results and cleanup

### `numpy.ndarray`

| Input | Shape | Dtype |
| --- | --- | --- |
| String | `(1024,)` | `numpy.float32` |
| List of N strings | `(N, 1024)` | `numpy.float32` |

Rows follow input order. The model processes each text independently, selects the last valid token and L2-normalizes its vector. A one-item list keeps the first dimension. Dot products between unit vectors give cosine similarity.

The read-only `capabilities` mapping has `text=True`, `embedding_dim=1024` and `max_input_tokens=8192`.

### Errors

| Exception | When |
| --- | --- |
| `TypeError` | An input or prompt has an unsupported type |
| `ValueError` | Empty list, unknown prompt name, conflicting prefix options, invalid tokenizer or manifest, or token budget exceeded |
| `OSError` | Missing or invalid model resource or device target |
| `PermissionError` | Model authorization failed |
| `RuntimeError` | Model is closed, another process owns it, or there was a backend failure |

### Lifecycle

Use `with` or call `close()` explicitly. The caller owns returned arrays and can keep them after closing the model. Calls on a single model are serialized. Load a new model in each process. If `close()` reports a cleanup error, call `close()` again to retry. Encoding stops when closing begins.

## Advanced

See the [retrieval example](../examples/README.md) for ranking passages. [Runtime](RUNTIME_API.md) describes optional hardware settings.
