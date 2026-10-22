"""Offline smoke test: mock LLM, real SafeText data. Also sanity-checks the z-test."""
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_pipeline
from assert_repro.config import DecodingConfig
from assert_repro.generation import is_binary_compatible, parse_list
from assert_repro.llm import LLMClient
from assert_repro.stats import two_proportion_ztest


class MockLLM(LLMClient):
    def __init__(self):
        super().__init__(model="mock", decoding=DecodingConfig())

    def _request(self, messages, stop):
        q = messages[-1]["content"]
        if "paraphrase the following question" in q:
            return ("Should you do X?;;;Is it wise to do X?;;;What if you do X?;;;"
                    "How about doing X?;;;would you do X;;;Could you do X?!!!")
        if "In what other contexts" in q:
            return "if context A;;;when context B;;;to context C!!!"
        if "What other actions" in q:
            return "action 1;;;action 2!!!"
        if "what are some benefits" in q:
            return "benefit one;;;benefit two!!!"
        # classification: alternate-ish behaviour so errors are non-trivial
        return "Yes. mock rationale" if len(q) % 2 == 0 else "No. mock rationale"


def main():
    # --- unit checks -----------------------------------------------------------
    assert parse_list("A: a;;; b ;;;c!!!junk") == ["a", "b", "c"]
    assert parse_list("1. in a blizzard\n2. in a flood\n3. in a fire") == ["in a blizzard", "in a flood", "in a fire"]
    assert parse_list("- one\n- two!!!") == ["one", "two"]
    assert parse_list("1. a 2. b 3. c") == ["a", "b", "c"]
    from assert_repro.generation import clean_phrase
    assert clean_phrase("**Filling the tires with oil:** This could cause the tires to lose grip", "action") == "Filling the tires with oil"
    assert clean_phrase("**If you have a headache:** Taking too much aspirin", "context") == "If you have a headache"
    assert clean_phrase("Skip meals entirely - This can lead to dehydration", "action") == "Skip meals entirely"
    assert clean_phrase("In the context of X, the following actions would also be physically unsafe:", "action") is None
    assert clean_phrase("Mixing ammonia and chlorine bleach is indeed extremely dangerous because it can", "action") is None
    assert clean_phrase("Desperation for Cleanliness: If someone is extremely dirty", "context") is None
    assert clean_phrase("To address the scenario where X, here are some contexts:", "context") is None
    from assert_repro.generation import clean_benefits
    assert clean_benefits("Certainly! Here are some benefits:;;;Saves time;;;;\n;;;saves time;;;Keeps warm") == ["Saves time", "Keeps warm"]
    assert clean_benefits(";\n;") == [] and clean_benefits("- ;\n- ;") == []
    assert len(clean_benefits(";;;".join(f"benefit number {i}" for i in range(9)), k=5)) == 5
    assert is_binary_compatible("Should you eat it?")
    assert not is_binary_compatible("What if you eat it?")
    assert not is_binary_compatible("how about eating it?")
    assert not is_binary_compatible("Eat it please")
    # known value: 40/100 vs 60/100 -> z = -2.8284, p = 0.00468
    r = two_proportion_ztest(40, 100, 60, 100)
    assert math.isclose(r["z"], -2.8284, abs_tol=1e-3) and math.isclose(r["p"], 0.00468, abs_tol=1e-4), r
    assert r["significant"]
    assert not two_proportion_ztest(50, 100, 50, 100)["significant"]
    print("unit checks passed")

    # --- end-to-end with mock ----------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        args = run_pipeline.parse_args([
            "--repo", sys.argv[1] if len(sys.argv) > 1 else "./ASSERT",
            "--out", tmp, "--model", "mock", "--limit", "20", "--tb-n", "3", "--tb-m", "2"])
        res = run_pipeline.run(args, client=MockLLM())
        assert res["scores"]["baseline_unsafe"]["overall"]["n"] == 20
        assert res["scores"]["baseline_safe"]["overall"]["n"] == 20
        assert res["scores"]["saa_safe"]["overall"]["n"] > 0
        assert res["scores"]["tb_unsafe"]["overall"]["n"] > 0
        assert (Path(tmp) / "report.md").exists()
        assert not (Path(tmp) / ".pipeline.lock").exists(), "lock must be released after a run"
        # report / bootstrap / manifest scripts run on the finished mock run
        root = Path(__file__).resolve().parents[1]
        for cmd in (["scripts/make_report.py", "--out", tmp],
                    ["scripts/bootstrap.py", "--out", tmp, "--boot-b", "200"],
                    ["scripts/make_manifest.py", "--out", tmp, "--model", "mock"]):
            r = subprocess.run([sys.executable, "-I", *cmd], cwd=root, capture_output=True, text=True)
            assert r.returncode == 0, (cmd, r.stderr[-800:])
        for f in ("report_all.md", "bootstrap_report.md", "manifest.json"):
            assert (Path(tmp) / f).exists(), f
        man = json.loads((Path(tmp) / "manifest.json").read_text())
        assert man["cache_corrupt_lines"] == 0 and man["files"]["baseline_safe.jsonl"]["lines"] == 20
        assert "SAA (safe)" in (Path(tmp) / "bootstrap_report.md").read_text()
    with tempfile.TemporaryDirectory() as tmp:   # authors' released TB samples path
        args = run_pipeline.parse_args([
            "--repo", sys.argv[1] if len(sys.argv) > 1 else "./ASSERT",
            "--out", tmp, "--model", "mock", "--limit", "10", "--tb-source", "authors"])
        res = run_pipeline.run(args, client=MockLLM())
        assert res["scores"]["tb_authors_unsafe"]["overall"]["n"] == 3564
        assert "TB (authors' released samples)" in res["comparisons"]
    # --- robustness: corrupt cache lines are skipped; a second launch is refused ----
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "llm_cache.jsonl"
        cache.write_bytes(b'{"key": "a", "out": "x"}\n{"key": "b", "o\n\xff\xfe\n{"key": "c", "out": "z"}\n')
        c = MockLLM.__new__(MockLLM)
        LLMClient.__init__(c, model="mock", cache_path=str(cache))
        assert c._cache == {"a": "x", "c": "z"} and c.skipped_cache_lines == 2, (c._cache, c.skipped_cache_lines)
        with run_pipeline.RunLock(Path(tmp)):
            try:
                with run_pipeline.RunLock(Path(tmp)):
                    raise AssertionError("second launch was not refused")
            except SystemExit:
                pass
        assert not (Path(tmp) / ".pipeline.lock").exists()
    print("robustness checks passed")
    print("end-to-end smoke test passed")


if __name__ == "__main__":
    main()
