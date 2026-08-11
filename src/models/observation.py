from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class ObservationStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"


class ObservationBase(BaseModel):
    """Shared source and point-in-time contract for provider observations."""

    source: str = Field(..., min_length=1)
    observed_at: datetime | None
    retrieved_at: datetime

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        if self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must include a timezone")
        if self.observed_at is not None:
            if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
                raise ValueError("observed_at must include a timezone")
            if self.observed_at > self.retrieved_at:
                raise ValueError("observed_at cannot be after retrieved_at")
        return self


class MetricObservation(BaseModel):
    status: ObservationStatus
    value: float | None = None
    unit: str = Field(..., min_length=1)
    missing_reason: str | None = None

    @model_validator(mode="after")
    def validate_status_fields(self) -> Self:
        if self.status == ObservationStatus.AVAILABLE:
            if self.value is None:
                raise ValueError("available observations require a value")
            if self.missing_reason is not None:
                raise ValueError("available observations cannot have a missing reason")
        else:
            if self.value is not None:
                raise ValueError("missing observations cannot have a value")
            if not self.missing_reason:
                raise ValueError("missing observations require a reason")

        return self

    @classmethod
    def available(cls, value: int | float, unit: str) -> Self:
        return cls(status=ObservationStatus.AVAILABLE, value=value, unit=unit)

    @classmethod
    def missing(cls, unit: str, reason: str) -> Self:
        return cls(
            status=ObservationStatus.MISSING,
            value=None,
            unit=unit,
            missing_reason=reason,
        )

    @property
    def is_available(self) -> bool:
        return self.status == ObservationStatus.AVAILABLE
