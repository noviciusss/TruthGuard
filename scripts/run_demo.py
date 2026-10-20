"""Run the fixed, offline TruthGuard judge demo.

The demo deliberately uses the deterministic critic and local corpus so a
submission can be reproduced without API keys, network access, or quota.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

# The judge demo must remain reproducible even when a developer's .env enables
# live providers for other commands.
os.environ["TRUTHGUARD_OFFLINE"] = "true"

from truthguard.pipeline import build_default_pipeline  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]

DEMO_CASES = (
    ("T1 supersession", "What is the hospitalization waiting period for the Standard plan?"),
    ("T2 scope", "Is the co-payment different for a member aged 60 or above?"),
    ("T3 numeric change", "When does the claim submission window close after discharge?"),
    ("T5 exception", "Can an emergency admission proceed without prior approval?"),
    ("T6 abstention", "What is the annual hospitalization limit for the Aurelia Standard plan?"),
    ("T7 unknown", "Does Aurelia cover hearing-aid batteries after a routine replacement?"),
)


def _short_text(text: str, limit: int = 520) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"


def _markdown_section(label: str, question: str, answer) -> str:
    lines = [f"## {label}", "", f"**Question:** {question}", "", f"**Status:** `{answer.status}`", "", "### Answer", "", _short_text(answer.answer_text or "(no answer; TruthGuard abstained)"), ""]
    if answer.conflicts:
        lines.extend(["### Conflicts", ""])
        for conflict in answer.conflicts:
            winner = conflict.winner_doc_id or "no single winner"
            lines.append(f"- `{conflict.type}` `{conflict.conflict_id}` — {winner}; {conflict.rationale}")
    else:
        lines.extend(["### Conflicts", "", "- No conflict was retained by the critic."])
    if answer.claims:
        lines.extend(["", "### Claims", ""])
        for claim in answer.claims:
            evidence_ids = [span.chunk_id for span in claim.supporting_spans]
            evidence = ", ".join(evidence_ids[:3]) or "none"
            if len(evidence_ids) > 3:
                evidence += ", …"
            lines.append(f"- `{claim.verdict}` {_short_text(claim.text, 220)} (evidence: `{evidence}`)")
    if answer.citations:
        citation_ids = sorted({span.chunk_id for span in answer.citations})
        lines.extend(["", "### Citations", "", ", ".join(f"`{chunk_id}`" for chunk_id in citation_ids)])
    lines.extend(["", "---", ""])
    return "\n".join(lines)


def run_demo(output_path: str | Path) -> Path:
    pipeline = build_default_pipeline(no_llm_critic=True)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        "# TruthGuard Judge Demo",
        "",
        "This report was generated offline from the committed synthetic corpus. "
        "It demonstrates supersession, scope, numeric, exception, abstention, "
        "and not-in-corpus behavior without provider calls.",
        "",
    ]
    for label, question in DEMO_CASES:
        answer = pipeline.run(question)
        sections.append(_markdown_section(label, question, answer))
    output_path.write_text("\n".join(sections), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/demo_output.md")
    args = parser.parse_args()
    path = run_demo(args.output)
    print(f"Wrote offline judge demo to {path}")


if __name__ == "__main__":
    main()
