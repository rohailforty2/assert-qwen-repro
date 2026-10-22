"""Integrity checks for one run folder. Exit code 0 = all PASS, 1 = something failed.

    python scripts/check_run.py --out <run folder> [--partial]

Catches the problems seen in the original run: generation/evaluation files that disagree
(two concurrent launches), duplicated evaluation records, corrupt cache lines, unparsed
answers, and malformed TB phrases. --partial skips the full-size baseline check (for --limit runs).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assert_repro import evaluate as ev  # noqa: E402

PAIRS = [("saa_safe_gen", "saa_safe_eval"), ("saa_unsafe_gen", "saa_unsafe_eval"),
         ("tb_gen", "tb_eval"), ("tb_authors_gen", "tb_authors_eval"),
         ("aki_benefits", "aki_zeroshot_eval"), ("aki_benefits", "aki_fourshot_eval")]
TRUTH_SAFE = {"baseline_safe": True, "saa_safe_eval": True}   # everything else is an unsafe-truth file


def main(out: str, partial: bool) -> int:
    out = Path(out)
    fails, warns = [], []
    load = lambda n: [json.loads(l) for l in open(out / f"{n}.jsonl", encoding="utf-8") if l.strip()]
    exists = lambda n: (out / f"{n}.jsonl").exists()

    for name, want in (("baseline_safe", 1095), ("baseline_unsafe", 370)):
        if not exists(name):
            fails.append(f"missing {name}.jsonl"); continue
        n = len(load(name))
        print(f"{name}: {n} records")
        if not partial and n != want:
            fails.append(f"{name} has {n} records, expected {want}")

    for g, e in PAIRS:
        if not (exists(g) and exists(e)):
            warns.append(f"skipped {g} / {e} (file missing)"); continue
        gl, el = load(g), load(e)
        uniq = len({json.dumps({k: v for k, v in r.items() if k not in ("rationale", "pred")}, sort_keys=True)
                    for r in el})
        flag = "OK" if len(gl) == len(el) else "MISMATCH"
        print(f"{g}: {len(gl)} | {e}: {len(el)} (unique {uniq}) {flag}")
        if len(gl) != len(el):
            fails.append(f"{g} vs {e}: {len(gl)} != {len(el)}")
        if uniq != len(el):
            fails.append(f"{e}: {len(el) - uniq} duplicated records (double launch?)")

    for n in ["baseline_safe", "baseline_unsafe"] + [e for _, e in PAIRS]:
        if exists(n):
            s = ev.score(load(n), safe=TRUTH_SAFE.get(n, False))
            un = s["overall"]["unparsed"]
            print(f"{n}: unparsed {un}/{s['overall']['n']}")
            if un:
                warns.append(f"{n}: {un} unparsed answers (counted as errors)")

    if exists("tb_gen"):
        bad = [r for r in load("tb_gen")
               if len(r["prompt"].split()) > 15 or len(r["advice"].split()) > 15 or ":" in r["prompt"] + r["advice"]]
        print(f"tb_gen: {len(bad)} suspicious phrases (>15 words or containing ':')")
        if bad:
            warns.append(f"tb_gen has {len(bad)} suspicious phrases, e.g. {bad[0]['prompt'][:60]!r}")

    cache = out / "llm_cache.jsonl"
    if cache.exists():
        good = badn = 0
        for raw in open(cache, "rb"):
            try:
                row = json.loads(raw.decode("utf-8")); assert "key" in row and "out" in row; good += 1
            except Exception:
                badn += 1
        print(f"llm_cache.jsonl: {good} good, {badn} corrupt lines")
        if badn:
            warns.append(f"cache has {badn} corrupt lines (skipped on load)")
    if (out / ".pipeline.lock").exists():
        fails.append(".pipeline.lock present: a run is active or crashed")

    for w in warns: print("WARN ", w)
    for f in fails: print("FAIL ", f)
    print("RESULT:", "FAIL" if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--partial", action="store_true")
    a = ap.parse_args()
    sys.exit(main(a.out, a.partial))
