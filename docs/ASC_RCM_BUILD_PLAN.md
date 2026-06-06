# Citron Health Build Plan

## Repository Baseline

The requested base branch is `main`, which currently contains only the initial `README.md` and `LICENSE`. The existing Clinical RI Lite implementation is present on `smarterdx-lite-v0.1` and should be used as the architectural source for the conversion: synthetic encounter bundles flow through deterministic normalization, graph-backed evidence, workflow detectors, reviewer actions, evals, and the Streamlit UI.

This plan does not change runtime behavior.

## Target Architecture

Citron Health should keep the same deterministic-first pipeline:

```text
synthetic ASC case JSON
-> normalized ASC case bundle
-> case / claim evidence graph
-> deterministic RCM detectors
-> evidence-cited opportunities
-> human reviewer packets
-> eval metrics
-> Streamlit command center UI
```

The architecture should remain local-only and synthetic-only. Deterministic rules are the source of truth for surfaced opportunities. Any optional narrative text must be derived from rule outputs and cited evidence, not from external APIs, payer portals, claims submission systems, or model adjudication.

Primary modules to preserve and adapt:

- `asc_rcm_lite/core`: shared models, ingest, normalization, graph construction, evidence graph, audit log, guardrail helpers.
- `asc_rcm_lite/rules`: deterministic detector rules grouped by ASC revenue cycle domain.
- `asc_rcm_lite/workflows`: workflow agents that convert rule findings into reviewer actions and packets.
- `asc_rcm_lite/evals`: reusable metric assertions for citation completeness, safety, unsupported claims, and packet completeness.
- `evals`: command-line eval runners for each workflow.
- `tests`: detector, workflow, graph, ingest, and eval tests.
- `ui/streamlit_app.py`: local Streamlit reviewer command center.

## Data Model

Replace the Clinical RI encounter-centered model with a synthetic ASC case model while preserving graph-backed evidence primitives.

Core entities:

- `AscCaseBundle`: synthetic source bundle with `case_id`, `source_type`, `facility`, `patient_stub`, `case`, `orders`, `procedure_notes`, `anesthesia_record`, `implant_log`, `charge_lines`, `claim_lines`, `authorization`, `payer_policy_refs`, `denial_history`, and `gold_opportunities`.
- `NormalizedAscCase`: normalized representation with synthetic demographics, case metadata, coded procedures, modifiers, units, revenue codes, diagnosis codes, authorization facts, payer facts, charge facts, and links to evidence graphs.
- `Citation`: unchanged concept; every cited fact includes source id, source type, timestamp, label, and excerpt.
- `Fact`: generalized from clinical fact to ASC RCM fact, with domains such as procedure, charge, claim, authorization, modifier, diagnosis, payer policy, implant, supply, anesthesia, and denial.
- `GraphEntity` / `GraphEdge`: unchanged evidence graph shape, but entity types should include `procedure`, `cpt_code`, `modifier`, `diagnosis_code`, `charge_line`, `claim_line`, `authorization`, `payer_policy`, `implant`, `supply`, `anesthesia_time`, `denial_reason`, and `case_event`.
- `RcmOpportunity`: replacement for diagnosis-focused `Opportunity`, with fields for `opportunity_domain`, `title`, `summary`, `rank_score`, `financial_context`, `evidence`, `recommended_reviewer_action`, `human_review_required`, and `audit_trace`.
- `ReviewerAction`: retained as the workflow output; action types should be review-only, such as `review_claim_edit`, `review_authorization_gap`, `review_charge_capture_gap`, `review_denial_workup`, and `review_coding_modifier_gap`.

No model should contain real patient identifiers, real claim identifiers, real payer account data, or portal credentials.

## Synthetic Data Plan

Create a synthetic corpus under `data/` with small, readable fixtures before expanding volume.

Initial folders:

- `data/synthetic_asc_cases/`: complete case bundles used by ingest, UI, and end-to-end evals.
- `data/synthetic_payer_policies/`: simplified synthetic payer policy snippets with stable ids and cited policy criteria.
- `data/synthetic_charge_masters/`: synthetic ASC charge master entries for procedure, supply, implant, anesthesia, and recovery charges.
- `data/synthetic_denials/`: synthetic denial remits and denial reason examples.
- `data/synthetic_claims/`: synthetic claim-line examples generated from case facts.
- `data/gold_labels/`: expected detector outputs by case and workflow.

The first corpus should include 15-25 cases covering common ASC workflows:

- missing or mismatched prior authorization
- CPT / modifier mismatch
- missing implant or high-cost supply charge
- duplicate charge line
- unit mismatch
- diagnosis-policy mismatch for medical necessity review
- anesthesia time discrepancy
- bundled charge risk
- denial appeal packet candidate
- clean negative controls with no opportunity

All names, dates, member ids, claim ids, payer names, facility names, policy ids, and clinical snippets must be synthetic. Fixtures should include an explicit `synthetic: true` flag and should fail ingest if omitted.

## Detectors

Detectors should remain deterministic, auditable, and testable. Each detector returns an opportunity only when all required evidence citations are present.

Initial detector groups:

- Authorization: missing authorization, expired authorization, procedure not covered by authorization, facility mismatch, and date-of-service mismatch.
- Coding and modifiers: CPT mismatch against procedure note, missing laterality modifier, missing discontinued/reduced-service modifier, invalid modifier combination, diagnosis mismatch for procedure support.
- Charge capture: missing implant charge, missing supply charge, missing anesthesia charge, missing recovery charge, duplicate charge, unit mismatch, and charge posted without supporting evidence.
- Claim scrub: place-of-service mismatch, revenue code mismatch, payer-specific required field missing, NCCI-style synthetic edit, and line-level bundling risk.
- Denial workup: denial reason mapped to missing evidence, appeal evidence checklist completeness, timely filing risk, and under-documented medical necessity packet.
- Workqueue prioritization: deterministic priority scoring based on evidence strength, deadline, expected operational impact, and review complexity.

