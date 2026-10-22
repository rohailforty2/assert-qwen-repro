"""Write <run folder>/manifest.json: everything needed to say exactly what produced a run.

    python scripts/make_manifest.py --out <run> --model <id> --revision <hf sha> --authors-repo <path>

Records: UTC time, this repo's git commit (and whether the tree was dirty), the authors' repo
commit, package versions, GPU, decoding settings, and per-file line counts + SHA-256.
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from assert_repro.config import DecodingConfig  # noqa: E402


def sh(*cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30).stdout.strip() or None
    except Exception:
        return None


def version(pkg):
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(out: Path, model: str, revision: str, authors_repo: str) -> dict:
    files = {}
    for p in sorted(out.iterdir()):
        if p.suffix in (".jsonl", ".md", ".json") and p.name != "manifest.json":
            info = {"bytes": p.stat().st_size, "sha256": sha256(p)}
            if p.suffix == ".jsonl":
                info["lines"] = sum(1 for _ in open(p, "rb"))
            files[p.name] = info
    bad = 0
    cache = out / "llm_cache.jsonl"
    if cache.exists():
        for raw in open(cache, "rb"):
            try:
                row = json.loads(raw.decode("utf-8"))
                assert "key" in row and "out" in row
            except Exception:
                bad += 1
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": out.name,
        "model": model,
        "model_revision": revision,
        "decoding": DecodingConfig().as_dict(),
        "repo_commit": sh("git", "rev-parse", "HEAD", cwd=ROOT),
        "repo_dirty": bool(sh("git", "status", "--porcelain", cwd=ROOT)),
        "authors_repo_commit": sh("git", "rev-parse", "HEAD", cwd=authors_repo) if authors_repo else None,
        "python": platform.python_version(),
        "packages": {p: version(p) for p in ("vllm", "openai", "numpy", "torch", "transformers")},
        "gpu": sh("nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"),
        "cache_corrupt_lines": bad,
        "files": files,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--revision", default="unpinned")
    ap.add_argument("--authors-repo", default=None)
    a = ap.parse_args()
    m = build_manifest(Path(a.out), a.model, a.revision, a.authors_repo)
    Path(a.out, "manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in m.items() if k != "files"}, indent=2))
    print(f"{len(m['files'])} files hashed")
