# Re-analysis of the ASSERT authors' released outputs

Source: github.com/alexmeigz/ASSERT `data/` at commit 1cafa82. No model calls. Cluster bootstrap B=10000, seed 0. Unparsed answers count as errors. Δ = method error − baseline error (points).

## 1. Linking paraphrases to source scenarios

GPT-3.5/GPT-4 files hold exactly 5 paraphrases per source in source order (checked: domain matches 100%). The aligner is tested by deleting paraphrases at random from those files and recovering the source:

| Split | Deleted | Exact source | Same context |
|---|---|---|---|
| unsafe | 0% | 1.0000 | 1.0000 |
| unsafe | 20% | 1.0000 | 1.0000 |
| unsafe | 45% | 1.0000 | 1.0000 |
| safe | 0% | 1.0000 | 1.0000 |
| safe | 20% | 0.9674 | 1.0000 |
| safe | 45% | 0.9353 | 1.0000 |

Safe items are therefore clustered by context (exact source can be confused between safe answers that share a context); unsafe items by exact source.

## 2. Paper's comparison vs. paired cluster bootstrap

*Paper-style* = all method items vs. the FULL baseline, two-proportion z-test (as in the paper). *Paired* = only source scenarios that have variants, resampling whole scenarios. TB is unpaired (new scenarios), clustered by context.

| Model | Method | n | Paper Δ | Paper-style Δ (recomputed) | z-test p | Paired base % | Paired Δ [95% CI] | Bootstrap p | Scenarios covered |
|---|---|---|---|---|---|---|---|---|---|
| GPT-3.5 | SAA (safe) | 5475 | +2.77 | +2.76 | 0.0024 | 5.94 | +2.76 [+1.48, +4.03] | <0.0001 | 367 |
| GPT-3.5 | SAA (unsafe) | 1850 | +1.78 | +1.78 | 0.2324 | 5.95 | +1.78 [+0.11, +3.46] | 0.0396 | 370 |
| GPT-3.5 | TB | 3564 | -4.27 | -4.26 | 0.0000 | 5.95 | -4.26 [-6.82, -1.89] | <0.0001 | 367/1320 |
| GPT-3.5 | AKI 0-shot | 1835 | +7.60 | +7.62 | 0.0000 | 5.99 | +7.57 [+5.01, +10.25] | <0.0001 | 367 |
| GPT-3.5 | AKI 4-shot | 1835 | +45.60 | +45.61 | 0.0000 | 5.99 | +45.56 [+40.76, +50.14] | <0.0001 | 367 |
| GPT-4 | SAA (safe) | 5475 | +0.45 | +0.44 | 0.3658 | 1.83 | +0.44 [-0.26, +1.11] | 0.2194 | 367 |
| GPT-4 | SAA (unsafe) | 1850 | +0.81 | +0.81 | 0.4120 | 2.43 | +0.81 [-0.54, +2.16] | 0.2614 | 370 |
| GPT-4 | TB | 3564 | +1.55 | +1.55 | 0.1392 | 2.43 | +1.55 [-0.22, +3.15] | 0.0860 | 367/1320 |
| GPT-4 | AKI 0-shot | 1068 | +17.30 | +17.32 | 0.0000 | 3.41 | +16.35 [+12.48, +20.50] | <0.0001 | 264 |
| GPT-4 | AKI 4-shot | 1068 | +30.70 | +30.71 | 0.0000 | 3.41 | +29.74 [+24.46, +35.10] | <0.0001 | 264 |
| Alpaca | SAA (safe) | 5357 | +7.26 | +7.27 | 0.0000 | 27.40 | +7.27 [+5.22, +9.33] | <0.0001 | 367 |
| Alpaca | SAA (unsafe) | 1834 | +1.52 | +1.52 | 0.3013 | 5.95 | +1.52 [-0.35, +3.41] | 0.1218 | 370 |
| Alpaca | TB | 3564 | -4.55 | -4.54 | 0.0000 | 5.95 | -4.54 [-7.09, -2.11] | 0.0002 | 367/1320 |
| Vicuna | SAA (safe) | 4593 | +4.23 | +4.24 | 0.0001 | 8.59 | +4.32 [+2.86, +5.79] | <0.0001 | 363 |
| Vicuna | SAA (unsafe) | 1078 | +7.27 | +7.27 | 0.0010 | 15.10 | +2.71 [-0.84, +6.22] | 0.1398 | 245 |
| Vicuna | TB | 3564 | -7.12 | -7.12 | 0.0000 | 10.54 | -7.12 [-10.47, -3.94] | <0.0001 | 367/1320 |

## 3. Cross-model table (paper Table 5), target Alpaca, adversarial 4-shot

Implied baseline = paper error − paper Δ. It matches the SOURCE model's baseline, not Alpaca's.

| Benefits from | Domain | Paper error | Recomputed error | Paper Δ | Implied baseline | Alpaca baseline | Source baseline | Δ vs Alpaca baseline |
|---|---|---|---|---|---|---|---|---|
| GPT-3.5 | nature | 51.7 | 51.71 | 41.9 | 9.80 | 7.32 | 9.76 | +44.39 |
| GPT-3.5 | medical | 39.8 | 39.81 | 33.3 | 6.50 | 4.63 | 6.48 | +35.18 |
| GPT-3.5 | household | 67.0 | 67.03 | 63.9 | 3.10 | 6.98 | 3.10 | +60.05 |
| GPT-3.5 | other | 49.6 | 49.60 | 43.7 | 5.90 | 3.92 | 5.88 | +45.68 |
| GPT-3.5 | overall | 53.5 | 53.30 | 47.3 | 6.20 | 5.95 | 5.95 | +47.35 |
| GPT-4 | nature | 59.4 | 59.44 | 53.3 | 6.10 | 7.32 | 6.10 | +52.12 |
| GPT-4 | medical | 44.8 | 44.85 | 42.1 | 2.70 | 4.63 | 2.78 | +40.22 |
| GPT-4 | household | 72.8 | 72.82 | 72.0 | 0.80 | 6.98 | 0.78 | +65.85 |
| GPT-4 | other | 50.4 | 50.36 | 50.4 | 0.00 | 3.92 | 0.00 | +46.44 |
| GPT-4 | overall | 58.9 | 58.90 | 56.5 | 2.40 | 5.95 | 2.43 | +52.95 |

Vicuna target (outputs not released): overall error implied by the paper's own domain cells, weighted by the number of injected scenarios per domain:

- GPT-4 → Vicuna: weighted 55.3 vs printed overall 66.2
- GPT-3.5 → Vicuna: weighted 39.7 vs printed overall 39.7
