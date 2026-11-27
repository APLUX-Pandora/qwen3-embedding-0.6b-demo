import argparse
import json
import signal
import sys
from contextlib import ExitStack, contextmanager
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Condition, Lock
from time import perf_counter

import numpy as np

from pandora_qwen3_embedding_0_6b import EmbeddingModel

from .documents import DOCUMENTS

_STATIC = Path(__file__).with_name("static")
_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/style.css": ("style.css", "text/css; charset=utf-8"),
    "/static/demo.js": ("demo.js", "text/javascript; charset=utf-8"),
    "/static/logo.png": ("logo.png", "image/png"),
    "/static/pandora-mark.svg": ("pandora-mark.svg", "image/svg+xml"),
}
_WARMUP_QUERY = "如何取消推理？"
_MAX_TEXT_BYTES = 128 * 1024
_MAX_JSON_BYTES = 12 * _MAX_TEXT_BYTES + 1024
_MAX_DOCUMENTS = 200
_MAX_TITLE = 80
_SNIPPET_LENGTH = 240
_TOP_K = 10


def _text(fields, name, *, required=True, max_bytes=_MAX_TEXT_BYTES):
    text = fields.get(name, "")
    if not isinstance(text, str):
        raise ValueError("Enter text.")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError as error:
        raise ValueError("Enter valid UTF-8 text.") from error
    if size > max_bytes:
        raise ValueError("Each text input must be 128 KiB or smaller.")
    text = text.strip()
    if required and not text:
        raise ValueError("Fill in the required text.")
    return text


def _score(value):
    return float(np.clip(value, -1.0, 1.0))


def _chip():
    try:
        machine = Path("/sys/devices/soc0/machine").read_text(encoding="utf-8").strip()
    except OSError:
        return "Unknown chip"
    return machine.partition("_")[0] or "Unknown chip"


class Demo:
    def __init__(self, model, load_s):
        self.model = model
        self.lock = Lock()
        self.chip = _chip()
        self.load_s = load_s

        # Match the acceptance probe's first query before indexing or serving requests.
        started = perf_counter()
        model.encode(_WARMUP_QUERY, prompt_name="query")
        self.first_encode_ms = (perf_counter() - started) * 1000

        started = perf_counter()
        self.documents = tuple({"title": title, "text": text} for title, text in DOCUMENTS)
        self.vectors = model.encode([document["text"] for document in self.documents])
        self.index_s = perf_counter() - started

    def _encode(self, texts, *, prompt_name=None):
        started = perf_counter()
        vectors = self.model.encode(texts, prompt_name=prompt_name)
        elapsed = perf_counter() - started
        token_count = self.model._count_input_tokens(texts, prompt_name=prompt_name)
        return vectors, {"encode_ms": elapsed * 1000, "input_tokens": token_count}

    def _index_stats(self):
        count = len(self.documents)
        return {
            "count": count, "limit": _MAX_DOCUMENTS, "total_s": self.index_s,
            "average_ms": self.index_s * 1000 / count,
        }

    def library(self):
        return {
            "chip": self.chip, "load_s": self.load_s, "first_encode_ms": self.first_encode_ms,
            "embedding_dim": self.model.capabilities["embedding_dim"],
            "max_input_tokens": self.model.capabilities["max_input_tokens"],
            "documents": self.documents, "index": self._index_stats(),
        }

    def similarity(self, fields):
        first, second = _text(fields, "first"), _text(fields, "second")
        vectors, encoding = self._encode([first, second])
        return {"score": _score(vectors[0] @ vectors[1]), "encoding": encoding}

    def search(self, fields):
        query, encoding = self._encode(_text(fields, "query"), prompt_name="query")
        scores = self.vectors @ query
        best = np.argsort(-scores, kind="stable")[:_TOP_K]
        results = []
        for index in best:
            document = self.documents[index]
            text = document["text"]
            snippet = text[:_SNIPPET_LENGTH] + ("…" if len(text) > _SNIPPET_LENGTH else "")
            results.append({"title": document["title"], "snippet": snippet, "score": _score(scores[index])})
        return {"results": results, "encoding": encoding, "index": self._index_stats()}

    def add_document(self, fields):
        if len(self.documents) >= _MAX_DOCUMENTS:
            raise ValueError("The document library is full (200 documents).")
        text = _text(fields, "text")
        title = _text(fields, "title", required=False)
        if len(title) > _MAX_TITLE:
            raise ValueError("The document title must be 80 characters or fewer.")
        document = {"title": title or text.split("\n", 1)[0][:_MAX_TITLE], "text": text}
        output, encoding = self._encode([text])
        started = perf_counter()
        vectors = np.concatenate((self.vectors, output))
        self.documents += (document,)
        self.vectors = vectors
        self.index_s += encoding["encode_ms"] / 1000 + perf_counter() - started
        return {"document": document, "encoding": encoding, "index": self._index_stats()}


