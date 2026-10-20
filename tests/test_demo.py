from __future__ import annotations

from scripts.run_demo import DEMO_CASES, run_demo


def test_offline_judge_demo_writes_all_six_cases(tmp_path) -> None:
    output = run_demo(tmp_path / "demo.md")
    text = output.read_text(encoding="utf-8")

    assert len(DEMO_CASES) == 6
    assert text.startswith("# TruthGuard Judge Demo")
    for label, question in DEMO_CASES:
        assert f"## {label}" in text
        assert question in text

    expected_statuses = {
        "T1 supersession": "resolved",
        "T2 scope": "conditional",
        "T3 numeric change": "resolved",
        "T5 exception": "conditional",
        "T6 abstention": "abstained",
        "T7 unknown": "not_in_corpus",
    }
    for label, status in expected_statuses.items():
        section = text.split(f"## {label}", 1)[1].split("\n## ", 1)[0]
        assert f"**Status:** `{status}`" in section
