# Citron Health Phase 7: Operational Credibility & Workflow of Record

## Objective

Make Citron plausibly usable by specialty RCM operators all day.

The primary product identity becomes:

- workflow system of record
- work object system
- operator workspace
- decision memory engine
- payer learning system

Not:

- generic dashboard
- generic copilot
- investor demo

## Canonical Data Model

Normalize the product around:

- Organization
- Facility
- Patient Account
- Encounter
- Procedure
- Claim
- Remittance
- Payer
- Authorization
- Denial
- Appeal
- Work Object
- Recommendation
- Action
- Outcome
- Timeline Event

The first implementation pass uses the existing synthetic ASC claim model and adds a canonical
work-object layer that hangs operational state, evidence, artifacts, actions, outcomes, and
memory from one object.

## Product Surface Shift

### Primary Screen

The primary operating screen becomes the Account Workspace:

- claim summary
- payer summary
- financial impact
- timeline
- open work objects
- evidence
- generated artifacts
- recommended actions
- prior outcomes
- activity history
- current owner
- recovery potential

### Workflow Workspaces

Add dedicated workflow-native surfaces for:

- denial resolution
- AR recovery
- manager intervention
- decision memory
- payer intelligence graph
- Nimble evaluation mode

## Intelligence Principle

Copilot outputs are work product, not chat.

Outputs should be directly usable operational artifacts such as:

- appeal packet
- payer summary
- evidence summary
- documentation checklist
- escalation summary
- manager briefing

## Acceptance Strategy

Acceptance tests should fail if:

- work objects stop being created
- timeline state stops updating
- evidence or artifacts disappear
- manager actions stop affecting workflow
- outcomes stop flowing into decision memory
- payer intelligence stops learning from workflow outcomes

## Current Implementation Scope

This phase adds:

- canonical work objects
- account workspaces
- denial and AR workspaces
- manager intervention system
- decision memory registry
- payer intelligence graph
- Nimble evaluation mode
- scenario-based workflow acceptance coverage

## Follow-On Work

The next credibility steps should focus on:

- deeper account / patient-account normalization in the base case model
- explicit appeal objects rather than inferred denial states
- richer artifact generation from existing copilot modules
- deeper manager intervention writeback into persistent workflow state
- public demo parity with the new account workspace
