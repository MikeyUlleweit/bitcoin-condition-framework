from enum import StrEnum

from pydantic import BaseModel, Field

from src.models.signal import SignalOutput


class BitcoinMarketCondition(StrEnum):
    ACCUMULATION = "Accumulation"
    EXPANSION = "Expansion"
    OVERHEATED = "Overheated"
    DISTRIBUTION = "Distribution"
    STRESS_CAPITULATION = "Stress / Capitulation"
    NEUTRAL_MIXED = "Neutral / Mixed"
    NOT_ENOUGH_DATA = "Not enough connected data"


class ConditionResult(BaseModel):
    final_condition: BitcoinMarketCondition
    confidence_score: float | None = Field(default=None, ge=0, le=100)
    usable_signal_count: int = Field(..., ge=0)
    minimum_required_signals: int = Field(..., ge=1)
    usable_signals: list[SignalOutput] = Field(default_factory=list)
    not_scored_signals: list[SignalOutput] = Field(default_factory=list)
    missing_categories: list[str] = Field(default_factory=list)
    summary: str
    evidence: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)

    def is_classified(self) -> bool:
        return self.final_condition != BitcoinMarketCondition.NOT_ENOUGH_DATA