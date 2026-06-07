# Citron Health Workflow-Native Reset Audit

## 1. Current Object Model

### Base Clinical / RCM Objects

The repository currently starts from synthetic ASC case facts in [asc_rcm_lite/models.py](/Users/rakes/Documents/pixel/asc_rcm_lite/models.py):

- `ASCCase`
- `PatientEncounter`
- `ProcedureCase`
- `ChargeLine`
- `Claim`
- `Authorization`
- `PayerPolicy`
- `Denial`
- `Remit`
- `RCMOpportunity`
- `WorkQueueItem`
- `EvidenceCitation`

This layer is strong on raw claim and denial facts, but it does not define:

- `Account`
- canonical `Work Object`
- reusable timeline object
- reusable evidence bundle object
- generated operational work product object

### Current Operating-System Objects

The current operating layer in [asc_rcm_lite/operations.py](/Users/rakes/Documents/pixel/asc_rcm_lite/operations.py) adds:

- `WorkflowDefinition`
- `WorkflowStage`
- `Organization`
- `Facility`
- `Team`
- `OperatorUser`
- `OperationalTask`
- `TaskRecommendation`
- `HumanDecision`
- `TaskOutcome`
- `DecisionMemoryRecord`
- HoldCo / initiative / benchmark / playbook objects

This means the true operational center today is still:

`Case -> OperationalTask -> Recommendation -> Decision -> Outcome`

not:

`Organization -> Facility -> Account -> Claim -> Work Object`

### Current Object-Model Conclusion

The system is richer than a simple copilot, but it is still task-first and portfolio-rollup-first rather than work-object-first.

## 2. Current Workflow Model

### Workflow Definitions

Config-backed workflow definitions exist in:

- [data/workflows/specialty_rcm_workflows.json](/Users/rakes/Documents/pixel/data/workflows/specialty_rcm_workflows.json)
- [asc_rcm_lite/operations.py](/Users/rakes/Documents/pixel/asc_rcm_lite/operations.py)

Current workflows include:

- `asc_authorization`
- `asc_coding_review`
- `asc_denial_review`
- `asc_charge_capture`
- `asc_ar_followup`

Each workflow currently has:

- stages
- owners
- SLAs
- trigger sources
- decision options
- target outcomes

### Workflow State Machinery

A lower-level state machine exists in:

- [asc_rcm_lite/workflow/state.py](/Users/rakes/Documents/pixel/asc_rcm_lite/workflow/state.py)
- [asc_rcm_lite/workflow/actions.py](/Users/rakes/Documents/pixel/asc_rcm_lite/workflow/actions.py)

Current states:

- `new`
- `needs_review`
- `needs_provider_info`
- `ready_for_correction`
- `ready_for_appeal`
- `pending_payer`
- `escalated`
- `closed`
- `written_off`

Current actions include:

- `prepare_payer_followup`
- `prepare_appeal_packet`
- `prepare_corrected_claim`
- `escalate_to_manager`
- `close_resolved`

### Workflow Model Conclusion

The repository already contains real workflow machinery, but the primary UI and data contract still present workflow through tasks and recommendations rather than through a canonical lifecycle-centered work object.

## 3. Current Role Model

The current operator role model is defined across:

- [asc_rcm_lite/operations.py](/Users/rakes/Documents/pixel/asc_rcm_lite/operations.py)
- [asc_rcm_lite/copilot/workflow_assistant.py](/Users/rakes/Documents/pixel/asc_rcm_lite/copilot/workflow_assistant.py)
- [ui/streamlit_app.py](/Users/rakes/Documents/pixel/ui/streamlit_app.py)

Supported roles:

- `manager`
- `denial_specialist`
- `biller` (AR Specialist)
- `coder`
- `auth_specialist`

Role-specific ownership and actions exist, but the current model has two weaknesses relative to the reset:

- `manager` is overloaded between manager and VP revenue-cycle usage
- role experiences still orbit tabs and dashboards rather than work resolution views

## 4. Current Navigation Model

### Streamlit Navigation

The Streamlit app currently uses tab navigation in [ui/streamlit_app.py](/Users/rakes/Documents/pixel/ui/streamlit_app.py):

