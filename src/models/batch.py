from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from src.models.snapshot import ResearchObservation


class ProviderFailure(BaseModel):
    provider: str = Field(..., min_length=1)
    observation_type: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    error_type: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    occurred_at: datetime


class ObservationBatch(BaseModel):
    collected_at: datetime
    observations: list[ResearchObservation]
    failures: list[ProviderFailure]

    @model_validator(mode="after")
    def collected_at_must_be_timezone_aware(self) -> Self:
        if self.collected_at.tzinfo is None or self.collected_at.utcoffset() is None:
            raise ValueError("collected_at must include a timezone")
        return self
