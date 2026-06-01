# Clinical RI Lite operating doctrine

This repo is a venture prototype for a synthetic clinical revenue integrity workflow.

## Founder intent

Build a credible local prototype that tests whether chart-scale evidence extraction can surface diagnosis documentation opportunities for human CDI / revenue integrity review.

## Product boundary

This is not a medical device, not a coding authority, not a claims system, and not a real patient workflow. Use synthetic data only.

## Architecture

Prefer deterministic, auditable logic for detection.

Pipeline:
synthetic chart JSON -> ingestion -> normalized facts -> deterministic detectors -> opportunities -> reviewer packet -> evals -> UI

## Clinical safety rules

Never state that a patient definitively has a diagnosis.

Use:
"possible opportunity for reviewer validation"

Do not use:
"patient has"
"confirmed"
"must code"
"billable diagnosis"

Every opportunity must include evidence citations.

If evidence is insufficient, do not surface the opportunity.

Provider queries must be neutral and non-leading.

## Engineering rules

Use Python.
Prefer `uv`.
Use Pydantic models.
Keep modules small.
Write tests for every detector.
Run tests before declaring completion.
Do not add external services.
Do not call external APIs.
Do not introduce cloud infrastructure.
Do not use real PHI.

## Eval doctrine

Every meaningful feature must be measurable.

Track:
- opportunity recall
- false positive rate
- evidence citation completeness
- unsupported assertion count
- provider query safety
- reviewer packet completeness

## Founder update format

At major checkpoints, summarize:
- Built
- Verified
- Risks
- Not built
- Next step
