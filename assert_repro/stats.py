"""Two-tailed two-proportion z-test (pooled), no SciPy needed."""
import math
from typing import Dict

from .config import ALPHA


def two_proportion_ztest(x1: int, n1: int, x2: int, n2: int, alpha: float = ALPHA) -> Dict[str, float]:
    """H0: p1 == p2. x = error counts, n = sample sizes.

    z = (p1 - p2) / sqrt(p_pool (1 - p_pool) (1/n1 + 1/n2));  p = 2 * (1 - Phi(|z|)).
    """
    if n1 == 0 or n2 == 0:
        return {"z": float("nan"), "p": float("nan"), "significant": False}
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:  # both proportions are 0 or both are 1
        return {"z": 0.0, "p": 1.0, "significant": False}
    z = (p1 - p2) / se
    p = math.erfc(abs(z) / math.sqrt(2))  # == 2 * (1 - Phi(|z|))
    return {"z": z, "p": p, "significant": p < alpha}
