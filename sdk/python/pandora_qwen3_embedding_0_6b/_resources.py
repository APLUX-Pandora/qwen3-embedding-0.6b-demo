import json
from pathlib import Path

_TARGETS = {
    603: "qcs8550_qnn248",
    675: "qcs8275_qnn248",
    676: "qcs9075_qnn248",
    702: "qcs8625_qnn248",
}


def _resource(root, entry, scope):
    path = entry["path"]
    size = entry["size_bytes"]
    if not isinstance(path, str) or not path or type(size) is not int or size <= 0:
        raise ValueError("Expected a resource path and a positive size in bytes")
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or not relative.is_relative_to(scope):
        raise ValueError(f"Resource is outside its declared directory: {path}")
    file = root / relative
    if not file.is_file() or file.stat().st_size != size:
        raise OSError(f"Missing model resource or incorrect size: {file}")
    return file


def resolve_resources(model_dir, soc_id):
    root = Path(model_dir).expanduser().resolve()
    manifest = root / "models.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        targets = data["targets"]
        if not isinstance(targets, dict):
            raise TypeError("Expected a mapping of target directories")
        requested = _TARGETS.get(soc_id)
        target = requested
        if soc_id == 675 and requested not in targets:
            target = _TARGETS[702]
        if target is None or target not in targets:
            found = ", ".join(sorted(targets)) or "(none)"
            raise OSError(f"Missing model target for {requested or f'SoC {soc_id}'}; found: {found}")
        folder = Path("targets") / target
        graph = _resource(root, targets[target]["context"], folder)
        common = data["common"]
        tokenizer = _resource(root, common["tokenizer"], Path("."))
        embedding = _resource(root, common["token_embedding"], Path("."))
        return graph, tokenizer, embedding
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid model manifest {manifest}: {exc}") from exc
