# ASC RCM Command Center Lite

ASC RCM Command Center Lite is a synthetic ambulatory surgery center (ASC) and
surgical revenue cycle prototype. It is intended for demonstrating command-center
workflows across scheduling, case readiness, charge capture, denial prevention,
and operational revenue cycle review using synthetic examples only.

The project is beginning a transition from Clinical RI Lite to an ASC-focused
revenue cycle command center. Existing Clinical RI Lite functionality remains
available as legacy clinical revenue integrity examples while new ASC-specific
capabilities are developed in the `asc_rcm_lite` package.

This is a venture diligence prototype, not clinical software. It does not ingest
PHI, call external APIs, use an LLM for diagnosis detection, provide coding
advice, provide billing advice, connect to real payers, or state that a patient
definitively has a diagnosis.

## Packages

- `asc_rcm_lite`: New top-level package for ASC RCM Command Center Lite
  functionality.
- `clinical_ri_lite`: Legacy clinical revenue integrity examples, including the
  existing AKI, sepsis, and respiratory examples and tests.

## Legacy Clinical RI Examples

The current implemented workflow scans synthetic inpatient chart JSON,
normalizes clinical facts, applies deterministic evidence detectors, and emits
reviewer-validatable opportunities with chart citations, neutral query drafts,
reviewer packets, an eval harness, and a simple Streamlit UI.

Supported legacy opportunities:

- AKI
- Sepsis / severe sepsis documentation clarification
- Acute respiratory failure

Every surfaced item is framed as an opportunity for reviewer validation and
includes cited evidence from the synthetic chart.

## Legacy Pipeline

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

The Streamlit app lets a reviewer inspect the selected synthetic chart, coded
diagnoses, ranked opportunities, evidence timeline, reviewer packet, neutral
provider query, and audit trace.

## Project Layout

- `asc_rcm_lite/`: New ASC RCM Command Center Lite package.
- `clinical_ri_lite/ingestion.py`: JSON ingestion and fact normalization.
- `clinical_ri_lite/detectors/`: Deterministic AKI, sepsis, and respiratory
  failure detectors.
- `clinical_ri_lite/pipeline.py`: Detector orchestration, ranking, and deduping.
- `clinical_ri_lite/reviewer/packet.py`: Reviewer packet and compliance-safe
  framing.
- `data/charts/`: 10 synthetic inpatient charts with embedded gold labels; at
  least 3 are negative controls.
- `docs/ASC_RCM_BUILD_PLAN.md`: Build plan for the ASC RCM transition.
- `docs/COMPLIANCE_GUARDRAILS.md`: Prototype compliance guardrails.
- `evals/run_eval.py`: Metrics harness.
- `tests/`: Ingestion, detector, packet/query safety, and eval tests.
- `ui/streamlit_app.py`: Local demo UI.

## Eval Metrics

`uv run python evals/run_eval.py` reports:

- opportunity recall
- false positive rate
- evidence citation completeness
- unsupported assertion count
- provider query safety pass rate
- reviewer packet completeness

Current legacy synthetic-corpus result:

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

## Compliance Boundaries

This repository is a prototype built around synthetic scenarios.

- It is not clinical software.
- It does not provide coding advice.
- It does not provide billing advice.
- It is not connected to real payers, clearinghouses, EHRs, practice management
  systems, or patient data.
- Outputs should be treated as operational workflow examples only and must not be
  used for patient care, claims submission, reimbursement decisions, or
  compliance determinations.
- Deterministic rules are the source of truth for detection.
- No opportunity is emitted without evidence citations.
- Packets and queries avoid definitive diagnosis statements.
- Queries are neutral and include "if clinically appropriate."

See `docs/COMPLIANCE_GUARDRAILS.md` for the project guardrails.

## Known Limitations

- The corpus is small and intentionally synthetic; metrics should not be
  interpreted as real-world performance.
- AKI logic uses observed creatinine trends inside the chart rather than robust
  baseline provenance or full KDIGO timing windows.
- Sepsis logic is simplified to infection concern, antimicrobial therapy, and
  physiologic abnormalities; it is not a complete Sepsis-3 adjudication engine.
- Respiratory failure logic uses oxygen escalation plus hypoxemia or distress;
  it does not model chronic baseline oxygen use.
- No claims, coding grouper, denial workflow, utilization review integration,
  EHR integration, user authentication, database, queue, or cloud deployment is
  included in the legacy Clinical RI examples.
- Reviewer packet generation is deterministic text templating; no local LLM
  summarizer is used in v0.1.
