# Citron Health

Citron Health is a synthetic ambulatory surgery center and surgical revenue-cycle copilot prototype. It helps coders, billers, denial specialists, auth specialists, and managers identify work, review cited evidence, understand why it matters, and generate reviewer-safe drafts.

The product is deterministic-first. Synthetic rules, synthetic payer policies, and synthetic contract references are the source of truth. Copilot output is assistive only.

## Positioning

- Synthetic ASC/surgical RCM workflow prototype
- Deterministic detectors for coding QA, A/R, denials, workflow routing, and payer intelligence
- Reviewer-safe drafts, packets, queue prioritization, and Streamlit workbench
- Local-only by default with a swappable mock copilot provider

## Compliance Guardrails

- Synthetic data only
- No PHI
- No external APIs by default
- No real payer submission
- No payer portal automation
- No autonomous coding decisions
- No definitive billing, coding, compliance, or payment claims
- Every surfaced item cites evidence
- Every draft and recommendation requires human review

## Supported ASC / Surgical RCM Opportunities

- Coding QA: modifier risk, laterality mismatch, bundled procedure risk, missing implant charge, documentation insufficiency, site-of-service issues, CPT/op-note mismatch
- A/R: high-dollar aging, 60/90/120+ aging, near-deadline denial work, stale follow-up, missing payer response, underpayment recovery
- Denials: prior auth, medical necessity, modifier/bundling, timely filing, payer-processing style classification
- Workflow: role-aware action suggestions, audit trace, queue routing, escalation support
- Payer intelligence: synthetic denial patterns, payer friction, top root causes, top recoverable A/R patterns

## Copilot Surfaces

- `asc_rcm_lite/copilot/coding_copilot.py`
- `asc_rcm_lite/copilot/ar_copilot.py`
- `asc_rcm_lite/copilot/denial_copilot.py`
- `asc_rcm_lite/copilot/workflow_assistant.py`
- `asc_rcm_lite/copilot/payer_intelligence_copilot.py`
- `ui/streamlit_app.py`

## Quickstart

```bash
uv sync --dev
uv run pytest
uv run python evals/run_asc_copilot_eval.py
uv run python -m asc_rcm_lite.pipeline --all
```

For the local Streamlit workbench, install the optional UI extra first:

```bash
uv sync --extra ui
uv run streamlit run ui/streamlit_app.py
```

## Vercel Deployment

This repository now exposes a top-level WSGI app at `app.py`, which matches Vercel's Python entrypoint requirements. The deployed surface provides:

- `/`: HTML dashboard for the synthetic ASC RCM workbench
- `/api/summary`: pipeline summary JSON
- `/api/case?case_id=ASC-CASE-008`: per-case JSON
- `/health`: deployment health check

To link the repo to the existing Vercel project and deploy from a machine with a valid Vercel login:

```bash
vercel link --yes --project pixel --scope rakesh-paridas-projects
vercel pull --yes --environment production
vercel build --yes
vercel deploy --prebuilt --prod
```

## Key Modules

- `asc_rcm_lite/ingestion.py`: synthetic ASC case loading and validation
- `asc_rcm_lite/detectors/`: deterministic coding, A/R, and denial detection
- `asc_rcm_lite/workqueue.py`: priority scoring and queue filtering
- `asc_rcm_lite/workflow/`: workflow states, actions, and audit trace
- `asc_rcm_lite/reviewer/`: unified reviewer packets and draft validation
- `asc_rcm_lite/pipeline.py`: end-to-end pipeline and CLI
- `asc_rcm_lite/persistence.py`: lightweight local workflow persistence
- `asc_rcm_lite/export.py`: deterministic export helpers
- `evals/run_asc_copilot_eval.py`: synthetic ASC copilot eval harness

## Current Eval Snapshot

`uv run python evals/run_asc_copilot_eval.py` currently reports:

```json
{
  "appeal_draft_completeness": 1.0,
  "ar_flag_recall": 1.0,
  "ar_priority_accuracy": 1.0,
  "cases": 8,
  "citation_completeness": 1.0,
  "coding_false_positive_rate": 0.0,
  "coding_opportunity_recall": 1.0,
  "denial_classification_accuracy": 1.0,
  "human_review_required_rate": 1.0,
  "owner_role_routing_accuracy": 1.0,
  "packets": 22,
  "phi_guardrail_pass_rate": 1.0,
  "priority_band_accuracy": 1.0,
  "unsafe_language_count": 0,
  "unsupported_assertion_count": 0,
  "workflow_next_action_accuracy": 1.0
}
```

## Known Limitations

- The corpus is intentionally small and synthetic.
- Touch-history and real follow-up activity are approximated through deterministic synthetic due dates.
- No real clearinghouse, payer, EHR, PM, or contract integrations exist.
- The mock copilot provider is local and template-based rather than model-backed.
- Some opportunity classes are represented by the current synthetic scenarios more richly than others.

See [docs/COMPLIANCE_GUARDRAILS.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/COMPLIANCE_GUARDRAILS.md), [docs/PRODUCT_SPEC.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/PRODUCT_SPEC.md), and [docs/COPILOT_DEMO_SCRIPT.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/COPILOT_DEMO_SCRIPT.md) for more detail.
