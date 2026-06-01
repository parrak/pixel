# smarter-rcm

`smarter-rcm` is a local, synthetic clinical revenue integrity prototype. The current working workflow is prebill documentation review: synthetic encounter bundles are converted into a shared encounter graph, evaluated through an evidence graph by workflow agents, and routed as evidence-cited reviewer actions.

This is a venture diligence prototype, not clinical software. It does not ingest PHI, call external APIs, use an LLM for diagnosis detection, or state that a patient definitively has a diagnosis.

## Current Workflow

Implemented and tested:
- Prebill detection for AKI
- Prebill detection for sepsis / severe sepsis documentation clarification
- Prebill detection for acute respiratory failure
- Evidence citations
- Neutral provider query drafts
- Reviewer action and packet generation
- Prebill eval metrics
- Streamlit UI

Scaffolded for later RCM expansion:
- Coding assist
- Denials
- Charges
- Utilization management
- Workqueue routing
- Payer policy and billing rule surfaces

## Pipeline

```text
synthetic chart JSON
-> encounter bundle
-> encounter graph
-> evidence graph
-> workflow agents
-> reviewer actions
-> evals
-> UI
```

## Quickstart

```bash
uv run pytest
uv run python evals/run_all.py
uv run python evals/run_prebill.py
uv run streamlit run ui/streamlit_app.py
```

The Streamlit app lets a reviewer inspect the selected synthetic encounter bundle, coded diagnoses, ranked reviewer actions, graph-backed evidence timeline, reviewer packet, neutral provider query, and audit trace.

## Project Layout

```text
smarter-rcm/
  AGENTS.md
  README.md
  pyproject.toml

  app/
    main.py
    core/
    rules/
    workflows/
    evals/

  data/
    synthetic_charts/
    synthetic_denials/
    synthetic_charge_masters/
    synthetic_policies/
    synthetic_claims/
    gold_labels/

  tests/
    core/
    rules/
    workflows/
    evals/

  evals/
    run_all.py
    run_prebill.py
    run_coding.py
    run_denials.py
    run_charges.py
    run_um.py

  ui/
    streamlit_app.py
```

## Eval Metrics

`uv run python evals/run_prebill.py` reports:

- opportunity recall
- false positive rate
- evidence citation completeness
- unsupported assertion count
- provider query safety pass rate
- reviewer packet completeness

Current synthetic prebill result:

```json
{
  "charts": 10,
  "evidence_citation_completeness": 1.0,
  "false_positive_rate": 0.0,
  "opportunities_emitted": 10,
  "opportunities_expected": 10,
  "opportunity_recall": 1.0,
  "provider_query_safety_pass_rate": 1.0,
  "reviewer_actions_emitted": 10,
  "reviewer_packet_completeness": 1.0,
  "unsupported_assertion_count": 0
}
```

## Guardrails

- Synthetic data only; no PHI.
- No external APIs.
- Deterministic rules are the source of truth for detection.
- No reviewer action is emitted without graph-backed evidence citations.
- Packets and queries avoid definitive diagnosis statements.
- Queries are neutral and include “if clinically appropriate.”
- The prototype optimizes for clinical validity and documentation accuracy, not revenue capture.

## Known Limitations

- The corpus is small and intentionally synthetic; metrics should not be interpreted as real-world performance.
- AKI logic uses observed creatinine trends inside the chart rather than robust baseline provenance or full KDIGO timing windows.
- Sepsis logic is simplified to infection concern, antimicrobial therapy, and physiologic abnormalities; it is not a complete Sepsis-3 adjudication engine.
- Respiratory failure logic uses oxygen escalation plus hypoxemia or distress; it does not model chronic baseline oxygen use.
- Coding assist, denials, charge validation, utilization management, and workqueue modules are scaffolds unless noted otherwise.
- No claims grouper, denial workflow integration, EHR integration, user authentication, database, queue, or cloud deployment is included.
