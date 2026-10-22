"""Loading SafeText, few-shot demonstrations, and JSONL helpers."""
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

from .config import DOMAINS

Example = Dict[str, str]  # {"prompt": c, "advice": a, "domain": d}


def load_safetext(repo: str, safe: bool) -> List[Example]:
    name = "safe" if safe else "unsafe"
    path = Path(repo) / "data" / "safetext" / f"{name}_samples.json"
    examples = json.loads(path.read_text())
    for ex in examples:
        if ex["domain"] not in DOMAINS:
            raise ValueError(f"unexpected domain {ex['domain']!r}")
    return examples


def load_few_shot(repo: str, name: str) -> List[dict]:
    """name in {paraphrase, bootstrap, adversarial, rationalize}."""
    return json.loads((Path(repo) / "data" / "few_shot" / f"{name}.json").read_text())


def domain_counts(examples: List[Example]) -> Dict[str, int]:
    return dict(Counter(ex["domain"] for ex in examples))


def save_jsonl(records: List[dict], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_jsonl(path: str) -> List[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
