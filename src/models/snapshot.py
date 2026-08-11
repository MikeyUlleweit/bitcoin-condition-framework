from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, model_validator

from src.models.blockspace import BlockspaceObservation
from src.models.liquidity import LiquidityObservation
from src.models.provisional import (
    HolderOnChainObservation,
    LeverageObservation,
    MarketRegimeObservation,
    MinerEconomicsObservation,
)
from src.models.signal import SignalOutput

ResearchObservation = Annotated[
    BlockspaceObservation
    | LiquidityObservation
    | MarketRegimeObservation
    | MinerEconomicsObservation
    | LeverageObservation
    | HolderOnChainObservation,
    Field(discriminator="observation_type"),
]


class ResearchSnapshot(BaseModel):
    schema_version: Literal[1] = 1
    snapshot_id: str = Field(..., min_length=1)
    created_at: datetime
    information_cutoff: datetime
    observations: list[ResearchObservation]
    signals: list[SignalOutput]

    @model_validator(mode="after")
    def validate_point_in_time_contract(self) -> Self:
        for name, timestamp in (
            ("created_at", self.created_at),
            ("information_cutoff", self.information_cutoff),
        ):
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError(f"{name} must include a timezone")

        for observation in self.observations:
            if observation.retrieved_at > self.information_cutoff:
                raise ValueError("observation retrieval time cannot be after information cutoff")

        observation_types = {observation.observation_type for observation in self.observations}
        referenced_types = {
            observation_type
            for signal in self.signals
            for observation_type in signal.input_observation_types
        }
        missing_types = sorted(referenced_types - observation_types)
        if missing_types:
            raise ValueError(
                "signal references observations absent from snapshot: " + ", ".join(missing_types)
            )

        return self
