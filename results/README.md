# Results

One folder per run: `results/<run-id>/` containing only small summary files:

- `report_all.md` — z-test tables, all methods
- `bootstrap_report.md` — cluster-bootstrap tables
- `manifest.json` — commit hash, package versions, GPU, model revision, file hashes

Raw generations, evaluation records and the LLM cache stay in Google Drive
(`MyDrive/assert/runs/<run-id>/`) and are not committed.
