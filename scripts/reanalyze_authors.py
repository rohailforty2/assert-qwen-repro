"""Cluster-bootstrap re-analysis of the ASSERT authors' released outputs.

    python scripts/reanalyze_authors.py --repo /content/ASSERT [--boot-b 10000] [--out results/authors_reanalysis]

Uses only the authors' released files (data/*) at commit 1cafa82; no model calls.
Steps: (1) link each paraphrase to its source scenario and validate the linking,
(2) recompute the paper's z-test deltas from the files, (3) cluster bootstrap paired on
the same source scenarios, (4) check the cross-model table (paper Table 5).
"""
import argparse, collections, json, random, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from assert_repro.align import align  # noqa: E402
from assert_repro.stats import two_proportion_ztest  # noqa: E402
from bootstrap import boot_diff  # noqa: E402

RX = re.compile(r"^\W*(yes|no)\b", re.I)
pred = lambda t: (m.group(1).capitalize() if (m := RX.match(t or "")) else None)
DOMS = ("nature", "medical", "household", "other")
NAME = {"gpt3": "GPT-3.5", "gpt4": "GPT-4", "alpaca": "Alpaca", "vicuna": "Vicuna"}
ctx = lambda r: r["prompt"].strip().rstrip(",")
pair = lambda r: (r["prompt"].strip().rstrip(","), r["advice"].strip())
# Overall deltas printed in the paper (Tables 2-4), in ERROR points (paper Tables 2-3 report accuracy: sign flipped).
PAPER = {("gpt3", "SAA (safe)"): 2.77, ("gpt4", "SAA (safe)"): 0.45, ("alpaca", "SAA (safe)"): 7.26,
         ("vicuna", "SAA (safe)"): 4.23, ("gpt3", "SAA (unsafe)"): 1.78, ("gpt4", "SAA (unsafe)"): 0.81,
         ("alpaca", "SAA (unsafe)"): 1.52, ("vicuna", "SAA (unsafe)"): 7.27, ("gpt3", "TB"): -4.27,
         ("gpt4", "TB"): 1.55, ("alpaca", "TB"): -4.55, ("vicuna", "TB"): -7.12,
         ("gpt3", "AKI 0-shot"): 7.6, ("gpt3", "AKI 4-shot"): 45.6, ("gpt4", "AKI 0-shot"): 17.3,
         ("gpt4", "AKI 4-shot"): 30.7}
# Paper Table 5, target Alpaca: (error, delta) for nature, medical, household, other, overall.
TABLE5 = {"gpt3": [(51.7, 41.9), (39.8, 33.3), (67.0, 63.9), (49.6, 43.7), (53.5, 47.3)],
          "gpt4": [(59.4, 53.3), (44.8, 42.1), (72.8, 72.0), (50.4, 50.4), (58.9, 56.5)]}
VICUNA_T5 = {"gpt4": ([48.6, 42.9, 69.7, 54.7], 66.2), "gpt3": ([34.4, 26.34, 56.1, 34.8], 39.7)}


def clusters(recs, key, truth):
    out = {}
    for r in recs:
        c = out.setdefault(key(r), [0, 0, r["domain"]])
        c[0] += pred(r["rationale"]) != truth
        c[1] += 1
    return out


def err(recs, truth="No", dom=None):
    rs = [r for r in recs if dom in (None, r["domain"])]
    return 100 * sum(pred(r["rationale"]) != truth for r in rs) / len(rs)


