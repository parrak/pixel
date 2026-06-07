# Citron Health Phase 2 Architecture Assessment

## Current State

The repository currently delivers a deterministic ASC RCM copilot prototype with these strengths:

- Strong synthetic case model and fixture discipline
- Deterministic detectors for coding, A/R, and denials
- Reviewer-safe drafts and evidence-cited packets
- Queue prioritization and workflow audit scaffolding
- Streamlit workbench for local product demonstration

The center of gravity is still:

Case -> Opportunity -> Packet

That orientation is visible in both the Python architecture and the UI:

- `asc_rcm_lite/pipeline.py` orchestrates case-level detector output
- `asc_rcm_lite/workqueue.py` only promotes A/R flags into queue entries
- `asc_rcm_lite/workflow/state.py` tracks state, but not recommendation, decision, or outcome memory
- `ui/streamlit_app.py` starts from case selection and copilot tabs rather than an operations queue

## Architectural Gaps Against Phase 2

### 1. Missing first-class task object

The current product has work queue entries, workflow items, opportunities, and packets, but no canonical operational task that can unify:

Task -> Recommendation -> Human Decision -> Outcome

As a result, each module emits useful work, but the platform cannot yet compound operational memory across workflows.

### 2. Producers are coupled to point-solution surfaces

Coding, denial, A/R, reviewer packet, and payer intelligence modules are implemented as destination features. In Phase 2, they should become producers that feed a shared operations layer.

### 3. Workflow definitions are implicit

Workflow routing is present, but workflow definitions are not configurable first-class objects. There is no system-level representation of:

- workflow identity
- queue semantics
- service-level expectations
- default ownership
- eligible states
- target outcomes

### 4. No decision memory or outcome tracking

The current stack records audit events, but not durable decision objects or outcome objects. That prevents the platform from learning from operator choices and realized recoveries.

### 5. Manager view is too shallow

Current manager metrics summarize queue counts and payer mix, but Phase 2 requires operational health views such as:

- revenue at risk
- queue aging
- open work by workflow
- bottlenecks
- recovery pipeline
- specialist productivity

### 6. Public product story is missing

The repo has no production-facing marketing surface. The current Streamlit app is useful as an internal workbench, but not as the branded public expression of the product.

## Phase 2 Architectural Direction

The platform should shift to a shared operating-system layer that sits between producers and user-facing surfaces.

### Target operating model

Detectors, copilot modules, and imported operational signals produce:

- operational tasks
- evidence-backed recommendations
- workflow-specific context

Operators then create:

- human decisions
- outcomes

Those records should drive:

- operations command center
- manager dashboard
- workflow engine
- no-login public demo

## First Milestone Definition

Phase 2 Milestone 1 establishes the new center of gravity without removing any existing capability.

### Milestone 1 scope

- Add first-class workflow definitions
- Add first-class operational task, recommendation, decision, and outcome models
- Transform existing coding, A/R, denials, and seeded work queue signals into operational tasks
- Re-center the Streamlit experience around an Operations Command Center and manager dashboard
- Preserve existing copilot tabs as supporting surfaces
- Launch a production-quality static citron.health site with a synthetic interactive demo

### Out of scope for Milestone 1

- External integrations
- Persistent real-user decision logging
- Multi-tenant authentication
- Admin workflow builder UI
- Net-new copilot categories

## Risks

- The current pipeline is case-centric, so task-centric orchestration must be layered in carefully to avoid regressions.
- Public-site demo data must stay synthetic and clearly separated from the local workbench.
- Manager metrics can only be approximate until persistent operator actions and outcomes exist.

## Recommendation

Keep the current deterministic modules intact and introduce a new operating-system layer as an additive abstraction. The first milestone should prove the architectural shift in both product surfaces and data model before deeper workflow configurability work begins.