Detectors must not make final billing, coding, medical necessity, or submission decisions. They should surface possible opportunities for reviewer validation only.

## Reviewer Packet Model

Every surfaced opportunity should produce a reviewer packet with:

- case id and workflow
- opportunity title and deterministic rule id
- reviewer framing that avoids definitive billing or coding assertions
- required human decision
- evidence citations with source ids, excerpts, timestamps, and graph links
- policy or charge master citations when relevant
- recommended reviewer checklist
- non-submission disclaimer
- audit trace of normalization, detector, scoring, and packet rendering

Packet language should use review framing such as:

- "possible opportunity for reviewer validation"
- "please verify against source documentation"
- "if appropriate after human review"

Packet language should avoid:

- "submit this claim"
- "bill this code"
- "payer will deny"
- "guaranteed reimbursement"
- "patient has"
- "confirmed"

The packet should not automate payer portal actions, claims submission, coding finalization, or denial appeals. It should prepare a human reviewer to decide.

## Eval Metrics

Keep the existing eval doctrine and add ASC-specific metrics.

Core metrics:

- opportunity recall against synthetic gold labels
- false positive rate
- evidence citation completeness
- unsupported assertion count
- reviewer packet completeness
- human-review-required pass rate
- synthetic-data-only pass rate
- no-external-api pass rate

ASC-specific metrics:

- authorization gap recall
- charge capture gap recall
- coding / modifier edit recall
- claim scrub edit recall
- denial workup packet completeness
- policy citation completeness
- charge master citation completeness
- negative-control silence rate
- duplicate opportunity rate
- priority ordering agreement with gold severity labels

Every eval runner should be executable with `uv run python evals/run_<workflow>.py`, and `uv run python evals/run_all.py` should aggregate all workflow metrics.

## UI Pages

Keep Streamlit as the local UI and convert the page title and workflow surfaces to Citron Health.

Proposed pages:

- Overview: total synthetic cases, open reviewer actions, workflow counts, guardrail status, and eval summary.
- Workqueue: prioritized reviewer actions across authorization, coding, charge capture, claim scrub, and denials.
- Case Review: selected synthetic ASC case, source bundle, timeline, claim lines, charge lines, authorization, and policy references.
- Evidence Graph: graph-backed timeline and linked evidence for selected opportunities.
- Reviewer Packet: packet text, checklist, cited evidence, audit trace, and explicit human-review-required status.
- Evals: latest local eval metrics and gold-label comparison.
- Guardrails: synthetic-only status, no PHI checks, no external API checks, no submission / portal automation checks.

The UI must not include controls that imply real claims submission, payer portal automation, final coding approval, or direct appeal filing.

## Compliance Guardrails

Hard constraints:

- synthetic data only
- no PHI
- no external APIs
- no real claims submission
- no payer portal automation
- deterministic rules are source of truth
- every surfaced opportunity includes evidence citations
- every recommendation requires human review

Implementation guardrails:

- Ingest rejects bundles without `synthetic: true`.
- Ingest rejects PHI-like fields such as real names, street addresses, phone numbers, email addresses, MRNs, SSNs, real member ids, and real claim ids.
- Tests assert no network calls are required or configured.
- UI copy states that the app is local, synthetic, and review-only.
- Reviewer actions include `human_review_required=True`.
- Packet completeness checks fail when citations, audit trace, or review disclaimers are missing.
- Rule tests include negative controls to ensure insufficient evidence emits no opportunity.
- No module should contain payer portal URLs, credentials, submission endpoints, or automation hooks.

## Staged Implementation Sequence

1. Baseline restoration and rename
   - Bring the Clinical RI Lite code structure from the implementation branch onto `main`.
   - Rename user-facing product text to Citron Health.
   - Keep tests, eval runners, synthetic-data folders, and Streamlit entry point intact.

2. Core model conversion
   - Add ASC case models while preserving citation, graph entity, evidence item, reviewer action, and audit trace primitives.
   - Update ingest and normalization for synthetic ASC bundles.
   - Add synthetic-only validation.

3. Synthetic corpus
   - Add initial ASC case fixtures, payer policy snippets, charge master snippets, claims, denials, and gold labels.
   - Include negative controls and edge cases for each workflow.

4. Deterministic detectors
   - Implement authorization detectors first.
   - Add charge capture detectors.
   - Add coding / modifier detectors.
   - Add claim scrub detectors.
   - Add denial workup detectors.
   - Add deterministic workqueue prioritization.

5. Reviewer packet conversion
   - Replace provider-query packet content with ASC reviewer checklists.
   - Require evidence citations, audit trace, policy / charge master references where applicable, and human review disclaimers.

6. Eval expansion
   - Convert prebill evals into ASC workflow evals.
   - Add guardrail assertions for synthetic-only data, citation completeness, unsupported claims, and human-review-required recommendations.
   - Aggregate workflow evals in `evals/run_all.py`.

7. Streamlit command center
   - Convert the current single-review view into the proposed command center pages.
   - Keep the UI local-only and review-only.
   - Surface evidence citations before recommendations.

8. Regression hardening
   - Add tests for every detector and packet renderer.
   - Add fixture validation tests for no PHI and no real submission artifacts.
   - Run `uv run pytest` and all eval runners before declaring the conversion complete.

9. Documentation update
   - Update `README.md` and operating doctrine after implementation.
   - Document quickstart commands, guardrails, known limitations, and current eval results.