- Operational Journeys
- HoldCo Command Center
- Value Creation
- Portfolio Benchmarks
- Playbooks
- Executive Review
- Monday Morning
- Role Queues
- Decision Intelligence
- Workflow Engine
- Acquisition Integration
- Legacy Features

This is broad and informative, but it is not workflow-native. Operators still enter a multi-tab command center rather than a work queue.

### Website / Demo Navigation

The public site currently routes through:

- `/`
- `/demo`
- `/architecture`
- `/about`

The demo at [demo.html](/Users/rakes/Documents/pixel/demo.html) and [site.js](/Users/rakes/Documents/pixel/site.js) is still built around a portfolio/holdco explanation model rather than around realistic operator work resolution.

## 5. Current Demo Architecture

There are now two demo architectures:

### Product Demo Surfaces

- Streamlit workbench
- fallback WSGI app in [app.py](/Users/rakes/Documents/pixel/app.py)
- static website demo in [demo.html](/Users/rakes/Documents/pixel/demo.html)

### Executable Journey Demos

Recent journey scripts exist:

- [demo_ar_specialist.py](/Users/rakes/Documents/pixel/demo_ar_specialist.py)
- [demo_ar_manager.py](/Users/rakes/Documents/pixel/demo_ar_manager.py)
- [demo_vp_revenue_cycle.py](/Users/rakes/Documents/pixel/demo_vp_revenue_cycle.py)
- journey engine in [asc_rcm_lite/journeys.py](/Users/rakes/Documents/pixel/asc_rcm_lite/journeys.py)

These are useful validations, but they are still centered on deterministic task runs rather than on canonical work objects with full operator-facing timelines, evidence packets, and generated work product.

## 6. Current Test Coverage

The repository currently has `103` automated tests covering:

- ingestion and PHI guardrails
- detectors
- copilot outputs and guardrails
- reviewer packets
- work queue generation
- workflow assistant action constraints
- persistence
- pipeline assembly
- operations / portfolio snapshot
- Vercel fallback routes
- end-to-end AR / manager / VP journey scripts

Current strengths:

- synthetic safety is well-covered
- pipeline integrity is well-covered
- recommendation and packet guardrails are well-covered
- Phase 4 holdco payloads are covered

Current gaps:

- no canonical work-object contract tests
- no timeline completeness tests
- no evidence-first rendering tests
- no generated work-product lifecycle tests
- no acceptance tests for the four scenario journeys in this reset
- no tests that assert operator surfaces begin from work rather than dashboard views

## 7. Gaps Relative To The Workflow-Native Strategy

### Object-Model Gaps

- No first-class `Account`
- No first-class `Work Object`
- Timeline, evidence, documents, recommendations, actions, outcome, and memory are spread across multiple objects instead of hanging from one work object

### Workflow Gaps

- The canonical lifecycle is still task-first
- Human + AI teaming states are not explicit at the work-object level
- Timeline exists implicitly in case facts and audit traces, but not as the primary operator record

### Operator-Experience Gaps

- The product still opens into leadership and portfolio surfaces
- Operators do not primarily begin in a work queue
- Recommendations are visible, but evidence and generated work product are not the dominant UI object

### Manager Gaps

- Manager intervention exists in journeys and some state transitions
- The product does not yet consistently present queue rebalancing, blocked work, escalation, and priority overrides as the manager's primary operating tools

### Demo Gaps

- Website demo is strategy-forward, not operator-workflow-forward
- Demo architecture still explains Citron instead of making a denial or AR specialist feel they could run work inside it

### Strategic Conclusion

Citron already has many building blocks required for the reset:

- deterministic case facts
- workflow definitions
- role-aware queueing
- recommendations
- decisions
- outcomes
- memory

But the center of gravity is still:

`task + recommendation + dashboard`

instead of:

`work object + timeline + evidence + operator workflow`

The implementation priority should therefore be:

1. Introduce a canonical work-object layer.
2. Make timeline first-class.
3. Make evidence and generated work product first-class.
4. Move operator surfaces to begin from work queues.
5. Re-express journeys and tests around work-object lifecycle integrity.
