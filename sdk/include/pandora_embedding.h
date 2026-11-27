#ifndef PANDORA_EMBEDDING_H
#define PANDORA_EMBEDDING_H

#include <stddef.h>
#include <stdint.h>
#include "pandora_runtime.h"

#ifdef __cplusplus
extern "C" {
#endif

#define PANDORA_EMBEDDING_API __attribute__((visibility("default")))
#define PANDORA_EMBEDDING_VERSION "1.0.0"
#define PANDORA_EMBEDDING_DIM 1024
#define PANDORA_EMBEDDING_MAX_INPUT_TOKENS 8192

typedef struct pandora_embedding pandora_embedding_t;

enum pandora_embedding_error {
    PANDORA_EMBEDDING_OK = 0,
    PANDORA_EMBEDDING_ARGUMENT = -1,
    PANDORA_EMBEDDING_RESOURCE = -2,
    PANDORA_EMBEDDING_AUTHORIZATION = -3,
    PANDORA_EMBEDDING_BACKEND = -4,
    PANDORA_EMBEDDING_INTERNAL = -5
};

/* Pass an empty output slot. The model takes a snapshot of runtime (NULL selects defaults). */
PANDORA_EMBEDDING_API int pandora_embedding_create(
    const char *context_path, const char *token_embedding_path,
    const pandora_runtime_t *runtime, pandora_embedding_t **out);

/* The caller tokenizes, including special tokens, and owns all input and output buffers.
 * On success exactly PANDORA_EMBEDDING_DIM floats are written. On error vector is untouched. */
PANDORA_EMBEDDING_API int pandora_embedding_encode(
    pandora_embedding_t *model, const uint32_t *tokens, size_t token_count,
    float *vector, size_t vector_count);

/* Wait for all calls on this handle before destroy. A NULL slot value is already closed.
 * On cleanup failure the slot retains the handle. Retry destroy with the same slot.
 * The handle cannot encode after cleanup starts. If terminal power cleanup is
 * reported, the remaining vendor resources are quarantined until process exit
 * and a subsequent destroy releases the model handle. */
PANDORA_EMBEDDING_API int pandora_embedding_destroy(pandora_embedding_t **model);

/* Borrowed thread-local message, valid until the next model API call on this thread. */
PANDORA_EMBEDDING_API const char *pandora_embedding_last_error(void);

#ifdef __cplusplus
}
#endif

#endif
