# Citron Health Phase 8: Revenue Recovery Audit

## What Currently Exists

Citron now has a workflow-of-record foundation:

- canonical work objects with timeline, evidence, artifacts, recommendations, actions, outcomes, and institutional memory
- account workspaces built from work objects
- denial resolution and AR recovery workspaces
- manager intervention system
- decision memory registry
- payer intelligence graph
- executable workflow journeys and acceptance tests
- Streamlit operator surfaces for account workspace, work queue, denial, AR, manager OS, payer graph, and decision memory

## What Already Supports Denial Resolution

- Denial opportunities are detected from synthetic cases.
- Denial work objects include financial impact, payer-linked account, timeline, evidence, generated appeal packet, checklist, recommendations, owner, status, and outcome.
- Denial workspaces expose lifecycle stages from denial receipt through payment.
- Decision memory and payer graph already learn from completed denial work.

## What Already Supports AR Recovery

- AR flags produce work queue entries and operational tasks.
- AR work objects include aging, financial impact, payer summary, timeline, payer summary artifact, checklist, recommendations, and outcome.
- AR recovery workspace already groups AR follow-up and underpayment work.
- AR specialist and manager journeys already demonstrate follow-up, escalation, reassignment, and recovery.

## What Should Be Reused

- `WorkObject` as the canonical operating object.
- account workspace payload as the primary operating screen.
- generated artifacts from work-object documents.
- decision memory registry for similar recoveries and prior outcomes.
- payer intelligence graph as the basis for payer playbooks.
- workflow journeys as living product validation.

## What Should Be Removed Or De-Emphasized

Do not remove implemented capabilities, but de-emphasize them in the operator flow:

- holdco and investor storytelling should not be primary for Phase 8
- generic dashboard views should remain secondary
- generic copilot/chat framing should not be introduced
- broad specialty expansion should pause

## Remaining Gaps

- Revenue recovery needs a dedicated operating console, not only generic account/work-object views.
- Denial recovery needs explicit categories: missing documentation, medical necessity, authorization, coding, timely filing, eligibility, COB.
- Appeal workspace needs package readiness, submission status, and similar recovery context in one object.
- Evidence assembly should be explicit and grouped by operational evidence type.
- Payer playbooks should read like institutional expertise by payer.
- Synthetic scale should feel operationally alive: 500+ claims, 100+ denials, 50+ appeals.
- Nimble evaluation mode should tell one practical recovery story: 100 denials, $2.5M at risk, what to work first, and what gets recovered.
