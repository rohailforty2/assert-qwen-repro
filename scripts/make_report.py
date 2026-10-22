"""Rebuild every z-test table from the saved evaluation files of one run.

    python scripts/make_report.py --out <run folder>

Writes <run folder>/report_all.md. Needs: baseline_{safe,unsafe}.jsonl and any of the
method evaluation files (missing ones are skipped with a message).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assert_repro import evaluate as ev  # noqa: E402

UNSAFE_WORDS = re.compile(r"unsafe|dangerous|harmful|hazard|toxic|injur|risk", re.I)


def build_report(out: str) -> str:
    load = lambda n: [json.loads(l) for l in open(f"{out}/{n}.jsonl", encoding="utf-8") if l.strip()]
    base_unsafe = ev.score(load("baseline_unsafe"), safe=False)
    base_safe = ev.score(load("baseline_safe"), safe=True)
    runs = [  # (name, eval file, ground truth is safe?, baseline)
        ("SAA (safe)", "saa_safe_eval", True, base_safe),
        ("SAA (unsafe)", "saa_unsafe_eval", False, base_unsafe),
        ("TB, our generation (unsafe)", "tb_eval", False, base_unsafe),
        ("TB, authors' released samples (unsafe)", "tb_authors_eval", False, base_unsafe),
        ("AKI zero-shot (unsafe)", "aki_zeroshot_eval", False, base_unsafe),
        ("AKI 4-shot (unsafe)", "aki_fourshot_eval", False, base_unsafe),
    ]
    md = []
    for name, fname, safe, base in runs:
        if not os.path.exists(f"{out}/{fname}.jsonl"):
            print("missing:", fname)
            continue
        recs = load(fname)
        s = ev.score(recs, safe=safe)
        contra = ""
        if not safe:  # crude proxy: 'Yes' answers whose own rationale calls the action unsafe
            yes_errs = [r for r in recs if r["pred"] == "Yes"]
            n_c = sum(bool(UNSAFE_WORDS.search(r["rationale"][:150])) for r in yes_errs)
            contra = f" | 'Yes' errors whose rationale says unsafe/dangerous/...: {n_c}/{len(yes_errs)}"
        md.append(ev.to_markdown(name, ev.compare(base, s)) + f"\nn = {s['overall']['n']}{contra}\n")
    return "\n".join(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="run folder holding the *.jsonl files")
    a = ap.parse_args()
    report = build_report(a.out)
    Path(a.out, "report_all.md").write_text(report, encoding="utf-8")
    print(report)
