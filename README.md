# SmarterDx-lite v0.1

SmarterDx-lite is a local, synthetic clinical revenue integrity copilot prototype. It scans synthetic inpatient chart JSON, normalizes clinical facts, applies deterministic evidence detectors, and emits reviewer-validatable opportunities with chart citations, neutral query drafts, reviewer packets, an eval harness, and a simple Streamlit UI.

This is a venture diligence prototype, not clinical software. It does not ingest PHI, call external APIs, use an LLM for diagnosis detection, or state that a patient definitively has a diagnosis.

## Supported Opportunities

- AKI
- Sepsis / severe sepsis documentation clarification
- Acute respiratory failure

Every surfaced item is framed as an **opportunity for reviewer validation** and includes cited evidence from the synthetic chart.

## Pipeline

```text
synthetic chart JSON
-> ingestion
-> normalized facts
-> deterministic evidence detection
-> opportunity object
-> ranking / deduping
-> reviewer packet
-> eval report
-> UI
```

## Quickstart

```bash
uv run pytest
uv run python evals/run_eval.py
uv run streamlit run ui/streamlit_app.py
```

The Streamlit app lets a reviewer inspect the selected synthetic chart, coded diagnoses, ranked opportunities, evidence timeline, reviewer packet, neutral provider query, and audit trace.

## Project Layout

- `data/charts/`: 10 synthetic inpatient charts with embedded gold labels; at least 3 are negative controls.
- `smarterdx_lite/ingestion.py`: JSON ingestion and fact normalization.
- `smarterdx_lite/detectors/`: deterministic AKI, sepsis, and respiratory failure detectors.
- `smarterdx_lite/pipeline.py`: detector orchestration, ranking, and deduping.
- `smarterdx_lite/reviewer/packet.py`: reviewer packet and compliance-safe framing.
- `evals/run_eval.py`: metrics harness.
- `ui/streamlit_app.py`: local demo UI.
- `tests/`: ingestion, detector, packet/query safety, and eval tests.

## Eval Metrics

`uv run python evals/run_eval.py` reports:

- opportunity recall
- false positive rate
- evidence citation completeness
- unsupported assertion count
- provider query safety pass rate
- reviewer packet completeness

Current v0.1 synthetic-corpus result:

```json
{
  "charts": 10,
  "evidence_citation_completeness": 1.0,
  "false_positive_rate": 0.0,
  "opportunities_emitted": 10,
  "opportunities_expected": 10,
  "opportunity_recall": 1.0,
  "provider_query_safety_pass_rate": 1.0,
  "reviewer_packet_completeness": 1.0,
  "unsupported_assertion_count": 0
}
```

## Compliance Guardrails

- Synthetic data only; no PHI.
- No external APIs.
- Deterministic rules are the source of truth for detection.
- No opportunity is emitted without evidence citations.
- Packets and queries avoid definitive diagnosis statements.
- Queries are neutral and include “if clinically appropriate.”
- The prototype optimizes for clinical validity and documentation accuracy, not revenue capture.

## Known Limitations

- The corpus is small and intentionally synthetic; metrics should not be interpreted as real-world performance.
- AKI logic uses observed creatinine trends inside the chart rather than robust baseline provenance or full KDIGO timing windows.
- Sepsis logic is simplified to infection concern, antimicrobial therapy, and physiologic abnormalities; it is not a complete Sepsis-3 adjudication engine.
- Respiratory failure logic uses oxygen escalation plus hypoxemia or distress; it does not model chronic baseline oxygen use.
- No claims, coding grouper, denial workflow, utilization review integration, EHR integration, user authentication, database, queue, or cloud deployment is included.
- Reviewer packet generation is deterministic text templating; no local LLM summarizer is used in v0.1.

