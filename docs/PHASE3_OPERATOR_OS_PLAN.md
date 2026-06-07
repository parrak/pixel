# Citron Health Phase 3: Operator Operating System

## Reframe

Phase 2 established the first operating-system layer.

Phase 3 makes that layer operationally credible for acquired specialty RCM businesses.

Citron is not the productization of coding review, denial review, or reimbursement detection.
Those capabilities remain inside the system, but they now behave as workflow features inside a
larger operating model.

## Phase 3 Objective

Answer the question:

If Citron acquired a 75-person specialty RCM operator tomorrow, how would that business run
inside the software?

## Core Architectural Shift

The center of gravity moves from:

- task creation
- recommendation display

to a fuller operational graph:

- organization
- facility
- team
- user
- workflow definition
- task
- recommendation
- human decision
- outcome
- portfolio rollup

## Deliverables

### 1. Day In The Life

- Synthetic Monday morning operating view
- VP Revenue Cycle executive briefing
- Role-specific specialist queues
- Assignment and outcome narrative

### 2. Multi-Organization Support

- Portfolio model for ASC Alpha, ASC Bravo, and ASC Charlie
- Organization, facility, team, and user concepts
- Rollup dashboard for revenue at risk, recovery pipeline, productivity, aging, and health

### 3. Decision Memory

- First-class recommendation, decision, and outcome history
- Financial result and resolution time at the decision-memory level
- Visible history view for each task

### 4. Workflow Definition Engine

- Workflow definitions loaded from configuration
- Stages, actions, owners, SLAs, and outcomes represented outside detector code

### 5. Acquisition Integration Simulator

- Synthetic intake for ASC, Ophthalmology, GI, and Orthopedics acquisitions
- Workflow map, gaps, standardization opportunities, and deployment plan generation

### 6. Technology + Services Thesis

- Dedicated architecture storytelling on the website
- Clear explanation that Citron sits beside EHRs, PM systems, clearinghouses, and payer portals

## Implementation Strategy

### Domain

- Extend the operations layer rather than the detector layer
- Preserve all existing copilot and detector modules
- Make portfolio, workflow configuration, and decision memory additive

### Product Surfaces

- Rebuild Streamlit around portfolio operations and role-based work
- Rebuild the public demo around operational storytelling rather than detector storytelling
- Preserve legacy feature tabs as supporting modules

### Data

- Keep synthetic-only guardrails
- Add deterministic portfolio and user assignments
- Add deterministic decision-memory records and outcome metrics

## Acceptance Criteria

- The product reads as an operating system for specialty RCM, not an ASC copilot
- A VP Revenue Cycle can understand portfolio health in one view
- A specialist can see a role-specific queue, workload, recommendation, and outcome trail
- Workflow definitions come from configuration rather than only hard-coded catalog entries
- The website clearly explains the technology + services thesis and acquisition strategy
