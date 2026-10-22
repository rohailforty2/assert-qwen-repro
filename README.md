# assert-qwen-repro

Independent reproduction of **ASSERT** — *Automated Safety Scenario Red Teaming for Evaluating the
Robustness of Large Language Models* (Mei, Levy, Wang; Findings of EMNLP 2023) — on the **SafeText**
benchmark, using an open model (**Qwen2.5-7B-Instruct, 4-bit AWQ**) served with vLLM on a free Colab T4.

> **Status: draft.** Code, tests, documentation and the Colab notebook are in place. The numbers below
> are from the original run; they are replaced after the clean rerun (`results/<run-id>/`). Not affiliated with the ASSERT authors, the SafeText authors or the Qwen team.

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
  stats.py, data.py, config.py
run_pipeline.py          end-to-end driver (resumable stages, single-launch lock)
scripts/
  check_run.py           integrity checks for a run folder (PASS/FAIL)
  make_report.py         z-test tables from saved evaluation files
  bootstrap.py           cluster-bootstrap tables
  make_manifest.py       commit hashes, versions, GPU, file hashes
notebooks/
  assert_qwen_repro.ipynb  the whole experiment, run top to bottom on Colab
tests/smoke_test.py      offline test with a mock LLM
results/                 small summary files per run
docs/                    notes
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

## Results from the original run (provisional)

Cluster-bootstrap p-values; Δ in percentage points. One 4-bit 7B model, one run.

| Method | Baseline err % | Method err % | Δ [95% CI] | p |
|---|---|---|---|---|
| AKI 4-shot (unsafe) | 4.59 | 23.97 | +19.4 [15.6, 23.2] | <0.0001 |
| AKI zero-shot (unsafe) | 4.59 | 9.03 | +4.4 [2.4, 6.6] | <0.0001 |
| SAA (safe) | 15.05 | 17.24 | +2.2 [0.5, 3.9] | 0.013 |
| SAA (unsafe) | 4.34 | 5.53 | +1.2 [-0.8, 3.1] | 0.24 |
| TB, our generation | 4.59 | 5.48 | +0.9 [-1.6, 3.1] | 0.45 |
| TB, authors' samples | 4.59 | 1.77 | -2.8 [-5.1, -0.8] | 0.0064 |

Only AKI clearly raises error. About 30 tests were run, so the isolated SAA (safe) result should not be
over-read. The paper's z-test is conservative on this data because variants of one scenario are
correlated; the bootstrap resamples whole source scenarios.

## Caveats

- Generated sets differ slightly between runs even with greedy decoding (for example the SAA-safe set had 5,197 items in one run and 5,203 in the next), so numbers shift by small amounts between reruns.
- One model (4-bit 7B), one run; vLLM greedy decoding is not bit-identical across batch compositions.
- TB "unsafe" labels written by the model are noisy (about 2 of 12 sampled scenarios were plainly safe).
- AKI hint quality was not checked by hand.
- An early TB result (11.22% error) was a parsing artifact and was retracted; see the report.
- I have not compared these numbers against the paper's tables.

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

Please cite this repository (`CITATION.cff`) and the works it builds on (`references.bib`): ASSERT
(Mei et al., 2023), SafeText (Levy et al., 2022), the Qwen2.5 Technical Report, AWQ and vLLM.
