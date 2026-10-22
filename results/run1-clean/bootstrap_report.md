### SAA (safe)

| Domain | Baseline err % | Method err % | Δ (pts) | 95% CI (cluster bootstrap) | p (cluster bootstrap) | p (naive z-test) | clusters |
|---|---|---|---|---|---|---|---|
| Outdoors | 10.61 | 15.08 | +4.47 | [+1.31, +7.62] | 0.0054 | 0.0664 | 234 |
| Medical | 10.90 | 14.14 | +3.24 | [+0.24, +6.20] | 0.0346 | 0.1237 | 301 |
| Household | 19.90 | 20.23 | +0.33 | [-2.92, +3.51] | 0.8276 | 0.9378 | 371 |
| Extra | 17.76 | 19.81 | +2.04 | [-2.70, +6.64] | 0.3980 | 0.5626 | 148 |
| Overall | 14.94 | 17.30 | +2.36 | [+0.62, +4.06] | 0.0094 | 0.0625 | 1054 |

### SAA (unsafe)

| Domain | Baseline err % | Method err % | Δ (pts) | 95% CI (cluster bootstrap) | p (cluster bootstrap) | p (naive z-test) | clusters |
|---|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 5.61 | +0.73 | [-2.44, +3.66] | 0.6774 | 0.7906 | 82 |
| Medical | 1.85 | 5.38 | +3.53 | [+0.37, +7.04] | 0.0248 | 0.1171 | 108 |
| Household | 6.25 | 5.31 | -0.94 | [-5.00, +2.66] | 0.6682 | 0.4529 | 128 |
| Extra | 3.92 | 5.88 | +1.96 | [-3.53, +8.24] | 0.5570 | 0.5768 | 51 |
| Overall | 4.34 | 5.48 | +1.14 | [-0.81, +3.09] | 0.2500 | 0.4903 | 369 |

### TB, our generation (unsafe)

| Domain | Baseline err % | Method err % | Δ (pts) | 95% CI (cluster bootstrap) | p (cluster bootstrap) | p (naive z-test) | clusters |
|---|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 5.09 | +0.21 | [-5.35, +4.79] | 0.8830 | 0.9341 | 82 |
| Medical | 1.85 | 4.08 | +2.23 | [-1.05, +4.89] | 0.1642 | 0.2543 | 108 |
| Household | 6.98 | 5.84 | -1.14 | [-6.04, +3.35] | 0.6562 | 0.6054 | 129 |
| Extra | 3.92 | 6.97 | +3.05 | [-3.70, +8.28] | 0.3362 | 0.4074 | 51 |
| Overall | 4.59 | 5.32 | +0.73 | [-1.73, +2.95] | 0.5300 | 0.5526 | 370 |

### TB, authors' samples (unsafe)  [clustered by context; unpaired]

| Domain | Baseline err % | Method err % | Δ (pts) | 95% CI (cluster bootstrap) | p (cluster bootstrap) | p (naive z-test) | clusters |
|---|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 1.35 | -3.53 | [-8.66, +0.58] | 0.1206 | 0.0164 | 82/311 |
| Medical | 1.85 | 0.79 | -1.06 | [-4.13, +1.03] | 0.4184 | 0.2633 | 108/350 |
| Household | 6.98 | 2.78 | -4.19 | [-8.96, +0.06] | 0.0528 | 0.0103 | 129/471 |
| Extra | 3.92 | 1.76 | -2.16 | [-8.40, +2.38] | 0.4478 | 0.2883 | 51/188 |
| Overall | 4.59 | 1.71 | -2.88 | [-5.21, -0.83] | 0.0054 | 0.0002 | 370/1320 |

### AKI zero-shot (unsafe)

| Domain | Baseline err % | Method err % | Δ (pts) | 95% CI (cluster bootstrap) | p (cluster bootstrap) | p (naive z-test) | clusters |
|---|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 9.13 | +4.25 | [+0.92, +8.22] | 0.0078 | 0.2202 | 82 |
| Medical | 1.89 | 2.50 | +0.61 | [-2.07, +3.56] | 0.6584 | 0.6998 | 106 |
| Household | 7.03 | 12.22 | +5.19 | [+1.09, +9.69] | 0.0116 | 0.0939 | 128 |
| Extra | 3.92 | 12.58 | +8.66 | [+3.03, +15.20] | 0.0010 | 0.0790 | 51 |
| Overall | 4.63 | 8.98 | +4.34 | [+2.27, +6.58] | 0.0002 | 0.0065 | 367 |

### AKI 4-shot (unsafe)

| Domain | Baseline err % | Method err % | Δ (pts) | 95% CI (cluster bootstrap) | p (cluster bootstrap) | p (naive z-test) | clusters |
|---|---|---|---|---|---|---|---|
| Outdoors | 4.88 | 19.05 | +14.17 | [+7.41, +21.49] | <0.0001 | 0.0021 | 82 |
| Medical | 1.89 | 11.56 | +9.68 | [+4.07, +16.23] | <0.0001 | 0.0024 | 106 |
| Household | 7.03 | 36.44 | +29.41 | [+22.63, +36.45] | <0.0001 | 0.0000 | 128 |
| Extra | 3.92 | 26.42 | +22.49 | [+11.39, +34.64] | <0.0001 | 0.0006 | 51 |
| Overall | 4.63 | 24.64 | +20.01 | [+16.11, +24.04] | <0.0001 | 0.0000 | 367 |
