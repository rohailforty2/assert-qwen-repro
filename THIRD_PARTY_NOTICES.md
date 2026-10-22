# Third-party materials and attribution

The MIT license in `LICENSE` covers **only the code and documentation written for this
repository**. It does not relicense, and does not change the terms of, anything below.

| Material | Owner / source | License | How this repo uses it |
|---|---|---|---|
| ASSERT code, few-shot files, bootstrap samples, model outputs | Mei, Levy, Wang — https://github.com/alexmeigz/ASSERT | Authors' own terms | **Not included.** Cloned at run time. Pinned commit: `1cafa82`. |
| ASSERT prompt text | same | Used with the authors' permission | Reproduced in **`assert_repro/authors_prompts.py` only**, so the same protocol is run. That file is **not part of this repo's MIT grant**; credit and rights stay with the authors. |
| SafeText dataset | Levy et al. — https://github.com/sharonlevy/SafeText | MIT, "Copyright (c) 2022 sharonlevy" | Not included. Read at run time from the cloned ASSERT repo. |
| Qwen2.5-7B-Instruct-AWQ weights | Qwen team — https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-AWQ | Apache License 2.0 | Not included. Downloaded at run time by vLLM. This repo is not affiliated with or endorsed by the Qwen team. |
| vLLM | https://github.com/vllm-project/vllm | Apache License 2.0 | Installed with pip; not included. |

Papers: ASSERT and SafeText are published under CC BY 4.0 on the ACL Anthology.
Full citations are in `references.bib` and `CITATION.cff`.

## Not committed on purpose

Model-generated scenarios, evaluation records and the LLM response cache are kept out of
the repository (see `.gitignore`): they contain unsafe-advice text derived from the
authors' data. Only aggregate tables are published under `results/`.
