# Examples

## Overview

| Example | What it shows |
| --- | --- |
| [python/short_passage_search.py](python/short_passage_search.py) | Rank ten labeled MIRACL passages for a query in one of six languages. |
| [python/long_document_search.py](python/long_document_search.py) | Rank three MLDR document excerpts and show the encoded input length and time. |

## Before you run

Complete [Install](../README.md#1-install) and [Get the model](../README.md#2-get-the-model). Run every command from the Demo root in the activated environment. Stop the Web Demo first; examples and the Web Demo share the NPU.

## Python examples

Both examples use the SDK to encode a query with the Qwen instruction prefix and documents as plain text. They rank the results by cosine similarity, calculated as a dot product of unit vectors.

### short_passage_search.py

Each language has one query and ten judged passages. The output shows the passage ID, score, original text and a marker for each labeled positive.

```bash
python examples/python/short_passage_search.py
python examples/python/short_passage_search.py --lang zh
```

| Option | Default | Purpose |
| --- | --- | --- |
| `--lang` | `en` | Choose `zh`, `en`, `ja`, `ko`, `fr` or `es`. |
| `--model-dir` | `models` | Local model folder. |

Output (first result, excerpted):

```text
Query (en): When did Philip Melanchthon die?
 1. 39209#0  score=0.6796 [labeled positive]
Philip Melanchthon (born Philipp Schwartzerdt; 16 February 1497 – 19 April 1560) was a German Lutheran reformer, collaborator with Martin Luther, the first…
```

### long_document_search.py

The example ranks three document excerpts. Input counts include any special tokens and use the model tokenizer with padding and truncation disabled. The SDK accepts up to 8192 input tokens per text. Each reported time covers one SDK document encoding call.

```bash
python examples/python/long_document_search.py
```

| Option | Default | Purpose |
| --- | --- | --- |
| `--model-dir` | `models` | Local model folder. |

Output (excerpt):

```text
Query: How many general-purpose data registers does the CPU have in the 68000 family?
Input limit: 8192 tokens per text
1. doc-en-3800  Motorola 68000  score=0.5986  tokens=8166
2. doc-en-9697  ASCII art  score=0.2581  tokens=5585
3. doc-en-7486  Computational chemistry  score=0.2177  tokens=4696
```

## Reference

- The queries and relevance judgments in [the short-passage samples](data/short_passages.json) come from the [MIRACL project](https://arxiv.org/abs/2210.09984), [topics and qrels](https://huggingface.co/datasets/miracl/miracl), under [Apache 2.0](../LICENSES/Apache-2.0.txt). Passage text comes from the [MIRACL corpus](https://huggingface.co/datasets/miracl/miracl-corpus). The text is by the linked Wikipedia article contributors and is shared under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Each record links to the article and its contribution history. MIRACL extracted the plain-text passages from the original articles.
- The query and document IDs in [the long-document samples](data/long_documents.json) come from [MLDR](https://huggingface.co/datasets/Shitao/MLDR) by Jianlv Chen, Shitao Xiao, Peitian Zhang, Kun Luo, Defu Lian and Zheng Liu. The dataset specifies the [MIT License](https://opensource.org/license/mit). The document excerpts are adapted from the English Wikipedia articles by their respective contributors under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). MLDR extracted the plain text. This example selects consecutive sections and trims trailing whitespace.
  - [ASCII art](https://en.wikipedia.org/wiki/ASCII_art)
  - [Motorola 68000](https://en.wikipedia.org/wiki/Motorola_68000)
  - [Computational chemistry](https://en.wikipedia.org/wiki/Computational_chemistry)