class SearchServer(ThreadingHTTPServer):
    def __init__(self, address, handler):
        self._requests = Condition()
        self._active_requests = 0
        self._stopping = False
        super().__init__(address, handler)

    @contextmanager
    def inference_request(self):
        with self._requests:
            admitted = not self._stopping
            if admitted:
                self._active_requests += 1
        try:
            yield admitted
        finally:
            if admitted:
                with self._requests:
                    self._active_requests -= 1
                    self._requests.notify_all()

    def server_close(self):
        with self._requests:
            self._stopping = True
        super().server_close()
        with self._requests:
            self._requests.wait_for(lambda: self._active_requests == 0)


class SearchHandler(BaseHTTPRequestHandler):
    timeout = 10

    def __init__(self, *args, demo):
        self.demo = demo
        super().__init__(*args)

    def _reply(self, body, content_type, status=HTTPStatus.OK):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status=HTTPStatus.OK):
        self._reply(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def do_GET(self):
        if self.path == "/api/library":
            with self.demo.lock:
                data = self.demo.library()
            self._json(data)
        elif self.path in _ASSETS:
            filename, content_type = _ASSETS[self.path]
            self._reply((_STATIC / filename).read_bytes(), content_type)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        actions = {
            "/api/similarity": self.demo.similarity,
            "/api/search": self.demo.search,
            "/api/documents": self.demo.add_document,
        }
        action = actions.get(self.path)
        if action is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            self._json({"error": "Submit the request from the demo page."}, HTTPStatus.FORBIDDEN)
            return
        try:
            if self.headers.get_content_type() != "application/json":
                raise ValueError
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= _MAX_JSON_BYTES:
                raise ValueError
            fields = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(fields, dict):
                raise ValueError
        except (ValueError, RecursionError):
            self._json({"error": "The request format is invalid or the input is too long."}, HTTPStatus.BAD_REQUEST)
            return

        with self.server.inference_request() as admitted:
            if not admitted:
                self._json({"error": "The demo is shutting down."}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            try:
                with self.demo.lock:
                    data = action(fields)
            except ValueError as error:
                self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            except (OSError, RuntimeError) as error:
                print(f"Encoding failed: {error}", file=sys.stderr)
                self._json({"error": "Encoding failed. Check the server log."}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                self._json(data)


def _interrupt(_signum, _frame):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description="Run the Qwen3 Embedding Web Demo.")
    parser.add_argument("--host", default="127.0.0.1", help="address to listen on")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    args = parser.parse_args()

    with ExitStack() as stack:
        started = perf_counter()
        model = EmbeddingModel.from_pretrained(args.model_dir)
        load_s = perf_counter() - started
        stack.enter_context(model)
        demo = Demo(model, load_s)
        handler = partial(SearchHandler, demo=demo)
        server = stack.enter_context(SearchServer((args.host, args.port), handler))
        previous = signal.signal(signal.SIGTERM, _interrupt)
        print(f"Embedding demo is listening at http://{args.host}:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    main()
