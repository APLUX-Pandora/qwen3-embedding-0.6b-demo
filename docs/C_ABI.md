# C ABI

`sdk/include/pandora_embedding.h` · `sdk/lib/libpandora_embedding.so` · Native inference for token IDs.

## Build and link

Install the Runtime wheel in the same environment first. Follow [SDK installation](../sdk/README.md#install).

From the Demo root, compile against the shipped header and library; the library carries its QNN runtime:

```bash
runtime_dir=$(python -c "import pathlib,pandora_runtime; print(pathlib.Path(pandora_runtime.__file__).parent)")
cc -std=c99 -I sdk/include your_app.c -L sdk/lib -L"$runtime_dir" -Wl,--no-as-needed -l:libpandora_runtime.so.5 -Wl,--as-needed -Wl,-rpath,"$runtime_dir" -lpandora_embedding -Wl,-rpath,'$ORIGIN/sdk/lib' -o your_app
```

## Lifecycle

```text
pandora_embedding_create → pandora_embedding_encode (repeat) → pandora_embedding_destroy
```

Initialize the output handle to NULL. If creation fails, read the error before another API call. Start a new load after correcting the issue.

If destroy fails during cleanup, the handle stays in the same slot. Read the error and retry destroy with that slot. The model cannot encode once cleanup starts.

## Functions

| Function | Purpose | Returns |
| --- | --- | --- |
| `pandora_embedding_create` | Load the protected QNN graph and token embedding table; NULL Runtime uses defaults | Error code |
| `pandora_embedding_encode` | Encode 1–8192 token IDs including special tokens into 1024 floats | Error code |
| `pandora_embedding_destroy` | Release a model and clear the handle on success; an empty handle is already closed | Error code |
| `pandora_embedding_last_error` | Read the error from this thread | Borrowed string |

## Error codes

| Code | Meaning | What the caller should do |
| --- | --- | --- |
| `PANDORA_EMBEDDING_OK` | Success | Use the result. |
| `PANDORA_EMBEDDING_ARGUMENT` | Invalid argument | Check the handles, token IDs and buffer sizes. |
| `PANDORA_EMBEDDING_RESOURCE` | Missing, malformed or incompatible model resource | Check the files for the selected device target. |
| `PANDORA_EMBEDDING_AUTHORIZATION` | LMS did not authorize loading | Check activation. |
| `PANDORA_EMBEDDING_BACKEND` | QNN or Runtime failure | Inspect the error and close the handle if it remains open. |
| `PANDORA_EMBEDDING_INTERNAL` | Unexpected native failure | Inspect the error and close the handle if it remains open. |

## Threads and ownership

The caller selects the device target and tokenizes with the model's tokenizer, including special tokens. The caller owns tokens and output storage. The SDK borrows them during the call and writes the output only on success. Each call returns one independently normalized vector.

Inference on one model is serialized. The caller must wait for all calls before destroying that handle. Load a new model after forking.

## Example

```c
#include <stdio.h>
#include "pandora_embedding.h"

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s CONTEXT_AIDEM TOKEN_EMBEDDING\n", argv[0]);
        return 1;
    }
    pandora_embedding_t *model = NULL;
    int status = pandora_embedding_create(argv[1], argv[2], NULL, &model);
    if (status) {
        fprintf(stderr, "%s\n", pandora_embedding_last_error());
        return 1;
    }
    const uint32_t tokens[] = {151643}; /* end-of-text token for the empty string */
    float vector[PANDORA_EMBEDDING_DIM];
    status = pandora_embedding_encode(model, tokens, 1, vector, PANDORA_EMBEDDING_DIM);
    if (status) fprintf(stderr, "%s\n", pandora_embedding_last_error());
    else printf("%f\n", vector[0]);
    const int cleanup = pandora_embedding_destroy(&model);
    if (cleanup) fprintf(stderr, "%s\n", pandora_embedding_last_error());
    return status != 0 || cleanup != 0;
}
```
