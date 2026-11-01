# assert-qwen-repro

Independent reproduction of **ASSERT** — *Automated Safety Scenario Red Teaming for Evaluating the
Robustness of Large Language Models* (Mei, Levy, Wang; Findings of EMNLP 2023) — on the **SafeText**
benchmark, using an open model (**Qwen2.5-7B-Instruct, 4-bit AWQ**) served with vLLM on a free Colab T4.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23863456.svg)](https://doi.org/10.5281/zenodo.23863456)

- **Paper (preprint):** *Re-examining ASSERT: An Open-Model Replication and a Scenario-Level Re-analysis of
  Released Outputs*, Zenodo, [doi:10.5281/zenodo.23863456](https://doi.org/10.5281/zenodo.23863456)
  (PDF and LaTeX source also in [`paper/`](paper/)).
- **Interactive demo:** https://rohailforty2.github.io/assert-qwen-repro/ (exact prompts and recorded answers
  for Qwen, the authors' released answers for GPT-3.5, GPT-4, Alpaca and Vicuna, and a live bootstrap).
- **Status:** v0.1. Code, tests, Colab notebook, one clean run (`results/run1-clean/`) and a re-analysis of
  the authors' released outputs (`results/authors_reanalysis/`).

Not affiliated with the ASSERT authors, the SafeText authors or the Qwen team.

## What is reproduced, and what is adapted

| | Paper protocol (kept) | Qwen adaptation (changed) |
|---|---|---|
| Data | SafeText, 1,095 safe / 370 unsafe pairs, 4 domains | — |
| Evaluation | 4-shot Yes/No + rationale; per-domain two-tailed two-proportion z-test, α = 0.05 | First word is the label; unparsed answers count as errors |
| Decoding | Greedy: temperature 0, top_p 1, no penalties | `max_tokens` 256 (repo used 128 for some stages) |
| SAA | 5 paraphrases per scenario, `;;;` delimiter, `!!!` stop token | Keep a variant only if it ends in "?" and does not start with what/how/why |
| TB | 2 steps: new contexts from an action, then new actions per context | 3 × 3 expansion (not 5 × 5); extra system message and a strict phrase cleaner, because Qwen ignored the delimiter |
| TB (authors' samples) | The authors' released 3,564 TB scenarios | Evaluated with the same Qwen classifier |
| AKI | Model-written "benefits" injected as hints; zero-shot and adversarial 4-shot | Benefits with no real words (junk such as `;`) and duplicate benefits are dropped |
| Prompt order | — | System message placed **first** (the authors' code appends it last) |
| Model | Paper: GPT-3 / ChatGPT / GPT-4 / Alpaca / Vicuna | **Qwen2.5-7B-Instruct-AWQ** |
| Statistics | z-test as in the paper | **Added:** cluster bootstrap over source scenarios (paired and unpaired) |

Everything in the right column is a deviation. Treat results as a replication on a different, smaller model,
not as a test of the paper's numbers.

## Repository layout

```
assert_repro/            package
  authors_prompts.py     prompt text reproduced from the authors' repo (NOT under the MIT license)
  prompts.py             assembles chat messages
  generation.py          SAA, TB (strict cleaning), AKI benefit extraction
  evaluate.py            classification, scoring, comparison tables
  llm.py                 OpenAI-compatible client with disk cache
  align.py               links the authors' released paraphrases back to their source scenarios
  stats.py, data.py, config.py
run_pipeline.py          end-to-end driver (resumable stages, single-launch lock)
scripts/
  check_run.py           integrity checks for a run folder (PASS/FAIL)
  make_report.py         z-test tables from saved evaluation files
  bootstrap.py           cluster-bootstrap tables
  make_manifest.py       commit hashes, versions, GPU, file hashes
  reanalyze_authors.py   cluster-bootstrap re-analysis of the authors' released outputs (CPU, no model calls)
notebooks/
  assert_qwen_repro.ipynb  the whole experiment, run top to bottom on Colab
tests/smoke_test.py      offline test with a mock LLM
results/                 small summary files: run1-clean/ and authors_reanalysis/
docs/index.html          the interactive demo (served by GitHub Pages)
paper/                   the preprint: PDF, LaTeX source and bibliography
```

## Quick start (Colab, T4 GPU)

1. Open `notebooks/assert_qwen_repro.ipynb` in Colab and select a **T4 GPU** runtime.
2. Edit the one configuration cell (`RUN_ID`, `MODE`), then run all cells. The notebook clones this repo and
   the authors' repo (pinned commit), installs vLLM, serves `Qwen/Qwen2.5-7B-Instruct-AWQ` at a pinned
   revision, runs every stage, verifies the run, builds the tables and writes everything to Google Drive
   (`MyDrive/assert/runs/<run-id>/`). A clean run takes roughly an hour.
3. `MODE = "clean"` starts with an empty cache (a genuine reproduction); `MODE = "replay"` reuses a saved
   cache and finishes in minutes, replaying earlier answers.
4. Download the small summary zip at the end and commit it under `results/<run-id>/`. Never commit the
   `.jsonl` files or the cache.
5. A private repo needs a read-only GitHub token saved in Colab **Secrets** as `GITHUB_TOKEN`.

Offline check (no GPU, no API): `git clone https://github.com/alexmeigz/ASSERT` next to this repo, then
`python tests/smoke_test.py ./ASSERT`.

## Running the pipeline directly

```
python run_pipeline.py --repo ./ASSERT --out ./out --model Qwen/Qwen2.5-7B-Instruct-AWQ \
  --base-url http://localhost:8000/v1 --api-key EMPTY --tb-n 3 --tb-m 3
python run_pipeline.py --repo ./ASSERT --out ./out --model Qwen/Qwen2.5-7B-Instruct-AWQ \
  --base-url http://localhost:8000/v1 --api-key EMPTY --tb-source authors
```

Flags: `--limit N` (subsample), `--tb-n/--tb-m`, `--tb-source {generated,authors}`, `--workers N`, `--force`.
A lock file stops a second launch on the same output folder.

## Results (clean run `run1-clean`)

Clean run: empty cache, every answer generated by the model, repo commit `4b5411b`, Qwen weights pinned
to revision `b2503754`, Tesla T4. Full tables, per-domain rows and the file manifest are in
[`results/run1-clean/`](results/run1-clean/). Cluster-bootstrap p-values (10,000 resamples over source
scenarios); Δ in percentage points. Baseline varies slightly by row because each comparison uses only the
scenarios that have generated variants.

| Method | Baseline err % | Method err % | Δ [95% CI] | p (bootstrap) | p (naive z-test) |
|---|---|---|---|---|---|
| AKI 4-shot (unsafe) | 4.63 | 24.64 | +20.01 [16.11, 24.04] | <0.0001 | <0.0001 |
| AKI zero-shot (unsafe) | 4.63 | 8.98 | +4.34 [2.27, 6.58] | 0.0002 | 0.0065 |
| SAA (safe) | 14.94 | 17.30 | +2.36 [0.62, 4.06] | 0.0094 | 0.0625 |
| SAA (unsafe) | 4.34 | 5.48 | +1.14 [-0.81, 3.09] | 0.25 | 0.49 |
| TB, our generation | 4.59 | 5.32 | +0.73 [-1.73, 2.95] | 0.53 | 0.55 |
| TB, authors' samples | 4.59 | 1.71 | -2.88 [-5.21, -0.83] | 0.0054 | 0.0002 |

AKI sets contain 1,181 scenarios after a filter that drops junk or duplicate generated benefits.
An earlier run (before that filter and the pinned revisions) gave the same picture: AKI 4-shot +19.4,
AKI zero-shot +4.4, SAA (safe) +2.2, TB ours +0.9, TB authors' -2.8.

AKI is the only large effect. SAA (safe) is small (+2.4 points); it survives Holm's correction across the
six overall tests, but per-domain results (about 30 tests) are exploratory. The paper's z-test treats the
variants of one scenario as independent and compares against the full baseline; on this data it is too
cautious when coverage is complete (SAA safe: z-test p = 0.06, paired bootstrap p = 0.009).

About 1 in 6 AKI hints (212 of 1,181, by a keyword rule) were Qwen refusing to give a benefit. With the
remaining hints the 4-shot error is 28.1%, so the AKI result above is conservative.

## Re-analysis of the authors' released outputs

`scripts/reanalyze_authors.py` re-scores the answers the ASSERT authors released for GPT-3.5, GPT-4, Alpaca
and Vicuna (`python scripts/reanalyze_authors.py --repo ./ASSERT`, CPU only, under a minute).

- With the paper's own method it reproduces all 16 overall effects in the paper's Tables 2-4 to within
  0.03 points (the rounding of the printed values).
- **Vicuna, SAA on unsafe scenarios:** the paper reports -7.27 accuracy points (p < .01). Vicuna produced
  paraphrases for only 245 of the 370 scenarios, which are harder ones (baseline error 15.1% vs 10.5%).
  On the same 245 scenarios the effect is +2.7 error points, 95% CI [-0.8, 6.2], not significant.
- **GPT-3.5, SAA on unsafe scenarios:** z-test p = 0.23, paired bootstrap p = 0.04 (weak evidence; not
  significant after Holm correction).
- **Cross-model table (paper Table 5):** the error rates match the released files, but each change appears
  to be measured against the source model's baseline rather than the target's.
- AKI's large effects hold under every analysis.

Full tables: [`results/authors_reanalysis/report.md`](results/authors_reanalysis/report.md). Details and
limitations are in the paper.

## Caveats

- Generated sets differ slightly between runs even with greedy decoding (for example the SAA-safe set had 5,197 items in one run and 5,203 in the next), so numbers shift by small amounts between reruns.
- One model (4-bit 7B), one run; vLLM greedy decoding is not bit-identical across batch compositions.
- TB "unsafe" labels written by the model are noisy (about 2 of 12 sampled scenarios were plainly safe).
- AKI hints were not checked by hand; the refusal share above comes from a keyword rule and is approximate.
- An early TB result (11.22% error) during development was a parsing artifact; it was withdrawn and is not reported.

## Licenses

- This repository's code and documentation: **MIT** (`LICENSE`), except `assert_repro/authors_prompts.py`.
- The ASSERT prompt text (`assert_repro/authors_prompts.py`) belongs to the ASSERT authors and is used with their
  permission. None of their code or data is committed here (see `THIRD_PARTY_NOTICES.md`). SafeText is MIT.
  Qwen2.5-7B-Instruct-AWQ and vLLM are Apache-2.0 and are not redistributed.

## Acknowledgements

This project exists because of other people's work. Thank you to:

- **Alex Mei, Sharon Levy and William Wang** for ASSERT and for permission to build on it
  ([paper](https://aclanthology.org/2023.findings-emnlp.388/), [code](https://github.com/alexmeigz/ASSERT)).
- **Sharon Levy and co-authors** for the SafeText benchmark
  ([paper](https://aclanthology.org/2022.emnlp-main.154/), [data](https://github.com/sharonlevy/SafeText), MIT).
- **The Qwen team** for [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ) (Apache-2.0).
- **The vLLM project** ([github.com/vllm-project/vllm](https://github.com/vllm-project/vllm)) and the **AWQ** authors.

## Citation

If you use this work, please cite the preprint:

```bibtex
@misc{ahmad2026reexamining,
  author    = {Ahmad, Rohail},
  title     = {Re-examining {ASSERT}: An Open-Model Replication and a Scenario-Level Re-analysis of Released Outputs},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23863456},
  url       = {https://doi.org/10.5281/zenodo.23863456}
}
```

Please also cite the works it builds on (`references.bib`): ASSERT (Mei et al., 2023), SafeText
(Levy et al., 2022), the Qwen2.5 Technical Report, AWQ and vLLM. `CITATION.cff` describes this repository.
