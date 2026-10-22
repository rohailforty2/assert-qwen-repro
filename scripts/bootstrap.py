"""Cluster bootstrap over source scenarios (paired with the baseline where the source is known).

    python scripts/bootstrap.py --out <run folder> [--boot-b 10000] [--seed 0]

Why: SAA/TB/AKI create several variants of one source scenario. The paper's z-test treats
variants as independent. Here whole source scenarios are resampled, so variants stay together.
Writes <run folder>/bootstrap_report.md.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assert_repro.stats import two_proportion_ztest  # noqa: E402

DOMS = ("nature", "medical", "household", "other")
LABEL = {"nature": "Outdoors", "medical": "Medical", "household": "Household", "other": "Extra"}


def clusters(records, key_fn, truth):
    """key -> [errors, n, domain]. A record is an error when pred != truth (unparsed counts as an error)."""
    out = {}
    for r in records:
        c = out.setdefault(key_fn(r), [0, 0, r["domain"]])
        c[0] += r["pred"] != truth
        c[1] += 1
    return out


def _arrays(cl, keys):
    return (np.array([cl[k][0] for k in keys], float), np.array([cl[k][1] for k in keys], float))


def boot_diff(base, meth, paired, B=10000, seed=0, chunk=1000):
    """Cluster bootstrap of (method error rate - baseline error rate), in percentage points.

    paired=True : the same source scenarios are resampled on both sides (they exist in both).
    paired=False: the two sides are resampled independently.
    Two-sided percentile p-value: 2*min(P(d<=0), P(d>=0)), floored at 1/B.
    """
    rng = np.random.default_rng(seed)
    if paired:
        keys = [k for k in base if k in meth and meth[k][1] > 0]
        if not keys:
            return None
        be, bn = _arrays(base, keys)
        me, mn = _arrays(meth, keys)
        K = len(keys)
        ds = []
        for _ in range(0, B, chunk):
            idx = rng.integers(0, K, (chunk, K))
            ds.append(me[idx].sum(1) / mn[idx].sum(1) - be[idx].sum(1) / bn[idx].sum(1))
        n_cl = K
    else:
        bk, mk = list(base), [k for k in meth if meth[k][1] > 0]
        if not bk or not mk:
            return None
        be, bn = _arrays(base, bk)
        me, mn = _arrays(meth, mk)
        ds = []
        for _ in range(0, B, chunk):
            ib = rng.integers(0, len(bk), (chunk, len(bk)))
            im = rng.integers(0, len(mk), (chunk, len(mk)))
            ds.append(me[im].sum(1) / mn[im].sum(1) - be[ib].sum(1) / bn[ib].sum(1))
        n_cl = f"{len(bk)}/{len(mk)}"
    d = np.concatenate(ds) * 100
    p = min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))
    lo, hi = np.percentile(d, [2.5, 97.5])
    return dict(base=100 * be.sum() / bn.sum(), meth=100 * me.sum() / mn.sum(),
                diff=100 * (me.sum() / mn.sum() - be.sum() / bn.sum()),
                lo=lo, hi=hi, p=max(p, 1.0 / len(d)), p_floor=(p < 1.0 / len(d)), clusters=n_cl)


def run_all(out, B=10000, seed=0):
    load = lambda n: [json.loads(l) for l in open(f"{out}/{n}.jsonl", encoding="utf-8") if l.strip()]
    src = lambda r: (r["src_prompt"], r["src_advice"])
    orig = lambda r: (r["prompt"], r["advice"])
    base_cl = {True: clusters(load("baseline_safe"), orig, "Yes"),
               False: clusters(load("baseline_unsafe"), orig, "No")}
    specs = [  # name, eval file, ground truth safe?, cluster key, paired with baseline?
        ("SAA (safe)", "saa_safe_eval", True, src, True),
        ("SAA (unsafe)", "saa_unsafe_eval", False, src, True),
        ("TB, our generation (unsafe)", "tb_eval", False, src, True),
        ("TB, authors' samples (unsafe)  [clustered by context; unpaired]", "tb_authors_eval", False,
         lambda r: r["prompt"], False),
        ("AKI zero-shot (unsafe)", "aki_zeroshot_eval", False, orig, True),
        ("AKI 4-shot (unsafe)", "aki_fourshot_eval", False, orig, True),
    ]
    md = []
    for name, fname, safe, key_fn, paired in specs:
        if not os.path.exists(f"{out}/{fname}.jsonl"):
            md.append(f"### {name}\n\nmissing: {fname}\n")
            continue
        base = base_cl[safe]
        meth = clusters(load(fname), key_fn, "Yes" if safe else "No")
        rows = [f"### {name}", "",
                "| Domain | Baseline err % | Method err % | Δ (pts) | 95% CI (cluster bootstrap) | p (cluster bootstrap) | p (naive z-test) | clusters |",
                "|---|---|---|---|---|---|---|---|"]
        for dom in (*DOMS, "overall"):
            sel = lambda cl: cl if dom == "overall" else {k: v for k, v in cl.items() if v[2] == dom}
            b, m = sel(base), sel(meth)
            res = boot_diff(b, m, paired, B=B, seed=seed)
            if res is None:
                rows.append(f"| {LABEL.get(dom, 'Overall')} | n/a | n/a | | | | | |")
                continue
            z = two_proportion_ztest(sum(v[0] for v in b.values()), sum(v[1] for v in b.values()),
                                     sum(v[0] for v in m.values()), sum(v[1] for v in m.values()))
            pb = ("<" if res["p_floor"] else "") + f"{res['p']:.4f}"
            rows.append(f"| {LABEL.get(dom, 'Overall')} | {res['base']:.2f} | {res['meth']:.2f} | {res['diff']:+.2f} "
                        f"| [{res['lo']:+.2f}, {res['hi']:+.2f}] | {pb} | {z['p']:.4f} | {res['clusters']} |")
        md.append("\n".join(rows) + "\n")
    report = "\n".join(md)
    Path(out, "bootstrap_report.md").write_text(report, encoding="utf-8")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="run folder holding the *.jsonl files")
    ap.add_argument("--boot-b", type=int, default=10000, help="bootstrap resamples")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    print(run_all(a.out, B=a.boot_b, seed=a.seed))
