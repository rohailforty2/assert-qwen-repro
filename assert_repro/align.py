"""Order-preserving alignment of paraphrases to SafeText source scenarios (Viterbi, <=5 per source).

The authors' released paraphrase files have no source id; outputs are stored in source order.
Validated in scripts/reanalyze_authors.py against GPT-3.5/GPT-4 files where the order is known.
"""
import re
import numpy as np
STOP = {"should","would","could","with","that","this","your","have","when","from","into","they","them",
        "what","there","their","being","while","about","after","someone","person","advisable","okay","safe"}
W = lambda s: frozenset(re.findall(r"[a-z]{4,}", s.lower())) - STOP

def score_matrix(paras, srcs):
    P = [W(p) for p in paras]; S = [W(s["prompt"] + " " + s["advice"]) for s in srcs]
    M = np.zeros((len(P), len(S)), np.float32)
    for i, a in enumerate(P):
        for j, b in enumerate(S):
            if a and b: M[i, j] = len(a & b) / len(a | b)
    return M

def align(paras, srcs, doms_p=None, k=5):
    """Return src index per paraphrase; assignment is non-decreasing, each source used <= k times."""
    M = score_matrix(paras, srcs)
    if doms_p is not None:  # forbid domain mismatches
        sd = np.array([s["domain"] for s in srcs]); pd = np.array(doms_p)
        M = np.where(pd[:, None] == sd[None, :], M, -5.0)
    n, m = M.shape; NEG = -1e9
    best = np.full((m, k), NEG); best[:, 0] = M[0]          # best[j,c]: item i at source j, c+1-th item there
    back = np.zeros((n, m, k), np.int32)                     # encoded previous state j*k+c
    for i in range(1, n):
        flat = best.max(1); arg = best.argmax(1)
        pm = np.maximum.accumulate(np.concatenate([[NEG], flat[:-1]]))   # best over sources < j
        pa = np.zeros(m, int); cur = -1; v = NEG
        for j in range(1, m):                                # argmax of prefix
            if flat[j-1] > v: v, cur = flat[j-1], j-1
            pa[j] = cur
        nb = np.full((m, k), NEG)
        nb[:, 0] = pm + M[i]
        back[i, :, 0] = np.where(pa >= 0, pa * k + arg[np.maximum(pa, 0)], 0)
        nb[:, 1:] = best[:, :-1] + M[i][:, None]
        back[i, :, 1:] = (np.arange(m)[:, None] * k + np.arange(k - 1)[None, :])
        best = nb
    j, c = np.unravel_index(best.argmax(), best.shape); out = [0] * n
    for i in range(n - 1, -1, -1):
        out[i] = j
        if i: s = back[i, j, c]; j, c = divmod(int(s), k)
    return out
