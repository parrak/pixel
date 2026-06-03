# ASC RCM Copilot Execution Plan

## Already completed before this run

- ASC RCM ingestion and domain model layer in [asc_rcm_lite](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite).
- Synthetic ASC case loading with fixture validation in [asc_rcm_lite/ingestion.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/ingestion.py) and [data/asc_cases](/Users/rakes/.codex/worktrees/a754/pixel/data/asc_cases).
- Stage 3A deterministic/local copilot abstraction in [asc_rcm_lite/copilot](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/copilot).
- Baseline tests for ingestion, legacy clinical detectors, reviewer packets, evals, and copilot safety in [tests](/Users/rakes/.codex/worktrees/a754/pixel/tests).

## Planned overnight execution

Use `main` as the base branch and continue building the remaining synthetic ASC/surgical RCM copilot product in small deterministic stages. This run completed the full planned scope.

## Stage checklist

- [x] Stage 0: Repo inspection, baseline test run, checkpoint file setup
- [x] Stage 1: AI Coding Copilot
- [x] Stage 2: A/R Flagging and Work Queue Prioritization
- [x] Stage 3: Denials / appeals copilot expansion
- [x] Stage 4: Workflow assistant, payer pattern intelligence, reviewer packets
- [x] Stage 5: Streamlit ASC RCM Copilot workbench
- [x] Stage 6: Copilot eval harness, demo script, docs polish

## Current completed stages

- Stage 0: repo inspection, checkpoint file creation, and clean baseline test confirmation.
- Stage 1: deterministic coding QA detectors and coding copilot drafts.
- Stage 2: deterministic A/R flags, work queue prioritization, and A/R copilot drafts.
- Stage 3+: workflow assistant, denial copilot, payer intelligence, reviewer packets, pipeline orchestration, provider abstraction, persistence, import/export, Streamlit workbench, eval harness, and documentation polish.

## Current in-progress stage

- None. All planned stages are complete.

## Remaining stages

- None.

## Files added/modified in each completed stage

- Stage 0
  - Added [docs/ASC_RCM_COPILOT_EXECUTION_PLAN.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/ASC_RCM_COPILOT_EXECUTION_PLAN.md)
- Stage 1
  - Added [asc_rcm_lite/detectors/__init__.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/detectors/__init__.py)
  - Added [asc_rcm_lite/detectors/coding.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/detectors/coding.py)
  - Added [asc_rcm_lite/copilot/coding_copilot.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/copilot/coding_copilot.py)
  - Added [tests/test_coding_copilot.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_coding_copilot.py)
  - Updated [asc_rcm_lite/__init__.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/__init__.py)
- Stage 2
  - Added [asc_rcm_lite/detectors/ar.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/detectors/ar.py)
  - Added [asc_rcm_lite/workqueue.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/workqueue.py)
  - Added [asc_rcm_lite/copilot/ar_copilot.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/copilot/ar_copilot.py)
  - Added [tests/test_ar_copilot.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_ar_copilot.py)
  - Added [tests/test_workqueue.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_workqueue.py)
- Stage 3+
  - Added workflow modules in [asc_rcm_lite/workflow](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/workflow)
  - Added [asc_rcm_lite/detectors/denials.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/detectors/denials.py)
  - Added [asc_rcm_lite/copilot/denial_copilot.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/copilot/denial_copilot.py)
  - Added [asc_rcm_lite/intelligence/payer_patterns.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/intelligence/payer_patterns.py), [asc_rcm_lite/intelligence/root_cause.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/intelligence/root_cause.py), and [asc_rcm_lite/copilot/payer_intelligence_copilot.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/copilot/payer_intelligence_copilot.py)
  - Added reviewer packet and draft helpers in [asc_rcm_lite/reviewer](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/reviewer)
  - Added provider abstraction in [asc_rcm_lite/copilot/provider.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/copilot/provider.py)
  - Added orchestration in [asc_rcm_lite/pipeline.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/pipeline.py)
  - Added persistence, import, and export helpers in [asc_rcm_lite/persistence.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/persistence.py), [asc_rcm_lite/import_validation.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/import_validation.py), and [asc_rcm_lite/export.py](/Users/rakes/.codex/worktrees/a754/pixel/asc_rcm_lite/export.py)
  - Added gold labels in [data/gold_labels/asc_copilot_gold_labels.json](/Users/rakes/.codex/worktrees/a754/pixel/data/gold_labels/asc_copilot_gold_labels.json)
  - Added eval harness in [evals/run_asc_copilot_eval.py](/Users/rakes/.codex/worktrees/a754/pixel/evals/run_asc_copilot_eval.py)
  - Replaced the Streamlit UI in [ui/streamlit_app.py](/Users/rakes/.codex/worktrees/a754/pixel/ui/streamlit_app.py)
  - Added tests: [tests/test_workflow_assistant.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_workflow_assistant.py), [tests/test_denial_copilot.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_denial_copilot.py), [tests/test_payer_intelligence.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_payer_intelligence.py), [tests/test_reviewer_packets.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_reviewer_packets.py), [tests/test_pipeline.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_pipeline.py), [tests/test_provider.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_provider.py), [tests/test_copilot_eval.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_copilot_eval.py), [tests/test_persistence.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_persistence.py), and [tests/test_import_export.py](/Users/rakes/.codex/worktrees/a754/pixel/tests/test_import_export.py)
  - Updated [README.md](/Users/rakes/.codex/worktrees/a754/pixel/README.md) and added [docs/PRODUCT_SPEC.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/PRODUCT_SPEC.md), [docs/DATA_DICTIONARY.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/DATA_DICTIONARY.md), [docs/COPILOT_DEMO_SCRIPT.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/COPILOT_DEMO_SCRIPT.md), and [docs/EVAL_RESULTS.md](/Users/rakes/.codex/worktrees/a754/pixel/docs/EVAL_RESULTS.md)

## Tests run and results

- Stage 0
  - `uv run pytest`
  - Result: 21 passed, 0 failed
- Stage 1
  - `uv run pytest`
  - Result: 31 passed, 0 failed
- Stage 2
  - `uv run pytest`
  - Result: 41 passed, 0 failed
- Stage 3+
  - `uv run pytest`
  - Result: 81 passed, 0 failed
  - `uv run python -m asc_rcm_lite.pipeline --all`
  - Result: succeeded and returned structured case, queue, packet, and manager summary output
  - `uv run python evals/run_asc_copilot_eval.py`
  - Result: succeeded with citation completeness 1.0, human review required rate 1.0, zero unsafe language, and zero unsupported assertions

## Known gaps / TODOs

- The corpus remains intentionally small and synthetic.
- Follow-up history still uses `due_date` as a deterministic proxy rather than a richer touch-history model.
- The Streamlit workbench is a local demo surface rather than a production application.

## Resume instructions

- All planned stages are complete.
- If additional work is requested, preserve the current deterministic, synthetic-only, human-review-required guardrails.

## Current risks

- New enhancements should continue to preserve Python 3.9 compatibility.
- Any future scenario expansion should keep the gold labels and eval harness synchronized.
- UI work should remain clearly separated from any real payer, EHR, or PHI-bearing workflow.

## Next exact Codex prompt to resume from current stopping point

ASC RCM copilot execution is complete in `/Users/rakes/.codex/worktrees/a754/pixel`. If more work is needed, read `/Users/rakes/.codex/worktrees/a754/pixel/docs/ASC_RCM_COPILOT_EXECUTION_PLAN.md`, inspect the completed pipeline and docs, then define the next enhancement scope while preserving the existing synthetic-only, deterministic, and human-review-required guardrails.