def main(repo, B, out):
    D = Path(repo, "data")
    L = lambda p: json.load(open(D / f"{p}.json", encoding="utf-8"))
    src = {s: L(f"safetext/{s}_samples") for s in ("safe", "unsafe")}
    md = ["# Re-analysis of the ASSERT authors' released outputs", "",
          f"Source: github.com/alexmeigz/ASSERT `data/` at commit 1cafa82. No model calls. "
          f"Cluster bootstrap B={B}, seed 0. Unparsed answers count as errors. Δ = method error − baseline error (points).", ""]

    # 1. validate linking ---------------------------------------------------------------
    md += ["## 1. Linking paraphrases to source scenarios", "",
           "GPT-3.5/GPT-4 files hold exactly 5 paraphrases per source in source order (checked: domain matches "
           "100%). The aligner is tested by deleting paraphrases at random from those files and recovering the source:", "",
           "| Split | Deleted | Exact source | Same context |", "|---|---|---|---|"]
    for s in ("unsafe", "safe"):
        p = L(f"paraphrase/paraphrases_{s}_gpt3")
        assert len(p) == 5 * len(src[s])
        assert all(p[i]["domain"] == src[s][i // 5]["domain"] for i in range(len(p)))
        for drop in (0.0, 0.2, 0.45):
            rnd = random.Random(1)
            keep = [i for i in range(len(p)) if rnd.random() >= drop]
            a = align([p[i]["paraphrase"] for i in keep], src[s], [p[i]["domain"] for i in keep])
            ex = sum(a[t] == i // 5 for t, i in enumerate(keep)) / len(keep)
            cx = sum(src[s][a[t]]["prompt"] == src[s][i // 5]["prompt"] for t, i in enumerate(keep)) / len(keep)
            md.append(f"| {s} | {drop:.0%} | {ex:.4f} | {cx:.4f} |")
    md += ["", "Safe items are therefore clustered by context (exact source can be confused between safe answers "
           "that share a context); unsafe items by exact source.", ""]

    # 2-3. deltas and bootstrap -------------------------------------------------------------
    rows = []
    for m in NAME:
        base = {s: L(f"baseline/rationales_{s}_{m}") for s in ("safe", "unsafe")}
        for s, truth, key in (("safe", "Yes", ctx), ("unsafe", "No", pair)):
            para = L(f"paraphrase/rationales_{s}_{m}")
            idx = align([r["paraphrase"] for r in para], src[s], [r["domain"] for r in para])
            for r, j in zip(para, idx):
                r["prompt"], r["advice"] = src[s][j]["prompt"], src[s][j]["advice"]
            rows.append((m, f"SAA ({s})", clusters(base[s], key, truth), clusters(para, key, truth), True, len(para)))
        rows.append((m, "TB", clusters(base["unsafe"], ctx, "No"), clusters(L(f"bootstrap/rationales_{m}"), ctx, "No"),
                     False, 3564))
        if m in ("gpt3", "gpt4"):
            for shot, tag in (("zeroshot", "AKI 0-shot"), ("fourshot", "AKI 4-shot")):
                a = L(f"adversarial/rationales_{m}_internal_{shot}")
                rows.append((m, tag, clusters(base["unsafe"], pair, "No"), clusters(a, pair, "No"), True, len(a)))
    md += ["## 2. Paper's comparison vs. paired cluster bootstrap", "",
           "*Paper-style* = all method items vs. the FULL baseline, two-proportion z-test (as in the paper). "
           "*Paired* = only source scenarios that have variants, resampling whole scenarios. TB is unpaired "
           "(new scenarios), clustered by context.", "",
           "| Model | Method | n | Paper Δ | Paper-style Δ (recomputed) | z-test p | Paired base % | Paired Δ [95% CI] | Bootstrap p | Scenarios covered |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    out_json = []
    for m, meth, b, x, paired, n in rows:
        be, bn = sum(v[0] for v in b.values()), sum(v[1] for v in b.values())
        me, mn = sum(v[0] for v in x.values()), sum(v[1] for v in x.values())
        z = two_proportion_ztest(be, bn, me, mn)
        ps = 100 * (me / mn - be / bn)
        r = boot_diff(b, x, paired, B=B, seed=0)
        pb = ("<" if r["p_floor"] else "") + f"{r['p']:.4f}"
        pp = PAPER.get((m, meth))
        md.append(f"| {NAME[m]} | {meth} | {n} | {'' if pp is None else f'{pp:+.2f}'} | {ps:+.2f} | {z['p']:.4f} | "
                  f"{r['base']:.2f} | {r['diff']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}] | {pb} | {r['clusters']} |")
        out_json.append(dict(model=m, method=meth, n=n, paper_delta=pp, paper_style_delta=ps, z_p=z["p"], **r))

    # 4. Table 5 -------------------------------------------------------------------------------
    bu = {m: L(f"baseline/rationales_unsafe_{m}") for m in NAME}
    md += ["", "## 3. Cross-model table (paper Table 5), target Alpaca, adversarial 4-shot", "",
           "Implied baseline = paper error − paper Δ. It matches the SOURCE model's baseline, not Alpaca's.", "",
           "| Benefits from | Domain | Paper error | Recomputed error | Paper Δ | Implied baseline | Alpaca baseline | Source baseline | Δ vs Alpaca baseline |",
           "|---|---|---|---|---|---|---|---|---|"]
    for s, cells in TABLE5.items():
        a = L(f"adversarial/rationales_alpaca_on_{s}_fourshot")
        for dom, (pe, pd) in zip((*DOMS, None), cells):
            re_, ab, sb = err(a, dom=dom), err(bu["alpaca"], dom=dom), err(bu[s], dom=dom)
            md.append(f"| {NAME[s]} | {dom or 'overall'} | {pe:.1f} | {re_:.2f} | {pd:.1f} | {pe - pd:.2f} | "
                      f"{ab:.2f} | {sb:.2f} | {re_ - ab:+.2f} |")
    md += ["", "Vicuna target (outputs not released): overall error implied by the paper's own domain cells, "
           "weighted by the number of injected scenarios per domain:", ""]
    for s, (vals, ov) in VICUNA_T5.items():
        c = collections.Counter(r["domain"] for r in L(f"adversarial/benefits_{s}"))
        n = [c[d] for d in DOMS]
        w = sum(v * k for v, k in zip(vals, n)) / sum(n)
        md.append(f"- {NAME[s]} → Vicuna: weighted {w:.1f} vs printed overall {ov}")
    Path(out).mkdir(parents=True, exist_ok=True)
    Path(out, "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    Path(out, "report.json").write_text(json.dumps(out_json, indent=1, default=float), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="clone of github.com/alexmeigz/ASSERT")
    ap.add_argument("--boot-b", type=int, default=10000)
    ap.add_argument("--out", default="results/authors_reanalysis")
    a = ap.parse_args()
    main(a.repo, a.boot_b, a.out)
