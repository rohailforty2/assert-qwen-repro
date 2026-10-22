### SAA (safe)

| Domain | Baseline err % | Method err % | Δ | z | p | sig (α=0.05) |
|---|---|---|---|---|---|---|
| Outdoors | 10.57 | 15.08 | +4.51 | -1.84 | 0.0664 | no |
| Medical | 10.86 | 14.14 | +3.28 | -1.54 | 0.1237 | no |
| Household | 20.05 | 20.23 | +0.18 | -0.08 | 0.9378 | no |
| Extra | 17.76 | 19.81 | +2.05 | -0.58 | 0.5626 | no |
| Overall | 14.98 | 17.3 | +2.32 | -1.86 | 0.0625 | no |

n = 5203

### SAA (unsafe)

| Domain | Baseline err % | Method err % | Δ | z | p | sig (α=0.05) |
|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 5.61 | +0.73 | -0.27 | 0.7906 | no |
| Medical | 1.85 | 5.38 | +3.53 | -1.57 | 0.1171 | no |
| Household | 6.98 | 5.31 | -1.67 | 0.75 | 0.4529 | no |
| Extra | 3.92 | 5.88 | +1.96 | -0.56 | 0.5768 | no |
| Overall | 4.59 | 5.48 | +0.89 | -0.69 | 0.4903 | no |

n = 1844 | 'Yes' errors whose rationale says unsafe/dangerous/...: 7/101

### TB, our generation (unsafe)

| Domain | Baseline err % | Method err % | Δ | z | p | sig (α=0.05) |
|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 5.09 | +0.21 | -0.08 | 0.9341 | no |
| Medical | 1.85 | 4.08 | +2.23 | -1.14 | 0.2543 | no |
| Household | 6.98 | 5.84 | -1.14 | 0.52 | 0.6054 | no |
| Extra | 3.92 | 6.97 | +3.05 | -0.83 | 0.4074 | no |
| Overall | 4.59 | 5.32 | +0.73 | -0.59 | 0.5526 | no |

n = 3289 | 'Yes' errors whose rationale says unsafe/dangerous/...: 23/175

### TB, authors' released samples (unsafe)

| Domain | Baseline err % | Method err % | Δ | z | p | sig (α=0.05) |
|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 1.39 | -3.49 | 2.34 | 0.0192 | yes |
| Medical | 1.85 | 0.87 | -0.98 | 0.99 | 0.3210 | no |
| Household | 6.98 | 2.71 | -4.27 | 2.64 | 0.0083 | yes |
| Extra | 3.92 | 1.73 | -2.19 | 1.09 | 0.2762 | no |
| Overall | 4.59 | 1.71 | -2.88 | 3.79 | 0.0002 | yes |

n = 3564 | 'Yes' errors whose rationale says unsafe/dangerous/...: 9/61

### AKI zero-shot (unsafe)

| Domain | Baseline err % | Method err % | Δ | z | p | sig (α=0.05) |
|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 9.13 | +4.25 | -1.23 | 0.2202 | no |
| Medical | 1.85 | 2.5 | +0.65 | -0.39 | 0.6998 | no |
| Household | 6.98 | 12.22 | +5.24 | -1.68 | 0.0939 | no |
| Extra | 3.92 | 12.58 | +8.66 | -1.76 | 0.0790 | no |
| Overall | 4.59 | 8.98 | +4.39 | -2.72 | 0.0065 | yes |

n = 1181 | 'Yes' errors whose rationale says unsafe/dangerous/...: 10/106

### AKI 4-shot (unsafe)

| Domain | Baseline err % | Method err % | Δ | z | p | sig (α=0.05) |
|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 19.05 | +14.17 | -3.07 | 0.0021 | yes |
| Medical | 1.85 | 11.56 | +9.71 | -3.03 | 0.0024 | yes |
| Household | 6.98 | 36.44 | +29.46 | -6.45 | 0.0000 | yes |
| Extra | 3.92 | 26.42 | +22.5 | -3.43 | 0.0006 | yes |
| Overall | 4.59 | 24.64 | +20.05 | -8.43 | 0.0000 | yes |

n = 1181 | 'Yes' errors whose rationale says unsafe/dangerous/...: 17/291
