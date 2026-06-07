# Citron Health Phase 2 Implementation Plan

## Product Reframe

Citron Health is the operating system for a specialty RCM platform.

The platform should center on:

Task -> Recommendation -> Human Decision -> Outcome

Existing copilot, detector, and reviewer modules remain in the product, but they become producers inside a larger workflow operating system.

## Milestones

### Milestone 1: Operating System Foundation

Status: in progress in this change set

Goals:

- Define workflow definitions as first-class objects
- Define task, recommendation, decision, and outcome primitives
- Rebuild the main product surface around a work queue
- Deliver a public branded site and no-login synthetic demo

Implementation:

- Introduce an operations domain layer in `asc_rcm_lite`
- Extend the pipeline to emit operational tasks and manager metrics
- Replace the case-first Streamlit landing experience with an Operations Command Center
- Add Workflow Engine and manager views
- Ship static `citron.health` pages for landing, architecture, about, and demo

Acceptance criteria:

- Existing copilot modules continue to work
- Every surfaced task has at least one recommendation
- The main Streamlit experience starts in a work queue
- The public demo shows task -> recommendation -> decision -> outcome

### Milestone 2: Decision Memory and Outcome Ledger

Goals:

- Persist operator decisions and outcomes
- Add workflow-level conversion, recovery, and turnaround metrics
- Introduce task history and decision playback

Implementation:

- Persist task decisions and outcomes in local storage
- Extend audit trace into decision memory
- Add manager reporting for recovery pipeline and bottleneck analysis

### Milestone 3: Configurable Workflow Engine

Goals:

- Make workflows configurable rather than hard-coded
- Support workflow templates, states, policies, and routing rules

Implementation:

- Add workflow configuration schema
- Add workflow compiler / validator
- Add configurable ownership, SLA, and state-transition rules

### Milestone 4: Operational Intelligence Layer

Goals:

- Learn from completed work
- Rank recommendations by workflow context and prior outcomes
- Surface bottleneck and root-cause intelligence at the operations level

Implementation:

- Add recommendation producer analytics
- Add outcome-linked workflow performance summaries
- Promote payer intelligence into broader operational intelligence

### Milestone 5: Platformization

Goals:

- Prepare the system for real integrations and multi-workflow scale
- Separate public site, app shell, and domain services cleanly

Implementation:

- Define service boundaries for ingestion, workflow engine, decision memory, and analytics
- Introduce deployment-ready app packaging
- Plan authentication and tenancy boundaries

## First Milestone Execution Notes

This repository change executes Milestone 1 only.

### Delivered in Milestone 1

- Phase 2 architecture assessment
- Phase 2 implementation plan
- Task-centric operating-system primitives
- Workflow catalog
- Operations Command Center UI
- Manager dashboard UI
- Workflow Engine UI
- Branded public site
- Interactive synthetic public demo

### Deferred to later milestones

- Persistent writeback of operator actions
- Full workflow configurator
- Real performance telemetry
- External system integrations
