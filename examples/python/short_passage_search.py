import argparse
import json
from pathlib import Path

from _output import result_stream
from pandora_qwen3_embedding_0_6b import EmbeddingModel

LANGUAGES = ("zh", "en", "ja", "ko", "fr", "es")
SAMPLES = Path(__file__).resolve().parents[1] / "data" / "short_passages.json"
TOP_K = 10


def main():
    parser = argparse.ArgumentParser(description="Rank multilingual MIRACL passages.")
    parser.add_argument("--lang", choices=LANGUAGES, default="en")
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    args = parser.parse_args()
    with result_stream() as output:
        search(args, output)


def search(args, output):
    samples = json.loads(SAMPLES.read_text(encoding="utf-8"))
    sample = samples["languages"][args.lang]
    passages = sample["passages"]
    with EmbeddingModel.from_pretrained(args.model_dir) as model:
        query = model.encode(sample["query"], prompt=samples["query_prefix"])
        documents = model.encode([passage["text"] for passage in passages])

    scores = documents @ query
    ranked = sorted(zip(passages, scores), key=lambda row: -row[1])
    print(f"Query ({args.lang}): {sample['query']}", file=output)
    for rank, (passage, score) in enumerate(ranked[:TOP_K], start=1):
        label = " [labeled positive]" if passage["relevant"] else ""
        print(
            f"{rank:2}. {passage['document_id']}  score={score:.4f}{label}", file=output
        )
        print(passage["text"], file=output)


if __name__ == "__main__":
    main()
