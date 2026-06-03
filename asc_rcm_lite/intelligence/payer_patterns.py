"""Synthetic payer-pattern aggregation."""

from __future__ import annotations

from dataclasses import dataclass

from asc_rcm_lite.detectors.ar import ARFlag
from asc_rcm_lite.detectors.denials import DenialOpportunity
from asc_rcm_lite.models import ASCCase

from .root_cause import top_root_causes


@dataclass(frozen=True)
class PayerPatternSummary:
    denials_by_payer: dict[str, int]
    denials_by_cpt: dict[str, int]
    denials_by_category: dict[str, int]
    ar_aging_by_payer: dict[str, dict[str, int]]
    underpayment_patterns: dict[str, int]
    repeated_documentation_patterns: dict[str, int]
    repeated_modifier_patterns: dict[str, int]
    top_preventable_root_causes: dict[str, int]
    top_recoverable_ar_opportunities: dict[str, int]
    payer_friction_score: dict[str, int]
    aggregate_evidence_ids: tuple[str, ...]


def build_payer_pattern_summary(
    cases: tuple[ASCCase, ...],
    denial_items: tuple[DenialOpportunity, ...],
    ar_flags: tuple[ARFlag, ...],
) -> PayerPatternSummary:
    denials_by_payer: dict[str, int] = {}
    denials_by_cpt: dict[str, int] = {}
    ar_aging_by_payer: dict[str, dict[str, int]] = {}
    underpayment_patterns: dict[str, int] = {}
    repeated_documentation_patterns: dict[str, int] = {}
    repeated_modifier_patterns: dict[str, int] = {}
    top_recoverable_ar_opportunities: dict[str, int] = {}
    evidence_ids: list[str] = []

    payer_by_case = {case.case_id: (case.claims[0].payer_id if case.claims else "NO-CLAIM") for case in cases}
    cpt_by_case = {case.case_id: (case.procedure_cases[0].cpt_code if case.procedure_cases else "NO-CPT") for case in cases}

    for item in denial_items:
        payer = payer_by_case.get(item.case_id, "NO-CLAIM")
        cpt = cpt_by_case.get(item.case_id, "NO-CPT")
        denials_by_payer[payer] = denials_by_payer.get(payer, 0) + 1
        denials_by_cpt[cpt] = denials_by_cpt.get(cpt, 0) + 1
        evidence_ids.extend(item.evidence_citation_ids)
        repeated_documentation_patterns[item.denial_category] = repeated_documentation_patterns.get(item.denial_category, 0) + (
            1 if item.denial_category == "medical_necessity" else 0
        )
        repeated_modifier_patterns[item.denial_category] = repeated_modifier_patterns.get(item.denial_category, 0) + (
            1 if item.denial_category in {"coding_modifier", "bundled_service"} else 0
        )

    for case in cases:
        for item in case.payer_policies:
            evidence_ids.append(item.citation.source_id)

    for flag in ar_flags:
        ar_aging_by_payer.setdefault(flag.payer, {})
        ar_aging_by_payer[flag.payer][flag.aging_bucket] = ar_aging_by_payer[flag.payer].get(flag.aging_bucket, 0) + 1
        if flag.flag_type == "underpayment":
            underpayment_patterns[flag.payer] = underpayment_patterns.get(flag.payer, 0) + 1
        top_recoverable_ar_opportunities[flag.flag_type] = top_recoverable_ar_opportunities.get(flag.flag_type, 0) + 1
        evidence_ids.extend(flag.evidence_citation_ids)

    root_causes = top_root_causes(denial_items)
    payer_friction_score = {
        payer: denials_by_payer.get(payer, 0) * 10 + sum(ar_aging_by_payer.get(payer, {}).values()) * 5
        for payer in set(denials_by_payer) | set(ar_aging_by_payer)
    }
    return PayerPatternSummary(
        denials_by_payer=denials_by_payer,
        denials_by_cpt=denials_by_cpt,
        denials_by_category=root_causes,
        ar_aging_by_payer=ar_aging_by_payer,
        underpayment_patterns=underpayment_patterns,
        repeated_documentation_patterns=repeated_documentation_patterns,
        repeated_modifier_patterns=repeated_modifier_patterns,
        top_preventable_root_causes=root_causes,
        top_recoverable_ar_opportunities=top_recoverable_ar_opportunities,
        payer_friction_score=payer_friction_score,
        aggregate_evidence_ids=tuple(dict.fromkeys(evidence_ids)),
    )
