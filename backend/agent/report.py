"""Structured, source-cited investigation report contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceFinding(BaseModel):
    evidence_id: str = Field(description="Exact evidence ID returned by a read-only evidence tool")
    interpretation: str = Field(min_length=4, max_length=240, description="Short interpretation directly supported by this evidence")


class InvestigationReport(BaseModel):
    classification: Literal["REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE"]
    summary: str = Field(min_length=20, max_length=700)
    evidence: list[EvidenceFinding] = Field(max_length=8)
    contradictions: list[str] = Field(max_length=8)
    missing_evidence: list[str] = Field(max_length=8)
    recommended_action: Literal["HUMAN_VERIFICATION", "CONTINUE_MONITORING", "NO_FURTHER_ACTION"]
