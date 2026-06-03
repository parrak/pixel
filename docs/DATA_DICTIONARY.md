# Data Dictionary

## ASC Case

- `case_id`: synthetic case identifier
- `scenario`: synthetic scenario label
- `encounter`: encounter-level metadata and evidence citation
- `procedure_cases`: performed CPT-level procedures
- `charge_lines`: synthetic charge export lines
- `claims`: synthetic claims
- `authorizations`: synthetic authorization records
- `payer_policies`: synthetic payer policy or contract snippets
- `denials`: synthetic denials
- `remits`: synthetic remits
- `opportunities`: synthetic seeded opportunities used by deterministic workflows
- `work_queue_items`: synthetic queue entries

## Coding Opportunity

- `coding_issue_type`
- `severity`
- `risk_reason`
- `evidence_citation_ids`
- `suggested_human_review_action`
- `financial_impact_estimate`

## A/R Flag

- `flag_type`
- `days_in_ar`
- `balance`
- `aging_bucket`
- `next_deadline`
- `priority_score`
- `priority_band`
- `owner_role`

## Denial Opportunity

- `denial_category`
- `root_cause_hypothesis`
- `appealability`
- `missing_evidence`
- `recommended_path`
- `amount_at_risk`

## Workflow Item

- `current_state`
- `queue_type`
- `owner_role`
- `reason`
- `audit_trace`

## Reviewer Packet

- `packet_id`
- `case_id`
- `claim_id`
- `work_item_id`
- `opportunity_summary`
- `evidence_table`
- `recommended_next_action`
- `human_review_checklist`
- `human_review_required`
