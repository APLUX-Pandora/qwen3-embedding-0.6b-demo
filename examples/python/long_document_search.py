import argparse
import json
from pathlib import Path
from time import perf_counter

from _output import result_stream
from pandora_qwen3_embedding_0_6b import EmbeddingModel
from tokenizers import Tokenizer

SAMPLES = Path(__file__).resolve().parents[1] / "data"


def main():
    parser = argparse.ArgumentParser(description="Rank long MLDR documents.")
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    args = parser.parse_args()
    with result_stream() as output:
        search(args, output)


def search(args, output):
    sample = json.loads((SAMPLES / "long_documents.json").read_text(encoding="utf-8"))
    model_dir = args.model_dir.expanduser()
    manifest = json.loads((model_dir / "models.json").read_text(encoding="utf-8"))
    tokenizer_path = model_dir / manifest["common"]["tokenizer"]["path"]
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer.no_truncation()
    tokenizer.no_padding()

    ranked = []
    with EmbeddingModel.from_pretrained(model_dir) as model:
        limit = model.capabilities["max_input_tokens"]
        query = model.encode(sample["query"], prompt=sample["query_prefix"])
        for document in sample["documents"]:
            text = (SAMPLES / document["file"]).read_text(encoding="utf-8")
            # Match the SDK's document tokenization, including special tokens.
            input_tokens = len(tokenizer.encode(text, add_special_tokens=True).ids)
            start = perf_counter()
            embedding = model.encode(text)
            elapsed_ms = (perf_counter() - start) * 1000
            score = float(embedding @ query)
            ranked.append((score, document, input_tokens, elapsed_ms))

    print(f"Query: {sample['query']}", file=output)
    print(f"Input limit: {limit} tokens per text", file=output)
    for rank, (score, document, input_tokens, elapsed_ms) in enumerate(
        sorted(ranked, key=lambda row: -row[0]),
        start=1,
    ):
        print(
            f"{rank}. {document['document_id']}  {document['title']}"
            f"  score={score:.4f}  tokens={input_tokens}  encode={elapsed_ms:.1f} ms",
            file=output,
        )


if __name__ == "__main__":
    main()
