"""Structured, source-cited investigation report contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceFinding(BaseModel):
    evidence_id: str = Field(description="Exact evidence ID returned by a read-only evidence tool")
    interpretation: str = Field(min_length=4, max_length=240, description="Short interpretation directly supported by this evidence")


class EvidenceContradiction(BaseModel):
    evidence_ids: list[str] = Field(min_length=2, max_length=8, description="IDs of the supplied records that conflict")
    explanation: str = Field(min_length=8, max_length=300, description="Exact conflict between the cited records")


class InvestigationReport(BaseModel):
    classification: Literal["REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE"]
    summary: str = Field(min_length=20, max_length=700)
    evidence: list[EvidenceFinding] = Field(max_length=8)
    contradictions: list[EvidenceContradiction] = Field(max_length=8)
    missing_evidence: list[str] = Field(max_length=12)
    uncertainties: list[str] = Field(max_length=8)
    recommendations: list[Literal[
        "HUMAN_VERIFICATION",
        "REVIEW_SENSOR_DISAGREEMENT",
        "REVIEW_EXPOSURE",
        "REVIEW_DATA_QUALITY",
        "REQUEST_ADDITIONAL_EVIDENCE",
        "NO_ADDITIONAL_ACTION_FROM_AGENT",
    ]] = Field(min_length=1, max_length=4)
