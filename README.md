# Qwen3-Embedding-0.6B

<p align="center">
  <a href="https://huggingface.co/APLUX-Pandora/Qwen3-Embedding-0.6B"><img src="https://img.shields.io/badge/Hugging%20Face-QWEN3--EMBEDDING--0.6B-E3B800?style=for-the-badge&amp;logo=huggingface&amp;logoColor=FFD21E&amp;labelColor=555555" alt="Hugging Face: Qwen3-Embedding-0.6B"></a>
  <a href="https://github.com/APLUX-Pandora/qwen3-embedding-0.6b-demo"><img src="https://img.shields.io/badge/GitHub-QWEN3--EMBEDDING--0.6B-000000?style=for-the-badge&amp;logo=github&amp;logoColor=white&amp;labelColor=555555" alt="GitHub: Qwen3-Embedding-0.6B"></a>
</p>

Encode queries and documents as vectors for semantic search on compatible Qualcomm NPUs.

Based on [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).

**Demo recording:** reserved for a post-release recording.

## 1. Install

Clone the Demo and enter its root directory:

```bash
git clone https://github.com/APLUX-Pandora/qwen3-embedding-0.6b-demo.git
cd qwen3-embedding-0.6b-demo
```

### Prepare the device

Use a compatible Linux device with Aidlux LMS and the required drivers, DSP firmware and BSP/FastRPC support. The SDK includes its QNN runtime libraries; no separate QNN installation or path configuration is required.

Check the activation:

```bash
sudo lms check
```

Continue only when it returns true.

### Install the Demo and SDK

Use Python 3.10–3.12. Create and activate the Demo environment, then install:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

This installs the SDK, the Web Demo and the Hugging Face CLI. To use only the SDK in your own application, see the [SDK installation](sdk/README.md#install).

## 2. Get the model

Download the shared files and one device target. The commands below use QCS8625; for another device, use the folder in the [targets table](docs/MODEL_SETUP.md#targets).

For a private model, run `hf auth login` first.

```bash
hf download APLUX-Pandora/Qwen3-Embedding-0.6B --local-dir models --exclude "targets/*" --exclude "media/*" --exclude README.md --exclude .gitattributes
hf download APLUX-Pandora/Qwen3-Embedding-0.6B --local-dir models --include "targets/qcs8625_qnn248/*"
```

## 3. Run the Web Demo

```bash
bash demo/run.sh --port 7860
```

Open `http://127.0.0.1:7860/` on the device. In **Sentence similarity**, enter two sentences or select an example, then select **Compute similarity**. In **Document search**, search the bilingual library or add your own text by pasting it or uploading a UTF-8 `.txt` file. Both tabs show on-device performance. Stop with `Ctrl+C`. See the [Web Demo guide](demo/README.md) for details and network access.

## 4. Python Usage

In the same environment, from the Demo root:

```python
from pandora_qwen3_embedding_0_6b import EmbeddingModel

with EmbeddingModel.from_pretrained("models") as model:
    query = model.encode("How can I cancel inference?", prompt_name="query")
    documents = model.encode(["Click Stop to cancel inference.", "Model files are stored locally."])

scores = documents @ query
print(scores)
```

Run the passage and long-document search examples with the installed SDK.

```bash
python examples/python/short_passage_search.py --lang en
python examples/python/long_document_search.py
```

See the [Python API](sdk/PYTHON_API.md) and the [examples guide](examples/README.md) for options and sample sources.

## Documentation

- [Model setup](docs/MODEL_SETUP.md) covers device requirements, targets, download and folder layout.
- [Python API](sdk/PYTHON_API.md) describes the model interface.
- [C ABI](docs/C_ABI.md) describes native integration.
- [Examples](examples/README.md) covers multilingual passage search and long-document search.

## License

See [LICENSING.md](LICENSING.md), [NOTICE](NOTICE) and [LICENSES](LICENSES/).
