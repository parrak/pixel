"""Synthetic ASC RCM domain model and ingestion helpers."""

from .copilot import CopilotRequest, CopilotResponse, CopilotService, MockLLM, build_case_context
from .copilot.ar_copilot import ARCopilot, ARCopilotDraft
from .copilot.coding_copilot import CodingCopilot, CodingCopilotDraft
from .copilot.denial_copilot import DenialCopilot, DenialCopilotDraft
from .copilot.payer_intelligence_copilot import PayerIntelligenceAnswer, PayerIntelligenceCopilot
from .copilot.provider import MockLLMProvider, get_copilot_provider
from .copilot.workflow_assistant import WorkflowAssistant, WorkflowAssistantNote
from .detectors import ARFlag, CodingOpportunity, detect_ar_flags, detect_coding_opportunities
from .detectors.denials import DenialOpportunity, detect_denial_opportunities
from .ingestion import load_asc_cases
from .intelligence.payer_patterns import PayerPatternSummary, build_payer_pattern_summary
from .models import (
    ASCCase,
    Authorization,
    ChargeLine,
    Claim,
    Denial,
    EvidenceCitation,
    PatientEncounter,
    PayerPolicy,
    ProcedureCase,
    RCMOpportunity,
    Remit,
    WorkQueueItem,
)
from .operations import HumanDecision, OperationalTask, TaskOutcome, TaskRecommendation, WorkflowDefinition, workflow_catalog
from .pipeline import PipelineResult, run_pipeline
from .reviewer.packet import ReviewerPacket
from .workflow.state import WorkflowAuditEvent, WorkflowItem
from .workqueue import WorkQueueEntry

__all__ = [
    "ARCopilot",
    "ARCopilotDraft",
    "ARFlag",
    "ASCCase",
    "Authorization",
    "ChargeLine",
    "Claim",
    "CodingCopilot",
    "CodingCopilotDraft",
    "CodingOpportunity",
    "CopilotRequest",
    "CopilotResponse",
    "CopilotService",
    "DenialCopilot",
    "DenialCopilotDraft",
    "Denial",
    "DenialOpportunity",
    "EvidenceCitation",
    "HumanDecision",
    "MockLLM",
    "MockLLMProvider",
    "OperationalTask",
    "PatientEncounter",
    "PayerIntelligenceAnswer",
    "PayerIntelligenceCopilot",
    "PayerPatternSummary",
    "PayerPolicy",
    "PipelineResult",
    "ProcedureCase",
    "RCMOpportunity",
    "Remit",
    "ReviewerPacket",
    "WorkflowAssistant",
    "WorkflowAssistantNote",
    "WorkflowAuditEvent",
    "WorkflowDefinition",
    "WorkflowItem",
    "WorkQueueEntry",
    "WorkQueueItem",
    "build_case_context",
    "build_payer_pattern_summary",
    "detect_ar_flags",
    "detect_coding_opportunities",
    "detect_denial_opportunities",
    "get_copilot_provider",
    "load_asc_cases",
    "run_pipeline",
    "TaskOutcome",
    "TaskRecommendation",
    "workflow_catalog",
]
