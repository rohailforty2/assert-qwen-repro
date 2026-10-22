"""End-to-end ASSERT pipeline: baseline -> SAA / TB / AKI generation -> evaluation -> z-tests.

Example (smoke test on 30 scenarios per class):
    python run_pipeline.py --repo ./ASSERT --model gpt-4o-mini --limit 30
Full run against a custom OpenAI-compatible endpoint:
    python run_pipeline.py --repo ./ASSERT --model my-model --base-url http://localhost:8000/v1
Credentials come from OPENAI_API_KEY (or --api-key).
"""
import argparse
import json
import os
import random
from pathlib import Path

from assert_repro import evaluate as ev
from assert_repro import generation as gen
from assert_repro.config import DecodingConfig
from assert_repro.data import (domain_counts, load_few_shot, load_jsonl,
                               load_safetext, save_jsonl)
from assert_repro.llm import LLMClient


def cached(path: Path, fn, force: bool):
    """Run fn() and save as JSONL, or reload if already computed (resumable stages)."""
    if path.exists() and not force:
        print(f"  [skip] {path.name} exists")
        return load_jsonl(str(path))
    records = fn()
    save_jsonl(records, str(path))
    print(f"  [done] {path.name}: {len(records)} records")
    return records


def build_client(args) -> LLMClient:
    return LLMClient(
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key or os.getenv("OPENAI_API_KEY", "EMPTY"),
        decoding=DecodingConfig(),  # temp 0, max_tokens 256, top_p 1, penalties 0
        cache_path=str(Path(args.out) / "llm_cache.jsonl"),
        workers=args.workers,
    )


class RunLock:
    """Refuse a second launch on the same output folder (two writers corrupted the cache once)."""

    def __init__(self, out: Path):
        self.path = out / ".pipeline.lock"

    def __enter__(self):
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise SystemExit(
                f"{self.path} exists: another run is using this folder. If you are sure none is "
                "running (e.g. the runtime was reset), delete that file and start again.")
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


def run(args, client: LLMClient = None) -> dict:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with RunLock(out):
        return _run(args, out, client or build_client(args))


def _run(args, out: Path, client: LLMClient) -> dict:
    if getattr(client, "skipped_cache_lines", 0):
        print(f"  [warn] skipped {client.skipped_cache_lines} corrupt cache lines")

    safe = load_safetext(args.repo, safe=True)
    unsafe = load_safetext(args.repo, safe=False)
    if args.limit:
        rng = random.Random(69)
        rng.shuffle(safe), rng.shuffle(unsafe)
        safe, unsafe = safe[: args.limit], unsafe[: args.limit]
    print(f"SafeText: {len(safe)} safe {domain_counts(safe)} | {len(unsafe)} unsafe {domain_counts(unsafe)}")

    d_rat = load_few_shot(args.repo, "rationalize")
    d_para = load_few_shot(args.repo, "paraphrase")
    d_boot = load_few_shot(args.repo, "bootstrap")
    d_adv = load_few_shot(args.repo, "adversarial")
    f = args.force

    scores, comparisons = {}, {}

    # ---- baseline -------------------------------------------------------------------
    print("Baseline")
    base_safe = cached(out / "baseline_safe.jsonl", lambda: ev.run_classification(
        client, [{**e, "safe": True} for e in safe], ev.baseline_builder(d_rat)), f)
    base_unsafe = cached(out / "baseline_unsafe.jsonl", lambda: ev.run_classification(
        client, [{**e, "safe": False} for e in unsafe], ev.baseline_builder(d_rat)), f)
    scores["baseline_safe"] = ev.score(base_safe, safe=True)
    scores["baseline_unsafe"] = ev.score(base_unsafe, safe=False)

    # ---- Method 1: SAA ----------------------------------------------------------------
    print("Method 1: Semantically Aligned Augmentation")
    for name, exs, is_safe in (("safe", safe, True), ("unsafe", unsafe, False)):
        gen_recs = cached(out / f"saa_{name}_gen.jsonl", lambda: gen.semantically_aligned_augmentation(
            client, exs, d_para, safe=is_safe), f)
        res = cached(out / f"saa_{name}_eval.jsonl", lambda: ev.run_classification(
            client, gen_recs, ev.scenario_builder(d_rat)), f)
        scores[f"saa_{name}"] = ev.score(res, safe=is_safe)
        comparisons[f"SAA ({name})"] = ev.compare(scores[f"baseline_{name}"], scores[f"saa_{name}"])

    # ---- Method 2: TB (unsafe only: contexts/actions are bootstrapped from unsafe pairs) --
    print("Method 2: Targeted Bootstrapping")
    if args.tb_source == "authors":
        # the authors' released, already-clean TB scenarios (3,564), instead of our own generation
        tag, label = "tb_authors", "TB (authors' released samples)"
        make_tb = lambda: [{**r, "safe": False} for r in json.loads(
            (Path(args.repo) / "data" / "bootstrap" / "bootstrap_samples.json").read_text())]
    else:
        tag, label = "tb", "TB (unsafe)"
        make_tb = lambda: gen.targeted_bootstrapping(
            client, unsafe, d_boot, n=args.tb_n, m=args.tb_m)
    tb_gen = cached(out / f"{tag}_gen.jsonl", make_tb, f)
    tb_res = cached(out / f"{tag}_eval.jsonl", lambda: ev.run_classification(
        client, tb_gen, ev.baseline_builder(d_rat)), f)
    scores[f"{tag}_unsafe"] = ev.score(tb_res, safe=False)
    comparisons[label] = ev.compare(scores["baseline_unsafe"], scores[f"{tag}_unsafe"])

    # ---- Method 3: AKI ----------------------------------------------------------------
    print("Method 3: Adversarial Knowledge Injection")
    benefits = cached(out / "aki_benefits.jsonl", lambda: gen.extract_benefits(
        client, unsafe, d_adv), f)
    for tag, four_shot in (("zeroshot", False), ("fourshot", True)):
        res = cached(out / f"aki_{tag}_eval.jsonl", lambda: ev.run_classification(
            client, benefits, ev.aki_builder(d_adv, four_shot)), f)
        scores[f"aki_{tag}"] = ev.score(res, safe=False)
        comparisons[f"AKI {tag} (unsafe)"] = ev.compare(scores["baseline_unsafe"], scores[f"aki_{tag}"])

    # ---- report ---------------------------------------------------------------------------
    (out / "report.json").write_text(json.dumps({"scores": scores, "comparisons": comparisons}, indent=2))
    md = "\n".join(ev.to_markdown(k, v) for k, v in comparisons.items())
    (out / "report.md").write_text(md)
    print("\n" + md)
    return {"scores": scores, "comparisons": comparisons}


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default="./ASSERT", help="path to the cloned alexmeigz/ASSERT repo")
    p.add_argument("--out", default="./outputs")
    p.add_argument("--model", required=True)
    p.add_argument("--base-url", default=None)
    p.add_argument("--api-key", default=None)
    p.add_argument("--limit", type=int, default=None, help="subsample N safe + N unsafe for a quick test")
    p.add_argument("--tb-n", type=int, default=5, help="new contexts per unsafe scenario")
    p.add_argument("--tb-m", type=int, default=5, help="new actions per new context")
    p.add_argument("--tb-source", choices=["generated", "authors"], default="generated",
                   help="TB scenarios: generate with our model, or use the authors' released samples")
    p.add_argument("--workers", type=int, default=32, help="parallel requests to the endpoint")
    p.add_argument("--force", action="store_true", help="recompute stages even if outputs exist")
    return p.parse_args(argv)


if __name__ == "__main__":
    run(parse_args())
