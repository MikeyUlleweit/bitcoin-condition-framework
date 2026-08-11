from enum import StrEnum

from pydantic import BaseModel, Field


class SignalType(StrEnum):
    DESCRIPTIVE = "Descriptive"
    RISK = "Risk indicator"
    REGIME = "Regime indicator"
    PREDICTIVE = "Potentially predictive"
    MIXED = "Mixed"


class SourceStatus(StrEnum):
    CONNECTED = "Connected"
    VALID_PUBLIC_SOURCE = "Valid public source"
    DATA_UNAVAILABLE = "Data unavailable"
    SOURCE_REQUIRED = "Source required"
    NOT_SCORED = "Not scored"
    RESEARCH_ONLY = "Research only"


class CalibrationStatus(StrEnum):
    NOT_ASSESSED = "Not assessed"
    PROVISIONAL = "Provisional"
    VALIDATED = "Validated"


class ScoreContribution(BaseModel):
    name: str = Field(..., min_length=1)
    raw_value: float
    unit: str = Field(..., min_length=1)
    normalized_score: float = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    weighted_points: float = Field(..., ge=0, le=100)
    rationale: str = Field(..., min_length=1)


class SignalOutput(BaseModel):
    category: str = Field(..., min_length=1)
    score: float | None = Field(default=None, ge=0, le=100)
    condition: str = Field(..., min_length=1)
    signal_type: SignalType
    source_status: SourceStatus
    used_in_final_condition: bool
    evidence: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    required_sources: list[str] = Field(default_factory=list)
    score_breakdown: list[ScoreContribution] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    input_observation_types: list[str] = Field(default_factory=list)
    calibration_status: CalibrationStatus = CalibrationStatus.NOT_ASSESSED
    data_coverage: float = Field(default=0, ge=0, le=1)
    scope: str = Field(default="Not specified", min_length=1)

    def is_usable(self) -> bool:
        return (
            self.used_in_final_condition
            and self.score is not None
            and self.source_status
            in {
                SourceStatus.CONNECTED,
                SourceStatus.VALID_PUBLIC_SOURCE,
            }
        )
